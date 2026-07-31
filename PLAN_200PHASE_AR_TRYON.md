# 200-Phase Plan: AR Virtual Try-On with 8th Wall + MediaPipe Body Tracking

## Executive Summary

Build a web-based AR virtual try-on system that anchors 3D garment models (GLB) to the user's body in real-time using their phone camera. The system combines 8th Wall's open-source SLAM engine for world tracking with MediaPipe Pose for body tracking, overlaid with Three.js cloth simulation for garment rendering.

**Target**: Mobile web browser (no app install), 30fps, <3s load time, works on iOS Safari + Android Chrome.

**Architecture**:
```
Phone Camera → 8th Wall SLAM (world position) → MediaPipe Pose (body keypoints) 
→ SMPL Body Model Fit → Cloth Simulation → Three.js Render → AR Overlay
```

---

## Phase 1-10: Project Setup & Infrastructure

### Phase 1: Repository & Toolchain
- Create `ar-tryon/` directory in project root
- Initialize npm project with Vite (fast bundling, ESM)
- Configure TypeScript + ESLint + Prettier
- Set up git submodules for 8th Wall engine binary

### Phase 2: 8th Wall Engine Integration
- Download 8th Wall XR Engine binary from [8th.io/xrjs](https://8th.io/xrjs)
- Add `xrengine.js` to project
- Create minimal HTML page with 8th Wall canvas
- Verify SLAM initializes on mobile (Android + iOS)

### Phase 3: Three.js Scene Setup
- Install Three.js (r152+)
- Create `ARScene` class wrapping Three.js `WebGLRenderer`
- Configure renderer with `alpha: true`, `antialias: true`, `powerPreference: 'high-performance'`
- Set up `PerspectiveCamera` synced to 8th Wall camera pose
- Render loop: requestAnimationFrame at 60fps target

### Phase 4: 8th Wall ↔ Three.js Camera Sync
- Read camera pose from 8th Wall SLAM each frame
- Extract position (x,y,z) and quaternion from 8th Wall camera
- Apply to Three.js camera: `camera.position.set(...)`, `camera.quaternion.set(...)`
- Test: tap to place cube at world origin, verify it sticks to real-world position

### Phase 5: MediaPipe Pose Integration
- Install `@mediapipe/pose` (or use CDN)
- Configure `Pose` with `modelComplexity: 2` (full model, 33 keypoints)
- Set `enableSegmentation: false`, `minDetectionConfidence: 0.7`, `minTrackingConfidence: 0.5`
- Pipe camera feed from 8th Wall video element to MediaPipe

### Phase 6: Body Keypoint Extraction
- Extract 33 pose landmarks from MediaPipe output
- Convert normalized coordinates to 3D world space using camera intrinsics
- Map MediaPipe keypoints to SMPL joint indices
- Key joints: left/right shoulder, elbow, wrist, hip, knee, ankle, neck, nose

### Phase 7: SMPL Body Model Loading
- Load SMPL body model (`.npz` format) with Three.js
- Create `SMPLBody` class with pose/shape parameters
- Initialize with T-pose: `theta = zeros(72)`, `beta = zeros(10)`
- Render SMPL mesh wireframe for debugging

### Phase 8: SMPL Pose Fitting (Initial)
- Implement `fitSMPLtoKeypoints(mediapipeLandmarks, smplModel)`
- Use iterative closest point (ICP) to align SMPL joints to MediaPipe joints
- Optimize: `minimize ||SMPL_joints(theta) - MP_joints||^2 + regularization`
- Start with analytical solution (rigid transform), refine with gradient descent

### Phase 9: Shape Parameter Estimation
- Use user's KORRA scan data if available (stored `beta` params)
- If no scan: estimate `beta` from body proportions (shoulder width, torso length, limb ratios)
- Map MediaPipe keypoint distances to SMPL shape space
- Store estimated shape in session localStorage

### Phase 10: Body Mesh Rendering
- Render fitted SMPL mesh in AR scene (hidden, used for collision)
- Add debug toggle to show/hide body mesh
- Verify body mesh tracks user movement with <50ms latency
- Performance target: SMPL forward pass <5ms on mobile

---

## Phase 11-25: Garment Loading & Rendering

### Phase 11: GLB Garment Loading
- Load garment GLB files via Three.js `GLTFLoader`
- Support existing KORRA garments: `atomic_jacket_morphed.glb`, `tshirt.glb`, `dress.glb`, etc.
- Create `GarmentLoader` class with error handling and progress callbacks
- Preload first 3 garments in background

### Phase 12: Garment-SMPL Binding
- Bind garment vertices to SMPL mesh vertices (pre-computed correspondence)
- Use linear blend skinning (LBS) with SMPL joint weights
- Each garment vertex deforms based on nearby SMPL joint transforms
- Store binding data in garment metadata (`.json` sidecar or embedded)

### Phase 13: Garment Draping (Initial)
- Apply SMPL body pose transforms to garment mesh
- Simple approach: rigid bind per-triangle to nearest SMPL triangle
- Garment follows body movement without cloth simulation
- Visual: garment looks "painted on" — acceptable MVP

### Phase 14: Cloth Simulation Setup
- Install cannon-es or ammo.js (WebAssembly physics)
- Create `ClothSimulator` class with Verlet integration
- Initialize cloth particles at garment vertex positions
- Connect particles with spring constraints (structural, shear, bending)

### Phase 15: Cloth-Body Collision
- Use SMPL mesh as collision body for cloth simulation
- Detect vertex penetration through SMPL triangles
- Push cloth vertices outward along collision normal
- Handle self-collision between cloth particles (approximate with spatial hashing)

### Phase 16: Cloth Parameters Tuning
- Tune per-garment: stiffness, damping, mass, friction
- Jacket: stiff, heavy. Dress: light, flowing. T-shirt: medium.
- Add wind force for realism (subtle, ~0.1 m/s²)
- Add gravity (9.81 m/s²) — baseline force

### Phase 17: Garment Texture & Material
- Apply PBR materials from GLB (albedo, normal, roughness)
- Handle transparency: force opaque for solid garments
- Add environment map for realistic reflections (HDRI or probe)
- Shadow casting onto body mesh

### Phase 18: Garment Size Scaling
- Scale garment mesh to match user's SMPL body dimensions
- Use body measurements (chest, waist, hip) from KORRA scan or MediaPipe estimates
- Apply uniform scale per garment region (torso, sleeves, legs)
- Prevent clipping: ensure garment envelops body mesh

### Phase 19: Garment Library UI
- Horizontal carousel of available garments (reuse gallery UI pattern)
- Thumbnail previews rendered from garment GLB
- Tap to select → garment loads and binds to body
- Loading indicator during GLB parse

### Phase 20: Multi-Garment Support
- Support top + bottom simultaneously (shirt + pants)
- Layer garments: outer over inner, handle z-fighting
- Each garment has独立 cloth simulation (separate particle systems)
- Collision between garments (pants don't clip through shirt)

### Phase 21: Garment Removal
- Remove current garment from scene
- Dispose geometry, material, textures (WebGL memory)
- Return to "body only" mode
- Smooth transition: garment fades out over 300ms

### Phase 22: Garment Color/Variant Switch
- Support multiple color variants per garment
- Swap texture maps without reloading geometry
- Variant data stored in garment metadata
- UI: color picker dropdown

### Phase 23: Garment Fit Indicator
- Show real-time fit quality (tight/loose/ideal) via color overlay
- Green = good fit, Yellow = tight, Red = very tight
- Based on distance between garment mesh and SMPL body mesh
- Helps user choose correct size

### Phase 24: Capture Screenshot
- Capture current AR frame (video + 3D overlay)
- Use `renderer.domElement.toDataURL()` for image
- Share via Web Share API (native share sheet on mobile)
- Save to device gallery with permission

### Phase 25: Recording Video
- Record 5-second AR video clip
- Use `MediaRecorder` API on canvas stream
- Output as WebM (Chrome) or MP4 (Safari via workaround)
- Share via Web Share API

---

## Phase 26-50: Body Tracking Refinement

### Phase 26: Temporal Smoothing
- Apply Kalman filter to MediaPipe keypoints (reduce jitter)
- Smooth over 5-10 frames (83-167ms at 60fps)
- Tune process/measurement noise for each joint type
- Shoulders/hips: low noise (stable). Wrists: higher noise (fast movement)

### Phase 27: Latency Compensation
- MediaPipe inference: ~30ms on modern phones
- 8th Wall SLAM: ~16ms
- Total pipeline: ~50ms
- Predict body pose 1-2 frames ahead using velocity extrapolation
- Align SMPL output to predicted future frame, not current

### Phase 28: Handling Occlusion
- Detect when body part is occluded (MediaPipe confidence drops)
- For occluded joints: extrapolate from last known position + velocity
- Increase regularization on occluded joints (prefer smooth motion)
- Visual cue: dim garment region when occluded

### Phase 29: Multi-Person Support
- MediaPipe Pose supports multiple people (up to ~4)
- Track each person independently with unique ID
- Bind separate garment instances per person
- Limit: only render garments for nearest 2 people (performance)

### Phase 30: Front/Back Detection
- Determine body facing direction from nose-ear-shoulder geometry
- Flip garment when user turns around (back view)
- Smooth transition: garment cross-fades between front/back meshes
- Handle 180° rotation gracefully (no sudden pop)

### Phase 31: Arm Pose Refinement
- MediaPipe sometimes gives incorrect arm rotations
- Apply anatomical constraints: elbow can't bend backward
- Use learned prior from KORRA dataset for arm pose distribution
- Smooth arm transitions during fast movement

### Phase 32: Leg Tracking
- MediaPipe legs less accurate than torso/arms
- Use hip-knee-ankle chain with IK solver
- Anchor: hip position (stable), extend: knee angle, end: ankle
- Apply SMPL leg shape parameters for width

### Phase 33: Head Tracking
- Use MediaPipe face mesh (468 landmarks) for head orientation
- Map to SMPL head joint rotation
- Attach headwear/collar garments if needed
- Head movement → garment collar follows

### Phase 34: Body Scale Normalization
- Account for different phone distances (selfie vs. arm's length)
- Use 8th Wall absolute scale feature (if available) or estimate from MediaPipe
- Normalize SMPL body to real-world scale
- Prevent body from appearing too large/small in AR

### Phase 35: Standing vs. Sitting Detection
- Detect body posture from keypoint angles (hip-knee, hip-spine)
- Switch SMPL pose mode: standing T-pose vs. sitting
- Adjust garment drape for sitting (fabric bunches at waist)
- Pre-computed sitting poses for common positions

### Phase 36: Walking Motion
- Track body velocity from frame-to-frame keypoint changes
- Add subtle garment sway during walking
- Cloth simulation: add forward force component
- Prevent garment from "floating" during movement

### Phase 37: Gesture Recognition
- Detect simple gestures: arms raised, arms crossed, hands on hips
- Use for UI interaction: arms raised = "show size info"
- Hands on hips = "rotate garment view"
- Avoid false positives with temporal filtering

### Phase 38: Camera Switch (Front/Back)
- Support both front (selfie) and rear camera
- Detect camera switch, reinitialize SLAM
- Re-detect body in new camera feed
- Seamless transition: garment persists across camera switch

### Phase 39: Light Estimation
- Use 8th Wall's light estimation (ambient intensity + direction)
- Apply to garment lighting in Three.js
- Match virtual garment lighting to real environment
- Prevent garment from looking "flat" in dark/bright scenes

### Phase 40: Depth Estimation
- Use MediaPipe depth estimation (if available) or monocular depth network
- Improve cloth-body collision accuracy
- Better occlusion handling (garment behind body parts)
- Optional: use LiDAR on iPhone Pro for ground truth depth

---

## Phase 51-75: Cloth Simulation Engine

### Phase 51: Verlet Integration Core
- Implement stable Verlet integrator for cloth particles
- Position-based dynamics (PBD) for constraint solving
- 10-20 solver iterations per frame (quality vs. speed tradeoff)
- Time step: 1/60s with sub-stepping if needed

### Phase 52: Structural Springs
- Connect adjacent particles (horizontal + vertical)
- Rest length = initial distance between vertices
- Stiffness: 1.0 (fully rigid)
- Prevents stretching along grid lines

### Phase 53: Shear Springs
- Connect diagonal particles (4 per interior particle)
- Prevents shearing deformation
- Stiffness: 0.8 (slightly flexible)
- Important for fabric drape quality

### Phase 54: Bending Springs
- Connect particles 2 apart (skip one)
- Simulates fabric resistance to bending
- Stiffness: 0.1-0.3 (varies by fabric type)
- Silk = low stiffness, denim = high stiffness

### Phase 55: Gravity & External Forces
- Constant downward force (9.81 m/s²)
- Optional wind: Perlin noise-based directional force
- User interaction: swipe to push garment
- Centrifugal force during fast rotation

### Phase 56: Collision Detection (SMPL Body)
- Treat SMPL mesh as triangle soup
- For each cloth vertex: find nearest SMPL triangle
- If penetration detected: project vertex outward along triangle normal
- Handle edge cases: vertex inside multiple triangles

### Phase 57: Collision Response
- Push cloth vertex to closest point on triangle surface
- Add small offset (0.5cm) to prevent z-fighting
- Apply friction: reduce tangential velocity on contact
- Energy dissipation: reduce vertex velocity on collision

### Phase 58: Self-Collision (Cloth)
- Spatial hashing for O(n) neighbor detection
- Hash grid cell size = 2× average particle spacing
- Check cloth vertices within same/adjacent cells
- Push apart if distance < minimum threshold

### Phase 59: Collision with Other Garments
- Multi-layer collision: inner garment pushes outer garment
- Priority system: body > inner garment > outer garment
- Simple approach: treat each garment as separate collision body
- Performance: skip self-collision for inner garments

### Phase 60: Constraint Projection
- Iterative solver: project each constraint per iteration
- 10 iterations = 10 constraint solves per frame
- Convergence: after 5-10 iterations, cloth is stable
- Adaptive: reduce iterations if frame time >16ms

### Phase 61: Fabric Presets
- **Cotton**: medium stiffness, medium damping
- **Silk**: low stiffness, low damping, high drape
- **Denim**: high stiffness, high damping
- **Knit**: medium stiffness, high stretch
- **Leather**: very high stiffness, very low stretch
- Store as JSON config per garment

### Phase 62: GPU Cloth Simulation
- Move cloth simulation to WebGPU compute shaders
- Particle positions stored in GPU buffers
- Spring constraints as compute dispatch
- Expected speedup: 5-10x on supported devices
- Fallback: CPU Verlet for unsupported browsers

### Phase 63: Cloth LOD (Level of Detail)
- Reduce particle count based on distance from camera
- Close: full resolution (100% particles)
- Medium: 50% particles (merge adjacent)
- Far: 25% particles (simplified mesh)
- Seamless transition between LOD levels

### Phase 64: Cloth Caching
- Cache cloth simulation results for static poses
- If body hasn't moved for 500ms: freeze simulation
- Resume when body moves again
- Saves ~30% CPU during idle periods

### Phase 65: Cloth Pre-warming
- Pre-simulate garment drape before showing to user
- Run 100 frames of simulation on initial T-pose
- Garment starts in natural drape state
- Prevents "falling" animation on load

### Phase 66: Fabric Wrinkle Generation
- Add procedural wrinkles based on joint bending
- Elbow bend > 45°: add crease wrinkles
- Knee bend > 30°: add fabric folds
- Use normal map perturbation for visual detail

### Phase 67: Fabric Stretch Visualization
- Show strain (stretch/compression) as color overlay
- Green = relaxed, Red = stretched, Blue = compressed
- Debug mode for tuning cloth parameters
- Hidden in production, useful for development

### Phase 68: Cloth Thickness
- Add virtual thickness to cloth (prevent body poking through)
- Offset collision by thickness parameter (0.5-2mm)
- Different thickness per garment type (t-shirt vs. jacket)
- Visual: slight gap between body and garment

### Phase 69: Fabric Weight Simulation
- Heavier fabrics drape differently (fewer wrinkles, more hang)
- Mass per particle varies by garment region
- Jacket body: heavy. Sleeve lining: light.
- Affects gravity response and wind resistance

### Phase 70: Cloth Interaction
- User can poke/swipe garment on screen
- Convert screen touch to 3D ray using camera
- Apply force to nearest cloth particles
- Fabric responds with realistic push/pull

### Phase 71: Cloth Tearing (Optional)
- If force exceeds threshold: break spring constraint
- Garment tears at stress point
- Fun feature for demo/entertainment
- Disable in production try-on

### Phase 72: Cloth Folding
- Detect when garment folds over itself (e.g., jacket collar)
- Render both sides: front face + back face
- Double-sided material for folded regions
- Avoid visual artifacts from backface culling

### Phase 73: Cloth Settling
- After garment loads, let it settle for 1-2 seconds
- Gravity pulls garment to natural position
- Show loading indicator during settling
- Garment reaches equilibrium before user interaction

### Phase 74: Cloth Reset
- Reset garment to initial T-pose position
- Re-run pre-warming simulation
- Useful after body pose changes drastically (e.g., sit → stand)
- Button in UI: "Reset Garment"

### Phase 75: Cloth Performance Profiling
- Measure per-frame: simulation time, collision time, render time
- Target: <8ms total cloth pipeline (50% of 16ms frame budget)
- Adaptive quality: reduce iterations if behind schedule
- Performance overlay in debug mode

---

## Phase 76-100: 8th Wall Integration

### Phase 76: 8th Wall Project Setup
- Create 8th Wall project (npm or Desktop)
- Configure `index.html` with XR canvas
- Add `xrengine.js` and `xrextras.js`
- Enable SLAM module (world tracking)

### Phase 77: World Effects Setup
- Initialize 8th Wall World Effects (SLAM-based placement)
- Tap to place AR content on detected surfaces
- Verify plane detection works on target devices
- Ground plane + vertical plane support

### Phase 78: Camera Feed Pipeline
- 8th Wall provides camera feed as video element
- Pipe to MediaPipe Pose for body tracking
- Share single camera feed (avoid double-processing)
- Handle camera permissions gracefully

### Phase 79: SLAM ↔ Three.js Sync
- Read 8th Wall camera matrix each frame
- Extract view matrix, projection matrix
- Apply to Three.js camera
- Verify: virtual objects stay anchored to real world

### Phase 80: Absolute Scale Calibration
- Use 8th Wall Absolute Scale feature (if available)
- Calibrate virtual units to real-world meters
- SMPL body in meters (height ~1.7m)
- Verify: body appears correct size relative to environment

### Phase 81: Surface Detection
- Detect horizontal surfaces (floor, table)
- Detect vertical surfaces (wall, mirror)
- Show hit test results as invisible plane
- User taps surface to start AR try-on

### Phase 82: Light Estimation
- 8th Wall provides ambient light intensity + color
- Apply to Three.js scene: `scene.environment`, `scene.ambientLight`
- Match virtual garment lighting to real room
- Critical for garment looking "real" in AR

### Phase 83: 8th Wall Camera Permissions
- Handle iOS Safari permission flow (user must tap "Allow")
- Handle Android Chrome permission flow
- Fallback: show instructions if denied
- Retry button if permission denied

### Phase 84: 8th Wall Error Handling
- Handle SLAM initialization failure (low light, no features)
- Handle camera access denied
- Handle unsupported browser (show message)
- Graceful degradation: 2D try-on if AR fails

### Phase 85: 8th Wall Performance Optimization
- Monitor 8th Wall SLAM frame rate
- If <24fps: reduce cloth simulation quality
- If <15fps: pause cloth, use rigid garment binding
- Battery-aware: reduce quality on low battery

### Phase 86: 8th Wall Memory Management
- Monitor WebGL memory usage
- Dispose unused textures, geometries
- Aggressive garbage collection for mobile
- Target: <200MB total memory

### Phase 87: 8th Wall Multi-Session
- Support multiple AR sessions (user closes/reopens)
- Properly dispose previous session resources
- Reinitialize SLAM + MediaPipe on new session
- No memory leaks across sessions

### Phase 88: 8th Wall Image Targets (Optional)
- Scan QR code or image to trigger try-on
- User points camera at garment label → try-on starts
- Use 8th Wall Image Targets module
- Marketing use: scan poster → see garment on you

### Phase 89: 8th Wall Sky Effects (Optional)
- Replace sky with brand-themed environment
- Indoor: show virtual fitting room backdrop
- Outdoor: show fashion show runway
- Optional fun feature for engagement

### Phase 90: 8th Wall Physics (Optional)
- Use 8th Wall physics module for garment interaction
- Tap garment to make it bounce/swing
- Realistic physics response
- Entertainment feature

### Phase 91: 8th Wall Face Effects (Optional)
- Add accessories: glasses, hat, earrings
- Use face tracking from 8th Wall
- Complement body try-on with face accessories
- Separate from body garment system

### Phase 92: 8th Wall Desktop Integration
- Use 8th Wall Desktop editor for visual prototyping
- Drag-and-drop garment placement
- Test AR scenes without mobile device
- Export to web for deployment

### Phase 93: 8th Wall Build Pipeline
- Configure Vite to bundle 8th Wall + Three.js + MediaPipe
- Tree-shake unused 8th Wall modules
- Optimize bundle size (target: <5MB total)
- Gzip/Brotli compression

### Phase 94: 8th Wall HTTPS Requirement
- 8th Wall requires HTTPS for camera access
- Configure EC2 nginx with SSL (Let's Encrypt)
- Subdomain: `ar.korra.style`
- Redirect HTTP → HTTPS

### Phase 95: 8th Wall Deployment
- Deploy to EC2 (same server as KORRA)
- Static files served from nginx
- API endpoints on FastAPI (garment management)
- CDN for GLB garment files (Cloudflare)

### Phase 96: 8th Wall Analytics
- Track: session starts, garment selections, captures
- Custom events via Google Analytics or Mixpanel
- A/B test: cloth simulation ON vs. OFF
- User engagement metrics

### Phase 97: 8th Wall Browser Compatibility
- iOS Safari 15+: full support
- Android Chrome 90+: full support
- Samsung Internet: partial support
- Desktop browsers: fallback to 2D try-on

### Phase 98: 8th Wall Accessibility
- Screen reader support for garment selection
- High contrast mode for visually impaired
- Voice commands: "try the red dress"
- Keyboard navigation for desktop fallback

### Phase 99: 8th Wall Security
- Validate all GLB files before loading (size, format)
- Sanitize user-uploaded garment images
- Rate limit garment API calls
- CORS configuration for AR subdomain

### Phase 100: 8th Wall Documentation
- Developer setup guide
- API documentation for garment format
- Troubleshooting guide (common AR issues)
- User guide (how to use AR try-on)

---

## Phase 101-125: SMPL Body Model

### Phase 101: SMPL Model Integration
- Load SMPL model files: `smpl_male.npz`, `smpl_female.npz`
- Create `SMPLModel` class with forward kinematics
- Implement `body_model(pose, shape)` → vertices + joints
- Verify SMPL renders correctly in Three.js

### Phase 102: SMPL Pose Parameters
- 72D pose vector: 24 joints × 3 (axis-angle rotation)
- Root joint: global orientation
- Body joints: 23 body part rotations
- Initialize: T-pose (zero rotations)

### Phase 103: SMPL Shape Parameters
- 10D shape vector (beta): principal components of body shape
- Controls: height, weight, proportions, fat distribution
- From KORRA scan: direct beta values
- Without scan: estimate from MediaPipe proportions

### Phase 104: SMPL Forward Kinematics
- Compute joint locations from pose + shape
- Chain rule: parent → child joint transforms
- World-space joint positions for each frame
- Compare with MediaPipe keypoints for validation

### Phase 105: SMPL Mesh Generation
- 6890 vertices, 13776 triangles
- Skinning weights: which joints affect each vertex
- Linear blend skinning (LBS): weighted sum of joint transforms
- Output: deformed body mesh for collision + rendering

### Phase 106: SMPL Pose Optimization
- Minimize: `||SMPL_joints(beta, theta) - MediaPipe_joints||^2`
- Regularization: `lambda * ||theta - theta_prior||^2`
- Solver: L-BFGS-B (fast, bounded)
- Convergence: <10 iterations, <5ms on mobile

### Phase 107: SMPL Shape Optimization
- If no KORRA scan: optimize beta from body proportions
- MediaPipe measurements: shoulder width, torso length, limb ratios
- Map to SMPL shape space via pre-trained regressor
- Output: estimated beta for user

### Phase 108: SMPL Pose Prior
- Use pre-trained VAE on SMPL poses from AMASS dataset
- Regularize theta to be "human-like"
- Prevent: impossible poses (arm through body, etc.)
- Weight: low (0.01) to allow flexibility

### Phase 109: SMPL+H Extension (Optional)
- Add hands (SMPL+H) for finger tracking
- MediaPipe provides hand landmarks (21 per hand)
- Fit SMPL+H hand poses to MediaPipe hands
- Allow garment interaction with fingers

### Phase 110: SMPL-X Integration (Optional)
- Full body + hands + face (SMPL-X)
- 104 shape params, 69 pose params
- Higher quality but more computation
- Use if device supports it (high-end phones)

### Phase 111: SMPL Body Texture
- Apply body texture (skin, clothing) to SMPL mesh
- Use KORRA scan texture if available
- Default: neutral gray body
- Optional: skin tone matching from camera

### Phase 112: SMPL Body Occlusion
- Use SMPL mesh for depth-based occlusion
- Real body parts occlude virtual garment
- Render SMPL to depth buffer → use as occlusion mask
- Prevents garment from appearing over real body

### Phase 113: SMPL Body Shadows
- Render SMPL body as shadow receiver
- Garment casts shadow onto body
- Ground plane catches shadows
- Enhances realism significantly

### Phase 114: SMPL Body Animation
- Animate SMPL body with walking/standing transitions
- Blend between keyframe poses
- Smooth transitions (lerp quaternion rotations)
- Body animation drives garment animation

### Phase 115: SMPL Body Segmentation
- Use MediaPipe segmentation mask to isolate body
- Remove background from camera feed
- Render: body + garment only (no background)
- "Virtual fitting room" effect

### Phase 116: SMPL Body Background Removal
- Replace real background with virtual environment
- Use 8th Wall Sky Effects for background
- Or: transparent background (garment floating in space)
- User preference toggle

### Phase 117: SMPL Body Measurement
- Compute body measurements from SMPL mesh
- Chest, waist, hip, shoulder, inseam, etc.
- Compare with KORRA scan measurements
- Display on screen as reference

### Phase 118: SMPL Body Size Recommendation
- Use body measurements → size recommendation
- Map to garment sizes (S, M, L, XL)
- Show "Your size: M" overlay
- Link to KORRA signup for full measurements

### Phase 119: SMPL Body Comparison
- Show before/after: body with vs. without garment
- Toggle button to switch views
- Useful for seeing how garment changes appearance
- A/B comparison slider

### Phase 120: SMPL Body Customization
- Allow user to adjust body shape (slider)
- "See how you'd look with broader shoulders"
- Modify beta parameters in real-time
- Fun engagement feature

### Phase 121: SMPL Body History
- Save body pose history (last 100 frames)
- Replay: "Show me that pose again"
- Compare different garment on same pose
- Useful for side-by-side comparison

### Phase 122: SMPL Body Recording
- Record body pose sequence (30 seconds)
- Replay with different garments
- Share body motion with friends
- Social feature

### Phase 123: SMPL Body Sharing
- Export body pose as JSON
- Import into other AR experiences
- Cross-platform body sharing
- Network feature

### Phase 124: SMPL Body Privacy
- All body processing happens on-device
- No body data sent to server (unless user opts in)
- GDPR/CCPA compliant
- Clear privacy policy

### Phase 125: SMPL Body Performance
- Profile SMPL forward pass on target devices
- iPhone 12+: <3ms
- Android mid-range: <8ms
- Fallback: reduce SMPL resolution if slow

---

## Phase 126-150: User Experience & UI

### Phase 126: Onboarding Flow
- Step 1: "Point camera at your full body"
- Step 2: "Stand back 2-3 meters"
- Step 3: "Make sure you're well-lit"
- Step 4: "Tap to start AR try-on"

### Phase 127: Body Detection UI
- Show skeleton overlay when body detected (green lines)
- Show "No body detected" message when lost
- Auto-hide skeleton after 3 seconds (clean view)
- Debug mode: always show skeleton

### Phase 128: Garment Selection Panel
- Bottom sheet with garment thumbnails
- Scrollable horizontally (reuse gallery pattern)
- Tap to select, long-press for preview
- Swipe up for full garment catalog

### Phase 129: Size Selection
- Show recommended size based on body scan
- Allow manual override (S, M, L, XL, XXL)
- Visual indicator: "Best fit: M"
- Link to KORRA scan for accurate sizing

### Phase 130: Color Selection
- Color swatches below garment thumbnail
- Tap to change garment color
- Real-time color swap (no reload)
- "Custom" option for hex color input

### Phase 131: View Controls
- Pinch to zoom (adjust garment size)
- Two-finger rotate (rotate garment around body)
- One-finger drag (adjust garment position)
- Double-tap to reset view

### Phase 132: Camera Controls
- Switch front/back camera button
- Flash toggle (for dark environments)
- Grid overlay for composition
- Timer (3s delay for full-body shot)

### Phase 133: Capture UI
- Large capture button (center bottom)
- Photo mode: single tap
- Video mode: hold to record (5s max)
- Preview after capture with share/save options

### Phase 134: Share Sheet
- Native Web Share API (iOS/Android)
- Share to: WhatsApp, Instagram, Twitter, SMS
- Copy link: `korra.style/ar?garment=dress&color=red`
- Download: save to device gallery

### Phase 135: Size Chart Overlay
- Show garment size chart on tap
- Highlight user's recommended size
- Show measurements for each size
- Link to detailed size guide

### Phase 136: Fit Feedback
- "This garment fits you well!" (green)
- "Consider sizing up" (yellow)
- "This garment is too small" (red)
- Based on SMPL-garment distance

### Phase 137: Outfit Builder
- Select multiple garments (top + bottom + accessories)
- Layer garments correctly
- Save outfit as preset
- Share outfit with friends

### Phase 138: History Panel
- Show recently tried garments
- Quick re-select without browsing
- Clear history option
- Persist across sessions (localStorage)

### Phase 139: Wishlist
- Heart button to save garment to wishlist
- Access wishlist from profile
- Notify when wishlist items go on sale
- Integration with KORRA merchant portal

### Phase 140: Price Display
- Show garment price on AR view
- "Buy Now" button → checkout
- Merchant revenue attribution
- Commission tracking

### Phase 141: Social Features
- "Try this outfit" link → friend opens same garment
- Group try-on: multiple people try same outfit
- Comment/react on shared try-on photos
- Leaderboard: most shared outfits

### Phase 142: Tutorial Overlay
- First-time user: animated tutorial
- "Swipe to browse garments"
- "Tap to try on"
- "Pinch to resize"
- Dismiss after viewing

### Phase 143: Error States
- "Camera access denied" → settings link
- "Body not detected" → reposition instructions
- "Garment failed to load" → retry button
- "Low light" → turn on lights

### Phase 144: Loading States
- Skeleton shimmer during garment load
- Progress bar for large GLB files
- "Preparing your try-on..." message
- Smooth transition from loading to ready

### Phase 145: Empty States
- "No garments available" → browse catalog
- "No body scan" → take scan now
- "No internet" → cached garments only
- Helpful CTAs for each empty state

### Phase 146: Accessibility
- VoiceOver/TalkBack support for all UI elements
- High contrast mode
- Large text mode
- Keyboard navigation (desktop fallback)

### Phase 147: Localization
- Support 10+ languages (English, Spanish, French, etc.)
- RTL support (Arabic, Hebrew)
- Currency conversion for prices
- Date/number formatting per locale

### Phase 148: Dark Mode
- Auto-detect system dark mode preference
- Dark UI theme for AR view
- Garment lighting adjusts for dark environments
- Toggle in settings

### Phase 149: Haptic Feedback
- Vibrate on garment selection
- Vibrate on capture
- Vibrate on error
- Subtle, non-intrusive

### Phase 150: Sound Effects
- Optional sound on garment load (subtle "whoosh")
- Sound on capture (camera shutter)
- Sound on error (gentle alert)
- Mute toggle in settings

---

## Phase 151-175: Performance & Optimization

### Phase 151: Bundle Size Optimization
- Target: <5MB JavaScript bundle
- Tree-shake Three.js (import only needed modules)
- Lazy-load MediaPipe (only when AR starts)
- Gzip/Brotli: target <1.5MB compressed

### Phase 152: GLB File Optimization
- Draco compression for all garment GLBs
- Texture atlas: combine small textures
- Reduce polygon count (simplify mesh if >50K tris)
- LOD system: high/medium/low per garment

### Phase 153: Texture Optimization
- Max texture size: 2048×2048
- Use WebP format (smaller than PNG)
- Mipmap generation for distance-based filtering
- Compress with Basis Universal (GPU-friendly)

### Phase 154: Memory Management
- Monitor WebGL memory: `renderer.info.memory`
- Dispose unused: `geometry.dispose()`, `material.dispose()`
- Pool Three.js objects (reuse geometries, materials)
- Target: <150MB peak memory

### Phase 155: Frame Rate Monitoring
- Track FPS over time
- If <24fps for 3 seconds: reduce quality
- Auto-adjust: cloth iterations, texture quality, shadow resolution
- Log performance data for analysis

### Phase 156: CPU Profiling
- Use Chrome DevTools CPU profiler
- Identify bottlenecks: SMPL, cloth, render
- Optimize hot paths (SIMD, Web Workers)
- Target: <8ms per frame on mid-range phone

### Phase 157: GPU Profiling
- Use GPU Chrome DevTools
- Monitor draw calls, texture bandwidth
- Reduce draw calls: instancing, batching
- Target: <2ms GPU per frame

### Phase 158: Web Workers
- Move SMPL computation to Web Worker
- Move cloth simulation to Web Worker
- Main thread: only rendering + 8th Wall
- Reduces main thread blocking

### Phase 159: WASM Acceleration
- Compile SMPL forward pass to WASM
- Use TinyGrad or ONNX Runtime for inference
- 2-5x speedup over JavaScript
- Fallback: pure JS if WASM fails

### Phase 160: Adaptive Quality
- Monitor device capabilities at startup
- High-end: full quality (cloth sim, shadows, AA)
- Mid-range: medium quality (reduced iterations)
- Low-end: low quality (rigid binding, no cloth)

### Phase 161: Battery Optimization
- Monitor battery level (`navigator.getBattery()`)
- Low battery (<20%): reduce quality significantly
- Very low (<10%): pause AR, show static preview
- Warn user: "AR mode uses significant battery"

### Phase 162: Thermal Management
- Monitor device temperature (if available)
- Throttling detected: reduce quality immediately
- Pause non-essential computation
- Resume when temperature normalizes

### Phase 163: Network Optimization
- Cache GLB files in IndexedDB (offline support)
- Preload next 3 garments while user views current
- Lazy-load garment textures (progressive)
- CDN for static assets (Cloudflare)

### Phase 164: Lazy Loading
- Load 8th Wall engine on demand (not at page load)
- Load MediaPipe only when AR starts
- Load SMPL model only on first try-on
- Reduces initial page load time

### Phase 165: Code Splitting
- Split bundle: AR core, MediaPipe, SMPL, UI
- Load chunks on demand
- Dynamic imports for optional features
- Reduces initial bundle by ~60%

### Phase 166: Preloading
- Preload critical GLBs (popular garments)
- Preload SMPL model files
- Preload MediaPipe WASM files
- Use `<link rel="preload">` for critical resources

### Phase 167: Caching Strategy
- Service Worker for offline support
- Cache-first for static assets
- Network-first for API calls
- Stale-while-revalidate for garment metadata

### Phase 168: Image Optimization
- Lazy-load garment thumbnails
- Use `loading="lazy"` attribute
- Responsive images (srcset)
- WebP with JPEG fallback

### Phase 169: Animation Optimization
- Use `requestAnimationFrame` (not `setInterval`)
- Batch Three.js updates per frame
- Avoid `renderer.render()` calls outside render loop
- Use `renderer.setAnimationLoop()` for clean lifecycle

### Phase 170: Geometry Optimization
- Merge static geometries
- Use `BufferGeometry` (not `Geometry`)
- Dispose unused buffer attributes
- Share geometries between garment instances

### Phase 171: Material Optimization
- Share materials between garments
- Use `MeshStandardMaterial` (not custom shaders)
- Limit texture sampling (max 4 per material)
- Use material instancing for multiple garments

### Phase 172: Draw Call Reduction
- Instanced rendering for repeated elements
- Merge geometries where possible
- Use `Object3D.traverse()` to batch
- Target: <50 draw calls per frame

### Phase 173: Frustum Culling
- Only render objects visible in camera frustum
- Three.js: `renderer.info.render.frame` analysis
- Custom culling for off-screen garments
- Reduces GPU workload significantly

### Phase 174: LOD Management
- Implement Three.js LOD system
- Distance-based quality switching
- Seamless transitions (cross-fade)
- Automatic LOD selection per device

### Phase 175: Performance Budget
- Total frame budget: 16.6ms (60fps)
- 8th Wall SLAM: ~3ms
- MediaPipe Pose: ~5ms
- SMPL forward: ~3ms
- Cloth simulation: ~3ms
- Three.js render: ~2ms
- Buffer: ~0.6ms

---

## Phase 176-200: Deployment & Production

### Phase 176: EC2 Deployment
- Deploy AR try-on to EC2 (same server as KORRA)
- Nginx config for AR subdomain
- HTTPS with Let's Encrypt
- Gzip/Brotli compression enabled

### Phase 177: CDN Setup
- Cloudflare CDN for GLB files
- Edge caching for garment assets
- Reduce latency for global users
- Cache invalidation on garment update

### Phase 178: Backend API
- FastAPI endpoints for AR try-on:
  - `GET /api/ar/garments` — list available garments
  - `GET /api/ar/garments/{id}` — garment metadata + GLB URL
  - `POST /api/ar/capture` — save user capture
  - `GET /api/ar/outfits` — user's saved outfits

### Phase 179: Database Schema
- Table: `ar_sessions` (user_id, start_time, device_info)
- Table: `ar_captures` (session_id, garment_id, image_url)
- Table: `ar_outfits` (user_id, garment_ids, name)
- Integrate with existing Supabase database

### Phase 180: Analytics Integration
- Track: session starts, garment views, captures, shares
- Funnel: visit → start AR → try garment → capture → share → purchase
- A/B test: cloth simulation on/off, garment order, UI layout
- Dashboard: real-time engagement metrics

### Phase 181: A/B Testing Framework
- Test garment loading order (popular vs. new)
- Test UI layouts (bottom sheet vs. side panel)
- Test capture flow (photo vs. video default)
- Test cloth simulation quality levels

### Phase 182: Error Monitoring
- Sentry for JavaScript error tracking
- Custom error logging for AR-specific issues
- Alert on: SLAM failures, MediaPipe crashes, WebGL errors
- Dashboard: error rates by device/browser

### Phase 183: Performance Monitoring
- Real User Monitoring (RUM) for AR sessions
- Track: load time, FPS, memory, battery impact
- Alert on: FPS drops, memory leaks, crashes
- Dashboard: performance by device/browser

### Phase 184: User Feedback
- In-app feedback button
- "Rate your try-on experience" (1-5 stars)
- "Report issue" with screenshot
- Feedback → Slack channel

### Phase 185: Merchant Dashboard
- Show AR try-on metrics per garment
- "Your garment was tried on 1,234 times today"
- "Conversion rate: 12% (try-on → purchase)"
- Revenue attribution

### Phase 186: Garment Management
- Admin UI to upload/manage garments
- Drag-and-drop GLB upload
- Auto-optimize: Draco compress, resize textures
- Preview in AR before publishing

### Phase 187: User Accounts
- Login via KORRA Supabase auth
- Save try-on history
- Sync body scan across devices
- Personalized recommendations

### Phase 188: Social Sharing
- Share try-on photos to social media
- Embed try-on widget in merchant sites
- Referral tracking (shared by user X)
- Viral loop: "Try this outfit" links

### Phase 189: Monetization
- Premium garments (pay per try-on)
- Subscription: unlimited AR try-ons
- Merchant fees: % of conversions from AR
- Free tier: 5 try-ons per month

### Phase 190: Privacy & Compliance
- GDPR: cookie consent, data deletion
- CCPA: "Do Not Sell My Data"
- Body data: processed on-device, never stored
- Camera: permission-only, clear indicators

### Phase 191: Security
- Rate limiting: 100 requests/min per user
- Input validation: GLB file size, format
- CORS: only allow korra.style origins
- CSP: strict content security policy

### Phase 192: Testing
- Unit tests: SMPL, cloth simulation, body fitting
- Integration tests: 8th Wall ↔ Three.js sync
- E2E tests: full AR try-on flow (Playwright)
- Device testing: iPhone 12+, Android flagship

### Phase 193: Beta Testing
- Internal team: 2 weeks
- Closed beta: 50 users
- Open beta: 500 users
- Iterate based on feedback

### Phase 194: Launch Preparation
- Performance audit (Lighthouse score >90)
- Security audit (penetration testing)
- Load testing (1000 concurrent AR sessions)
- Documentation: developer guide, user guide

### Phase 195: Marketing
- Landing page: AR try-on demo video
- Social media: "Try before you buy" campaign
- Influencer partnerships: fashion bloggers
- Press coverage: tech + fashion media

### Phase 196: Post-Launch Monitoring
- 24/7 error monitoring
- Performance dashboards
- User feedback triage
- Hotfix deployment process

### Phase 197: Iteration Sprint 1
- Fix top 10 user-reported issues
- Optimize top 3 performance bottlenecks
- Add top 3 requested features
- Ship within 2 weeks of launch

### Phase 198: Iteration Sprint 2
- Add garment favorites/wishlist
- Improve cloth simulation quality
- Add more garment categories (shoes, hats)
- Multi-language support

### Phase 199: Iteration Sprint 3
- Social features (outfit sharing, comments)
- Merchant analytics dashboard
- Advanced size recommendation
- AR try-on for accessories (jewelry, watches)

### Phase 200: Long-Term Roadmap
- **Month 3**: WebGPU cloth simulation (10x faster)
- **Month 6**: AI-generated garments (text → 3D)
- **Month 9**: Full-body scanning in AR (no separate scan needed)
- **Month 12**: Virtual fashion shows, collaborative try-on

---

## Technical Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| AR Engine | 8th Wall (open source) | Free, SLAM, world tracking |
| 3D Rendering | Three.js r152+ | Web standard, GPU-accelerated |
| Body Tracking | MediaPipe Pose | Real-time, 33 keypoints, mobile-optimized |
| Body Model | SMPL | Industry standard, 6890 vertices |
| Cloth Simulation | Verlet/PBD (custom) | Real-time, mobile-friendly |
| Bundler | Vite | Fast, ESM, HMR |
| Language | TypeScript | Type safety, better DX |
| Backend | FastAPI (existing KORRA) | Python, async, fast |
| Database | Supabase (existing KORRA) | Postgres, auth, storage |
| CDN | Cloudflare | Global, fast, free tier |
| Hosting | EC2 (existing KORRA) | Already deployed |

## Device Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| iOS | iPhone X (2017) | iPhone 12+ (2020) |
| Android | Samsung S10 / Pixel 3 | Samsung S21+ / Pixel 6+ |
| RAM | 3GB | 6GB+ |
| Browser | Safari 15 / Chrome 85 | Safari 16+ / Chrome 100+ |
| Connection | 3G (slow load) | 4G/WiFi |
| Camera | 720p | 1080p+ |
| Battery | 20%+ | 50%+ |

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| 8th Wall SLAM fails on low-end devices | High | Fallback to 2D try-on (photo-based) |
| MediaPipe too slow on old phones | High | Reduce model complexity, use PoseNet |
| Cloth simulation drains battery | Medium | Adaptive quality, battery-aware |
| Garment GLB too large | Medium | Draco compression, LOD, streaming |
| iOS Safari incompatibility | High | Test on all iOS versions, fallback |
| Privacy concerns (camera access) | High | Clear messaging, on-device processing |
| Low AR adoption | Medium | Start with 2D VTON, upgrade to AR |
| 8th Wall license changes | Low | Already open source (MIT/binary) |

## Success Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| AR session start rate | >60% of visitors | Analytics |
| Garment try-on rate | >40% of AR sessions | Analytics |
| Capture/share rate | >20% of try-ons | Analytics |
| Purchase conversion | >5% of try-ons | Analytics + Paystack |
| Average session time | >60 seconds | Analytics |
| FPS (mobile) | >30fps avg | RUM monitoring |
| Load time | <3 seconds | Lighthouse |
| Error rate | <1% | Sentry |
| User satisfaction | >4.0/5.0 | Feedback survey |
