# KORRA: Digital Twin (30-Phase Implementation Plan)
**Objective**: Weaponize the 6,890-point HMR vertex mesh and skeletal landmarks into a persistent "3D Digital Twin" for both User and Admin Dashboards.

---

## 🏛️ Block 1: Storage & Schema Foundation (Phases 1-5)
1.  **Phase 1: Supabase Bucket Setup**
    *   **Action**: Create `korra-meshes` bucket in Supabase.
    *   **Config**: Public access disabled; RLS enabled for `user_id` ownership.
2.  **Phase 2: DB Schema Hardening**
    *   **File**: [FINAL_SYNC_REPAIR.sql](file:///Users/mac/ai-body-scan-saas/FINAL_SYNC_REPAIR.sql)
    *   **Action**: Add columns `mesh_url` (TEXT) and `landmarks_3d` (JSONB) to `public.measurements`.
3.  **Phase 3: RLS Policy Hardening**
    *   **Action**: Implement `FOR ALL` policies for Storage objects where `bucket_id = 'korra-meshes'` AND `owner = auth.uid()`.
4.  **Phase 4: Backend Asset Dir Pathing**
    *   **File**: [api/main.py](file:///Users/mac/ai-body-scan-saas/api/main.py)
    *   **Action**: Define `TEMP_MESH_DIR = BASE_DIR / 'data' / 'mesh_cache'`.
5.  **Phase 5: Binary Dependency Injection**
    *   **Action**: Install `pywavefront` (optional) or implement raw OBJ writer in [api/services/mesh_exporter.py](file:///Users/mac/ai-body-scan-saas/api/services/mesh_exporter.py).

---

## ⚙️ Block 2: Backend Mesh Serialization (Phases 6-10)
6.  **Phase 6: HMR Engine Refactor (Persistence)**
    *   **File**: [api/services/extract_measurements.py](file:///Users/mac/ai-body-scan-saas/api/services/extract_measurements.py)
    *   **Action**: Modify `HMRMasterEngine` to return the full 6890-point vertex array to the router.
7.  **Phase 7: OBJ Generator implementation**
    *   **File**: `[NEW] api/services/mesh_exporter.py`
    *   **Logic**: `def generate_obj(vertices, faces): ...` (Write X, Y, Z to standard OBJ format).
8.  **Phase 8: 3D Joint Coordinate Mapping**
    *   **Action**: Map the 72 SMPL joints to their 3D (X, Y, Z) world positions for visualization.
9.  **Phase 9: Supabase Storage Bridge**
    *   **File**: [api/services/database_service.py](file:///Users/mac/ai-body-scan-saas/api/services/database_service.py)
    *   **Action**: Add `upload_mesh_asset(file_path, user_id)` logic.
10. **Phase 10: Router Integration (Handshake)**
    *   **File**: [api/routes/measurements.py](file:///Users/mac/ai-body-scan-saas/api/routes/measurements.py)
    *   **Action**: Update `/extract` endpoint to trigger Mesh Export and return `mesh_url`.

---

## 🎨 Block 3: Frontend 3D Infrastructure (Phases 11-15)
11. **Phase 11: Local Three.js Procurement**
    *   **Action**: Download `three.min.js` to `public/assets/`.
12. **Phase 12: KORRA 3D Component Brain**
    *   **File**: `[NEW] public/assets/korra_viz.js`
    *   **Logic**: Create `window.KORRA_VIZ` namespace for 3D rendering.
13. **Phase 13: The "Electric Mint" Shader**
    *   **Logic**: Implement `THREE.WireframeGeometry` with color `#C6FF00` and 0.5 opacity.
14. **Phase 14: OrbitControl Implementation**
    *   **Action**: Allow users to rotate, zoom, and pan the 3D body.
15. **Phase 15: Cross-Page Component Injection**
    *   **Files**: [admin.html](file:///Users/mac/ai-body-scan-saas/admin.html) & [dashboard.html](file:///Users/mac/ai-body-scan-saas/dashboard.html)
    *   **Action**: Mount `<div id="3d-viewport"></div>` slots.

---

## 🛠️ Block 4: Admin Lab 3D Hardening (Phases 16-20)
16. **Phase 16: Admin 3D Viewport Activation**
    *   **Action**: Load the 3D model automatically after a successfull Admin Lab scan.
17. **Phase 17: "Vertex Slice" Visualization**
    *   **Logic**: Highlight the Y-index slices in Mint where Chest/Waist were measured.
18. **Phase 18: 3D Joint Marker Overlay**
    *   **Logic**: Place 3D spheres at the detected landmark coordinates in the 3D scene.
19. **Phase 19: Raw Point Cloud Export (.PLY)**
    *   **Action**: Add "Download Raw Mesh" button to the Testing Lab.
20. **Phase 20: Performance Audit (VRAM)**
    *   **Action**: Implement `scene.dispose()` logic to prevent memory leaks during multiple tests.

---

## 👤 Block 5: User Dashboard Activation (Phases 21-25)
21. **Phase 21: "My Digital Twin" UI Slot**
    *   **Action**: Place the 3D viewer as the "Hero" element of the User Workbench.
22. **Phase 22: Historical 3D Lookup**
    *   **Logic**: Allow users to switch between their old 3D models to see body changes.
23. **Phase 23: Interactive Rotation UI**
    *   **Action**: Add Mint-styled "Auto-Rotate" and "Inspect" toggles.
24. **Phase 24: 3D Thumbnail Generation**
    *   **Action**: Capture a PNG screenshot of the 3D scene for the "Recent Scans" list.
25. **Phase 25: Social Share (3D Preview)**
    *   **Action**: (Restricted) Allow users to share a view-only link to their 3D twin with their tailor.

---

## 🚀 Block 6: Performance & Lockdown (Phases 26-30)
26. **Phase 26: Draco Compression Integration**
    *   **Action**: Reduce OBJ file size from 1MB to ~150KB for faster Lagos/London transport.
27. **Phase 27: Multi-Subject Comparison (3D)**
    *   **Action**: Render two 3D meshes side-by-side in the Admin Lab for fit-drift auditing.
28. **Phase 28: Global 3D Error Handling**
    *   **Action**: Display "Mesh Generation Failed" UI if the body is clipped or pose is too noisy.
29. **Phase 29: Final "Obsidian & Mint" Polish**
    *   **Action**: Apply bloom effects and glassmorphic UI overlays to the 3D viewport.
30. **Phase 30: Gold Master Digital Twin Handover**
    *   **Action**: Final Production Lockdown and Documentation Update.

---
**Status**: Ready for implementation of Block 1.
