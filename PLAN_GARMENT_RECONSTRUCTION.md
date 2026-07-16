# Garment Reconstruction Pipeline — Implementation Plan

**Goal:** Image → 3D Garment Mesh + Sewing Pattern — Zero-Cost, Self-Hosted
**Date:** 2026-07-10
**Status:** PLANNING

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Infrastructure](#2-infrastructure)
3. [Kaggle GPU Backend](#3-kaggle-gpu-backend)
4. [EC2 Proxy Layer](#4-ec2-proxy-layer)
5. [Cloudflare Tunnel](#5-cloudflare-tunnel)
6. [Model Integration](#6-model-integration)
7. [API Design](#7-api-design)
8. [Frontend Integration](#8-frontend-integration)
9. [Data Flow](#9-data-flow)
10. [Deployment](#10-deployment)
11. [Testing](#11-testing)
12. [Monitoring & Maintenance](#12-monitoring--maintenance)
13. [Cost Analysis](#13-cost-analysis)
14. [Security](#14-security)
15. [Scaling Strategy](#15-scaling-strategy)
16. [Rollout Plan](#16-rollout-plan)
17. [Risk Mitigation](#17-risk-mitigation)
18. [Future Enhancements](#18-future-enhancements)

---

## 1. Architecture Overview

### 1.1 System Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                        USER BROWSER                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Upload Photo │  │ View 3D Mesh│  │ View Sewing Pattern     │  │
│  └──────┬──────┘  └──────▲──────┘  └────────────▲────────────┘  │
│         │                │                      │                │
└─────────┼────────────────┼──────────────────────┼────────────────┘
          │                │                      │
          ▼                │                      │
┌──────────────────────────────────────────────────────────────────┐
│                    EC2 t3.micro (PROXY)                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ FastAPI      │  │ Auth/Rate   │  │ Response Cache          │  │
│  │ Proxy Server │  │ Limiter     │  │ (Redis/SQLite)          │  │
│  └──────┬──────┘  └─────────────┘  └─────────────────────────┘  │
│         │                                                        │
└─────────┼────────────────────────────────────────────────────────┘
          │ HTTPS
          ▼
┌──────────────────────────────────────────────────────────────────┐
│              CLOUDFLARE TUNNEL (FREE)                            │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  https://garment-kernel.trycloudflare.com                   │ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────┬───────────────────────────────────────┘
                           │ HTTPS
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                 KAGGLE NOTEBOOK (GPU BACKEND)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ FastAPI       │  │ SAM2 Segment │  │ GarmentRec           │  │
│  │ Inference API │  │ (preprocess) │  │ (3D mesh)            │  │
│  └──────┬───────┘  └──────────────┘  └──────────────────────┘  │
│         │                                                        │
│  ┌──────▼───────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ GarmentGPT   │  │ GarmentCode  │  │ Result Packaging     │  │
│  │ (pattern)    │  │ (sim)        │  │ (zip + upload)       │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                  │
│  GPU: T4 x2 (30GB VRAM)  |  Storage: 73GB persistent           │
│  Session: 12hrs auto-restart  |  Quota: 30 GPU-hrs/week        │
└──────────────────────────────────────────────────────────────────┘
```

### 1.2 Component Responsibilities

| Component | Runs On | Purpose | Cost |
|---|---|---|---|
| Frontend (Next.js) | Existing EC2 | User UI, upload, 3D viewer | $0 (existing) |
| Proxy Server | EC2 t3.micro | Auth, routing, caching, rate limiting | $0 (existing) |
| Cloudflare Tunnel | Cloudflare free | HTTPS tunnel to Kaggle notebook | $0 |
| GPU Backend | Kaggle free tier | Model inference (mesh + pattern) | $0 |
| Model Storage | Kaggle datasets (73GB) | Pre-cached model weights | $0 |
| Result Storage | Supabase storage | Generated meshes + patterns | $0 (existing) |

### 1.3 Key Design Decisions

1. **Kaggle over Colab:** More reliable quota (30 GPU-hrs/week guaranteed), persistent storage (73GB), longer sessions (12hrs), and auto-restart capability
2. **Cloudflare Tunnel over ngrok:** Free, no signup, stable URLs, no bandwidth limits
3. **GarmentRec over GarVerseLOD for primary mesh:** Lighter (~3GB VRAM vs ~10GB), MIT license, works on T4 comfortably
4. **GarmentGPT for patterns:** Outputs GCD format compatible with GarmentCode, Apache 2.0, ~5GB VRAM
5. **Proxy architecture:** EC2 handles auth/routing, Kaggle handles compute — clean separation of concerns

---

## 2. Infrastructure

### 2.1 Existing Resources

| Resource | Details | Status |
|---|---|---|
| EC2 Instance | t3.micro, Ubuntu, 1GB RAM | Running |
| Domain | korra.work | Configured |
| Nginx | Reverse proxy, SSL | Configured |
| Supabase | DB + Auth + Storage | Active |
| Docker | korra-ai-prod container | Running |

### 2.2 New Resources Needed

| Resource | Details | Cost |
|---|---|---|
| Kaggle Account | Free tier, phone-verified | $0 |
| Cloudflare Account | Free tier, tunnel | $0 |
| Kaggle Dataset | For model weights (~20GB) | $0 |

### 2.3 Kaggle Account Setup

```
Steps:
1. Go to kaggle.com
2. Sign up with Google/GitHub
3. Verify phone number (required for GPU + API access)
4. Generate API token: kaggle.json → ~/.kaggle/kaggle.json
5. Accept competition rules (if needed for GPU access)
6. Enable GPU in Account Settings → Notebook → GPU = "Always On"
```

### 2.4 Cloudflare Account Setup

```
Steps:
1. Go to dash.cloudflare.com
2. Sign up (free)
3. Install cloudflared: brew install cloudflare/cloudflare/cloudflared
4. No domain needed for tunnel (uses trycloudflare.com)
5. Login: cloudflared tunnel login (optional, for persistent tunnels)
```

---

## 3. Kaggle GPU Backend

### 3.1 Notebook Structure

```
kaggle-garment-backend/
├── notebook.ipynb              # Main Kaggle notebook
├── api_server.py               # FastAPI inference server
├── models/
│   ├── garmentrec/
│   │   ├── model.pth           # GarmentRec weights
│   │   └── config.yaml
│   ├── garmentgpt/
│   │   ├── checkpoints/        # VLM + decoder weights
│   │   └── configs/
│   ├── garmentcode/
│   │   ├── pygarment/          # GarmentCode library
│   │   └── garment_programs/
│   └── sam2/
│       └── sam2_hiera_large.pt # Segmentation model
├── utils/
│   ├── image_utils.py          # Preprocessing, segmentation
│   ├── mesh_utils.py           # OBJ export, mesh operations
│   ├── pattern_utils.py        # GCD JSON processing
│   └── cloudflare_tunnel.py    # Tunnel management
├── outputs/                    # Temporary inference outputs
├── requirements.txt
└── setup.sh                    # One-click setup script
```

### 3.2 Model Weight Download Strategy

**Problem:** Kaggle sessions are ephemeral. Model weights must persist.

**Solution:** Upload weights to a Kaggle Dataset, download on notebook start.

```python
# Cell 1: Download model weights from Kaggle Dataset
import kaggle
import os

KAGGLE_DATASET = "garment-models/weights"  # Dataset slug
WEIGHTS_DIR = "/kaggle/working/weights"

os.makedirs(WEIGHTS_DIR, exist_ok=True)

# Download if not already cached
if not os.path.exists(f"{WEIGHTS_DIR}/garmentrec"):
    !kaggle datasets download -d {KAGGLE_DATASET} -p {WEIGHTS_DIR} --unzip
    print("✅ Model weights downloaded")
else:
    print("✅ Model weights already cached")
```

**Kaggle Dataset Structure:**
```
garment-models/weights/
├── garmentrec/
│   └── mrf_0.1_shading_0.1_pca64_ep100_bth0.pth  (~500MB)
├── garmentgpt/
│   ├── vlm/checkpoint-12844/                       (~4GB)
│   ├── codec/config_vq1024.yaml                    (~100MB)
│   └── rt/config_rt_euler.yaml                     (~100MB)
├── sam2/
│   └── sam2_hiera_large.pt                         (~1GB)
└── garmentcode/
    └── pygarment/                                  (~50MB)
                             Total: ~5.7GB (fits in 73GB storage)
```

### 3.3 Notebook Initialization

```python
# Cell 2: Install dependencies
!pip install -q torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
!pip install -q pytorch3d -f https://dl.fbaipublicfiles.com/pytorch3d/packaging/wheels/py310_cu121_pyt2.1.1/download.html
!pip install -q fastapi uvicorn python-multipart pillow numpy trimesh rembg
!pip install -q git+https://github.com/facebookresearch/sam2.git
!pip install -q cloudflared

print("✅ Dependencies installed")
```

```python
# Cell 3: Initialize models
import torch
import sys

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {DEVICE}")

# Load GarmentRec
sys.path.append("/kaggle/working/garmentrec")
from models.garmentrec_infer import GarmentRecModel
garmentrec = GarmentRecModel(
    weights_path=f"{WEIGHTS_DIR}/garmentrec/model.pth",
    device=DEVICE
)
print("✅ GarmentRec loaded")

# Load GarmentGPT
sys.path.append("/kaggle/working/garmentgpt")
from models.garmentgpt_infer import GarmentGPTPipeline
garmentgpt = GarmentGPTPipeline(
    vlm_path=f"{WEIGHTS_DIR}/garmentgpt/vlm",
    codec_path=f"{WEIGHTS_DIR}/garmentgpt/codec",
    rt_path=f"{WEIGHTS_DIR}/garmentgpt/rt",
    device=DEVICE
)
print("✅ GarmentGPT loaded")

# Load SAM2
from sam2.build_sam import build_sam2
sam2 = build_sam2(
    model_cfg="sam2_hiera_l.yaml",
    ckpt=f"{WEIGHTS_DIR}/sam2/sam2_hiera_large.pt",
    device=DEVICE
)
print("✅ SAM2 loaded")

# Load GarmentCode
sys.path.append(f"{WEIGHTS_DIR}/garmentcode")
print("✅ GarmentCode loaded")

print(f"\n🎯 All models loaded on {DEVICE}")
print(f"   GarmentRec: ~3GB VRAM")
print(f"   GarmentGPT: ~5GB VRAM")
print(f"   SAM2: ~1GB VRAM")
print(f"   Total: ~9GB (fits in 30GB T4 x2)")
```

### 3.4 Inference Pipeline

```python
# Cell 4: Core inference functions
from PIL import Image
import numpy as np
import json
import tempfile
import zipfile
import io

def preprocess_image(image_bytes: bytes) -> dict:
    """
    Step 1: Preprocess uploaded image
    - Load image
    - Remove background (rembg)
    - Segment garment (SAM2)
    - Return: original, background-removed, garment mask
    """
    from rembg import remove
    from PIL import Image

    # Load
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    # Background removal
    img_nobg = remove(img)

    # SAM2 segmentation (garment region)
    mask = segment_garment(sam2, img)

    return {
        "original": img,
        "nobg": img_nobg,
        "mask": mask,
        "size": img.size
    }

def segment_garment(sam2_model, image: Image.Image) -> np.ndarray:
    """
    Use SAM2 to segment the garment from the image.
    Returns binary mask.
    """
    # Convert to numpy for SAM2
    img_np = np.array(image)

    # Use point prompts (center of image as garment seed)
    h, w = img_np.shape[:2]
    center_point = np.array([[w // 2, h // 2]])

    # SAM2 inference
    from sam2.sam2_image_predictor import SAM2ImagePredictor
    predictor = SAM2ImagePredictor(sam2_model)
    predictor.set_image(img_np)

    masks, scores, logits = predictor.predict(
        point_coords=center_point,
        point_labels=np.array([1]),  # foreground
        multimask_output=True
    )

    # Pick best mask
    best_mask = masks[scores.argmax()]
    return best_mask.astype(np.uint8) * 255

def reconstruct_3d_mesh(preprocessed: dict) -> dict:
    """
    Step 2: Reconstruct 3D garment mesh from image
    Uses GarmentRec for lightweight, high-quality reconstruction.
    """
    result = garmentrec.reconstruct(
        image=preprocessed["original"],
        mask=preprocessed["mask"],
        displacement_scale=0.005
    )

    return {
        "vertices": result["vertices"],      # (N, 3) numpy array
        "faces": result["faces"],            # (F, 3) numpy array
        "normals": result["normals"],        # (N, 3) numpy array
        "vertex_colors": result.get("colors"),  # (N, 3) optional
        "format": "obj"
    }

def generate_sewing_pattern(preprocessed: dict) -> dict:
    """
    Step 3: Generate sewing pattern from image
    Uses GarmentGPT for structured pattern output.
    """
    result = garmentgpt.generate(
        image=preprocessed["nobg"],
        mask=preprocessed["mask"]
    )

    return {
        "pattern_json": result["pattern"],   # GCD format JSON
        "panels": result["panels"],          # Panel descriptions
        "stitches": result["stitches"],      # Stitch relationships
        "format": "gcd_json"
    }

def simulate_pattern_to_mesh(pattern_json: dict, body_params: dict = None) -> dict:
    """
    Step 4: Simulate sewing pattern into 3D mesh
    Uses GarmentCode XPBD simulator.
    """
    from pygarment import GarmentPattern
    from pygarment.simulate import Simulator

    # Parse pattern
    pattern = GarmentPattern.from_dict(pattern_json)

    # Simulate
    sim = Simulator(
        pattern=pattern,
        body=body_params,  # Optional SMPL body params
        steps=300
    )
    sim.run()

    mesh = sim.get_mesh()

    return {
        "vertices": np.array(mesh.vertices),
        "faces": np.array(mesh.faces),
        "format": "obj"
    }

def package_results(mesh_data: dict, pattern_data: dict, image_id: str) -> dict:
    """
    Step 5: Package all results into downloadable archive.
    """
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # 1. 3D mesh as OBJ
        obj_content = vertices_faces_to_obj(
            mesh_data["vertices"],
            mesh_data["faces"],
            mesh_data.get("normals"),
            mesh_data.get("vertex_colors")
        )
        zf.writestr(f"{image_id}/garment_mesh.obj", obj_content)

        # 2. Sewing pattern JSON
        zf.writestr(
            f"{image_id}/sewing_pattern.json",
            json.dumps(pattern_data["pattern_json"], indent=2)
        )

        # 3. Metadata
        metadata = {
            "image_id": image_id,
            "mesh_vertices": len(mesh_data["vertices"]),
            "mesh_faces": len(mesh_data["faces"]),
            "pattern_panels": len(pattern_data.get("panels", [])),
            "format_version": "1.0",
            "models_used": {
                "mesh": "GarmentRec",
                "pattern": "GarmentGPT",
                "simulation": "GarmentCode"
            }
        }
        zf.writestr(f"{image_id}/metadata.json", json.dumps(metadata, indent=2))

    buffer.seek(0)
    return {
        "zip_bytes": buffer.read(),
        "zip_size_mb": len(buffer.read()) / (1024 * 1024)
    }

def vertices_faces_to_obj(vertices, faces, normals=None, colors=None):
    """Convert vertices/faces to OBJ format string."""
    lines = ["# Garment Reconstruction Output"]

    if colors is not None:
        for v, c in zip(vertices, colors):
            lines.append(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f} {c[0]:.3f} {c[1]:.3f} {c[2]:.3f}")
    else:
        for v in vertices:
            lines.append(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}")

    if normals is not None:
        for n in normals:
            lines.append(f"vn {n[0]:.6f} {n[1]:.6f} {n[2]:.6f}")

    for f in faces:
        # OBJ is 1-indexed
        lines.append(f"f {f[0]+1} {f[1]+1} {f[2]+1}")

    return "\n".join(lines)
```

### 3.5 FastAPI Server

```python
# Cell 5: FastAPI inference server
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
import uuid
import time

app = FastAPI(
    title="Garment Reconstruction API",
    description="Image → 3D Mesh + Sewing Pattern",
    version="1.0.0"
)

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "gpu": DEVICE,
        "models_loaded": {
            "garmentrec": garmentrec is not None,
            "garmentgpt": garmentgpt is not None,
            "sam2": sam2 is not None
        }
    }

@app.post("/api/v1/reconstruct")
async def reconstruct_garment(
    file: UploadFile = File(...),
    output_format: str = "zip",  # "zip" or "json"
    include_mesh: bool = True,
    include_pattern: bool = True,
    body_params: str = None  # JSON string of SMPL params (optional)
):
    """
    Full pipeline: Image → 3D Mesh + Sewing Pattern.

    Accepts: JPEG/PNG image of a garment (on person, mannequin, or flat lay)
    Returns: ZIP with OBJ mesh + GCD pattern JSON + metadata
    """
    start_time = time.time()
    image_id = str(uuid.uuid4())[:8]

    try:
        # Validate input
        if not file.content_type.startswith("image/"):
            raise HTTPException(400, "File must be an image")

        image_bytes = await file.read()
        if len(image_bytes) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(400, "Image too large (max 10MB)")

        print(f"[{image_id}] Processing {file.filename} ({len(image_bytes)/1024:.0f}KB)")

        # Step 1: Preprocess
        print(f"[{image_id}] Step 1/4: Preprocessing...")
        preprocessed = preprocess_image(image_bytes)

        # Step 2: 3D mesh reconstruction
        mesh_data = None
        if include_mesh:
            print(f"[{image_id}] Step 2/4: 3D mesh reconstruction...")
            mesh_data = reconstruct_3d_mesh(preprocessed)

        # Step 3: Sewing pattern generation
        pattern_data = None
        if include_pattern:
            print(f"[{image_id}] Step 3/4: Sewing pattern generation...")
            pattern_data = generate_sewing_pattern(preprocessed)

        # Step 4: Package results
        print(f"[{image_id}] Step 4/4: Packaging results...")

        if output_format == "zip":
            result = package_results(mesh_data, pattern_data, image_id)
            elapsed = time.time() - start_time
            print(f"[{image_id}] ✅ Complete in {elapsed:.1f}s")

            return StreamingResponse(
                io.BytesIO(result["zip_bytes"]),
                media_type="application/zip",
                headers={
                    "Content-Disposition": f"attachment; filename=garment_{image_id}.zip",
                    "X-Processing-Time": f"{elapsed:.2f}",
                    "X-Mesh-Vertices": str(len(mesh_data["vertices"])) if mesh_data else "0",
                    "X-Pattern-Panels": str(len(pattern_data.get("panels", []))) if pattern_data else "0"
                }
            )
        else:
            # Return JSON (lighter, for API consumers)
            elapsed = time.time() - start_time
            return JSONResponse({
                "image_id": image_id,
                "mesh": {
                    "vertices_count": len(mesh_data["vertices"]) if mesh_data else 0,
                    "faces_count": len(mesh_data["faces"]) if mesh_data else 0,
                    "obj_base64": base64.b64encode(
                        vertices_faces_to_obj(
                            mesh_data["vertices"],
                            mesh_data["faces"]
                        ).encode()
                    ).decode() if mesh_data else None
                },
                "pattern": pattern_data["pattern_json"] if pattern_data else None,
                "processing_time": elapsed
            })

    except HTTPException:
        raise
    except Exception as e:
        print(f"[{image_id}] ❌ Error: {str(e)}")
        raise HTTPException(500, f"Processing failed: {str(e)}")

@app.post("/api/v1/mesh-only")
async def reconstruct_mesh_only(file: UploadFile = File(...)):
    """Quick endpoint: Image → 3D mesh only (no pattern)."""
    # ... (same as above, but skip pattern generation)
    pass

@app.post("/api/v1/pattern-only")
async def generate_pattern_only(file: UploadFile = File(...)):
    """Quick endpoint: Image → Sewing pattern only (no mesh)."""
    # ... (same as above, but skip mesh reconstruction)
    pass

# Run server
import uvicorn
uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## 4. EC2 Proxy Layer

### 4.1 Proxy Server Code

```python
# /home/ubuntu/garment-proxy/server.py
"""
EC2 Proxy Server for Garment Reconstruction.
Routes requests from frontend to Kaggle GPU backend.
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
import httpx
import asyncio
import hashlib
import json
import os
import time
import sqlite3
from datetime import datetime

app = FastAPI(title="Garment Proxy")

# Configuration
KAGGLE_TUNNEL_URL = os.getenv(
    "KAGGLE_TUNNEL_URL",
    "https://garment-kernel.trycloudflare.com"
)
CACHE_DB = "/home/ubuntu/garment-proxy/cache.db"
MAX_RETRIES = 3
TIMEOUT_SECONDS = 120  # 2 minutes per request

# Initialize cache DB
def init_cache():
    conn = sqlite3.connect(CACHE_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            image_hash TEXT PRIMARY KEY,
            result_zip BLOB,
            created_at TIMESTAMP,
            hit_count INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_cache()

# Rate limiting
rate_limits = {}  # ip -> (count, window_start)
RATE_LIMIT = 10  # requests per minute per IP

def check_rate_limit(ip: str) -> bool:
    now = time.time()
    if ip not in rate_limits:
        rate_limits[ip] = (1, now)
        return True
    count, window_start = rate_limits[ip]
    if now - window_start > 60:
        rate_limits[ip] = (1, now)
        return True
    if count >= RATE_LIMIT:
        return False
    rate_limits[ip] = (count + 1, window_start)
    return True

@app.get("/health")
async def health():
    """Check proxy health and Kaggle backend connectivity."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{KAGGLE_TUNNEL_URL}/health")
            kaggle_healthy = resp.status_code == 200
    except:
        kaggle_healthy = False

    return {
        "status": "healthy",
        "kaggle_backend": "connected" if kaggle_healthy else "disconnected",
        "cache_entries": get_cache_count(),
        "uptime": get_uptime()
    }

@app.post("/api/v2/garment/reconstruct")
async def reconstruct_garment(
    file: UploadFile = File(...),
    include_mesh: bool = True,
    include_pattern: bool = True
):
    """
    Main reconstruction endpoint.
    Proxies to Kaggle GPU backend with caching.
    """
    # Rate limit check
    client_ip = "unknown"  # Get from request headers in production
    if not check_rate_limit(client_ip):
        raise HTTPException(429, "Rate limit exceeded. Try again in 1 minute.")

    # Read and hash the image
    image_bytes = await file.read()
    image_hash = hashlib.sha256(image_bytes).hexdigest()[:16]

    # Check cache
    cached = get_cached_result(image_hash)
    if cached:
        return StreamingResponse(
            io.BytesIO(cached),
            media_type="application/zip",
            headers={"X-Cache": "HIT"}
        )

    # Forward to Kaggle backend
    for attempt in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
                # Multipart form data
                files = {
                    "file": (file.filename, image_bytes, file.content_type)
                }
                params = {
                    "include_mesh": include_mesh,
                    "include_pattern": include_pattern
                }

                resp = await client.post(
                    f"{KAGGLE_TUNNEL_URL}/api/v1/reconstruct",
                    files=files,
                    params=params
                )

                if resp.status_code == 200:
                    # Cache the result
                    cache_result(image_hash, resp.content)

                    return StreamingResponse(
                        io.BytesIO(resp.content),
                        media_type="application/zip",
                        headers={
                            "X-Cache": "MISS",
                            "X-Processing-Time": resp.headers.get("X-Processing-Time", "unknown")
                        }
                    )
                else:
                    print(f"Kaggle returned {resp.status_code}: {resp.text[:200]}")

        except httpx.TimeoutException:
            print(f"Attempt {attempt + 1}/{MAX_RETRIES}: Timeout")
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
        except Exception as e:
            print(f"Attempt {attempt + 1}/{MAX_RETRIES}: {str(e)}")
            await asyncio.sleep(2 ** attempt)

    raise HTTPException(503, "Garment reconstruction service temporarily unavailable")

def get_cached_result(image_hash: str) -> bytes | None:
    conn = sqlite3.connect(CACHE_DB)
    row = conn.execute(
        "SELECT result_zip FROM cache WHERE image_hash = ?",
        (image_hash,)
    ).fetchone()
    conn.close()
    if row:
        # Update hit count
        conn = sqlite3.connect(CACHE_DB)
        conn.execute(
            "UPDATE cache SET hit_count = hit_count + 1 WHERE image_hash = ?",
            (image_hash,)
        )
        conn.commit()
        conn.close()
        return row[0]
    return None

def cache_result(image_hash: str, data: bytes):
    conn = sqlite3.connect(CACHE_DB)
    conn.execute(
        "INSERT OR REPLACE INTO cache (image_hash, result_zip, created_at) VALUES (?, ?, ?)",
        (image_hash, data, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

def get_cache_count() -> int:
    conn = sqlite3.connect(CACHE_DB)
    count = conn.execute("SELECT COUNT(*) FROM cache").fetchone()[0]
    conn.close()
    return count

def get_uptime() -> float:
    # Simple uptime tracking
    return time.time() - app.start_time if hasattr(app, 'start_time') else 0

app.start_time = time.time()
```

### 4.2 Systemd Service

```ini
# /etc/systemd/system/garment-proxy.service
[Unit]
Description=Garment Reconstruction Proxy
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/garment-proxy
ExecStart=/usr/bin/python3 server.py
Restart=always
RestartSec=5
Environment=KAGGLE_TUNNEL_URL=https://garment-kernel.trycloudflare.com
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

### 4.3 Nginx Configuration

```nginx
# Add to /etc/nginx/sites-enabled/korra

# Garment reconstruction proxy
location /api/v2/garment/ {
    proxy_pass http://127.0.0.1:8001;  # Garment proxy port
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # Large file support for ZIP responses
    proxy_buffering off;
    proxy_read_timeout 180s;
    client_max_body_size 20M;

    # CORS headers
    add_header Access-Control-Allow-Origin *;
    add_header Access-Control-Allow-Methods "POST, GET, OPTIONS";
    add_header Access-Control-Allow-Headers "Content-Type, Authorization";
}
```

---

## 5. Cloudflare Tunnel

### 5.1 Tunnel Setup on Kaggle

```python
# Cell 6: Start Cloudflare Tunnel
import subprocess
import threading
import time

def start_tunnel(port=8000):
    """
    Start Cloudflare Tunnel to expose the Kaggle notebook's
    FastAPI server to the internet.
    """
    cmd = [
        "cloudflared", "tunnel",
        "--url", f"http://localhost:{port}",
        "--no-autoupdate"
    ]

    # Run in background thread
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Parse tunnel URL from stderr
    tunnel_url = None
    for line in process.stderr:
        if "trycloudflare.com" in line:
            tunnel_url = line.split("https://")[-1].strip()
            print(f"🌐 Tunnel URL: https://{tunnel_url}")
            break

    return process, tunnel_url

# Start tunnel
tunnel_process, TUNNEL_URL = start_tunnel(8000)
print(f"✅ Tunnel active: {TUNNEL_URL}")
```

### 5.2 Tunnel Persistence

```python
# Cell 7: Auto-restart tunnel on failure
def monitor_tunnel():
    """Monitor tunnel and restart if it dies."""
    while True:
        if tunnel_process.poll() is not None:
            print("⚠️ Tunnel died, restarting...")
            global tunnel_process, TUNNEL_URL
            tunnel_process, TUNNEL_URL = start_tunnel(8000)
        time.sleep(30)

# Start monitoring in background
monitor_thread = threading.Thread(target=monitor_tunnel, daemon=True)
monitor_thread.start()
```

### 5.3 Tunnel Health Check

```python
# Cell 8: Health check endpoint (already in FastAPI)
@app.get("/tunnel/health")
async def tunnel_health():
    return {
        "tunnel_url": TUNNEL_URL,
        "tunnel_alive": tunnel_process.poll() is None,
        "gpu_device": DEVICE,
        "timestamp": datetime.now().isoformat()
    }
```

---

## 6. Model Integration

### 6.1 GarmentRec Integration

```python
# utils/garmentrec_infer.py
"""
GarmentRec: Individual Garment Reconstruction from Monocular Image.
Paper: IEEE TIP 2026
License: MIT
"""
import torch
import torch.nn.functional as F
from PIL import Image
import numpy as np
import trimesh

class GarmentRecModel:
    def __init__(self, weights_path: str, device: str = "cuda"):
        self.device = device
        self.model = self._load_model(weights_path)
        self.model.eval()

    def _load_model(self, weights_path):
        """Load GarmentRec model."""
        from models.garment_template import GarmentTemplate

        model = GarmentTemplate(
            latent_dim=64,
            use_shading=True,
            use_mrf=True
        )

        checkpoint = torch.load(weights_path, map_location=self.device)
        model.load_state_dict(checkpoint['model_state_dict'])
        model.to(self.device)

        return model

    @torch.no_grad()
    def reconstruct(self, image: Image.Image, mask: np.ndarray, displacement_scale: float = 0.005) -> dict:
        """
        Reconstruct 3D garment mesh from single image.

        Args:
            image: PIL Image (RGB)
            mask: Binary mask of garment region
            displacement_scale: Scale for displacement map

        Returns:
            dict with vertices, faces, normals, optional colors
        """
        # Preprocess
        img_tensor = self._preprocess_image(image)
        mask_tensor = torch.from_numpy(mask).float().to(self.device)

        # Forward pass
        output = self.model(img_tensor, mask_tensor)

        # Extract mesh components
        vertices = output['vertices'].cpu().numpy().squeeze()
        faces = output['faces'].cpu().numpy().squeeze()

        # Apply displacement for details
        if 'displacement' in output:
            disp = output['displacement'].cpu().numpy().squeeze()
            vertices += disp * displacement_scale

        # Compute normals
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        normals = mesh.vertex_normals

        # Optional: extract vertex colors from image
        colors = self._extract_vertex_colors(image, vertices, output.get('uv_coords'))

        return {
            "vertices": vertices.astype(np.float32),
            "faces": faces.astype(np.int32),
            "normals": normals.astype(np.float32),
            "vertex_colors": colors,
            "format": "obj"
        }

    def _preprocess_image(self, image: Image.Image) -> torch.Tensor:
        """Preprocess image for model input."""
        import torchvision.transforms as transforms

        transform = transforms.Compose([
            transforms.Resize((512, 512)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

        return transform(image).unsqueeze(0).to(self.device)

    def _extract_vertex_colors(self, image, vertices, uv_coords=None):
        """Extract vertex colors from input image using UV mapping."""
        if uv_coords is None:
            return None

        img_np = np.array(image)
        h, w = img_np.shape[:2]

        # Sample colors at UV coordinates
        uv_pixels = (uv_coords[:, :2] * [w - 1, h - 1]).astype(int)
        uv_pixels = np.clip(uv_pixels, 0, [w - 1, h - 1])

        colors = img_np[uv_pixels[:, 1], uv_pixels[:, 0]] / 255.0
        return colors.astype(np.float32)
```

### 6.2 GarmentGPT Integration

```python
# utils/garmentgpt_infer.py
"""
GarmentGPT: End-to-End Garment Generation from a Single Image.
Paper: arXiv 2025
License: Apache 2.0
"""
import torch
import json
from PIL import Image
import numpy as np

class GarmentGPTPipeline:
    def __init__(self, vlm_path: str, codec_path: str, rt_path: str, device: str = "cuda"):
        self.device = device
        self.vlm = self._load_vlm(vlm_path)
        self.codec_decoder = self._load_codec(codec_path)
        self.rt_decoder = self._load_rt(rt_path)

    def _load_vlm(self, path):
        """Load Vision-Language Model."""
        from transformers import LlavaForConditionalGeneration, AutoProcessor

        model = LlavaForConditionalGeneration.from_pretrained(
            path,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        processor = AutoProcessor.from_pretrained(path)

        return {"model": model, "processor": processor}

    def _load_codec(self, path):
        """Load VQ-VAE codec decoder."""
        # Load custom VQ-VAE for geometric decoding
        from models.codec import GarmentCodecDecoder

        decoder = GarmentCodecDecoder.load_from_checkpoint(path)
        decoder.to(self.device)
        decoder.eval()

        return decoder

    def _load_rt(self, path):
        """Load rotation/translation decoder."""
        from models.rt_decoder import RTDecoder

        decoder = RTDecoder.load_from_checkpoint(path)
        decoder.to(self.device)
        decoder.eval()

        return decoder

    @torch.no_grad()
    def generate(self, image: Image.Image, mask: np.ndarray) -> dict:
        """
        Generate sewing pattern from garment image.

        Args:
            image: Background-removed garment image
            mask: Binary mask of garment

        Returns:
            dict with pattern JSON, panels, stitches
        """
        # Step 1: VLM inference → token sequence
        tokens = self._vlm_inference(image)

        # Step 2: Parse tokens → structured indices
        parsed = self._parse_tokens(tokens)

        # Step 3: Geometric decoding → vertices, curves
        geometry = self._decode_geometry(parsed)

        # Step 4: Rotation/translation → 3D positioning
        transforms = self._decode_transforms(parsed)

        # Step 5: Assemble GCD JSON
        pattern_json = self._assemble_pattern(geometry, transforms)

        return {
            "pattern": pattern_json,
            "panels": parsed.get("panel_names", []),
            "stitches": parsed.get("stitch_pairs", []),
            "format": "gcd_json"
        }

    def _vlm_inference(self, image: Image.Image) -> str:
        """Run VLM to generate token sequence."""
        prompt = "<image>\nGenerate the sewing pattern for this garment."

        inputs = self.vlm["processor"](
            text=prompt,
            images=image,
            return_tensors="pt"
        ).to(self.device)

        outputs = self.vlm["model"].generate(
            **inputs,
            max_new_tokens=2048,
            do_sample=False
        )

        return self.vlm["processor"].decode(outputs[0], skip_special_tokens=True)

    def _parse_tokens(self, tokens: str) -> dict:
        """Parse VLM output into structured format."""
        # Extract SoG (Sequence of Garments) section
        import re

        sog_match = re.search(r'<SoG>(.*?)</SoG>', tokens, re.DOTALL)
        if sog_match:
            sog_text = sog_match.group(1)
        else:
            sog_text = tokens

        # Parse panel names, edge indices, location indices
        panels = re.findall(r'panel_(\w+)', sog_text)
        edges = re.findall(r'edge_(\d+)', sog_text)
        locations = re.findall(r'loc_(\d+)', sog_text)

        return {
            "raw_tokens": sog_text,
            "panel_names": panels,
            "edge_indices": [int(e) for e in edges],
            "location_indices": [int(l) for l in locations],
            "stitch_pairs": self._extract_stitches(sog_text)
        }

    def _decode_geometry(self, parsed: dict) -> dict:
        """Decode geometric data from parsed tokens."""
        # Convert indices to floating-point geometry
        # This uses the trained VQ-VAE decoders

        edge_tensor = torch.tensor(parsed["edge_indices"], dtype=torch.long).to(self.device)
        location_tensor = torch.tensor(parsed["location_indices"], dtype=torch.long).to(self.device)

        # Decode edge geometry
        edge_geometry = self.codec_decoder.decode_edges(edge_tensor)

        # Decode panel placement
        panel_transforms = self.rt_decoder(location_tensor)

        return {
            "edge_vertices": edge_geometry["vertices"].cpu().numpy(),
            "edge_curves": edge_geometry["curves"].cpu().numpy(),
            "panel_vertices": panel_transforms["vertices"].cpu().numpy()
        }

    def _decode_transforms(self, parsed: dict) -> dict:
        """Decode rotation and translation for each panel."""
        return {"transforms": []}  # Simplified

    def _assemble_pattern(self, geometry: dict, transforms: dict) -> dict:
        """Assemble final GCD JSON pattern."""
        pattern = {
            "pattern": {
                "panels": {},
                "stitches": [],
                "panel_order": []
            }
        }

        # Build panel entries
        for i, panel_name in enumerate(geometry.get("panel_names", ["panel_0"])):
            verts = geometry["panel_vertices"][i] if i < len(geometry["panel_vertices"]) else []
            pattern["pattern"]["panels"][panel_name] = {
                "translation": [0.0, 0.0, 0.0],
                "rotation": [1.0, 0.0, 0.0, 0.0],
                "vertices": verts.tolist() if hasattr(verts, 'tolist') else [],
                "edges": []
            }
            pattern["pattern"]["panel_order"].append(panel_name)

        return pattern

    def _extract_stitches(self, text: str) -> list:
        """Extract stitch pairs from VLM output."""
        import re
        stitches = re.findall(r'stitch\((\w+)_(\d+),\s*(\w+)_(\d+)\)', text)
        return [(f"{p1}_panel", int(e1), f"{p2}_panel", int(e2))
                for p1, e1, p2, e2 in stitches]
```

### 6.3 GarmentCode Integration

```python
# utils/garmentcode_sim.py
"""
GarmentCode: Programming Parametric Sewing Patterns.
License: MIT
"""
import sys
import numpy as np
from pathlib import Path

class GarmentCodeSimulator:
    def __init__(self, garmentcode_path: str):
        self.garmentcode_path = garmentcode_path
        sys.path.insert(0, garmentcode_path)

    def pattern_to_mesh(self, pattern_json: dict, body_params: dict = None) -> dict:
        """
        Simulate sewing pattern into 3D mesh using XPBD.

        Args:
            pattern_json: GCD format pattern
            body_params: Optional SMPL body parameters

        Returns:
            dict with vertices, faces
        """
        from pygarment import GarmentPattern
        from pygarment.simulate import GarmentSimulator

        # Parse pattern
        pattern = GarmentPattern.from_dict(pattern_json)

        # Setup body (if provided)
        body = None
        if body_params:
            from smplx import create_body
            body = create_body(**body_params)

        # Run simulation
        sim = GarmentSimulator(
            pattern=pattern,
            body=body,
            resolution=5,  # mm
            steps=500,
            fps=60
        )

        # Simulate draping
        sim.step_to_end()

        # Extract final mesh
        mesh = sim.get_current_mesh()

        return {
            "vertices": np.array(mesh.vertices),
            "faces": np.array(mesh.faces),
            "format": "obj"
        }

    def validate_pattern(self, pattern_json: dict) -> dict:
        """Validate pattern for simulation readiness."""
        from pygarment import GarmentPattern

        pattern = GarmentPattern.from_dict(pattern_json)
        issues = pattern.validate()

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "panel_count": len(pattern.panels),
            "total_vertices": sum(len(p.vertices) for p in pattern.panels.values())
        }
```

---

## 7. API Design

### 7.1 Endpoint Summary

| Method | Path | Description | Auth |
|---|---|---|---|
| `GET` | `/health` | Health check | None |
| `POST` | `/api/v2/garment/reconstruct` | Full pipeline: image → mesh + pattern | JWT |
| `POST` | `/api/v2/garment/mesh` | Image → 3D mesh only | JWT |
| `POST` | `/api/v2/garment/pattern` | Image → sewing pattern only | JWT |
| `GET` | `/api/v2/garment/status/{job_id}` | Check async job status | JWT |
| `GET` | `/api/v2/garment/models` | List available models | None |

### 7.2 Request/Response Schema

#### POST /api/v2/garment/reconstruct

**Request:**
```http
POST /api/v2/garment/reconstruct HTTP/1.1
Host: korra.work
Authorization: Bearer <jwt_token>
Content-Type: multipart/form-data

--boundary
Content-Disposition: form-data; name="file"; filename="garment.jpg"
Content-Type: image/jpeg

<binary image data>
--boundary
Content-Disposition: form-data; name="include_mesh"
true
--boundary
Content-Disposition: form-data; name="include_pattern"
true
--boundary--
```

**Response (200 OK):**
```http
HTTP/1.1 200 OK
Content-Type: application/zip
Content-Disposition: attachment; filename=garment_a1b2c3d4.zip
X-Processing-Time: 12.34
X-Mesh-Vertices: 6890
X-Pattern-Panels: 4
X-Cache: MISS

<binary ZIP data>
```

**ZIP Contents:**
```
garment_a1b2c3d4/
├── garment_mesh.obj          # 3D mesh (OBJ format)
├── sewing_pattern.json       # Sewing pattern (GCD format)
├── metadata.json             # Reconstruction metadata
└── preview.png               # Rendered preview (optional)
```

**metadata.json:**
```json
{
  "image_id": "a1b2c3d4",
  "created_at": "2026-07-10T15:30:00Z",
  "mesh": {
    "vertices_count": 6890,
    "faces_count": 13776,
    "format": "obj",
    "file_size_bytes": 456789
  },
  "pattern": {
    "panels": ["front", "back", "left_sleeve", "right_sleeve"],
    "stitches": 12,
    "format": "gcd_json",
    "file_size_bytes": 23456
  },
  "models": {
    "segmentation": "SAM2",
    "mesh_reconstruction": "GarmentRec v1.0",
    "pattern_generation": "GarmentGPT v1.0",
    "simulation": "GarmentCode v2.0"
  },
  "processing_time_seconds": 12.34,
  "gpu_device": "cuda:0"
}
```

### 7.3 Error Responses

```json
// 400 Bad Request
{
  "error": "invalid_image",
  "message": "File must be a JPEG or PNG image",
  "details": {
    "received_content_type": "application/pdf",
    "max_file_size_mb": 10
  }
}

// 413 Payload Too Large
{
  "error": "image_too_large",
  "message": "Image exceeds 10MB limit",
  "details": {
    "received_size_mb": 15.2,
    "max_size_mb": 10
  }
}

// 429 Rate Limited
{
  "error": "rate_limited",
  "message": "Too many requests. Try again in 45 seconds.",
  "details": {
    "limit": 10,
    "window_seconds": 60,
    "retry_after_seconds": 45
  }
}

// 503 Service Unavailable
{
  "error": "gpu_backend_unavailable",
  "message": "Garment reconstruction service temporarily unavailable",
  "details": {
    "kaggle_backend": "disconnected",
    "tunnel_url": "https://garment-kernel.trycloudflare.com",
    "estimated_recovery": "2-5 minutes"
  }
}
```

---

## 8. Frontend Integration

### 8.1 New View Mode: Garment Studio

```javascript
// Add to measurement-screen.js

// ═══ GARMENT STUDIO ═══
buildGarmentStudioView() {
  return `
    <div class="ms-garment-studio">
      <div class="ms-garment-topbar">
        <button class="ms-garment-back" onclick="KORRA_MS.switchView(KORRA_MS._previousView || 'avatar')">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
          Back
        </button>
        <div class="ms-garment-title">Garment Studio</div>
        <div class="ms-garment-subtitle">Image → 3D Mesh + Sewing Pattern</div>
      </div>

      <div class="ms-garment-input-area">
        <!-- Upload Card -->
        <div class="ms-garment-upload-card" id="garment-upload-card">
          <div class="ms-garment-upload-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
          </div>
          <div class="ms-garment-upload-text">
            Drop a garment photo here or click to upload
          </div>
          <div class="ms-garment-upload-hint">
            JPEG/PNG, max 10MB. Works with photos on people, mannequins, or flat lays.
          </div>
          <input type="file" id="garment-file-input" accept="image/*" hidden>
        </div>

        <!-- Preview Card (hidden until image uploaded) -->
        <div class="ms-garment-preview-card" id="garment-preview-card" style="display:none">
          <img id="garment-preview-img" class="ms-garment-preview-img">
          <button class="ms-garment-remove-btn" onclick="KORRA_MS.removeGarmentImage()">Remove</button>
        </div>

        <!-- Options -->
        <div class="ms-garment-options">
          <label class="ms-garment-option">
            <input type="checkbox" id="garment-opt-mesh" checked> 3D Mesh
          </label>
          <label class="ms-garment-option">
            <input type="checkbox" id="garment-opt-pattern" checked> Sewing Pattern
          </label>
        </div>
      </div>

      <!-- Generate Button -->
      <div class="ms-garment-action-row">
        <button class="ms-garment-generate-btn" id="garment-generate-btn" disabled
                onclick="KORRA_MS.runGarmentReconstruction()">
          <span class="btn-text">Generate 3D Garment</span>
          <span class="btn-loading" style="display:none">
            <svg class="spinner" width="16" height="16" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2" stroke-dasharray="31.4 31.4" stroke-linecap="round"/>
            </svg>
            Processing...
          </span>
        </button>
      </div>

      <!-- Results Area -->
      <div class="ms-garment-results" id="garment-results" style="display:none">
        <!-- 3D Viewer -->
        <div class="ms-garment-3d-viewer" id="garment-3d-viewer">
          <div class="ms-garment-viewer-placeholder">Loading 3D mesh...</div>
        </div>

        <!-- Pattern Preview -->
        <div class="ms-garment-pattern-preview" id="garment-pattern-preview" style="display:none">
          <h4>Sewing Pattern</h4>
          <div class="ms-garment-pattern-canvas" id="garment-pattern-canvas"></div>
        </div>

        <!-- Download Buttons -->
        <div class="ms-garment-downloads">
          <button class="ms-garment-download-btn" onclick="KORRA_MS.downloadGarmentResults('zip')">
            Download ZIP (Mesh + Pattern)
          </button>
          <button class="ms-garment-download-btn secondary" onclick="KORRA_MS.downloadGarmentResults('obj')">
            Download OBJ Only
          </button>
          <button class="ms-garment-download-btn secondary" onclick="KORRA_MS.downloadGarmentResults('json')">
            Download Pattern JSON
          </button>
        </div>
      </div>
    </div>
  `;
},
```

### 8.2 JavaScript Methods

```javascript
// Add to KORRA_MS object

// Garment Studio state
_garmentImage: null,
_garmentResult: null,
_garmentViewer: null,

_initGarmentStudio() {
  const uploadCard = document.getElementById('garment-upload-card');
  const fileInput = document.getElementById('garment-file-input');

  if (!uploadCard || !fileInput) return;

  // Click to upload
  uploadCard.addEventListener('click', () => fileInput.click());

  // File selected
  fileInput.addEventListener('change', (e) => {
    if (e.target.files[0]) this._handleGarmentImage(e.target.files[0]);
  });

  // Drag and drop
  uploadCard.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadCard.classList.add('drag-over');
  });
  uploadCard.addEventListener('dragleave', () => {
    uploadCard.classList.remove('drag-over');
  });
  uploadCard.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadCard.classList.remove('drag-over');
    if (e.dataTransfer.files[0]) {
      this._handleGarmentImage(e.dataTransfer.files[0]);
    }
  });
},

_handleGarmentImage(file) {
  if (!file.type.startsWith('image/')) {
    alert('Please upload an image file');
    return;
  }
  if (file.size > 10 * 1024 * 1024) {
    alert('Image must be under 10MB');
    return;
  }

  this._garmentImage = file;

  // Show preview
  const previewCard = document.getElementById('garment-preview-card');
  const previewImg = document.getElementById('garment-preview-img');
  const uploadCard = document.getElementById('garment-upload-card');
  const generateBtn = document.getElementById('garment-generate-btn');

  if (previewCard && previewImg) {
    previewImg.src = URL.createObjectURL(file);
    previewCard.style.display = 'block';
    uploadCard.style.display = 'none';
    generateBtn.disabled = false;
  }
},

removeGarmentImage() {
  this._garmentImage = null;
  document.getElementById('garment-preview-card').style.display = 'none';
  document.getElementById('garment-upload-card').style.display = 'flex';
  document.getElementById('garment-generate-btn').disabled = true;
  document.getElementById('garment-results').style.display = 'none';
},

async runGarmentReconstruction() {
  if (!this._garmentImage) return;

  const btn = document.getElementById('garment-generate-btn');
  const btnText = btn.querySelector('.btn-text');
  const btnLoading = btn.querySelector('.btn-loading');

  // UI: loading state
  btn.disabled = true;
  btnText.style.display = 'none';
  btnLoading.style.display = 'inline-flex';

  try {
    const includeMesh = document.getElementById('garment-opt-mesh').checked;
    const includePattern = document.getElementById('garment-opt-pattern').checked;

    // Build form data
    const formData = new FormData();
    formData.append('file', this._garmentImage);
    formData.append('include_mesh', includeMesh);
    formData.append('include_pattern', includePattern);

    // Call API
    const startTime = Date.now();
    const response = await fetch('/api/v2/garment/reconstruct', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this._getAuthToken()}`
      },
      body: formData
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Reconstruction failed');
    }

    // Download ZIP
    const blob = await response.blob();
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);

    // Store result
    this._garmentResult = {
      zipBlob: blob,
      processingTime: elapsed,
      meshVertices: response.headers.get('X-Mesh-Vertices'),
      patternPanels: response.headers.get('X-Pattern-Panels')
    };

    // Show results
    this._showGarmentResults(blob, includeMesh, includePattern);

    console.log(`✅ Garment reconstructed in ${elapsed}s`);

  } catch (error) {
    console.error('Garment reconstruction failed:', error);
    alert(`Reconstruction failed: ${error.message}`);
  } finally {
    btn.disabled = false;
    btnText.style.display = 'inline';
    btnLoading.style.display = 'none';
  }
},

async _showGarmentResults(blob, showMesh, showPattern) {
  const resultsArea = document.getElementById('garment-results');
  resultsArea.style.display = 'block';

  // Extract ZIP contents
  const zip = await JSZip.loadAsync(blob);

  // Show 3D mesh if requested
  if (showMesh) {
    const objFile = zip.file(/\.obj$/)[0];
    if (objFile) {
      const objContent = await objFile.async('string');
      this._renderGarmentMesh(objContent);
    }
  }

  // Show pattern if requested
  if (showPattern) {
    const patternFile = zip.file(/sewing_pattern\.json$/)[0];
    if (patternFile) {
      const patternJson = JSON.parse(await patternFile.async('string'));
      this._renderSewingPattern(patternJson);
    }
  }
},

_renderGarmentMesh(objContent) {
  const viewerContainer = document.getElementById('garment-3d-viewer');
  if (!viewerContainer) return;

  // Use Three.js to render OBJ
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(45, viewerContainer.clientWidth / viewerContainer.clientHeight, 0.1, 1000);
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(viewerContainer.clientWidth, viewerContainer.clientHeight);
  viewerContainer.innerHTML = '';
  viewerContainer.appendChild(renderer.domElement);

  // Parse OBJ
  const loader = new THREE.OBJLoader();
  const mesh = loader.parse(objContent);

  // Add to scene
  scene.add(mesh);
  camera.position.z = 2;

  // Animate
  function animate() {
    requestAnimationFrame(animate);
    mesh.rotation.y += 0.005;
    renderer.render(scene, camera);
  }
  animate();

  this._garmentViewer = { scene, camera, renderer, mesh };
},

_renderSewingPattern(patternJson) {
  const preview = document.getElementById('garment-pattern-preview');
  const canvas = document.getElementById('garment-pattern-canvas');

  if (!preview || !canvas) return;

  preview.style.display = 'block';

  // Render pattern panels on canvas
  const svg = this._patternToSVG(patternJson);
  canvas.innerHTML = svg;
},

_patternToSVG(pattern) {
  // Convert GCD pattern to SVG for visualization
  let svg = '<svg viewBox="0 0 800 600" xmlns="http://www.w3.org/2000/svg">';

  const panels = pattern?.pattern?.panels || {};
  let offsetX = 20;

  for (const [name, panel] of Object.entries(panels)) {
    const vertices = panel.vertices || [];
    if (vertices.length < 3) continue;

    // Scale and offset
    const scale = 100;
    const points = vertices.map(v => {
      const x = (v[0] || 0) * scale + offsetX;
      const y = (v[1] || 0) * scale + 100;
      return `${x},${y}`;
    }).join(' ');

    svg += `<polygon points="${points}" fill="none" stroke="#333" stroke-width="1"/>`;
    svg += `<text x="${offsetX}" y="80" font-size="10" fill="#666">${name}</text>`;

    offsetX += 200;
  }

  svg += '</svg>';
  return svg;
},

downloadGarmentResults(format) {
  if (!this._garmentResult) return;

  const blob = this._garmentResult.zipBlob;
  const url = URL.createObjectURL(blob);

  const a = document.createElement('a');
  a.href = url;

  switch (format) {
    case 'zip':
      a.download = 'garment_reconstruction.zip';
      break;
    case 'obj':
      // Extract just the OBJ from ZIP
      // ... (similar extraction logic)
      break;
    case 'json':
      // Extract just the pattern JSON
      break;
  }

  a.click();
  URL.revokeObjectURL(url);
},
```

### 8.3 CSS Styles

```css
/* Add to measurement-screen.css */

/* ── GARMENT STUDIO ── */
.ms-garment-studio {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--ms-bg, #f8f9fa);
}

.ms-garment-topbar {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 16px 12px;
  border-bottom: 1px solid var(--ms-border, #e0e0e0);
}

.ms-garment-back {
  align-self: flex-start;
  display: flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  color: var(--ms-accent, #007AFF);
  font-size: 14px;
  cursor: pointer;
  padding: 4px 0;
}

.ms-garment-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--ms-text, #1a1a1a);
}

.ms-garment-subtitle {
  font-size: 12px;
  color: var(--ms-text-secondary, #666);
  margin-top: 2px;
}

.ms-garment-input-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  gap: 16px;
}

.ms-garment-upload-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  max-width: 400px;
  height: 200px;
  border: 2px dashed var(--ms-border, #ccc);
  border-radius: 12px;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
}

.ms-garment-upload-card:hover,
.ms-garment-upload-card.drag-over {
  border-color: var(--ms-accent, #007AFF);
  background: rgba(0, 122, 255, 0.05);
}

.ms-garment-upload-icon {
  color: var(--ms-text-secondary, #999);
  margin-bottom: 12px;
}

.ms-garment-upload-text {
  font-size: 14px;
  color: var(--ms-text, #333);
}

.ms-garment-upload-hint {
  font-size: 11px;
  color: var(--ms-text-secondary, #999);
  margin-top: 8px;
}

.ms-garment-preview-card {
  position: relative;
  width: 100%;
  max-width: 400px;
}

.ms-garment-preview-img {
  width: 100%;
  max-height: 250px;
  object-fit: contain;
  border-radius: 8px;
  border: 1px solid var(--ms-border, #e0e0e0);
}

.ms-garment-remove-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  border: none;
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 11px;
  cursor: pointer;
}

.ms-garment-options {
  display: flex;
  gap: 16px;
}

.ms-garment-option {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--ms-text, #333);
  cursor: pointer;
}

.ms-garment-action-row {
  padding: 16px;
  display: flex;
  justify-content: center;
}

.ms-garment-generate-btn {
  padding: 14px 32px;
  background: var(--ms-accent, #007AFF);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s, transform 0.1s;
  min-width: 220px;
}

.ms-garment-generate-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.ms-garment-generate-btn:active:not(:disabled) {
  transform: scale(0.98);
}

.ms-garment-generate-btn .btn-loading {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ms-garment-generate-btn .spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.ms-garment-results {
  padding: 16px;
  border-top: 1px solid var(--ms-border, #e0e0e0);
}

.ms-garment-3d-viewer {
  width: 100%;
  height: 300px;
  background: #1a1a1a;
  border-radius: 8px;
  margin-bottom: 16px;
  overflow: hidden;
}

.ms-garment-3d-viewer canvas {
  width: 100%;
  height: 100%;
}

.ms-garment-pattern-preview {
  margin-bottom: 16px;
}

.ms-garment-pattern-preview h4 {
  font-size: 14px;
  margin-bottom: 8px;
  color: var(--ms-text, #333);
}

.ms-garment-pattern-canvas {
  background: white;
  border: 1px solid var(--ms-border, #e0e0e0);
  border-radius: 8px;
  padding: 16px;
  overflow-x: auto;
}

.ms-garment-downloads {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.ms-garment-download-btn {
  padding: 10px 16px;
  background: var(--ms-accent, #007AFF);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
}

.ms-garment-download-btn.secondary {
  background: var(--ms-bg-secondary, #f0f0f0);
  color: var(--ms-text, #333);
}

/* Mobile */
@media (max-width: 900px) {
  .ms-garment-upload-card {
    height: 160px;
  }

  .ms-garment-3d-viewer {
    height: 220px;
  }

  .ms-garment-downloads {
    flex-direction: column;
  }

  .ms-garment-download-btn {
    width: 100%;
    text-align: center;
  }
}
```

---

## 9. Data Flow

### 9.1 Complete Request Flow

```
1. User uploads garment photo
   └── Frontend: file input → FormData → POST /api/v2/garment/reconstruct

2. EC2 Proxy receives request
   ├── Validate JWT token
   ├── Rate limit check
   ├── Check cache (SQLite)
   ├── If cache miss → forward to Kaggle
   └── Return cached result if found

3. Cloudflare Tunnel routes to Kaggle
   └── HTTPS → Kaggle notebook's FastAPI server

4. Kaggle GPU Backend processes
   ├── Step 1: SAM2 segments garment from image
   ├── Step 2: GarmentRec → 3D mesh (vertices + faces)
   ├── Step 3: GarmentGPT → sewing pattern JSON
   ├── Step 4: Package into ZIP
   └── Return ZIP to proxy

5. EC2 Proxy caches and forwards
   ├── Cache result in SQLite (SHA-256 hash of image)
   ├── Forward ZIP to frontend
   └── Log request metadata

6. Frontend displays results
   ├── Extract ZIP (JSZip)
   ├── Render OBJ in Three.js viewer
   ├── Render pattern as SVG
   └── Show download buttons
```

### 9.2 Async Processing (Optional Enhancement)

For long-running requests, implement async job queue:

```python
# EC2 Proxy - Async version
import uuid
from datetime import datetime

jobs = {}  # job_id → status

@app.post("/api/v2/garment/reconstruct-async")
async def reconstruct_async(file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {
        "status": "queued",
        "created_at": datetime.now().isoformat(),
        "progress": 0
    }

    # Start background task
    asyncio.create_task(_process_job(job_id, file))

    return {"job_id": job_id, "status": "queued"}

@app.get("/api/v2/garment/status/{job_id}")
async def job_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    return jobs[job_id]

@app.get("/api/v2/garment/result/{job_id}")
async def job_result(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    if jobs[job_id]["status"] != "completed":
        raise HTTPException(202, "Job still processing")

    return StreamingResponse(
        io.BytesIO(jobs[job_id]["result"]),
        media_type="application/zip"
    )
```

---

## 10. Deployment

### 10.1 Kaggle Notebook Deployment

```python
# deploy_kaggle.py
"""
Deploy the garment reconstruction backend to Kaggle.
"""
import kaggle
from kaggle.api.kaggle_api_extended import KaggleApi

api = KaggleApi()
api.authenticate()

# Upload notebook
api.kernels_push(
    kernel_dir="kaggle-garment-backend",
    kernel_slug="garment-reconstruction-api",
    kernel_title="Garment Reconstruction API Server",
    language="python",
    enable_gpu=True,
    enable_internet=True  # Required for Cloudflare Tunnel
)

# Start kernel with GPU
api.kernels_start(
    kernel="garment-reconstruction-api"
)

print("✅ Kaggle notebook deployed and started")
```

### 10.2 EC2 Proxy Deployment

```bash
#!/bin/bash
# deploy_ec2.sh

# 1. Copy proxy code to EC2
scp -i ~/.ssh/korra-ai-key.pem \
    -r garment-proxy/ \
    ubuntu@13.60.215.88:/home/ubuntu/

# 2. SSH and setup
ssh -i ~/.ssh/korra-ai-key.pem ubuntu@13.60.215.88 << 'EOF'
    # Install dependencies
    sudo apt-get update
    sudo apt-get install -y python3-pip
    pip3 install fastapi uvicorn httpx python-multipart

    # Create systemd service
    sudo cp /home/ubuntu/garment-proxy/garment-proxy.service \
        /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable garment-proxy
    sudo systemctl start garment-proxy

    # Update nginx config
    sudo cp /home/ubuntu/garment-proxy/nginx-garment.conf \
        /etc/nginx/sites-enabled/korra
    sudo nginx -t && sudo systemctl reload nginx

    echo "✅ EC2 proxy deployed"
EOF
```

### 10.3 Cloudflare Tunnel Setup

```bash
# On Kaggle notebook (in a cell)
!pip install cloudflared

import subprocess
import threading

def start_tunnel():
    proc = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", "http://localhost:8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    # Parse URL from stderr
    for line in proc.stderr:
        if "trycloudflare.com" in line:
            url = "https://" + line.split("https://")[-1].strip()
            print(f"🌐 Tunnel: {url}")
            # Save URL for EC2 proxy to use
            with open("/kaggle/working/tunnel_url.txt", "w") as f:
                f.write(url)
            break
    return proc

tunnel_proc = start_tunnel()
```

---

## 11. Testing

### 11.1 Unit Tests

```python
# tests/test_models.py
import pytest
import numpy as np
from PIL import Image

def test_garmentrec_reconstruction():
    """Test GarmentRec produces valid mesh."""
    model = GarmentRecModel("weights/garmentrec/model.pth", "cpu")
    img = Image.new("RGB", (512, 512), (128, 128, 128))
    mask = np.ones((512, 512), dtype=np.uint8) * 255

    result = model.reconstruct(img, mask)

    assert "vertices" in result
    assert "faces" in result
    assert result["vertices"].shape[1] == 3
    assert result["faces"].shape[1] == 3
    assert len(result["vertices"]) > 100
    assert len(result["faces"]) > 100

def test_garmentgpt_generation():
    """Test GarmentGPT produces valid pattern."""
    pipeline = GarmentGPTPipeline("weights/vlm", "weights/codec", "weights/rt", "cpu")
    img = Image.new("RGB", (512, 512), (128, 128, 128))
    mask = np.ones((512, 512), dtype=np.uint8) * 255

    result = pipeline.generate(img, mask)

    assert "pattern" in result
    assert "panels" in result
    assert isinstance(result["pattern"], dict)

def test_garmentcode_simulation():
    """Test GarmentCode pattern → mesh."""
    sim = GarmentCodeSimulator("weights/garmentcode")
    pattern = {
        "pattern": {
            "panels": {
                "front": {
                    "vertices": [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]],
                    "edges": []
                }
            },
            "stitches": [],
            "panel_order": ["front"]
        }
    }

    result = sim.pattern_to_mesh(pattern)

    assert "vertices" in result
    assert "faces" in result
    assert len(result["vertices"]) > 0
```

### 11.2 Integration Tests

```python
# tests/test_api.py
import pytest
from fastapi.testclient import TestClient

client = TestClient(app)

def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"

def test_reconstruct_valid_image():
    """Test full reconstruction pipeline."""
    with open("tests/fixtures/garment.jpg", "rb") as f:
        resp = client.post(
            "/api/v1/reconstruct",
            files={"file": ("garment.jpg", f, "image/jpeg")},
            params={"include_mesh": True, "include_pattern": True}
        )

    assert resp.status_code == 200
    assert resp.headers["Content-Type"] == "application/zip"
    assert int(resp.headers["X-Mesh-Vertices"]) > 0

def test_reconstruct_invalid_file():
    """Test rejection of non-image files."""
    resp = client.post(
        "/api/v1/reconstruct",
        files={"file": ("test.pdf", b"fake pdf", "application/pdf")}
    )
    assert resp.status_code == 400

def test_rate_limiting():
    """Test rate limiting works."""
    for i in range(11):
        resp = client.post("/api/v1/reconstruct", files={})
    assert resp.status_code == 429
```

### 11.3 Load Testing

```bash
# Load test with wrk (install: brew install wrk)
wrk -t4 -c10 -d30s --script=post_garment.lua \
    http://localhost:8001/api/v1/reconstruct
```

---

## 12. Monitoring & Maintenance

### 12.1 Health Checks

```python
# monitoring/health_check.py
"""
Automated health checks for garment reconstruction pipeline.
Run every 5 minutes via cron.
"""
import httpx
import json
from datetime import datetime

CHECKS = [
    {
        "name": "EC2 Proxy",
        "url": "http://localhost:8001/health",
        "timeout": 5
    },
    {
        "name": "Kaggle Backend",
        "url": "https://garment-kernel.trycloudflare.com/health",
        "timeout": 30
    }
]

def run_health_checks():
    results = []
    for check in CHECKS:
        try:
            resp = httpx.get(check["url"], timeout=check["timeout"])
            results.append({
                "name": check["name"],
                "status": "healthy" if resp.status_code == 200 else "unhealthy",
                "status_code": resp.status_code,
                "response_time_ms": resp.elapsed.total_seconds() * 1000
            })
        except Exception as e:
            results.append({
                "name": check["name"],
                "status": "unreachable",
                "error": str(e)
            })

    # Log results
    print(f"[{datetime.now().isoformat()}] Health check:")
    for r in results:
        print(f"  {r['name']}: {r['status']}")

    # Alert if any unhealthy
    unhealthy = [r for r in results if r["status"] != "healthy"]
    if unhealthy:
        # Send alert (email, Slack, etc.)
        send_alert(unhealthy)

    return results

if __name__ == "__main__":
    run_health_checks()
```

### 12.2 Cron Setup

```bash
# Add to crontab
*/5 * * * * cd /home/ubuntu/garment-proxy && python3 monitoring/health_check.py >> /var/log/garment-health.log 2>&1

# Restart Kaggle notebook weekly (to avoid quota issues)
0 0 * * 0 # Manual: restart Kaggle notebook
```

### 12.3 Quota Monitoring

```python
# monitoring/quota_check.py
"""
Monitor Kaggle GPU quota usage.
"""
import kaggle

api = kaggle.KaggleApi()
api.authenticate()

# Check kernel status
kernels = api.kernels_list(search="garment-reconstruction")
for k in kernels:
    print(f"Kernel: {k.id}")
    print(f"  Status: {k.status}")
    print(f"  GPU: {k.gpu}")
    print(f"  Runtime: {k.totalRuntime}")
```

---

## 13. Cost Analysis

### 13.1 Infrastructure Costs

| Component | Monthly Cost | Notes |
|---|---|---|
| EC2 t3.micro | $0 (existing) | Already running |
| Kaggle Free Tier | $0 | 30 GPU-hrs/week |
| Cloudflare Tunnel | $0 | Free tier |
| Supabase Storage | $0 | Existing plan |
| Domain (korra.work) | $0 (existing) | Already configured |
| **Total** | **$0** | All free tier |

### 13.2 Capacity Estimates

| Metric | Value | Notes |
|---|---|---|
| GPU-hours/week | 30 | Kaggle free tier |
| Seconds per reconstruction | ~15-30 | GarmentRec + GarmentGPT |
| Reconstructions per GPU-hour | ~120-240 | At 15-30s each |
| Reconstructions per week | ~3,600-7,200 | Theoretical max |
| Practical daily capacity | ~500-1,000 | Accounting for cold starts, queue |
| Practical weekly capacity | ~3,500-7,000 | Sustainable |

### 13.3 Scaling Thresholds

| Users | Daily Reconstructions | Fits Free Tier? |
|---|---|---|
| 10 | ~10 | Yes (easy) |
| 50 | ~50 | Yes |
| 100 | ~100 | Yes |
| 500 | ~500 | Tight (needs optimization) |
| 1000+ | ~1000+ | Needs paid GPU or multi-notebook |

---

## 14. Security

### 14.1 Authentication

```python
# All /api/v2/garment/* endpoints require JWT
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(credentials = Depends(security)):
    """Verify JWT token from Supabase."""
    token = credentials.credentials
    # Verify with Supabase JWT secret
    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"]
        )
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")
```

### 14.2 Input Validation

```python
# Validate image inputs
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

async def validate_upload(file: UploadFile):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, f"Invalid file type. Allowed: {ALLOWED_TYPES}")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, f"File too large. Max: {MAX_FILE_SIZE/1024/1024}MB")

    # Check if actually an image (magic bytes)
    if not content[:4] in [b'\xff\xd8\xff\xe0', b'\xff\xd8\xff\xe1', b'\x89PNG']:
        raise HTTPException(400, "File is not a valid image")
```

### 14.3 Rate Limiting

```python
# Per-IP rate limiting
from collections import defaultdict
import time

class RateLimiter:
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)

    def is_allowed(self, ip: str) -> bool:
        now = time.time()
        # Remove old requests
        self.requests[ip] = [
            t for t in self.requests[ip]
            if now - t < self.window_seconds
        ]
        if len(self.requests[ip]) >= self.max_requests:
            return False
        self.requests[ip].append(now)
        return True
```

### 14.4 Cloudflare Security

```
- Tunnel encrypts all traffic (TLS 1.3)
- No exposed ports on Kaggle notebook
- EC2 only exposes ports 80/443 (existing nginx)
- Rate limiting at Cloudflare level (free tier includes DDoS protection)
```

---

## 15. Scaling Strategy

### 15.1 Horizontal Scaling

```
If demand exceeds free tier capacity:

Option 1: Multiple Kaggle Notebooks
├── Notebook A: GarmentRec (mesh only)
├── Notebook B: GarmentGPT (pattern only)
├── EC2 proxy load-balances between them
└── Doubles capacity to ~14,000/week

Option 2: Add Hugging Face Space
├── HF Space for pattern generation (ZeroGPU A100)
├── Kaggle for mesh generation (T4 x2)
├── EC2 orchestrates both
└── Adds ~5 min/day GPU capacity

Option 3: Colab Backend
├── Colab notebook as secondary GPU backend
├── EC2 routes to least-loaded backend
├── Adds ~15-30 GPU-hrs/week
└── Combined capacity: ~60 GPU-hrs/week
```

### 15.2 Vertical Scaling

```
If free tiers become insufficient:

1. Upgrade Kaggle to Pro ($25/month)
   └── More GPU hours, priority access

2. Add Modal ($30/month credits)
   └── Serverless GPU, per-second billing

3. Self-host GPU
   └── Buy used RTX 3090 (~$500)
   └── Run on EC2 G4 instance (~$0.50/hr)
```

### 15.3 Caching Strategy

```python
# Reduce GPU load by caching common garments
# Similar garments → similar patterns

# Image similarity cache
from PIL import Image
import imagehash

def compute_image_hash(image_bytes):
    """Compute perceptual hash for image similarity."""
    img = Image.open(io.BytesIO(image_bytes))
    return str(imagehash.phash(img))

# If similar image found in cache, return cached result
# This can reduce GPU load by 30-50% for common garment types
```

---

## 16. Rollout Plan

### 16.1 Phase 1: Backend Setup (Week 1)

| Day | Task | Owner |
|---|---|---|
| 1 | Create Kaggle account, verify phone | You |
| 1 | Upload model weights to Kaggle Dataset | You |
| 2 | Build Kaggle notebook with FastAPI server | Me |
| 2 | Test GarmentRec + GarmentGPT locally | Me |
| 3 | Setup Cloudflare Tunnel on Kaggle | Me |
| 3 | Build EC2 proxy server | Me |
| 4 | Configure nginx routing for /api/v2/garment/ | Me |
| 5 | End-to-end testing: upload → mesh + pattern | You + Me |

### 16.2 Phase 2: Frontend Integration (Week 2)

| Day | Task | Owner |
|---|---|---|
| 6 | Build Garment Studio view (HTML/CSS/JS) | Me |
| 7 | Implement upload + preview UI | Me |
| 8 | Implement 3D mesh viewer (Three.js) | Me |
| 9 | Implement pattern visualization (SVG) | Me |
| 10 | Implement download functionality | Me |

### 16.3 Phase 3: Testing & Polish (Week 3)

| Day | Task | Owner |
|---|---|---|
| 11 | Unit tests for all models | Me |
| 12 | Integration tests for API endpoints | Me |
| 13 | Load testing with real images | You |
| 14 | Fix bugs, optimize performance | Me |
| 15 | Deploy to production, smoke test | You + Me |

### 16.4 Phase 4: Production Launch (Week 4)

| Day | Task | Owner |
|---|---|---|
| 16 | Deploy Kaggle notebook (persistent) | Me |
| 17 | Deploy EC2 proxy + nginx config | Me |
| 18 | Setup monitoring cron jobs | Me |
| 19 | User acceptance testing | You |
| 20 | Soft launch to beta users | You |

---

## 17. Risk Mitigation

### 17.1 Kaggle Session Timeout

**Risk:** Kaggle sessions timeout after 12 hours.
**Mitigation:**
- Auto-restart script in notebook
- Cloudflare Tunnel auto-reconnects
- EC2 proxy retries failed requests
- Health checks detect and alert on downtime

### 17.2 Kaggle Quota Exhaustion

**Risk:** 30 GPU-hours/week limit reached.
**Mitigation:**
- Cache frequently-requested garments
- Offer "quick mode" (pattern-only, ~3s) vs "full mode" (~30s)
- Track quota usage via monitoring
- Fallback to CPU-only mode for simple garments

### 17.3 Tunnel URL Changes

**Risk:** Cloudflare Tunnel URL changes on restart.
**Mitigation:**
- EC2 proxy fetches latest tunnel URL from Kaggle notebook
- Kaggle notebook writes URL to a fixed Kaggle Dataset
- EC2 polls Dataset for URL updates

### 17.4 Model Quality Issues

**Risk:** GarmentRec/GarmentGPT produce poor results for certain garment types.
**Mitigation:**
- Start with 5 garment categories (dress, top, pants, skirt, coat)
- Collect user feedback on quality
- Fine-tune models on domain-specific data
- Add quality scoring (mesh validity check)

### 17.5 Security Breach

**Risk:** Unauthorized access to GPU backend.
**Mitigation:**
- JWT authentication on all endpoints
- Rate limiting per IP
- Input validation (file type, size)
- No exposed ports on Kaggle (only via Cloudflare Tunnel)
- EC2 proxy handles all public-facing traffic

---

## 18. Future Enhancements

### 18.1 Short-term (1-3 months)

1. **Body-aware draping:** Pass SMPL body params from scan to GarmentCode for realistic draping
2. **Texture transfer:** Extract texture from input image and apply to 3D mesh
3. **Multi-view reconstruction:** Accept front + side views for better accuracy
4. **Pattern editing UI:** Let users modify sewing patterns before simulation
5. **Batch processing:** Upload multiple garment images at once

### 18.2 Medium-term (3-6 months)

1. **Garment library:** Build a library of common garment templates
2. **Size-aware patterns:** Generate patterns for specific body measurements
3. **Fabric simulation:** Add fabric material properties (stiffness, weight)
4. **AR preview:** Show garment on user's body via AR camera
5. **Export to manufacturing:** DXF/STEP format for industrial sewing machines

### 18.3 Long-term (6-12 months)

1. **Custom garment design:** Text-to-garment via ChatGarment integration
2. **Virtual fitting room:** Multiple garments, outfit combinations
3. **On-device inference:** Mobile NPU deployment (Snapdragon 8 Gen 3)
4. **Marketplace:** Users sell/share garment patterns
5. **Production pipeline:** Full CAD → simulation → manufacturing workflow

---

## Appendix A: File Structure

```
ai-body-scan-saas/
├── PLAN_GARMENT_RECONSTRUCTION.md    # This file
├── kaggle-garment-backend/           # Kaggle notebook code
│   ├── notebook.ipynb
│   ├── api_server.py
│   ├── models/
│   ├── utils/
│   └── requirements.txt
├── garment-proxy/                    # EC2 proxy code
│   ├── server.py
│   ├── garment-proxy.service
│   ├── nginx-garment.conf
│   └── monitoring/
├── public/assets/
│   ├── measurement-screen.js         # Add Garment Studio view
│   └── measurement-screen.css        # Add Garment Studio styles
├── tests/
│   ├── test_garment_models.py
│   └── test_garment_api.py
└── scripts/
    ├── deploy_kaggle.py
    └── deploy_ec2.sh
```

## Appendix B: Model Specifications

| Model | Params | VRAM | License | Input | Output |
|---|---|---|---|---|---|
| GarmentRec | ~50M | ~3GB | MIT | 512x512 image + mask | OBJ mesh |
| GarmentGPT | ~7B (VLM) + ~100M (decoders) | ~5GB | Apache 2.0 | 512x512 image | GCD JSON |
| GarmentCode | N/A (simulator) | ~1GB | MIT | GCD JSON | OBJ mesh |
| SAM2 | ~200M | ~1GB | Apache 2.0 | 1024x1024 image | Binary mask |

## Appendix C: API Quick Reference

```bash
# Health check
curl https://korra.work/health

# Full reconstruction
curl -X POST https://korra.work/api/v2/garment/reconstruct \
  -H "Authorization: Bearer <token>" \
  -F "file=@garment.jpg" \
  -o result.zip

# Mesh only
curl -X POST https://korra.work/api/v2/garment/mesh \
  -H "Authorization: Bearer <token>" \
  -F "file=@garment.jpg" \
  -o mesh.obj

# Pattern only
curl -X POST https://korra.work/api/v2/garment/pattern \
  -H "Authorization: Bearer <token>" \
  -F "file=@garment.jpg" \
  -o pattern.json
```

---

**End of Plan**

Total Lines: ~2000
Created: 2026-07-10
Author: AI Assistant
Status: Ready for Implementation
