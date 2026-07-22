"""TailorNet inference bridge — trimesh-based, no psbody.mesh or dataset dependency.

Usage:
    result = run_tailornet('t-shirt', 'male', betas=betas_10d)
    mesh = trimesh.Trimesh(vertices=result['garment_verts'], faces=result['garment_faces'])
"""
import os, sys, json, pickle, gc, logging
import numpy as np

logger = logging.getLogger("TAILORNET_BRIDGE")

# NumPy compat aliases (pre-1.24 chumpy compat)
np.bool = bool
np.int = int
np.float = float
np.complex = complex
np.object = object
np.str = str
np.unicode = str

import torch
import inspect

# Monkey-patch for chumpy compatibility with Python 3.11+
inspect.getargspec = inspect.getfullargspec

_BRIDGE_DIR = os.path.dirname(os.path.abspath(__file__))
TAILORNET_DIR = os.path.join(_BRIDGE_DIR, 'tailornet')
sys.path.insert(0, TAILORNET_DIR)
sys.path.insert(0, _BRIDGE_DIR)

import global_var as tn_gv
from tailornet_setup import TAILORNET_DATA_DIR, MODEL_WEIGHTS_PATH, SMPL_PATH_MALE, SMPL_PATH_FEMALE

tn_gv.DATA_DIR = TAILORNET_DATA_DIR
tn_gv.MODEL_WEIGHTS_PATH = MODEL_WEIGHTS_PATH
tn_gv.SMPL_PATH_MALE = SMPL_PATH_MALE
tn_gv.SMPL_PATH_FEMALE = SMPL_PATH_FEMALE
tn_gv.GAR_INFO_FILE = 'garment_class_info.pkl'
tn_gv.POSE_SPLIT_FILE = 'split_static_pose_shape.npz'

from models.networks import FullyConnected
from models import ops
from models.smpl4garment import SMPL4Garment


def _load_runner(ckpt_dir):
    """Load a trained MLP runner from a checkpoint directory.
    Infers input/output dimensions from checkpoint state dict since
    params.json does not always contain them."""
    with open(os.path.join(ckpt_dir, 'params.json')) as f:
        params = json.load(f)
    ckpt = os.path.join(ckpt_dir, 'lin.pth.tar')
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    state = torch.load(ckpt, map_location=device)
    input_size = state['net.0.weight'].shape[1]
    output_size = state['net.5.weight'].shape[0]
    model = FullyConnected(
        input_size=input_size,
        output_size=output_size,
        hidden_size=params.get('hidden_size', 1024),
        num_layers=params.get('num_layers', 3),
    )
    model.load_state_dict(state)
    model.eval()
    model.to(device)
    return model, params


class _TailorNetModel:
    """Mini reimplementation — load HF pivots one-at-a-time for memory efficiency."""

    def __init__(self, garment_class, gender):
        base = os.path.join(MODEL_WEIGHTS_PATH, f'{garment_class}_{gender}_weights')
        lf_dir = os.path.join(base, f'tn_orig_lf/{garment_class}_{gender}')
        ss2g_dir = os.path.join(base, f'tn_orig_ss2g/{garment_class}_{gender}')
        hf_base = os.path.join(base, f'tn_orig_hf/{garment_class}_{gender}')

        self.lf_model, _ = _load_runner(lf_dir)
        self.ss2g_model, _ = _load_runner(ss2g_dir)
        self.garment_class = garment_class

        self.hf_pivot_dirs = []
        if os.path.isdir(hf_base):
            for pd_name in sorted(os.listdir(hf_base)):
                pivot_dir = os.path.join(hf_base, pd_name)
                if os.path.isdir(pivot_dir):
                    self.hf_pivot_dirs.append(pivot_dir)

    @torch.no_grad()
    def forward(self, thetas, betas, gammas):
        import gc
        inp_type = type(thetas)
        if isinstance(thetas, np.ndarray):
            thetas = torch.from_numpy(thetas.astype(np.float32))
            betas = torch.from_numpy(betas.astype(np.float32))
            gammas = torch.from_numpy(gammas.astype(np.float32))

        device = next(self.lf_model.parameters()).device
        thetas = thetas.to(device)
        betas = betas.to(device)
        gammas = gammas.to(device)

        # LF: [thetas (72), betas (10), gammas (4)] → 86 dims
        lf_input = torch.cat([thetas, betas, gammas], dim=1)
        pred_lf = self.lf_model(lf_input).view(1, -1, 3)

        # HF: load one at a time, accumulate, free — OOM-safe on t3.micro
        masked_thetas = ops.mask_thetas(thetas, self.garment_class)
        hf_sum = None
        hf_count = 0
        for hf_dir in self.hf_pivot_dirs:
            rr, _ = _load_runner(hf_dir)
            out = rr(masked_thetas).view(1, -1, 3)
            if hf_sum is None:
                hf_sum = out
            else:
                hf_sum += out
            hf_count += 1
            del rr, out
            gc.collect()

        if hf_count > 0:
            pred_hf = hf_sum / hf_count
        else:
            pred_hf = torch.zeros_like(pred_lf)

        out = pred_lf + pred_hf
        if inp_type == np.ndarray:
            out = out.cpu().numpy()
        return out

    def cuda(self):
        pass

    def to(self, device):
        pass


