#!/usr/bin/env python3
"""Train MLP: 12 independent measurements → 10 SMPL betas.

Version 3 — reduced from 35 to 12 truly independent measurements to eliminate
correlated/redundant inputs that caused inverted sliders and compensating weights.

The 12 independent measurements:
  Chest Round, Waist Round, Hip Round, Thigh Round, Bicep Round, Neck Round,
  Shoulder, Half Length, Waist to Hip, Trouser Length, Sleeve Length, Bust Point

Architecture: 13 → 128 → ReLU → 64 → ReLU → 10 (13 = 12 meas + 1 gender flag)
No BatchNorm (matches JS forward pass exactly).

Includes monotonicity validation: for each measurement, verify that increasing
it actually increases the corresponding mesh dimension.
"""

import json, os, sys, time
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(PROJECT_ROOT, 'public', 'assets', 'smpl_mlp_weights.json')
NUM_BETAS = 10
SHAPES_PER_GENDER = 5000
BREAST_BETAS = [1, 2, 5]
BREAST_CLAMP = 0.3
BATCH_SIZE = 256
EPOCHS = 100
LEARNING_RATE = 1e-3
DEVICE = 'mps' if torch.backends.mps.is_available() else 'cpu'

# 12 truly independent measurements — no aliases, no copies
INDEPENDENT_MEASUREMENTS = [
    'Chest Round',     # Torso circumference
    'Waist Round',     # Core circumference
    'Hip Round',       # Lower circumference
    'Thigh Round',     # Leg circumference
    'Bicep Round',     # Arm circumference
    'Neck Round',      # Neck circumference
    'Shoulder',        # Width
    'Half Length',     # Neck-to-waist distance
    'Waist to Hip',    # Lower torso length
    'Trouser Length',  # Full leg length
    'Sleeve Length',   # Arm length
    'Bust Point',      # Bust position (female)
]
NUM_MEASUREMENTS = len(INDEPENDENT_MEASUREMENTS)  # 12
INPUT_DIM = NUM_MEASUREMENTS + 1  # 13 (12 + 1 gender flag)


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
    """Circumference via plane-mesh-like intersection on XZ plane."""
    if len(indices) < 3:
        return 0.0
    gv = verts[indices]
    mask = np.abs(gv[:, 1] - plane_y) <= band_width
    band = gv[mask] if np.sum(mask) >= 4 else gv
    if len(band) < 3:
        return 0.0
    pts = band[:, [0, 2]]
    unique = [pts[0]]
    for p in pts[1:]:
        if min(np.linalg.norm(np.array(unique) - p, axis=1)) > 0.0005:
            unique.append(p)
    if len(unique) < 3:
        return 0.0
    return convex_hull_perimeter_2d(np.array(unique))


def circ_yz(verts, indices, plane_y, band_width=0.03):
    """Circumference on YZ plane."""
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
    """Compute all measurements — returns both independent and full set."""
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

    ankle_raw = r_calf + r_foot
    ankle_v = [vi for vi in ankle_raw if verts[vi, 1] < -1.0]
    ankleY = cy(ankle_v) if ankle_v else cy(r_calf) - 0.12
    wrist_raw = r_fore + r_hand
    wrist_v = [vi for vi in wrist_raw if verts[vi, 1] < 0.19]
    wristY = cy(wrist_v) if wrist_v else foreArmY - 0.15
    r_knee = [vi for vi in r_calf if verts[vi, 1] > -0.8]
    l_knee = [vi for vi in l_calf if verts[vi, 1] > -0.8]
    rKneeY = cy(r_knee) if r_knee else rCalfY + 0.1
    lKneeY = cy(l_knee) if l_knee else lCalfY + 0.1

    # Circumferences
    M['Chest Round'] = round(circ_xz(verts, chest_all, chestY, 0.04), 1)
    M['Waist Round'] = round(circ_xz(verts, waist_v, waistY, 0.03), 1)
    M['Hip Round'] = round(circ_xz(verts, hips_v, hipsY, 0.04), 1)
    M['Neck Round'] = round(circ_xz(verts, neck_v, neckY, 0.03), 1)
    M['Thigh Round'] = round((circ_xz(verts, r_leg, rLegY, 0.05) + circ_xz(verts, l_leg, lLegY, 0.05)) / 2, 1)
    M['Bicep Round'] = round((circ_yz(verts, r_arm, rArmY, 0.04) + circ_yz(verts, l_arm, lArmY, 0.04)) / 2, 1)

    # Widths
    M['Shoulder'] = round(xspan(shoulder_v), 1)

    # Lengths
    M['Half Length'] = round(dist(neck_v, waist_v), 1)
    M['Waist to Hip'] = round(dist(waist_v, hips_v), 1)
    M['Trouser Length'] = round(dist(waist_v, ankle_v if ankle_v else r_calf), 1)
    M['Sleeve Length'] = round(dist(shoulder_v, wrist_v if wrist_v else r_fore), 1)

    # Bust
    M['Bust Point'] = round(dist(neck_v, chest_v[:3] if len(chest_v) >= 3 else chest_v), 1)

    return M


