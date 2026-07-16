# KORRA Garment Platform — Unified Master Plan

**Atomic merge of:**
- `PLAN_GARMENT_RECONSTRUCTION.md` (backend pipeline, ~2827 lines)
- `PLAN_GARMENT_FRONTEND.md` (frontend reconstruction UI, 100 phases)
- `VTO_FULL_ROTATION_SYNTHESIS_PLAN.md` (multi-angle VTO, 50 phases)

**Total: 240 phases (0–239) across 8 tracks.**

**API Versioning Convention:** Kaggle internal API is v1 (`/api/v1/...`); EC2 proxy public API is v2 (`/api/v2/garment/...`).

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                        USER BROWSER                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Upload Photo │  │ 3D Preview │  │ Multi-Angle VTO         │  │
│  │ (recon)      │  │ (Three.js) │  │ [F][S][B] Carousel     │  │
│  └──────┬──────┘  └──────▲──────┘  └────────────▲────────────┘  │
│         │                │                      │                │
└─────────┼────────────────┼──────────────────────┼────────────────┘
          │ POST /api/v2/garment/reconstruct       │
          ▼                │                      │
┌──────────────────────────────────────────────────────────────────┐
│                    EC2 t3.micro (PROXY)                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ FastAPI      │  │ JWT Auth    │  │ Job Queue + Polling     │  │
│  │ Proxy Server │  │ Rate Limit  │  │ SSE Relay               │  │
│  └──────┬──────┘  └─────────────┘  └─────────────────────────┘  │
│         │                                                         │
└─────────┼─────────────────────────────────────────────────────────┘
          │ HTTPS (Cloudflare Tunnel)
          ▼
┌──────────────────────────────────────────────────────────────────┐
│               KAGGLE NOTEBOOK (GPU BACKEND)                      │
│  ┌───────┐  ┌────────┐  ┌──────────┐  ┌──────────┐  ┌───────┐  │
│  │ rembg │→│ SAM2   │→│GarmentRec│→│GarmentGPT│→│ ZIP   │  │
│  │ BG    │  │Segment │  │3D Mesh  │  │Pattern   │  │ Pkg   │  │
│  │ removal│  │        │  │(OBJ)    │  │(GCD JSON)│  │       │  │
│  └───────┘  └────────┘  └──────────┘  └──────────┘  └───────┘  │
│                                                                  │
│  GPU: T4 x2 (30GB)  |  SSE progress → proxy → frontend          │
│  View Synthesis: SAM2 refine → UV project → VLM back in-paint   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Phase Index

| Track | Name | Phases | Source Plans |
|-------|------|--------|-------------|
| **0** | Backend Infrastructure | 000–029 (30) | Reconstruction: infra, Kaggle, models, proxy, tunnel, deploy |
| **1** | Pipeline Hardening + SSE | 030–049 (20) | Reconstruction: async, monitoring, security; Frontend: SSE hooks; VTO: multi-track SSE |
| **2** | Reconstruct UI — Dedicated CSS | 050–069 (20) | Frontend Track A (renumbered 0→50) |
| **3** | Reconstruct UI — Inline Error States | 070–089 (20) | Frontend Track B (renumbered 20→70) |
| **4** | Reconstruct UI — SSE Progress | 090–109 (20) | Frontend Track C (renumbered 40→90) |
| **5** | Reconstruct UI — 3D Preview | 110–129 (20) | Frontend Track D (renumbered 60→110) |
| **6** | Reconstruct → Try-On Bridge | 130–144 (15) | Frontend Track E (renumbered 80→130) + VTO Phase 35 (blueprint) |
| **7** | VTO Full Rotation | 145–214 (70) | VTO Tracks A–D (70 phases merged, renumbered 1→145) |
| **8** | Polish & Launch | 215–239 (25) | Frontend Track F (renumbered 90→215) + VTO Track D hardening |

---

# Track 0: Backend Infrastructure (Phases 000–029)

| Phase | Deliverable | File | Description |
|-------|------------|------|-------------|
| 000 | Kaggle account + phone verify | — | Create 4 Kaggle accounts, verify phone number (required for GPU access), generate API tokens from kaggle.json. Enable GPU in Account Settings → Notebook → GPU = "Always On". |
| 001 | Model weights Kaggle Dataset | `garment-models/weights` (Kaggle cloud) | Upload GarmentRec weights (~500MB), GarmentGPT VLM + codec + rt (~4.2GB), SAM2 (~1GB), GarmentCode/pygarment (~50MB). Total ~5.7GB fits within Kaggle's 73GB persistent storage. Dataset slug: `garment-models/weights`. |
| 002 | Kaggle Dataset structure | `kaggle-garment-backend/` (Kaggle VM only) | Organize weights by model: `garmentrec/model.pth`, `garmentgpt/vlm/checkpoint-12844`, `garmentgpt/codec/config_vq1024.yaml`, `garmentgpt/rt/config_rt_euler.yaml`, `sam2/sam2_hiera_large.pt`, `garmentcode/pygarment/`. |
| 003 | Notebook Cell 1: Install | `notebook.ipynb` | Install torch 2.5.1+cu121 for P100 compat, pytorch3d, fastapi, uvicorn, python-multipart, pillow, numpy, trimesh, rembg, SAM2 from GitHub, cloudflared binary. |
| 004 | Notebook Cell 1: Force-reinstall torch | `notebook.ipynb` | Force-reinstall torch with CUDA 12.1 for T4 (sm_75) / P100 (sm_60) compatibility. Install onnxruntime (CPU to avoid libcudart issues). Pre-warm rembg during startup to cache u2net model. |
| 005 | Notebook Cell 2: Model weights download | `notebook.ipynb` | Download model weights using gdown (Google Drive), HuggingFace Hub (VLM), and wget/requests (GarmentRec). Check for cached weights first, skip download if already present. Verify all weight files exist before proceeding. |
| 006 | Notebook Cell 2: VRAM budget | `notebook.ipynb` | Ensure total VRAM (9GB: GarmentRec ~3GB + GarmentGPT ~5GB + SAM2 ~1GB) fits in T4 16GB or P100 16GB. Load models sequentially on CPU first, then move to GPU. Add `gc.collect()` + `torch.cuda.empty_cache()` between loads. |
| 007 | Cell 3: Preprocess pipeline | `notebook.ipynb` | rembg background removal + SAM2 garment segmentation with center-point prompt. Returns dict with original image, background-removed image, binary garment mask, and image dimensions. SAM2 uses point_coords at image center with point_label=1 (foreground), multimask_output=True. |
| 008 | Cell 3: GarmentRec inference | `notebook.ipynb` | 3D mesh reconstruction from single image + mask. GarmentRec takes (image, mask, displacement_scale=0.005) and returns vertices (N,3), faces (F,3), normals (N,3), optional vertex_colors. Output is exportable to OBJ format. |
| 009 | Cell 3: GarmentGPT inference | `notebook.ipynb` | Sewing pattern generation (GCD JSON format) from background-removed image and mask. Outputs structured pattern with panels, stitches, metadata. Compatible with GarmentCode XPBD simulator. |
| 010 | Cell 3: GarmentCode simulation | `notebook.ipynb` | Pattern → 3D mesh XPBD simulation. Parses GCD JSON into GarmentPattern, runs Simulator with 300 steps, returns simulated vertices and faces. SMPL body params are optional for draping on a mannequin (skipped in initial MVP). |
| 011 | Cell 3: Result packaging | `notebook.ipynb` | ZIP archive with: mesh.obj (OBJ format), sewing_pattern.json (GCD JSON), metadata.json (image_id, vertex count, face count, panel count, model versions). Uses `vertices_faces_to_obj()` for OBJ export with normals and vertex colors. |
| 012 | Cell 4: FastAPI server | `api_server.py` | POST /api/v1/reconstruct — accepts image file, runs full pipeline, returns ZIP. GET /health — returns status, GPU device, model load state. GET /debug/error — returns last error traceback. POST /api/v1/callback — receives result URL from async processing. |
| 013 | Cell 4: vLLM shim | `api_server.py` | Transformers-based shim for GarmentGPT which imports vllm (incompatible with P100 sm_60). Patches `importlib.util.find_spec` to return None for vllm, provides `_HF_LLM` class using AutoProcessor + AutoModelForVision2Seq, supports 8-bit quantization on sm_70+. |
| 014 | Cell 4: Image validation | `api_server.py` | Content-type check (must start with "image/"), size limit (20MB), dimension bounds (32–4096px). Returns 400 with structured error JSON for invalid inputs. |
| 015 | Cell 4: Concurrency limit | `api_server.py` | `uvicorn.run(limit_concurrency=2, backlog=10)` for OOM safety on T4/P100. Prevents GPU memory exhaustion from concurrent inference requests. Queued requests return 503 immediately. |
| 016 | Cell 4: Error logging | `api_server.py` | `BaseException` catch-all middleware writes to `last_error.txt` with GPU state, model status, loading state. Structured error codes: CUDA_OOM, SAM2_LOAD_FAILED, INVALID_IMAGE, IMAGE_TOO_LARGE, REMBG_FAILED, UNKNOWN. Each error has `recoverable: bool` flag. |
| 017 | Cell 5: Cloudflare tunnel (blocking) | `cell5_code.py` | Start tunnel FIRST before server (not in thread). Parse tunnel URL from stdout using regex for `trycloudflare.com`. Cloudflared binary at `/kaggle/working/cloudflared` (v2026.7.1). Uses quick tunnel mode: `cloudflared tunnel --url URL --no-autoupdate`. |
| 018 | Cell 5: FastAPI server start | `cell5_code.py` | Start server AFTER tunnel is ready. Wait for "Uvicorn running" in stdout before proceeding. Server runs on port 8000 with async model loading in background thread. |
| 019 | Cell 5: Keep-alive loop (60-600s) | `cell5_code.py` | Health check every 60s, tunnel liveliness via Cloudflare URL probe. Exponential backoff: 60s–600s, reset on success (`*0.75`), double on failure. |
| 020 | Cell 5: Consecutive-failure counter | `cell5_code.py` | 3 health fails before server restart. No `t_proc.kill()` on every exception. Separate counters for health fails and tunnel fails. |
| 021 | Cell 5: Tunnel uptime + restart tracking | `cell5_code.py` | `_tunnel_start_time`, `_tunnel_restarts`, `_server_restarts` tracked and printed in status line. Logs: `[HH:MM:SS] ACTIVE/DEGRADED | GPU: T4 ok=True | Tunnel: URL [CF/LOCAL] up=Xm | tunnel_restarts=N server_restarts=M`. |
| 022 | Cell 5: Tunnel auto-registration | `cell5_code.py` | `register_tunnel(tunnel_url)` called after every `start_tunnel()` and every keep-alive cycle. POSTs URL to EC2 proxy at `https://korra.work/api/v2/garment/internal/tunnel`, writes to `/kaggle/working/output/tunnel_url.txt`. Retries up to 5 times. |
| 023 | EC2 proxy: FastAPI server | `garment-proxy/server.py` | `POST /api/v2/garment/reconstruct` — proxies to Kaggle tunnel. `GET /health` — proxy + Kaggle backend connectivity. `POST /api/v2/garment/internal/tunnel` — receives tunnel URL from Kaggle. Runs on port 8001. |
| 024 | EC2 proxy: JWT auth | `garment-proxy/server.py` | `verify_jwt()` via Supabase `/auth/v1/user` endpoint. Validates Bearer token from Authorization header. Returns 401 for invalid/expired tokens. |
| 025 | EC2 proxy: Rate limiting | `garment-proxy/server.py` | 10 req/min per IP. Returns 429 with Retry-After header when exceeded. In-memory dict with (count, window_start) per IP. Window resets every 60s. |
| 026 | EC2 proxy: Retry loop (MAX_RETRIES=5) | `garment-proxy/server.py` | Exponential backoff to Kaggle backend. Separate connect/read/write timeouts. Retries on timeout, 5xx, connection errors. Caches successful results by SHA-256 hash. |
| 027 | EC2 proxy: Tunnel pre-check | `garment-proxy/server.py` | `GET /health` through tunnel before forwarding reconstruction request. Logs ALIVE/DEAD status. Returns 503 if tunnel is unreachable. |
| 028 | EC2 proxy: Tunnel URL cache to disk | `garment-proxy/server.py` | `/tmp/kaggle_tunnel_url.txt` — survives proxy restart. Read on startup, updated when Kaggle registers new tunnel URL. |
| 029 | EC2 proxy: Supabase job tracking | `garment-proxy/server.py` | Create `garment_jobs` table via `kaggle-garment-backend/supabase_garment_jobs.sql` (run once). Then implement job tracking in `server.py`: status (pending/processing/completed/failed), retrying (bool), error_message (text), progress (int 0-100), progress_message (text). Creates job on reconstruct request, updates on progress/completion. |

