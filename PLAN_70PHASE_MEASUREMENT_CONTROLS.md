# 70-Phase Plan: Enable All 34 Measurement Controls (Non-Destructive)

## Principles

1. **Non-destructive**: Every phase creates a backup BEFORE any change. No file is overwritten without a .bak copy.
2. **Atomic**: Each phase is a single, self-contained change (one file, one function, one slider).
3. **Rollbackable**: Every phase has a ROLLBACK command that restores the exact prior state in <60 seconds.
4. **Additive**: New capabilities are ADDED. Old code paths are preserved but may be bypassed.
5. **Verified**: Each phase has a VERIFY step with concrete pass/fail criteria.
6. **Deployable**: Each phase can be deployed to EC2 independently without breaking anything.

## Current State (Baseline)

| Metric | Value |
|--------|-------|
| Total UI sliders | 34 (28 universal + 6 female-only) |
| Active sliders | 13 |
| Disabled (vis-slider-disabled) sliders | 21 |
| Morph targets per gender | 17 |
| Vertex groups | 10 |
| Morph binary size | 2,946,576 bytes |

## Phase Summary

| Block | Phases | Goal | Sliders Unlocked |
|-------|--------|------|------------------|
| Infrastructure | 1-5 | Safety net: backups, validation harness | 0 |
| Unlock Existing | 6-14 | Enable 4 already-wired disabled sliders | 4 |
| Morph Synthesis | 15-32 | Import 3 MakeHuman measurement morphs | 3 |
| Vertex Groups | 33-48 | Add 8 new vertex groups for measurement extraction | 0 |
| Vertex Displacement | 49-66 | Enable 14 remaining sliders via post-morph displacement | 14 |
| Hardening | 67-70 | Final validation, performance, deployment | 0 |

---

## BLOCK 1: INFRASTRUCTURE (Phases 1-5)

### Phase 1: Create Full Backup of All Target Files

**What:** Create timestamped backups of every file that will be touched.
**Files created:** .bak.20260726 copies of all 8 target files.
**VERIFY:** ls shows .bak files for all targets.
**ROLLBACK:** rm -f all .bak files.

### Phase 2: Create Validation Harness Script

**What:** Create scripts/validate_morph_system.js that validates morph integrity after each phase.
Checks: morph_count vs binary size, morph_names length, limits array length, no duplicates, no NaN, sane limits.
**VERIFY:** node scripts/validate_morph_system.js exits 0.
**ROLLBACK:** rm scripts/validate_morph_system.js

### Phase 3: Snapshot Current EC2 State

**What:** Verify current deployed state works before any changes.
**VERIFY:** HTTP 200 from root URL.
**ROLLBACK:** N/A (read-only).

### Phase 4: Create Phase Tracking File

**What:** Create scripts/phase_tracker.json.
**VERIFY:** JSON parses correctly.
**ROLLBACK:** rm scripts/phase_tracker.json

### Phase 5: Create Deployment Staging Directory

**What:** mkdir -p scripts/staging/{male,female,child}
**VERIFY:** Directory exists.
**ROLLBACK:** rm -rf scripts/staging

---

## BLOCK 2: UNLOCK EXISTING MORPHS (Phases 6-14)

### Phase 6: Backup index.html

**Command:** cp index.html index.html.bak.phase6
**ROLLBACK:** cp index.html.bak.phase6 index.html

### Phase 7: Enable Stomach Round Slider

**File:** index.html line 799
**Change:** Remove vis-slider-disabled from stomach slider div.
**VERIFY:** grep returns empty.
**ROLLBACK:** cp index.html.bak.phase6 index.html

### Phase 8: Enable Wrist Round Slider

**File:** index.html line 824
**Change:** Remove vis-slider-disabled from wrist_round slider div.
**VERIFY:** grep returns empty.
**ROLLBACK:** cp index.html.bak.phase6 index.html

### Phase 9: Enable Calf Round Slider

**File:** index.html line 831
**Change:** Remove vis-slider-disabled from calf_round slider div.
**VERIFY:** grep returns empty.
**ROLLBACK:** cp index.html.bak.phase6 index.html

### Phase 10: Enable Bust Round Slider (Female)

**File:** index.html line 839
**Change:** Remove vis-slider-disabled from bust_round slider div.
**VERIFY:** grep returns empty.
**ROLLBACK:** cp index.html.bak.phase6 index.html

### Phase 11: Fix Stomach Form Mapping

