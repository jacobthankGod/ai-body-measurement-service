#!/usr/bin/env python3
"""
Generate morph targets using vertex groups for correct body-part isolation.

Key improvement over v1: Uses MAKEHUMAN_POINTS vertex groups instead of
Y-range spatial filtering. This prevents arm/leg vertices from being
caught by torso morphs.

All limits use lo=default so morphs don't fire at default preset.
"""
import json
import numpy as np
from pathlib import Path
from collections import defaultdict

V = 14444
INPUT_DIR = Path("public/models/makehuman/male")
OUTPUT_DIR = Path("public/models/makehuman/male")
GROUPS_PATH = Path("data/corrected_vertex_groups.json")


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def load_vertex_groups():
    """Load corrected vertex groups from JSON."""
    return json.loads(GROUPS_PATH.read_text())


def convex_hull_perimeter(points_2d):
    """Compute perimeter of 2D convex hull."""
    pts = sorted(points_2d.tolist(), key=lambda p: (p[0], p[1]))
    if len(pts) <= 2:
        return 0.0

    def cross(O, A, B):
        return (A[0] - O[0]) * (B[1] - O[1]) - (A[1] - O[1]) * (B[0] - O[0])

    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(tuple(p))

    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(tuple(p))

    hull = lower[:-1] + upper[:-1]
    if len(hull) < 3:
        return 0.0

    perim = 0.0
    for i in range(len(hull)):
        j = (i + 1) % len(hull)
        dx = hull[j][0] - hull[i][0]
        dz = hull[j][1] - hull[i][1]
        perim += np.sqrt(dx * dx + dz * dz)
    return perim


BILATERAL_GROUPS = {"knee", "ankle", "calf", "elbow", "bicep", "wrist", "thigh"}


def compute_ring_circumference(base, vertex_indices, group_name=None):
    """Compute circumference of a vertex ring (XZ plane convex hull).

    For bilateral groups (legs/arms), filter to X>0 (right side) to avoid
    the convex hull connecting both limbs.
    """
    if len(vertex_indices) < 3:
        return 0.0

    positions = base[vertex_indices]

    # Filter to one side for bilateral groups
    is_bilateral = group_name in BILATERAL_GROUPS
    if is_bilateral:
        right_mask = positions[:, 0] > 0
        if right_mask.sum() >= 3:
            positions = positions[right_mask]

    pts = positions[:, [0, 2]]  # X, Z
    perim = convex_hull_perimeter(pts)
    return perim * 10  # dm -> cm


def compute_ring_x_width(base, vertex_indices):
    """Compute X-width of a vertex group."""
    if len(vertex_indices) < 2:
        return 0.0
    positions = base[vertex_indices]
    return (positions[:, 0].max() - positions[:, 0].min()) * 10  # dm -> cm


def compute_ring_y_height(base, vertex_indices):
    """Compute Y-height of a vertex group."""
    if len(vertex_indices) < 2:
        return 0.0
    positions = base[vertex_indices]
    return (positions[:, 1].max() - positions[:, 1].min()) * 10  # dm -> cm


def generate_radial_morph(base, vertex_indices, scale_factor, falloff_padding=0.3):
    """Generate morph: radial X/Z scaling of vertex ring.

    ONLY modifies vertices IN the group. No falloff to other body parts.
    This prevents arm/leg contamination from Y-range filtering.
    """
    morph = base.copy()
    group_set = set(vertex_indices)
    group_positions = base[vertex_indices]

    # Compute centroid of the ring in XZ
    cx = group_positions[:, 0].mean()
    cz = group_positions[:, 2].mean()

    for v in group_set:
        x, y, z = base[v]

        # Scale X and Z from ring centroid
        s = scale_factor
        morph[v, 0] = cx + (x - cx) * s
        morph[v, 2] = cz + (z - cz) * s

    return morph


def generate_xscale_morph(base, vertex_indices, scale_factor, falloff_padding=0.3):
    """Generate morph: X-only scaling of vertex group.

    ONLY modifies vertices IN the group. No falloff.
    """
    morph = base.copy()
    group_set = set(vertex_indices)

    for v in group_set:
        morph[v, 0] *= scale_factor

    return morph


def generate_ystretch_morph(base, vertex_indices, anchor_y, scale_factor, falloff_padding=0.3, x_max=99.0):
    """Generate morph: Y-stretching from anchor point.

    ONLY modifies vertices IN the group. No falloff.
    """
    morph = base.copy()
    group_set = set(vertex_indices)

    for v in group_set:
        x, y, z = base[v]
        if abs(x) > x_max:
            continue  # Skip arms for body stretches

        s = scale_factor
        morph[v, 1] = anchor_y + (y - anchor_y) * s

    return morph


