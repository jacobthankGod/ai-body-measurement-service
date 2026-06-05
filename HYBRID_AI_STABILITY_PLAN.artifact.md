# Hybrid AI Strategy: Zero-Crash Vercel Deployment

Vercel Serverless has a **250MB limit** for the entire deployment package (including your code, dependencies like TensorFlow/MediaPipe, and ML models). Your current models alone are ~440MB, which guarantees a crash on Vercel.

## 1. The "Stable SaaS" Architecture
To prevent crashes while maintaining "Ultra-Luxury" accuracy, we will implement a **Hybrid Pipeline**:

### Stage A: Client-Side "Heavy Lifting" (Flutter/Web)
- **Engine**: MediaPipe (JS/Dart).
- **Action**: Detect landmarks (pose points) directly on the user's device.
- **Payload**: Send only the **Landmark JSON** (tiny text data) to the server.
- **Benefit**: Zero server load, instant UI feedback, and no Vercel package size issues.

### Stage B: Server-Side "Intelligence" (Vercel)
- **Engine**: Lightweight Anthropometric Logic (Python).
- **Action**: Convert landmarks + height into ±1cm measurements using your professional ratios.
- **Persistence**: Save results to Supabase.
- **Benefit**: Fast, stable, and fits within the 250MB limit.

---

## 2. Technical Implementation Plan

### [Lighter Backend]
-   **requirements.serverless.txt**: Remove `tensorflow`, `mediapipe`, and `opencv`. Keep `numpy` (minimized) and `supabase`.
-   **Measurement Proxy**: Create a new endpoint `/api/v2/measurements/compute` that accepts MediaPipe Landmark JSON instead of raw image files.

### [Fallback Strategy]
-   **Accuracy Cascade**:
    1.  If Landmarks provided -> Use High-Accuracy Proxy.
    2.  If Images provided -> Attempt lightweight `numpy` processing.
    3.  If Only Height provided -> Use standard Anthropometric Ratios.

---

## 3. Implementation Steps

### Step 1: Update Serverless Config
Update `requirements.serverless.txt` to strictly essential libraries only.

### Step 2: Implement "Landmark-to-Measurement" Logic
Update `api/services/measurement_engine.py` to handle pre-processed landmarks.

### Step 3: Vercel Optimization
Configure `vercel.json` to exclude the `/models` directory from the function bundle while keeping it in the repo (using LFS for your local/dedicated testing).

---
**Status**: Recommendation prepared.
**Action**: Should I begin refactoring the backend to support this Landmark-based hybrid flow?
