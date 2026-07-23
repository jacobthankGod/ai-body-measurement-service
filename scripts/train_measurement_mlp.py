#!/usr/bin/env python3
"""Train MLP: 35 measurements → 10 SMPL betas.

Matches browser's computeAllMeasurements exactly:
- Convex hull perimeter (not ellipse)
- YZ projection for arms, XZ for everything else
- Same vertex groups (SMPL segmentation)
- Same band filtering logic
- No BatchNorm (avoids training/inference mismatch in JS)
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
EPOCHS = 100
LEARNING_RATE = 1e-3
DEVICE = 'mps' if torch.backends.mps.is_available() else 'cpu'


def load_smpl():
    vt = np.load(os.path.join(PROJECT_ROOT, 'models', 'v_template.npy'))
    sd = np.load(os.path.join(PROJECT_ROOT, 'models', 'shapedirs.npy')).reshape(6890, 3, NUM_BETAS)
    faces = np.load(os.path.join(PROJECT_ROOT, 'api', 'services', 'src', 'tf_smpl', 'smpl_faces.npy'))
    return vt, sd, faces


def load_smpl_segmentation():
    """Load SMPL part segmentation from the JS file."""
    path = os.path.join(PROJECT_ROOT, 'public', 'assets', 'smpl_segmentation.js')
    parts = {}
    with open(path) as f:
        content = f.read()
    import re
    pattern = r'"(\w+)":\s*\[([\d,\s]+)\]'
    for m in re.finditer(pattern, content):
        name = m.group(1)
        indices = [int(x.strip()) for x in m.group(2).split(',') if x.strip()]
        parts[name] = indices
    return parts


def convex_hull_perimeter_2d(points):
    """Convex hull perimeter of 2D points — matches browser's _convexHull2D."""
    if len(points) < 3:
        return 0.0
    pts = np.ascontiguousarray(points, dtype=np.float64)
    try:
        from scipy.spatial import ConvexHull
        hull = ConvexHull(pts)
        hp = pts[hull.vertices]
        perim = 0.0
        for i in range(len(hp)):
            j = (i + 1) % len(hp)
            dx = hp[j][0] - hp[i][0]
            dz = hp[j][1] - hp[i][1]
            perim += np.sqrt(dx * dx + dz * dz)
        return perim * 100
    except Exception:
        return 0.0


def circ_xz(verts, indices, plane_y, band_width=0.03):
    """Circumference via plane-mesh-like intersection on XZ plane — matches browser _computeCircumference."""
    if len(indices) < 3:
        return 0.0
    gv = verts[indices]
    # Band filter by Y
    mask = np.abs(gv[:, 1] - plane_y) <= band_width
    band = gv[mask] if np.sum(mask) >= 4 else gv
    if len(band) < 3:
        return 0.0
    # Project to XZ and compute convex hull perimeter
    pts = band[:, [0, 2]]
    # Remove duplicates
    unique = [pts[0]]
    for p in pts[1:]:
        if min(np.linalg.norm(np.array(unique) - p, axis=1)) > 0.0005:
            unique.append(p)
    if len(unique) < 3:
        return 0.0
    return convex_hull_perimeter_2d(np.array(unique))


def circ_yz(verts, indices, plane_y, band_width=0.03):
    """Circumference on YZ plane — matches browser's _circFromVerts with proj='yz'."""
    if len(indices) < 3:
        return 0.0
    gv = verts[indices]
    mask = np.abs(gv[:, 1] - plane_y) <= band_width
    band = gv[mask] if np.sum(mask) >= 4 else gv
    if len(band) < 3:
        return 0.0
    pts = band[:, [1, 2]]
    unique = [pts[0]]
    for p in pts[1:]:
        if min(np.linalg.norm(np.array(unique) - p, axis=1)) > 0.0005:
            unique.append(p)
    if len(unique) < 3:
        return 0.0
    return convex_hull_perimeter_2d(np.array(unique))