## Track 1: Pipeline Hardening + SSE (Phases 030–049)

| Phase | Deliverable | File | Description |
|-------|------------|------|-------------|
| 030 | Nginx proxy config | `garment-proxy/bootstrap.sh` | `location /api/v2/garment/` → `proxy_pass http://127.0.0.1:8001`. Large file support: `proxy_buffering off`, `proxy_read_timeout 180s`, `client_max_body_size 20M`. CORS headers for all origins. |
| 031 | Systemd service | `garment-proxy/bootstrap.sh` | `/etc/systemd/system/garment-proxy.service`: `ExecStart=/usr/bin/python3 server.py`, `Restart=always`, `RestartSec=5`. `Environment=KAGGLE_TUNNEL_URL=...`. `ExecStartPost` curl health check. |
| 032 | Bootstrap: cron auto-recovery | `garment-proxy/bootstrap.sh` | Every 5min: `curl http://localhost:8001/health` — restart systemd service on failure. Logs to syslog. |
| 033 | Health check script | `scripts/garment_proxy_health_check.sh` | Probes `/api/v2/garment/health` locally and tunnel URL. Returns 0 if healthy, 1 if degraded, 2 if down. Human-readable output with status summary. |
| 034 | E2E test script | `scripts/e2e_garment_test.py` | 4 stages: health check (proxy + Kaggle), tunnel reachability, reconstruct with test image, verify ZIP contents (mesh.obj + pattern.json + metadata.json). |
| 035 | Log parser script | `scripts/parse_proxy_logs.py` | Parse journalctl output for garment-proxy service. Extract request_id, retries, error types, processing time per request. Summary stats: avg processing time, error rate, cache hit rate. |
| 036 | Deploy script | `garment-proxy/deploy.sh` | `scp server.py → EC2`, restart systemd service, verify health. Idempotent: checks if file changed before restart. |
| 037 | Async job queue (EC2) | `garment-proxy/server.py` | Create Supabase garment_jobs row on reconstruct request. Background task polls Kaggle via HTTP polling (GET /api/v1/job/{id} every 3s). Updates job status on completion or failure. SSE upgrade in Phase 042. |
| 038 | request_id correlation | `garment-proxy/server.py` | `req_id = job_id` printed on every log line across proxy, Kaggle, and frontend. Passed as X-Request-ID header. Enables end-to-end tracing. |
| 039 | Multi-account rotation | `scripts/auto_kaggle_rotate.py` | Cycle through 4 Kaggle accounts on quota exhaustion. Checks quota via Kaggle API, triggers rotation when < 5 GPU-hours remaining. Updates notebook to use active account. |
| 040 | Kaggle SSE endpoint: progress stream | `api_server.py` | `GET /api/v1/reconstruct/progress/{job_id}` — SSE event stream. Content-Type: text/event-stream. Emits events as JSON data lines: `{"type":"segmenting","progress":15,"message":"Segmenting garment..."}` |
| 041 | Pipeline emission hooks | `api_server.py` | Progress events emitted at each pipeline stage: rembg→"segmenting" (15%), SAM2→"meshing" (35%), GarmentRec→"patterning" (65%), GarmentGPT→"zipping" (90%), done→"complete" (100%). Error→"error" with detail. |
| 042 | Proxy SSE relay | `garment-proxy/server.py` | Proxy opens SSE connection to Kaggle tunnel, streams events to frontend. Falls back to polling (GET /api/v1/job/{id} every 3s) if SSE fails. |
| 043 | SSE sequence guard | `api_server.py` | Sequence number per event (monotonic counter). Frontend ignores out-of-order events. Prevents race conditions from concurrent pipeline processing. |
| 044 | SSE idle timeout | `api_server.py` | 60s after last event, close SSE connection. Cleanup: remove event listeners, close file handles. Prevents memory leak from abandoned connections. |
| 045 | Progress → Supabase | `garment-proxy/server.py` | On each SSE event, PATCH garment_jobs row: update progress (0–100) + progress_message. Enables page-refresh recovery — frontend can resume progress display. |
| 046 | Supabase garment_jobs migration | `scripts/007_garment_jobs_progress.sql` | ALTER existing `garment_jobs` table (created by `supabase_garment_jobs.sql`): add `progress INT DEFAULT 0` and `progress_message TEXT` columns. |
| 047 | Garment storage bucket | `scripts/setup_garment_storage.py` | Create `garment_meshes`, `garment_patterns` Supabase storage buckets. RLS policies: owner can read/write, service_role can read/write all. |
| 048 | Result persistence: save ZIP to Supabase | `garment-proxy/server.py` | On job complete, upload ZIP to garment_meshes bucket, store URL in garment_jobs row. Frontend fetches ZIP from Supabase CDN. |
| 049 | Perceptual hash cache (EC2) | `garment-proxy/server.py` | `imagehash.phash` → compare new upload to cached results. Skip GPU inference for near-identical images (same phash within hamming distance ≤ 5). Returns cached ZIP directly. |

