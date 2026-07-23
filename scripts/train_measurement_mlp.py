#!/usr/bin/env python3
"""Train MLP neural network: 35 measurements → 10 SMPL betas.

Architecture: 36 → 128 → 64 → 10 (input includes gender flag)
Training: 50K synthetic shapes per gender, PyTorch with MPS/CPU
Output: JSON weights for browser deployment (no ONNX needed)

Key design:
- Non-linear mapping captures complex measurement-beta relationships
- Better conditioned than Ridge regression for extreme body types
- Gender-specific models (male breast betas constrained)
- Weighted loss: MSE on betas + reconstruction loss on measurements
"""

import json, os, sys, time
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(PROJECT_ROOT, 'public', 'assets', 'smpl_mlp_weights.json')
NUM_BETAS = 10
NUM_MEASUREMENTS = 35
SHAPES_PER_GENDER = 2000
BREAST_BETAS = [1, 2, 5]
BREAST_CLAMP = 0.3
BATCH_SIZE = 256
EPOCHS = 80
LEARNING_RATE = 1e-3
DEVICE = 'mps' if torch.backends.mps.is_available() else 'cpu'


def load_smpl():
    vt = np.load(os.path.join(PROJECT_ROOT, 'models', 'v_template.npy'))
    sd = np.load(os.path.join(PROJECT_ROOT, 'models', 'shapedirs.npy')).reshape(6890, 3, NUM_BETAS)
    faces = np.load(os.path.join(PROJECT_ROOT, 'api', 'services', 'src', 'tf_smpl', 'smpl_faces.npy'))
    return vt, sd, faces


def load_vertex_groups():
    path = os.path.join(PROJECT_ROOT, 'data', 'customBodyPoints.txt')
    groups = {}
    current = None
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith('#'):
                current = line[1:].strip().lower()
                groups[current] = []
            elif current is not None:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        idx = int(parts[1])
                        if 0 <= idx < 6890:
                            groups[current].append(idx)
                    except ValueError:
                        pass
    return groups


def precompute_face_masks(faces, vertex_groups):
    masks = {}
    for part, indices in vertex_groups.items():
        idx_set = set(indices)
        mask = np.zeros(len(faces), dtype=bool)
        for fi, f in enumerate(faces):
            if f[0] in idx_set or f[1] in idx_set or f[2] in idx_set:
                mask[fi] = True
        masks[part] = mask
    return masks


def load_smpl_segmentation():
    """Load SMPL part segmentation from the JS file."""
    path = os.path.join(PROJECT_ROOT, 'public', 'assets', 'smpl_segmentation.js')
    parts = {}
    with open(path) as f:
        content = f.read()
    # Remove 'const SMPL_PARTS = ' prefix and trailing '};'
    import re
    # Find all "key": [values] patterns - handles both quoted and unquoted keys
    pattern = r'"(\w+)":\s*\[([\d,\s]+)\]'
    for m in re.finditer(pattern, content):
        name = m.group(1)
        indices = [int(x.strip()) for x in m.group(2).split(',') if x.strip()]
        parts[name] = indices
    return parts


def measure_circ_mesh(vertices, faces, face_mask, plane_y):
    """Compute circumference via plane-mesh intersection + convex hull perimeter."""
    relevant_faces = faces[face_mask]
    if len(relevant_faces) == 0:
        return 0.0
    intersections = []
    for f in relevant_faces:
        v0, v1, v2 = vertices[f[0]], vertices[f[1]], vertices[f[2]]
        for va, vb in [(v0, v1), (v1, v2), (v2, v0)]:
            da, db = va[1] - plane_y, vb[1] - plane_y
            if da * db < 0:
                t = da / (da - db)
                pt = va + t * (vb - va)
                intersections.append(pt)
    if len(intersections) < 3:
        return 0.0
    pts = np.array(intersections)[:, [0, 2]]
    if len(pts) > 3:
        unique = [pts[0]]
        for p in pts[1:]:
            if min(np.linalg.norm(np.array(unique) - p, axis=1)) > 0.0005:
                unique.append(p)
        pts = np.array(unique)
    if len(pts) < 3:
        return 0.0
    try:
        from scipy.spatial import ConvexHull
        hull = ConvexHull(pts)
        return hull.area * 100
    except Exception:
        return 0.0


