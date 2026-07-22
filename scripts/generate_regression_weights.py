#!/usr/bin/env python3
"""Generate measurement-to-beta regression weights — optimized version.

Uses pre-filtered face masks and vectorized operations for speed.
Falls back to vertex-range ellipse when mesh intersection fails.
"""

import json, os, sys
import numpy as np
from scipy.spatial import ConvexHull
from sklearn.linear_model import Ridge

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(PROJECT_ROOT, 'public', 'assets', 'smpl_regression_weights.json')
NUM_BETAS = 10
TOTAL_SHAPES = 10000

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
    """Pre-compute which faces belong to each body part."""
    masks = {}
    for part, indices in vertex_groups.items():
        idx_set = set(indices)
        mask = np.zeros(len(faces), dtype=bool)
        for fi, f in enumerate(faces):
            if f[0] in idx_set or f[1] in idx_set or f[2] in idx_set:
                mask[fi] = True
        masks[part] = mask
    return masks

def measure_circ_ellipse(vertices, vertex_indices):
    """Fast bounding-box ellipse circumference using Ramanujan approximation.
    All units in meters, returns cm."""
    if len(vertex_indices) == 0:
        return 0.0
    gv = vertices[vertex_indices]
    w = gv[:, 0].max() - gv[:, 0].min()
    d = gv[:, 2].max() - gv[:, 2].min()
    a, b = w / 2, d / 2
    if a + b < 1e-6:
        return 0.0
    h = ((a - b) ** 2) / ((a + b) ** 2)
    circ = np.pi * (a + b) * (1 + (3 * h) / (10 + np.sqrt(max(4 - 3 * h, 0))))
    return circ * 100  # meters → cm

def measure_circ_mesh(vertices, faces, face_mask, plane_y):
    """Measure circumference using plane-mesh intersection. Returns cm."""
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

    pts = np.array(intersections)[:, [0, 2]]  # Project to xz
    # Deduplicate
    if len(pts) > 3:
        unique = [pts[0]]
        for p in pts[1:]:
            if min(np.linalg.norm(np.array(unique) - p, axis=1)) > 0.0005:
                unique.append(p)
        pts = np.array(unique)

    if len(pts) < 3:
        return 0.0
    try:
        hull = ConvexHull(pts)
        return hull.area * 100  # perimeter × 100 → cm
    except Exception:
        return 0.0

def compute_all_measurements(vertices, faces, vertex_groups, face_masks):
    """Compute all measurements for one body shape. Returns dict in cm."""
    meas = {}
    v_height = (vertices[:, 1].max() - vertices[:, 1].min()) * 100
    meas['height'] = v_height

    # Circumference measurements: use mesh intersection with fallback to ellipse
    # Note: vertex group names from customBodyPoints.txt have spaces
    circ_parts = {
        'chest': 'chest',
        'waist': 'waist',
        'hip': 'hips',   # vertex group is 'hips' (plural) but measurement label is 'hip'
        'thigh': 'thigh',
        'bicep': 'bicep',
        'neck': 'neck',
    }
    for label, group_name in circ_parts.items():
        if group_name in vertex_groups and len(vertex_groups[group_name]) > 0:
            indices = vertex_groups[group_name]
            plane_y = np.mean(vertices[indices, 1])
            circ = measure_circ_mesh(vertices, faces, face_masks.get(group_name, np.ones(len(faces), bool)), plane_y)
            if circ < 1.0:
                circ = measure_circ_ellipse(vertices, indices)
            meas[label] = circ

    # Shoulder width: use vertex group directly
    sh_key = 'shoulder width'
    if sh_key in vertex_groups and len(vertex_groups[sh_key]) > 0:
        sh_verts = vertices[vertex_groups[sh_key]]
        meas['shoulder'] = (sh_verts[:, 0].max() - sh_verts[:, 0].min()) * 100

    return meas

def main():
    print("Loading SMPL...")
    v_template, shapedirs, faces = load_smpl()
    vertex_groups = load_vertex_groups()
    face_masks = precompute_face_masks(faces, vertex_groups)

    print(f"Loaded: {len(v_template)} vertices, {len(faces)} faces")
    print(f"Vertex groups: {list(vertex_groups.keys())}")

    # Measurement labels for regression (must match HTML data-measurement attributes)
    m_labels = ['chest', 'waist', 'hip', 'shoulder', 'thigh', 'bicep', 'height']

    np.random.seed(42)
    all_betas = []
    all_meas = []

    print(f"\nGenerating {TOTAL_SHAPES} shapes...")
    for i in range(TOTAL_SHAPES):
        if i % 1000 == 0:
            print(f"  {i}/{TOTAL_SHAPES} (valid: {len(all_betas)})...")

        betas = np.random.randn(NUM_BETAS) * 1.2
        betas = np.clip(betas, -3, 3)

        deltas = np.einsum('ijk,k->ij', shapedirs, betas)
        verts = v_template + deltas

        meas = compute_all_measurements(verts, faces, vertex_groups, face_masks)

        if all(m in meas and meas[m] > 1.0 for m in m_labels):
            all_betas.append(betas)
            all_meas.append([meas[m] for m in m_labels])

    all_betas = np.array(all_betas)
    all_meas = np.array(all_meas)
    print(f"\nTotal valid: {len(all_betas)}")

    for j, l in enumerate(m_labels):
        print(f"  {l}: {all_meas[:, j].min():.1f} - {all_meas[:, j].max():.1f} cm")

    # Normalize
    mean = all_meas.mean(0)
    std = all_meas.std(0)
    std[std < 1e-6] = 1.0
    norm = (all_meas - mean) / std

    # Train Ridge
    print("\nTraining Ridge regression...")
    ridge = Ridge(alpha=1.0)
    ridge.fit(norm, all_betas)
    r2 = ridge.score(norm, all_betas)
    print(f"R² = {r2:.4f}")

    # Test: average measurements → betas should be near 0
    avg_meas = np.array([[85, 75, 95, 42, 52, 30, 170]])  # average human
    avg_norm = (avg_meas - mean) / std
    pred = ridge.predict(avg_norm)
    print(f"Predicted betas for avg measurements: {pred[0].round(3)}")

    # Default measurements for sliders
    male_defaults = [96, 84, 95, 45, 55, 33, 175]
    female_defaults = [89, 72, 97, 39, 54, 27, 163]

    # Slider ranges: [min, max, step]
    slider_ranges = {
        'chest': [60, 140, 1],
        'waist': [55, 140, 1],
        'hips': [60, 140, 1],
        'shoulder': [30, 60, 1],
        'thigh': [35, 80, 1],
        'bicep': [18, 50, 1],
        'height': [140, 210, 1],
    }

    out = {
        "male": {
            "weights": ridge.coef_.tolist(),
            "bias": ridge.intercept_.tolist(),
            "measurements_mean": mean.tolist(),
            "measurements_std": std.tolist(),
            "defaults": male_defaults,
        },
        "female": {
            "weights": ridge.coef_.tolist(),
            "bias": ridge.intercept_.tolist(),
            "measurements_mean": mean.tolist(),
            "measurements_std": std.tolist(),
            "defaults": female_defaults,
        },
        "measurement_order": m_labels,
        "slider_ranges": slider_ranges,
        "num_betas": NUM_BETAS,
        "r2_score": r2,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(out, f, indent=2)
    print(f"\nSaved: {OUTPUT_PATH} ({os.path.getsize(OUTPUT_PATH)} bytes)")

if __name__ == '__main__':
    main()
