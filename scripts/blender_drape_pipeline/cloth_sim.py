"""
04_cloth_sim.py — Stability hardened cloth simulation.
"""
import bpy
import bmesh
import numpy as np
import os
import sys
import time

def apply_scale_to_object(obj):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    obj.select_set(False)

def setup_collision_body(body_obj):
    for mod in list(body_obj.modifiers):
        if mod.type == 'COLLISION':
            body_obj.modifiers.remove(mod)
    col_mod = body_obj.modifiers.new(name='ClothCollision', type='COLLISION')
    cs = col_mod.settings
    cs.thickness_outer = 0.01
    cs.thickness_inner = 0.01
    cs.damping = 0.5
    if hasattr(cs, "use_culling"): cs.use_culling = False

def setup_cloth_modifier(garment_obj, pin_group_name):
    for mod in list(garment_obj.modifiers):
        if mod.type == 'CLOTH':
            garment_obj.modifiers.remove(mod)
    cloth_mod = garment_obj.modifiers.new(name="ClothSim", type='CLOTH')
    s = cloth_mod.settings
    s.mass = 0.2
    s.quality = 10
    s.vertex_group_mass = pin_group_name
    s.effector_weights.gravity = 0.1 # Slow gravity

    # Stiffness
    s.tension_stiffness = 50.0
    s.compression_stiffness = 50.0
    s.shear_stiffness = 50.0
    s.bending_stiffness = 10.0

    cs = cloth_mod.collision_settings
    cs.use_collision = True
    cs.distance_min = 0.01
    cs.collision_quality = 10
    cs.use_self_collision = False
    cs.impulse_clamp = 0.01

    cache = cloth_mod.point_cache
    cache.frame_start = 1
    cache.frame_end = 20
    return cloth_mod

def bake_cloth_simulation(garment_obj, cloth_mod):
    cache = cloth_mod.point_cache
    try:
        with bpy.context.temp_override(scene=bpy.context.scene, active_object=garment_obj, point_cache=cache):
            bpy.ops.ptcache.bake(bake=True)
        return cache.is_baked
    except Exception: return False

def offset_garment_outward(garment_obj, offset_distance=0.05):
    verts = garment_obj.data.vertices
    # Get bounding box of vertices
    v_cos = np.array([[v.co.x, v.co.y, v.co.z] for v in verts])
    cx = (np.max(v_cos[:, 0]) + np.min(v_cos[:, 0])) / 2
    cy = (np.max(v_cos[:, 1]) + np.min(v_cos[:, 1])) / 2

    for v in verts:
        dir_x = v.co.x - cx
        dir_y = v.co.y - cy
        mag = (dir_x**2 + dir_y**2)**0.5
        if mag > 1e-6:
            v.co.x += (dir_x / mag) * offset_distance
            v.co.y += (dir_y / mag) * offset_distance
    garment_obj.data.update()
    print(f"  Offset garment from center by {offset_distance*100:.1f}cm")

def drape_garment_on_size(garment_obj, body_obj, size_name, proxy_obj=None):
    print(f"\n  === Simulating: {size_name} ===")
    sim_start = time.time()
    apply_scale_to_object(body_obj)
    apply_scale_to_object(garment_obj)

    # Use full body for stability
    collision_obj = body_obj
    setup_collision_body(collision_obj)
    offset_garment_outward(garment_obj, offset_distance=0.01) # 1cm

    # Pin top 10% (Z is height)
    for vg in list(garment_obj.vertex_groups):
        if vg.name == "PinGroup": garment_obj.vertex_groups.remove(vg)
    vg = garment_obj.vertex_groups.new(name="PinGroup")
    zs = [v.co.z for v in garment_obj.data.vertices]
    sorted_idx = sorted(range(len(zs)), key=lambda k: -zs[k])
    pin_indices = sorted_idx[:int(len(zs) * 0.1)]
    vg.add(pin_indices, 1.0, 'REPLACE')

    cloth_mod = setup_cloth_modifier(garment_obj, "PinGroup")
    success = bake_cloth_simulation(garment_obj, cloth_mod)
    if not success: return None

    bpy.context.scene.frame_set(20)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = garment_obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()
    final_positions = np.array([[v.co.x, v.co.y, v.co.z] for v in mesh.vertices])
    eval_obj.to_mesh_clear()

    for mod in list(garment_obj.modifiers):
        if mod.type in ['CLOTH', 'COLLISION']: garment_obj.modifiers.remove(mod)

    print(f"  [{size_name}] Done in {time.time() - sim_start:.1f}s")
    return final_positions
