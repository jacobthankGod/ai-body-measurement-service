#!/usr/bin/env python3
"""
MakeHuman binary model rebuild from source — body-only (no cloth).

Parses hm08.obj from the MakeHuman repository, filters out cloth geometry
(helper-tights, helper-skirt), and generates all binary files:
  - {gender}_vertices.bin (base mesh vertices)
  - {gender}_faces.bin (triangulated face indices)
  - {gender}_normals.bin (vertex normals)
  - {gender}_uvs.bin (UV coordinates)
  - {gender}_face_uv_idx.bin (UV indices per face vertex)
  - {gender}_morphs.bin (33 morph targets as absolute positions)
  - {gender}_face_mats.bin (material indices per face)
  - model_config.json (morph names, limits, mesh counts)

Source: github.com/makehumancommunity/makehuman (data/3dobjs/base.obj)
Targets: github.com/makehumancommunity/makehuman (data/targets/)

Usage:
    python3 scripts/build_model_from_source.py [--gender male|female|child]
"""

import os
import sys
import json
import numpy as np
from scipy.spatial import cKDTree

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)

# MakeHuman source paths
MH_SRC = "/tmp/makehuman-src"
MH_BASE_OBJ = os.path.join(MH_SRC, "makehuman/data/3dobjs/base.obj")
MH_TARGETS = os.path.join(MH_SRC, "makehuman/data/targets")

# Output directory — parent for both male/ and female/ subdirectories
OUT_DIR = os.path.join(BASE_DIR, "public/models/makehuman")

# Hand vertex detection
HAND_X_THRESHOLD = 3.5
HAND_Y_MIN = 9.0
HAND_Y_MAX = 11.0

# Cloth/non-body groups to REMOVE from the mesh
CLOTH_GROUPS = {
    "helper-tights", "helper-skirt", "helper-genital", "helper-hair",
    "helper-tongue", "helper-l-eye", "helper-r-eye",
    "helper-l-eyelashes-1", "helper-l-eyelashes-2",
    "helper-r-eyelashes-1", "helper-r-eyelashes-2",
    "helper-upper-teeth", "helper-lower-teeth",
}
# Also remove ALL joint-* groups (bone attachment cubes)
JOINT_PATTERN = "joint-"


# ---------------------------------------------------------------------------
# OBJ Parser with group tracking
# ---------------------------------------------------------------------------

def parse_obj(path):
    """Parse OBJ file into vertices, faces, UVs, and UV face indices.

    All faces are triangulated (quads → 2 tris using same split as Three.js).
    Returns face_groups: list of group names per face (before triangulation,
    so length matches raw_faces count).
    """
    raw_verts = []
    raw_uvs = []
    raw_faces = []      # list of [(v_idx, vt_idx), ...] per face
    face_groups = []    # group name per raw face
    current_group = "__default__"

    with open(path, 'r') as f:
        for line in f:
            if line.startswith('v '):
                parts = line.split()
                raw_verts.append([float(parts[1]), float(parts[2]), float(parts[3])])
            elif line.startswith('vt '):
                parts = line.split()
                raw_uvs.append([float(parts[1]), float(parts[2])])
            elif line.startswith('g ') or line.startswith('o '):
                current_group = line.split()[1]
            elif line.startswith('f '):
                parts = line.strip().split()[1:]
                face = []
                for p in parts:
                    idxs = p.split('/')
                    v_idx = int(idxs[0]) - 1
                    vt_idx = int(idxs[1]) - 1 if len(idxs) > 1 and idxs[1] else 0
                    face.append((v_idx, vt_idx))
                raw_faces.append(face)
                face_groups.append(current_group)

    verts = np.array(raw_verts, dtype=np.float32)
    uvs = np.array(raw_uvs, dtype=np.float32)

    # Triangulate: quads → 2 tris (same split order as Three.js: a,b,d + b,c,d)
    tri_v = []
    tri_uv = []
    tri_group = []
    for fi, face in enumerate(raw_faces):
        gname = face_groups[fi]
        n = len(face)
        if n == 3:
            tri_v.append([face[0][0], face[1][0], face[2][0]])
            tri_uv.append([face[0][1], face[1][1], face[2][1]])
            tri_group.append(gname)
        elif n == 4:
            a, b, c, d = face
            tri_v.append([a[0], b[0], d[0]])
            tri_uv.append([a[1], b[1], d[1]])
            tri_group.append(gname)
            tri_v.append([b[0], c[0], d[0]])
            tri_uv.append([b[1], c[1], d[1]])
            tri_group.append(gname)
        else:
            for i in range(1, n - 1):
                tri_v.append([face[0][0], face[i][0], face[i + 1][0]])
                tri_uv.append([face[0][1], face[i][1], face[i + 1][1]])
                tri_group.append(gname)

    faces = np.array(tri_v, dtype=np.uint32)
    face_uvs = np.array(tri_uv, dtype=np.uint32)

    return verts, faces, uvs, face_uvs, tri_group


