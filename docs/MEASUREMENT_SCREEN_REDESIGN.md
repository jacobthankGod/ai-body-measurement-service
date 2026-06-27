# Measurement Screen Redesign — Implementation Plan

**Date:** 2026-06-25
**Status:** Ready for Implementation
**Estimated Effort:** ~1,200 lines across 6 files

---

## 1. Goal

Transform the measurement results from a scrollable card (`#measurementResultsCard`) into a **dedicated, app-like screen** within the existing dashboard tab system. The screen is a new `view-scanresult` tab that takes over the main content area when a scan completes or a historical scan is viewed.

**Design principle:** "Apple Health precision + body intelligence + luxury fitness product + zero learning curve."

**Non-negotiable:** Zero changes to existing sidebar, header, or navigation. This is purely additive.

---

## 2. Architecture

### 2.1 Tab System Integration

The dashboard uses a tab system where each view is a `<div id="view-{name}" class="tab-view">`. Clicking sidebar items calls `switchTab('name')` which shows/hides tabs.

**Existing flow:**
```
switchTab('vault')     → shows #view-vault, hides all others
switchTab('overview')  → shows #view-overview, hides all others
```

**New flow:**
```
switchTab('scanresult')  → shows #view-scanresult, hides all others
                          → measurement screen renders inside #ms-mount
```

**Back navigation:**
```
KORRA_MS.goBack() → switchTab('vault')  → returns to clients list
```

### 2.3 Vault & Ledger Integration

The measurement screen integrates with the vault (clients) tab through 4 entry points:

```
ENTRY POINTS                              EXIT POINT
─────────────────────────────────────     ─────────────────────────────
Vault Ledger "View" button        ──┐
Passport card click               ──┼──→ KORRA_MS.open(data)  ──→  Back button ──→ switchTab('vault')
Passport "View Measurements" btn  ──┤         │
Scan completion (pollTask)        ──┘         └──→ switchTab('scanresult')
```

**Current vault layout:**
- Left column: 3D poster + 3D viewport + measurement card (scrollable, cramped)
- Right column: Ledger with scan list

**After redesign:**
- Left column: 3D poster + 3D viewport only (cleaner)
- Right column: Ledger with scan list (unchanged)
- Measurement screen: Dedicated full-width tab (view-scanresult)

**Key change:** The measurement card is removed from the vault's left column. When a user clicks "View" on a scan, they leave the vault tab entirely and enter the dedicated measurement screen. The back button returns them to the vault.

### 2.2 Data Flow

```
User clicks "View Measurements" on client card
  → window.viewScan(idx) is called
  → data = masterHistory[idx]
  → window.KORRA_MS.open(data) is called
  → switchTab('scanresult')
  → MS renders header, loads 3D mesh, populates tabs

OR

User completes a new scan
  → pollTask() detects status === 'completed'
  → data = response JSON
  → window.KORRA_MS.open(data) is called
  → switchTab('scanresult')
  → MS renders header, loads 3D mesh, populates tabs
```

### 2.3 Scan Data Structure

The data object passed to `KORRA_MS.open()` has this shape (from `api/routes/measurements.py:225-234`):

```json
{
  "status": "completed",
  "measurements": {
    "Shoulder": 44.8,
    "Neck Round": 39.0,
    "Chest Round": 104.4,
    "Stomach Round": 85.9,
    "Waist Round": 92.2,
    "Hip Round": 99.1,
    "Thigh Round": 55.1,
    "Knee Round": 37.5,
    "Calf Round": 35.8,
    "Ankle Round": 22.2,
    "Inseam": 66.6,
    "Half Length": 53.1,
    "Full Top Length": 63.0,
    "Across Back": 41.2,
    "Across Chest": 43.0,
    "Trouser Waist": 92.2,
    "Trouser Length": 85.4,
    "Crotch Depth": 9.9
  },
  "mesh_url": "/meshes/korra_twin_{task_id}.obj",
  "landmarks": {
    "Shoulder_L": [x, y, z],
    "Shoulder_R": [x, y, z],
    "Hip_L": [x, y, z],
    "Hip_R": [x, y, z],
    "Nose": [x, y, z]
  },
  "body_shape": "Standard",
  "size_recommendation": "M",
  "clinical_realism_index": 97.0,
  "height": 175,
  "gender": "male",
  "client_name": "John Doe",
  "created_at": "2026-06-25T10:30:00"
}
```

For historical scans (from `masterHistory`), the fields are:
```json
{
  "client_name": "John Doe",
  "height": 175,
  "gender": "male",
  "measurements": { ... },
  "biometrics": { ... },     // alias for measurements
  "landmarks": { ... },
  "landmarks_3d": { ... },   // alias for landmarks
  "mesh_url": "/meshes/...",
  "body_shape": "Standard",
  "size_recommendation": "M",
  "created_at": "2026-06-25T10:30:00"
}
```

---

## 3. File Changes

### 3.1 Files to Create

| File | Purpose | Lines |
|------|---------|-------|
| `public/assets/measurement-screen.css` | All styles for the new screen | ~400 |
| `public/assets/measurement-screen.js` | Interaction logic, state machine | ~500 |
| `api/routes/ai_assistant.py` | Free AI endpoint (Groq) | ~80 |

### 3.2 Files to Modify

| File | Changes | Lines Added |
|------|---------|------------|
| `public/assets/korra_viz.js` | Add ring highlight methods | +80 |
| `dashboard.html` | Add link/script tags + tab div + wire functions | +6 |
| `api/main.py` | Register AI router | +2 |

---

## 4. Detailed Specifications

### 4.1 `public/assets/measurement-screen.css` (NEW)

All styles scoped under `.ms-*` prefix to avoid conflicts with existing CSS.

#### 4.1.1 Container

```css
.ms-root {
  /* Full viewport within the tab-view container */
  display: flex;
  flex-direction: column;
  height: calc(100vh - 80px);  /* minus header height */
  overflow: hidden;
  position: relative;
  background: var(--Obsidian-Deep);
}
```

#### 4.1.2 Header Bar

```css
.ms-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 56px;
  flex-shrink: 0;
  background: var(--Obsidian-Layer);
  border-bottom: 1px solid var(--Glass-Border);
  z-index: 10;
}

.ms-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ms-back-btn {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  border: 1px solid var(--Glass-Border);
  background: var(--Glass);
  color: var(--Neutral-400);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}
.ms-back-btn:hover {
  color: var(--Mint);
  border-color: var(--Mint);
}

.ms-scan-info {
  display: flex;
  flex-direction: column;
}
.ms-scan-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--White);
}
.ms-scan-subtitle {
  font-size: 10px;
  color: var(--Neutral-500);
  font-weight: 500;
}

.ms-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ms-header-btn {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  border: 1px solid var(--Glass-Border);
  background: var(--Glass);
  color: var(--Neutral-400);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}
.ms-header-btn:hover {
  color: var(--Mint);
  border-color: var(--Mint);
}
.ms-header-btn.active {
  color: var(--Mint);
  border-color: var(--Mint);
  background: rgba(198, 255, 0, 0.08);
}

.ms-unit-toggle {
  display: flex;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 20px;
  padding: 2px;
  border: 1px solid var(--Glass-Border);
}
.ms-unit-btn {
  padding: 4px 12px;
  border-radius: 18px;
  font-size: 10px;
  font-weight: 900;
  color: var(--Neutral-400);
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  background: none;
}
.ms-unit-btn.active {
  background: var(--Mint);
  color: var(--Teal-900);
}
```

#### 4.1.3 3D Viewer Area

```css
.ms-viewer {
  flex: 1;
  position: relative;
  min-height: 0;
  background: #D4D4D4;
  overflow: hidden;
}
.ms-viewer canvas {
  display: block;
  width: 100% !important;
  height: 100% !important;
}

/* Floating measurement badge on 3D area */
.ms-badge {
  position: absolute;
  top: 16px;
  left: 16px;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(198, 255, 0, 0.3);
  border-radius: 12px;
  padding: 12px 16px;
  z-index: 5;
  pointer-events: none;
}
.ms-badge-label {
  font-size: 9px;
  font-weight: 900;
  color: var(--Neutral-500);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 4px;
}
.ms-badge-value {
  font-size: 24px;
  font-weight: 900;
  color: var(--Mint);
  letter-spacing: -0.02em;
}
.ms-badge-unit {
  font-size: 12px;
  font-weight: 600;
  color: var(--Neutral-400);
  margin-left: 4px;
}
.ms-badge-desc {
  font-size: 10px;
  color: var(--Neutral-500);
  margin-top: 4px;
}
```