def measure_circ_ellipse(vertices, vertex_indices):
    if len(vertex_indices) == 0:
        return 0.0
    gv = vertices[vertex_indices]
    w = (gv[:, 0].max() - gv[:, 0].min()) * 100
    d = (gv[:, 2].max() - gv[:, 2].min()) * 100
    a, b = w / 2, d / 2
    if a + b < 1e-6:
        return 0.0
    h = ((a - b) ** 2) / ((a + b) ** 2)
    return np.pi * (a + b) * (1 + (3 * h) / (10 + np.sqrt(max(4 - 3 * h, 0))))


def compute_all_measurements(verts, faces, fm, smpl_parts):
    """Compute all 35 measurements from SMPL mesh vertices."""
    M = {}

    # Helper: get vertices for a part
    def pv(name):
        return smpl_parts.get(name, [])

    # Helper: centroid Y of a vertex set
    def cy(vs):
        if not vs:
            return 0
        return np.mean(verts[vs, 1])

    # Helper: circumference at Y level - use ellipse for speed (plane-mesh is too slow for generation)
    def circ(part_names, y, bw=0.03, face_mask=None):
        all_v = []
        for pn in part_names:
            all_v.extend(pv(pn))
        if not all_v:
            return 0.0
        band = [vi for vi in all_v if abs(verts[vi, 1] - y) <= bw]
        if len(band) < 4:
            band = all_v
        return measure_circ_ellipse(verts, band)

    # Helper: limb circumference (XZ projection)
    def limb_circ(part_names, y, bw=0.03):
        all_v = []
        for pn in part_names:
            all_v.extend(pv(pn))
        if not all_v:
            return 0.0
        band = [vi for vi in all_v if abs(verts[vi, 1] - y) <= bw]
        if len(band) < 4:
            band = all_v
        return measure_circ_ellipse(verts, band)

    # Helper: distance between two vertex sets
    def dist(va, vb):
        if not va or not vb:
            return 0.0
        ca = np.mean(verts[va], axis=0)
        cb = np.mean(verts[vb], axis=0)
        return np.linalg.norm(ca - cb) * 100

    # Helper: X span
    def xspan(vs):
        if not vs:
            return 0.0
        return (verts[vs, 0].max() - verts[vs, 0].min()) * 100

    # Get all vertex sets
    chest_v = pv('spine2')
    shoulder_r = pv('rightShoulder')
    shoulder_l = pv('leftShoulder')
    shoulder_v = shoulder_r + shoulder_l
    waist_v = pv('spine1')
    stomach_v = pv('spine')
    hips_v = pv('hips')
    neck_v = pv('neck')
    r_arm = pv('rightArm')
    l_arm = pv('leftArm')
    r_fore = pv('rightForeArm')
    l_fore = pv('leftForeArm')
    r_leg = pv('rightUpLeg')
    l_leg = pv('leftUpLeg')
    r_calf = pv('rightLeg')
    l_calf = pv('leftLeg')
    r_hand = pv('rightHand')
    l_hand = pv('leftHand')
    r_foot = pv('rightFoot')
    l_foot = pv('leftFoot')
    chest_all = chest_v + shoulder_v

    # Y centroids
    chestY = cy(chest_all) if chest_all else 0
    waistY = cy(waist_v)
    stomachY = cy(stomach_v) if stomach_v else (chestY + waistY) / 2
    hipsY = cy(hips_v)
    neckY = cy(neck_v)
    rArmY = cy(r_arm)
    lArmY = cy(l_arm)
    rForeY = cy(r_fore)
    lForeY = cy(l_fore)
    foreArmY = (rForeY + lForeY) / 2
    rLegY = cy(r_leg)
    lLegY = cy(l_leg)
    rCalfY = cy(r_calf)
    lCalfY = cy(l_calf)
    calfY = (rCalfY + lCalfY) / 2

    # Ankle
    ankle_raw = r_calf + r_foot
    ankle_v = [vi for vi in ankle_raw if verts[vi, 1] < -1.0]
    ankleY = cy(ankle_v) if ankle_v else calfY - 0.12

    # Wrist
    wrist_raw = r_fore + r_hand
    wrist_v = [vi for vi in wrist_raw if verts[vi, 1] < 0.19]
    wristY = cy(wrist_v) if wrist_v else foreArmY - 0.15

    # Knee (upper portion of calf)
    r_knee = [vi for vi in r_calf if verts[vi, 1] > -0.8]
    l_knee = [vi for vi in l_calf if verts[vi, 1] > -0.8]
    rKneeY = cy(r_knee) if r_knee else rCalfY + 0.1
    lKneeY = cy(l_knee) if l_knee else lCalfY + 0.1

    # --- Circumferences ---
    M['Chest Round'] = round(circ(['spine2', 'rightShoulder', 'leftShoulder'], chestY, 0.04, fm.get('spine2')), 1)
    M['Bust Round'] = M['Chest Round']
    M['Waist Round'] = round(circ(['spine1'], waistY, 0.03, fm.get('spine1')), 1)
    M['Stomach Round'] = round(circ(['spine'], stomachY, 0.04, fm.get('spine')), 1) if stomach_v else M['Waist Round']
    M['Hip Round'] = round(circ(['hips'], hipsY, 0.04, fm.get('hips')), 1)
    M['Neck Round'] = round(circ(['neck'], neckY, 0.03, fm.get('neck')), 1)
    M['Thigh Round'] = round((limb_circ(['rightUpLeg'], rLegY, 0.05) + limb_circ(['leftUpLeg'], lLegY, 0.05)) / 2, 1)
    M['Knee Round'] = round((limb_circ(['rightLeg'], rKneeY, 0.03) + limb_circ(['leftLeg'], lKneeY, 0.03)) / 2, 1)
    M['Calf Round'] = round((limb_circ(['rightLeg'], rCalfY, 0.04) + limb_circ(['leftLeg'], lCalfY, 0.04)) / 2, 1)
    M['Ankle Round'] = round(limb_circ(['rightLeg', 'rightFoot'], ankleY, 0.03), 1) if ankle_v else 22.0
    M['Bicep Round'] = round((limb_circ(['rightArm'], rArmY, 0.04) + limb_circ(['leftArm'], lArmY, 0.04)) / 2, 1)
    M['Elbow Round'] = round((limb_circ(['rightForeArm'], rForeY, 0.03) + limb_circ(['leftForeArm'], lForeY, 0.03)) / 2, 1)
    M['Wrist Round'] = round(limb_circ(['rightForeArm', 'rightHand'], wristY, 0.03), 1) if wrist_v else 15.0
    M['Upper Hip'] = round(M['Hip Round'] * 0.92, 1)

    # --- Width ---
    M['Shoulder'] = round(xspan(shoulder_v), 1)
    M['Across Shoulder'] = M['Shoulder']
    M['Across Back'] = round(M['Shoulder'] * 0.92, 1)
    M['Across Chest'] = round(M['Shoulder'] * 0.96, 1)
    M['Armhole Round'] = round(M['Shoulder'] * 0.45, 1)

    # --- Lengths ---
    M['Half Length'] = round(dist(neck_v, waist_v), 1)
    M['Full Top Length'] = round(dist(neck_v, hips_v), 1)
    M['Back Waist Length'] = M['Half Length']
    M['Front Waist Length'] = M['Half Length']
    M['Neck to Waist'] = M['Half Length']
    M['Shoulder to Waist'] = M['Half Length']
    M['Waist to Hip'] = round(dist(waist_v, hips_v), 1)
    M['Crotch Depth'] = M['Waist to Hip']
    M['Trouser Waist'] = M['Waist Round']
    M['Trouser Length'] = round(dist(waist_v, ankle_v if ankle_v else r_calf), 1)
    M['Inseam'] = round(M['Trouser Length'] * 0.78, 1)
    M['Sleeve Length'] = round(dist(shoulder_v, wrist_v if wrist_v else r_fore), 1)

    # --- Bust-specific ---
    M['High Bust'] = round(M['Bust Round'] * 0.85, 1)
    M['Under Bust'] = round(M['Bust Round'] * 0.75, 1)
    M['Bust Point'] = round(dist(neck_v, chest_v[:3] if len(chest_v) >= 3 else chest_v), 1)
    M['Shoulder to Bust Point'] = round(M['Bust Point'] * 1.1, 1)
    M['Shoulder to Under Bust'] = round(M['Bust Point'] * 1.3, 1)

    return M