## Track 2: Reconstruct UI — Dedicated CSS (Phases 050–069)

| Phase | Deliverable | File | Description |
|-------|------------|------|-------------|
| 050 | Audit shared `.ms-tryon-*` classes | `measurement-screen.css` | Grep `measurement-screen.css` for every `.ms-tryon-*` selector. Cross-reference against `buildReconstructView()` HTML template. List which classes are shared with actual Try-On and which are reconstruct-only. **Deliverable**: Annotated list at the top of the plan. |
| 051 | `.ms-recon-view` | `measurement-screen.css` | Copy `.ms-tryon-view` CSS block to new `.ms-recon-view` class. Same flex column layout, full height, overflow behavior. **Deliverable**: New CSS class in `measurement-screen.css`. |
| 052 | `.ms-recon-topbar` + `.ms-recon-back` | `measurement-screen.css` | Copy `.ms-tryon-topbar` → `.ms-recon-topbar`. Copy `.ms-tryon-back` → `.ms-recon-back`. Same header bar styling, mint green back button with hover/active states. **Deliverable**: New CSS classes in `measurement-screen.css`. |
| 053 | `.ms-recon-title` + `.ms-recon-subtitle` | `measurement-screen.css` | Copy `.ms-tryon-title` → `.ms-recon-title`. Copy `.ms-tryon-subtitle` → `.ms-recon-subtitle`. White bold title, gray subtitle. **Deliverable**: New CSS classes in `measurement-screen.css`. |
| 054 | `.ms-recon-input-area` | `measurement-screen.css` | Copy `.ms-tryon-input-area` → `.ms-recon-input-area`. Flex row container for upload area. **Deliverable**: New CSS class in `measurement-screen.css`. |
| 055 | `.ms-recon-preview-box` + `.ms-recon-preview-label` + `.ms-recon-preview-img` | `measurement-screen.css` | Copy the three `.ms-tryon-preview-*` classes. 3:4 aspect ratio container, small uppercase label, preview wrapper. **Deliverable**: 3 new CSS classes in `measurement-screen.css`. |
| 056 | `.ms-recon-placeholder` | `measurement-screen.css` | Copy `.ms-tryon-placeholder` → `.ms-recon-placeholder`. Centered flex with SVG icon + instruction text. **Deliverable**: New CSS class in `measurement-screen.css`. |
| 057 | `.ms-recon-upload-btn` | `measurement-screen.css` | Copy `.ms-tryon-upload-btn` → `.ms-recon-upload-btn`. Dashed-border upload button, same hover/active states. **Deliverable**: New CSS class in `measurement-screen.css`. |
| 058 | `.ms-recon-action-row` + `.ms-recon-generate-btn` | `measurement-screen.css` | Copy `.ms-tryon-action-row` → `.ms-recon-action-row`. Copy `.ms-tryon-generate-btn` → `.ms-recon-generate-btn`. Teal accent primary action button, disabled state styling. **Deliverable**: 2 new CSS classes in `measurement-screen.css`. |
| 059 | `.ms-recon-status` + `.ms-recon-spinner` | `measurement-screen.css` | Copy `.ms-tryon-status` → `.ms-recon-status`. Copy `.ms-tryon-spinner` → `.ms-recon-spinner`. Flex centered row, 36px CSS spinning ring animation. **Deliverable**: 2 new CSS classes in `measurement-screen.css`. |
| 060 | `.ms-recon-results` + `.ms-recon-results-label` | `measurement-screen.css` | Copy `.ms-tryon-results` → `.ms-recon-results`. Copy `.ms-tryon-results-label` → `.ms-recon-results-label`. Results section container, small uppercase label. **Deliverable**: 2 new CSS classes in `measurement-screen.css`. |
| 061 | `.ms-recon-error` + `.ms-recon-error-message` + `.ms-recon-error-dismiss` | `measurement-screen.css` | *New* — no try-on equivalent. `.ms-recon-error`: Red-tinted container, border, background. `.ms-recon-error-message`: Error text styling. `.ms-recon-error-dismiss`: Small dismiss button. **Deliverable**: 3 new CSS classes in `measurement-screen.css`. |
| 062 | `.ms-recon-progress-bar` + `.ms-recon-progress-fill` + `.ms-recon-progress-text` | `measurement-screen.css` | *New* — no try-on equivalent. Full-width progress bar container. `.ms-recon-progress-fill`: Animated fill element (width transitions). `.ms-recon-progress-text`: Step label overlay. **Deliverable**: 3 new CSS classes in `measurement-screen.css`. |
| 063 | `.ms-recon-3d-container` | `measurement-screen.css` | *New* — no try-on equivalent. Container div for embedded Three.js canvas. Aspect ratio 4:5, rounded corners, dark background. **Deliverable**: New CSS class in `measurement-screen.css`. |
| 064 | `.ms-recon-download-btn` | `measurement-screen.css` | *New* — no try-on equivalent. Styled download button for ZIP (not the same as generate). Download icon SVG, hover state. **Deliverable**: New CSS class in `measurement-screen.css`. |
| 065 | `.ms-recon-viewer-controls` | `measurement-screen.css` | *New* — Overlay controls for 3D viewer: rotate, zoom, fullscreen toggle buttons. Positioned absolute over the 3D container. **Deliverable**: New CSS class in `measurement-screen.css`. |
| 066 | `body.recon-mode` | `measurement-screen.css` | Copy `body.tryon-mode` → add `body.recon-mode` to same selectors. Hides header, sheet controls, tabs on mobile. Full-screen overlay on mobile (fixed inset, z-index 2200). **Deliverable**: Extended CSS selector in `measurement-screen.css`. |
| 067 | Replace `.ms-tryon-*` → `.ms-recon-*` in `buildReconstructView()` | `measurement-screen.js` | Replace every class reference in the HTML template. Replace IDs where appropriate (keep `ms-recon-*` IDs for JS hooks). **Deliverable**: Updated `buildReconstructView()` in `measurement-screen.js`. |
| 068 | Replace `tryon-mode` → `recon-mode` in `switchView()` | `measurement-screen.js` | Change body class from `tryon-mode` to `recon-mode`. Keep all the same chrome-hiding behavior. **Deliverable**: Updated `switchView()` in `measurement-screen.js`. |
| 069 | Responsive audit | `measurement-screen.css` | Test both views at 375px, 768px, 1440px. Confirm all `.ms-tryon-*` classes still render correctly for Try-On view. Confirm all `.ms-recon-*` classes render correctly for Reconstruct view. No CSS leaks between views. **Deliverable**: QA verification checklist passed. |

## Track 3: Reconstruct UI — Inline Error States (Phases 070–089)

