# Garment Reconstruction Frontend — 100-Phase Improvement Plan

## Current State (7 Gaps)

| # | Gap | Severity |
|---|-----|----------|
| 1 | Result is ZIP download only — no inline 3D preview in the Three.js viewport | **Critical** |
| 2 | No real-time progress indicator — static "~30 sec" text, can actually take 5min | **High** |
| 3 | No 3D visualization of reconstruction output — mesh OBJ files never rendered in browser | **High** |
| 4 | Error handling uses native `alert()` — not an in-view error state | **Medium** |
| 5 | All CSS uses `.ms-tryon-*` classes — no dedicated `.ms-recon-*` CSS | **Low** |
| 6 | `tryon-mode` body class reused for reconstruct — both hide same chrome | **Low** |
| 7 | Auth token validated client-side before API call (this is actually *good* — keep it) | **N/A** |

## Track Structure

| Track | Phases | Theme | Files Affected |
|-------|--------|-------|----------------|
| **A** | 0–19 | Dedicated Reconstruct CSS + Body Class | `measurement-screen.css`, `measurement-screen.js` |
| **B** | 20–39 | Inline Error States (kill `alert()`) | `measurement-screen.js`, `measurement-screen.css` |
| **C** | 40–59 | Real-Time Progress via Server-Sent Events | `api_server.py`, `server.py`, `measurement-screen.js` |
| **D** | 60–79 | Inline 3D Preview in Three.js Viewport | `korra_viz.js`, `measurement-screen.js` |
| **E** | 80–89 | Auto-Load Reconstructed Mesh into Virtual Try-On | `measurement-screen.js` |
| **F** | 90–99 | Polish, Testing, Edge Cases | All frontend files |

**Total: 100 phases** (0-indexed for Kaggle-style numbering)

---

# Track A — Dedicated Reconstruct CSS + Body Class (Phases 0–19)

## Phase 0: Audit all `.ms-tryon-*` CSS classes used by reconstruct view
- Grep `measurement-screen.css` for every `.ms-tryon-*` selector
- Cross-reference against `buildReconstructView()` HTML template
- List which classes are shared with actual Try-On and which are reconstruct-only
- **Deliverable**: Annotated list at the top of the plan

## Phase 1: Create `.ms-recon-view` root class
- Copy `.ms-tryon-view` CSS block to new `.ms-recon-view` class
- Same flex column layout, full height, overflow behavior
- **Deliverable**: New CSS class in `measurement-screen.css`

## Phase 2: Create `.ms-recon-topbar` class
- Copy `.ms-tryon-topbar` → `.ms-recon-topbar`
- Same header bar styling (back button, title, subtitle)
- **Deliverable**: New CSS class in `measurement-screen.css`

## Phase 3: Create `.ms-recon-back` class
- Copy `.ms-tryon-back` → `.ms-recon-back`
- Mint green back button, same hover/active states
- **Deliverable**: New CSS class in `measurement-screen.css`

## Phase 4: Create `.ms-recon-title` and `.ms-recon-subtitle` classes
- Copy `.ms-tryon-title` → `.ms-recon-title`
- Copy `.ms-tryon-subtitle` → `.ms-recon-subtitle`
- White bold title, gray subtitle
- **Deliverable**: New CSS classes in `measurement-screen.css`

## Phase 5: Create `.ms-recon-input-area` class
- Copy `.ms-tryon-input-area` → `.ms-recon-input-area`
- Flex row container for upload area
- **Deliverable**: New CSS class in `measurement-screen.css`

## Phase 6: Create `.ms-recon-preview-box`, `.ms-recon-preview-label`, `.ms-recon-preview-img`
- Copy the three `.ms-tryon-preview-*` classes
- 3:4 aspect ratio container, small uppercase label, preview wrapper
- **Deliverable**: 3 new CSS classes in `measurement-screen.css`

## Phase 7: Create `.ms-recon-placeholder` class
- Copy `.ms-tryon-placeholder` → `.ms-recon-placeholder`
- Centered flex with SVG icon + instruction text
- **Deliverable**: New CSS class in `measurement-screen.css`

## Phase 8: Create `.ms-recon-upload-btn` class
- Copy `.ms-tryon-upload-btn` → `.ms-recon-upload-btn`
- Dashed-border upload button, same hover/active states
- **Deliverable**: New CSS class in `measurement-screen.css`

