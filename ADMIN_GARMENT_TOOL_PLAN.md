# Admin Garment Tool: Implementation Plan

**Objective**: Automate the 9-size Blender cloth draping pipeline to allow admins to add new garment types with high-fidelity fit morphs.

## Current Technical Achievements (Fixed in this session)
These fixes solved the core blockers of the draping pipeline and are already integrated into the production scripts:

1.  **HMR Intelligence Bridge**: Fixed `setup_tf_bridge()` to handle TensorFlow 1.x/2.x environment drift.
2.  **Scale Normalization**: Implemented `dm -> m` conversion in `create_blender_mesh` to ensure body models match real-world scale.
3.  **Hierarchy Hardening**: Implemented critical **unparenting** in `import_garment` to clear 750x legacy transforms from Sketchfab/GLB nodes.
4.  **Coordinate Alignment**: Synchronized Blender and Three.js by rotating body meshes to **Z-up** during import.
5.  **Clean GLB Export**: Updated `export_gltf.py` to use `use_selection=True` and scene cleanup to ensure garment-only assets.
6.  **Morph Interpretation**: Fixed `GarmentMorphController` to use `morphTargetsRelative=true`, resolving the "tiny collapsed mesh" bug.
7.  **WebGL Texture Stability**: Fixed `0x0000` internal format errors and `glGenerateMipmap` failures by implementing pre-upload material normalization and disabling mipmaps on non-diffuse maps.
8.  **Concurrency Locking**: Added `_loadingGarment` guards in `index.html` to prevent parallel resource loading and race conditions.

---

## Phase 1: Backend Infrastructure (FastAPI + Blender)
1.  **Blender Task Queue**: Implement a Celery or background task system to handle heavy Blender simulations without blocking the main API.
2.  **Simulation Endpoint**: Create `POST /api/v2/admin/garments/simulate`
    *   Accepts: Base GLB file, Garment Name, Category (Jacket, Trouser, etc.).
    *   Triggers: Orchestrated `run_pipeline.py` execution.
3.  **Pipeline Integration**: Update `run_pipeline.py` to be callable as a module or with standardized subprocess arguments for any garment path.

## Phase 2: Frontend Admin UI
1.  **Garment Dashboard**: Create a new view in `admin.html` for "Garment Management."
2.  **Upload Interface**:
    *   Drag-and-drop zone for base GLB files.
    *   Form fields for metadata (Display Name, Description, Ease Factor override).
3.  **Progress Monitor**: 
    *   Real-time status updates using SSE (Server-Sent Events) or polling.
    *   States: "Uploading" → "Simulating (0/9)" → "Exporting" → "Ready".

---

## Phase 3: Automated Storage & Registry
1.  **Asset Persistence**: Automatically save the final `{name}_morphed.glb` and `{name}_morphed_config.json` to the `public/models/garments/` directory on the server.
2.  **Database Registry**: Insert new garment records into a `garments` table in Supabase to track availability and metadata.
3.  **Automatic Frontend Refresh**: Implement logic in `index.html` to fetch available garments from the registry instead of hardcoded options.

---

## Phase 4: Future Stability & Quality Enhancements
These are next-generation fixes planned to further professionalize the output:

1.  **Automatic Pivot Centering**: Script to automatically center the garment's horizontal pivot point during import to prevent "drift" on asymmetric models.
2.  **Ambient Occlusion (AO) Baking**: Integrate Cycles baking into the pipeline to improve visual depth on draped cloth.
3.  **Low-Poly LOD Generation**: Automatically generate a 5k-vertex "Fast" version of the 20k-vertex morphed mesh for low-end mobile devices.
4.  **Shadow Plane Projection**: Bake contact shadows into the GLB for better groundedness on the 3D model.

## Verification Plan
*   **Unit Tests**: Verify the `simulate` endpoint starts a Blender process.
*   **E2E Test**: Upload a simple cube-jacket GLB and verify it appears in the visualizer with 8 morph targets.
*   **Sanity Check**: Ensure disk cache is cleaned up after successful export.
