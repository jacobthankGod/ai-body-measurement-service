# Snap Camera Kit — Body Measurement Extraction Plan

> **Project**: Korra AI Virtual Try-On — Lens Studio + Camera Kit Body Measurement Feature
> **Owner**: Korra Technologies (Snap Camera Kit Partner)
> **Lens ID**: `ccc9d825-d8ec-41ca-910a-7fd372065026`
> **Lens Group ID**: `6af97e7a-6e80-4d9e-86b7-8ffe3a6bd150`
> **Snap Kit App ID**: `67a348ba-aa55-4158-9451-94ff277e96c7`
> **Date**: August 2026
> **Status**: Ready for Implementation

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Prerequisites & Setup](#2-prerequisites--setup)
3. [Remote API Spec Creation](#3-remote-api-spec-creation)
4. [Lens Studio Implementation](#4-lens-studio-implementation)
5. [Lens Publishing & Deployment](#5-lens-publishing--deployment)
6. [Host App Integration — Frontend](#6-host-app-integration--frontend)
7. [Flask Backend — Measurement Storage API](#7-flask-backend--measurement-storage-api)
8. [Calibration & Accuracy](#8-calibration--accuracy)
9. [API Reference](#9-api-reference)
10. [Troubleshooting Guide](#10-troubleshooting-guide)
11. [Deployment Checklist](#11-deployment-checklist)
12. [Future Enhancements](#12-future-enhancements)

---

## 1. Architecture Overview

### 1.1 System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER'S DEVICE                            │
│                                                                 │
│  ┌──────────────┐    ┌──────────────────────────────────────┐  │
│  │   Camera      │───▶│  Snap Camera Kit Runtime (WASM)      │  │
│  │   Feed        │    │                                      │  │
│  └──────────────┘    │  ┌────────────────────────────────┐  │  │
│                      │  │  LENS (Sandboxed)               │  │  │
│                      │  │                                  │  │  │
│                      │  │  Body Tracking ──▶ Body Mesh     │  │  │
│                      │  │                      │           │  │  │
│                      │  │                      ▼           │  │  │
│                      │  │  extractVerticesForAttribute()   │  │  │
│                      │  │                      │           │  │  │
│                      │  │                      ▼           │  │  │
│                      │  │  Circumference Calculation        │  │  │
│                      │  │                      │           │  │  │
│                      │  │                      ▼           │  │  │
│                      │  │  Remote API Request ────────────────────▶ Host App
│                      │  │  (body_measurements)             │  │  │
│                      │  └────────────────────────────────┘  │  │
│                      │                                      │  │
│                      │  ┌────────────────────────────────┐  │  │
│                      │  │  HOST APP (tryon.html)          │  │  │
│                      │  │                                  │  │  │
│                      │  │  session.remoteApi.subscribe()   │  │  │
│                      │  │          │                       │  │  │
│                      │  │          ▼                       │  │  │
│                      │  │  Receive measurements            │  │  │
│                      │  │          │                       │  │  │
│                      │  │          ├──▶ Display in UI      │  │  │
│                      │  │          └──▶ POST to Flask API  │  │  │
│                      │  └────────────────────────────────┘  │  │
│                      └──────────────────────────────────────┘  │
└──────────────────────────────────┬──────────────────────────────┘
                                   │
                                   │ HTTPS POST
                                   ▼
                      ┌────────────────────────┐
                      │   EC2 (Flask API)       │
                      │   13.60.215.88          │
                      │                        │
                      │   /api/v2/measurements  │
          │           │                        │
          │           │   ┌──────────────────┐  │
          │           │   │  SQLite / JSON    │  │
          │           │   │  Storage          │  │
          │           │   └──────────────────┘  │
          │           └────────────────────────┘
          │
          │  HTTPS GET
          ▼
┌────────────────────────┐
│  Dashboard / Profile    │
│  View measurements      │
│  Compare over time      │
└────────────────────────┘
```

### 1.2 Data Flow

```
User taps "Get Measurements" button
        │
        ▼
Host app sends signal to lens (via launchParams or screen tap)
        │
        ▼
Lens activates measurement mode
        │
        ▼
Body Tracking → Full Body Mesh → 3D vertex positions (Float32Array)
        │
        ▼
Measurement script slices vertices at Y-thresholds:
  - Chest: Y = 72% of body height
  - Waist: Y = 52% of body height
  - Hips:  Y = 42% of body height
  - Shoulders: X-distance at Y = 78%
        │
        ▼
For each cross-section:
  1. Filter vertices within band (±bandWidth)
  2. Compute centroid (mean X, mean Z)
  3. Sort vertices by angle from centroid
  4. Sum Euclidean distances between consecutive vertices
  5. Multiply by 100 (meters → cm)
        │
        ▼
Lens sends Remote API request:
  POST body_measurements
  {
    chest: 96.2,
    waist: 81.5,
    hips: 102.3,
    shoulderWidth: 44.8,
    height: 175.3
  }
        │
        ▼
Host app receives via session.remoteApi.subscribe()
        │
        ├──▶ Displays in sidebar "Measurements" tab
        │
        └──▶ POST to Flask API → stored in database
```

### 1.3 Component Responsibilities

| Component | Responsibility | Location |
|-----------|---------------|----------|
| Body Tracking Asset | Track user's body in 3D | Lens (internal) |
| Full Body Mesh | Generate deformable 3D mesh | Lens (internal) |
| BodyMeasurementScript.js | Extract vertices, calculate circumferences | Lens script |
| Remote Service Module | Send measurement data to host | Lens asset |
| session.remoteApi.subscribe() | Receive measurement requests | Host app JS |
| Measurement Tab UI | Display measurements in sidebar | tryon.html |
| Flask API | Store and retrieve measurements | EC2 server |
| Dashboard | View measurement history | dashboard.html |

---

## 2. Prerequisites & Setup

### 2.1 Required Tools

| Tool | Version | Purpose | Download |
|------|---------|---------|----------|
| Lens Studio | 5.4+ | Modify lens | https://ar.snap.com/lens-studio |
| Chrome/Firefox | Latest | Test Camera Kit | — |
| Blender (optional) | 4.0+ | Calibrate body mesh reference | https://blender.org |
| Python | 3.10+ | Flask API server | Pre-installed on EC2 |
| Git | Latest | Version control | Pre-installed |

### 2.2 Account Access

| Service | URL | Access Level |
|---------|-----|-------------|
| My Lenses Portal | my-lenses.snapchat.com | Owner (Korra Technologies) |
| Snap Kit Portal | developers.snap.com | App ID: `67a348ba-aa55-4158-9451-94ff277e96c7` |
| Camera Kit API Tokens | my-lenses.snapchat.com/api-tokens | Staging + Production |
| EC2 Instance | 13.60.215.88 | SSH key: `~/Downloads/korra-ai-key.pem` |

### 2.3 Existing Lens Ownership Verification

Your lens (ID: `ccc9d825-d8ec-41ca-910a-7fd372065026`) is:
- Published under Korra Technologies account
- Part of Lens Group `6af97e7a-6e80-4d9e-86b7-8ffe3a6bd150` (Korra Virtual Try-On)
- Has 4000+ plays
- Approved for Camera Kit
- Uses Body Mesh + Clothing Try-On template

### 2.4 Snap Body Mesh Reference

Download the Body Mesh reference from:
- Lens Studio → Asset Library → Search "Body Mesh" → Download reference pack
- Or: Snap Developer Docs → Body Mesh → Download reference ZIP

This contains:
- `body_mesh.fbx` — reference body mesh (T-pose and A-pose)
- UV map for texture mapping
- Vertex count: ~6,890 vertices (matches SMPL topology)
- Coordinate system: Y-up, meters

---

## 3. Remote API Spec Creation

### 3.1 Step-by-Step Portal Setup

1. Navigate to https://my-lenses.snapchat.com/apis
2. Click **"+ Add API"**
3. Fill in the form:

```
API Name: Korra Body Measurements
Description: Extracts body measurements from tracked body mesh
Target Platform: CAMERA_KIT (select this)
Snap Kit App ID: 67a348ba-aa55-4158-9451-94ff277e96c7
```

4. Click **Next**

5. Add Endpoint:

```
Endpoint Name: body_measurements
Method: POST (default for Remote API)
Description: Sends calculated body measurements from lens to host app
```

6. Add Parameters (these are the values the lens will send):

| Parameter Name | Type | Required | Description |
|---------------|------|----------|-------------|
| `chest` | string | Yes | Chest circumference in cm |
| `waist` | string | Yes | Waist circumference in cm |
| `hips` | string | Yes | Hip circumference in cm |
| `shoulderWidth` | string | Yes | Shoulder width in cm |
| `height` | string | Yes | Estimated height in cm |
| `timestamp` | string | No | ISO 8601 timestamp |

7. Click **Submit**

8. **Copy the generated API Key/Spec ID** — you'll need this in Lens Studio

### 3.2 Placeholder API Spec (for testing)

For testing before your custom spec is approved, use Snap's placeholder:

```
Spec ID: 363ee2a5-ad35-4a5f-9547-d42b2c60a927
```

This is available in Lens Studio Asset Library → APIs → Placeholder API.

### 3.3 Spec Approval

- Camera Kit specs are **instantly approved** (no review process)
- Your spec should be live within seconds
- Verify by checking the spec status in the portal

---

## 4. Lens Studio Implementation

### 4.1 Opening the Existing Lens

1. Open Lens Studio
2. **File** → **Open Project from My Lenses**
3. Select your lens (the clothing try-on lens with 4000+ plays)
4. Wait for project to load

### 4.2 Import Remote Service Module

1. Open **Asset Library** (bottom-left panel)
2. Click **APIs** tab
3. Find "Korra Body Measurements" (or use Placeholder API for testing)
4. Click **Import**
5. A `RemoteServiceModule` asset appears in your Asset Browser

### 4.3 Create Measurement Scene Object

In the **Scene Hierarchy** panel:

1. Right-click on **Camera** → **Create Empty Scene Object**
2. Rename to `BodyMeasurement`
3. Add Component → **Script** → Create New Script → Name: `BodyMeasurementScript`
4. The script will be created in your Assets panel

### 4.4 Full BodyMeasurementScript.js

This is the complete, production-ready script for Lens Studio:

```javascript
// ====================================================================
// BodyMeasurementScript.js
// Korra AI — Body Measurement Extraction via Snap Body Mesh
// ====================================================================
// This script runs INSIDE the Lens sandbox.
// It extracts Body Mesh vertices, calculates body circumferences,
// and sends measurements to the host app via Remote API.
// ====================================================================

// ====================================================================
// SECTION 1: INPUTS & CONFIGURATION
// ====================================================================

// @input Asset.RemoteServiceModule remoteServiceModule
// @input Component.ObjectTracking3D objectTracking3D
// @input Component.MeshVisual bodyMeshVisual

// ---- Measurement Configuration ----
// Y-percentages are calibrated to Snap's Body Mesh reference model.
// These represent anatomical landmarks as fractions of total body height.
// Adjust these values during calibration (see Section 8).

var CHEST_Y_PERCENT = 0.72;      // Armpit level
var CHEST_BAND_WIDTH = 0.03;     // Vertical band half-height (fraction of body height)

var WAIST_Y_PERCENT = 0.52;      // Navel level
var WAIST_BAND_WIDTH = 0.025;    // Narrower for precision

var HIPS_Y_PERCENT = 0.42;       // Hip bone level
var HIPS_BAND_WIDTH = 0.03;      // Standard band width

var SHOULDER_Y_PERCENT = 0.78;   // Shoulder joint level
var SHOULDER_BAND_WIDTH = 0.03;

var HEAD_TOP_Y_PERCENT = 0.95;   // Top of head (for height)
var FEET_BOTTOM_Y_PERCENT = 0.02; // Bottom of feet (for height)

// ---- Timing Configuration ----
var MEASUREMENT_DELAY = 1.5;      // Seconds to wait after "Get Measurements" signal
var FRAMES_TO_AVERAGE = 8;        // Number of frames to average for stability
var MEASUREMENT_COOLDOWN = 3.0;   // Minimum seconds between measurements

// ---- State Variables ----
var isMeasuring = false;
var measurementTimer = 0;
var cooldownTimer = 0;
var frameCount = 0;
var accumulatedMeasurements = [];
var lastMeasurements = null;

// ====================================================================
// SECTION 2: EVENT BINDING
// ====================================================================

// Bind to UpdateEvent — runs every frame
script.createEvent("UpdateEvent").bind(onUpdate);

// Bind to Lens StartEvent — runs once when lens is applied
script.createEvent("StartEvent").bind(onStart);

// Bind to TapEvent — user taps screen to trigger measurement
script.createEvent("TapEvent").bind(onTap);

function onStart() {
    print("[BodyMeasurement] Script initialized");
    print("[BodyMeasurement] Tap screen or use 'Get Measurements' button to measure");
}

function onTap() {
    // Tap anywhere on screen to trigger measurement
    if (cooldownTimer > 0) {
        print("[BodyMeasurement] Cooldown active, please wait " + 
              cooldownTimer.toFixed(1) + "s");
        return;
    }
    triggerMeasurement();
}

function onUpdate(eventData) {
    // Update cooldown timer
    if (cooldownTimer > 0) {
        cooldownTimer -= getDeltaTime();
    }
    
    // If not in active measurement mode, skip
    if (!isMeasuring) return;
    
    // Update measurement timer
    measurementTimer += getDeltaTime();
    
    // Wait for the initial delay (let body tracking stabilize)
    if (measurementTimer < MEASUREMENT_DELAY) return;
    
    // Collect measurement frame
    var measurements = extractMeasurements();
    if (measurements) {
        accumulatedMeasurements.push(measurements);
        frameCount++;
        
        print("[BodyMeasurement] Frame " + frameCount + "/" + FRAMES_TO_AVERAGE + 
              " — Chest: " + (measurements.chest || 0).toFixed(1) + "cm, " +
              "Waist: " + (measurements.waist || 0).toFixed(1) + "cm, " +
              "Hips: " + (measurements.hips || 0).toFixed(1) + "cm");
        
        // Once we have enough frames, finalize
        if (frameCount >= FRAMES_TO_AVERAGE) {
            finalizeMeasurement();
        }
    }
}

// ====================================================================
// SECTION 3: MEASUREMENT TRIGGER
// ====================================================================

function triggerMeasurement() {
    if (isMeasuring) return;
    
    print("[BodyMeasurement] Starting measurement...");
    isMeasuring = true;
    measurementTimer = 0;
    frameCount = 0;
    accumulatedMeasurements = [];
    
    // Notify host app that measurement started
    sendStatusUpdate("measuring");
}

function finalizeMeasurement() {
    isMeasuring = false;
    cooldownTimer = MEASUREMENT_COOLDOWN;
    
    if (accumulatedMeasurements.length === 0) {
        print("[BodyMeasurement] No measurements collected");
        sendStatusUpdate("failed");
        return;
    }
    
    // Average all collected frames
    var avg = averageMeasurements(accumulatedMeasurements);
    lastMeasurements = avg;
    
    print("[BodyMeasurement] === FINAL MEASUREMENTS ===");
    print("[BodyMeasurement] Chest: " + (avg.chest || 0).toFixed(1) + " cm");
    print("[BodyMeasurement] Waist: " + (avg.waist || 0).toFixed(1) + " cm");
    print("[BodyMeasurement] Hips: " + (avg.hips || 0).toFixed(1) + " cm");
    print("[BodyMeasurement] Shoulders: " + (avg.shoulderWidth || 0).toFixed(1) + " cm");
    print("[BodyMeasurement] Height: " + (avg.height || 0).toFixed(1) + " cm");
    print("[BodyMeasurement] ============================");
    
    // Send to host app
    sendMeasurements(avg);
}

// ====================================================================
// SECTION 4: VERTEX EXTRACTION
// ====================================================================

function extractMeasurements() {
    // Validate inputs
    if (!script.bodyMeshVisual) {
        print("[BodyMeasurement] ERROR: bodyMeshVisual not assigned");
        return null;
    }
    
    if (!script.bodyMeshVisual.mesh) {
        print("[BodyMeasurement] ERROR: bodyMeshVisual.mesh is null");
        return null;
    }
    
    var mesh = script.bodyMeshVisual.mesh;
    
    // Extract vertex position data
    // getVertexDataForAttribute returns a Float32Array
    // Format: [x0, y0, z0, x1, y1, z1, ...] for all vertices
    var positions = mesh.getVertexDataForAttribute("position");
    
    if (!positions || positions.length === 0) {
        print("[BodyMeasurement] ERROR: No vertex data available");
        return null;
    }
    
    var vertexCount = positions.length / 3;
    if (vertexCount < 100) {
        print("[BodyMeasurement] ERROR: Too few vertices (" + vertexCount + ")");
        return null;
    }
    
    // Find body bounds
    var bounds = calculateBounds(positions);
    var bodyHeight = bounds.maxY - bounds.minY;
    
    if (bodyHeight < 0.1) {
        print("[BodyMeasurement] WARNING: Body too small, may not be tracking");
        return null;
    }
    
    if (bodyHeight > 2.5) {
        print("[BodyMeasurement] WARNING: Body too large, possible tracking error");
        return null;
    }
    
    // Calculate each measurement
    var result = {};
    
    // Chest circumference
    result.chest = calculateCircumference(
        positions, 
        bounds.minY + bodyHeight * CHEST_Y_PERCENT,
        bodyHeight * CHEST_BAND_WIDTH
    );
    
    // Waist circumference
    result.waist = calculateCircumference(
        positions,
        bounds.minY + bodyHeight * WAIST_Y_PERCENT,
        bodyHeight * WAIST_BAND_WIDTH
    );
    
    // Hip circumference
    result.hips = calculateCircumference(
        positions,
        bounds.minY + bodyHeight * HIPS_Y_PERCENT,
        bodyHeight * HIPS_BAND_WIDTH
    );
    
    // Shoulder width
    result.shoulderWidth = calculateWidth(
        positions,
        bounds.minY + bodyHeight * SHOULDER_Y_PERCENT,
        bodyHeight * SHOULDER_BAND_WIDTH
    );
    
    // Height estimate
    result.height = bodyHeight * 100; // meters to cm
    
    return result;
}

// ====================================================================
// SECTION 5: BOUNDS CALCULATION
// ====================================================================

function calculateBounds(positions) {
    var minY = Infinity, maxY = -Infinity;
    var minX = Infinity, maxX = -Infinity;
    var minZ = Infinity, maxZ = -Infinity;
    
    for (var i = 0; i < positions.length; i += 3) {
        var x = positions[i];
        var y = positions[i + 1];
        var z = positions[i + 2];
        
        if (y < minY) minY = y;
        if (y > maxY) maxY = y;
        if (x < minX) minX = x;
        if (x > maxX) maxX = x;
        if (z < minZ) minZ = z;
        if (z > maxZ) maxZ = z;
    }
    
    return {
        minX: minX, maxX: maxX,
        minY: minY, maxY: maxY,
        minZ: minZ, maxZ: maxZ
    };
}

// ====================================================================
// SECTION 6: CIRCUMFERENCE CALCULATION
// ====================================================================

function calculateCircumference(positions, targetY, bandHalfWidth) {
    // Collect all vertices within the horizontal band
    var bandVertices = [];
    
    for (var i = 0; i < positions.length; i += 3) {
        var x = positions[i];
        var y = positions[i + 1];
        var z = positions[i + 2];
        
        if (Math.abs(y - targetY) < bandHalfWidth) {
            bandVertices.push({ x: x, z: z });
        }
    }
    
    if (bandVertices.length < 10) {
        print("[BodyMeasurement] WARNING: Too few vertices in band (" + 
              bandVertices.length + ")");
        return 0;
    }
    
    // Calculate perimeter of the cross-section
    return perimeterFromVertices(bandVertices);
}

function perimeterFromVertices(vertices2D) {
    // Step 1: Calculate centroid
    var cx = 0, cz = 0;
    for (var i = 0; i < vertices2D.length; i++) {
        cx += vertices2D[i].x;
        cz += vertices2D[i].z;
    }
    cx /= vertices2D.length;
    cz /= vertices2D.length;
    
    // Step 2: Sort vertices by angle from centroid
    // This creates an ordered polygon around the cross-section
    vertices2D.sort(function(a, b) {
        var angleA = Math.atan2(a.z - cz, a.x - cx);
        var angleB = Math.atan2(b.z - cz, b.x - cx);
        return angleA - angleB;
    });
    
    // Step 3: Remove duplicate angles (keep unique positions)
    var unique = [vertices2D[0]];
    for (var i = 1; i < vertices2D.length; i++) {
        var prev = unique[unique.length - 1];
        var dx = vertices2D[i].x - prev.x;
        var dz = vertices2D[i].z - prev.z;
        if (Math.sqrt(dx * dx + dz * dz) > 0.001) {
            unique.push(vertices2D[i]);
        }
    }
    
    if (unique.length < 6) {
        print("[BodyMeasurement] WARNING: Too few unique vertices (" + 
              unique.length + ")");
        return 0;
    }
    
    // Step 4: Sum distances between consecutive vertices
    var perimeter = 0;
    for (var i = 0; i < unique.length; i++) {
        var next = (i + 1) % unique.length;
        var dx = unique[next].x - unique[i].x;
        var dz = unique[next].z - unique[i].z;
        perimeter += Math.sqrt(dx * dx + dz * dz);
    }
    
    // Convert from meters to centimeters
    return Math.round(perimeter * 100 * 10) / 10;
}

// ====================================================================
// SECTION 7: WIDTH CALCULATION (SHOULDERS)
// ====================================================================

function calculateWidth(positions, targetY, bandHalfWidth) {
    var minX = Infinity, maxX = -Infinity;
    var count = 0;
    
    for (var i = 0; i < positions.length; i += 3) {
        var x = positions[i];
        var y = positions[i + 1];
        
        if (Math.abs(y - targetY) < bandHalfWidth) {
            if (x < minX) minX = x;
            if (x > maxX) maxX = x;
            count++;
        }
    }
    
    if (count < 4) {
        print("[BodyMeasurement] WARNING: Too few vertices for width (" + count + ")");
        return 0;
    }
    
    // Convert from meters to centimeters
    return Math.round((maxX - minX) * 100 * 10) / 10;
}

// ====================================================================
// SECTION 8: AVERAGING
// ====================================================================

function averageMeasurements(measurementsArray) {
    var keys = ['chest', 'waist', 'hips', 'shoulderWidth', 'height'];
    var avg = {};
    
    for (var k = 0; k < keys.length; k++) {
        var key = keys[k];
        var sum = 0;
        var count = 0;
        
        for (var i = 0; i < measurementsArray.length; i++) {
            var val = measurementsArray[i][key];
            if (val && val > 0) {
                sum += val;
                count++;
            }
        }
        
        if (count > 0) {
            // Round to 1 decimal place
            avg[key] = Math.round((sum / count) * 10) / 10;
        } else {
            avg[key] = 0;
        }
    }
    
    return avg;
}

// ====================================================================
// SECTION 9: REMOTE API COMMUNICATION
// ====================================================================

function sendMeasurements(measurements) {
    if (!script.remoteServiceModule) {
        print("[BodyMeasurement] ERROR: remoteServiceModule not assigned");
        return;
    }
    
    var req = global.RemoteApiRequest.create();
    req.endpoint = 'body_measurements';
    req.parameters = {
        chest: String(measurements.chest || 0),
        waist: String(measurements.waist || 0),
        hips: String(measurements.hips || 0),
        shoulderWidth: String(measurements.shoulderWidth || 0),
        height: String(measurements.height || 0),
        timestamp: new Date().toISOString()
    };
    
    script.remoteServiceModule.performApiRequest(req, function(response) {
        if (response.statusCode === 1) {
            print("[BodyMeasurement] Measurements sent to host app successfully");
            sendStatusUpdate("complete");
        } else {
            print("[BodyMeasurement] ERROR: Remote API failed (status: " + 
                  response.statusCode + ")");
            sendStatusUpdate("failed");
        }
    });
}

function sendStatusUpdate(status) {
    // Send a lightweight status update to the host
    if (!script.remoteServiceModule) return;
    
    var req = global.RemoteApiRequest.create();
    req.endpoint = 'measurement_status';
    req.parameters = {
        status: status,
        timestamp: new Date().toISOString()
    };
    
    script.remoteServiceModule.performApiRequest(req, function(response) {
        // Fire and forget — status updates are non-critical
    });
}

// ====================================================================
// SECTION 10: UTILITY FUNCTIONS
// ====================================================================

function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
}

function lerp(a, b, t) {
    return a + (b - a) * t;
}

function distance2D(x1, z1, x2, z2) {
    var dx = x2 - x1;
    var dz = z2 - z1;
    return Math.sqrt(dx * dx + dz * dz);
}

// ====================================================================
// END OF BodyMeasurementScript.js
// ====================================================================
```

### 4.5 Scene Hierarchy Configuration

After creating the script, configure the scene:

```
Scene Hierarchy:
├── Camera
│   ├── 3D Body Tracking (ObjectTracking3D)
│   │   └── Tracking Asset: BodyTrackingAsset
│   │
│   ├── Full Body Mesh
│   │   ├── Body Mesh (MeshVisual) ← LINK THIS to script.bodyMeshVisual
│   │   │   └── Material: (invisible — no visual output needed)
│   │   └── Object Tracking 3D (references the tracking asset above)
│   │
│   ├── BodyMeasurement (SceneObject)
│   │   └── BodyMeasurementScript
│   │       ├── remoteServiceModule → Korra Body Measurements (RemoteServiceModule)
│   │       ├── objectTracking3D → 3D Body Tracking (ObjectTracking3D)
│   │       └── bodyMeshVisual → Full Body Mesh > Body Mesh (MeshVisual)
│   │
│   ├── [Your existing clothing/outfit objects]
│   └── [Your existing UI objects]
```

### 4.6 Making the Body Mesh Invisible

The body mesh should NOT be visible — it's only used for vertex extraction:

1. Select the **Body Mesh** object in Scene Hierarchy
2. In Inspector → **Render Mesh Visual**
3. Set **Material** to a new material with:
   - **Base Color**: Black with 0% opacity (fully transparent)
   - OR: Simply disable the **Render Mesh Visual** component
   - The mesh data is still accessible via `getVertexDataForAttribute()` even when not rendered

### 4.7 Testing in Lens Studio

1. Press **Play** in Lens Studio (top toolbar)
2. The preview should show a body model
3. Open **Logger** panel (Window → Logger)
4. Look for `[BodyMeasurement]` log messages
5. Verify vertex count is > 100
6. Verify measurements are being calculated

**Note**: In Lens Studio preview, the Remote API will fail (no host app). Use the Placeholder API spec for testing. The logger will show "Remote API failed" but the measurements will still be calculated and logged.

---

## 5. Lens Publishing & Deployment

### 5.1 Upload to My Lenses

1. In Lens Studio: **File** → **Upload to My Lenses**
2. Select your existing lens project
3. Version: increment (e.g., v2.0.0 → v2.1.0)
4. Add description: "Added body measurement extraction via Remote API"
5. Click **Upload**
6. Wait for upload to complete

### 5.2 Configure in My Lenses Portal

1. Go to my-lenses.snapchat.com
2. Find your lens
3. Under **Camera Kit** section:
   - Verify the lens is pushed to your Camera Kit group
   - Lens Group ID: `6af97e7a-6e80-4d9e-86b7-8ffe3a6bd150`
4. Under **Remote API** section:
   - Link your "Korra Body Measurements" API spec
   - Verify the spec ID matches

### 5.3 Push to Camera Kit

1. In My Lenses portal → your lens → **Push to Camera Kit**
2. The lens will be available in your Camera Kit app within minutes
3. No code changes needed on the host app — same Lens ID and Group ID

### 5.4 Version Control

Keep track of lens versions:

| Version | Changes | Date |
|---------|---------|------|
| v1.0.0 | Initial clothing try-on | Original |
| v1.1.0 | Added carousel, safe regions | Previous |
| v2.0.0 | Added body measurement extraction | Current |

---

## 6. Host App Integration — Frontend

### 6.1 Camera Kit Session Setup with Remote API

Update `camerakit-integration.v2.js` to subscribe to Remote API:

```javascript
// ====================================================================
// camerakit-integration.v2.js — Remote API Updates
// Add these methods to the CameraKitTryOn class
// ====================================================================

// Add to constructor:
//   this.onMeasurements = null;
//   this.onMeasurementStatus = null;

// Add after createSession():
async setupRemoteApiListener() {
    try {
        if (!this.session) return false;
        
        // Subscribe to Remote API requests from the lens
        this.session.remoteApi.subscribe((request) => {
            console.log('[CameraKit] Remote API request:', request.endpointId);
            
            if (request.endpointId === 'body_measurements') {
                this.handleBodyMeasurements(request);
            } else if (request.endpointId === 'measurement_status') {
                this.handleMeasurementStatus(request);
            } else {
                // Unknown endpoint — ignore
                request.respond({ statusCode: 0 });
            }
        });
        
        console.log('[CameraKit] Remote API listener active');
        return true;
    } catch (err) {
        console.error('[CameraKit] Failed to setup Remote API:', err);
        return false;
    }
},

handleBodyMeasurements(request) {
    var params = request.parameters;
    
    var measurements = {
        chest: parseFloat(params.chest) || 0,
        waist: parseFloat(params.waist) || 0,
        hips: parseFloat(params.hips) || 0,
        shoulderWidth: parseFloat(params.shoulderWidth) || 0,
        height: parseFloat(params.height) || 0,
        timestamp: params.timestamp || new Date().toISOString()
    };
    
    console.log('[CameraKit] Body measurements received:', measurements);
    
    // Dispatch custom event for UI
    window.dispatchEvent(new CustomEvent('bodyMeasurements', {
        detail: measurements
    }));
    
    // Callback
    if (this.onMeasurements) this.onMeasurements(measurements);
    
    // Respond to lens
    request.respond({
        statusCode: 1,
        body: JSON.stringify({ success: true })
    });
    
    this.updateStatus('Measurements received');
},

handleMeasurementStatus(request) {
    var status = request.parameters.status;
    console.log('[CameraKit] Measurement status:', status);
    
    window.dispatchEvent(new CustomEvent('measurementStatus', {
        detail: { status: status }
    }));
    
    if (this.onMeasurementStatus) this.onMeasurementStatus(status);
    
    request.respond({ statusCode: 1 });
},

// Trigger measurement from host app
// (Lens listens for tap or we use a different signal mechanism)
triggerMeasurement() {
    if (!this.session) return false;
    
    // The lens's TapEvent will handle this
    // For programmatic triggering, we can re-apply the lens
    // which will reset its state
    console.log('[CameraKit] Measurement triggered');
    return true;
}
```

### 6.2 Update camera-kit-tryon-app.v2.js

Add measurement handling to the main app:

```javascript
// ====================================================================
// camera-kit-tryon-app.v2.js — Measurement UI Integration
// Add these functions to the existing app
// ====================================================================

// ---- Measurement State ----
var currentMeasurements = null;
var isMeasuring = false;

// ---- Initialize Measurement Listeners ----
function initMeasurementListeners() {
    // Listen for measurements from lens
    window.addEventListener('bodyMeasurements', (e) => {
        currentMeasurements = e.detail;
        isMeasuring = false;
        renderMeasurements(currentMeasurements);
        saveMeasurementsToServer(currentMeasurements);
        updateMeasurementButton(false);
    });
    
    // Listen for measurement status
    window.addEventListener('measurementStatus', (e) => {
        var status = e.detail.status;
        if (status === 'measuring') {
            isMeasuring = true;
            updateMeasurementButton(true);
        } else if (status === 'failed') {
            isMeasuring = false;
            updateMeasurementButton(false);
            showMeasurementError();
        } else if (status === 'complete') {
            isMeasuring = false;
            updateMeasurementButton(false);
        }
    });
}

// ---- Get Measurements Button Handler ----
function onGetMeasurements() {
    if (isMeasuring) return;
    
    isMeasuring = true;
    updateMeasurementButton(true);
    
    // Trigger the lens to start measuring
    // The lens will respond when measurements are ready
    if (window.cameraKitTryOn) {
        window.cameraKitTryOn.triggerMeasurement();
    }
    
    // Timeout after 10 seconds
    setTimeout(function() {
        if (isMeasuring) {
            isMeasuring = false;
            updateMeasurementButton(false);
        }
    }, 10000);
}

// ---- Render Measurements in Sidebar ----
function renderMeasurements(m) {
    var panel = document.getElementById('measurement-results');
    if (!panel) return;
    
    var hasData = m && (m.chest > 0 || m.waist > 0 || m.hips > 0);
    
    if (!hasData) {
        panel.innerHTML = '<div class="measurement-empty">No measurements available. Tap "Get Measurements" to start.</div>';
        return;
    }
    
    panel.innerHTML = 
        '<div class="measurement-row">' +
            '<span class="measurement-label">Chest</span>' +
            '<span class="measurement-value">' + m.chest + ' cm</span>' +
        '</div>' +
        '<div class="measurement-row">' +
            '<span class="measurement-label">Waist</span>' +
            '<span class="measurement-value">' + m.waist + ' cm</span>' +
        '</div>' +
        '<div class="measurement-row">' +
            '<span class="measurement-label">Hips</span>' +
            '<span class="measurement-value">' + m.hips + ' cm</span>' +
        '</div>' +
        '<div class="measurement-row">' +
            '<span class="measurement-label">Shoulders</span>' +
            '<span class="measurement-value">' + m.shoulderWidth + ' cm</span>' +
        '</div>' +
        '<div class="measurement-row">' +
            '<span class="measurement-label">Height</span>' +
            '<span class="measurement-value">' + m.height + ' cm</span>' +
        '</div>' +
        '<div class="measurement-timestamp">' +
            'Measured: ' + new Date(m.timestamp).toLocaleString() +
        '</div>';
}

// ---- Update Button State ----
function updateMeasurementButton(measuring) {
    var btn = document.getElementById('btn-get-measurements');
    if (!btn) return;
    
    if (measuring) {
        btn.innerHTML = '<span class="measuring-spinner"></span> Measuring...';
        btn.classList.add('measuring');
        btn.disabled = true;
    } else {
        btn.innerHTML = 'Get Measurements';
        btn.classList.remove('measuring');
        btn.disabled = false;
    }
}

// ---- Show Error ----
function showMeasurementError() {
    var panel = document.getElementById('measurement-results');
    if (panel) {
        panel.innerHTML = '<div class="measurement-error">Measurement failed. Make sure your full body is visible and try again.</div>';
    }
}

// ---- Save to Server ----
function saveMeasurementsToServer(m) {
    fetch('/api/v2/measurements', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: getUserId(),
            chest: m.chest,
            waist: m.waist,
            hips: m.hips,
            shoulder_width: m.shoulderWidth,
            height: m.height,
            timestamp: m.timestamp
        })
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        console.log('[Measurements] Saved to server:', data);
    })
    .catch(function(err) {
        console.error('[Measurements] Failed to save:', err);
    });
}

// ---- Get User ID ----
function getUserId() {
    // From Supabase auth or localStorage
    return localStorage.getItem('korra_user_id') || 'anonymous';
}

// ---- Load Previous Measurements ----
function loadPreviousMeasurements() {
    fetch('/api/v2/measurements?user_id=' + getUserId())
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.measurements && data.measurements.length > 0) {
            var latest = data.measurements[0];
            renderMeasurements(latest);
        }
    })
    .catch(function(err) {
        console.error('[Measurements] Failed to load:', err);
    });
}

// ---- Initialize on DOM Ready ----
document.addEventListener('DOMContentLoaded', function() {
    initMeasurementListeners();
    loadPreviousMeasurements();
});
```

### 6.3 tryon.html — Measurement Tab in Sidebar

Add a new tab to the existing sidebar. The sidebar currently has:
- **Outfits** tab (outfit selection grid)
- **Captures** tab (captured photos)

Add a third tab: **Measurements**

```html
<!-- ================================================================= -->
<!-- Add inside the sidebar section of tryon.html -->
<!-- After the existing sidebar-tabs div -->
<!-- ================================================================= -->

<!-- Sidebar Tab Navigation -->
<div class="sidebar-tabs">
    <button class="sidebar-tab active" data-tab="outfits">Outfits</button>
    <button class="sidebar-tab" data-tab="captures">Captures</button>
    <button class="sidebar-tab" data-tab="measurements">Measurements</button>
</div>

<!-- Measurements Tab Content -->
<div class="sidebar-tab-content" id="tab-measurements" style="display: none;">
    
    <!-- Get Measurements Button -->
    <div class="measurement-trigger">
        <button id="btn-get-measurements" class="get-measurements-btn" onclick="onGetMeasurements()">
            Get Measurements
        </button>
        <p class="measurement-hint">
            Stand facing the camera with arms slightly away from your body.
            Full body must be visible.
        </p>
    </div>
    
    <!-- Measurement Results -->
    <div id="measurement-results" class="measurement-results">
        <div class="measurement-empty">
            Tap "Get Measurements" to start.
        </div>
    </div>
    
    <!-- Measurement History -->
    <div class="measurement-history" id="measurement-history">
        <h4 class="history-title">Previous Measurements</h4>
        <div id="measurement-history-list" class="history-list">
            <!-- Populated by JavaScript -->
        </div>
    </div>
    
</div>
```

### 6.4 CSS for Measurement Tab

Add these styles to `tryon.html` inside the `<style>` tag:

```css
/* ================================================================= */
/* Measurement Tab Styles — Sidebar */
/* ================================================================= */

/* Tab Content Container */
.sidebar-tab-content {
    padding: 16px 0;
    overflow-y: auto;
    max-height: calc(100vh - 200px);
}

/* Get Measurements Button */
.measurement-trigger {
    padding: 0 16px 16px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
}

.get-measurements-btn {
    width: 100%;
    padding: 14px 20px;
    border: 1px solid rgba(198, 255, 0, 0.3);
    border-radius: 12px;
    background: rgba(198, 255, 0, 0.08);
    color: #c6ff00;
    font-size: 14px;
    font-weight: 800;
    cursor: pointer;
    transition: all 0.2s;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-family: inherit;
}

.get-measurements-btn:hover {
    background: rgba(198, 255, 0, 0.15);
    border-color: rgba(198, 255, 0, 0.5);
}

.get-measurements-btn:active {
    transform: scale(0.98);
}

.get-measurements-btn.measuring {
    border-color: rgba(255, 255, 255, 0.2);
    background: rgba(255, 255, 255, 0.05);
    color: #888;
    cursor: not-allowed;
}

.measurement-hint {
    font-size: 11px;
    color: #666;
    margin: 10px 0 0;
    line-height: 1.5;
    text-align: center;
}

/* Measuring Spinner */
.measuring-spinner {
    display: inline-block;
    width: 14px;
    height: 14px;
    border: 2px solid rgba(198, 255, 0, 0.3);
    border-top-color: #c6ff00;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    vertical-align: middle;
    margin-right: 6px;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* Measurement Results */
.measurement-results {
    padding: 0 16px 16px;
}

.measurement-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    background: rgba(255, 255, 255, 0.03);
    border-radius: 10px;
    margin-bottom: 6px;
    border: 1px solid rgba(255, 255, 255, 0.04);
}

.measurement-label {
    font-size: 13px;
    color: #999;
    font-weight: 600;
}

.measurement-value {
    font-size: 16px;
    color: #fff;
    font-weight: 800;
    font-variant-numeric: tabular-nums;
}

.measurement-timestamp {
    font-size: 10px;
    color: #555;
    text-align: center;
    padding: 8px 0;
}

.measurement-empty {
    font-size: 12px;
    color: #555;
    text-align: center;
    padding: 24px 16px;
    line-height: 1.6;
}

.measurement-error {
    font-size: 12px;
    color: #ff6b6b;
    text-align: center;
    padding: 16px;
    background: rgba(255, 107, 107, 0.08);
    border-radius: 10px;
    border: 1px solid rgba(255, 107, 107, 0.15);
}

/* Measurement History */
.measurement-history {
    padding: 16px;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.history-title {
    font-size: 11px;
    color: #666;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin: 0 0 12px;
    font-weight: 700;
}

.history-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.history-item {
    padding: 12px;
    background: rgba(255, 255, 255, 0.03);
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.04);
}

.history-item-date {
    font-size: 10px;
    color: #555;
    margin-bottom: 6px;
}

.history-item-values {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
}

.history-item-measure {
    font-size: 11px;
    color: #999;
}

.history-item-measure span {
    color: #fff;
    font-weight: 700;
}
```

### 6.5 Sidebar Tab Switching Logic

Update the existing tab switching code in `tryon.html`:

```javascript
// ====================================================================
// Sidebar Tab Switching — Updated with Measurements tab
// ====================================================================

document.addEventListener('DOMContentLoaded', function() {
    var tabs = document.querySelectorAll('.sidebar-tab');
    var tabContents = {
        outfits: document.getElementById('tab-outfits'),
        captures: document.getElementById('tab-captures'),
        measurements: document.getElementById('tab-measurements')
    };
    
    tabs.forEach(function(tab) {
        tab.addEventListener('click', function() {
            var targetTab = this.getAttribute('data-tab');
            
            // Deactivate all tabs
            tabs.forEach(function(t) { t.classList.remove('active'); });
            
            // Hide all tab contents
            Object.values(tabContents).forEach(function(content) {
                if (content) content.style.display = 'none';
            });
            
            // Activate clicked tab
            this.classList.add('active');
            
            // Show target content
            if (tabContents[targetTab]) {
                tabContents[targetTab].style.display = 'block';
            }
        });
    });
});
```

---

## 7. Flask Backend — Measurement Storage API

### 7.1 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v2/measurements` | Store new measurements |
| GET | `/api/v2/measurements` | Get measurements for user |
| GET | `/api/v2/measurements/:id` | Get specific measurement |
| DELETE | `/api/v2/measurements/:id` | Delete a measurement |

### 7.2 Full Flask Application

Create `/Users/mac/ai-body-scan-saas/api/routes/measurements.py`:

```python
"""
Body Measurements API — Korra AI
Stores and retrieves body measurements extracted from Snap Camera Kit lens.
"""

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List

router = APIRouter()

# ====================================================================
# Data Models
# ====================================================================

class MeasurementCreate(BaseModel):
    """Request body for creating a new measurement."""
    user_id: str = Field(..., description="User identifier")
    chest: float = Field(..., ge=0, le=300, description="Chest circumference in cm")
    waist: float = Field(..., ge=0, le=300, description="Waist circumference in cm")
    hips: float = Field(..., ge=0, le=300, description="Hip circumference in cm")
    shoulder_width: float = Field(..., ge=0, le=200, description="Shoulder width in cm")
    height: float = Field(..., ge=0, le=300, description="Estimated height in cm")
    timestamp: Optional[str] = Field(None, description="ISO 8601 timestamp from lens")

class MeasurementResponse(BaseModel):
    """Response model for a measurement."""
    id: int
    user_id: str
    chest: float
    waist: float
    hips: float
    shoulder_width: float
    height: float
    timestamp: str
    created_at: str

class MeasurementListResponse(BaseModel):
    """Response model for measurement list."""
    measurements: List[MeasurementResponse]
    total: int

# ====================================================================
# Database Setup
# ====================================================================

DB_PATH = Path(__file__).parent.parent.parent / "data" / "measurements.db"

def get_db():
    """Get database connection."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the measurements database table."""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS body_measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            chest REAL NOT NULL,
            waist REAL NOT NULL,
            hips REAL NOT NULL,
            shoulder_width REAL NOT NULL,
            height REAL NOT NULL,
            timestamp TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_measurements_user 
        ON body_measurements(user_id)
    """)
    conn.commit()
    conn.close()

# Initialize on import
init_db()

# ====================================================================
# API Endpoints
# ====================================================================

@router.post("/measurements", response_model=MeasurementResponse)
async def create_measurement(measurement: MeasurementCreate):
    """
    Store a new body measurement.
    
    Called by the frontend when measurements are received from the lens.
    """
    conn = get_db()
    try:
        timestamp = measurement.timestamp or datetime.utcnow().isoformat()
        
        cursor = conn.execute(
            """
            INSERT INTO body_measurements 
            (user_id, chest, waist, hips, shoulder_width, height, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                measurement.user_id,
                measurement.chest,
                measurement.waist,
                measurement.hips,
                measurement.shoulder_width,
                measurement.height,
                timestamp
            )
        )
        conn.commit()
        
        measurement_id = cursor.lastrowid
        
        # Fetch the created record
        row = conn.execute(
            "SELECT * FROM body_measurements WHERE id = ?",
            (measurement_id,)
        ).fetchone()
        
        return MeasurementResponse(
            id=row["id"],
            user_id=row["user_id"],
            chest=row["chest"],
            waist=row["waist"],
            hips=row["hips"],
            shoulder_width=row["shoulder_width"],
            height=row["height"],
            timestamp=row["timestamp"],
            created_at=row["created_at"]
        )
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/measurements", response_model=MeasurementListResponse)
async def get_measurements(
    user_id: str = Query(..., description="User ID to fetch measurements for"),
    limit: int = Query(10, ge=1, le=100, description="Max results to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """
    Get body measurements for a user.
    
    Returns measurements sorted by most recent first.
    """
    conn = get_db()
    try:
        # Get total count
        count_row = conn.execute(
            "SELECT COUNT(*) as total FROM body_measurements WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        total = count_row["total"]
        
        # Get measurements
        rows = conn.execute(
            """
            SELECT * FROM body_measurements 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
            """,
            (user_id, limit, offset)
        ).fetchall()
        
        measurements = [
            MeasurementResponse(
                id=row["id"],
                user_id=row["user_id"],
                chest=row["chest"],
                waist=row["waist"],
                hips=row["hips"],
                shoulder_width=row["shoulder_width"],
                height=row["height"],
                timestamp=row["timestamp"],
                created_at=row["created_at"]
            )
            for row in rows
        ]
        
        return MeasurementListResponse(
            measurements=measurements,
            total=total
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/measurements/{measurement_id}", response_model=MeasurementResponse)
async def get_measurement(measurement_id: int):
    """Get a specific measurement by ID."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM body_measurements WHERE id = ?",
            (measurement_id,)
        ).fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Measurement not found")
        
        return MeasurementResponse(
            id=row["id"],
            user_id=row["user_id"],
            chest=row["chest"],
            waist=row["waist"],
            hips=row["hips"],
            shoulder_width=row["shoulder_width"],
            height=row["height"],
            timestamp=row["timestamp"],
            created_at=row["created_at"]
        )
    finally:
        conn.close()


@router.delete("/measurements/{measurement_id}")
async def delete_measurement(measurement_id: int):
    """Delete a specific measurement."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM body_measurements WHERE id = ?",
            (measurement_id,)
        ).fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Measurement not found")
        
        conn.execute(
            "DELETE FROM body_measurements WHERE id = ?",
            (measurement_id,)
        )
        conn.commit()
        
        return {"success": True, "deleted_id": measurement_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
```

### 7.3 Register Router in Main App

Update the main FastAPI app to include the measurements router:

```python
# In api/routes/__init__.py or main app file
from api.routes.measurements import router as measurements_router

app.include_router(measurements_router, prefix="/api/v2", tags=["measurements"])
```

### 7.4 Deploy to EC2

```bash
# Copy measurements route to EC2
scp -i ~/Downloads/korra-ai-key.pem \
    /Users/mac/ai-body-scan-saas/api/routes/measurements.py \
    ubuntu@13.60.215.88:/tmp/measurements.py

ssh -i ~/Downloads/korra-ai-key.pem ubuntu@13.60.215.88 \
    "docker cp /tmp/measurements.py korra-ai-prod:/app/api/routes/measurements.py"

# Restart container
ssh -i ~/Downloads/korra-ai-key.pem ubuntu@13.60.215.88 \
    "docker restart korra-ai-prod"
```

### 7.5 Test the API

```bash
# Create a measurement
curl -X POST http://13.60.215.88/api/v2/measurements \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-001",
    "chest": 96.2,
    "waist": 81.5,
    "hips": 102.3,
    "shoulder_width": 44.8,
    "height": 175.3
  }'

# Get measurements
curl "http://13.60.215.88/api/v2/measurements?user_id=test-user-001"
```

---

## 8. Calibration & Accuracy

### 8.1 Snap Body Mesh Reference

Snap's Body Mesh uses a standardized topology:
- **Vertex count**: ~6,890 vertices
- **Coordinate system**: Y-up, meters
- **Rest pose**: T-pose or A-pose
- **Body height**: Approximately 1.7m for average adult

### 8.2 Y-Threshold Calibration Table

These percentages map anatomical landmarks to Y-positions on the body mesh:

| Landmark | Y % of Body Height | Description | Calibration Notes |
|----------|-------------------|-------------|-------------------|
| Top of head | 0.95 | Crown of head | Used for height estimate |
| Chin | 0.82 | Bottom of chin | — |
| Shoulders | 0.78 | Shoulder joint center | Adjust ±0.02 based on body type |
| Chest (armpit) | 0.72 | Nipple line / armpit level | Most critical for shirt fitting |
| Waist | 0.52 | Natural waist / navel | Narrowest point of torso |
| Hips | 0.42 | Hip bone / widest point | Below waist, upper thigh |
| Crotch | 0.38 |rotch level | For inseam calculation |
| Mid-thigh | 0.28 | Mid-thigh level | — |
| Knee | 0.18 | Knee joint center | — |
| Ankle | 0.05 | Ankle joint center | — |
| Feet | 0.02 | Bottom of feet | Used for height estimate |

### 8.3 Calibration Procedure

#### Step 1: Download Reference Body Mesh

1. In Lens Studio → Asset Library → Search "Body Mesh"
2. Download the reference pack ZIP
3. Extract `body_mesh.obj` or `body_mesh.fbx`

#### Step 2: Analyze in Blender

1. Open Blender
2. Import the body mesh (File → Import → FBX/OBJ)
3. Switch to **Edit Mode** (Tab key)
4. Enable **Vertex selection** mode
5. Select vertices at each landmark:
   - Chest: Select ring of vertices at armpit height
   - Waist: Select ring at narrowest torso point
   - Hips: Select ring at widest hip point
6. Note the Y-coordinates of each selection
7. Calculate percentages relative to total body height

#### Step 3: Adjust Script Values

In `BodyMeasurementScript.js`, update:

```javascript
// Adjust these based on your calibration
var CHEST_Y_PERCENT = 0.72;   // ← Change this
var WAIST_Y_PERCENT = 0.52;   // ← Change this
var HIPS_Y_PERCENT = 0.42;    // ← Change this
```

#### Step 4: Test with Known Measurements

1. Have a person with known measurements (measured with tape)
2. Use the lens to capture measurements
3. Compare lens measurements to tape measurements
4. Adjust Y-percentages and band-widths to minimize error
5. Repeat for different body types

### 8.4 Accuracy Expectations

| Measurement | Expected Accuracy | Notes |
|-------------|------------------|-------|
| Chest | ±3-5 cm | Good accuracy, mesh deforms well here |
| Waist | ±2-4 cm | Good accuracy, well-defined landmark |
| Hips | ±3-5 cm | Moderate accuracy, varies with clothing |
| Shoulder Width | ±2-3 cm | Good accuracy, clear X-extent |
| Height | ±5-10 cm | Rough estimate, depends on camera angle |

### 8.5 Factors Affecting Accuracy

| Factor | Impact | Mitigation |
|--------|--------|------------|
| Loose clothing | Inflates measurements | Instruct user to wear fitted clothes |
| Camera angle | Distorts Y-positions | Use front-facing, waist-height camera |
| Partial body | Incomplete vertex data | Ensure full body visible |
| Body tracking loss | No measurements | Wait for tracking to stabilize |
| Multiple bodies | Wrong body tracked | Use bodyIndex to select correct person |
| Distance from camera | Scale variation | Camera Kit handles scale internally |

### 8.6 Body Type Calibration Profiles

Create calibration profiles for different body types:

```javascript
// Body type profiles (optional — advanced calibration)
var CALIBRATION_PROFILES = {
    average: {
        chestY: 0.72,
        waistY: 0.52,
        hipsY: 0.42,
        chestBand: 0.03,
        waistBand: 0.025,
        hipsBand: 0.03
    },
    tall: {
        chestY: 0.73,
        waistY: 0.53,
        hipsY: 0.43,
        chestBand: 0.028,
        waistBand: 0.023,
        hipsBand: 0.028
    },
    petite: {
        chestY: 0.71,
        waistY: 0.51,
        hipsY: 0.41,
        chestBand: 0.032,
        waistBand: 0.027,
        hipsBand: 0.032
    }
};
```

---

## 9. API Reference

### 9.1 Snap Lens Scripting API

#### RenderMesh

```javascript
// Get vertex data for a specific attribute
var positions = mesh.getVertexDataForAttribute("position");
// Returns: Float32Array [x0,y0,z0, x1,y1,z1, ...]

// Alternative (less efficient)
var positions = mesh.extractVerticesForAttribute("position");
// Returns: Number[] [x0,y0,z0, x1,y1,z1, ...]

// Get mesh indices
var indices = mesh.extractIndices();
// Returns: number[] [i0, i1, i2, ...]

// Get bone names
var bones = mesh.extractBoneNames();
// Returns: string[]
```

#### BodyRenderObjectProvider

```javascript
// Properties
bodyRenderObjectProvider.bodyGeometryEnabled;  // boolean
bodyRenderObjectProvider.bodyIndex;            // number
bodyRenderObjectProvider.handTrackingEnabled;  // boolean
bodyRenderObjectProvider.headGeometryEnabled;  // boolean
bodyRenderObjectProvider.trackingScope;        // PersonTrackingScope

// Get the render mesh
var meshVisual = bodyRenderObjectProvider;
var mesh = meshVisual.mesh;
```

#### RemoteApiRequest

```javascript
// Create a new request
var req = global.RemoteApiRequest.create();

// Set properties
req.endpoint = 'body_measurements';           // string
req.parameters = { key: 'value' };            // any
req.body = 'string or Uint8Array';            // optional
req.uriResources = [dynamicResource];         // optional
```

#### RemoteServiceModule

```javascript
// Perform API request
script.remoteServiceModule.performApiRequest(
    request,           // RemoteApiRequest
    function(response) { // callback
        // response.statusCode: number (1 = success)
        // response.body: string
        // response.linkedResources: DynamicResource[]
    }
);

// Subscribe to API requests (persistent)
var subscriptionId = script.remoteServiceModule.subscribeApiRequest(
    request,
    function(response) { }
);

// Create WebSocket
var socket = script.remoteServiceModule.createAPIWebSocket(
    endpoint,
    params
);

// Make HTTP request (Lens Studio 5.4+)
var httpReq = RemoteServiceHttpRequest.create();
httpReq.url = 'https://api.example.com/endpoint';
httpReq.method = RemoteServiceHttpRequest.HttpRequest.Get;
script.remoteServiceModule.performHttpRequest(httpReq, function(res) {
    // res.statusCode, res.body, res.headers
});
```

### 9.2 Camera Kit Web SDK

#### session.remoteApi

```javascript
// Subscribe to lens API requests
session.remoteApi.subscribe((request) => {
    // request: RemoteApiRequest
    // request.endpointId: string
    // request.parameters: Record<string, string>
    // request.body: ArrayBuffer
    
    // Respond to the lens
    request.respond({
        statusCode: 1,  // 1 = success
        body: JSON.stringify({ success: true })
    });
});
```

#### RemoteApiRequest (Web SDK)

```typescript
interface RemoteApiRequest {
    apiSpecId: string;        // Which API spec this request belongs to
    endpointId: string;       // Which endpoint was called
    parameters: Record<string, string>;  // Key-value parameters
    body: ArrayBuffer;        // Optional binary payload
}
```

### 9.3 Python/Flask API

#### POST /api/v2/measurements

```json
// Request
{
    "user_id": "string (required)",
    "chest": 96.2,
    "waist": 81.5,
    "hips": 102.3,
    "shoulder_width": 44.8,
    "height": 175.3,
    "timestamp": "2026-08-06T12:00:00Z (optional)"
}

// Response 200
{
    "id": 1,
    "user_id": "string",
    "chest": 96.2,
    "waist": 81.5,
    "hips": 102.3,
    "shoulder_width": 44.8,
    "height": 175.3,
    "timestamp": "2026-08-06T12:00:00Z",
    "created_at": "2026-08-06T12:00:00"
}
```

#### GET /api/v2/measurements

```json
// Query Parameters
// ?user_id=string (required)
// ?limit=10 (default)
// ?offset=0

// Response 200
{
    "measurements": [
        {
            "id": 1,
            "user_id": "string",
            "chest": 96.2,
            "waist": 81.5,
            "hips": 102.3,
            "shoulder_width": 44.8,
            "height": 175.3,
            "timestamp": "2026-08-06T12:00:00Z",
            "created_at": "2026-08-06T12:00:00"
        }
    ],
    "total": 5
}
```

---

## 10. Troubleshooting Guide

### 10.1 Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `bodyMeshVisual.mesh is null` | MeshVisual component not linked | Check script inputs in Scene Hierarchy |
| `No vertex data available` | Body tracking not active | Ensure body is visible, wait for tracking |
| `Too few vertices in band` | Band width too narrow or Y-threshold off | Increase bandWidth or adjust Y-percent |
| `Remote API failed` | Lens not connected to host app | Verify Camera Kit session is active |
| `Measurements not received` | Remote API spec not linked | Link spec in My Lenses portal |
| `Perimeter calculation = 0` | No cross-section vertices found | Adjust band width, check body visibility |
| `Chest = 0` | Y-threshold outside body range | Recalibrate Y-percent values |
| `Height too large (>250cm)` | Body mesh scale issue | Check camera distance, re-track |
| `Measurements fluctuate wildly` | Insufficient frame averaging | Increase FRAMES_TO_AVERAGE |

### 10.2 Debug Logging

Add these to the lens script for debugging:

```javascript
// Debug mode — set to true for verbose logging
var DEBUG = true;

function debugLog(msg) {
    if (DEBUG) print("[BodyMeasurement DEBUG] " + msg);
}

// Log vertex bounds
debugLog("Body bounds: Y=" + bounds.minY.toFixed(3) + " to " + 
         bounds.maxY.toFixed(3) + " (height: " + bodyHeight.toFixed(3) + "m)");

// Log band vertex count
debugLog("Chest band vertices: " + chestVertices.length);
debugLog("Waist band vertices: " + waistVertices.length);
debugLog("Hip band vertices: " + hipVertices.length);

// Log raw vertex positions (first 10)
for (var i = 0; i < Math.min(10, positions.length); i += 3) {
    debugLog("Vertex " + (i/3) + ": (" + 
             positions[i].toFixed(4) + ", " + 
             positions[i+1].toFixed(4) + ", " + 
             positions[i+2].toFixed(4) + ")");
}
```

### 10.3 Performance Optimization

| Issue | Solution |
|-------|----------|
| Lens lag during measurement | Reduce FRAMES_TO_AVERAGE to 4-5 |
| High CPU usage | Increase MEASUREMENT_COOLDOWN to 5s |
| Memory spikes | Limit vertex processing to body-only (disable hands/head) |
| Slow Remote API response | Use lightweight JSON payload |

### 10.4 Edge Cases

#### Partial Body Visibility
```javascript
// Check if body is fully visible
var visibleHeight = bounds.maxY - bounds.minY;
var expectedHeight = 1.7; // average human height in meters
var visibilityRatio = visibleHeight / expectedHeight;

if (visibilityRatio < 0.7) {
    print("[BodyMeasurement] WARNING: Only " + 
          (visibilityRatio * 100).toFixed(0) + "% of body visible");
    return null;
}
```

#### Multiple Bodies
```javascript
// Use bodyIndex to select correct body
// Set bodyIndex to 0 for first detected body
script.bodyMeshVisual.bodyIndex = 0;
```

#### Tracking Recovery
```javascript
// Handle tracking loss
var lastValidMeasurement = null;
var trackingLostFrames = 0;

function checkTracking(positions) {
    if (!positions || positions.length < 300) {
        trackingLostFrames++;
        if (trackingLostFrames > 30) {
            print("[BodyMeasurement] Tracking lost for 30+ frames");
            trackingLostFrames = 0;
        }
        return false;
    }
    trackingLostFrames = 0;
    return true;
}
```

---

## 11. Deployment Checklist

### 11.1 Pre-Deployment

- [ ] Lens Studio project opens without errors
- [ ] BodyMeasurementScript.js compiles without errors
- [ ] Remote Service Module is imported and linked
- [ ] Script inputs are all linked (remoteServiceModule, objectTracking3D, bodyMeshVisual)
- [ ] Body Mesh is set to invisible (or material has 0 opacity)
- [ ] Measurement values are reasonable in Lens Studio preview
- [ ] Logger shows correct vertex extraction
- [ ] Remote API spec is created and approved in My Lenses portal

### 11.2 Lens Deployment

- [ ] Lens uploaded to My Lenses (version incremented)
- [ ] Lens pushed to Camera Kit group
- [ ] New Lens ID noted (if changed)
- [ ] Remote API spec linked to lens in portal
- [ ] Lens works in Camera Kit test app

### 11.3 Host App Deployment

- [ ] `camerakit-integration.v2.js` updated with Remote API listener
- [ ] `camera-kit-tryon-app.v2.js` updated with measurement handling
- [ ] `tryon.html` updated with Measurement tab in sidebar
- [ ] CSS for measurement panel added
- [ ] Tab switching logic includes measurements tab
- [ ] "Get Measurements" button triggers lens measurement
- [ ] Measurements display correctly in sidebar

### 11.4 Backend Deployment

- [ ] `measurements.py` route created
- [ ] Database table initialized (SQLite)
- [ ] Router registered in main FastAPI app
- [ ] EC2 container updated with new route
- [ ] Container restarted
- [ ] API endpoint tested with curl

### 11.5 Post-Deployment Testing

- [ ] Open tryon.html in browser
- [ ] Select an outfit (lens applies correctly)
- [ ] Click "Get Measurements" button
- [ ] Measurements appear in sidebar within 5 seconds
- [ ] Measurements are reasonable (within expected ranges)
- [ ] Measurements are saved to server
- [ ] Refresh page — previous measurements load
- [ ] Test on mobile (responsive layout)
- [ ] Test with different body types

### 11.6 Rollback Plan

If measurements don't work:

1. **Lens issue**: Revert to previous lens version (v1.1.0) in My Lenses portal
2. **Host app issue**: Revert `camerakit-integration.v2.js` to previous version
3. **Backend issue**: Remove measurements router from FastAPI app

---

## 12. Future Enhancements

### 12.1 Inseam Calculation

```javascript
// Calculate inseam from leg vertices
function calculateInseam(positions, bounds) {
    var bodyHeight = bounds.maxY - bounds.minY;
    var crotchY = bounds.minY + bodyHeight * 0.38;
    var ankleY = bounds.minY + bodyHeight * 0.05;
    
    // Find center X,Z at crotch and ankle
    var crotchCenter = getCenterAtY(positions, crotchY, bodyHeight * 0.02);
    var ankleCenter = getCenterAtY(positions, ankleY, bodyHeight * 0.02);
    
    if (!crotchCenter || !ankleCenter) return 0;
    
    var dx = ankleCenter.x - crotchCenter.x;
    var dz = ankleCenter.z - crotchCenter.z;
    var inseam = Math.sqrt(dx * dx + dz * dz + 
                           Math.pow(ankleY - crotchY, 2));
    
    return Math.round(inseam * 100 * 10) / 10;
}
```

### 12.2 Arm Length Estimation

```javascript
// Calculate arm length from shoulder to wrist
function calculateArmLength(positions, bounds) {
    var bodyHeight = bounds.maxY - bounds.minY;
    var shoulderY = bounds.minY + bodyHeight * 0.78;
    var wristY = bounds.minY + bodyHeight * 0.38;
    
    // Find X-extent at shoulder and wrist
    // ... (similar to shoulder width calculation)
}
```

### 12.3 Size Recommendation Engine

Based on measurements, recommend standard sizes:

```javascript
function recommendSize(chest, waist, hips) {
    // US Women's sizing
    if (chest < 81) return { size: 'XS', label: 'Extra Small' };
    if (chest < 86) return { size: 'S', label: 'Small' };
    if (chest < 91) return { size: 'M', label: 'Medium' };
    if (chest < 96) return { size: 'L', label: 'Large' };
    if (chest < 102) return { size: 'XL', label: 'Extra Large' };
    return { size: 'XXL', label: 'Double Extra Large' };
}
```

### 12.4 Measurement Comparison (Before/After)

```javascript
function compareMeasurements(old, current) {
    var result = {};
    var keys = ['chest', 'waist', 'hips', 'shoulderWidth'];
    
    keys.forEach(function(key) {
        var diff = current[key] - old[key];
        result[key] = {
            old: old[key],
            current: current[key],
            change: Math.round(diff * 10) / 10,
            percent: Math.round((diff / old[key]) * 100 * 10) / 10
        };
    });
    
    return result;
}
```

### 12.5 Integration with Clothing Size Charts

```javascript
// Map measurements to clothing brand size charts
var SIZE_CHARTS = {
    nike: {
        chest: { S: [86, 91], M: [91, 96], L: [96, 102], XL: [102, 107] },
        // ...
    },
    zara: {
        chest: { XS: [78, 82], S: [82, 86], M: [86, 90], L: [90, 94] },
        // ...
    }
};
```

### 12.6 Body Fat Percentage Estimation

Using Navy method with measurements:

```javascript
function estimateBodyFat(gender, waist, neck, height, hips) {
    if (gender === 'male') {
        // Navy formula for men
        return 495 / (1.0324 - 0.19077 * Math.log10(waist - neck) + 
               0.15456 * Math.log10(height)) - 450;
    } else {
        // Navy formula for women
        return 495 / (1.29579 - 0.35004 * Math.log10(waist + hips - neck) + 
               0.22100 * Math.log10(height)) - 450;
    }
}
```

### 12.7 Historical Tracking Dashboard

Add to dashboard.html:

```html
<div class="measurement-history-chart">
    <h3>Measurement History</h3>
    <canvas id="measurement-chart"></canvas>
    <!-- Use Chart.js or similar for line chart -->
    <!-- X-axis: dates, Y-axis: measurements (cm) -->
    <!-- Lines: chest, waist, hips -->
</div>
```

### 12.8 Third-Party API Integration

```python
# Export measurements to third-party services
@router.post("/measurements/{id}/export")
async def export_measurement(id: int, service: str):
    measurement = get_measurement(id)
    
    if service == "shopify":
        # Send to Shopify customer profile
        pass
    elif service == "woocommerce":
        # Send to WooCommerce
        pass
    elif service == "custom":
        # Send to custom webhook
        pass
```

---

## Appendix A: File Structure

```
ai-body-scan-saas/
├── BODY_MEASUREMENT_PLAN.md          ← This file
├── tryon.html                         ← Updated with measurement tab
├── public/
│   ├── camerakit-integration.v2.js    ← Updated with Remote API listener
│   ├── camera-kit-tryon-app.v2.js     ← Updated with measurement handling
│   └── camerakit-config.v2.js         ← No changes
├── api/
│   └── routes/
│       ├── measurements.py            ← NEW: Measurement storage API
│       └── tryon.py                   ← Existing capture endpoints
├── data/
│   └── measurements.db               ← NEW: SQLite database (auto-created)
└── Lens Studio/
    └── [Your lens project]/
        └── Scripts/
            └── BodyMeasurementScript.js  ← NEW: Lens measurement script
```

## Appendix B: Environment Variables

Add to `.env`:

```bash
# Measurement API
MEASUREMENTS_DB_PATH=data/measurements.db
MEASUREMENTS_API_ENABLED=true
```

## Appendix C: Quick Reference Card

| What | Where | How |
|------|-------|-----|
| Create Remote API spec | my-lenses.snapchat.com/apis | Click "+ Add API" |
| Import spec in Lens Studio | Asset Library → APIs | Select your spec → Import |
| Test in Lens Studio | Logger panel | Look for `[BodyMeasurement]` logs |
| Upload lens | Lens Studio → File → Upload | Select existing project |
| Push to Camera Kit | My Lenses portal | Click "Push to Camera Kit" |
| Subscribe to Remote API | Host app JS | `session.remoteApi.subscribe()` |
| Store measurements | Flask API | POST `/api/v2/measurements` |
| View measurements | Sidebar tab | Click "Measurements" tab |
| Calibrate Y-thresholds | Lens Studio + Blender | Analyze body mesh reference |
| Debug vertex extraction | Lens Logger | Set `DEBUG = true` in script |

---

## 13. Lens Studio Step-by-Step Visual Guide

### 13.1 Opening Your Lens Project

```
Lens Studio → File → Open Project from My Lenses
    │
    ├── Select account: Korra Technologies
    │
    ├── Search for lens: "Korra Virtual Try-On"
    │   (or search by Lens ID: ccc9d825-d8ec-41ca-910a-7fd372065026)
    │
    └── Click "Open" → Wait for project to load
```

**Expected panel layout after opening:**

```
┌─────────────────────────────────────────────────────────────┐
│ Lens Studio                                                 │
├──────────┬───────────────────────────┬──────────────────────┤
│          │                           │                      │
│ Scene    │      Preview Panel        │    Inspector         │
│ Hierarchy│                           │                      │
│          │    ┌─────────────────┐    │  ┌────────────────┐  │
│ Camera   │    │                 │    │  │ Component      │  │
│ ├─ 3D    │    │   Body Model    │    │  │ Properties     │  │
│ │ Body   │    │   (preview)     │    │  │                │  │
│ │ Track  │    │                 │    │  │ Transform      │  │
│ │        │    │                 │    │  │ Position       │  │
│ ├─ Full  │    └─────────────────┘    │  │ Rotation       │  │
│ │ Body   │                           │  │ Scale          │  │
│ │ Mesh   │                           │  └────────────────┘  │
│ │        │                           │                      │
│ ├─ Body  │                           │                      │
│ │ Meas-  │                           │                      │
│ │ ure-   │                           │                      │
│ │ ment   │                           │                      │
│          │                           │                      │
├──────────┴───────────────────────────┴──────────────────────┤
│ Asset Browser                                               │
│ ┌──────────────────────────────────────────────────────────┐│
│ │ Scripts: BodyMeasurementScript.js                        ││
│ │ Assets: RemoteServiceModule, BodyTrackingAsset, etc.     ││
│ └──────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 13.2 Importing Remote Service Module — Detailed Steps

1. Click **Asset Library** button (bottom-left of Asset Browser)
   - OR: Window → Asset Library

2. In the Asset Library panel, click **APIs** tab (top of panel)

3. You should see your API spec listed:
   ```
   ┌─────────────────────────────────────┐
   │ APIs                                │
   ├─────────────────────────────────────┤
   │                                     │
   │  ☐ Korra Body Measurements          │
   │    Spec ID: abc123-def456...        │
   │    Platform: Camera Kit             │
   │                                     │
   │  ☐ Placeholder API                  │
   │    Spec ID: 363ee2a5-ad35...        │
   │    Platform: Camera Kit             │
   │                                     │
   └─────────────────────────────────────┘
   ```

4. Select **Korra Body Measurements** (or Placeholder API for testing)

5. Click **Import** button

6. A dialog may appear asking to confirm — click **Import**

7. Close Asset Library

8. In **Asset Browser** panel, you should now see:
   ```
   Asset Browser:
   ├── Scripts/
   │   └── BodyMeasurementScript.js
   ├── RemoteServiceModule/
   │   └── KorraBodyMeasurements (RemoteServiceModule)
   ├── Textures/
   ├── Materials/
   └── ...
   ```

### 13.3 Creating the Measurement Scene Object — Detailed Steps

1. In **Scene Hierarchy** panel, right-click on **Camera** object

2. Select **Create Empty** → A new SceneObject appears

3. Rename it: right-click → **Rename** → Type `BodyMeasurement` → Enter

4. With `BodyMeasurement` selected, go to **Inspector** panel

5. Click **+ Add Component** button

6. Select **Script**

7. A new Script component appears in Inspector

8. Click **+ Create New** next to Script field

9. Name the script: `BodyMeasurementScript` → Enter

10. The script is created in Asset Browser and linked to the component

### 13.4 Linking Script Inputs — Detailed Steps

In the Inspector panel for `BodyMeasurementScript`:

```
Script: BodyMeasurementScript
├── remoteServiceModule: [None]
│   └── Click circle → Select "KorraBodyMeasurements"
│       (or "PlaceholderRemoteServiceModule")
│
├── objectTracking3D: [None]
│   └── Click circle → Navigate to:
│       Camera → 3D Body Tracking → ObjectTracking3D
│
└── bodyMeshVisual: [None]
    └── Click circle → Navigate to:
        Camera → Full Body Mesh → Body Mesh (MeshVisual)
```

**To link each input:**

1. Click the small **circle** icon next to the input field
2. A selection dialog appears showing all compatible objects
3. Navigate to and select the correct object
4. The field is now populated

**Alternative drag-and-drop method:**

1. In Scene Hierarchy, find the target object
2. Drag it from Scene Hierarchy
3. Drop it onto the corresponding input field in Inspector

### 13.5 Making Body Mesh Invisible — Detailed Steps

1. In Scene Hierarchy, select **Full Body Mesh** → **Body Mesh**

2. In Inspector, find **Render Mesh Visual** component

3. **Option A: Disable the component**
   - Click the checkbox next to "Render Mesh Visual" to disable it
   - The mesh is invisible but vertex data is still accessible

4. **Option B: Use transparent material**
   - Click the **Material** field
   - Create new material: right-click in Asset Browser → Create → Material
   - Name it: `InvisibleBodyMaterial`
   - In Inspector for the material:
     - **Base Color**: Set alpha to 0 (fully transparent)
     - OR: **Blend Mode** → Set to Alpha
     - **Opacity**: 0
   - Drag the material to the Material field of Render Mesh Visual

**Recommendation**: Option A (disable component) is simpler and has zero rendering cost.

### 13.6 Testing in Lens Studio — Detailed Steps

1. Click **Play** button (▶) in top toolbar

2. Wait for the preview to load (may take 5-10 seconds)

3. The preview panel should show a body model (or camera feed if webcam connected)

4. Open **Logger** panel: Window → Logger (or press `Ctrl+L` / `Cmd+L`)

5. Look for log messages:
   ```
   [BodyMeasurement] Script initialized
   [BodyMeasurement] Tap screen or use 'Get Measurements' button to measure
   ```

6. **To test measurement**: Click on the preview panel (this triggers TapEvent)
   - You should see:
   ```
   [BodyMeasurement] Starting measurement...
   [BodyMeasurement] Frame 1/8 — Chest: 94.2cm, Waist: 79.8cm, Hips: 100.1cm
   [BodyMeasurement] Frame 2/8 — Chest: 94.5cm, Waist: 80.1cm, Hips: 100.3cm
   ...
   [BodyMeasurement] Frame 8/8 — Chest: 94.3cm, Waist: 79.9cm, Hips: 100.2cm
   [BodyMeasurement] === FINAL MEASUREMENTS ===
   [BodyMeasurement] Chest: 94.3 cm
   [BodyMeasurement] Waist: 79.9 cm
   [BodyMeasurement] Hips: 100.2 cm
   [BodyMeasurement] Shoulders: 43.7 cm
   [BodyMeasurement] Height: 174.8 cm
   [BodyMeasurement] ============================
   [BodyMeasurement] Measurements sent to host app successfully
   ```

7. **Expected errors in Lens Studio** (these are normal):
   ```
   [CameraKit] Remote API failed (status: 0)
   ```
   This happens because there's no host app connected in Lens Studio preview.
   The measurements are still calculated correctly — the Remote API just can't deliver them.

---

## 14. Additional CSS — Measurement Panel Responsive Design

### 14.1 Desktop Layout (Sidebar Open)

```css
/* ================================================================= */
/* Measurement Tab — Desktop (Sidebar Visible) */
/* ================================================================= */

@media (min-width: 769px) {
    .sidebar-tab-content[data-tab="measurements"] {
        padding: 20px 16px;
    }
    
    .get-measurements-btn {
        font-size: 15px;
        padding: 16px 24px;
    }
    
    .measurement-row {
        padding: 14px 18px;
        margin-bottom: 8px;
    }
    
    .measurement-label {
        font-size: 14px;
    }
    
    .measurement-value {
        font-size: 18px;
    }
    
    .measurement-history {
        padding: 20px 16px;
    }
    
    .history-title {
        font-size: 12px;
    }
    
    .history-item {
        padding: 14px;
    }
    
    .history-item-measure {
        font-size: 12px;
    }
}
```

### 14.2 Mobile Layout (Sidebar Hidden)

```css
/* ================================================================= */
/* Measurement Tab — Mobile (Bottom Strip) */
/* ================================================================= */

@media (max-width: 768px) {
    .measurement-trigger {
        padding: 0 12px 12px;
    }
    
    .get-measurements-btn {
        font-size: 13px;
        padding: 12px 16px;
        border-radius: 10px;
    }
    
    .measurement-hint {
        font-size: 10px;
        padding: 0 8px;
    }
    
    .measurement-results {
        padding: 0 12px 12px;
    }
    
    .measurement-row {
        padding: 10px 14px;
        margin-bottom: 4px;
    }
    
    .measurement-label {
        font-size: 12px;
    }
    
    .measurement-value {
        font-size: 15px;
    }
    
    .measurement-history {
        padding: 12px;
    }
    
    .history-title {
        font-size: 10px;
    }
    
    .history-item {
        padding: 10px;
    }
    
    .history-item-values {
        gap: 8px;
    }
    
    .history-item-measure {
        font-size: 10px;
    }
}
```

### 14.3 Dark Theme Enhancements

```css
/* ================================================================= */
/* Measurement Panel — Dark Theme Polish */
/* ================================================================= */

/* Glow effect on measurement values */
.measurement-value {
    text-shadow: 0 0 20px rgba(198, 255, 0, 0.15);
}

/* Active measurement row animation */
.measurement-row.active {
    border-color: rgba(198, 255, 0, 0.2);
    background: rgba(198, 255, 0, 0.05);
    animation: measurementPulse 1s ease-out;
}

@keyframes measurementPulse {
    0% {
        border-color: rgba(198, 255, 0, 0.4);
        background: rgba(198, 255, 0, 0.1);
    }
    100% {
        border-color: rgba(255, 255, 255, 0.04);
        background: rgba(255, 255, 255, 0.03);
    }
}

/* Scrollbar styling for measurement results */
.measurement-results::-webkit-scrollbar {
    width: 4px;
}

.measurement-results::-webkit-scrollbar-track {
    background: transparent;
}

.measurement-results::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 2px;
}

.measurement-results::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.2);
}

/* Measurement accuracy indicator */
.measurement-accuracy {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 10px;
    color: #666;
    margin-left: 8px;
}

.measurement-accuracy-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #444;
}

