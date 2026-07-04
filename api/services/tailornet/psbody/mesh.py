"""psbody.mesh.Mesh compatibility layer using trimesh + numpy."""

import numpy as np
import trimesh


class Mesh:
    """Drop-in replacement for psbody.mesh.Mesh used by TailorNet.

    Supports:
        Mesh(v=verts, f=faces)
        mesh.v, mesh.f  (numpy arrays)
        mesh.write_ply(path)
        Mesh(filename=path)  (load from file)
    """

    def __init__(self, v=None, f=None, filename=None, _trimesh=None):
        if _trimesh is not None:
            self._tm = _trimesh
        elif filename:
            self._tm = trimesh.load(filename)
        else:
            if v is not None and f is not None:
                if hasattr(v, 'r'):
                    v = v.r
                self._tm = trimesh.Trimesh(
                    vertices=np.asarray(v, dtype=np.float32),
                    faces=np.asarray(f, dtype=np.int64),
                    process=False,
                )
            else:
                self._tm = trimesh.Trimesh(process=False)

    @property
    def v(self):
        return np.asarray(self._tm.vertices, dtype=np.float64)

    @v.setter
    def v(self, val):
        if hasattr(val, 'r'):
            val = val.r
        self._tm.vertices = np.asarray(val, dtype=np.float32)

    @property
    def f(self):
        return np.asarray(self._tm.faces, dtype=np.int64)

    @f.setter
    def f(self, val):
        self._tm.faces = np.asarray(val, dtype=np.int64)

    def write_ply(self, path):
        self._tm.export(path, file_type='ply')

    def show(self):
        self._tm.show()

    def keep_vertices(self, idx):
        """Return new Mesh keeping only specified vertex indices + their faces."""
        idx = np.asarray(idx)
        mask = np.zeros(self._tm.vertices.shape[0], dtype=bool)
        mask[idx] = True
        face_mask = np.all(mask[self._tm.faces], axis=1)
        new_faces = self._tm.faces[face_mask]
        # remap vertex indices
        new_verts = self._tm.vertices[idx]
        idx_map = {old: new for new, old in enumerate(idx)}
        remapped = np.array([
            [idx_map[v] for v in face]
            for face in new_faces
        ])
        return Mesh(v=new_verts, f=remapped)

    def __repr__(self):
        return (f'<psbody_shim.Mesh n_verts={self._tm.vertices.shape[0] if self._tm.vertices is not None else 0} '
                f'n_faces={self._tm.faces.shape[0] if self._tm.faces is not None else 0}>')
