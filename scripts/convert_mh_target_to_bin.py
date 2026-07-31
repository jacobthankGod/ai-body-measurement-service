#!/usr/bin/env python3
"""Convert MakeHuman .target sparse deltas to BodyApps dense morph binaries.

Strategy:
1. Load hm08.obj base mesh (19,158 verts)
2. Load BodyApps model vertices (14,444 verts) from existing binary
3. Build KD-tree correspondence: hm08_idx → BodyApps_nearest_idx
4. For each target file, apply sparse deltas to hm08 base
5. Compute delta between morphed and base
6. Map deltas to BodyApps vertex ordering via correspondence
7. Save as dense morph binary (14,444 × 3 floats)
"""

import gzip
import struct
import numpy as np
from scipy.spatial import cKDTree
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
TARGETS_DIR = os.path.join(SCRIPT_DIR, "makehuman_targets")
RAW_DIR = os.path.join(TARGETS_DIR, "raw")

# BodyApps binary layout
NUM_VERTS = 14444
FLOAT_SIZE = 4
MORPH_SIZE = NUM_VERTS * 3 * FLOAT_SIZE  # 173,328 bytes

def load_obj_vertices(obj_path):
    """Load vertex positions from .obj file."""
    verts = []
    with open(obj_path, 'r') as f:
        for line in f:
            if line.startswith('v '):
                parts = line.strip().split()
                verts.append([float(parts[1]), float(parts[2]), float(parts[3])])
    return np.array(verts, dtype=np.float32)

def load_bodyapps_binary(gender):
    """Load existing BodyApps base vertices (from vertices.bin, NOT morphs.bin)."""
    bin_path = os.path.join(BASE_DIR, "public", "models", "makehuman", gender, f"{gender}_vertices.bin")
    with open(bin_path, 'rb') as f:
        data = f.read(NUM_VERTS * 3 * FLOAT_SIZE)
    return np.frombuffer(data, dtype=np.float32).reshape(NUM_VERTS, 3)

def load_target(target_path):
    """Load sparse delta target file. Returns dict of {vert_idx: (dx, dy, dz)}."""
    deltas = {}
    with gzip.open(target_path, 'rt') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 4:
                idx = int(parts[0])
                dx, dy, dz = float(parts[1]), float(parts[2]), float(parts[3])
                deltas[idx] = np.array([dx, dy, dz], dtype=np.float32)
    return deltas

def normalize_mesh(verts):
    """Normalize mesh to [0,1] bounding box for correspondence."""
    mins = verts.min(axis=0)
    maxs = verts.max(axis=0)
    return (verts - mins) / (maxs - mins)

def build_correspondence(hm08_verts, bodyapps_verts):
    """Build KD-tree mapping from hm08 vertices to BodyApps nearest neighbors.
    Both meshes normalized to [0,1] bounding box first."""
    hm08_norm = normalize_mesh(hm08_verts)
    ba_norm = normalize_mesh(bodyapps_verts)
    tree = cKDTree(ba_norm)
    distances, indices = tree.query(hm08_norm)
    return indices, distances

def convert_target_to_morph(hm08_base, bodyapps_base, target_deltas, correspondence, num_bodyapps_verts):
    """Convert sparse hm08 target to dense BodyApps morph binary (absolute positions).

    The engine expects morph binaries to store ABSOLUTE positions (not deltas).
    On load, it computes: engineDelta = morphBinary - baseVertices.
    So we must output: baseVertices + mappedDelta.
    """
    # Apply deltas to hm08 base to get morphed mesh
    morphed = hm08_base.copy()
    for idx, delta in target_deltas.items():
        if idx < len(morphed):
            morphed[idx] += delta

    # Compute per-vertex delta (morphed - base) in hm08 space
    hm08_deltas = morphed - hm08_base

    # Map to BodyApps vertex ordering via correspondence
    bodyapps_deltas = np.zeros((num_bodyapps_verts, 3), dtype=np.float32)
    for hm08_idx, bodyapps_idx in enumerate(correspondence):
        if bodyapps_idx < num_bodyapps_verts:
            bodyapps_deltas[bodyapps_idx] = hm08_deltas[hm08_idx]

    # Return ABSOLUTE positions (base + delta) — engine will subtract base on load
    return bodyapps_base + bodyapps_deltas

def main():
    print("=== MakeHuman Target → BodyApps Binary Converter ===\n")

    # Load hm08 base mesh
    hm08_path = os.path.join(TARGETS_DIR, "hm08.obj")
    if not os.path.exists(hm08_path):
        print(f"ERROR: hm08.obj not found at {hm08_path}")
        sys.exit(1)

    hm08_verts = load_obj_vertices(hm08_path)
    print(f"hm08 base: {len(hm08_verts)} vertices")

    # Define targets to convert
    targets = {
        "ankle_round": {
            "incr": os.path.join(RAW_DIR, "ankle_incr.target.gz"),
            "decr": os.path.join(RAW_DIR, "ankle_decr.target.gz"),
        },
        "across_chest": {
            "incr": os.path.join(RAW_DIR, "bust_incr.target.gz"),
            "decr": os.path.join(RAW_DIR, "bust_decr.target.gz"),
        },
        "knee_round": {
            "incr": os.path.join(RAW_DIR, "knee_incr.target.gz"),
            "decr": os.path.join(RAW_DIR, "knee_decr.target.gz"),
        },
    }

    # Process each gender
    for gender in ["male", "female"]:
        print(f"\n--- {gender.upper()} ---")

        # Load BodyApps base pose
        bodyapps_base = load_bodyapps_binary(gender)
        print(f"BodyApps base: {bodyapps_base.shape}")

        # Build correspondence
        correspondence, distances = build_correspondence(hm08_verts, bodyapps_base)
        max_dist = distances.max()
        mean_dist = distances.mean()
        print(f"Correspondence: max_dist={max_dist:.4f}, mean_dist={mean_dist:.4f}")

        if max_dist > 0.5:
            print(f"WARNING: Large correspondence distance ({max_dist:.4f}). Results may be noisy.")

        # Convert each target
        for morph_name, files in targets.items():
            incr_deltas = load_target(files["incr"])
            decr_deltas = load_target(files["decr"])

            # Use incr as the morph (positive influence = larger measurement)
            morph_binary = convert_target_to_morph(
                hm08_verts, bodyapps_base, incr_deltas, correspondence, NUM_VERTS
            )

            # Save to staging directory
            staging_dir = os.path.join(SCRIPT_DIR, "staging", gender)
            os.makedirs(staging_dir, exist_ok=True)
            out_path = os.path.join(staging_dir, f"{morph_name}.bin")
            with open(out_path, 'wb') as f:
                f.write(morph_binary.tobytes())

            print(f"  {morph_name}: {len(incr_deltas)} deltas → {out_path} ({os.path.getsize(out_path)} bytes)")

    print("\n=== Done ===")
    print("Next: Append morphs to existing morph.bin files and update config.")

if __name__ == "__main__":
    main()
