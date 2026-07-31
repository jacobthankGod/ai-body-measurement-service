#!/usr/bin/env python3
"""
Analyze vertex positions for each body part group.
Identifies correct vertices per body part based on spatial analysis.
Outputs corrected vertex groups for morph generation.
"""
import json
import numpy as np
import re
from pathlib import Path

V = 14444
VERTS_PATH = Path("public/models/makehuman/male/male_vertices.bin")
POINTS_PATH = Path("public/assets/makehuman_body_points.js")

def load_vertices():
    return np.fromfile(VERTS_PATH, dtype=np.float32).reshape(V, 3)

def load_vertex_groups():
    """Parse makehuman_body_points.js to extract vertex index arrays."""
    text = POINTS_PATH.read_text()
    groups = {}
    # Match patterns like: var _waist = [1,2,3,...];
    for match in re.finditer(r'var\s+_(\w+)\s*=\s*\[([^\]]+)\]', text):
        name = match.group(1)
        indices = [int(x.strip()) for x in match.group(2).split(',') if x.strip()]
        groups[name] = indices
    return groups

def analyze_group(name, indices, verts):
    """Analyze spatial distribution of a vertex group."""
    if not indices:
        return None
    positions = verts[indices]
    centroid = positions.mean(axis=0)
    y_min, y_max = positions[:, 1].min(), positions[:, 1].max()
    x_min, x_max = positions[:, 0].min(), positions[:, 0].max()
    z_min, z_max = positions[:, 2].min(), positions[:, 2].max()
    x_abs_max = max(abs(x_min), abs(x_max))

    return {
        'name': name,
        'count': len(indices),
        'centroid': centroid.tolist(),
        'y_range': [float(y_min), float(y_max)],
        'x_range': [float(x_min), float(x_max)],
        'z_range': [float(z_min), float(z_max)],
        'x_abs_max': float(x_abs_max),
        'y_center': float((y_min + y_max) / 2),
    }

def filter_group_by_body_part(name, indices, verts, verbose=True):
    """Filter a vertex group to only include vertices from the correct body part.
    Returns (filtered_indices, removed_indices).
    """
    if not indices:
        return [], []

    positions = verts[indices]
    y_vals = positions[:, 1]
    x_vals = positions[:, 0]
    x_abs = np.abs(x_vals)

    # Body part definitions: (y_min, y_max, x_max_abs, description)
    # These define the EXPECTED spatial region for each body part
    BODY_PART_REGIONS = {
        # Torso circumference measurements (body only, exclude arms)
        'waist':      (8.5, 10.5, 2.0, 'torso'),
        'stomach':    (7.0, 10.0, 2.0, 'torso'),
        'upper_hip':  (8.0, 10.0, 2.0, 'torso'),
        'hips':       (6.0, 8.5,  2.5, 'torso'),
        'chest':      (10.0, 13.0, 3.0, 'torso'),
        'neck':       (13.0, 15.0, 2.0, 'torso'),

        # Limb circumference measurements (exclude torso)
        'thigh':      (4.5, 8.5,  99.0, 'limb'),   # x_min check instead
        'calf':       (1.5, 5.0,  99.0, 'limb'),
        'ankle':      (0.0, 2.5,  99.0, 'limb'),
        'knee':       (2.5, 5.5,  99.0, 'limb'),
        'bicep':      (9.0, 14.0, 99.0, 'limb'),
        'elbow':      (7.0, 10.5, 99.0, 'limb'),
        'wrist':      (5.0, 9.0,  99.0, 'limb'),

        # Width measurements
        'shoulder':   (12.0, 15.0, 99.0, 'shoulder'),

        # Bust/chest detail
        'bust_point':  (9.5, 12.0, 3.0, 'torso'),
        'high_bust':   (10.5, 12.5, 3.0, 'torso'),
        'under_bust':  (9.0, 11.0, 3.0, 'torso'),
        'armhole':     (10.0, 13.5, 99.0, 'armhole'),
    }

    if name not in BODY_PART_REGIONS:
        return indices, []  # No filtering rules, keep all

    y_lo, y_hi, x_max, part_type = BODY_PART_REGIONS[name]

    filtered = []
    removed = []

    for i, idx in enumerate(indices):
        x, y, z = verts[idx]
        keep = True

        if part_type == 'torso':
            # Torso: keep only vertices within Y range AND |X| < x_max
            if y < y_lo or y > y_hi:
                keep = False
            if abs(x) > x_max:
                keep = False
        elif part_type == 'limb':
            # Limb: keep only vertices with |X| > 1.0 (exclude torso center)
            # AND within Y range
            if y < y_lo or y > y_hi:
                keep = False
            # For limbs, we need to check if vertex is on a limb, not torso
            # Limbs have |X| > ~1.0 for legs, |X| > ~2.5 for arms
            if name in ('thigh', 'calf', 'ankle', 'knee'):
                # Leg vertices: must be away from center (one leg)
                if abs(x) < 0.8:
                    keep = False
            elif name in ('bicep', 'elbow', 'wrist'):
                # Arm vertices: must be far from center
                if abs(x) < 2.0:
                    keep = False
        elif part_type == 'shoulder':
            # Shoulder: vertices at top of torso, including arm transition
            if y < y_lo or y > y_hi:
                keep = False
        elif part_type == 'armhole':
            # Armhole: around shoulder joint
            if y < y_lo or y > y_hi:
                keep = False

        if keep:
            filtered.append(idx)
        else:
            removed.append(idx)

    return filtered, removed


