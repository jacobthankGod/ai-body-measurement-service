# Expert UX & Asset Recovery Plan: Zero-Failure Implementation

The previous attempt failed to resolve the broken images and non-responsive buttons on Render. This indicates a **Silent Failure** in either the Render build cache or the JavaScript execution order.

## 1. Root Cause Analysis
*   **Image Pathing**: The Render server serves the `api/main.py` which is one directory level deep. Even though we set `BASE_DIR`, the browser might be resolving paths incorrectly if it's not looking in the exact root.
*   **JS Initialization**: Using `.onclick` on elements before they are fully hydrated or if a script error occurs earlier in the block (e.g., Supabase failing to init) results in completely dead buttons.
*   **Asset Caching**: Render's CDN or the browser might be serving a cached version of `index.html` or the old malformed image name.

## 2. The "Zero-Failure" Strategy

### Step 1: Resilient Pathing (Hard-Coded Root)
We will update `api/main.py` to use an explicit `StaticFiles` mount for the root directory. This forces the server to treat every `.png` file at the root as a public asset.

### Step 2: Resilient JS (Event Delegation)
Instead of assigning `.onclick` to individual buttons, we will use a global **Event Listener** on the `document`. This ensures that even if an element is hidden or swapped, the button click will ALWAYS be caught.

### Step 3: Cache Busting
We will append a version string (`?v=2.0.1`) to all image sources and script links in the `index.html`.

---

## 3. Implementation Tasks

### [Backend]
#### [main.py](file:///Users/mac/ai-body-scan-saas/api/main.py)
- Explicitly mount the root folder as `/assets` to avoid path resolution ambiguity.

### [Frontend]
#### [index.html](file:///Users/mac/ai-body-scan-saas/index.html)
- Wrap all JS in `window.addEventListener('DOMContentLoaded', ...)`
- Use `document.addEventListener('click', ...)` for all buttons.
- Add `PfDebug` console logging to verify every step of the load.

---

## 4. Verification Plan
1. **Console Check**: Verify that "PfDebug: App Initialized" appears in the browser console.
2. **Path Verification**: Hit `https://url/homepage_image.png` directly to confirm public access.

**Protocol**: Push update to github after every edit.
