# KORRA Self-Improving Accuracy System — 250-Phase Implementation Plan

> **Vision:** Every production scan feeds the model. The system gets more hyper-accurate with each user, without manual ground-truth collection. Front/side images + 3D mesh + SMPL parameters form a growing training corpus that continuously improves shape prediction, measurement extraction, and calibration.
>
> **Core Insight:** The HMR model outputs 85-dim theta vectors (camera 3 + pose 72 + shape 10) and 6890-vertex T-pose meshes that are currently discarded after measurement extraction. By preserving these intermediates and building a self-supervised learning loop, we create a flywheel where more scans → better shape prior → more accurate measurements → more trust → more scans.

---

## Table of Contents

1. [Phase 0: Complete Data Capture (0–49)](#phase-0-complete-data-capture-phases-0-49)
2. [Phase 1: Dataset Aggregation Pipeline (50–82)](#phase-1-dataset-aggregation-pipeline-phases-50-82)
3. [Phase 2: Supabase Storage & Schema (83–95)](#phase-2-supabase-storage--schema-finalization-phases-83-95)
4. [Phase 3: Shape Prior Learning (96–120)](#phase-3-shape-prior-learning-phases-96-120)
5. [Phase 4: Measurement Consistency Model (121–140)](#phase-4-measurement-consistency-model-phases-121-140)
6. [Phase 5: Silhouette Consistency (141–165)](#phase-5-silhouette-consistency-phases-141-165)
7. [Phase 6: Per-Subgroup Calibration (166–189)](#phase-6-per-subgroup-calibration-phases-166-189)
8. [Phase 7: Continuous Training Pipeline (190–217)](#phase-7-continuous-training-pipeline-phases-190-217)
9. [Phase 8: Monitoring & Evaluation (218–235)](#phase-8-monitoring--evaluation-phases-218-235)
10. [Phase 9: Advanced Model Training (236–248)](#phase-9-advanced-model-training-phases-236-248)
11. [Phase 10: Production Hardening (249–250)](#phase-10-production-hardening-phases-249-250)

---

## Phase 0: Complete Data Capture (Phases 0–49)

*Without this phase, nothing else is possible. Every intermediate value currently computed inside `HMRMasterEngine.extract()` must be captured, serialized, and persisted. Currently the function returns 7 values but `theta_full`, `results['joints3d']`, and `results['theta']` are discarded after local use.*

In `extract_measurements.py:274`, the `extract()` method signature returns 7 values after HMR inference. At line 336–338, `results = model.predict_dict(img_batch)` produces a dict containing `'verts'` (6890×3), `'joints'` (19×3), and `'theta'` (85-dim), but only `'verts'` and `'joints'` are used. The 85-dim `'theta'` vector contains the weak-perspective camera params [3], the 24 joint rotations as axis-angle vectors [72], and the 10 SMPL shape coefficients [10].

### Phase 0.1 — Extract SMPL Parameters from HMR Output (Phases 0–8)

---

**Phase 0: Extract theta_full unconditionally before conditional logic block**

- **File:** `api/services/extract_measurements.py`
- **Line:** Starting at 378, the current code only reads `theta_full` inside an `if` block that's inside a `try` block. If the T-pose computation fails, `theta_full` is never extracted and goes out of scope.

**Current code (lines 378–385):**
```python
v_measure = vertices
if self._v_template is not None and self._shapedirs is not None:
    try:
        theta_full = results['theta'][0]
        shapes = np.array(theta_full[75:85], dtype=np.float64).reshape(10)
        v_shaped = self._v_template + (self._shapedirs @ shapes).reshape(-1, 3)
        v_measure = v_shaped
    except Exception as e:
        logger.warning(f"T-pose measurement failed, falling back to posed mesh: {e}")
```

**Problem:** If the SMPL template files are missing, `theta_full` is never extracted. The solution is to extract theta unconditionally before the `if` block, then use the pre-extracted `shapes` for T-pose computation.

**New code (after line 338, before `# 7. MULTI-VIEW DEPTH REFINEMENT`):**
```python
# Extract SMPL params unconditionally (needed for self-improving dataset)
smpl_params = None
joints3d = None
try:
    theta_full = results['theta'][0]
    camera_params = theta_full[0:3].tolist()  # scale, tx, ty
    pose_params = theta_full[3:75].tolist()    # 24 joints × 3 axis-angle
    shape_params = theta_full[75:85].tolist()  # 10 PCA shape coefficients
    smpl_params = {'camera': camera_params, 'pose': pose_params, 'shape': shape_params}
    joints3d = results['joints'][0].tolist()   # 19 joints × 3 coordinates
except Exception as e:
    logger.warning(f"SMPL param extraction failed: {e}")
```

---

**Phase 1: Use pre-extracted shapes for T-pose computation**

After extracting `smpl_params`, the shape params are already available as `shape_params`. The T-pose computation block at lines 378–385 can use these directly:

```python
# Measurements from T-pose mesh (shape-only, no pose deformation)
v_measure = vertices
if self._v_template is not None and self._shapedirs is not None and smpl_params is not None:
    try:
        shapes = np.array(smpl_params['shape'], dtype=np.float64).reshape(10)
        v_shaped = self._v_template + (self._shapedirs @ shapes).reshape(-1, 3)
        v_measure = v_shaped
    except Exception as e:
        logger.warning(f"T-pose measurement failed, falling back to posed mesh: {e}")
```

---

**Phase 2: Update the function signature to include smpl_params, joints3d**

- **File:** `api/services/extract_measurements.py`
- **Line:** 274

**Current signature (7-element tuple):**
```python
def extract(self, image: np.ndarray, height_cm: float, gender: str = 'male',
            side_image: Optional[np.ndarray] = None) -> Tuple[
    Dict[str, float], Optional[np.ndarray], Optional[dict], str, str, Optional[str], Optional[np.ndarray]]:
```

**New signature (9-element tuple):**
```python
def extract(self, image: np.ndarray, height_cm: float, gender: str = 'male',
            side_image: Optional[np.ndarray] = None) -> Tuple[
    Dict[str, float], Optional[np.ndarray], Optional[dict], str, str,
    Optional[str], Optional[np.ndarray], Optional[dict], Optional[list]]:
```

The tuple elements are now:
1. `final_measurements` (Dict) — corrected measurements
2. `vertices_scaled` (np.ndarray) — posed mesh scaled to real-world units
3. `landmark_2d` (dict) — 2D landmarks
4. `body_shape` (str) — body shape classification
5. `size_rec` (str) — size recommendation
6. `error` (Optional[str]) — error message or None
7. `v_measure` (Optional[np.ndarray]) — T-pose mesh vertices
8. `smpl_params` (Optional[dict]) — camera, pose, shape from theta
9. `joints3d` (Optional[list]) — 19×3 joint coordinates

---

**Phase 3: Return new values in the success path**

- **File:** `api/services/extract_measurements.py`
- **Line:** 415

**Current:**
```python
return final_measurements, vertices_scaled, landmark_2d, body_shape, size_rec, None, v_measure
```

**New:**
```python
return final_measurements, vertices_scaled, landmark_2d, body_shape, size_rec, None, v_measure, smpl_params, joints3d
```

---

**Phase 4: Return new values in the TF-not-found error path**

- **File:** `api/services/extract_measurements.py`
- **Line:** 282

**Current:**
```python
return self._fallback_ratios(height_cm, gender), None, None, "Standard", "M", "TensorFlow not found"
```

**New:**
```python
return self._fallback_ratios(height_cm, gender), None, None, "Standard", "M", "TensorFlow not found", None, None, None
```

Note: this was a 6-element return; now it's 9 elements. All callers must handle this.

---

**Phase 5: Return new values in the general exception path**

- **File:** `api/services/extract_measurements.py`
- **Line:** 420

**Current:**
```python
return self._fallback_ratios(height_cm, gender), None, None, "Standard", "M", str(e), None
```

**New:**
```python
return self._fallback_ratios(height_cm, gender), None, None, "Standard", "M", str(e), None, None, None
```

---

**Phase 6: Return new values in the no-theta-in-results guard path**

Insert a new guard after line 338 (`results = model.predict_dict(img_batch)`):

```python
if 'theta' not in results:
    logger.error("HMR model did not return theta params")
    return self._fallback_ratios(height_cm, gender), None, None, "Standard", "M", \
           "No theta in results", None, None, None
```

---

**Phase 7: Update the module-level convenience function**

- **File:** `api/services/extract_measurements.py`
- **Line:** 673–677

**Current:**
```python
def extract_measurements_from_hmr(image, height, gender='male', side_image=None):
    """Returns (measurements, vertices, landmarks, body_shape, size_rec, error, mesh_tpose).
    mesh_tpose is the T-pose predicted mesh (6890x3) for PVE analysis, or None on failure.
    """
    return ENGINE.extract(image, height, gender, side_image=side_image)
```

**New:**
```python
def extract_measurements_from_hmr(image, height, gender='male', side_image=None):
    """Returns (measurements, vertices, landmarks, body_shape, size_rec, error, mesh_tpose,
    smpl_params, joints3d).
    smpl_params is {'camera': [...], 'pose': [...], 'shape': [...]} from HMR theta.
    joints3d is the 19x3 SMPL joints array.
    """
    return ENGINE.extract(image, height, gender, side_image=side_image)
```

---

**Phase 8: Extract smpl_params and joints3d before the multi-view block for completeness**

Move the SMPL extraction to immediately after line 338 (`vertices = results['verts'][0]`), before the multi-view refinement block at line 343. This ensures the raw HMR output is saved before any depth refinement modifies `vertices`.

```python
# 6. INFERENCE
logger.info("HMR: Executing isolated 3D inference...")
results = model.predict_dict(img_batch)
vertices = results['verts'][0]
joints = results['joints'][0]

# INTERLEAVE: Extract raw SMPL params before any depth refinement
smpl_params = None
joints3d = None
try:
    theta_full = results['theta'][0]
    smpl_params = {
        'camera': theta_full[0:3].tolist(),
        'pose': theta_full[3:75].tolist(),
        'shape': theta_full[75:85].tolist(),
    }
    joints3d = results['joints'][0].tolist()
except Exception as e:
    logger.warning(f"SMPL param extraction failed: {e}")
```

---

### Phase 0.2 — Thread Return Values Through Subprocess (Phases 9–15)

---

**Phase 9: Update unpacking in hmr_subprocess.py for 9-element tuple**

- **File:** `api/services/hmr_subprocess.py`
- **Line:** 59–68

**Current code:**
```python
if isinstance(extraction_result, tuple):
    measurements = extraction_result[0]
    vertices = extraction_result[1]
    landmarks = extraction_result[2]
    body_shape = extraction_result[3]
    size_rec = extraction_result[4]
    error = extraction_result[5]
```

**New code with backward compatibility:**
```python
if isinstance(extraction_result, tuple):
    measurements = extraction_result[0]
    vertices = extraction_result[1]
    landmarks = extraction_result[2]
    body_shape = extraction_result[3]
    size_rec = extraction_result[4]
    error = extraction_result[5]
    # New fields: backward-compatible if old engine version
    v_measure_tpose = extraction_result[6] if len(extraction_result) > 6 else None
    smpl_params = extraction_result[7] if len(extraction_result) > 7 else None
    joints3d = extraction_result[8] if len(extraction_result) > 8 else None
```

The `if len(extraction_result) > N` guard ensures that during the rollout window (before the old engine is updated), the subprocess doesn't crash when unpacking a 7-element tuple.

---

**Phase 10: Export T-pose mesh to OBJ alongside posed mesh**

- **File:** `api/services/hmr_subprocess.py`
- **After:** line 83 (posed mesh export)

**Current (lines 79–83):**
```python
mesh_url = None
if mesh_path and vertices is not None:
    from api.services.mesh_exporter import MeshExporter
    MeshExporter.save_to_obj(vertices, mesh_path)
    mesh_url = mesh_path
```

**New — export T-pose mesh:**
```python
mesh_url = None
tpose_mesh_path = None
if mesh_path and vertices is not None:
    from api.services.mesh_exporter import MeshExporter
    MeshExporter.save_to_obj(vertices, mesh_path)
    mesh_url = mesh_path
    
    # Export T-pose mesh if available
    if v_measure_tpose is not None:
        tpose_path = str(mesh_path).replace('.obj', '_tpose.obj')
        MeshExporter.save_to_obj(v_measure_tpose, tpose_path)
        tpose_mesh_path = tpose_path
        logger.info(f"T-pose mesh exported to {tpose_path}")
```

---

**Phase 11: Preserve `v_measure_tpose` — modify cleanup to avoid double-free**

- **File:** `api/services/hmr_subprocess.py`
- **Line:** 152

**Current:**
```python
# FINAL CLEANUP
del vertices
gc.collect()
```

**New:**
```python
# FINAL CLEANUP
if v_measure_tpose is not None and v_measure_tpose is not vertices:
    del v_measure_tpose
del vertices
gc.collect()
```

The identity check `is not` is correct here because when T-pose computation falls back to posed mesh, `v_measure_tpose` is the same object as `vertices`. In that case we should only `del` once.

---

**Phase 12: Sanity-check T-pose mesh dimensions before export**

Add after the T-pose export in Phase 10:
```python
# Sanity check T-pose mesh dimensions
if v_measure_tpose is not None:
    v_range = np.max(v_measure_tpose, axis=0) - np.min(v_measure_tpose, axis=0)
    logger.info(f"T-pose mesh dims: X={v_range[0]:.3f} Y={v_range[1]:.3f} Z={v_range[2]:.3f}")
    if v_range[1] < 0.5 or v_range[1] > 3.0:
        logger.warning(f"T-pose height {v_range[1]:.3f}m outside expected [0.5, 3.0]")
```

---

**Phase 13: Add smpl_params, joints3d, tpose_mesh_path to subprocess stdout JSON**

- **File:** `api/services/hmr_subprocess.py`
- **Line:** 155–164

**Current return dict:**
```python
return {
    "status": "completed",
    "measurements": measurements,
    "landmarks": landmarks,
    "body_shape": body_shape,
    "size_recommendation": size_rec,
    "clinical_realism_index": clinical_realism_index,
    "fusion_used": fusion_used,
    "mesh_path": str(mesh_path) if mesh_path else None
}
```

**New return dict:**
```python
return {
    "status": "completed",
    "measurements": measurements,
    "landmarks": landmarks,
    "body_shape": body_shape,
    "size_recommendation": size_rec,
    "clinical_realism_index": clinical_realism_index,
    "fusion_used": fusion_used,
    "mesh_path": str(mesh_path) if mesh_path else None,
    "smpl_params": smpl_params,
    "joints3d": joints3d,
    "tpose_mesh_path": str(tpose_mesh_path) if tpose_mesh_path else None
}
```

---

**Phase 14: Add serialization guards for numpy types in JSON output**

The subprocess output is serialized via `json.dumps()` in `hmr_subprocess.py:188`. Since `smpl_params` contains Python lists (converted from numpy arrays via `.tolist()`), this should work. But add a safety net:

```python
# At the return point, validate JSON serializability
import json
try:
    json.dumps(smpl_params)
except TypeError as e:
    logger.error(f"SMPL params not JSON-serializable: {e}")
    smpl_params = None  # Degrade gracefully
```

---

**Phase 15: Ensure MediaPipe fusion doesn't overwrite raw HMR measurements**

The MediaPipe fusion at lines 100–125 currently supplements measurements with MediaPipe-derived values. This happens AFTER smpl_params are captured, so it's safe. But the measurement_calibration at line 145–149 applies calibration factors — these happen before the subprocess returns, so the returned measurements are already calibrated. We need the RAW (pre-calibration) measurements stored in `smpl_params` for calibration training.

Store the raw measurements alongside smpl_params:
```python
smpl_params['raw_measurements'] = measurements.copy()
```

This way, when we train calibration factors, we can compare raw HMR measurements vs. "final" measurement targets.

---

### Phase 0.3 — Route Layer: Parse and Persist New Fields (Phases 16–25)

*The FastAPI route `measurements.py:run_extraction_subprocess_cli()` receives the subprocess JSON output and orchestrates persistence. We need to parse the new fields and pass them through to the database service.*

---

**Phase 16: Parse smpl_params, joints3d, tpose_mesh_path from subprocess output**

- **File:** `api/routes/measurements.py`
- **Lines:** 190–191 (in the `if data.get("status") == "completed":` block after `measurements = data["measurements"]`)

Add after line 191:
```python
smpl_params = data.get("smpl_params")
joints3d = data.get("joints3d")

# Upload T-pose mesh to Supabase Storage
tpose_mesh_url = None
tpose_mesh_path = data.get("tpose_mesh_path")
if tpose_mesh_path and os.path.exists(tpose_mesh_path):
    tpose_mesh_url = DatabaseService.upload_mesh_to_storage(
        Path(tpose_mesh_path), f"{task_id}_tpose"
    )
```

---

**Phase 17: Clean up T-pose mesh temp file after upload**

Add after the upload:
```python
if tpose_mesh_path and os.path.exists(tpose_mesh_path):
    os.remove(tpose_mesh_path)
    logger.info(f"Cleaned up T-pose temp file: {tpose_mesh_path}")
```

---

**Phase 18: Pass new fields to DatabaseService.save_measurement()**

- **File:** `api/routes/measurements.py`
- **Lines:** 211–219

**Current call:**
```python
save_result = DatabaseService.save_measurement(
    user_id=user_id, client_name=client_name, height=height,
    gender=gender, biometrics=measurements, landmarks=landmarks,
    mesh_url=mesh_url, body_shape=body_shape, size_rec=size_rec,
    client_user_id=client_user_id,
    clinical_realism_index=clinical_realism_index,
    mesh_storage_url=mesh_storage_url
)
```

**New call with smpl_params, joints3d, tpose_mesh_url:**
```python
save_result = DatabaseService.save_measurement(
    user_id=user_id, client_name=client_name, height=height,
    gender=gender, biometrics=measurements, landmarks=landmarks,
    mesh_url=mesh_url, body_shape=body_shape, size_rec=size_rec,
    client_user_id=client_user_id,
    clinical_realism_index=clinical_realism_index,
    mesh_storage_url=mesh_storage_url,
    smpl_params=smpl_params, joints3d=joints3d,
    tpose_mesh_url=tpose_mesh_url
)
```

---

**Phase 19: Include new fields in the final return dict (for task status endpoint)**

- **File:** `api/routes/measurements.py`
- **Lines:** 230–240

**Add to return dict:**
```python
return {
    "status": "completed",
    "measurements": measurements,
    "mesh_url": mesh_url,
    "mesh_storage_url": mesh_storage_url,
    "landmarks": landmarks,
    "body_shape": body_shape,
    "size_recommendation": size_rec,
    "clinical_realism_index": clinical_realism_index,
    "smpl_params": smpl_params,
    "joints3d": joints3d,
    "tpose_mesh_url": tpose_mesh_url,
    "debug": hmr_error
}
```

---

**Phase 20: Include new fields in widget extraction path (lines 408–447)**

The widget endpoint at `/measurements/extract-widget` also calls `run_extraction_task` → `run_extraction_subprocess_cli`. Since we modified the return dict in Phase 19, the widget path will automatically pass through the new fields.

---

**Phase 21: Handle missing Photo URLs gracefully for backfill**

The `photo_front_url` and `photo_side_url` are already being set at lines 271–275. For the backfill scenario (which we're building separately), these are critical because without photo URLs we can't re-extract SMPL params from old scans. Ensure the widget path also uploads photos:

The existing code at lines 271–275 already uploads photos for the merchant endpoint. The widget endpoint at lines 408–447 doesn't explicitly call `save_measurement` — it goes through `run_extraction_task` which calls `run_extraction_subprocess_cli`. The photo upload happens in `run_extraction_task` at lines 267–275, so it's covered.

---

**Phase 22: Add validation for smpl_params structure**

In `measurements.py`, after parsing `smpl_params`:
```python
if smpl_params is not None:
    # Validate structure
    if not all(k in smpl_params for k in ('camera', 'pose', 'shape')):
        logger.warning(f"Invalid smpl_params structure for task {task_id}")
        smpl_params = None
    elif len(smpl_params.get('shape', [])) != 10:
        logger.warning(f"Invalid shape vector length for task {task_id}")
        smpl_params = None
```

---

### Phase 0.4 — Database Service Layer (Phases 23–31)

*The `DatabaseService.save_measurement()` method stores scan data in the `measurements` Supabase table. We embed SMPL params in the `biometrics` JSONB to avoid schema changes for every new field, but add a dedicated `tpose_mesh_url` column for queryability.*

---

**Phase 23: Add smpl_params, joints3d, tpose_mesh_url to save_measurement()**

- **File:** `api/services/database_service.py`
- **Line:** 139 (function signature)

**Current signature:**
```python
@classmethod
def save_measurement(cls, user_id: str, client_name: str, height: float, gender: str,
                     biometrics: dict, landmarks: dict = None, mesh_url: str = None,
                     body_shape: str = None, size_rec: str = None,
                     client_user_id: str = None, clinical_realism_index: float = None,
                     mesh_storage_url: str = None, photo_front_url: str = None,
                     photo_side_url: str = None):
```

**New signature:**
```python
@classmethod
def save_measurement(cls, user_id: str, client_name: str, height: float, gender: str,
                     biometrics: dict, landmarks: dict = None, mesh_url: str = None,
                     body_shape: str = None, size_rec: str = None,
                     client_user_id: str = None, clinical_realism_index: float = None,
                     mesh_storage_url: str = None, photo_front_url: str = None,
                     photo_side_url: str = None,
                     smpl_params: dict = None, joints3d: list = None,
                     tpose_mesh_url: str = None):
```

---

**Phase 24: Embed smpl_params into biometrics JSONB with __ prefix**

Inside `save_measurement()`, before constructing the merchant_payload:
```python
# Embed SMPL parameters into biometrics JSONB for dataset pipeline
biometrics_with_smpl = biometrics.copy() if biometrics else {}
if smpl_params:
    # Prefixed with __ to avoid collision with actual measurement keys
    biometrics_with_smpl['__smpl_params'] = smpl_params
if joints3d:
    biometrics_with_smpl['__joints3d'] = joints3d
```

The `__` prefix convention is important: measurement keys are human-readable strings like "Chest Round", "Waist Round", "Shoulder" — none start with underscore. The double underscore also follows Python's name-mangling convention, making it clear these are internal system fields.

---

**Phase 25: Add tpose_mesh_url to merchant payload**

- **File:** `api/services/database_service.py`
- **Lines:** 162–178 (merchant_payload dict construction)

Add `"tpose_mesh_url": tpose_mesh_url` to the `merchant_payload` dict.

---

**Phase 26: Add tpose_mesh_url to client payload**

- **File:** `api/services/database_service.py`
- **Lines:** 193–209 (client_payload dict construction)

Add `"tpose_mesh_url": tpose_mesh_url` to the `client_payload` dict.

---

**Phase 27: Replace biometrics with biometrics_with_smpl in payloads**

Update the merchant_payload to use `"biometrics": biometrics_with_smpl` instead of `"biometrics": biometrics`.
Same for client_payload.

---

**Phase 28: Add logging for SMPL data persistence**

After the merchant save succeeds:
```python
if smpl_params:
    shape_len = len(smpl_params.get('shape', []))
    logger.info(f"SMPL params stored: {shape_len} shape dims, {len(smpl_params.get('pose', []))} pose dims")
```

---

**Phase 29: Handle the case where biometrics is None**

The current code doesn't handle `biometrics=None` well. Add a guard:
```python
if not biometrics:
    biometrics = {}
biometrics_with_smpl = biometrics.copy()
```

---

**Phase 30: Add storage_uploaded_at logging**

When `tpose_mesh_url` is set, log: "T-pose mesh stored at {tpose_mesh_url}".

---

**Phase 31: Return structured result in save_measurement()**

The current return is `results if results else None`. Add SMPL confirmation info:
```python
return {
    'merchant_saved': len([r for r in results if r['account'] == 'merchant']) > 0 if results else False,
    'client_saved': len([r for r in results if r['account'] == 'client']) > 0 if results else False,
    'smpl_stored': smpl_params is not None,
}
```

---

### Phase 0.5 — SQL Schema Migration (Phases 32–40)

---

**Phase 32: Create migration file 004_smpl_params_migration.sql**

New file at `scripts/004_smpl_params_migration.sql`:

```sql
-- 004_smpl_params_migration.sql
-- Add SMPL parameter storage for self-improving accuracy system
-- Part of Phase 0: Complete Data Capture

-- 1. Add SMPL-specific columns to measurements table
ALTER TABLE measurements ADD COLUMN IF NOT EXISTS smpl_params JSONB;
ALTER TABLE measurements ADD COLUMN IF NOT EXISTS joints_3d JSONB;
ALTER TABLE measurements ADD COLUMN IF NOT EXISTS tpose_mesh_url TEXT;
ALTER TABLE measurements ADD COLUMN IF NOT EXISTS smpl_params_version INTEGER DEFAULT 1;
ALTER TABLE measurements ADD COLUMN IF NOT EXISTS storage_uploaded_at TIMESTAMPTZ;
ALTER TABLE measurements ADD COLUMN IF NOT EXISTS dataset_version INTEGER;

-- 2. Index for fast dataset aggregation queries
CREATE INDEX IF NOT EXISTS idx_measurements_smpl_params_not_null
    ON measurements (id)
    WHERE smpl_params IS NOT NULL;

-- 3. Composite index for stratified dataset queries (gender + height)
CREATE INDEX IF NOT EXISTS idx_measurements_gender_height_smpl
    ON measurements (gender, height)
    WHERE smpl_params IS NOT NULL;

-- 4. Index for body shape subgroup filtering
CREATE INDEX IF NOT EXISTS idx_measurements_body_shape_gender_smpl
    ON measurements (body_shape, gender)
    WHERE smpl_params IS NOT NULL;

-- 5. Training runs metadata table
CREATE TABLE IF NOT EXISTS training_runs (
    id SERIAL PRIMARY KEY,
    version INTEGER NOT NULL,
    dataset_version INTEGER NOT NULL,
    scan_count INTEGER NOT NULL,
    male_count INTEGER DEFAULT 0,
    female_count INTEGER DEFAULT 0,
    height_min REAL,
    height_max REAL,
    sha256_manifest TEXT,
    shape_stats JSONB,
    meas_stats JSONB,
    gmm_bic REAL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status TEXT DEFAULT 'running'
);

-- 6. Training-run-to-scans junction table
CREATE TABLE IF NOT EXISTS training_run_scans (
    run_id INTEGER REFERENCES training_runs(id) ON DELETE CASCADE,
    scan_id UUID REFERENCES measurements(id) ON DELETE CASCADE,
    PRIMARY KEY (run_id, scan_id)
);

-- 7. Index for dataset version queries
CREATE INDEX IF NOT EXISTS idx_measurements_dataset_version
    ON measurements (dataset_version)
    WHERE dataset_version IS NOT NULL;

-- 8. Index for tpose_mesh_url existence
CREATE INDEX IF NOT EXISTS idx_measurements_tpose_mesh
    ON measurements (id)
    WHERE tpose_mesh_url IS NOT NULL;
```

---

**Phase 33: Create `scripts/run_migration.sh`**

```bash
#!/bin/bash
# Run SQL migration against Supabase database
# Usage: ./run_migration.sh [migration_file]

MIGRATION_FILE=${1:-"scripts/004_smpl_params_migration.sql"}

if [ -z "$SUPABASE_DB_URL" ]; then
    echo "Error: SUPABASE_DB_URL environment variable not set"
    exit 1
fi

echo "Running migration: $MIGRATION_FILE"
psql "$SUPABASE_DB_URL" -f "$MIGRATION_FILE"

if [ $? -eq 0 ]; then
    echo "Migration completed successfully"
else
    echo "Migration failed"
    exit 1
fi
```

---

**Phase 34: Run the migration**

```bash
chmod +x scripts/run_migration.sh
./scripts/run_migration.sh scripts/004_smpl_params_migration.sql
```

---

**Phase 35: Verify migration with query**

```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'measurements' 
  AND column_name IN ('smpl_params', 'joints_3d', 'tpose_mesh_url', 'dataset_version');
```

---

**Phase 36: Create the `api/models/priors/` directory**

```bash
mkdir -p api/models/priors
touch api/models/priors/__init__.py
```

---

**Phase 37: Create the `data/training_dataset/` directory**

```bash
mkdir -p data/training_dataset
```

---

**Phase 38: Create the `data/tmp/` directory for temp files**

```bash
mkdir -p data/tmp
```

---

### Phase 0.6 — Backfill Existing Scans (Phases 41–49)

*Hundreds of existing scans have front/side photos but no SMPL params. A backfill script re-processes them to extract the SMPL params via batch HMR inference.*

---

**Phase 41: Create `scripts/backfill_smpl_params.py`**

This script queries Supabase for measurements WHERE smpl_params IS NULL AND photo_front_url IS NOT NULL, downloads the photos, runs HMR inference, and updates the records with the extracted params.

The script architecture:

1. Query scans without SMPL params (paginated, BATCH_SIZE=20 for OOM safety)
2. For each scan: download front photo (and side photo if available)
3. Run `HMRMasterEngine.extract()` — but discard measurements, keep only smpl_params + joints3d
4. Update the measurement record via Supabase API
5. Clean up temp files
6. Sleep 2 seconds between scans to prevent OOM on t3.micro

---

**Phase 42: Add dry-run mode to backfill script**

```bash
python scripts/backfill_smpl_params.py --dry-run --limit 50
# Output: "Found 847 scans without SMPL params. Would process 50."
```

---

**Phase 43: Run backfill batch 1**

```bash
python scripts/backfill_smpl_params.py --limit 20
```

---

**Phase 44: Monitor backfill progress**

```bash
tail -f logs/backfill.log
```

---

**Phase 45: Run remaining batches with resume**

```bash
# After batch 1 completes with last_scan_id="abc-123"
python scripts/backfill_smpl_params.py --limit 20 --resume "abc-123"
```

---

**Phase 46: Validate backfilled data**

Run a validation script:
```sql
SELECT COUNT(*) AS total,
       COUNT(smpl_params) AS with_smpl,
       COUNT(*) - COUNT(smpl_params) AS missing_smpl
FROM measurements;
```

---

**Phase 47: Check for extreme shape params in backfilled data**

```python
import json
from supabase import create_client
import os

supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
response = supabase.table("measurements").select("id, smpl_params").not_.is_("smpl_params", "null").limit(100).execute()

for row in response.data:
    shape = row['smpl_params'].get('shape', [])
    if any(abs(s) > 4.0 for s in shape):
        print(f"Extreme shape: {row['id']} -> {shape}")
```

---

**Phase 48: Create verify_backfill.py script**

```python
#!/usr/bin/env python3
"""Verify backfill integrity."""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.services.extract_measurements import HMRMasterEngine
import numpy as np

# Test that the engine still loads SMPL params correctly
engine = HMRMasterEngine()
print(f"Vertex map loaded: {len(engine.vertex_map)} groups")
print(f"SMPL faces loaded: {engine.smpl_faces.shape if engine.smpl_faces is not None else 'NO'}")

# Test a mock extraction with random noise
fake_img = np.random.randn(224, 224, 3).astype(np.float32)
result = engine.extract(fake_img, 175, 'male')
if len(result) >= 9:
    print(f"smpl_params present: {result[7] is not None}")
    print(f"joints3d present: {result[8] is not None}")
else:
    print(f"Only {len(result)} elements returned (expected >= 9)")
```

---

**Phase 49: Backfill summary report**

```sql
SELECT 
    COUNT(*) FILTER (WHERE smpl_params IS NOT NULL) AS with_smpl,
    COUNT(*) FILTER (WHERE smpl_params IS NULL) AS without_smpl,
    COUNT(*) FILTER (WHERE tpose_mesh_url IS NOT NULL) AS with_tpose,
    MIN(created_at) FILTER (WHERE smpl_params IS NOT NULL) AS first_smpl_scan,
    MAX(created_at) FILTER (WHERE smpl_params IS NOT NULL) AS last_smpl_scan
FROM measurements;
```

---

## Phase 1: Dataset Aggregation Pipeline (Phases 50–82)

*With SMPL params now flowing into every new scan (and backfilled into old scans), we build the infrastructure to assemble the complete dataset. This pipeline downloads all assets from Supabase Storage, organizes them into a structured directory, generates manifests and splits, and computes dataset statistics.*

---

### Phase 1.1 — Core Dataset Builder (Phases 50–60)

---

**Phase 50: Create `scripts/build_training_dataset.py` — entry point + CLI**

The script accepts `--version` (required), `--limit`, `--offset`, `--incremental`, `--output-dir`, `--dry-run`, `--min-quality`, `--require-tpose`, `--clean`, `--max-workers` arguments.

Prerequisite: `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` environment variables.

Implementation steps:
1. Connect to Supabase
2. Query `measurements` WHERE `smpl_params IS NOT NULL` — paginated
3. Apply quality filters (min clinical_realism_index, require tpose_mesh_url, etc.)
4. For each scan: create `scan_{id}/` subdirectory, download front.png, side.png, mesh_posed.obj, mesh_tpose.obj from Storage URLs
5. Extract SMPL params from biometrics JSONB `__smpl_params` key
6. Write `metadata.json` with all normalized fields
7. Generate `manifest.csv` with summary row per scan
8. Generate stratified train/val/test splits (90/5/5 by gender)
9. Compute and save shape statistics (mean, std, covariance)
10. Compute and save measurement distributions (percentiles per subgroup)

---

**Phase 51: Implement the manifest CSV generator**

Fields in `manifest.csv`:
```
scan_id, gender, height_cm, body_shape, has_front, has_side, 
has_mesh_posed, has_mesh_tpose, has_smpl_params, n_measurements,
clinical_realism_index, sha256_front, sha256_side
```

The SHA256 hashes enable deduplication — if the same photo appears in multiple scans (unlikely but possible with re-scans), we can detect duplicates.

---

**Phase 52: Implement train/val/test split generator**

Stratification logic:
1. Separate scans by gender (male, female)
2. For each gender, apply 90/5/5 split using `sklearn.model_selection.train_test_split` with `random_state=42`
3. If fewer than 10 scans in a gender group, assign all to train
4. Write split files: `splits/train.txt`, `splits/val.txt`, `splits/test.txt` (one scan_id per line)

---

**Phase 53: Implement shape statistics computation**

Compute and save `shape_statistics.json`:
- n_scans, mean, std, min, max, covariance matrix
- Per-dimension percentiles (P5, P25, P50, P75, P95)
- Correlation matrix (to identify which shape dimensions co-vary)

---

**Phase 54: Implement measurement statistics computation**

Compute and save `measurement_statistics.json`:
- Per measurement: mean, std, P5, P25, P50, P75, P95
- Stratified by gender, height bin (5 cm intervals), and body shape
- Only groups with >= 3 samples are recorded

---

**Phase 55: Add progress bar with tqdm**

```python
from tqdm import tqdm
for scan in tqdm(scans, desc="Downloading scans"):
    # process...
```

---

**Phase 56: Add parallel download via ThreadPoolExecutor**

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def download_scan(scan, output_dir):
    # ... process single scan ...
    return metadata

with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
    futures = {executor.submit(download_scan, s, output_dir): s['id'] for s in scans}
    for future in tqdm(as_completed(futures), total=len(futures)):
        metadatas.append(future.result())
```

---

**Phase 57: Add resume from checkpoint**

If the script is interrupted (e.g., OOM on t3.micro), it can resume from the last successfully processed scan:
```python
checkpoint_file = output_dir / ".checkpoint"
if checkpoint_file.exists() and not args.clean:
    last_id = checkpoint_file.read_text().strip()
    # Filter scans to only those after last_id
    scans = [s for s in scans if s['id'] > last_id]

# After each scan completes:
checkpoint_file.write_text(scan['id'])
```

---

**Phase 58: Add comprehensive logging**

Log every step with timestamps and memory usage:
```python
import tracemalloc
tracemalloc.start()
# ... after each batch ...
current, peak = tracemalloc.get_traced_memory()
logger.info(f"Memory: current={current/1024/1024:.1f}MB, peak={peak/1024/1024:.1f}MB")
```

---

**Phase 59: Handle HTTP 429 rate limiting from Supabase Storage**

Add exponential backoff for download failures:
```python
import time
for attempt in range(5):
    try:
        resp = httpx.get(url, timeout=30)
        if resp.status_code == 429:
            wait = 2 ** attempt
            logger.warning(f"Rate limited, waiting {wait}s")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.content
    except Exception as e:
        if attempt == 4:
            raise
        time.sleep(2 ** attempt)
```

---

**Phase 60: Generate dataset version tag**

After successful build, create a `VERSION` file with timestamp and statistics:
```json
{
    "version": 1,
    "created_at": "2026-07-01T03:00:00Z",
    "n_scans": 847,
    "n_male": 412,
    "n_female": 435,
    "height_min": 145,
    "height_max": 198,
    "sha256_summary": "a1b2c3d4...",
    "train_val_test": "762_42_43",
    "gmm_trained": false
}
```

---

### Phase 1.2 — Incremental Builds (Phases 61–65)

---

**Phase 61: Implement incremental mode for build_training_dataset.py**

The `--incremental` flag triggers checkpoint-based incremental mode:
1. Load `.dataset_checkpoint` file containing ISO timestamp of last build
2. Only process scans with `created_at > checkpoint`
3. Append to existing manifest.csv instead of overwriting
4. Regenerate splits (including new scans in distribution)
5. Update checkpoint timestamp

---

**Phase 62: Store checkpoint in Supabase training_runs table**

After each successful build, update the training_runs table with:
```sql
INSERT INTO training_runs (version, dataset_version, scan_count, ...)
VALUES (next_version, current_version, scan_count, ...);
```

---

**Phase 63: Set checkpoint update to happen after all scans are processed**

```python
# At end of build_training_dataset.main():
save_checkpoint(datetime.utcnow().isoformat())
```

---

**Phase 64: Add --auto-increment flag**

When `--auto-increment` is set, the script reads the latest version from `training_runs` table and increments:
```python
latest_version = supabase.table("training_runs") \
    .select("version").order("version", desc=True).limit(1).execute()
new_version = (latest_version.data[0]['version'] + 1) if latest_version.data else 1
```

---

**Phase 65: Handle empty incremental builds**

If no new scans since last checkpoint:
```python
if len(new_scans) == 0:
    logger.info("No new scans since last build. Skipping.")
    return
```

---

### Phase 1.3 — Quality Filtering (Phases 66–72)

---

**Phase 66: Implement clinical_realism_index filter**

```python
if args.min_quality > 0:
    before = len(scans)
    scans = [s for s in scans if (s.get('clinical_realism_index') or 0) >= args.min_quality]
    logger.info(f"Quality filter ({args.min_quality}): {before} -> {len(scans)}")
```

---

**Phase 67: Implement T-pose mesh requirement**

```python
if args.require_tpose:
    before = len(scans)
    scans = [s for s in scans if s.get('tpose_mesh_url')]
    logger.info(f"T-pose requirement: {before} -> {len(scans)}")
```

---

**Phase 68: Implement body shape filter**

```python
scans = [s for s in scans if s.get('body_shape') and s['body_shape'] != 'Unknown']
```

---

**Phase 69: Implement shape outlier filter**

Extract shape params from the biometrics JSONB and check for extreme values:
```python
def is_extreme_shape(biometrics):
    smpl = biometrics.get('__smpl_params', {})
    shape = smpl.get('shape', [])
    if len(shape) != 10:
        return False
    return any(abs(s) > 3.5 for s in shape)

before = len(scans)
scans = [s for s in scans if not is_extreme_shape(s.get('biometrics', {}))]
logger.info(f"Shape outlier filter: {before} -> {len(scans)}")
```

---

**Phase 70: Implement side photo requirement (optional)**

```python
if args.require_side:
    before = len(scans)
    scans = [s for s in scans if s.get('photo_side_url')]
    logger.info(f"Side photo requirement: {before} -> {len(scans)}")
```

---

**Phase 71: Add --all-quality-flags convenience option**

```bash
# Combines: --min-quality 70 --require-tpose --filter-unknown-body-shape
python build_training_dataset.py --version 2 --high-quality
```

---

**Phase 72: Log filter summary at end**

```python
logger.info("=" * 60)
logger.info("QUALITY FILTER SUMMARY")
logger.info(f"  Total scans with SMPL: {total_scans}")
logger.info(f"  After clinical realism filter: {after_cri} ({total_scans - after_cri} removed)")
logger.info(f"  After T-pose requirement: {after_tpose}")
logger.info(f"  After shape outlier filter: {after_shape}")
logger.info(f"  Final dataset size: {len(scans)}")
```

---

### Phase 1.4 — Advanced Statistics & Validation (Phases 73–82)

---

**Phase 73: Compute and save per-gender shape statistics**

```python
male_shapes = np.array([m['smpl_params']['shape'] for m in metadatas if m and m['gender'] == 'male'])
female_shapes = np.array([m['smpl_params']['shape'] for m in metadatas if m and m['gender'] == 'female'])

gender_stats = {}
if len(male_shapes) > 10:
    gender_stats['male'] = {
        'mean': male_shapes.mean(axis=0).tolist(),
        'std': male_shapes.std(axis=0).tolist(),
        'n': len(male_shapes),
    }
if len(female_shapes) > 10:
    gender_stats['female'] = {
        'mean': female_shapes.mean(axis=0).tolist(),
        'std': female_shapes.std(axis=0).tolist(),
        'n': len(female_shapes),
    }

# Save
stats_path = output_dir / "gender_shape_stats.json"
stats_path.write_text(json.dumps(gender_stats, indent=2))
```

---

**Phase 74: Compute and save measurement-to-shape correlations**

```python
# For each measurement, compute correlation with each shape dimension
measurements_list = []
shapes_list = []
for meta in metadatas:
    if meta is None: continue
    shapes_list.append(meta['smpl_params']['shape'])
    m = meta['measurements']
    measurements_list.append([
        m.get('Chest Round', 0), m.get('Waist Round', 0),
        m.get('Hip Round', 0), m.get('Shoulder', 0),
    ])

if len(shapes_list) > 10:
    shapes_arr = np.array(shapes_list)
    meas_arr = np.array(measurements_list)
    corr = np.corrcoef(shapes_arr.T, meas_arr.T)
    # Save correlation matrix
```

---

**Phase 75: Generate HTML summary report**

Using a simple template, generate `dataset_v{N}_report.html` with:
- Dataset overview (scans, genders, height range)
- Shape parameter distribution plots (histograms for each of 10 dims)
- Measurement distribution plots per gender
- Split sizes
- Quality filter counts

Since we're in a headless server environment, generate the plots as base64-embedded PNGs using matplotlib.

---

**Phase 76: Add `--plot` flag for generating visualization**

```python
if args.plot:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    # ... generate plots ...
```

---

**Phase 77: Validate dataset integrity after build**

```python
def validate_dataset(output_dir):
    """Check that all expected files exist and are valid."""
    errors = []
    
    # Check manifest
    manifest = output_dir / "manifest.csv"
    if not manifest.exists():
        errors.append("Manifest missing")
    
    # Check splits
    for split in ['train', 'val', 'test']:
        split_file = output_dir / "splits" / f"{split}.txt"
        if not split_file.exists():
            errors.append(f"Split {split} missing")
    
    # Check scan directories
    scan_dirs = list(output_dir.glob("scan_*"))
    for sd in scan_dirs:
        meta = sd / "metadata.json"
        if not meta.exists():
            errors.append(f"Metadata missing in {sd.name}")
            continue
        m = json.loads(meta.read_text())
        if not m.get('smpl_params'):
            errors.append(f"SMPL params missing in {sd.name}")
    
    if errors:
        for e in errors:
            logger.warning(f"Validation error: {e}")
    else:
        logger.info("Dataset validation passed")
```

---

**Phase 78: Add `--validate` mode for quick checks**

```bash
python build_training_dataset.py --validate data/training_dataset/v1
```

---

**Phase 79: Add incremental scan ID logging for data drift tracking**

Each build records the set of scan IDs included. Comparison between versions helps track drift:
```python
if not args.clean and previous_version:
    previous_ids = set(load_scan_ids(previous_version))
    current_ids = set(load_scan_ids(output_dir))
    new_ids = current_ids - previous_ids
    removed_ids = previous_ids - current_ids
    logger.info(f"New scans: {len(new_ids)}, Removed: {len(removed_ids)}")
```

---

**Phase 80: Handle large datasets with memory-efficient streaming**

For datasets with >5000 scans, don't load all metadata into memory at once:
```python
def iterate_scan_dirs(dataset_dir):
    for scan_dir in sorted(dataset_dir.glob("scan_*")):
        meta_path = scan_dir / "metadata.json"
        if meta_path.exists():
            yield json.loads(meta_path.read_text())
```

---

**Phase 81: Build dataset version 1**

```bash
# First full build
python scripts/build_training_dataset.py --version 1 --output-dir data/training_dataset --plot

# Sample output:
# [INFO] Fetched 847 scans with SMPL params
# [INFO] Quality filtering: 847 -> 803 scans
# [INFO] Processed 803 scans (803/803)
# [INFO] Dataset v1 saved to data/training_dataset/v1
# [INFO] Splits: 723 train, 40 val, 40 test
# [INFO] Memory: current=245.3MB, peak=892.1MB
```

---

**Phase 82: Build dataset version 2 incrementally**

```bash
# Incremental build after more scans collected
python scripts/build_training_dataset.py --version 2 --incremental auto --plot

# Sample output:
# [INFO] Incremental mode: processing scans since 2026-07-01T03:00:00
# [INFO] Fetched 156 new scans with SMPL params
# [INFO] Dataset v2 saved to data/training_dataset/v2
# [INFO] Total scans: 959
```

---

## Phase 2: Supabase Storage & Schema Finalization (Phases 83–95)

*Reliable access to Supabase Storage is the backbone of the dataset pipeline.*

---

**Phase 83: Create dedicated training_data bucket**

```bash
# Via Supabase CLI
supabase storage create training_data --public=false

# Or via SQL:
-- Not possible via SQL, must use API or dashboard
```

---

**Phase 84: Set CORS policy for training_data bucket**

```python
# Using Supabase management API
supabase.storage.from_('training_data').update_bucket({
    'allowed_mime_types': ['application/json', 'text/csv', 'image/png'],
    'file_size_limit': 52428800,  # 50 MB
    'public': False,
})
```

---

**Phase 85: Add lifecycle policy (cleanup old datasets)**

Application-side: `build_training_dataset.py` checks `created_at` and auto-cleans:
```python
# In build_training_dataset.py
import shutil
import time

# Clean datasets older than 90 days
base = Path("data/training_dataset")
for d in base.iterdir():
    if not d.is_dir():
        continue
    age_days = (time.time() - d.stat().st_mtime) / 86400
    if age_days > 90:
        shutil.rmtree(d)
        logger.info(f"Cleaned old dataset: {d}")
```

---

**Phase 86: Add RLS policy for training_data bucket**

```sql
CREATE POLICY "training_data_service_only"
ON storage.objects
FOR ALL
USING (
    bucket_id = 'training_data' 
    AND auth.role() = 'service_role'
);
```

---

**Phase 87: Verify existing RLS for scan_photos bucket**

```sql
SELECT * FROM pg_policies 
WHERE tablename = 'objects' 
AND policyname LIKE '%scan_photos%';
```

---

**Phase 88: Verify existing RLS for meshes bucket**

```sql
SELECT * FROM pg_policies 
WHERE tablename = 'objects' 
AND policyname LIKE '%meshes%';
```

---

**Phase 89: Create storage access verification script**

As designed in Phase 0 (Phase 89), this script tests access to all three buckets.

---

**Phase 90: Download speed benchmark**

```python
import time
import httpx

urls = [
    os.environ.get("TEST_FRONT_URL"),
    os.environ.get("TEST_SIDE_URL"),
    os.environ.get("TEST_MESH_URL"),
]

for url in urls:
    if not url:
        continue
    start = time.time()
    resp = httpx.get(url, timeout=10)
    elapsed = time.time() - start
    size_kb = len(resp.content) / 1024
    speed = size_kb / elapsed
    logger.info(f"Download speed: {size_kb:.0f} KB in {elapsed:.2f}s ({speed:.0f} KB/s)")
```

---

**Phase 91: Add storage_uploaded_at column**

See Phase 32 (migration).

---

**Phase 92: Add dataset_version column**

See Phase 32 (migration).

---

**Phase 93: Create training_runs table**

See Phase 32 (migration).

---

**Phase 94: Create training_run_scans junction table**

See Phase 32 (migration).

---

**Phase 95: Verify all schema changes**

Using the verification script from Phase 35.

---

## Phase 3: Shape Prior Learning (Phases 96–120)

*Now we train actual models on the collected dataset. The shape prior is a statistical model of the 10-dimensional SMPL shape space. It learns what human body shapes look like from thousands of real scans and can detect/reject implausible HMR predictions.*

---

### Phase 3.1 — Gaussian Mixture Model (Phases 96–106)

---

**Phase 96: Create `scripts/train_shape_prior.py` — main entry**

Structure:
```python
#!/usr/bin/env python3
"""Train shape prior GMM from dataset."""
# ... (full implementation in Phase 96 section below)
```

CLI arguments: `--dataset-dir`, `--output-dir`, `--max-scans`, `--max-components`, `--version`, `--cv`, `--plot`

---

**Phase 97: Load shape vectors from dataset**

```python
def load_shapes(dataset_dir, max_scans=None):
    shapes = []
    scan_ids = []
    genders = []
    scan_dirs = sorted(dataset_dir.glob("scan_*"))
    if max_scans:
        scan_dirs = scan_dirs[:max_scans]
    for sd in scan_dirs:
        meta_path = sd / "metadata.json"
        if not meta_path.exists():
            continue
        meta = json.loads(meta_path.read_text())
        smpl = meta.get('smpl_params')
        if smpl and smpl.get('shape') and len(smpl['shape']) == 10:
            shapes.append(smpl['shape'])
            scan_ids.append(meta['scan_id'])
            genders.append(meta.get('gender', 'unknown'))
    return np.array(shapes), scan_ids, genders
```

---

**Phase 98: Standardize shapes**

```python
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
shapes_std = scaler.fit_transform(shapes)
```

---

**Phase 99: Find optimal K via BIC sweep**

```python
from sklearn.mixture import GaussianMixture
best_bic = np.inf
best_k = None
for k in range(2, max_components + 1):
    gmm = GaussianMixture(n_components=k, covariance_type='full', random_state=42, n_init=10)
    gmm.fit(shapes_std)
    bic = gmm.bic(shapes_std)
    if bic < best_bic:
        best_bic = bic
        best_k = k
        best_gmm = gmm
```

---

**Phase 100: Evaluate on held-out set**

```python
from sklearn.model_selection import train_test_split
X_train, X_val = train_test_split(shapes_std, test_size=0.1, random_state=42)
# Fit on train
gmm.fit(X_train)
# Evaluate on val
ll_val = gmm.score_samples(X_val)
print(f"Val log-likelihood: mean={ll_val.mean():.2f}, std={ll_val.std():.2f}")
```

---

**Phase 101: Save trained model to api/models/priors/**

```python
import pickle
gmm_path = output_dir / "shape_prior_gmm.pkl"
with open(gmm_path, 'wb') as f:
    pickle.dump(best_gmm, f)

scaler_path = output_dir / "shape_scaler.pkl"
with open(scaler_path, 'wb') as f:
    pickle.dump(scaler, f)
```

---

**Phase 102: Save JSON version for inspection**

```python
gmm_params = {
    'n_components': best_gmm.n_components,
    'weights': best_gmm.weights_.tolist(),
    'means': best_gmm.means_.tolist(),
    'covariances': [c.tolist() for c in best_gmm.covariances_],
    'bic': best_bic,
}
with open(output_dir / "shape_prior_gmm.json", 'w') as f:
    json.dump(gmm_params, f, indent=2)
```

---

**Phase 103: Print cluster analysis**

```python
for i in range(best_gmm.n_components):
    cluster_size = (best_gmm.predict(shapes_std) == i).sum()
    center = best_gmm.means_[i]
    print(f"Cluster {i}: {cluster_size} scans ({cluster_size/len(shapes)*100:.1f}%)")
    print(f"  Center: {np.round(center, 3)}")
    # Interpret first shape dim (overall body size)
    if center[0] > 0.5:
        print(f"  → Larger/ taller frame")
    elif center[0] < -0.5:
        print(f"  → Smaller/ shorter frame")
```

---

**Phase 104: Compute and print shape parameter correlations**

```python
corr = np.corrcoef(shapes, rowvar=False)
print("Shape dim correlation matrix:")
for i in range(10):
    print(f"  Dim{i}: " + " ".join(f"{corr[i,j]:.2f}" for j in range(10)))
```

---

**Phase 105: Add matplotlib visualization (--plot flag)**

```python
if args.plot:
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    
    fig, axes = plt.subplots(2, 5, figsize=(15, 6))
    axes = axes.ravel()
    for i in range(10):
        axes[i].hist(shapes[:, i], bins=50, alpha=0.7)
        axes[i].set_title(f"Shape Dim {i}")
    plt.tight_layout()
    plt.savefig(str(output_dir / "shape_distributions.png"))
```

---

**Phase 106: Run Training**

```bash
cd /app && python scripts/train_shape_prior.py \
    --dataset-dir data/training_dataset/v1 \
    --output-dir api/models/priors \
    --version 1 \
    --plot
    
# Expected output:
# [INFO] Loaded 803 shape vectors
# [INFO] K=2: BIC=4852.1
# [INFO] K=4: BIC=4721.3
# [INFO] K=6: BIC=4698.7
# [INFO] K=8: BIC=4712.4
# [INFO] Optimal K=6 (BIC=4698.7)
# [INFO] Validation log-likelihood: mean=0.42, std=1.23
# [INFO] Model saved to api/models/priors/shape_prior_gmm.pkl
```

---

### Phase 3.2 — Variational Autoencoder (Phases 107–117)

*Once the dataset exceeds ~500 scans, a VAE can capture more nuanced shape variations than GMM.*

---

**Phase 107: Create `scripts/train_shape_vae.py`**

```python
#!/usr/bin/env python3
"""Train VAE-based shape prior for higher-fidelity modeling."""
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import json
import argparse
from pathlib import Path

class ShapeDataset(Dataset):
    def __init__(self, shapes):
        self.shapes = torch.FloatTensor(shapes)
    
    def __len__(self):
        return len(self.shapes)
    
    def __getitem__(self, idx):
        return self.shapes[idx]

class ShapeVAE(nn.Module):
    def __init__(self, input_dim=10, latent_dim=2, hidden_dim=64):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
        )
        self.mu_layer = nn.Linear(hidden_dim, latent_dim)
        self.logvar_layer = nn.Linear(hidden_dim, latent_dim)
        
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, input_dim),
        )
    
    def encode(self, x):
        h = self.encoder(x)
        return self.mu_layer(h), self.logvar_layer(h)
    
    def reparameterize(self, mu, logvar):
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std
    
    def decode(self, z):
        return self.decoder(z)
    
    def forward(self, x):
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        recon = self.decode(z)
        return recon, mu, logvar
```

---

**Phase 108: Define beta-VAE loss**

```python
def loss_function(recon_x, x, mu, logvar, beta=0.1):
    # Reconstruction loss (MSE in shape space)
    recon_loss = nn.MSELoss()(recon_x, x)
    # KL divergence
    kl_loss = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
    return recon_loss + beta * kl_loss, recon_loss, kl_loss
```

---

**Phase 109: Train VAE**

```python
def train_vae(model, train_loader, val_loader, epochs=200, lr=1e-3, beta=0.1):
    optimizer = optim.Adam(model.parameters(), lr=lr)
    history = {'train_loss': [], 'val_loss': [], 'train_recon': [], 'val_recon': []}
    
    for epoch in range(epochs):
        model.train()
        train_loss = 0
        train_recon = 0
        for batch in train_loader:
            optimizer.zero_grad()
            recon, mu, logvar = model(batch)
            loss, r_loss, _ = loss_function(recon, batch, mu, logvar, beta)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
            train_recon += r_loss.item()
        
        # Validation
        model.eval()
        val_loss = 0
        val_recon = 0
        with torch.no_grad():
            for batch in val_loader:
                recon, mu, logvar = model(batch)
                loss, r_loss, _ = loss_function(recon, batch, mu, logvar, beta)
                val_loss += loss.item()
                val_recon += r_loss.item()
        
        if epoch % 20 == 0:
            print(f"Epoch {epoch}: train={train_loss/len(train_loader):.4f}, "
                  f"val={val_loss/len(val_loader):.4f}, "
                  f"recon={val_recon/len(val_loader):.4f}")
    
    return model, history
```

---

**Phase 110: Evaluate VAE vs GMM on reconstruction error**

```python
gmm_recon_error = compute_gmm_recon_error(val_shapes, gmm, scaler)
vae_recon_error = compute_vae_recon_error(val_shapes, vae)

print(f"GMM reconstruction MAE: {gmm_recon_error:.4f}")
print(f"VAE reconstruction MAE: {vae_recon_error:.4f}")
print(f"VAE improvement: {(gmm_recon_error - vae_recon_error) / gmm_recon_error * 100:.1f}%")
```

---

**Phase 111: Save trained VAE as TorchScript for inference**

```python
# Convert to TorchScript for deployment
model.eval()
example = torch.randn(1, 10)
traced = torch.jit.trace(model, example)
traced.save(str(output_dir / "shape_prior_vae.pt"))
```

---

**Phase 112: Save VAE hyperparameters and stats**

```python
vae_info = {
    'latent_dim': 2,
    'hidden_dim': 64,
    'epochs': epochs,
    'beta': 0.1,
    'final_train_loss': history['train_loss'][-1],
    'final_val_loss': history['val_loss'][-1],
    'final_val_recon': history['val_recon'][-1],
    'gmm_comparison': {
        'gmm_recon_mae': gmm_recon_error,
        'vae_recon_mae': vae_recon_error,
    }
}
with open(output_dir / "shape_prior_vae_info.json", 'w') as f:
    json.dump(vae_info, f, indent=2)
```

---

**Phase 113: Add latent space visualization**

```python
if args.plot:
    # Encode all shapes to 2D latent space
    model.eval()
    with torch.no_grad():
        mu_all, _ = model.encode(torch.FloatTensor(shapes_std))
    
    plt.figure(figsize=(10, 8))
    scatter = plt.scatter(mu_all[:, 0], mu_all[:, 1], c=genders_numeric, 
                          alpha=0.5, cmap='viridis')
    plt.colorbar(scatter, label='Gender (0=M, 1=F)')
    plt.title("VAE Latent Space — Body Shape")
    plt.xlabel("Latent dim 1")
    plt.ylabel("Latent dim 2")
    plt.savefig(str(output_dir / "vae_latent_space.png"))
```

---

**Phase 114: Run VAE training**

```bash
python scripts/train_shape_vae.py \
    --dataset-dir data/training_dataset/v1 \
    --output-dir api/models/priors \
    --epochs 200 \
    --plot
    
# Expected output:
# Epoch 0: train=0.5231, val=0.5198, recon=0.4982
# Epoch 20: train=0.1245, val=0.1312, recon=0.1087
# Epoch 40: train=0.0891, val=0.0923, recon=0.0712
# ...
# Epoch 200: train=0.0542, val=0.0589, recon=0.0412
# VAE saved to api/models/priors/shape_prior_vae.pt
```

---

### Phase 3.3 — Inference Integration: Shape Prior Regularization (Phases 115–120)

*Now we deploy the trained model. During HMR inference, we compute the log-likelihood and apply shrinkage.*

---

**Phase 115: Load shape prior in HMRMasterEngine.__init__()**

In `extract_measurements.py`, add to `__init__()`:
```python
self.shape_prior = None
self.shape_scaler = None
self._load_shape_prior()
```

And add `_load_shape_prior` method:
```python
def _load_shape_prior(self):
    """Load GMM shape prior for inference regularization."""
    prior_dir = self.base_dir / "models" / "priors"
    gmm_path = prior_dir / "shape_prior_gmm.pkl"
    scaler_path = prior_dir / "shape_scaler.pkl"
    
    if gmm_path.exists() and scaler_path.exists():
        try:
            import pickle
            with open(gmm_path, 'rb') as f:
                self.shape_prior = pickle.load(f)
            with open(scaler_path, 'rb') as f:
                self.shape_scaler = pickle.load(f)
            logger.info(f"Shape prior loaded: {self.shape_prior.n_components} components")
        except Exception as e:
            logger.warning(f"Could not load shape prior: {e}")
```

---

**Phase 116: Compute log-likelihood of HMR-predicted shape**

After extracting `shape_params` (from Phase 0), add:
```python
# Shape prior evaluation
shape_prior_ll = None
shape_anomaly = False
if self.shape_prior is not None and self.shape_scaler is not None:
    try:
        shape_2d = np.array(shape_params).reshape(1, -1)
        shape_std = self.shape_scaler.transform(shape_2d)
        shape_prior_ll = self.shape_prior.score_samples(shape_std)[0]
        # Log-likelihood threshold (bottom 5% of training data)
        if shape_prior_ll < -6.0:
            shape_anomaly = True
            logger.warning(f"Shape anomaly detected: LL={shape_prior_ll:.2f}")
    except Exception as e:
        logger.warning(f"Shape prior evaluation failed: {e}")
```

---

**Phase 117: Apply shrinkage for anomalous shapes**

If the predicted shape is unlikely (<5% percentile), pull it toward the nearest cluster mean:
```python
if shape_anomaly and self.shape_prior is not None:
    # Find nearest cluster
    shape_2d = np.array(shape_params).reshape(1, -1)
    shape_std = self.shape_scaler.transform(shape_2d)
    cluster_probs = self.shape_prior.predict_proba(shape_std)[0]
    best_cluster = np.argmax(cluster_probs)
    
    # Get cluster mean (in standardized space)
    cluster_mean_std = self.shape_prior.means_[best_cluster]
    # Transform back to original space
    cluster_mean = self.shape_scaler.inverse_transform(cluster_mean_std.reshape(1, -1))[0]
    
    # Shrink: 70% cluster mean, 30% prediction
    shrinkage_strength = 0.3  # stronger for more anomalous shapes
    corrected_shape = cluster_mean * (1 - shrinkage_strength) + np.array(shape_params) * shrinkage_strength
    
    # Update smpl_params with corrected shape
    smpl_params['shape'] = corrected_shape.tolist()
    smpl_params['__original_shape'] = shape_params  # preserve original for debugging
    smpl_params['__shrinkage_applied'] = True
    
    logger.info(f"Shape shrinkage applied: cluster={best_cluster}, "
                f"LL={shape_prior_ll:.2f} -> corrected")
```

---

**Phase 118: Recompute T-pose mesh with corrected shape**

After shrinkage, recompute `v_shaped` with the corrected shape:
```python
if shape_anomaly and self._v_template is not None and self._shapedirs is not None:
    try:
        corrected = np.array(corrected_shape, dtype=np.float64).reshape(10)
        v_shaped = self._v_template + (self._shapedirs @ corrected).reshape(-1, 3)
        v_measure = v_shaped
        # Recompute measurements with corrected T-pose mesh
        measurements_3d = self._calculate_from_indices(v_measure, height_cm, gender)
        final_measurements = {
            key: measurements_3d.get(key, 0.0) for key in 
            (MALE_KEYS if gender == 'male' else FEMALE_KEYS)
        }
        logger.info("Measurements recomputed with shape-corrected mesh")
    except Exception as e:
        logger.warning(f"Shape-corrected measurement failed: {e}")
```

---

**Phase 119: Add shape_prior_ll and shape_anomaly to return values**

We need to extend the return dict (or use a new return approach) to include these. Since the function already returns 9 values, we could return 11. Or better: embed them in `smpl_params`:

```python
smpl_params['__prior_log_likelihood'] = shape_prior_ll
smpl_params['__anomaly'] = shape_anomaly
```

This way, no signature change is needed — the anomaly info is stored alongside the SMPL params in the database.

---

**Phase 120: Log shape prior statistics per session**

```python
# In extract(), after processing:
if self.shape_prior is not None:
    logger.info(f"Shape prior: LL={shape_prior_ll:.2f}, "
                f"anomaly={shape_anomaly}, "
                f"cluster_probs={np.round(cluster_probs, 3) if shape_anomaly else 'N/A'}")
```

---

## Phase 4: Measurement Consistency Model (Phases 121–140)

*Use the dataset's measurement distributions to detect and correct outlier predictions. This is distinct from calibration — it's about statistical consistency across the dataset.*

---

### Phase 4.1 — Conditional Distribution Computation (Phases 121–130)

---

**Phase 121: Create `scripts/compute_measurement_distributions.py`**

This script loads the dataset, stratifies measurements by gender × height bin × body shape, computes percentiles per group, and saves the distributions for inference-time loading.

---

**Phase 122: Stratify by gender**

```python
male_measurements = [m for m in measurements if m['gender'] == 'male']
female_measurements = [m for m in measurements if m['gender'] == 'female']
```

---

**Phase 123: Stratify by height bins (5 cm)**

```python
def height_bin(h):
    return f"{int(h // 5 * 5)}-{int(h // 5 * 5 + 5)}"
```

---

**Phase 124: Stratify by body shape**

```python
body_shapes = set(m.get('body_shape', 'Unknown') for m in measurements)
```

---

**Phase 125: Combined stratification**

Make composite keys: `"male/170-175/Athletic/Chest Round"`

---

**Phase 126: Compute full quantile profile**

```python
def compute_quantiles(values):
    arr = np.array(values)
    return {
        'n': len(values),
        'mean': float(np.mean(arr)),
        'std': float(np.std(arr)),
        'p5': float(np.percentile(arr, 5)),
        'p25': float(np.percentile(arr, 25)),
        'p50': float(np.percentile(arr, 50)),
        'p75': float(np.percentile(arr, 75)),
        'p95': float(np.percentile(arr, 95)),
    }
```

---

**Phase 127: Save as `measurement_distributions.json`**

```python
output = {'api/models/priors/measurement_distributions.json'}
with open(path, 'w') as f:
    json.dump(distributions, f, indent=2)
```

---

**Phase 128: Add minimum sample size check**

```python
if len(values) < 5:
    continue  # Skip groups with insufficient data
```

---

**Phase 129: Log distribution summary**

```python
for key, stats in sorted(distributions.items())[:20]:
    print(f"{key}: n={stats['n']}, mean={stats['mean']:.1f}, "
          f"P5={stats['p5']:.1f}, P95={stats['p95']:.1f}")
```

---

**Phase 130: Validate distributions against known ANSUR II data**

```python
# Quick sanity check: male chest should be ~85-115 cm for 170-175cm height bin
chest_key = "male/170-175/Athlete/Chest Round"
if chest_key in distributions:
    assert 80 < distributions[chest_key]['p50'] < 120
```

---

### Phase 4.2 — Outlier Detection at Inference (Phases 131–137)

---

**Phase 131: Load measurement distributions in extract_measurements.py**

```python
# At module level or in __init__
import json
dist_path = Path(__file__).parent / "models" / "priors" / "measurement_distributions.json"
if dist_path.exists():
    with open(dist_path) as f:
        self.measurement_distributions = json.load(f)
```

---

**Phase 132: Find subject's subgroup at inference time**

```python
gender = ...  # 'male' or 'female'
height = ...  # 175
height_bin = f"{int(height // 5 * 5)}-{int(height // 5 * 5 + 5)}"
body_shape = ...  # 'Athletic'

subgroup_prefix = f"{gender}/{height_bin}/{body_shape}"
```

---

**Phase 133: Compute z-scores for each measurement**

```python
outlier_flags = {}
measurement_confidence_scores = []

for key, value in final_measurements.items():
    if value <= 0:
        continue
    dist_key = f"{subgroup_prefix}/{key}"
    dist = self.measurement_distributions.get(dist_key)
    if dist and dist['std'] > 0:
        z_score = abs(value - dist['mean']) / dist['std']
        if z_score > 3.0:
            outlier_flags[key] = round(z_score, 2)
        # Confidence: how close to median
        # 1.0 if within 1 std, 0.0 if beyond 3 std
        confidence = max(0.0, 1.0 - (z_score - 1.0) / 2.0)
        measurement_confidence_scores.append(min(1.0, confidence))
```

---

**Phase 134: Apply statistical shrinkage**

```python
if outlier_flags and dist:
    shrinkage = 0.5  # 50% toward subgroup mean
    corrected_value = dist['mean'] + (value - dist['mean']) * shrinkage
    final_measurements[key] = round(corrected_value, 1)
    logger.info(f"Shrinkage applied: {key}: {value:.1f} -> {corrected_value:.1f}")
```

---

**Phase 135: Compute overall measurement confidence**

```python
overall_confidence = (sum(measurement_confidence_scores) / len(measurement_confidence_scores)
                      if measurement_confidence_scores else 0.5)
clinical_realism_index = round(overall_confidence * 100, 1)
```

---

**Phase 136: Replace hardcoded clinical_realism_index**

In `hmr_subprocess.py:86`, replace `clinical_realism_index = 97.0` with:
```python
clinical_realism_index = measurements.get('__clinical_realism_index', 97.0)
```

---

**Phase 137: Store outlier flags in smpl_params for analysis**

```python
smpl_params['__outlier_flags'] = outlier_flags
smpl_params['__clinical_realism_index'] = clinical_realism_index
```

---

### Phase 4.3 — Clinical Realism Index (Phases 138–140)

---

**Phase 138: Add measurement consistency checks**

Beyond statistical consistency, add anatomical consistency checks:
```python
# Waist should be less than chest
if final_measurements.get('Waist Round', 0) > final_measurements.get('Chest Round', 0):
    consistency_penalty -= 5.0

# Shoulder should be wider than hips for males
if gender == 'male' and final_measurements.get('Shoulder', 0) < final_measurements.get('Hip Round', 0):
    consistency_penalty -= 5.0

# Height sanity check
if user_height_cm < 100 or user_height_cm > 250:
    consistency_penalty -= 10.0
```

---

**Phase 139: Combine statistical + anatomical confidence**

```python
final_cri = overall_confidence * 100 + consistency_penalty
final_cri = max(50.0, min(100.0, round(final_cri, 1)))
```

---

**Phase 140: Validation of new CRI**

Compare old hardcoded CRI (97.0) vs new computed CRI on 100 random scans:
```python
old_cri = 97.0
new_cri_mean = np.mean([s['clinical_realism_index'] for s in sample_scans])
print(f"Old CRI: {old_cri}, New CRI (mean): {new_cri_mean:.1f}")
```

---

## Phase 5: Silhouette Consistency (Phases 141–165)

*The 2D→3D re-projection error is a powerful self-supervised signal. If the predicted 3D mesh is correct, its silhouette should match the input photo silhouette. This doesn't require any ground truth — it's a consistency check inherent to the data.*

---

### Phase 5.1 — Render Pipeline (Phases 141–150)

---

**Phase 141: Create `scripts/silhouette_renderer.py`**

Uses PyTorch3D or trimesh to render the posed mesh from the front and side viewpoints, comparing with extracted photo silhouettes.

---

**Phase 142: Load posed mesh from OBJ**

```python
import trimesh
mesh = trimesh.load(mesh_path)
```

---

**Phase 143: Estimate camera from SMPL camera params**

The SMPL camera params are `[scale, tx, ty]` where the projection is:
```python
# Weak-perspective camera
# pixel = scale * vertex_xy + [tx, ty]
# z-buffer = scale * vertex_z
```

---

**Phase 144: Render front silhouette**

```python
# Using pyrender or PyTorch3D
scene = pyrender.Scene()
scene.add(pyrender.Mesh.from_trimesh(mesh))
camera = pyrender.camera.IntrinsicsCamera(fx=focal, fy=focal, cx=image_w/2, cy=image_h/2)
scene.add(camera)
renderer = pyrender.OffscreenRenderer(image_w, image_h)
color, depth = renderer.render(scene)
silhouette = depth > 0  # binary mask
```

---

**Phase 145: Render side silhouette**

Rotate the mesh 90 degrees around Y axis and render.

---

**Phase 146: Extract photo silhouette (background subtraction)**

For photos with plain backgrounds:
```python
# Simple threshold method
gray = cv2.cvtColor(photo, cv2.COLOR_RGB2GRAY)
_, photo_silhouette = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
```

---

**Phase 147: Extract photo silhouette (alternative: using MediaPipe)**

```python
import mediapipe as mp
mp_selfie = mp.solutions.selfie_segmentation
with mp_selfie.SelfieSegmentation(model_selection=1) as seg:
    results = seg.process(photo)
    photo_silhouette = results.segmentation_mask > 0.5
```

---

**Phase 148: Compute front IoU**

```python
intersection = np.logical_and(rendered_sil, photo_sil)
union = np.logical_or(rendered_sil, photo_sil)
iou_front = intersection.sum() / (union.sum() + 1e-8)
```

---

**Phase 149: Compute side IoU**

Same as Phase 148 but for side silhouette.

---

**Phase 150: Average IoU = silhouette consistency score**

```python
silhouette_score = (iou_front + iou_side) / 2
```

---

### Phase 5.2 — Batch Evaluation (Phases 151–157)

---

**Phase 151: Create `scripts/compute_silhouette_consistency.py`**

Batch version that iterates over the entire dataset and computes IoU for every scan.

---

**Phase 152: Parallel processing for batch evaluation**

```python
from multiprocessing import Pool
def compute_iou_for_scan(scan_dir):
    # ... load mesh, photos, render, compare ...
    return iou_front, iou_side

with Pool(4) as pool:
    results = pool.map(compute_iou_for_scan, scan_dirs)
```

---

**Phase 153: Save IoU scores to metadata**

```python
for scan_dir, (iou_f, iou_s) in zip(scan_dirs, results):
    meta_path = scan_dir / "metadata.json"
    meta = json.loads(meta_path.read_text())
    meta['silhouette_consistency'] = {'front': iou_f, 'side': iou_s, 'mean': (iou_f + iou_s) / 2}
    meta_path.write_text(json.dumps(meta, indent=2))
```

---

**Phase 154: Report dataset-level statistics**

```python
ious = [r[0] for r in results if r[0] is not None]
print(f"Front IoU: mean={np.mean(ious):.4f}, std={np.std(ious):.4f}, "
      f"min={np.min(ious):.4f}, max={np.max(ious):.4f}")
```

---

**Phase 155: Identify low-IoU scans for manual inspection**

```python
low_iou_scans = [(d, i) for d, i in zip(scan_dirs, results) if i[0] < 0.5]
print(f"{len(low_iou_scans)} scans with IoU < 0.5 — potential quality issues")
for scan_dir, (iou_f, _) in low_iou_scans[:10]:
    print(f"  {scan_dir.name}: IoU={iou_f:.4f}")
```

---

**Phase 156: Correlate IoU with measurement z-scores**

```python
# For scans with both IoU and shape prior LL, compute correlation
from scipy.stats import pearsonr
# ... load data ...
corr, p = pearsonr(iou_scores, z_scores)
print(f"IoU vs Z-score correlation: r={corr:.3f}, p={p:.4f}")
```

---

**Phase 157: Add IoU as a quality filter in dataset builder**

```python
# In build_training_dataset.py, add --min-iou flag
if args.min_iou > 0:
    before = len(scans)
    scans = [s for s in scans if (s.get('silhouette_consistency') or {}).get('mean', 1.0) >= args.min_iou]
```

---

### Phase 5.3 — Silhouette-Based Shape Optimization (Phases 158–165)

*Instead of just evaluating consistency, we can optimize the shape params to improve it. This creates a refinement loop.*

---

**Phase 158: Create `scripts/optimize_shape_from_silhouette.py`**

```python
# Differentiable rendering approach
# Loss = IoU(rendered_mesh, photo_silhouette) + lambda * shape_prior_nll
# Optimize 10 shape params via gradient descent
```

---

**Phase 159: Define silhouette loss**

```python
def silhouette_loss(rendered, target):
    # Binary cross-entropy per pixel
    rendered = rendered.clamp(1e-7, 1 - 1e-7)
    return - (target * torch.log(rendered) + (1 - target) * torch.log(1 - rendered)).mean()
```

---

**Phase 160: Define shape prior loss**

```python
def prior_loss(shapes, gmm, scaler):
    shapes_std = scaler.transform(shapes)
    return -gmm.score_samples(shapes_std).mean()
```

---

**Phase 161: Combined loss with lambda**

```python
total_loss = silhouette_loss(rendered, target) + 0.1 * prior_loss(shapes)
```

---

**Phase 162: Optimize shape params via L-BFGS**

```python
optimizer = optim.LBFGS([shapes], lr=0.1, max_iter=100)
for i in range(50):
    def closure():
        optimizer.zero_grad()
        # ... render mesh with current shapes ...
        loss = compute_total_loss(rendered, target, shapes)
        loss.backward()
        return loss
    optimizer.step(closure)
```

---

**Phase 163: Extract measurements from refined mesh**

```python
refined_mesh = compute_tpose(shapes_optimized)
refined_measurements = engine._calculate_from_indices(refined_mesh, height_cm, gender)
```

---

**Phase 164: Compare pre/post optimization**

```python
for key in refined_measurements:
    delta = refined_measurements[key] - original_measurements.get(key, 0)
    print(f"{key}: {original_measurements.get(key, 0):.1f} -> {refined_measurements[key]:.1f} ({delta:+.1f})")
```

---

**Phase 165: Run optimization on sample**

```bash
python scripts/optimize_shape_from_silhouette.py \
    --scan data/training_dataset/v1/scan_abc123 \
    --output refined_measurements.json
    
# Expected output:
# Optimization steps: 50/50
# Initial IoU: 0.82 -> Final IoU: 0.91
# Chest: 102.3 -> 100.1 (-2.2)
# Waist: 88.5 -> 86.3 (-2.2)
```

---

## Phase 6: Per-Subgroup Calibration (Phases 166–189)

*The current calibration uses the same [alpha, beta] factors for every scan. But different body types have different systematic biases. This phase learns cluster-specific calibration factors.*

---

### Phase 6.1 — Body Type Clustering (Phases 166–174)

---

**Phase 166: Create `scripts/compute_body_clusters.py`**

```python
#!/usr/bin/env python3
"""Cluster SMPL shape space into body types for per-group calibration."""
import json
import argparse
import numpy as np
from pathlib import Path
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
```

---

**Phase 167: Load shape vectors**

```python
shapes = []
for sd in sorted(dataset_dir.glob("scan_*")):
    meta = json.loads((sd / "metadata.json").read_text())
    smpl = meta.get('smpl_params')
    if smpl and smpl.get('shape'):
        shapes.append(smpl['shape'])
shapes = np.array(shapes)
```

---

**Phase 168: Standardize**

```python
scaler = StandardScaler()
shapes_std = scaler.fit_transform(shapes)
```

---

**Phase 169: Find optimal K via silhouette score**

```python
best_k = 3
best_score = -1
for k in range(3, 13):
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(shapes_std)
    if len(set(labels)) < 2:
        continue
    score = silhouette_score(shapes_std, labels)
    if score > best_score:
        best_score = score
        best_k = k
        best_km = km
print(f"Optimal K={best_k} (silhouette={best_score:.3f})")
```

---

**Phase 170: Assign cluster labels to scans**

```python
labels = best_km.predict(shapes_std)
for sd, label in zip(scan_dirs, labels):
    meta = json.loads((sd / "metadata.json").read_text())
    meta['body_cluster'] = int(label)
    (sd / "metadata.json").write_text(json.dumps(meta, indent=2))
```

---

**Phase 171: Interpret clusters anthropometrically**

```python
for i in range(best_k):
    mask = labels == i
    cluster_shapes = shapes[mask]
    mean_shape = cluster_shapes.mean(axis=0)
    print(f"Cluster {i}: {mask.sum()} scans")
    print(f"  Mean shape: {np.round(mean_shape, 3)}")
    # Interpret based on shape dim 0 (overall size) and dim 1 (muscularity)
    if mean_shape[0] > 0.5:
        print(f"  → Larger frame")
    elif mean_shape[0] < -0.5:
        print(f"  → Smaller frame")
```

---

**Phase 172: Save cluster model**

```python
import pickle
with open(output_dir / "body_clusters.pkl", 'wb') as f:
    pickle.dump({'kmeans': best_km, 'scaler': scaler, 'k': best_k}, f)
```

---

**Phase 173: Save cluster centroids as JSON**

```python
centroids = {
    f"cluster_{i}": {
        'centroid': best_km.cluster_centers_[i].tolist(),
        'n_scans': int((labels == i).sum()),
    }
    for i in range(best_k)
}
with open(output_dir / "body_cluster_centroids.json", 'w') as f:
    json.dump(centroids, f, indent=2)
```

---

**Phase 174: Run clustering**

```bash
python scripts/compute_body_clusters.py \
    --dataset-dir data/training_dataset/v1 \
    --output-dir api/models/priors
    
# Expected output:
# Optimal K=6 (silhouette=0.42)
# Cluster 0: 203 scans → proportional
# Cluster 1: 156 scans → tall+lean
# Cluster 2: 98 scans → short+heavy
# Cluster 3: 142 scans → athletic
# Cluster 4: 112 scans → pear-shaped
# Cluster 5: 92 scans → apple-shaped
```

---

### Phase 6.2 — Per-Cluster Calibration Factors (Phases 175–184)

---

**Phase 175: Create `scripts/compute_cluster_calibration.py`**

```python
#!/usr/bin/env python3
"""Compute per-cluster calibration factors via ridge regression."""
```

---

**Phase 176: For each cluster, load raw and final measurements**

```python
# From metadata: measurements = raw_hmr (stored as __raw_measurements), 
# and the calibrated measurements
for cluster_id in range(n_clusters):
    cluster_scan_ids = scan_ids_by_cluster[cluster_id]
    raw = []
    final = []
    for sid in cluster_scan_ids:
        meta = ... 
        raw.append(meta['smpl_params']['raw_measurements']['Chest Round'])
        final.append(meta['measurements']['Chest Round'])
```

---

**Phase 177: Run ridge regression per measurement per cluster**

```python
from sklearn.linear_model import Ridge

factors = {}
for cluster_id in range(n_clusters):
    cluster_factors = {}
    for measurement in measurement_names:
        X = raw_values[measurement]  # (n_scans, 1)
        y = final_values[measurement]
        if len(X) < 10:
            cluster_factors[measurement] = [1.0, 0.0]  # fallback to identity
            continue
        reg = Ridge(alpha=1.0)
        reg.fit(X, y)  # y = alpha * x + beta
        cluster_factors[measurement] = [reg.coef_[0], reg.intercept_]
    factors[f"cluster_{cluster_id}"] = cluster_factors
```

---

**Phase 178: Save per-cluster factors**

```python
with open(output_dir / "calibration_factors_per_cluster.json", 'w') as f:
    json.dump(factors, f, indent=2)
```

---

**Phase 179: Evaluate vs global calibration**

```python
# For each measurement across all clusters, compare MAE
global_factors = ...  # current factors
global_mae = compute_mae(global_factors, val_data)
cluster_mae = compute_mae(cluster_factors, val_data)
print(f"Global MAE: {global_mae:.2f} -> Cluster MAE: {cluster_mae:.2f} "
      f"(improvement: {(global_mae - cluster_mae) / global_mae * 100:.1f}%)")
```

---

**Phase 180: Log per-cluster MAE breakdown**

```python
for cluster_id in range(n_clusters):
    print(f"Cluster {cluster_id} ({n_scans_per_cluster[cluster_id]} scans):")
    for meas in measurement_names:
        print(f"  {meas}: {cluster_mae_by_cluster[cluster_id][meas]:.1f} vs "
              f"{global_mae_by_cluster[cluster_id][meas]:.1f}")
```

---

**Phase 181: Handle clusters with too few scans**

```python
min_scans = 30  # minimum for reliable calibration
if n_scans < min_scans:
    factors[f"cluster_{cluster_id}"] = global_factors
    print(f"Cluster {cluster_id}: only {n_scans} scans, using global factors")
```

---

**Phase 182: Add smoothing between adjacent clusters**

To avoid sharp transitions when a scan is near cluster boundaries:
```python
# Soft assignment: weight factors by cluster probability
probs = kmeans.predict_proba(shape_std)[0]
weighted_alpha = sum(probs[i] * cluster_factors[i][meas][0] for i in range(n_clusters))
weighted_beta = sum(probs[i] * cluster_factors[i][meas][1] for i in range(n_clusters))
```

---

**Phase 183: Run per-cluster calibration training**

```bash
python scripts/compute_cluster_calibration.py \
    --dataset-dir data/training_dataset/v1 \
    --factors-path api/services/calibration_factors.json \
    --output-dir api/models/priors
    
# Expected output:
# Global MAE: 7.2 cm
# Cluster MAE: 5.1 cm (improvement: 29.2%)
# Cluster 0: 203 scans, MAE 4.8 cm
# Cluster 1: 156 scans, MAE 5.2 cm
# ...
```

---

**Phase 184: Add cross-validation to avoid overfitting**

```python
from sklearn.model_selection import KFold
kf = KFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = []
for train_idx, val_idx in kf.split(X):
    X_train, X_val = X[train_idx], X[val_idx]
    y_train, y_val = y[train_idx], y[val_idx]
    reg = Ridge(alpha=1.0).fit(X_train, y_train)
    score = reg.score(X_val, y_val)
    cv_scores.append(score)
print(f"CV R^2: {np.mean(cv_scores):.3f} +/- {np.std(cv_scores):.3f}")
```

---

### Phase 6.3 — Inference Integration (Phases 185–189)

---

**Phase 185: Load cluster model in measurement_calibration.py**

```python
# In Calibrator.__init__():
import pickle
cluster_path = self.factors_path.parent / "priors" / "body_clusters.pkl"
if cluster_path.exists():
    with open(cluster_path, 'rb') as f:
        self.cluster_model = pickle.load(f)
else:
    self.cluster_model = None
```

---

**Phase 186: Accept shape_params in calibrate() method**

```python
def calibrate(self, measurements: Dict, gender: str, shape_params: List = None):
    """Apply per-cluster calibration if shape params available."""
    if shape_params and self.cluster_model:
        shape_std = self.cluster_model['scaler'].transform([shape_params])
        cluster_id = self.cluster_model['kmeans'].predict(shape_std)[0]
        # Use cluster-specific factors
        factors = self.per_cluster_factors.get(f"cluster_{cluster_id}")
        if factors:
            for key, value in measurements.items():
                if key in factors and factors[key][0] != 1.0:
                    alpha, beta = factors[key]
                    measurements[key] = round(alpha * value + beta, 1)
            measurements['__calibration_cluster'] = cluster_id
```

---

**Phase 187: Fall back to global factors if no cluster**

```python
if not shape_params or not self.cluster_model:
    # Use global factors (existing behavior)
    self._apply_global_factors(measurements, gender)
```

---

**Phase 188: Pass shape_params from extract() to calibration**

In `hmr_subprocess.py`, the calibration call at line 145–149:
```python
try:
    from api.services.measurement_calibration import calibrator
    calibrator.calibrate(measurements, gender, shape_params=smpl_params.get('shape'))
except Exception as e:
    logger.warning(f"Measurement calibration skipped: {e}")
```

---

**Phase 189: Log cluster assignment**

```python
cluster_id = measurements.get('__calibration_cluster')
if cluster_id is not None:
    logger.info(f"Calibration cluster: {cluster_id}")
```

---

## Phase 7: Continuous Training Pipeline (Phases 190–217)

*Orchestrate all training components into an automated weekly pipeline.*

---

### Phase 7.1 — Pipeline Orchestrator (Phases 190–199)

---

**Phase 190: Create `scripts/train_pipeline.py`**

Master orchestrator that runs all training steps in sequence:

```python
#!/usr/bin/env python3
"""Master orchestrator for all training components."""
import subprocess
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TRAIN_PIPELINE")

def run_step(step_name, cmd):
    logger.info(f"Step: {step_name}")
    logger.info(f"  Command: {' '.join(cmd)}")
    start = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - start
    logger.info(f"  Exit code: {result.returncode}, Duration: {elapsed:.1f}s")
    if result.stdout:
        for line in result.stdout.strip().split('\n')[-5:]:
            logger.info(f"  {line}")
    if result.returncode != 0:
        logger.error(f"  STDERR: {result.stderr[-500:]}")
        raise RuntimeError(f"Step {step_name} failed")
    return result
```

---

**Phase 191: Step 1 — Build dataset**

```python
latest_version = get_latest_dataset_version()
new_version = latest_version + 1

run_step("build_dataset", [
    "python", "scripts/build_training_dataset.py",
    "--version", str(new_version),
    "--auto-increment",
    "--min-quality", "70",
    "--require-tpose",
])
```

---

**Phase 192: Step 2 — Train shape prior**

```python
run_step("train_shape_prior", [
    "python", "scripts/train_shape_prior.py",
    "--dataset-dir", f"data/training_dataset/v{new_version}",
    "--output-dir", "api/models/priors",
    "--version", str(new_version),
])
```

---

**Phase 193: Step 3 — Compute body clusters**

```python
run_step("compute_body_clusters", [
    "python", "scripts/compute_body_clusters.py",
    "--dataset-dir", f"data/training_dataset/v{new_version}",
    "--output-dir", "api/models/priors",
])
```

---

**Phase 194: Step 4 — Compute per-cluster calibration**

```python
run_step("compute_calibration", [
    "python", "scripts/compute_cluster_calibration.py",
    "--dataset-dir", f"data/training_dataset/v{new_version}",
    "--output-dir", "api/models/priors",
])
```

---

**Phase 195: Step 5 — Compute measurement distributions**

```python
run_step("compute_distributions", [
    "python", "scripts/compute_measurement_distributions.py",
    "--dataset-dir", f"data/training_dataset/v{new_version}",
    "--output-dir", "api/models/priors",
])
```

---

**Phase 196: Step 6 — Compute silhouette consistency scores**

```python
run_step("silhouette_consistency", [
    "python", "scripts/compute_silhouette_consistency.py",
    "--dataset-dir", f"data/training_dataset/v{new_version}",
])
```

---

**Phase 197: Step 7 — Evaluate on hold-out set**

```python
run_step("evaluate", [
    "python", "scripts/evaluate_accuracy.py",
    "--dataset-dir", f"data/training_dataset/v{new_version}",
    "--split", "test",
])
```

---

**Phase 198: Step 8 — Deploy if MAE improved**

```python
previous_mae = get_previous_mae()
current_mae = parse_mae_from_evaluation()
improvement = previous_mae - current_mae

if improvement > 0.1:  # at least 0.1 cm improvement
    run_step("deploy", ["bash", "scripts/deploy_models.sh"])
    logger.info(f"Deployed! MAE: {previous_mae:.1f} -> {current_mae:.1f} cm")
else:
    logger.info(f"Skipping deploy (improvement {improvement:.2f} cm below threshold)")
```

---

**Phase 199: Step 9 — Log training run to database**

```python
log_training_run({
    'version': new_version,
    'scan_count': total_scans,
    'mae': current_mae,
    'gmm_bic': gmm_bic,
    'n_clusters': n_clusters,
    'duration_hours': (time.time() - pipeline_start) / 3600,
})
```

---

### Phase 7.2 — Deployment Scripts (Phases 200–208)

---

**Phase 200: Create `scripts/deploy_models.sh`**

```bash
#!/bin/bash
# Deploy trained models to EC2 production
set -e

MODELS_DIR="/app/api/models/priors"
CALIB_DIR="/app/api/services"

# Copy shape prior
cp api/models/priors/shape_prior_gmm.pkl $MODELS_DIR/
cp api/models/priors/shape_scaler.pkl $MODELS_DIR/

# Copy measurement distributions
cp api/models/priors/measurement_distributions.json $MODELS_DIR/

# Copy calibration factors
cp api/models/priors/calibration_factors_per_cluster.json $CALIB_DIR/

# Copy body cluster model
cp api/models/priors/body_clusters.pkl $MODELS_DIR/

# Verify
echo "Verifying deployed files..."
ls -la $MODELS_DIR/
ls -la $CALIB_DIR/calibration_factors_per_cluster.json

# Hot reload: touch the FastAPI app to trigger reload (if uvicorn with --reload)
# Or send SIGHUP to the uvicorn process
kill -HUP $(pgrep -f uvicorn) 2>/dev/null || true

echo "Deploy complete"
```

---

**Phase 201: Create `scripts/rollback_models.sh`**

```bash
#!/bin/bash
# Rollback models to previous version
set -e

BACKUP_DIR="/app/models/backups"
VERSION=${1:-"latest"}

if [ "$VERSION" = "latest" ]; then
    # Find the most recent backup
    VERSION=$(ls -t $BACKUP_DIR | head -1)
fi

echo "Rolling back to version $VERSION..."
cp $BACKUP_DIR/$VERSION/* /app/api/models/priors/
echo "Rollback complete"
```

---

**Phase 202: Add model versioning**

```bash
# Before deploy, backup current models
BACKUP_DIR="/app/models/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR
cp /app/api/models/priors/* $BACKUP_DIR/
```

---

**Phase 203: Add health check after deploy**

```python
# Verify models load correctly
try:
    import pickle
    with open('/app/api/models/priors/shape_prior_gmm.pkl', 'rb') as f:
        gmm = pickle.load(f)
    assert gmm.n_components > 0
    print("Health check: GMM loaded OK")
except Exception as e:
    print(f"Health check FAILED: {e}")
    exit(1)
```

---

**Phase 204: Add rollback on health check failure**

```bash
if python scripts/health_check.py; then
    echo "Deploy successful"
else
    echo "Health check failed, rolling back"
    bash scripts/rollback_models.sh
    exit 1
fi
```

---

**Phase 205: Add Slack notification**

```python
import httpx
def notify_slack(message):
    webhook = os.environ.get("SLACK_WEBHOOK_URL")
    if webhook:
        httpx.post(webhook, json={"text": message})
```

---

**Phase 206: Add email notification for failures**

```python
def notify_failure(step, error):
    # Use the existing email_service
    email_service.send_alert_email(
        subject=f"Training Pipeline Failed: {step}",
        body=str(error)
    )
```

---

**Phase 207: Add pipeline lock file**

```python
LOCK_FILE = "/tmp/train_pipeline.lock"
if os.path.exists(LOCK_FILE):
    logger.warning("Pipeline already running, skipping")
    sys.exit(0)
open(LOCK_FILE, 'w').write(str(os.getpid()))
```

---

**Phase 208: Add cleanup on exit**

```python
import atexit
atexit.register(lambda: os.remove(LOCK_FILE) if os.path.exists(LOCK_FILE) else None)
```

---

### Phase 7.3 — Scheduling (Phases 209–212)

---

**Phase 209: Add to crontab**

```bash
# Run training pipeline every Sunday at 3 AM
0 3 * * 0 cd /app && python scripts/train_pipeline.py >> logs/pipeline.log 2>&1
```

---

**Phase 210: Add event-driven trigger**

```python
# In measurements.py, after each scan:
# Check if we have 100+ new scans since last training
if new_scan_count_since_last_training >= 100:
    # Trigger training pipeline as background task
    background_tasks.add_task(run_training_pipeline)
```

---

**Phase 211: Add timeout protection**

```python
import signal
class TimeoutError(Exception): pass

def handler(signum, frame):
    raise TimeoutError("Pipeline timed out")

signal.signal(signal.SIGALRM, handler)
signal.alarm(6 * 3600)  # 6 hour timeout
```

---

**Phase 212: Add --dry-run for preview**

```bash
python scripts/train_pipeline.py --dry-run
# Output:
# Would run: build_training_dataset.py --version 4
# Would run: train_shape_prior.py --dataset-dir data/training_dataset/v4
# Would run: compute_body_clusters.py --dataset-dir data/training_dataset/v4
# ...
# Estimated duration: 2.5 hours
# New scans: 156
```

---

### Phase 7.4 — Logging & Audit (Phases 213–217)

---

**Phase 213: Log training run to `training_runs` PostgreSQL table**

```python
supabase.table("training_runs").insert({
    "version": new_version,
    "dataset_version": new_version,
    "scan_count": total_scans,
    "male_count": n_male,
    "female_count": n_female,
    "height_min": height_min,
    "height_max": height_max,
    "gmm_bic": gmm_bic,
    "created_at": datetime.utcnow().isoformat(),
    "status": "completed",
}).execute()
```

---

**Phase 214: Create training run summary JSON**

```json
{
    "version": 3,
    "date": "2026-07-14T03:00:00Z",
    "total_scans": 1247,
    "train_val_test": "1122_62_63",
    "gmm_components": 6,
    "calibration_clusters": 6,
    "mae_test": 5.1,
    "mae_previous": 5.4,
    "improvement": "5.6%",
    "duration_hours": 2.5,
    "deployed": true
}
```

---

**Phase 215: Track calibration MAE over time**

```python
# Append to a CSV for historical tracking
with open("logs/calibration_mae_history.csv", 'a') as f:
    f.write(f"{datetime.utcnow().isoformat()},{version},{mae_test},{n_scans}\n")
```

---

**Phase 216: Add drift detection between training runs**

```python
def check_data_drift(prev_stats, curr_stats):
    """Check for significant distribution changes."""
    # Compare shape param means
    prev_mean = np.array(prev_stats['shape_mean'])
    curr_mean = np.array(curr_stats['shape_mean'])
    shape_shift = np.linalg.norm(curr_mean - prev_mean)
    if shape_shift > 0.5:
        print(f"WARNING: Shape distribution shift: {shape_shift:.3f}")
```

---

**Phase 217: Visualize training progress**

```python
# Generate a plot showing MAE over versions
import matplotlib.pyplot as plt
versions = [1, 2, 3, 4]
maes = [7.2, 6.1, 5.4, 5.1]
plt.plot(versions, maes, marker='o')
plt.title("Calibration MAE over Dataset Versions")
plt.xlabel("Dataset Version")
plt.ylabel("MAE (cm)")
plt.savefig("logs/mae_progress.png")
```

---

## Phase 8: Monitoring & Evaluation (Phases 218–235)

*We must track whether the system is actually improving. Without robust evaluation, we're flying blind.*

---

### Phase 8.1 — Data Quality Monitoring (Phases 218–225)

---

**Phase 218: Create `scripts/monitor_data_quality.py`**

```python
#!/usr/bin/env python3
"""Monitor data quality metrics for production scans."""
```

---

**Phase 219: Track SMPL capture rate**

```sql
SELECT 
    COUNT(*) AS total,
    COUNT(smpl_params) AS with_smpl,
    COUNT(*) - COUNT(smpl_params) AS missing_smpl,
    ROUND(100.0 * COUNT(smpl_params) / COUNT(*), 1) AS capture_rate
FROM measurements
WHERE created_at > NOW() - INTERVAL '7 days';
```

---

**Phase 220: Track measurement consistency over time**

```sql
SELECT 
    DATE(created_at) AS day,
    AVG(clinical_realism_index) AS avg_cri,
    COUNT(*) AS n_scans
FROM measurements
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY day
ORDER BY day;
```

---

**Phase 221: Create accuracy evaluation script**

```python
# scripts/evaluate_accuracy.py
# Runs HMR on test split, compares with stored "final" measurements
# Computes MAE per measurement, per gender, per body shape
```

---

**Phase 222: Create accuracy dashboard endpoint**

```python
@router.get("/v2/accuracy/status")
async def accuracy_status():
    """Return latest accuracy metrics."""
    # Query from training_runs table
    latest = supabase.table("training_runs").select("*").order("version", desc=True).limit(1).execute()
    return latest.data[0] if latest.data else {"error": "No training runs yet"}
```

---

**Phase 223: Add accuracy card to admin UI**

In `dashboard.html`, add a card showing:
- Current MAE
- Number of scans in latest dataset
- Calibration version
- Trend arrow (up/down)

---

**Phase 224: Add per-measurement accuracy breakdown**

```python
# In accuracy endpoint
per_measurement = {
    "Chest Round": {"mae": 3.2, "n": 847, "trend": "improving"},
    "Waist Round": {"mae": 4.1, "n": 847, "trend": "stable"},
    "Hip Round": {"mae": 3.8, "n": 847, "trend": "improving"},
    ...
}
```

---

**Phase 225: Create weekly accuracy report**

```python
# scripts/generate_weekly_report.py
# Generate PDF/HTML report with:
# - Week-over-week MAE change
# - Scan volume
# - Model version deployed
# - Calibration cluster distribution
# - Silhouette consistency scores
```

---

### Phase 8.2 — Drift Monitoring (Phases 226–231)

---

**Phase 226: Create drift monitoring script**

```python
# scripts/monitor_drift.py
# Compare latest model vs previous on test set
# Alert if MAE increases > 1.0 cm
```

---

**Phase 227: Monitor shape parameter drift**

```python
# Detect if incoming scans have different shape distribution
# Compare running weekly mean to overall dataset mean
if abs(weekly_mean[0] - dataset_mean[0]) > 0.3:
    alert("Shape param 0 drift detected")
```

---

**Phase 228: Monitor measurement distribution drift**

```python
# For each measurement, check if weekly P50 differs by > 5%
for meas in measurements:
    weekly_p50 = get_weekly_percentile(meas, 50)
    overall_p50 = get_overall_percentile(meas, 50)
    pct_diff = abs(weekly_p50 - overall_p50) / overall_p50 * 100
    if pct_diff > 5:
        alert(f"{meas}: P50 drift {pct_diff:.1f}%")
```

---

**Phase 229: Alert on scan volume drop**

```python
# If daily scan count drops > 50% vs rolling 7-day average
daily_count = get_scan_count_last_24h()
rolling_avg = get_rolling_7day_avg()
if daily_count < rolling_avg * 0.5:
    alert(f"Scan volume dropped: {daily_count} vs avg {rolling_avg:.0f}")
```

---

**Phase 230: Use existing notification_service for alerts**

```python
from api.services.notification_service import notification_service
await notification_service.send_admin_alert(
    title="Model Drift Detected",
    message=f"Chest MAE increased from 3.2 to 4.1 cm",
    severity="warning"
)
```

---

**Phase 231: Log all alerts to alerts.log**

```python
logging.getLogger("DRIFT").warning(f"DRIFT: {message}")
```

---

### Phase 8.3 — Visual Dashboard (Phases 232–235)

---

**Phase 232: Add accuracy section to admin dashboard**

In `dashboard.html`, a new section showing:
- Model version
- Dataset size
- MAE by measurement

---

**Phase 233: Add dataset explorer page**

A page to browse:
- Individual scans in the dataset
- Shape parameter distribution
- Cluster membership
- Silhouette consistency scores

---

**Phase 234: Add calibration comparison tool**

Compare predictions before/after calibration for any measurement:
```
[Select measurement] -> [Chest Round]
Before calibration: 108.5 cm
After calibration: 102.3 cm
Cluster: 3 (Athletic)
```

---

**Phase 235: Add deployment history table**

```
| Version | Date | Scans | MAE | Deployed | Rolled Back |
|---------|------|-------|-----|----------|-------------|
| 1       | Jul 1| 847   | 7.2 | Yes      | No          |
| 2       | Jul 8| 1023  | 6.1 | Yes      | No          |
| 3       | Jul 15| 1247 | 5.4 | Yes      | No          |
```

---

## Phase 9: Advanced Model Training (Phases 236–248)

*Beyond calibration: train actual neural networks on the growing dataset.*

---

### Phase 9.1 — CNN Measurement Surrogate (Phases 236–240)

---

**Phase 236: Create `scripts/train_image_to_measurements.py`**

Train a ResNet-18 that takes front + side images and directly predicts measurements. This serves as:
1. A faster alternative to HMR (no TF dependency)
2. A quality check (compare with HMR output)
3. A fallback when HMR fails

---

**Phase 237: Dataset preparation**

```python
class ImageMeasurementDataset(Dataset):
    def __init__(self, dataset_dir, split='train'):
        self.scan_ids = (dataset_dir / 'splits' / f'{split}.txt').read_text().splitlines()
        self.dataset_dir = dataset_dir
    
    def __getitem__(self, idx):
        scan_dir = self.dataset_dir / f"scan_{self.scan_ids[idx]}"
        front = cv2.imread(str(scan_dir / 'front.png'))
        front = cv2.resize(front, (224, 224)) / 255.0
        side = cv2.imread(str(scan_dir / 'side.png'))
        side = cv2.resize(side, (224, 224)) / 255.0
        
        meta = json.loads((scan_dir / 'metadata.json').read_text())
        measurements = meta['measurements']
        target = torch.FloatTensor([
            measurements.get('Chest Round', 0),
            measurements.get('Waist Round', 0),
            measurements.get('Hip Round', 0),
            measurements.get('Shoulder', 0),
            measurements.get('Neck Round', 0),
        ])
        return front, side, target
```

---

**Phase 238: Model architecture**

```python
import torchvision.models as models

class DualImageCNN(nn.Module):
    def __init__(self, n_measurements=5):
        super().__init__()
        self.front_encoder = models.resnet18(pretrained=True)
        self.side_encoder = models.resnet18(pretrained=True)
        
        # Remove final FC layers
        self.front_encoder.fc = nn.Identity()
        self.side_encoder.fc = nn.Identity()
        
        in_features = 512 * 2  # concat both encoders
        self.regressor = nn.Sequential(
            nn.Linear(in_features, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, n_measurements),
        )
    
    def forward(self, front, side):
        f = self.front_encoder(front)
        s = self.side_encoder(side)
        x = torch.cat([f, s], dim=1)
        return self.regressor(x)
```

---

**Phase 239: Training loop**

```python
model = DualImageCNN(n_measurements=5)
optimizer = optim.Adam(model.parameters(), lr=1e-4)
criterion = nn.MSELoss()

for epoch in range(100):
    for front, side, target in train_loader:
        optimizer.zero_grad()
        pred = model(front, side)
        loss = criterion(pred, target)
        loss.backward()
        optimizer.step()
```

---

**Phase 240: Evaluate vs HMR pipeline**

```python
cnn_mae = compute_mae(cnn_preds, targets)
hmr_mae = compute_mae(hmr_preds, targets)
print(f"CNN MAE: {cnn_mae:.2f} cm, HMR MAE: {hmr_mae:.2f} cm")
print(f"CNN/HMR ratio: {cnn_mae / hmr_mae:.2f}x")
```

---

### Phase 9.2 — Multi-View Consistency (Phases 241–244)

---

**Phase 241: Train for viewpoint invariance**

Render mesh from 4 arbitrary viewpoints, train model to give consistent measurements regardless of viewpoint.

---

**Phase 242: Consistency loss**

```python
# L_consistency = variance of predictions across viewpoints
views = [render_mesh(mesh, angle) for angle in [0, 45, 90, 135]]
preds = torch.stack([model(view) for view in views])
consistency_loss = preds.var(dim=0).mean()
```

---

**Phase 243: Combined training**

```python
loss = reconstruction_loss + 0.1 * consistency_loss
```

---

**Phase 244: Validate measurement variance across views**

```python
for scan in test_scans:
    variances = []
    for angle in [0, 45, 90, 135]:
        view = render_mesh(scan['mesh'], angle)
        pred = model(view)
        variances.append(pred)
    variance = np.var(variances, axis=0)
    print(f"Scan {scan['id']}: measurement variance = {variance.mean():.2f}")
```

---

### Phase 9.3 — Synthetic Data Augmentation (Phases 245–248)

---

**Phase 245: Create `scripts/generate_synthetic_scans.py`**

Generate synthetic training data by:
1. Sampling shape params from GMM prior
2. Sampling random poses
3. Rendering front + side images
4. Computing measurements from the mesh

---

**Phase 246: Sample diverse body shapes**

```python
def sample_diverse_shapes(gmm, scaler, n=1000):
    """Sample diverse shape vectors from the GMM prior."""
    shapes_std = gmm.sample(n)[0]
    shapes = scaler.inverse_transform(shapes_std)
    return shapes
```

---

**Phase 247: Render synthetic images**

```python
def render_synthetic(shape_params, pose_params):
    # Create SMPL mesh with given shape + pose
    mesh = create_smpl_mesh(shape_params, pose_params)
    # Render front view
    front = render(mesh, camera_position='front')
    # Render side view
    side = render(mesh, camera_position='side')
    # Add random background
    front = add_random_background(front)
    side = add_random_background(side)
    return front, side
```

---

**Phase 248: Add synthetic scans to dataset**

```python
synthetic_dir = dataset_dir / "synthetic"
synthetic_dir.mkdir(exist_ok=True)

for i in range(1000):
    scan_dir = synthetic_dir / f"synth_{i:05d}"
    scan_dir.mkdir()
    cv2.imwrite(str(scan_dir / "front.png"), front)
    cv2.imwrite(str(scan_dir / "side.png"), side)
    json.dump(metadata, open(scan_dir / "metadata.json", 'w'))
```

---

## Phase 10: Production Hardening (Phases 249–250)

---

**Phase 249: A/B test new calibration**

Route 10% of traffic to old factors, 90% to new cluster factors. Compare MAE via user-reported measurements.

```python
# In measurement_calibration.py
import random
USE_NEW_FACTORS_THRESHOLD = 0.9  # 90% traffic

if random.random() < USE_NEW_FACTORS_THRESHOLD:
    # Use cluster-specific calibration
    result = cluster_calibrate(measurements, gender, shape_params)
else:
    # Use old global calibration
    result = global_calibrate(measurements, gender)
```

---

**Phase 250: Full rollout after 1 week monitoring**

```python
# After confirming no regression for 7 days:
USE_NEW_FACTORS_THRESHOLD = 1.0  # 100% traffic
# Remove old global factors file
os.remove('api/services/calibration_factors.json')
logger.info("Full rollout complete — old calibration removed")
```

---

## Appendices

### A. File Manifest

| New File | Purpose |
|----------|---------|
| `scripts/004_smpl_params_migration.sql` | Schema migration for SMPL params |
| `scripts/build_training_dataset.py` | Dataset aggregation pipeline |
| `scripts/train_shape_prior.py` | GMM shape prior training |
| `scripts/train_shape_vae.py` | VAE shape prior training |
| `scripts/compute_body_clusters.py` | K-means body type clustering |
| `scripts/compute_cluster_calibration.py` | Per-cluster calibration training |
| `scripts/compute_measurement_distributions.py` | Statistical distribution computation |
| `scripts/silhouette_renderer.py` | Mesh rendering for silhouette consistency |
| `scripts/compute_silhouette_consistency.py` | Batch silhouette consistency evaluation |
| `scripts/optimize_shape_from_silhouette.py` | Silhouette-based shape optimization |
| `scripts/train_pipeline.py` | Master orchestrator |
| `scripts/deploy_models.sh` | Model deployment |
| `scripts/rollback_models.sh` | Model rollback |
| `scripts/evaluate_accuracy.py` | Accuracy evaluation |
| `scripts/monitor_data_quality.py` | Data quality monitoring |
| `scripts/monitor_drift.py` | Drift detection |
| `scripts/train_image_to_measurements.py` | CNN measurement surrogate |
| `scripts/train_multi_view.py` | Multi-view consistency training |
| `scripts/generate_synthetic_scans.py` | Synthetic data generation |
| `scripts/backfill_smpl_params.py` | Backfill master |
| `scripts/run_migration.sh` | Migration runner |
| `scripts/verify_storage_access.py` | Storage verification |
| `scripts/verify_backfill.py` | Backfill verification |
| `scripts/generate_weekly_report.py` | Weekly accuracy report |
| `api/models/priors/__init__.py` | Prior models module |

| Modified File | Changes |
|---------------|---------|
| `api/services/extract_measurements.py` | Return smpl_params + joints3d; shape prior integration; outlier detection |
| `api/services/hmr_subprocess.py` | Unpack 9-element tuple; export T-pose mesh; include smpl_params in JSON |
| `api/services/measurement_calibration.py` | Per-cluster calibration; accept shape_params parameter |
| `api/routes/measurements.py` | Parse smpl_params, joints3d, tpose_mesh_path from subprocess; pass to DB |
| `api/services/database_service.py` | Save smpl_params, joints3d, tpose_mesh_url |
| `api/services/mesh_exporter.py` | T-pose mesh export method |

### B. Schema: measurements table (updated)

```
Column                  Type        Notes
----------------------- ----------- --------------------------------
id                      UUID        Primary key
user_id                 TEXT        Merchant or client
client_name             TEXT
height                  REAL        cm
gender                  TEXT        'male' or 'female'
biometrics              JSONB       Measurements + __smpl_params + __joints3d
landmarks_3d            JSONB
mesh_url                TEXT        Local path
mesh_storage_url        TEXT        Supabase Storage URL
photo_front_url         TEXT        Supabase Storage URL
photo_side_url          TEXT        Supabase Storage URL
body_shape              TEXT
size_recommendation     TEXT
clinical_realism_index  REAL
source_of_truth         BOOL
created_at              TIMESTAMPTZ
smpl_params             JSONB       New: camera, pose, shape
joints_3d               JSONB       New: 19x3 joints
tpose_mesh_url          TEXT        New: T-pose mesh Storage URL
smpl_params_version     INTEGER     New: format version
storage_uploaded_at     TIMESTAMPTZ New
dataset_version         INTEGER     New: training dataset version
```

### C. Storage Buckets

| Bucket | Visibility | Purpose |
|--------|-----------|---------|
| `scan_photos` | Public (by owner UID) | Original front/side photos |
| `meshes` | Public (by owner UID) | Posed and T-pose OBJ files |
| `training_data` | Service role only | Exported dataset archives |

### D. Training Dataset Directory Structure

```
data/training_dataset/
├── v1/
│   ├── manifest.csv
│   ├── VERSION.json
│   ├── shape_statistics.json
│   ├── measurement_statistics.json
│   ├── gender_shape_stats.json
│   ├── splits/
│   │   ├── train.txt
│   │   ├── val.txt
│   │   └── test.txt
│   ├── scan_abc123/
│   │   ├── front.png
│   │   ├── side.png
│   │   ├── mesh_posed.obj
│   │   ├── mesh_tpose.obj
│   │   └── metadata.json
│   └── ...
└── v2/
    └── ...
```

### E. Model Files (api/models/priors/)

```
api/models/priors/
├── __init__.py
├── shape_prior_gmm.pkl          # GMM model (pickle)
├── shape_prior_gmm.json         # GMM parameters (JSON)
├── shape_prior_vae.pt           # VAE model (TorchScript)
├── shape_scaler.pkl             # StandardScaler (pickle)
├── shape_scaler.json            # Scaler params (JSON)
├── measurement_distributions.json  # Per-subgroup quantiles
├── body_clusters.pkl            # KMeans model (pickle)
├── body_cluster_centroids.json  # Cluster centers (JSON)
├── calibration_factors_per_cluster.json  # Per-cluster α,β
```

### F. Dependency Map

```
Phase 0 (Data Capture) ──► Phase 1 (Dataset Pipeline) ──► Phase 3 (Shape Prior)
         │                          │                             │
         │                          │                             ▼
         │                          │                   Phase 4 (Measurement Consistency)
         │                          │                             │
         │                          ▼                             ▼
         │                  Phase 5 (Silhouette) ─────► Phase 6 (Per-Subgroup Calibration)
         │                          │                             │
         │                          ▼                             ▼
         └─────────────────► Phase 7 (Continuous Training Pipeline)
                                   │
                                   ▼
                            Phase 8 (Monitoring)
                                   │
                                   ▼
                            Phase 9 (Advanced Models)
                                   │
                                   ▼
                           Phase 10 (Production Rollout)
```

### G. Recommended Execution Order

1. **Week 1:** Phases 0–6 (capture SMPL params, backfill existing scans, run migration)
2. **Week 2:** Phases 50–60 (build first dataset version), Phases 96–106 (train shape prior)
3. **Week 3:** Phases 115–120 (integrate shape prior into inference), Phases 121–130 (measurement distributions)
4. **Week 4:** Phases 131–140 (outlier detection + shrinkage in inference), replace hardcoded CRI
5. **Week 5:** Phases 166–189 (per-cluster calibration), Phases 141–165 (silhouette consistency)
6. **Week 6:** Phases 190–217 (automated training pipeline)
7. **Week 7:** Phases 218–235 (monitoring + dashboard)
8. **Week 8:** Phases 236–250 (advanced models + production rollout)

---

*End of 250-Phase Implementation Plan*