#### 4.1.4 View Mode Tabs

```css
.ms-tabs {
  display: flex;
  gap: 4px;
  padding: 0 16px;
  height: 44px;
  flex-shrink: 0;
  background: var(--Obsidian-Layer);
  border-top: 1px solid var(--Glass-Border);
  border-bottom: 1px solid var(--Glass-Border);
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}
.ms-tabs::-webkit-scrollbar { display: none; }

.ms-tab {
  padding: 0 16px;
  height: 44px;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 700;
  color: var(--Neutral-500);
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
  flex-shrink: 0;
}
.ms-tab:hover {
  color: var(--Neutral-400);
}
.ms-tab.active {
  color: var(--Mint);
  border-bottom-color: var(--Mint);
}
.ms-tab-icon {
  width: 14px;
  height: 14px;
  opacity: 0.6;
}
.ms-tab.active .ms-tab-icon {
  opacity: 1;
}
```

#### 4.1.5 Bottom Sheet

```css
.ms-sheet {
  height: 38vh;
  min-height: 200px;
  flex-shrink: 0;
  background: var(--Obsidian-Layer);
  border-top: 1px solid var(--Glass-Border);
  border-radius: 20px 20px 0 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: height 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  z-index: 5;
}
.ms-sheet.expanded {
  height: 70vh;
}
.ms-sheet-handle {
  width: 36px;
  height: 4px;
  border-radius: 2px;
  background: var(--Neutral-500);
  margin: 10px auto 0;
  flex-shrink: 0;
  cursor: grab;
}
.ms-sheet-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px 8px;
  flex-shrink: 0;
}
.ms-sheet-title {
  font-size: 13px;
  font-weight: 800;
  color: var(--White);
}
.ms-sheet-body {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 0 20px 20px;
  -webkit-overflow-scrolling: touch;
}
```

#### 4.1.6 Measurement List (inside sheet)

```css
.ms-meas-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.ms-meas-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.03);
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}
.ms-meas-item:hover {
  background: rgba(255, 255, 255, 0.06);
}
.ms-meas-item.active {
  background: rgba(198, 255, 0, 0.08);
  border-color: rgba(198, 255, 0, 0.3);
}
.ms-meas-item-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.ms-meas-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.ms-meas-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--White);
}
.ms-meas-value {
  font-size: 15px;
  font-weight: 800;
  color: var(--Mint);
  font-variant-numeric: tabular-nums;
}
```

#### 4.1.7 Size Grid (Sizes tab)

```css
.ms-size-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}
.ms-size-card {
  padding: 14px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--Glass-Border);
  text-align: center;
}
.ms-size-label {
  font-size: 9px;
  font-weight: 900;
  color: var(--Neutral-500);
  text-transform: uppercase;
  margin-bottom: 6px;
}
.ms-size-value {
  font-size: 22px;
  font-weight: 900;
  color: var(--Mint);
}
.ms-size-cm {
  font-size: 11px;
  color: var(--Neutral-400);
  margin-top: 2px;
}
```

#### 4.1.8 Shape Card (Shape tab)

```css
.ms-shape-card {
  padding: 24px;
  border-radius: 16px;
  background: rgba(198, 255, 0, 0.05);
  border: 1px solid rgba(198, 255, 0, 0.2);
  text-align: center;
}
.ms-shape-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 16px;
  border-radius: 50%;
  background: rgba(198, 255, 0, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
}
.ms-shape-name {
  font-size: 20px;
  font-weight: 900;
  color: var(--Mint);
  margin-bottom: 8px;
}
.ms-shape-desc {
  font-size: 12px;
  color: var(--Neutral-400);
  line-height: 1.6;
}
.ms-shape-ratio {
  margin-top: 16px;
  padding: 12px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.03);
}
.ms-ratio-label {
  font-size: 9px;
  font-weight: 900;
  color: var(--Neutral-500);
  text-transform: uppercase;
}
.ms-ratio-value {
  font-size: 18px;
  font-weight: 900;
  color: var(--White);
}
```

#### 4.1.9 Compare View (Compare tab)

```css
.ms-compare-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.ms-compare-col {
  text-align: center;
}
.ms-compare-label {
  font-size: 9px;
  font-weight: 900;
  color: var(--Neutral-500);
  text-transform: uppercase;
  margin-bottom: 8px;
}
.ms-compare-viz {
  width: 100%;
  height: 200px;
  background: #D4D4D4;
  border-radius: 12px;
  overflow: hidden;
}
.ms-delta-table {
  margin-top: 16px;
  width: 100%;
}
.ms-delta-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid var(--Glass-Border);
}
.ms-delta-name {
  font-size: 12px;
  color: var(--Neutral-400);
}
.ms-delta-change {
  font-size: 13px;
  font-weight: 800;
}
.ms-delta-change.positive { color: #ff4d4d; }
.ms-delta-change.negative { color: var(--Mint); }
.ms-delta-change.neutral { color: var(--Neutral-500); }
```

#### 4.1.10 AI FAB + Drawer

```css
.ms-ai-fab {
  position: fixed;
  bottom: calc(38vh + 20px);
  right: 24px;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--Mint);
  color: var(--Teal-900);
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 20px rgba(198, 255, 0, 0.3);
  z-index: 20;
  transition: all 0.2s;
}
.ms-ai-fab:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 30px rgba(198, 255, 0, 0.4);
}

.ms-ai-drawer {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.9);
  backdrop-filter: blur(20px);
  z-index: 100;
  display: none;
  flex-direction: column;
}
.ms-ai-drawer.open {
  display: flex;
  animation: msSlideUp 0.3s ease-out;
}

.ms-ai-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid var(--Glass-Border);
  flex-shrink: 0;
}
.ms-ai-title {
  font-size: 16px;
  font-weight: 800;
  color: var(--White);
}
.ms-ai-close {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: 1px solid var(--Glass-Border);
  background: var(--Glass);
  color: var(--Neutral-400);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 14px;
}

.ms-ai-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.ms-ai-prompt {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.ms-ai-prompt-btn {
  padding: 8px 16px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--Glass-Border);
  color: var(--Neutral-400);
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.ms-ai-prompt-btn:hover {
  background: rgba(198, 255, 0, 0.08);
  border-color: var(--Mint);
  color: var(--Mint);
}

.ms-ai-input-bar {
  display: flex;
  gap: 8px;
  padding: 16px 24px;
  border-top: 1px solid var(--Glass-Border);
  flex-shrink: 0;
}
.ms-ai-input {
  flex: 1;
  padding: 12px 16px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--Glass-Border);
  color: var(--White);
  font-size: 13px;
  outline: none;
}
.ms-ai-input:focus {
  border-color: var(--Mint);
}
.ms-ai-send {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: var(--Mint);
  color: var(--Teal-900);
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ms-ai-message {
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.6;
}
.ms-ai-message.user {
  background: rgba(198, 255, 0, 0.08);
  border: 1px solid rgba(198, 255, 0, 0.2);
  color: var(--White);
  align-self: flex-end;
  max-width: 80%;
}
.ms-ai-message.assistant {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--Glass-Border);
  color: var(--Neutral-400);
  align-self: flex-start;
  max-width: 80%;
}
```

#### 4.1.11 Animations

```css
@keyframes msSlideUp {
  from { transform: translateY(100%); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
@keyframes msFadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
@keyframes msPulse {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}
@keyframes msCounter {
  from { transform: scale(0.95); opacity: 0.5; }
  to { transform: scale(1); opacity: 1; }
}
```

#### 4.1.12 Responsive