def generate_shapes(v_template, shapedirs, faces, smpl_parts, n_shapes, gender):
    """Generate n valid shapes with independent measurements."""
    betas_list = []
    meas_list = []
    attempts = 0
    max_attempts = n_shapes * 5

    while len(betas_list) < n_shapes and attempts < max_attempts:
        attempts += 1
        r = np.random.random()
        if r < 0.60:
            betas = np.random.randn(NUM_BETAS) * 1.2
            betas = np.clip(betas, -2.5, 2.5)
        elif r < 0.85:
            betas = np.random.randn(NUM_BETAS) * 2.0
            betas = np.clip(betas, -3.5, 3.5)
        else:
            betas = np.random.uniform(-4, 4, NUM_BETAS)

        if gender == 'male':
            for bi in BREAST_BETAS:
                betas[bi] = np.clip(betas[bi], -BREAST_CLAMP, BREAST_CLAMP)

        deltas = np.einsum('ijk,k->ij', shapedirs, betas)
        verts = v_template + deltas

        meas = compute_all_measurements(verts, faces, smpl_parts)

        if all(m in meas and meas[m] > 5.0 for m in INDEPENDENT_MEASUREMENTS):
            meas_vec = [meas[m] for m in INDEPENDENT_MEASUREMENTS]
            if all(v > 0 for v in meas_vec):
                betas_list.append(betas)
                meas_list.append(meas_vec)

    return np.array(betas_list), np.array(meas_list)


class MeasurementMLP(nn.Module):
    """MLP without BatchNorm — matches JS forward pass exactly.
    Input: 13 (12 independent measurements + 1 gender flag)
    Output: 10 SMPL betas
    """

    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(INPUT_DIM, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, NUM_BETAS),
        )

    def forward(self, x):
        return self.net(x)


def validate_monotonicity(model, v_template, shapedirs, smpl_parts, meas_mean, meas_std, gender_flag_val):
    """Quick monotonicity check: for each measurement, verify that increasing it
    changes betas in a consistent direction (not noise).
    Uses mean-body delta rather than full mesh computation for speed.
    """
    model.eval()
    results = {}

    # Mean body betas
    mean_input = torch.zeros(1, INPUT_DIM).to(DEVICE)
    mean_input[0, NUM_MEASUREMENTS] = gender_flag_val

    with torch.no_grad():
        betas_mean = model(mean_input).cpu().numpy()[0]

    PERTURB_CM = 5.0  # 5cm perturbation

    for i, meas_name in enumerate(INDEPENDENT_MEASUREMENTS):
        perturbed_input = mean_input.clone()
        perturbed_input[0, i] = PERTURB_CM / meas_std[i]

        with torch.no_grad():
            betas_plus = model(perturbed_input).cpu().numpy()[0]

        delta_betas = betas_plus - betas_mean

        # The delta should be non-trivial (not just noise)
        beta_norm = np.linalg.norm(delta_betas)
        ok = beta_norm > 0.001  # betas actually changed

        # Compute approximate mesh measurement change
        mesh_mean = v_template + np.einsum('ijk,k->ij', shapedirs, betas_mean)
        mesh_plus = v_template + np.einsum('ijk,k->ij', shapedirs, betas_plus)
        meas_mean_dict = compute_all_measurements(mesh_mean, None, smpl_parts)
        meas_plus_dict = compute_all_measurements(mesh_plus, None, smpl_parts)
        base_val = meas_mean_dict.get(meas_name, 0)
        plus_val = meas_plus_dict.get(meas_name, 0)
        delta = plus_val - base_val
        ok = delta > 0

        results[meas_name] = (ok, delta, base_val, plus_val)

    return results