**File:** makehuman-body-visualizer.js lines 348-356 (male), 396-403 (female), 440-447 (child)
**Change:** Use stomach slider value directly with clamped ratio instead of raw ratio * 20.
**VERIFY:** Move stomach slider, belly area expands/contracts.
**ROLLBACK:** Restore from .bak.20260726.

### Phase 12: Verify All 4 Unlocked Sliders

**VERIFY:** All 4 sliders respond to input, presets update them, no console warnings.
**ROLLBACK:** cp index.html.bak.phase6 index.html

### Phase 13: Deploy Phase 6-12 to EC2

**Command:** scp index.html + makehuman-body-visualizer.js to EC2.
**VERIFY:** Open korra.work, all 4 sliders active.
**ROLLBACK:** Restore .bak.20260726 on EC2.

### Phase 14: Clean Phase 6-12 Backup

**Command:** rm index.html.bak.phase6

---

## BLOCK 3: MORPH SYNTHESIS (Phases 15-32)

### Phase 15: Download MakeHuman hm08 Base Mesh

**Command:** curl hm08.obj from GitHub.
**VERIFY:** File has ~20,000 lines.
**ROLLBACK:** rm hm08.obj

### Phase 16: Parse hm08.obj to Binary

**File:** scripts/parse_hm08.py (NEW)
**VERIFY:** hm08_vertices.bin exists with correct size.
**ROLLBACK:** rm scripts/parse_hm08.py hm08_vertices.bin

### Phase 17: Download MakeHuman Measurement Targets

**Command:** Download 3 .target files (ankle-circ, frontchest-dist, knee-circ).
**VERIFY:** All 3 files exist with >100 lines.
**ROLLBACK:** rm measure-*.target

### Phase 18: Build Vertex Correspondence Map

**File:** scripts/build_vertex_map.py (NEW)
**Algorithm:** KD-tree nearest-neighbor, Y-band restriction (0.5 dm), coordinate transform (shift +8.17 Y, scale 1.0385).
**Output:** scripts/makehuman_targets/vertex_map.json
**VERIFY:** Map has >3000 valid mappings.
**ROLLBACK:** rm build_vertex_map.py vertex_map.json

### Phase 19: Validate Vertex Map Region Alignment

**File:** scripts/validate_vertex_map.py (NEW)
**Check:** Mapped vertices in ankle region (Y 0.2-0.8), knee region (Y 4.0-5.0), chest region (Y 10.7-14.9).
**VERIFY:** All 3 regions have >50 mapped vertices.
**ROLLBACK:** rm validate_vertex_map.py

### Phase 20: Convert Ankle Target to Dense Morph

**File:** scripts/convert_single_target.py (NEW)
**Input:** measure-ankle-circ.target + vertex_map.json
**Output:** scripts/staging/male/ankle_round_morph.bin (Float32Array(43332))
**VERIFY:** Output file is exactly 173,328 bytes.
**ROLLBACK:** rm ankle_round_morph.bin

### Phase 21: Convert Across-Chest Target to Dense Morph

**Input:** measure-frontchest-dist.target + vertex_map.json
**Output:** scripts/staging/male/across_chest_morph.bin
**VERIFY:** Output file is exactly 173,328 bytes.
**ROLLBACK:** rm across_chest_morph.bin

### Phase 22: Convert Knee Target to Dense Morph

**Input:** measure-knee-circ.target + vertex_map.json
**Output:** scripts/staging/male/knee_round_morph.bin
**VERIFY:** Output file is exactly 173,328 bytes.
**ROLLBACK:** rm knee_round_morph.bin

### Phase 23: Visual Validation of Ankle Morph

**File:** scripts/preview_morph.py (NEW)
**Loads** base vertices + ankle morph, applies morph at influence=1.0, compares Y-range of affected vertices with expected ankle region.
**VERIFY:** Affected vertices are in Y range 0.2-0.8 dm.
**ROLLBACK:** rm preview_morph.py

### Phase 24: Visual Validation of Across-Chest Morph

**CHECK:** Affected vertices are in Y range 10.7-14.9 dm and X range 1.5-4.0 dm.
**VERIFY:** Pass.
**ROLLBACK:** N/A.

### Phase 25: Visual Validation of Knee Morph

**CHECK:** Affected vertices are in Y range 4.0-5.0 dm.
**VERIFY:** Pass.
**ROLLBACK:** N/A.

### Phase 26: Append 3 Morphs to Male Morph Binary