## Phase 9: Create `.ms-recon-action-row` and `.ms-recon-generate-btn` classes
- Copy `.ms-tryon-action-row` → `.ms-recon-action-row`
- Copy `.ms-tryon-generate-btn` → `.ms-recon-generate-btn`
- Teal accent primary action button, disabled state styling
- **Deliverable**: 2 new CSS classes in `measurement-screen.css`

## Phase 10: Create `.ms-recon-status`, `.ms-recon-spinner` classes
- Copy `.ms-tryon-status` → `.ms-recon-status`
- Copy `.ms-tryon-spinner` → `.ms-recon-spinner`
- Flex centered row, 36px CSS spinning ring animation
- **Deliverable**: 2 new CSS classes in `measurement-screen.css`

## Phase 11: Create `.ms-recon-results` and `.ms-recon-results-label`
- Copy `.ms-tryon-results` → `.ms-recon-results`
- Copy `.ms-tryon-results-label` → `.ms-recon-results-label`
- Results section container, small uppercase label
- **Deliverable**: 2 new CSS classes in `measurement-screen.css`

## Phase 12: Create `.ms-recon-error` and `.ms-recon-error-message` classes
- *New* — no try-on equivalent
- `.ms-recon-error`: Red-tinted container, border, background
- `.ms-recon-error-message`: Error text styling
- `.ms-recon-error-dismiss`: Small dismiss button
- **Deliverable**: 3 new CSS classes in `measurement-screen.css`

## Phase 13: Create `.ms-recon-progress-bar` class
- *New* — no try-on equivalent
- Full-width progress bar container
- `.ms-recon-progress-fill`: Animated fill element (width transitions)
- `.ms-recon-progress-text`: Step label overlay
- **Deliverable**: 3 new CSS classes in `measurement-screen.css`

## Phase 14: Create `.ms-recon-3d-container` class
- *New* — no try-on equivalent
- Container div for embedded Three.js canvas
- Aspect ratio 4:5, rounded corners, dark background
- **Deliverable**: New CSS class in `measurement-screen.css`

## Phase 15: Create `.ms-recon-download-btn` class
- *New* — no try-on equivalent
- Styled download button for ZIP (not the same as generate)
- Download icon SVG, hover state
- **Deliverable**: New CSS class in `measurement-screen.css`

## Phase 16: Create `body.recon-mode` CSS class
- Copy `body.tryon-mode` → add `body.recon-mode` to same selectors
- Hides header, sheet controls, tabs on mobile
- Full-screen overlay on mobile (fixed inset, z-index 2200)
- **Deliverable**: Extended CSS selector in `measurement-screen.css`

## Phase 17: Update `buildReconstructView()` — replace all `.ms-tryon-*` with `.ms-recon-*`
- Replace every class reference in the HTML template
- Replace IDs where appropriate (keep `ms-recon-*` IDs for JS hooks)
- **Deliverable**: Updated `buildReconstructView()` in `measurement-screen.js`

## Phase 18: Update `switchView('reconstruct')` — replace `tryon-mode` with `recon-mode`
- Change body class from `tryon-mode` to `recon-mode`
- Keep all the same chrome-hiding behavior
- **Deliverable**: Updated `switchView()` in `measurement-screen.js`

## Phase 19: Verify no CSS leaks — audit both views render correctly
- Load Try-On view: confirm all `.ms-tryon-*` classes still render correctly
- Load Reconstruct view: confirm all `.ms-recon-*` classes render correctly
- Test mobile responsive (max-width: 900px)
- **Deliverable**: QA verification checklist passed

---

# Track B — Inline Error States (Phases 20–39)

## Phase 20: Design error state states (3 variants)
- Define 3 error sub-states:
  - **Validation error**: File too large, wrong format, no file
  - **Auth error**: Session expired, not logged in
  - **Server error**: 503, 502, 500, timeout
- **Deliverable**: Error state spec in this document

## Phase 21: Add error container to `buildReconstructView()` HTML
- Add `<div class="ms-recon-error" id="ms-recon-error" style="display:none">` to template
- Inner: `<div class="ms-recon-error-message" id="ms-recon-error-text"></div>`
- Inner: `<button class="ms-recon-error-dismiss" onclick="KORRA_MS._dismissReconError()">×</button>`
- **Deliverable**: Updated template in `measurement-screen.js`

