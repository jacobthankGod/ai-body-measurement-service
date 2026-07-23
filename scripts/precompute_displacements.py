#!/usr/bin/env python3
"""Precompute per-measurement vertex displacement vectors for browser.

For each of the 35 measurements, computes the vertex displacement needed
to change that measurement by 1cm at T-pose. Stored as sparse delta-vertices
that the browser can scale and add to any mesh.

Output: public/assets/smpl_displacements.json (~200KB)
"""

import json, os
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(PROJECT_ROOT, 'public', 'assets', 'smpl_displacements.json')
NUM_BETAS = 10
NUM_VERTS = 6890


def load_smpl():
    vt = np.load(os.path.join(PROJECT_ROOT, 'models', 'v_template.npy'))
    sd = np.load(os.path.join(PROJECT_ROOT, 'models', 'shapedirs.npy')).reshape(NUM_VERTS, 3, NUM_BETAS)
    return vt, sd


def load_smpl_segmentation():
    import re
    path = os.path.join(PROJECT_ROOT, 'public', 'assets', 'smpl_segmentation.js')
    parts = {}
    with open(path) as f:
        content = f.read()
    pattern = r'"(\w+)":\s*\[([\d,\s]+)\]'
    for m in re.finditer(pattern, content):
        name = m.group(1)
        indices = [int(x.strip()) for x in m.group(2).split(',') if x.strip()]
        parts[name] = indices
    return parts


def load_custom_body_points():
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
                        if 0 <= idx < NUM_VERTS:
                            groups[current].append(idx)
                    except ValueError:
                        pass
    return groups


def measure_circ_ellipse(vertices, vertex_indices, axis='xz'):
    """Convex hull perimeter — matches browser's _circFromVerts."""
    if len(vertex_indices) == 0:
        return 0.0
    gv = vertices[vertex_indices]
    if axis == 'yz':
        pts = gv[:, [1, 2]]
    else:
        pts = gv[:, [0, 2]]
    if len(pts) < 3:
        return 0.0
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


def compute_vertex_displacement_for_circumference(verts, verts_indices, target_delta_cm, plane_axis='xz'):
    """
    Compute vertex displacement to change circumference by target_delta_cm.
    Returns sparse displacement array (NUM_VERTS, 3).
    """
    displacement = np.zeros((NUM_VERTS, 3), dtype=np.float32)
    if not verts_indices or target_delta_cm == 0:
        return displacement

    gv = verts[verts_indices]

    if plane_axis == 'xz':
        # Compute centroid in XZ
        cx = np.mean(gv[:, 0])
        cz = np.mean(gv[:, 2])
        # Current radius
        radii = np.sqrt((gv[:, 0] - cx)**2 + (gv[:, 2] - cz)**2)
        mean_r = np.mean(radii)
        if mean_r < 0.001:
            return displacement
        # Scale factor for 1cm change
        # circumference = 2*pi*r, so dc = 2*pi*dr => dr = dc/(2*pi)
        target_r = mean_r + target_delta_cm / (200 * np.pi)  # cm to m, divide by 2*pi
        scale = target_r / mean_r
        # Apply displacement radially in XZ
        for i, vi in enumerate(verts_indices):
            dx = verts[vi, 0] - cx
            dz = verts[vi, 2] - cz
            displacement[vi, 0] = dx * (scale - 1)
            displacement[vi, 2] = dz * (scale - 1)
    elif plane_axis == 'yz':
        # Arm circumference: YZ plane (arm hangs vertically)
        cy = np.mean(gv[:, 1])
        cz = np.mean(gv[:, 2])
        radii = np.sqrt((gv[:, 1] - cy)**2 + (gv[:, 2] - cz)**2)
        mean_r = np.mean(radii)
        if mean_r < 0.001:
            return displacement
        target_r = mean_r + target_delta_cm / (200 * np.pi)
        scale = target_r / mean_r
        for i, vi in enumerate(verts_indices):
            dy = verts[vi, 1] - cy
            dz = verts[vi, 2] - cz
            displacement[vi, 1] = dy * (scale - 1)
            displacement[vi, 2] = dz * (scale - 1)

    return displacement


