"""
run_pipeline.py — Master orchestrator for the Blender cloth draping pipeline.

Usage:
  blender --background --python scripts/blender_drape_pipeline/run_pipeline.py

  With specific size:
  blender --background --python scripts/blender_drape_pipeline/run_pipeline.py -- --size M

  Export only (collects all cached .npy files):
  blender --background --python scripts/blender_drape_pipeline/run_pipeline.py -- --export-only
"""
import bpy
import numpy as np
import os
import sys
import time

# Add script dir to path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from config import SIZES, BASE_SIZE, GARMENTS_DIR, MAKEHUMAN_DIR, COLLISION_PARAMS
from import_body import load_makehuman_binary, create_blender_mesh, apply_morphs_to_verts, apply_height_scaling
from generate_sizes import create_collision_proxy
from garment_import import import_garment, position_garment_on_body
from cloth_sim import drape_garment_on_size
from export_gltf import build_morph_deltas, export_garment_with_morphs, save_morph_config


def clear_scene():
    """Remove all objects from the scene."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    # Clear orphan data
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)


def main():
    start_time = time.time()

    # Parse command line args (after --)
    argv = sys.argv
    garment_path = None
    target_size = None
    frame_count = None
    export_only = False

    if "--" in argv:
        args = argv[argv.index("--") + 1:]
        skip_next = False
        for i, arg in enumerate(args):
            if skip_next:
                skip_next = False
                continue
            if arg == "--size" and i + 1 < len(args):
                target_size = args[i+1]
                skip_next = True
            elif arg == "--frames" and i + 1 < len(args):
                frame_count = int(args[i+1])
                skip_next = True
            elif arg == "--export-only":
                export_only = True
            elif not arg.startswith("--") and garment_path is None:
                garment_path = arg

    if not garment_path:
        garment_path = os.path.join(GARMENTS_DIR, "atomic_jacket.glb")

    # Update frame count in config if provided
    if frame_count is not None:
        from config import CLOTH_PARAMS
        CLOTH_PARAMS["frame_count"] = frame_count

    garment_name = os.path.splitext(os.path.basename(garment_path))[0]
    output_path = os.path.join(GARMENTS_DIR, f"{garment_name}_morphed.glb")
    cache_dir = os.path.join(GARMENTS_DIR, "cache", garment_name)
    os.makedirs(cache_dir, exist_ok=True)

    # Determine which sizes to process
    sizes_to_process = SIZES
    if target_size:
        if target_size in SIZES:
            sizes_to_process = {target_size: SIZES[target_size]}
        else:
            print(f"ERROR: Size {target_size} not found in config.py")
            return

    print("=" * 60)
    print(f"BLENDER CLOTH DRAPING PIPELINE")
    print(f"Garment: {garment_path}")
    print(f"Output:  {output_path}")
    print(f"Sizes:   {list(sizes_to_process.keys())}")
    print(f"Mode:    {'EXPORT ONLY' if export_only else 'SIMULATE'}")
    print("=" * 60)

    # Step 0: Clear scene
    print("\n[0/5] Clearing scene...")
    clear_scene()

    # Step 1: Import MakeHuman body
    print("\n[1/5] Importing MakeHuman body...")
    gender = "male"
    base_verts, base_faces, morph_deltas, model = load_makehuman_binary(gender)
    print(f"  Loaded: {len(base_verts)} verts, {len(base_faces)} faces, {len(morph_deltas)} morphs")

    # Step 2: Generate body size variants
    print("\n[2/5] Generating body sizes...")
    body_objects = {}
    proxy_objects = {}

    for size_name, measurements in SIZES.items():
        # Apply morphs
        deformed = apply_morphs_to_verts(base_verts, morph_deltas, measurements,
                                          {k: v for k, v in [
                                              ("height", (0, 175, 195)),
                                              ("chest", (1, 96, 130)),
                                              ("waist", (8, 84, 140)),
                                              ("hips", (12, 96, 130)),
                                          ]})
        deformed = apply_height_scaling(measurements["height"], deformed)
        mesh = create_blender_mesh(deformed, base_faces, f"Body_{size_name}")
        obj = bpy.data.objects.new(f"Body_{size_name}", mesh)
        bpy.context.collection.objects.link(obj)
        body_objects[size_name] = obj
        proxy = create_collision_proxy(obj, COLLISION_PARAMS["target_faces"])
        proxy_objects[size_name] = proxy

    # Step 3: Import garment (Initial check)
    print(f"\n[3/5] Importing garment: {garment_path}")
    garment_obj = import_garment(garment_path)

    # Step 4: Drape or Load from Cache
    print(f"\n[4/5] Draping garment on sizes...")
    all_draped = {}

    for size_name in SIZES:
        cache_path = os.path.join(cache_dir, f"{size_name}.npy")

        # Load from cache if exists
        if os.path.exists(cache_path):
            print(f"  {size_name}: Loading from cache...")
            all_draped[size_name] = np.load(cache_path)
            continue

        # Skip if not in process list and not in cache
        if size_name not in sizes_to_process:
            continue
        if export_only:
            continue

        body_obj = body_objects[size_name]
        proxy_obj = proxy_objects[size_name]

        # Re-import garment for each size to ensure consistent starting mesh
        garment_obj = import_garment(garment_path)
        position_garment_on_body(garment_obj, body_obj, ease=1.08)

        # Before simulation check
        pre_pos = np.array([[v.co.x, v.co.y, v.co.z] for v in garment_obj.data.vertices])

        # Run cloth simulation
        draped = drape_garment_on_size(garment_obj, body_obj, size_name, proxy_obj=proxy_obj)
        if draped is not None:
            all_draped[size_name] = draped
            np.save(cache_path, draped)
            print(f"  {size_name}: Saved to cache.")

            diff = draped - pre_pos
            print(f"    Move: max={np.max(np.linalg.norm(diff, axis=1))*100:.1f}cm")

    if not all_draped:
        print("\nERROR: No sizes simulated or cached!")
        return

    # Step 5: Export
    print(f"\n[5/5] Exporting morph target GLB...")

    # Use first available size as base if BASE_SIZE not in all_draped
    export_base_size = BASE_SIZE if BASE_SIZE in all_draped else list(all_draped.keys())[0]
    base_positions = all_draped[export_base_size]

    # Build morph deltas
    morph_deltas = build_morph_deltas(base_positions, all_draped)

    # CRITICAL: Use the ALREADY POSITIONED object if possible, or re-import and reposition perfectly.
    # To be safe, we re-import but we MUST reposition it exactly as it was during simulation.
    garment_obj = import_garment(garment_path)
    position_garment_on_body(garment_obj, body_objects[export_base_size], ease=1.08)

    from cloth_sim import apply_scale_to_object, offset_garment_outward
    apply_scale_to_object(garment_obj)
    offset_garment_outward(garment_obj, offset_distance=0.01)

    # Set vertex positions to match base_positions (this is the Settled XXS shape)
    for i, v in enumerate(garment_obj.data.vertices):
        v.co.x = float(base_positions[i, 0])
        v.co.y = float(base_positions[i, 1])
        v.co.z = float(base_positions[i, 2])
    garment_obj.data.update()

    # Export
    # CRITICAL: Select ONLY the garment and hide/delete bodies to ensure clean GLB
    bpy.ops.object.select_all(action='DESELECT')
    garment_obj.select_set(True)
    bpy.context.view_layer.objects.active = garment_obj

    # Delete body objects before export
    for obj in body_objects.values():
        bpy.data.objects.remove(obj, do_unlink=True)
    for obj in proxy_objects.values():
        bpy.data.objects.remove(obj, do_unlink=True)

    export_garment_with_morphs(garment_obj, morph_deltas, output_path)
    save_morph_config(morph_deltas, output_path, garment_name)

    elapsed = time.time() - start_time
    print(f"\n{'=' * 60}")
    print(f"DONE — {elapsed:.1f}s total")
    print(f"Output: {output_path}")
    print(f"Morph targets: {len(morph_deltas)}")
    print(f"Sizes simulated: {list(all_draped.keys())}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
