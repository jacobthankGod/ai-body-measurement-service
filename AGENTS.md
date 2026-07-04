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
- Limbs use plane-mesh intersection with face-mask filtering (X-sign side filtering for bilateral limbs)
- Shoulder width uses dynamic mesh-based extreme-X extraction at `chest_y + 0.015` with 25-65cm sanity check
- All measurements scaled by `user_height_cm / (v_height * 100)`
- **Calibration**: Linear `corrected = alpha * smpl + beta` per-measurement per-gender via ridge regression from UniData (6 subjects); applied in both `measurement_engine.py` and `hmr_subprocess.py`

### Validation Datasets (status: 2026-06-26)
| Dataset | Subjects | Photos | Measurements | HMR-usable? |
|---------|----------|--------|-------------|-------------|
| **BodyM (AWS S3)** | **2,505** ✅ | ~9K binary silhouettes | 14 (3D scan gold standard) | ❌ Silhouettes |
| **UniData (Kaggle)** | **6** ⚠️ | 78 real photos (front+side+body-part) | 11 + height/weight/age/gender | ✅ Yes (but tiny) |
| **tapakah68 (Kaggle)** | **21** (metadata only) | No images in download | JSON format (files missing) | ❌ No images |
| **HF ud-biometrics** | **6** | 78 images (same as UniData) | Classification labels only | ❌ No measurements |
| **HF UniqueData/body** | 315 | Image URLs | Body-shape classification only | ❌ No regression data |
| **SSP-3D (GitHub)** | **311** ✅ | 311 sport images (tight clothes) | GT SMPL shapes from `labels.npz` | ✅ Yes (PVE gold standard) |
| **HBW (MPI)** | **10** ✅ | 705 val images | SMPL-X mesh measurements | ✅ Yes (SMPL-X pipeline) |

**Batch evaluation on UniData (6 subjects)** — MAE 37.4cm overall:
- Chest: MAE 24.2cm (overestimates, esp for males)
- Waist: MAE 67.4cm (massive overestimate — T-pose shape mismatch)
- Hip: MAE 72.9cm (massive overestimate — same cause)
- Thigh: MAE 6.9cm (reasonable)
- Calf: MAE 4.9cm (reasonable)
- Stomach: MAE 48.3cm (overestimate)
- Body shape classified as "Oval"/"Rectangle" for all, sizes M/XL
- Likely cause: HMR shape params from 2D image don't match true 3D shape; T-pose reconstruction amplifies errors

**Batch evaluation on SSP-3D (311 subjects)** — MAE 10.74cm overall (tight sportswear):
- Chest: MAE 16.6cm, Waist: MAE 18.7cm, Hip: MAE 12.1cm, Shoulder: MAE 5.3cm, Neck: MAE 5.7cm, Thigh: MAE 6.0cm
- T-pose reconstruction reduces waist/hip overestimation vs UniData (tight clothes help)

**Split test on UniData (6 subjects, 3 pipeline paths)** — after calibration integration:
- Fusion: MAE 7.2cm (Chest 6.7cm, Waist 8.3cm, Hip 7.6cm, Thigh 6.1cm)
- HMR raw: MAE 9.4cm (Waist 13.6cm, Hip 11.5cm, Chest 10.8cm)
- MediaPipe: MAE 7.0cm (Waist 9.5cm, Hip 11.3cm)
- Calibration improves Waist -39%, Chest -38%, Hip -34% on Fusion path
- **Known limitation**: Single calibration factor over-corrects S002 (large subject, GT waist 99 — HMR 98.0 was excellent); needs per-quantile or multi-factor calibration with more GT data

**PVE-T-SC on SSP-3D (311 subjects)** — Mean 2.16cm (SD=1.16cm):
- Scale-corrected per-vertex error between HMR-predicted T-pose mesh and GT SMPL shape
- Min: 0.39cm, Max: 5.23cm — confirms HMR shape params are accurate at the mesh level
- Persistent TF pipeline processes 311 subjs in ~370s (1.2s/subject)

### Limitations / Known Issues
- No ground-truth validation dataset with sufficient subjects
- SMPL mean template has T-pose which overestimates relaxed waist/hip
- MediaPipe `HAS_CV2` flag removed (cv2 no longer required)
- Clinical Realism Index is hardcoded to 97.0 (not actually computed from mesh)
- `mesh_validator.py` has circular validation (compares mesh against itself)
- `sh_indices` referenced before assignment bug in `_calculate_from_indices` — FIXED
- `Chest Round` missing from `FEMALE_KEYS` — FIXED (added to output list)
- **Calibration**: Single calibration factor over-corrects large subjects; needs per-quantile or multi-factor calibration with more GT data

### UI Modals (as of 2026-06-28)
- **Share Scan Modal** (`#shareScanModal`): Split-screen layout with `Share-screen-image-new.png` on left, form on right. Used to share individual scan results via link.
- **Invite Modal** (`#shareModal`): Split-screen layout with `Invite-screen-image.png` on left, form on right. Used to generate deep links for biometric enrollment. Includes Import from Contacts button, WhatsApp-specific phone field. Both use `.ss-*` CSS classes in `measurement-screen.css`.

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
| `scripts/compute_pve.py` | PVE-T-SC analysis: per-vertex error between HMR-predicted and GT SMPL meshes |
| `scripts/convert_unidata.py` | Converter: UniData Kaggle → batch_evaluation format |
| `scripts/convert_bodym.py` | Converter: BodyM AWS S3 → ground_truth.csv |
| `data/unidata/` | UniData dataset (6 subjects, front+side photos + ground_truth.csv) |
| `data/bodym/` | BodyM measurements CSVs + ground_truth.csv (2,505 subjects) |