| Phase | Deliverable | File | Description |
|-------|------------|------|-------------|
| 070 | Define 3 error types | `measurement-screen.js` | Define 3 error sub-states: **Validation error** (file too large, wrong format, no file), **Auth error** (session expired, not logged in), **Server error** (503, 502, 500, timeout). Each type has distinct icon + message + action button. **Deliverable**: Error state spec in document. |
| 071 | Add error container to template | `measurement-screen.js` | Add `<div class="ms-recon-error" id="ms-recon-error" style="display:none">` to template. Inner: `<div class="ms-recon-error-message" id="ms-recon-error-text"></div>`. Inner: `<button class="ms-recon-error-dismiss" onclick="KORRA_MS._dismissReconError()">×</button>`. **Deliverable**: Updated template in `measurement-screen.js`. |
| 072 | `_showReconError(message, type)` | `measurement-screen.js` | Accepts error string + type enum ('validation' | 'auth' | 'server'). Sets error container text, shows error container (display: block), hides status spinner, shows/hides generate button based on type. **Deliverable**: New method on `KORRA_MS` in `measurement-screen.js`. |
| 073 | `_dismissReconError()` | `measurement-screen.js` | Hides error container, restores UI to file-selected state if file still exists. **Deliverable**: New method in `measurement-screen.js`. |
| 074 | Error icons by type | `measurement-screen.js` | Validation: ⚠️ yellow triangle. Auth: 🔒 lock icon. Server: ❌ red X circle. SVG inline in `buildReconstructView()` or template strings. **Deliverable**: SVG icons in HTML template. |
| 075 | Auto-dismiss on re-upload | `measurement-screen.js` | Bind `onchange` in `_initReconstruct()` to call `_dismissReconError()`. User reselects file → error disappears. **Deliverable**: Updated `_initReconstruct()` in `measurement-screen.js`. |
| 076 | Validation: no file | `measurement-screen.js` | If `_runReconstruct()` called with null/undefined `_reconFile` — show validation error: "Please select a garment photo first". **Deliverable**: Guard clause in `_runReconstruct()` in `measurement-screen.js`. |
| 077 | Validation: unsupported format | `measurement-screen.js` | Check file.type in `_initReconstruct()` onchange. Reject non-image files (gif, webp, etc. are OK; PDF, txt, etc. are not). Show validation error: "Please select an image file (JPEG, PNG, WebP)". **Deliverable**: File type validation in `_initReconstruct()`. |
| 078 | Validation: file too large (20MB) | `measurement-screen.js` | Match proxy's 20MB limit. Check `file.size > 20 * 1024 * 1024` in `_initReconstruct()`. Show validation error: "Image too large (max 20MB)". **Deliverable**: File size check in `_initReconstruct()`. |
| 079 | Auth: session expired | `measurement-screen.js` | Replace `alert('Your session has expired...')` with `_showReconError('Your session has expired. Please sign in again.', 'auth')`. Add "Sign In" button in auth error state that triggers login flow. **Deliverable**: Updated auth error handling in `_runReconstruct()`. |
| 080 | Server: 503 unavailable | `measurement-screen.js` | Replace catch in `_runReconstruct()` for 503 responses. Show server error: "Garment reconstruction service is temporarily unavailable. Please try again in a few minutes." **Deliverable**: Updated 503 handling in `_runReconstruct()`. |
| 081 | Server: 502 backend error | `measurement-screen.js` | Replace catch for 502 responses. Show server error: "The reconstruction backend encountered an error. Our team has been notified." **Deliverable**: Updated 502 handling in `_runReconstruct()`. |
| 082 | Server: timeout (5min) | `measurement-screen.js` | Currently no frontend timeout — user just stares at spinner. Add `AbortController` with 310s timeout (just over proxy's 300s). Show server error on timeout: "Reconstruction timed out. Try a simpler garment photo." **Deliverable**: AbortController timeout in `_runReconstruct()`. |
| 083 | Server: network error | `measurement-screen.js` | Catch `TypeError: Failed to fetch` (network down, DNS failure). Show server error: "Network error. Check your internet connection and try again." **Deliverable**: Network error handling in `_runReconstruct()`. |
| 084 | Server: corrupt ZIP | `measurement-screen.js` | If res.blob() returns 0 bytes or wrong content-type. Show server error: "Received an empty response. Please try again." **Deliverable**: Post-success validation in `_runReconstruct()`. |
| 085 | Retry button | `measurement-screen.js` | After server error, show "Retry" button alongside dismiss. Clicking retry re-calls `_runReconstruct()` with same file. **Deliverable**: Retry button in error state in `measurement-screen.js`. |
| 086 | Error CSS transitions | `measurement-screen.css` | `.ms-recon-error` enters with fadeIn + slideDown animation (300ms), exits with fadeOut + slideUp animation (200ms). Error dismiss button fades on hover, error icon gets gentle shake for server errors. **Deliverable**: CSS animations in `measurement-screen.css`. |
| 087 | Console error logging | `measurement-screen.js` | `console.error('[Reconstruct]', { type, message, fileSize, timestamp })` in all error paths. Helps debug production issues. **Deliverable**: console.error calls in all error paths. |
| 088 | Client-side error analytics | `measurement-screen.js` | Track error count by type (validation/auth/server), surface in dashboard or monitoring endpoint. `_reconErrorCount = { validation: 0, auth: 0, server: 0 }`. **Deliverable**: Error tracking in `measurement-screen.js`. |
| 089 | QA: test all error paths | manual | Test validation: no file, bad file, too-large file. Test auth: expired token, missing token. Test server: stop Kaggle, stop proxy, timeout. **Deliverable**: QA verification checklist passed. |

## Track 4: Reconstruct UI — SSE Progress (Phases 090–109)

| Phase | Deliverable | File | Description |
|-------|------------|------|-------------|
| 090 | Define 6 progress event types | `measurement-screen.js` | `uploading→0`, `segmenting→15`, `meshing→35`, `patterning→65`, `zipping→90`, `complete→100`, `error→-1`. Each event has type, progress (0–100), and human-readable message string. **Deliverable**: Event type spec in document. |
| 091 | Progress bar in template | `measurement-screen.js` | Replace `<div class="ms-recon-spinner">` + static text with `<div class="ms-recon-progress-bar"><div class="ms-recon-progress-fill"></div></div>` + `<span class="ms-recon-progress-text" id="ms-recon-progress-text">Uploading image...</span>`. **Deliverable**: Updated HTML template in `buildReconstructView()`. |
| 092 | `_updateReconProgress(type, progress, message)` | `measurement-screen.js` | Accepts event type, progress %, message string. Updates progress bar width (`transform: scaleX(progress/100)`). Updates status text with message. **Deliverable**: New method on KORRA_MS in `measurement-screen.js`. |
| 093 | EventSource connection | `measurement-screen.js` | After POST returns `{ job_id }`, open `EventSource(progressUrl)`. Listen for `onmessage` events. Update progress bar on each event. Close EventSource on 'complete' or 'error'. **Deliverable**: SSE consumer in `_runReconstruct()`. |
| 094 | EventSource cleanup | `measurement-screen.js` | `close()` on 'complete' or 'error' or component unmount. Remove event listeners. Prevent memory leak from abandoned SSE connections. **Deliverable**: Cleanup in `measurement-screen.js`. |
| 095 | Per-step icon indicators | `measurement-screen.js` | Each step gets a small icon: Segmenting→🔍, Meshing→🏗️, Patterning→📐, Zipping→📦, Done→✅. Show current step icon + completed checkmarks for prior steps. **Deliverable**: Step indicator UI in `buildReconstructView()`. |
| 096 | Elapsed time counter | `measurement-screen.js` | Show "Elapsed: 0:23 / Estimated: ~2:00". Updated every second via `setInterval`. Estimate based on current step (segmenting=20s, meshing=50s, patterning=50s, zipping=5s). **Deliverable**: Elapsed time display. |
| 097 | Step-specific time estimates | `measurement-screen.js` | Per-step ETA: segmenting~20s, meshing~50s, patterning~50s, zipping~5s. Shown as dynamic estimated total in elapsed time counter. **Deliverable**: Time estimates in `measurement-screen.js`. |
| 098 | SSE reconnection | `measurement-screen.js` | EventSource auto-reconnects on drop. Add exponential backoff display: "Reconnecting... (attempt 2)". After 5 failed reconnection attempts, fall back to polling. **Deliverable**: Reconnection handling. |
| 099 | SSE heartbeat guard | `measurement-screen.js` | No event for 90s → show warning: "Still processing... this is taking longer than usual". After 300s with no complete event → timeout error. **Deliverable**: Timeout handling in `measurement-screen.js`. |
| 100 | Graceful degradation | `measurement-screen.js` | If proxy SSE endpoint returns 404 or 501, check `sse_supported` flag from health endpoint. Fall back to current polling (GET /api/v1/job/{id} every 3s). **Deliverable**: Fallback logic in `_runReconstruct()`. |
| 101 | Progress bar indeterminate pulse | `measurement-screen.css` | While waiting for first event: animated gradient pulse on the progress bar. Uses CSS keyframes with moving gradient background. **Deliverable**: CSS animation in `measurement-screen.css`. |
| 102 | Step indicator responsive | `measurement-screen.css` | Mobile: horizontal scroll for step indicators, compact labels. Desktop: full-width labels with icon + text side by side. **Deliverable**: Responsive CSS in `measurement-screen.css`. |
| 103 | Progress bar color states | `measurement-screen.css` | segmenting=blue (#4A90D9), meshing=purple (#9B59B6), patterning=orange (#E67E22), zipping=teal (#1DBFAF), complete=green (#2ECC71). Fill color transitions smoothly between states. **Deliverable**: CSS per-state colors. |
| 104 | QA: 6 events in order | manual | Start reconstruction, confirm all 6 progress events arrive in correct order. Kill tunnel mid-stream, test reconnection displays. **Deliverable**: QA verification. |
| 105 | QA: fallback to polling | manual | Return 404 from SSE endpoint, confirm polling kicks in and progress still works. **Deliverable**: QA verification. |
| 106 | QA: timeout display | manual | Kill Kaggle process mid-pipeline, confirm 300s timeout triggers, verify error message shown. **Deliverable**: QA verification. |
| 107 | Kaggle: add SSE status endpoint | `api_server.py` | `GET /api/v1/reconstruct/status` — returns current job status without polling overhead. Used by polling fallback. **Deliverable**: New endpoint in `api_server.py`. |
| 108 | Proxy: SSE health flag | `garment-proxy/server.py` | Health endpoint returns `sse_supported: true/false`. Frontend checks this before deciding to use SSE or polling. **Deliverable**: Updated health endpoint. |
| 109 | Proxy: SSE ↔ poll hybrid | `garment-proxy/server.py` | Open SSE connection to Kaggle. If no event received in 10s, fall back to polling. Continue trying SSE in background, switch back if it recovers. **Deliverable**: Hybrid relay in `server.py`. |

## Track 5: Reconstruct UI — 3D Preview (Phases 110–129)

| Phase | Deliverable | File | Description |
|-------|------------|------|-------------|
| 110 | Add JSZip dependency | HTML | `<script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js">` added to page. Or bundle with existing JS build. **Deliverable**: JSZip loaded in HTML. |
| 111 | Add 3D container to results template | `measurement-screen.js` | `<div class="ms-recon-3d-container" id="ms-recon-3d-container" style="display:none">` with child `<canvas id="ms-recon-3d-canvas"></canvas>`. Added to results section in `buildReconstructView()`. **Deliverable**: Updated HTML template. |
| 112 | `_renderReconMesh(zip)` | `measurement-screen.js` | Uses `JSZip.loadAsync(res.blob())` to read ZIP content in browser. Extracts `mesh_upper.obj`, `mesh_lower.obj` text. Creates blob URLs for Three.js loader. **Deliverable**: New method on KORRA_MS. |
| 113 | `_initReconViewer(containerId)` | `measurement-screen.js` | Creates new Three.js scene, camera, renderer. Dark background (0x1a1a1a), ambient + directional lighting. OrbitControls for interaction (rotate, pan, zoom). Same style as main korra_viz.js viewport. **Deliverable**: New method on KORRA_MS. |
| 114 | `loadGarmentFromOBJ(objText, color)` | `korra_viz.js` | Currently `loadGarment()` expects a URL. New overload accepts raw OBJ string, uses `THREE.OBJLoader().parse(objText)` internally, returns Three.js Group. **Deliverable**: Updated `korra_viz.js`. |
| 115 | Auto-rotate (0.5 rad/s, idle 3s) | `measurement-screen.js` | Auto-rotate at 0.5 rad/s when idle (no user interaction for 3s). `OrbitControls.autoRotate = true`. Toggle button: "Auto-Rotate: On/Off". **Deliverable**: Auto-rotate in `_initReconViewer()`. |
| 116 | Wireframe overlay toggle | `measurement-screen.js` | Small button overlay: "Show Wireframe". Toggles between solid render and wireframe render. Helps inspect mesh topology and garment structure. **Deliverable**: Wireframe toggle in `measurement-screen.js`. |
| 117 | Fullscreen toggle | `measurement-screen.js` | Button in top-right of 3D container. Expands to fill viewport (overlay, z-index 3000). Close button (×) returns to normal size. **Deliverable**: Fullscreen toggle. |
| 118 | Screenshot capture | `measurement-screen.js` | Button: "Capture Screenshot". Uses `renderer.domElement.toDataURL()`. Triggers download of PNG file with timestamp in filename. **Deliverable**: Screenshot in `measurement-screen.js`. |
| 119 | Mesh statistics display | `measurement-screen.js` | Below 3D container: vertex count, face count per mesh part. "Upper: 2,450 verts / 4,896 faces", "Lower: 1,820 verts / 3,636 faces". **Deliverable**: Stats display in `buildReconstructView()`. |
| 120 | Missing-part graceful handling | `measurement-screen.js` | If ZIP has only `mesh_upper.obj` (no lower): show upper only, display note. If ZIP has only `mesh_lower.obj` (no upper): show lower only, display note. If neither: hide 3D container, show "No 3D mesh in result". **Deliverable**: Graceful handling in `_renderReconMesh()`. |
| 121 | Three.js memory cleanup | `measurement-screen.js` | When navigating away from reconstruct view: `renderer.dispose()`, `geometry.dispose()`, `material.dispose()`, `texture.dispose()`. Prevent GPU memory leak across view switches. **Deliverable**: Cleanup in `switchView()`. |
| 122 | Garment mesh coloring | `measurement-screen.js` | Upper mesh: light blue (#4A90D9) with semi-transparency. Lower mesh: dark blue (#2C5F8A) with semi-transparency. Single-piece garment: teal (#1DBFAF). Materials stored for toggle visibility. **Deliverable**: Mesh coloring in `_renderReconMesh()`. |
| 123 | Loading overlay on 3D canvas | `measurement-screen.js` | While JSZip extracts + Three.js parses: show skeleton/spinner overlay on canvas. "Loading 3D mesh..." overlay text. Dismissed once mesh is rendered. **Deliverable**: Loading overlay in `_renderReconMesh()`. |
| 124 | Raycaster click info | `measurement-screen.js` | Raycaster on click: show face normal, vertex index on hover. Debug info overlay (small, fade-out after 3s). Useful for garment fit analysis. **Deliverable**: Click picking in `measurement-screen.js`. |
| 125 | OBJ download button | `measurement-screen.js` | Extract individual OBJ files from ZIP, download as standalone `.obj`. Separate buttons for upper and lower parts. Uses `URL.createObjectURL()` for download. **Deliverable**: OBJ download in `measurement-screen.js`. |
| 126 | Pattern SVG preview | `measurement-screen.js` | Parse `sewing_pattern.json` from ZIP. Overlay sewing pattern panels as SVG on right side of 3D container. Shows panel shapes with labels. **Deliverable**: Pattern preview in `buildReconstructView()`. |
| 127 | 3D container responsive | `measurement-screen.css` | Mobile: 100% width × 300px height. Desktop: max-width 400px × 500px height. Dark background (0x1a1a1a), rounded corners (8px), subtle border. **Deliverable**: CSS rules in `measurement-screen.css`. |
| 128 | QA: upper+lower mesh | manual | Test with both upper+lower mesh ZIP. Test with upper-only ZIP (one-piece garment). Test with corrupt ZIP (no mesh files). **Deliverable**: QA verification. |
| 129 | QA: memory leak check | manual | Navigate in/out of reconstruct view 10x. Check GPU memory usage before and after. Confirm no leak via browser dev tools. **Deliverable**: QA verification. |

## Track 6: Reconstruct → Try-On Bridge (Phases 130–144)

| Phase | Deliverable | File | Description |
|-------|------------|------|-------------|
| 130 | Store recon mesh on KORRA_MS | `measurement-screen.js` | `_reconMeshData = { upper: OBJText, lower: OBJText, pattern: JSON, zipBlob: Blob }`. Set after successful ZIP parse in `_runReconstruct()`. **Deliverable**: Data storage in `measurement-screen.js`. |
| 131 | Clear on new upload | `measurement-screen.js` | `_initReconstruct()` nulls `_reconMeshData`. Also cleared when view is destroyed or component unmounts. Prevents stale mesh data from previous reconstruction. **Deliverable**: Null check in `_initReconstruct()`. |
| 132 | "Use in Virtual Try-On" button | `measurement-screen.js` | Currently: just switches view, doesn't pass reconstructed mesh. New: store reconstructed mesh data on `KORRA_MS._reconMeshData`. On click: switch to try-on view, call `_updateGarmentForContext()` with stored mesh data. **Deliverable**: Updated button handler in `_runReconstruct()`. |
| 133 | `_loadReconMeshIntoTryon()` | `measurement-screen.js` | Called when "Use in Virtual Try-On" is clicked. Reads `_reconMeshData`, calls `_updateGarmentForContext()` with mesh data, switches view to 'tryon'. **Deliverable**: New method on KORRA_MS. |
| 134 | `_updateGarmentForContext()` overload | `measurement-screen.js` | Current: calls `POST /measurements/{scan_id}/garment/drape` (TailorNet). New overload: if `reconMeshData` present, skip TailorNet, use reconstructed mesh directly. Creates Three.js mesh from OBJ text, positions and scales over body scan. **Deliverable**: Updated `_updateGarmentForContext()`. |
| 135 | Auto-scale to body scan | `measurement-screen.js` | Reconstructed mesh is in arbitrary scale (relative to image). Auto-scale: fit mesh height to torso height of body scan. Uses bounding box comparison. **Deliverable**: Auto-scaling logic. |
| 136 | Manual scale slider | `measurement-screen.js` | Range 0.5x – 2.0x. Overrides auto-scale when adjusted. Real-time mesh scaling via slider `input` event. Includes reset button. **Deliverable**: Scale slider in `measurement-screen.js`. |
| 137 | Manual position controls | `measurement-screen.js` | X (left/right), Y (up/down), Z (forward/backward). Drag sliders or arrow buttons for each axis. Visual indicators showing offset values in cm. **Deliverable**: Position controls. |
| 138 | "Auto-Fit" button | `measurement-screen.js` | Aligns mesh bounding box to body scan bounding box. Centers garment on torso, adjusts rotation to match body pose. **Deliverable**: Auto-fit in `_loadReconMeshIntoTryon()`. |
| 139 | Garment opacity slider | `measurement-screen.js` | Slider: garment opacity 0%–100%. Blend modes: normal, multiply, screen. Helps see body scan through garment for fit check. **Deliverable**: Opacity control. |
| 140 | "Save Garment to Scan" | `measurement-screen.js` | Button: "Save Garment to This Scan". Stores mesh + pattern in Supabase storage. Links `garment_mesh_url` and `garment_pattern_url` to scan record. **Deliverable**: Save functionality. |
| 141 | "Load Saved Garment" | `measurement-screen.js` | If scan has saved garment, show "Load Saved Garment" button on revisit. Loads mesh from Supabase storage URL. No need to re-reconstruct. **Deliverable**: Load-from-storage. |
| 142 | Saved garment indicator | `measurement-screen.js` | Badge on scan card: "Has 3D garment". Visible in scan history/dashboard. Links directly to try-on view with saved garment loaded. **Deliverable**: Badge in dashboard. |
| 143 | Blueprint comparison | `measurement-screen.js` | Show pattern SVG next to garment on body. Side-by-side layout: left=3D body+garment, right=pattern panels. Overlay measurements on pattern. **Deliverable**: Blueprint overlay. |
| 144 | QA: try-on integration | manual | Reconstruct garment → click "Use in Virtual Try-On" → verify it loads on body. Test scaling slider, opacity slider. Test save → reload → verify persistence. **Deliverable**: QA verification. |

## Track 7: VTO Full Rotation (Phases 145–214)

### Track 7a: Frontend Logic & Asset Retrieval (Phases 145–156)

| Phase | Deliverable | File | Description |
|-------|------------|------|-------------|
| 145 | VTO auto-population | `measurement-screen.js` | Modify `buildTryOnView` to hide the "Person Upload" slot if `this.data.id` (scan ID) exists. Auto-populate from scan photos. **Code Ref**: Line 2101. |
| 146 | `_getScanPhotos()` helper | `measurement-screen.js` | Create helper to fetch URLs from `photo_front_url` and `photo_side_url` from KORRA_MS.data (populated in measurement-screen.js line 180). **Code Ref**: `photo_front_url`, `photo_side_url`. |
| 147 | `_checkTryOnReady()` guard | `measurement-screen.js` | Ensure try-on ready check only requires Garment File if scan photos are present. Skip person-photo validation when scan data exists. **Code Ref**: Line 2240. |
| 148 | Refinement loading state | `measurement-screen.js` | Add specific status message: "Refining your profile for digital fitting..." shown during SAM2 refinement pipeline. |
| 149 | `_vtoAngles = ['front', 'side', 'back']` | `measurement-screen.js` | Initialize three-angle data model on `KORRA_MS` object. Sets up data structure for multi-angle VTO results storage and retrieval. |
| 150 | Scan photo thumbnails | `measurement-screen.js` | Display original scan images as "Reference Images" in the VTO input area. Shows Front and Side thumbnails so user can verify scan quality. |
| 151 | `/tryon` scan_id passthrough | `api/routes/tryon.py` | Update `/tryon` endpoint to accept `scan_id` parameter. Internally resolve photo URLs from Supabase using the scan record. No need for frontend to pass photo URLs. |
| 152 | Refined photo persistence | `api/services/database_service.py` | Store refined "neutral" photos (after SAM2 refinement) in `profiles` storage bucket. Overwrite on re-refinement. |
| 153 | Multi-angle result slots | `measurement-screen.js` | Add `[FRONT][SIDE][BACK]` toggle buttons in VTO carousel. Each angle shows the corresponding VTO result image. Empty state for unfinished angles. |
| 154 | Missing scan fallback | `measurement-screen.js` | If user navigates directly to VTO without a scan, fall back to manual upload of front/side photos. Shows upload UI for both angles. |
| 155 | Refined-back cache check | `api/services/tryon_service.py` | Before running view synthesis, check if "Refined Back" already exists for this `scan_id`. Skip synthesis if cached. |
| 156 | VTO launch from scan sheet | `dashboard.html` | Verify VTO button exists on "Scan Result" sheet. Button navigates to VTO with scan_id parameter. |

### Track 7b: Persona Refinement & Synthesis (Phases 157–169)

| Phase | Deliverable | File | Description |
|-------|------------|------|-------------|
| 157 | SAM2 persona masking | `notebook.ipynb` | Implement background removal on retrieved Front/Side scan images. Use SAM2 with center-point prompt to extract user silhouette from original background. |
| 158 | Side-to-front alignment | `notebook.ipynb` | Align Side profile to Front using pose landmarks. Apply affine transform to match shoulder/hip positions. Ensures consistent positioning across angles. |
| 159 | Neutralization shader | `notebook.ipynb` | Apply gray-scale base-layer overlay for try-on standardization. Converts user's clothing in scan photos to neutral tone. Image-to-Image pass. |
| 160 | UV-space manifold projection | `api/services/shape_transformer.py` | Map 2D Front/Side textures (Skin + Base-Layer) into 3D SMPL UV-coordinates. Creates a UV texture map from the refined photos. |
| 161 | 180° occlusion map | `notebook.ipynb` | Identify "Texture Voids" in the UV-map caused by 180° camera rotation to back view. Marks areas that need in-painting. |
| 162 | VLM back-texture in-paint | `vlm/checkpoint-12844` | Use VLM to predict back textures (hair, skin, body shape) from front persona. VLM analyzes front style to in-paint back-view voids (glutes, back of head). |
| 163 | `POST /api/v1/synthesize-views` | `api_server.py` | Add endpoint to generate Front/Side/Back neutral triad. Runs full view synthesis pipeline: SAM2 refine → UV project → VLM in-paint → super-res. Returns triad URLs. |
| 164 | Back-view super-resolution | `notebook.ipynb` | Upscale synthesized back view to match original photo quality. Use Super-Res model to ensure texture detail matches front/side. |
| 165 | Symmetry verification | `notebook.ipynb` | AI checks that synthesized back matches shoulder-width measurements from scan. Verifies body proportions match the original scan data. |
| 166 | Hair/neck continuity | `vlm/checkpoint-12844` | VLM analyzes front hair length and style, extends it realistically to back view. Ensures hair/neck transition looks natural. |
| 167 | Lighting match | `notebook.ipynb` | Match synthesized back view's light source to original front photo. Analyzes front lighting direction and intensity, applies to back. |
| 168 | View triad result object | `api/routes/tryon.py` | Return JSON with all three processed source URLs: `{ front_url, side_url, back_url }`. Used by multi-angle VTO pipeline. |
| 169 | Backend synthesis test | `tests/` | Automated test verifying 180° rotation output. Test with known scan photos, verify back view has expected dimensions and quality. |

### Track 7c: Multi-Angle VTO Execution (Phases 170–185)

| Phase | Deliverable | File | Description |
|-------|------------|------|-------------|
| 170 | `asyncio.gather` three OOTDiffusion tasks | `api/services/tryon_service.py` | Run Front/Side/Back VTO in parallel using `asyncio.gather`. Each task processes one angle independently. Coordinate results for consistent output. |
| 171 | Consistent seed for all three views | `api/services/tryon_service.py` | Use same AI seed for all three angles → garment color/shape identical across front, side, and back views. Prevents visual inconsistency. |
| 172 | Garment body-map dispatch | `api/services/tryon_service.py` | Determine "Upper" or "Full Body" for all three angles. Ensures same garment type mapping across the entire rotation. |
| 173 | Multi-track SSE progress | `api_server.py` | Stream progress updates for each angle individually: `[0/3]`, `[1/3]`, `[2/3]`. Frontend shows per-angle progress in carousel. |
| 174 | Post-diffusion detail recovery | `notebook.ipynb` | Apply sharpen + denoise pass to VTO outputs. Recover fine details lost during diffusion (fabric texture, seams, edge crispness). |
| 175 | Result persistence to tryon_history | `api/services/database_service.py` | Save all three VTO result URLs and metadata to `tryon_history` JSONB column in Supabase. Timestamp, seed, garment type stored. |
| 176 | View-synchronized carousel | `measurement-screen.js` | `[FRONT][SIDE][BACK]` toggle buttons switch the displayed VTO image. Smooth cross-fade transition between angles (300ms). |
| 177 | Split-screen VTO layout | `measurement-screen.css` | `.ms-side-by-side` CSS class for VTO result view. Left: VTO image, Right: 3D mesh or pattern blueprint. |
| 178 | Multi-angle `_showTryOnResult` | `measurement-screen.js` | Replace single-image show with carousel support. Pass array of `{ angle, url }` objects instead of single URL. |
| 179 | Blueprint overlay per angle | `measurement-screen.js` | Show pattern SVG corresponding to active angle. Front: front pattern panel, Side: side panel, Back: back panel. |
| 180 | Linked zoom/pan VTO ↔ 3D | `measurement-screen.js` | Zoom on VTO image syncs to 3D mesh zoom state. Pan on one view moves the other. Keeps visual comparison aligned. |
| 181 | "Deep View" high-res modal | `dashboard.html` | Create modal to examine garment textures at full resolution. Zoom and pan within modal. Shows fabric detail close-up. |
| 182 | VTO history restore | `measurement-screen.js` | Allow users to re-load previous multi-angle try-ons from the ledger. Load from `tryon_history` JSONB. |
| 183 | Refined-source caching | `garment-proxy/server.py` | Cache neutralized Front/Side/Back triad images in proxy. Skip SAM2 refinement if triad already cached for this scan_id. |
| 184 | Synthesis QA | `tests/` | Manual verification of back-view anatomical accuracy. Check shoulder width, head position, hair continuity. |
| 185 | Error recovery per-angle | `measurement-screen.js` | If one angle fails, show remaining two + warning message. "Back view failed to generate. Front and Side views available." |

### Track 7d: VTO Hardening (Phases 186–214)

| Phase | Deliverable | File | Description |
|-------|------------|------|-------------|
| 186 | Portrait lock during synthesis | `dashboard.html` | Force portrait mode during loading sequence via CSS orientation media query. Show rotation reminder if in landscape. |
| 187 | Haptic feedback on angle switch | `measurement-screen.js` | Trigger haptic (`navigator.vibrate()`) when switching between `[FRONT]` ↔ `[BACK]` toggles. Subtle 10ms pulse. |
| 188 | VTO images in PDF export | `korra_export.js` | Add all three VTO angles to final generated PDF report. Each angle on separate page with timestamp and garment metadata. |
| 189 | Multi-view synthesis timeout | `garment-proxy/server.py` | 180s per-angle timeout, 540s total for all three angles. Return partial results if one angle times out. |
| 190 | Privacy face blur | `korra_viz.js` | Option to blur face in generated back view. Uses face detection model to mask face region. Configurable per-user. |
| 191 | VTO in share links | `api/routes/tryon.py` | Include generated VTO images in share-scan payload. Share link shows all three VTO angles. |
| 192 | AI Master Tailor integration | `AI_MASTER_TAILOR_CONSULTATION_PLAN.md` | Link VLM chat to active VTO result. User can ask about fit, fabric, or styling while viewing try-on. |
| 193 | VTO view dedicated URL param | `measurement-screen.js` | `?vto=scan_abc` loads VTO directly with scan data. Deep link support for sharing and navigation. |
| 194 | Garment type selector for VTO | `measurement-screen.js` | Dropdown: T-shirt, Dress, Jacket, Pants, Skirt. Passes garment type as model hint to diffusion pipeline. |
| 195 | Garment color picker pre-VTO | `measurement-screen.js` | Override garment color before synthesis. Color picker renders desired garment color for all three angles. |
| 196 | Side-view body completion | `notebook.ipynb` | If side photo is missing, generate it from front photo + SMPL mesh. Project front texture onto SMPL side view. |
| 197 | Back-view hair extension VLM fine-tune | `vlm/checkpoint-12844` | Fine-tune VLM on hair symmetry dataset for better back-view hair prediction. Improve hair texture and flow. |
| 198 | VTO result comparison slider | `measurement-screen.js` | Side-by-side before/after slider for each angle. Drag divider to compare VTO result with original scan photo. |
| 199 | VTO animation (cross-fade angles) | `measurement-screen.js` | Auto-rotate through `[Front]→[Side]→[Back]` with 2s crossfade. Play/pause button. Configurable speed. |
| 200 | Garment fit score per angle | `measurement-screen.js` | AI computes how well garment fits body in each view. Score 0-100 based on alignment, coverage, wrinkle detection. |
| 201 | VTO batch mode | `measurement-screen.js` | Queue multiple garments, process sequentially. Compare different garments on same body across all three angles. |
| 202 | VTO ARM64 CDN delivery | `garment-proxy/bootstrap.sh` | CloudFront or nginx cache for VTO result images. Serve optimized WebP from CDN with cache headers. |
| 203 | VTO result versioning | `api/services/tryon_service.py` | Keep last 3 VTO versions per scan. Allow user to revert to previous try-on result. |
| 204 | VTO rate limit (user-level) | `garment-proxy/server.py` | 5 VTO generations per user per day. Track in Supabase. Return 429 with reset timestamp when exceeded. |
| 205 | Studio 2.0 UI audit | `measurement-screen.css` | Final CSS polish for "Parallel Studio" experience. Consistent spacing, typography, color palette. Cross-view consistency. |
| 206 | DB migration for tryon_history | `scripts/run_migration.sh` | Schema update for JSONB array multi-angle storage. `ALTER TABLE scans ADD COLUMN tryon_history JSONB DEFAULT '[]'`. |
| 207 | Load test: 10 concurrent VTOs | `tests/` | wrk + custom lua script for `/synthesize-views`. Measure p50/p95/p99 latency. Identify bottlenecks. |
| 208 | VTO cold-start optimization | `notebook.ipynb` | Pre-warm SAM2 + VLM on heartbeat, not on first request. Keep models in GPU memory between requests. |
| 209 | VTO cost tracking | `scripts/monitoring/quota_check.py` | Track GPU minutes per VTO generation. Separate counters per angle. Alert on quota threshold. |
| 210 | VTO A/B test framework | `scripts/ab_test_framework.py` | Compare OOTDiffusion vs IDM-VTON quality. Random 50/50 split. Track user satisfaction score. |
| 211 | VTO user feedback collection | `measurement-screen.js` | "Was this try-on accurate?" thumbs up/down per angle. Aggregate scores over time. |
| 212 | VTO quality dashboard | `scripts/evaluate_pipeline.py` | Track MAE of garment alignment per angle. Compare against manual measurements. Historical trend graph. |
| 213 | Production deploy | `scripts/run_migration.sh` | Deploy DB migration + proxy + frontend. Run migration, restart proxy, deploy frontend assets. |
| 214 | MISSION COMPLETE: Full-Rotation VTO | — | Launch "Full-Rotation Virtual Try-On" feature. Announce to users. |

## Track 8: Polish & Launch (Phases 215–239)

| Phase | Deliverable | File | Description |
|-------|------------|------|-------------|
| 215 | Keyboard shortcuts | `measurement-screen.js` | `Esc`: Go back to previous view. `Enter` (when file selected): Trigger reconstruct. `Ctrl+S` (when complete): Download ZIP. **Deliverable**: Keyboard handler added to `measurement-screen.js`. |
| 216 | Drag-and-drop file upload | `measurement-screen.js` | Currently only `[Choose Image]` button triggers file dialog. Add: drag-drop zone over preview box. `dragover`/`dragleave` visual feedback (highlight border). `drop` handler calls `_initReconstruct()` onchange. **Deliverable**: Drag-drop in `measurement-screen.js`. |
| 217 | Loading skeleton placeholder | `measurement-screen.css` + `.js` | Before view is fully rendered: show skeleton placeholder with gray pulsing rectangles matching layout. Dismissed when `buildReconstructView()` completes. **Deliverable**: Skeleton CSS + JS. |
| 218 | "Take Photo" camera capture (mobile) | `measurement-screen.js` | Button: "Take Photo" (mobile only). Uses `navigator.mediaDevices.getUserMedia()`. Opens native camera, captures photo, uses as input. **Deliverable**: Camera capture in `measurement-screen.js`. |
| 219 | Recent reconstructions history | `measurement-screen.js` | Store last 5 reconstructions in `localStorage`. Each entry: timestamp, image preview (dataURL), mesh data keys. Show "Recent Reconstructions" below upload area. Click to reload previous result. **Deliverable**: History in `measurement-screen.js`. |
| 220 | Garment type selector | `measurement-screen.js` | Dropdown before reconstruct: "What type of garment?" Options: T-shirt, Shirt, Dress, Jacket, Pants, Skirt, Unknown. Passes `garment_type` to API for model hint. Default: "Unknown" (general pipeline). **Deliverable**: Garment type selector in `buildReconstructView()`. |
| 221 | AR preview (mobile) | `measurement-screen.js` | "View in AR" button (mobile ARCore/ARKit capable devices). Uses `<model-viewer>` or WebXR. Shows reconstructed mesh in real-world camera view. **Deliverable**: AR mode in `measurement-screen.js`. |
| 222 | Garment measurement overlay | `measurement-screen.js` | Parse `sewing_pattern.json` for measurements. Display: Chest, Waist, Hip, Length, Sleeve Length. Show in cm/inches toggle (reuse `.ms-unit-toggle`). **Deliverable**: Measurement display. |
| 223 | Compare with body scan | `measurement-screen.js` | Show garment measurements vs user's body measurements from scan. Highlight fit issues: too tight (garment < body), too loose (>20% ease), good fit. **Deliverable**: Comparison in `measurement-screen.js`. |
| 224 | Share reconstruction result | `measurement-screen.js` | Social share: "Check out this garment I reconstructed!" Share screenshot of 3D preview + measurements. Generates shareable image via canvas `toDataURL()`. **Deliverable**: Share functionality. |
| 225 | Reconstruct loading skeleton | `measurement-screen.js` | Pulsing placeholder shapes matching upload area layout. Shows before user interacts. Gray rectangles with shimmer animation. **Deliverable**: Skeleton in `measurement-screen.js`. |
| 226 | Full regression test suite | manual | Test all 7 original gaps closed. Flow: idle → file selected → reconstruct → progress → 3D preview → try-on. Error paths: validation, auth, server, timeout, network. **Deliverable**: QA checklist. |
| 227 | Cross-browser test | manual | Chrome, Firefox, Safari, Edge at 375px / 768px / 1440px. Verify SSE, 3D (WebGL), drag-drop, camera capture work across all browsers. **Deliverable**: Browser QA. |
| 228 | Bundle size audit | `measurement-screen.js` | JSZip + Three.js loads via CDN, not in bundle. Measure impact: measure-screen.js size before/after. Target < 50KB for main JS. **Deliverable**: Bundle analysis. |
| 229 | Lighthouse score target 85+ | — | Performance, accessibility, SEO audit. Optimize Largest Contentful Paint, reduce JS execution time, add ARIA labels. **Deliverable**: Lighthouse report. |
| 230 | Accessibility audit | `measurement-screen.js` | ARIA labels on all interactive elements. Keyboard navigation for 3D viewer (Tab, Arrow keys, Enter, Escape). Screen reader support for progress updates. **Deliverable**: A11y fixes. |
| 231 | Error tracking integration | `measurement-screen.js` | Send client errors to monitoring endpoint. POST structured error data: type, message, fileSize, timestamp, userAgent. **Deliverable**: Error tracking. |
| 232 | Usage analytics | `measurement-screen.js` | Track reconstruct completions, VTO generations, errors. Send to analytics endpoint. Privacy-compliant (no PII). **Deliverable**: Analytics. |
| 233 | Beta user feedback form | `measurement-screen.js` | In-app feedback after successful reconstruction. "How was your experience?" rating (1-5) + optional comment. **Deliverable**: Feedback form. |
| 234 | Soft launch to 10 beta users | — | Email invite with dedicated support channel. Monitor error rates, processing times, user satisfaction. |
| 235 | Bug fix sprint | all | Fix all beta-reported issues. Prioritize by severity: crashes > wrong output > UX issues > cosmetic. |
| 236 | Production deploy: proxy | `garment-proxy/deploy.sh` | Deploy updated proxy to EC2: `scp server.py`, restart systemd, verify health. **Deliverable**: Deployed proxy. |
| 237 | Production deploy: frontend | — | Deploy updated `measurement-screen.js` + `.css`. Invalidate CDN cache. Verify with health check. **Deliverable**: Deployed frontend. |
| 238 | Monitoring + alerting | `scripts/` | Health check cron, quota monitor, error rate alert. PagerDuty or email alert on critical failures. **Deliverable**: Monitoring. |
| 239 | Public launch | — | Enable for all users. Blog post + social media announcement. Feature flag rollout: 10% → 50% → 100%. **Deliverable**: Public launch. |

---

## Appendix A: Dependency Graph

```
Track 0 (Backend) ─────────────────────────► Track 1 (Hardening)
        │                                            │
        └────────────────────────────────────────────┘
                        │
                        ▼
         ┌──────────────┼──────────────┐
         │              │              │
         ▼              ▼              ▼
    Track 2       Track 3        Track 4
    (CSS)         (Errors)       (Progress)
         │              │              │
         └──────────────┼──────────────┘
                        │
                        ▼
                   Track 5
                   (3D Preview)
                        │
                        ▼
                   Track 6
                (Try-On Bridge)
                        │
                        ▼
                   Track 7
                (VTO Rotation)
                        │
                        ▼
                   Track 8
              (Polish & Launch)
```

**Prerequisites:**
- Track 0 must finish before Tracks 1–6 (no backend = nothing to build against)
- Tracks 2–4 can run in parallel (CSS, errors, progress are independent)
- Track 5 needs Track 4 (SSE progress tells 3D preview when ZIP is ready)
- Track 6 needs Track 5 (can't load mesh into try-on without 3D preview)
- Track 7 depends on Track 6 (try-on bridge provides reconstructed mesh to VTO pipeline)
- Track 8 depends on everything else

## Appendix B: File Change Summary

| File | Tracks | Estimated Changes |
|------|--------|-------------------|
| `kaggle-garment-backend/notebook.ipynb` | 0, 1, 7 | +200 lines (model loading, synthesis cells) |
| `kaggle-garment-backend/api_server.py` | 0, 1, 7 | +250 lines (SSE, view synthesis) |
| `kaggle-garment-backend/cell5_code.py` | 0 | +100 lines (keep-alive, tunnel registration) |
| `garment-proxy/server.py` | 0, 1, 7 | +200 lines (SSE relay, cache, Supabase jobs) |
| `garment-proxy/deploy.sh` | 0 | +50 lines (health verify, health check script copy) |
| `garment-proxy/bootstrap.sh` | 0 | +30 lines (ExecStartPost, cron, nginx) |
| `public/assets/measurement-screen.js` | 2–6, 7a, 7c, 8 | +1000 lines (all frontend features) |
| `public/assets/measurement-screen.css` | 2–6, 7c, 8 | +500 lines (dedicated recon classes, progress, 3D) |
| `public/assets/korra_viz.js` | 5 | +60 lines (loadGarmentFromOBJ, memory cleanup) |
| `api/routes/tryon.py` | 7a | +40 lines (scan_id passthrough, view triad) |
| `api/services/tryon_service.py` | 7b, 7c | +120 lines (parallel VTO, consistent seed) |
| `api/services/database_service.py` | 7a, 7c | +40 lines (refined photo persistence) |
| `scripts/e2e_garment_test.py` | 1 | +130 lines (4-stage test) |
| `scripts/garment_proxy_health_check.sh` | 1 | +24 lines (health probe) |
| `scripts/parse_proxy_logs.py` | 1 | +90 lines (log parser) |
| `scripts/auto_kaggle_rotate.py` | 1 | +80 lines (multi-account rotation) |
| `scripts/setup_garment_storage.py` | 1 | +60 lines (storage bucket + RLS) |
| `dashboard.html` | 7d, 8 | +30 lines (VTO launch button, deep view modal) |
| `korra_export.js` | 7d | +20 lines (VTO images in PDF) |
| `AI_MASTER_TAILOR_CONSULTATION_PLAN.md` | 7d | +10 lines (link VLM chat to VTO) |
| SQL migration | 1, 7d | +2 columns: garment_jobs.progress, progress_message; +tryon_history JSONB |

## Appendix C: Total Phase Count by Track

| Track | Phase Range | Count |
|-------|------------|-------|
| 0: Backend Infrastructure | 000–029 | 30 |
| 1: Pipeline Hardening + SSE | 030–049 | 20 |
| 2: Reconstruct CSS | 050–069 | 20 |
| 3: Reconstruct Errors | 070–089 | 20 |
| 4: Reconstruct Progress | 090–109 | 20 |
| 5: Reconstruct 3D Preview | 110–129 | 20 |
| 6: Reconstruct → Try-On Bridge | 130–144 | 15 |
| 7: VTO Full Rotation | 145–214 | 70 |
| 8: Polish & Launch | 215–239 | 25 |
| **Total** | **000–239** | **240** |