def main():
    print(f"Device: {DEVICE}")
    print(f"Input dimension: {INPUT_DIM} ({NUM_MEASUREMENTS} measurements + 1 gender)")
    print(f"Independent measurements: {INDEPENDENT_MEASUREMENTS}")
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
    for j, m in enumerate(INDEPENDENT_MEASUREMENTS):
        print(f"    {m}: {male_meas[:,j].min():.1f} - {male_meas[:,j].max():.1f} (mean={male_meas[:,j].mean():.1f})")

    # Generate female shapes
    print(f"\nGenerating {SHAPES_PER_GENDER} FEMALE shapes...")
    t0 = time.time()
    female_betas, female_meas = generate_shapes(v_template, shapedirs, faces, smpl_parts, SHAPES_PER_GENDER, 'female')
    print(f"  Generated {len(female_betas)} in {time.time()-t0:.1f}s")
    for j, m in enumerate(INDEPENDENT_MEASUREMENTS):
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
        gender_flag = 0.0 if gender == 'male' else 1.0
        gender_col = torch.full((len(meas_norm), 1), gender_flag).to(DEVICE)
        X = torch.cat([X, gender_col], dim=1)
        y = torch.FloatTensor(betas).to(DEVICE)

        print(f"  Input shape: {X.shape} (expected [{len(meas_norm)}, {INPUT_DIM}])")

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

            if (epoch + 1) % 50 == 0:
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

        # Verify with default T-pose (all zeros = mean body)
        with torch.no_grad():
            zero_input = torch.zeros(1, INPUT_DIM).to(DEVICE)
            zero_input[0, NUM_MEASUREMENTS] = gender_flag
            pred_betas = model(zero_input).cpu().numpy()[0]
        print(f"  Default betas (mean body): {pred_betas.round(3)}")

        # Monotonicity validation
        print(f"\n  Monotonicity validation ({gender}):")
        mono = validate_monotonicity(model, v_template, shapedirs, smpl_parts,
                                     meas_mean, meas_std, gender_flag)
        all_ok = True
        for meas_name, (ok, delta, base_val, plus_val) in mono.items():
            status = "OK" if ok else "INVERTED"
            if not ok:
                all_ok = False
            print(f"    {meas_name}: {base_val:.1f} → {plus_val:.1f} (Δ={delta:+.1f}cm) [{status}]")
        if all_ok:
            print("  All measurements monotonically correct!")
        else:
            print("  WARNING: Some measurements are inverted!")

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
        "version": 3,
        "architecture": [INPUT_DIM, 128, 64, NUM_BETAS],
        "measurement_order": INDEPENDENT_MEASUREMENTS,
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
            # Average male: chest=96, waist=84, hip=96, thigh=55, bicep=32, neck=39,
            # shoulder=43, half_length=28, waist_to_hip=28, trouser_length=116, sleeve_length=62, bust_point=7
            test_meas = np.array([96, 84, 96, 55, 32, 39, 43, 28, 28, 116, 62, 7])
            gender_flag = 0.0
        else:
            test_meas = np.array([88, 72, 94, 55, 29, 35, 38, 26, 26, 112, 60, 23])
            gender_flag = 1.0

        x = (test_meas - meas_mean) / meas_std
        x = np.append(x, gender_flag)

        l0_w = np.array(w['net.0.weight'])
        l0_b = np.array(w['net.0.bias'])
        h0 = np.maximum(0, x @ l0_w.T + l0_b)
        l2_w = np.array(w['net.2.weight'])
        l2_b = np.array(w['net.2.bias'])
        h2 = np.maximum(0, h0 @ l2_w.T + l2_b)
        l4_w = np.array(w['net.4.weight'])
        l4_b = np.array(w['net.4.bias'])
        out = h2 @ l4_w.T + l4_b

        betas_clipped = np.clip(out, -1.5, 1.5)
        print(f"  {gender}: betas = {betas_clipped.round(3)}")

        # Compute mesh and check height
        mesh = v_template + np.einsum('ijk,k->ij', shapedirs, betas_clipped)
        ymin, ymax = mesh[:, 1].min(), mesh[:, 1].max()
        height_cm = (ymax - ymin) * 100
        print(f"    Mesh height: {height_cm:.1f}cm (T-pose, no height scaling)")


if __name__ == '__main__':
    main()
