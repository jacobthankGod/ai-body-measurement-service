#!/usr/bin/env python3
"""Generate measurement-to-beta regression weights — v7: Gender-split Ridge.

Key design decisions:
- Ridge regression (linear = predictable, no measurement coupling)
- Height EXCLUDED from regression — handled by direct Y-scaling in JS
- Plane-mesh intersection for proper measurements
- 5K shapes per gender (10K total)
- Male: breast-deforming betas [1,2,5] constrained to |b| < 0.3
- Female: all betas vary freely
- Separate normalization stats per gender
"""

import json, os, sys
import numpy as np
from scipy.spatial import ConvexHull
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(PROJECT_ROOT, 'public', 'assets', 'smpl_regression_weights.json')
NUM_BETAS = 10
SHAPES_PER_GENDER = 5000
BREAST_BETAS = [1, 2, 5]  # SMPL shape components that control breast deformation
BREAST_CLAMP = 0.3  # Male breast beta magnitude limit

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
            if not line: continue
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

def measure_circ_mesh(vertices, faces, face_mask, plane_y):
    relevant_faces = faces[face_mask]
    if len(relevant_faces) == 0: return 0.0
    intersections = []
    for f in relevant_faces:
        v0, v1, v2 = vertices[f[0]], vertices[f[1]], vertices[f[2]]
        for va, vb in [(v0, v1), (v1, v2), (v2, v0)]:
            da, db = va[1] - plane_y, vb[1] - plane_y
            if da * db < 0:
                t = da / (da - db)
                pt = va + t * (vb - va)
                intersections.append(pt)
    if len(intersections) < 3: return 0.0
    pts = np.array(intersections)[:, [0, 2]]
    if len(pts) > 3:
        unique = [pts[0]]
        for p in pts[1:]:
            if min(np.linalg.norm(np.array(unique) - p, axis=1)) > 0.0005:
                unique.append(p)
        pts = np.array(unique)
    if len(pts) < 3: return 0.0
    try:
        hull = ConvexHull(pts)
        return hull.area * 100
    except Exception:
        return 0.0

def measure_circ_ellipse(vertices, vertex_indices):
    if len(vertex_indices) == 0: return 0.0
    gv = vertices[vertex_indices]
    w = (gv[:, 0].max() - gv[:, 0].min()) * 100
    d = (gv[:, 2].max() - gv[:, 2].min()) * 100
    a, b = w / 2, d / 2
    if a + b < 1e-6: return 0.0
    h = ((a - b) ** 2) / ((a + b) ** 2)
    return np.pi * (a + b) * (1 + (3 * h) / (10 + np.sqrt(max(4 - 3 * h, 0))))

def compute_measurements(verts, faces, vg, fm):
    meas = {}
    circ_map = {
        'chest': 'chest', 'waist': 'waist', 'hip': 'hips',
        'thigh': 'thigh', 'neck': 'neck', 'bicep': 'bicep',
    }
    for label, gname in circ_map.items():
        if gname in vg and len(vg[gname]) > 0:
            plane_y = np.mean(verts[vg[gname], 1])
            circ = measure_circ_mesh(verts, faces, fm.get(gname, np.ones(len(faces), bool)), plane_y)
            if circ < 1.0:
                circ = measure_circ_ellipse(verts, vg[gname])
            meas[label] = circ

    if 'shoulder width' in vg and len(vg['shoulder width']) > 0:
        sv = verts[vg['shoulder width']]
        meas['shoulder'] = (sv[:, 0].max() - sv[:, 0].min()) * 100

    return meas

def generate_shapes(v_template, shapedirs, faces, vg, fm, n_shapes, gender):
    """Generate n valid shapes for a given gender.
    Male: breast betas [1,2,5] clamped to |b| < BREAST_CLAMP
    Female: all betas free
    """
    betas_list = []
    meas_list = []
    attempts = 0
    max_attempts = n_shapes * 5

    while len(betas_list) < n_shapes and attempts < max_attempts:
        attempts += 1
        betas = np.random.randn(NUM_BETAS) * 1.2
        betas = np.clip(betas, -3, 3)

        if gender == 'male':
            for bi in BREAST_BETAS:
                betas[bi] = np.clip(betas[bi], -BREAST_CLAMP, BREAST_CLAMP)

        deltas = np.einsum('ijk,k->ij', shapedirs, betas)
        verts = v_template + deltas
        meas = compute_measurements(verts, faces, vg, fm)

        m_labels = ['chest', 'waist', 'hip', 'shoulder', 'thigh', 'bicep', 'neck']
        if all(m in meas and meas[m] > 1.0 for m in m_labels):
            betas_list.append(betas)
            meas_list.append([meas[m] for m in m_labels])

    return np.array(betas_list), np.array(meas_list)