## Phase 22: Create `_showReconError(message, type)` method
- Accepts error string + type enum ('validation' | 'auth' | 'server')
- Sets error container text
- Shows error container (display: block)
- Hides status spinner
- Shows or hides generate button based on type (validation/auth → keep btn, server → show btn)
- **Deliverable**: New method on `KORRA_MS` in `measurement-screen.js`

## Phase 23: Create `_dismissReconError()` method
- Hides error container
- Restores UI to file-selected state if file still exists
- **Deliverable**: New method in `measurement-screen.js`

## Phase 24: Add error icon SVG by type
- Validation: ⚠️ yellow triangle
- Auth: 🔒 lock icon
- Server: ❌ red X circle
- SVG inline in `buildReconstructView()` or template strings
- **Deliverable**: SVG icons in HTML template

## Phase 25: Auto-dismiss on re-upload
- Bind `onchange` in `_initReconstruct()` to call `_dismissReconError()`
- User reselects file → error disappears
- **Deliverable**: Updated `_initReconstruct()` in `measurement-screen.js`

## Phase 26: Validation — no file selected
- If `_runReconstruct()` called with null/undefined `_reconFile`
- Show validation error: "Please select a garment photo first"
- **Deliverable**: Guard clause in `_runReconstruct()` in `measurement-screen.js`

## Phase 27: Validation — unsupported file format
- Check file.type in `_initReconstruct()` onchange
- Reject non-image files (gif, webp, etc. are OK; PDF, txt, etc. are not)
- Show validation error: "Please select an image file (JPEG, PNG, WebP)"
- **Deliverable**: File type validation in `_initReconstruct()` in `measurement-screen.js`

## Phase 28: Validation — file too large (frontend 20MB check)
- Match proxy's 20MB limit
- Check `file.size > 20 * 1024 * 1024` in `_initReconstruct()`
- Show validation error: "Image too large (max 20MB)"
- **Deliverable**: File size check in `_initReconstruct()` in `measurement-screen.js`

## Phase 29: Auth — session expired error
- Replace `alert('Your session has expired...')` with `_showReconError('Your session has expired. Please sign in again.', 'auth')`
- Add "Sign In" button in auth error state that triggers login flow
- **Deliverable**: Updated auth error handling in `_runReconstruct()` in `measurement-screen.js`

## Phase 30: Server — 503 "Service unavailable" error
- Replace catch in `_runReconstruct()` for 503 responses
- Show server error: "Garment reconstruction service is temporarily unavailable. Please try again in a few minutes."
- **Deliverable**: Updated 503 handling in `_runReconstruct()` in `measurement-screen.js`

## Phase 31: Server — 502 "Backend error" error
- Replace catch for 502 responses
- Show server error: "The reconstruction backend encountered an error. Our team has been notified."
- **Deliverable**: Updated 502 handling in `_runReconstruct()` in `measurement-screen.js`

