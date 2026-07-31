#!/bin/bash
# End-to-end validation script for AR Try-On
# Tests everything that can be verified without a real browser

PASS=0
FAIL=0
WARN=0

pass() { echo "  ✅ $1"; PASS=$((PASS+1)); }
fail() { echo "  ❌ $1"; FAIL=$((FAIL+1)); }
warn() { echo "  ⚠️  $1"; WARN=$((WARN+1)); }
header() { echo -e "\n=== $1 ==="; }

# ============================================================
header "1. JS SYNTAX VALIDATION"
# ============================================================
if node -c /Users/mac/ai-body-scan-saas/public/assets/ar-tryon.js 2>&1; then
  pass "ar-tryon.js syntax valid"
else
  fail "ar-tryon.js has syntax errors"
fi

# ============================================================
header "2. DOM ELEMENTS - JS references vs HTML IDs"
# ============================================================
# Elements referenced in ar-tryon.js
REQUIRED_IDS=(
  arTryOnOverlay arVideo arSkeletonCanvas arThreeCanvas
  arCloseBtn arSwitchBtn arCaptureBtn arGarmentLabel
  arLoading arStatus arErrorMsg arErrorTitle arErrorDesc
)

for id in "${REQUIRED_IDS[@]}"; do
  if grep -q "id=\"$id\"" /Users/mac/ai-body-scan-saas/index.html; then
    pass "Element #$id exists in HTML"
  else
    fail "Element #$id MISSING from HTML"
  fi
done

# ============================================================
header "3. GLB FILE PATHS - data-garb vs EC2 files"
# ============================================================
GLB_PATHS=(
  /assets/beige_business_suit_with_short_skirt.glb
  /assets/floral_dress.glb
  /assets/white_shirt_black_leather_skirt_outfit.glb
  /assets/medieval_cloth_001.glb
  /assets/men_jacket.glb
  /assets/gold_dress.glb
  /assets/man_black_business_suit.glb
  /assets/women_turtleneck.glb
)

# Check HTML has data-garb for each
for glb in "${GLB_PATHS[@]}"; do
  if grep -q "data-garb=\"$glb\"" /Users/mac/ai-body-scan-saas/index.html; then
    pass "data-garb points to $glb"
  else
    fail "data-garb MISSING for $glb"
  fi
done

# Check EC2 has each file
echo -n "  Checking EC2 files..."
for glb in "${GLB_PATHS[@]}"; do
  SIZE=$(ssh -i /Users/mac/Downloads/korra-ai-key.pem ubuntu@13.60.215.88 "docker exec korra-ai-prod stat -c%s /app/public$glb 2>/dev/null" 2>/dev/null)
  if [ -n "$SIZE" ] && [ "$SIZE" -gt 0 ] 2>/dev/null; then
    pass "$glb exists on EC2 ($(($SIZE/1048576))MB)"
  else
    fail "$glb MISSING on EC2"
  fi
done

# ============================================================
header "4. CDN URLS"
# ============================================================
CDN_URLS=(
  "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.18/vision_bundle.mjs"
  "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.18/wasm/vision_wasm_internal.js"
  "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"
  "https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js"
)

for url in "${CDN_URLS[@]}"; do
  CODE=$(curl -sI "$url" -o /dev/null -w "%{http_code}" 2>/dev/null)
  if [ "$CODE" = "200" ]; then
    pass "CDN accessible: $(echo $url | sed 's|.*/||')"
  else
    fail "CDN FAILED ($CODE): $url"
  fi
done

# ============================================================
header "5. HTML STRUCTURE - script tags + overlay placement"
# ============================================================
# Check ar-tryon.js is loaded
if grep -q 'src="/assets/ar-tryon.js"' /Users/mac/ai-body-scan-saas/index.html; then
  pass "ar-tryon.js script tag present"
else
  fail "ar-tryon.js script tag MISSING"
fi

# Check Three.js is loaded
if grep -q 'three.min.js' /Users/mac/ai-body-scan-saas/index.html; then
  pass "three.min.js loaded"
else
  fail "three.min.js NOT loaded"
fi

# Check GLTFLoader is loaded
if grep -q 'GLTFLoader.js' /Users/mac/ai-body-scan-saas/index.html; then
  pass "GLTFLoader.js loaded"
else
  fail "GLTFLoader.js NOT loaded"
fi

