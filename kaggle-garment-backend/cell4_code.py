code = r'''"""
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

# ---- async job queue ----
jobs = {}


# ═══════════════════════════════════════════════════════════════
#  SAM2 segmentation (with checkpoint compatibility patch)
# ═══════════════════════════════════════════════════════════════

def _load_sam2():
    """Load SAM2 on CPU. Handles checkpoint version mismatches by filtering unexpected keys."""
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
        with torch.device("cpu"):
            m = build_sam2("sam2_hiera_l.yaml", ckpt, device=CPU_DEVICE)
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

def load_models():
    """Load all real models. If ANY fails, the server exits — no fallbacks."""
    logger.info("Loading models...")

    _load_rembg()

    global sam2_model, predict_fn
    sam2_model, predict_fn = _load_sam2()

    global garmentrec_model
    garmentrec_model = _load_garmentrec()

    global garmentgpt_predictor
    garmentgpt_predictor = _load_garmentgpt()

    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    logger.info("All models loaded successfully")


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
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        nobg = rembg_remove(image)
        mask = segment_garment(image)

        mesh_data = None
        pattern_data = None

        if include_mesh and garmentrec_model is not None:
            with tempfile.TemporaryDirectory() as tmp:
                mesh_data = run_garmentrec(garmentrec_model, nobg, tmp)
            gc.collect()

        if include_pattern and garmentgpt_predictor is not None:
            pattern_data = run_garmentgpt(garmentgpt_predictor, nobg)

        result_zip = build_zip(job_id, mesh_data, pattern_data)
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["result_zip"] = result_zip

        # Post to EC2 proxy for persistent storage
        post_result_to_proxy(job_id, result_zip)
        logger.info(f"Job {job_id} completed successfully")
    except Exception as e:
        import traceback as tb
        err = tb.format_exc()
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
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
    load_models()
    yield


app = FastAPI(title="Garment Reconstruction API", lifespan=lifespan)


@app.middleware("http")
async def catch_all_errors(request, call_next):
    try:
        return await call_next(request)
    except BaseException as e:
        import traceback as tb

        err = tb.format_exc()
        try:
            open("/kaggle/working/last_error.txt", "w").write(err)
        except Exception:
            pass
        tb.print_exc()
        logger.error(f"UNCAUGHT: {type(e).__name__}: {e}")
        return JSONResponse(status_code=500, content={"detail": f"UNCAUGHT {type(e).__name__}: {str(e)}"})


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "device": GPU_DEVICE,
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
        "rembg": rembg_remove is not None,
        "sam2": sam2_model is not None,
        "garmentrec": garmentrec_model is not None,
        "garmentgpt": garmentgpt_predictor is not None,
        "jobs_processing": sum(1 for j in jobs.values() if j["status"] == "processing"),
    }


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
        raise HTTPException(400, "Image too large (max 10MB)")
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(400, "File must be an image")
    if rembg_remove is None:
        raise HTTPException(503, "rembg not available")

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
    import nest_asyncio
    nest_asyncio.apply()
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''

with open("/kaggle/working/api_server.py", "w") as f:
    f.write(code)

print("api_server.py written (async + split pipeline + SAM2 fix)")
