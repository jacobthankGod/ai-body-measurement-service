# Homepage AR Try-On: Specialized Implementation Plan

## Executive Summary

Add a **"Try On"** button to each garment in the homepage 3D gallery. When clicked, the user's phone camera opens, their body is tracked in real-time, and the selected garment is anchored to their body in augmented reality. No app install required — runs entirely in the mobile browser.

**Scope**: 8 existing gallery garments (beige suit, floral dress, white shirt, medieval cloth, men jacket, gold dress, black suit, turtleneck) → camera AR try-on → capture/share.

**Target**: Mobile web (iOS Safari + Android Chrome), 30fps, <5s total load (camera + body tracking + garment), zero backend changes.

**Total Phases**: 116 (implementation + testing + deployment, no beta/marketing/iteration phases)

---

## Architecture

```
Gallery "Try On" button click
  → Fullscreen camera overlay opens
  → 8th Wall SLAM initializes (world tracking)
  → MediaPipe Pose starts (body keypoint detection)
  → SMPL body model fits to keypoints
  → Garment GLB binds to SMPL body
  → Three.js renders garment over camera feed
  → User sees themselves wearing the garment
  → Capture photo / share / close
```

---

## Phase 1-15: Camera Overlay & Permissions

### Phase 1: Try-On Button on Gallery Items
- Add "Try On" button below each gallery label
- Style: `btn btn-primary`, small, centered under garment name
- Button text: "Try On" with camera icon
- Click handler: opens AR try-on overlay (not navigation)

### Phase 2: Fullscreen Camera Overlay
- Create `<div id="arTryOnOverlay">` covering full viewport
- Contains: `<video>` element (camera feed), `<canvas>` (Three.js), UI controls
- CSS: `position:fixed; inset:0; z-index:9999; background:#000`
- Smooth entry: opacity transition 0→1 over 300ms

### Phase 3: Camera Permission Request
- On overlay open: request camera via `navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } } })`
- Pipe stream to `<video>` element
- If denied: show "Camera access needed" message with "Open Settings" button
- If unsupported: show "AR not supported on this device" message

### Phase 4: Camera Feed Display
- `<video>` element fills overlay, `object-fit: cover`
- Mirror on front camera (`transform: scaleX(-1)`)
- Auto-rotate on device orientation change
- Handle iOS safe area (notch, home indicator)

### Phase 5: Close Button
- Top-left: X button to close overlay
- Top-right: camera switch button (front/back)
- Bottom: capture button (large, centered)
- Dismiss: click X or swipe down

### Phase 6: Loading State
- Show "Initializing camera..." with spinner
- Show "Detecting body..." once camera ready
- Show skeleton overlay when body detected (green lines)
- Hide skeleton after 3 seconds (clean view)

### Phase 7: 8th Wall Engine Initialization
- Load 8th Wall XR Engine binary (`xrengine.js`)
- Initialize SLAM on camera start
- Configure: world effects enabled, face effects disabled
- Target: SLAM ready in <2 seconds

### Phase 8: 8th Wall Camera Sync
- Read 8th Wall camera pose each frame
- Apply to Three.js camera (position + quaternion)
- Virtual objects stay anchored to real world
- Camera feed renders as background (alpha: 0)

### Phase 9: Three.js Scene Setup (AR)
- `WebGLRenderer` with `alpha: true`, `antialias: true`
- `PerspectiveCamera` synced to 8th Wall camera
- Scene background: null (camera feed shows through)
- Lighting: hemisphere light + ambient light + 3 directional

### Phase 10: MediaPipe Pose Initialization
- Load `@mediapipe/pose` (CDN or bundled)
- Configure: `modelComplexity: 1` (balanced), `minDetectionConfidence: 0.6`, `minTrackingConfidence: 0.5`
- Pipe camera feed from `<video>` to MediaPipe
- Output: 33 body landmarks per frame

### Phase 11: Body Keypoint Extraction
- Extract 33 landmarks from MediaPipe output
- Convert normalized coords to 3D positions using camera intrinsics
- Key joints: shoulders, elbows, wrists, hips, knees, ankles, neck, nose
- Smooth over 5 frames (Kalman filter) to reduce jitter