## Phase 32: Server — timeout (no response in 5min)
- Currently no frontend timeout — user just stares at spinner forever
- Add `AbortController` with 310s timeout (just over proxy's 300s)
- Show server error on timeout: "Reconstruction timed out. Try a simpler garment photo."
- **Deliverable**: AbortController timeout in `_runReconstruct()` in `measurement-screen.js`

## Phase 33: Server — network error (fetch failed)
- Catch `TypeError: Failed to fetch` (network down, DNS failure)
- Show server error: "Network error. Check your internet connection and try again."
- **Deliverable**: Network error handling in `_runReconstruct()` in `measurement-screen.js`

## Phase 34: Server — corrupt ZIP response
- If res.blob() returns 0 bytes or wrong content-type
- Show server error: "Received an empty response. Please try again."
- **Deliverable**: Post-success validation in `_runReconstruct()` in `measurement-screen.js`

## Phase 35: Add error state CSS transitions
- `.ms-recon-error` enters with fadeIn + slideDown animation (300ms)
- `.ms-recon-error` exits with fadeOut + slideUp animation (200ms)
- **Deliverable**: CSS animations in `measurement-screen.css`

## Phase 36: Add error state to buildReconstructView (visual polish)
- Error container placed between action row and results section
- Error dismiss button fades on hover
- Error icon animates (gentle shake for server errors)
- **Deliverable**: Visual polish CSS in `measurement-screen.css`

## Phase 37: Add retry button for server errors
- After server error, show "Retry" button alongside dismiss
- Clicking retry re-calls `_runReconstruct()` with same file
- **Deliverable**: Retry button in error state in `measurement-screen.js`

## Phase 38: Log client-side errors to console with structured format
- `console.error('[Reconstruct]', { type, message, fileSize, timestamp })`
- Helps debug production issues
- **Deliverable**: console.error calls in all error paths in `measurement-screen.js`

## Phase 39: QA — test all error paths end-to-end
- Test validation: no file, bad file, too-large file
- Test auth: expired token, missing token
- Test server: stop Kaggle, stop proxy, timeout
- **Deliverable**: QA verification checklist passed

---

# Track C — Real-Time Progress via Server-Sent Events (Phases 40–59)

## Phase 40: Define progress event types
```json
{"type": "uploading",    "progress": 0,   "message": "Uploading image..."}
{"type": "segmenting",   "progress": 15,  "message": "Segmenting garment..."}
{"type": "meshing",      "progress": 35,  "message": "Reconstructing 3D mesh..."}
{"type": "patterning",   "progress": 65,  "message": "Generating sewing pattern..."}
{"type": "zipping",      "progress": 90,  "message": "Packaging results..."}
{"type": "complete",     "progress": 100, "message": "Reconstruction complete!"}
{"type": "error",        "progress": -1,  "message": "Error: <detail>"}
```
- **Deliverable**: Event type spec in this document

## Phase 41: Add SSE endpoint to Kaggle API server
- `GET /api/v1/reconstruct/progress/{job_id}` — SSE stream
- Server-sent events: `data: {"type":"segmenting","progress":15,...}\n\n`
- Emitted by `process_full_pipeline()` as each stage completes
- **Deliverable**: New endpoint in `api_server.py`

## Phase 42: Add progress emission hooks to `process_full_pipeline()`
- After rembg: `emit('segmenting')`
- After SAM2: `emit('meshing')`
- After GarmentRec: `emit('patterning')`
- After GarmentGPT: `emit('zipping')`
- Before return: `emit('complete')`
- On catch: `emit('error', str(e))`
- **Deliverable**: Progress emission in api_server.py pipeline

## Phase 43: Add SSE relay endpoint to proxy
- `POST /api/v2/garment/reconstruct/start` — creates job, returns SSE URL
- Or: `GET /api/v2/garment/reconstruct/progress/{job_id}` — proxies SSE from Kaggle
- Proxy streams SSE events directly from Kaggle tunnel to frontend
- **Deliverable**: New endpoint in `server.py`

## Phase 44: Replace polling with SSE in `server.py`
- Currently proxy polls `GET /api/v1/job/{id}` every 3s
- After SSE: proxy opens SSE connection to Kaggle, streams events to frontend
- Falls back to polling if SSE fails
- **Deliverable**: Updated `poll_and_return_job()` in `server.py`

## Phase 45: Add `EventSource` frontend connection in `_runReconstruct()`
- After POST returns `{ job_id }`, open `EventSource(progressUrl)`
- Listen for `onmessage` events
- Update progress bar on each event
- Close EventSource on 'complete' or 'error'
- **Deliverable**: SSE consumer in `_runReconstruct()` in `measurement-screen.js`

## Phase 46: Create `_updateReconProgress(type, progress, message)` method
- Accepts event type, progress %, message string
- Updates progress bar width (`transform: scaleX(progress/100)`)
- Updates status text with message
- **Deliverable**: New method on KORRA_MS in `measurement-screen.js`

## Phase 47: Replace static spinner with animated progress bar
- Replace `<div class="ms-recon-spinner">` + static text
- With: `<div class="ms-recon-progress-bar"><div class="ms-recon-progress-fill"></div></div>`
- With: `<span class="ms-recon-progress-text" id="ms-recon-progress-text">Uploading image...</span>`
- **Deliverable**: Updated HTML template in `buildReconstructView()` in `measurement-screen.js`

## Phase 48: Add CSS keyframe animation for progress fill
- `.ms-recon-progress-fill` transitions width with `transition: width 0.4s ease`
- Add indeterminate pulse animation while waiting for first event
- **Deliverable**: CSS animations in `measurement-screen.css`

## Phase 49: Add per-step icon indicators
- Each step gets a small icon or checkmark
- Segmenting: 🔍 → Meshing: 🏗️ → Patterning: 📐 → Zipping: 📦 → Done: ✅
- Show current step icon + completed checkmarks for prior steps
- **Deliverable**: Step indicator UI in `buildReconstructView()` in `measurement-screen.js`

## Phase 50: Add time-elapsed counter
- Show "Elapsed: 0:23 / Estimated: ~2:00"
- Updated every second via `setInterval`
- Estimate based on current step (segmenting=20s, meshing=50s, patterning=50s, zipping=5s)
- **Deliverable**: Elapsed time display in `measurement-screen.js`

## Phase 51: Handle SSE reconnection
- EventSource auto-reconnects on drop (built-in behavior)
- Add exponential backoff display: "Reconnecting... (attempt 2)"
- After 5 failed reconnection attempts, fall back to polling
- **Deliverable**: Reconnection handling in `measurement-screen.js`

## Phase 52: Handle SSE timeout
- If no event received for 90s, show warning: "Still processing... this is taking longer than usual"
- After 300s with no complete event, show timeout error
- **Deliverable**: Timeout handling in `measurement-screen.js`

## Phase 53: Graceful degradation — fall back to polling if SSE fails
- If proxy SSE endpoint returns 404 or 501, fall back to current polling
- `_runReconstruct()` checks response content-type
- If not SSE-compatible, start polling fallback
- **Deliverable**: Fallback logic in `_runReconstruct()` in `measurement-screen.js`

## Phase 54: Add proxy SSE health check
- `GET /api/v2/garment/health` returns `"sse_supported": true/false`
- Frontend checks before opening EventSource
- **Deliverable**: Updated health endpoint in `server.py`

## Phase 55: Add Kaggle-side SSE timeout/cleanup
- SSE connection idle timeout: 60s after last event
- Cleanup: remove event listeners, close resources
- Prevent memory leak from abandoned SSE connections
- **Deliverable**: SSE cleanup in `api_server.py`

## Phase 56: SSE event ordering guard
- Ensure events can't arrive out of order (segmenting after meshing)
- Add sequence number to each event
- Frontend ignores events with sequence < last received
- **Deliverable**: Sequence guard in both `api_server.py` and `measurement-screen.js`

## Phase 57: Add progress to Supabase garment_jobs
- Add `progress` column (integer 0-100)
- Add `progress_message` column (string)
- Kaggle proxy updates these via PATCH after each SSE event
- Frontend can reconnect and see last progress on page refresh
- **Deliverable**: DB migration + proxy updates in `server.py`

## Phase 58: Add progress CSS responsive behavior
- On mobile: progress bar full-width, step icons smaller
- On desktop: progress bar with step labels below
- **Deliverable**: Responsive CSS in `measurement-screen.css`

## Phase 59: QA — test SSE flow end-to-end
- Start reconstruction, confirm all 6 progress events arrive
- Test SSE reconnection (kill tunnel mid-stream)
- Test fallback (return 404 from SSE endpoint, confirm polling kicks in)
- Test out-of-order events (force wrong sequence, confirm guard works)
- **Deliverable**: QA verification checklist passed

---

# Track D — Inline 3D Preview in Three.js Viewport (Phases 60–79)

## Phase 60: Design 3D preview placement in reconstruct view
- After success, show embedded Three.js canvas below success message
- 400px × 500px container with dark background
- Orbit controls: rotate, pan, zoom
- Auto-rotate enabled by default, disabled on user interaction
- **Deliverable**: Layout mockup in this document

## Phase 61: Add 3D container to `buildReconstructView()` results section
- `<div class="ms-recon-3d-container" id="ms-recon-3d-container" style="display:none">`
- Child: `<canvas id="ms-recon-3d-canvas"></canvas>`
- **Deliverable**: Updated HTML template in `measurement-screen.js`

## Phase 62: Extract OBJs from ZIP in frontend without downloading
- Use `JSZip` library to read ZIP contents in browser
- Extract `mesh_upper.obj`, `mesh_lower.obj` text
- Create blob URLs for Three.js loader
- **Deliverable**: ZIP parsing in `_runReconstruct()` in `measurement-screen.js`

## Phase 63: Add JSZip dependency
- Add `<script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js">` to page
- Or bundle with existing JS build
- **Deliverable**: JSZip loaded in HTML

## Phase 64: Create `_renderReconMesh(zip)` method
- Uses `JSZip.loadAsync(res.blob())` to read ZIP
- Finds `mesh_upper.obj` and `mesh_lower.obj`
- Passes to `loadGarment()` from korra_viz.js
- **Deliverable**: New method on KORRA_MS in `measurement-screen.js`

## Phase 65: Create `_initReconViewer(containerId)` method
- Creates new Three.js scene, camera, renderer
- Same style as main korra_viz.js viewport
- Dark background (0x1a1a1a), ambient + directional lighting
- OrbitControls for interaction
- **Deliverable**: New method on KORRA_MS in `measurement-screen.js`

## Phase 66: Add `loadGarmentFromOBJ(objText, color)` to korra_viz.js
- Currently `loadGarment()` expects a URL
- New overload: `loadGarmentFromOBJ(objText, color)` accepts raw OBJ string
- Uses `THREE.OBJLoader().parse(objText)` internally
- Returns Three.js Group
- **Deliverable**: Updated `korra_viz.js`

## Phase 67: Add garment mesh coloring by type
- Upper mesh: light blue (#4A90D9) with semi-transparency
- Lower mesh: dark blue (#2C5F8A) with semi-transparency
- If only one mesh, use teal (#1DBFAF)
- Store materials for toggling visibility
- **Deliverable**: Mesh coloring in `_renderReconMesh()` in `measurement-screen.js`

## Phase 68: Add wireframe overlay toggle
- Small button overlay: "Show Wireframe"
- Toggles between solid render and wireframe render
- Helps inspect mesh topology
- **Deliverable**: Wireframe toggle in `measurement-screen.js`

## Phase 69: Add mesh statistics display
- Below 3D container: vertex count, face count
- "Upper: 2,450 verts / 4,896 faces"
- "Lower: 1,820 verts / 3,636 faces"
- **Deliverable**: Stats display in `buildReconstructView()` in `measurement-screen.js`

## Phase 70: Add fullscreen toggle for 3D preview
- Button in top-right of 3D container
- Expands to fill viewport (overlay, z-index 3000)
- Close button (×) returns to normal size
- **Deliverable**: Fullscreen toggle in `measurement-screen.js`

## Phase 71: Add auto-rotate with toggle
- Auto-rotate at 0.5 rad/s when idle (no user interaction for 3s)
- OrbitalControls.autoRotate = true
- Toggle button: "Auto-Rotate: On/Off"
- **Deliverable**: Auto-rotate in `_initReconViewer()` in `measurement-screen.js`

## Phase 72: Add screenshot capture button
- Button: "Capture Screenshot"
- Uses `renderer.domElement.toDataURL()`
- Triggers download of PNG file
- **Deliverable**: Screenshot in `measurement-screen.js`

## Phase 73: Handle missing mesh parts gracefully
- If ZIP has only `mesh_upper.obj` (no lower): show upper only, display note
- If ZIP has only `mesh_lower.obj` (no upper): show lower only, display note
- If ZIP has neither: hide 3D container, show note "No 3D mesh in result"
- **Deliverable**: Graceful handling in `_renderReconMesh()` in `measurement-screen.js`

## Phase 74: Add loading state for OBJ parsing
- While JSZip extracts + Three.js parses: show skeleton/spinner overlay on canvas
- "Loading 3D mesh..." overlay text
- Dismissed once mesh is rendered
- **Deliverable**: Loading overlay in `_renderReconMesh()` in `measurement-screen.js`

## Phase 75: Wire up "Use in Virtual Try-On" button
- Currently: just switches view, doesn't pass reconstructed mesh
- New: store reconstructed mesh data on `KORRA_MS._reconMeshData`
- On click: switch to try-on view, call `_updateGarmentForContext()` with stored mesh data
- **Deliverable**: Updated button handler in `_runReconstruct()` in `measurement-screen.js`

## Phase 76: Add CSS for 3D container responsive behavior
- Mobile: 100% width × 300px height
- Desktop: max-width: 400px × 500px height
- Dark background, rounded corners, subtle border
- **Deliverable**: CSS rules in `measurement-screen.css`

## Phase 77: Add memory cleanup for Three.js resources
- When navigating away from reconstruct view: dispose of geometries, materials, textures, renderer
- `renderer.dispose()`, `geometry.dispose()`, `material.dispose()`
- Prevent GPU memory leak
- **Deliverable**: Cleanup in `switchView()` in `measurement-screen.js`

## Phase 78: Add object picking — click on mesh to show face/vertex info
- Raycaster on click: show face normal, vertex index on hover
- Debug info overlay (small, fade-out after 3s)
- Useful for garment fit analysis
- **Deliverable**: Click picking in `measurement-screen.js`

## Phase 79: QA — test 3D preview end-to-end
- Test with both upper+lower mesh ZIP
- Test with upper-only ZIP (one-piece garment)
- Test with corrupt ZIP (no mesh files)
- Test memory: navigate in/out of reconstruct view 10x, check for leaks
- **Deliverable**: QA verification checklist passed

---

# Track E — Auto-Load Reconstructed Mesh into Virtual Try-On (Phases 80–89)

## Phase 80: Design try-on integration flow
- User reconstructs garment → sees 3D preview → clicks "Use in Virtual Try-On"
- OR: User clicks "Use in Virtual Try-On" → reconstruct view switches to try-on view
- Try-on view loads the reconstructed mesh draped onto the user's body scan
- **Deliverable**: Integration flow spec in this document

## Phase 81: Store reconstructed mesh data on KORRA_MS instance
- `_reconMeshData = { upper: OBJText, lower: OBJText, pattern: JSON, zipBlob: Blob }`
- Set after successful ZIP parse in `_runReconstruct()`
- Cleared when new upload starts or view is destroyed
- **Deliverable**: Data storage in `measurement-screen.js`

## Phase 82: Create `_loadReconMeshIntoTryon()` method
- Called when "Use in Virtual Try-On" is clicked
- Reads `_reconMeshData`
- Calls `_updateGarmentForContext()` with mesh data
- Switches view to 'tryon'
- **Deliverable**: New method on KORRA_MS in `measurement-screen.js`

## Phase 83: Update `_updateGarmentForContext()` to accept OBJ text
- Current: calls `POST /measurements/{scan_id}/garment/drape` (TailorNet)
- New overload: if `reconMeshData` present, skip TailorNet, use reconstructed mesh directly
- Creates Three.js mesh from OBJ text
- Positions and scales it over the body scan
- **Deliverable**: Updated `_updateGarmentForContext()` in `measurement-screen.js`

## Phase 84: Add scaling transformation for reconstructed mesh
- Reconstructed mesh is in arbitrary scale (relative to image)
- Need to scale to match body scan proportions
- Auto-scale: fit mesh height to torso height of body scan
- Add manual scale slider: 0.5x – 2.0x
- **Deliverable**: Scaling logic in `measurement-screen.js`

## Phase 85: Add positioning controls for reconstructed garment
- Manual offset: X (left/right), Y (up/down), Z (forward/backward)
- Drag sliders or arrow buttons
- "Auto-Fit" button attempts to align based on bounding box
- **Deliverable**: Positioning controls in `measurement-screen.js`

## Phase 86: Add opacity/blend mode control
- Slider: garment opacity 0%–100%
- Blend modes: normal, multiply, screen
- Helps see body scan through garment for fit check
- **Deliverable**: Opacity control in `measurement-screen.js`

## Phase 87: Save reconstructed garment to scan
- Button: "Save Garment to This Scan"
- Stores mesh + pattern in Supabase storage
- Links garment_mesh_url and garment_pattern_url to scan record
- **Deliverable**: Save functionality in `measurement-screen.js`

## Phase 88: Load saved reconstructed garment on revisit
- If scan has saved reconstructed garment, show "Load Saved Garment" button
- Loads mesh from Supabase storage URL
- No need to re-reconstruct
- **Deliverable**: Load-from-storage in `measurement-screen.js`

## Phase 89: QA — test try-on integration
- Reconstruct garment → click "Use in Virtual Try-On" → verify it loads on body
- Test scaling slider adjusts mesh size
- Test opacity slider shows/hides mesh
- Test save → reload → verify persistence
- **Deliverable**: QA verification checklist passed

---

# Track F — Polish, Testing, Edge Cases (Phases 90–99)

## Phase 90: Add keyboard shortcuts for reconstruct view
- `Esc`: Go back to previous view
- `Enter` (when file selected): Trigger reconstruct
- `Ctrl+S` (when complete): Download ZIP
- **Deliverable**: Keyboard handler in `measurement-screen.js`

## Phase 91: Add drag-and-drop file upload
- Currently: only `[ Choose Image ]` button triggers file dialog
- Add: drag-drop zone over preview box
- `dragover`/`dragleave` visual feedback (highlight border)
- `drop` handler calls same `_initReconstruct()` onchange
- **Deliverable**: Drag-drop in `measurement-screen.js`

## Phase 92: Add loading skeleton for initial view
- Before view is fully rendered: show skeleton placeholder
- Gray pulsing rectangles matching layout
- Dismissed when `buildReconstructView()` completes
- **Deliverable**: Skeleton CSS + JS in `measurement-screen.js`/`.css`

## Phase 93: Add "Reconstruct from camera" option
- Button: "Take Photo" (mobile only)
- Uses `navigator.mediaDevices.getUserMedia()`
- Opens native camera, captures photo, uses as input
- **Deliverable**: Camera capture in `measurement-screen.js`

## Phase 94: Add history of recent reconstructions
- Store last 5 reconstructions in `localStorage`
- Each entry: timestamp, image preview (dataURL), mesh data keys
- Show "Recent Reconstructions" below upload area
- Click to reload previous result
- **Deliverable**: History in `measurement-screen.js`

## Phase 95: Add garment type selection before reconstruct
- Dropdown: "What type of garment?"
- Options: T-shirt, Shirt, Dress, Jacket, Pants, Skirt, Unknown
- Passes `garment_type` to API for model hint
- Default: "Unknown" (general pipeline)
- **Deliverable**: Garment type selector in `buildReconstructView()` in `measurement-screen.js`

## Phase 96: Add AR preview mode (mobile)
- "View in AR" button (mobile ARCore/ARKit capable devices)
- Uses `<model-viewer>` or WebXR
- Shows reconstructed mesh in real-world camera view
- **Deliverable**: AR mode in `measurement-screen.js`

## Phase 97: Add garment measurement display
- Parse `sewing_pattern.json` for measurements
- Display: Chest, Waist, Hip, Length, Sleeve Length
- Show in cm/inches toggle (reuse `.ms-unit-toggle`)
- Compare with user's body measurements from scan
- **Deliverable**: Measurement display in `measurement-screen.js`

## Phase 98: Add share reconstruction result
- Social share: "Check out this garment I reconstructed!"
- Share screenshot of 3D preview + measurements
- Generates shareable image (canvas toDataURL)
- **Deliverable**: Share functionality in `measurement-screen.js`

## Phase 99: Full regression test suite
- Test all 7 original gaps are closed
- Test flow: idle → file selected → reconstruct → progress → 3D preview → try-on
- Test error paths: validation, auth, server, timeout, network
- Test responsive: mobile (375×667), tablet (768×1024), desktop (1440×900)
- Test browser: Chrome, Firefox, Safari, Edge
- **Deliverable**: Complete QA verification checklist

---

# Appendix: Dependency Graph

```
Phase 0-19 (Track A: CSS) ──────► Phase 20-39 (Track B: Errors)
                                      │
                                      ▼
                               Phase 40-59 (Track C: SSE Progress)
                                      │
                                      ▼
                               Phase 60-79 (Track D: 3D Preview)
                                      │
                                      ▼
                               Phase 80-89 (Track E: Try-On Integration)
                                      │
                                      ▼
                               Phase 90-99 (Track F: Polish)
```

- **Track A** is a prerequisite for all other tracks (clean CSS foundation).
- **Track B** (inline errors) is independent but should come before Track C (so errors have proper UI).
- **Track C** (SSE progress) is independent of Track D/E but improves UX before 3D preview lands.
- **Track D** (3D preview) must come before Track E (try-on integration).
- **Track F** (polish) should come last as it builds on everything else.

# Appendix: File Change Summary

| File | Tracks | Estimated Changes |
|------|--------|-------------------|
| `measurement-screen.css` | A, B, C, D, F | +400 lines CSS |
| `measurement-screen.js` | A, B, C, D, E, F | +800 lines JS |
| `korra_viz.js` | D | +60 lines JS |
| `api_server.py` | C | +80 lines Python |
| `server.py` | C | +60 lines Python |
| SQL migration | C | +2 columns |

# Appendix: Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| JSZip adds 300KB to bundle | Low | Low | Load from CDN, not bundle |
| SSE connection consumes Kaggle resources | Medium | Low | 60s idle timeout, cleanup hooks |
| 3D preview leaks GPU memory | Medium | Medium | Phase 77 memory cleanup |
| Drag-and-drop doesn't work on Safari | Low | Medium | Feature detection, fallback to button |
| AR preview requires WebXR | Medium | Low | Feature detection, graceful hide |
| Try-on integration mismatches garment/body scale | Medium | Medium | Auto-scale + manual slider |