```css
@media (max-width: 900px) {
  .ms-root {
    height: calc(100vh - 80px - 72px); /* minus header minus bottom bar */
  }
  .ms-sheet {
    height: 45vh;
    min-height: 160px;
  }
  .ms-sheet.expanded {
    height: 75vh;
  }
  .ms-ai-fab {
    bottom: calc(45vh + 16px);
    right: 16px;
  }
  .ms-badge {
    top: 12px;
    left: 12px;
    padding: 8px 12px;
  }
  .ms-badge-value {
    font-size: 20px;
  }
  .ms-compare-grid {
    grid-template-columns: 1fr;
  }
}
```

---

### 4.2 `public/assets/measurement-screen.js` (NEW)

#### 4.2.1 Measurement Ring Color Map

```javascript
const MEASUREMENT_COLORS = {
  // Torso — Mint
  'Chest Round': '#C6FF00',
  'Bust Round': '#C6FF00',
  'Waist Round': '#C6FF00',
  'Hip Round': '#C6FF00',
  'Stomach Round': '#C6FF00',
  'Upper Hip': '#C6FF00',
  // Neck — White
  'Neck Round': '#FFFFFF',
  // Shoulder — Lavender
  'Shoulder': '#B388FF',
  'Across Chest': '#B388FF',
  'Across Back': '#B388FF',
  // Arms — Cyan
  'Bicep Round': '#00D4FF',
  'Elbow Round': '#00D4FF',
  'Wrist Round': '#00D4FF',
  'Sleeve Length': '#00D4FF',
  'Armhole Round': '#00D4FF',
  // Legs — Amber
  'Thigh Round': '#FFC247',
  'Knee Round': '#FFC247',
  'Calf Round': '#FFC247',
  'Ankle Round': '#FFC247',
  'Inseam': '#FFC247',
  'Trouser Length': '#FFC247',
};
```

#### 4.2.2 Measurement Y-Position Map (% of mesh height)

```javascript
const MEASUREMENT_Y_POSITIONS = {
  'Neck Round': 0.90,
  'Shoulder': 0.82,
  'Across Chest': 0.78,
  'Across Back': 0.78,
  'Chest Round': 0.72,
  'Bust Round': 0.72,
  'High Bust': 0.70,
  'Under Bust': 0.65,
  'Bust Point': 0.65,
  'Armhole Round': 0.70,
  'Sleeve Length': 0.65,
  'Stomach Round': 0.60,
  'Waist Round': 0.55,
  'Half Length': 0.50,
  'Full Top Length': 0.45,
  'Hip Round': 0.45,
  'Upper Hip': 0.48,
  'Thigh Round': 0.35,
  'Knee Round': 0.25,
  'Calf Round': 0.18,
  'Ankle Round': 0.08,
  'Inseam': 0.35,
  'Trouser Length': 0.35,
  'Bicep Round': 0.60,
  'Elbow Round': 0.50,
  'Wrist Round': 0.35,
};
```

#### 4.2.3 Measurement Descriptions

```javascript
const MEASUREMENT_DESCRIPTIONS = {
  'Chest Round': 'Circumference at the widest point of the chest.',
  'Bust Round': 'Circumference at the fullest part of the bust.',
  'Waist Round': 'Circumference at the natural waistline.',
  'Hip Round': 'Circumference at the widest point of the hips.',
  'Shoulder': 'Width between the shoulder points.',
  'Neck Round': 'Circumference at the base of the neck.',
  'Thigh Round': 'Circumference at the widest part of the thigh.',
  'Calf Round': 'Circumference at the widest part of the calf.',
  'Inseam': 'Leg length from crotch to floor.',
  'Stomach Round': 'Circumference at the navel level.',
  'Bicep Round': 'Circumference at the widest part of the upper arm.',
  'Wrist Round': 'Circumference at the wrist bone.',
  'Knee Round': 'Circumference at the knee cap.',
  'Ankle Round': 'Circumference at the ankle.',
  'Across Chest': 'Width across the chest between armpits.',
  'Across Back': 'Width across the upper back between armpits.',
  'Half Length': 'Back waist length from neck to waist.',
  'Full Top Length': 'Total length from shoulder to hem.',
  'Sleeve Length': 'Length from shoulder point to wrist.',
  'Elbow Round': 'Circumference at the elbow.',
  'Armhole Round': 'Circumference of the armhole opening.',
  'Upper Hip': 'Circumference at the upper hip level.',
  'Trouser Length': 'Outer leg length from waist to hem.',
  'Crotch Depth': 'Distance from waist to seat.',
  'Trouser Waist': 'Waist measurement for trouser fitting.',
  'High Bust': 'Circumference above the bust, under the arms.',
  'Under Bust': 'Circumference directly under the bust.',
  'Bust Point': 'Distance between the bust points.',
  'Shoulder to Bust Point': 'Length from shoulder to bust point.',
  'Shoulder to Under Bust': 'Length from shoulder to under bust.',
  'Shoulder to Waist': 'Length from shoulder to natural waist.',
  'Front Waist Length': 'Front measurement from shoulder to waist.',
  'Back Waist Length': 'Back measurement from neck to waist.',
  'Waist to Hip': 'Distance from waist to hip line.',
};
```

#### 4.2.4 Body Shape Descriptions

```javascript
const BODY_SHAPE_INFO = {
  'Standard': {
    icon: '○',
    desc: 'Proportional measurements across all regions.',
    advice: 'Standard sizing should fit well off-the-rack.'
  },
  'Hourglass': {
    icon: '⌛',
    desc: 'Balanced bust and hips with a defined waist.',
    advice: 'Empire waists and wrap styles complement this shape.'
  },
  'Rectangle': {
    icon: '▬',
    desc: 'Similar measurements across bust, waist, and hips.',
    advice: 'Structured jackets and A-line skirts create definition.'
  },
  'Inverted Triangle': {
    icon: '▽',
    desc: 'Broader shoulders relative to hips.',
    advice: 'V-necklines and A-line bottoms balance proportions.'
  },
  'Oval': {
    icon: '⬭',
    desc: ' Fuller midsection relative to shoulders and hips.',
    advice: 'Straight-cut shirts and structured blazers work well.'
  },
};
```

#### 4.2.5 Core State Machine