def main():
    print("Loading SMPL...")
    v_template, shapedirs, faces = load_smpl()
    vg = load_vertex_groups()
    fm = precompute_face_masks(faces, vg)
    m_labels = ['chest', 'waist', 'hip', 'shoulder', 'thigh', 'bicep', 'neck']

    np.random.seed(42)

    # Generate male shapes (breast betas clamped)
    print(f"\nGenerating {SHAPES_PER_GENDER} MALE shapes (breast betas clamped to |b|<{BREAST_CLAMP})...")
    male_betas, male_meas = generate_shapes(v_template, shapedirs, faces, vg, fm, SHAPES_PER_GENDER, 'male')
    print(f"  Male valid: {len(male_betas)}")
    for j, l in enumerate(m_labels):
        print(f"    {l}: {male_meas[:,j].min():.1f} - {male_meas[:,j].max():.1f} (mean={male_meas[:,j].mean():.1f})")
    print(f"    Breast betas [1,2,5] max abs: {[np.abs(male_betas[:,bi]).max().round(3) for bi in BREAST_BETAS]}")

    # Generate female shapes (all betas free)
    print(f"\nGenerating {SHAPES_PER_GENDER} FEMALE shapes (all betas free)...")
    female_betas, female_meas = generate_shapes(v_template, shapedirs, faces, vg, fm, SHAPES_PER_GENDER, 'female')
    print(f"  Female valid: {len(female_betas)}")
    for j, l in enumerate(m_labels):
        print(f"    {l}: {female_meas[:,j].min():.1f} - {female_meas[:,j].max():.1f} (mean={female_meas[:,j].mean():.1f})")
    print(f"    Breast betas [1,2,5] max abs: {[np.abs(female_betas[:,bi]).max().round(3) for bi in BREAST_BETAS]}")

    # Train separate regressions
    results = {}
    for gender, betas, meas in [('male', male_betas, male_meas), ('female', female_betas, female_meas)]:
        print(f"\n--- Training {gender.upper()} Ridge regression ---")

        mean = meas.mean(0)
        std = meas.std(0)
        std[std < 1e-6] = 1.0
        norm = (meas - mean) / std

        ridge = Ridge(alpha=1.0)
        ridge.fit(norm, betas)
        train_r2 = ridge.score(norm, betas)
        print(f"  Train R² = {train_r2:.4f}")

        # Cross-check: predict betas for average measurements
        if gender == 'male':
            avg = np.array([[96, 84, 95, 45, 55, 33, 38]])
        else:
            avg = np.array([[89, 72, 97, 39, 54, 27, 34]])
        avg_norm = (avg - mean) / std
        pred = ridge.predict(avg_norm)
        print(f"  Predicted betas for avg {gender}: {pred[0].round(3)}")
        print(f"  Breast betas [1,2,5]: {pred[0][BREAST_BETAS].round(3)}")
        print(f"  Abs max: {np.abs(pred[0]).max():.3f}")

        results[gender] = {
            'weights': ridge.coef_.tolist(),
            'bias': ridge.intercept_.tolist(),
            'measurements_mean': mean.tolist(),
            'measurements_std': std.tolist(),
            'train_r2': float(train_r2),
        }

    # Verify male breast betas are suppressed
    print("\n--- Verification ---")
    male_avg_norm = (np.array([[96, 84, 95, 45, 55, 33, 38]]) - results['male']['measurements_mean']) / results['male']['measurements_std']
    male_pred = np.array(results['male']['weights']) @ male_avg_norm[0] + np.array(results['male']['bias'])
    print(f"Male avg breast betas [1,2,5]: {male_pred[BREAST_BETAS].round(3)} (should be near 0)")

    female_avg_norm = (np.array([[89, 72, 97, 39, 54, 27, 34]]) - results['female']['measurements_mean']) / results['female']['measurements_std']
    female_pred = np.array(results['female']['weights']) @ female_avg_norm[0] + np.array(results['female']['bias'])
    print(f"Female avg breast betas [1,2,5]: {female_pred[BREAST_BETAS].round(3)} (should be nonzero)")

    # Output
    slider_ranges = {
        'chest': [60, 140, 1], 'waist': [55, 140, 1], 'hip': [60, 140, 1],
        'shoulder': [30, 60, 1], 'thigh': [35, 80, 1], 'bicep': [18, 50, 1],
        'neck': [28, 50, 1],
    }

    out = {
        "model_type": "ridge",
        "version": 7,
        "gender_split": True,
        "breast_betas": BREAST_BETAS,
        "breast_clamp_male": BREAST_CLAMP,
        "measurement_order": m_labels,
        "slider_ranges": slider_ranges,
        "num_betas": NUM_BETAS,
        "male": {
            **results['male'],
            "defaults": [96, 84, 95, 45, 55, 33, 38],
        },
        "female": {
            **results['female'],
            "defaults": [89, 72, 97, 39, 54, 27, 34],
        },
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(out, f, indent=2)
    print(f"\nSaved: {OUTPUT_PATH} ({os.path.getsize(OUTPUT_PATH)} bytes)")

if __name__ == '__main__':
    main()