# ---------------------------------------------------------------------------
# Normals computation
# ---------------------------------------------------------------------------

def compute_normals(verts, faces):
    """Compute smooth per-vertex normals from face normals."""
    normals = np.zeros_like(verts)

    for f in range(len(faces)):
        ia, ib, ic = faces[f]
        ax, ay, az = verts[ia]
        bx, by, bz = verts[ib]
        cx, cy, cz = verts[ic]

        ex, ey, ez = bx - ax, by - ay, bz - az
        fx, fy, fz = cx - ax, cy - ay, cz - az
        nx = ey * fz - ez * fy
        ny = ez * fx - ex * fz
        nz = ex * fy - ey * fx

        normals[ia] += [nx, ny, nz]
        normals[ib] += [nx, ny, nz]
        normals[ic] += [nx, ny, nz]

    lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    lengths[lengths == 0] = 1
    normals /= lengths

    return normals.astype(np.float32)


# ---------------------------------------------------------------------------
# Target file loader
# ---------------------------------------------------------------------------

def load_target(path):
    """Load sparse delta target file. Returns dict {vert_idx: (dx, dy, dz)}."""
    deltas = {}
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) == 4:
                idx = int(parts[0])
                dx, dy, dz = float(parts[1]), float(parts[2]), float(parts[3])
                deltas[idx] = np.array([dx, dy, dz], dtype=np.float32)
    return deltas


# ---------------------------------------------------------------------------
# Morph mapping
# ---------------------------------------------------------------------------

