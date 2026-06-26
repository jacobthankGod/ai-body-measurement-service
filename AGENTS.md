# AI Body Scan SaaS — Project Context

## Stack
- Frontend: Next.js, Tailwind CSS, Supabase auth
- Backend: FastAPI (Python), TF1/TF2 compatibility bridge for HMR model
- AI: HMR (Human Mesh Recovery) → SMPL body model → mesh-based measurements
- Infra: EC2 t3.micro, Supabase (DB + auth + storage), Paystack payments

## Key Architecture Decisions

### Measurement Pipeline (api/services/)
- **HMR-only runs in production** via `hmr_subprocess.py` (spawned as isolated OS process)
- Fusion path (`measurement_engine.py`) is wired but was previously disabled; now enabled via `hmr_subprocess.py`
- MediaPipe path (`mediapipe_measurement_engine.py`) was broken — `model_complexity` removed, RGB/BGR conversion fixed
- Plane-mesh intersection replaced bounding-box ellipse for torso measurements in `extract_measurements.py`

### Measurement Accuracy (as of latest session)
- SMPL faces loaded once in `HMRMasterEngine.__init__()` from `smpl_faces.npy`
- Torso measurements use plane-mesh intersection → `ConvexHull` perimeter
- Limbs still use bounding-box ellipse (until body-part face segmentation is added)
- Shoulder width uses dynamic mesh-based extreme-X extraction at `chest_y + 0.015` with 25-65cm sanity check
- All measurements scaled by `user_height_cm / (v_height * 100)`

### Limitations / Known Issues
- No ground-truth validation dataset yet
- SMPL mean template has T-pose which overestimates relaxed waist/hip
- MediaPipe `HAS_CV2` flag removed (cv2 no longer required)
- Clinical Realism Index is hardcoded to 97.0 (not actually computed from mesh)
- `mesh_validator.py` has circular validation (compares mesh against itself)

### Files to Know
| File | Purpose |
|---|---|
| `api/services/extract_measurements.py` | Core engine: HMR model, SMPL mesh, plane-mesh circumference |
| `api/services/hmr_subprocess.py` | Production subprocess: HMR + optional MediaPipe/ANSUR fusion |
| `api/services/mediapipe_measurement_engine.py` | MediaPipe Pose Landmarker + proportional measurements |
| `api/services/measurement_engine.py` | Full fusion engine (HMR + MP + ANSUR) — used by subprocess |
| `api/services/measurement_utils.py` | Unused geodesic function `calc_measure` |
| `api/services/mesh_validator.py` | Circular Clinical Realism Index |
| `api/services/imputation_service.py` | ANSUR II statistical imputation |
| `api/services/shape_transformer.py` | SMPL mesh deformation |
| `api/routes/measurements.py` | FastAPI route: accepts images, spawns subprocess |
| `data/customBodyPoints.txt` | Vertex group definitions for body parts |
| `scripts/batch_evaluation.py` | Batch evaluation script (needs real images + ground truth) |

### Relevant Conventions
- Subprocess communicates via JSON on stdout; stderr for logging
- All numpy bool/int/float/complex/object/str/unicode must be aliased at module level for TF1 compat
- Always use `gc.collect()` after mesh operations
- `OMP_NUM_THREADS=1` for t3.micro memory safety
- scipy `ConvexHull.area` returns perimeter in 2D

### Next Build / TODOs
1. Fix MediaPipe model file path (`pose_landmarker_full.task`) or auto-download
2. Create ground-truth dataset (10-20 subjects with tailor tape measurements)
3. Port body-part face segmentation from SMPL-Anthropometry for accurate limb circumference
4. Replace hardcoded Clinical Realism Index with actual mesh-based validation
5. Run batch_evaluation.py on real images to validate accuracy
6. Add trimesh as optional dependency for better plane-mesh intersection