def compute_vertex_displacement_for_width(verts, verts_indices, target_delta_cm):
    """
    Compute vertex displacement to change X-width by target_delta_cm.
    Scales X coordinates symmetrically from centroid.
    """
    displacement = np.zeros((NUM_VERTS, 3), dtype=np.float32)
    if not verts_indices or target_delta_cm == 0:
        return displacement

    gv = verts[verts_indices]
    cx = np.mean(gv[:, 0])
    current_width = (gv[:, 0].max() - gv[:, 0].min()) * 100
    if current_width < 0.001:
        return displacement
    # Scale factor
    target_width = current_width + target_delta_cm
    scale = target_width / current_width
    for vi in verts_indices:
        dx = verts[vi, 0] - cx
        displacement[vi, 0] = dx * (scale - 1)
    return displacement


def compute_vertex_displacement_for_length(verts, verts_a, verts_b, target_delta_cm):
    """
    Compute vertex displacement to change centroid-to-centroid distance by target_delta_cm.
    Moves verts_b up/down (Y axis) to achieve target distance.
    """
    displacement = np.zeros((NUM_VERTS, 3), dtype=np.float32)
    if not verts_a or not verts_b or target_delta_cm == 0:
        return displacement

    ca = np.mean(verts[verts_a], axis=0)
    cb = np.mean(verts[verts_b], axis=0)
    current_dist = np.linalg.norm(ca - cb) * 100
    if current_dist < 0.001:
        return displacement

    # Move verts_b along the vector from ca to cb
    direction = (cb - ca) / np.linalg.norm(cb - ca)
    delta_m = target_delta_cm / 100  # cm to meters
    for vi in verts_b:
        displacement[vi] = direction * delta_m
    return displacement