def get_morph_mapping():
    """Return ordered list of (morph_name, target_spec) for all 33 male morphs."""
    def t(subdir, name):
        return os.path.join(MH_TARGETS, subdir, name)

    return [
        ("height",            ("diff", t("macrodetails/height", "male-young-averagemuscle-averageweight-maxheight.target"),
                                    t("macrodetails/height", "male-young-averagemuscle-averageweight-minheight.target"))),
        ("chest",             ("single", t("measure", "measure-bust-circ-incr.target"))),
        ("neck",              ("single", t("measure", "measure-neck-circ-incr.target"))),
        ("neckheight",        ("single", t("measure", "measure-neck-height-incr.target"))),
        ("shoulders",         ("single", t("measure", "measure-shoulder-dist-incr.target"))),
        ("shoulder_slope",    ("single", t("torso", "torso-vshape-incr.target"))),
        ("bust_girth",        ("single", t("measure", "measure-underbust-circ-incr.target"))),
        ("stomach_form",      ("single", t("stomach", "stomach-pregnant-incr.target"))),
        ("waist",             ("single", t("measure", "measure-waist-circ-incr.target"))),
        ("arm_length",        ("single", t("measure", "measure-upperarm-length-incr.target"))),
        ("armgirth",          ("single", t("measure", "measure-upperarm-circ-incr.target"))),
        ("wrist_girth",       ("single", t("measure", "measure-wrist-circ-incr.target"))),
        ("hips",              ("single", t("measure", "measure-hips-circ-incr.target"))),
        ("hip_height",        ("single", t("measure", "measure-upperleg-height-incr.target"))),
        ("thigh_girth",       ("single", t("measure", "measure-thigh-circ-incr.target"))),
        ("lowerleg_length",   ("single", t("measure", "measure-lowerleg-height-incr.target"))),
        ("calf_girth",        ("single", t("measure", "measure-calf-circ-incr.target"))),
        ("ankle_round",       ("single", t("measure", "measure-ankle-circ-incr.target"))),
        ("across_chest",      ("single", t("measure", "measure-frontchest-dist-incr.target"))),
        ("knee_round",        ("single", t("measure", "measure-knee-circ-incr.target"))),
        ("across_back",       ("single", t("torso", "torso-scale-horiz-incr.target"))),
        ("across_shoulder",   ("single", t("measure", "measure-shoulder-dist-incr.target"))),
        ("elbow_round",       ("single", t("armslegs", "l-upperarm-scale-horiz-incr.target"))),
        ("inseam",            ("single", t("measure", "measure-upperleg-height-incr.target"))),
        ("trouser_waist",     ("single", t("measure", "measure-waist-circ-incr.target"))),
        ("crotch_depth",      ("single", t("measure", "measure-upperleg-height-incr.target"))),
        ("bust_point",        ("single", t("measure", "measure-frontchest-dist-incr.target"))),
        ("shoulder_to_bust",  ("single", t("measure", "measure-bust-circ-incr.target"))),
        ("back_waist_length", ("single", t("torso", "torso-scale-vert-incr.target"))),
        ("front_waist_length",("single", t("measure", "measure-napetowaist-dist-incr.target"))),
        ("high_bust",         ("single", t("breast", "breast-volume-vert-up.target"))),
        ("under_bust",        ("diff", t("measure", "measure-underbust-circ-incr.target"),
                                    t("measure", "measure-underbust-circ-decr.target"))),
        ("armhole_round",     ("single", t("armslegs", "l-upperarm-scale-horiz-incr.target"))),
    ]


def get_female_morph_mapping():
    """Return ordered list of (morph_name, target_spec) for all 35 female morphs.

    Includes all 33 male morphs (body measurements) plus 2 female-specific morphs:
      - breast_size: diff between maxcup-maxfirmness and mincup-minfirmness (creates breast protrusion)
      - buttocks_size: buttocks-volume-incr (creates buttocks volume)
    """
    male_morphs = get_morph_mapping()

    def t(subdir, name):
        return os.path.join(MH_TARGETS, subdir, name)

    female_extras = [
        # Breast size: diff isolates breast volume change while keeping other params constant
        ("breast_size", ("diff",
            t("breast", "female-young-averagemuscle-averageweight-maxcup-maxfirmness.target"),
            t("breast", "female-young-averagemuscle-averageweight-mincup-minfirmness.target"))),
        # Buttocks volume
        ("buttocks_size", ("single", t("buttocks", "buttocks-volume-incr.target"))),
    ]

    return male_morphs + female_extras


# ---------------------------------------------------------------------------
# Morph generation
# ---------------------------------------------------------------------------

