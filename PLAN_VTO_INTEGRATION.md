## TailorNet Body + VTO Integration — 100-Phase Implementation Plan

Every scan gets a TailorNet body OBJ from `SMPL4Garment`. The existing 3D viewport loads this body instead of the standard HMR SMPL mesh. Garment meshes from TailorNet auto-align because they share the same model instance.

---

### Track 0 — Backend: TailorNet body export (Phases 0–19)

#### Phase 0
Read `hmr_subprocess.py` lines 190–218. Confirm where TailorNet block sits. Read `smpl4garment.py` to verify `SMPL4Garment.run()` signature and that it can be called with betas only (no garment_d).

#### Phase 1
Read `tailornet_bridge.py` `run_tailornet()` to confirm `body_verts/body_faces` are in the return dict. Check coordinate system (SMPL orientation, scale) matches standard SMPL body.

#### Phase 2
Read the existing SMPL body export in `hmr_subprocess.py` lines 105–111 (`MeshExporter.save_to_obj(vertices, mesh_path)`). Note the pose: is this the posed mesh or T-pose? Confirm the TailorNet body is also posed (with thetas).

#### Phase 3
In `hmr_subprocess.py`, add new block after SMPL params are ready, before TailorNet garment block (~line 190):
```python
tn_body_path = None
if mesh_path and smpl_params:
    try:
        betas_300 = smpl_params.get('betas_300')
        if betas_300 is not None:
            from api.services.tailornet.models.smpl4garment import SMPL4Garment
            smpl4g = SMPL4Garment(gender)
            body_m, _ = smpl4g.run(beta=np.array(betas_300, dtype=np.float32))
            import trimesh
            bm = trimesh.Trimesh(vertices=body_m.v, faces=body_m.f, process=False)
            tn_body_path = str(mesh_path).replace('.obj', '_tn_body.obj')
            bm.export(tn_body_path, file_type='obj')
    except Exception as e:
        logger.warning(f"TailorNet body export skipped: {e}")
```

#### Phase 4
Verify `gender` variable is in scope (`gender = 'male' | 'female'`). Normalize casing if needed.

#### Phase 5
Add `"tailornet_body_path": str(tn_body_path) if tn_body_path else None` to the return dict.

#### Phase 6
Add `gc.collect()` and `del smpl4g, body_m, bm` after export for memory safety.

#### Phase 7
Read `measurements.py` `/drape` endpoint (lines 567–591). Confirm where `result['body_verts/body_faces']` are available.

#### Phase 8
In `/drape`, after each garment export (line 578–582), add body export (once per call, not per garment class):
```python
if not public_body_url:
    body_m = trimesh.Trimesh(vertices=result['body_verts'], faces=result['body_faces'], process=False)
    body_file = f"garment_{scan_id}_{attire}_body.obj"
    body_m.export(str(out_dir / body_file))
    public_body_url = f"/meshes/garments/{body_file}"
```

#### Phase 9
Initialize `public_body_url = None` before the loop. Return it in the response.

#### Phase 10
Read response construction (lines 587–591). Add `"body_mesh": public_body_url` to the return dict.

#### Phase 11
Verify the `/drape` response is backward-compatible — existing frontend code accesses `result.garment_meshes` and ignores unknown fields.

#### Phase 12
Read `api/services/__init__.py` — verify `tailornet.models.smpl4garment` import path works from `hmr_subprocess.py`.

#### Phase 13
Check `SMPL4Garment` constructor — does `gender` need `'male'` or `'m'`? Verify against usage in `tailornet_bridge.py`.

#### Phase 14
Trace `thetas`: standard SMPL body uses HMR-estimated pose, `SMPL4Garment.run()` defaults to zero pose (T-pose). If arms differ, confirm this is acceptable for the viewport.

#### Phase 15
If pose difference matters, read thetas from `smpl_params['pose']` and pass to `smpl4g.run(theta=...)` to match standard posed mesh.

#### Phase 16
Read HMR engine to understand where `v_measure_tpose` originates (lines 114–116 in hmr_subprocess.py). Confirm whether the standard SMPL posed mesh or T-pose is used in the viewport.

#### Phase 17
Check `mesh_path` routing through the API: how does `mesh_path` → `tailornet_body_path` → frontend URL? Read scan data route.

