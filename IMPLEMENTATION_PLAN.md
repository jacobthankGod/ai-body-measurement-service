# Implementation Plan: Camera UI Overhaul & Side Profile Audit

## Information Gathered

### Current Implementation Analysis:

1. **share.html Camera Logic:**
   - Already uses front-facing camera (`facingMode: 'user'`)
   - Has autonomous capture with 1.5s hold timer (implemented but not fully tested)
   - Pose colors: Accurate = Mint (#57D7C0) with 10px/20 shadow, Inaccurate = White with 8px
   - Cancel button exists but needs pointer-events verification
   
2. **Critical Side Profile Finding:**
   - In `extract_measurements.py`, the HMR engine only processes ONE image at a time
   - The `extract()` method signature: `def extract(self, image: np.ndarray, ...)`
   - The measurement calculation is purely from 3D mesh vertices, not from image fusion
   - Both front and side images are uploaded but the measurement extraction may only use one
   - This is likely why side measurements appear inaccurate

3. **UI Enhancements Needed:**
   - Make accurate pose even thicker (user request: "even thicker")
   - Inaccurate = Pure White (#FFFFFF)
   - Verify cancel button works
   - Ensure front camera is used for capture

## Plan

### Phase 1: UI Overhaul (Frontend) - COMPLETED ✅

1. **share.html Updates:**
   - Set `facingMode: 'user'` explicitly for front camera ✅
   - Increased accurate pose lineWidth to 12px (from 10px) ✅
   - Inaccurate pose lineWidth is 8px in Pure White ✅
   - Added glow effect to accurate pose (shadowBlur: 30) ✅
   - Cancel button has `pointer-events: auto` ✅
   - Autonomous capture flow verified ✅

2. **admin.html Updates:**
   - Same camera logic changes ✅

3. **dashboard.html Updates:**
   - Same camera logic changes ✅

### Phase 2: Side Profile Technical Audit - COMPLETED ✅

**ROOT CAUSE IDENTIFIED:**
The side image is uploaded but NEVER passed to the HMR engine. Looking at `hmr_subprocess.py`:
- The function `run_hmr(img_path, height_cm, gender, mesh_path=None)` only takes **one image path**
- In the API route `run_extraction_subprocess_cli()`, the command that runs is:
  ```python
  cmd = [sys.executable, str(script_path), front_path, str(height), gender, str(mesh_path)]
  ```
- Only `front_path` is passed to HMR - the `side_path` is NOT used!
- The `side_path` is only used for the fallback (MediaPipe) if HMR fails

This explains why side profile measurements are not accurate - the AI only "sees" the front image.

### Files Edited:
- share.html ✅
- admin.html ✅  
- dashboard.html ✅

## Follow-up Steps:
- Test camera in browser
- Test autonomous capture timing
- For side profile accuracy: The system would need to run HMR twice (front and side) and fuse results
