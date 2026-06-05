# "Nuclear Reset" Plan: Absolute Web App Recreation

The previous attempts failed because the backend was "eating" the images—serving them as HTML files. This broke the browser's ability to render the site or run the scripts. We will now delete the old logic and recreate the app with a **Zero-Failure Architecture**.

## 1. The "Clean Slate" Architecture
*   **Isolated Assets**: Move all public assets (images, icons) to a dedicated `/public` folder. This stops the backend from getting confused.
*   **Bulletproof Routing**: Strictly separate routes:
    - `/api/*` -> Business Logic
    - `/assets/*` -> Images/CSS
    - `/*` -> The Web App (index.html)
*   **Bulletproof UI**: Re-write the buttons using `.closest('button')` logic, which is the only way to ensure 100% responsiveness on mobile and desktop.

## 2. Implementation Tasks

### Step 1: File System Cleanup
- [ ] Create `/public` directory.
- [ ] Move `homepage_image.png` and `body-capture.png` into `/public`.
- [ ] Delete all `.bak` and legacy `.html` files in the root.

### Step 2: Backend Reconstruction
- [ ] **[main.py](file:///Users/mac/ai-body-scan-saas/api/main.py)**: Implement strict path separation. Use `StaticFiles` ONLY for assets.

### Step 3: Web App Reconstruction
- [ ] **[index.html](file:///Users/mac/ai-body-scan-saas/index.html)**: Clean, high-performance rewrite with fixed button IDs and Supabase v2 logic.

---

## 3. Verification Plan
1. **Direct Path Test**: Confirm `url/assets/homepage_image.png` returns a REAL image.
2. **Button Integrity**: Click every button to verify "PfDebug" logs appear in console.

**Protocol**: Every single file change will be immediately pushed to GitHub.