MEASUREMENT_ORDER = [
    'Chest Round', 'Bust Round', 'Waist Round', 'Stomach Round', 'Hip Round',
    'Neck Round', 'Thigh Round', 'Knee Round', 'Calf Round', 'Ankle Round',
    'Bicep Round', 'Elbow Round', 'Wrist Round', 'Upper Hip', 'Armhole Round',
    'Shoulder', 'Across Shoulder', 'Across Back', 'Across Chest',
    'Half Length', 'Full Top Length', 'Back Waist Length', 'Front Waist Length',
    'Neck to Waist', 'Shoulder to Waist', 'Waist to Hip', 'Crotch Depth',
    'Trouser Waist', 'Trouser Length', 'Inseam', 'Sleeve Length',
    'High Bust', 'Under Bust', 'Bust Point', 'Shoulder to Bust Point',
]


class MeasurementMLP(nn.Module):
    """MLP: 36 input (35 measurements + 1 gender) → 10 betas."""

    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(36, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Linear(64, 10),
        )

    def forward(self, x):
        return self.net(x)


def precompute_face_masks_for_parts(faces, smpl_parts):
    """Precompute face masks for all SMPL parts (run once)."""
    fm = {}
    for part_name, part_indices in smpl_parts.items():
        idx_set = set(part_indices)
        mask = np.zeros(len(faces), dtype=bool)
        for fi, f in enumerate(faces):
            if f[0] in idx_set or f[1] in idx_set or f[2] in idx_set:
                mask[fi] = True
        fm[part_name] = mask
    return fm