def main():
    print("=== Analyzing Vertex Groups ===\n")

    verts = load_vertices()
    groups = load_vertex_groups()

    print(f"Loaded {V} vertices, {len(groups)} groups\n")

    # Analyze each group
    for name in sorted(groups.keys()):
        indices = groups[name]
        info = analyze_group(name, indices, verts)
        if info is None:
            continue

        centroid_y = info['centroid'][1]
        centroid_x = info['centroid'][0]

        print(f"--- {name} ({info['count']} verts) ---")
        print(f"  Centroid: X={centroid_x:.3f} Y={centroid_y:.3f} Z={info['centroid'][2]:.3f}")
        print(f"  Y range: [{info['y_range'][0]:.3f}, {info['y_range'][1]:.3f}]")
        print(f"  X range: [{info['x_range'][0]:.3f}, {info['x_range'][1]:.3f}] (|X|_max={info['x_abs_max']:.3f})")
        print(f"  Z range: [{info['z_range'][0]:.3f}, {info['z_range'][1]:.3f}]")

        # Filter and report
        filtered, removed = filter_group_by_body_part(name, indices, verts)
        if removed:
            print(f"  FILTERED: {len(removed)} vertices removed, {len(filtered)} kept")
            if len(removed) <= 10:
                for idx in removed:
                    x, y, z = verts[idx]
                    print(f"    Removed vert {idx}: X={x:.3f} Y={y:.3f} Z={z:.3f}")
            else:
                # Show Y/X distribution of removed
                rem_pos = verts[removed]
                print(f"    Removed Y range: [{rem_pos[:,1].min():.3f}, {rem_pos[:,1].max():.3f}]")
                print(f"    Removed X range: [{rem_pos[:,0].min():.3f}, {rem_pos[:,0].max():.3f}]")
        else:
            print(f"  OK: all {len(filtered)} vertices pass filter")
        print()

    # Now generate corrected groups
    print("\n=== Generating Corrected Groups ===\n")

    corrected = {}
    for name in sorted(groups.keys()):
        indices = groups[name]
        filtered, removed = filter_group_by_body_part(name, indices, verts)
        corrected[name] = filtered
        if removed:
            print(f"  {name}: {len(indices)} -> {len(filtered)} ({len(removed)} removed)")
        else:
            print(f"  {name}: {len(indices)} (unchanged)")

    # Output corrected groups as JS
    output_lines = ["/**", " * Corrected MakeHuman body point vertex groups.", " * Filtered to exclude wrong body-part vertices.", " */", "", "(function () {", '"use strict";']

    for name in sorted(corrected.keys()):
        indices = corrected[name]
        output_lines.append(f"")
        output_lines.append(f"  // {name} — {len(indices)} vertices")
        # Write in rows of 20
        for i in range(0, len(indices), 20):
            chunk = indices[i:i+20]
            output_lines.append(f"  var _{name}_part{i//20} = [{','.join(str(x) for x in chunk)}];")

        # Merge all parts
        all_vars = [f"_{name}_part{i//20}" for i in range(0, len(indices), 20)]
        if len(all_vars) == 1:
            output_lines.append(f"  var _{name} = {all_vars[0]};")
        else:
            output_lines.append(f"  var _{name} = [{','.join(all_vars)}].flat();")

    output_lines.append("")
    output_lines.append("  window.MAKEHUMAN_POINTS = {")
    for name in sorted(corrected.keys()):
        output_lines.append(f"    {name}: _{name},")
    output_lines.append("  };")
    output_lines.append("})();")
    output_lines.append("")

    out_path = Path("public/assets/makehuman_body_points_corrected.js")
    out_path.write_text("\n".join(output_lines))
    print(f"\n  Wrote {out_path}")

    # Also output as JSON for Python morph generation
    json_data = {name: corrected[name] for name in sorted(corrected.keys())}
    json_path = Path("data/corrected_vertex_groups.json")
    json_path.parent.mkdir(exist_ok=True)
    json_path.write_text(json.dumps(json_data, indent=2))
    print(f"  Wrote {json_path}")


if __name__ == "__main__":
    main()