#### Phase 18
In scan data route, add `tailornet_body_url` field that translates file path to public URL.

#### Phase 19
Verify nginx/CORS — `public/meshes/` is already served. The `_tn_body.obj` file is accessible at `<base_url>/meshes/<filename>`.

---

### Track 1 — Frontend: korra_viz.js engine upgrades (Phases 20–39)

#### Phase 20
Read `korra_viz.js` `parseAndRenderOBJ()` (lines 312–406). Understand mesh creation, position/rotation/scale, outline, return value `{vertices, faces, size}`.

#### Phase 21
Read `korra_viz.js` `loadMesh()` (lines 231–272). Understand caching, `createTechnicalProxy()` fallback, `this.mesh` assignment.

#### Phase 22
Add `loadTailornetBody(url)` method to KorraVisualizer:
```javascript
async loadTailornetBody(url) {
  const text = await fetch(url).then(r => { if (!r.ok) throw new Error('Failed'); return r.text(); });
  const meshData = this.parseAndRenderOBJ(text);
  return meshData;
}
```

#### Phase 23
In `loadTailornetBody`, if `this.mesh` exists, dispose it first: `this.mesh.geometry.dispose()`, `this.mesh.material.dispose()`, `scene.remove(this.mesh)`.

#### Phase 24
After `parseAndRenderOBJ`, re-apply custom settings: wireframe mode, visibility, landmarks.

#### Phase 25
Add `this._tailornetBodyLoaded = true` flag to prevent double-loading.

#### Phase 26
In `init()`, after renderer creation, add tone mapping:
```javascript
this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
this.renderer.toneMappingExposure = 1.2;
```

#### Phase 27
Add `this.autoRotate = false` and `this.autoRotateSpeed = 2.0` to constructor.

#### Phase 28
In animation loop, add:
```javascript
if (this.autoRotate) {
  this._orbitSpherical.theta += 0.005 * this.autoRotateSpeed;
  this._applyOrbit();
}
```

#### Phase 29
Add `setAutoRotate(enabled)` method.

#### Phase 30
Read `removeGarment()` (lines 525–544). Confirm it disposes geometry/material and removes from scene.

#### Phase 31
Read `toggleGarmentVisibility()` (lines 546–551). Add a version that toggles all layers if missing.

#### Phase 32
Add `getGarmentVisibility()` — returns visibility state of first garment mesh.

#### Phase 33
Verify `loadGarment()` line 509–513 copies `position/rotation/scale` from `this.mesh`. Confirm this works after `loadTailornetBody()` replaces `this.mesh`.

#### Phase 34
Read `parseAndRenderOBJ()` line ~377: `mesh.position.set(0, size.y * 0.637, 0)`. Confirm TailorNet body uses same positioning convention.

#### Phase 35
Read `parseAndRenderOBJ()` line ~367: `mesh.rotation.x = Math.PI`. Confirm TailorNet body also needs this flip.

#### Phase 36
Test: load TailorNet body OBJ vs standard SMPL OBJ. Compare bounding box, orientation, vertex positions. Adjust positioning if needed.

#### Phase 37
Read `toggleProjection()` (lines 821–846). Confirm it works with tone mapping and auto-rotate.

#### Phase 38
Wireframe/solid toggle: confirm `loadTailornetBody()` reuses `_wireframeMat`/`_solidMat` correctly.

#### Phase 39
Background toggle: confirm `toggleBackground()` works with `ACESFilmicToneMapping`.

---

### Track 2 — Frontend: measurement-screen.js integration (Phases 40–54)

#### Phase 40
Read `initViewer()` (lines 1094–1144). Find `meshUrl` determination (line 1115).

#### Phase 41
After existing mesh loading block (line 1141), add TailorNet body swap:
```javascript
const tnBodyUrl = this.data?.tailornet_body_storage_url || this.data?.tailornet_body_url;
if (tnBodyUrl && this.viewerInstance?.loadTailornetBody) {
  fetch(tnBodyUrl)
    .then(r => r.text())
    .then(text => {
      this.viewerInstance._meshCache.set(tnBodyUrl, text);
      this.viewerInstance.loadTailornetBody(tnBodyUrl);
    })
    .catch(() => { console.warn('TailorNet body not available'); });
}
```