def generate_morphs(hm08_verts, our_base, hand_mask, morph_mapping):
    """Generate all morph targets as dense absolute-position binary data."""
    num_morphs = len(morph_mapping)
    num_verts = len(our_base)

    # Build KD-tree correspondence once
    def normalize(v):
        mn = v.min(axis=0)
        mx = v.max(axis=0)
        return (v - mn) / (mx - mn)

    hm08_norm = normalize(hm08_verts)
    our_norm = normalize(our_base)
    tree = cKDTree(our_norm)
    distances, indices = tree.query(hm08_norm)
    print(f"  KD-tree: max_dist={distances.max():.4f} mean={distances.mean():.4f}")

    hand_indices = np.where(hand_mask)[0]

    morphs = np.zeros((num_morphs, num_verts, 3), dtype=np.float32)

    for i, (name, spec) in enumerate(morph_mapping):
        if spec[0] == "single":
            target_path = spec[1]
            deltas = load_target(target_path)

            morphed = hm08_verts.copy()
            for idx, d in deltas.items():
                if idx < len(morphed):
                    morphed[idx] += d

            hm08_delta = morphed - hm08_verts

            our_delta = np.zeros((num_verts, 3), dtype=np.float32)
            for hm08_i, our_i in enumerate(indices):
                if our_i < num_verts:
                    our_delta[our_i] = hm08_delta[hm08_i]

            morphs[i] = our_base + our_delta

        elif spec[0] == "diff":
            pos_path = spec[1]
            neg_path = spec[2]
            pos_deltas = load_target(pos_path)
            neg_deltas = load_target(neg_path)

            pos_morphed = hm08_verts.copy()
            for idx, d in pos_deltas.items():
                if idx < len(pos_morphed):
                    pos_morphed[idx] += d

            neg_morphed = hm08_verts.copy()
            for idx, d in neg_deltas.items():
                if idx < len(neg_morphed):
                    neg_morphed[idx] += d

            diff_delta = pos_morphed - neg_morphed

            our_delta = np.zeros((num_verts, 3), dtype=np.float32)
            for hm08_i, our_i in enumerate(indices):
                if our_i < num_verts:
                    our_delta[our_i] = diff_delta[hm08_i]

            morphs[i] = our_base + our_delta

        # Zero hand vertices
        if len(hand_indices) > 0:
            morphs[i][hand_mask] = our_base[hand_mask]

        # Stats
        delta = morphs[i] - our_base
        nz = np.any(delta != 0, axis=1).sum()
        mx = np.abs(delta).max()
        print(f"  [{i:2d}] {name:25s}  nz={nz:5d}  max={mx:.4f}")

    return morphs


# ---------------------------------------------------------------------------
# Cloth filtering
# ---------------------------------------------------------------------------