### Phase 12: SMPL Body Model Loading
- Load SMPL model (`smpl_male.npz` or `smpl_female.npz`) — detect gender from user's KORRA scan or default to male
- Create `SMPLBody` class: `body_model(pose, shape)` → vertices + joints
- Initialize: T-pose (`theta = zeros(72)`, `beta = zeros(10)`)
- Load once, reuse across sessions

### Phase 13: SMPL Pose Fitting
- Fit SMPL joints to MediaPipe keypoints
- Rigid transform alignment (rotation + translation)
- L-BFGS-B optimization: `||SMPL_joints - MP_joints||^2 + lambda * ||theta||^2`
- Convergence: <10 iterations, <5ms on mobile

### Phase 14: SMPL Shape Estimation
- If user has KORRA scan: use stored beta values
- If no scan: estimate from body proportions
  - Shoulder width → beta[0]
  - Torso length → beta[1]
  - Limb ratios → beta[2-5]
  - Weight estimate → beta[6-9]
- Store in session localStorage

### Phase 15: Body Mesh Rendering (Debug)
- Render fitted SMPL mesh as wireframe (debug mode toggle)
- Verify: body tracks user movement, correct size relative to environment
- Debug button: top-right corner, hidden in production
- Use for development validation only

---

## Phase 16-30: Garment Binding & Rendering

### Phase 16: Garment GLB Loading
- On "Try On" click: load selected garment's GLB file
- Use existing GLBs from `/assets/` (beige_business_suit.glb, floral_dress.glb, etc.)
- `GLTFLoader` with DRACOLoader (already configured)
- Show progress: "Loading garment... 40%"
- Target: <2 seconds for largest GLB (24MB black suit)

### Phase 17: Garment-SMPL Binding
- Each garment needs a binding file (JSON): vertex-to-SMPL correspondence
- Map garment vertices to nearest SMPL triangles
- Compute skinning weights per vertex (which SMPL joints affect it)
- Store binding in `garment_name_binding.json` sidecar

### Phase 18: Initial Binding (Rigid)
- MVP: bind garment rigidly to SMPL body
- Each garment vertex = offset from nearest SMPL vertex
- Garment follows body pose without cloth simulation
- Visual: garment looks "painted on" but tracks correctly
- Ship this first, iterate to cloth sim later

### Phase 19: Garment Scale Matching
- Scale garment to fit user's estimated body size
- Use SMPL beta params to determine body dimensions
- Scale garment uniformly: `model.scale.setScalar(bodyScale / garmentOriginalScale)`
- Ensure garment envelops body mesh (no clipping)

### Phase 20: Garment Positioning
- Center garment on SMPL body center of mass
- Align garment shoulders to SMPL shoulders
- Align garment hips to SMPL hips
- Y-offset: garment bottom should align with SMPL mid-thigh (for tops)

### Phase 21: Garment Rotation
- Match garment rotation to SMPL body rotation
- Use SMPL root joint orientation
- Prevent: garment facing wrong direction when user turns
- Smooth rotation tracking (quaternion slerp)

### Phase 22: Three.js Garment Rendering
- Add garment `Mesh` to AR scene
- Apply PBR materials from GLB (albedo, normal, roughness)
- Force opaque: `material.transparent = false; material.opacity = 1.0`
- Double-sided: `material.side = THREE.DoubleSide`

### Phase 23: Garment Lighting
- Hemisphere light (intensity 0.6) — ambient fill
- 3 directional lights matching camera direction
- Light intensity adjusted by 8th Wall light estimation
- Prevent garment from looking "flat" in dark rooms

### Phase 24: Garment Shadow (Optional)
- Garment casts shadow onto SMPL body (if body mesh visible)
- Shadow map: 1024×1024 resolution
- Soft shadow (PCF filtering)
- Enhances depth perception

### Phase 25: Multi-Garment Layering
- Support top + bottom simultaneously (if user selects both)
- Render order: body → inner garment → outer garment
- Z-fighting prevention: offset each layer by 0.001
- Each garment has independent binding to SMPL

