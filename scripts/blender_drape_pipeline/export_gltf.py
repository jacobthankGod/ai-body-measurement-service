"""
05_export_gltf.py — Export garment with morph targets to GLB.

Morph targets encode per-vertex position deltas from the base (XXS) drape.
Three.js loads these via GLTFLoader and exposes as mesh.morphTargetInfluences[].
"""
import bpy
import bmesh
import numpy as np
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import SIZES, BASE_SIZE, GARMENTS_DIR


def build_morph_deltas(base_positions, all_draped):
    """
    Compute morph deltas from base drape.

    Args:
        base_positions: np.array (V, 3) — base (XXS) drape positions
        all_draped: dict {size_name: np.array (V, 3)} — draped positions per size

    Returns:
        dict {morph_name: np.array (V, 3)} — deltas
    """
    morphs = {}

    for size_name, positions in all_draped.items():
        if size_name == BASE_SIZE:
            continue  # Base is the identity

        delta = positions - base_positions
        morph_name = f"draped_{size_name}"
        morphs[morph_name] = delta

        max_disp = np.max(np.abs(delta))
        rms = np.sqrt(np.mean(delta ** 2))
        print(f"  {morph_name}: max={max_disp*100:.1f}cm, rms={rms*100:.1f}cm")

    return morphs


def export_garment_with_morphs(garment_obj, morph_deltas, output_path):
    """
    Export garment GLB with morph targets.

    Blender's glTF exporter exports shape keys as morph targets.
    """
    bpy.context.view_layer.objects.active = garment_obj
    garment_obj.select_set(True)

    # Ensure we're in object mode
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    # Create basis shape key (base positions)
    if not garment_obj.data.shape_keys:
        basis = garment_obj.shape_key_add(name='Basis', from_mix=False)
        print(f"  Created Basis shape key")

    # Add morph targets as shape keys
    for morph_name, delta_arr in morph_deltas.items():
        sk = garment_obj.shape_key_add(name=morph_name, from_mix=False)

        # Set vertex positions = base + delta
        for i, v in enumerate(sk.data):
            v.co.x += float(delta_arr[i, 0])
            v.co.y += float(delta_arr[i, 1])
            v.co.z += float(delta_arr[i, 2])

        print(f"  Added shape key: {morph_name}")

    # Export to GLB
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)

    bpy.ops.export_scene.gltf(
        filepath=str(output_path),
        export_format='GLB',
        use_selection=True,  # Blender 5.x keyword for "Selected Only"
        export_morph=True,
        export_morph_normal=True,
        export_apply=True,
        export_texcoords=True,
        export_normals=True,
    )

    file_size = os.path.getsize(output_path)
    print(f"\n  Exported: {output_path}")
    print(f"  File size: {file_size / 1024 / 1024:.1f} MB")
    print(f"  Morph targets: {list(morph_deltas.keys())}")

    return output_path


def save_morph_config(morph_deltas, output_path, garment_name):
    """Save morph target metadata as JSON."""
    import json

    config = {
        "garment": garment_name,
        "base_size": BASE_SIZE,
        "morph_targets": {},
        "anchors": {}
    }

    for name, delta in morph_deltas.items():
        size_key = name.replace("draped_", "")
        config["morph_targets"][name] = {
            "size": size_key,
            "max_displacement_cm": float(np.max(np.abs(delta)) * 100),
        }

    for size_name, measurements in SIZES.items():
        config["anchors"][size_name] = measurements

    config_path = output_path.replace('.glb', '_config.json')
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    print(f"  Config: {config_path}")
    return config_path