#### Phase 42
Read `open()` (lines 137–221). Confirm `this.data` is populated before `initViewer()`.

#### Phase 43
Read `_updateGarmentForContext()` (lines 1920–1968). Find `/drape` response handler.

#### Phase 44
After garment mesh loading, add body swap from drape response:
```javascript
if (result.body_mesh && this.viewerInstance && !this.viewerInstance._tailornetBodyLoaded) {
  fetch(result.body_mesh)
    .then(r => r.text())
    .then(text => {
      this.viewerInstance._meshCache.set(result.body_mesh, text);
      this.viewerInstance.loadTailornetBody(result.body_mesh);
    })
    .catch(() => {});
}
```

#### Phase 45
Standard context handler (lines 1921–1926): keep garment removal + VTO controls hide. Do NOT remove body.

#### Phase 46
Add `this._tailornetBodyLoadAttempted` flag to prevent double-fetching on repeated attire selections.

#### Phase 47
Read `goBack()` / `cleanup()` (lines 2263–2291). Reset `_tailornetBodyLoadAttempted` and `_tailornetBodyLoaded` flags.

#### Phase 48
Read `buildHTML()` (lines 230–356). Find `.ms-vto-controls` (line ~288).

#### Phase 49
Add garment visibility ON/OFF button to `.ms-vto-controls`.

#### Phase 50
Add `setGarmentVisibility(visible)` method calling `viewerInstance.toggleGarmentVisibility(visible)`.

#### Phase 51
Add auto-rotate toggle button to `.ms-viewer-toolbar`, matching existing projection toggle pattern.

#### Phase 52
Wire auto-rotate button click → `viewerInstance.setAutoRotate()` + toggle `.active` class.

#### Phase 53
Read `setGarmentOpacity()` (lines 1988–2003). Confirm it loops over `garmentMeshes`. Visibility toggle uses same pattern.

#### Phase 54
Read `FABRIC_PRESETS`. Confirm material settings pass through `_updateGarmentForContext()` correctly.

---

### Track 3 — Frontend: CSS & UI (Phases 55–69)

#### Phase 55
Read `.ms-viewer-toolbar` CSS (~lines 1070–1120). Note button size, background, icon colors, active state.

#### Phase 56
Add CSS for auto-rotate toggle: same dimensions as existing toolbar buttons (40px), glass-morphism background, `.active` state with accent color.

#### Phase 57
Add CSS for garment visibility toggle: pill-shaped button in `.ms-vto-controls`, active/inactive states.

#### Phase 58
Read `.ms-vto-controls` CSS (lines 2290–2320). Fit visibility toggle into flex row alongside opacity slider.

#### Phase 59
If visibility toggle doesn't fit in one row, create a second row below using same flex pattern.

#### Phase 60
Add SVG icons: auto-rotate = loop/refresh, visibility = eye / eye-off.

#### Phase 61
Read `.ms-viewer-badge` CSS (~lines 1130–1160). Confirm it renders correctly over TailorNet body.

#### Phase 62
Read `.ms-canvas-container` CSS (~lines 205–230). Confirm canvas resizes correctly.

#### Phase 63
Show VTO spinner during TailorNet body loading, not just during garment loading.

#### Phase 64
Add error state: red border or overlay if TailorNet body fails to load, with retry button.

#### Phase 65
Read side-by-side layout CSS (`.ms-side-by-side`, lines 1052–1073). Confirm 55% viewer width works.

#### Phase 66
Add responsive CSS for mobile: smaller toolbar buttons, stacked VTO controls.

#### Phase 67
Read light mode CSS (`ms-bg-light`, ~lines 1200+). Confirm TailorNet body + garment look good on light bg.

#### Phase 68
Test contrast: TailorNet body uses `_solidMat: 0x4A6FA5`. Confirm with ACES tone mapping.

#### Phase 69
Add transition/animation for garment visibility toggle (fade in/out).

---

### Track 4 — API route refinements (Phases 70–79)

#### Phase 70
Read scan data route (`/api/v2/measurements/complete/{scan_id}`). Find response dict assembly.

#### Phase 71
Find `mesh_storage_url` / `mesh_url`. Add `tailornet_body_storage_url` and `tailornet_body_url` alongside them.

#### Phase 72
Read Supabase storage upload code in `measurements.py` (around line 238). Confirm TailorNet body OBJ is uploaded.

