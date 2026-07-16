import os
import sys
import pickle

# Patch chumpy for Python 3.11+ before it's imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import chumpy_patch  # noqa: F401 — patches inspect.getargspec

import chumpy as ch
import numpy as np
import cv2
from psbody.mesh import Mesh
from smpl_lib.ch_smpl import Smpl
from utils.smpl_paths import SmplPaths

import global_var


class SMPL4Garment(object):
    """SMPL class for garments."""
    def __init__(self, gender, body_only=False):
        self.gender = gender
        self._body_only = body_only
        smpl_model = SmplPaths(gender=gender).get_hres_smpl_model_data()
        self.smpl_base = Smpl(smpl_model)
        self._garment_loaded = False
        if not body_only:
            self._load_garment_data()

    def _load_garment_data(self):
        if self._garment_loaded:
            return
        with open(os.path.join(global_var.DATA_DIR, global_var.GAR_INFO_FILE), 'rb') as f:
            self.class_info = pickle.load(f)
        self.skirt_weight = ch.array(np.load(os.path.join(
            global_var.DATA_DIR, 'skirt_weight.npz'))['w'])
        self.skirt_skinning = self.skirt_weight.dot(self.smpl_base.weights)
        self._garment_loaded = True

    def run(self, beta=None, theta=None, garment_d=None, garment_class=None):
        """Outputs body and garment of specified garment class given theta, beta and displacements."""
        if garment_d is not None and garment_class is not None:
            self._load_garment_data()
        if beta is not None:
            self.smpl_base.betas[:beta.shape[0]] = beta
        else:
            self.smpl_base.betas[:] = 0
        if theta is not None:
            self.smpl_base.pose[:] = theta
        else:
            self.smpl_base.pose[:] = 0
        self.smpl_base.v_personal[:] = 0
        if garment_d is not None and garment_class is not None:
            if 'skirt' not in garment_class:
                vert_indices = self.class_info[garment_class]['vert_indices']
                f = self.class_info[garment_class]['f']
                self.smpl_base.v_personal[vert_indices] = garment_d
                garment_m = Mesh(v=self.smpl_base.r[vert_indices], f=f)
            else:
                # vert_indices = self.class_info[garment_class]['vert_indices']
                f = self.class_info[garment_class]['f']

                A = self.smpl_base.A.reshape((16, 24)).T
                skirt_V = self.skirt_skinning.dot(A).reshape((-1, 4, 4))

                verts = self.skirt_weight.dot(self.smpl_base.v_poseshaped)
                verts = verts + garment_d
                verts_h = ch.hstack((verts, ch.ones((verts.shape[0], 1))))
                verts = ch.sum(skirt_V * verts_h.reshape(-1, 1, 4), axis=-1)[:, :3]
                garment_m = Mesh(v=verts, f=f)
        else:
            garment_m = None
        self.smpl_base.v_personal[:] = 0
        body_m = Mesh(v=self.smpl_base.r, f=self.smpl_base.f)
        return body_m, garment_m


if __name__ == '__main__':
    gender = 'female'
    garment_class = 'skirt'
    shape_idx = '005'
    style_idx = '020'
    split = 'train'
    smpl = SMPL4Garment(gender)

    from dataset.static_pose_shape_final import OneStyleShape
    ds = OneStyleShape(garment_class, shape_idx, style_idx, split)
    K = 87
    verts_d, theta, beta, gamma, idx = ds[K]
    body_m, gar_m = smpl.run(theta=theta, beta=beta, garment_class=garment_class, garment_d=verts_d)
    gar_m.write_ply('/BS/cpatel/work/gar.ply')
    body_m.write_ply('/BS/cpatel/work/body.ply')
