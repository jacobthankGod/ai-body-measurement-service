"""
Modal GPU backend for Garment Reconstruction.
Serves the FastAPI app at https://jacobthankgod4--garment-reconstruction-garment-app.modal.run

Usage:
  modal deploy kaggle-garment-backend/modal_app.py
  modal run kaggle-garment-backend/modal_app.py  # ephemeral test
"""
import os
import sys
import time
import subprocess
from pathlib import Path

import modal

app = modal.App("garment-reconstruction")

_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git", "wget", "cmake", "libgl1-mesa-glx", "libglib2.0-0", "libsm6", "libxext6", "libxrender-dev", "libgomp1", "libopengl0", "libglu1-mesa")
    # Force numpy<2 BEFORE torch to avoid np.float removal in SMPL.py
    .run_commands(["pip install 'numpy<2.0' --force-reinstall --no-deps"])
    # Pin torch to 2.6.0 for pytorch3d wheel compatibility
    .run_commands(["pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124"])
    # Force numpy<2 AFTER torch (torch may pull numpy 2.x)
    .run_commands(["pip install 'numpy<2.0' --force-reinstall --no-deps"])
    .pip_install("fastapi", "uvicorn", "python-multipart", "httpx",
                 "Pillow>=10.0.0", "scipy>=1.14.1", "transformers", "huggingface_hub", "pooch",
                 "pymeshlab", "trimesh", "protobuf", "sentencepiece", "accelerate", "requests")
    .pip_install("hydra-core>=1.3.2", "iopath>=0.1.10", "omegaconf>=2.2")
    .pip_install("rembg", "onnxruntime")
    .run_commands(["pip install sam2 --no-deps"])
    .pip_install("vector-quantize-pytorch", "pymatting")
    .run_commands(["pip install opencv-python-headless fire llamafactory torch_geometric torch_scatter bitsandbytes loguru scikit-learn"])
    .run_commands(["pip install 'openmesh>=1.0,<2' --force-reinstall"])  # compiled from source on linux
    # pytorch3d from prebuilt wheel (CUDA 12.4, torch 2.6.0, python 3.11)
    .run_commands(["pip install https://github.com/MiroPsota/torch_packages_builder/releases/download/pytorch3d-0.7.9%2Bd9839a9/pytorch3d-0.7.9%2Bd9839a9pt2.6.0cu124-cp311-cp311-linux_x86_64.whl"])
    # Final numpy<2 downgrade (some late deps pull numpy 2.x)
    .run_commands(["pip install 'numpy<2.0' --force-reinstall --no-deps"])
    .add_local_file("kaggle-garment-backend/api_server.py", "/root/api_server.py", copy=True)
    .add_local_file("kaggle-garment-backend/generate_template_objs.py", "/root/generate_template_objs.py", copy=True)
)

