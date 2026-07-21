"""Generate missing garment_tmp.obj, garment_tmp_subdivide_uv_new.obj,
and spiral_indices_2.npy for each garment type in the GarmentRec dataset.

Uses the same approach as the Kaggle notebook: face topology comes from
tex_uv.pkl (faces_uvs), vertex positions from PCA mean, UV coords from verts_uvs.
"""

import argparse
import os
import sys
import numpy as np
import pickle
from collections import deque
from pathlib import Path


GARMENTS_META = [
    ("T-shirt", 1954),
    ("front_open_T-shirt", 1954),
    ("Shirt", 2468),
    ("front_open_Shirt", 2468),
    ("Shorts", 678),
    ("Pants", 1180),
]


def _check_pymeshlab():
    try:
        import pymeshlab
        ms = pymeshlab.MeshSet()
        ms.load_new_mesh = ms.load_new_mesh
        return True
    except Exception:
        return False


def generate_all_templates(tmps_dir: str):
    tmps_path = Path(tmps_dir)
    if not tmps_path.exists():
        print(f"ERROR: {tmps_dir} does not exist")
        return False

    pymeshlab_works = _check_pymeshlab()

    all_ok = True
    for gtype, vnum in GARMENTS_META:
        try:
            gar_dir = tmps_path / gtype
            if not gar_dir.exists():
                print(f"  Skipping {gtype}: directory not found")
                continue

            obj_path = gar_dir / "garment_tmp.obj"
            dense_obj_path = gar_dir / "garment_tmp_subdivide_uv_new.obj"
            spiral_path = gar_dir / "spiral_indices_2.npy"
            pca_path = gar_dir / "pca_data_64.npz"
            tex_uv_path = gar_dir / "tex_uv.pkl"

            cached = (
                obj_path.exists()
                and dense_obj_path.exists()
                and spiral_path.exists()
                and obj_path.stat().st_size > 0
            )
            if cached:
                print(f"{gtype}: templates cached")
                continue

            if not pca_path.exists() or not tex_uv_path.exists():
                print(f"  *** {gtype}: SKIPPING, base assets missing (PCA/UV) ***")
                continue

            print(f"Processing {gtype}...")

            pca = np.load(str(pca_path))
            verts = pca["mean"].reshape(-1, 3)

            with open(str(tex_uv_path), "rb") as f:
                tex_uv = pickle.load(f)
            fu = tex_uv["faces_uvs"]
            vu = tex_uv["verts_uvs"]
            faces_uvs = fu.numpy() if hasattr(fu, "numpy") else fu
            verts_uvs = vu.numpy() if hasattr(vu, "numpy") else vu

            with open(str(obj_path), "w") as f:
                for v in verts:
                    f.write(f"v {v[0]:.8f} {v[1]:.8f} {v[2]:.8f}\n")
                for vt in verts_uvs:
                    f.write(f"vt {vt[0]:.8f} {vt[1]:.8f}\n")
                for face in faces_uvs:
                    f.write(
                        f"f {face[0]+1}/{face[0]+1} {face[1]+1}/{face[1]+1} {face[2]+1}/{face[2]+1}\n"
                    )

            try:
                import trimesh as _tm_check
                _tm_mesh = _tm_check.load(str(obj_path), force="mesh")
                _tm_mesh.export(str(obj_path))
            except Exception:
                pass

            if pymeshlab_works:
                try:
                    import pymeshlab

                    ms = pymeshlab.MeshSet()
                    ms.load_new_mesh(str(obj_path))
                    _Threshold = getattr(pymeshlab, "PercentageValue", None) or getattr(
                        pymeshlab, "Percentage", None
                    )
                    ms.meshing_surface_subdivision_loop(
                        loopweight=0,
                        iterations=2,
                        threshold=_Threshold(0) if _Threshold else 0,
                    )
                    m = ms.current_mesh()
                    dense_verts = m.vertex_matrix()
                    dense_faces = m.face_matrix()
                    with open(str(dense_obj_path), "w") as f:
                        for v in dense_verts:
                            f.write(f"v {v[0]:.8f} {v[1]:.8f} {v[2]:.8f}\n")
                        if m.has_vertex_tex_coord():
                            vt = m.vertex_tex_coord_matrix()
                            for uv in vt:
                                f.write(f"vt {uv[0]:.8f} {uv[1]:.8f}\n")
                            for face in dense_faces:
                                f.write(
                                    f"f {face[0]+1}/{face[0]+1} {face[1]+1}/{face[1]+1} {face[2]+1}/{face[2]+1}\n"
                                )
                        else:
                            for face in dense_faces:
                                f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")
                    print(f"  {gtype}: pymeshlab subdivision OK ({len(dense_verts)} verts)")
                except Exception as _sub_e:
                    print(f"  pymeshlab subdivision failed: {_sub_e}, using trimesh fallback")
                    try:
                        import trimesh as _tm
                        _mesh = _tm.load(str(obj_path), force="mesh")
                        for _ in range(2):
                            _mesh = _mesh.subdivide()
                        _verts = _mesh.vertices
                        _faces = _mesh.faces
                        _c = _verts.mean(axis=0)
                        _, _, _Vt = np.linalg.svd(_verts - _c, full_matrices=False)
                        _uv = (_verts - _c) @ _Vt[:2].T
                        _uv -= _uv.min(axis=0)
                        _r = _uv.max(axis=0)
                        _r[_r < 1e-8] = 1.0
                        _uv /= _r
                        with open(str(dense_obj_path), "w") as f:
                            for v in _verts:
                                f.write(f"v {v[0]:.8f} {v[1]:.8f} {v[2]:.8f}\n")
                            for vt in _uv:
                                f.write(f"vt {vt[0]:.6f} {vt[1]:.6f}\n")
                            for face in _faces:
                                f.write(f"f {int(face[0])+1}/{int(face[0])+1} {int(face[1])+1}/{int(face[1])+1} {int(face[2])+1}/{int(face[2])+1}\n")
                        print(f"  {gtype}: trimesh subdivision OK ({len(_verts)} verts)")
                    except Exception as _tm_e:
                        print(f"  trimesh subdivision failed: {_tm_e}, copying base mesh")
                        import shutil as _sh
                        _sh.copy2(str(obj_path), str(dense_obj_path))
            else:
                try:
                    import trimesh as _tm
                    _mesh = _tm.load(str(obj_path), force="mesh")
                    for _ in range(2):
                        _mesh = _mesh.subdivide()
                    _verts = _mesh.vertices
                    _faces = _mesh.faces
                    _c = _verts.mean(axis=0)
                    _, _, _Vt = np.linalg.svd(_verts - _c, full_matrices=False)
                    _uv = (_verts - _c) @ _Vt[:2].T
                    _uv -= _uv.min(axis=0)
                    _r = _uv.max(axis=0)
                    _r[_r < 1e-8] = 1.0
                    _uv /= _r
                    with open(str(dense_obj_path), "w") as f:
                        for v in _verts:
                            f.write(f"v {v[0]:.8f} {v[1]:.8f} {v[2]:.8f}\n")
                        for vt in _uv:
                            f.write(f"vt {vt[0]:.6f} {vt[1]:.6f}\n")
                        for face in _faces:
                            f.write(f"f {int(face[0])+1}/{int(face[0])+1} {int(face[1])+1}/{int(face[1])+1} {int(face[2])+1}/{int(face[2])+1}\n")
                    print(f"  {gtype}: trimesh subdivision OK ({len(_verts)} verts)")
                except Exception as _tm_e:
                    print(f"  trimesh subdivision failed: {_tm_e}, copying base mesh")
                    import shutil as _sh
                    _sh.copy2(str(obj_path), str(dense_obj_path))

            V = verts.shape[0]
            faces_for_adj = np.array(faces_uvs, dtype=int)
            adj = {i: set() for i in range(V)}
            for face in faces_for_adj:
                for i in range(3):
                    for j in range(i + 1, 3):
                        v0, v1 = int(face[i]), int(face[j])
                        adj[v0].add(v1)
                        adj[v1].add(v0)
            max_neighbors = 20
            spiral = np.zeros((V, max_neighbors), dtype=np.int64)
            for v in range(V):
                seq = [v]
                visited = {v}
                q = deque([(nbr, 1) for nbr in sorted(adj[v])])
                visited.update(adj[v])
                seq.extend(sorted(adj[v]))
                while len(seq) < max_neighbors and q:
                    cur, dist = q.popleft()
                    for nbr in sorted(adj[cur]):
                        if nbr not in visited and len(seq) < max_neighbors:
                            visited.add(nbr)
                            seq.append(nbr)
                            q.append((nbr, dist + 1))
                while len(seq) < max_neighbors:
                    seq.append(v)
                spiral[v] = seq[:max_neighbors]
            np.save(str(spiral_path), spiral[np.newaxis, :, :])
            print(f"  {gtype}: Done (Spiral: {spiral.shape[0]}x{max_neighbors})")

        except Exception as e:
            print(f"  *** {gtype}: FAILED -> {e} ***")
            import traceback
            traceback.print_exc()
            all_ok = False

    print("GarmentRec templates: processing finished")
    return all_ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate missing GarmentRec template OBJ files + spiral indices"
    )
    parser.add_argument(
        "tmps_dir",
        type=str,
        help="Path to the tmps/ directory containing per-garment subdirectories",
    )
    args = parser.parse_args()

    print(f"GarmentRec template generator")
    print(f"  tmps_dir: {args.tmps_dir}")
    print()

    success = generate_all_templates(args.tmps_dir)
    sys.exit(0 if success else 1)