def _remove_interpenetration(gar_verts, gar_faces, body_verts, body_faces, ww=2.0, eps=0.001):
    """Resolve body-garment interpenetration using trimesh proximity + sparse solve."""
    import trimesh
    import scipy.sparse as sp
    from scipy.sparse.linalg import spsolve

    body_mesh = trimesh.Trimesh(vertices=body_verts, faces=body_faces, process=False)
    prox = trimesh.proximity.ProximityQuery(body_mesh)
    closest, tri_idx, _ = prox.on_surface(gar_verts)
    tri_idx = np.asarray(tri_idx, dtype=np.int32)
    norms = body_mesh.face_normals[tri_idx]
    norms = norms / (np.linalg.norm(norms, axis=-1, keepdims=True) + 1e-10)

    direction = np.sign(np.sum((gar_verts - closest) * norms, axis=-1))
    idx = np.where(direction < 0)[0]
    if len(idx) == 0:
        return gar_verts

    pentgt = closest[idx] - gar_verts[idx]
    pentgt = closest[idx] + eps * pentgt / (np.linalg.norm(pentgt, axis=1, keepdims=True) + 1e-10)
    tgt = gar_verts.copy()
    tgt[idx] = ww * pentgt

    L = _laplacian(gar_verts, gar_faces)
    eye = sp.eye(gar_verts.shape[0], format='csr')
    eye.data[idx] *= ww
    A = sp.vstack([L, eye]).tocsr()
    b = np.vstack([L.dot(gar_verts), tgt])
    return spsolve(A.T.dot(A), A.T.dot(b))


def _laplacian(v, f):
    """Uniform laplacian via adjacency (no psbody.mesh dependency)."""
    n = v.shape[0]
    import scipy.sparse as sp
    rows, cols = [], []
    for i in range(3):
        rows.append(f[:, i])
        cols.append(f[:, (i + 1) % 3])
    rows = np.concatenate(rows)
    cols = np.concatenate(cols)
    adj = sp.csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n))
    adj = adj + adj.T
    adj.data = np.clip(adj.data, 0, 1)
    deg_inv = np.where(np.array(adj.sum(axis=1)).ravel() > 0, 1.0, 0)
    L = sp.diags(deg_inv) @ adj - sp.eye(n)
    return L.tocsr()


def run_tailornet(
    garment_class='t-shirt',
    gender='male',
    betas=None,
    thetas=None,
    gammas=None,
    remove_penetration=True,
    _cache=None,
):
    """Run TailorNet inference. Returns dict with garment_verts, garment_faces, body_verts, body_faces.
    Accepts 300-dim betas; passes first 10 to garment neural net (trained w/ 10 PCs),
    and all 300 to SMPL4Garment body model (uses dynamic shapedirs dim).
    """
    try:
        betas = np.asarray(np.zeros(300) if betas is None else betas, dtype=np.float32)
        thetas = np.asarray(np.zeros(72) if thetas is None else thetas, dtype=np.float32)
        gammas = np.asarray(np.zeros(4) if gammas is None else gammas, dtype=np.float32)

        # Check cache (keyed on garment_class + gender + betas hash)
        cache_key = (garment_class, gender, betas[:10].tobytes())
        if _cache is not None and cache_key in _cache:
            logger.info(f"TailorNet cache hit: {garment_class}_{gender}")
            return _cache[cache_key]

        # Garment neural net (SS2G) was trained on 10 betas + 4 gammas = 14-dim input
        betas_nn = betas[:10]
        model = _TailorNetModel(garment_class, gender)
        pred_disp = model.forward(thetas[None], betas_nn[None], gammas[None])[0]
        del model
        gc.collect()

        # SMPL body model uses dynamic shapedirs (now 300-dim)
        smpl = SMPL4Garment(gender)
        body_m, garment_m = smpl.run(beta=betas, theta=thetas, garment_class=garment_class, garment_d=pred_disp)

        body_verts = np.array(body_m.v, dtype=np.float32)
        body_faces = np.array(body_m.f, dtype=np.int32)
        garment_verts = np.array(garment_m.v, dtype=np.float32)
        garment_faces = np.array(garment_m.f, dtype=np.int32)

        if remove_penetration:
            garment_verts = _remove_interpenetration(garment_verts, garment_faces, body_verts, body_faces)

        result = dict(success=True, body_verts=body_verts, body_faces=body_faces,
                    garment_verts=garment_verts, garment_faces=garment_faces, error=None)

        # Store in cache (copy arrays to prevent mutation)
        if _cache is not None:
            _cache[cache_key] = {
                'success': True,
                'body_verts': body_verts.copy(),
                'body_faces': body_faces.copy(),
                'garment_verts': garment_verts.copy(),
                'garment_faces': garment_faces.copy(),
                'error': None,
            }
            if len(_cache) > 50:  # prevent unbounded growth
                oldest = next(iter(_cache))
                del _cache[oldest]

        return result

    except Exception as e:
        import traceback
        return dict(success=False, body_verts=None, body_faces=None,
                    garment_verts=None, garment_faces=None, error=f'{e}\n{traceback.format_exc()}')
