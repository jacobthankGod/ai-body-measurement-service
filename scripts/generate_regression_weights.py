#!/usr/bin/env python3
"""Generate measurement-to-beta regression weights — v5: plane-mesh intersection + MLP.

Uses proper plane-mesh intersection for circumferences.
5K shapes for reasonable training time.
"""

import json, os, sys
import numpy as np
from scipy.spatial import ConvexHull
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(PROJECT_ROOT, 'public', 'assets', 'smpl_regression_weights.json')
NUM_BETAS = 10
TOTAL_SHAPES = 5000

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
    """Measure circumference using plane-mesh intersection. Returns cm."""
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
    v_height = (verts[:, 1].max() - verts[:, 1].min()) * 100
    meas['height'] = v_height

    # Circumferences: plane-mesh intersection with vertex-group landmarks
    circ_map = {
        'chest': 'chest', 'waist': 'waist', 'hip': 'hips',
        'thigh': 'thigh', 'neck': 'neck',
    }
    for label, gname in circ_map.items():
        if gname in vg and len(vg[gname]) > 0:
            plane_y = np.mean(verts[vg[gname], 1])
            circ = measure_circ_mesh(verts, faces, fm.get(gname, np.ones(len(faces), bool)), plane_y)
            if circ < 1.0:
                circ = measure_circ_ellipse(verts, vg[gname])
            meas[label] = circ

    # Shoulder from vertex group
    if 'shoulder width' in vg and len(vg['shoulder width']) > 0:
        sv = verts[vg['shoulder width']]
        meas['shoulder'] = (sv[:, 0].max() - sv[:, 0].min()) * 100

    # Bicep: plane-mesh intersection at bicep vertex Y level
    if 'bicep' in vg and len(vg['bicep']) > 0:
        plane_y = np.mean(verts[vg['bicep'], 1])
        circ = measure_circ_mesh(verts, faces, fm.get('bicep', np.ones(len(faces), bool)), plane_y)
        if circ < 1.0:
            circ = measure_circ_ellipse(verts, vg['bicep'])
        meas['bicep'] = circ

    return meas

def main():
    print("Loading SMPL...")
    v_template, shapedirs, faces = load_smpl()
    vg = load_vertex_groups()
    fm = precompute_face_masks(faces, vg)

    np.random.seed(42)
    m_labels = ['chest', 'waist', 'hip', 'shoulder', 'thigh', 'bicep', 'height', 'neck']

    all_betas = []
    all_meas = []

    print(f"Generating {TOTAL_SHAPES} shapes with plane-mesh intersection...")
    for i in range(TOTAL_SHAPES):
        if i % 500 == 0:
            print(f"  {i}/{TOTAL_SHAPES} (valid: {len(all_betas)})...")

        betas = np.random.randn(NUM_BETAS) * 1.2
        betas = np.clip(betas, -3, 3)

        deltas = np.einsum('ijk,k->ij', shapedirs, betas)
        verts = v_template + deltas

        meas = compute_measurements(verts, faces, vg, fm)

        if all(m in meas and meas[m] > 1.0 for m in m_labels):
            all_betas.append(betas)
            all_meas.append([meas[m] for m in m_labels])

    all_betas = np.array(all_betas)
    all_meas = np.array(all_meas)
    print(f"\nTotal valid: {len(all_betas)}")

    for j, l in enumerate(m_labels):
        print(f"  {l}: {all_meas[:,j].min():.1f} - {all_meas[:,j].max():.1f} (mean={all_meas[:,j].mean():.1f})")

    scaler = StandardScaler()
    norm = scaler.fit_transform(all_meas)

    print("\nTraining MLP...")
    mlp = MLPRegressor(
        hidden_layer_sizes=(128, 64),
        activation='relu',
        max_iter=500,
        early_stopping=True,
        validation_fraction=0.1,
        random_state=42,
    )
    mlp.fit(norm, all_betas)
    train_r2 = mlp.score(norm, all_betas)
    print(f"Train R² = {train_r2:.4f}")

    cv = cross_val_score(mlp, norm, all_betas, cv=3, scoring='r2')
    print(f"3-fold CV R² = {cv.mean():.4f} ± {cv.std():.4f}")

    avg = scaler.transform([[96, 84, 95, 45, 55, 33, 175, 38]])
    pred = mlp.predict(avg)
    print(f"Predicted betas for avg male: {pred[0].round(3)}")

    male_defaults = [96, 84, 95, 45, 55, 33, 175, 38]
    female_defaults = [89, 72, 97, 39, 54, 27, 163, 34]

    slider_ranges = {
        'chest': [60, 140, 1], 'waist': [55, 140, 1], 'hip': [60, 140, 1],
        'shoulder': [30, 60, 1], 'thigh': [35, 80, 1], 'bicep': [18, 50, 1],
        'height': [140, 210, 1], 'neck': [28, 50, 1],
    }

    out = {
        "model_type": "mlp",
        "measurement_order": m_labels,
        "slider_ranges": slider_ranges,
        "num_betas": NUM_BETAS,
        "train_r2": float(train_r2),
        "cv_r2": float(cv.mean()),
        "male": {
            "weights": [c.T.tolist() for c in mlp.coefs_],
            "bias": [b.tolist() for b in mlp.intercepts_],
            "measurements_mean": scaler.mean_.tolist(),
            "measurements_std": scaler.scale_.tolist(),
            "defaults": male_defaults,
        },
        "female": {
            "weights": [c.T.tolist() for c in mlp.coefs_],
            "bias": [b.tolist() for b in mlp.intercepts_],
            "measurements_mean": scaler.mean_.tolist(),
            "measurements_std": scaler.scale_.tolist(),
            "defaults": female_defaults,
        },
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(out, f, indent=2)
    print(f"\nSaved: {OUTPUT_PATH} ({os.path.getsize(OUTPUT_PATH)} bytes)")

if __name__ == '__main__':
    main()
