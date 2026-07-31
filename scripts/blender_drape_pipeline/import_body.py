"""
01_import_body.py — Load MakeHuman body from binary files into Blender.

Reads: {gender}_vertices.bin, {gender}_faces.bin, {gender}_morphs.bin
Creates: Blender mesh in decimeters (native MakeHuman units)
"""
import bpy
import bmesh
import numpy as np
import json
import os
import sys

# Add parent dir to path for config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import MAKEHUMAN_DIR


def load_makehuman_binary(gender="male"):
    """Load MakeHuman body from binary files."""
    base = os.path.join(MAKEHUMAN_DIR, gender)

    verts = np.fromfile(
        os.path.join(base, f"{gender}_vertices.bin"), dtype=np.float32
    ).reshape(-1, 3)

    faces = np.fromfile(
        os.path.join(base, f"{gender}_faces.bin"), dtype=np.uint32
    ).reshape(-1, 3)

    config_path = os.path.join(MAKEHUMAN_DIR, "model_config.json")
    with open(config_path) as f:
        config = json.load(f)
    model = config["models"][gender]

    morph_count = model["morph_count"]
    vert_count = model["vert_count"]

    morphs_raw = np.fromfile(
        os.path.join(base, f"{gender}_morphs.bin"), dtype=np.float32
    )
    morphs = morphs_raw.reshape(morph_count, vert_count, 3)

    # Compute deltas from base pose
    morph_deltas = morphs - verts[np.newaxis, :, :]

    return verts, faces, morph_deltas, model


def create_blender_mesh(verts, faces, name="MakeHumanBody"):
    """Create Blender mesh from numpy arrays. Converts decimeters to meters and rotates to Z-up."""
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()

    # Convert decimeters to meters and rotate Y-up to Z-up
    # MakeHuman (X, Y, Z) where Y is up -> Blender (X, -Z, Y) where Z is up
    for v in verts:
        m_v = v * 0.1
        # Rotate: (x, y, z) -> (x, -z, y)
        # This keeps the model facing the camera in Blender
        bm.verts.new((m_v[0], -m_v[2], m_v[1]))

    bm.verts.ensure_lookup_table()
    for f in faces:
        try:
            bm.faces.new([bm.verts[int(i)] for i in f])
        except ValueError:
            continue

    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return mesh


def apply_morphs_to_verts(base_verts, morph_deltas, measurements, morph_map):
    """
    Convert measurements (cm) to morph influences, compute deformed vertices.

    Args:
        base_verts: np.array (V, 3) — base pose vertices
        morph_deltas: np.array (M, V, 3) — per-morph deltas
        measurements: dict — {measurement_name: value_cm}
        morph_map: dict — {measurement_name: (index, low_cm, high_cm)}

    Returns:
        np.array (V, 3) — deformed vertices
    """
    result = base_verts.copy()

    for name, (idx, low, high) in morph_map.items():
        value = measurements.get(name)
        if value is None or high <= low:
            continue

        # Clamp influence to [0, 1]
        influence = max(0.0, min(1.0, (value - low) / (high - low)))

        if abs(influence) > 1e-6:
            result += morph_deltas[idx] * influence

    return result


def apply_height_scaling(target_height_cm, vertices):
    """
    Scale vertices to match target height.
    Same logic as MakeHumanEngine._applyHeightScaling.
    """
    y_values = vertices[:, 1]
    body_min_y = y_values.min()
    body_max_y = y_values.max()
    body_height_dm = body_max_y - body_min_y

    if body_height_dm <= 0:
        return vertices

    body_height_cm = body_height_dm * 10
    height_scale = target_height_cm / body_height_cm

    # Scale Y relative to feet (minY stays fixed)
    result = vertices.copy()
    result[:, 1] = body_min_y + (y_values - body_min_y) * height_scale

    # Scale X/Z proportionally (from MakeHuman morph data: X/Y=0.33, Z/Y=0.22)
    xz_scale = 1.0 + (height_scale - 1.0) * 0.275  # average of 0.33 and 0.22
    center_x = (vertices[:, 0].min() + vertices[:, 0].max()) / 2
    center_z = (vertices[:, 2].min() + vertices[:, 2].max()) / 2
    result[:, 0] = center_x + (vertices[:, 0] - center_x) * xz_scale
    result[:, 2] = center_z + (vertices[:, 2] - center_z) * xz_scale

    return result


if __name__ == "__main__":
    gender = "male"
    verts, faces, morph_deltas, model = load_makehuman_binary(gender)
    print(f"[01] Loaded {gender}: {len(verts)} verts, {len(faces)} faces, {len(morph_deltas)} morphs")
    print(f"     Y range: [{verts[:,1].min():.2f}, {verts[:,1].max():.2f}] dm")
    print(f"     Height: {(verts[:,1].max() - verts[:,1].min()) * 10:.1f} cm")