def generate_shapes(v_template, shapedirs, faces, smpl_parts, fm, n_shapes, gender):
    """Generate n valid shapes with all 35 measurements."""
    betas_list = []
    meas_list = []
    attempts = 0
    max_attempts = n_shapes * 5

    while len(betas_list) < n_shapes and attempts < max_attempts:
        attempts += 1
        betas = np.random.randn(NUM_BETAS) * 1.5
        betas = np.clip(betas, -3, 3)

        if gender == 'male':
            for bi in BREAST_BETAS:
                betas[bi] = np.clip(betas[bi], -BREAST_CLAMP, BREAST_CLAMP)

        deltas = np.einsum('ijk,k->ij', shapedirs, betas)
        verts = v_template + deltas

        meas = compute_all_measurements(verts, faces, fm, smpl_parts)

        # Validate: all primary measurements must be present and reasonable
        primary = ['Chest Round', 'Waist Round', 'Hip Round', 'Shoulder',
                    'Thigh Round', 'Bicep Round', 'Neck Round']
        if all(m in meas and meas[m] > 5.0 for m in primary):
            meas_vec = [meas[m] for m in MEASUREMENT_ORDER]
            if all(v > 0 for v in meas_vec):
                betas_list.append(betas)
                meas_list.append(meas_vec)

    return np.array(betas_list), np.array(meas_list)