### Relevant Conventions
- Subprocess communicates via JSON on stdout; stderr for logging
- All numpy bool/int/float/complex/object/str/unicode must be aliased at module level for TF1 compat
- Always use `gc.collect()` after mesh operations
- `OMP_NUM_THREADS=1` for t3.micro memory safety
- scipy `ConvexHull.area` returns perimeter in 2D
- `FEMALE_KEYS` includes both `Chest Round` and `Bust Round` (Bust Round = Chest Round for females)

### 250-Phase Self-Improving Accuracy Plan
See `PLAN_SELF_IMPROVING_ACCURACY.md` (4,100 lines) — full implementation plan for a self-supervised learning flywheel using production scan data.

**10 Major Tracks:**
| Phases | Track | Key Deliverable | Scans Needed |
|--------|-------|-----------------|-------------|
| 0–49 | Complete Data Capture | SMPL params stored per scan | 0 (blocker) |
| 50–82 | Dataset Pipeline | `build_training_dataset.py` | ≥ 100 |
| 83–95 | Storage & Schema | Production infra | 0 |
| 96–120 | Shape Prior | GMM shape prior deployed | ≥ 200 |
| 121–140 | Measurement Consistency | Outlier detection + shrinkage | ≥ 300 |
| 141–165 | Silhouette Consistency | IoU scores, shape optimization | ≥ 100 |
| 166–189 | Per-Subgroup Calibration | Cluster-specific factors | ≥ 500 |
| 190–217 | Continuous Training | Automated weekly pipeline | ≥ 100 |
| 218–235 | Monitoring & Evaluation | Accuracy dashboard | ≥ 100 |
| 236–250 | Advanced Models + Hardening | CNN surrogate, A/B test | ≥ 1000 |

**Phase 0 (SMPL capture) blocks everything else** — commit it first.

### Research Completed (2026-06-29)
- Deep tolerance research completed for all ~30 remaining attires (20+ web sources: tailor shops, size charts, pattern reviews, cultural garment guides)
- **5 corrections applied across frontend + backend**: Hawaiian Shirt 1.08→1.1, Abaya off 15→18, Vyshyvanka 1.08→1.15, Flamenco Dress 1.3→1.05, Anarkali 1.2→1.12
- All 104 entries cross-validated against research; 99 confirmed within acceptable ranges
- Key findings: Vyshyvanka size charts show 18-20% ease; Flamenco bodice has "practically no ease"; Anarkali tailors add 2-3" ease (8-12%); Pollera 4-8 varas fabric = 30%+ volume; Gho bloused at waist = 30%+ volume

## Phase 2-10 Implementation Status (2026-07-01)

### Phase 2: Supabase Storage & Schema ✅
- `scripts/setup_storage.py` — idempotent bucket creator for training_data, scan_photos, meshes
- `scripts/005_rls_policies.sql` — RLS for training_data (service_role), scan_photos/meshes (owner)
- `scripts/run_migration.sh` — updated with `RUN_ALL=true` mode, sequential multi-file runner

### Phase 3: Shape Prior (GMM) ✅
- `scripts/train_shape_prior.py` — BIC sweep for optimal K, train/val split, cluster analysis with per-gender evaluation, matplotlib plots
- `api/services/extract_measurements.py` — `_load_shape_prior()` loads GMM + scaler at init; `_apply_shape_prior()` shrinks implausible shapes (logprob < 5th percentile) toward nearest cluster mean

### Phase 4: Measurement Consistency ✅
- `scripts/train_consistency_model.py` — IsolationForest on multi-measurement vectors; z-score bounds per measurement; anomaly detection

### Phase 5: Silhouette Consistency ✅
- `scripts/compute_silhouette_consistency.py` — projects SMPL mesh to 2D via weak-perspective camera, computes IoU vs image mask; batch evaluation over dataset

### Phase 6: Per-Subgroup Calibration ✅
- `scripts/train_subgroup_calibration.py` — KMeans on (shape + gender + height); Ridge regression per-cluster per-measurement (alpha, beta); extends current gender-level calibration

### Phase 7: Continuous Training Pipeline ✅
- `scripts/continuous_training_pipeline.sh` — orchestrates: build dataset → train shape prior → train consistency model → train subgroup calibration → evaluate → deploy; dry-run mode, auto versioning, cron-ready

### Phase 8: Monitoring & Evaluation ✅
- `scripts/evaluate_pipeline.py` — loads dataset records, matches to ground truth, computes per-measurement MAE, shape statistics; generates JSON dashboard

### Phase 9: Advanced Models ✅
- `scripts/train_vae_shape_prior.py` — β-VAE (10→4→10) with PyTorch; early stopping; saves state_dict + normalization params

### Phase 10: Production Hardening ✅
- `scripts/ab_test_framework.py` — register/promote/rollback/starts for model version A/B testing; traffic splitting config; JSON log

### Track E: Freesewing Microservice ❌ (removed 2026-07-03)
Entire Freesewing implementation removed: `services/freesewing/` directory, Docker container, all frontend pattern code (PatternDraft engine, PatternTemplates, pattern tab/view, DXF export, download modal), backend `compute_freesewing_measurements()` in extract_measurements.py, and nginx proxy rules.

## Next Steps
- Run `setup_storage.py` (needs SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY)
- Run migration (needs SUPABASE_DB_URL)
- Backfill SMPL params for production scans
- Build first dataset → train models → deploy via A/B test
- Start Track F: TailorNet neural cloth simulation bridge
