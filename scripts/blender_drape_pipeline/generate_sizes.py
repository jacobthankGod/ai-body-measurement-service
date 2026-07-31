"""
02_generate_body_sizes.py — Create 9 body size variants for cloth simulation.

For each size in SIZES:
1. Apply morph targets to create deformed body
2. Apply height scaling
3. Create Blender mesh + collision modifier
4. Decimate to collision proxy (~2000 faces)
"""
import bpy
import numpy as np
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import SIZES, BASE_SIZE, MALE_MORPH_MAP, COLLISION_PARAMS, MAKEHUMAN_DIR
from import_body import load_makehuman_binary, apply_morphs_to_verts, apply_height_scaling


def create_collision_proxy(body_obj, target_faces=2000):
    """
    Decimate body to a simplified collision proxy.
    Preserves outer silhouette while reducing collision detection time by ~13x.
    """
    proxy = body_obj.copy()
    proxy.data = body_obj.data.copy()
    proxy.name = f"{body_obj.name}_proxy"

    # Link to scene
    bpy.context.collection.objects.link(proxy)

    current_faces = len(proxy.data.polygons)
    if current_faces > target_faces:
        ratio = target_faces / current_faces
        mod = proxy.modifiers.new(name="Decimate", type='DECIMATE')
        mod.ratio = ratio
        mod.use_collapse_triangulate = True
        mod.use_symmetry = False

        bpy.context.view_layer.objects.active = proxy
        bpy.ops.object.modifier_apply(modifier="Decimate")

    # Add collision physics
    cp = proxy.modifiers.new(name="Collision", type='COLLISION')
    cp.settings.damping = COLLISION_PARAMS["damping"]
    cp.settings.friction_factor = COLLISION_PARAMS["friction_factor"]
    cp.settings.thickness_outer = COLLISION_PARAMS["thickness_outer"]
    cp.settings.thickness_inner = COLLISION_PARAMS["thickness_inner"]

    actual_faces = len(proxy.data.polygons)
    print(f"  Proxy: {actual_faces} faces (was {current_faces})")
    return proxy


def generate_all_sizes(gender="male"):
    """Generate all 9 body size variants as Blender objects."""
    print(f"\n[02] Generating {len(SIZES)} body sizes for {gender}...")

    base_verts, base_faces, morph_deltas, model = load_makehuman_binary(gender)
    morph_map = MALE_MORPH_MAP

    body_objects = {}
    proxy_objects = {}

    for size_name, measurements in SIZES.items():
        print(f"\n  === Size: {size_name} ===")
        print(f"  Measurements: chest={measurements['chest']}cm, waist={measurements['waist']}cm, hip={measurements['hip']}cm")

        # Apply morphs
        deformed = apply_morphs_to_verts(base_verts, morph_deltas, measurements, morph_map)

        # Apply height scaling
        deformed = apply_height_scaling(measurements["height"], deformed)

        # Create Blender mesh (in decimeters, same as MakeHuman)
        mesh = create_blender_mesh(deformed, base_faces, f"Body_{size_name}")
        obj = bpy.data.objects.new(f"Body_{size_name}", mesh)
        bpy.context.collection.objects.link(obj)

        body_objects[size_name] = obj

        # Create collision proxy
        proxy = create_collision_proxy(obj, COLLISION_PARAMS["target_faces"])
        proxy_objects[size_name] = proxy

        print(f"  Created: {size_name} (height={measurements['height']}cm)")

    return body_objects, proxy_objects


if __name__ == "__main__":
    body_objs, proxy_objs = generate_all_sizes("male")
    print(f"\n[02] Done: {len(body_objs)} bodies, {len(proxy_objs)} proxies")
