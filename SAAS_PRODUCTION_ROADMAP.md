# Body Measurement SaaS: Production Implementation Roadmap

## 1. Project Objective
Build a standalone, production-ready AI Body Measurement SaaS platform hosted on Vercel. This service will allow external applications (like Desby OS) to extract precision body measurements from dual photos using a secure API Key.

## 2. Technical Stack
- **Backend:** FastAPI (Python 3.10+)
- **Hosting:** Vercel (Serverless Functions)
- **AI Core:**
  - HMR (3D Human Mesh Recovery) for vertex-based accuracy (±1-2cm)
  - MediaPipe Pose Landmarker for keypoint-based precision (±3-5cm)
  - Anthropometric Ratios for fail-safe fallback
- **Authentication:** API Key Header (`X-API-Key`)
- **Database:** Supabase/Firebase (for API key management and usage quotas)

## 3. Atomic Implementation Steps

### Phase 1: Dependency & Environment Stabilization (COMPLETED ✅)
- [x] Fix `mediapipe` model assets (Download real `pose_landmarker_full.task`)
- [x] Resolve `chumpy` installation for HMR support
- [x] Downgrade `numpy` for legacy HMR compatibility
- [x] Verify measurement logic with synthetic landmarks

### Phase 2: Standalone API Refactoring
- [ ] Decouple AI services from Desby app logic
- [ ] Implement robust error handling for invalid image formats
- [ ] Add `X-API-Key` middleware for authentication
- [ ] Create `/v1/extract` endpoint accepting height, gender, and base64/file images

### Phase 3: Vercel Deployment Strategy
- [ ] Configure `vercel.json` with Python runtime
- [ ] Optimize model loading (Lazy loading models in serverless functions)
- [ ] Set up `api/index.py` as entry point for Vercel
- [ ] Configure environment variables for API keys

### Phase 4: SaaS Monetization & Quotas
- [ ] Implement simple usage tracking (Request logging)
- [ ] Define API key permission levels (Free/Basic/Pro)
- [ ] Add endpoint for subscription status and remaining quotas

### Phase 5: Flutter Integration (Desby OS)
- [ ] Update `BodyMeasurementService` to use external URL
- [ ] Securely store SaaS API key in Desby OS config
- [ ] Add loading/progress indicators for neural scanning animation

## 4. Accuracy Cascade (Deterministic)
1. **HMR 3D:** Vertex-to-vertex measurement (requires TensorFlow + SMPL models)
2. **MediaPipe Pose:** Keypoint-to-keypoint measurement (requires `.task` model file)
3. **Anthropometric:** Height-to-ratio measurement (no external dependencies)

## 5. Deployment Checklist
- [ ] `chumpy` installed
- [ ] `scipy` installed
- [ ] `mediapipe` installed
- [ ] Model files uploaded to Vercel (or stored in cloud bucket)
- [ ] API Key generated and stored