def compute_all_measurements(verts, faces, smpl_parts):
    """Compute all 35 measurements — matches browser computeAllMeasurements exactly."""
    M = {}
    def pv(name):
        return smpl_parts.get(name, [])
    def cy(vs):
        if not vs:
            return 0.0
        return float(np.mean(verts[vs, 1]))
    def dist(va, vb):
        if not va or not vb:
            return 0.0
        ca = np.mean(verts[va], axis=0)
        cb = np.mean(verts[vb], axis=0)
        return float(np.linalg.norm(ca - cb) * 100)
    def xspan(vs):
        if not vs:
            return 0.0
        return float((verts[vs, 0].max() - verts[vs, 0].min()) * 100)

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

    ankle_raw = r_calf + r_foot
    ankle_v = [vi for vi in ankle_raw if verts[vi, 1] < -1.0]
    ankleY = cy(ankle_v) if ankle_v else calfY - 0.12
    wrist_raw = r_fore + r_hand
    wrist_v = [vi for vi in wrist_raw if verts[vi, 1] < 0.19]
    wristY = cy(wrist_v) if wrist_v else foreArmY - 0.15
    r_knee = [vi for vi in r_calf if verts[vi, 1] > -0.8]
    l_knee = [vi for vi in l_calf if verts[vi, 1] > -0.8]
    rKneeY = cy(r_knee) if r_knee else rCalfY + 0.1
    lKneeY = cy(l_knee) if l_knee else lCalfY + 0.1

    # Circumferences (XZ convex hull — matches browser _computeCircumference)
    M['Chest Round'] = round(circ_xz(verts, chest_all, chestY, 0.04), 1)
    M['Bust Round'] = M['Chest Round']
    M['Waist Round'] = round(circ_xz(verts, waist_v, waistY, 0.03), 1)
    M['Stomach Round'] = round(circ_xz(verts, stomach_v, stomachY, 0.04), 1) if stomach_v else M['Waist Round']
    M['Hip Round'] = round(circ_xz(verts, hips_v, hipsY, 0.04), 1)
    M['Neck Round'] = round(circ_xz(verts, neck_v, neckY, 0.03), 1)

    # Limb circumferences — use YZ for arms (along X in T-pose), XZ for legs (along Y)
    M['Thigh Round'] = round((circ_xz(verts, r_leg, rLegY, 0.05) + circ_xz(verts, l_leg, lLegY, 0.05)) / 2, 1)
    M['Knee Round'] = round((circ_xz(verts, r_knee, rKneeY, 0.03) + circ_xz(verts, l_knee, lKneeY, 0.03)) / 2, 1)
    M['Calf Round'] = round((circ_xz(verts, r_calf, rCalfY, 0.04) + circ_xz(verts, l_calf, lCalfY, 0.04)) / 2, 1)
    M['Ankle Round'] = round(circ_xz(verts, ankle_v, ankleY, 0.03), 1) if ankle_v else 22.0
    M['Bicep Round'] = round((circ_yz(verts, r_arm, rArmY, 0.04) + circ_yz(verts, l_arm, lArmY, 0.04)) / 2, 1)
    M['Elbow Round'] = round((circ_yz(verts, r_fore, rForeY, 0.03) + circ_yz(verts, l_fore, lForeY, 0.03)) / 2, 1)
    M['Wrist Round'] = round(circ_yz(verts, wrist_v, wristY, 0.03), 1) if wrist_v else 15.0
    M['Upper Hip'] = round(M['Hip Round'] * 0.92, 1)

    # Widths
    M['Shoulder'] = round(xspan(shoulder_v), 1)
    M['Across Shoulder'] = M['Shoulder']
    M['Across Back'] = round(M['Shoulder'] * 0.92, 1)
    M['Across Chest'] = round(M['Shoulder'] * 0.96, 1)
    M['Armhole Round'] = round(M['Shoulder'] * 0.45, 1)

    # Lengths
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

    # Bust
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
    """MLP without BatchNorm — matches JS forward pass exactly."""

    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(36, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 10),
        )

    def forward(self, x):
        return self.net(x)


def generate_shapes(v_template, shapedirs, faces, smpl_parts, n_shapes, gender):
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

        meas = compute_all_measurements(verts, faces, smpl_parts)

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

    np.random.seed(42)

    # Generate male shapes
    print(f"\nGenerating {SHAPES_PER_GENDER} MALE shapes...")
    t0 = time.time()
    male_betas, male_meas = generate_shapes(v_template, shapedirs, faces, smpl_parts, SHAPES_PER_GENDER, 'male')
    print(f"  Generated {len(male_betas)} in {time.time()-t0:.1f}s")
    for j, m in enumerate(MEASUREMENT_ORDER[:15]):
        print(f"    {m}: {male_meas[:,j].min():.1f} - {male_meas[:,j].max():.1f} (mean={male_meas[:,j].mean():.1f})")

    # Generate female shapes
    print(f"\nGenerating {SHAPES_PER_GENDER} FEMALE shapes...")
    t0 = time.time()
    female_betas, female_meas = generate_shapes(v_template, shapedirs, faces, smpl_parts, SHAPES_PER_GENDER, 'female')
    print(f"  Generated {len(female_betas)} in {time.time()-t0:.1f}s")
    for j, m in enumerate(MEASUREMENT_ORDER[:15]):
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

        X = torch.FloatTensor(meas_norm).to(DEVICE)
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

        model.load_state_dict(best_state)
        model.eval()

        with torch.no_grad():
            pred = model(X)
            ss_res = ((pred - y) ** 2).sum()
            ss_tot = ((y - y.mean(0)) ** 2).sum()
            r2 = 1 - ss_res / ss_tot
            print(f"  R² = {r2:.4f}")

        # Verify with default T-pose (all zeros)
        with torch.no_grad():
            zero_input = torch.zeros(1, 36).to(DEVICE)
            if gender == 'female':
                zero_input[0, 35] = 1.0
            pred_betas = model(zero_input).cpu().numpy()[0]
        print(f"  Default betas (zero input): {pred_betas.round(3)}")

        # Export weights
        weights = {}
        for name, param in model.named_parameters():
            arr = param.detach().cpu().numpy().astype(np.float32)
            arr = np.round(arr, 6)
            weights[name] = arr.tolist()

        results[gender] = {'weights': weights}

    # Output
    out = {
        "model_type": "mlp",
        "version": 2,
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
    for gender in ['male', 'female']:
        g = results[gender]
        w = g['weights']
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

        l0_w = np.array(w['net.0.weight'])
        l0_b = np.array(w['net.0.bias'])
        h0 = np.maximum(0, x @ l0_w.T + l0_b)
        l3_w = np.array(w['net.3.weight'])
        l3_b = np.array(w['net.3.bias'])
        h3 = np.maximum(0, h0 @ l3_w.T + l3_b)
        l6_w = np.array(w['net.6.weight'])
        l6_b = np.array(w['net.6.bias'])
        out = h3 @ l6_w.T + l6_b

        print(f"  {gender}: betas = {np.clip(out, -2, 2).round(3)}")


if __name__ == '__main__':
    main()
