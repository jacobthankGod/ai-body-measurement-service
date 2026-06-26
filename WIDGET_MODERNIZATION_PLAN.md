# Widget System & Modern UI Overhaul Plan

## Current State Analysis

### 1. Widget ID System (widget.html)
- Merchant IDs are linked via URL parameter: `?merchant=YOUR_MERCHANT_ID`
- Falls back to `'PUBLIC_WIDGET'` if no merchant specified
- Currently sends `merchant_id` in form data to backend API

### 2. Technical Jargon - COMPLETED FIXES ✅
- **"Digital Twin Handshake"** → Changed to "3D Body Model" ✅
- **"Handshake"** → Changed to "Syncing/Connection" ✅
- **"Super-Workbench"** → Changed to "Admin Panel" ✅

### 3. Admin.html Bug Fixes ✅
- Fixed missing NetworkGuard.update function syntax
- Fixed orphan header HTML elements
- Added missing offlineOverlay div

### 4. Widget Settings Page Gaps (Future)
- No dedicated widget settings page in current implementation
- Widget customization happens ONLY in code (hardcoded colors)
- Missing real-time preview of customizations

### 5. Widget Customization Colors (widget.html CSS)
Only colors defined in CSS :root:
```
--Mint: #C6FF00
--Obsidian: #000000
--Glass: rgba(255, 255, 255, 0.04)
```

Missing user customization options:
- Button border radius
- Button colors
- Accent colors
- Font sizes

## Implementation Plan - COMPLETED

### Phase 1: Fix Technical Jargon ✅ COMPLETE
1. ✅ Replace "Digital Twin Handshake" → "3D Body Model" in widget.html
2. ✅ Replace "Handshake" → "Syncing" or "Connection" in admin.html
3. ✅ Replace "Super-Workbench" → "Admin Panel" in admin.html

### Phase 2: Admin Bug Fixes ✅ COMPLETE
1. ✅ Fixed NetworkGuard.update syntax (missing indent)
2. ✅ Fixed orphan HTML in header section
3. ✅ Added missing offlineOverlay div

### Phase 3: Widget Settings Page (Future)
1. Create widget settings UI in admin.html (new tab)
2. Add color picker for primary accent
3. Add button roundness slider (0-20px)
4. Add real-time preview iframe

### Phase 4: Real-time Customization Preview (Future)
1. Add live preview panel in widget settings
2. Show widget as it would appear with current settings
3. Add "Test Widget" button to simulate customer flow

### Phase 5: Modern Scanning UI (Future)
- Design glowing grid overlay
- Add haptic feedback indicators
- Add countdown animations for auto-capture

## Files Edited
1. **admin.html** - Fixed syntax errors and jargon
2. **widget.html** - No changes needed (already updated)

## User-Friendly Term Mappings
| Technical Jargon | User-Friendly Term |
|-----------------|-------------------|
| Digital Twin | 3D Body Model ✅ |
| Biometrics Vault | Size Passport |
| Handshake | Syncing ✅ |
| Super-Workbench | Admin Panel ✅ |