def generate_front_push_morph(base, vertex_indices, push_dm, falloff_padding=0.3):
    """Generate morph: push front vertices (Z>0) forward.

    ONLY modifies vertices IN the group. No falloff.
    """
    morph = base.copy()
    group_set = set(vertex_indices)
    group_positions = base[vertex_indices]

    # Find max Z in the group
    max_z = group_positions[:, 2].max()
    if max_z <= 0:
        return morph

    for v in group_set:
        x, y, z = base[v]
        if z <= 0:
            continue  # Only push front vertices

        z_factor = z / max_z
        morph[v, 2] += push_dm * z_factor

    return morph
    group_y_min = group_positions[:, 1].min()
    group_y_max = group_positions[:, 1].max()

    # Find max Z in the group
    max_z = group_positions[:, 2].max()
    if max_z <= 0:
        return morph

    for v in range(len(base)):
        x, y, z = base[v]
        if z <= 0:
            continue  # Only push front vertices

        if group_y_min <= y <= group_y_max:
            weight = 1.0
        elif y < group_y_min and y >= group_y_min - falloff_padding:
            weight = smoothstep((y - (group_y_min - falloff_padding)) / falloff_padding)
        elif y > group_y_max and y <= group_y_max + falloff_padding:
            weight = smoothstep(((group_y_max + falloff_padding) - y) / falloff_padding)
        else:
            continue

        z_factor = z / max_z
        morph[v, 2] += push_dm * weight * z_factor

    return morph


