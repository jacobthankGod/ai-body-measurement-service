# Implementation Plan: Camera UI Overhaul & Side Profile Audit

## Current State Analysis

After fetching latest GitHub code, here's what's in place:

### Frontend (share.html):
✅ Already implemented:
- Vibrant Mint (#57D7C0) for accurate pose
- Pure White (#FFFFFF) for inaccurate pose  
- 6px/4px lineWidth (sleeker lines)
- No glow (shadowBlur: 0)

❌ Missing features:
- Joint nodes (circles at keypoints)
- Autonomous capture (auto-snap when pose is correct)
- A-Pose validation only checking one arm (needs dual-arm check)

### Backend:
- No dual image processing (side image is uploaded but ignored)
- Only processes front image currently

---

## Plan

### Phase 1: Frontend UI Enhancements

1. **Add Joint Nodes:**
   - Draw circles at each keypoint (shoulders, elbows, wrists, hips, knees, ankles)
   - 8px radius for accurate, 6px for inaccurate

2. **Improve A-Pose Algorithm:**
   - Check BOTH arms must be away from body (not just one)

3. **Add Autonomous Capture:**
   - Auto-snap photo after 1.5 seconds of holding correct A-pose
   - Add visual countdown

4. **Verify Front Camera:**
   - Ensure facingMode: 'user' is set

### Phase 2: Side Profile Technical Audit

1. **Audit Side Image Usage:**
   - Check if side image is passed to HMR engine
   - If not, implement dual image processing

2. **Measurement Enhancement:**
   - Fuse front + side measurements for better accuracy

---

## Files to Edit:
- share.html (frontend)
- api/services/extract_measurements.py (backend)
- api/services/hmr_subprocess.py (subprocess)
- api/routes/measurements.py (API route)

## Follow-up Steps:
- Test camera capture
- Verify side profile accuracy
