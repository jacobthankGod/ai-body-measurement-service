# AUDIT FIX PLAN

## Issue 1: admin.html - Null Reference Error (Line 578)
**Error:** `Cannot read properties of null (reading 'addEventListener')` at line 578

**Root Cause:** JavaScript code references `btnRestoreBrain` element which doesn't exist in the HTML

**Affected Lines:** 578-579 in admin.html

**Fix:** Remove the orphaned btnRestoreBrain code block

---

## Issue 2: extract_measurements.py - _fallback_ratios Incomplete
**Error:** Backend returns only 3 measurements instead of all expected measurements

**Root Cause:** `_fallback_ratios` method only returns 3 hardcoded values instead of using MALE_RATIOS/FEMALE_RATIOS dictionaries

**Affected Function:** `_fallback_ratios` in api/services/extract_measurements.py

**Fix:** Expand to return all measurements using existing MALE_RATIOS and FEMALE_RATIOS dictionaries