def filter_cloth(verts, faces, face_uvs, face_groups, tri_group):
    """Remove cloth faces (tights, skirt) and remap vertex indices.

    Returns filtered verts, faces, face_uvs, face_mats, and the old→new mapping.
    """
    orig_vert_count = len(verts)
    orig_face_count = len(faces)

    # Separate body vs cloth faces
    keep_mask = np.array([g not in CLOTH_GROUPS and not g.startswith(JOINT_PATTERN) for g in tri_group])
    remove_count = (~keep_mask).sum()
    print(f"  Cloth faces to remove: {remove_count} ({', '.join(sorted(CLOTH_GROUPS))})")
    print(f"  Body+helper faces to keep: {keep_mask.sum()}")

    # Keep non-cloth faces
    kept_faces = faces[keep_mask]
    kept_face_uvs = face_uvs[keep_mask]

    # Find which vertices are used by kept faces
    used_verts = np.unique(kept_faces.ravel())

    # Build old→new remapping table (-1 = not used)
    remap = np.full(orig_vert_count, -1, dtype=np.int32)
    remap[used_verts] = np.arange(len(used_verts), dtype=np.int32)

    # Remap face indices
    new_faces = remap[kept_faces].astype(np.uint32)

    # Remap vertex positions
    new_verts = verts[used_verts].astype(np.float32)

    # Filter UVs: find UVs actually used by kept face_uv_indices
    used_uvs = np.unique(kept_face_uvs.ravel())
    uv_remap = np.full(len(verts), -1, dtype=np.int32)  # approximate
    # UVs are indexed differently — just keep all UVs used by faces
    new_uv_indices = kept_face_uvs.copy()

    print(f"  Original: {orig_vert_count} verts, {orig_face_count} faces")
    print(f"  Filtered: {len(new_verts)} verts, {len(new_faces)} faces")
    print(f"  Vertices removed: {orig_vert_count - len(new_verts)}")
    print(f"  Faces removed: {orig_face_count - len(new_faces)}")

    # Remove degenerate (near-zero-area) faces that cause z-fighting artifacts
    v0 = new_verts[new_faces[:, 0]]
    v1 = new_verts[new_faces[:, 1]]
    v2 = new_verts[new_faces[:, 2]]
    cross = np.cross(v1 - v0, v2 - v0)
    areas = 0.5 * np.linalg.norm(cross, axis=1)
    degen_mask = areas > 5e-5
    n_degen = (~degen_mask).sum()
    if n_degen > 0:
        print(f"  Degenerate faces removed: {n_degen} (area < 5e-5)")
        new_faces = new_faces[degen_mask]
        new_uv_indices = new_uv_indices[degen_mask]
        # Some vertices may now be orphaned — rebuild remap
        used_v2 = np.unique(new_faces.ravel())
        remap2 = np.full(len(new_verts), -1, dtype=np.int32)
        remap2[used_v2] = np.arange(len(used_v2), dtype=np.int32)
        new_faces = remap2[new_faces].astype(np.uint32)
        new_verts = new_verts[used_v2]
        # Update remap: compose original remap with new remap
        # remap[orig_idx] → old_new_idx; remap2[old_new_idx] → final_new_idx
        # We need: final_remap[orig_idx] = remap2[remap[orig_idx]] if remap[orig_idx] >= 0
        final_remap = np.full(orig_vert_count, -1, dtype=np.int32)
        for i in range(orig_vert_count):
            if remap[i] >= 0 and remap2[remap[i]] >= 0:
                final_remap[i] = remap2[remap[i]]
        remap = final_remap
        used_verts = used_v2
        print(f"  After degenerate removal: {len(new_verts)} verts, {len(new_faces)} faces")

    return new_verts, new_faces, new_uv_indices, remap, used_verts


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_gender(gender, morph_mapping, hm08_verts, verts, faces, uvs, face_uv_idx,
                 normals, hand_mask, used_verts):
    """Build binary files for a single gender.

    Returns morph_names, display_names for config merging.
    """
    prefix = gender
    gender_dir = os.path.join(OUT_DIR, gender)
    os.makedirs(gender_dir, exist_ok=True)

    num_verts = len(verts)
    num_faces = len(faces)

    # Verify all target files exist
    missing = []
    for name, spec in morph_mapping:
        if spec[0] == "single":
            if not os.path.exists(spec[1]):
                missing.append(f"  {name}: {spec[1]}")
        elif spec[0] == "diff":
            for p in [spec[1], spec[2]]:
                if not os.path.exists(p):
                    missing.append(f"  {name}: {p}")
    if missing:
        print(f"ERROR [{gender}]: Missing target files:")
        for m in missing:
            print(m)
        sys.exit(1)

    print(f"  morphs: {len(morph_mapping)}")
    print(f"  all target files verified")

    # Generate morphs for full hm08 mesh first (19158 verts)
    print(f"  Generating morphs for full mesh...")
    full_morphs = generate_morphs(hm08_verts, hm08_verts, np.zeros(len(hm08_verts), dtype=bool), morph_mapping)

    # Remap morphs to filtered vertex set
    print(f"  Remapping morphs to filtered vertex set...")
    num_morphs = len(morph_mapping)
    num_new_verts = len(verts)
    morphs = np.zeros((num_morphs, num_new_verts, 3), dtype=np.float32)
    for i in range(num_morphs):
        morphs[i] = full_morphs[i][used_verts]

    print(f"  Morphs remapped: {num_morphs} × {num_new_verts} verts")

    # Amplify morphs for more visible effect
    base_verts = verts
    for i, (name, spec) in enumerate(morph_mapping):
        if gender == "female" and name == "breast_size":
            delta = morphs[i] - base_verts
            morphs[i] = base_verts + delta * 1.5
            mx = np.abs(delta * 1.5).max()
            print(f"  Amplified breast_size by 1.5x: max_delta={mx:.4f} ({mx*10:.1f}cm)")
        elif gender == "female" and name == "buttocks_size":
            delta = morphs[i] - base_verts
            morphs[i] = base_verts + delta * 6.0
            mx = np.abs(delta * 6.0).max()
            print(f"  Amplified buttocks_size by 6.0x: max_delta={mx:.4f} ({mx*10:.1f}cm)")

    # ---- Write binary files ----
    print(f"\n  Writing binary files to {gender_dir}")

    # vertices.bin
    v_path = os.path.join(gender_dir, f"{prefix}_vertices.bin")
    verts.tofile(v_path)
    print(f"    {os.path.basename(v_path)}: {os.path.getsize(v_path):,} bytes ({num_verts} verts)")

    # faces.bin
    f_path = os.path.join(gender_dir, f"{prefix}_faces.bin")
    faces.astype(np.uint32).tofile(f_path)
    print(f"    {os.path.basename(f_path)}: {os.path.getsize(f_path):,} bytes ({num_faces} tris)")

    # normals.bin
    n_path = os.path.join(gender_dir, f"{prefix}_normals.bin")
    normals.tofile(n_path)
    print(f"    {os.path.basename(n_path)}: {os.path.getsize(n_path):,} bytes")

    # uvs.bin
    all_used_uvs = np.unique(face_uv_idx.ravel())
    print(f"    UVs referenced by faces: {len(all_used_uvs)} / {len(uvs)}")

    uv_path = os.path.join(gender_dir, f"{prefix}_uvs.bin")
    uvs.astype(np.float32).tofile(uv_path)
    print(f"    {os.path.basename(uv_path)}: {os.path.getsize(uv_path):,} bytes ({len(uvs)} UVs)")

    # face_uv_idx.bin
    fuv_path = os.path.join(gender_dir, f"{prefix}_face_uv_idx.bin")
    face_uv_idx.astype(np.uint32).tofile(fuv_path)
    print(f"    {os.path.basename(fuv_path)}: {os.path.getsize(fuv_path):,} bytes")

    # morphs.bin
    m_path = os.path.join(gender_dir, f"{prefix}_morphs.bin")
    morphs.tofile(m_path)
    print(f"    {os.path.basename(m_path)}: {os.path.getsize(m_path):,} bytes ({len(morph_mapping)} morphs)")

    # face_mats.bin — all 0 (single material)
    fm_path = os.path.join(gender_dir, f"{prefix}_face_mats.bin")
    np.zeros(num_faces, dtype=np.uint8).tofile(fm_path)
    print(f"    {os.path.basename(fm_path)}: {os.path.getsize(fm_path):,} bytes")

    # ---- Validation ----
    print(f"\n  Validating {gender}...")
    v2 = np.fromfile(v_path, dtype=np.float32).reshape(num_verts, 3)
    m2 = np.fromfile(m_path, dtype=np.float32).reshape(len(morph_mapping), num_verts, 3)

    morph_names = [name for name, _ in morph_mapping]
    display_names = [n.replace('_', ' ').title() for n in morph_names]

    all_zero = 0
    for i, name in enumerate(morph_names):
        delta = m2[i] - v2
        nz = np.any(delta != 0, axis=1).sum()
        if nz == 0:
            print(f"    WARNING: {name} is all-zero (no effect)")
            all_zero += 1

    hand_contam = 0
    for i in range(len(morph_names)):
        delta = m2[i] - v2
        if np.abs(delta[hand_mask]).sum() > 1e-6:
            hand_contam += 1
            print(f"    HAND CONTAMINATION: {morph_names[i]}")

    if hand_contam == 0:
        print("    No hand contamination")

    # Check file sizes
    expected_sizes = {
        f"{prefix}_vertices.bin": num_verts * 3 * 4,
        f"{prefix}_faces.bin": num_faces * 3 * 4,
        f"{prefix}_normals.bin": num_verts * 3 * 4,
        f"{prefix}_uvs.bin": len(uvs) * 2 * 4,
        f"{prefix}_face_uv_idx.bin": num_faces * 3 * 4,
        f"{prefix}_morphs.bin": len(morph_mapping) * num_verts * 3 * 4,
        f"{prefix}_face_mats.bin": num_faces,
    }

    all_ok = True
    for fname, expected in expected_sizes.items():
        fpath = os.path.join(gender_dir, fname)
        actual = os.path.getsize(fpath)
        status = "OK" if actual == expected else "MISMATCH"
        if actual != expected:
            all_ok = False
        print(f"    {fname}: {actual:,} (expected {expected:,}) {status}")

    return morph_names, display_names, all_ok, all_zero, hand_contam