**File:** scripts/append_morphs.py (NEW)
**Read** existing male_morphs.bin, append 3 new morph chunks, write to scripts/staging/male/male_morphs.bin.
**VERIFY:** Output is 20 * 173,328 = 3,466,560 bytes.
**ROLLBACK:** rm staged binary.

### Phase 27: Append 3 Morphs to Female Morph Binary

**Same as Phase 26 for female.**
**VERIFY:** Output is 3,466,560 bytes.
**ROLLBACK:** rm staged binary.

### Phase 28: Append 3 Morphs to Child Morph Binary

**Same as Phase 26 for child.**
**VERIFY:** Output is 3,466,560 bytes.
**ROLLBACK:** rm staged binary.

### Phase 29: Update model_config.json with 3 New Morph Entries

**File:** model_config.json
**Add** ankle_round, across_chest, knee_round to morph_names, display_names, and limits arrays for all 3 genders.
**VERIFY:** morph_count=20, all arrays length 20.
**ROLLBACK:** Restore from .bak.20260726.

### Phase 30: Run Validation Harness After Morph Append

**Command:** node scripts/validate_morph_system.js
**VERIFY:** All checks pass with morph_count=20.

### Phase 31: Deploy Morph Synthesis to EC2

**Command:** scp all 3 morph binaries + model_config.json to EC2.
**VERIFY:** Engine loads 20 morphs, console shows morph names.

### Phase 32: Wire 3 New Morphs in Visualizer Mapping

**File:** makehuman-body-visualizer.js
**Add** entries to _applyMaleMappings, _applyFemaleMappings, _applyChildMappings:
  - ['ankle_round', m.ankle_round || m['Ankle Round'] || 24],
  - ['across_chest', m.across_chest || m['Across Chest'] || 41],
  - ['knee_round', m.knee_round || m['Knee Round'] || 38],
**Remove** vis-slider-disabled from index.html for these 3 sliders (lines 817, 830, 832).
**VERIFY:** All 3 sliders active, mesh deforms in correct regions.

---

## BLOCK 4: VERTEX GROUPS (Phases 33-48)

### Phase 33: Backup makehuman_body_points.js

**Command:** cp makehuman_body_points.js makehuman_body_points.js.bak.phase33
**ROLLBACK:** Restore from backup.

### Phase 34: Analyze Vertex Y-Position Distribution

**File:** scripts/analyze_vertex_positions.py (NEW)
**Output:** Histogram of vertex Y-positions to identify region boundaries.
**VERIFY:** Output shows clear peaks at ankle, knee, waist, chest, shoulder heights.
**ROLLBACK:** rm analyze_vertex_positions.py

### Phase 35: Define Knee Vertex Group

**Method:** Y-band 4.0-5.0 dm, radial >1.2 (legs, not crotch).
**Output:** Vertex list for knee group.
**VERIFY:** 50-200 vertices in range.
**ROLLBACK:** Undo addition to makehuman_body_points.js.

### Phase 36: Define Ankle Vertex Group

**Method:** Y-band 0.2-0.8 dm, radial >1.5.
**VERIFY:** 30-150 vertices.
**ROLLBACK:** Undo.

### Phase 37: Define Elbow Vertex Group

**Method:** Y-band 9.5-11.0 dm, X >4.0 (arms in T-pose).
**VERIFY:** 30-100 vertices.
**ROLLBACK:** Undo.

### Phase 38: Define Upper Hip Vertex Group

**Method:** Y-band 8.8-9.5 dm, radial >1.0.
**VERIFY:** 50-200 vertices.
**ROLLBACK:** Undo.

### Phase 39: Define High Bust Vertex Group

**Method:** Y-band 12.0-12.8 dm, radial >0.5.
**VERIFY:** 50-200 vertices.
**ROLLBACK:** Undo.

### Phase 40: Define Under Bust Vertex Group

**Method:** Y-band 10.8-11.5 dm, radial >0.5.
**VERIFY:** 50-200 vertices.
**ROLLBACK:** Undo.

### Phase 41: Define Bust Point Vertex Group

**Method:** Y-band 11.5-12.5 dm, Z >1.0 (front), X >0.3.
**VERIFY:** 30-100 vertices.
**ROLLBACK:** Undo.

### Phase 42: Define Armhole Vertex Group

**Method:** Y-band 12.5-14.0 dm, X between 2.0-4.0.
**VERIFY:** 30-150 vertices.
**ROLLBACK:** Undo.

### Phase 43: Add All 8 New Groups to makehuman_body_points.js

