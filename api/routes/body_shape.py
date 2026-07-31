"""
Body Shape Computation Endpoint
================================
Server-side Anny blendshape evaluation.
Returns computed vertex positions as binary Float32Array.
"""
import struct
import numpy as np
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
import logging
import time

router = APIRouter()
logger = logging.getLogger("BODY_SHAPE")

_MODEL = None


def _load_model():
    """Load the pruned Anny phenotype binary once at startup."""
    global _MODEL
    if _MODEL is not None:
        return _MODEL

    bin_path = Path("public/models/anny/anny_phenotype.bin")
    if not bin_path.exists():
        raise FileNotFoundError(f"Binary not found: {bin_path}")

    data = bin_path.read_bytes()
    p = 0
    header = struct.unpack_from("<6I", data, p)
    p += 24
    version, V, C, M, F, _ = header

    template = np.frombuffer(data, dtype=np.float32, count=V * 3, offset=p).reshape(V, 3).copy()
    p += V * 3 * 4

    faces = np.frombuffer(data, dtype=np.uint32, count=F * 3, offset=p).reshape(F, 3).copy()
    p += F * 3 * 4

    mask = np.frombuffer(data, dtype=np.float32, count=C * M, offset=p).reshape(C, M).copy()
    p += C * M * 4

    bs16 = np.frombuffer(data, dtype=np.float16, count=C * V * 3, offset=p).reshape(C, V, 3)

    _MODEL = {
        "V": V, "C": C, "M": M, "F": F,
        "template": template,
        "faces": faces,
        "mask": mask,
        "bs16": bs16,
    }
    logger.info(f"Loaded Anny model: V={V}, C={C}, M={M}, F={F}")
    return _MODEL


def _f16_to_f32_array(arr):
    """Convert float16 numpy array to float32 via numpy (fast C loop)."""
    return arr.astype(np.float32)


def _linear_interp_coeffs(value, anchors):
    n = len(anchors)
    if value <= anchors[0]:
        out = np.zeros(n, dtype=np.float32)
        out[0] = 1.0
        return out
    if value >= anchors[-1]:
        out = np.zeros(n, dtype=np.float32)
        out[-1] = 1.0
        return out
    for i in range(n - 1):
        if anchors[i] <= value <= anchors[i + 1]:
            t = (value - anchors[i]) / (anchors[i + 1] - anchors[i])
            out = np.zeros(n, dtype=np.float32)
            out[i] = 1.0 - t
            out[i + 1] = t
            return out
    out = np.zeros(n, dtype=np.float32)
    out[-1] = 1.0
    return out


def _compute_blendshape_coefficients(params, model):
    """Product-of-experts coefficient computation.

    Column order MUST match the Anny model's PHENOTYPE_VARIATIONS:
      race(3), gender(2), age(5), muscle(3), weight(3),
      height(2), proportions(2), cupsize(3), firmness(3)
    Total = 26 dimensions.

    Formula: coeff = product over active mask columns of allVars[m].
    Unmasked dimensions get factor 1 (neutral), NOT (1 - allVars).
    """
    C = model["C"]
    M = model["M"]
    mask = model["mask"]

    african = params.get("african", 0)
    asian = params.get("asian", 0)
    caucasian = params.get("caucasian", 1)
    race_sum = african + asian + caucasian
    if race_sum < 1e-6:
        race_sum = 1

    all_vars = []

    # Race (3 dims) — FIRST, matches PHENOTYPE_VARIATIONS order
    all_vars.extend([african / race_sum, asian / race_sum, caucasian / race_sum])

    # Gender (2 dims)
    all_vars.extend(_linear_interp_coeffs(params.get("gender", 0.5), [0, 1]).tolist())

    # Age (5 dims)
    all_vars.extend(_linear_interp_coeffs(params.get("age", 0.5), [-1/3, 0, 1/3, 2/3, 1]).tolist())

    # Muscle (3 dims)
    all_vars.extend(_linear_interp_coeffs(params.get("muscle", 0.5), [0, 0.5, 1]).tolist())

    # Weight (3 dims)
    all_vars.extend(_linear_interp_coeffs(params.get("weight", 0.5), [0, 0.5, 1]).tolist())

    # Height (2 dims)
    all_vars.extend(_linear_interp_coeffs(params.get("height", 0.5), [0, 1]).tolist())

    # Proportions (2 dims)
    all_vars.extend(_linear_interp_coeffs(params.get("proportions", 0.5), [0, 1]).tolist())

    # Cupsize (3 dims)
    all_vars.extend(_linear_interp_coeffs(params.get("cupsize", 0.5), [0, 0.5, 1]).tolist())

    # Firmness (3 dims)
    all_vars.extend(_linear_interp_coeffs(params.get("firmness", 0.5), [0, 0.5, 1]).tolist())

    all_vars_arr = np.array(all_vars, dtype=np.float32)

    # Anny formula: mask=1 -> allVars (apply), mask=0 -> 1 (neutral/skip)
    use = np.where(mask > 0.5, all_vars_arr[None, :], 1.0)
    log_coeffs = np.log(np.clip(use, 1e-20, None)).sum(axis=1)
    coeffs = np.exp(log_coeffs).astype(np.float32)

    return coeffs


def _compute_vertices(params, model):
    """Compute final vertices from phenotype parameters."""
    coeffs = _compute_blendshape_coefficients(params, model)

    active_mask = np.abs(coeffs) > 1e-4
    active_indices = np.where(active_mask)[0]

    if len(active_indices) == 0:
        return model["template"].copy()

    V = model["V"]
    bs16 = model["bs16"]

    out = model["template"].copy()
    for c in active_indices:
        w = coeffs[c]
        bs = bs16[c].astype(np.float32)
        out += bs * w

    return out


class BodyShapeRequest(BaseModel):
    gender: Optional[float] = 0.0
    age: Optional[float] = 0.2
    muscle: Optional[float] = 0.5
    weight: Optional[float] = 0.5
    height: Optional[float] = 0.5
    proportions: Optional[float] = 0.5
    cupsize: Optional[float] = 0.0
    firmness: Optional[float] = 0.5
    african: Optional[float] = 0.0
    asian: Optional[float] = 0.0
    caucasian: Optional[float] = 1.0


@router.on_event("startup")
async def load_body_shape_model():
    try:
        _load_model()
    except Exception as e:
        logger.error(f"Failed to load body shape model: {e}")


@router.post("/body-shape/compute")
async def compute_body_shape(req: BodyShapeRequest):
    t0 = time.time()
    model = _load_model()

    params = req.dict()
    verts = _compute_vertices(params, model)

    verts_y = verts[:, 2].copy()
    verts_z = -verts[:, 1].copy()
    verts[:, 1] = verts_y
    verts[:, 2] = verts_z

    elapsed_ms = (time.time() - t0) * 1000

    return Response(
        content=verts.tobytes(),
        media_type="application/octet-stream",
        headers={
            "X-Compute-Ms": f"{elapsed_ms:.1f}",
            "X-Vertex-Count": str(model["V"]),
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.get("/body-shape/info")
async def body_shape_info():
    model = _load_model()
    return {
        "V": model["V"],
        "C": model["C"],
        "M": model["M"],
        "F": model["F"],
    }


@router.get("/body-shape/faces")
async def body_shape_faces():
    model = _load_model()
    return Response(
        content=model["faces"].tobytes(),
        media_type="application/octet-stream",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "public, max-age=86400",
        },
    )