### Phase 26: Garment Swap
- User can switch garments while in AR view
- Bottom panel: horizontal carousel of 8 garments
- Tap new garment → dispose old → load new → bind → render
- Transition: cross-fade over 200ms

### Phase 27: Garment Removal
- "Remove" button to clear current garment
- Dispose geometry, material, textures (WebGL memory cleanup)
- Return to body-only mode (camera + tracked body, no garment)
- Smooth fade-out animation (opacity 1→0 over 300ms)

### Phase 28: Garment Color Variants
- Each garment supports 2-3 color variants
- Swap texture maps without reloading geometry
- UI: color swatches below garment name
- Pre-computed color variants per garment

### Phase 29: Front/Back View
- Detect body facing direction from MediaPipe landmarks
- Flip garment when user turns 180°
- Smooth transition: garment cross-fades between front/back
- Handle: user turns around to show back of garment

### Phase 30: Garment Fit Indicator
- Show real-time fit quality overlay
- Green: "Good fit" (garment-body distance in range)
- Yellow: "Slightly tight" (garment clips body)
- Red: "Too small" (significant clipping)
- Based on vertex distance between garment and SMPL mesh

---

## Phase 31-50: Cloth Simulation (Enhanced Realism)

### Phase 31: Verlet Cloth Simulation
- Initialize cloth particles at garment vertex positions
- Connect with spring constraints (structural + shear + bending)
- 10 solver iterations per frame
- Time step: 1/60s

### Phase 32: Cloth-Body Collision
- SMPL mesh as collision body
- Detect cloth vertex penetration through SMPL triangles
- Push cloth outward along collision normal
- Offset: 2mm to prevent z-fighting

### Phase 33: Gravity & Forces
- Constant downward force: 9.81 m/s²
- Subtle wind: Perlin noise, 0.1 m/s²
- User interaction: swipe to push garment
- Centrifugal force during fast body rotation

### Phase 34: Fabric Presets per Garment
- **Beige suit jacket**: stiff, heavy (stiffness: 0.9, damping: 0.8)
- **Floral dress**: light, flowing (stiffness: 0.3, damping: 0.4)
- **White shirt**: medium (stiffness: 0.6, damping: 0.6)
- **Medieval cloth**: heavy, draped (stiffness: 0.7, damping: 0.7)
- **Men jacket**: stiff, structured (stiffness: 0.85, damping: 0.75)
- **Gold dress**: medium-heavy (stiffness: 0.5, damping: 0.5)
- **Black suit**: very stiff (stiffness: 0.95, damping: 0.85)
- **Turtleneck**: medium (stiffness: 0.55, damping: 0.55)

### Phase 35: Self-Collision
- Spatial hashing for O(n) neighbor detection
- Push apart if cloth vertices within 1cm of each other
- Prevent: dress folds clipping through itself
- Performance: skip for close-up views

### Phase 36: Cloth LOD
- Close (<1m): full resolution (100% particles)
- Medium (1-2m): 50% particles
- Far (>2m): 25% particles (rigid fallback)
- Seamless transition between LOD levels

### Phase 37: Cloth Pre-warming
- Pre-simulate 100 frames before showing to user
- Garment starts in natural drape state
- Prevents "falling" animation on load
- Show "Preparing garment..." during pre-warm

### Phase 38: Cloth Caching
- If body hasn't moved for 500ms: freeze simulation
- Resume when body moves
- Saves ~30% CPU during idle periods
- Automatic: no user action needed

### Phase 39: Cloth Interaction
- User can poke/swipe garment on screen
- Convert touch to 3D ray using camera
- Apply force to nearest cloth particles
- Fabric responds with realistic push/pull

### Phase 40: Cloth Performance Profiling
- Measure per-frame: simulation time, collision time, render time
- Target: <8ms total cloth pipeline
- Adaptive: reduce iterations if frame time >16ms
- Debug overlay in development only

---

## Phase 51-70: Body Tracking Refinement

### Phase 41: Temporal Smoothing
- Kalman filter on MediaPipe keypoints
- Smooth over 5 frames (83ms at 60fps)
- Shoulders/hips: low noise (stable)
- Wrists: higher noise (fast movement allowed)