```javascript
window.KORRA_MS = {
  // ── State ──
  active: false,
  data: null,
  viewMode: 'avatar',      // avatar | sizes | metrics | shape | compare
  selectedMeasurement: 'Chest Round',
  unit: 'cm',
  overlaysVisible: true,
  sheetExpanded: false,
  aiOpen: false,
  viewerInstance: null,     // KorraVisualizer instance for this screen
  compareBaseline: null,

  // ── Entry Point ──
  open(data) {
    // data can be from pollTask() completion or viewScan()
    // Normalize: biometrics alias
    if (data.biometrics && !data.measurements) data.measurements = data.biometrics;
    if (data.landmarks_3d && !data.landmarks) data.landmarks = data.landmarks_3d;

    this.data = data;
    this.active = true;
    this.viewMode = 'avatar';
    this.selectedMeasurement = 'Chest Round';
    this.unit = window.CURRENT_UNIT || 'cm';
    this.overlaysVisible = true;
    this.sheetExpanded = false;
    this.aiOpen = false;

    // Store for back navigation
    this._previousTab = document.querySelector('.tab-view.active')?.id?.replace('view-', '') || 'vault';

    // Render HTML into mount point
    this.render();
    this.initViewer();
    this.bindEvents();
    this.updateBadge();

    // Switch to the tab
    window.switchTab('scanresult');
  },

  // ── Render ──
  render() {
    const mount = document.getElementById('ms-mount');
    if (!mount) return;
    mount.innerHTML = this.buildHTML();
  },

  buildHTML() {
    const d = this.data;
    const name = d.client_name || 'Scan Result';
    const date = d.created_at ? new Date(d.created_at).toLocaleDateString() : 'Today';
    const height = d.height ? `${d.height} cm` : '';
    const gender = (d.gender || 'male').charAt(0).toUpperCase() + (d.gender || 'male').slice(1);

    return `
      <div class="ms-root">
        <!-- HEADER -->
        <div class="ms-header">
          <div class="ms-header-left">
            <button class="ms-back-btn" onclick="KORRA_MS.goBack()">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
            </button>
            <div class="ms-scan-info">
              <div class="ms-scan-title">${name}</div>
              <div class="ms-scan-subtitle">${date} · ${height} · ${gender}</div>
            </div>
          </div>
          <div class="ms-header-right">
            <div class="ms-unit-toggle">
              <button class="ms-unit-btn ${this.unit === 'cm' ? 'active' : ''}" onclick="KORRA_MS.setUnit('cm')">CM</button>
              <button class="ms-unit-btn ${this.unit === 'in' ? 'active' : ''}" onclick="KORRA_MS.setUnit('in')">IN</button>
            </div>
            <button class="ms-header-btn ${this.overlaysVisible ? 'active' : ''}" onclick="KORRA_MS.toggleOverlays()" title="Toggle measurement lines">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
            </button>
            <button class="ms-header-btn" onclick="KORRA_MS.resetView()" title="Reset view">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
            </button>
            <button class="ms-header-btn" onclick="KORRA_MS.goBack()" title="Close">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>
        </div>

        <!-- 3D VIEWER -->
        <div class="ms-viewer" id="ms-viewer">
          ${this.buildBadge()}
        </div>

        <!-- VIEW MODE TABS -->
        <div class="ms-tabs">
          <button class="ms-tab ${this.viewMode === 'avatar' ? 'active' : ''}" onclick="KORRA_MS.switchView('avatar')">
            <svg class="ms-tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            Avatar
          </button>
          <button class="ms-tab ${this.viewMode === 'sizes' ? 'active' : ''}" onclick="KORRA_MS.switchView('sizes')">
            <svg class="ms-tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/></svg>
            Sizes
          </button>
          <button class="ms-tab ${this.viewMode === 'metrics' ? 'active' : ''}" onclick="KORRA_MS.switchView('metrics')">
            <svg class="ms-tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3v18h18"/><path d="M18.7 8l-5.1 5.2-2.8-2.7L7 14.3"/></svg>
            Metrics
          </button>
          <button class="ms-tab ${this.viewMode === 'shape' ? 'active' : ''}" onclick="KORRA_MS.switchView('shape')">
            <svg class="ms-tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>
            Shape
          </button>
          <button class="ms-tab ${this.viewMode === 'compare' ? 'active' : ''}" onclick="KORRA_MS.switchView('compare')">
            <svg class="ms-tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="8" height="18" rx="1"/><rect x="14" y="3" width="8" height="18" rx="1"/></svg>
            Compare
          </button>
        </div>

        <!-- BOTTOM SHEET -->
        <div class="ms-sheet" id="ms-sheet">
          <div class="ms-sheet-handle" id="ms-sheet-handle"></div>
          <div class="ms-sheet-header">
            <div class="ms-sheet-title" id="ms-sheet-title">Measurements</div>
          </div>
          <div class="ms-sheet-body" id="ms-sheet-body">
            ${this.buildSheetContent()}
          </div>
        </div>

        <!-- AI FAB -->
        <button class="ms-ai-fab" onclick="KORRA_MS.openAI()" title="Ask AI">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
        </button>

        <!-- AI DRAWER -->
        <div class="ms-ai-drawer" id="ms-ai-drawer">
          <div class="ms-ai-header">
            <div class="ms-ai-title">AI Assistant</div>
            <button class="ms-ai-close" onclick="KORRA_MS.closeAI()">✕</button>
          </div>
          <div class="ms-ai-body" id="ms-ai-body">
            <div class="ms-ai-prompt">
              <button class="ms-ai-prompt-btn" onclick="KORRA_MS.askAI('Explain my body measurements')">Explain this scan</button>
              <button class="ms-ai-prompt-btn" onclick="KORRA_MS.askAI('Recommend clothing fit for my body')">Clothing fit</button>
              <button class="ms-ai-prompt-btn" onclick="KORRA_MS.askAI('Give me a body summary')">Body summary</button>
              <button class="ms-ai-prompt-btn" onclick="KORRA_MS.askAI('What measurements changed since last scan?')">Progress insights</button>
            </div>
          </div>
          <div class="ms-ai-input-bar">
            <input class="ms-ai-input" id="ms-ai-input" placeholder="Ask about your measurements..." onkeydown="if(event.key==='Enter')KORRA_MS.askAI(this.value)">
            <button class="ms-ai-send" onclick="KORRA_MS.askAI(document.getElementById('ms-ai-input').value)">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
            </button>
          </div>
        </div>
      </div>
    `;
  },

  // ... (remaining methods below)
};
```

#### 4.2.6 Sheet Content Builders