def setup():
    """Clone repos and download weights. Idempotent."""
    HUGGINGFACE_TOKEN = os.environ.get("HUGGINGFACE_TOKEN", "")
    
    WORKING_DIR = Path("/root")
    GARMENT_REC_DIR = WORKING_DIR / "GarmentRec"
    GARMENT_GPT_DIR = WORKING_DIR / "Garment-GPT"
    WEIGHTS_DIR = WORKING_DIR / "weights"
    SAM2_DIR = WEIGHTS_DIR / "sam2"
    SMPL_DIR = GARMENT_REC_DIR / "smpl_pytorch" / "model"
    REC_WEIGHT_DIR = GARMENT_REC_DIR / "models" / "mrf_0.1_shading_0.1"

    def log(msg):
        print(f"[setup] {msg}", flush=True)

    def git_clone(url, dest):
        if dest.exists():
            log(f"Already cloned: {dest.name}")
            return
        log(f"Cloning {dest.name}...")
        subprocess.check_call(
            ["git", "clone", "--depth=1", url, str(dest)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        log(f"Cloned {dest.name}")

    def hf_download(repo_id, filename, local_dir):
        from huggingface_hub import hf_hub_download
        path = Path(local_dir) / filename
        if path.exists():
            log(f"Already downloaded: {filename}")
            return
        log(f"Downloading {filename}...")
        hf_hub_download(
            repo_id=repo_id, filename=filename,
            local_dir=str(local_dir), local_dir_use_symlinks=False,
            token=HUGGINGFACE_TOKEN or None,
        )
        log(f"Downloaded {filename}")

    # Clone repos
    git_clone("https://github.com/worryDes/GarmentRec.git", GARMENT_REC_DIR)
    git_clone("https://github.com/ChimerAI-MMLab/Garment-GPT.git", GARMENT_GPT_DIR)

    # SMPL model
    SMPL_DIR.mkdir(parents=True, exist_ok=True)
    hf_download("jacobthankgod4/smpl-model-garmentrec", "neutral_smpl_with_cocoplus_reg.txt", SMPL_DIR)

    # SAM2 weights
    SAM2_DIR.mkdir(parents=True, exist_ok=True)
    try:
        hf_download("facebook/sam2-hiera-large", "sam2_hiera_large.pt", SAM2_DIR)
    except Exception as e:
        log(f"SAM2 download failed (non-fatal): {e}")

    # GarmentRec model weights
    REC_WEIGHT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        hf_download(
            "jacobthankgod4/smpl-model-garmentrec",
            "mrf_0.1_shading_0.1_pca64_ep100_bth0.pth",
            REC_WEIGHT_DIR,
        )
    except Exception as e:
        log(f"GarmentRec weights download failed (non-fatal): {e}")

    # GarmentRec data assets (tmps/, texture_data/ - from HuggingFace dataset)
    data_dir = GARMENT_REC_DIR / "data"
    tmps_dir = data_dir / "tmps"
    if not tmps_dir.exists():
        try:
            from huggingface_hub import snapshot_download
            log("Downloading GarmentRec data assets from HuggingFace dataset...")
            snapshot_download(
                repo_id="jacobthankgod4/garmentrec-data-assets",
                repo_type="dataset",
                local_dir=str(data_dir),
                local_dir_use_symlinks=False,
                token=HUGGINGFACE_TOKEN or None,
                max_workers=2,
            )
            log("GarmentRec data assets downloaded")
        except Exception as e:
            log(f"GarmentRec data assets download failed: {e}")

    # Generate missing garment_tmp.obj and garment_tmp_subdivide_uv_new.obj
    # from PCA mean data using 2D Delaunay triangulation
    if tmps_dir.exists():
        try:
            log("Generating GarmentRec template OBJ files from PCA mean...")
            sys.path.insert(0, "/root")
            import generate_template_objs as gen
            gen.generate_all_templates(str(tmps_dir))
            log("Template OBJ generation complete")
        except Exception as e:
            log(f"Template OBJ generation failed (non-fatal): {e}")
    else:
        log(f"tmps_dir {tmps_dir} does not exist, skipping template generation")

    # GarmentGPT checkpoints (from HuggingFace ChimerAI/GarmentGPT)
    # Includes: vlm/checkpoint-12844 (14GB LLM), vqvae/ (Codec model), rt/ (RT decoder)
    gpt_checkpoint_dir = GARMENT_GPT_DIR / "checkpoints" / "vlm" / "checkpoint-12844"
    gpt_checkpoint_dir.mkdir(parents=True, exist_ok=True)
    vqvae_dir = GARMENT_GPT_DIR / "checkpoints" / "vqvae"
    rt_dir = GARMENT_GPT_DIR / "checkpoints" / "rt"
    try:
        from huggingface_hub import snapshot_download
        # Download all GarmentGPT files: VLM + VQVAE + RT
        snapshot_download(
            repo_id="ChimerAI/GarmentGPT",
            allow_patterns=["vlm/checkpoint-12844/*", "vqvae/*", "rt/*"],
            local_dir=str(GARMENT_GPT_DIR / "checkpoints"),
            local_dir_use_symlinks=False,
            token=HUGGINGFACE_TOKEN or None,
            max_workers=4,
        )
        log("GarmentGPT all checkpoints downloaded")
    except Exception as e:
        log(f"GarmentGPT checkpoint download failed: {e}")

    # Pre-download rembg u2net model (~176MB)
    u2net_dir = Path.home() / ".u2net"
    u2net_dir.mkdir(parents=True, exist_ok=True)
    u2net_path = u2net_dir / "u2net.onnx"
    if not u2net_path.exists():
        try:
            log("Downloading rembg u2net model (~176MB)...")
            import urllib.request
            urllib.request.urlretrieve(
                "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx",
                str(u2net_path),
            )
            log(f"u2net model downloaded ({u2net_path.stat().st_size / 1024 / 1024:.0f}MB)")
        except Exception as e:
            log(f"u2net download failed (will download at runtime): {e}")
    else:
        log(f"u2net model already cached ({u2net_path.stat().st_size / 1024 / 1024:.0f}MB)")

    # Pre-warm rembg (import + small dummy inference) to cache the model
    try:
        log("Warming up rembg...")
        from rembg import remove as _rembg_remove
        from PIL import Image as _PIL
        _dummy = _PIL.new("RGB", (8, 8), (255, 255, 255))
        _rembg_remove(_dummy)
        log("rembg warmup complete")
    except Exception as e:
        log(f"rembg warmup failed: {e}")

    log("Setup complete")


def install_missing_deps():
    """Install packages not available during image build (e.g. pytorch3d, llamafactory)."""
    import subprocess, sys as _sys

    deps = []
    try:
        import pytorch3d  # noqa: F401
    except ImportError:
        deps.append("pytorch3d")

    try:
        import llamafactory  # noqa: F401
    except ImportError:
        deps.append("llamafactory")

    if not deps:
        return

    print(f"[deps] Installing missing: {deps}", flush=True)
    for dep in deps:
        try:
            if dep == "pytorch3d":
                subprocess.check_call([
                    _sys.executable, "-m", "pip", "install",
                    "https://github.com/MiroPsota/torch_packages_builder/releases/download/pytorch3d-0.7.9%2Bd9839a9/pytorch3d-0.7.9%2Bd9839a9pt2.6.0cu124-cp311-cp311-linux_x86_64.whl",
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.check_call([
                    _sys.executable, "-m", "pip", "install", dep,
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"[deps] Installed {dep}", flush=True)
        except Exception as e:
            print(f"[deps] Failed to install {dep}: {e}", flush=True)


@app.function(
    image=_image,
    gpu="t4",
    secrets=[modal.Secret.from_name("huggingface-token")],
    scaledown_window=1200,
    timeout=36000,
)
@modal.asgi_app()
def garment_app():
    """Serve the FastAPI app via Modal's HTTP endpoint."""
    setup()
    install_missing_deps()
    os.chdir("/root")
    sys.path.insert(0, "/root")
    from api_server import app as fastapi_app
    return fastapi_app


@app.function(
    image=_image,
    gpu="t4",
    secrets=[modal.Secret.from_name("huggingface-token")],
    timeout=36000,
)
def run_setup():
    """Run setup (clone, download weights) on Modal GPU, for testing."""
    setup()
    print("Setup done")
    # Also run template generation as a test
    tmps_dir = Path("/root") / "GarmentRec" / "data" / "tmps"
    if tmps_dir.exists():
        sys.path.insert(0, "/root")
        import generate_template_objs as gen
        gen.generate_all_templates(str(tmps_dir))
    print("Template generation done")
