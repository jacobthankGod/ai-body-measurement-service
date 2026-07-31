"""
03_import_garment.py — Import garment mesh and position it on the body.

Handles multi-object joining, centering, and scaling.
"""
import bpy
import mathutils
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import GARMENTS_DIR


def import_garment(garment_path):
    """Import garment and JOIN all meshes into one cohesive object."""
    bpy.ops.object.select_all(action='DESELECT')

    # 1. Import
    ext = os.path.splitext(garment_path)[1].lower()
    if ext in ['.glb', '.gltf']:
        bpy.ops.import_scene.gltf(filepath=garment_path)
    elif ext == '.obj':
        bpy.ops.import_scene.obj(filepath=garment_path)
    else:
        raise ValueError(f"Unsupported format: {ext}")

    imported_meshes = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
    if not imported_meshes:
        raise ValueError("No meshes found in imported file")

    # 2. Bake hierarchy transforms into vertices for ALL parts
    bpy.context.view_layer.update()
    for obj in imported_meshes:
        world_mat = obj.matrix_world.copy()
        mesh = obj.data
        for v in mesh.vertices:
            v.co = world_mat @ v.co
        obj.matrix_world = mathutils.Matrix.Identity(4)
        obj.parent = None

    # 3. Join all meshes
    bpy.ops.object.select_all(action='DESELECT')
    for obj in imported_meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = imported_meshes[0]
    bpy.ops.object.join()

    garment_obj = bpy.context.active_object
    garment_obj.name = "Garment_Joined"

    # 4. Y-up -> Z-up rotation check
    ys = [v.co.y for v in garment_obj.data.vertices]
    zs = [v.co.z for v in garment_obj.data.vertices]
    if (max(ys) - min(ys)) > (max(zs) - min(zs)):
        print("    Rotating Joined Garment Y-up -> Z-up manually...")
        for v in garment_obj.data.vertices:
            old_y, old_z = v.co.y, v.co.z
            v.co.y = -old_z
            v.co.z = old_y

    nfaces = len(garment_obj.data.polygons)
    nverts = len(garment_obj.data.vertices)
    print(f"  Joined: {garment_obj.name} ({nfaces} faces, {nverts} verts)")
    return garment_obj


def position_garment_on_body(garment_obj, body_obj, ease=1.08):
    """Position joined garment on body torso with precise center-scale."""
    garment_obj.matrix_world = mathutils.Matrix.Identity(4)
    bpy.context.view_layer.update()

    # Body Metrics
    body_verts = [body_obj.matrix_world @ v.co for v in body_obj.data.vertices]
    b_min = mathutils.Vector((min(v.x for v in body_verts), min(v.y for v in body_verts), min(v.z for v in body_verts)))
    b_max = mathutils.Vector((max(v.x for v in body_verts), max(v.y for v in body_verts), max(v.z for v in body_verts)))
    body_cx = (b_min.x + b_max.x) / 2
    body_cy = (b_min.y + b_max.y) / 2
    body_height = b_max.z - b_min.z

    # Garment Metrics
    g_verts = [v.co for v in garment_obj.data.vertices]
    g_min = mathutils.Vector((min(v.x for v in g_verts), min(v.y for v in g_verts), min(v.z for v in g_verts)))
    g_max = mathutils.Vector((max(v.x for v in g_verts), max(v.y for v in g_verts), max(v.z for v in g_verts)))
    g_cx = (g_min.x + g_max.x) / 2
    g_cy = (g_min.y + g_max.y) / 2
    g_cz_min = g_min.z

    garment_width = g_max.x - g_min.x
    garment_depth = g_max.y - g_min.y

    # Calculate scale factor
    body_width = b_max.x - b_min.x
    body_depth = b_max.y - b_min.y
    scale_h = ((body_width * ease / garment_width) + (body_depth * ease / garment_depth)) / 2

    # Target: Torso (bottom of jacket at 55% of body height)
    target_z = b_min.z + body_height * 0.55

    print(f"    Positioning: scale={scale_h:.3f}, target_z={target_z:.3f}")

    # Transformation math: (v - centroid_xy) * scale + body_center_xy
    for v in garment_obj.data.vertices:
        # Scale & Center XY
        v.co.x = (v.co.x - g_cx) * scale_h + body_cx
        v.co.y = (v.co.y - g_cy) * scale_h + body_cy
        # Position Z (bottom to target)
        v.co.z = (v.co.z - g_cz_min) + target_z

    garment_obj.data.update()
    return garment_obj
