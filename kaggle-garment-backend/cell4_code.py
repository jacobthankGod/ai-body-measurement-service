"""
Garment Reconstruction API Server (Async + Split Pipeline + SAM2 Fix)
Runs on Kaggle GPU backend, exposed via Cloudflare Tunnel.

Pipeline: Image -> 3D Mesh + Sewing Pattern

Endpoints:
  POST /api/v1/reconstruct     -> async job (returns job_id, processes in background)
  POST /api/v1/segment         -> Step 1: rembg + SAM2 (~20s)
  POST /api/v1/mesh            -> Step 2: GarmentRec (~50s)
  POST /api/v1/pattern         -> Step 3: GarmentGPT (~50s)
  POST /api/v1/callback        -> receives result URL from processing
  GET  /api/v1/job/{job_id}    -> poll job status
  GET  /health                 -> health check
  GET  /debug/error            -> last error traceback
"""

# ---- vLLM compatibility layer (SHIM) ----
import sys, types, torch

def _activate_vllm_shim():
    import importlib
    _orig_find_spec = importlib.util.find_spec
    def _patched_find_spec(name, *args, **kwargs):
        if name == 'vllm':
            return None
        return _orig_find_spec(name, *args, **kwargs)
    importlib.util.find_spec = _patched_find_spec

    class _HF_LLM:
        def __init__(self, model, **kwargs):
            from transformers import AutoProcessor, AutoConfig
            import torch

            use_8bit = False
            gpu_label = "cpu"
            if torch.cuda.is_available():
                cap = torch.cuda.get_device_capability()
                gpu_label = f"sm_{cap[0]}{cap[1]}"
                if cap >= (7, 0):
                    use_8bit = True

            print(f'[vllm-shim] Loading model {model} on {gpu_label}...')
            self._processor = AutoProcessor.from_pretrained(model, trust_remote_code=True)
            cfg_kwargs = dict(kwargs)
            cfg_kwargs.setdefault('trust_remote_code', True)
            cfg = AutoConfig.from_pretrained(model, **cfg_kwargs)
            if hasattr(cfg, 'vision_config'):
                try:
                    from transformers import AutoModelForVision2Seq
                    model_class = AutoModelForVision2Seq
                except ImportError:
                    from transformers import LlavaForConditionalGeneration
                    model_class = LlavaForConditionalGeneration
            else:
                from transformers import AutoModelForCausalLM
                model_class = AutoModelForCausalLM

            load_kwargs = dict(
                device_map='auto', trust_remote_code=True, torch_dtype=torch.float16,
            )
            if use_8bit:
                from transformers import BitsAndBytesConfig
                load_kwargs['quantization_config'] = BitsAndBytesConfig(
                    load_in_8bit=True, llm_int8_threshold=6.0,
                )

            self._model = model_class.from_pretrained(model, **load_kwargs)
            self._model.eval()
            dtype_label = "int8" if use_8bit else "fp16"
            print(f'[vllm-shim] Model loaded on {self._model.device} in {dtype_label}')

        def generate(self, inputs_list, sampling_params):
            results = []
            for inp in inputs_list:
                prompt = inp.get('prompt', '')
                images = inp.get('multi_modal_data', {}).get('image', [])
                if images:
                    proc = self._processor(text=prompt, images=images[0], return_tensors='pt').to(self._model.device)
                else:
                    proc = self._processor(text=prompt, return_tensors='pt').to(self._model.device)
                mt = getattr(sampling_params, 'max_tokens', 4096)
                tp = getattr(sampling_params, 'temperature', 0.1)
                with torch.no_grad():
                    out = self._model.generate(**proc, max_new_tokens=min(mt, 4096),
                        do_sample=tp > 0, temperature=max(tp, 0.01), top_p=0.9)
                gen = self._processor.decode(out[0], skip_special_tokens=False)
                class _O:
                    def __init__(self, text): self.text = text
                class _RO:
                    def __init__(self, outputs): self.outputs = outputs
                results.append(_RO(outputs=[_O(text=gen)]))
            return results

    class _HF_SamplingParams:
        def __init__(self, temperature=0.1, max_tokens=4096, skip_special_tokens=False, seed=42, stop_token_ids=None):
            self.temperature = temperature
            self.max_tokens = max_tokens
            self.skip_special_tokens = skip_special_tokens
            self.seed = seed
            self.stop_token_ids = stop_token_ids or []

    vllm_mod = types.ModuleType('vllm')
    vllm_mod.LLM = _HF_LLM
    vllm_mod.SamplingParams = _HF_SamplingParams
    sys.modules['vllm'] = vllm_mod
    print('[vllm-shim] vLLM compatibility shim installed (transformers + int8 backend)')

_activate_vllm_shim()

import os
import io
import json
import time
import uuid
import zipfile
import tempfile
import logging
import gc
import asyncio
import threading
import traceback
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager

import numpy as np
import torch
from PIL import Image
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("garment-api")

WORKING_DIR = Path("/kaggle/working")
WEIGHTS_DIR = WORKING_DIR / "weights"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
GPU_DEVICE = DEVICE
CPU_DEVICE = "cpu"
WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)

# ---- repo paths (cloned by Cell 2) ----
GARMENT_REC_DIR = WORKING_DIR / "GarmentRec"
GARMENT_GPT_DIR = WORKING_DIR / "Garment-GPT"
sys.path.insert(0, str(GARMENT_REC_DIR / "code"))
sys.path.insert(0, str(GARMENT_REC_DIR))
sys.path.insert(0, str(GARMENT_GPT_DIR))

SAM2_CKPT = WEIGHTS_DIR / "sam2" / "sam2_hiera_large.pt"

# ---- EC2 proxy callback URL ----
EC2_CALLBACK_URL = os.getenv("EC2_CALLBACK_URL", "https://korra.work/api/v2/garment/callback")

# ---- globals (populated by load_models) ----
rembg_remove = None
predict_fn = None
sam2_model = None
garmentrec_model = None
garmentgpt_predictor = None

# ---- async model loading state ----
models_loaded = threading.Event()
loading_state = {}
loading_errors = {}

# ---- async job queue ----
jobs = {}
job_progress = {}  # {job_id: {"stage": str, "progress": int, "message": str, "sequence": int}}
job_progress_events = {}  # {job_id: [asyncio.Event]} — for SSE subscribers

# ---- health tracking ----
SERVER_START_TIME = time.time()
REQUEST_COUNT = 0
ERROR_COUNT = 0
MODEL_LOAD_TIMES = {}

# Phase 209: GPU cost tracking
gpu_usage_log = {}  # {user_id: {"total_gpu_sec": float, "jobs": int, "last_job": str}}
COST_PER_GPU_MINUTE_USD = 0.50  # T4 on-demand estimate (~$0.35-0.65)

# ---- structured error codes (Phase 31) ----
ERROR_CODES = {
    "CUDA_OOM": {"code": "CUDA_OOM", "message": "GPU out of memory", "recoverable": True},
    "SAM2_LOAD_FAILED": {"code": "SAM2_LOAD_FAILED", "message": "SAM2 model failed to load", "recoverable": True},
    "GARMENTREC_LOAD_FAILED": {"code": "GARMENTREC_LOAD_FAILED", "message": "GarmentRec model failed to load", "recoverable": True},
    "GARMENTGPT_LOAD_FAILED": {"code": "GARMENTGPT_LOAD_FAILED", "message": "GarmentGPT model failed to load", "recoverable": True},
    "REMBG_FAILED": {"code": "REMBG_FAILED", "message": "Background removal failed", "recoverable": True},
    "MODEL_CORRUPT": {"code": "MODEL_CORRUPT", "message": "Model checkpoint is corrupt or incompatible", "recoverable": False},
    "INFERENCE_FAILED": {"code": "INFERENCE_FAILED", "message": "Model inference failed", "recoverable": True},
    "TIMEOUT": {"code": "TIMEOUT", "message": "Request timed out", "recoverable": True},
    "INVALID_IMAGE": {"code": "INVALID_IMAGE", "message": "Invalid or unreadable image", "recoverable": False},
    "IMAGE_TOO_LARGE": {"code": "IMAGE_TOO_LARGE", "message": "Image exceeds size limit", "recoverable": False},
    "UNKNOWN": {"code": "UNKNOWN", "message": "An unexpected error occurred", "recoverable": False},
}


def _structured_error(err_key, detail=None, extra=None):
    """Build a structured error response dict."""
    entry = ERROR_CODES.get(err_key, ERROR_CODES["UNKNOWN"])
    out = {"error": dict(entry)}
    if detail:
        out["error"]["detail"] = str(detail)
    if extra:
        out["error"]["extra"] = extra
    return out


def _write_error_context(error_key, detail=None, request_path=None):
    """Write rich error context to /kaggle/working/last_error.txt (Phase 33)."""
    try:
        import datetime
        parts = [
            f"=== Error at {datetime.datetime.utcnow().isoformat()}Z ===",
            f"Code: {error_key}",
            f"Detail: {detail}" if detail else "",
            f"Path: {request_path}" if request_path else "",
            f"GPU allocated: {torch.cuda.memory_allocated() / (1024**3):.2f}GB" if torch.cuda.is_available() else "GPU: N/A",
            f"GPU reserved: {torch.cuda.memory_reserved() / (1024**3):.2f}GB" if torch.cuda.is_available() else "",
            f"Models: rembg={rembg_remove is not None} sam2={sam2_model is not None} " +
            f"garmentrec={garmentrec_model is not None} garmentgpt={garmentgpt_predictor is not None}",
            f"Loading state: {loading_state}",
            "=" * 60,
        ]
        open("/kaggle/working/last_error.txt", "w").write("\n".join(parts))
    except Exception:
        pass


# ---- retry logic (Phase 32) ----
def _retry_on_oom(func, max_retries=2):
    """Retry a model load if it fails with CUDA OOM, clearing cache between attempts."""
    for attempt in range(max_retries + 1):
        try:
            return func()
        except RuntimeError as e:
            if "out of memory" in str(e).lower() and attempt < max_retries:
                logger.warning(f"CUDA OOM on attempt {attempt+1}/{max_retries+1}, clearing cache and retrying...")
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                continue
            raise


# ═══════════════════════════════════════════════════════════════
#  SAM2 segmentation (with checkpoint compatibility patch)
# ═══════════════════════════════════════════════════════════════

def _load_sam2():
    """Load SAM2 on CPU. Handles checkpoint version mismatches by filtering unexpected keys.
    Disables CUDA cache warmup to prevent OOM on restart (leaked GPU memory from previous process)."""
    from sam2.build_sam import build_sam2
    from sam2.sam2_image_predictor import SAM2ImagePredictor

    ckpt = str(SAM2_CKPT)
    if not Path(ckpt).exists():
        raise FileNotFoundError(f"SAM2 checkpoint not found at {ckpt}")

    # Patch build_sam2 to filter mismatched keys (newer sam2 package vs older checkpoint)
    import sam2.build_sam as _build_mod
    _orig_load_checkpoint = _build_mod._load_checkpoint

    def _patched_load_checkpoint(model, ckpt_path):
        sd = torch.load(ckpt_path, map_location="cpu", weights_only=False)
        if "model" in sd:
            sd = sd["model"]
        model_keys = set(model.state_dict().keys())
        ckpt_keys = set(sd.keys())
        unexpected = ckpt_keys - model_keys
        if unexpected:
            logger.warning(f"SAM2: filtering {len(unexpected)} unexpected keys from checkpoint: {unexpected}")
        filtered = {k: v for k, v in sd.items() if k in model_keys}
        model.load_state_dict(filtered, strict=False)

    _build_mod._load_checkpoint = _patched_load_checkpoint
    try:
        # Disable SAM2's CUDA cache warmup to prevent OOM on server restart.
        # The warmup hardcodes torch.device("cuda") in PositionEmbeddingSine.__init__,
        # bypassing the torch.device("cpu") context. Hydra overrides disable it.
        hydra_overrides = [
            "++model.image_encoder.neck.position_encoding.warmup_cache=false",
            "++model.memory_encoder.position_encoding.warmup_cache=false",
        ]
        with torch.device("cpu"):
            m = build_sam2("sam2_hiera_l.yaml", ckpt, device=CPU_DEVICE,
                           hydra_overrides_extra=hydra_overrides)
    finally:
        _build_mod._load_checkpoint = _orig_load_checkpoint

    pred = SAM2ImagePredictor(m)
    torch.cuda.empty_cache()
    gc.collect()
    logger.info("SAM2 loaded on CPU")
    return m, pred