# Check DRACOLoader is loaded
if grep -q 'DRACOLoader.js' /Users/mac/ai-body-scan-saas/index.html; then
  pass "DRACOLoader.js loaded"
else
  fail "DRACOLoader.js NOT loaded"
fi

# ============================================================
header "6. OVERLAY CSS - visibility + positioning"
# ============================================================
if grep -q '#arTryOnOverlay' /Users/mac/ai-body-scan-saas/index.html; then
  pass "#arTryOnOverlay CSS exists"
else
  fail "#arTryOnOverlay CSS MISSING"
fi

if grep -q 'position: fixed' /Users/mac/ai-body-scan-saas/index.html && grep -A5 '#arTryOnOverlay' /Users/mac/ai-body-scan-saas/index.html | grep -q 'position: fixed'; then
  pass "Overlay uses position:fixed"
else
  warn "Overlay positioning may be incorrect"
fi

# ============================================================
header "7. JS VARIABLE REFERENCES - check for broken refs"
# ============================================================
# Check that ar-tryon.js references the correct data attribute
if grep -q 'btn.dataset.garb' /Users/mac/ai-body-scan-saas/public/assets/ar-tryon.js; then
  pass "JS reads data-garb (matches HTML)"
else
  fail "JS does NOT read data-garb"
fi

if grep -q 'btn.dataset.glb' /Users/mac/ai-body-scan-saas/public/assets/ar-tryon.js; then
  pass "JS also has fallback to data-glb"
else
  warn "No data-glb fallback (not critical if data-garb is always present)"
fi

# Check that model path in JS matches HTML
if grep -q "@mediapipe/pose@0.5.1675469404" /Users/mac/ai-body-scan-saas/public/assets/ar-tryon.js; then
  pass "Uses legacy @mediapipe/pose@0.5.1675469404 (same as dashboard)"
else
  fail "NOT using dashboard's MediaPipe version"
fi

# Check camera_utils
if grep -q "camera_utils" /Users/mac/ai-body-scan-saas/index.html; then
  pass "camera_utils loaded (same as dashboard)"
else
  fail "camera_utils NOT loaded"
fi

# Check for Vision Tasks (should NOT be present)
if grep -q "PoseLandmarker\|tasks-vision\|detectForVideo" /Users/mac/ai-body-scan-saas/public/assets/ar-tryon.js; then
  fail "Still using Vision Tasks API (should be legacy)"
else
  pass "No Vision Tasks API (correct — using legacy)"
fi

# Check onResults callback pattern
if grep -q "onResults" /Users/mac/ai-body-scan-saas/public/assets/ar-tryon.js; then
  pass "Uses onResults callback (same as dashboard)"
else
  fail "Missing onResults callback"
fi

# Check Camera utility
if grep -q "new Camera" /Users/mac/ai-body-scan-saas/public/assets/ar-tryon.js; then
  pass "Uses Camera utility (same as dashboard)"
else
  fail "Missing Camera utility"
fi

# ============================================================
header "8. POTENTIAL ISSUES"
# ============================================================
# Check for requestAnimationFrame conflicts
GALLERY_LOOPS=$(grep -c 'requestAnimationFrame' /Users/mac/ai-body-scan-saas/index.html)
if [ "$GALLERY_LOOPS" -le 3 ]; then
  pass "Gallery animation loops: $GALLERY_LOOPS (acceptable)"
else
  warn "Gallery has $GALLERY_LOOPS requestAnimationFrame calls (may cause jank)"
fi

# Check body-visualizer has visibility control
if ssh -i /Users/mac/Downloads/korra-ai-key.pem ubuntu@13.60.215.88 "docker exec korra-ai-prod grep -q '_isVisible' /app/public/assets/body-visualizer.js 2>/dev/null"; then
  pass "body-visualizer.js has visibility control"
else
  warn "body-visualizer.js lacks visibility control (may lag on scroll)"
fi

# ============================================================
header "RESULTS"
# ============================================================
TOTAL=$((PASS+FAIL+WARN))
echo -e "  Passed: $PASS / $TOTAL"
echo -e "  Failed: $FAIL"
echo -e "  Warnings: $WARN"
echo ""
if [ $FAIL -eq 0 ]; then
  echo "  🟢 ALL CHECKS PASSED"
else
  echo "  🔴 $FAIL CHECKS FAILED — fix before testing in browser"
fi
