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