def main():
    print("=== Generating Morph Targets (v2: Vertex-Group Based) ===\n")

    base = np.fromfile(INPUT_DIR / "male_vertices.bin", dtype=np.float32).reshape(V, 3)
    existing_morphs = np.fromfile(INPUT_DIR / "male_morphs.bin", dtype=np.float32).reshape(-1, V, 3)
    config = json.loads((OUTPUT_DIR.parent / "model_config.json").read_text())
    old_names = config["models"]["male"]["morph_names"]
    old_limits = config["models"]["male"]["morph_limits"]

    print(f"  Loaded {len(existing_morphs)} existing morphs")
    print(f"  Morph names: {old_names}\n")

    # Load corrected vertex groups
    groups = load_vertex_groups()
    print(f"  Loaded {len(groups)} vertex groups\n")

    # Compute base measurements from vertex groups
    print("=== Base Measurements (from vertex groups) ===")
    measurements = {}
    for name, indices in groups.items():
        if len(indices) < 3:
            continue
        circ = compute_ring_circumference(base, indices, group_name=name)
        if circ > 0:
            measurements[name] = circ
            print(f"  {name:16s} ({len(indices):4d} verts): {circ:.1f} cm")

    # Also compute X-widths
    for name in ['shoulder', 'chest']:
        if name in groups and len(groups[name]) >= 2:
            w = compute_ring_x_width(base, groups[name])
            measurements[f'{name}_width'] = w
            print(f"  {name+'_width':16s} ({len(groups[name]):4d} verts): {w:.1f} cm")

    # Compute Y-heights
    for name in ['waist', 'stomach', 'hips', 'thigh', 'chest']:
        if name in groups and len(groups[name]) >= 2:
            h = compute_ring_y_height(base, groups[name])
            measurements[f'{name}_height'] = h
            print(f"  {name+'_height':16s} ({len(groups[name]):4d} verts): {h:.1f} cm")

    print()

    # === Define morphs to generate ===
    # These replace the broken Y-range morphs with vertex-group-based ones

    # Morph definitions: (name, morph_type, group_name, target_value_cm, extra_params)
    MORPH_DEFS = [
        # REPLACEMENTS for broken morphs
        ("waist",            "radial",   "waist",      None,  {}),  # Use existing morph
        ("stomach_form",     "radial",   "stomach",    None,  {}),  # Use existing morph
        ("hips",             "radial",   "hips",       None,  {}),  # Use existing morph
        ("ankle_round",      "radial",   "ankle",      None,  {}),  # Use existing morph
        ("across_chest",     "xscale",   "chest",      None,  {}),  # Use existing morph
        ("knee_round",       "radial",   "knee",       None,  {}),  # Use existing morph

        # NEW morphs for non-functional sliders
        ("upper_hip",        "radial",   "upper_hip",  None,  {}),
        ("across_back",      "xscale",   "chest",      None,  {}),
        ("across_shoulder",  "xscale",   "shoulder",   None,  {}),
        ("elbow_round",      "radial",   "elbow",      None,  {}),
        ("inseam",           "ystretch", "thigh",      None,  {"anchor": "bottom", "x_max": 1.5}),
        ("trouser_waist",    "radial",   "upper_hip",  None,  {}),
        ("back_waist_length","ystretch", "waist",      None,  {"anchor": "top"}),
        ("front_waist_length","ystretch","stomach",    None,  {"anchor": "top"}),
        ("neck_to_waist",    "ystretch", "waist",      None,  {"anchor": "top", "x_max": 2.5}),
        ("crotch_depth",     "ystretch", "hips",       None,  {"anchor": "top"}),
        ("bust_point",       "front_push","bust_point", None, {}),
        ("shoulder_to_bust", "ystretch", "bust_point", None,  {"anchor": "top"}),
    ]

    # For morphs that use existing deltas (waist, stomach_form, hips, etc.),
    # we keep the original deltas from the JSON source. Only generate NEW deltas
    # for the 12 non-functional sliders.

    # Names of morphs to KEEP from original (don't replace)
    KEEP_ORIGINAL = {"waist", "stomach_form", "hips", "ankle_round", "across_chest", "knee_round"}

    # Generate new deltas
    generated = {}
    for name, mtype, group_name, target_val, params in MORPH_DEFS:
        if name in KEEP_ORIGINAL:
            continue  # Keep original morph delta

        if group_name not in groups or len(groups[group_name]) < 3:
            print(f"  SKIP {name}: no vertex group '{group_name}'")
            continue

        indices = groups[group_name]

        # Compute base measurement from the group
        if mtype == "radial":
            base_val = compute_ring_circumference(base, indices, group_name=group_name)
        elif mtype == "xscale":
            base_val = compute_ring_x_width(base, indices)
        elif mtype == "ystretch":
            base_val = compute_ring_y_height(base, indices)
        elif mtype == "front_push":
            base_val = 1  # Not used for front_push, skip size check
        else:
            continue

        if mtype != "front_push" and base_val < 1:
            print(f"  SKIP {name}: base measurement too small ({base_val:.1f})")
            continue

        # Compute target from slider range
        # For circumferences: target = base * 1.2 (20% increase at full influence)
        # For widths: target = base * 1.15 (15% increase)
        # For lengths: target = base * 1.15 (15% increase)
        if mtype == "radial":
            target_cm = base_val * 1.25  # 25% increase at full influence
        elif mtype == "xscale":
            target_cm = base_val * 1.20  # 20% increase
        elif mtype == "ystretch":
            target_cm = base_val * 1.15  # 15% increase
        elif mtype == "front_push":
            target_cm = 0.3  # 3cm push

        # Compute scale factor
        if mtype == "front_push":
            scale = target_cm
        else:
            scale = target_cm / base_val

        print(f"  {name:20s}: {mtype:10s} group={group_name:12s} base={base_val:.1f} -> target={target_cm:.1f} scale={scale:.3f}")

        # Anchor point for ystretch
        anchor_y = None
        if mtype == "ystretch":
            group_ys = base[indices, 1]
            if params.get("anchor") == "top":
                anchor_y = group_ys.max()
            elif params.get("anchor") == "bottom":
                anchor_y = group_ys.min()
            else:
                anchor_y = group_ys.mean()

        # Generate morph
        if mtype == "radial":
            morph_target = generate_radial_morph(base, indices, scale)
        elif mtype == "xscale":
            morph_target = generate_xscale_morph(base, indices, scale)
        elif mtype == "ystretch":
            x_max = params.get("x_max", 99.0)
            morph_target = generate_ystretch_morph(base, indices, anchor_y, scale, x_max=x_max)
        elif mtype == "front_push":
            morph_target = generate_front_push_morph(base, indices, target_cm)

        generated[name] = morph_target

    print()

    # === Build final morph array ===
    # Start with original morphs (keep all 17 from JSON source)
    final_morphs = existing_morphs.copy()
    final_names = list(old_names)

    # Replace existing morphs that we generated new deltas for
    for name, morph_target in generated.items():
        if name in final_names:
            idx = final_names.index(name)
            final_morphs[idx] = morph_target
            print(f"  Replaced morph [{idx}] {name}")

    # Append new morphs (ones not in original)
    new_appends = []
    for name, morph_target in generated.items():
        if name not in final_names:
            new_appends.append((name, morph_target))
            final_names.append(name)
            print(f"  Appended morph [{len(final_names)-1}] {name}")

    if new_appends:
        append_array = np.stack([mt for _, mt in new_appends])
        final_morphs = np.concatenate([final_morphs, append_array], axis=0)

    # Remove identity morphs that are now handled by other morphs
    # (ankle_round, across_chest, knee_round are in KEEP_ORIGINAL, so they stay)

    print(f"\n  Total morphs: {len(final_morphs)}")

    # === Fix ALL limits: lo = default ===
    print("\n=== Fixing Morph Limits (lo = default) ===")

    # Define corrected limits for ALL morphs
    ALL_LIMITS = {
        # Original morphs - lo=default so they don't fire at default
        "height":         {"default": 175, "low": 175, "high": 195},
        "chest":          {"default": 96,  "low": 96,  "high": 130},
        "neck":           {"default": 39,  "low": 39,  "high": 45},
        "neckheight":     {"default": 28,  "low": 28,  "high": 36},
        "shoulders":      {"default": 43,  "low": 43,  "high": 55},
        "shoulder_slope": {"default": 1,   "low": 1,   "high": 2},
        "bust_girth":     {"default": 86,  "low": 86,  "high": 100},
        "stomach_form":   {"default": 1,   "low": 1,   "high": 2},
        "waist":          {"default": 84,  "low": 84,  "high": 140},
        "arm_length":     {"default": 62,  "low": 62,  "high": 80},
        "armgirth":       {"default": 32,  "low": 32,  "high": 42},
        "wrist_girth":    {"default": 17,  "low": 17,  "high": 22},
        "hips":           {"default": 96,  "low": 96,  "high": 130},
        "hip_height":     {"default": 28,  "low": 28,  "high": 38},
        "thigh_girth":    {"default": 55,  "low": 55,  "high": 75},
        "lowerleg_length":{"default": 116, "low": 116, "high": 130},
        "calf_girth":     {"default": 36,  "low": 36,  "high": 48},

        # New morphs
        "ankle_round":      {"default": 24,  "low": 24,  "high": 35},
        "across_chest":     {"default": 41,  "low": 41,  "high": 55},
        "knee_round":       {"default": 38,  "low": 38,  "high": 50},
        "upper_hip":        {"default": 91,  "low": 91,  "high": 135},
        "across_back":      {"default": 39,  "low": 39,  "high": 55},
        "across_shoulder":  {"default": 42,  "low": 42,  "high": 60},
        "elbow_round":      {"default": 25,  "low": 25,  "high": 35},
        "inseam":           {"default": 91,  "low": 91,  "high": 110},
        "trouser_waist":    {"default": 84,  "low": 84,  "high": 150},
        "back_waist_length":{"default": 28,  "low": 28,  "high": 40},
        "front_waist_length":{"default": 28, "low": 28,  "high": 40},
        "neck_to_waist":    {"default": 28,  "low": 28,  "high": 40},
        "crotch_depth":     {"default": 28,  "low": 28,  "high": 40},
        "bust_point":       {"default": 7,   "low": 7,   "high": 12},
        "shoulder_to_bust": {"default": 8,   "low": 8,   "high": 14},
        "fat":              {"default": 0,   "low": 0,   "high": 1},
    }

    # Build limit arrays matching morph order
    limits_default = []
    limits_low = []
    limits_high = []

    for name in final_names:
        if name in ALL_LIMITS:
            lim = ALL_LIMITS[name]
            limits_default.append(lim["default"])
            limits_low.append(lim["low"])
            limits_high.append(lim["high"])
        else:
            # Unknown morph - use safe defaults
            limits_default.append(0)
            limits_low.append(0)
            limits_high.append(1)
            print(f"  WARNING: No limits defined for '{name}'")

    # Verify lo=default for all morphs
    print("\n  Verifying lo=default:")
    all_ok = True
    for i, name in enumerate(final_names):
        lo = limits_low[i]
        defl = limits_default[i]
        hi = limits_high[i]
        if lo != defl:
            print(f"  FAIL: {name} lo={lo} != default={defl}")
            all_ok = False
    if all_ok:
        print("  ALL OK: lo = default for every morph")

    # === Write binary files ===
    morphs_flat = final_morphs.reshape(-1).astype(np.float32)
    out_path = OUTPUT_DIR / "male_morphs.bin"
    morphs_flat.tofile(out_path)
    print(f"\n  Wrote {out_path}: {morphs_flat.nbytes:,} bytes ({len(final_morphs)} morphs x {V} verts)")

    # === Update config ===
    config["models"]["male"]["morph_count"] = len(final_morphs)
    config["models"]["male"]["morph_names"] = final_names
    config["models"]["male"]["morph_limits"] = {
        "default": limits_default,
        "low": limits_low,
        "high": limits_high,
    }
    config["models"]["male"]["display_names"] = [
        n.replace("_", " ").title() for n in final_names
    ]

    config_path = OUTPUT_DIR.parent / "model_config.json"
    config_path.write_text(json.dumps(config, indent=2))
    print(f"  Wrote {config_path}")
    print(f"\n  Morph names ({len(final_names)}): {final_names}")
    print(f"\n=== Done ===")


if __name__ == "__main__":
    main()