```javascript
  buildBadge() {
    const m = this.data.measurements || {};
    const val = m[this.selectedMeasurement];
    const factor = this.unit === 'in' ? 0.393701 : 1;
    const displayVal = val ? (val * factor).toFixed(1) : '—';
    const desc = MEASUREMENT_DESCRIPTIONS[this.selectedMeasurement] || '';
    const color = MEASUREMENT_COLORS[this.selectedMeasurement] || '#C6FF00';

    return `
      <div class="ms-badge">
        <div class="ms-badge-label">${this.selectedMeasurement}</div>
        <div class="ms-badge-value" style="color:${color}">
          ${displayVal}<span class="ms-badge-unit">${this.unit}</span>
        </div>
        <div class="ms-badge-desc">${desc}</div>
      </div>
    `;
  },

  buildSheetContent() {
    switch (this.viewMode) {
      case 'avatar':
      case 'metrics':
        return this.buildMetricsList();
      case 'sizes':
        return this.buildSizesGrid();
      case 'shape':
        return this.buildShapeCard();
      case 'compare':
        return this.buildCompareView();
      default:
        return this.buildMetricsList();
    }
  },

  buildMetricsList() {
    const m = this.data.measurements || {};
    const gender = (this.data.gender || 'male').toLowerCase();
    const factor = this.unit === 'in' ? 0.393701 : 1;

    const maleKeys = ['Shoulder', 'Neck Round', 'Chest Round', 'Across Chest', 'Across Back', 'Stomach Round', 'Waist Round', 'Hip Round', 'Thigh Round', 'Knee Round', 'Calf Round', 'Ankle Round', 'Inseam', 'Half Length', 'Full Top Length', 'Sleeve Length', 'Bicep Round', 'Elbow Round', 'Wrist Round', 'Trouser Length', 'Trouser Waist', 'Crotch Depth'];
    const femaleKeys = ['Shoulder', 'Neck Round', 'Bust Round', 'High Bust', 'Under Bust', 'Bust Point', 'Shoulder to Bust Point', 'Across Chest', 'Across Back', 'Armhole Round', 'Shoulder to Waist', 'Front Waist Length', 'Back Waist Length', 'Waist Round', 'Half Length', 'Waist to Hip', 'Sleeve Length', 'Bicep Round', 'Elbow Round', 'Wrist Round', 'Upper Hip', 'Hip Round', 'Thigh Round', 'Knee Round', 'Calf Round', 'Ankle Round'];

    const keys = gender === 'female' ? femaleKeys : maleKeys;

    return `<div class="ms-meas-list">` + keys.map(k => {
      const val = m[k];
      const displayVal = val !== undefined && val !== null ? (val * factor).toFixed(1) : '—';
      const color = MEASUREMENT_COLORS[k] || '#C6FF00';
      const isActive = k === this.selectedMeasurement;
      return `
        <div class="ms-meas-item ${isActive ? 'active' : ''}" onclick="KORRA_MS.selectMeasurement('${k}')">
          <div class="ms-meas-item-left">
            <div class="ms-meas-dot" style="background:${color}"></div>
            <div class="ms-meas-name">${k}</div>
          </div>
          <div class="ms-meas-value">${displayVal}${val !== undefined && val !== null ? this.unit : ''}</div>
        </div>
      `;
    }).join('') + '</div>';
  },

  buildSizesGrid() {
    const m = this.data.measurements || {};
    const sizeRec = this.data.size_recommendation || 'M';
    const factor = this.unit === 'in' ? 0.393701 : 1;

    const sizeMap = {
      'Chest Round': this.getSizeLabel(m['Chest Round'], 'chest'),
      'Waist Round': this.getSizeLabel(m['Waist Round'], 'waist'),
      'Hip Round': this.getSizeLabel(m['Hip Round'], 'hip'),
      'Shoulder': this.getSizeLabel(m['Shoulder'] * 2, 'shoulder'),
      'Thigh Round': this.getSizeLabel(m['Thigh Round'], 'thigh'),
      'Overall': sizeRec,
    };

    return `
      <div class="ms-size-grid">
        ${Object.entries(sizeMap).map(([label, size]) => `
          <div class="ms-size-card">
            <div class="ms-size-label">${label}</div>
            <div class="ms-size-value">${size}</div>
            ${m[label] ? `<div class="ms-size-cm">${(m[label] * factor).toFixed(1)} ${this.unit}</div>` : ''}
          </div>
        `).join('')}
      </div>
    `;
  },

  getSizeLabel(value, region) {
    if (!value) return '—';
    // Simple size mapping based on common measurements
    const sizes = {
      chest: [[80,'XS'],[88,'S'],[96,'M'],[104,'L'],[112,'XL'],[120,'XXL']],
      waist: [[68,'XS'],[76,'S'],[84,'M'],[92,'L'],[100,'XL'],[108,'XXL']],
      hip: [[84,'XS'],[92,'S'],[100,'M'],[108,'L'],[116,'XL'],[124,'XXL']],
      shoulder: [[40,'XS'],[43,'S'],[46,'M'],[49,'L'],[52,'XL'],[55,'XXL']],
      thigh: [[48,'XS'],[52,'S'],[56,'M'],[60,'L'],[64,'XL'],[68,'XXL']],
    };
    const thresholds = sizes[region];
    if (!thresholds) return '—';
    for (const [thresh, label] of thresholds) {
      if (value <= thresh) return label;
    }
    return 'XXL';
  },

  buildShapeCard() {
    const shape = this.data.body_shape || 'Standard';
    const info = BODY_SHAPE_INFO[shape] || BODY_SHAPE_INFO['Standard'];
    const m = this.data.measurements || {};
    const chest = m['Chest Round'] || 0;
    const waist = m['Waist Round'] || 1;
    const ratio = waist > 0 ? (chest / waist).toFixed(2) : '—';

    return `
      <div class="ms-shape-card">
        <div class="ms-shape-icon" style="font-size:28px">${info.icon}</div>
        <div class="ms-shape-name">${shape}</div>
        <div class="ms-shape-desc">${info.desc}</div>
        <div class="ms-shape-desc" style="margin-top:8px; color:var(--Mint)">${info.advice}</div>
        <div class="ms-shape-ratio">
          <div class="ms-ratio-label">Chest / Waist Ratio</div>
          <div class="ms-ratio-value">${ratio}</div>
        </div>
      </div>
    `;
  },

  buildCompareView() {
    // Get previous scans for same client
    const clientName = this.data.client_name;
    const scans = (window.masterHistory || []).filter(s => s.client_name === clientName && s !== this.data);

    if (scans.length === 0) {
      return '<div style="text-align:center; padding:40px; color:var(--Neutral-500)"><p>No previous scans for comparison.</p><p style="font-size:11px; margin-top:8px">Take another scan to see changes over time.</p></div>';
    }

    const baseline = scans[scans.length - 1]; // oldest
    const current = this.data;
    const factor = this.unit === 'in' ? 0.393701 : 1;

    // Compute deltas
    const m1 = baseline.measurements || baseline.biometrics || {};
    const m2 = current.measurements || current.biometrics || {};
    const allKeys = [...new Set([...Object.keys(m1), ...Object.keys(m2)])];

    let deltaHTML = '';
    for (const key of allKeys) {
      const v1 = m1[key];
      const v2 = m2[key];
      if (v1 === undefined && v2 === undefined) continue;
      const val1 = (v1 || 0) * factor;
      const val2 = (v2 || 0) * factor;
      const delta = val2 - val1;
      const cls = delta > 0.5 ? 'positive' : delta < -0.5 ? 'negative' : 'neutral';
      const sign = delta > 0 ? '+' : '';
      deltaHTML += `
        <div class="ms-delta-row">
          <div class="ms-delta-name">${key}</div>
          <div class="ms-delta-change ${cls}">${sign}${delta.toFixed(1)}${this.unit}</div>
        </div>`;
    }

    return `
      <div class="ms-compare-grid">
        <div class="ms-compare-col">
          <div class="ms-compare-label">Baseline</div>
          <div class="ms-compare-viz" id="ms-compare-baseline"></div>
          <div style="font-size:10px; color:var(--Neutral-500); margin-top:8px">${new Date(baseline.created_at).toLocaleDateString()}</div>
        </div>
        <div class="ms-compare-col">
          <div class="ms-compare-label">Current</div>
          <div class="ms-compare-viz" id="ms-compare-current"></div>
          <div style="font-size:10px; color:var(--Neutral-500); margin-top:8px">${new Date(current.created_at).toLocaleDateString()}</div>
        </div>
      </div>
      <div class="ms-delta-table">${deltaHTML}</div>
    `;
  },
```

#### 4.2.7 Core Methods