MEASUREMENT_CONFIGS = [
    # Circumferences (torso)
    {'key': 'Chest Round', 'parts': ['spine2', 'rightShoulder', 'leftShoulder'], 'axis': 'xz', 'type': 'circ'},
    {'key': 'Bust Round', 'alias': 'Chest Round'},
    {'key': 'Waist Round', 'parts': ['spine1'], 'axis': 'xz', 'type': 'circ'},
    {'key': 'Stomach Round', 'parts': ['spine'], 'axis': 'xz', 'type': 'circ'},
    {'key': 'Hip Round', 'parts': ['hips'], 'axis': 'xz', 'type': 'circ'},
    {'key': 'Neck Round', 'parts': ['neck'], 'axis': 'xz', 'type': 'circ'},

    # Circumferences (limbs)
    {'key': 'Thigh Round', 'parts': ['rightUpLeg', 'leftUpLeg'], 'axis': 'xz', 'type': 'circ'},
    {'key': 'Knee Round', 'parts': ['rightLeg', 'leftLeg'], 'axis': 'xz', 'type': 'circ',
     'y_filter': lambda v: v[1] > -0.8},
    {'key': 'Calf Round', 'parts': ['rightLeg', 'leftLeg'], 'axis': 'xz', 'type': 'circ'},
    {'key': 'Ankle Round', 'parts': ['rightLeg', 'rightFoot'], 'axis': 'xz', 'type': 'circ',
     'y_filter': lambda v: v[1] < -1.0},
    {'key': 'Bicep Round', 'parts': ['rightArm', 'leftArm'], 'axis': 'yz', 'type': 'circ'},
    {'key': 'Elbow Round', 'parts': ['rightForeArm', 'leftForeArm'], 'axis': 'yz', 'type': 'circ'},
    {'key': 'Wrist Round', 'parts': ['rightForeArm', 'rightHand'], 'axis': 'yz', 'type': 'circ',
     'y_filter': lambda v: v[1] < 0.19},

    # Derived circumferences
    {'key': 'Upper Hip', 'alias': 'Hip Round', 'scale': 0.92},

    # Width (must come before derived width aliases)
    {'key': 'Shoulder', 'parts': ['rightShoulder', 'leftShoulder'], 'type': 'width'},
    {'key': 'Across Shoulder', 'alias': 'Shoulder'},
    {'key': 'Across Back', 'alias': 'Shoulder', 'scale': 0.92},
    {'key': 'Across Chest', 'alias': 'Shoulder', 'scale': 0.96},
    {'key': 'Armhole Round', 'alias': 'Shoulder', 'scale': 0.45},

    # Lengths
    {'key': 'Half Length', 'parts_a': ['neck'], 'parts_b': ['spine1'], 'type': 'length'},
    {'key': 'Full Top Length', 'parts_a': ['neck'], 'parts_b': ['hips'], 'type': 'length'},
    {'key': 'Back Waist Length', 'alias': 'Half Length'},
    {'key': 'Front Waist Length', 'alias': 'Half Length'},
    {'key': 'Neck to Waist', 'alias': 'Half Length'},
    {'key': 'Shoulder to Waist', 'alias': 'Half Length'},
    {'key': 'Waist to Hip', 'parts_a': ['spine1'], 'parts_b': ['hips'], 'type': 'length'},
    {'key': 'Crotch Depth', 'alias': 'Waist to Hip'},
    {'key': 'Trouser Waist', 'alias': 'Waist Round'},
    {'key': 'Trouser Length', 'parts_a': ['spine1'], 'parts_b': ['rightLeg', 'rightFoot'],
     'type': 'length', 'y_filter_b': lambda v: v[1] < -1.0},
    {'key': 'Inseam', 'alias': 'Trouser Length', 'scale': 0.78},
    {'key': 'Sleeve Length', 'parts_a': ['rightShoulder', 'leftShoulder'],
     'parts_b': ['rightForeArm', 'rightHand'], 'type': 'length',
     'y_filter_b': lambda v: v[1] < 0.19},

    # Bust-specific
    {'key': 'High Bust', 'alias': 'Bust Round', 'scale': 0.85},
    {'key': 'Under Bust', 'alias': 'Bust Round', 'scale': 0.75},
    {'key': 'Bust Point', 'parts_a': ['neck'], 'parts_b': ['spine2'], 'type': 'length',
     'y_filter_b': lambda v: True, 'max_b_verts': 3},
    {'key': 'Shoulder to Bust Point', 'alias': 'Bust Point', 'scale': 1.1},
    {'key': 'Shoulder to Under Bust', 'alias': 'Bust Point', 'scale': 1.3},
]


def get_verts_for_config(config, smpl_parts, verts, suffix=''):
    """Get vertex indices for a config, with optional Y filtering."""
    parts_key = f'parts{suffix}'
    if parts_key not in config:
        return []
    all_v = []
    for pn in config[parts_key]:
        all_v.extend(smpl_parts.get(pn, []))
    # Apply Y filter if specified
    y_filter_key = f'y_filter{suffix}' if suffix else 'y_filter'
    if y_filter_key in config and all_v:
        filt = config[y_filter_key]
        all_v = [vi for vi in all_v if filt(verts[vi])]
    # Limit vertices if specified
    max_key = f'max_b_verts{suffix}' if suffix else 'max_b_verts'
    if max_key in config and len(all_v) > config[max_key]:
        all_v = all_v[:config[max_key]]
    return all_v