#### Phase 73
If not uploaded, add parallel storage upload for `tn_body_path` alongside garment.

#### Phase 74
Confirm `MeshExporter` or trimesh is used for TailorNet body export — either is fine.

#### Phase 75
Read line ~238 where `garment_mesh_path` is uploaded. Add parallel upload for `tn_body_path`.

#### Phase 76
Verify Supabase storage bucket `meshes` has CORS headers for OBJ fetch.

#### Phase 77
Read `tailornet_setup.py`. Confirm `TAILORNET_DATA_DIR` is accessible from inside Docker container.

#### Phase 78
Add config flag in `tailornet_setup.py` to toggle TailorNet body export on/off.

#### Phase 79
Confirm `trimesh` is in `requirements.txt` (it is — used for garment export already).

---

### Track 5 — Testing (Phases 80–89)

#### Phase 80
Start local server: `cd public && python3 -m http.server 8081`. Verify VTO viewer loads with no console errors.

#### Phase 81
Run TailorNet bridge directly: `python3 -c "from api.services.tailornet_bridge import run_tailornet; r = run_tailornet('t-shirt', 'male'); print('keys:', r.keys(), 'body:', r['body_verts'].shape)"`. Confirm body_verts is 27K+.

#### Phase 82
Export a TailorNet body OBJ manually using `SMPL4Garment`. Verify it opens in a 3D viewer.

#### Phase 83
Compare standard SMPL body OBJ vs TailorNet body OBJ vertex count and structure.

#### Phase 84
Load standalone VTO viewer. Verify: body renders with DoubleSide, semi-transparent with depthWrite:false, garment overlays correctly, no console errors.

#### Phase 85
Test `loadTailornetBody()` from browser console with a known OBJ URL.

#### Phase 86
Deploy to EC2: scp changed files, docker restart. Verify scan creation still works.

#### Phase 87
Verify `public/meshes/` contains `_tn_body.obj` after a scan.

#### Phase 88
Open scan result in browser. Verify: body shows, TailorNet body replaces standard body, no visual glitch.

#### Phase 89
Test garment loading: select attire → garment loads on TailorNet body → opacity slider works → visibility toggle works → auto-rotate works → switch to "standard" → garment removed, body stays.

---

### Track 6 — Hardening (Phases 90–99)

#### Phase 90
Handle missing `betas_300`: fall back to `betas_10` if needed (pad with zeros to 300).

#### Phase 91
Wrap TailorNet body fetch in `initViewer()` in try/catch — failure shouldn't block standard SMPL body display.

#### Phase 92
Add 15s timeout to TailorNet body fetch in `loadTailornetBody()`, matching existing pattern.

#### Phase 93
Add `gc.collect()` after `SMPL4Garment` instantiation + disposal in backend for t3.micro memory safety.

#### Phase 94
Add logging: `logger.info` on successful export, `logger.warning` on skip.

#### Phase 95
Add `dispose()` to `loadTailornetBody()` to clean old `this.mesh` geometry/material before replacing.

#### Phase 96
If `SMPL4Garment` import fails (missing chumpy/psbody deps), log warning and skip. Scan still succeeds with standard SMPL body.

#### Phase 97
Verify TailorNet body OBJ is cleaned up when scan is deleted (if cleanup logic exists).

#### Phase 98
Add "Reset View" toolbar button that resets camera position + auto-rotate to defaults.

#### Phase 99
Update `AGENTS.md` with TailorNet body flow: key file paths, load order, fallback logic.

---

### Summary

| Track | Phases | Deliverable |
|-------|--------|-------------|
| 0: Backend export | 0–19 | `_tn_body.obj` on every scan, `body_mesh` in `/drape` response |
| 1: korra_viz.js engine | 20–39 | `loadTailornetBody()`, ACES tone mapping, auto-rotate |
| 2: measurement-screen.js | 40–54 | Swap body on init + drape, keep body on standard context |
| 3: CSS & UI | 55–69 | Auto-rotate + visibility toggle buttons, responsive styling |
| 4: API routes | 70–79 | `tailornet_body_url` in scan data response, storage upload |
| 5: Testing | 80–89 | Local + EC2 verification of full pipeline |
| 6: Hardening | 90–99 | Error recovery, memory safety, docs |