```javascript
  // ── Navigation ──
  goBack() {
    this.cleanup();
    window.switchTab(this._previousTab || 'vault');
  },

  // ── View Mode ──
  switchView(mode) {
    this.viewMode = mode;
    // Update tab active state
    document.querySelectorAll('.ms-tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`.ms-tab[onclick*="${mode}"]`)?.classList.add('active');
    // Rebuild sheet content
    const body = document.getElementById('ms-sheet-body');
    const title = document.getElementById('ms-sheet-title');
    if (body) body.innerHTML = this.buildSheetContent();
    if (title) {
      const titles = { avatar: 'Measurements', sizes: 'Size Chart', metrics: 'All Metrics', shape: 'Body Shape', compare: 'Compare Scans' };
      title.textContent = titles[mode] || 'Measurements';
    }
    // Initialize compare viewers if needed
    if (mode === 'compare') this.initCompareViewers();
  },

  // ── Measurement Selection ──
  selectMeasurement(key) {
    this.selectedMeasurement = key;
    this.updateBadge();
    // Highlight ring on 3D model
    if (this.viewerInstance) {
      this.viewerInstance.clearMeasurementRings();
      const yPct = MEASUREMENT_Y_POSITIONS[key] || 0.5;
      const color = MEASUREMENT_COLORS[key] || '#C6FF00';
      this.viewerInstance.showMeasurementRing(yPct, color);
    }
    // Update active state in list
    document.querySelectorAll('.ms-meas-item').forEach(el => el.classList.remove('active'));
    // Re-render badge
    const badge = document.getElementById('ms-badge');
    if (badge) badge.outerHTML = this.buildBadge();
    // Auto-collapse sheet on mobile
    if (window.innerWidth <= 900) this.collapseSheet();
  },

  // ── Badge Update ──
  updateBadge() {
    const viewer = document.getElementById('ms-viewer');
    if (!viewer) return;
    const existing = viewer.querySelector('.ms-badge');
    if (existing) existing.remove();
    viewer.insertAdjacentHTML('beforeend', this.buildBadge());
  },

  // ── Unit Toggle ──
  setUnit(unit) {
    this.unit = unit;
    window.CURRENT_UNIT = unit;
    // Update toggle buttons
    document.querySelectorAll('.ms-unit-btn').forEach(btn => {
      btn.classList.toggle('active', btn.textContent.trim().toLowerCase() === unit);
    });
    this.updateBadge();
    // Rebuild sheet content
    const body = document.getElementById('ms-sheet-body');
    if (body) body.innerHTML = this.buildSheetContent();
  },

  // ── Overlay Toggle ──
  toggleOverlays() {
    this.overlaysVisible = !this.overlaysVisible;
    const btn = document.querySelector('.ms-header-btn[onclick*="toggleOverlays"]');
    if (btn) btn.classList.toggle('active', this.overlaysVisible);
    if (this.viewerInstance) {
      if (this.overlaysVisible) {
        const yPct = MEASUREMENT_Y_POSITIONS[this.selectedMeasurement] || 0.5;
        const color = MEASUREMENT_COLORS[this.selectedMeasurement] || '#C6FF00';
        this.viewerInstance.showMeasurementRing(yPct, color);
      } else {
        this.viewerInstance.clearMeasurementRings();
      }
    }
  },

  // ── Reset View ──
  resetView() {
    if (this.viewerInstance) this.viewerInstance.resetCamera();
    this.selectMeasurement('Chest Round');
    this.overlaysVisible = true;
    this.updateBadge();
  },

  // ── Sheet Drag ──
  expandSheet() {
    this.sheetExpanded = true;
    document.getElementById('ms-sheet')?.classList.add('expanded');
  },
  collapseSheet() {
    this.sheetExpanded = false;
    document.getElementById('ms-sheet')?.classList.remove('expanded');
  },

  // ── 3D Viewer ──
  initViewer() {
    if (!window.KORRA_VIZ) return;
    // Create a new instance for the measurement screen
    if (window.createKorraVisualizer) {
      this.viewerInstance = window.createKorraVisualizer();
    } else {
      this.viewerInstance = window.KORRA_VIZ;
    }
    this.viewerInstance.init('ms-viewer');
    // Load mesh
    const meshUrl = this.data.mesh_url;
    if (meshUrl) {
      const lm = this.data.landmarks;
      const lm3d = lm ? Object.fromEntries(
        Object.entries(lm).map(([k, v]) => [k, { x: v[0], y: v[1], z: 0 }])
      ) : null;
      this.viewerInstance.loadMesh(meshUrl, lm3d).catch(e =>
        console.warn('🟡 Mesh unavailable:', e?.message)
      );
    }
    // Show initial measurement ring
    setTimeout(() => {
      if (this.overlaysVisible && this.viewerInstance) {
        const yPct = MEASUREMENT_Y_POSITIONS[this.selectedMeasurement] || 0.5;
        const color = MEASUREMENT_COLORS[this.selectedMeasurement] || '#C6FF00';
        this.viewerInstance.showMeasurementRing(yPct, color);
      }
    }, 500);
  },

  initCompareViewers() {
    // Initialize side-by-side viewers for compare tab
    // Uses createKorraVisualizer() factory
    const baselineViz = window.createKorraVisualizer?.();
    const currentViz = window.createKorraVisualizer?.();
    if (baselineViz) baselineViz.init('ms-compare-baseline');
    if (currentViz) currentViz.init('ms-compare-current');
    // Load meshes
    const clientName = this.data.client_name;
    const scans = (window.masterHistory || []).filter(s => s.client_name === clientName && s !== this.data);
    if (scans.length > 0) {
      const baseline = scans[scans.length - 1];
      if (baseline.mesh_url && baselineViz) baselineViz.loadMesh(baseline.mesh_url);
      if (this.data.mesh_url && currentViz) currentViz.loadMesh(this.data.mesh_url);
    }
  },

  // ── Sheet Handle Drag ──
  bindEvents() {
    const handle = document.getElementById('ms-sheet-handle');
    if (!handle) return;
    let startY = 0;
    let startHeight = 0;
    handle.addEventListener('touchstart', (e) => {
      startY = e.touches[0].clientY;
      startHeight = document.getElementById('ms-sheet')?.offsetHeight || 0;
    }, { passive: true });
    handle.addEventListener('touchmove', (e) => {
      const delta = startY - e.touches[0].clientY;
      const newHeight = Math.max(150, Math.min(window.innerHeight * 0.8, startHeight + delta));
      const sheet = document.getElementById('ms-sheet');
      if (sheet) sheet.style.height = newHeight + 'px';
    }, { passive: true });
    handle.addEventListener('touchend', () => {
      const sheet = document.getElementById('ms-sheet');
      if (!sheet) return;
      const height = sheet.offsetHeight;
      const threshold = window.innerHeight * 0.5;
      if (height > threshold) {
        this.expandSheet();
      } else {
        this.collapseSheet();
      }
      sheet.style.height = '';
    });
    // Mouse drag for desktop
    handle.addEventListener('mousedown', (e) => {
      startY = e.clientY;
      startHeight = document.getElementById('ms-sheet')?.offsetHeight || 0;
      const onMove = (e) => {
        const delta = startY - e.clientY;
        const newHeight = Math.max(150, Math.min(window.innerHeight * 0.8, startHeight + delta));
        const sheet = document.getElementById('ms-sheet');
        if (sheet) sheet.style.height = newHeight + 'px';
      };
      const onUp = () => {
        window.removeEventListener('mousemove', onMove);
        window.removeEventListener('mouseup', onUp);
        const sheet = document.getElementById('ms-sheet');
        if (!sheet) return;
        const height = sheet.offsetHeight;
        const threshold = window.innerHeight * 0.5;
        if (height > threshold) {
          this.expandSheet();
        } else {
          this.collapseSheet();
        }
        sheet.style.height = '';
      };
      window.addEventListener('mousemove', onMove);
      window.addEventListener('mouseup', onUp);
    });
  },

  // ── AI ──
  openAI() {
    this.aiOpen = true;
    document.getElementById('ms-ai-drawer')?.classList.add('open');
  },
  closeAI() {
    this.aiOpen = false;
    document.getElementById('ms-ai-drawer')?.classList.remove('open');
  },
  async askAI(prompt) {
    if (!prompt || !prompt.trim()) return;
    const body = document.getElementById('ms-ai-body');
    const input = document.getElementById('ms-ai-input');
    if (!body) return;

    // Add user message
    body.insertAdjacentHTML('beforeend', `<div class="ms-ai-message user">${prompt}</div>`);
    if (input) input.value = '';
    body.scrollTop = body.scrollHeight;

    // Add loading
    body.insertAdjacentHTML('beforeend', `<div class="ms-ai-message assistant" id="ms-ai-loading" style="animation:msPulse 1s infinite">Thinking...</div>`);
    body.scrollTop = body.scrollHeight;

    try {
      const res = await fetch('/api/v2/ai/assist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt,
          measurements: this.data.measurements || this.data.biometrics || {},
          body_shape: this.data.body_shape || 'Standard',
          size_recommendation: this.data.size_recommendation || 'M',
          height: this.data.height,
          gender: this.data.gender
        })
      });
      const data = await res.json();
      const loading = document.getElementById('ms-ai-loading');
      if (loading) loading.remove();
      body.insertAdjacentHTML('beforeend', `<div class="ms-ai-message assistant">${data.response || 'No response available.'}</div>`);
    } catch (e) {
      const loading = document.getElementById('ms-ai-loading');
      if (loading) loading.remove();
      body.insertAdjacentHTML('beforeend', `<div class="ms-ai-message assistant">Sorry, AI assistant is unavailable. Please try again later.</div>`);
    }
    body.scrollTop = body.scrollHeight;
  },

  // ── Cleanup ──
  cleanup() {
    this.active = false;
    this.data = null;
    if (this.viewerInstance && this.viewerInstance !== window.KORRA_VIZ) {
      // Don't destroy the global instance
    }
    this.viewerInstance = null;
  }
};
```

---

### 4.3 `public/assets/korra_viz.js` (MODIFY — +80 lines)

Add these methods to the `KorraVisualizer` class:

```javascript
// ── NEW METHODS (add inside class body) ──

showMeasurementRing(yPercent, color = '#C6FF00') {
  /**
   * Draw a torus ring at yPercent (0-1) of the mesh height.
   * yPercent: 0 = feet, 1 = top of head
   */
  if (!this.mesh || !this.scene) return;
  this.clearMeasurementRings();

  // Get mesh bounding box
  this.mesh.geometry.computeBoundingBox();
  const bbox = this.mesh.geometry.boundingBox;
  const meshHeight = bbox.max.y - bbox.min.y;
  const meshY = bbox.min.y + meshHeight * yPercent;

  // Create torus
  const torusGeo = new THREE.TorusGeometry(0.35, 0.008, 8, 64);
  const torusMat = new THREE.MeshBasicMaterial({
    color: new THREE.Color(color),
    transparent: true,
    opacity: 0.9,
    side: THREE.DoubleSide
  });
  const torus = new THREE.Mesh(torusGeo, torusMat);
  torus.position.y = meshY;
  torus.rotation.x = Math.PI / 2; // horizontal

  // Add glow ring (slightly larger, more transparent)
  const glowGeo = new THREE.TorusGeometry(0.36, 0.02, 8, 64);
  const glowMat = new THREE.MeshBasicMaterial({
    color: new THREE.Color(color),
    transparent: true,
    opacity: 0.25,
    side: THREE.DoubleSide
  });
  const glow = new THREE.Mesh(glowGeo, glowMat);
  glow.position.y = meshY;
  glow.rotation.x = Math.PI / 2;

  // Create group for cleanup
  if (!this._measurementRings) this._measurementRings = new THREE.Group();
  this._measurementRings.add(torus);
  this._measurementRings.add(glow);
  this.scene.add(this._measurementRings);
}

clearMeasurementRings() {
  if (this._measurementRings && this.scene) {
    this.scene.remove(this._measurementRings);
    this._measurementRings.traverse(child => {
      if (child.geometry) child.geometry.dispose();
      if (child.material) child.material.dispose();
    });
    this._measurementRings = null;
  }
}

resetCamera() {
  this.camera.position.set(0, 1.0, 3.0);
  this.camera.lookAt(0, 1, 0);
  this.targetRotationX = 0;
  this.targetRotationY = 0;
  if (this.mesh) {
    this.mesh.rotation.x = 0;
    this.mesh.rotation.y = 0;
  }
  if (this.landmarksGroup) {
    this.landmarksGroup.rotation.x = 0;
    this.landmarksGroup.rotation.y = 0;
  }
}
```