def main():
    print("Loading SMPL...")
    v_template, shapedirs = load_smpl()
    smpl_parts = load_smpl_segmentation()
    cbp = load_custom_body_points()
    print(f"  SMPL parts: {len(smpl_parts)}")
    print(f"  Custom body points: {len(cbp)}")

    # Use T-pose (beta=0)
    verts = v_template.copy()

    # Compute displacement vectors for each measurement
    displacements = {}
    unit_deltas = {}  # displacement per 1cm change

    for config in MEASUREMENT_CONFIGS:
        key = config['key']

        if 'alias' in config:
            # Alias: reference another measurement's displacement
            alias_key = config['alias']
            scale = config.get('scale', 1.0)
            if alias_key in unit_deltas:
                unit_deltas[key] = unit_deltas[alias_key] * scale
                displacements[key] = {
                    'type': 'alias',
                    'alias': alias_key,
                    'scale': round(scale, 4),
                }
                print(f"  {key}: alias of {alias_key} × {scale}")
            else:
                print(f"  {key}: WARNING - alias target {alias_key} not found")
            continue

        mtype = config.get('type', 'circ')

        if mtype == 'circ':
            # Circumference displacement
            verts_indices = get_verts_for_config(config, smpl_parts, verts)
            if not verts_indices:
                print(f"  {key}: no vertices found")
                continue
            axis = config.get('axis', 'xz')
            disp = compute_vertex_displacement_for_circumference(verts, verts_indices, 1.0, axis)
            unit_deltas[key] = disp

            # Compute current measurement
            curr = measure_circ_ellipse(verts, verts_indices, axis)
            displacements[key] = {
                'type': 'circ',
                'axis': axis,
                'verts': verts_indices,
                'current_value': round(curr, 2),
            }
            print(f"  {key}: {len(verts_indices)} verts, current={curr:.1f}cm")

        elif mtype == 'width':
            verts_indices = get_verts_for_config(config, smpl_parts, verts)
            if not verts_indices:
                print(f"  {key}: no vertices found")
                continue
            disp = compute_vertex_displacement_for_width(verts, verts_indices, 1.0)
            unit_deltas[key] = disp

            gv = verts[verts_indices]
            curr = (gv[:, 0].max() - gv[:, 0].min()) * 100
            displacements[key] = {
                'type': 'width',
                'verts': verts_indices,
                'current_value': round(curr, 2),
            }
            print(f"  {key}: {len(verts_indices)} verts, current={curr:.1f}cm")

        elif mtype == 'length':
            verts_a = get_verts_for_config(config, smpl_parts, verts, suffix='_a')
            verts_b = get_verts_for_config(config, smpl_parts, verts, suffix='_b')
            if not verts_a or not verts_b:
                print(f"  {key}: missing vertex sets (a={len(verts_a)}, b={len(verts_b)})")
                continue
            disp = compute_vertex_displacement_for_length(verts, verts_a, verts_b, 1.0)
            unit_deltas[key] = disp

            ca = np.mean(verts[verts_a], axis=0)
            cb = np.mean(verts[verts_b], axis=0)
            curr = np.linalg.norm(ca - cb) * 100
            displacements[key] = {
                'type': 'length',
                'verts_a': verts_a,
                'verts_b': verts_b,
                'current_value': round(curr, 2),
            }
            print(f"  {key}: a={len(verts_a)}, b={len(verts_b)}, current={curr:.1f}cm")

    # Save unit deltas as sparse arrays (only non-zero entries)
    sparse_deltas = {}
    for key, disp in unit_deltas.items():
        # Find non-zero entries
        nonzero_mask = np.any(disp != 0, axis=1)
        indices = np.where(nonzero_mask)[0]
        if len(indices) > 0:
            sparse_deltas[key] = {
                'indices': indices.tolist(),
                'dx': [round(float(disp[i, 0]), 6) for i in indices],
                'dy': [round(float(disp[i, 1]), 6) for i in indices],
                'dz': [round(float(disp[i, 2]), 6) for i in indices],
            }
        else:
            sparse_deltas[key] = {'indices': [], 'dx': [], 'dy': [], 'dz': []}

    # Output
    out = {
        'version': 1,
        'num_verts': NUM_VERTS,
        'displacements': displacements,
        'unit_deltas': sparse_deltas,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(out, f)
    print(f"\nSaved: {OUTPUT_PATH} ({os.path.getsize(OUTPUT_PATH)} bytes)")

    # Summary
    total_sparse = sum(len(d.get('indices', [])) for d in sparse_deltas.values())
    print(f"Total sparse entries: {total_sparse}")
    print(f"Memory estimate: {total_sparse * 3 * 8 / 1024:.1f} KB (float64)")


if __name__ == '__main__':
    main()
