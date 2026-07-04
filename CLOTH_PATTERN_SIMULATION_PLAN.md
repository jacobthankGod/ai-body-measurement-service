# KORRA: Cloth Pattern Generation & 3D Simulation Roadmap
**Objective**: Transform the Scan Result Screen into a complete "Design & Fitting Studio" by integrating with an expanded Attire and Fabric library.

---

## Core Tech Stack

| Layer | Technology | Why? |
|-------|-----------|------|
| 2D Pattern Drafting | Client-side SVG (JavaScript) | Programmatic pattern drafting from SMPL measurements using custom geometry engine. |
| 3D Cloth Simulation | [TailorNet](https://github.com/zgeng/TailorNet) (Python) | Neural cloth engine that uses SMPL body parameters to predict garment drape with realistic wrinkles in real-time. |
| Virtual Try-On Rendering | PyTorch3D / Blender bpy | Renders virtual garments on the user's 3D digital twin. Handles collisions (cloth-skin clipping). |
| Core Inference | Python + JavaScript | Extract measurements (Python), draft patterns (JavaScript), simulate drape (Python/TailorNet). |
| 3D Viewport | Three.js (existing `korra_viz.js`) | Client-side rendering of body + garment meshes. |

### How the user "wears" the cloth (Neural Prediction)
1. **Input**: KORRA sends the 10 SMPL shape coefficients (the DNA of the body) to the simulation engine.
2. **Process**: The engine (TailorNet) has been trained on thousands of garments. It automatically deforms a garment mesh to perfectly hug the user's specific shape.
3. **Output**: A high-fidelity 3D garment mesh is returned and layered over the body mesh in the User Dashboard.

---

## 🏗️ 1. UI/UX: Integrated Design Studio

The new features will be bridged directly to the existing **Attire Dropdown** and **Material Rail** already present on the Scan Result Screen.

### **A. View Pattern (2D Visualization)**
*   **The Switch**: A new tab in the Measurement Sheet (alongside "Measurements", "Sizes", "Shape", "Compare").
*   **Dynamic Drafting**: When the user switches to the **Pattern View**, the 2D geometry is generated based on:
    1.  **Current Attire**: Uses `window.ACTIVE_CONTEXT` (e.g., Agbada, Kaftan, Senator, Jacket, Jumpsuit) to select the correct mathematical pattern template.
    2.  **Current Material**: Uses `window.ACTIVE_MATERIAL` to adjust seam allowances and grain lines.
*   **Transition**: Uses the same smooth transition logic as the "Ask AI" chatbot. The UI hides controls and focuses entirely on the interactive SVG pattern canvas.

### **B. Download Pattern Workflow**
*   **Button**: A primary "Download Pattern" button added to the sheet footer.
*   **Format Selection UI**: Clicking the button triggers a luxury glass modal:
    -   **Option 1: DXF-AAMA** (For industrial CAD/Cutters like Optitex or CLO3D).
    -   **Option 2: PDF** (For local printing & manual cutting).
*   **Context-Aware**: The download includes the specific attire and fabric settings selected in the dropdowns.

### **C. Virtual Mirror (3D Integration)**
*   **Automatic Draping**: The 3D model instantly "wears" the attire selected in the dropdown.
*   **Fabric Intelligence**: The simulation engine (TailorNet/Taichi) uses the **Material Rail** selection to adjust the 3D drape:
    -   **Silk**: High drape, soft wrinkles, fluid movement.
    -   **Denim**: Low drape, stiff silhouette, heavy-duty creases.
    -   **Linen**: Natural wrinkles, moderate drape, breathable volume.
    -   **Wool**: Structured drape, thick folds, high retention.
    -   **Starch Bazin**: Stiff, voluminous folds (typical for West African luxury garments).
*   **Real-time Fitting**: The 3D Digital Twin updates its garment layer whenever the dropdown or rail is changed.

---

## 📦 2. Expanded Registry (New Additions)

### **A. Modern English Attires (New IDs)**
| ID | Name | Type | Gender | Key Feature |
| :--- | :--- | :--- | :--- | :--- |
| `bomber_jacket` | Bomber Jacket | Outerwear | Unisex | Ribbed cuffs & 12% ease buffer. |
| `blazer_business` | Business Blazer | Formal | Unisex | Structured shoulders & tailored waist. |
| `classic_jumpsuit` | Classic Jumpsuit | Full-Body | Female | Unified torso-to-crotch pattern. |
| `a_line_skirt` | A-Line Skirt | Lower | Female | High-waist flare & hip ease. |
| `trench_coat` | Trench Coat | Outerwear | Unisex | Double-breasted draft & overlay ease. |
| `pencil_skirt` | Pencil Skirt | Lower | Female | Negative ease for contouring. |

### **B. Fabric Intelligence Coefficients**
| Material | Stretch (K) | Stiffness (B) | Mass (M) | Visual Effect |
| :--- | :--- | :--- | :--- | :--- |
| **Woven** | 0.8 | 0.3 | 1.0 | Standard fabric, balanced drape. |
| **Knit** | 0.4 | 0.1 | 0.7 | Stretchy, soft wrinkles, body-con. |
| **Starch Bazin** | 0.95 | 0.9 | 1.2 | Stiff, voluminous folds. |
| **Technical** | 0.5 | 0.4 | 0.8 | Performance fabric, moderate drape. |
| **Silk** | 0.3 | 0.05 | 0.5 | High fluid motion, low opacity. |
| **Denim** | 0.9 | 0.7 | 1.3 | Rigid folds, high shadow contrast. |
| **Linen** | 0.7 | 0.6 | 0.9 | Sharp wrinkles, natural bounce. |
| **Wool** | 0.6 | 0.5 | 1.1 | Structured volume, soft edges. |

---

## 🚀 3. Implementation Plan (200 Phases)

### Track A: Infrastructure & Data Model (Phases 1–25)
**Foundation for the entire system — registry expansion, fabric model, measurement schema.**

| Phase | Deliverable | Files Changed | Description |
|-------|------------|--------------|-------------|
| 1 | 6 new attire entries in ATTIRE_REGISTRY | `dashboard.html` | Add bomber_jacket, blazer_business, classic_jumpsuit, a_line_skirt, trench_coat, pencil_skirt with mult/off/heat |
| 2 | Fabric model: data structure | `measurement-screen.js` | Expand materialCoeffs from 4 to 8 entries: add silk, denim, linen, wool with K/B/M properties |
| 3 | Fabric model: K (stretch) | `measurement-screen.js` | Add stretch field per material |
| 4 | Fabric model: B (stiffness) | `measurement-screen.js` | Add stiffness field per material |
| 5 | Fabric model: M (mass) | `measurement-screen.js` | Add mass field per material |
| 6 | Registry: patternType field | `dashboard.html` | Add patternType string to each attire (e.g., 'shirt', 'jacket', 'skirt') |
| 7 | Registry: patternSections field | `dashboard.html` | Add patternSections[] array listing required pattern pieces per attire |
| 8 | Registry: seamAllowance defaults | `dashboard.html` | Add seamAllowance float (cm) per attire |
| 9 | Registry: grainOverride field | `dashboard.html` | Add grainOverride string per attire |
| 10 | KORRA_MS: patternViewMode state | `measurement-screen.js` | Add patternViewMode: '2d' to state machine |
| 11 | KORRA_MS: activePattern state | `measurement-screen.js` | Add activePattern: null |
| 12 | KORRA_MS: simulationActive state | `measurement-screen.js` | Add simulationActive: false |
| 13 | KORRA_MS: downloadFormat state | `measurement-screen.js` | Add downloadFormat: 'dxf' |
| 14 | ACTIVE_FABRIC global | `dashboard.html` | Add window.ACTIVE_FABRIC = null |
| 15 | getPatternMeasurements() accessor | `measurement-screen.js` | Map measurement keys to pattern dimensions |
| 16 | Pattern dimension keys (backend) | `extract_measurements.py` | Add Across Shoulder, Neck to Waist, Waist to Hip to MALE_KEYS/FEMALE_KEYS |
| 17 | Pattern dimension calibration | `measurement_calibration.py` | Add alpha/beta for new pattern keys |
| 18 | Pattern dimension extraction | `extract_measurements.py` | Compute pattern-specific lengths from T-pose joints |
| 19 | Pattern dimensions in DB | `dashboard.html` | Include new keys in output measurements dict |
| 20 | FABRIC_PRESETS constant | `measurement-screen.js` | Define 8-fabric object with K/B/M values |
| 21 | PATTERN_TEMPLATES constant | `measurement-screen.js` | Map patternType to SVG drafting templates |
| 22 | SEAM_ALLOWANCE_DEFAULTS | `measurement-screen.js` | Default seam allowance per garment category |
| 23 | PATTERN_PIECE_CATALOG | `measurement-screen.js` | Map each section to its geometric formula |
| 24 | ANSUR mapping extended | `imputation_service.py` | Add pattern dimension fields to ANSUR regression |
| 25 | Registry validation test | `test/` | Validate all attire entries have required pattern fields |

### Track B: UI/UX — Design Studio (Phases 26–50)
**Tabs, Pattern view, Material rail, luxury glass modal, download UI.**

| Phase | Deliverable | Files Changed | Description |
|-------|------------|--------------|-------------|
| 26 | "Pattern" tab button | `measurement-screen.js` | Insert tab button after Compare |
| 27 | pattern case in switchView | `measurement-screen.js` | Add case 'pattern' to buildSheetContent() |
| 28 | Pattern tab CSS | `measurement-screen.css` | Style pattern tab with active mint border |
| 29 | buildPatternView() method | `measurement-screen.js` | Pattern view container with canvas |
| 30 | Pattern view CSS | `measurement-screen.css` | Pattern view layout styles |
| 31 | Hide controls on pattern enter | `measurement-screen.js` | Hide tabs/attire/material in pattern mode |
| 32 | Show controls on pattern exit | `measurement-screen.js` | Restore controls when leaving pattern |
| 33 | Pattern view transition | `measurement-screen.js` | Fade transition for pattern canvas |
| 34 | 2D SVG renderer init | `measurement-screen.js` | renderPattern() generates SVG with viewBox |
| 35 | Zoom/pan controls | `measurement-screen.js` | Mousewheel zoom, click-drag pan |
| 36 | Pattern canvas resize handler | `measurement-screen.js` | ResizeObserver re-scales pattern SVG |
| 37 | Material rail 8-button expansion | `measurement-screen.js` | Add silk, denim, linen, wool buttons |
| 38 | Material rail CSS for 8 buttons | `measurement-screen.css` | Adjust grid/wrap for 8 buttons |
| 39 | Material rail scroll on overflow | `measurement-screen.css` | overflow-x: auto with touch scroll |
| 40 | Material rail active state | `measurement-screen.js` | Active border per selected material |
| 41 | Material rail fabric preview | `measurement-screen.js` | Fabric color indicators per button |
| 42 | Download pattern button | `measurement-screen.js` | Add to sheet footer |
| 43 | openPatternDownloadModal() | `measurement-screen.js` | Modal trigger that populates fields |
| 44 | Download modal HTML | `dashboard.html` | Luxury glass #downloadPatternModal |
| 45 | Modal left-side graphic | `dashboard.html` | Pattern silhouette SVG/PNG |
| 46 | Modal right-side form | `dashboard.html` | Format picker, attire, material, seam allowance |
| 47 | Format toggle (DXF/PDF) | `dashboard.html` | Pill buttons for format selection |
| 48 | Modal action buttons | `dashboard.html` | Generate + Cancel |
| 49 | Modal CSS glass styling | `measurement-screen.css` | .ss-format-picker, .ss-format-pill |
| 50 | Modal mobile responsive | `measurement-screen.css` | Stack at <=900px, fullscreen at <=600px |

### Track C: Pattern Generation Engine (Phases 51–85)
**2D SVG pattern drafting from measurements — the core algorithmic work.**

| Phase | Deliverable | Files Changed | Description |
|-------|------------|--------------|-------------|
| 51 | PatternDraft coordinate system | `measurement-screen.js` | Class with origin, scale, cm→SVG converter |
| 52 | drawRect() SVG primitive | `measurement-screen.js` | Path generator for rounded rectangle |
| 53 | drawCurve() SVG primitive | `measurement-screen.js` | Bezier curve from control points |
| 54 | drawArc() SVG primitive | `measurement-screen.js` | Arc path from center, radius, angles |
| 55 | drawDart() SVG primitive | `measurement-screen.js` | Dart notch path (triangle fold indicator) |
| 56 | drawGrainline() SVG primitive | `measurement-screen.js` | Arrow path for grain direction |
| 57 | drawSeamAllowance() | `measurement-screen.js` | Offset path by seamAllowance cm |
| 58 | drawNotch() SVG primitive | `measurement-screen.js` | Triangle notch at seam intersection |
| 59 | drawLabel() SVG primitive | `measurement-screen.js` | Text label with piece name, cut count |
| 60 | ShirtFront template | `measurement-screen.js` | Draft from chest/waist/shoulder measurements |
| 61 | ShirtBack template | `measurement-screen.js` | Back bodice (different ease) |
| 62 | ShirtSleeve template | `measurement-screen.js` | Draft from bicep/elbow/sleeve-length |
| 63 | ShirtCollar template | `measurement-screen.js` | Collar band + fall from neck circumference |
| 64 | JacketFront template | `measurement-screen.js` | Front with lapel notch, chest dart |
| 65 | JacketBack template | `measurement-screen.js` | Back with center seam allowance |
| 66 | JacketSleeve template | `measurement-screen.js` | Two-piece sleeve cap |
| 67 | SkirtFront template | `measurement-screen.js` | A-line flare formula from waist/hip |
| 68 | SkirtBack template | `measurement-screen.js` | Back with waist dart |
| 69 | PantsFront template | `measurement-screen.js` | From waist/hip/inseam/crotch-depth |
| 70 | PantsBack template | `measurement-screen.js` | Back with larger crotch curve |
| 71 | DressFront template | `measurement-screen.js` | From bust/waist/hip/full-length |
| 72 | DressBack template | `measurement-screen.js` | Back with zipper allowance |
| 73 | FullBody template | `measurement-screen.js` | Jumpsuit from shoulder-to-crotch + crotch-to-ankle |
| 74 | patternType→template mapping | `measurement-screen.js` | _selectTemplate(type) returns template function |
| 75 | section→template mapping | `measurement-screen.js` | patternSections[] maps to template pieces |
| 76 | measurement→template params | `measurement-screen.js` | _mapMeasurementsToParams() translates keys |
| 77 | Template invocation | `measurement-screen.js` | _generatePattern() calls each template |
| 78 | Combine sections into SVG | `measurement-screen.js` | _renderPatternSVG() layers sections |
| 79 | Section labels + cut counts | `measurement-screen.js` | _annotateSVG() adds labels |
| 80 | Seam allowance application | `measurement-screen.js` | _applySeamAllowance() offsets paths |
| 81 | Grainlines | `measurement-screen.js` | _addGrainlines() per section |
| 82 | Notches | `measurement-screen.js` | _addNotches() at key intersections |
| 83 | Fabric-specific adjustments | `measurement-screen.js` | _applyFabricAdjustments() modifies ease from K/B/M |
| 84 | Render to canvas (live) | `measurement-screen.js` | Full pipeline → #ms-pattern-canvas |
| 85 | Re-render on context/material change | `measurement-screen.js` | Hook setContext() and setMaterial() to renderPattern() |

### Track D: DXF Export (Phases 86–100)
**Industrial CAD format generation for professional pattern cutting.**

| Phase | Deliverable | Files Changed | Description |
|-------|------------|--------------|-------------|
| 86 | DXF header section | `measurement-screen.js` | $ACADVER, $INSUNITS (cm) |
| 87 | DXF ENTITIES section | `measurement-screen.js` | Opens ENTITIES section |
| 88 | DXF LINE entity | `measurement-screen.js` | LINE with LAYER assignment |
| 89 | DXF LWPOLYLINE entity | `measurement-screen.js` | Polyline for curved sections |
| 90 | DXF ARC entity | `measurement-screen.js` | Arc for curved seam allowances |
| 91 | DXF CIRCLE entity | `measurement-screen.js` | Circle for button/notch markers |
| 92 | DXF TEXT entity | `measurement-screen.js` | Text for labels |
| 93 | DXF INSERT entity | `measurement-screen.js` | Block ref for reusable darts/notches |
| 94 | DXF layers definition | `measurement-screen.js` | CUTTING, SEAM_ALLOWANCE, GRAINLINE, NOTCH, LABEL |
| 95 | Layer assignment per entity | `measurement-screen.js` | Each entity gets correct layer |
| 96 | exportDXF() method | `measurement-screen.js` | Assembles full DXF string |
| 97 | DXF file download | `measurement-screen.js` | Blob + anchor click |
| 98 | cm→DXF mm conversion | `measurement-screen.js` | Measurements × 10 for DXF mm |
| 99 | Tolerance cleanup | `measurement-screen.js` | Round to 3dp, merge colinear |
| 100 | DXF metadata + version | `measurement-screen.js` | Date, attire, fabric, measurements as DXF comments |

### Track E: TailorNet Cloth Simulation (Phases 101–125)
**Neural cloth draping using TailorNet on SMPL body parameters.**

| Phase | Deliverable | Files Changed | Description |
|-------|------------|--------------|-------------|
| 101 | TailorNet environment setup | `Dockerfile.tailornet` | PyTorch, CUDNN, TailorNet dependencies |
| 102 | SMPL→TailorNet parameter bridge | `api/services/tailornet/` | Convert KORRA 10-shape params to TailorNet input |
| 103 | Garment template loader | `api/services/tailornet/` | Load pre-trained TailorNet garment templates |
| 104 | TailorNet inference endpoint | `api/routes/measurements.py` | POST /api/v2/garment/drape |
| 105 | Garment mesh generation | `api/services/tailornet/` | Run TailorNet forward pass → deformed mesh |
| 106 | Garment OBJ export | `api/services/tailornet/` | Export deformed mesh as OBJ for Three.js |
| 107 | Garment collision with body | `api/services/tailornet/` | PyTorch3D mesh intersection → push garment outside body |
| 108 | Garment smoothing pass | `api/services/tailornet/` | Laplacian smoothing on garment mesh |
| 109 | Fabric parameters → TailorNet | `api/services/tailornet/` | Pass K/B/M to modify drape coefficients |
| 110 | Multi-garment stacking | `api/services/tailornet/` | Layer multiple garments (shirt + jacket) |
| 111 | Garment cache per shape | `api/services/tailornet/` | Store meshes to avoid re-inference |
| 112 | TailorNet training data prep | `scripts/prepare_tailornet_data.py` | Generate garment-body pairs for fine-tuning |
| 113 | Fine-tune TailorNet on KORRA shapes | `scripts/train_tailornet.py` | Adapt TailorNet to KORRA shape distribution |
| 114 | TailorNet → Three.js bridge | `korra_viz.js` | Load garment OBJ, align to body mesh |
| 115 | `loadGarment()` in korra_viz.js | `korra_viz.js` | Accept geometry data, create garment mesh |
| 116 | `removeGarment()` in korra_viz.js | `korra_viz.js` | Dispose garment geometry |
| 117 | Garment material from FABRIC_PRESETS | `korra_viz.js` | Color/shininess/opacity from fabric |
| 118 | Garment fabric opacity | `korra_viz.js` | Silk=0.6, Denim=0.95, Linen=0.85, Wool=0.9 |
| 119 | Garment fabric shininess | `korra_viz.js` | Silk=80, Denim=20, Linen=10, Wool=30 |
| 120 | Garment specular mapping | `korra_viz.js` | Per-fabric specular color |
| 121 | Garment toggle visibility | `korra_viz.js` | toggleGarment(visible) |
| 122 | Garment wireframe mode | `korra_viz.js` | Wireframe for garment too |
| 123 | Garment animate loop sync | `korra_viz.js` | Sync with body in render loop |
| 124 | Garment + body group | `korra_viz.js` | Three.Group containing both meshes |
| 125 | Garment scene cleanup | `korra_viz.js` | Remove on viewport reset |

### Track F: Virtual Mirror & Real-time Fitting (Phases 126–145)
**Connecting attire/material selection to the 3D garment.**

| Phase | Deliverable | Files Changed | Description |
|-------|------------|--------------|-------------|
| 126 | setContext() triggers loadGarment | `measurement-screen.js` | Generate garment mesh on attire change |
| 127 | setMaterial() updates fabric | `measurement-screen.js` | Update garment material on fabric change |
| 128 | _updateGarmentForContext() | `measurement-screen.js` | Calls TailorNet API, loads into viewer |
| 129 | _updateGarmentFabric() | `measurement-screen.js` | Updates material from FABRIC_PRESETS |
| 130 | Garment on avatar tab | `measurement-screen.js` | Show garment when activeContext != standard |
| 131 | Garment hidden on 'standard' | `measurement-screen.js` | Remove garment when standard selected |
| 132 | Body visible through sheer fabrics | `korra_viz.js` | Silk depthWrite=false for see-through |
| 133 | Easing toggle updates garment | `measurement-screen.js` | toggleEase() re-generates with updated ease |
| 134 | Heatmap on garment | `measurement-screen.js` | Apply heatmap coloring to garment mesh |
| 135 | Auto-load garment on scan open | `measurement-screen.js` | Restore last context + material |
| 136 | Simulate on orbit end | `korra_viz.js` | Restart TailorNet after camera orbit |
| 137 | Simulate on attire change | `measurement-screen.js` | Re-drape when attire changes |
| 138 | Simulate on material change | `measurement-screen.js` | Adjust existing draping parameters |
| 139 | Garment loading spinner | `measurement-screen.js` | Show spinner during TailorNet inference |
| 140 | Garment error fallback | `measurement-screen.js` | Hide garment on inference failure |
| 141 | Garment toggle button | `measurement-screen.js` | Show/hide garment with keyboard shortcut |
| 142 | Garment opacity slider | `measurement-screen.js` | User-adjustable garment opacity |
| 143 | Multi-angle export with garment | `korra_export.js` | Captures include garment |
| 144 | Share link includes garment | `measurement-screen.js` | Garment state in share data |
| 145 | Garment visible on share page | `share.html` | Apply context + material to garment |

### Track G: Fabric Physics & Simulation (Phases 146–160)
**On-device fabric physics using simplified spring-mass system.**

| Phase | Deliverable | Files Changed | Description |
|-------|------------|--------------|-------------|
| 146 | Spring-mass model class | `korra_viz.js` | FabricSimulation class |
| 147 | Particle system init | `korra_viz.js` | _initParticles(vertices, mass, stiffness) |
| 148 | Structural springs | `korra_viz.js` | Adjacent vertex connections |
| 149 | Shear springs | `korra_viz.js` | Diagonal springs for shear resistance |
| 150 | Bend springs | `korra_viz.js` | Second-order neighbor springs |
| 151 | Gravity step | `korra_viz.js` | _applyGravity(dt) |
| 152 | Spring forces | `korra_viz.js` | Hooke's law: -k(dist - rest) |
| 153 | Damping | `korra_viz.js` | Velocity damping |
| 154 | Body collision | `korra_viz.js` | Push garment outside body bounds |
| 155 | Verlet integration | `korra_viz.js` | Stable position update |
| 156 | Fixed vertices (shoulder) | `korra_viz.js` | Pinned at shoulder/neck |
| 157 | Animate loop integration | `korra_viz.js` | Step simulation each frame |
| 158 | Fabric K→spring stiffness | `korra_viz.js` | Map from FABRIC_PRESETS |
| 159 | Fabric B→bend coefficient | `korra_viz.js` | Map bending resistance |
| 160 | Fabric M→particle mass | `korra_viz.js` | Map mass per particle |

### Track H: PDF Export, Polish & Share (Phases 161–175)
**Pattern PDF, export integration, share, production hardening.**

| Phase | Deliverable | Files Changed | Description |
|-------|------------|--------------|-------------|
| 161 | SVG→canvas rasterize | `measurement-screen.js` | Render SVG to offscreen canvas |
| 162 | Single-page PDF layout | `measurement-screen.js` | Fit sections on A4/letter |
| 163 | Multi-page PDF sections | `measurement-screen.js` | Flow sections across pages |
| 164 | Scale markers on PDF | `measurement-screen.js` | 10cm scale bar per page |
| 165 | Fold/cut lines on PDF | `measurement-screen.js` | Dashed fold, solid cut |
| 166 | exportPatternPDF() full method | `measurement-screen.js` | jspdf-based PDF generation |
| 167 | Measurement chart overlay on PDF | `measurement-screen.js` | Small table on page 1 |
| 168 | Fabric info block on PDF | `measurement-screen.js` | Type, yardage, grain info |
| 169 | exportPattern() unified | `measurement-screen.js` | Dispatches to DXF or PDF |
| 170 | Pattern in clinical PDF export | `korra_export.js` | Append pattern pages |
| 171 | Pattern in tailor brief | `korra_export.js` | Append to existing PDF |
| 172 | Garment in share state | `measurement-screen.js` | Context + material in share data |
| 173 | localStorage for attire/fabric | `dashboard.html` | Save last context + material |
| 174 | Restore garment on load | `measurement-screen.js` | Read localStorage, apply on open |
| 175 | Pattern download analytics | `scripts/evaluate_pipeline.py` | Track downloads by format, attire |

### Track I: Backend & Production (Phases 176–185)
**Server-side support, storage, testing, documentation.**

| Phase | Deliverable | Files Changed | Description |
|-------|------------|--------------|-------------|
| 176 | API: POST /api/v2/pattern/draft | `api/routes/measurements.py` | Accept measurements + attire + material |
| 177 | API: pattern validation | `api/routes/measurements.py` | Validate completeness for requested pattern |
| 178 | API: DXF generation endpoint | `api/services/` | Server-side DXF alternative |
| 179 | API: pattern template registry | `api/services/` | Server-side JSON of all templates |
| 180 | DB: garment_settings column | Supabase migration | Store context + material + format |
| 181 | DB: fabric_properties table | Supabase migration | K/B/M lookup per fabric |
| 182 | Train draping params from data | `scripts/` | Learn optimal springs from user interaction |
| 183 | Refine fabric coefficients | `scripts/` | K/B/M from user feedback |
| 184 | Performance: garment < 2000 verts | `korra_viz.js` | Mobile budget |
| 185 | Final docs + CLOTH_PATTERN_SIMULATION_PLAN.md | `/` | Update this file |

---

## Summary: 9 Tracks, 185 Phases

| Track | Phases | Theme |
|-------|--------|-------|
| A | 1–25 | Infrastructure & Data Model |
| B | 26–50 | UI/UX — Design Studio |
| C | 51–85 | Pattern Generation Engine (SVG) |
| D | 86–100 | DXF Export |
| E | 101–125 | TailorNet Cloth Simulation |
| F | 126–145 | Virtual Mirror & Real-time Fitting |
| G | 146–160 | Fabric Physics & Simulation |
| H | 161–175 | PDF Export, Polish & Share |
| I | 176–185 | Backend & Production |

## Status (as of 2026-07-04)
- **Track A (1–25)**: ✅ ~95% — Registry, FABRIC_PRESETS, ACTIVE_FABRIC, PATTERN_TEMPLATES, SEAM_ALLOWANCE_DEFAULTS, PATTERN_PIECE_CATALOG, getPatternMeasurements(), KORRA_MS state vars all done. Missing ANSUR mapping extension, registry validation test.
- **Track B (26–50)**: ✅ ~85% — Pattern tab, canvas, zoom/pan, controls hide/show all done. Download modal HTML+CSS+JS implemented (DXF/PDF format selection, SVG preview). openPatternDownloadModal() full implementation.
- **Track C (51–85)**: ✅ ~90% — SVG primitives (drawCurve, drawArc, drawDart, drawGrainline, drawSeamAllowance, drawNotch, drawLabel), 12 pattern templates (Shirt, Pant, Skirt, Jacket, Dress, Jumpsuit families), updated renderPattern() with templateMap dispatch.
- **Track D (86–100)**: ✅ ~60% — DXF export with bezier curve sampling (_sampleBezier, _dxfPathToSegments), piece layer naming, mm conversion. Missing piece alignment optimization.
- **Track E (101–125)**: [/] ~80% — Bridge, API endpoint, Three.js loader done. Multi-garment stacking implemented (garmentMeshes array, garment_map with multi-class entries). Missing female weights download.
- **Track F (126–145)**: ✅ ~70% — Core hooks wired, VTO loading spinner, opacity slider with range input, share integration (context+material in link params). Missing body visibility through sheer, multi-angle export.
- **Track G (146–160)**: ✅ ~20% — FabricSimulation class implemented (spring-mass, Verlet integration, gravity, damping, body collision, fixed vertices, K/B/M mapping). Missing animate loop integration into renderer.
- **Track H (161–175)**: ❌ Not started — PDF export, share, polish.
- **Track I (176–185)**: ❌ Not started — Backend, storage, testing.