---

### 4.4 `dashboard.html` (MODIFY — ~6 lines)

#### 4.4.1 Add CSS link (in `<head>`, after existing `<link>` tags):

```html
<link rel="stylesheet" href="/assets/measurement-screen.css">
```

#### 4.4.2 Add tab-view div (after the mobile-3d-overlay, before `#view-billing`):

```html
<div id="view-scanresult" class="tab-view">
  <div id="ms-mount"></div>
</div>
```

#### 4.4.3 Add JS script (before `</body>`, after existing scripts):

```html
<script src="/assets/measurement-screen.js"></script>
```

#### 4.4.4 Change `pollTask()` completion (line 3456):

```javascript
// OLD:
document.getElementById('measurementResultsCard').style.display='block';

// NEW:
window.KORRA_MS && window.KORRA_MS.open(data);
```

#### 4.4.5 Rewrite `viewScan()` (line 3008-3047):

The current `viewScan()` does 4 things that are now handled by `KORRA_MS.open()`:
1. Loads mesh into global KORRA_VIZ → **handled by MS.initViewer()**
2. Syncs UI state (attire context, material rail) → **handled by MS.open()**
3. Calls renderMeasurementGrids() → **handled by MS.buildSheetContent()**
4. Shows #measurementResultsCard → **handled by switchTab('scanresult')**

**New `viewScan()` — simplified to 3 lines:**
```javascript
window.viewScan = (idx) => {
    const s = masterHistory[idx];
    if (!s) return;
    if (s.biometrics && !s.measurements) s.measurements = s.biometrics;
    if (s.landmarks_3d && !s.landmarks) s.landmarks = s.landmarks_3d;
    window.KORRA_MS && window.KORRA_MS.open(s);
};
```

**What gets removed from viewScan():**
- Lines 3013: `window.LAST_MEASUREMENT_DATA = s;` → **MS stores its own data**
- Lines 3015-3017: ACTIVE_CONTEXT/ACTIVE_MATERIAL reset → **MS handles context internally**
- Lines 3019-3023: KORRA_VIZ.loadMesh() → **MS.initViewer() handles this**
- Lines 3025-3038: Attire/Material UI sync → **MS has its own UI**
- Lines 3040: renderMeasurementGrids() → **MS.buildSheetContent()**
- Lines 3042-3044: Craftsman Notes → **MS has AI drawer**
- Line 3046: Show measurementResultsCard → **switchTab('scanresult')**

#### 4.4.6 Simplify passport card onclick handlers:

**Passport card entire card click (line 3108):**
```javascript
// OLD:
onclick="event.stopPropagation(); window.switchTab('overview'); requestAnimationFrame(() => window.viewScan(${viewIdx}))"

// NEW:
onclick="event.stopPropagation(); window.KORRA_MS && window.KORRA_MS.open(masterHistory[${viewIdx}])"
```

**Passport "View Measurements" button (line 3138):**
```javascript
// OLD:
onclick="event.stopPropagation(); window.switchTab('overview'); requestAnimationFrame(() => window.viewScan(${viewIdx}))"

// NEW:
onclick="event.stopPropagation(); window.KORRA_MS && window.KORRA_MS.open(masterHistory[${viewIdx}])"
```

**Why:** The current code does a double-hop (switch to overview → then viewScan shows the card). The new code directly opens the measurement screen without the intermediate tab switch. This eliminates the brief flash of the overview tab.

---

### 4.5 `api/routes/ai_assistant.py` (NEW — ~80 lines)

```python
"""
AI Assistant Route — Free Groq Integration
==========================================
POST /api/v2/ai/assist
Uses Groq free tier (llama-3.3-70b-versatile, 14,400 req/day).
Falls back to static responses if GROQ_API_KEY is not set.
"""
import os
import logging
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional

router = APIRouter()
logger = logging.getLogger("KORRA_AI")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_BASE_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are KORRA AI, a body measurement assistant for tailors and fashion professionals. 
You help users understand their body measurements, recommend clothing sizes, and provide fitting advice.

Key guidelines:
- Be concise and direct (2-3 sentences max per answer)
- Use measurement data provided to give specific advice
- Reference specific numbers from the measurements
- If asked about sizes, use standard sizing charts
- Be professional but friendly
- If you don't have enough data, say so honestly

You have access to the user's scan data including measurements, body shape, and size recommendation."""


class AIRequest(BaseModel):
    prompt: str
    measurements: Dict = {}
    body_shape: str = "Standard"
    size_recommendation: str = "M"
    height: Optional[float] = None
    gender: Optional[str] = None


def build_context(data: AIRequest) -> str:
    """Build context string from measurement data."""
    lines = [f"Body Shape: {data.body_shape}", f"Size Recommendation: {data.size_recommendation}"]
    if data.height:
        lines.append(f"Height: {data.height} cm")
    if data.gender:
        lines.append(f"Gender: {data.gender}")
    if data.measurements:
        lines.append("Measurements:")
        for k, v in sorted(data.measurements.items()):
            if v is not None:
                lines.append(f"  {k}: {v} cm")
    return "\n".join(lines)


@router.post("/ai/assist")
async def assist(data: AIRequest):
    """AI assistant endpoint using Groq free tier."""
    if not data.prompt or not data.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt is required")

    # Fallback: static responses if no API key
    if not GROQ_API_KEY:
        return {"response": get_static_response(data.prompt, data)}

    try:
        context = build_context(data)
        user_message = f"User data:\n{context}\n\nUser question: {data.prompt}"

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                GROQ_BASE_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_message}
                    ],
                    "max_tokens": 200,
                    "temperature": 0.7
                }
            )

            if resp.status_code == 200:
                result = resp.json()
                reply = result["choices"][0]["message"]["content"]
                return {"response": reply}
            else:
                logger.error(f"Groq API error: {resp.status_code} - {resp.text[:200]}")
                return {"response": get_static_response(data.prompt, data)}

    except Exception as e:
        logger.error(f"AI assist error: {e}")
        return {"response": get_static_response(data.prompt, data)}


def get_static_response(prompt: str, data: AIRequest) -> str:
    """Generate static response based on measurement data."""
    prompt_lower = prompt.lower()
    m = data.measurements
    shape = data.body_shape
    size = data.size_recommendation

    if any(w in prompt_lower for w in ['explain', 'summary', 'overview']):
        chest = m.get('Chest Round', 0)
        waist = m.get('Waist Round', 0)
        hip = m.get('Hip Round', 0)
        return (f"Your scan shows a {shape.lower()} body profile. "
                f"Chest: {chest}cm, Waist: {waist}cm, Hip: {hip}cm. "
                f"Recommended size: {size}. "
                f"Height: {data.height or 'not specified'}cm.")

    if any(w in prompt_lower for w in ['size', 'fit', 'clothing']):
        return (f"Based on your measurements, you're a size {size}. "
                f"For best fit, consider your {shape.lower()} body shape when selecting styles. "
                f"Chest {m.get('Chest Round', 0)}cm suggests {size} in most brands.")

    if any(w in prompt_lower for w in ['shape', 'body', 'proportion']):
        shape_advice = {
            'Standard': 'Your proportions are balanced across all regions.',
            'Hourglass': 'You have balanced bust and hips with a defined waist.',
            'Rectangle': 'Your bust, waist, and hip measurements are similar.',
            'Inverted Triangle': 'Your shoulders are broader than your hips.',
            'Oval': 'Your midsection is fuller relative to shoulders and hips.',
        }
        return f"Your body shape is {shape}. {shape_advice.get(shape, shape_advice['Standard'])}"

    if any(w in prompt_lower for w in ['progress', 'change', 'compare']):
        return "Compare your current scan with previous scans to track changes over time. Use the Compare tab to see measurement deltas."

    return (f"Your measurements: Chest {m.get('Chest Round', 0)}cm, "
            f"Waist {m.get('Waist Round', 0)}cm, Hip {m.get('Hip Round', 0)}cm. "
            f"Size: {size}. Shape: {shape}. "
            f"Ask me about sizing, fit recommendations, or body analysis.")
```