def main():
    print("=" * 60)
    print("MakeHuman Body-Only Model Rebuild from Source")
    print("  (cloth geometry removed: tights, skirt)")
    print("  Builds BOTH male and female binaries")
    print("=" * 60)

    # ---- Step 1: Parse hm08.obj with group tracking ----
    print(f"\n[1] Parsing {MH_BASE_OBJ}")
    if not os.path.exists(MH_BASE_OBJ):
        print(f"ERROR: base.obj not found. Run:")
        print(f"  git clone --depth=1 https://github.com/makehumancommunity/makehuman.git {MH_SRC}")
        sys.exit(1)

    hm08_verts, hm08_faces, hm08_uvs, hm08_face_uvs, tri_group = parse_obj(MH_BASE_OBJ)
    print(f"  vertices: {len(hm08_verts)}")
    print(f"  triangles: {len(hm08_faces)}")
    print(f"  UVs: {len(hm08_uvs)}")
    print(f"  groups: {len(set(tri_group))}")

    # Show group breakdown
    from collections import Counter
    group_counts = Counter(tri_group)
    for g, c in sorted(group_counts.items(), key=lambda x: -x[1]):
        marker = " [CLOTH]" if g in CLOTH_GROUPS else ""
        print(f"    {g}: {c} faces{marker}")

    # ---- Step 2: Use hm08 as base mesh ----
    print("\n[2] Using hm08 as base mesh")
    verts = hm08_verts
    faces = hm08_faces
    uvs = hm08_uvs
    face_uv_idx = hm08_face_uvs

    # ---- Step 3: Filter cloth ----
    print("\n[3] Filtering cloth geometry")
    new_verts, new_faces, new_face_uv_idx, remap, used_verts = filter_cloth(
        verts, faces, face_uv_idx, None, tri_group
    )
    verts = new_verts
    faces = new_faces
    face_uv_idx = new_face_uv_idx

    # ---- Step 4: Compute normals ----
    print("\n[4] Computing vertex normals")
    normals = compute_normals(verts, faces)
    print(f"  normals: {len(normals)}")

    # ---- Step 5: Detect hand vertices ----
    print("\n[5] Detecting hand vertices")
    x = np.abs(verts[:, 0])
    y = verts[:, 1]
    hand_mask = (x > HAND_X_THRESHOLD) & (y >= HAND_Y_MIN) & (y <= HAND_Y_MAX)
    hand_count = hand_mask.sum()
    print(f"  hand vertices: {hand_count}")
    if hand_count > 0:
        print(f"  X range: [{verts[hand_mask, 0].min():.2f}, {verts[hand_mask, 0].max():.2f}]")
        print(f"  Y range: [{verts[hand_mask, 1].min():.2f}, {verts[hand_mask, 1].max():.2f}]")

    # ---- Step 6: Build MALE model (34 morphs) ----
    print("\n[6] Building MALE model (34 morphs)")
    male_mapping = get_morph_mapping()
    os.makedirs(OUT_DIR, exist_ok=True)

    male_names, male_display, male_ok, male_zero, male_hand = build_gender(
        "male", male_mapping, hm08_verts, verts, faces, uvs, face_uv_idx,
        normals, hand_mask, used_verts
    )

    # ---- Step 7: Build FEMALE model (35 morphs) ----
    print("\n[7] Building FEMALE model (35 morphs)")
    female_mapping = get_female_morph_mapping()

    female_names, female_display, female_ok, female_zero, female_hand = build_gender(
        "female", female_mapping, hm08_verts, verts, faces, uvs, face_uv_idx,
        normals, hand_mask, used_verts
    )

    # ---- Step 8: Write merged model_config.json ----
    print("\n[8] Writing model_config.json (merged male + female)")

    # Morph limits (cm-based) — 33 base morphs (no fat)
    # Order: height, chest, neck, neckheight, shoulders, shoulder_slope, bust_girth,
    # stomach_form, waist, arm_length, armgirth, wrist_girth, hips, hip_height,
    # thigh_girth, lowerleg_length, calf_girth, ankle_round, across_chest, knee_round,
    # across_back, across_shoulder, elbow_round, inseam, trouser_waist,
    # crotch_depth, bust_point, shoulder_to_bust,
    # back_waist_length, front_waist_length, high_bust, under_bust, armhole_round
    base_default = [
        175, 96, 39, 28, 43, 1, 86, 82, 84, 62, 32, 17, 96, 28, 55, 116,
        36, 24, 41, 38, 39, 42, 25, 91, 84, 28, 7, 8,
        28, 28, 83, 73, 19
    ]
    base_low = [
        175, 96, 39, 28, 43, 1, 86, 55, 84, 62, 32, 17, 96, 28, 55, 116,
        36, 24, 41, 38, 39, 42, 25, 91, 84, 28, 7, 8,
        28, 28, 83, 73, 19
    ]
    base_high = [
        195, 130, 45, 36, 55, 2, 100, 140, 140, 80, 42, 22, 130, 38, 75, 130,
        48, 35, 55, 50, 55, 60, 35, 110, 150, 40, 12, 14,
        40, 40, 105, 95, 30
    ]

    # Female-specific limits: breast_size, buttocks_size
    female_default = base_default + [0, 0]
    female_low = base_low + [0, 0]
    female_high = base_high + [100, 100]

    config = {
        "version": 3,
        "source": "MakeHuman CC0 (github.com/makehumancommunity/makehuman)",
        "description": "Body-only mesh with skin textures (cloth removed) — male + female",
        "models": {
            "male": {
                "vert_count": len(verts),
                "face_count": len(faces),
                "morph_count": len(male_names),
                "morph_names": male_names,
                "display_names": male_display,
                "texture_path": "/models/makehuman/textures/male_diffuse.png",
                "morph_limits": {
                    "default": base_default,
                    "low": base_low,
                    "high": base_high
                }
            },
            "female": {
                "vert_count": len(verts),
                "face_count": len(faces),
                "morph_count": len(female_names),
                "morph_names": female_names,
                "display_names": female_display,
                "texture_path": "/models/makehuman/textures/female_diffuse.png",
                "morph_limits": {
                    "default": female_default,
                    "low": female_low,
                    "high": female_high
                }
            }
        }
    }

    cfg_path = os.path.join(BASE_DIR, "public/models/makehuman/model_config.json")
    with open(cfg_path, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"  model_config.json written (male={len(male_names)} morphs, female={len(female_names)} morphs)")

    # ---- Final summary ----
    print("\n" + "=" * 60)
    male_pass = male_ok and male_zero == 0 and male_hand == 0
    female_pass = female_ok and female_zero == 0 and female_hand == 0
    if male_pass and female_pass:
        print("BUILD SUCCESSFUL — both male and female")
    else:
        if not male_pass:
            print(f"MALE: {'WARNINGS' if male_ok else 'ERRORS'} (zero={male_zero}, hand={male_hand})")
        if not female_pass:
            print(f"FEMALE: {'WARNINGS' if female_ok else 'ERRORS'} (zero={female_zero}, hand={female_hand})")
    print("=" * 60)


if __name__ == "__main__":
    main()