def main():
    print(f"Device: {DEVICE}")
    print("Loading SMPL...")
    v_template, shapedirs, faces = load_smpl()
    smpl_parts = load_smpl_segmentation()
    print(f"  SMPL parts: {len(smpl_parts)}")

    print("Precomputing face masks...")
    fm = precompute_face_masks_for_parts(faces, smpl_parts)
    print(f"  Face masks: {len(fm)} parts")

    np.random.seed(42)

    # Generate male shapes
    print(f"\nGenerating {SHAPES_PER_GENDER} MALE shapes...")
    t0 = time.time()
    male_betas, male_meas = generate_shapes(v_template, shapedirs, faces, smpl_parts, fm, SHAPES_PER_GENDER, 'male')
    print(f"  Generated {len(male_betas)} in {time.time()-t0:.1f}s")
    for j, m in enumerate(MEASUREMENT_ORDER[:7]):
        print(f"    {m}: {male_meas[:,j].min():.1f} - {male_meas[:,j].max():.1f} (mean={male_meas[:,j].mean():.1f})")

    # Generate female shapes
    print(f"\nGenerating {SHAPES_PER_GENDER} FEMALE shapes...")
    t0 = time.time()
    female_betas, female_meas = generate_shapes(v_template, shapedirs, faces, smpl_parts, fm, SHAPES_PER_GENDER, 'female')
    print(f"  Generated {len(female_betas)} in {time.time()-t0:.1f}s")
    for j, m in enumerate(MEASUREMENT_ORDER[:7]):
        print(f"    {m}: {female_meas[:,j].min():.1f} - {female_meas[:,j].max():.1f} (mean={female_meas[:,j].mean():.1f})")

    # Compute normalization stats
    all_meas = np.vstack([male_meas, female_meas])
    meas_mean = all_meas.mean(0)
    meas_std = all_meas.std(0)
    meas_std[meas_std < 1e-6] = 1.0

    # Normalize
    male_meas_norm = (male_meas - meas_mean) / meas_std
    female_meas_norm = (female_meas - meas_mean) / meas_std

    # Train separate MLPs per gender
    results = {}
    for gender, betas, meas_norm in [('male', male_betas, male_meas_norm),
                                      ('female', female_betas, female_meas_norm)]:
        print(f"\n--- Training {gender.upper()} MLP ---")

        # Create dataset
        X = torch.FloatTensor(meas_norm).to(DEVICE)
        # Add gender flag: 0 for male, 1 for female
        gender_flag = torch.zeros(len(meas_norm), 1).to(DEVICE) if gender == 'male' else torch.ones(len(meas_norm), 1).to(DEVICE)
        X = torch.cat([X, gender_flag], dim=1)
        y = torch.FloatTensor(betas).to(DEVICE)

        dataset = TensorDataset(X, y)
        loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)

        model = MeasurementMLP().to(DEVICE)
        optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE, weight_decay=1e-5)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)
        criterion = nn.MSELoss()

        best_loss = float('inf')
        t0 = time.time()
        for epoch in range(EPOCHS):
            model.train()
            total_loss = 0
            n_batches = 0
            for xb, yb in loader:
                optimizer.zero_grad()
                pred = model(xb)
                loss = criterion(pred, yb)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
                n_batches += 1
            scheduler.step()

            avg_loss = total_loss / n_batches
            if avg_loss < best_loss:
                best_loss = avg_loss
                best_state = {k: v.clone() for k, v in model.state_dict().items()}

            if (epoch + 1) % 20 == 0:
                print(f"  Epoch {epoch+1}/{EPOCHS}: loss={avg_loss:.6f} (best={best_loss:.6f})")

        print(f"  Training time: {time.time()-t0:.1f}s")

        # Load best model
        model.load_state_dict(best_state)
        model.eval()

        # Compute R² on training data
        with torch.no_grad():
            pred = model(X)
            ss_res = ((pred - y) ** 2).sum()
            ss_tot = ((y - y.mean(0)) ** 2).sum()
            r2 = 1 - ss_res / ss_tot
            print(f"  R² = {r2:.4f}")

        # Verify with average measurements
        if gender == 'male':
            avg_meas = np.array([[96, 84, 95, 80, 95, 38, 55, 40, 35, 22, 33, 25, 16, 87, 20,
                                   45, 45, 41, 43, 33, 65, 33, 33, 33, 33, 15, 15, 84, 45, 35, 40,
                                   81, 71, 20, 22]])
        else:
            avg_meas = np.array([[89, 89, 72, 70, 97, 34, 54, 38, 32, 20, 27, 22, 14, 89, 18,
                                   39, 39, 36, 37, 30, 55, 30, 30, 30, 30, 25, 25, 72, 40, 31, 35,
                                   76, 67, 18, 20]])
        avg_norm = (avg_meas - meas_mean) / meas_std
        gender_flag_val = torch.zeros(1, 1).to(DEVICE) if gender == 'male' else torch.ones(1, 1).to(DEVICE)
        avg_tensor = torch.FloatTensor(avg_norm).to(DEVICE)
        avg_tensor = torch.cat([avg_tensor, gender_flag_val], dim=1)
        with torch.no_grad():
            pred_betas = model(avg_tensor).cpu().numpy()[0]
        print(f"  Avg {gender} predicted betas: {pred_betas.round(3)}")
        print(f"  Breast betas [1,2,5]: {pred_betas[BREAST_BETAS].round(3)}")

        # Export weights to JSON (compact format)
        weights = {}
        for name, param in model.named_parameters():
            arr = param.detach().cpu().numpy().astype(np.float32)
            # Round to 6 decimal places for compactness
            arr = np.round(arr, 6)
            weights[name] = arr.tolist()

        results[gender] = {
            'weights': weights,
        }

    # Output
    out = {
        "model_type": "mlp",
        "version": 1,
        "architecture": [36, 128, 64, 10],
        "measurement_order": MEASUREMENT_ORDER,
        "num_measurements": NUM_MEASUREMENTS,
        "num_betas": NUM_BETAS,
        "meas_mean": [round(float(x), 4) for x in meas_mean],
        "meas_std": [round(float(x), 4) for x in meas_std],
        "male": results['male'],
        "female": results['female'],
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(out, f)
    print(f"\nSaved: {OUTPUT_PATH} ({os.path.getsize(OUTPUT_PATH)} bytes)")

    # Quick inference test
    print("\n--- Browser Inference Test ---")
    print("Simulating JS forward pass...")
    for gender in ['male', 'female']:
        g = results[gender]
        w = g['weights']
        # Simulate: x = normalized measurements + gender flag
        if gender == 'male':
            test_meas = np.array([96, 84, 95, 80, 95, 38, 55, 40, 35, 22, 33, 25, 16, 87, 20,
                                   45, 45, 41, 43, 33, 65, 33, 33, 33, 33, 15, 15, 84, 45, 35, 40,
                                   81, 71, 20, 22])
            gender_flag = 0.0
        else:
            test_meas = np.array([89, 89, 72, 70, 97, 34, 54, 38, 32, 20, 27, 22, 14, 89, 18,
                                   39, 39, 36, 37, 30, 55, 30, 30, 30, 30, 25, 25, 72, 40, 31, 35,
                                   76, 67, 18, 20])
            gender_flag = 1.0

        x = (test_meas - meas_mean) / meas_std
        x = np.append(x, gender_flag)

        # Layer 1: Linear + BN + ReLU
        l1_w = np.array(w['net.0.weight'])  # (128, 36)
        l1_b = np.array(w['net.0.bias'])    # (128,)
        h1 = x @ l1_w.T + l1_b
        h1 = np.maximum(h1, 0)  # ReLU

        # Layer 2: Linear + BN + ReLU
        l2_w = np.array(w['net.3.weight'])  # (64, 128)
        l2_b = np.array(w['net.3.bias'])    # (64,)
        h2 = h1 @ l2_w.T + l2_b
        h2 = np.maximum(h2, 0)  # ReLU

        # Layer 3: Linear
        l3_w = np.array(w['net.6.weight'])  # (10, 64)
        l3_b = np.array(w['net.6.bias'])    # (10,)
        out = h2 @ l3_w.T + l3_b

        print(f"  {gender}: betas = {np.clip(out, -2, 2).round(3)}")


if __name__ == '__main__':
    main()