---

### 4.6 `api/main.py` (MODIFY — +2 lines)

Add after line 83 (after `scan_requests` import):

```python
from api.routes import ai_assistant
app.include_router(ai_assistant.router, prefix="/api/v2", tags=["AI"])
```

---

## 5. Interaction Flows

### 5.1 Entry Flow (New Scan)

```
1. User fills scan form → submits
2. pollTask() polls /api/v2/measurements/status/{task_id}
3. status === 'completed' → data received
4. window.KORRA_MS.open(data) called
5. switchTab('scanresult') → #view-scanresult shown
6. MS renders: header (client name, date, height)
7. MS initializes 3D viewer → loads mesh
8. MS shows measurement ring (Chest Round default)
9. MS shows badge: "Chest Round — 104.4 cm"
10. MS shows bottom sheet with measurement list
```

### 5.2 Entry Flow (Historical Scan — 4 Entry Points)

#### 5.2.1 Ledger "View" Button
```
1. User clicks "View" button on scan item in vault ledger
2. window.viewScan(idx) called with masterHistory index
3. viewScan() normalizes data (biometrics→measurements, landmarks_3d→landmarks)
4. viewScan() calls window.KORRA_MS.open(data)
5. KORRA_MS.open() stores _previousTab = 'vault'
6. KORRA_MS.open() calls switchTab('scanresult')
7. Measurement screen renders: header, 3D viewer, tabs, sheet
```

#### 5.2.2 Passport Card Click (entire card)
```
1. User clicks anywhere on passport card
2. onclick fires: KORRA_MS.open(masterHistory[viewIdx])
3. KORRA_MS.open() stores _previousTab = 'vault'
4. KORRA_MS.open() calls switchTab('scanresult')
5. Measurement screen renders
NOTE: Current code does switchTab('overview') first (flash), then viewScan().
      New code eliminates the intermediate tab switch.
```

#### 5.2.3 Passport "View Measurements" Button
```
1. User clicks "View Measurements" button on passport card
2. onclick fires: KORRA_MS.open(masterHistory[viewIdx])
3. Same flow as 5.2.2
```

#### 5.2.4 Scan Completion (new scan)
```
1. User completes scan via scan modal
2. pollTask() detects status === 'completed'
3. data = response JSON from /api/v2/measurements/status/{task_id}
4. window.KORRA_MS.open(data) called
5. KORRA_MS.open() stores _previousTab = 'vault' (current active tab)
6. KORRA_MS.open() calls switchTab('scanresult')
7. Measurement screen renders
NOTE: Scan modal is dismissed by pollTask() before KORRA_MS.open() is called.
```

### 5.3 Measurement Selection

```
1. User taps measurement in bottom sheet list
2. KORRA_MS.selectMeasurement('Hip Round') called
3. selectedMeasurement = 'Hip Round'
4. Badge updates: "Hip Round — 99.1 cm"
5. Ring color changes: Mint (torso)
6. Ring position moves to Y=0.45 (hip level)
7. Camera auto-rotates to show hip region
8. On mobile: sheet collapses to show 3D viewer
```

### 5.4 View Mode Switch

```
1. User taps "Sizes" tab
2. KORRA_MS.switchView('sizes') called
3. viewMode = 'sizes'
4. Tab active state updates
5. Sheet content rebuilds: size grid
6. Title updates: "Size Chart"
```

### 5.5 AI Assistant

```
1. User taps ⚡ FAB button
2. KORRA_MS.openAI() called
3. AI drawer slides up (0.3s animation)
4. User taps quick prompt or types custom question
5. KORRA_MS.askAI(prompt) called
6. User message appears in drawer
7. Loading indicator shows
8. POST /api/v2/ai/assist sent with measurement context
9. Response appears in drawer
10. User swipes down or taps ✕ to close
```

### 5.6 Back Navigation

```
1. User taps back arrow in header
2. KORRA_MS.goBack() called
3. switchTab(previousTab) → returns to vault/overview
4. Measurement screen DOM is preserved (tab hidden, not destroyed)
```

---

## 6. Implementation Order

| Step | File | Action | Description |
|------|------|--------|-------------|
| 1 | `public/assets/measurement-screen.css` | CREATE | All styles (~400 lines) |
| 2 | `public/assets/korra_viz.js` | MODIFY | Add ring methods (+80 lines) |
| 3 | `public/assets/measurement-screen.js` | CREATE | State machine + logic (~500 lines) |
| 4 | `dashboard.html` | MODIFY | Add link/script tags + tab div + wire functions (~6 lines) |
| 5 | `api/routes/ai_assistant.py` | CREATE | AI endpoint (~80 lines) |
| 6 | `api/main.py` | MODIFY | Register AI router (+2 lines) |
| 7 | — | TEST | Verify full flow locally |
| 8 | — | DEPLOY | Git push + EC2 rebuild |

---

## 7. What Is NOT Touched

- ✅ Sidebar navigation (zero changes)
- ✅ Header (zero changes)
- ✅ Existing tab views (zero changes)
- ✅ Existing measurement card HTML (hidden when new tab active, but untouched)
- ✅ Existing CSS variables (zero changes)
- ✅ Existing JS functions (only 2 lines redirected in viewScan)
- ✅ Mobile bottom bar (zero changes)
- ✅ Scan modal (zero changes)
- ✅ Vault tab layout (two-column split unchanged)
- ✅ Ledger search/filter (unchanged)
- ✅ Passport card data (unchanged — same glass-card structure)
- ✅ Scan list rendering (renderLedger unchanged)
- ✅ Passport rendering (renderPassports unchanged)

---

## 8. Testing Checklist

### Core Measurement Screen
- [ ] Scan completes → measurement screen opens automatically
- [ ] Historical scan "View" button → measurement screen opens
- [ ] Back button returns to vault/overview
- [ ] 3D mesh loads and renders correctly
- [ ] Measurement ring appears at correct Y-position
- [ ] Ring color matches body region
- [ ] Tapping measurement in list updates badge + ring
- [ ] CM/IN toggle updates all values
- [ ] Eye toggle shows/hides rings
- [ ] Refresh resets camera + default measurement
- [ ] Avatar tab shows measurement list
- [ ] Sizes tab shows size grid
- [ ] Metrics tab shows full measurement list
- [ ] Shape tab shows body shape analysis
- [ ] Compare tab shows delta table (if 2+ scans exist)
- [ ] AI FAB opens drawer
- [ ] Quick prompts send to backend
- [ ] Custom input sends to backend
- [ ] AI response renders in drawer
- [ ] Close button dismisses drawer
- [ ] Sheet drag-to-expand works on mobile
- [ ] Sheet drag-to-collapse works on mobile
- [ ] Responsive layout works at 900px breakpoint
- [ ] No console errors
- [ ] No regressions in existing dashboard functionality

### Vault & Ledger Integration
- [ ] Vault ledger "View" button opens measurement screen
- [ ] Vault passport card click opens measurement screen (no flash)
- [ ] Vault "View Measurements" button opens measurement screen
- [ ] Measurement screen back button returns to vault tab
- [ ] Vault left column no longer shows measurement card
- [ ] Existing measurement card is hidden when scanresult tab is active