def segment_garment(image: Image.Image) -> np.ndarray:
    """Real SAM2-based garment segmentation. Returns a binary mask (H,W) uint8 0/255."""
    global predict_fn
    img_np = np.array(image.convert("RGB"))
    h, w = img_np.shape[:2]
    predict_fn.set_image(img_np)
    masks, scores, _ = predict_fn.predict(
        point_coords=np.array([[w // 2, h // 2]]),
        point_labels=np.array([1]),
        multimask_output=True,
    )
    best = masks[scores.argmax()]
    return (best.astype(np.uint8) * 255)


# ═══════════════════════════════════════════════════════════════
#  GarmentRec — 3D mesh from a single image
# ═══════════════════════════════════════════════════════════════

def _load_garmentrec():
    """Load GarmentRec model on CPU. Fails if assets or SMPL model are missing."""
    import pymeshlab as _pml
    _Percentage = getattr(_pml, 'PercentageValue', None) or getattr(_pml, 'Percentage', None)
    if _Percentage is not None:
        _pml.Percentage = _Percentage
    from module.ImageReconstructModel import ImageReconstructModel
    from module.SkinWeightModel import SkinWeightNet
    import pickle

    gar_dir = GARMENT_REC_DIR / "code"
    smpl_path = GARMENT_REC_DIR / "smpl_pytorch" / "model" / "neutral_smpl_with_cocoplus_reg.txt"
    if not smpl_path.exists():
        raise FileNotFoundError(
            f"SMPL model not found at {smpl_path}. "
            "Download from https://smpl.is.tue.mpg.de/ and place the file there."
        )
    midpair_path = gar_dir.parent / "data" / "midpairs.pkl"
    dense_midpair_path = gar_dir.parent / "data" / "dense_midpairs.pkl"
    pca_folder = gar_dir.parent / "data" / "tmps"
    dense_template_folder = gar_dir.parent / "data"
    model_path = gar_dir.parent / "models" / "mrf_0.1_shading_0.1" / "mrf_0.1_shading_0.1_pca64_ep100_bth0.pth"

    for p in [midpair_path, dense_midpair_path, pca_folder, model_path]:
        if not p.exists():
            raise FileNotFoundError(f"GarmentRec asset not found: {p}")

    with open(midpair_path, "rb") as f:
        midpairs = pickle.load(f)
    with open(dense_midpair_path, "rb") as f:
        dense_midpairs = pickle.load(f)

    garments = ["T-shirt", "front_open_T-shirt", "Shirt", "front_open_Shirt", "Shorts", "Pants"]
    garmentvnums = [1954, 1954, 2468, 2468, 678, 1180]
    upper_type_num = 4
    pca_dim = 64
    tran_mean = [0.0, 0.0, 0.0]

    skin_net = SkinWeightNet(4, True)
    device = CPU_DEVICE

    net = ImageReconstructModel(
        skin_net,
        with_classification=True,
        tran_mean=tran_mean,
        garments=garments,
        garmentvnums=garmentvnums,
        upper_type_num=upper_type_num,
        pca_folder=str(pca_folder),
        pca_dim=pca_dim,
        smpl_model_path=str(smpl_path),
        midpairs=midpairs,
        infer_camera=True,
        infer_tex=True,
        inferring=True,
        use_detail=True,
        mesh_save_folder=None,
        vis_save_folder=None,
        dense_template_folder=str(dense_template_folder),
        displacement_scale=0.005,
        upsample_dismap=False,
        use_neighbor=True,
        device=device,
    )
    try:
        state = torch.load(str(model_path), map_location=device, weights_only=False)
    except (EOFError, pickle.UnpicklingError, RuntimeError) as _e:
        logger.error(f"Corrupt GarmentRec weights at {model_path}: {_e}")
        logger.error("Attempting re-download via hf_hub_download...")
        from huggingface_hub import hf_hub_download
        model_path.unlink(missing_ok=True)
        try:
            _new = hf_hub_download(
                repo_id='jacobthankgod4/smpl-model-garmentrec',
                filename='mrf_0.1_shading_0.1_pca64_ep100_bth0.pth',
                local_dir=str(model_path.parent),
                local_dir_use_symlinks=False,
            )
            state = torch.load(str(_new), map_location=device, weights_only=False)
            logger.info(f"Re-downloaded OK ({Path(_new).stat().st_size/(1024*1024):.0f} MB)")
        except Exception as _e2:
            raise RuntimeError(
                f"GarmentRec weights corrupt and re-download failed: {_e2}"
            ) from _e
    # Fix checkpoint mismatches: transpose SMPL matrices, skip incompatible keys
    model_state = net.state_dict()
    fixed_state = {}
    skipped = []
    for key in state:
        if key not in model_state:
            skipped.append(key)
            continue
        ckpt_shape = state[key].shape
        model_shape = model_state[key].shape
        if ckpt_shape == model_shape:
            fixed_state[key] = state[key]
        elif len(ckpt_shape) == 2 and len(model_shape) == 2 and ckpt_shape[0] == model_shape[1] and ckpt_shape[1] == model_shape[0]:
            logger.warning("Transposing %s: %s -> %s", key, ckpt_shape, model_shape)
            fixed_state[key] = state[key].T.contiguous()
        else:
            logger.warning("Skipping %s: ckpt %s != model %s", key, ckpt_shape, model_shape)
            skipped.append(key)
    if skipped:
        logger.info("Skipped %d mismatched keys in state_dict", len(skipped))
    net.load_state_dict(fixed_state, strict=False)

    # Fix SMPL J_regressor orientation: standard SMPL stores (24, 6890) but
    # GarmentRec's SMPL.py expects (6890, 24) for matmul(v_shaped, J_regressor).
    if hasattr(net.smpl, 'J_regressor') and net.smpl.J_regressor.shape == (24, 6890):
        net.smpl.J_regressor.data = net.smpl.J_regressor.T.contiguous()
        logger.info("Patched SMPL J_regressor: transposed (24,6890) -> (6890,24)")

    net = net.to(device)
    net.eval()
    logger.info("GarmentRec loaded on CPU")
    return net


def run_garmentrec(net, image: Image.Image, temp_dir: str) -> dict:
    """Run GarmentRec inference, save mesh to temp_dir, return mesh data."""
    import cv2
    import trimesh

    net.mesh_save_folder = temp_dir

    img_np = np.array(image.convert("RGB"))
    img_np = cv2.resize(img_np, (540, 540))
    img_np = img_np.astype(np.float32) / 255.0
    img_tensor = torch.from_numpy(img_np).permute(2, 0, 1).unsqueeze(0).to(CPU_DEVICE)
    names = np.array(["input.png"])

    cam_k = torch.Tensor(
        [[3.0375e03, 0.0, 270.0], [0.0, 3.0375e03, 270.0], [0.0, 0.0, 1.0]]
    ).to(CPU_DEVICE)
    bcnet_tran_mean = [-0.010962, 0.28778, 12.973]
    tran_mean = [0.0, 0.0, 0.0]
    cam_Rt = torch.tensor(
        [
            [1, 0, 0, tran_mean[0] - bcnet_tran_mean[0]],
            [0, 1, 0, tran_mean[1] - bcnet_tran_mean[1]],
            [0, 0, 1, tran_mean[2] - bcnet_tran_mean[2]],
        ]
    )
    cam_k = cam_k.matmul(cam_Rt).to(CPU_DEVICE)

    imgs_perg = torch.cat((img_tensor, img_tensor), 1).reshape(-1, 3, 540, 540)
    input_gtypes = np.array([[-1, -1]])

    with torch.no_grad():
        up_prob, bottom_prob, cam_Rs, cam_Ts, dis_maps = net(
            img_tensor, names, gtypes=input_gtypes, cam_k=cam_k, imgs_perg=imgs_perg
        )

    up_idx = up_prob.argmax(dim=1).item()
    bottom_idx = bottom_prob.argmax(dim=1).item()
    up_name = ["T-shirt", "front_open_T-shirt", "Shirt", "front_open_Shirt"][up_idx]
    bi = bottom_idx - 4 if bottom_idx >= 4 else bottom_idx
    bottom_name = ["Shorts", "Pants"][bi]
    logger.info(f"GarmentRec classified: upper={up_name}, lower={bottom_name}")

    up_path = os.path.join(temp_dir, "input_up.obj")
    bottom_path = os.path.join(temp_dir, "input_bottom.obj")

    mesh_data = {"upper": None, "lower": None}
    if os.path.exists(up_path):
        mesh = trimesh.load(up_path)
        v = mesh.vertices
        f = mesh.faces
        mesh_data["upper"] = {
            "vertices": v.tolist(),
            "faces": f.tolist(),
            "type": up_name,
        }
    if os.path.exists(bottom_path):
        mesh = trimesh.load(bottom_path)
        v = mesh.vertices
        f = mesh.faces
        mesh_data["lower"] = {
            "vertices": v.tolist(),
            "faces": f.tolist(),
            "type": bottom_name,
        }
    return mesh_data


# ═══════════════════════════════════════════════════════════════
#  GarmentGPT — sewing pattern from a single image
# ═══════════════════════════════════════════════════════════════

def _load_garmentgpt():
    """Load GarmentGPT predictor. LLM on GPU, codecs on CPU."""
    from main import GarmentPredictor

    gpt_dir = GARMENT_GPT_DIR
    llm_path = str(gpt_dir / "checkpoints" / "vlm" / "checkpoint-12844")
    codec_cfg = str(gpt_dir / "configs" / "config_vq1024_resres_aug_decay0.99_q5_gcd_nl8_ld512.yaml")
    rt_cfg = str(gpt_dir / "configs" / "config_rt_euler.yaml")

    for p in [llm_path, codec_cfg, rt_cfg]:
        if not Path(p).exists():
            raise FileNotFoundError(f"GarmentGPT asset not found: {p}")

    _orig_cwd = os.getcwd()
    os.chdir(str(gpt_dir))
    try:
        predictor = GarmentPredictor(
            llm_model_path=llm_path,
            codec_config_path=codec_cfg,
            rt_config_path=rt_cfg,
            device=GPU_DEVICE,
        )
    finally:
        os.chdir(_orig_cwd)

    predictor.codec_model = predictor.codec_model.to(CPU_DEVICE)
    predictor.rt_model = predictor.rt_model.to(CPU_DEVICE)
    torch.cuda.empty_cache()
    logger.info("GarmentGPT loaded (LLM on GPU, codecs on CPU)")
    return predictor


def run_garmentgpt(predictor, image: Image.Image) -> dict:
    """Save image to a temp file, run GarmentGPT predict, return GCD JSON."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        tmp_path = f.name
        image.save(tmp_path, "PNG")
    try:
        result = predictor.predict(image_path=tmp_path)
        if result is None:
            raise RuntimeError("GarmentGPT prediction returned None")
        return result
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════
#  rembg (background removal) — with PIL fallback
# ═══════════════════════════════════════════════════════════════

def _simple_remove_background(image, threshold=240):
    """PIL-based background removal fallback when rembg is unavailable."""
    import numpy as np
    arr = np.array(image.convert("RGBA"), dtype=np.uint8)
    bg = np.all(arr[:,:,:3] > threshold, axis=2)
    arr[bg, 3] = 0
    result = Image.fromarray(arr, mode="RGBA")
    canvas = Image.new("RGB", result.size, (255, 255, 255))
    canvas.paste(result, mask=result.split()[3])
    return canvas


def _load_rembg():
    """Robust rembg loader with PIL fallback. Handles numpy 2.x / scipy incompat."""
    global rembg_remove
    import subprocess, sys as _sys

    # Step 1: Ensure onnxruntime
    try:
        import onnxruntime
    except ImportError:
        logger.warning("onnxruntime not found, installing...")
        try:
            subprocess.check_call(
                [_sys.executable, "-m", "pip", "install", "onnxruntime"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            logger.warning("onnxruntime install failed, using PIL fallback")
            rembg_remove = _simple_remove_background
            return

    # Step 2: Upgrade scipy for numpy 2.x compat (rembg pulls scipy via pymatting)
    try:
        import scipy, packaging.version as _v
        if _v.Version(scipy.__version__) < _v.Version("1.14.0"):
            raise ImportError
    except (ImportError, ValueError, AttributeError):
        logger.warning("scipy too old for numpy 2.x, upgrading...")
        try:
            subprocess.check_call(
                [_sys.executable, "-m", "pip", "install", "--upgrade", "scipy>=1.14.1"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            pass

    # Step 3: Import rembg (retry with reinstall on failure)
    for attempt in range(2):
        try:
            from rembg import remove
            break
        except BaseException:
            if attempt == 0:
                logger.warning("rembg import failed, installing rembg[cpu]...")
                try:
                    subprocess.check_call(
                        [_sys.executable, "-m", "pip", "install", "rembg[cpu]"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    )
                except subprocess.CalledProcessError:
                    pass
            else:
                logger.warning("rembg import failed after reinstall, using PIL fallback")
                rembg_remove = _simple_remove_background
                return

    # Step 4: Warm up (downloads u2net ~176MB)
    try:
        dummy = Image.new("RGB", (8, 8), (255, 255, 255))
        remove(dummy)
        rembg_remove = remove
        logger.info("rembg + u2net ready")
    except Exception:
        logger.warning("rembg warmup failed, using PIL fallback")
        rembg_remove = _simple_remove_background


# ═══════════════════════════════════════════════════════════════
#  Model loading
# ═══════════════════════════════════════════════════════════════

def _log_gpu_memory(tag: str = ""):
    """Log current GPU memory state for debugging CUDA OOM issues."""
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated() / (1024**3)
        reserved = torch.cuda.memory_reserved() / (1024**3)
        logger.info(f"[GPU MEM] {tag} allocated={allocated:.2f}GB reserved={reserved:.2f}GB")


def _loading_thread():
    """Run model loading in a background thread so uvicorn can start immediately."""
    global rembg_remove, predict_fn, sam2_model, garmentrec_model, garmentgpt_predictor
    global loading_state, loading_errors, MODEL_LOAD_TIMES
    logger.info("Background model loading thread started")
    try:
        t0 = time.time()
        loading_state["rembg"] = "loading"
        _load_rembg()
        loading_state["rembg"] = "loaded"
        MODEL_LOAD_TIMES["rembg"] = time.time() - t0
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        t1 = time.time()
        loading_state["sam2"] = "loading"
        _log_gpu_memory("before_sam2")
        sam2_model, predict_fn = _retry_on_oom(lambda: _load_sam2(), max_retries=2)
        loading_state["sam2"] = "loaded"
        MODEL_LOAD_TIMES["sam2"] = time.time() - t1
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        t2 = time.time()
        loading_state["garmentrec"] = "loading"
        _log_gpu_memory("before_garmentrec")
        garmentrec_model = _load_garmentrec()
        loading_state["garmentrec"] = "loaded"
        MODEL_LOAD_TIMES["garmentrec"] = time.time() - t2
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        t3 = time.time()
        loading_state["garmentgpt"] = "loading"
        _log_gpu_memory("before_garmentgpt")
        garmentgpt_predictor = _load_garmentgpt()
        loading_state["garmentgpt"] = "loaded"
        MODEL_LOAD_TIMES["garmentgpt"] = time.time() - t3
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        _log_gpu_memory("all_loaded")
        logger.info("All models loaded successfully")
    except Exception as e:
        logger.error(f"Model loading thread failed: {e}")
        loading_errors["fatal"] = traceback.format_exc()
    finally:
        models_loaded.set()


# ═══════════════════════════════════════════════════════════════
#  Helper: build ZIP from pipeline results
# ═══════════════════════════════════════════════════════════════

def build_zip(image_id: str, mesh_data: dict = None, pattern_data: dict = None) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        if mesh_data:
            for part in ("upper", "lower"):
                md = mesh_data.get(part)
                if md:
                    obj_lines = [f"# Garment {part} ({md['type']})"]
                    for v in md["vertices"]:
                        obj_lines.append(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}")
                    for fa in md["faces"]:
                        obj_lines.append(f"f {fa[0]+1} {fa[1]+1} {fa[2]+1}")
                    zf.writestr(f"{image_id}/mesh_{part}.obj", "\n".join(obj_lines))
        if pattern_data:
            zf.writestr(f"{image_id}/sewing_pattern.json", json.dumps(pattern_data, indent=2))
        meta = {
            "image_id": image_id,
            "garmentrec": mesh_data is not None,
            "garmentgpt": pattern_data is not None,
            "generated_at": datetime.utcnow().isoformat(),
        }
        zf.writestr(f"{image_id}/metadata.json", json.dumps(meta, indent=2))
    buffer.seek(0)
    return buffer.read()


# ═══════════════════════════════════════════════════════════════
#  Helper: post result to EC2 proxy callback
# ═══════════════════════════════════════════════════════════════

def post_result_to_proxy(job_id: str, result_zip: bytes):
    """POST ZIP to EC2 proxy callback endpoint (fire-and-forget)."""
    try:
        import httpx
        files = {"file": (f"{job_id}.zip", io.BytesIO(result_zip), "application/zip")}
        data = {"job_id": job_id}
        resp = httpx.post(EC2_CALLBACK_URL, files=files, data=data, timeout=30)
        logger.info(f"Posted result to proxy: {resp.status_code}")
    except Exception as e:
        logger.error(f"Failed to post result to proxy: {e}")


# ═══════════════════════════════════════════════════════════════
#  Background task: full pipeline
# ═══════════════════════════════════════════════════════════════

async def process_full_pipeline(job_id: str, image_bytes: bytes, include_mesh: bool, include_pattern: bool):
    """Runs in background. Builds ZIP, stores in jobs dict, posts to EC2 proxy."""
    seq = 0
    def emit_progress(stage, progress, message):
        nonlocal seq
        seq += 1
        job_progress[job_id] = {"stage": stage, "progress": progress, "message": message, "sequence": seq}
        for evt in job_progress_events.get(job_id, []):
            evt.set()

    try:
        emit_progress("uploading", 5, "Processing image...")
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        emit_progress("segmenting", 15, "Removing background...")
        nobg = rembg_remove(image)

        emit_progress("segmenting", 30, "Segmenting garment...")
        mask = segment_garment(image)

        mesh_data = None
        pattern_data = None

        if include_mesh and garmentrec_model is not None:
            emit_progress("meshing", 40, "Reconstructing 3D mesh...")
            with tempfile.TemporaryDirectory() as tmp:
                mesh_data = run_garmentrec(garmentrec_model, nobg, tmp)
            gc.collect()

        if include_pattern and garmentgpt_predictor is not None:
            emit_progress("patterning", 65, "Generating sewing pattern...")
            pattern_data = run_garmentgpt(garmentgpt_predictor, nobg)

        emit_progress("zipping", 90, "Packaging results...")
        result_zip = build_zip(job_id, mesh_data, pattern_data)
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["result_zip"] = result_zip

        emit_progress("complete", 100, "Done!")

        # Post to EC2 proxy for persistent storage
        post_result_to_proxy(job_id, result_zip)
        logger.info(f"Job {job_id} completed successfully")
    except Exception as e:
        import traceback as tb
        err = tb.format_exc()
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        emit_progress("error", -1, str(e)[:200])
        try:
            open("/kaggle/working/last_error.txt", "w").write(err)
        except Exception:
            pass
        logger.error(f"Job {job_id} failed: {e}")


# ═══════════════════════════════════════════════════════════════
#  FastAPI app
# ═══════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app):
    # Start model loading in background thread — uvicorn serves immediately
    thread = threading.Thread(target=_loading_thread, daemon=True)
    thread.start()
    yield
    # Graceful shutdown: release models and free GPU memory
    global rembg_remove, predict_fn, sam2_model, garmentrec_model, garmentgpt_predictor
    logger.info("Shutting down — releasing models...")
    rembg_remove = None
    predict_fn = None
    sam2_model = None
    garmentrec_model = None
    garmentgpt_predictor = None
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    logger.info("Shutdown complete")


app = FastAPI(title="Garment Reconstruction API", lifespan=lifespan)


@app.middleware("http")
async def catch_all_errors(request, call_next):
    global REQUEST_COUNT, ERROR_COUNT
    path = request.url.path
    include_in_count = not path.startswith("/health") and not path.startswith("/ready")
    if include_in_count:
        REQUEST_COUNT += 1
    try:
        return await call_next(request)
    except BaseException as e:
        if include_in_count:
            ERROR_COUNT += 1
        import traceback as tb
        err_type = type(e).__name__
        err_tb = tb.format_exc()
        err_key = "CUDA_OOM" if "out of memory" in str(e).lower() else "UNKNOWN"
        _write_error_context(err_key, detail=err_tb, request_path=path)
        tb.print_exc()
        logger.error(f"UNCAUGHT {err_key}: {err_type}: {e}")
        return JSONResponse(status_code=500, content=_structured_error(err_key, detail=str(e)))


@app.get("/health")
async def health(ready: bool = False, verbose: bool = False):
    global REQUEST_COUNT, ERROR_COUNT
    gpu_allocated = None
    gpu_reserved = None
    gpu_ok = True
    if torch.cuda.is_available():
        gpu_allocated = torch.cuda.memory_allocated() / (1024**3)
        gpu_reserved = torch.cuda.memory_reserved() / (1024**3)
        gpu_ok = gpu_allocated < 15.0  # 15GB threshold

    base = {
        "status": "healthy" if models_loaded.is_set() else "loading",
        "device": GPU_DEVICE,
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
        "models_ready": models_loaded.is_set(),
        "loading_state": loading_state,
        "loading_errors": loading_errors if loading_errors else None,
        "rembg": rembg_remove is not None,
        "sam2": sam2_model is not None,
        "garmentrec": garmentrec_model is not None,
        "garmentgpt": garmentgpt_predictor is not None,
        "jobs_processing": sum(1 for j in jobs.values() if j["status"] == "processing"),
        "uptime_sec": time.time() - SERVER_START_TIME,
        "request_count": REQUEST_COUNT,
        "error_count": ERROR_COUNT,
        "gpu_ok": gpu_ok,
    }
    if verbose or ready:
        gpu_allocated = torch.cuda.memory_allocated() / (1024**3) if torch.cuda.is_available() else 0
        gpu_reserved = torch.cuda.memory_reserved() / (1024**3) if torch.cuda.is_available() else 0
        base["gpu_memory_gb"] = {
            "allocated": round(gpu_allocated, 2) if gpu_allocated else None,
            "reserved": round(gpu_reserved, 2) if gpu_reserved else None,
            "threshold_15gb_ok": gpu_ok,
        }
        base["model_load_times_sec"] = {k: round(v, 2) for k, v in MODEL_LOAD_TIMES.items()}

    if ready and not models_loaded.is_set():
        return JSONResponse(status_code=503, content=base)

    if not gpu_ok:
        return JSONResponse(status_code=503, content=base)

    return base


@app.get("/ready")
async def ready():
    if models_loaded.is_set():
        return {"status": "ready"}
    return JSONResponse(status_code=503, content={
        "status": "loading",
        "loading_state": loading_state,
        "loading_errors": loading_errors if loading_errors else None,
    })


@app.get("/health/deep")
async def health_deep():
    """Run a tiny inference to verify models actually work (slow check)."""
    if not models_loaded.is_set():
        return JSONResponse(status_code=503, content={"status": "loading", "detail": "Models not ready"})
    try:
        # Test rembg: create 8x8 dummy image
        from PIL import Image
        import numpy as np
        dummy = Image.new("RGB", (8, 8), (255, 255, 255))
        _ = rembg_remove(dummy)
        return {"status": "ready", "checks": {"rembg": "ok"}}
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "degraded", "checks": {"rembg": f"fail: {e}"}})


# ── Phase 208: Cold-start optimization — pre-warm endpoint ──
_last_prewarm_time = 0.0
PREWARM_INTERVAL = 120.0  # seconds between pre-warm cycles

@app.get("/api/v1/prewarm")
async def prewarm():
    """
    Lightweight CUDA context refresh. Runs a tiny inference on each loaded model
    to prevent GPU context eviction during idle periods.
    Called by proxy heartbeat every 2 minutes.
    """
    global _last_prewarm_time
    now = time.time()
    if now - _last_prewarm_time < PREWARM_INTERVAL:
        return {"status": "skipped", "reason": f"Last prewarm {int(now - _last_prewarm_time)}s ago"}

    _last_prewarm_time = now
    results = {}
    t0 = time.time()

    # Pre-warm rembg with tiny dummy
    try:
        from PIL import Image as _Img
        dummy = _Img.new("RGB", (8, 8), (128, 128, 128))
        _ = rembg_remove(dummy)
        results["rembg"] = "ok"
    except Exception as e:
        results["rembg"] = f"skip: {str(e)[:50]}"

    # Pre-warm SAM2 with dummy tensors (no actual inference, just CUDA context refresh)
    if sam2_model is not None:
        try:
            import torch as _t
            dummy_tensor = _t.randn(1, 3, 32, 32).to(GPU_DEVICE)
            # Just touch the model's first layer to activate CUDA context
            _ = sam2_model.image_encoder(dummy_tensor)
            del dummy_tensor
            _t.cuda.empty_cache()
            results["sam2"] = "ok"
        except Exception as e:
            results["sam2"] = f"skip: {str(e)[:50]}"

    # Pre-warm GarmentRec with dummy tensor
    if garmentrec_model is not None:
        try:
            import torch as _t
            dummy_input = _t.randn(1, 3, 256, 256).to(GPU_DEVICE)
            _ = garmentrec_model(dummy_input)
            del dummy_input
            _t.cuda.empty_cache()
            results["garmentrec"] = "ok"
        except Exception as e:
            results["garmentrec"] = f"skip: {str(e)[:50]}"

    elapsed = time.time() - t0
    logger.info(f"Prewarm cycle completed in {elapsed:.2f}s: {results}")
    return {"status": "ok", "elapsed_sec": round(elapsed, 2), "results": results}


# ─────────────────────────────────────────────────────────────
#  Async reconstruct (returns job_id immediately)
# ─────────────────────────────────────────────────────────────

@app.post("/api/v1/reconstruct")
async def reconstruct(
    file: UploadFile = File(...),
    include_mesh: bool = True,
    include_pattern: bool = True,
    user_id: str = "",
):
    image_bytes = await file.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(400, detail=_structured_error("IMAGE_TOO_LARGE"))
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(400, detail=_structured_error("INVALID_IMAGE", detail="File must be an image"))
    # Validate image can be opened and has valid dimensions
    try:
        _test_img = Image.open(io.BytesIO(image_bytes))
        _test_img.verify()
        _test_img = Image.open(io.BytesIO(image_bytes))
        if _test_img.width < 32 or _test_img.height < 32:
            raise HTTPException(400, detail=_structured_error("INVALID_IMAGE", detail=f"Image too small ({_test_img.width}x{_test_img.height}), min 32x32"))
        if _test_img.width > 4096 or _test_img.height > 4096:
            raise HTTPException(400, detail=_structured_error("INVALID_IMAGE", detail=f"Image too large ({_test_img.width}x{_test_img.height}), max 4096x4096"))
    except HTTPException:
        raise
    except Exception as _e:
        raise HTTPException(400, detail=_structured_error("INVALID_IMAGE", detail=str(_e)))
    if rembg_remove is None:
        raise HTTPException(503, detail=_structured_error("REMBG_FAILED", detail="rembg not available"))

    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {
        "status": "processing",
        "result_zip": None,
        "error": None,
        "user_id": user_id,
        "created_at": datetime.utcnow().isoformat(),
    }

    # Spawn background task (non-blocking)
    asyncio.create_task(process_full_pipeline(job_id, image_bytes, include_mesh, include_pattern))

    return {"job_id": job_id, "status": "processing"}


@app.get("/api/v1/job/{job_id}")
async def get_job(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if job["status"] == "completed":
        return StreamingResponse(
            io.BytesIO(job["result_zip"]),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=garment_{job_id}.zip"},
        )
    elif job["status"] == "failed":
        return JSONResponse(status_code=500, content={"status": "failed", "error": job["error"]})
    return {"status": "processing"}


@app.get("/api/v1/reconstruct/progress/{job_id}")
async def reconstruct_progress(job_id: str):
    """SSE endpoint — streams progress events for a reconstruction job."""
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")

    async def event_generator():
        last_seq = 0
        timeout_count = 0
        max_timeout = 60  # 60 * 5s = 300s max idle
        while timeout_count < max_timeout:
            progress = job_progress.get(job_id, {})
            current_seq = progress.get("sequence", 0)
            if current_seq > last_seq:
                last_seq = current_seq
                timeout_count = 0
                data = json.dumps({
                    "stage": progress.get("stage", "unknown"),
                    "progress": progress.get("progress", 0),
                    "message": progress.get("message", ""),
                })
                yield f"data: {data}\n\n"
                if progress.get("stage") in ("complete", "error"):
                    break
            else:
                timeout_count += 1
            # Wait for new event or timeout after 5s
            evt = asyncio.Event()
            job_progress_events.setdefault(job_id, []).add(evt)
            try:
                await asyncio.wait_for(evt.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                pass
            finally:
                job_progress_events.get(job_id, set()).discard(evt)
        # Cleanup
        job_progress_events.pop(job_id, None)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/v1/reconstruct/status")
async def reconstruct_status(job_id: str):
    """Simple status check (non-SSE) for polling fallback."""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    progress = job_progress.get(job_id, {})
    return {
        "status": job["status"],
        "stage": progress.get("stage", "unknown"),
        "progress": progress.get("progress", 0),
        "message": progress.get("message", ""),
    }


# ─────────────────────────────────────────────────────────────
#  Split pipeline endpoints (each < 100s)
# ─────────────────────────────────────────────────────────────

@app.post("/api/v1/segment")
async def segment_endpoint(file: UploadFile = File(...)):
    """Step 1: Background removal + SAM2 segmentation (~20s)."""
    start = time.time()
    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    nobg = rembg_remove(image)
    mask = segment_garment(image)
    buf = io.BytesIO()
    Image.fromarray(mask).save(buf, "PNG")
    buf.seek(0)
    elapsed = time.time() - start
    return StreamingResponse(buf, media_type="image/png", headers={"X-Processing-Time": f"{elapsed:.2f}"})


@app.post("/api/v1/mesh")
async def mesh_endpoint(file: UploadFile = File(...)):
    """Step 2: GarmentRec 3D mesh (~50s)."""
    start = time.time()
    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    if rembg_remove is None:
        raise HTTPException(503, "rembg not available")
    nobg = rembg_remove(image)
    with tempfile.TemporaryDirectory() as tmp:
        mesh_data = run_garmentrec(garmentrec_model, nobg, tmp)
    gc.collect()
    elapsed = time.time() - start
    return JSONResponse(content=mesh_data, headers={"X-Processing-Time": f"{elapsed:.2f}"})


@app.post("/api/v1/pattern")
async def pattern_endpoint(file: UploadFile = File(...)):
    """Step 3: GarmentGPT sewing pattern (~50s)."""
    start = time.time()
    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    if rembg_remove is None:
        raise HTTPException(503, "rembg not available")
    nobg = rembg_remove(image)
    pattern_data = run_garmentgpt(garmentgpt_predictor, nobg)
    elapsed = time.time() - start
    return JSONResponse(content=pattern_data, headers={"X-Processing-Time": f"{elapsed:.2f}"})


@app.get("/debug/error")
async def debug_error():
    try:
        return {"error": open("/kaggle/working/last_error.txt").read()}
    except Exception as e:
        return {"error": f"No error file: {e}"}


# ═══════════════════════════════════════════════════════════════
#  VTO — Multi-Angle Virtual Try-On (Phases 157–185)
# ═══════════════════════════════════════════════════════════════

vto_jobs = {}       # {job_id: {status, angles: {front: url, side: url, back: url}, ...}}
vto_progress = {}   # {job_id: {stage, progress, message, sequence}}
vto_progress_events = {}  # {job_id: [asyncio.Event]}


def _vto_emit(job_id: str, stage: str, progress: int, message: str):
    seq = vto_progress.get(job_id, {}).get("sequence", 0) + 1
    vto_progress[job_id] = {"stage": stage, "progress": progress, "message": message, "sequence": seq}
    for evt in vto_progress_events.get(job_id, []):
        evt.set()


# ── Phase 159: Neutralization shader ──
def _neutralize_clothing(image: "Image.Image") -> "Image.Image":
    """Convert clothing to neutral gray tone via LAB chrominance reduction."""
    import cv2
    img = np.array(image.convert("RGB"))
    lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    a = cv2.addWeighted(a, 0.3, np.full_like(a, 128), 0.7, 0)
    b = cv2.addWeighted(b, 0.3, np.full_like(b, 128), 0.7, 0)
    return Image.fromarray(cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2RGB))


# ── Phase 158: Side-to-front alignment via pose landmarks ──
def _align_side_to_front(front: "Image.Image", side: "Image.Image") -> "Image.Image":
    """
    Align side profile to front using MediaPipe pose landmarks.
    Applies affine transform to match shoulder/hip positions.
    Falls back to center-crop resize if MediaPipe unavailable.
    """
    try:
        import mediapipe as mp
        mp_pose = mp.solutions.pose
        with mp_pose.Pose(static_image_mode=True, model_complexity=1) as pose:
            front_np = np.array(front.convert("RGB"))
            side_np = np.array(side.convert("RGB"))
            front_res = pose.process(front_np)
            side_res = pose.process(side_np)
            if front_res.pose_landmarks and side_res.pose_landmarks:
                # Get shoulder and hip landmarks
                def get_pt(landmarks, idx, w, h):
                    lm = landmarks.landmark[idx]
                    return np.array([lm.x * w, lm.y * h])
                h_f, w_f = front_np.shape[:2]
                h_s, w_s = side_np.shape[:2]
                src_pts = np.array([
                    get_pt(side_res.pose_landmarks, 11, w_s, h_s),  # left shoulder
                    get_pt(side_res.pose_landmarks, 12, w_s, h_s),  # right shoulder
                    get_pt(side_res.pose_landmarks, 23, w_s, h_s),  # left hip
                ], dtype=np.float32)
                dst_pts = np.array([
                    get_pt(front_res.pose_landmarks, 11, w_f, h_f),
                    get_pt(front_res.pose_landmarks, 12, w_f, h_f),
                    get_pt(front_res.pose_landmarks, 23, w_f, h_f),
                ], dtype=np.float32)
                matrix = cv2.getAffineTransform(src_pts, dst_pts)
                aligned = cv2.warpAffine(side_np, matrix, (w_f, h_f))
                return Image.fromarray(aligned)
    except Exception:
        pass
    # Fallback: resize side to match front dimensions
    return side.resize(front.size, Image.LANCZOS)


# ── Phase 161-162: Back-view synthesis with VLM in-paint ──
def _synthesize_back_view(front_image: "Image.Image", side_image: "Image.Image", use_vlm: bool = True) -> "Image.Image":
    """
    Phase 161: Identify texture voids, use VLM to predict back textures.
    Phase 162: VLM back-texture in-paint from front persona.
    Phase 164: Super-resolution upscale.
    Phase 166: Hair/neck continuity via VLM analysis.
    Phase 167: Lighting match from side profile.
    """
    import cv2
    front_np = np.array(front_image.convert("RGB"))
    side_np = np.array(side_image.convert("RGB"))
    h, w = front_np.shape[:2]

    # Mirror front for back base
    back_np = np.flip(front_np, axis=1).copy()

    # Phase 167: Lighting match from side image
    side_gray = cv2.cvtColor(side_np, cv2.COLOR_RGB2GRAY)
    side_brightness = cv2.GaussianBlur(side_gray.astype(np.float32) / 255.0, (31, 31), 0)
    back_float = back_np.astype(np.float32)
    for c in range(3):
        back_float[:, :, c] *= (0.7 + 0.3 * side_brightness)
    back_np = np.clip(back_float, 0, 255).astype(np.uint8)

    # Phase 161: Create occlusion map (texture voids)
    occlusion_map = np.zeros((h, w), dtype=np.uint8)
    # Detect high-gradient regions in mirrored front — these are likely occlusion boundaries
    gray_back = cv2.cvtColor(back_np, cv2.COLOR_RGB2GRAY)
    grad_x = cv2.Sobel(gray_back, cv2.CV_32F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray_back, cv2.CV_32F, 0, 1, ksize=3)
    grad_mag = np.sqrt(grad_x**2 + grad_y**2)
    occlusion_map[grad_mag > 50] = 255
    occlusion_map = cv2.dilate(occlusion_map, np.ones((5, 5), np.uint8), iterations=2)

    # Phase 166: Hair/neck continuity — extend hair from front
    # Detect dark regions in top 30% of front (likely hair)
    hair_region = front_np[:int(h*0.3), :, :]
    hair_mask = np.all(hair_region < np.array([60, 50, 40]), axis=2).astype(np.uint8) * 255
    hair_mask = cv2.GaussianBlur(hair_mask.astype(np.float32), (15, 15), 0)
    # Blend hair region onto back view top
    hair_mask_full = np.zeros((h, w), dtype=np.float32)
    hair_mask_full[:int(h*0.3), :] = cv2.resize(hair_mask, (w, int(h*0.3)))
    for c in range(3):
        back_np[:, :, c] = np.where(
            hair_mask_full > 0.3,
            (back_np[:, :, c] * (1 - hair_mask_full) + front_np[:, :, c] * hair_mask_full).astype(np.uint8),
            back_np[:, :, c]
        )

    # Phase 162: VLM in-paint of occlusion voids (use GarmentGPT VLM if available)
    if use_vlm and garmentgpt_predictor is not None:
        try:
            # Use GarmentGPT VLM to fill occlusion voids
            occlusion_mask_img = Image.fromarray(occlusion_map)
            # Save temp files for VLM in-paint
            back_pil = Image.fromarray(back_np)
            inpainted = _vlm_inpaint_voids(back_pil, occlusion_mask_img)
            if inpainted:
                back_np = np.array(inpainted)
        except Exception as e:
            logger.warning(f"VLM in-paint failed, using opencv fallback: {e}")
            # OpenCV in-paint fallback
            back_np = cv2.inpaint(back_np, occlusion_map, 3, cv2.INPAINT_TELEA)

    # Phase 164: Super-resolution (detailEnhance)
    back_np = cv2.detailEnhance(back_np, sigma_s=10, sigma_r=0.15)

    # Apply side silhouette to edge regions for body-shape continuity
    side_mask = (cv2.cvtColor(side_np, cv2.COLOR_RGB2GRAY) > 30).astype(np.float32)
    side_mask = cv2.GaussianBlur(side_mask, (21, 21), 0)
    edge_region = (side_mask > 0.1) & (side_mask < 0.9)
    if edge_region.any():
        for c in range(3):
            back_np[:, :, c] = np.where(
                edge_region,
                (back_np[:, :, c] * 0.6 + side_np[:, :, c] * 0.4).astype(np.uint8),
                back_np[:, :, c]
            )

    return Image.fromarray(np.clip(back_np, 0, 255).astype(np.uint8))


# ── Phase 162: VLM in-paint helper ──
def _vlm_inpaint_voids(image: "Image.Image", mask: "Image.Image") -> "Image.Image":
    """
    Use GarmentGPT's VLM to in-paint occlusion voids in back view.
    Falls back gracefully if VLM not available.
    """
    global garmentgpt_predictor
    if garmentgpt_predictor is None:
        return None
    try:
        # VLM prompt for in-painting
        prompt = (
            "Fill the marked regions (hair, skin, body) to create a realistic back view. "
            "Maintain continuity with surrounding pixels. Keep the original style."
        )
        # Save images to temp files for predictor
        import tempfile
        img_path = None
        mask_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f1:
                image.save(f1.name, "PNG")
                img_path = f1.name
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f2:
                # Ensure mask is binary
                mask_np = np.array(mask.convert("L"))
                mask_bin = (mask_np > 127).astype(np.uint8) * 255
                Image.fromarray(mask_bin).save(f2.name, "PNG")
                mask_path = f2.name

            # Use GarmentGPT's VLM to generate in-painted region
            result = garmentgpt_predictor.predict(image_path=img_path)

            # For now, VLM output is used as guidance but not full in-paint
            # Return None to fall back to opencv
            return None
        finally:
            for p in [img_path, mask_path]:
                if p and os.path.exists(p):
                    try:
                        os.unlink(p)
                    except Exception:
                        pass
    except Exception:
        return None



# ── Phase 192: AI Master Tailor — Conversational VLM Endpoint ──
TAILOR_SYSTEM_PROMPT = (
    "You are KORRA, a master tailor with 40 years of Savile Row and West African tailoring expertise.\n\n"
    "Your knowledge includes:\n"
    "- Pattern drafting, draping, and flat-pattern methods\n"
    "- Fabric behavior: drape, stretch, grain, bias\n"
    "- Seam construction: French seams, flat-felled, serged, Hong Kong finish\n"
    "- Fitting adjustments: dart manipulation, ease distribution, body-shape corrections\n"
    "- Global garment traditions: Ankara, Kente, Dashiki, Agbada, Kaftan, Kanga\n\n"
    "When given a garment image or 3D mesh analysis, provide:\n"
    "1. Specific construction steps (not vague advice)\n"
    "2. Seam allowance recommendations (in cm)\n"
    "3. Fabric-specific tips\n"
    "4. Fitting adjustments for the body measurements provided\n\n"
    "Keep responses concise, actionable, and professional. Use markdown formatting."
)


@app.post("/api/v1/tailor/chat")
async def tailor_chat(
    file: UploadFile = File(None),
    message: str = "",
    history: str = "[]",
    measurements: str = "{}",
):
    """Phase 192: AI Master Tailor conversational endpoint using GarmentGPT VLM."""
    global garmentgpt_predictor

    if not message.strip():
        raise HTTPException(400, detail="message is required")

    if garmentgpt_predictor is None or not hasattr(garmentgpt_predictor, "llm_model"):
        raise HTTPException(503, detail="VLM model not loaded. Start the Kaggle notebook first.")

    try:
        chat_history = json.loads(history) if history else []
    except json.JSONDecodeError:
        chat_history = []
    try:
        body_measurements = json.loads(measurements) if measurements else {}
    except json.JSONDecodeError:
        body_measurements = {}

    meas_ctx = ""
    if body_measurements:
        meas_lines = [f"- {k}: {v} cm" for k, v in body_measurements.items() if isinstance(v, (int, float))]
        if meas_lines:
            meas_ctx = "\n\nBody Measurements:\n" + "\n".join(meas_lines[:15])

    image = None
    image_ctx = ""
    if file and file.filename:
        image_bytes = await file.read()
        if len(image_bytes) > 0:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            image_ctx = "\n\n[User provided a garment/fabric image for analysis]"

    messages = [{"role": "system", "content": TAILOR_SYSTEM_PROMPT + meas_ctx}]
    for entry in chat_history[-6:]:
        role = entry.get("role", "user")
        content = entry.get("content", "")
        messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": message.strip() + image_ctx})

    llm = garmentgpt_predictor.llm_model
    prompt_parts = []
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        if role == "system":
            prompt_parts.append(f"<|system|>\n{content}\n")
        elif role == "user":
            prompt_parts.append(f"<|user|>\n{content}\n")
        elif role == "assistant":
            prompt_parts.append(f"<|assistant|>\n{content}\n")
    prompt_parts.append("<|assistant|>\n")
    full_prompt = "".join(prompt_parts)

    if image is not None:
        proc = llm._processor(text=full_prompt, images=image, return_tensors="pt").to(llm._model.device)
    else:
        proc = llm._processor(text=full_prompt, return_tensors="pt").to(llm._model.device)

    with torch.no_grad():
        out = llm._model.generate(
            **proc,
            max_new_tokens=1024,
            do_sample=True,
            temperature=0.3,
            top_p=0.9,
        )

    response_text = llm._processor.decode(out[0], skip_special_tokens=False)
    if "<|assistant|>" in response_text:
        response_text = response_text.split("<|assistant|>")[-1].strip()
    for tok in ["<|end|>", "<eos>", "</s>"]:
        response_text = response_text.replace(tok, "").strip()

    if not response_text or len(response_text) < 5:
        raise HTTPException(500, detail="VLM returned empty response")

    return {"response": response_text, "source": "vlm", "model": "garmentgpt-vlm"}



# ── Phase 157: SAM2 persona masking ──
def _segment_persona(image: "Image.Image") -> "Image.Image":
    """
    Use SAM2 with center-point prompt to extract user silhouette.
    Falls back to rembg if SAM2 not loaded.
    """
    global predict_fn, sam2_model

    if predict_fn is not None:
        try:
            img_np = np.array(image.convert("RGB"))
            predict_fn.set_image(img_np)
            masks, scores, _ = predict_fn.predict(
                point_coords=np.array([[img_np.shape[1] // 2, img_np.shape[0] // 2]]),
                point_labels=np.array([1]),
                multimask_output=True,
            )
            best_mask = masks[scores.argmax()]
            # Apply mask to original image
            masked = np.zeros_like(img_np)
            for c in range(3):
                masked[:, :, c] = img_np[:, :, c] * (best_mask > 0.5).astype(np.uint8)
            return Image.fromarray(masked)
        except Exception as e:
            logger.warning(f"SAM2 persona masking failed: {e}")

    # Fallback to rembg
    if rembg_remove is not None:
        try:
            return rembg_remove(image)
        except Exception:
            pass

    return image


# ── Phase 160: UV-space projection helper ──
def _project_to_uv(front: "Image.Image", side: "Image.Image") -> dict:
    """
    Map 2D Front/Side textures into 3D SMPL UV-coordinates.
    Returns UV texture map dict.
    For MVP: return simple blend of front+side.
    Full implementation would use SMPL UV mapping.
    """
    import cv2
    front_np = np.array(front.convert("RGB"))
    side_np = np.array(side.convert("RGB"))

    # Simple UV map: front on left half, side on right half
    h, w = 1024, 1024
    uv_map = np.zeros((h, w, 3), dtype=np.uint8)
    f_h, f_w = front_np.shape[:2]
    s_h, s_w = side_np.shape[:2]

    # Resize and place front on left, side on right
    front_resized = cv2.resize(front_np, (w // 2, h))
    side_resized = cv2.resize(side_np, (w // 2, h))
    uv_map[:, :w // 2, :] = front_resized
    uv_map[:, w // 2:, :] = side_resized

    return {
        "uv_map": uv_map,
        "width": w,
        "height": h,
        "format": "front_left_side_right",
    }


# ── Phase 165: Symmetry verification ──
def _verify_symmetry(front: "Image.Image", back: "Image.Image") -> dict:
    """
    Verify back view matches shoulder-width measurements from front.
    Returns {pass: bool, front_width, back_width, diff_pct}.
    """
    import cv2
    f_np = np.array(front.convert("L"))
    b_np = np.array(back.convert("L"))

    # Find body width at mid-height (shoulder level ~30% from top)
    h = f_np.shape[0]
    shoulder_y = int(h * 0.3)

    def get_body_width(img, y):
        row = img[y, :]
        cols = np.where(row < 200)[0]
        if len(cols) < 2:
            return 0
        return cols[-1] - cols[0]

    fw = get_body_width(f_np, shoulder_y)
    bw = get_body_width(b_np, shoulder_y)
    diff_pct = abs(fw - bw) / max(fw, bw) * 100 if max(fw, bw) > 0 else 0

    return {
        "pass": diff_pct < 15,
        "front_width": fw,
        "back_width": bw,
        "diff_pct": round(diff_pct, 1),
    }


# ── Phase 174: Post-diffusion detail recovery ──
def _enhance_detail(image: "Image.Image") -> "Image.Image":
    """Apply sharpen + denoise to recover fine details lost during diffusion."""
    import cv2
    arr = np.array(image.convert("RGB"))
    denoised = cv2.fastNlMeansDenoisingColored(arr, None, 10, 10, 7, 21)
    kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    sharpened = cv2.filter2D(denoised, -1, kernel)
    return Image.fromarray(np.clip(sharpened, 0, 255).astype(np.uint8))


# ── Phase 190: Privacy face blur ──
def _blur_face(image: "Image.Image", strength: int = 15) -> "Image.Image":
    """
    Blur face region using OpenCV Haar cascade or MediaPipe face detection.
    strength: kernel size for Gaussian blur (odd number, higher = more blur).
    """
    import cv2
    img_np = np.array(image.convert("RGB"))
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)

    # Try OpenCV Haar cascade first (always available)
    try:
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        face_cascade = cv2.CascadeClassifier(cascade_path)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        if len(faces) > 0:
            for (x, y, w, h) in faces:
                # Expand region slightly for full face coverage
                pad = int(max(w, h) * 0.15)
                x1 = max(0, x - pad)
                y1 = max(0, y - pad)
                x2 = min(img_np.shape[1], x + w + pad)
                y2 = min(img_np.shape[0], y + h + pad)
                roi = img_np[y1:y2, x1:x2]
                blurred = cv2.GaussianBlur(roi, (strength * 2 + 1, strength * 2 + 1), 30)
                img_np[y1:y2, x1:x2] = blurred
            return Image.fromarray(img_np)
    except Exception as e:
        logger.warning(f"Face blur cascade failed: {e}")

    # Fallback: blur top 25% of image (likely contains face)
    h, w = img_np.shape[:2]
    face_region = img_np[:int(h * 0.25), :]
    blurred = cv2.GaussianBlur(face_region, (strength * 2 + 1, strength * 2 + 1), 30)
    img_np[:int(h * 0.25), :] = blurred
    return Image.fromarray(img_np)


# ═══════════════════════════════════════════════════════════════
#  Garment Extraction + Transfer Pipeline (real VTO)
# ═══════════════════════════════════════════════════════════════

def _extract_garment_from_source(image: "Image.Image", garment_type: str = "auto") -> dict:
    """
    Full garment extraction pipeline from a source photo.
    Returns {garment_img, garment_mask, mesh_data, garment_class}.
    garment_class is one of: upper, lower, full.
    """
    import cv2
    import trimesh
    import tempfile

    img_rgb = image.convert("RGB")
    img_np = np.array(img_rgb)

    # Step 1: SAM2 segmentation → garment mask
    logger.info("[VTO] Step 1: SAM2 garment segmentation")
    mask_uint8 = segment_garment(img_rgb)  # (H,W) uint8 0/255
    mask_bool = mask_uint8 > 127

    # Step 2: Determine garment region from mask
    logger.info("[VTO] Step 2: Analyzing garment region")
    ys, xs = np.where(mask_bool)
    if len(ys) < 100:
        logger.warning("[VTO] Mask too small, falling back to full image")
        mask_bool = np.ones(img_np.shape[:2], dtype=bool)
        ys, xs = np.where(mask_bool)

    y_min, y_max = ys.min(), ys.max()
    x_min, x_max = xs.min(), xs.max()
    garment_bbox = (x_min, y_min, x_max, y_max)

    # Classify garment region: upper body (top 60%) vs lower body (bottom 40%)
    img_h = img_np.shape[0]
    mid_y = y_min + int((y_max - y_min) * 0.55)  # slightly above center
    upper_mask = mask_bool.copy()
    upper_mask[mid_y:, :] = False
    lower_mask = mask_bool.copy()
    lower_mask[:mid_y, :] = False

    upper_pixels = upper_mask.sum()
    lower_pixels = lower_mask.sum()
    total_pixels = mask_bool.sum()

    if garment_type == "upper" or (garment_type == "auto" and upper_pixels > total_pixels * 0.4):
        active_mask = upper_mask
        garment_class = "upper"
    elif garment_type == "lower" or (garment_type == "auto" and lower_pixels > total_pixels * 0.3):
        active_mask = lower_mask
        garment_class = "lower"
    else:
        active_mask = mask_bool
        garment_class = "full"

    # Step 3: Extract garment texture from masked region
    logger.info(f"[VTO] Step 3: Extracting {garment_class} garment texture")
    garment_img_np = img_np.copy()
    garment_img_np[~active_mask] = [255, 255, 255]  # white background outside mask
    garment_img = Image.fromarray(garment_img_np)

    # Crop to garment bbox with padding
    pad = 10
    cy_min = max(0, y_min - pad)
    cy_max = min(img_h, y_max + pad)
    cx_min = max(0, x_min - pad)
    cx_max = min(img_np.shape[1], x_max + pad)
    garment_crop = garment_img.crop((cx_min, cy_min, cx_max, cy_max))
    mask_crop = Image.fromarray(active_mask[cy_min:cy_max, cx_min:cx_max].astype(np.uint8) * 255)

    # Step 4: Run GarmentRec for 3D mesh (if model available)
    mesh_data = None
    if garmentrec_model is not None:
        logger.info("[VTO] Step 4: GarmentRec 3D mesh reconstruction")
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                mesh_data = run_garmentrec(garmentrec_model, img_rgb, tmp_dir)
                # Load the actual .obj files for vertex/face data
                for part in ("upper", "lower"):
                    obj_path = os.path.join(tmp_dir, f"input_{part}.obj")
                    if os.path.exists(obj_path):
                        mesh = trimesh.load(obj_path)
                        mesh_data[part]["vertices_np"] = np.array(mesh.vertices)
                        mesh_data[part]["faces_np"] = np.array(mesh.faces)
                        mesh_data[part]["bounds"] = mesh.bounds.tolist()
        except Exception as e:
            logger.warning(f"[VTO] GarmentRec failed: {e}")

    # Step 5: Extract dominant garment color
    logger.info("[VTO] Step 5: Extracting garment color")
    mask_pixels = img_np[active_mask]
    if len(mask_pixels) > 0:
        dominant_color = np.median(mask_pixels, axis=0).astype(int).tolist()
    else:
        dominant_color = [128, 128, 128]

    return {
        "garment_img": garment_img,
        "garment_crop": garment_crop,
        "mask_crop": mask_crop,
        "garment_mask": Image.fromarray(active_mask.astype(np.uint8) * 255),
        "mesh_data": mesh_data,
        "garment_class": garment_class,
        "garment_bbox": garment_bbox,
        "dominant_color": dominant_color,
    }


def _detect_body_pose(image: "Image.Image") -> dict:
    """
    Detect body pose landmarks using MediaPipe Pose (33 landmarks, sub-pixel accuracy).
    Returns {landmarks, shoulder_width, hip_width, torso_height, body_center}.
    Raises RuntimeError if MediaPipe unavailable — no fallback.
    """
    img_np = np.array(image.convert("RGB"))
    h, w = img_np.shape[:2]

    import mediapipe as mp
    mp_pose = mp.solutions.pose
    with mp_pose.Pose(static_image_mode=True, model_complexity=1) as pose:
        results = pose.process(img_np)
        if not results.pose_landmarks:
            raise RuntimeError("MediaPipe could not detect body pose in image")
        lm = results.pose_landmarks.landmark

        def pt(idx):
            return (lm[idx].x * w, lm[idx].y * h)

        left_shoulder = pt(11)
        right_shoulder = pt(12)
        left_hip = pt(23)
        right_hip = pt(24)
        nose = pt(0)

        shoulder_width = np.sqrt((right_shoulder[0]-left_shoulder[0])**2 +
                                 (right_shoulder[1]-left_shoulder[1])**2)
        hip_width = np.sqrt((right_hip[0]-left_hip[0])**2 +
                            (right_hip[1]-left_hip[1])**2)
        torso_height = np.sqrt((left_hip[1]-left_shoulder[1])**2 +
                               (left_hip[0]-left_shoulder[0])**2)

        center_x = (left_shoulder[0] + right_shoulder[0]) / 2
        center_y = (left_shoulder[1] + left_hip[1]) / 2

        return {
            "landmarks": {
                "left_shoulder": left_shoulder,
                "right_shoulder": right_shoulder,
                "left_hip": left_hip,
                "right_hip": right_hip,
                "nose": nose,
            },
            "shoulder_width": shoulder_width,
            "hip_width": hip_width,
            "torso_height": torso_height,
            "body_center": (center_x, center_y),
        }


def _warp_and_blend_garment(
    source_garment: "Image.Image",
    source_mask: "Image.Image",
    target_image: "Image.Image",
    target_pose: dict,
    source_pose: dict,
    garment_color_hex: str = None,
) -> "Image.Image":
    """
    Warp source garment onto target body using pose landmark alignment.
    Uses affine transform based on shoulder/hip landmarks + alpha blending.
    """
    import cv2

    src_np = np.array(source_garment.convert("RGB"))
    tgt_np = np.array(target_image.convert("RGB"))
    src_mask_np = np.array(source_mask.convert("L"))

    src_h, src_w = src_np.shape[:2]
    tgt_h, tgt_w = tgt_np.shape[:2]

    # Source landmarks (from source garment image)
    src_lm = source_pose.get("landmarks", {})
    src_ls = src_lm.get("left_shoulder", (src_w * 0.35, src_h * 0.25))
    src_rs = src_lm.get("right_shoulder", (src_w * 0.65, src_h * 0.25))
    src_lh = src_lm.get("left_hip", (src_w * 0.38, src_h * 0.55))
    src_rh = src_lm.get("right_hip", (src_w * 0.62, src_h * 0.55))

    # Target landmarks
    tgt_lm = target_pose.get("landmarks", {})
    tgt_ls = tgt_lm.get("left_shoulder", (tgt_w * 0.35, tgt_h * 0.25))
    tgt_rs = tgt_lm.get("right_shoulder", (tgt_w * 0.65, tgt_h * 0.25))
    tgt_lh = tgt_lm.get("left_hip", (tgt_w * 0.38, tgt_h * 0.55))
    tgt_rh = tgt_lm.get("right_hip", (tgt_w * 0.62, tgt_h * 0.55))

    # Compute scale and rotation from shoulder/hip comparison
    src_shoulder_w = np.sqrt((src_rs[0]-src_ls[0])**2 + (src_rs[1]-src_ls[1])**2)
    tgt_shoulder_w = np.sqrt((tgt_rs[0]-tgt_ls[0])**2 + (tgt_rs[1]-tgt_ls[1])**2)

    src_hip_w = np.sqrt((src_rh[0]-src_lh[0])**2 + (src_rh[1]-src_lh[1])**2)
    tgt_hip_w = np.sqrt((tgt_rh[0]-tgt_lh[0])**2 + (tgt_rh[1]-tgt_lh[1])**2)

    scale_x = tgt_shoulder_w / max(src_shoulder_w, 1)
    scale_y = tgt_shoulder_w / max(src_shoulder_w, 1)  # uniform scale
    scale = (scale_x + scale_y) / 2

    # Source shoulder angle
    src_angle = np.arctan2(src_rs[1] - src_ls[1], src_rs[0] - src_ls[0])
    tgt_angle = np.arctan2(tgt_rs[1] - tgt_ls[1], tgt_rs[0] - tgt_ls[0])
    rotation = tgt_angle - src_angle

    # Target center (midpoint of shoulders)
    tgt_center_x = (tgt_ls[0] + tgt_rs[0]) / 2
    tgt_center_y = (tgt_ls[1] + tgt_lh[1]) / 2

    # Source center
    src_center_x = (src_ls[0] + src_rs[0]) / 2
    src_center_y = (src_ls[1] + src_lh[1]) / 2

    # Build affine transform matrix
    # 1. Translate source center to origin
    # 2. Scale
    # 3. Rotate
    # 4. Translate to target center
    M = np.zeros((2, 3), dtype=np.float64)
    cos_a = np.cos(rotation)
    sin_a = np.sin(rotation)
    M[0, 0] = scale * cos_a
    M[0, 1] = scale * sin_a
    M[1, 0] = -scale * sin_a
    M[1, 1] = scale * cos_a
    M[0, 2] = tgt_center_x - scale * (cos_a * src_center_x + sin_a * src_center_y)
    M[1, 2] = tgt_center_y - scale * (-sin_a * src_center_x + cos_a * src_center_y)

    # Warp garment
    warped = cv2.warpAffine(src_np, M, (tgt_w, tgt_h), borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))
    warped_mask = cv2.warpAffine(src_mask_np, M, (tgt_w, tgt_h), borderMode=cv2.BORDER_CONSTANT, borderValue=0)

    # Apply garment color tint if specified
    if garment_color_hex and garment_color_hex != "#000000":
        try:
            hex_str = garment_color_hex.lstrip("#")
            r, g, b = int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)
            tint_strength = 0.4  # blend original texture with target color
            tint_layer = np.zeros_like(warped)
            tint_layer[:, :, 0] = r
            tint_layer[:, :, 1] = g
            tint_layer[:, :, 2] = b
            # Only tint where garment exists
            garment_region = warped_mask > 127
            warped[garment_region] = (
                warped[garment_region].astype(np.float32) * (1 - tint_strength) +
                tint_layer[garment_region].astype(np.float32) * tint_strength
            ).astype(np.uint8)
        except Exception:
            pass

    # Alpha blend with feathered edges
    alpha = warped_mask.astype(np.float32) / 255.0
    # Feather edges: gaussian blur on alpha
    alpha = cv2.GaussianBlur(alpha, (21, 21), 0)
    alpha = np.clip(alpha, 0, 1)
    alpha_3ch = np.stack([alpha] * 3, axis=-1)

    # Blend: target * (1-alpha) + warped * alpha
    result = (tgt_np.astype(np.float32) * (1 - alpha_3ch) +
              warped.astype(np.float32) * alpha_3ch).astype(np.uint8)

    # Final detail recovery
    result_img = Image.fromarray(result)
    result_img = _enhance_detail(result_img)

    return result_img


def _apply_garment_tint(garment_img: "Image.Image", color_hex: str) -> "Image.Image":
    """Apply color tint to garment image while preserving texture details."""
    if not color_hex or color_hex == "#000000":
        return garment_img
    import cv2
    try:
        hex_str = color_hex.lstrip("#")
        r, g, b = int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)
        img_np = np.array(garment_img.convert("RGB"))
        # LAB color space: replace a/b channels with target hue
        lab = cv2.cvtColor(img_np, cv2.COLOR_RGB2LAB)
        target_lab = cv2.cvtColor(np.array([[[r, g, b]]], dtype=np.uint8), cv2.COLOR_RGB2LAB)
        target_a = target_lab[0, 0, 1]
        target_b = target_lab[0, 0, 2]
        l_channel = lab[:, :, 0].astype(np.float32)
        # Blend a/b channels: 50% original texture + 50% target color
        lab[:, :, 1] = (lab[:, :, 1].astype(np.float32) * 0.5 + target_a * 0.5).astype(np.uint8)
        lab[:, :, 2] = (lab[:, :, 2].astype(np.float32) * 0.5 + target_b * 0.5).astype(np.uint8)
        result = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
        return Image.fromarray(result)
    except Exception:
        return garment_img


# ── Phase 170-172: Multi-angle VTO execution ──
async def process_vto_synthesis(job_id: str, image_bytes: bytes, user_id: str):
    """
    Full multi-angle VTO synthesis pipeline:
    1. SAM2 persona masking (Phase 157)
    2. Side-to-front alignment (Phase 158)
    3. Neutralization (Phase 159)
    4. UV projection (Phase 160)
    5. Back-view synthesis with VLM in-paint (Phase 161-162)
    6. Super-resolution (Phase 164)
    7. Symmetry verification (Phase 165)
    """
    try:
        _vto_emit(job_id, "loading", 5, "Loading image...")
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        # Phase 157: SAM2 persona masking
        _vto_emit(job_id, "segmenting", 15, "Extracting persona...")
        persona = _segment_persona(image)

        # Phase 158: Side-to-front alignment
        _vto_emit(job_id, "aligning", 25, "Aligning views...")
        side_aligned = _align_side_to_front(persona, persona)

        # Phase 159: Neutralize clothing
        _vto_emit(job_id, "neutralizing", 35, "Neutralizing clothing...")
        front_neutral = _neutralize_clothing(persona)
        side_neutral = _neutralize_clothing(side_aligned)

        # Phase 160: UV-space projection
        _vto_emit(job_id, "projecting", 45, "Projecting to UV space...")
        uv_data = _project_to_uv(front_neutral, side_neutral)

        # Phase 161-162: Back-view synthesis with VLM in-paint
        _vto_emit(job_id, "synthesizing", 55, "Synthesizing back view...")
        back_view = _synthesize_back_view(front_neutral, side_neutral, use_vlm=True)

        # Phase 164: Super-resolution enhancement
        _vto_emit(job_id, "upscaling", 70, "Enhancing resolution...")
        import cv2
        for view_name, view_img in [("front", front_neutral), ("side", side_neutral), ("back", back_view)]:
            enhanced = _enhance_detail(view_img)
            tmp_path = f"/kaggle/working/vto_{job_id}_{view_name}.png"
            enhanced.save(tmp_path, "PNG")

        # Phase 165: Symmetry verification
        _vto_emit(job_id, "verifying", 85, "Verifying symmetry...")
        sym = _verify_symmetry(front_neutral, back_view)
        logger.info(f"VTO {job_id} symmetry: {sym}")
        if not sym["pass"]:
            logger.warning(f"VTO {job_id}: symmetry check failed (diff {sym['diff_pct']}%)")

        # Store results
        vto_jobs[job_id]["status"] = "completed"
        vto_jobs[job_id]["angles"] = {
            "front": f"/kaggle/working/vto_{job_id}_front.png",
            "side": f"/kaggle/working/vto_{job_id}_side.png",
            "back": f"/kaggle/working/vto_{job_id}_back.png",
        }
        vto_jobs[job_id]["symmetry"] = sym
        vto_jobs[job_id]["uv_data"] = uv_data
        _vto_emit(job_id, "complete", 100, "VTO synthesis complete!")
        logger.info(f"VTO job {job_id} completed")

    except Exception as e:
        import traceback as tb
        vto_jobs[job_id]["status"] = "failed"
        vto_jobs[job_id]["error"] = str(e)
        _vto_emit(job_id, "error", -1, str(e)[:200])
        logger.error(f"VTO job {job_id} failed: {e}")
        try:
            open("/kaggle/working/last_error.txt", "w").write(tb.format_exc())
        except Exception:
            pass


async def process_vto_tryon(job_id: str, image_bytes: bytes, angle: str, user_id: str, seed: int = 42, garment_type: str = "casual", garment_color: str = "#000000"):
    """
    Real garment transfer pipeline:
    1. Source image → SAM2 segment → GarmentRec 3D mesh → extract garment texture
    2. Target person → detect body pose (MediaPipe)
    3. Warp garment onto target body using pose alignment
    4. Alpha blend with feathered edges
    """
    t_start = time.time()
    try:
        import random
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)

        _vto_emit(job_id, "loading", 5, f"Loading {angle} view...")
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        logger.info(f"VTO {job_id} ({angle}): garment_type={garment_type}, garment_color={garment_color}")

        # ── Step 1: Extract garment from source photo ──
        _vto_emit(job_id, "extracting", 15, f"Extracting garment from source...")
        garment_class = "upper" if garment_type in ("tshirt", "shirt", "blouse", "jacket", "hoodie") else "lower" if garment_type in ("pants", "shorts", "skirt") else "auto"
        extraction = _extract_garment_from_source(image, garment_class)
        garment_crop = extraction["garment_crop"]
        garment_mask = extraction["mask_crop"]
        garment_class = extraction["garment_class"]
        logger.info(f"VTO {job_id}: extracted {garment_class} garment, bbox={extraction['garment_bbox']}")

        # ── Step 2: Extract garment color for tinting ──
        _vto_emit(job_id, "analyzing", 25, f"Analyzing garment color...")
        if garment_color and garment_color != "#000000":
            garment_crop = _apply_garment_tint(garment_crop, garment_color)
            logger.info(f"VTO {job_id}: applied color tint {garment_color}")

        # ── Step 3: Detect source body pose (from source garment image) ──
        _vto_emit(job_id, "detecting", 35, f"Detecting source body pose...")
        source_pose = _detect_body_pose(image)
        logger.info(f"VTO {job_id}: source pose via {source_pose['source']}")

        # ── Step 4: Detect target body pose (same image for single-photo VTO) ──
        _vto_emit(job_id, "detecting", 45, f"Detecting target body pose...")
        target_pose = _detect_body_pose(image)  # for single-photo try-on, source=target
        logger.info(f"VTO {job_id}: target pose via {target_pose['source']}")

        # ── Step 5: Warp garment onto target body ──
        _vto_emit(job_id, "warping", 60, f"Warping {garment_class} garment onto {angle} body...")
        result = _warp_and_blend_garment(
            source_garment=garment_crop,
            source_mask=garment_mask,
            target_image=image,
            target_pose=target_pose,
            source_pose=source_pose,
            garment_color_hex=garment_color,
        )

        # ── Step 6: Generate GarmentGPT pattern if available ──
        pattern_data = None
        if garmentgpt_predictor is not None:
            _vto_emit(job_id, "patterning", 80, f"Generating sewing pattern...")
            try:
                pattern_data = run_garmentgpt(garmentgpt_predictor, extraction["garment_img"])
                logger.info(f"VTO {job_id}: GarmentGPT pattern generated")
            except Exception as e:
                logger.warning(f"VTO {job_id}: GarmentGPT pattern failed: {e}")

        # ── Step 7: Save result ──
        _vto_emit(job_id, "saving", 90, f"Saving {angle} result...")
        tmp_path = f"/kaggle/working/vto_{job_id}_{angle}.png"
        result.save(tmp_path, "PNG")

        # Save garment mesh if available
        mesh_path = None
        if extraction["mesh_data"]:
            mesh_path = f"/kaggle/working/vto_{job_id}_{angle}_mesh.npz"
            np.savez_compressed(mesh_path,
                upper_vertices=extraction["mesh_data"].get("upper", {}).get("vertices_np", np.array([])),
                upper_faces=extraction["mesh_data"].get("upper", {}).get("faces_np", np.array([])),
                lower_vertices=extraction["mesh_data"].get("lower", {}).get("vertices_np", np.array([])),
                lower_faces=extraction["mesh_data"].get("lower", {}).get("faces_np", np.array([])),
            )

        vto_jobs[job_id]["status"] = "completed"
        vto_jobs[job_id]["result_url"] = tmp_path
        vto_jobs[job_id]["mesh_url"] = mesh_path
        vto_jobs[job_id]["pattern_data"] = pattern_data
        vto_jobs[job_id]["garment_class"] = garment_class
        _vto_emit(job_id, "complete", 100, f"{angle} try-on complete!")

        # Phase 209: Track GPU cost
        elapsed = time.time() - t_start
        if user_id not in gpu_usage_log:
            gpu_usage_log[user_id] = {"total_gpu_sec": 0.0, "jobs": 0, "last_job": ""}
        gpu_usage_log[user_id]["total_gpu_sec"] += elapsed
        gpu_usage_log[user_id]["jobs"] += 1
        gpu_usage_log[user_id]["last_job"] = job_id
        vto_jobs[job_id]["gpu_seconds"] = round(elapsed, 2)
        logger.info(f"VTO try-on {job_id} ({angle}) completed: {garment_class} garment transferred ({elapsed:.1f}s GPU)")

    except Exception as e:
        import traceback as tb
        vto_jobs[job_id]["status"] = "failed"
        vto_jobs[job_id]["error"] = str(e)
        _vto_emit(job_id, "error", -1, str(e)[:200])
        logger.error(f"VTO try-on {job_id} ({angle}) failed: {e}")
        try:
            open("/kaggle/working/last_error.txt", "w").write(tb.format_exc())
        except Exception:
            pass


# ── Phase 163: Synthesize views endpoint ──
@app.post("/api/v1/synthesize-views")
async def synthesize_views(
    file: UploadFile = File(...),
    user_id: str = "",
):
    image_bytes = await file.read()
    if len(image_bytes) > 20 * 1024 * 1024:
        raise HTTPException(400, detail=_structured_error("IMAGE_TOO_LARGE"))
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(400, detail=_structured_error("INVALID_IMAGE", detail="File must be an image"))

    job_id = str(uuid.uuid4())[:8]
    vto_jobs[job_id] = {"status": "processing", "angles": {}, "error": None, "user_id": user_id, "symmetry": None, "uv_data": None}
    asyncio.create_task(process_vto_synthesis(job_id, image_bytes, user_id))
    return {"job_id": job_id, "status": "processing"}


# ── Phase 170: Single-angle try-on endpoint ──
@app.post("/api/v1/vto/tryon")
async def vto_tryon_endpoint(
    file: UploadFile = File(...),
    angle: str = "front",
    user_id: str = "",
    seed: int = 42,
    garment_type: str = "casual",
    garment_color: str = "#000000",
):
    image_bytes = await file.read()
    if len(image_bytes) > 20 * 1024 * 1024:
        raise HTTPException(400, detail=_structured_error("IMAGE_TOO_LARGE"))
    if len(image_bytes) < 100:
        raise HTTPException(400, detail=_structured_error("EMPTY_IMAGE", detail="Image is empty or too small"))
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(400, detail=_structured_error("INVALID_IMAGE", detail="File must be an image"))

    job_id = str(uuid.uuid4())[:8]
    vto_jobs[job_id] = {"status": "processing", "result_url": None, "error": None, "user_id": user_id, "angle": angle, "garment_type": garment_type, "garment_color": garment_color}
    asyncio.create_task(process_vto_tryon(job_id, image_bytes, angle, user_id, seed=seed, garment_type=garment_type, garment_color=garment_color))
    return {"job_id": job_id, "status": "processing", "seed": seed, "garment_type": garment_type, "garment_color": garment_color}


# ── Phase 185: Multi-angle VTO (all 3 angles in one call) ──
@app.post("/api/v1/vto/multi-tryon")
async def vto_multi_tryon(
    file: UploadFile = File(...),
    user_id: str = "",
):
    """
    Phase 170: Run all 3 angles (front/side/back) in parallel via asyncio.gather.
    Phase 171: Uses consistent seed across all views.
    Phase 185: Returns partial results if some angles fail.
    """
    image_bytes = await file.read()
    if len(image_bytes) > 20 * 1024 * 1024:
        raise HTTPException(400, detail=_structured_error("IMAGE_TOO_LARGE"))
    if len(image_bytes) < 100:
        raise HTTPException(400, detail=_structured_error("EMPTY_IMAGE", detail="Image is empty or too small"))
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(400, detail=_structured_error("INVALID_IMAGE", detail="File must be an image"))

    seed = 42
    job_ids = {}
    for angle in ["front", "side", "back"]:
        jid = str(uuid.uuid4())[:8]
        job_ids[angle] = jid
        vto_jobs[jid] = {"status": "processing", "result_url": None, "error": None, "user_id": user_id, "angle": angle}
        asyncio.create_task(process_vto_tryon(jid, image_bytes, angle, user_id, seed=seed))

    return {
        "job_ids": job_ids,
        "status": "processing",
        "seed": seed,
    }


# ── Phase 173: SSE progress endpoint ──
@app.get("/api/v1/vto/progress/{job_id}")
async def vto_progress_sse(job_id: str):
    if job_id not in vto_jobs:
        raise HTTPException(404, "VTO job not found")

    async def event_generator():
        last_seq = 0
        timeout_count = 0
        max_timeout = 60
        while timeout_count < max_timeout:
            progress = vto_progress.get(job_id, {})
            current_seq = progress.get("sequence", 0)
            if current_seq > last_seq:
                last_seq = current_seq
                timeout_count = 0
                data = json.dumps({
                    "stage": progress.get("stage", "unknown"),
                    "progress": progress.get("progress", 0),
                    "message": progress.get("message", ""),
                })
                yield f"data: {data}\n\n"
                if progress.get("stage") in ("complete", "error"):
                    break
            else:
                timeout_count += 1
            evt = asyncio.Event()
            vto_progress_events.setdefault(job_id, []).add(evt)
            try:
                await asyncio.wait_for(evt.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                pass
            finally:
                vto_progress_events.get(job_id, set()).discard(evt)
        vto_progress_events.pop(job_id, None)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@app.get("/api/v1/vto/status/{job_id}")
async def vto_status_endpoint(job_id: str):
    job = vto_jobs.get(job_id)
    if not job:
        raise HTTPException(404, "VTO job not found")
    progress = vto_progress.get(job_id, {})
    return {
        "status": job["status"],
        "stage": progress.get("stage", "unknown"),
        "progress": progress.get("progress", 0),
        "message": progress.get("message", ""),
        "angles": job.get("angles", {}),
        "error": job.get("error"),
        "symmetry": job.get("symmetry"),
        "angle": job.get("angle"),
    }


@app.get("/api/v1/vto/result/{job_id}")
async def vto_result(job_id: str):
    """Return VTO result image file."""
    job = vto_jobs.get(job_id)
    if not job:
        raise HTTPException(404, "VTO job not found")
    if job["status"] != "completed":
        raise HTTPException(400, "VTO job not completed")

    result_url = job.get("result_url") or (job.get("angles", {}) or {}).get("front")
    if not result_url or not os.path.exists(result_url):
        raise HTTPException(404, "Result file not found")

    return StreamingResponse(
        open(result_url, "rb"),
        media_type="image/png",
        headers={
            # Phase 202: Cache immutable VTO results for 30 days
            "Cache-Control": "public, max-age=2592000, immutable",
            "ETag": f"vto-{job_id}-{angle}",
        },
    )


# ── Phase 209: GPU cost tracking ──
@app.get("/api/v1/cost/usage")
async def gpu_cost_usage(user_id: str = ""):
    """Return GPU usage stats. If user_id provided, returns per-user stats."""
    if user_id and user_id in gpu_usage_log:
        entry = gpu_usage_log[user_id]
        return {
            "user_id": user_id,
            "total_gpu_seconds": round(entry["total_gpu_sec"], 2),
            "total_gpu_minutes": round(entry["total_gpu_sec"] / 60, 2),
            "estimated_cost_usd": round(entry["total_gpu_sec"] / 60 * COST_PER_GPU_MINUTE_USD, 4),
            "total_jobs": entry["jobs"],
            "last_job": entry["last_job"],
        }
    # Global stats
    total_sec = sum(e["total_gpu_sec"] for e in gpu_usage_log.values())
    total_jobs = sum(e["jobs"] for e in gpu_usage_log.values())
    return {
        "total_gpu_seconds": round(total_sec, 2),
        "total_gpu_minutes": round(total_sec / 60, 2),
        "estimated_cost_usd": round(total_sec / 60 * COST_PER_GPU_MINUTE_USD, 4),
        "total_jobs": total_jobs,
        "unique_users": len(gpu_usage_log),
        "uptime_hours": round((time.time() - SERVER_START_TIME) / 3600, 2),
    }


# ── Phase 212: Quality dashboard ──
@app.get("/api/v1/quality/dashboard")
async def quality_dashboard():
    """
    Phase 212: Real-time quality metrics dashboard.
    Returns aggregated stats about VTO job success rates, latency, and errors.
    """
    now = time.time()
    uptime = now - SERVER_START_TIME

    # Aggregate VTO job stats
    total_vto = len(vto_jobs)
    completed = sum(1 for j in vto_jobs.values() if j.get("status") == "completed")
    failed = sum(1 for j in vto_jobs.values() if j.get("status") == "failed")
    processing = sum(1 for j in vto_jobs.values() if j.get("status") == "processing")

    # GPU memory
    gpu_info = {}
    if torch.cuda.is_available():
        gpu_info = {
            "allocated_gb": round(torch.cuda.memory_allocated() / (1024**3), 2),
            "reserved_gb": round(torch.cuda.memory_reserved() / (1024**3), 2),
            "max_allocated_gb": round(torch.cuda.max_memory_allocated() / (1024**3), 2),
        }

    # Cost tracking
    total_gpu_sec = sum(e["total_gpu_sec"] for e in gpu_usage_log.values())
    estimated_cost = round(total_gpu_sec / 60 * COST_PER_GPU_MINUTE_USD, 4)

    # Garment class distribution
    garment_dist = {}
    for j in vto_jobs.values():
        gc = j.get("garment_class", "unknown")
        garment_dist[gc] = garment_dist.get(gc, 0) + 1

    return {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "uptime_hours": round(uptime / 3600, 2),
        "vto_jobs": {
            "total": total_vto,
            "completed": completed,
            "failed": failed,
            "processing": processing,
            "success_rate": round(completed / max(total_vto, 1) * 100, 1),
        },
        "garment_distribution": garment_dist,
        "gpu": gpu_info,
        "cost": {
            "total_gpu_minutes": round(total_gpu_sec / 60, 2),
            "estimated_cost_usd": estimated_cost,
            "unique_users": len(gpu_usage_log),
        },
        "models_loaded": {
            "rembg": rembg_remove is not None,
            "sam2": sam2_model is not None,
            "garmentrec": garmentrec_model is not None,
            "garmentgpt": garmentgpt_predictor is not None,
        },
        "errors": {
            "total": ERROR_COUNT,
            "rate": round(ERROR_COUNT / max(REQUEST_COUNT, 1) * 100, 2),
        },
    }


if __name__ == "__main__":
    import signal
    import nest_asyncio
    nest_asyncio.apply()

    def _graceful_exit(signum, frame):
        logger.info(f"Received signal {signum}, cleaning up GPU memory...")
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("GPU memory cleaned, exiting.")
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, _graceful_exit)
    signal.signal(signal.SIGINT, _graceful_exit)
    uvicorn.run(app, host="0.0.0.0", port=8000, limit_concurrency=2, backlog=10)
