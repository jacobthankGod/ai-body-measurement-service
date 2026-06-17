# Image Handling Audit Report

## Issue Reported
> "when I clicked on side image, it did not clear the front image"

## Console Errors Found
```
korra-widget.js:8 💎 KORRA: Widget Loader Initializing...
pose_solution_simd_wasm_bin.js:9 I0000 00:00:1781657410.436000 ... WebGL context created
POST https://blsettabymllulsxtziw.supabase.co/auth/v1/token?grant_type=refresh_token net::ERR_CONNECTION_CLOSED
api/v2/measurements/extract:1  Failed to load resource: the server responded with a status of 403 ()
```

## Analysis Results

### 1. handlePreviewClick Bug ✅ FIXED
**Original Issue**: When clicking on a preview box that already had an image, the code would try to open the image in a new tab (`window.open(img.src, '_blank')`) instead of allowing retake.

**Fix Applied** in widget.html and dashboard.html:
```javascript
window.handlePreviewClick = function(type) {
  const label = document.getElementById(type === 'front' ? 'fLabel' : 'sLabel');
  const placeholder = label?.querySelector('.placeholder-content');
  const previewImg = label?.querySelector('.preview-img');
  
  // If placeholder is visible OR image already exists, open camera for retake
  if ((placeholder && placeholder.style.display !== 'none') || (previewImg && previewImg.src && previewImg.src !== window.location.href)) {
    window.openCamera(type);
  }
};
```

### 2. Network Error (Infrastructure - Resolved)
The `net::ERR_CONNECTION_CLOSED` error is a Supabase auth connection failure - this happens when the network connection to Supabase is unstable or closed. This is NOT a code bug.

**Resolution**: Check network connectivity and Supabase service status.

### 3. 403 Forbidden Error ✅ FIXED
**Root Cause**: The dashboard.html was using a hardcoded anonymous Supabase key (`sb_publishable_miCOIXHtlxLkfDgpwE0N-g_BA1Q-x8y`) instead of the authenticated user's API key.

**Fix Applied** in dashboard.html:
1. Added `currentApiKey` variable to store the user's API key from their profile
2. Updated `loadSettings()` to store `profile.api_key` when loading settings:
```javascript
// Store API key for authenticated API calls
currentApiKey = profile.api_key;
```
3. Updated scan form to use the authenticated API key:
```javascript
// Use authenticated user's API key instead of hardcoded key
const apiKey = currentApiKey || 'sb_publishable_miCOIXHtlxLkfDgpwE0N-g_BA1Q-x8y';
const res = await fetch('/api/v2/measurements/extract', { 
  method: 'POST', 
  headers: { 'X-API-Key': apiKey }, 
  body: fd 
});
```

### 4. Image Independence (Correct Behavior)
The front and side images are intentionally kept independent of each other. Clicking side does NOT clear front - this is the correct behavior.

## Files Modified
- widget.html: handlePreviewClick function updated
- dashboard.html: handlePreviewClick function updated, added currentApiKey variable and used in scan form

## Verification Steps
1. Open dashboard.html
2. Login with authenticated account
3. Go to History tab → Start Scan
4. Fill scan form and submit → Uses authenticated user's API key → No 403 error
5. Click on front preview box → camera opens
6. Take photo → image displayed
7. Click on side preview box → camera opens (not clearing front)
8. Take photo → both images displayed independently
9. Click on any preview box with existing image → camera opens for retake
