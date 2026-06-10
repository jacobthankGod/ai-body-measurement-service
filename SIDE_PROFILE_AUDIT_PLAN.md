# Side Profile Accuracy Audit Plan

## Problem Statement
The user reports that the side profile measurements are not accurate. We need to investigate the technical implementation to understand why.

## Current Understanding

### How Measurement Extraction Works (extract_measurements.py):
1. The HMR engine processes ONE image at a time via the `extract()` method
2. Both front and side images are uploaded to the server
3. But the measurement calculation is purely from the 3D mesh vertices extracted from the image
4. There's no evidence of multi-image fusion between front and side inputs

### Technical Questions:
1. Are both images being passed to the HMR engine?
2. Is there any side-specific measurement adjustment?
3. Is the mesh being reconstructed from both images or just one?

## Audit Plan

### Step 1: Trace the Image Processing Pipeline
- Check how 'side' image is handled in the API routes
- Verify if side image is passed to HMR engine

### Step 2: Analyze Measurement Calculation
- Check if measurements are derived purely from mesh vertices
- Investigate if side profile provides different/better measurements

### Step 3: Identify Root Cause
- Determine if the issue is in image processing or measurement calculation

### Step 4: Propose Fixes
- Options:
  a. Implement multi-image fusion (combine data from both images)
  b. Add side-specific measurement adjustments
  c. Improve HMR processing for side profile

## Files to Audit:
- api/routes/measurements.py
- api/services/extract_measurements.py
- api/services/hmr_subprocess.py

## Follow-up:
After the audit, we'll provide findings and recommended fixes.