**File:** makehuman_body_points.js
**Add** _knee, _ankle, _elbow, _upper_hip, _high_bust, _under_bust, _bust_point, _armhole arrays.
**Update** window.MAKEHUMAN_POINTS to include all 18 groups.
**VERIFY:** window.MAKEHUMAN_POINTS has 18 keys.
**ROLLBACK:** Restore from .bak.phase33.

### Phase 44: Validate No Vertex Overlap Between Groups

**File:** scripts/validate_vertex_groups.py (NEW)
**Check:** No vertex index appears in more than 2 groups (allow shoulder+armhole overlap).
**VERIFY:** Pass.
**ROLLBACK:** rm validate_vertex_groups.py.

### Phase 45: Update computeAllMeasurements for New Groups

**File:** makehuman-body-visualizer.js
**Add** lookups for knee, ankle, elbow, upper_hip, high_bust, under_bust, armhole vertex groups.
**Replace** derived estimates with actual limbCirc/circ computations where vertex groups exist.
**VERIFY:** Extracted measurements are within 20% of default slider values.
**ROLLBACK:** Restore from .bak.20260726.

### Phase 46: Deploy Vertex Groups to EC2

**Command:** scp makehuman_body_points.js + makehuman-body-visualizer.js.
**VERIFY:** All 18 vertex groups load, measurement extraction uses new groups.

### Phase 47: Verify Measurement Extraction Roundtrip

**CHECK:** Set ankle slider to 25 -> extract ankle measurement -> should be ~25cm.
**VERIFY:** Within 5cm tolerance for all new groups.
**ROLLBACK:** Restore backups.

### Phase 48: Clean Phase 33 Backup

**Command:** rm makehuman_body_points.js.bak.phase33

---

## BLOCK 5: VERTEX DISPLACEMENT (Phases 49-66)

### Phase 49: Backup Visualizer Before Displacement Work

**Command:** cp makehuman-body-visualizer.js makehuman-body-visualizer.js.bak.phase49
**ROLLBACK:** Restore from backup.

### Phase 50: Implement _computeRingCircumference Helper

**File:** makehuman-body-visualizer.js
**Add** method that computes ConvexHull perimeter of a vertex ring in the XZ plane.
**VERIFY:** Call with chest vertices, returns ~96cm.
**ROLLBACK:** Remove method.

### Phase 51: Implement _radialScale Helper

**File:** makehuman-body-visualizer.js
**Add** method that scales vertex positions radially from ring centroid to achieve target circumference.
**VERIFY:** Call on wrist vertices with target=20cm, wrist thickens.
**ROLLBACK:** Remove method.

### Phase 52: Implement _xScaleRegion Helper

**File:** makehuman-body-visualizer.js
**Add** method that scales vertex positions along X-axis within a region.
**VERIFY:** Call on shoulder vertices, shoulder width changes.
**ROLLBACK:** Remove method.

### Phase 53: Implement _yStretchZone Helper

**File:** makehuman-body-visualizer.js
**Add** method that stretches/compresses Y positions within a Y-band to achieve target distance between landmarks.
**VERIFY:** Call with neck->waist landmarks, torso length changes.
**ROLLBACK:** Remove method.

### Phase 54: Implement _applyVertexDisplacements Skeleton

**File:** makehuman-body-visualizer.js
**Add** empty method that reads measurements and will dispatch to displacement helpers.
**VERIFY:** Method exists, called from updateFromMeasurements.
**ROLLBACK:** Remove method + call.

### Phase 55: Wire Elbow Round Displacement

**In** _applyVertexDisplacements: call _radialScale on elbow vertex group.
**VERIFY:** Move elbow slider, elbow region expands.
**ROLLBACK:** Remove elbow wiring.

### Phase 56: Wire Armhole Round Displacement

**In** _applyVertexDisplacements: call _radialScale on armhole vertex group.
**VERIFY:** Move armhole slider, armhole region expands.
**ROLLBACK:** Remove armhole wiring.

### Phase 57: Wire Upper Hip Displacement

**In** _applyVertexDisplacements: call _radialScale on upper_hip vertex group.
**VERIFY:** Move upper_hip slider, upper hip expands.
**ROLLBACK:** Remove upper_hip wiring.

### Phase 58: Wire High Bust Displacement

**In** _applyVertexDisplacements: call _radialScale on high_bust vertex group.
**VERIFY:** Move high_bust slider, upper chest expands.
**ROLLBACK:** Remove high_bust wiring.