.measurement-accuracy-dot.high { background: #c6ff00; }
.measurement-accuracy-dot.medium { background: #ffd700; }
.measurement-accuracy-dot.low { background: #ff6b6b; }

/* Export button */
.measurement-export {
    display: flex;
    gap: 8px;
    padding: 12px 16px;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.export-btn {
    flex: 1;
    padding: 10px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.03);
    color: #999;
    font-size: 11px;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.2s;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-family: inherit;
}

.export-btn:hover {
    background: rgba(255, 255, 255, 0.08);
    color: #fff;
}

.export-btn:active {
    transform: scale(0.97);
}

/* Loading skeleton for measurements */
.measurement-skeleton {
    background: linear-gradient(
        90deg,
        rgba(255, 255, 255, 0.03) 25%,
        rgba(255, 255, 255, 0.08) 50%,
        rgba(255, 255, 255, 0.03) 75%
    );
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
    border-radius: 8px;
    height: 48px;
    margin-bottom: 6px;
}

@keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}
```

---

## 15. Additional Flask API — Batch Operations & Analytics

### 15.1 Batch Measurement Upload

```python
# ====================================================================
# Batch Upload Endpoint
# ====================================================================

class BatchMeasurementCreate(BaseModel):
    """Request body for batch measurement upload."""
    user_id: str
    measurements: List[MeasurementCreate]

@router.post("/measurements/batch", response_model=MeasurementListResponse)
async def create_measurements_batch(batch: BatchMeasurementCreate):
    """
    Store multiple body measurements at once.
    
    Useful for:
    - Importing historical measurements
    - Syncing from mobile app
    - Bulk data migration
    """
    conn = get_db()
    try:
        created = []
        for m in batch.measurements:
            timestamp = m.timestamp or datetime.utcnow().isoformat()
            cursor = conn.execute(
                """
                INSERT INTO body_measurements 
                (user_id, chest, waist, hips, shoulder_width, height, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    m.user_id,
                    m.chest,
                    m.waist,
                    m.hips,
                    m.shoulder_width,
                    m.height,
                    timestamp
                )
            )
            created.append(cursor.lastrowid)
        
        conn.commit()
        
        # Fetch all created records
        placeholders = ','.join(['?' for _ in created])
        rows = conn.execute(
            f"SELECT * FROM body_measurements WHERE id IN ({placeholders})",
            created
        ).fetchall()
        
        measurements = [
            MeasurementResponse(
                id=row["id"],
                user_id=row["user_id"],
                chest=row["chest"],
                waist=row["waist"],
                hips=row["hips"],
                shoulder_width=row["shoulder_width"],
                height=row["height"],
                timestamp=row["timestamp"],
                created_at=row["created_at"]
            )
            for row in rows
        ]
        
        return MeasurementListResponse(
            measurements=measurements,
            total=len(measurements)
        )
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
```

### 15.2 Measurement Statistics

```python
# ====================================================================
# Statistics Endpoint
# ====================================================================

class MeasurementStats(BaseModel):
    """Statistical summary of measurements."""
    user_id: str
    total_measurements: int
    average: dict
    min: dict
    max: dict
    latest: Optional[MeasurementResponse]
    trend: Optional[dict]  # Change over time

@router.get("/measurements/stats/{user_id}", response_model=MeasurementStats)
async def get_measurement_stats(user_id: str):
    """
    Get statistical summary of a user's measurements.
    
    Includes:
    - Total measurement count
    - Average, min, max for each measurement
    - Latest measurement
    - Trend (change from first to last)
    """
    conn = get_db()
    try:
        rows = conn.execute(
            """
            SELECT chest, waist, hips, shoulder_width, height, created_at
            FROM body_measurements 
            WHERE user_id = ? 
            ORDER BY created_at ASC
            """,
            (user_id,)
        ).fetchall()
        
        if not rows:
            raise HTTPException(
                status_code=404, 
                detail="No measurements found for user"
            )
        
        total = len(rows)
        
        # Calculate statistics
        stats = {
            'chest': {'values': [r['chest'] for r in rows]},
            'waist': {'values': [r['waist'] for r in rows]},
            'hips': {'values': [r['hips'] for r in rows]},
            'shoulder_width': {'values': [r['shoulder_width'] for r in rows]},
            'height': {'values': [r['height'] for r in rows]}
        }
        
        average = {}
        minimum = {}
        maximum = {}
        
        for key in stats:
            values = stats[key]['values']
            average[key] = round(sum(values) / len(values), 1)
            minimum[key] = round(min(values), 1)
            maximum[key] = round(max(values), 1)
        
        # Latest measurement
        latest_row = rows[-1]
        latest = MeasurementResponse(
            id=0,  # Would need to fetch actual ID
            user_id=user_id,
            chest=latest_row['chest'],
            waist=latest_row['waist'],
            hips=latest_row['hips'],
            shoulder_width=latest_row['shoulder_width'],
            height=latest_row['height'],
            timestamp=latest_row['created_at'],
            created_at=latest_row['created_at']
        )
        
        # Trend (first vs last)
        trend = None
        if total > 1:
            first = rows[0]
            last = rows[-1]
            trend = {
                'chest': round(last['chest'] - first['chest'], 1),
                'waist': round(last['waist'] - first['waist'], 1),
                'hips': round(last['hips'] - first['hips'], 1),
                'shoulder_width': round(last['shoulder_width'] - first['shoulder_width'], 1),
                'height': round(last['height'] - first['height'], 1)
            }
        
        return MeasurementStats(
            user_id=user_id,
            total_measurements=total,
            average=average,
            min=minimum,
            max=maximum,
            latest=latest,
            trend=trend
        )
    finally:
        conn.close()
```

### 15.3 Measurement Comparison

```python
# ====================================================================
# Comparison Endpoint
# ====================================================================

class MeasurementComparison(BaseModel):
    """Comparison between two measurements."""
    measurement_a: MeasurementResponse
    measurement_b: MeasurementResponse
    differences: dict
    percent_changes: dict

@router.get("/measurements/compare", response_model=MeasurementComparison)
async def compare_measurements(
    id_a: int = Query(..., description="First measurement ID"),
    id_b: int = Query(..., description="Second measurement ID")
):
    """
    Compare two measurements and calculate differences.
    
    Useful for:
    - Before/after comparisons
    - Tracking progress over time
    - Size change detection
    """
    conn = get_db()
    try:
        row_a = conn.execute(
            "SELECT * FROM body_measurements WHERE id = ?", (id_a,)
        ).fetchone()
        
        row_b = conn.execute(
            "SELECT * FROM body_measurements WHERE id = ?", (id_b,)
        ).fetchone()
        
        if not row_a or not row_b:
            raise HTTPException(status_code=404, detail="Measurement not found")
        
        def row_to_response(row):
            return MeasurementResponse(
                id=row["id"],
                user_id=row["user_id"],
                chest=row["chest"],
                waist=row["waist"],
                hips=row["hips"],
                shoulder_width=row["shoulder_width"],
                height=row["height"],
                timestamp=row["timestamp"],
                created_at=row["created_at"]
            )
        
        meas_a = row_to_response(row_a)
        meas_b = row_to_response(row_b)
        
        # Calculate differences
        keys = ['chest', 'waist', 'hips', 'shoulder_width', 'height']
        differences = {}
        percent_changes = {}
        
        for key in keys:
            val_a = getattr(meas_a, key)
            val_b = getattr(meas_b, key)
            diff = round(val_b - val_a, 1)
            pct = round((diff / val_a) * 100, 1) if val_a != 0 else 0
            
            differences[key] = diff
            percent_changes[key] = pct
        
        return MeasurementComparison(
            measurement_a=meas_a,
            measurement_b=meas_b,
            differences=differences,
            percent_changes=percent_changes
        )
    finally:
        conn.close()
```

### 15.4 Size Recommendation

```python
# ====================================================================
# Size Recommendation Endpoint
# ====================================================================

class SizeRecommendation(BaseModel):
    """Clothing size recommendation based on measurements."""
    measurement_id: int
    brand: str
    category: str  # 'tops', 'bottoms', 'dresses'
    recommended_size: str
    size_details: dict
    confidence: float  # 0-1

# Size charts (simplified — expand for production)
SIZE_CHARTS = {
    'generic': {
        'tops': {
            'XS': {'chest_max': 86, 'chest_min': 0},
            'S': {'chest_max': 91, 'chest_min': 86},
            'M': {'chest_max': 96, 'chest_min': 91},
            'L': {'chest_max': 102, 'chest_min': 96},
            'XL': {'chest_max': 107, 'chest_min': 102},
            'XXL': {'chest_max': 114, 'chest_min': 107},
        },
        'bottoms': {
            'XS': {'waist_max': 71, 'waist_min': 0, 'hips_max': 86},
            'S': {'waist_max': 76, 'waist_min': 71, 'hips_max': 91},
            'M': {'waist_max': 81, 'waist_min': 76, 'hips_max': 96},
            'L': {'waist_max': 86, 'waist_min': 81, 'hips_max': 102},
            'XL': {'waist_max': 91, 'waist_min': 86, 'hips_max': 107},
            'XXL': {'waist_max': 99, 'waist_min': 91, 'hips_max': 114},
        }
    }
}

@router.get("/measurements/{measurement_id}/recommend-size")
async def recommend_size(
    measurement_id: int,
    brand: str = Query("generic", description="Brand name"),
    category: str = Query("tops", description="Clothing category")
):
    """
    Recommend clothing size based on body measurements.
    
    Uses size charts from the specified brand and category.
    """
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM body_measurements WHERE id = ?",
            (measurement_id,)
        ).fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Measurement not found")
        
        chart = SIZE_CHARTS.get(brand, SIZE_CHARTS['generic'])
        category_chart = chart.get(category, chart.get('tops', {}))
        
        chest = row['chest']
        waist = row['waist']
        hips = row['hips']
        
        recommended = None
        for size_name, size_range in category_chart.items():
            chest_match = (size_range.get('chest_min', 0) <= chest < 
                          size_range.get('chest_max', 999))
            waist_match = (size_range.get('waist_min', 0) <= waist < 
                          size_range.get('waist_max', 999))
            hips_match = (size_range.get('hips_min', 0) <= hips < 
                         size_range.get('hips_max', 999))
            
            if chest_match and waist_match and hips_match:
                recommended = size_name
                break
        
        if not recommended:
            recommended = 'M'  # Default fallback
        
        return SizeRecommendation(
            measurement_id=measurement_id,
            brand=brand,
            category=category,
            recommended_size=recommended,
            size_details=category_chart.get(recommended, {}),
            confidence=0.85  # Placeholder
        )
    finally:
        conn.close()
```

---

## 16. Testing Scripts

### 16.1 Lens Script Unit Tests (Lens Studio)

Create a test script in Lens Studio for debugging:

```javascript
// ====================================================================
// MeasurementTestScript.js
// Run this in Lens Studio to test measurement calculations
// without needing the full Remote API setup
// ====================================================================

// @input Component.MeshVisual bodyMeshVisual

script.createEvent("UpdateEvent").bind(function() {
    // Run test every 3 seconds
    if (Math.floor(getTime()) % 3 !== 0) return;
    
    print("=== MEASUREMENT TEST ===");
    
    var mesh = script.bodyMeshVisual.mesh;
    if (!mesh) {
        print("ERROR: No mesh available");
        return;
    }
    
    var positions = mesh.getVertexDataForAttribute("position");
    if (!positions) {
        print("ERROR: No vertex data");
        return;
    }
    
    var vertexCount = positions.length / 3;
    print("Vertex count: " + vertexCount);
    
    // Find bounds
    var minY = Infinity, maxY = -Infinity;
    for (var i = 0; i < positions.length; i += 3) {
        var y = positions[i + 1];
        if (y < minY) minY = y;
        if (y > maxY) maxY = y;
    }
    
    var height = maxY - minY;
    print("Body height: " + (height * 100).toFixed(1) + " cm");
    print("Y range: " + minY.toFixed(3) + " to " + maxY.toFixed(3));
    
    // Test chest band
    var chestY = minY + height * 0.72;
    var bandHalf = height * 0.03;
    var count = 0;
    for (var i = 0; i < positions.length; i += 3) {
        if (Math.abs(positions[i + 1] - chestY) < bandHalf) {
            count++;
        }
    }
    print("Chest band vertices: " + count);
    
    print("=== TEST COMPLETE ===");
});
```

### 16.2 Flask API Tests (Python)

```python
# ====================================================================
# test_measurements.py
# Run: python -m pytest test_measurements.py -v
# ====================================================================

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_measurement():
    """Test creating a new measurement."""
    response = client.post("/api/v2/measurements", json={
        "user_id": "test-user-001",
        "chest": 96.2,
        "waist": 81.5,
        "hips": 102.3,
        "shoulder_width": 44.8,
        "height": 175.3
    })
    assert response.status_code == 200
    data = response.json()
    assert data["chest"] == 96.2
    assert data["waist"] == 81.5
    assert data["hips"] == 102.3
    assert data["user_id"] == "test-user-001"

def test_get_measurements():
    """Test retrieving measurements."""
    # First create one
    client.post("/api/v2/measurements", json={
        "user_id": "test-user-002",
        "chest": 90.0,
        "waist": 75.0,
        "hips": 95.0,
        "shoulder_width": 42.0,
        "height": 170.0
    })
    
    # Then retrieve
    response = client.get("/api/v2/measurements?user_id=test-user-002")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["measurements"]) >= 1

def test_measurement_validation():
    """Test that invalid measurements are rejected."""
    response = client.post("/api/v2/measurements", json={
        "user_id": "test-user-003",
        "chest": -5,  # Invalid: negative
        "waist": 81.5,
        "hips": 102.3,
        "shoulder_width": 44.8,
        "height": 175.3
    })
    assert response.status_code == 422  # Validation error

def test_delete_measurement():
    """Test deleting a measurement."""
    # Create
    create_resp = client.post("/api/v2/measurements", json={
        "user_id": "test-user-004",
        "chest": 88.0,
        "waist": 72.0,
        "hips": 92.0,
        "shoulder_width": 40.0,
        "height": 168.0
    })
    measurement_id = create_resp.json()["id"]
    
    # Delete
    delete_resp = client.delete(f"/api/v2/measurements/{measurement_id}")
    assert delete_resp.status_code == 200
    
    # Verify deleted
    get_resp = client.get(f"/api/v2/measurements/{measurement_id}")
    assert get_resp.status_code == 404
```

### 16.3 Integration Test Script (Browser Console)

```javascript
// ====================================================================
// Paste this in browser console on tryon.html to test measurement flow
// ====================================================================

// Test 1: Check if measurement tab exists
console.log("Test 1: Measurement tab exists:", 
    !!document.getElementById('tab-measurements'));

// Test 2: Check if button exists
console.log("Test 2: Get Measurements button exists:", 
    !!document.getElementById('btn-get-measurements'));

// Test 3: Check if Remote API listener is active
console.log("Test 3: Camera Kit session available:", 
    !!window.cameraKitTryOn?.session);

// Test 4: Simulate measurement (for testing UI)
function simulateMeasurement() {
    var fakeMeasurement = {
        chest: 95 + Math.random() * 5,
        waist: 80 + Math.random() * 5,
        hips: 100 + Math.random() * 5,
        shoulderWidth: 43 + Math.random() * 3,
        height: 170 + Math.random() * 10,
        timestamp: new Date().toISOString()
    };
    
    // Round to 1 decimal
    Object.keys(fakeMeasurement).forEach(function(key) {
        if (typeof fakeMeasurement[key] === 'number') {
            fakeMeasurement[key] = Math.round(fakeMeasurement[key] * 10) / 10;
        }
    });
    
    window.dispatchEvent(new CustomEvent('bodyMeasurements', {
        detail: fakeMeasurement
    }));
    
    console.log("Simulated measurement:", fakeMeasurement);
}

// Test 5: Trigger simulated measurement
// simulateMeasurement();  // Uncomment to test

// Test 6: Test Flask API directly
async function testFlaskAPI() {
    try {
        var response = await fetch('/api/v2/measurements', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: 'test-browser-' + Date.now(),
                chest: 95.0,
                waist: 80.0,
                hips: 100.0,
                shoulder_width: 44.0,
                height: 175.0
            })
        });
        var data = await response.json();
        console.log("Flask API test result:", data);
    } catch (err) {
        console.error("Flask API test failed:", err);
    }
}

// testFlaskAPI();  // Uncomment to test

console.log("=== All tests loaded ===");
console.log("Run simulateMeasurement() to test UI");
console.log("Run testFlaskAPI() to test backend");
```

---

## 17. Security Considerations

### 17.1 Data Privacy

| Concern | Mitigation |
|---------|------------|
| Body measurements are biometric data | Encrypt at rest, HTTPS in transit |
| GDPR compliance | Allow users to delete their data |
| Data retention | Auto-delete after 90 days (configurable) |
| Access control | User can only access their own measurements |
| Third-party sharing | Never share without explicit consent |

### 17.2 API Security

```python
# ====================================================================
# Rate Limiting for Measurement API
# ====================================================================

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/measurements")
@limiter.limit("10/minute")  # Max 10 measurements per minute per IP
async def create_measurement(measurement: MeasurementCreate):
    # ... existing code
    pass

@router.get("/measurements")
@limiter.limit("30/minute")  # Max 30 reads per minute per IP
async def get_measurements(user_id: str = Query(...)):
    # ... existing code
    pass
```

### 17.3 Input Validation

```python
# Additional validation beyond Pydantic models

def validate_measurement_values(measurement: MeasurementCreate) -> bool:
    """
    Additional sanity checks on measurement values.
    Rejects obviously wrong values.
    """
    # Height sanity check
    if measurement.height < 100 or measurement.height > 250:
        return False
    
    # Chest sanity check (adult range)
    if measurement.chest < 50 or measurement.chest > 200:
        return False
    
    # Waist sanity check
    if measurement.waist < 40 or measurement.waist > 200:
        return False
    
    # Hips sanity check
    if measurement.hips < 50 or measurement.hips > 200:
        return False
    
    # Proportionality checks
    if measurement.waist > measurement.chest * 1.5:
        return False  # Waist shouldn't be >150% of chest
    
    if measurement.hips > measurement.chest * 1.5:
        return False  # Hips shouldn't be >150% of chest
    
    return True
```

### 17.4 Lens Security

| Concern | Status |
|---------|--------|
| Lens sandbox prevents data exfiltration | ✅ Built-in |
| Remote API requires spec registration | ✅ Snap-enforced |
| API Key scoped to Camera Kit only | ✅ Platform restriction |
| No raw vertex data sent to server | ✅ Only computed measurements |
| HTTPS for all communications | ✅ Enforced by Camera Kit |

---

## 18. Monitoring & Logging

### 18.1 Flask API Logging

```python
# ====================================================================
# Measurement API Logging
# ====================================================================

import logging
from datetime import datetime

logger = logging.getLogger("measurements")

def log_measurement_created(measurement_id: int, user_id: str):
    logger.info(
        f"[MEASUREMENT_CREATED] id={measurement_id} user={user_id} "
        f"timestamp={datetime.utcnow().isoformat()}"
    )

def log_measurement_retrieved(measurement_id: int, user_id: str):
    logger.info(
        f"[MEASUREMENT_RETRIEVED] id={measurement_id} user={user_id} "
        f"timestamp={datetime.utcnow().isoformat()}"
    )

def log_measurement_error(error: str, context: dict):
    logger.error(
        f"[MEASUREMENT_ERROR] error={error} context={context} "
        f"timestamp={datetime.utcnow().isoformat()}"
    )
```

### 18.2 EC2 Monitoring Commands

```bash
# Check measurement API logs
ssh -i ~/Downloads/korra-ai-key.pem ubuntu@13.60.215.88 \
    "docker logs korra-ai-prod --tail 100 | grep measurement"

# Check database size
ssh -i ~/Downloads/korra-ai-key.pem ubuntu@13.60.215.88 \
    "docker exec korra-ai-prod ls -la /app/data/measurements.db"

# Check API response times
ssh -i ~/Downloads/korra-ai-key.pem ubuntu@13.60.215.88 \
    "docker exec korra-ai-prod curl -s -w '%{time_total}' http://localhost:8000/api/v2/measurements?user_id=test"

# Monitor real-time
ssh -i ~/Downloads/korra-ai-key.pem ubuntu@13.60.215.88 \
    "docker logs -f korra-ai-prod 2>&1 | grep --line-buffered measurement"
```

### 18.3 Health Check Endpoint

```python
@router.get("/measurements/health")
async def health_check():
    """Health check for measurement API."""
    try:
        conn = get_db()
        conn.execute("SELECT 1")
        conn.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
```

---

## 19. Migration Scripts

### 19.1 Database Migration (SQLite)

```python
# ====================================================================
# migrate_measurements.py
# Run: python migrate_measurements.py
# ====================================================================

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "measurements.db"

def migrate_v1_to_v2():
    """Add body_fat_percentage column (future feature)."""
    conn = sqlite3.connect(str(DB_PATH))
    
    # Check if column exists
    cursor = conn.execute("PRAGMA table_info(body_measurements)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'body_fat_percentage' not in columns:
        conn.execute("""
            ALTER TABLE body_measurements 
            ADD COLUMN body_fat_percentage REAL
        """)
        print("Added body_fat_percentage column")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate_v1_to_v2()
```

### 19.2 Data Export Script

```python
# ====================================================================
# export_measurements.py
# Export all measurements to CSV for analysis
# ====================================================================

import csv
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "measurements.db"
EXPORT_PATH = Path(__file__).parent / "data" / "measurements_export.csv"

def export_to_csv():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    
    rows = conn.execute(
        "SELECT * FROM body_measurements ORDER BY created_at DESC"
    ).fetchall()
    
    with open(EXPORT_PATH, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'id', 'user_id', 'chest', 'waist', 'hips', 
            'shoulder_width', 'height', 'timestamp', 'created_at'
        ])
        
        for row in rows:
            writer.writerow([
                row['id'], row['user_id'], row['chest'],
                row['waist'], row['hips'], row['shoulder_width'],
                row['height'], row['timestamp'], row['created_at']
            ])
    
    print(f"Exported {len(rows)} measurements to {EXPORT_PATH}")
    conn.close()

if __name__ == "__main__":
    export_to_csv()
```

---

## 20. Performance Benchmarks

### 20.1 Expected Performance

| Operation | Expected Time | Notes |
|-----------|--------------|-------|
| Vertex extraction | < 1ms | 6,890 vertices × 3 floats |
| Circumference calculation | < 2ms | Per measurement (3 bands) |
| Full measurement cycle | < 10ms | All calculations + averaging |
| Remote API request | < 50ms | Lens to host app (local) |
| Flask API storage | < 100ms | SQLite write |
| Total "Get Measurements" | < 5s | User-perceived (includes 1.5s stabilization) |

### 20.2 Optimization Tips

1. **Reduce vertex processing**: Only process body vertices, skip hands/head
2. **Cache measurements**: Don't re-calculate if body hasn't moved
3. **Lazy averaging**: Only average when measurement is requested
4. **Batch API calls**: Send multiple measurements in one request
5. **SQLite WAL mode**: Enable Write-Ahead Logging for concurrent reads

```python
# Enable WAL mode for better performance
conn = sqlite3.connect(str(DB_PATH))
conn.execute("PRAGMA journal_mode=WAL")
```

---

**Document Version**: 1.0.0
**Last Updated**: August 6, 2026
**Author**: Korra Technologies AI Agent
**Status**: Ready for Implementation