### Phase 42: Latency Compensation
- MediaPipe inference: ~30ms
- 8th Wall SLAM: ~16ms
- Total pipeline: ~50ms
- Predict body pose 1 frame ahead using velocity

### Phase 43: Occlusion Handling
- Detect when body part is occluded (MediaPipe confidence <0.5)
- Extrapolate from last known position + velocity
- Increase regularization on occluded joints
- Visual: dim garment region when occluded

### Phase 44: Arm Pose Refinement
- Apply anatomical constraints (elbow can't bend backward)
- Use learned prior from KORRA dataset
- Smooth arm transitions during fast movement
- Fix: MediaPipe sometimes gives incorrect arm rotations

### Phase 45: Leg Tracking
- Hip-knee-ankle chain with IK solver
- Anchor: hip position (stable)
- Extend: knee angle from MediaPipe
- End: ankle position

### Phase 46: Head Tracking
- Use MediaPipe face mesh (468 landmarks) for head orientation
- Map to SMPL head joint rotation
- Garment collar follows head movement
- Optional: add headwear

### Phase 47: Body Scale Normalization
- Account for phone distance (selfie vs. arm's length)
- Use 8th Wall absolute scale or estimate from MediaPipe
- Normalize SMPL body to real-world scale
- Prevent: body too large/small in AR

### Phase 48: Standing vs. Sitting
- Detect posture from hip-knee angle
- Switch SMPL pose mode accordingly
- Adjust garment drape for sitting
- Pre-computed sitting poses

### Phase 49: Walking Motion
- Track body velocity from frame-to-frame changes
- Add subtle garment sway during walking
- Cloth simulation: add forward force
- Prevent garment from "floating"

### Phase 50: Camera Switch
- Support front (selfie) and rear camera
- Button: top-right corner
- On switch: reinitialize SLAM, re-detect body
- Seamless: garment persists across switch

---

## Phase 71-90: User Interface

### Phase 51: AR Overlay Layout
```
┌─────────────────────────────┐
│ [X]              [📷] [🔄] │  ← Close, Camera switch, Debug
│                             │
│                             │
│      ┌───────────────┐      │
│      │               │      │
│      │   CAMERA FEED │      │
│      │   + GARMENT   │      │
│      │               │      │
│      └───────────────┘      │
│                             │
│  "Beige Business Suit"      │  ← Garment name
│  ┌───┬───┬───┬───┬───┐     │
│  │ 👔│ 👗│ 👕│ ...│    │     │  ← Garment carousel
│  └───┴───┴───┴───┴───┘     │
│                             │
│      [  📸 Capture  ]      │  ← Capture button
│                             │
│  Size: M | Fit: ✓ Good     │  ← Size + fit info
└─────────────────────────────┘
```

### Phase 52: Garment Carousel
- Bottom of AR overlay: horizontal scroll of 8 garments
- Thumbnail (small GLB preview) + name
- Active garment: highlighted border (Mint color)
- Swipe left/right to browse
- Tap to select → dispose old, load new

### Phase 53: Capture Button
- Large circular button, bottom center
- Camera icon inside
- Tap: capture current frame (camera + garment overlay)
- Haptic feedback on capture
- Visual: flash animation (white flash 100ms)

### Phase 54: Capture Flow
- On capture: `renderer.domElement.toDataURL('image/png')`
- Overlay: preview with "Save" and "Share" buttons
- Save: download to device (trigger `<a download>`)
- Share: Web Share API (native share sheet)
- Close preview: return to AR view

### Phase 55: Share Sheet
- Native Web Share API on mobile
- Share options: WhatsApp, Instagram, Twitter, SMS, Copy Link
- Share link: `korra.style/ar?garment=beige_suit&photo=base64...`
- Fallback: copy image to clipboard

### Phase 56: Size Selection
- Show recommended size from KORRA scan (if available)
- Manual override: S / M / L / XL / XXL buttons
- Visual indicator: "Your size: M"
- Link: "Don't know your size? Take a scan →"

### Phase 57: Fit Feedback
- Real-time fit quality indicator
- Green badge: "Good fit" (garment-body distance 1-3cm)
- Yellow badge: "Slightly tight" (distance <1cm)
- Red badge: "Too small" (clipping detected)
- Updates every frame as body moves

### Phase 58: Tutorial Overlay (First Time)
- First AR session: animated tutorial
- Step 1: "Point camera at your full body"
- Step 2: "Stand 2-3 meters away"
- Step 3: "Swipe to browse, tap to try"
- Step 4: "Tap capture to save"
- Dismiss: "Got it!" button
- Store flag in localStorage (show once)

### Phase 59: Error States
- "Camera denied" → "Enable camera in Settings" + deep link
- "Body not detected" → "Stand back, make sure you're visible"
- "Garment failed to load" → "Tap to retry"
- "Low light" → "Turn on room lights"
- "Unsupported browser" → "Use Chrome or Safari"

### Phase 60: Loading States
- Camera init: "Starting camera..." with spinner
- Body detection: "Looking for your body..." with skeleton outline
- Garment loading: "Loading [garment name]..." with progress bar
- Cloth settling: "Preparing garment..." (1-2 seconds)

### Phase 61: Haptic Feedback
- Vibrate on: garment selection, capture, error
- Short pulse (50ms) for selection
- Double pulse (50ms + 50ms) for capture
- Triple pulse (50ms × 3) for error
- Non-intrusive, subtle

### Phase 62: Sound Effects (Optional)
- Subtle "whoosh" on garment load
- Camera shutter sound on capture
- Gentle alert on error
- Mute toggle in settings
- Off by default

### Phase 63: Dark Mode
- Auto-detect system preference
- Dark UI for AR overlay controls
- Garment lighting adjusts for dark environments
- Toggle in settings

### Phase 64: Accessibility
- VoiceOver/TalkBack: announce garment names, controls
- High contrast mode for buttons
- Large text mode
- Keyboard navigation (desktop fallback)

### Phase 65: Localization
- English, Spanish, French, Arabic, Portuguese
- RTL support for Arabic
- Date/number formatting per locale
- Currency for prices (if purchase flow added)

---

## Phase 91-110: Performance & Optimization

### Phase 66: Bundle Optimization
- Target: <3MB JavaScript (AR-specific code)
- Tree-shake Three.js (import only needed modules)
- Lazy-load MediaPipe (only when AR starts)
- Lazy-load 8th Wall (only when AR starts)
- Gzip: <1MB compressed

### Phase 67: GLB Optimization
- Draco compression for all 8 garments
- Max polygon: 50K triangles per garment
- Max texture: 2048×2048
- WebP format for textures
- Pre-compressed on EC2, served from nginx

### Phase 68: Memory Management
- Target: <150MB peak memory
- Dispose: `geometry.dispose()`, `material.dispose()`, `texture.dispose()`
- Pool: reuse renderers, cameras across sessions
- Monitor: `renderer.info.memory` per frame

### Phase 69: Frame Rate Monitoring
- Track FPS over time
- If <24fps for 3 seconds: reduce quality
- Adaptive: reduce cloth iterations, texture quality
- Log performance data for analysis

### Phase 70: CPU Profiling
- Target: <10ms per frame on mid-range phone
- Breakdown: SMPL (3ms) + Cloth (3ms) + Render (2ms) + Buffer (2ms)
- Chrome DevTools profiling sessions
- Optimize hot paths

### Phase 71: GPU Profiling
- Target: <3ms GPU per frame
- Monitor draw calls (target: <30)
- Monitor texture bandwidth
- Reduce: instancing, batching, LOD

### Phase 72: Web Workers
- Move SMPL computation to Web Worker
- Move cloth simulation to Web Worker
- Main thread: only rendering + camera
- Reduces main thread blocking

### Phase 73: Adaptive Quality
- High-end (iPhone 12+, flagship Android): full quality
- Mid-range (iPhone X, Pixel 3): medium quality
- Low-end (older devices): low quality (rigid binding, no cloth)
- Auto-detect at startup

### Phase 74: Battery Optimization
- Monitor: `navigator.getBattery()`
- Low battery (<20%): reduce quality
- Very low (<10%): pause AR, show static preview
- Warn user: "AR uses significant battery"

### Phase 75: Thermal Management
- If device throttles: reduce quality immediately
- Pause non-essential computation
- Resume when temperature normalizes
- Detect via frame rate drops

### Phase 76: Caching Strategy
- Cache GLB files in IndexedDB (offline support)
- Preload next garment while user views current
- Service Worker for static assets
- Stale-while-revalidate for garment metadata

### Phase 77: Lazy Loading
- 8th Wall engine: load on "Try On" click (not at page load)
- MediaPipe: load on AR overlay open
- SMPL model: load on first try-on
- Reduces initial page load by ~2MB

### Phase 78: Code Splitting
- Split: AR core, MediaPipe, SMPL, UI, cloth sim
- Load chunks on demand via dynamic imports
- AR-specific bundle loaded only when needed
- Reduces main bundle by ~60%

### Phase 79: Preloading
- Preload 8th Wall binary on gallery hover (if desktop)
- Preload MediaPipe WASM on "Try On" click
- Preload SMPL model on first try-on
- Use `<link rel="preload">` for critical resources

### Phase 80: Performance Budget
- Total frame budget: 16.6ms (60fps)
- 8th Wall SLAM: ~3ms
- MediaPipe Pose: ~4ms
- SMPL forward: ~3ms
- Cloth simulation: ~3ms (or 0ms if rigid)
- Three.js render: ~2ms
- Buffer: ~1.6ms

---

## Phase 111-130: Deployment & Integration

### Phase 81: No Backend Changes Required
- AR try-on runs entirely client-side
- GLB files served from existing nginx (`/assets/`)
- SMPL model loaded from `/assets/` or CDN
- No new API endpoints needed
- No database changes

### Phase 82: EC2 Deployment
- Upload AR-specific JS/CSS to `/app/public/assets/`
- GLB files already on EC2 (no change)
- SMPL model files: upload to `/app/public/assets/smpl/`
- 8th Wall binary: upload to `/app/public/assets/8thwall/`

### Phase 83: Nginx Configuration
- Add cache headers for AR assets:
  ```nginx
  location /assets/8thwall/ {
      add_header Cache-Control "public, max-age=31536000, immutable";
  }
  location /assets/smpl/ {
      add_header Cache-Control "public, max-age=31536000, immutable";
  }
  ```
- Gzip: enable for JS/CSS
- Brotli: enable if available
- HTTP/2: already enabled

### Phase 84: HTTPS Requirement
- 8th Wall requires HTTPS for camera access
- Already configured: EC2 has SSL via Let's Encrypt
- Domain: `korra.style` (already HTTPS)
- No additional SSL setup needed

### Phase 85: Browser Compatibility
- iOS Safari 15+: full support
- Android Chrome 90+: full support
- Samsung Internet: partial (test)
- Desktop browsers: show "Open on your phone" message
- Fallback: 2D try-on (photo-based, no AR)

### Phase 86: Device Testing Matrix
| Device | Browser | Expected |
|--------|---------|----------|
| iPhone 14+ | Safari 16+ | Full quality, 60fps |
| iPhone 12-13 | Safari 15+ | Full quality, 45-60fps |
| iPhone X-11 | Safari 15+ | Medium quality, 30-45fps |
| Samsung S21+ | Chrome 100+ | Full quality, 60fps |
| Samsung S10 | Chrome 90+ | Medium quality, 30-45fps |
| Pixel 6+ | Chrome 100+ | Full quality, 60fps |
| Pixel 3-5 | Chrome 90+ | Medium quality, 30-45fps |
| Desktop | Chrome/Firefox | "Open on phone" message |

### Phase 87: Error Monitoring
- Console.error logging for AR-specific errors
- Track: SLAM failures, MediaPipe crashes, WebGL errors
- Sentry integration (if already configured)
- Alert on: >5% error rate per device

### Phase 88: Analytics Events
- `ar_tryon_opened` — user clicked "Try On"
- `ar_camera_allowed` — camera permission granted
- `ar_body_detected` — first body tracking success
- `ar_garment_loaded` — garment GLB loaded successfully
- `ar_captured` — user took photo
- `ar_shared` — user shared photo
- `ar_closed` — user closed AR overlay

### Phase 89: A/B Testing
- Test: cloth simulation ON vs. rigid binding
- Test: carousel position (bottom vs. side)
- Test: capture button size/placement
- Test: tutorial shown vs. skipped
- Metrics: capture rate, share rate, session duration

### Phase 90: User Feedback
- In-AR feedback button (small, top-right)
- "Rate your experience" (1-5 stars)
- "Report issue" with screenshot
- Feedback → Slack channel

---

## Phase 131-150: Polish & Edge Cases

### Phase 91: Graceful Degradation
- If 8th Wall fails: fallback to no-SLAM AR (garment floats, doesn't track world)
- If MediaPipe fails: fallback to static garment on screen center
- If WebGL fails: fallback to 2D photo try-on
- Always show something, never a blank screen

### Phase 92: Memory Leak Prevention
- Dispose all resources on overlay close
- Dispose: renderer, scene, geometries, materials, textures
- Dispose: MediaPipe instance, 8th Wall instance
- Verify: no WebGL context leaks across sessions
- Test: open/close AR 50 times, monitor memory

### Phase 93: Concurrent Session Prevention
- Only one AR session at a time
- If already running: ignore new "Try On" click
- Show: "Close current try-on first"
- Prevent: double-tap opening two overlays

### Phase 94: Orientation Change
- Handle device rotation (portrait ↔ landscape)
- Resize renderer to new dimensions
- Reinitialize camera with new aspect ratio
- Garment persists across rotation

### Phase 95: Background/Foreground
- When app goes to background: pause AR
- When app returns: resume AR
- Reinitialize SLAM (may have lost tracking)
- Re-detect body
- Seamless: garment reappears in correct position

### Phase 96: Network Failure
- If GLB loading fails: show cached version (if available)
- If no cache: show "Connect to internet to try on garments"
- Retry button on network error
- Graceful offline experience

### Phase 97: Low-End Device Handling
- Detect device capabilities at startup
- If <3GB RAM: skip cloth simulation (rigid only)
- If <2GB RAM: skip SMPL (simple 2D overlay)
- If <1GB RAM: show "Device not supported" message
- Never crash, always degrade gracefully

### Phase 98: iOS Safari Quirks
- Handle: `playsinline` attribute on video (required for iOS)
- Handle: fullscreen API differences
- Handle: safe area insets (notch, home indicator)
- Handle: permission prompt styling

### Phase 99: Android Chrome Quirks
- Handle: `autoplay` policy (user gesture required)
- Handle: pip (picture-in-picture) interference
- Handle: tab switching (pause/resume)
- Handle: notification permission for share

### Phase 100: Garment GLB Consistency
- All 8 garments must have consistent scale (meters)
- All garments must be in T-pose (matching SMPL)
- All garments must have PBR materials
- All garments must have Draco compression
- Validate: automated GLB checker script

---

## Phase 151-170: Future Enhancements (Post-MVP)

### Phase 101: Outfit Builder
- Select top + bottom + accessories simultaneously
- Layer garments correctly
- Save outfit as preset
- Share full outfit

### Phase 102: Social Features
- "Try this outfit" link → friend opens same garment
- Group try-on: multiple people try same outfit
- Comment/react on shared photos
- Leaderboard: most shared outfits

### Phase 103: Purchase Integration
- "Buy Now" button → checkout
- Size recommendation from body scan
- Price display on AR view
- Merchant revenue attribution

### Phase 104: Virtual Fitting Room
- Background removal: show only body + garment
- MediaPipe segmentation mask
- Replace background with virtual room
- "Fitting room" effect

### Phase 105: Body Measurement Overlay
- Show body measurements on AR view
- Chest, waist, hip, inseam
- Compare with garment size chart
- "This garment fits your 34" chest"

### Phase 106: AR Video Recording
- Record 5-second AR video
- `MediaRecorder` API on canvas stream
- Share video via Web Share API
- Save to device gallery

### Phase 107: Gesture Control
- Arms raised: show size info
- Hands on hips: rotate garment view
- Wave: dismiss overlay
- Avoid false positives

### Phase 108: Multi-Language
- English, Spanish, French, Arabic, Portuguese
- RTL support
- Localized garment names
- Localized UI strings

### Phase 109: Merchant Analytics
- Track: try-on count per garment
- Track: capture rate, share rate
- Track: conversion (try-on → purchase)
- Dashboard for merchants

### Phase 110: Advanced Cloth Simulation
- GPU cloth simulation (WebGPU)
- Fabric tearing (fun feature)
- Fabric wrinkling (procedural)
- Multi-layer collision

---

## Phase 171-200: Testing & Launch

### Phase 111: Unit Tests
- SMPL body model: forward pass, joint positions
- Cloth simulation: constraint solving, collision
- Body fitting: pose optimization, shape estimation
- Garment binding: vertex correspondence

### Phase 112: Integration Tests
- 8th Wall ↔ Three.js camera sync
- MediaPipe ↔ SMPL keypoint mapping
- Garment loading → binding → rendering pipeline
- Capture → share flow

### Phase 113: E2E Tests (Playwright)
- Open gallery → click "Try On" → camera opens
- Body detected → garment loads → renders correctly
- Capture photo → share → close overlay
- Error states: camera denied, body lost, garment fails

### Phase 114: Device Testing
- Physical testing on all target devices
- Performance benchmarking per device
- Memory leak detection (50 open/close cycles)
- Battery drain measurement (10-minute session)

### Phase 115: Performance Audit
- Lighthouse score: >90
- First Contentful Paint: <1.5s
- Largest Contentful Paint: <3s
- Cumulative Layout Shift: <0.1

### Phase 116: Security Audit
- Validate GLB files before loading
- Rate limit: 100 requests/min per user
- CORS: only allow korra.style origins
- CSP: strict content security policy

---

## Technical Stack (Minimal)

| Component | Technology | File Size |
|-----------|-----------|-----------|
| AR Engine | 8th Wall XR Engine (binary) | ~500KB |
| 3D Rendering | Three.js r152+ | ~600KB |
| Body Tracking | MediaPipe Pose | ~2MB (WASM) |
| Body Model | SMPL (npz) | ~10MB |
| Cloth Simulation | Custom Verlet (JS) | ~20KB |
| Garment GLBs | Existing 8 garments | 1-24MB each |
| Bundler | Vite | Dev only |
| Language | JavaScript (no TypeScript for MVP) | — |

**Total new code**: ~15KB JavaScript + CSS
**Total new assets**: ~12MB (SMPL model + 8th Wall binary + MediaPipe WASM)
**Total page load impact**: ~0KB (all lazy-loaded on "Try On" click)

---

## Key Differences from Full AR Plan (PLAN_200PHASE_AR_TRYON.md)

| Aspect | Full AR Plan | This Plan |
|--------|-------------|-----------|
| Scope | Full standalone AR app | Homepage gallery feature |
| Phases | 200 | 116 (focused) |
| Backend changes | New API endpoints, DB schema | None |
| Deployment | New subdomain (ar.korra.style) | Existing korra.style |
| Garments | User uploads + catalog | 8 existing gallery garments |
| Body scan | Required for full experience | Optional (estimate without) |
| Cloth simulation | Full GPU cloth (WebGPU) | CPU Verlet (mobile-optimized) |
| Multi-garment | Full outfit builder | Top + bottom only |
| Social | Sharing, groups, leaderboard | Share photo only |
| Monetization | Premium garments, subscriptions | Free (marketing feature) |
| Timeline | 3-6 months | 2-3 weeks |

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| 8th Wall binary incompatible with iOS | High | Test on all iOS versions; fallback to no-SLAM |
| MediaPipe too slow on old phones | High | Reduce model complexity; use PoseNet fallback |
| GLB too large to load quickly | Medium | Draco compress; lazy load; show progress |
| Cloth simulation drains battery | Medium | Adaptive quality; battery-aware |
| Camera permission denied | High | Clear messaging; deep link to settings |
| Body not detected (poor lighting) | Medium | Light estimation; "turn on lights" prompt |
| Memory leak across sessions | High | Rigorous disposal; 50-cycle test |
| Low AR adoption | Medium | Track analytics; iterate on UX |