### Phase 59: Wire Under Bust Displacement

**In** _applyVertexDisplacements: call _radialScale on under_bust vertex group.
**VERIFY:** Move under_bust slider, ribcage below bust expands.
**ROLLBACK:** Remove under_bust wiring.

### Phase 60: Wire Trouser Waist Displacement

**In** _applyVertexDisplacements: call _radialScale on waist vertex group (independent of waist morph).
**VERIFY:** Move trouser_waist slider, waist area scales.
**ROLLBACK:** Remove trouser_waist wiring.

### Phase 61: Wire Across Back Displacement

**In** _applyVertexDisplacements: call _xScaleRegion on chest vertices (backOnly=true).
**VERIFY:** Move across_back slider, back widens.
**ROLLBACK:** Remove across_back wiring.

### Phase 62: Wire Across Shoulder Displacement

**In** _applyVertexDisplacements: call _xScaleRegion on shoulder vertices.
**VERIFY:** Move across_shoulder slider, shoulder width changes.
**ROLLBACK:** Remove across_shoulder wiring.

### Phase 63: Wire Length Displacements (Back/Front Waist, Neck-to-Waist, Crotch Depth)

**In** _applyVertexDisplacements: call _yStretchZone for each length measurement.
**VERIFY:** Each length slider changes the corresponding body proportion.
**ROLLBACK:** Remove length wiring.

### Phase 64: Wire Inseam + Shoulder-to-Bust Displacements

**In** _applyVertexDisplacements: call _yStretchZone for inseam and shoulder_to_bust.
**VERIFY:** Lower legs lengthen/shorten, bust position moves.
**ROLLBACK:** Remove wiring.

### Phase 65: Remove vis-slider-disabled from All 14 Remaining Sliders

**File:** index.html
**Remove** vis-slider-disabled from lines 802, 807, 808, 809, 811, 816, 818, 823, 833, 835, 840, 841, 843, 844.
**VERIFY:** grep vis-slider-disabled returns 0 results in body-visualizer section.
**ROLLBACK:** Restore from .bak.phase49.

### Phase 66: Deploy Vertex Displacement to EC2

**Command:** scp all modified files.
**VERIFY:** All 34 sliders active, mesh deforms correctly for each.
**ROLLBACK:** Restore .bak.20260726 files on EC2.

---

## BLOCK 6: HARDENING (Phases 67-70)

### Phase 67: Push All Sliders to Extremes

**CHECK:** Set every slider to min, then max. Mesh should not invert, tear, or produce NaN.
**VERIFY:** No console errors, mesh stays manifold.
**ROLLBACK:** N/A.

### Phase 68: Performance Profiling

**CHECK:** Profile updateFromMeasurements with all 34 sliders active.
**VERIFY:** <10ms per call, no frame drops at 60fps.
**ROLLBACK:** N/A.

### Phase 69: Full Preset Roundtrip

**CHECK:** Click every preset (Slim, Average, Heavy, Athletic, XL, XXL, Female variants, Pregnant).
**VERIFY:** All 34 sliders update, mesh renders correctly for each, no console errors.
**ROLLBACK:** N/A.

### Phase 70: Final Cleanup + Archive

**What:**
1. Run validate_morph_system.js one final time
2. Remove all intermediate scripts (parse_hm08.py, build_vertex_map.py, etc.)
3. Archive .bak.20260726 files to scripts/archive/
4. Update AGENTS.md with new measurement controls status
**VERIFY:** Clean repo, all 34 sliders working in production.
**ROLLBACK:** N/A.

---

## Deployment Gates

Deployment to EC2 should ONLY happen after these gate phases pass:

| Gate | After Phase | Criteria |
|------|-------------|----------|
| Gate 1 | 14 | 4 unlocked sliders work |
| Gate 2 | 32 | 3 new morphs load + work |
| Gate 3 | 48 | Vertex groups correct |
| Gate 4 | 66 | All 34 sliders work |
| Gate 5 | 70 | Hardening complete |

## Total Estimated Effort

| Block | Phases | Estimated Time |
|-------|--------|---------------|
| Infrastructure | 1-5 | 30 minutes |
| Unlock Existing | 6-14 | 1 hour |
| Morph Synthesis | 15-32 | 4-6 hours |
| Vertex Groups | 33-48 | 3-4 hours |
| Vertex Displacement | 49-66 | 6-8 hours |
| Hardening | 67-70 | 2 hours |
| **Total** | **70** | **16-21 hours** |
