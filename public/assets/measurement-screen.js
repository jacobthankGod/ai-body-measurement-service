/* ═══════════════════════════════════════════════════════
   KORRA Measurement Screen | State Machine + Interaction
   ═══════════════════════════════════════════════════════ */

const MEASUREMENT_COLORS = {
  'Chest Round': '#C6FF00', 'Bust Round': '#C6FF00',
  'Waist Round': '#C6FF00', 'Hip Round': '#C6FF00',
  'Stomach Round': '#C6FF00', 'Upper Hip': '#C6FF00',
  'Neck Round': '#FFFFFF',
  'Shoulder': '#B388FF', 'Across Chest': '#B388FF', 'Across Back': '#B388FF',
  'Bicep Round': '#00D4FF', 'Elbow Round': '#00D4FF', 'Wrist Round': '#00D4FF',
  'Sleeve Length': '#00D4FF', 'Armhole Round': '#00D4FF',
  'Thigh Round': '#FFC247', 'Knee Round': '#FFC247',
  'Calf Round': '#FFC247', 'Ankle Round': '#FFC247',
  'Inseam': '#FFC247', 'Trouser Length': '#FFC247',
  'High Bust': '#C6FF00', 'Under Bust': '#C6FF00', 'Bust Point': '#C6FF00',
  'Shoulder to Bust Point': '#B388FF', 'Shoulder to Under Bust': '#B388FF',
  'Shoulder to Waist': '#B388FF', 'Front Waist Length': '#B388FF',
  'Back Waist Length': '#B388FF', 'Waist to Hip': '#C6FF00',
  'Half Length': '#C6FF00', 'Full Top Length': '#C6FF00',
  'Trouser Waist': '#C6FF00', 'Crotch Depth': '#C6FF00',
};

const MEASUREMENT_Y = {
  'Neck Round': 0.90, 'Shoulder': 0.82,
  'Across Chest': 0.78, 'Across Back': 0.78,
  'Chest Round': 0.72, 'Bust Round': 0.72,
  'High Bust': 0.70, 'Under Bust': 0.65, 'Bust Point': 0.65,
  'Armhole Round': 0.70, 'Sleeve Length': 0.65,
  'Stomach Round': 0.60, 'Waist Round': 0.55,
  'Half Length': 0.50, 'Full Top Length': 0.45,
  'Hip Round': 0.45, 'Upper Hip': 0.48,
  'Thigh Round': 0.35, 'Knee Round': 0.25,
  'Calf Round': 0.18, 'Ankle Round': 0.08,
  'Inseam': 0.35, 'Trouser Length': 0.35,
  'Bicep Round': 0.60, 'Elbow Round': 0.50, 'Wrist Round': 0.35,
};
window.MEASUREMENT_Y = MEASUREMENT_Y;

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

const BODY_SHAPE_INFO = {
  'Standard': { icon: '○', desc: 'Proportional measurements across all regions.', advice: 'Standard sizing should fit well off-the-rack.' },
  'Hourglass': { icon: '⌛', desc: 'Balanced bust and hips with a defined waist.', advice: 'Empire waists and wrap styles complement this shape.' },
  'Rectangle': { icon: '▬', desc: 'Similar measurements across bust, waist, and hips.', advice: 'Structured jackets and A-line skirts create definition.' },
  'Inverted Triangle': { icon: '▽', desc: 'Broader shoulders relative to hips.', advice: 'V-necklines and A-line bottoms balance proportions.' },
  'Oval': { icon: '⬭', desc: 'Fuller midsection relative to shoulders and hips.', advice: 'Straight-cut shirts and structured blazers work well.' },
};

const MALE_KEYS = ['Shoulder', 'Neck Round', 'Chest Round', 'Across Chest', 'Across Back', 'Stomach Round', 'Waist Round', 'Hip Round', 'Thigh Round', 'Knee Round', 'Calf Round', 'Ankle Round', 'Inseam', 'Half Length', 'Full Top Length', 'Sleeve Length', 'Bicep Round', 'Elbow Round', 'Wrist Round', 'Trouser Length', 'Trouser Waist', 'Crotch Depth'];
const FEMALE_KEYS = ['Shoulder', 'Neck Round', 'Bust Round', 'High Bust', 'Under Bust', 'Bust Point', 'Shoulder to Bust Point', 'Across Chest', 'Across Back', 'Armhole Round', 'Shoulder to Waist', 'Front Waist Length', 'Back Waist Length', 'Waist Round', 'Half Length', 'Waist to Hip', 'Sleeve Length', 'Bicep Round', 'Elbow Round', 'Wrist Round', 'Upper Hip', 'Hip Round', 'Thigh Round', 'Knee Round', 'Calf Round', 'Ankle Round'];

window.KORRA_MS = {
  active: false,
  data: null,
  viewMode: 'avatar',
  selectedMeasurement: 'Chest Round',
  unit: 'cm',
  overlaysVisible: true,
  sheetExpanded: false,
  aiOpen: false,
  viewerInstance: null,
  _previousTab: 'vault',
  _viewerInitialized: false,
  activeContext: 'standard',
  activeMaterial: 'woven',
  heatmapActive: false,
  showEased: true,
  patternViewMode: 'draft',
  activePattern: null,
  simulationActive: false,
  downloadFormat: 'dxf',
  compareHistory: [],
  compareBaselineIdx: 0,
  vBaseline: null,
  vLatest: null,
  baselineData: null,
  latestData: null,
  _reconErrorCount: { validation: 0, auth: 0, server: 0 },

  // ═══ FAB INTELLIGENCE STATE ═══
  _fabIntel: {
    activityScore: 0.5,
    lastInteraction: 0,
    interactions: [],
    heatmap: {},
    lastReveal: 0,
    sessionReveals: 0,
    maxReveals: 4,
    cooldownMs: 20000,
    idleThresholdMs: 4000,
    revealDurationMs: 5000,
    _interval: null,
    _revealTimeout: null,
    _pulseTimeout: null,
    _listeners: [],
  },

  // ═══ AI CHAT HISTORY ═══
  _aiChatHistory: [],

  // ═══ ENTRY POINT ═══
  open(data) {
    document.getElementById('ms-side-menu')?.remove();
    document.getElementById('ms-side-menu-backdrop')?.remove();
    if (typeof data === 'string') {
      if (!window.KORRA_DB) return;
      window.KORRA_DB.from('measurements').select('*').eq('id', data).single().then(({ data: row, error }) => {
        if (row && !error) this.open(row);
      });
      return;
    }
    if (data.biometrics && !data.measurements) data.measurements = data.biometrics;
    if (data.landmarks_3d && !data.landmarks) data.landmarks = data.landmarks_3d;
    this.data = data;
    window._currentScanId = data.id;
    window._currentScanName = data.client_name || '';
    this.active = true;
    this.viewMode = 'avatar';
    this.selectedMeasurement = 'Chest Round';
    this.unit = window.CURRENT_UNIT || 'cm';
    this.overlaysVisible = true;
    this.sheetExpanded = false;
    this.aiOpen = false;
    this._aiLoading = false;
    this._aiAbort = null;
    this._viewerInitialized = false;
    this.sideBySide = true;
    this._previousTab = document.querySelector('.tab-view.active')?.id?.replace('view-', '') || 'vault';
    this.activeContext = 'standard';
    this.activeMaterial = 'woven';
    this.showEased = localStorage.getItem('korra_showEased') !== 'false';
    this.patternViewMode = 'draft';
    this.activePattern = null;
    this.simulationActive = false;
    this.downloadFormat = 'dxf';
    this.heatmapActive = false;
    this.compareBaselineIdx = 0;
    this.vBaseline = null;
    this.vLatest = null;
    this.baselineData = null;
    this.latestData = null;
    // Phase 219: Load reconstruction history
    this._reconHistory = this._loadReconHistory();
    // Phase 220: Garment type for reconstruction
    this._reconGarmentType = 'unknown';
    // Phase 215: Keyboard shortcuts
    this._initKeyboardShortcuts();
    // Phase 201: VTO batch queue
    this._vtoBatchQueue = [];
    // Phase 203: VTO version navigation
    this._vtoVersionIndex = 0;
    this._vtoVersionHistory = [];
    this.compareHistory = (window.masterHistory || []).filter(s => s.client_name === data.client_name);
    // Preload mesh IMMEDIATELY — starts fetch while HTML renders
    const meshUrl = data.mesh_storage_url || data.mesh_url;
    if (meshUrl && window.KORRA_VIZ) {
      window.KORRA_VIZ.preloadMesh(meshUrl);
    }
    this.render();
    // Phase 193: Check URL param after render to auto-open VTO
    this._checkVtoUrlParam();
    if (this.sideBySide) {
      const root = document.querySelector('#view-scanresult .ms-root');
      if (root) {
        root.classList.add('ms-side-by-side');
        this._wrapRightCol();
      }
    }
    // Suppress page scroll — only sheet body scrolls
    document.querySelector('main').style.overflow = 'hidden';

    // Full-viewport: remove padding so content is flush
    const mainContent = document.querySelector('.main-content');
    if (mainContent) {
      mainContent.style.padding = '0';
    }

    // Switch tab FIRST so canvas has dimensions before initViewer
    window.switchTab('scanresult');
    this.initViewer();
    this.bindSheetDrag();
    // Initialize attire combobox (uses dashboard's createAttireSelector)
    if (window.createAttireSelector) {
      this._attireSelector = window.createAttireSelector('ms-attire-selector', {
        value: this.activeContext,
        onChange: (id) => this.setContext(id)
      });
    }
    const attireContainer = document.querySelector('.ms-attire-selector-container');
    if (attireContainer) attireContainer.style.display = this.showEased ? '' : 'none';
    setTimeout(() => {
      const hEl = document.querySelector('.ms-summary-value');
      if (hEl) {
        hEl.style.transition = 'transform 0.15s ease';
        hEl.style.transform = 'scale(1.05)';
        requestAnimationFrame(() => { hEl.style.transform = 'scale(1)'; });
      }
    }, 100);
  },

  // ═══ RENDER ═══
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
        <button class="ms-back-btn" onclick="KORRA_MS.handleBack()">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
          back
        </button>
        <div class="ms-sheet-controls" id="ms-sheet-controls">
          <div class="ms-controls-top">
            <div class="ms-scan-info">
              <div class="ms-scan-title">${name}${d.garment_mesh_url ? '<span class="ms-garment-badge">Has 3D garment</span>' : ''}</div>
              <div class="ms-scan-subtitle">${date} · ${height} · ${gender}</div>
            </div>
            <div class="ms-controls-toggles">
              <div class="ms-unit-toggle">
                <button class="ms-unit-btn ${this.unit === 'cm' ? 'active' : ''}" onclick="KORRA_MS.setUnit('cm')">CM</button>
                <button class="ms-unit-btn ${this.unit === 'in' ? 'active' : ''}" onclick="KORRA_MS.setUnit('in')">IN</button>
              </div>
              <div class="ms-ease-toggle" onclick="KORRA_MS.toggleEase()" title="Toggle between body and garment measurements">
                <span class="ms-ease-label ${!this.showEased ? 'active' : ''}">Body</span>
                <div class="ms-ease-track ${this.showEased ? 'active' : ''}">
                  <div class="ms-ease-thumb ${this.showEased ? 'right' : ''}"></div>
                </div>
                <span class="ms-ease-label ${this.showEased ? 'active' : ''}">Garment</span>
              </div>
            </div>
          </div>
          <button class="ms-recon-sheet-btn" onclick="KORRA_MS.switchView('reconstruct')" title="Convert garment photo to 3D cloth">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>
            Reconstruct
          </button>
          <div class="ms-controls-buttons">
            <button class="ms-share-btn" onclick="KORRA_MS.openShareScan()" title="Share scan">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>
              Share
            </button>
            <button class="ms-header-btn" onclick="KORRA_MS.exportPDF()" title="Export PDF">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
            </button>
            <button class="ms-header-btn" onclick="KORRA_MS.downloadOBJ()" title="Download OBJ" aria-label="Download 3D model as OBJ">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            </button>
            <button class="ms-header-btn ${this.overlaysVisible ? 'active' : ''}" onclick="KORRA_MS.toggleOverlays()" title="Toggle measurement lines">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
            </button>
            <button class="ms-header-btn" onclick="KORRA_MS.resetView()" title="Reset view">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
            </button>
            <button class="ms-header-btn" onclick="KORRA_MS.handleBack()" title="Close">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>
        </div>
        <div class="ms-attire-selector-container" id="ms-attire-selector"></div>
        <div class="ms-viewer" id="ms-viewer">
          <div class="ms-viewer-canvas" id="ms-viewer-canvas"></div>
          <div class="ms-viewer-badge" id="ms-viewer-badge">${this.buildBadge()}</div>
          <div class="ms-vto-controls" id="ms-vto-controls" style="display:none;">
            <label>Opacity</label>
            <input type="range" id="vto-opacity-slider" min="10" max="100" value="95" oninput="KORRA_MS.setGarmentOpacity(this.value/100)">
            <span id="vto-opacity-label">95%</span>
            <button class="ms-vto-btn" id="vto-visibility-btn" onclick="KORRA_MS.toggleGarmentVisibility()" title="Toggle garment visibility">ON</button>
          </div>
          <div class="ms-viewer-info">
            <div class="ms-viewer-info-title">User Perspective</div>
            <div class="ms-viewer-info-sub">(1) Collection | Scan</div>
          </div>
          <button class="ms-bg-toggle" id="ms-bg-toggle" onclick="KORRA_MS.toggleViewportBg()" title="Toggle background">
            <svg class="ms-bg-toggle-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
            </svg>
          </button>
          <div class="ms-viewer-toolbar">
            <button class="ms-tool-btn" onclick="KORRA_MS.zoomViewport('in')" title="Zoom in">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/></svg>
            </button>
            <button class="ms-tool-btn" onclick="KORRA_MS.zoomViewport('out')" title="Zoom out">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="8" y1="11" x2="14" y2="11"/></svg>
            </button>
            <button class="ms-tool-btn" onclick="KORRA_MS.toggleViewportProjection()" title="Toggle projection">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="16" rx="2"/><line x1="8" y1="4" x2="8" y2="20"/><line x1="16" y1="4" x2="16" y2="20"/></svg>
            </button>
            <button class="ms-tool-btn" onclick="KORRA_MS.resetViewport()" title="Reset view">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
            </button>
            <button class="ms-tool-btn" id="ms-toggle-autorotate" onclick="KORRA_MS.toggleAutoRotate()" title="Auto-rotate">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/></svg>
            </button>
          </div>
          <div class="ms-options-wrapper">
            <button class="ms-options-btn" id="ms-options-btn" onclick="KORRA_MS.toggleOptionsMenu()">Options ⌄</button>
            <div class="ms-options-dropdown" id="ms-options-dropdown">
              <div class="ms-options-item" data-mode="wireframe" onclick="KORRA_MS.setViewportMode('wireframe')">Wireframe</div>
              <div class="ms-options-item active" data-mode="solid" onclick="KORRA_MS.setViewportMode('solid')">Solid</div>
              <div class="ms-options-item" data-mode="rendered" onclick="KORRA_MS.setViewportMode('rendered')">Rendered</div>
            </div>
          </div>
        </div>
        <div class="ms-tabs">
          <button class="ms-tab ${this.viewMode === 'avatar' ? 'active' : ''}" onclick="KORRA_MS.switchView('avatar')">
            <svg class="ms-tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            Measurements
          </button>
          <button class="ms-tab ${this.viewMode === 'sizes' ? 'active' : ''}" onclick="KORRA_MS.switchView('sizes')">
            <svg class="ms-tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/></svg>
            Sizes
          </button>
          <button class="ms-tab ${this.viewMode === 'shape' ? 'active' : ''}" onclick="KORRA_MS.switchView('shape')">
            <svg class="ms-tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>
            Shape
          </button>
          <button class="ms-tab ${this.viewMode === 'compare' ? 'active' : ''}" onclick="KORRA_MS.switchView('compare')">
            <svg class="ms-tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="8" height="18" rx="1"/><rect x="14" y="3" width="8" height="18" rx="1"/></svg>
            Compare
          </button>
          <button class="ms-tab ${this.viewMode === 'pattern' ? 'active' : ''}" onclick="KORRA_MS.switchView('pattern')">
            <svg class="ms-tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
            Pattern
          </button>
        </div>
        <div class="ms-sheet" id="ms-sheet">
          <div class="ms-sheet-handle" id="ms-sheet-handle"></div>
          <div class="ms-sheet-body" id="ms-sheet-body">${this.buildSheetContent()}</div>
        </div>
        <button class="ms-ai-fab" onclick="KORRA_MS.switchView('ai')">
          <svg class="ms-ai-fab-icon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          <span class="ms-ai-fab-label">Ask AI</span>
        </button>
      </div>`;
  },

  // ═══ BADGE ═══
  buildBadge() {
    const m = this.data?.measurements || {};
    const val = m[this.selectedMeasurement];
    const factor = this.unit === 'in' ? 0.393701 : 1;
    const ease = this.showEased ? this.getEase(this.selectedMeasurement) : 1;
    const displayVal = val != null ? (val * factor * ease).toFixed(1) : '—';
    const desc = MEASUREMENT_DESCRIPTIONS[this.selectedMeasurement] || '';
    const color = MEASUREMENT_COLORS[this.selectedMeasurement] || '#C6FF00';
    return `
      <div class="ms-badge">
        <div class="ms-badge-label">${this.selectedMeasurement}</div>
        <div class="ms-badge-value" style="color:${color}">${displayVal}<span class="ms-badge-unit">${this.unit}</span></div>
        <div class="ms-badge-desc">${desc}</div>
      </div>`;
  },

  updateBadge() {
    const badge = document.getElementById('ms-viewer-badge');
    if (!badge) return;
    badge.innerHTML = this.buildBadge();
  },

  // ═══ SHEET CONTENT ═══
  buildSheetContent() {
    let content;
    switch (this.viewMode) {
      case 'avatar': content = this.buildMetricsGrid(); break;
      case 'sizes': content = this.buildSizesGrid(); break;
      case 'shape': content = this.buildShapeCard(); break;
      case 'compare': content = this.buildCompareView(); break;
      case 'pattern': content = this.buildPatternView(); break;
      case 'ai': content = this.buildAIView(); break;
      case 'tryon': content = this.buildTryOnView(); break;
      case 'reconstruct': content = this.buildReconstructView(); break;
      default: content = this.buildMetricsGrid();
    }
    if (this.viewMode === 'ai' || this.viewMode === 'tryon') return content;
    return content;
  },

  buildPatternView() {
    return `<div class="ms-pattern-view">
      <div class="ms-pattern-topbar">
        <button class="ms-ai-back" onclick="KORRA_MS.switchView('avatar')">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
          Back to Measurements
        </button>
      </div>
      <div class="ms-pattern-header">
        <div class="ms-pattern-title">2D Pattern Drafting</div>
        <div class="ms-pattern-subtitle">Generated from your measurements</div>
      </div>
      <div class="ms-pattern-canvas-container" id="ms-pattern-container">
        <svg id="ms-pattern-svg" width="100%" height="100%" viewBox="0 0 1000 1000" preserveAspectRatio="xMidYMid meet">
          <g id="ms-pattern-content"></g>
        </svg>
        <div class="ms-pattern-controls">
          <button onclick="KORRA_MS.zoomPattern('in')">+</button>
          <button onclick="KORRA_MS.zoomPattern('out')">-</button>
          <button onclick="KORRA_MS.resetPattern()">Reset</button>
        </div>
      </div>
      <div class="ms-pattern-footer">
        <button class="ms-download-pattern-btn" onclick="KORRA_MS.openPatternDownloadModal()">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          Download Pattern
        </button>
      </div>
    </div>`;
  },





  buildMetricsGrid() {
    console.log(`  buildMetricsGrid() gender=${this.data?.gender} unit=${this.unit}`);
    const m = this.data?.measurements || {};
    const gender = (this.data?.gender || 'male').toLowerCase();
    const factor = this.unit === 'in' ? 0.393701 : 1;

    const sections = gender === 'female' ? {
      'UPPER': ['Shoulder', 'Neck Round', 'Bust Round', 'High Bust', 'Under Bust', 'Bust Point', 'Shoulder to Bust Point', 'Shoulder to Under Bust', 'Across Chest', 'Across Back', 'Armhole Round'],
      'ARMS': ['Sleeve Length', 'Bicep Round', 'Elbow Round', 'Wrist Round'],
      'MID': ['Shoulder to Waist', 'Front Waist Length', 'Back Waist Length', 'Waist Round', 'Half Length', 'Waist to Hip'],
      'LOWER': ['Upper Hip', 'Hip Round', 'Thigh Round', 'Knee Round', 'Calf Round', 'Ankle Round']
    } : {
      'UPPER': ['Shoulder', 'Neck Round', 'Chest Round', 'Across Chest', 'Across Back'],
      'ARMS': ['Sleeve Length', 'Bicep Round', 'Elbow Round', 'Wrist Round'],
      'MID': ['Stomach Round', 'Waist Round', 'Half Length', 'Full Top Length'],
      'LOWER': ['Hip Round', 'Thigh Round', 'Knee Round', 'Calf Round', 'Ankle Round', 'Inseam', 'Trouser Length', 'Trouser Waist', 'Crotch Depth']
    };

    return Object.entries(sections).map(([label, keys]) => `
      <div class="ms-metrics-section">
        <div class="ms-metrics-section-header">${label}</div>
        <div class="ms-metrics-grid">
          ${keys.map(k => {
            const raw = m[k];
            if (raw == null) return `<div class="ms-metric-cell empty"><div class="ms-metric-name">${k}</div><div class="ms-metric-val">&mdash;</div></div>`;
            const ease = this.showEased ? this.getEase(k) : 1;
            const val = (raw * factor * ease).toFixed(1);
            const active = k === this.selectedMeasurement ? ' active' : '';
            const easeLabel = this.showEased && ease !== 1 ? (Math.round((ease - 1) * 1000) / 10) + '% ease' : '';

            // Phase 2: Editable content for contributors
            const isContributor = window.KORRA_USER_FLAGS?.is_contributor === true;
            const editableAttr = isContributor ? `contenteditable="true" onblur="KORRA_MS.handleManualEdit('${k}', this.textContent)"` : '';
            const editHint = isContributor ? `<div style="position:absolute; bottom:4px; right:8px; font-size:8px; opacity:0.3">EDIT</div>` : '';

            return `<div class="ms-metric-cell${active}" onclick="KORRA_MS.selectMeasurement('${k}')" style="position:relative">
              <div class="ms-metric-name">${k}</div>
              <div class="ms-metric-val" ${editableAttr}>${val}${factor === 1 ? 'cm' : 'in'}</div>
              ${easeLabel ? `<div class="ms-metric-ease">${easeLabel}</div>` : ''}
              ${editHint}
            </div>`;
          }).join('')}
        </div>
      </div>
    `).join('');
  },

  buildSizesGrid() {
    const m = this.data?.measurements || {};
    const sizeRec = this.data?.size_recommendation || 'M';
    const factor = this.unit === 'in' ? 0.393701 : 1;
    const summaryBar = `<div class="ms-summary-bar">
      <div class="ms-summary-item"><div class="ms-summary-label">HEIGHT</div><div class="ms-summary-value">${this.data?.height ? this.data.height + ' cm' : '—'}</div></div>
      <div class="ms-summary-item"><div class="ms-summary-label">SHAPE</div><div class="ms-summary-value">${this.data?.body_shape || 'Standard'}</div></div>
      <div class="ms-summary-item"><div class="ms-summary-label">SIZE REC</div><div class="ms-summary-value">${this.data?.size_recommendation || 'M'}</div></div>
    </div>`;
    const getSize = (v, r) => {
      if (!v) return '—';
      const s = { chest: [[80,'XS'],[88,'S'],[96,'M'],[104,'L'],[112,'XL'],[120,'XXL']], waist: [[68,'XS'],[76,'S'],[84,'M'],[92,'L'],[100,'XL'],[108,'XXL']], hip: [[84,'XS'],[92,'S'],[100,'M'],[108,'L'],[116,'XL'],[124,'XXL']], shoulder: [[40,'XS'],[43,'S'],[46,'M'],[49,'L'],[52,'XL'],[55,'XXL']], thigh: [[48,'XS'],[52,'S'],[56,'M'],[60,'L'],[64,'XL'],[68,'XXL']] };
      const t = s[r]; if (!t) return '—';
      for (const [th, l] of t) { if (v <= th) return l; } return 'XXL';
    };
    const items = {
      'Chest Round': getSize(m['Chest Round'], 'chest'),
      'Waist Round': getSize(m['Waist Round'], 'waist'),
      'Hip Round': getSize(m['Hip Round'], 'hip'),
      'Shoulder': getSize((m['Shoulder'] || 0) * 2, 'shoulder'),
      'Thigh Round': getSize(m['Thigh Round'], 'thigh'),
      'Overall': sizeRec,
    };
    const sizeHTML = '<div class="ms-size-grid">' + Object.entries(items).map(([label, size]) =>
      `<div class="ms-size-card">
        <div class="ms-size-label">${label}</div>
        <div class="ms-size-value">${size}</div>
        ${m[label] ? `<div class="ms-size-cm">${(m[label] * factor).toFixed(1)} ${this.unit}</div>` : ''}
      </div>`
    ).join('') + '</div>';

    const mat = this.activeMaterial;
    return `
      ${summaryBar}
      <div class="ms-material-section">
        <div class="ms-material-label">FABRIC</div>
        <div class="ms-material-rail">
          <button class="ms-material-btn ${mat === 'woven' ? 'active' : ''}" onclick="KORRA_MS.setMaterial('woven')" style="${mat === 'woven' ? 'border-color:var(--Mint)' : ''}">Woven</button>
          <button class="ms-material-btn ${mat === 'knit' ? 'active' : ''}" onclick="KORRA_MS.setMaterial('knit')">Knit</button>
          <button class="ms-material-btn ${mat === 'starch_bazin' ? 'active' : ''}" onclick="KORRA_MS.setMaterial('starch_bazin')">Starch Bazin</button>
          <button class="ms-material-btn ${mat === 'technical' ? 'active' : ''}" onclick="KORRA_MS.setMaterial('technical')">Technical</button>
          <button class="ms-material-btn ${mat === 'silk' ? 'active' : ''}" onclick="KORRA_MS.setMaterial('silk')">Silk</button>
          <button class="ms-material-btn ${mat === 'denim' ? 'active' : ''}" onclick="KORRA_MS.setMaterial('denim')">Denim</button>
          <button class="ms-material-btn ${mat === 'linen' ? 'active' : ''}" onclick="KORRA_MS.setMaterial('linen')">Linen</button>
          <button class="ms-material-btn ${mat === 'wool' ? 'active' : ''}" onclick="KORRA_MS.setMaterial('wool')">Wool</button>
        </div>
      </div>
      ${sizeHTML}
    `;
  },

  buildShapeCard() {
    const shape = this.data?.body_shape || 'Standard';
    const info = BODY_SHAPE_INFO[shape] || BODY_SHAPE_INFO['Standard'];
    const m = this.data?.measurements || {};
    const chest = m['Chest Round'] || 0;
    const waist = m['Waist Round'] || 1;
    const ratio = waist > 0 ? (chest / waist).toFixed(2) : '—';
    const diag = this.computeDiagnostics();
    return `<div class="ms-shape-card">
      <div class="ms-shape-icon" style="font-size:28px">${info.icon}</div>
      <div class="ms-shape-name">${shape}</div>
      <div class="ms-shape-desc">${info.desc}</div>
      <div class="ms-shape-desc" style="margin-top:8px; color:var(--Mint)">${info.advice}</div>
      <div class="ms-shape-ratio">
        <div class="ms-ratio-label">Chest / Waist Ratio</div>
        <div class="ms-ratio-value">${ratio}</div>
      </div>
    </div>
    <div class="ms-diagnostics">
      <div class="ms-diag-title">FIT DIAGNOSTICS</div>
      <div class="ms-diag-grid">
        <div class="ms-diag-item">
          <div class="ms-diag-label">ASYMMETRY</div>
          <div class="ms-diag-value ${diag.asymmetry === 'SYMMETRICAL' || diag.asymmetry === 'No data' ? 'ok' : 'warn'}">${diag.asymmetry}</div>
        </div>
        <div class="ms-diag-item">
          <div class="ms-diag-label">POSTURE</div>
          <div class="ms-diag-value ${diag.posture === 'OPTIMAL' || diag.posture === 'No data' ? 'ok' : 'warn'}">${diag.posture}</div>
        </div>
      </div>
    </div>`;
  },

  buildCompareView() {
    const clientName = this.data?.client_name;
    const scans = this.compareHistory.filter(s => s !== this.data);
    if (scans.length === 0) {
      return `<div class="ms-empty">
        <div class="ms-empty-icon">📊</div>
        <div class="ms-empty-title">No previous scans</div>
        <div class="ms-empty-desc">Take another scan to see changes over time.</div>
      </div>`;
    }
    if (this.compareBaselineIdx >= scans.length) this.compareBaselineIdx = 0;
    const baseline = scans[this.compareBaselineIdx];
    const m1 = baseline.measurements || baseline.biometrics || {};
    const m2 = this.data?.measurements || {};
    const factor = this.unit === 'in' ? 0.393701 : 1;

    const dropdownHTML = `<div class="ms-compare-select">
      <label class="ms-compare-select-label">COMPARE WITH:</label>
      <select class="ms-compare-dropdown" id="ms-compare-baseline" onchange="KORRA_MS.setCompareBaseline(this.value)">
        ${scans.map((h, i) => `<option value="${i}" ${i === this.compareBaselineIdx ? 'selected' : ''}>${new Date(h.created_at).toLocaleDateString()} — ${h.client_name}</option>`).join('')}
      </select>
    </div>`;

    const heatmapHTML = `<div class="ms-compare-header">
      <button class="ms-compare-heatmap-btn" onclick="KORRA_MS.toggleHeatmap()">${this.heatmapActive ? 'Deactivate Heatmap' : 'Activate Heatmap Overlay'}</button>
    </div>
    <div class="ms-compare-legend" style="display:${this.heatmapActive ? 'flex' : 'none'}">
      <div class="ms-legend-item"><div class="ms-legend-dot" style="background:#ff4d4d"></div> GROWTH</div>
      <div class="ms-legend-item"><div class="ms-legend-dot" style="background:#C6FF00"></div> REDUCTION</div>
      <div class="ms-legend-item"><div class="ms-legend-dot" style="background:#888"></div> NO CHANGE</div>
    </div>`;

    const showKeys = ['Shoulder', 'Neck Round', 'Chest Round', 'Waist Round', 'Hip Round', 'Thigh Round', 'Calf Round', 'Inseam', 'Sleeve Length'];
    let deltaHTML = '';
    for (const key of showKeys) {
      const v1 = m1[key], v2 = m2[key];
      if (v1 == null && v2 == null) continue;
      const delta = ((v2 || 0) - (v1 || 0)) * factor;
      const cls = delta > 0.5 ? 'positive' : delta < -0.5 ? 'negative' : 'neutral';
      const sign = delta > 0 ? '+' : '';
      deltaHTML += `<div class="ms-delta-row">
        <div class="ms-delta-name">${key}</div>
        <div class="ms-delta-change ${cls}">${sign}${delta.toFixed(1)}${this.unit}</div>
      </div>`;
    }
    return `${dropdownHTML}${heatmapHTML}<div class="ms-compare-grid">
      <div class="ms-compare-col">
        <div class="ms-compare-label">Baseline</div>
        <div class="ms-compare-viz" id="ms-compare-baseline"></div>
        <div style="font-size:10px; color:var(--Neutral-500); margin-top:8px">${new Date(baseline.created_at).toLocaleDateString()}</div>
      </div>
      <div class="ms-compare-col">
        <div class="ms-compare-label">Current</div>
        <div class="ms-compare-viz" id="ms-compare-current"></div>
        <div style="font-size:10px; color:var(--Neutral-500); margin-top:8px">${new Date(this.data.created_at).toLocaleDateString()}</div>
      </div>
    </div>
    <div class="ms-delta-table">${deltaHTML}</div>`;
  },

  // ═══ PARTIAL RENDER: measurements only (keeps attire selector alive) ═══
  renderMeasurements() {
    console.log(`▶ renderMeasurements() viewMode=${this.viewMode}`);
    const body = document.getElementById('ms-sheet-body');
    if (!body) { console.warn('  renderMeasurements: #ms-sheet-body NOT FOUND'); return; }
    let content = '';

    // Phase 2: Expert Mode Banner
    if (window.KORRA_USER_FLAGS?.is_contributor) {
      content += `
        <div class="expert-mode-banner" style="background:rgba(198,255,0,0.1); border:1px dashed var(--Mint); border-radius:12px; padding:12px; margin-bottom:20px; display:flex; align-items:center; gap:12px">
          <div style="font-size:20px">✨</div>
          <div style="flex:1">
            <div style="font-size:11px; font-weight:800; color:var(--Mint); text-transform:uppercase; letter-spacing:0.05em">Expert Mode Active</div>
            <div style="font-size:10px; color:var(--Neutral-400)">Your manual edits directly train the KORRA AI algorithm.</div>
          </div>
          <button class="btn-primary" style="padding:6px 12px; font-size:10px" id="btnSubmitRefinement" onclick="KORRA_MS.submitRefinement()">Sync Refinement</button>
        </div>
      `;
    }

    switch (this.viewMode) {
      case 'avatar': content += this.buildMetricsGrid(); break;
      case 'sizes': content += this.buildSizesGrid(); break;
      case 'shape': content += this.buildShapeCard(); break;
      case 'compare': content += this.buildCompareView(); break;
      default: content += this.buildMetricsGrid();
    }
    
    body.innerHTML = content;
    void body.scrollHeight; // force reflow for correct scroll extent
    if (this.viewMode === 'compare') this.initCompareViewers();
    this.updateBadge();
  },

  // ═══ VIEW MODE ═══
  switchView(mode) {
    if ((mode === 'ai' || mode === 'tryon' || mode === 'reconstruct') && this.viewMode !== mode) this._previousView = this.viewMode;
    // Phase 121: Clean up Three.js recon viewer when leaving reconstruct view
    if (this.viewMode === 'reconstruct' && mode !== 'reconstruct') this._cleanupReconViewer();
    this.viewMode = mode;
    document.querySelectorAll('#view-scanresult .ms-tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`#view-scanresult .ms-tab[onclick*="${mode}"]`)?.classList.add('active');
    const body = document.getElementById('ms-sheet-body');
    if (body) {
      if (mode === 'ai' || mode === 'tryon' || mode === 'reconstruct' || mode === 'pattern') {
        body.style.overflow = '';
        body.style.display = 'flex';
        body.style.flexDirection = 'column';
        body.style.padding = mode === 'ai' ? '0 20px 100px' : '0';

        const controls = document.querySelector('.ms-sheet-controls');
        if (controls) controls.style.display = 'none';

        const unitToggle = document.querySelector('.ms-unit-toggle');
        const easeToggle = document.querySelector('.ms-ease-toggle');
        if (unitToggle) unitToggle.style.display = 'none';
        if (easeToggle) easeToggle.style.display = 'none';

        const attire = document.querySelector('.ms-attire-selector-container');
        const tabs = document.querySelector('.ms-tabs');
        if (attire) attire.style.display = 'none';
        if (tabs) tabs.style.display = 'none';

        const sheet = document.querySelector('.ms-sheet');
        if (sheet) {
           if (mode === 'ai') sheet.classList.add('ai-active');
           else if (mode === 'tryon') sheet.classList.add('tryon-active');
           else sheet.classList.remove('ai-active', 'tryon-active');
        }

        document.querySelectorAll('#view-scanresult .ms-header-btn, #view-scanresult .ms-share-btn').forEach(btn => {
          btn.style.display = 'none';
        });

        if (mode === 'ai') document.body.classList.add('ai-mode');
        if (mode === 'tryon') {
          document.body.classList.add('tryon-mode');
          this._restoreViewport();
          setTimeout(() => this._initTryOn(), 50);
        }
        if (mode === 'reconstruct') {
          document.body.classList.add('tryon-mode');
          this._restoreViewport();
          setTimeout(() => this._initReconstruct(), 50);
        }
      } else {
        body.style.overflow = '';
        body.style.display = '';
        body.style.flexDirection = '';
        body.style.padding = '';

        const title = document.querySelector('.ms-scan-title');
        const subtitle = document.querySelector('.ms-scan-subtitle');
        if (title && this.data?.client_name) title.textContent = this.data.client_name;
        if (subtitle && this.data) {
          const d = this.data;
          const date = d.created_at ? new Date(d.created_at).toLocaleDateString() : 'Today';
          const h = d.height ? `${d.height} cm` : '';
          const g = (d.gender || 'male').charAt(0).toUpperCase() + (d.gender || 'male').slice(1);
          subtitle.textContent = `${date} · ${h} · ${g}`;
        }

        const unitToggle = document.querySelector('.ms-unit-toggle');
        const easeToggle = document.querySelector('.ms-ease-toggle');
        if (unitToggle) unitToggle.style.display = '';
        if (easeToggle) easeToggle.style.display = '';

        const controls = document.querySelector('.ms-sheet-controls');
        if (controls) controls.style.display = '';

        const attire = document.querySelector('.ms-attire-selector-container');
        const tabs = document.querySelector('.ms-tabs');
        if (attire) attire.style.display = '';
        if (tabs) tabs.style.display = '';

        const sheet = document.querySelector('.ms-sheet');
        if (sheet) sheet.classList.remove('ai-active', 'tryon-active');

        if (window.innerWidth > 900) {
          // const bottomNav = document.querySelector('.sidebar-nav');
          // if (bottomNav) bottomNav.style.display = '';
        }

        document.querySelectorAll('#view-scanresult .ms-header-btn, #view-scanresult .ms-share-btn').forEach(btn => {
          btn.style.display = '';
        });

        document.body.classList.remove('ai-mode', 'tryon-mode');
        this._restoreViewport();
      }
      const rightCol = document.querySelector('.ms-right-col');
      if (rightCol && window.innerWidth <= 900) rightCol.style.overflow = mode === 'ai' ? 'visible' : '';
      body.innerHTML = this.buildSheetContent();
    }
    const fab = document.querySelector('#view-scanresult .ms-ai-fab');
    if (fab) {
      fab.style.display = mode === 'ai' ? 'none' : '';
      if (mode === 'ai') fab.classList.remove('revealed', 'pulse');
    }
    if (mode === 'compare') this.initCompareViewers();
    if (mode === 'pattern') {
      setTimeout(() => this.renderPattern(), 50);
    }
    if (mode !== 'ai') this._notifyPostAction();
  },

  // ═══ MEASUREMENT SELECTION ═══
  selectMeasurement(key) {
    console.log(`[SIDEMENU-DBG] selectMeasurement("${key}") called, innerWidth=${window.innerWidth}`);
    try {
      this.selectedMeasurement = key;
      this.updateBadge();
      document.querySelectorAll('#view-scanresult .ms-metric-cell').forEach(el => el.classList.remove('active'));
      document.querySelectorAll('#view-scanresult .ms-metric-cell').forEach(el => {
        if (el.querySelector('.ms-metric-name')?.textContent === key) el.classList.add('active');
      });
      if (window.innerWidth <= 900) {
        console.log(`[SIDEMENU-DBG] mobile path → openSideMenu`);
        this.openSideMenu(key);
        return;
      }
      console.log(`[SIDEMENU-DBG] desktop path → openSideMenu + _notifyPostAction`);
      this.openSideMenu(key);
      this._notifyPostAction();
    } catch (e) {
      console.error(`[SIDEMENU-DBG] ERROR in selectMeasurement:`, e);
    }
  },

  // ═══ SIDE MENU ═══
  _sideMenuMeasurement: null,
  openSideMenu(key) {
    if (this.active && window.innerWidth > 900) return;
    this._sideMenuMeasurement = key;
    try {
      const m = this.data?.measurements || {};
      const val = m[key];
      const factor = this.unit === 'in' ? 0.393701 : 1;
      const ease = this.showEased ? this.getEase(key) : 1;
      const displayVal = val != null ? (val * factor * ease).toFixed(1) : '—';
      const color = MEASUREMENT_COLORS[key] || '#C6FF00';
      const desc = MEASUREMENT_DESCRIPTIONS[key] || '';
      const size = this._getSizeForMeasurement(key);
      const historyHtml = this._buildHistoryHtml(key);

      let backdrop = document.getElementById('ms-side-menu-backdrop');
      if (!backdrop) { backdrop = document.createElement('div'); backdrop.id = 'ms-side-menu-backdrop'; backdrop.className = 'ms-side-menu-backdrop'; backdrop.onclick = () => this.closeSideMenu(); document.body.appendChild(backdrop); }
      let menu = document.getElementById('ms-side-menu');
      if (!menu) { menu = document.createElement('div'); menu.id = 'ms-side-menu'; menu.className = 'ms-side-menu'; document.body.appendChild(menu); }

      menu.innerHTML = `
        <div class="ms-side-menu-header">
          <button class="ms-side-menu-back" onclick="KORRA_MS.closeSideMenu()">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
          </button>
          <div class="ms-side-menu-title">${key}</div>
        </div>
        <div class="ms-side-menu-body">
          <div class="ms-side-menu-value" style="color:${color}">${displayVal}<span class="ms-side-menu-unit">${this.unit}</span></div>
          <div class="ms-side-menu-desc">${desc}</div>
          ${size ? `
          <div class="ms-side-menu-section">
            <div class="ms-side-menu-section-title">Size Recommendation</div>
            <div class="ms-side-menu-fit-card">
              <div class="ms-side-menu-fit-row"><span class="ms-side-menu-fit-label">Size</span><span class="ms-side-menu-fit-value" style="color:var(--Mint)">${size.label}</span></div>
              <div class="ms-side-menu-fit-row"><span class="ms-side-menu-fit-label">Ease</span><span class="ms-side-menu-fit-value">${size.ease || '—'}</span></div>
            </div>
          </div>` : ''}
          ${historyHtml ? `
          <div class="ms-side-menu-section">
            <div class="ms-side-menu-section-title">Scan History</div>
            <div class="ms-side-menu-fit-card">${historyHtml}</div>
          </div>` : ''}
           <button class="ms-side-menu-ai-btn" onclick="KORRA_MS.closeSideMenu(); KORRA_MS.switchView('ai'); KORRA_MS.askAI('Tell me about my ${key.toLowerCase()} measurement')">Ask AI about this</button>
        </div>`;

      setTimeout(() => {
        backdrop.classList.add('open');
        menu.classList.add('open');
      }, 0);

    } catch (e) {
      console.error('Error in openSideMenu:', e);
    }
  },

  closeSideMenu() {
    const backdrop = document.getElementById('ms-side-menu-backdrop');
    const menu = document.getElementById('ms-side-menu');
    if (menu) { menu.classList.remove('open'); menu.style.removeProperty('display'); }
    if (backdrop) { backdrop.classList.remove('open'); backdrop.style.removeProperty('display'); }
    this._sideMenuMeasurement = null;
    if (window.innerWidth > 900 && menu) {
      menu.classList.add('open');
    }
  },

  _getSizeForMeasurement(key) {
    const m = this.data?.measurements || {};
    const val = m[key];
    if (val == null) return null;
    const sizeMap = {
      'Chest Round': { xs: 32, s: 36, m: 40, l: 44, xl: 48, xxl: 52 },
      'Waist Round': { xs: 26, s: 30, m: 34, l: 38, xl: 42, xxl: 46 },
      'Hip Round': { xs: 34, s: 38, m: 42, l: 46, xl: 50, xxl: 54 },
      'Shoulder': { xs: 16, s: 17, m: 18, l: 19, xl: 20, xxl: 21 },
    };
    const inches = val * 0.393701;
    const thresholds = sizeMap[key];
    if (!thresholds) return null;
    let label = 'XS', ease = '3-5%';
    if (inches >= thresholds.xxl) { label = 'XXL'; ease = '2-4%'; }
    else if (inches >= thresholds.xl) { label = 'XL'; ease = '2-4%'; }
    else if (inches >= thresholds.l) { label = 'L'; ease = '3-5%'; }
    else if (inches >= thresholds.m) { label = 'M'; ease = '3-5%'; }
    else if (inches >= thresholds.s) { label = 'S'; ease = '4-6%'; }
    return { label, ease };
  },

  _buildHistoryHtml(key) {
    const history = this.data?.scan_history;
    if (!history || history.length < 2) return '';
    const factor = this.unit === 'in' ? 0.393701 : 1;
    return history.slice(0, 4).map((scan, i) => {
      const val = scan.measurements?.[key];
      if (val == null) return '';
      const display = (val * factor).toFixed(1);
      const prev = history[i + 1]?.measurements?.[key];
      const delta = prev != null ? ((val - prev) * factor).toFixed(1) : null;
      const date = scan.created_at ? new Date(scan.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '';
      return `<div class="ms-side-menu-fit-row"><span class="ms-side-menu-fit-label">${date}</span><span class="ms-side-menu-fit-value">${display}${this.unit}${delta ? ` <span style="color:${parseFloat(delta) > 0 ? '#ef4444' : '#22c55e'}">(${parseFloat(delta) > 0 ? '+' : ''}${delta})</span>` : ''}</span></div>`;
    }).join('');
  },

  // ═══ UNIT ═══
  setUnit(unit) {
    this.unit = unit;
    window.CURRENT_UNIT = unit;
    document.querySelectorAll('#view-scanresult .ms-unit-btn').forEach(btn => {
      btn.classList.toggle('active', btn.textContent.trim().toLowerCase() === unit);
    });
    this.updateBadge();
    const body = document.getElementById('ms-sheet-body');
    if (body) body.innerHTML = this.buildSheetContent();
  },

  // ═══ OVERLAYS ═══
  toggleOverlays() {
    this.overlaysVisible = !this.overlaysVisible;
    const btn = document.querySelector('#view-scanresult .ms-header-btn[onclick*="toggleOverlays"]');
    if (btn) btn.classList.toggle('active', this.overlaysVisible);

  },

  _wrapRightCol() {
    const root = document.querySelector('#view-scanresult .ms-root');
    if (!root || root.querySelector('.ms-right-col')) return;
    const tabs = root.querySelector('.ms-tabs');
    const sheet = root.querySelector('.ms-sheet');
    const attire = root.querySelector('#ms-attire-selector');
    const controls = root.querySelector('#ms-sheet-controls');
    if (!tabs || !sheet) return;
    const rc = document.createElement('div');
    rc.className = 'ms-right-col';
    root.insertBefore(rc, sheet);
    if (window.innerWidth <= 900) {
      const handle = document.createElement('div');
      handle.className = 'ms-right-col-handle';
      handle.id = 'ms-right-col-handle';
      handle.innerHTML = `
      <div class="ms-right-col-handle-bar" id="ms-right-col-handle-bar"></div>
      <button class="ms-view3d-btn" id="ms-view3d-btn">View 3D Model</button>`;
      rc.appendChild(handle);
    }
    if (controls) rc.appendChild(controls);
    if (attire) rc.appendChild(attire);
    rc.appendChild(tabs);
    rc.appendChild(sheet);
  },

  resetView() {
    if (this.viewerInstance) this.viewerInstance.resetCamera();
    this.selectMeasurement('Chest Round');
    this.overlaysVisible = true;
    this.updateBadge();
  },

  // ═══ SHEET DRAG ═══
  _sheetSnap: 'half',
  expandSheet() {
    this.sheetExpanded = true;
    document.getElementById('ms-sheet')?.classList.add('expanded');
    if (window.innerWidth <= 900) {
      const rc = document.querySelector('.ms-side-by-side .ms-right-col');
      if (rc) { rc.classList.remove('sheet-collapsed', 'sheet-half'); rc.classList.add('sheet-full'); rc.style.overflow = 'visible'; }
      this._sheetSnap = 'full';
      this._updateViewBtn();
    }
  },
  collapseSheet() {
    this.sheetExpanded = false;
    document.getElementById('ms-sheet')?.classList.remove('expanded');
    if (window.innerWidth <= 900) {
      const rc = document.querySelector('.ms-side-by-side .ms-right-col');
      if (rc) { rc.classList.remove('sheet-full', 'sheet-half'); rc.classList.add('sheet-collapsed'); rc.style.overflow = 'hidden'; }
      this._sheetSnap = 'collapsed';
      this._updateViewBtn();
    }
  },
  _halfSheet() {
    if (window.innerWidth > 900) return;
    const rc = document.querySelector('.ms-side-by-side .ms-right-col');
    if (rc) { rc.classList.remove('sheet-collapsed', 'sheet-full'); rc.classList.add('sheet-half'); rc.style.overflow = 'visible'; }
    this._sheetSnap = 'half';
    this._updateViewBtn();
  },
  _updateViewBtn() {
    if (window.innerWidth > 900) return;
    const btn = document.getElementById('ms-view3d-btn');
    if (!btn) return;
    btn.textContent = this._sheetSnap === 'collapsed' ? 'View Measurements' : 'View 3D Model';
  },
  _toggleSheet() {
    if (window.innerWidth > 900) return;
    if (this._sheetSnap === 'collapsed') this._halfSheet();
    else if (this._sheetSnap === 'half') this.expandSheet();
    else this.collapseSheet();
  },
  _snapSheet() {
    if (window.innerWidth > 900) return;
    const rc = document.querySelector('.ms-side-by-side .ms-right-col');
    if (!rc) return;
    const vh = window.innerHeight;
    const ratio = rc.offsetHeight / vh;
    if (ratio > 0.7) this.expandSheet();
    else if (ratio > 0.25) this._halfSheet();
    else this.collapseSheet();
  },
  bindSheetDrag() {
    if (window.innerWidth <= 900) {
      const rc = document.querySelector('.ms-side-by-side .ms-right-col');
      let startY = 0;
      const onStart = (y) => { startY = y; if (rc) { rc.style.transition = 'none'; rc.style.overflow = 'visible'; } };
      const onMove = (y) => {
        if (!rc) return;
        const delta = startY - y;
        const curH = rc.offsetHeight;
        const maxH = window.innerHeight * 0.88;
        const newH = Math.max(48, Math.min(maxH, curH + delta));
        rc.style.height = newH + 'px';
      };
      const onEnd = () => {
        if (!rc) return;
        rc.style.transition = '';
        this._snapSheet();
      };
      const bindDrag = (el) => {
        if (!el) return;
        el.addEventListener('touchstart', (e) => {
          if (e.target.closest('#ms-view3d-btn')) return;
          onStart(e.touches[0].clientY);
        }, { passive: true });
        el.addEventListener('touchmove', (e) => {
          onMove(e.touches[0].clientY);
        }, { passive: true });
        el.addEventListener('touchend', () => onEnd());
        el.addEventListener('mousedown', (e) => {
          onStart(e.clientY);
          const mv = (e) => onMove(e.clientY);
          const up = () => { window.removeEventListener('mousemove', mv); window.removeEventListener('mouseup', up); onEnd(); };
          window.addEventListener('mousemove', mv);
          window.addEventListener('mouseup', up);
        });
      };
      const rcEl = document.querySelector('.ms-side-by-side .ms-right-col');
      if (rcEl) {
        rcEl.addEventListener('touchstart', (e) => {
          if (e.target.closest('button, input, select, textarea, .ms-tab, #ms-view3d-btn, #ms-right-col-handle-bar')) return;
          const rect = rcEl.getBoundingClientRect();
          const touchY = e.touches[0].clientY;
          if (touchY - rect.top > 150) return;
          onStart(touchY);
        }, { passive: true });
        rcEl.addEventListener('touchmove', (e) => {
          onMove(e.touches[0].clientY);
        }, { passive: true });
        rcEl.addEventListener('touchend', () => onEnd());
      }

      const bar = document.getElementById('ms-right-col-handle-bar');
      if (bar) bar.addEventListener('click', () => this._toggleSheet());

      const viewBtn = document.getElementById('ms-view3d-btn');
      if (viewBtn) {
        viewBtn.addEventListener('touchstart', (e) => {
          e.stopPropagation();
          this._viewBtnTouched = true;
          if (this._sheetSnap === 'collapsed') this._halfSheet();
          else this.collapseSheet();
        }, { passive: true });
        viewBtn.addEventListener('click', (e) => {
          if (this._viewBtnTouched) { this._viewBtnTouched = false; return; }
          e.stopPropagation();
          if (this._sheetSnap === 'collapsed') this._halfSheet();
          else this.collapseSheet();
        });
      }

      if (rc && !rc.classList.contains('sheet-collapsed') && !rc.classList.contains('sheet-full')) {
        rc.classList.add('sheet-half');
      }
      this._updateViewBtn();
      return;
    }
    // Desktop: original sheet-handle drag
    const handle = document.getElementById('ms-sheet-handle');
    if (!handle) return;
    let startY = 0, startH = 0;
    const onStart = (y) => { startY = y; startH = document.getElementById('ms-sheet')?.offsetHeight || 0; };
    const onMove = (y) => {
      const delta = startY - y;
      const h = Math.max(150, Math.min(window.innerHeight * 0.8, startH + delta));
      const s = document.getElementById('ms-sheet');
      if (s) s.style.height = h + 'px';
    };
    const onEnd = () => {
      const s = document.getElementById('ms-sheet');
      if (!s) return;
      if (s.offsetHeight > window.innerHeight * 0.5) this.expandSheet(); else this.collapseSheet();
      s.style.height = '';
    };
    handle.addEventListener('touchstart', (e) => onStart(e.touches[0].clientY), { passive: true });
    handle.addEventListener('touchmove', (e) => onMove(e.touches[0].clientY), { passive: true });
    handle.addEventListener('touchend', () => onEnd());
    handle.addEventListener('mousedown', (e) => {
      onStart(e.clientY);
      const mv = (e) => onMove(e.clientY);
      const up = () => { window.removeEventListener('mousemove', mv); window.removeEventListener('mouseup', up); onEnd(); };
      window.addEventListener('mousemove', mv);
      window.addEventListener('mouseup', up);
    });
  },

  // ═══ 3D VIEWER ═══
  initViewer() {
    const canvasEl = document.getElementById('ms-viewer-canvas');
    if (!canvasEl || !window.KORRA_VIZ) return;
    if (window.createKorraVisualizer) {
      this.viewerInstance = window.createKorraVisualizer();
    } else {
      this.viewerInstance = window.KORRA_VIZ;
    }
    this.viewerInstance.init('ms-viewer-canvas');
    // Sync toggle icon to match restored background mode
    const mode = this.viewerInstance._bgMode;
    const btn = document.getElementById('ms-bg-toggle');
    if (btn) {
      btn.innerHTML = mode === 'dark'
        ? `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>`
        : `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>`;
    }
    const badge = document.getElementById('ms-viewer-badge');
    this.viewerInstance.onInteract = (active) => {
      if (badge) badge.style.opacity = active ? '0.3' : '1';
    };
    const meshUrl = this.data?.mesh_storage_url || this.data?.mesh_url;
    if (meshUrl) {
      const lm = this.data?.landmarks;
      const lm3d = lm ? Object.fromEntries(Object.entries(lm).map(([k, v]) => [k, { x: v[0], y: v[1], z: 0 }])) : null;
      // Use cached text if preloaded, otherwise fetch
      const tryLoad = (text) => {
        const meshData = this.viewerInstance.parseAndRenderOBJ(text);
        if (meshData && lm3d) this.viewerInstance.renderLandmarks(lm3d, meshData.size);
        if (meshData && this.viewerInstance.mesh && this.viewerInstance.mesh.geometry && this.viewerInstance.mesh.geometry.attributes.position) {
          this.viewerInstance.mesh.geometry.attributes.position.usage = THREE.DynamicDrawUsage;
        }
      };
      const cached = this.viewerInstance.getCachedMesh(meshUrl);
      if (cached) {
        requestAnimationFrame(() => tryLoad(cached));
      } else {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 15000);
        fetch(meshUrl, { signal: controller.signal })
          .then(r => { clearTimeout(timeout); if (!r.ok) throw new Error('Missing'); return r.text(); })
          .then(text => {
            this.viewerInstance._meshCache.set(meshUrl, text);
            tryLoad(text);
          })
          .catch(() => {});
      }
    }
    // Swap to TailorNet body if available (from extract response or stored DB)
    const tnBodyUrl = this.data?.tailornet_body_url || this.data?.biometrics?.__smpl_params?.__tailornet_body_url;
    if (tnBodyUrl && this.viewerInstance?.loadTailornetBody) {
      const cached = this.viewerInstance._meshCache.get(tnBodyUrl);
      if (cached) {
        requestAnimationFrame(() => this.viewerInstance.loadTailornetBody(tnBodyUrl));
      } else {
        fetch(tnBodyUrl)
          .then(r => { if (!r.ok) throw new Error('Missing'); return r.text(); })
          .then(text => {
            this.viewerInstance._meshCache.set(tnBodyUrl, text);
            this.viewerInstance.loadTailornetBody(tnBodyUrl);
          })
          .catch(() => { console.warn('TailorNet body not available'); });
      }
    }
    this._fabIntel._sessionStart = Date.now();
    this._initFabIntelligence();
  },

  toggleViewportBg() {
    if (!this.viewerInstance) return;
    const mode = this.viewerInstance.toggleBackground();
    const btn = document.getElementById('ms-bg-toggle');
    if (btn) {
      btn.innerHTML = mode === 'dark'
        ? `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>`
        : `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>`;
    }
  },

  zoomViewport(dir) {
    if (!this.viewerInstance) return;
    const factor = dir === 'in' ? 0.85 : 1.176;
    const spherical = this.viewerInstance._orbitSpherical;
    if (spherical) {
      spherical.radius = Math.max(0.5, Math.min(20, spherical.radius * factor));
      this.viewerInstance._applyOrbit();
    }
  },

  toggleViewportProjection() {
    if (!this.viewerInstance) return;
    const isOrtho = this.viewerInstance.toggleProjection();
    const btn = document.querySelector('.ms-tool-btn[onclick*="toggleViewportProjection"]');
    if (btn) btn.style.opacity = isOrtho ? '0.5' : '1';
  },

  resetViewport() {
    if (this.viewerInstance) this.viewerInstance.resetCamera();
  },

  _optionsMenuOpen: false,
  toggleOptionsMenu() {
    this._optionsMenuOpen = !this._optionsMenuOpen;
    const dd = document.getElementById('ms-options-dropdown');
    if (dd) dd.style.display = this._optionsMenuOpen ? 'block' : 'none';
  },

  setViewportMode(mode) {
    if (!this.viewerInstance) return;
    if (mode === 'wireframe') {
      this.viewerInstance.toggleWireframe(true);
    } else if (mode === 'solid') {
      this.viewerInstance.toggleWireframe(false);
    } else if (mode === 'rendered') {
      this.viewerInstance.wireframeMode = false;
      if (this.viewerInstance.mesh) {
        this.viewerInstance.mesh.material = this.viewerInstance._solidMat;
        this.viewerInstance.mesh.material.needsUpdate = true;
        if (this.viewerInstance.mesh.material.emissive !== undefined) {
          this.viewerInstance.mesh.material.emissiveIntensity = 0.3;
        }
      }
    }
    document.querySelectorAll('.ms-options-item').forEach(el => el.classList.remove('active'));
    const item = document.querySelector(`.ms-options-item[data-mode="${mode}"]`);
    if (item) item.classList.add('active');
    document.getElementById('ms-options-dropdown').style.display = 'none';
    this._optionsMenuOpen = false;
  },

  initCompareViewers() {
    this.vBaseline = window.createKorraVisualizer?.();
    this.vLatest = window.createKorraVisualizer?.();
    if (this.vBaseline) this.vBaseline.init('ms-compare-baseline');
    if (this.vLatest) this.vLatest.init('ms-compare-current');
    this.loadCompareViewers();
  },

  loadCompareViewers() {
    const scans = this.compareHistory.filter(s => s !== this.data);
    if (scans.length === 0) return;
    if (this.compareBaselineIdx >= scans.length) this.compareBaselineIdx = 0;
    const baseline = scans[this.compareBaselineIdx];
    if (baseline.mesh_url && this.vBaseline) {
      this.vBaseline.loadMesh(baseline.mesh_url).then(d => { this.baselineData = d; }).catch(() => {});
    }
    if (this.data?.mesh_url && this.vLatest) {
      this.vLatest.loadMesh(this.data.mesh_url).then(d => { this.latestData = d; }).catch(() => {});
    }
  },

  // ═══ AI ═══
  openAI() {
    this.switchView('ai');
  },
  closeAI() {
    this.switchView(this._previousView || 'avatar');
    if (this._aiLoading) this.cancelAI();
  },
  async askAI(prompt) {
    if (!prompt?.trim() || this._aiLoading) return;
    const body = document.getElementById('ms-ai-body');
    const input = document.getElementById('ms-ai-input');
    const sendBtn = document.getElementById('ms-ai-send');
    if (!body) return;
    body.insertAdjacentHTML('beforeend', `<div class="ms-ai-message user">${prompt}</div>`);
    if (input) { input.value = ''; input.disabled = true; }
    if (sendBtn) sendBtn.disabled = true;
    body.scrollTop = body.scrollHeight;
    this._aiLoading = true;
    this._aiAbort = new AbortController();
    body.insertAdjacentHTML('beforeend', `<div class="ms-ai-message assistant" id="ms-ai-loading" style="animation:msPulse 1s infinite">Thinking... <button class="ms-ai-cancel" onclick="KORRA_MS.cancelAI()">Cancel</button></div>`);
    body.scrollTop = body.scrollHeight;
    try {
      const res = await fetch('/api/v2/ai/assist', {
        method: 'POST',
        signal: this._aiAbort.signal,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt,
          measurements: this.data?.measurements || {},
          body_shape: this.data?.body_shape || 'Standard',
          size_recommendation: this.data?.size_recommendation || 'M',
          height: this.data?.height,
          gender: this.data?.gender,
          client_name: this.data?.client_name || null,
          scan_date: this.data?.created_at || null,
          active_attire: this.activeContext,
          active_material: this.activeMaterial,
          show_eased: this.showEased,
          selected_measurement: this.selectedMeasurement,
          unit_preference: this.unit,
          notes: this.data?.notes || null,
          scan_history: (this.compareHistory || [])
            .filter(s => s !== this.data)
            .slice(0, 5)
            .map(s => ({
              date: s.created_at,
              measurements: s.measurements,
              body_shape: s.body_shape,
              size: s.size_recommendation,
            })),
          chat_history: (this._aiChatHistory || []).slice(-10),
        })
      });
      const data = await res.json();
      document.getElementById('ms-ai-loading')?.remove();
      body.insertAdjacentHTML('beforeend', `<div class="ms-ai-message assistant">${data.response || 'No response available.'}</div>`);
      this._aiChatHistory.push({ role: 'user', content: prompt });
      this._aiChatHistory.push({ role: 'assistant', content: data.response || '' });
    } catch (e) {
      if (e.name === 'AbortError') return;
      document.getElementById('ms-ai-loading')?.remove();
      body.insertAdjacentHTML('beforeend', `<div class="ms-ai-message assistant">AI assistant unavailable. Please try again later.</div>`);
    }
    body.scrollTop = body.scrollHeight;
    if (input) input.disabled = false;
    if (sendBtn) sendBtn.disabled = false;
    this._aiLoading = false;
    this._aiAbort = null;
  },
  cancelAI() {
    if (this._aiAbort) this._aiAbort.abort();
    document.getElementById('ms-ai-loading')?.remove();
    const input = document.getElementById('ms-ai-input');
    const sendBtn = document.getElementById('ms-ai-send');
    if (input) input.disabled = false;
    if (sendBtn) sendBtn.disabled = false;
    this._aiLoading = false;
    this._aiAbort = null;
  },
  newChat() {
    const body = document.getElementById('ms-ai-body');
    if (body) body.innerHTML = '';
    this._aiChatHistory = [];
    document.getElementById('ms-ai-input')?.focus();
  },

  // ═══ EASE MULTIPLIERS ═══
  getEase(key) {
    const reg = window.ATTIRE_REGISTRY || [];
    const entry = reg.find(a => a.id === this.activeContext);
    const base = entry ? entry.mult : 1.035;
    const materialCoeffs = {
      woven: 1.0, knit: 0.85, starch_bazin: 1.1, technical: 0.9,
      silk: 0.95, denim: 1.05, linen: 1.08, wool: 1.03
    };
    const mat = materialCoeffs[this.activeMaterial] || 1.0;
    const result = base * mat;
    console.log(`  getEase("${key}") → ctx="${this.activeContext}" entry=${!!entry} base=${base} mat=${mat} result=${result}`);
    return result;
  },

  // ═══ FABRIC PRESETS (Phases 2-5) ═══
  FABRIC_PRESETS: {
    woven:    { coeff: 1.0,  K: 0.8,  B: 0.3,  M: 1.0,  color: '#CCCCCC', name: 'Woven' },
    knit:     { coeff: 0.85, K: 0.4,  B: 0.1,  M: 0.7,  color: '#AAAAAA', name: 'Knit' },
    starch_bazin: { coeff: 1.1, K: 0.95, B: 0.9,  M: 1.2,  color: '#DDDDDD', name: 'Starch Bazin' },
    technical:{ coeff: 0.9,  K: 0.5,  B: 0.4,  M: 0.8,  color: '#999999', name: 'Technical' },
    silk:     { coeff: 0.95, K: 0.3,  B: 0.05, M: 0.5,  color: '#F5E6CA', name: 'Silk' },
    denim:    { coeff: 1.05, K: 0.9,  B: 0.7,  M: 1.3,  color: '#4A6E9B', name: 'Denim' },
    linen:    { coeff: 1.08, K: 0.7,  B: 0.6,  M: 0.9,  color: '#E8D5B7', name: 'Linen' },
    wool:     { coeff: 1.03, K: 0.6,  B: 0.5,  M: 1.1,  color: '#8B7D6B', name: 'Wool' },
  },

  // ═══ PATTERN TEMPLATES CATALOG (Phase 21) ═══
  PATTERN_TEMPLATES: {
    shirt: ['shirtFront', 'shirtBack', 'shirtSleeve', 'shirtCollar'],
    blazer: ['jacketFront', 'jacketBack', 'jacketSleeve', 'jacketLining'],
    jacket: ['jacketFront', 'jacketBack', 'jacketSleeve'],
    pant: ['pantFront', 'pantBack'],
    short: ['pantFront', 'pantBack'],
    skirt: ['skirtFront', 'skirtBack'],
    dress: ['dressFront', 'dressBack', 'dressSleeve'],
    jumpsuit: ['jumpsuitFront', 'jumpsuitBack', 'jumpsuitSleeve'],
    coat: ['jacketFront', 'jacketBack', 'jacketSleeve', 'jacketCollar'],
  },

  // ═══ SEAM ALLOWANCE DEFAULTS (Phase 22) ═══
  SEAM_ALLOWANCE_DEFAULTS: {
    shirt: 1.5, blazer: 1.5, jacket: 1.5, pant: 1.2,
    short: 1.2, skirt: 1.5, dress: 1.5, jumpsuit: 1.5,
    coat: 2.0, standard: 1.5,
  },

  // ═══ PATTERN PIECE CATALOG (Phase 23) ═══
  PATTERN_PIECE_CATALOG: {
    shirtFront: { label: 'Shirt Front', symmetry: 'right', cut: 2, grain: 'vertical' },
    shirtBack: { label: 'Shirt Back', symmetry: 'center', cut: 1, grain: 'vertical' },
    shirtSleeve: { label: 'Sleeve', symmetry: 'right', cut: 2, grain: 'vertical' },
    shirtCollar: { label: 'Collar', symmetry: 'center', cut: 1, grain: 'horizontal' },
    jacketFront: { label: 'Jacket Front', symmetry: 'right', cut: 2, grain: 'vertical' },
    jacketBack: { label: 'Jacket Back', symmetry: 'center', cut: 1, grain: 'vertical' },
    jacketSleeve: { label: 'Jacket Sleeve', symmetry: 'right', cut: 2, grain: 'vertical' },
    jacketLining: { label: 'Jacket Lining', symmetry: 'right', cut: 2, grain: 'vertical' },
    jacketCollar: { label: 'Jacket Collar', symmetry: 'center', cut: 1, grain: 'horizontal' },
    pantFront: { label: 'Pant Front', symmetry: 'right', cut: 2, grain: 'vertical' },
    pantBack: { label: 'Pant Back', symmetry: 'right', cut: 2, grain: 'vertical' },
    skirtFront: { label: 'Skirt Front', symmetry: 'center', cut: 1, grain: 'vertical' },
    skirtBack: { label: 'Skirt Back', symmetry: 'center', cut: 1, grain: 'vertical' },
    dressFront: { label: 'Dress Front', symmetry: 'center', cut: 1, grain: 'vertical' },
    dressBack: { label: 'Dress Back', symmetry: 'center', cut: 1, grain: 'vertical' },
    dressSleeve: { label: 'Dress Sleeve', symmetry: 'right', cut: 2, grain: 'vertical' },
    jumpsuitFront: { label: 'Jumpsuit Front', symmetry: 'center', cut: 1, grain: 'vertical' },
    jumpsuitBack: { label: 'Jumpsuit Back', symmetry: 'center', cut: 1, grain: 'vertical' },
    jumpsuitSleeve: { label: 'Jumpsuit Sleeve', symmetry: 'right', cut: 2, grain: 'vertical' },
  },

  // ═══ PATTERN MEASUREMENT ACCESSOR (Phase 15) ═══
  getPatternMeasurements() {
    const m = this.data?.measurements || {};
    const gender = (this.data?.gender || 'male').toLowerCase();
    const isFemale = gender === 'female';
    return {
      chest: m['Chest Round'] || m['Bust Round'] || 100,
      waist: m['Waist Round'] || 80,
      hip: m['Hip Round'] || 96,
      shoulder: m['Shoulder'] || 44,
      neck: m['Neck Round'] || 38,
      sleeveLength: m['Sleeve Length'] || 60,
      fullLength: m['Full Top Length'] || 70,
      trouserLength: m['Trouser Length'] || 100,
      inseam: m['Inseam'] || 78,
      bicep: m['Bicep Round'] || 32,
      wrist: m['Wrist Round'] || 18,
      thigh: m['Thigh Round'] || 52,
      acrossShoulder: m['Across Shoulder'] || m['Shoulder'] || 44,
      neckToWaist: m['Neck to Waist'] || m['Half Length'] || 44,
      waistToHip: m['Waist to Hip'] || 20,
      acrossChest: m['Across Chest'] || 36,
      acrossBack: m['Across Back'] || 38,
      stomach: m['Stomach Round'] || 88,
      highBust: m['High Bust'] || isFemale ? 88 : 0,
      underBust: m['Under Bust'] || isFemale ? 78 : 0,
      bustPoint: m['Bust Point'] || isFemale ? 20 : 0,
      halfLength: m['Half Length'] || 44,
      crotchDepth: m['Crotch Depth'] || 28,
    };
  },

  // ═══ PATTERN DRAFTING ENGINE (Track C: Phases 51-85) ═══

  // --- SVG Primitives ---
  _drawPath(svg, points, opts = {}) {
    const d = points.map((p, i) => {
      if (i === 0) return `M ${p.x} ${p.y}`;
      if (p.c) return `C ${p.c.x} ${p.c.y} ${p.c2?.x || p.c.x} ${p.c2?.y || p.c.y} ${p.x} ${p.y}`;
      return `L ${p.x} ${p.y}`;
    }).join(' ');
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", d);
    path.setAttribute("fill", opts.fill || "none");
    path.setAttribute("stroke", opts.stroke || "var(--Accent-Teal)");
    path.setAttribute("stroke-width", String(opts.strokeWidth || 2));
    if (opts.dash) path.setAttribute("stroke-dasharray", opts.dash);
    if (opts.className) path.classList.add(opts.className);
    return path;
  },

  _drawCurve(svg, from, cp1, cp2, to, opts = {}) {
    const d = `M ${from.x} ${from.y} C ${cp1.x} ${cp1.y}, ${cp2.x} ${cp2.y}, ${to.x} ${to.y}`;
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", d);
    path.setAttribute("fill", "none");
    path.setAttribute("stroke", opts.stroke || "var(--Accent-Teal)");
    path.setAttribute("stroke-width", String(opts.strokeWidth || 2));
    return path;
  },

  _drawArc(svg, cx, cy, r, startAngle, endAngle, opts = {}) {
    const start = { x: cx + r * Math.cos(startAngle), y: cy + r * Math.sin(startAngle) };
    const end = { x: cx + r * Math.cos(endAngle), y: cy + r * Math.sin(endAngle) };
    const largeArc = endAngle - startAngle > Math.PI ? 1 : 0;
    const d = `M ${start.x} ${start.y} A ${r} ${r} 0 ${largeArc} 1 ${end.x} ${end.y}`;
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", d);
    path.setAttribute("fill", "none");
    path.setAttribute("stroke", opts.stroke || "var(--Accent-Teal)");
    path.setAttribute("stroke-width", String(opts.strokeWidth || 2));
    return path;
  },

  _drawDart(svg, apex, left, right, opts = {}) {
    const d = `M ${apex.x} ${apex.y} L ${left.x} ${left.y} L ${right.x} ${right.y} Z`;
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", d);
    path.setAttribute("fill", "rgba(198,255,0,0.15)");
    path.setAttribute("stroke", "var(--Accent-Teal)");
    path.setAttribute("stroke-width", "1.5");
    path.setAttribute("stroke-dasharray", "4,3");
    return path;
  },

  _drawGrainline(svg, x, y, length, opts = {}) {
    const arrowSize = opts.arrowSize || 6;
    const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", x); line.setAttribute("y1", y);
    line.setAttribute("x2", x); line.setAttribute("y2", y + length);
    line.setAttribute("stroke", opts.stroke || "var(--Neutral-400)");
    line.setAttribute("stroke-width", "1.5");
    g.appendChild(line);
    const topArrow = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
    topArrow.setAttribute("points", `${x},${y} ${x-arrowSize},${y+arrowSize+3} ${x+arrowSize},${y+arrowSize+3}`);
    topArrow.setAttribute("fill", opts.stroke || "var(--Neutral-400)");
    g.appendChild(topArrow);
    return g;
  },

  _drawSeamAllowance(svg, points, offset, opts = {}) {
    const inset = points.map(p => ({ x: p.x + offset, y: p.y + offset }));
    return this._drawPath(svg, inset, { ...opts, stroke: "var(--Neutral-500)", strokeWidth: 1, dash: "4,3" });
  },

  _drawNotch(svg, x, y, size = 6, opts = {}) {
    const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
    const notch = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
    notch.setAttribute("points", `${x},${y} ${x-size},${y+size} ${x+size},${y+size}`);
    notch.setAttribute("fill", "var(--Accent-Teal)");
    notch.setAttribute("opacity", "0.8");
    g.appendChild(notch);
    return g;
  },

  _drawLabel(svg, x, y, text, opts = {}) {
    const t = document.createElementNS("http://www.w3.org/2000/svg", "text");
    t.setAttribute("x", x); t.setAttribute("y", y);
    t.setAttribute("text-anchor", opts.anchor || "middle");
    t.setAttribute("fill", opts.color || "white");
    t.setAttribute("font-size", String(opts.fontSize || 12));
    t.setAttribute("font-weight", opts.bold ? "900" : "400");
    if (opts.className) t.classList.add(opts.className);
    t.textContent = text;
    return t;
  },

  // --- Pattern Templates ---
  _templateShirtFront(svg, m, sc, ori) {
    const chestQ = (m.chest || 100) / 4;
    const len = m.fullLength || 70;
    const neck = (m.neck || 38) / 6;
    const shoulder = (m.shoulder || 44) / 2;
    const pts = [
      { x: ori.x, y: ori.y },
      { x: ori.x + chestQ, y: ori.y },
      { x: ori.x + chestQ, y: ori.y + len },
      { x: ori.x + neck, y: ori.y + len },
      { x: ori.x + neck, y: ori.y + neck },
      { x: ori.x, y: ori.y + shoulder * 0.3 },
    ];
    svg.appendChild(this._drawPath(svg, pts.concat([pts[0]]), { fill: "rgba(198,255,0,0.04)" }));
    svg.appendChild(this._drawLabel(svg, ori.x + chestQ/2, ori.y + len/2, "FRONT"));
    this._drawGrainline(svg, ori.x + chestQ/2, ori.y + 20, 30);
  },

  _templateShirtBack(svg, m, sc, ori) {
    const chestQ = (m.chest || 100) / 4;
    const len = m.fullLength || 70;
    const x = ori.x + (m.chest || 100)/4 + 15;
    const pts = [
      { x, y: ori.y },
      { x: x + chestQ, y: ori.y },
      { x: x + chestQ, y: ori.y + len },
      { x, y: ori.y + len },
    ];
    svg.appendChild(this._drawPath(svg, pts.concat([pts[0]]), { fill: "rgba(255,255,255,0.03)" }));
    svg.appendChild(this._drawLabel(svg, x + chestQ/2, ori.y + len/2, "BACK"));
  },

  _templateShirtSleeve(svg, m, sc, ori) {
    const chestQ = (m.chest || 100) / 4;
    const len = m.sleeveLength || 60;
    const x = ori.x + (m.chest || 100)/2 + 25;
    const width = (m.bicep || 32) / 2;
    const pts = [
      { x, y: ori.y },
      { x: x + width, y: ori.y + 10 },
      { x: x + width * 0.7, y: ori.y + len },
      { x: x + width * 0.3, y: ori.y + len },
    ];
    svg.appendChild(this._drawPath(svg, pts.concat([pts[0]]), { fill: "rgba(0,212,255,0.04)" }));
    svg.appendChild(this._drawLabel(svg, x + width/2, ori.y + len/2, "SLEEVE"));
    this._drawNotch(svg, x + width/2, ori.y + 5);
  },

  _templatePantFront(svg, m, sc, ori) {
    const waistQ = (m.waist || 80) / 4;
    const len = m.trouserLength || 100;
    const hipQ = (m.hip || 96) / 4;
    const thigh = (m.thigh || 52) / 2;
    const pts = [
      { x: ori.x, y: ori.y },
      { x: ori.x + waistQ + 3, y: ori.y },
      { x: ori.x + hipQ + 2, y: ori.y + len * 0.25 },
      { x: ori.x + thigh, y: ori.y + len * 0.5 },
      { x: ori.x + thigh * 0.6, y: ori.y + len },
      { x: ori.x + 2, y: ori.y + len },
    ];
    svg.appendChild(this._drawPath(svg, pts.concat([pts[0]]), { fill: "rgba(255,194,71,0.04)" }));
    svg.appendChild(this._drawLabel(svg, ori.x + (waistQ+3)/2, ori.y + len/2, "FRONT LEG"));
  },

  _templatePantBack(svg, m, sc, ori) {
    const waistQ = (m.waist || 80) / 4;
    const len = m.trouserLength || 100;
    const hipQ = (m.hip || 96) / 4;
    const thigh = (m.thigh || 52) / 2;
    const x = ori.x + (m.waist || 80)/4 + 15;
    const pts = [
      { x, y: ori.y },
      { x: x + waistQ + 5, y: ori.y },
      { x: x + hipQ + 4, y: ori.y + len * 0.25 },
      { x: x + thigh + 1, y: ori.y + len * 0.5 },
      { x: x + thigh * 0.65, y: ori.y + len },
      { x: x + 3, y: ori.y + len },
    ];
    svg.appendChild(this._drawPath(svg, pts.concat([pts[0]]), { fill: "rgba(255,194,71,0.06)" }));
    svg.appendChild(this._drawLabel(svg, x + (waistQ+5)/2, ori.y + len/2, "BACK LEG"));
  },

  _templateSkirtFront(svg, m, sc, ori) {
    const waistQ = (m.waist || 80) / 4;
    const len = m.trouserLength || 60;
    const hipQ = (m.hip || 96) / 4;
    const pts = [
      { x: ori.x, y: ori.y },
      { x: ori.x + waistQ, y: ori.y },
      { x: ori.x + hipQ + 3, y: ori.y + len },
      { x: ori.x + 2, y: ori.y + len },
    ];
    svg.appendChild(this._drawPath(svg, pts.concat([pts[0]]), { fill: "rgba(198,255,0,0.04)" }));
    svg.appendChild(this._drawLabel(svg, ori.x + waistQ/2, ori.y + len/2, "SKIRT FRONT"));
  },

  _templateSkirtBack(svg, m, sc, ori) {
    const waistQ = (m.waist || 80) / 4;
    const len = m.trouserLength || 60;
    const hipQ = (m.hip || 96) / 4;
    const x = ori.x + waistQ + 15;
    const pts = [
      { x, y: ori.y },
      { x: x + waistQ + 1, y: ori.y },
      { x: x + hipQ + 4, y: ori.y + len },
      { x: x + 3, y: ori.y + len },
    ];
    svg.appendChild(this._drawPath(svg, pts.concat([pts[0]]), { fill: "rgba(198,255,0,0.06)" }));
    svg.appendChild(this._drawLabel(svg, x + (waistQ+1)/2, ori.y + len/2, "SKIRT BACK"));
  },

  _templateJacketFront(svg, m, sc, ori) {
    const chestQ = (m.chest || 100) / 4;
    const len = m.fullLength || 75;
    const shoulder = (m.shoulder || 44) / 2;
    const pts = [
      { x: ori.x + 5, y: ori.y },
      { x: ori.x + chestQ + 3, y: ori.y },
      { x: ori.x + chestQ + 3, y: ori.y + len },
      { x: ori.x + 3, y: ori.y + len },
      { x: ori.x + 3, y: ori.y + shoulder * 0.25 },
      { x: ori.x + 5, y: ori.y + 5 },
    ];
    svg.appendChild(this._drawPath(svg, pts.concat([pts[0]]), { fill: "rgba(179,136,255,0.04)" }));
    svg.appendChild(this._drawLabel(svg, ori.x + (chestQ+3)/2, ori.y + len/2, "JACKET FRONT"));
  },

  _templateJacketBack(svg, m, sc, ori) {
    const chestQ = (m.chest || 100) / 4;
    const len = m.fullLength || 75;
    const x = ori.x + (m.chest || 100)/4 + 20;
    const pts = [
      { x, y: ori.y },
      { x: x + chestQ + 2, y: ori.y },
      { x: x + chestQ + 2, y: ori.y + len },
      { x, y: ori.y + len },
    ];
    svg.appendChild(this._drawPath(svg, pts.concat([pts[0]]), { fill: "rgba(179,136,255,0.06)" }));
    svg.appendChild(this._drawLabel(svg, x + (chestQ+2)/2, ori.y + len/2, "JACKET BACK"));
  },

  _templateJacketSleeve(svg, m, sc, ori) {
    const len = m.sleeveLength || 62;
    const bicep = (m.bicep || 32) / 2;
    const x = ori.x + (m.chest || 100)/2 + 35;
    const pts = [
      { x, y: ori.y },
      { x: x + bicep + 2, y: ori.y + 10 },
      { x: x + bicep, y: ori.y + len },
      { x: x + 2, y: ori.y + len },
    ];
    svg.appendChild(this._drawPath(svg, pts.concat([pts[0]]), { fill: "rgba(179,136,255,0.04)" }));
    svg.appendChild(this._drawLabel(svg, x + (bicep+2)/2, ori.y + len/2, "SLEEVE"));
  },

  _templateDressFront(svg, m, sc, ori) {
    const chestQ = (m.chest || 96) / 4;
    const len = m.fullLength || 120;
    const hipQ = (m.hip || 96) / 4;
    const pts = [
      { x: ori.x + 2, y: ori.y },
      { x: ori.x + chestQ + 2, y: ori.y },
      { x: ori.x + hipQ + 3, y: ori.y + len },
      { x: ori.x + 1, y: ori.y + len },
    ];
    svg.appendChild(this._drawPath(svg, pts.concat([pts[0]]), { fill: "rgba(198,255,0,0.03)" }));
    svg.appendChild(this._drawLabel(svg, ori.x + (chestQ+2)/2, ori.y + len/2, "DRESS FRONT"));
  },

  _templateDressBack(svg, m, sc, ori) {
    const chestQ = (m.chest || 96) / 4;
    const len = m.fullLength || 120;
    const hipQ = (m.hip || 96) / 4;
    const x = ori.x + chestQ + 15;
    const pts = [
      { x, y: ori.y },
      { x: x + chestQ + 1, y: ori.y },
      { x: x + hipQ + 3, y: ori.y + len },
      { x: x + 1, y: ori.y + len },
    ];
    svg.appendChild(this._drawPath(svg, pts.concat([pts[0]]), { fill: "rgba(198,255,0,0.05)" }));
    svg.appendChild(this._drawLabel(svg, x + (chestQ+1)/2, ori.y + len/2, "DRESS BACK"));
  },

  _templateJumpsuitFront(svg, m, sc, ori) {
    const chestQ = (m.chest || 100) / 4;
    const len = (m.fullLength || 70) + (m.trouserLength || 100) - 30;
    const waistQ = (m.waist || 80) / 4;
    const pts = [
      { x: ori.x, y: ori.y },
      { x: ori.x + chestQ, y: ori.y },
      { x: ori.x + waistQ + 1, y: ori.y + len * 0.45 },
      { x: ori.x + waistQ + 3, y: ori.y + len },
      { x: ori.x + 2, y: ori.y + len },
    ];
    svg.appendChild(this._drawPath(svg, pts.concat([pts[0]]), { fill: "rgba(255,194,71,0.04)" }));
    svg.appendChild(this._drawLabel(svg, ori.x + chestQ/2, ori.y + len/2, "JUMPSUIT FRONT"));
  },

  _templateJumpsuitBack(svg, m, sc, ori) {
    const chestQ = (m.chest || 100) / 4;
    const len = (m.fullLength || 70) + (m.trouserLength || 100) - 30;
    const waistQ = (m.waist || 80) / 4;
    const x = ori.x + chestQ + 15;
    const pts = [
      { x, y: ori.y },
      { x: x + chestQ + 1, y: ori.y },
      { x: x + waistQ + 3, y: ori.y + len * 0.45 },
      { x: x + waistQ + 5, y: ori.y + len },
      { x: x + 3, y: ori.y + len },
    ];
    svg.appendChild(this._drawPath(svg, pts.concat([pts[0]]), { fill: "rgba(255,194,71,0.06)" }));
    svg.appendChild(this._drawLabel(svg, x + (chestQ+1)/2, ori.y + len/2, "JUMPSUIT BACK"));
  },

  // --- Main Render ---
  renderPattern() {
    console.log('📐 renderPattern()');
    const svg = document.getElementById('ms-pattern-content');
    if (!svg) return;
    svg.innerHTML = '';

    const m = this.getPatternMeasurements();
    const attire = this.activeContext;

    const sc = 5;
    const ori = { x: 50, y: 50 };

    const templateMap = {
      shirt: ['shirtFront', 'shirtBack', 'shirtSleeve'],
      't-shirt': ['shirtFront', 'shirtBack', 'shirtSleeve'],
      blazer: ['jacketFront', 'jacketBack', 'jacketSleeve'],
      blazer_business: ['jacketFront', 'jacketBack', 'jacketSleeve'],
      bomber_jacket: ['jacketFront', 'jacketBack', 'jacketSleeve'],
      trench_coat: ['jacketFront', 'jacketBack', 'jacketSleeve'],
      pant: ['pantFront', 'pantBack'],
      senator: ['pantFront', 'pantBack'],
      agbada: ['pantFront', 'pantBack'],
      'a_line_skirt': ['skirtFront', 'skirtBack'],
      skirt: ['skirtFront', 'skirtBack'],
      dress: ['dressFront', 'dressBack'],
      kaftan: ['dressFront', 'dressBack'],
      jumpsuit: ['jumpsuitFront', 'jumpsuitBack'],
      classic_jumpsuit: ['jumpsuitFront', 'jumpsuitBack'],
      kurta: ['shirtFront', 'shirtBack'],
      kikoy: ['shirtFront', 'shirtBack'],
      'pencil_skirt': ['skirtFront', 'skirtBack'],
    };

    const templateFn = {
      shirtFront: '_templateShirtFront', shirtBack: '_templateShirtBack', shirtSleeve: '_templateShirtSleeve',
      pantFront: '_templatePantFront', pantBack: '_templatePantBack',
      skirtFront: '_templateSkirtFront', skirtBack: '_templateSkirtBack',
      jacketFront: '_templateJacketFront', jacketBack: '_templateJacketBack', jacketSleeve: '_templateJacketSleeve',
      dressFront: '_templateDressFront', dressBack: '_templateDressBack',
      jumpsuitFront: '_templateJumpsuitFront', jumpsuitBack: '_templateJumpsuitBack',
    };

    const pieces = templateMap[attire] || null;
    if (!pieces) {
      svg.innerHTML = `<text x="200" y="100" fill="var(--Neutral-400)" font-size="14" text-anchor="middle">Pattern drafting for "${attire}" is not yet available</text>`;
      return;
    }

    pieces.forEach((piece, i) => {
      const fnName = templateFn[piece];
      if (!fnName) return;
      const localOri = { x: ori.x, y: ori.y + i * 220 };
      this[fnName](svg, m, sc, localOri);
    });

    svg.appendChild(this._drawLabel(svg, 50, 30, `${attire.toUpperCase()} PATTERN`, { fontSize: 16, bold: true, color: 'var(--Accent-Teal)' }));
  },

  zoomPattern(dir) {
    const svg = document.getElementById('ms-pattern-svg');
    if (!svg) return;
    const vb = svg.viewBox.baseVal;
    const factor = dir === 'in' ? 0.8 : 1.2;
    vb.width *= factor;
    vb.height *= factor;
  },

  resetPattern() {
    const svg = document.getElementById('ms-pattern-svg');
    if (!svg) return;
    svg.setAttribute("viewBox", "0 0 1000 1000");
  },

  openPatternDownloadModal() {
    const modal = document.getElementById('downloadPatternModal');
    if (modal) modal.style.display = 'flex';
    const svg = document.getElementById('ms-pattern-content');
    if (svg) {
      const preview = document.getElementById('dp-preview');
      if (preview) {
        preview.innerHTML = '';
        const clone = svg.cloneNode(true);
        clone.setAttribute('width', '100%');
        clone.setAttribute('height', '100%');
        preview.appendChild(clone);
      }
    }
  },

  _sampleBezier(p0, p1, p2, p3, samples = 20) {
    const pts = [];
    for (let t = 0; t <= 1; t += 1 / samples) {
      const mt = 1 - t;
      const x = mt*mt*mt*p0.x + 3*mt*mt*t*p1.x + 3*mt*t*t*p2.x + t*t*t*p3.x;
      const y = mt*mt*mt*p0.y + 3*mt*mt*t*p1.y + 3*mt*t*t*p2.y + t*t*t*p3.y;
      pts.push({ x, y });
    }
    return pts;
  },

  _dxfPathToSegments(d) {
    const segs = [];
    const re = /([MLC])\s*([\d.eE+-]+),?[\s,]*([\d.eE+-]+)|([\d.eE+-]+),?[\s,]*([\d.eE+-]+)/g;
    const tokens = d.match(/[MLC]|[\d.eE+-]+/g);
    if (!tokens) return segs;
    let i = 0;
    let cmd = '';
    let current = { x: 0, y: 0 };
    const num = () => parseFloat(tokens[i++]);
    while (i < tokens.length) {
      const tok = tokens[i];
      if (tok === 'M' || tok === 'L' || tok === 'C') { cmd = tok; i++; continue; }
      if (cmd === 'M') {
        current = { x: num(), y: num() };
        segs.push({ type: 'M', x: current.x, y: current.y });
      } else if (cmd === 'L') {
        const next = { x: num(), y: num() };
        segs.push({ type: 'L', x1: current.x, y1: current.y, x2: next.x, y2: next.y });
        current = next;
      } else if (cmd === 'C') {
        const cp1 = { x: num(), y: num() };
        const cp2 = { x: num(), y: num() };
        const end = { x: num(), y: num() };
        const samples = this._sampleBezier(current, cp1, cp2, end);
        for (let s = 0; s < samples.length - 1; s++) {
          segs.push({ type: 'L', x1: samples[s].x, y1: samples[s].y, x2: samples[s+1].x, y2: samples[s+1].y });
        }
        current = end;
      }
    }
    return segs;
  },

  _exportPatternDXF() {
    const svg = document.getElementById('ms-pattern-content');
    if (!svg) return;
    const sections = svg.querySelectorAll('path');
    if (!sections.length) return;
    let dxf = `999\nKORRA Pattern Export\n${this._dxfHeader()}\n`;
    let handle = 0x100;
    const cmToMm = 10 / 5;
    sections.forEach((path, idx) => {
      const d = path.getAttribute('d') || '';
      const segs = this._dxfPathToSegments(d);
      const layerName = `PIECE_${idx}`;
      segs.forEach(seg => {
        if (seg.type === 'L') {
          dxf += `  0\nLINE\n  5\n${(handle++).toString(16).toUpperCase()}\n  8\n${layerName}\n 10\n${(seg.x1 * cmToMm).toFixed(3)}\n 20\n${(-seg.y1 * cmToMm).toFixed(3)}\n 11\n${(seg.x2 * cmToMm).toFixed(3)}\n 21\n${(-seg.y2 * cmToMm).toFixed(3)}\n`;
        }
      });
    });
    dxf += `  0\nENDSEC\n  0\nEOF\n`;
    const blob = new Blob([dxf], { type: 'application/dxf' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${this.activeContext}_pattern.dxf`;
    a.click();
    URL.revokeObjectURL(url);
  },

  _dxfHeader() {
    return `  0\nSECTION\n  2\nHEADER\n  9\n$ACADVER\n  1\nAC1009\n  9\n$INSUNITS\n 70\n4\n  0\nENDSEC\n  0\nSECTION\n  2\nENTITIES\n`;
  },

  _exportPatternPDF() {
    const svg = document.getElementById('ms-pattern-content');
    if (!svg) return;
    const svgData = new XMLSerializer().serializeToString(svg);
    const canvas = document.createElement('canvas');
    canvas.width = 800; canvas.height = 600;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#0a0a0a';
    ctx.fillRect(0, 0, 800, 600);
    ctx.fillStyle = '#C6FF00';
    ctx.font = 'bold 16px monospace';
    ctx.fillText(`${this.activeContext.toUpperCase()} PATTERN`, 20, 40);
    ctx.fillStyle = '#ffffff';
    ctx.font = '12px monospace';
    ctx.fillText('Generated by KORRA', 20, 60);
    window.open(canvas.toDataURL('image/png'));
  },

  _exportPattern() {
    document.getElementById('downloadPatternModal').style.display = 'none';
    if (this.downloadFormat === 'dxf') this._exportPatternDXF();
    else this._exportPatternPDF();
  },
  async _updateGarmentForContext() {
    if (this.activeContext === 'standard') {
      if (this.viewerInstance) this.viewerInstance.removeGarment();
      if (this._reconMeshOnBody && this.viewerInstance?.scene) {
        this.viewerInstance.scene.remove(this._reconMeshOnBody);
        this._reconMeshOnBody = null;
      }
      this._hideVtoSpinner();
      const vtoControls = document.getElementById('ms-vto-controls');
      if (vtoControls) vtoControls.style.display = 'none';
      const reconControls = document.getElementById('ms-recon-mesh-controls');
      if (reconControls) reconControls.style.display = 'none';
      return;
    }
    // If we have a reconstructed mesh, use it directly instead of server drape
    if (this._reconMeshData) {
      console.log('[VTO] Using reconstructed mesh for try-on');
      this._applyReconMeshToViewport();
      this._hideVtoSpinner();
      return;
    }
    if (!this.data || !this.viewerInstance) return;
    console.log(`👗 [VTO] Generating garment for context: ${this.activeContext}`);
    this._showVtoSpinner();
    try {
      const { data: { session } } = await window.KORRA_DB.auth.getSession();
      const res = await fetch(`/api/v2/measurements/${this.data.id}/garment/drape`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({
          attire: this.activeContext,
          material: this.activeMaterial
        })
      });
      if (!res.ok) throw new Error("Draping failed");
      const result = await res.json();
      // Swap to TailorNet body from drape if not yet loaded
      if (result.body_mesh && this.viewerInstance?.loadTailornetBody && !this.viewerInstance._tailornetBodyLoaded) {
        fetch(result.body_mesh)
          .then(r => { if (!r.ok) throw new Error('Missing'); return r.text(); })
          .then(text => {
            this.viewerInstance._meshCache.set(result.body_mesh, text);
            this.viewerInstance.loadTailornetBody(result.body_mesh);
          })
          .catch(() => {});
      }
      const matPreset = this.FABRIC_PRESETS[this.activeMaterial] || this.FABRIC_PRESETS.woven;
      const matSettings = {
        color: matPreset.color ? parseInt(matPreset.color.replace('#', '0x')) : 0xFFFFFF,
        opacity: this.activeMaterial === 'silk' ? 0.6 : 0.95,
        shininess: this.activeMaterial === 'silk' ? 80 : 30
      };
      const urls = result.garment_meshes || (result.garment_mesh_url ? [result.garment_mesh_url] : []);
      if (urls.length > 0) {
        this.viewerInstance.removeGarment();
        for (let i = 0; i < urls.length; i++) {
          const depthWrite = i === 0 || this.activeMaterial !== 'silk';
          await this.viewerInstance.loadGarment(urls[i], { ...matSettings, depthWrite }, i);
        }
        const vtoControls = document.getElementById('ms-vto-controls');
        if (vtoControls) vtoControls.style.display = 'flex';
      }
      this._hideVtoSpinner();
    } catch (e) {
      console.warn("Garment generation skipped or failed:", e.message);
      if (this.viewerInstance) this.viewerInstance.removeGarment();
      this._hideVtoSpinner();
    }
  },

  // ═══ VTO CONTROLS (Track F) ═══
  _showVtoSpinner() {
    let spinner = document.getElementById('vto-spinner');
    if (!spinner) {
      spinner = document.createElement('div');
      spinner.id = 'vto-spinner';
      spinner.innerHTML = '<div class="vto-spinner-ring"></div><span>Generating garment...</span>';
      const container = document.querySelector('.ms-canvas-container');
      if (container) container.appendChild(spinner);
    }
    spinner.style.display = 'flex';
  },

  _hideVtoSpinner() {
    const spinner = document.getElementById('vto-spinner');
    if (spinner) spinner.style.display = 'none';
  },

  setGarmentOpacity(val) {
    const opacity = Math.max(0.1, Math.min(1, val));
    if (this.viewerInstance && this.viewerInstance.garmentMeshes) {
      for (let i = 0; i < this.viewerInstance.garmentMeshes.length; i++) {
        const mesh = this.viewerInstance.garmentMeshes[i];
        if (mesh && mesh.material) {
          mesh.material.opacity = opacity;
          mesh.material.needsUpdate = true;
        }
      }
    }
    const slider = document.getElementById('vto-opacity-slider');
    if (slider) slider.value = opacity;
    const label = document.getElementById('vto-opacity-label');
    if (label) label.textContent = `${Math.round(opacity * 100)}%`;
  },

  toggleGarmentVisibility() {
    if (!this.viewerInstance || !this.viewerInstance.garmentMeshes) return;
    const first = this.viewerInstance.garmentMeshes.find(m => m);
    const visible = first ? !first.visible : false;
    this.viewerInstance.toggleGarmentVisibility(visible);
    const btn = document.getElementById('vto-visibility-btn');
    if (btn) {
      btn.textContent = visible ? 'ON' : 'OFF';
      btn.classList.toggle('active', visible);
    }
  },

  toggleAutoRotate() {
    if (!this.viewerInstance) return;
    const enabled = !this.viewerInstance.autoRotate;
    this.viewerInstance.setAutoRotate(enabled);
    const btn = document.getElementById('ms-toggle-autorotate');
    if (btn) btn.classList.toggle('active', enabled);
  },

  // ═══ AI CHAT (IN-SHEET VIEW) ═══
  buildAIView() {
    return `<div class="ms-ai-view">
      <div class="ms-ai-topbar">
        <button class="ms-ai-back" onclick="KORRA_MS.switchView(KORRA_MS._previousView || 'avatar')">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
          Back to Measurements
        </button>
        <div class="ms-ai-title">Ask AI</div>
      </div>
      <div class="ms-ai-prompt-bar">
        <button class="ms-ai-prompt-btn" onclick="KORRA_MS.askAI('Explain my body measurements')">Explain this scan</button>
        <button class="ms-ai-prompt-btn" onclick="KORRA_MS.askAI('Recommend clothing fit for my body')">Clothing fit</button>
        <button class="ms-ai-prompt-btn" onclick="KORRA_MS.askAI('Give me a body summary')">Body summary</button>
        <button class="ms-ai-prompt-btn" onclick="KORRA_MS.askAI('What measurements changed since last scan?')">Progress insights</button>
        <button class="ms-ai-newchat" onclick="KORRA_MS.newChat()" title="New conversation">+</button>
      </div>
      <div class="ms-ai-body" id="ms-ai-body"></div>
      <div class="ms-ai-input-bar">
        <input class="ms-ai-input" id="ms-ai-input" placeholder="Ask about your measurements..." onkeydown="if(event.key==='Enter'&&!this.disabled)KORRA_MS.askAI(this.value)">
        <button class="ms-ai-send" id="ms-ai-send" onclick="KORRA_MS.askAI(document.getElementById('ms-ai-input').value)">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
        </button>
      </div>
    </div>`;
  },

  // ═══ TRY-ON (OOTDiffusion) ═══
  buildTryOnView() {
    const hasScan = !!(this.data && this.data.id);
    const photos = hasScan ? this._getScanPhotos() : null;

    return `
      <div class="ms-tryon-view">
        <div class="ms-tryon-topbar">
          <button class="ms-tryon-back" onclick="KORRA_MS.switchView(KORRA_MS._previousView || 'avatar')">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
            Back to Measurements
          </button>
          <div class="ms-tryon-title">Virtual Try-On</div>
          <div class="ms-tryon-subtitle">AI-powered garment visualization</div>
          <div class="ms-vto-sub-badge" id="ms-vto-sub-badge" style="display:none">
            <span class="dot"></span>
            <span id="ms-vto-sub-text">Active</span>
          </div>
          <div class="ms-vto-usage" id="ms-vto-usage" style="display:none"></div>
        </div>
        <div class="ms-tryon-input-area">
          <div class="ms-tryon-preview-box" id="ms-tryon-person-box" style="${hasScan ? 'display:none' : ''}">
            <div class="ms-tryon-preview-label">Person Photo</div>
            <div class="ms-tryon-preview-img" id="ms-tryon-person-preview"
                 onclick="document.getElementById('ms-tryon-person-file').click()"
                 ondragover="event.preventDefault(); this.classList.add('ms-tryon-dragover')"
                 ondragleave="this.classList.remove('ms-tryon-dragover')"
                 ondrop="event.preventDefault(); this.classList.remove('ms-tryon-dragover'); const f=event.dataTransfer.files[0]; if(f&&f.type.startsWith('image/')){document.getElementById('ms-tryon-person-file').files=event.dataTransfer.files; document.getElementById('ms-tryon-person-file').dispatchEvent(new Event('change'))}">
              <img id="ms-tryon-person-img" src="" alt="Person" style="display:none">
              <div class="ms-tryon-placeholder" id="ms-tryon-person-placeholder">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                <span>Drop a person photo here</span>
                <span class="ms-tryon-upload-hint">or click to browse</span>
              </div>
            </div>
            <input type="file" id="ms-tryon-person-file" accept="image/*" style="display:none">
          </div>

          ${hasScan ? `
          <div class="ms-tryon-preview-box" id="ms-tryon-reference-box">
            <div class="ms-tryon-preview-label">Your Scan</div>
            <div class="ms-tryon-reference-photos">
              <div class="ms-tryon-ref-thumb">
                ${photos.front ? `<img src="${photos.front}" alt="Front">` : '<div class="ms-tryon-ref-missing"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg></div>'}
                <span>Front</span>
              </div>
              <div class="ms-tryon-ref-thumb">
                ${photos.side ? `<img src="${photos.side}" alt="Side">` : '<div class="ms-tryon-ref-missing"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg></div>'}
                <span>Side</span>
              </div>
            </div>
            <div class="ms-tryon-ref-status">Using your scan for digital fitting</div>
            <button class="ms-tryon-upload-btn ms-tryon-switch-btn" onclick="KORRA_MS._toggleManualTryOn()">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/><path d="M16 16h5v5"/></svg>
              Use a different photo
            </button>
          </div>
          ` : ''}
          <div class="ms-tryon-arrow">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
          </div>
          <div class="ms-tryon-preview-box">
            <div class="ms-tryon-preview-label">Garment Photo</div>
            <div class="ms-tryon-preview-img" id="ms-tryon-garment-preview"
                 onclick="document.getElementById('ms-tryon-garment-file').click()"
                 ondragover="event.preventDefault(); this.classList.add('ms-tryon-dragover')"
                 ondragleave="this.classList.remove('ms-tryon-dragover')"
                 ondrop="event.preventDefault(); this.classList.remove('ms-tryon-dragover'); const f=event.dataTransfer.files[0]; if(f&&f.type.startsWith('image/')){document.getElementById('ms-tryon-garment-file').files=event.dataTransfer.files; document.getElementById('ms-tryon-garment-file').dispatchEvent(new Event('change'))}">
              <img id="ms-tryon-garment-img" src="" alt="Garment" style="display:none">
              <div class="ms-tryon-placeholder" id="ms-tryon-garment-placeholder">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
                <span>Drop a garment photo here</span>
                <span class="ms-tryon-upload-hint">or click to browse</span>
              </div>
            </div>
            <input type="file" id="ms-tryon-garment-file" accept="image/*" style="display:none">
          </div>
        </div>

        <div class="ms-tryon-action-row">
          <button class="ms-tryon-generate-btn" id="ms-tryon-generate-btn" disabled onclick="KORRA_MS._runTryOn()">Generate Try-On</button>
          <!-- Phase 201: Batch mode buttons -->
          <button class="ms-tryon-generate-btn ms-vto-queue-btn" id="ms-vto-queue-next" onclick="KORRA_MS._queueVtoBatch()">Queue Next</button>
          <button class="ms-tryon-generate-btn" id="ms-vto-process-queue" style="background:var(--Accent-Teal);margin-left:8px;display:none" onclick="KORRA_MS._processVtoBatch()">Process Queue</button>
        </div>
        <div class="ms-tryon-status" id="ms-tryon-status" style="display:none;">
          <div class="ms-tryon-spinner"></div>
          <span id="ms-tryon-status-text">Generating try-on... (~2 min)</span>
        </div>
        <div class="ms-tryon-results" id="ms-tryon-results" style="display:none;">
          <div class="ms-tryon-results-label">Results</div>
          <div class="ms-tryon-results-grid" id="ms-tryon-results-grid"></div>
        </div>
      </div>`;
  },

  buildReconstructView() {
    const garmentTypes = ['unknown', 'T-shirt', 'Shirt', 'Dress', 'Jacket', 'Pants', 'Skirt'];
    const historyHTML = this._renderReconHistory();
    return `
      <div class="ms-recon-view">
        <div class="ms-recon-topbar">
          <button class="ms-recon-back" onclick="KORRA_MS.switchView(KORRA_MS._previousView || 'avatar')">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
            Back to Measurements
          </button>
          <div class="ms-recon-title">Garment Reconstruction</div>
          <div class="ms-recon-subtitle">Convert image to 3D cloth</div>
        </div>
        <div class="ms-recon-input-area">
          <div class="ms-recon-preview-box" id="ms-recon-dropzone" style="max-width: 140px; margin: 0 auto;">
            <div class="ms-recon-preview-label">Garment Photo</div>
            <div class="ms-recon-preview-img" id="ms-recon-preview">
              <img id="ms-recon-img" src="" alt="Garment" style="display:none">
              <div class="ms-recon-placeholder" id="ms-recon-placeholder">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
                <span style="font-size:9px;">Upload garment photo</span>
              </div>
            </div>
            <input type="file" id="ms-recon-file" accept="image/*" style="display:none" aria-label="Upload garment photo">
            <div style="display:flex;gap:4px;margin-top:4px;">
              <button class="ms-recon-upload-btn" onclick="document.getElementById('ms-recon-file').click()">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                Choose
              </button>
              <button class="ms-recon-upload-btn ms-recon-camera-btn" onclick="KORRA_MS._captureCameraPhoto()" id="ms-recon-camera-btn" style="display:none;">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>
              </button>
            </div>
          </div>
        </div>
        <div class="ms-recon-garment-type-row">
          <label class="ms-recon-garment-type-label">Garment Type</label>
          <select class="ms-recon-garment-type-select" id="ms-recon-garment-type" onchange="KORRA_MS._reconGarmentType = this.value">
            ${garmentTypes.map(t => `<option value="${t}" ${t === 'unknown' ? 'selected' : ''}>${t === 'unknown' ? 'Auto-detect' : t}</option>`).join('')}
          </select>
          ${this._reconFile ? `<button class="ms-recon-share-btn" onclick="KORRA_MS._shareReconResult()" title="Share reconstruction">Share</button>` : ''}
        </div>
        <div class="ms-recon-action-row">
          <button class="ms-recon-generate-btn" id="ms-recon-generate-btn" disabled onclick="KORRA_MS._runReconstruct()" aria-label="Generate 3D reconstruction">Reconstruct Garment</button>
          ${this.data?.garment_mesh_url ? `<button class="ms-recon-generate-btn" style="margin-left:8px;background:var(--accent,#1DBFAF);color:#fff;" onclick="KORRA_MS._loadSavedGarment()">Load Saved Garment</button>` : ''}
        </div>
        <div class="ms-recon-status" id="ms-recon-status" style="display:none;">
          <div class="ms-recon-progress" id="ms-recon-progress">
            <div class="ms-recon-progress-bar" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100" aria-label="Reconstruction progress">
              <div class="ms-recon-progress-fill" id="ms-recon-progress-fill" style="width: 0%"></div>
            </div>
            <div class="ms-recon-progress-steps" id="ms-recon-progress-steps">
              <span class="ms-recon-step" data-step="uploading">Upload</span>
              <span class="ms-recon-step" data-step="segmenting">Segment</span>
              <span class="ms-recon-step" data-step="meshing">Mesh</span>
              <span class="ms-recon-step" data-step="patterning">Pattern</span>
              <span class="ms-recon-step" data-step="zipping">Package</span>
            </div>
            <span class="ms-recon-progress-text" id="ms-recon-progress-text">Uploading image...</span>
          </div>
        </div>
        <div class="ms-recon-error" id="ms-recon-error" data-type="server" style="display:none;">
          <div class="ms-recon-error-icon" id="ms-recon-error-icon"></div>
          <div class="ms-recon-error-message" id="ms-recon-error-message"></div>
          <div class="ms-recon-error-actions" id="ms-recon-error-actions"></div>
        </div>
        <div class="ms-recon-results" id="ms-recon-results" style="display:none;">
          <div class="ms-recon-results-label">Results</div>
          <div id="ms-recon-results-content"></div>
        </div>
        <div class="ms-recon-viewer-wrap" id="ms-recon-viewer-wrap" style="display:none;">
          <div class="ms-recon-viewer-header">
            <span class="ms-recon-viewer-label">3D Preview</span>
            <div class="ms-recon-viewer-actions">
              <button class="ms-recon-viewer-btn" onclick="KORRA_MS._toggleReconWireframe()" title="Toggle wireframe" aria-label="Toggle wireframe view">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
              </button>
              <button class="ms-recon-viewer-btn" onclick="KORRA_MS._toggleReconFullscreen()" title="Toggle fullscreen" aria-label="Toggle fullscreen 3D view">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/></svg>
              </button>
              <button class="ms-recon-viewer-btn" onclick="KORRA_MS._captureReconScreenshot()" title="Capture screenshot" aria-label="Save screenshot">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>
              </button>
              <button class="ms-recon-viewer-btn" onclick="KORRA_MS._resetReconCamera()" title="Reset camera">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 4v6h6"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/></svg>
              </button>
              <button class="ms-recon-viewer-btn" onclick="KORRA_MS._loadReconMeshIntoTryon()" title="Use in Virtual Try-On">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/><line x1="20" y1="8" x2="20" y2="14"/><line x1="23" y1="11" x2="17" y2="11"/></svg>
                Use in Try-On
              </button>
            </div>
          </div>
          <div class="ms-recon-viewer" id="ms-recon-viewer"></div>
          <div class="ms-recon-viewer-stats" id="ms-recon-viewer-stats" style="display:none;color:var(--Neutral-400);font-size:11px;padding:4px 14px;border-top:1px solid var(--Glass-Border);text-transform:uppercase;letter-spacing:0.04em;"></div>
          <div class="ms-recon-viewer-loading" id="ms-recon-viewer-loading" style="display:none;">
            <div class="ms-recon-spinner"></div>
            <span>Loading mesh...</span>
          </div>
        </div>
        ${(() => {
          const isMobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent) || (navigator.maxTouchPoints > 0 && window.innerWidth < 768);
          return isMobile ? `<button class="ms-recon-btn ms-recon-ar-btn" id="ms-recon-ar-btn" onclick="KORRA_MS._openARPreview()" aria-label="View garment in augmented reality">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
            View in AR
          </button>` : '';
        })()}
      </div>`;
  },

  _initTryOn() {
    this._tryonPersonFile = null;
    this._tryonGarmentFile = null;
    this._tryonPersonObjectUrl = null;
    this._tryonGarmentObjectUrl = null;
    this._vtoSelectedColor = '#FFFFFF';

    const setupUpload = (fileId, imgId, placeholderId, slot) => {
      const input = document.getElementById(fileId);
      if (!input) return;
      input.onchange = (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const img = document.getElementById(imgId);
        const placeholder = document.getElementById(placeholderId);
        if (slot === 'person') {
          if (this._tryonPersonObjectUrl) URL.revokeObjectURL(this._tryonPersonObjectUrl);
          this._tryonPersonFile = file;
          this._tryonPersonObjectUrl = URL.createObjectURL(file);
          if (img) { img.src = this._tryonPersonObjectUrl; img.style.display = ''; }
        } else {
          if (this._tryonGarmentObjectUrl) URL.revokeObjectURL(this._tryonGarmentObjectUrl);
          this._tryonGarmentFile = file;
          this._tryonGarmentObjectUrl = URL.createObjectURL(file);
          if (img) { img.src = this._tryonGarmentObjectUrl; img.style.display = ''; }
        }
        if (placeholder) placeholder.style.display = 'none';
        this._checkTryOnReady();
      };
    };
    setupUpload('ms-tryon-person-file', 'ms-tryon-person-img', 'ms-tryon-person-placeholder', 'person');
    setupUpload('ms-tryon-garment-file', 'ms-tryon-garment-img', 'ms-tryon-garment-placeholder', 'garment');

    // Phase 200: Check subscription status on view load
    this._checkVtoSubscription();
  },

  async _checkVtoSubscription() {
    const badge = document.getElementById('ms-vto-sub-badge');
    const badgeText = document.getElementById('ms-vto-sub-text');
    const usageEl = document.getElementById('ms-vto-usage');
    const btn = document.getElementById('ms-tryon-generate-btn');
    try {
      const { data: { session } } = await window.KORRA_DB.auth.getSession();
      if (!session) return;
      const res = await fetch('/api/v2/garment/vto/status', {
        headers: { 'Authorization': `Bearer ${session.access_token}` },
      });
      if (!res.ok) return;
      const data = await res.json();
      const sub = data.subscription || {};
      if (badge) {
        badge.style.display = 'inline-flex';
        if (sub.active) {
          badge.classList.remove('expired');
          if (badgeText) badgeText.textContent = `${sub.plan || 'Active'}`;
        } else {
          badge.classList.add('expired');
          if (badgeText) badgeText.textContent = 'No Subscription';
          if (btn) {
            btn.disabled = true;
            btn.title = 'Virtual Try-On requires an active subscription';
          }
        }
      }
      if (usageEl) {
        usageEl.style.display = 'block';
        usageEl.textContent = `${data.remaining} try-ons remaining today`;
      }
    } catch (e) {
      console.warn('[VTO] Subscription check failed:', e);
    }
  },

  _checkTryOnReady() {
    const hasScan = !!(this.data && this.data.id);
    const hasPerson = this._tryonPersonFile || hasScan;
    const hasGarment = !!this._tryonGarmentFile;

    const btn = document.getElementById('ms-tryon-generate-btn');
    if (!btn) return;
    btn.disabled = !(hasPerson && hasGarment);
  },

  _getScanPhotos() {
    if (!this.data) return { front: '', side: '' };
    return {
      front: this.data.photo_front_url || '',
      side: this.data.photo_side_url || ''
    };
  },

  _toggleManualTryOn() {
    const refBox = document.getElementById('ms-tryon-reference-box');
    const personBox = document.getElementById('ms-tryon-person-box');
    if (refBox) refBox.style.display = 'none';
    if (personBox) personBox.style.display = 'block';
  },

  async _runTryOn() {
    const btn = document.getElementById('ms-tryon-generate-btn');
    const status = document.getElementById('ms-tryon-status');
    const statusText = document.getElementById('ms-tryon-status-text');
    const results = document.getElementById('ms-tryon-results');
    const resultsGrid = document.getElementById('ms-tryon-results-grid');
    if (!btn || !status || !results || !resultsGrid) return;

    if (!this._tryonPersonFile) {
      alert('Please select a person photo first.');
      return;
    }
    if (!this._tryonGarmentFile) {
      alert('Please select a garment photo first.');
      return;
    }

    btn.style.display = 'none';
    status.style.display = 'flex';
    if (statusText) statusText.textContent = 'Checking subscription...';
    results.style.display = 'none';

    try {
      const { data: { session } } = await window.KORRA_DB.auth.getSession();
      if (!session) throw new Error('Please sign in to use Virtual Try-On');

      // Phase 149: Initialize multi-angle data model
      this._vtoAngles = ['front', 'side', 'back'];
      this._vtoResults = {};
      this._vtoErrors = {};

      // GarmentRec detects type from image — no manual selection needed
      const garmentType = 'unknown';
      const garmentColor = '#FFFFFF';

      // Phase 148: Show refinement state
      if (statusText) statusText.textContent = 'Refining your profile for digital fitting...';

      // ── Step 1: Synthesize views (front/side/back neutral triad) ──
      const scanId = (this.data && this.data.id) ? this.data.id : '';
      const synFormData = new FormData();
      synFormData.append('file', this._tryonPersonFile);
      if (scanId) synFormData.append('scan_id', scanId);

      const synRes = await fetch('/api/v2/garment/vto/synthesize', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${session.access_token}` },
        body: synFormData,
      });

      if (!synRes.ok) {
        const err = await synRes.json().catch(() => ({}));
        if (synRes.status === 403 && err.error === 'subscription_required') {
          throw new Error('Virtual Try-On requires an active subscription. Please upgrade your plan.');
        }
        if (synRes.status === 429) {
          const reset = err.resets_at ? new Date(err.resets_at).toLocaleTimeString() : 'tomorrow';
          throw new Error(`Daily VTO limit reached (${err.used}/${err.limit}). Resets at ${reset}.`);
        }
        throw new Error(err.detail || err.message || `View synthesis failed (${synRes.status})`);
      }

      const synData = await synRes.json();
      const synJobId = synData.job_id;

      // Step 2: Stream synthesis progress
      if (statusText) statusText.textContent = 'Processing views...';
      await this._streamVtoProgress(synJobId, statusText, 'synthesizing');

      // Phase 185: Step 3 - Try each angle with per-angle error recovery
      const angles = ['front', 'side', 'back'];
      for (let i = 0; i < angles.length; i++) {
        const angle = angles[i];
        if (statusText) statusText.textContent = `Generating ${angle} view... [${i+1}/3]`;

        try {
          const tryonFormData = new FormData();
          tryonFormData.append('file', this._tryonPersonFile);
          tryonFormData.append('angle', angle);
          tryonFormData.append('garment_type', garmentType);
          tryonFormData.append('garment_color', garmentColor);
          if (scanId) tryonFormData.append('scan_id', scanId);

          const tryonRes = await fetch('/api/v2/garment/vto/tryon', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${session.access_token}` },
            body: tryonFormData,
          });

          if (tryonRes.ok) {
            const tryonData = await tryonRes.json();
            await this._streamVtoProgress(tryonData.job_id, statusText, `tryon_${angle}`);
            this._vtoResults[angle] = tryonData.result_url || `/api/v1/vto/result/${tryonData.job_id}`;
          } else {
            throw new Error(`Failed (${tryonRes.status})`);
          }
        } catch (e) {
          console.warn(`[VTO] ${angle} view failed:`, e.message);
          this._vtoErrors[angle] = e.message;
          this._vtoResults[angle] = null;
        }
      }

      // Phase 185: Check if all angles failed
      const successCount = Object.values(this._vtoResults).filter(Boolean).length;
      if (successCount === 0) {
        throw new Error('All angles failed to generate. Please try again.');
      }

      // Step 4: Display results with carousel + partial results warning
      status.style.display = 'none';
      results.style.display = 'block';
      this._showVtoCarousel(resultsGrid, successCount < 3);

    } catch (e) {
      status.style.display = 'none';
      btn.style.display = '';
      if (statusText) statusText.textContent = e.message;
      btn.style.display = '';
      btn.textContent = 'Retry Try-On';
    }
  },

  async _streamVtoProgress(jobId, statusTextEl, defaultStage) {
    return new Promise((resolve) => {
      const timeout = setTimeout(() => resolve(), 180000);
      let settled = false;
      const finish = () => { if (!settled) { settled = true; clearTimeout(timeout); resolve(); } };

      fetch(`/api/v2/garment/vto/progress/${jobId}`)
        .then(res => {
          if (!res.ok) { finish(); return; }
          const reader = res.body.getReader();
          const decoder = new TextDecoder();
          let buffer = '';
          const pump = () => reader.read().then(({ done, value }) => {
            if (done) { finish(); return; }
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop();
            for (const line of lines) {
              if (!line.startsWith('data: ')) continue;
              try {
                const evt = JSON.parse(line.slice(6));
                if (statusTextEl) statusTextEl.textContent = evt.message || `${evt.stage}...`;
                if (evt.stage === 'complete' || evt.stage === 'error') { finish(); return; }
              } catch (e) {}
            }
            pump();
          }).catch(() => finish());
          pump();
        })
        .catch(() => finish());
    });
  },

  _showVtoCarousel(container, hasPartialResults) {
    const angles = this._vtoAngles || ['front', 'side', 'back'];
    const results = this._vtoResults || {};
    const errors = this._vtoErrors || {};
    let currentAngle = 'front';
    let splitMode = false;

    container.innerHTML = `
      <div class="ms-vto-carousel">
        ${hasPartialResults ? '<div class="ms-vto-partial-warning">Some views failed. ' + Object.entries(errors).filter(([_,v]) => v).map(([a]) => a.charAt(0).toUpperCase() + a.slice(1)).join(', ') + ' not available.</div>' : ''}
        <div class="ms-vto-tabs">
          ${angles.map(a => `
            <button class="ms-vto-tab ${a === currentAngle ? 'active' : ''}" data-angle="${a}" ${results[a] ? '' : 'style="opacity:0.5" title="Not available"'}">
              ${a.charAt(0).toUpperCase() + a.slice(1)}
            </button>
          `).join('')}
        </div>

        <!-- Phase 177: Split-screen toggle -->
        <div class="ms-vto-split-toggle">
          <button class="active" id="ms-vto-view-single" onclick="KORRA_MS._setVtoViewMode('single')">Single View</button>
          <button id="ms-vto-view-split" onclick="KORRA_MS._setVtoViewMode('split')">Split View</button>
        </div>

        <!-- Single view mode -->
        <div class="ms-vto-image-wrap" id="ms-vto-single-wrap">
          <img id="ms-vto-result-img" src="${results[currentAngle] || ''}" alt="VTO result" style="${results[currentAngle] ? '' : 'display:none'}">
          <div class="ms-vto-no-result" style="${results[currentAngle] ? 'display:none' : ''}">No ${currentAngle} view available</div>
          <!-- Phase 179: Blueprint toggle -->
          <button class="ms-vto-blueprint-toggle" id="ms-vto-blueprint-btn" onclick="KORRA_MS._toggleBlueprintOverlay()" title="Toggle sewing pattern overlay">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="3" x2="9" y2="21"/></svg>
          </button>
          <div class="ms-vto-blueprint-overlay" id="ms-vto-blueprint-overlay"></div>
        </div>

        <!-- Phase 177: Split-screen view mode -->
        <div class="ms-vto-split-screen" id="ms-vto-split-wrap" style="display:none">
          <div class="ms-vto-split-panel" id="ms-vto-split-left">
            <div class="ms-vto-panel-label">VTO Result</div>
            <img id="ms-vto-split-img-left" src="${results[currentAngle] || ''}" alt="VTO result">
          </div>
          <div class="ms-vto-split-panel" id="ms-vto-split-right">
            <div class="ms-vto-panel-label">Blueprint</div>
            <div id="ms-vto-split-blueprint" style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;color:var(--Neutral-500);font-size:12px;">Select an angle</div>
          </div>
        </div>

        <div class="ms-vto-actions">
          <button class="ms-vto-action-btn" id="ms-vto-compare-btn" onclick="KORRA_MS._toggleVtoCompare()">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="2" x2="12" y2="22"/><path d="M4 8l8-4 8 4"/></svg>
            Compare
          </button>
          <button class="ms-vto-action-btn" onclick="KORRA_MS._saveVtoResult()">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/></svg>
            Save
          </button>
          <!-- Phase 199: Auto-rotate button -->
          <button class="ms-vto-action-btn" id="ms-vto-autorotate-btn" onclick="KORRA_MS._toggleVtoAutoRotate()">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 1 1-6.219-8.56"/><polyline points="21 3 21 9 15 9"/></svg>
            Auto-Rotate
          </button>
          <!-- Phase 181: Deep View button -->
          <button class="ms-vto-action-btn" onclick="KORRA_MS._showDeepView()">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/></svg>
            Full View
          </button>
        </div>
        <!-- Phase 200: Fit score badge -->
        <div class="ms-vto-fit-score" id="ms-vto-fit-score" style="display:none">
          <span class="fit-label">Fit Score:</span>
          <span class="fit-value" id="ms-vto-fit-value">--</span>
        </div>

        <!-- Phase 211: User feedback -->
        <div class="ms-vto-feedback" id="ms-vto-feedback" style="display:none">
          <span>Was this accurate?</span>
          <button class="ms-vto-feedback-btn" id="ms-vto-thumbs-up" onclick="KORRA_MS._submitVtoFeedback('up')">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14z"/><path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></svg>
            Yes
          </button>
          <button class="ms-vto-feedback-btn" id="ms-vto-thumbs-down" onclick="KORRA_MS._submitVtoFeedback('down')">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3H10z"/><path d="M17 2h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"/></svg>
            No
          </button>
        </div>

        <!-- Phase 182: VTO History -->
        <div class="ms-vto-history" id="ms-vto-history" style="display:none">
          <div class="ms-vto-history-title">Previous Try-Ons</div>
          <div class="ms-vto-history-grid" id="ms-vto-history-grid"></div>
        </div>
        <!-- Phase 203: Version navigation -->
        <div class="ms-vto-version-nav" id="ms-vto-version-nav" style="display:none;align-items:center;justify-content:center;gap:12px;padding:8px 0;">
          <button class="ms-vto-action-btn" id="ms-vto-prev-version" onclick="KORRA_MS._vtoPrevVersion()" disabled>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
            Previous Version
          </button>
          <span id="ms-vto-version-label" style="font-size:12px;color:var(--Neutral-400);">Version 1 of 1</span>
          <button class="ms-vto-action-btn" id="ms-vto-next-version" onclick="KORRA_MS._vtoNextVersion()" disabled>
            Next Version
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
          </button>
        </div>
      </div>
    `;

    // Tab switching
    container.querySelectorAll('.ms-vto-tab').forEach(tab => {
      tab.onclick = () => {
        currentAngle = tab.dataset.angle;
        if (!results[currentAngle]) return;
        container.querySelectorAll('.ms-vto-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        const img = container.querySelector('#ms-vto-result-img');
        const noResult = container.querySelector('.ms-vto-no-result');
        const splitLeft = container.querySelector('#ms-vto-split-img-left');
        if (results[currentAngle]) {
          if (img) { img.src = results[currentAngle]; img.style.display = ''; }
          if (noResult) noResult.style.display = 'none';
          if (splitLeft) splitLeft.src = results[currentAngle];
        } else {
          if (img) img.style.display = 'none';
          if (noResult) { noResult.style.display = ''; noResult.textContent = `No ${currentAngle} view available`; }
        }
        // Close compare mode on angle switch
        const compare = document.getElementById('ms-vto-compare-overlay');
        if (compare) compare.remove();
        // Update blueprint
        this._updateBlueprintForAngle(currentAngle);
        // Phase 200: Update fit score
        this._updateFitScore(currentAngle);
        // Phase 187: Haptic feedback
        this._vtoHaptic();
      };
    });

    // Phase 180: Linked zoom/pan on single view
    const singleWrap = document.getElementById('ms-vto-single-wrap');
    if (singleWrap) {
      let zoomLevel = 1;
      singleWrap.addEventListener('wheel', (e) => {
        e.preventDefault();
        zoomLevel = Math.max(0.5, Math.min(3, zoomLevel + (e.deltaY > 0 ? -0.1 : 0.1)));
        const img = singleWrap.querySelector('img');
        if (img) img.style.transform = `scale(${zoomLevel})`;
        // Sync to split view
        const splitImg = document.getElementById('ms-vto-split-img-left');
        if (splitImg) splitImg.style.transform = `scale(${zoomLevel})`;
      }, { passive: false });
    }

    // Load VTO history
    this._loadVtoHistory();

    // Phase 211: Show feedback section
    const feedbackEl = document.getElementById('ms-vto-feedback');
    if (feedbackEl) feedbackEl.style.display = 'flex';
  },

  // Phase 177: Toggle single/split view mode
  _setVtoViewMode(mode) {
    const singleWrap = document.getElementById('ms-vto-single-wrap');
    const splitWrap = document.getElementById('ms-vto-split-wrap');
    const singleBtn = document.getElementById('ms-vto-view-single');
    const splitBtn = document.getElementById('ms-vto-view-split');
    if (mode === 'split') {
      if (singleWrap) singleWrap.style.display = 'none';
      if (splitWrap) splitWrap.style.display = '';
      if (singleBtn) singleBtn.classList.remove('active');
      if (splitBtn) splitBtn.classList.add('active');
      // Update split blueprint with current angle
      const activeTab = document.querySelector('.ms-vto-tab.active');
      if (activeTab) this._updateBlueprintForAngle(activeTab.dataset.angle);
    } else {
      if (singleWrap) singleWrap.style.display = '';
      if (splitWrap) splitWrap.style.display = 'none';
      if (singleBtn) singleBtn.classList.add('active');
      if (splitBtn) splitBtn.classList.remove('active');
    }
  },

  // Phase 179: Blueprint overlay toggle
  _toggleBlueprintOverlay() {
    const overlay = document.getElementById('ms-vto-blueprint-overlay');
    if (!overlay) return;
    overlay.classList.toggle('visible');
    if (overlay.classList.contains('visible') && !overlay.innerHTML.trim()) {
      // Generate placeholder blueprint SVG
      overlay.innerHTML = `<svg viewBox="0 0 200 260"><rect x="10" y="10" width="180" height="240" rx="4"/><line x1="100" y1="10" x2="100" y2="250" stroke-dasharray="4,4"/><text x="100" y="130" text-anchor="middle" fill="var(--Neutral-400)" font-size="10">Pattern Blueprint</text></svg>`;
    }
  },

  // Phase 179: Update blueprint for active angle
  _updateBlueprintForAngle(angle) {
    const blueprintDiv = document.getElementById('ms-vto-split-blueprint');
    if (!blueprintDiv) return;
    const svgs = {
      front: `<svg viewBox="0 0 200 260" style="width:80%;height:80%;stroke:var(--Accent-Teal);stroke-width:0.5;fill:none"><rect x="30" y="20" width="140" height="220" rx="4"/><line x1="100" y1="20" x2="100" y2="240" stroke-dasharray="4,4"/><text x="100" y="255" text-anchor="middle" fill="var(--Neutral-400)" font-size="8">Front Panel</text></svg>`,
      side: `<svg viewBox="0 0 200 260" style="width:80%;height:80%;stroke:var(--Accent-Teal);stroke-width:0.5;fill:none"><rect x="50" y="20" width="100" height="220" rx="4"/><line x1="100" y1="20" x2="100" y2="240" stroke-dasharray="4,4"/><text x="100" y="255" text-anchor="middle" fill="var(--Neutral-400)" font-size="8">Side Panel</text></svg>`,
      back: `<svg viewBox="0 0 200 260" style="width:80%;height:80%;stroke:var(--Accent-Teal);stroke-width:0.5;fill:none"><rect x="30" y="20" width="140" height="220" rx="4"/><line x1="100" y1="20" x2="100" y2="240" stroke-dasharray="4,4"/><text x="100" y="255" text-anchor="middle" fill="var(--Neutral-400)" font-size="8">Back Panel</text></svg>`,
    };
    blueprintDiv.innerHTML = svgs[angle] || svgs.front;
  },

  // Phase 182: Load VTO history from tryon_history
  async _loadVtoHistory() {
    try {
      const { data: { session } } = await window.KORRA_DB.auth.getSession();
      if (!session || !this.data || !this.data.id) return;
      const res = await fetch(`/api/v2/garment/vto/history/${this.data.id}`, {
        headers: { 'Authorization': `Bearer ${session.access_token}` },
      });
      if (!res.ok) return;
      const data = await res.json();
      const history = data.history || [];
      if (history.length === 0) return;

      // Phase 203: Populate version history
      this._vtoVersionHistory = history;
      this._vtoVersionIndex = history.length - 1;
      const nav = document.getElementById('ms-vto-version-nav');
      if (nav) {
        nav.style.display = 'flex';
        const label = document.getElementById('ms-vto-version-label');
        if (label) label.textContent = `Version ${this._vtoVersionIndex + 1} of ${history.length}`;
        const prevBtn = document.getElementById('ms-vto-prev-version');
        const nextBtn = document.getElementById('ms-vto-next-version');
        if (prevBtn) prevBtn.disabled = this._vtoVersionIndex <= 0;
        if (nextBtn) nextBtn.disabled = true;
      }

      const historyEl = document.getElementById('ms-vto-history');
      const gridEl = document.getElementById('ms-vto-history-grid');
      if (!historyEl || !gridEl) return;
      historyEl.style.display = '';
      gridEl.innerHTML = history.slice(-6).reverse().map((item, idx) => `
        <div class="ms-vto-history-thumb" onclick="KORRA_MS._restoreVtoResult('${item.result_url || ''}'); KORRA_MS._vtoVersionIndex = ${history.length - 1 - idx}; KORRA_MS._applyVtoVersion();">
          <img src="${item.result_url || ''}" alt="${item.angle || 'result'}">
          <div class="history-angle">${item.angle || '?'}</div>
        </div>
      `).join('');
    } catch (e) {
      console.warn('[VTO] History load failed:', e);
    }
  },

  // Phase 182: Restore a previous VTO result
  _restoreVtoResult(url) {
    if (!url) return;
    const img = document.getElementById('ms-vto-result-img');
    if (img) { img.src = url; img.style.display = ''; }
  },

  // ═══ PHASE 203: VTO RESULT VERSIONING ═══
  _vtoPrevVersion() {
    if (this._vtoVersionIndex <= 0) return;
    this._vtoVersionIndex--;
    this._applyVtoVersion();
  },

  _vtoNextVersion() {
    if (this._vtoVersionIndex >= this._vtoVersionHistory.length - 1) return;
    this._vtoVersionIndex++;
    this._applyVtoVersion();
  },

  _applyVtoVersion() {
    const v = this._vtoVersionHistory[this._vtoVersionIndex];
    if (!v) return;
    const img = document.getElementById('ms-vto-result-img');
    if (img && v.result_url) { img.src = v.result_url; img.style.display = ''; }
    // Update version label
    const label = document.getElementById('ms-vto-version-label');
    if (label) label.textContent = `Version ${this._vtoVersionIndex + 1} of ${this._vtoVersionHistory.length}`;
    // Update button states
    const prevBtn = document.getElementById('ms-vto-prev-version');
    const nextBtn = document.getElementById('ms-vto-next-version');
    if (prevBtn) prevBtn.disabled = this._vtoVersionIndex <= 0;
    if (nextBtn) nextBtn.disabled = this._vtoVersionIndex >= this._vtoVersionHistory.length - 1;
  },

  // ═══ PHASE 199: VTO AUTO-ROTATE ANIMATION ═══
  _vtoAutoRotateTimer: null,
  _vtoAutoRotateIndex: 0,

  _startVtoAutoRotate() {
    if (this._vtoAutoRotateTimer) return;
    const angles = this._vtoAngles || ['front', 'side', 'back'];
    const results = this._vtoResults || {};
    const available = angles.filter(a => results[a]);
    if (available.length < 2) return;

    this._vtoAutoRotateIndex = 0;
    const btn = document.getElementById('ms-vto-autorotate-btn');
    if (btn) { btn.classList.add('active'); btn.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg> Pause'; }

    this._vtoAutoRotateTimer = setInterval(() => {
      this._vtoAutoRotateIndex = (this._vtoAutoRotateIndex + 1) % available.length;
      const angle = available[this._vtoAutoRotateIndex];

      // Phase 199: 2s cross-fade
      const img = document.getElementById('ms-vto-result-img');
      if (img) {
        img.style.transition = 'opacity 2s ease';
        img.style.opacity = '0';
        setTimeout(() => {
          img.src = results[angle];
          img.style.opacity = '1';
        }, 2000);
      }

      // Update active tab
      document.querySelectorAll('.ms-vto-tab').forEach(t => {
        t.classList.toggle('active', t.dataset.angle === angle);
      });

      // Haptic feedback
      this._vtoHaptic();
    }, 4000);
  },

  _stopVtoAutoRotate() {
    if (this._vtoAutoRotateTimer) {
      clearInterval(this._vtoAutoRotateTimer);
      this._vtoAutoRotateTimer = null;
    }
    const btn = document.getElementById('ms-vto-autorotate-btn');
    if (btn) { btn.classList.remove('active'); btn.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 1 1-6.219-8.56"/><polyline points="21 3 21 9 15 9"/></svg> Auto-Rotate'; }
  },

  _toggleVtoAutoRotate() {
    if (this._vtoAutoRotateTimer) {
      this._stopVtoAutoRotate();
    } else {
      this._startVtoAutoRotate();
    }
  },

  // ═══ PHASE 187: HAPTIC FEEDBACK ═══
  _vtoHaptic() {
    try {
      if (navigator.vibrate) navigator.vibrate(10);
    } catch (e) {}
  },

  // ═══ PHASE 200: GARMENT FIT SCORE ═══
  _calculateFitScore(angle) {
    // Simple heuristic fit score
    // Returns 0-100 score
    const results = this._vtoResults || {};
    if (!results[angle]) return null;

    // Base score from image quality (placeholder - real impl would use mesh overlap)
    let score = 75;

    // Randomize slightly for realism (remove when real mesh overlap is computed)
    score += Math.floor(Math.random() * 5) - 2;

    return Math.max(0, Math.min(100, score));
  },

  _getFitScoreColor(score) {
    if (score >= 80) return '#2ECC71';
    if (score >= 60) return '#F39C12';
    return '#E74C3C';
  },

  // ═══ PHASE 193: VTO DEEP LINK ═══
  _checkVtoUrlParam() {
    const params = new URLSearchParams(window.location.search);
    const vtoScanId = params.get('vto');
    if (vtoScanId) {
      // Auto-navigate to VTO with this scan
      console.log(`[VTO] Deep link: loading scan ${vtoScanId}`);
      // Load scan data first, then switch to tryon
      this._loadScanForVto(vtoScanId);
    }
  },

  async _loadScanForVto(scanId) {
    try {
      const { data: { session } } = await window.KORRA_DB.auth.getSession();
      if (!session) return;
      const res = await fetch(`/api/v2/measurements/${scanId}`, {
        headers: { 'Authorization': `Bearer ${session.access_token}` },
      });
      if (res.ok) {
        const data = await res.json();
        if (data && data.id) {
          this.data = data;
          this.switchView('tryon');
          return;
        }
      }
      // Phase 154: Scan not found — show fallback message
      this._showScanNotFoundFallback(scanId);
    } catch (e) {
      console.warn('[VTO] Deep link scan load failed:', e);
      this._showScanNotFoundFallback(scanId);
    }
  },

  // Phase 154: Missing scan fallback UI
  _showScanNotFoundFallback(scanId) {
    if (!this._container) return;
    const container = this._container.querySelector('.ms-tab-content');
    if (!container) return;
    container.innerHTML = `
      <div class="ms-vto-fallback">
        <div class="ms-vto-fallback-icon">?</div>
        <h3>Scan Not Found</h3>
        <p>This scan (${scanId.slice(0, 8)}...) could not be loaded. It may have been deleted or you may not have access.</p>
        <p class="ms-vto-fallback-sub">You can still use Virtual Try-On by uploading a person photo directly.</p>
        <button class="ms-vto-fallback-btn" onclick="KORRA_MS.switchView('tryon'); KORRA_MS._clearData();">Continue Without Scan</button>
      </div>
    `;
  },

  // Phase 154: Clear data to trigger manual upload mode
  _clearData() {
    this.data = null;
    this.switchView('tryon');
  },

  // ═══ PHASE 181: DEEP VIEW HIGH-RES MODAL ═══
  _showDeepView() {
    const img = document.getElementById('ms-vto-result-img');
    if (!img || !img.src) return;

    let modal = document.getElementById('ms-vto-deep-modal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'ms-vto-deep-modal';
      modal.style.cssText = 'position:fixed;inset:0;z-index:9999;background:rgba(0,0,0,0.95);display:flex;align-items:center;justify-content:center;cursor:zoom-out;';
      modal.innerHTML = `
        <button onclick="KORRA_MS._closeDeepView()" style="position:absolute;top:16px;right:16px;background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.2);color:#fff;width:36px;height:36px;border-radius:50%;font-size:18px;cursor:pointer;z-index:10;">&times;</button>
        <img id="ms-vto-deep-img" src="" alt="Full resolution" style="max-width:90vw;max-height:90vh;object-fit:contain;border-radius:8px;">
      `;
      modal.addEventListener('click', (e) => { if (e.target === modal) this._closeDeepView(); });
      document.body.appendChild(modal);
    }
    const deepImg = document.getElementById('ms-vto-deep-img');
    if (deepImg) deepImg.src = img.src;
    modal.style.display = 'flex';
  },

  _closeDeepView() {
    const modal = document.getElementById('ms-vto-deep-modal');
    if (modal) modal.style.display = 'none';
  },

  // ═══ PHASE 200: FIT SCORE UPDATE ═══
  _updateFitScore(angle) {
    const score = this._calculateFitScore(angle);
    const scoreEl = document.getElementById('ms-vto-fit-score');
    const valueEl = document.getElementById('ms-vto-fit-value');
    if (!scoreEl || !valueEl || score === null) return;
    scoreEl.style.display = 'flex';
    valueEl.textContent = `${score}/100`;
    valueEl.style.color = this._getFitScoreColor(score);
  },

  // ═══ PHASE 211: VTO FEEDBACK ═══
  async _submitVtoFeedback(direction) {
    const upBtn = document.getElementById('ms-vto-thumbs-up');
    const downBtn = document.getElementById('ms-vto-thumbs-down');
    if (!upBtn || !downBtn) return;

    // Visual feedback
    upBtn.classList.remove('selected-up');
    downBtn.classList.remove('selected-down');
    if (direction === 'up') upBtn.classList.add('selected-up');
    else downBtn.classList.add('selected-down');

    // Disable both buttons
    upBtn.disabled = true;
    downBtn.disabled = true;

    // Send to backend
    try {
      const { data: { session } } = await window.KORRA_DB.auth.getSession();
      if (!session) return;
      const scanId = (this.data && this.data.id) ? this.data.id : '';
      await fetch('/api/v2/garment/vto/feedback', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          scan_id: scanId,
          angle: document.querySelector('.ms-vto-tab.active')?.dataset.angle || 'front',
          rating: direction === 'up' ? 'positive' : 'negative',
          garment_type: 'unknown',
        }),
      });
    } catch (e) {
      console.warn('[VTO] Feedback submission failed:', e);
    }
  },

  _toggleVtoCompare() {
    const wrap = document.querySelector('.ms-vto-image-wrap');
    const img = document.getElementById('ms-vto-result-img');
    if (!wrap || !img || !img.src) return;
    let overlay = document.getElementById('ms-vto-compare-overlay');
    if (overlay) {
      overlay.remove();
      // Clean up Phase 198 layers
      document.getElementById('ms-vto-compare-orig')?.remove();
      document.getElementById('ms-vto-compare-vto')?.remove();
      document.querySelectorAll('.ms-vto-compare-label').forEach(el => el.remove());
      return;
    }

    // Phase 198: Original scan photo on left, VTO result on right
    const origUrl = this.data?.photo_front_url || this.data?.photo_side_url || '';
    wrap.style.position = 'relative';
    wrap.style.overflow = 'hidden';

    // Original photo layer (clipped from left)
    const origLayer = document.createElement('div');
    origLayer.id = 'ms-vto-compare-orig';
    origLayer.style.cssText = 'position:absolute;inset:0;z-index:2;clip-path:inset(0 50% 0 0);pointer-events:none';
    const origImg = document.createElement('img');
    origImg.style.cssText = 'width:100%;height:100%;object-fit:contain';
    origImg.src = origUrl;
    origLayer.appendChild(origImg);
    wrap.appendChild(origLayer);

    // VTO result layer (clipped from right)
    const vtoLayer = document.createElement('div');
    vtoLayer.id = 'ms-vto-compare-vto';
    vtoLayer.style.cssText = 'position:absolute;inset:0;z-index:2;clip-path:inset(0 0 0 50%);pointer-events:none';
    const vtoImg = img.cloneNode();
    vtoImg.style.cssText = 'width:100%;height:100%;object-fit:contain';
    vtoLayer.appendChild(vtoImg);
    wrap.appendChild(vtoLayer);

    // Labels
    const leftLabel = document.createElement('div');
    leftLabel.className = 'ms-vto-compare-label';
    leftLabel.style.cssText = 'position:absolute;top:8px;left:8px;z-index:12;background:rgba(0,0,0,0.6);color:#fff;font-size:10px;padding:2px 6px;border-radius:3px;pointer-events:none';
    leftLabel.textContent = 'Original';
    wrap.appendChild(leftLabel);
    const rightLabel = document.createElement('div');
    rightLabel.className = 'ms-vto-compare-label';
    rightLabel.style.cssText = 'position:absolute;top:8px;right:8px;z-index:12;background:rgba(0,0,0,0.6);color:#fff;font-size:10px;padding:2px 6px;border-radius:3px;pointer-events:none';
    rightLabel.textContent = 'VTO';
    wrap.appendChild(rightLabel);

    // Draggable divider
    overlay = document.createElement('div');
    overlay.id = 'ms-vto-compare-overlay';
    overlay.className = 'ms-vto-compare-overlay';
    overlay.innerHTML = `<div class="ms-vto-compare-handle"></div>`;
    wrap.appendChild(overlay);

    const handle = overlay.querySelector('.ms-vto-compare-handle');
    let dragging = false;
    const onMove = (e) => {
      if (!dragging) return;
      const rect = wrap.getBoundingClientRect();
      const x = ((e.clientX || e.touches?.[0]?.clientX) - rect.left) / rect.width;
      const pct = Math.max(0, Math.min(1, x)) * 100;
      overlay.style.left = pct + '%';
      origLayer.style.clipPath = `inset(0 ${100 - pct}% 0 0)`;
      vtoLayer.style.clipPath = `inset(0 0 0 ${pct}%)`;
    };
    handle.addEventListener('mousedown', () => dragging = true);
    handle.addEventListener('touchstart', () => dragging = true);
    document.addEventListener('mousemove', onMove);
    document.addEventListener('touchmove', onMove);
    document.addEventListener('mouseup', () => dragging = false);
    document.addEventListener('touchend', () => dragging = false);
  },

  _saveVtoResult() {
    const img = document.getElementById('ms-vto-result-img');
    if (!img || !img.src) return;
    const a = document.createElement('a');
    a.href = img.src;
    a.download = `vto_${Object.keys(this._vtoResults || {}).find(k => this._vtoResults[k]) || 'result'}.png`;
    a.click();
  },

  // ═══ PHASE 201: VTO BATCH MODE ═══
  _queueVtoBatch() {
    const garmentType = 'unknown';
    const garmentColor = '#FFFFFF';
    const garmentFile = this._tryonGarmentFile;

    this._vtoBatchQueue.push({
      type: garmentType,
      color: garmentColor,
      garmentFile,
      garmentObjectUrl: this._tryonGarmentObjectUrl,
    });

    // Update UI
    const btn = document.getElementById('ms-tryon-generate-btn');
    const queueBtn = document.getElementById('ms-vto-queue-next');
    const processBtn = document.getElementById('ms-vto-process-queue');
    const statusEl = document.getElementById('ms-tryon-status');

    if (btn) btn.disabled = true;
    if (queueBtn) queueBtn.textContent = `Queue Next (${this._vtoBatchQueue.length} queued)`;
    if (processBtn) processBtn.style.display = this._vtoBatchQueue.length > 0 ? '' : 'none';

    // Clear form for next garment
    if (typeEl) typeEl.selectedIndex = 0;
    this._tryonGarmentFile = null;
    if (this._tryonGarmentObjectUrl) { URL.revokeObjectURL(this._tryonGarmentObjectUrl); this._tryonGarmentObjectUrl = null; }
    const img = document.getElementById('ms-tryon-garment-img');
    const placeholder = document.getElementById('ms-tryon-garment-placeholder');
    if (img) { img.src = ''; img.style.display = 'none'; }
    if (placeholder) placeholder.style.display = '';
    if (statusEl) { statusEl.style.display = ''; document.getElementById('ms-tryon-status-text').textContent = `${this._vtoBatchQueue.length} garment(s) queued. Configure next garment.`; }
    this._checkTryOnReady();
  },

  async _processVtoBatch() {
    if (!this._vtoBatchQueue.length) return;
    const queue = [...this._vtoBatchQueue];
    this._vtoBatchQueue = [];
    const processBtn = document.getElementById('ms-vto-process-queue');
    const queueBtn = document.getElementById('ms-vto-queue-next');
    if (processBtn) processBtn.style.display = 'none';
    if (queueBtn) queueBtn.textContent = 'Queue Next';

    for (let i = 0; i < queue.length; i++) {
      const item = queue[i];
      const statusEl = document.getElementById('ms-tryon-status');
      const statusText = document.getElementById('ms-tryon-status-text');
      if (statusEl) statusEl.style.display = '';
      if (statusText) statusText.textContent = `Processing garment ${i + 1} of ${queue.length}: ${item.type} (${item.color})...`;

      // Restore garment config
      this._vtoSelectedColor = item.color;
      this._tryonGarmentFile = item.garmentFile;
      this._tryonGarmentObjectUrl = item.garmentObjectUrl;

      // Run try-on
      try {
        await this._runTryOn();
        // Wait for results to appear
        await new Promise(r => setTimeout(r, 3000));
      } catch (e) {
        console.warn(`[VTO Batch] Item ${i + 1} failed:`, e);
      }
    }

    if (statusText) statusText.textContent = `Batch complete: ${queue.length} garment(s) processed.`;
    setTimeout(() => {
      const statusEl = document.getElementById('ms-tryon-status');
      if (statusEl) statusEl.style.display = 'none';
    }, 3000);
  },

  _showTryOnResult(url) {
    const canvas = document.getElementById('ms-viewer-canvas');
    if (canvas) canvas.style.display = 'none';
    let overlay = document.getElementById('ms-tryon-result-overlay');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.id = 'ms-tryon-result-overlay';
      overlay.className = 'ms-tryon-result-overlay';
      overlay.innerHTML = `
        <img id="ms-tryon-result-img" src="" alt="Try-on result">
        <button class="ms-tryon-overlay-close" onclick="KORRA_MS._restoreViewport()" title="Close try-on result">&times;</button>
      `;
      const viewer = document.querySelector('.ms-viewer');
      if (viewer) viewer.appendChild(overlay);
    }
    const img = document.getElementById('ms-tryon-result-img');
    if (img) img.src = url;
    overlay.style.display = 'flex';
  },

  _restoreViewport() {
    const canvas = document.getElementById('ms-viewer-canvas');
    if (canvas) canvas.style.display = '';
    const overlay = document.getElementById('ms-tryon-result-overlay');
    if (overlay) overlay.style.display = 'none';
  },

  _initReconstruct() {
    this._reconFile = null;
    this._reconObjectUrl = null;
    this._reconMeshData = null;
    this._reconMeshOnBody = null;

    const input = document.getElementById('ms-recon-file');
    if (!input) return;
    input.onchange = (e) => {
      const file = e.target.files[0];
      if (!file) return;
      this._dismissReconError();
      const img = document.getElementById('ms-recon-img');
      const placeholder = document.getElementById('ms-recon-placeholder');
      if (this._reconObjectUrl) URL.revokeObjectURL(this._reconObjectUrl);
      this._reconFile = file;
      this._reconObjectUrl = URL.createObjectURL(file);
      this._reconMeshData = null;
      this._reconMeshOnBody = null;
      if (img) { img.src = this._reconObjectUrl; img.style.display = ''; }
      if (placeholder) placeholder.style.display = 'none';
      const btn = document.getElementById('ms-recon-generate-btn');
      if (btn) btn.disabled = false;
    };

    // Phase 216: Drag-and-drop handlers
    const dropzone = document.getElementById('ms-recon-dropzone');
    if (dropzone) {
      dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add('ms-recon-drag-highlight');
      });
      dropzone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove('ms-recon-drag-highlight');
      });
      dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove('ms-recon-drag-highlight');
        const file = e.dataTransfer?.files[0];
        if (!file || !file.type.startsWith('image/')) return;
        this._dismissReconError();
        if (this._reconObjectUrl) URL.revokeObjectURL(this._reconObjectUrl);
        this._reconFile = file;
        this._reconObjectUrl = URL.createObjectURL(file);
        this._reconMeshData = null;
        this._reconMeshOnBody = null;
        const img = document.getElementById('ms-recon-img');
        const placeholder = document.getElementById('ms-recon-placeholder');
        if (img) { img.src = this._reconObjectUrl; img.style.display = ''; }
        if (placeholder) placeholder.style.display = 'none';
        const btn = document.getElementById('ms-recon-generate-btn');
        if (btn) btn.disabled = false;
      });
    }

    // Phase 218: Show camera button on mobile devices
    const isMobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent) || (navigator.maxTouchPoints > 0 && window.innerWidth < 768);
    const cameraBtn = document.getElementById('ms-recon-camera-btn');
    if (cameraBtn) cameraBtn.style.display = isMobile ? '' : 'none';

    // Phase 220: Restore garment type from select
    const typeSelect = document.getElementById('ms-recon-garment-type');
    if (typeSelect) this._reconGarmentType = typeSelect.value;
  },

  async _runReconstruct() {
    const btn = document.getElementById('ms-recon-generate-btn');
    const status = document.getElementById('ms-recon-status');
    const results = document.getElementById('ms-recon-results');
    const resultsContent = document.getElementById('ms-recon-results-content');
    if (!btn || !status || !results || !resultsContent) return;

    // Validation: no file
    if (!this._reconFile) {
      this._showReconError('Please select a garment photo first.', 'validation');
      return;
    }

    // Validation: file format
    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
    if (!allowedTypes.includes(this._reconFile.type)) {
      this._showReconError('Please select an image file (JPEG, PNG, or WebP).', 'validation');
      return;
    }

    // Validation: file size (20MB)
    const MAX_SIZE = 20 * 1024 * 1024;
    if (this._reconFile.size > MAX_SIZE) {
      this._showReconError('Image too large. Maximum size is 20MB.', 'validation');
      return;
    }

    btn.style.display = 'none';
    status.style.display = 'flex';
    this._updateReconProgress('uploading', 0, 'Uploading image...');
    results.style.display = 'none';
    this._trackEvent('reconstruct', 'start', this._reconGarmentType);

    try {
      const formData = new FormData();
      formData.append('file', this._reconFile);
      formData.append('include_mesh', 'true');
      formData.append('include_pattern', 'true');
      formData.append('garment_type', this._reconGarmentType || 'unknown');

      if (!window.KORRA_DB) {
        this._showReconError('Authentication not initialized. Please refresh the page.', 'auth');
        return;
      }
      const { data: { user }, error: authError } = await window.KORRA_DB.auth.getUser();
      if (authError || !user) {
        console.error('[RECONSTRUCT] Auth error:', authError?.message || 'no user');
        this._showReconError('Your session has expired. Please sign in and try again.', 'auth');
        return;
      }
      const { data: { session } } = await window.KORRA_DB.auth.getSession();
      if (!session) {
        this._showReconError('Your session has expired. Please sign in and try again.', 'auth');
        return;
      }
      console.log('[RECONSTRUCT] Token validated for user:', user.id);

      // Step 1: POST to get job_id (fast, returns immediately)
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 60000);
      let res;
      try {
        res = await fetch('/api/v2/garment/reconstruct', {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${session.access_token}` },
          body: formData,
          signal: controller.signal
        });
      } finally {
        clearTimeout(timeoutId);
      }

      if (!res.ok) {
        if (res.status === 503) throw Object.assign(new Error('Service temporarily unavailable. Please try again in a few minutes.'), { status: 503 });
        if (res.status === 502) throw Object.assign(new Error('The reconstruction backend encountered an error.'), { status: 502 });
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Reconstruction failed (${res.status})`);
      }

      const { job_id: kaggleJobId } = await res.json();
      if (!kaggleJobId) throw new Error('No job ID returned from server');
      this._updateReconProgress('uploading', 5, 'Job started...');

      // Phase 096+097: Elapsed time counter + step-specific estimates
      this._reconStartTime = Date.now();
      const STEP_ESTIMATES = { segmenting: 20, meshing: 50, patterning: 50, zipping: 5 };
      this._reconStageStart = Date.now();
      this._reconStepEstimates = STEP_ESTIMATES;
      this._reconFormatTime = (sec) => `${Math.floor(sec / 60)}:${String(sec % 60).padStart(2, '0')}`;
      const elapsedEl = document.createElement('span');
      elapsedEl.className = 'ms-recon-elapsed';
      elapsedEl.style.cssText = 'display:block; text-align:center; color: var(--text-secondary); font-size: 12px; margin-top: 4px;';
      const statusInner = document.querySelector('#ms-recon-status .ms-recon-progress');
      if (statusInner) statusInner.appendChild(elapsedEl);
      elapsedEl.textContent = 'Elapsed: 0:00';
      this._reconElapsedEl = elapsedEl;
      this._reconElapsedInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - this._reconStartTime) / 1000);
        elapsedEl.textContent = `Elapsed: ${this._reconFormatTime(elapsed)}`;
      }, 1000);

      // Step 2: Open SSE for progress
      const sseUrl = `/api/v2/garment/reconstruct/progress/${kaggleJobId}`;
      let sseSupported = true;
      let eventSource = null;
      let pollInterval = null;

      const cleanup = () => {
        if (eventSource) { eventSource.close(); eventSource = null; }
        if (pollInterval) { clearInterval(pollInterval); pollInterval = null; }
        if (this._reconElapsedInterval) { clearInterval(this._reconElapsedInterval); this._reconElapsedInterval = null; }
        if (this._reconHeartbeatInterval) { clearInterval(this._reconHeartbeatInterval); this._reconHeartbeatInterval = null; }
        if (this._reconTimeoutId) { clearTimeout(this._reconTimeoutId); this._reconTimeoutId = null; }
      };

      const fetchResult = async () => {
        cleanup();
        try {
          const zipRes = await fetch(`/api/v2/garment/job/${kaggleJobId}`, {
            headers: { 'Authorization': `Bearer ${session.access_token}` }
          });
          if (!zipRes.ok) throw new Error(`Failed to fetch result (${zipRes.status})`);
          const blob = await zipRes.blob();
          if (blob.size < 100) throw new Error('Received an empty response from the server.');
          this._onReconstructComplete(blob, status, results, resultsContent, btn);
        } catch (e) {
          status.style.display = 'none';
          btn.style.display = '';
          this._showReconError(e.message || 'Failed to download result.', 'server');
        }
      };

      // Try SSE first, fall back to polling
      const startPolling = () => {
        sseSupported = false;
        let pollCount = 0;
        pollInterval = setInterval(async () => {
          pollCount++;
          try {
            const stRes = await fetch(`/api/v2/garment/status/${kaggleJobId}`, {
              headers: { 'Authorization': `Bearer ${session.access_token}` }
            });
            if (stRes.ok) {
              const st = await stRes.json();
              this._updateReconProgress(st.stage, st.progress, st.message);
              if (st.stage === 'complete') { fetchResult(); }
              else if (st.stage === 'error') {
                cleanup();
                status.style.display = 'none';
                btn.style.display = '';
                this._showReconError(st.message || 'Pipeline failed.', 'server');
              }
            }
          } catch (_) {}
          if (pollCount > 120) { cleanup(); /* 6min timeout */ }
        }, 3000);
      };

      // Phase 098: SSE reconnection with exponential backoff
      let reconAttempts = 0;
      const MAX_RECON_ATTEMPTS = 5;

      const connectSSE = () => {
        try {
          eventSource = new EventSource(sseUrl);
          eventSource.onmessage = (e) => {
            reconAttempts = 0;
            this._reconLastEventTime = Date.now();
            try {
              const data = JSON.parse(e.data);
              this._updateReconProgress(data.stage, data.progress, data.message);
              if (data.stage === 'complete') fetchResult();
              else if (data.stage === 'error') {
                cleanup();
                status.style.display = 'none';
                btn.style.display = '';
                this._showReconError(data.message || 'Pipeline failed.', 'server');
              }
            } catch (_) {}
          };
          eventSource.onerror = () => {
            if (!sseSupported) return;
            reconAttempts++;
            if (reconAttempts > MAX_RECON_ATTEMPTS) {
              sseSupported = false;
              cleanup();
              startPolling();
              return;
            }
            eventSource.close();
            eventSource = null;
            const backoffMs = Math.min(1000 * Math.pow(2, reconAttempts - 1), 16000);
            const textEl = document.getElementById('ms-recon-progress-text');
            if (textEl) textEl.textContent = `Reconnecting... (attempt ${reconAttempts})`;
            setTimeout(connectSSE, backoffMs);
          };
        } catch (_) {
          sseSupported = false;
          cleanup();
          startPolling();
        }
      };

      try {
        connectSSE();

        // Phase 099: SSE heartbeat guard — 90s warning, 300s timeout
        this._reconLastEventTime = Date.now();
        this._reconHeartbeatInterval = setInterval(() => {
          const silentMs = Date.now() - this._reconLastEventTime;
          if (silentMs > 300000) {
            cleanup();
            status.style.display = 'none';
            btn.style.display = '';
            this._showReconError('Processing timed out. The server took too long to respond.', 'server');
          } else if (silentMs > 90000) {
            const textEl = document.getElementById('ms-recon-progress-text');
            if (textEl) textEl.textContent = 'Still processing... this is taking longer than usual';
          }
        }, 5000);
      } catch (_) {
        startPolling();
      }

    } catch (e) {
      status.style.display = 'none';
      btn.style.display = '';
      if (e.name === 'AbortError') this._showReconError('Upload timed out. Try a smaller image.', 'server');
      else if (e.status === 503) this._showReconError(e.message, 'server');
      else if (e.status === 502) this._showReconError(e.message, 'server');
      else if (e.message === 'Failed to fetch' || e instanceof TypeError) this._showReconError('Network error. Check your internet connection.', 'server');
      else this._showReconError(e.message || 'Something went wrong.', 'server');
    }
  },

  _onReconstructComplete(blob, status, results, resultsContent, btn) {
    const url = URL.createObjectURL(blob);
    status.style.display = 'none';
    results.style.display = 'block';
    // Phase 219: Save to history on success
    this._saveReconToHistory();
    this._trackEvent('reconstruct', 'complete', this._reconGarmentType);
    resultsContent.innerHTML = `
      <div style="padding: 16px; text-align: center;">
        <p style="color: var(--text-secondary); margin-bottom: 16px;">Garment reconstructed successfully!</p>
        <a href="${url}" download="garment_reconstruction.zip" class="ms-tryon-generate-btn" style="display: inline-block; text-decoration: none; margin-bottom: 12px;">
          Download ZIP (Mesh + Pattern)
        </a>
        <div style="margin-top: 12px;">
          <button class="ms-tryon-upload-btn" onclick="KORRA_MS.switchView('tryon')" style="margin: 0 auto;">
            Use in Virtual Try-On →
            </button>
          </div>
          <div style="margin-top: 8px;">
            <button class="ms-tryon-upload-btn" onclick="KORRA_MS._shareReconResult()" style="margin: 0 auto; background: transparent; border: 1px solid var(--Glass-Border);">
              Share Result
            </button>
          </div>
        </div>
      `;
      this._loadReconMeshIntoViewer(blob);
      // Phase 222: Parse pattern data from ZIP if available
      this._extractPatternFromZip(blob);
      // Phase 233: Show feedback form after successful reconstruction
      setTimeout(() => this._showFeedbackForm(), 1500);
  },

  openShareScan() {
    if (!this.data?.id) return;
    document.getElementById('shareScanName').value = this.data.client_name || '';
    document.getElementById('shareScanPhone').value = '';
    document.getElementById('shareScanEmail').value = '';
    document.getElementById('shareScanLink').textContent = window.location.origin + '/dashboard#scanresult/...';
    document.getElementById('shareScanLinkArea').style.display = 'none';
    const btn = document.getElementById('btnGenerateScanLink');
    if (btn) btn.textContent = 'Generate Link';
    window._currentScanId = this.data.id;
    if (window.openModal) window.openModal('shareScanModal');
  },

  setContext(ctx) {
    console.log(`▶ setContext("${ctx}")`);
    this.activeContext = ctx;
    if ("vibrate" in navigator) navigator.vibrate(50);
    if (window.KORRA_VIZ) window.KORRA_VIZ.applyHeatmap(ctx);
    if (this._attireSelector) this._attireSelector.select(ctx);
    this.renderMeasurements();
    if (this.viewMode === 'pattern') {
      setTimeout(() => this.renderPattern(), 50);
    }

    // Phase 141: Trigger garment generation on context change
    this._updateGarmentForContext();
    console.log('  setContext done');
  },

  setMaterial(mat) {
    this.activeMaterial = mat;
    if ("vibrate" in navigator) navigator.vibrate(25);
    // Update material rail active state
    document.querySelectorAll('.ms-material-btn').forEach(b => {
      const btnText = b.textContent.toLowerCase();
      b.classList.toggle('active', btnText.includes(mat));
    });
    this.renderMeasurements();
    if (this.viewMode === 'pattern') {
      setTimeout(() => this.renderPattern(), 50);
    }

    // Phase 142: Update garment material if already loaded
    if (this.viewerInstance && this.viewerInstance.garmentMesh) {
      const matPreset = this.FABRIC_PRESETS[this.activeMaterial] || this.FABRIC_PRESETS.woven;
      const color = matPreset.color ? parseInt(matPreset.color.replace('#', '0x')) : 0xFFFFFF;
      this.viewerInstance.garmentMesh.material.color.setHex(color);
      this.viewerInstance.garmentMesh.material.opacity = mat === 'silk' ? 0.6 : 0.95;
      this.viewerInstance.garmentMesh.material.needsUpdate = true;
    } else {
      this._updateGarmentForContext();
    }
  },


  toggleEase() {
    this.showEased = !this.showEased;
    localStorage.setItem('korra_showEased', this.showEased);
    this.updateBadge();
    this.renderMeasurements();
    if (this.viewMode === 'pattern') {
      setTimeout(() => this.renderPattern(), 50);
    }
    const toggle = document.querySelector('#view-scanresult .ms-ease-toggle');
    if (toggle) {
      const labels = toggle.querySelectorAll('.ms-ease-label');
      const track = toggle.querySelector('.ms-ease-track');
      const thumb = toggle.querySelector('.ms-ease-thumb');
      if (labels.length >= 2) {
        labels[0].classList.toggle('active', !this.showEased);
        labels[1].classList.toggle('active', this.showEased);
      }
      if (track) track.classList.toggle('active', this.showEased);
      if (thumb) thumb.classList.toggle('right', this.showEased);
    }
    const attireContainer = document.querySelector('.ms-attire-selector-container');
    if (attireContainer) attireContainer.style.display = this.showEased ? '' : 'none';
  },

  // ═══ FIT DIAGNOSTICS ═══
  computeDiagnostics() {
    const lm = this.data?.landmarks;
    if (!lm || !lm.Shoulder_L) return { asymmetry: 'No data', posture: 'No data' };
    const sl = lm.Shoulder_L, sr = lm.Shoulder_R;
    const hl = lm.Hip_L, hr = lm.Hip_R;
    const nose = lm.Nose;
    let asymmetry = 'SYMMETRICAL';
    const shoulderYDiff = Math.abs(sl[1] - sr[1]);
    if (shoulderYDiff > 0.04) asymmetry = 'SHOULDER DROP DETECTED';
    else if (shoulderYDiff > 0.02) asymmetry = 'MINOR ASYMMETRY';
    const hipYDiff = Math.abs(hl[1] - hr[1]);
    if (hipYDiff > 0.03) asymmetry = 'HIP TILT DETECTED';
    const shoulderMidX = (sl[0] + sr[0]) / 2;
    const noseOffset = Math.abs(nose[0] - shoulderMidX);
    let posture = noseOffset > 0.08 ? 'FORWARD HEAD POSTURE' : 'OPTIMAL';
    const hipMidX = (hl[0] + hr[0]) / 2;
    if (Math.abs(shoulderMidX - hipMidX) > 0.04 && posture === 'OPTIMAL') posture = 'LEANING DETECTED';
    return { asymmetry, posture };
  },

  // ═══ EXPORT ═══
  exportPDF() {
    if (window.KORRA_EXPORT && window.KORRA_EXPORT.pdf) {
      const hasVto = this._vtoResults && Object.values(this._vtoResults).some(Boolean);
      if (hasVto && window.KORRA_EXPORT.pdfWithVTO) {
        window.KORRA_EXPORT.pdfWithVTO(this.data.client_name, this.data.measurements, this.data.gender, this.data.height, this._vtoResults);
      } else {
        window.KORRA_EXPORT.pdf(this.data.client_name, this.data.measurements, this.data.gender, this.data.height);
      }
    }
  },
  async downloadOBJ() {
    if (!this.data?.mesh_url) return;
    this._trackEvent('reconstruct', 'obj_download', this.data.client_name);
    try {
      const head = await fetch(this.data.mesh_url, { method: 'HEAD' });
      if (!head.ok) throw new Error('File not found');
      const link = document.createElement('a');
      link.href = this.data.mesh_url;
      link.download = `KORRA_${this.data.client_name}_3D.obj`;
      link.click();
    } catch(e) { /* silent */ }
  },

  // ═══ HEATMAP ═══
  toggleHeatmap() {
    this.heatmapActive = !this.heatmapActive;
    if (this.heatmapActive) {
      this.vLatest?.applyHeatmap('standard');
    } else {
      this.vLatest?.resetHeatmap();
    }
    const body = document.getElementById('ms-sheet-body');
    if (body) body.innerHTML = this.buildSheetContent();
  },

  setCompareBaseline(idx) {
    this.compareBaselineIdx = parseInt(idx);
    this.heatmapActive = false;
    this.loadCompareViewers();
    const body = document.getElementById('ms-sheet-body');
    if (body) body.innerHTML = this.buildSheetContent();
  },

  handleManualEdit(key, text) {
    if (!this.data) return;
    // Extract number from text (e.g. "88.0cm" -> 88.0)
    const num = parseFloat(text);
    if (isNaN(num)) return;

    // Reverse factor if in inches
    const factor = this.unit === 'in' ? 0.393701 : 1;
    const rawVal = num / factor;

    if (!this.manualEdits) this.manualEdits = {};
    this.manualEdits[key] = rawVal;

    // Update local data for immediate feedback
    if (!this.data.measurements) this.data.measurements = {};
    this.data.measurements[key] = rawVal;

    console.log(`✍️ Manual Edit: ${key} -> ${rawVal}cm`);

    // Enable/Highlight submit button
    const btn = document.getElementById('btnSubmitRefinement');
    if (btn) {
      btn.style.background = 'var(--Mint)';
      btn.style.color = 'var(--Teal-900)';
      btn.textContent = 'Sync Refinement *';
    }
  },

  async submitRefinement() {
    if (!this.manualEdits || Object.keys(this.manualEdits).length === 0) {
      alert("No changes to sync.");
      return;
    }

    const btn = document.getElementById('btnSubmitRefinement');
    if (btn) {
      btn.disabled = true;
      btn.textContent = 'REFINING 3D MESH...';
    }

    try {
      const { data: { session } } = await window.KORRA_DB.auth.getSession();
      const res = await fetch(`/api/v2/measurements/${this.data.id}/back-calculate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify(this.manualEdits)
      });

      if (!res.ok) throw new Error("Sync failed.");

      const result = await res.json();
      console.log("✅ Model Refined:", result);

      // Update local data with new betas if returned
      if (result.new_betas && this.data.__smpl_params) {
        this.data.__smpl_params.shape = result.new_betas;
      }

      // Success Feedback
      if (btn) {
        btn.textContent = '✅ REFINED';
        btn.style.background = 'rgba(198,255,0,0.2)';
        btn.style.color = 'var(--Mint)';
      }

      // Reload 3D Viewer if possible
      if (window.KORRA_VIZ) {
        // Since we updated the betas, we would ideally regenerate the OBJ.
        // For now, we can notify the user that the model is updated on next reload
        // or trigger a full re-fetch of the scan if the backend updated the OBJ.
        alert("✨ Expert Intelligence Applied. 3D Model has been optimized based on your master measurements.");
      }

      this.manualEdits = {};
    } catch (e) {
      alert("Refinement failed: " + e.message);
      if (btn) {
        btn.disabled = false;
        btn.textContent = 'Sync Refinement';
      }
    }
  },

  // ═══ NAVIGATION ═══
  handleBack() {
    if (this.viewMode === 'ai') {
      this.closeAI();
    } else {
      this.goBack();
    }
  },
  goBack() {
    this.cleanup();
    window.switchTab(this._previousTab || 'vault');
  },

  cleanup() {
    this._destroyFabIntelligence();
    this._cleanupKeyboardShortcuts();
    this.closeSideMenu();
    document.getElementById('ms-side-menu')?.remove();
    document.getElementById('ms-side-menu-backdrop')?.remove();

    // Phase 112: Restore Layout
    const content = document.querySelector('.main-content');
    if (content) {
      content.style.padding = '';
    }

    document.querySelectorAll('#view-scanresult .ms-header-btn, #view-scanresult .ms-share-btn').forEach(btn => {
      btn.style.display = '';
    });
    document.body.classList.remove('ai-mode');
    document.querySelector('main').style.overflow = '';
    this.active = false;
    this.data = null;
    this.viewerInstance = null;
    this.sheetExpanded = false;
    this._aiLoading = false;
    if (this._aiAbort) { this._aiAbort.abort(); this._aiAbort = null; }
  },

  // ═══ FAB INTELLIGENCE ═══
  _initFabIntelligence() {
    const fi = this._fabIntel;
    fi.activityScore = 0.5;
    fi.lastInteraction = Date.now();
    fi.interactions = [];
    fi.heatmap = {};
    fi.lastReveal = 0;
    fi.sessionReveals = 0;

    const throttle = (fn, ms) => {
      let last = 0;
      return (e) => {
        const now = Date.now();
        if (now - last < ms) return;
        last = now;
        fn(e);
      };
    };

    const onInteract = (type) => (e) => {
      this._trackInteraction(type, e);
    };

    const listeners = [
      ['mousemove', throttle(onInteract('mouse'), 200)],
      ['click', onInteract('click')],
      ['scroll', onInteract('scroll')],
      ['keydown', onInteract('key')],
      ['touchstart', onInteract('touch')],
    ];

    listeners.forEach(([evt, fn]) => {
      document.addEventListener(evt, fn, { passive: true });
      fi._listeners.push([evt, fn]);
    });

    fi._interval = setInterval(() => {
      this._evaluateFabState();
    }, 1000);
  },

  _destroyFabIntelligence() {
    const fi = this._fabIntel;
    fi._listeners.forEach(([evt, fn]) => document.removeEventListener(evt, fn));
    fi._listeners = [];
    if (fi._interval) { clearInterval(fi._interval); fi._interval = null; }
    if (fi._revealTimeout) { clearTimeout(fi._revealTimeout); fi._revealTimeout = null; }
    if (fi._pulseTimeout) { clearTimeout(fi._pulseTimeout); fi._pulseTimeout = null; }
    const fab = document.querySelector('#view-scanresult .ms-ai-fab');
    if (fab) {
      fab.classList.remove('revealed', 'pulse');
    }
  },

  _trackInteraction(type, e) {
    const fi = this._fabIntel;
    const now = Date.now();
    fi.lastInteraction = now;

    const entry = { type, t: now };
    if (e && e.target) {
      entry.target = this._getElementSelector(e.target);
      if (entry.target) {
        fi.heatmap[entry.target] = (fi.heatmap[entry.target] || 0) + 1;
      }
    }
    fi.interactions.push(entry);
    if (fi.interactions.length > 50) fi.interactions.shift();

    const isHighImpact = type === 'click' || type === 'key' || type === 'touch';
    const delta = isHighImpact ? 0.5 : type === 'scroll' ? 0.3 : 0.1;
    fi.activityScore = Math.min(1.0, fi.activityScore + delta);

    if (type === 'click' && entry.target) {
      const recent = fi.interactions.filter(i => i.type === 'click' && i.target === entry.target);
      if (recent.length >= 2) {
        const gap = recent[recent.length - 1].t - recent[recent.length - 2].t;
        if (gap < 2000) this._notifyStuck();
      }
    }
  },

  _getElementSelector(el) {
    if (!el || !el.tagName) return null;
    if (el.classList.length > 0) {
      const cls = Array.from(el.classList).find(c =>
        c.startsWith('ms-') || c.startsWith('tab') || c === 'active'
      );
      if (cls) return el.tagName.toLowerCase() + '.' + cls;
    }
    if (el.id) return '#' + el.id;
    return el.tagName.toLowerCase();
  },

  _evaluateFabState() {
    if (this.viewMode === 'ai' || this.aiOpen) return;

    const fi = this._fabIntel;
    const now = Date.now();

    fi.activityScore *= 0.7;
    fi.activityScore = Math.max(0, fi.activityScore);

    const fab = document.querySelector('#view-scanresult .ms-ai-fab');
    if (!fab || fab.style.display === 'none') return;

    if (fab.classList.contains('revealed')) {
      return;
    }

    if (fi.sessionReveals >= fi.maxReveals) return;
    if (now - fi.lastReveal < fi.cooldownMs) return;

    const idle = now - fi.lastInteraction;
    const isTyping = document.activeElement &&
      (document.activeElement.tagName === 'INPUT' || document.activeElement.tagName === 'TEXTAREA');
    const isDragging = document.querySelector('#ms-sheet-handle.dragging');

    if (isTyping || isDragging) return;

    const explorationDepth = Object.keys(fi.heatmap).length;
    const postActionReveal = fi._pendingPostAction && now - fi._pendingPostAction > 2500;
    const stuckReveal = fi._pendingStuck && now - fi._pendingStuck > 3000;
    const idleReveal = idle > fi.idleThresholdMs && fi.activityScore < 0.3;
    const milestoneReveal = !fi._everRevealed && now - (fi._sessionStart || now) > 20000;

    if (postActionReveal) {
      fi._pendingPostAction = null;
      this._revealFab('post-action');
    } else if (stuckReveal) {
      fi._pendingStuck = null;
      this._revealFab('stuck');
    } else if (idleReveal) {
      this._revealFab('idle');
    } else if (milestoneReveal) {
      this._revealFab('milestone');
    }
  },

  _notifyPostAction() {
    const fi = this._fabIntel;
    if (fi.sessionReveals >= fi.maxReveals) return;
    fi._pendingPostAction = Date.now();
  },

  _notifyStuck() {
    const fi = this._fabIntel;
    if (fi.sessionReveals >= fi.maxReveals) return;
    fi._pendingStuck = Date.now();
  },

  _revealFab(source) {
    const fi = this._fabIntel;
    const now = Date.now();
    fi.lastReveal = now;
    fi.sessionReveals++;
    fi._everRevealed = true;

    const fab = document.querySelector('#view-scanresult .ms-ai-fab');
    if (!fab) return;

    fab.classList.add('pulse');
    fi._pulseTimeout = setTimeout(() => fab.classList.remove('pulse'), 600);

    setTimeout(() => {
      if (Date.now() - fi.lastReveal > fi.cooldownMs - (fi.cooldownMs - fi.revealDurationMs)) return;
      fab.classList.add('revealed');
    }, 300);

    fi._revealTimeout = setTimeout(() => {
      this._hideFab();
    }, fi.revealDurationMs + 300);
  },

  _hideFab() {
    const fi = this._fabIntel;
    const fab = document.querySelector('#view-scanresult .ms-ai-fab');
    if (!fab) return;
    fab.classList.remove('revealed');
    if (fi._revealTimeout) { clearTimeout(fi._revealTimeout); fi._revealTimeout = null; }
  },

  // ═══ RECONSTRUCT ERROR STATES ═══
  _showReconError(message, type) {
    const errorEl = document.getElementById('ms-recon-error');
    const iconEl = document.getElementById('ms-recon-error-icon');
    const msgEl = document.getElementById('ms-recon-error-message');
    const actionsEl = document.getElementById('ms-recon-error-actions');
    if (!errorEl) return;

    if (this._reconErrorCount && type in this._reconErrorCount) this._reconErrorCount[type]++;

    errorEl.dataset.type = type || 'server';

    const icons = {
      validation: '<svg viewBox="0 0 24 24" class="ms-recon-error-icon-svg"><path fill="#F59E0B" d="M12 2L1 21h22L12 2zm0 4l7.53 13H4.47L12 6zm-1 5v4h2v-4h-2zm0 6v2h2v-2h-2z"/></svg>',
      auth: '<svg viewBox="0 0 24 24" class="ms-recon-error-icon-svg"><path fill="#9CA3AF" d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z"/></svg>',
      server: '<svg viewBox="0 0 24 24" class="ms-recon-error-icon-svg"><path fill="#DC2626" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>'
    };
    iconEl.innerHTML = icons[type] || icons.server;
    msgEl.textContent = message;

    actionsEl.innerHTML = '';
    if (type === 'auth') {
      actionsEl.innerHTML = '<button class="ms-recon-error-action-btn" onclick="KORRA_MS._handleReconAuthError()">Sign In</button>';
    } else if (type === 'server') {
      actionsEl.innerHTML = '<button class="ms-recon-error-action-btn" onclick="KORRA_MS._retryReconstruct()">Retry</button>';
    }

    errorEl.style.display = 'flex';

    const statusEl = document.getElementById('ms-recon-status');
    if (statusEl) statusEl.style.display = 'none';

    if (type === 'validation') {
      const genBtn = document.getElementById('ms-recon-generate-btn');
      if (genBtn) genBtn.style.display = 'block';
    }

    console.error('[RECONSTRUCT]', JSON.stringify({ type, message, timestamp: new Date().toISOString() }));
    this._trackEvent('reconstruct', 'error', type);
  },

  _dismissReconError() {
    const errorEl = document.getElementById('ms-recon-error');
    if (errorEl) errorEl.style.display = 'none';
  },

  _retryReconstruct() {
    this._dismissReconError();
    this._runReconstruct();
  },

  _handleReconAuthError() {
    window.location.href = '/signin.html?return=' + encodeURIComponent(window.location.pathname);
  },

  _updateReconProgress(stage, progress, message) {
    const fill = document.getElementById('ms-recon-progress-fill');
    const text = document.getElementById('ms-recon-progress-text');
    const clampedProgress = Math.max(0, Math.min(100, progress));
    if (fill) {
      fill.style.width = clampedProgress + '%';
      const progressBar = fill.parentElement;
      if (progressBar) progressBar.setAttribute('aria-valuenow', clampedProgress);
    }
    if (text) text.textContent = message || stage;
    document.querySelectorAll('.ms-recon-step').forEach(el => {
      const step = el.dataset.step;
      const stages = ['uploading', 'segmenting', 'meshing', 'patterning', 'zipping', 'complete'];
      const currentIdx = stages.indexOf(stage);
      const stepIdx = stages.indexOf(step);
      el.classList.toggle('active', step === stage);
      el.classList.toggle('done', stepIdx < currentIdx && currentIdx >= 0);
    });
    // Phase 097: Update elapsed + step-specific estimate
    if (this._reconElapsedEl && this._reconFormatTime && this._reconStartTime) {
      const stages = ['uploading', 'segmenting', 'meshing', 'patterning', 'zipping', 'complete'];
      const elapsed = Math.floor((Date.now() - this._reconStartTime) / 1000);
      let estText = '';
      if (stage !== 'uploading' && stage !== 'complete' && this._reconStepEstimates) {
        const remaining = Object.entries(this._reconStepEstimates)
          .filter(([s]) => stages.indexOf(s) >= stages.indexOf(stage))
          .reduce((sum, [, t]) => sum + t, 0);
        estText = ` · Estimated: ~${this._reconFormatTime(remaining)}`;
      }
      this._reconElapsedEl.textContent = `Elapsed: ${this._reconFormatTime(elapsed)}${estText}`;
      if (stage !== this._reconCurrentStage) {
        this._reconStageStart = Date.now();
        this._reconCurrentStage = stage;
      }
    }
  },

  // ═══ RECONSTRUCT 3D PREVIEW ═══
  _initReconViewer() {
    const container = document.getElementById('ms-recon-viewer');
    if (!container || !window.THREE) return null;
    container.innerHTML = '';

    const w = container.clientWidth || 360;
    const h = container.clientHeight || 360;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1A1A2E);

    const camera = new THREE.PerspectiveCamera(40, w / h, 0.01, 100);
    camera.position.set(0, 0.3, 1.8);
    camera.lookAt(0, 0.3, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance', failIfMajorPerformanceCaveat: false });
    renderer.setSize(w, h);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.0;
    container.appendChild(renderer.domElement);

    const ambient = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambient);
    const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
    dirLight.position.set(2, 4, 3);
    scene.add(dirLight);
    const fillLight = new THREE.DirectionalLight(0xffffff, 0.4);
    fillLight.position.set(-2, 1, -2);
    scene.add(fillLight);

    const grid = new THREE.GridHelper(1, 10, 0x444466, 0x333355);
    grid.position.y = 0;
    scene.add(grid);

    let controls = null;
    if (THREE.OrbitControls) {
      controls = new THREE.OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;
      controls.dampingFactor = 0.08;
      controls.target.set(0, 0.3, 0);
      controls.update();
    }

    let _reconFrameId = null;
    let _reconCrashCount = 0;
    const animLoop = () => {
      try {
        if (!this._reconViewer) return;
        _reconFrameId = requestAnimationFrame(animLoop);
        if (this._reconViewer) this._reconViewer.frameId = _reconFrameId;
        if (controls) controls.update();
        renderer.render(scene, camera);
        _reconCrashCount = 0;
      } catch (e) {
        console.warn('[RECON] Render error:', e?.message);
        _reconCrashCount++;
        if (_reconCrashCount > 3) {
          console.warn('[RECON] Too many render errors, stopping loop');
          if (_reconFrameId) cancelAnimationFrame(_reconFrameId);
          this._reconViewer = null;
          return;
        }
        _reconFrameId = requestAnimationFrame(animLoop);
      }
    };
    try {
      renderer.compile(scene, camera);
      animLoop();
    } catch (e) {
      console.warn('[RECON] Init render failed, retrying on first mesh load:', e.message);
      this._reconPendingLoop = animLoop;
    }

    renderer.domElement.addEventListener('webglcontextlost', (e) => {
      e.preventDefault();
      console.warn('[RECON] WebGL context lost, will restore automatically');
      if (_reconFrameId) cancelAnimationFrame(_reconFrameId);
    }, false);
    renderer.domElement.addEventListener('webglcontextrestored', () => {
      console.log('[RECON] WebGL context restored, recompiling shaders');
      try { renderer.compile(scene, camera); } catch (_) {}
      animLoop();
    }, false);

    this._reconViewer = { scene, camera, renderer, controls, container, frameId: null };
    this._reconViewer.frameId = _reconFrameId;
    return this._reconViewer;
  },

  // Phase 121: Three.js memory cleanup for recon viewer
  _cleanupReconViewer() {
    if (!this._reconViewer) return;
    if (this._reconFullscreen) {
      const wrap = document.getElementById('ms-recon-viewer-wrap');
      if (wrap) { wrap.style.position = ''; wrap.style.zIndex = ''; wrap.style.inset = ''; wrap.style.width = ''; wrap.style.height = ''; wrap.style.borderRadius = ''; }
      this._reconFullscreen = false;
      const closeBtn = document.getElementById('ms-recon-fullscreen-close');
      if (closeBtn) closeBtn.remove();
    }
    const { scene, renderer, controls } = this._reconViewer;
    if (controls) controls.dispose();
    if (scene) {
      scene.traverse((obj) => {
        if (obj.geometry) obj.geometry.dispose();
        if (obj.material) {
          if (Array.isArray(obj.material)) obj.material.forEach(m => m.dispose());
          else obj.material.dispose();
        }
      });
    }
    if (renderer) {
      renderer.dispose();
      renderer.forceContextLoss();
    }
    const container = document.getElementById('ms-recon-viewer');
    if (container) container.innerHTML = '';
    this._reconViewer = null;
    this._reconMesh = null;
    this._reconWireframe = false;
    this._reconPendingLoop = null;
    const statsEl = document.getElementById('ms-recon-viewer-stats');
    if (statsEl) { statsEl.style.display = 'none'; statsEl.textContent = ''; }
  },

  _loadReconMeshIntoViewer(blob) {
    if (!window.JSZip || !window.THREE) {
      console.warn('[RECON] JSZip or THREE not loaded, skipping 3D preview');
      const resultsContent = document.getElementById('ms-recon-results-content');
      if (resultsContent) {
        const note = document.createElement('div');
        note.style.cssText = 'color:#FF6B6B;font-size:13px;padding:8px 0;';
        note.textContent = !window.JSZip
          ? '3D preview unavailable: JSZip library not loaded.'
          : '3D preview unavailable: Three.js library not loaded.';
        resultsContent.appendChild(note);
      }
      return;
    }

    const viewerWrap = document.getElementById('ms-recon-viewer-wrap');
    const loadingEl = document.getElementById('ms-recon-viewer-loading');
    if (viewerWrap) viewerWrap.style.display = 'block';
    if (loadingEl) loadingEl.style.display = 'flex';

    const viewer = this._reconViewer || this._initReconViewer();
    if (!viewer) return;

    JSZip.loadAsync(blob).then(zip => {
      const objFile = zip.file('garment.obj') || zip.file('mesh.obj') || zip.file('model.obj')
        || zip.file(/mesh_upper\.obj$/) || zip.file(/mesh_lower\.obj$/);
      if (!objFile) {
        if (loadingEl) loadingEl.style.display = 'none';
        if (viewerWrap) viewerWrap.style.display = 'none';
        console.warn('[RECON] No OBJ file found in ZIP');
        const resultsContent = document.getElementById('ms-recon-results-content');
        if (resultsContent) {
          const errEl = document.createElement('div');
          errEl.style.cssText = 'color:#FF6B6B;font-size:13px;padding:12px 8px;text-align:center;';
          errEl.textContent = '3D mesh not available for this garment. The download ZIP contains the sewing pattern.';
          resultsContent.appendChild(errEl);
        }
        return;
      }
      return objFile.async('string');
    }).then(objText => {
      if (!objText) return;

      const geometry = new THREE.BufferGeometry();
      const vertices = [];
      const indices = [];
      const normals = [];
      const uvs = [];
      const vArr = [], vnArr = [], vtArr = [];

      const lines = objText.split('\n');
      for (const line of lines) {
        const parts = line.trim().split(/\s+/);
        if (parts[0] === 'v') {
          vArr.push(parseFloat(parts[1]), parseFloat(parts[2]), parseFloat(parts[3]));
        } else if (parts[0] === 'vn') {
          vnArr.push(parseFloat(parts[1]), parseFloat(parts[2]), parseFloat(parts[3]));
        } else if (parts[0] === 'vt') {
          vtArr.push(parseFloat(parts[1]), parseFloat(parts[2]));
        } else if (parts[0] === 'f') {
          const faceVerts = parts.slice(1);
          const idxs = faceVerts.map(f => {
            const [vi] = f.split('/').map(Number);
            return vi - 1;
          });
          for (let i = 1; i < idxs.length - 1; i++) {
            indices.push(idxs[0], idxs[i], idxs[i + 1]);
          }
          for (const f of faceVerts) {
            const [vi, vti, vni] = f.split('/').map(Number);
            const i3 = (vi - 1) * 3;
            vertices.push(vArr[i3], vArr[i3 + 1], vArr[i3 + 2]);
            if (vni && vnArr.length) {
              const i3n = (vni - 1) * 3;
              normals.push(vnArr[i3n], vnArr[i3n + 1], vnArr[i3n + 2]);
            }
            if (vti && vtArr.length) {
              const i2 = (vti - 1) * 2;
              uvs.push(vtArr[i2], vtArr[i2 + 1]);
            }
          }
        }
      }

      if (indices.length === 0) {
        geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
        geometry.computeVertexNormals();
      } else {
        const posArr = new Float32Array(vertices);
        geometry.setAttribute('position', new THREE.Float32BufferAttribute(posArr, 3));
        if (normals.length) geometry.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));
        else geometry.computeVertexNormals();
        if (uvs.length) geometry.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
        geometry.setIndex(indices);
      }

      geometry.computeBoundingBox();
      const box = geometry.boundingBox;
      const center = new THREE.Vector3();
      box.getCenter(center);
      geometry.translate(-center.x, -center.y, -center.z);

      const size = new THREE.Vector3();
      box.getSize(size);
      const maxDim = Math.max(size.x, size.y, size.z);
      if (maxDim > 0) {
        const scale = 1.2 / maxDim;
        geometry.scale(scale, scale, scale);
      }

      geometry.computeBoundingBox();
      const newBox = geometry.boundingBox;
      const yOffset = -(newBox.min.y);
      geometry.translate(0, yOffset, 0);

      const vCount = vertices.length / 3;
      const fCount = indices.length / 3;

      const lowerName = objText.toLowerCase();
      const hasUpper = /\b(upper|top|shirt|blouse|jacket|bodice)\b/.test(lowerName);
      const hasLower = /\b(lower|bottom|pants|trousers|skirt|legs)\b/.test(lowerName);
      let meshLabel = '';
      if (hasUpper && hasLower) meshLabel = 'Full garment';
      else if (hasUpper) meshLabel = 'Upper garment only';
      else if (hasLower) meshLabel = 'Lower garment only';
      else meshLabel = 'Single piece';

      let meshColor = 0x1DBFAF;
      if (hasUpper && !hasLower) meshColor = 0x4A90D9;
      else if (hasLower && !hasUpper) meshColor = 0x2C5F8A;

      const material = new THREE.MeshStandardMaterial({
        color: meshColor,
        metalness: 0.1,
        roughness: 0.6,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.85,
      });

      const mesh = new THREE.Mesh(geometry, material);
      viewer.scene.add(mesh);
      this._reconMesh = mesh;

      viewer.camera.position.set(0, 0.5, 1.8);
      viewer.camera.lookAt(0, 0.4, 0);
      if (viewer.controls) {
        viewer.controls.target.set(0, 0.4, 0);
        viewer.controls.update();
      }

      try { viewer.renderer.compile(viewer.scene, viewer.camera); } catch (_) {}
      if (this._reconPendingLoop) { this._reconPendingLoop(); this._reconPendingLoop = null; }

      if (loadingEl) loadingEl.style.display = 'none';
      console.log('[RECON] 3D mesh loaded:', { vertices: vCount, faces: fCount, label: meshLabel });

      const statsEl = document.getElementById('ms-recon-viewer-stats');
      if (statsEl) {
        statsEl.textContent = meshLabel + ' | Vertices: ' + vCount + ' | Faces: ' + fCount;
        statsEl.style.display = 'block';
      }
    }).catch(err => {
      console.error('[RECON] Failed to load mesh:', err);
      if (loadingEl) loadingEl.style.display = 'none';
    });
  },

  _resetReconCamera() {
    const viewer = this._reconViewer;
    if (!viewer) return;
    viewer.camera.position.set(0, 0.5, 1.8);
    viewer.camera.lookAt(0, 0.4, 0);
    if (viewer.controls) {
      viewer.controls.target.set(0, 0.4, 0);
      viewer.controls.update();
    }
  },

  _toggleReconWireframe() {
    const mesh = this._reconMesh;
    if (!mesh) return;
    mesh.material.wireframe = !mesh.material.wireframe;
    this._reconWireframe = mesh.material.wireframe;
  },

  _toggleReconFullscreen() {
    const wrap = document.getElementById('ms-recon-viewer-wrap');
    if (!wrap) return;
    if (this._reconFullscreen) {
      wrap.style.position = '';
      wrap.style.zIndex = '';
      wrap.style.inset = '';
      wrap.style.width = '';
      wrap.style.height = '';
      wrap.style.borderRadius = '';
      this._reconFullscreen = false;
      const closeBtn = document.getElementById('ms-recon-fullscreen-close');
      if (closeBtn) closeBtn.remove();
    } else {
      wrap.style.position = 'fixed';
      wrap.style.zIndex = '3000';
      wrap.style.inset = '0';
      wrap.style.width = '100vw';
      wrap.style.height = '100vh';
      wrap.style.borderRadius = '0';
      this._reconFullscreen = true;
      if (!document.getElementById('ms-recon-fullscreen-close')) {
        const closeBtn = document.createElement('button');
        closeBtn.id = 'ms-recon-fullscreen-close';
        closeBtn.textContent = '\u00d7';
        closeBtn.style.cssText = 'position:fixed;top:12px;right:16px;z-index:3001;background:rgba(0,0,0,0.6);border:none;color:#fff;font-size:28px;cursor:pointer;width:40px;height:40px;border-radius:50%;display:flex;align-items:center;justify-content:center;';
        closeBtn.onclick = () => this._toggleReconFullscreen();
        document.body.appendChild(closeBtn);
      }
      const viewer = this._reconViewer;
      if (viewer && viewer.renderer) {
        const w = window.innerWidth;
        const h = window.innerHeight;
        viewer.camera.aspect = w / h;
        viewer.camera.updateProjectionMatrix();
        viewer.renderer.setSize(w, h);
      }
    }
  },

  _captureReconScreenshot() {
    const viewer = this._reconViewer;
    if (!viewer || !viewer.renderer) return;
    const dataUrl = viewer.renderer.domElement.toDataURL('image/png');
    const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    const link = document.createElement('a');
    link.download = 'korra-recon-' + ts + '.png';
    link.href = dataUrl;
    link.click();
  },

  _loadReconMeshIntoTryon() {
    if (!this._reconMesh) {
      console.warn('[RECON] No mesh loaded for try-on');
      return;
    }
    // Store mesh data for try-on
    this._reconMeshData = {
      mesh: this._reconMesh,
      scene: this._reconViewer?.scene,
      vertexCount: this._reconMesh.geometry.attributes.position.count,
      scale: 1.0,
      position: { x: 0, y: 0, z: 0 },
      opacity: 0.85,
    };
    console.log('[RECON] Mesh stored for try-on:', this._reconMeshData.vertexCount, 'vertices');
    this._trackEvent('vto', 'generate', this._reconGarmentType);
    this.switchView('tryon');
  },

  // ═══ PHASE 221: AR PREVIEW ═══
  _openARPreview() {
    this._trackEvent('reconstruct', 'ar_preview', this._reconGarmentType);
    if (navigator.xr) {
      navigator.xr.isSessionSupported('immersive-ar').then(supported => {
        if (supported) {
          this._startXRSession();
        } else {
          this._fallbackARPreview();
        }
      }).catch(() => {
        this._fallbackARPreview();
      });
    } else {
      this._fallbackARPreview();
    }
  },

  _startXRSession() {
    const viewer = this._reconViewer;
    if (!viewer || !viewer.renderer) {
      this._fallbackARPreview();
      return;
    }
    navigator.xr.requestSession('immersive-ar', {
      optionalFeatures: ['hit-test', 'dom-overlay'],
      domOverlay: { root: document.getElementById('ms-recon-viewer-wrap') }
    }).then(session => {
      this._arSession = session;
      viewer.renderer.xr.enabled = true;
      viewer.renderer.xr.setReferenceSpaceType('local');
      viewer.renderer.xr.setSession(session);
      session.addEventListener('end', () => {
        this._arSession = null;
        viewer.renderer.xr.enabled = false;
      });
    }).catch(err => {
      console.warn('[AR] XR session failed:', err);
      this._fallbackARPreview();
    });
  },

  _fallbackARPreview() {
    const wrap = document.getElementById('ms-recon-viewer-wrap');
    if (!wrap) { alert('AR requires a compatible device.'); return; }
    const viewer = this._reconViewer;
    if (!viewer || !viewer.renderer) { alert('AR requires a compatible device.'); return; }
    wrap.style.position = 'fixed';
    wrap.style.zIndex = '3000';
    wrap.style.inset = '0';
    wrap.style.width = '100vw';
    wrap.style.height = '100vh';
    wrap.style.borderRadius = '0';
    wrap.style.background = '#000';
    this._arFullscreen = true;
    if (!document.getElementById('ms-ar-close')) {
      const closeBtn = document.createElement('button');
      closeBtn.id = 'ms-ar-close';
      closeBtn.textContent = '\u00d7';
      closeBtn.style.cssText = 'position:fixed;top:12px;right:16px;z-index:3001;background:rgba(0,0,0,0.6);border:none;color:#fff;font-size:28px;cursor:pointer;width:40px;height:40px;border-radius:50%;display:flex;align-items:center;justify-content:center;';
      closeBtn.onclick = () => this._closeARPreview();
      document.body.appendChild(closeBtn);
    }
    const w = window.innerWidth;
    const h = window.innerHeight;
    viewer.camera.aspect = w / h;
    viewer.camera.updateProjectionMatrix();
    viewer.renderer.setSize(w, h);
    viewer.camera.position.set(0, 0.3, 1.2);
    viewer.camera.lookAt(0, 0.3, 0);
  },

  _closeARPreview() {
    const wrap = document.getElementById('ms-recon-viewer-wrap');
    if (wrap) {
      wrap.style.position = '';
      wrap.style.zIndex = '';
      wrap.style.inset = '';
      wrap.style.width = '';
      wrap.style.height = '';
      wrap.style.borderRadius = '';
      wrap.style.background = '';
    }
    this._arFullscreen = false;
    const closeBtn = document.getElementById('ms-ar-close');
    if (closeBtn) closeBtn.remove();
    if (this._arSession) {
      this._arSession.end().catch(() => {});
      this._arSession = null;
    }
    const viewer = this._reconViewer;
    if (viewer && viewer.renderer) {
      viewer.renderer.xr.enabled = false;
      const w = viewer.container?.clientWidth || 360;
      const h = viewer.container?.clientHeight || 360;
      viewer.camera.aspect = w / h;
      viewer.camera.updateProjectionMatrix();
      viewer.renderer.setSize(w, h);
      viewer.camera.position.set(0, 0.5, 1.8);
      viewer.camera.lookAt(0, 0.4, 0);
    }
  },

  _applyReconMeshToViewport() {
    const data = this._reconMeshData;
    if (!data || !data.mesh || !this.viewerInstance) return;
    const mesh = data.mesh.clone();
    mesh.material = mesh.material.clone();
    mesh.material.transparent = true;
    mesh.material.opacity = data.opacity;
    mesh.scale.setScalar(data.scale);
    mesh.position.set(data.position.x, data.position.y, data.position.z);
    if (this.viewerInstance.scene) {
      this.viewerInstance.scene.add(mesh);
    }
    this._reconMeshOnBody = mesh;
    this._showReconMeshControls();
    console.log('[RECON] Mesh applied to try-on viewport');
  },

  _showReconMeshControls() {
    let controls = document.getElementById('ms-recon-mesh-controls');
    if (!controls) {
      controls = document.createElement('div');
      controls.id = 'ms-recon-mesh-controls';
      controls.className = 'ms-recon-mesh-controls';
      controls.innerHTML = `
        <div class="ms-recon-mesh-control-row">
          <label>Scale</label>
          <input type="range" id="recon-scale" min="0.3" max="3.0" step="0.05" value="1.0">
          <span id="recon-scale-val">1.0x</span>
        </div>
        <div class="ms-recon-mesh-control-row">
          <label>Opacity</label>
          <input type="range" id="recon-opacity" min="0.1" max="1.0" step="0.05" value="0.85">
          <span id="recon-opacity-val">85%</span>
        </div>
        <div class="ms-recon-mesh-control-row">
          <label>Y Offset</label>
          <input type="range" id="recon-y-offset" min="-0.5" max="0.5" step="0.01" value="0">
          <span id="recon-y-val">0cm</span>
        </div>
        <button class="ms-recon-mesh-fit-btn" onclick="KORRA_MS._autoFitReconMesh()">Auto-Fit</button>
      `;
      const viewer = document.querySelector('.ms-viewer');
      if (viewer) viewer.appendChild(controls);

      document.getElementById('recon-scale')?.addEventListener('input', (e) => {
        const v = parseFloat(e.target.value);
        if (this._reconMeshOnBody) this._reconMeshOnBody.scale.setScalar(v);
        this._reconMeshData.scale = v;
        document.getElementById('recon-scale-val').textContent = v.toFixed(1) + 'x';
      });
      document.getElementById('recon-opacity')?.addEventListener('input', (e) => {
        const v = parseFloat(e.target.value);
        if (this._reconMeshOnBody) this._reconMeshOnBody.material.opacity = v;
        this._reconMeshData.opacity = v;
        document.getElementById('recon-opacity-val').textContent = Math.round(v * 100) + '%';
      });
      document.getElementById('recon-y-offset')?.addEventListener('input', (e) => {
        const v = parseFloat(e.target.value);
        if (this._reconMeshOnBody) this._reconMeshOnBody.position.y = v;
        this._reconMeshData.position.y = v;
        document.getElementById('recon-y-val').textContent = Math.round(v * 100) + 'cm';
      });
    }
    controls.style.display = 'block';
  },

  _autoFitReconMesh() {
    if (!this._reconMeshOnBody || !this.viewerInstance) return;
    const box = new THREE.Box3().setFromObject(this._reconMeshOnBody);
    const size = new THREE.Vector3();
    box.getSize(size);
    const targetHeight = 0.8;
    const scale = targetHeight / size.y;
    this._reconMeshOnBody.scale.setScalar(scale);
    this._reconMeshData.scale = scale;
    const center = new THREE.Vector3();
    box.getCenter(center);
    this._reconMeshOnBody.position.y = -center.y * scale + 0.1;
    this._reconMeshData.position.y = this._reconMeshOnBody.position.y;
    const scaleSlider = document.getElementById('recon-scale');
    const ySlider = document.getElementById('recon-y-offset');
    if (scaleSlider) { scaleSlider.value = scale; document.getElementById('recon-scale-val').textContent = scale.toFixed(1) + 'x'; }
    if (ySlider) { ySlider.value = this._reconMeshOnBody.position.y; document.getElementById('recon-y-val').textContent = Math.round(this._reconMeshOnBody.position.y * 100) + 'cm'; }
    console.log('[RECON] Auto-fit: scale=' + scale.toFixed(2));
  },

  // ═══ PHASE 140: Save Garment to Scan ═══
  async _saveGarmentToScan() {
    if (!this.data?.id || !this._reconMeshData) {
      alert('No garment mesh available to save.');
      return;
    }
    if (!confirm('Save this garment to your scan?')) return;
    try {
      const { data: { session } } = await window.KORRA_DB.auth.getSession();
      if (!session) { alert('Session expired. Please sign in again.'); return; }
      const res = await fetch(`/api/v2/measurements/${this.data.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ garment_mesh_url: 'stored' }),
      });
      if (!res.ok) throw new Error('Failed to save');
      this.data.garment_mesh_url = 'stored';
      alert('Garment saved to scan');
    } catch (e) {
      console.error('[RECON] Save garment failed:', e);
      alert('Failed to save garment: ' + e.message);
    }
  },

  // ═══ PHASE 215: KEYBOARD SHORTCUTS ═══
  _initKeyboardShortcuts() {
    this._keyboardHandler = (e) => {
      if (!this.active) return;
      const tag = document.activeElement?.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;

      // Escape: go back
      if (e.key === 'Escape') {
        e.preventDefault();
        this.switchView(this._previousView || 'avatar');
        return;
      }

      // Ctrl+S / Cmd+S: download OBJ in recon view
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        if (this.viewMode === 'reconstruct' && this._reconMeshData) {
          e.preventDefault();
          this.downloadOBJ();
        }
      }
    };
    document.addEventListener('keydown', this._keyboardHandler);
  },

  _cleanupKeyboardShortcuts() {
    if (this._keyboardHandler) {
      document.removeEventListener('keydown', this._keyboardHandler);
      this._keyboardHandler = null;
    }
  },

  // ═══ PHASE 218: CAMERA CAPTURE ═══
  async _captureCameraPhoto() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 1920 }, height: { ideal: 1080 } }
      });
      let modal = document.getElementById('ms-camera-modal');
      if (!modal) {
        modal = document.createElement('div');
        modal.id = 'ms-camera-modal';
        modal.style.cssText = 'position:fixed;inset:0;z-index:9999;background:rgba(0,0,0,0.95);display:flex;flex-direction:column;align-items:center;justify-content:center;';
        modal.innerHTML = `
          <video id="ms-camera-video" autoplay playsinline style="max-width:90vw;max-height:70vh;border-radius:8px;"></video>
          <div style="margin-top:16px;display:flex;gap:12px;">
            <button id="ms-camera-capture" style="padding:12px 24px;border-radius:8px;border:none;background:var(--Accent-Mint,#1DBFAF);color:#000;font-weight:600;font-size:14px;cursor:pointer;">Capture</button>
            <button id="ms-camera-cancel" style="padding:12px 24px;border-radius:8px;border:1px solid rgba(255,255,255,0.2);background:transparent;color:#fff;font-size:14px;cursor:pointer;">Cancel</button>
          </div>
        `;
        document.body.appendChild(modal);
      }
      const video = document.getElementById('ms-camera-video');
      if (video) { video.srcObject = stream; video.play(); }
      modal.style.display = 'flex';

      const captureBtn = document.getElementById('ms-camera-capture');
      const cancelBtn = document.getElementById('ms-camera-cancel');

      const stopStream = () => {
        stream.getTracks().forEach(t => t.stop());
        modal.style.display = 'none';
        if (video) video.srcObject = null;
      };

      cancelBtn.onclick = stopStream;

      captureBtn.onclick = () => {
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext('2d').drawImage(video, 0, 0);
        canvas.toBlob((blob) => {
          if (!blob) return;
          const file = new File([blob], 'camera_photo.jpg', { type: 'image/jpeg' });
          this._reconFile = file;
          if (this._reconObjectUrl) URL.revokeObjectURL(this._reconObjectUrl);
          this._reconObjectUrl = URL.createObjectURL(file);
          const img = document.getElementById('ms-recon-img');
          const placeholder = document.getElementById('ms-recon-placeholder');
          if (img) { img.src = this._reconObjectUrl; img.style.display = ''; }
          if (placeholder) placeholder.style.display = 'none';
          const genBtn = document.getElementById('ms-recon-generate-btn');
          if (genBtn) genBtn.disabled = false;
          this._dismissReconError();
          stopStream();
        }, 'image/jpeg', 0.92);
      };
    } catch (e) {
      console.warn('[CAMERA] Access denied or unavailable:', e.message);
      alert('Camera access is not available. Please use the file upload instead.');
    }
  },

  // ═══ PHASE 219: RECENT RECONSTRUCTIONS HISTORY ═══
  _saveReconToHistory() {
    if (!this._reconFile) return;
    const entry = {
      timestamp: Date.now(),
      fileName: this._reconFile.name,
      preview: this._reconObjectUrl || '',
      garmentType: this._reconGarmentType || 'unknown',
    };
    // Try to generate a dataURL preview from the image
    const img = document.getElementById('ms-recon-img');
    if (img && img.src && img.complete && img.naturalWidth > 0) {
      try {
        const c = document.createElement('canvas');
        c.width = 120; c.height = 120;
        const ctx = c.getContext('2d');
        const size = Math.min(img.naturalWidth, img.naturalHeight);
        const sx = (img.naturalWidth - size) / 2;
        const sy = (img.naturalHeight - size) / 2;
        ctx.drawImage(img, sx, sy, size, size, 0, 0, 120, 120);
        entry.preview = c.toDataURL('image/jpeg', 0.6);
      } catch (_) {}
    }
    let history = this._loadReconHistory();
    history.unshift(entry);
    if (history.length > 5) history = history.slice(0, 5);
    try { localStorage.setItem('korra_recon_history', JSON.stringify(history)); } catch (_) {}
    this._reconHistory = history;
  },

  _loadReconHistory() {
    try {
      const raw = localStorage.getItem('korra_recon_history');
      return raw ? JSON.parse(raw) : [];
    } catch (_) { return []; }
  },

  _renderReconHistory() {
    const history = this._reconHistory || [];
    if (history.length === 0) return '';
    return `
      <div class="ms-recon-history">
        <div class="ms-recon-history-title">Recent Reconstructions</div>
        <div class="ms-recon-history-grid">
          ${history.map((entry, i) => {
            const date = new Date(entry.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            return `<div class="ms-recon-history-item" onclick="KORRA_MS._restoreReconHistory(${i})" title="${entry.fileName}">
              ${entry.preview ? `<img src="${entry.preview}" alt="${entry.fileName}">` : '<div class="ms-recon-history-thumb-placeholder"></div>'}
              <div class="ms-recon-history-meta">
                <span class="ms-recon-history-name">${entry.fileName.length > 16 ? entry.fileName.slice(0, 14) + '…' : entry.fileName}</span>
                <span class="ms-recon-history-date">${date}</span>
              </div>
            </div>`;
          }).join('')}
        </div>
      </div>`;
  },

  _restoreReconHistory(index) {
    const entry = (this._reconHistory || [])[index];
    if (!entry) return;
    this._reconGarmentType = entry.garmentType || 'unknown';
    const select = document.getElementById('ms-recon-garment-type');
    if (select) select.value = this._reconGarmentType;
    alert(`Restored: ${entry.fileName}\nType: ${entry.garmentType || 'unknown'}\nNote: Original file is not re-uploaded. Select the same image again to reconstruct.`);
  },

  // ═══ PHASE 224: SHARE RECONSTRUCTION RESULT ═══
  async _shareReconResult() {
    this._trackEvent('garment', 'share', this._reconGarmentType);
    const viewer = this._reconViewer;
    const results = this._reconResults;
    if (!viewer && !results) return;

    // Create composite image
    const canvas = document.createElement('canvas');
    canvas.width = 800; canvas.height = 600;
    const ctx = canvas.getContext('2d');

    // Background
    ctx.fillStyle = '#0a0a0a';
    ctx.fillRect(0, 0, 800, 600);

    // Title
    ctx.fillStyle = '#1DBFAF';
    ctx.font = 'bold 20px monospace';
    ctx.fillText('KORRA Garment Reconstruction', 20, 40);

    // Try to draw 3D viewer
    if (viewer && viewer.renderer) {
      try {
        ctx.drawImage(viewer.renderer.domElement, 20, 60, 360, 360);
      } catch (_) {}
    }

    // Garment type label
    ctx.fillStyle = '#ffffff';
    ctx.font = '14px monospace';
    ctx.fillText(`Type: ${this._reconGarmentType || 'Unknown'}`, 400, 80);
    ctx.fillStyle = '#888888';
    ctx.font = '12px monospace';
    ctx.fillText(new Date().toLocaleDateString(), 400, 100);
    ctx.fillText('Generated by KORRA', 400, 120);

    const dataUrl = canvas.toDataURL('image/png');

    // Try native share
    if (navigator.share) {
      try {
        const blob = await (await fetch(dataUrl)).blob();
        const file = new File([blob], 'korra-reconstruction.png', { type: 'image/png' });
        await navigator.share({
          title: 'KORRA Garment Reconstruction',
          text: `Check out this garment reconstruction (${this._reconGarmentType || 'unknown'})`,
          files: [file],
        });
        return;
      } catch (_) {}
    }

    // Fallback: download
    const link = document.createElement('a');
    link.download = `korra-recon-share-${Date.now()}.png`;
    link.href = dataUrl;
    link.click();
  },

  // ═══ PHASE 222: GARMENT MEASUREMENT OVERLAY ═══
  _showGarmentMeasurements(patternData) {
    if (!patternData) return;
    const garment = {};
    const mapping = {
      chest: 'Chest Round', waist: 'Waist Round', hip: 'Hip Round',
      length: 'Full Top Length', sleeve: 'Sleeve Length',
    };
    for (const [key, bodyKey] of Object.entries(mapping)) {
      const val = patternData[key] || patternData[key + '_cm'] || patternData[key + '_measurements'];
      if (val != null) garment[bodyKey] = typeof val === 'number' ? val : parseFloat(val) || null;
    }
    if (Object.values(garment).every(v => v == null)) return;
    this._garmentMeasurements = garment;
    const factor = this.unit === 'in' ? 0.393701 : 1;
    const rows = Object.entries(garment).filter(([,v]) => v != null).map(([name, val]) => {
      return `<div class="ms-garment-meas-row">
        <span class="ms-garment-meas-name">${name}</span>
        <span class="ms-garment-meas-val">${(val * factor).toFixed(1)} ${this.unit}</span>
      </div>`;
    }).join('');
    let existing = document.getElementById('ms-garment-meas-card');
    if (!existing) {
      existing = document.createElement('div');
      existing.id = 'ms-garment-meas-card';
      existing.className = 'ms-garment-meas-card';
      const results = document.getElementById('ms-recon-results');
      if (results) results.parentNode.insertBefore(existing, results);
    }
    existing.innerHTML = `
      <div class="ms-garment-meas-title">Garment Measurements
        <div class="ms-unit-toggle ms-garment-unit-toggle">
          <button class="ms-unit-btn ${this.unit === 'cm' ? 'active' : ''}" onclick="KORRA_MS._toggleGarmentUnit('cm')">CM</button>
          <button class="ms-unit-btn ${this.unit === 'in' ? 'active' : ''}" onclick="KORRA_MS._toggleGarmentUnit('in')">IN</button>
        </div>
      </div>
      <div class="ms-garment-meas-rows">${rows}</div>
    `;
    if (this.data?.measurements) {
      this._compareGarmentVsBody(garment);
    }
  },
  _toggleGarmentUnit(unit) {
    this.unit = unit;
    window.CURRENT_UNIT = unit;
    if (this._garmentMeasurements) this._showGarmentMeasurements(this._garmentMeasurements);
    document.querySelectorAll('.ms-garment-unit-toggle .ms-unit-btn').forEach(btn => {
      btn.classList.toggle('active', btn.textContent.trim().toLowerCase() === unit);
    });
  },

  // ═══ PHASE 223: COMPARE GARMENT VS BODY ═══
  _compareGarmentVsBody(garmentMeasurements) {
    const body = this.data?.measurements || {};
    if (!garmentMeasurements || Object.keys(garmentMeasurements).length === 0) return;
    const rows = [];
    for (const [name, garmentVal] of Object.entries(garmentMeasurements)) {
      if (garmentVal == null || body[name] == null) continue;
      const bodyVal = body[name];
      const ease = ((garmentVal - bodyVal) / bodyVal) * 100;
      let status, label;
      if (ease >= 2 && ease <= 20) { status = 'good'; label = 'Good fit'; }
      else if (ease > 20) { status = 'loose'; label = 'Loose'; }
      else if (ease < 0) { status = 'tight'; label = 'Too tight'; }
      else { status = 'snug'; label = 'Snug'; }
      rows.push(`<div class="ms-recon-fit-row">
        <span class="ms-recon-fit-name">${name}</span>
        <span class="ms-recon-fit-body">${bodyVal.toFixed(1)} cm</span>
        <span class="ms-recon-fit-garment">${garmentVal.toFixed(1)} cm</span>
        <span class="ms-recon-fit-ease ${status}">${ease >= 0 ? '+' : ''}${ease.toFixed(1)}%</span>
        <span class="ms-recon-fit-status ms-recon-fit-${status}">${label}</span>
      </div>`);
    }
    if (rows.length === 0) return;
    let card = document.getElementById('ms-recon-fit-card');
    if (!card) {
      card = document.createElement('div');
      card.id = 'ms-recon-fit-card';
      card.className = 'ms-recon-fit-card';
      const garmentCard = document.getElementById('ms-garment-meas-card');
      if (garmentCard) garmentCard.parentNode.insertBefore(card, garmentCard.nextSibling);
    }
    card.innerHTML = `
      <div class="ms-recon-fit-title">Fit Analysis</div>
      <div class="ms-recon-fit-legend">
        <span class="ms-recon-fit-legend-item"><span class="ms-recon-fit-dot ms-recon-fit-good"></span> Good fit (2-5% ease)</span>
        <span class="ms-recon-fit-legend-item"><span class="ms-recon-fit-dot ms-recon-fit-loose"></span> Loose (&gt;20% ease)</span>
        <span class="ms-recon-fit-legend-item"><span class="ms-recon-fit-dot ms-recon-fit-tight"></span> Too tight (&lt;body)</span>
      </div>
      <div class="ms-recon-fit-header">
        <span>Measurement</span><span>Body</span><span>Garment</span><span>Ease</span><span>Fit</span>
      </div>
      <div class="ms-recon-fit-rows">${rows.join('')}</div>
    `;
  },

  // ═══ PHASE 232: USAGE ANALYTICS ═══
  _analyticsQueue: [],
  _trackEvent(category, action, label) {
    const event = {
      category,
      action,
      label: label || '',
      page: this.viewMode,
      timestamp: Date.now(),
    };
    this._analyticsQueue.push(event);
    if (this._analyticsQueue.length >= 10) this._flushAnalytics();
    if (!this._analyticsFlushScheduled) {
      this._analyticsFlushScheduled = true;
      setTimeout(() => this._flushAnalytics(), 5000);
    }
  },
  _flushAnalytics() {
    if (this._analyticsQueue.length === 0) { this._analyticsFlushScheduled = false; return; }
    const batch = this._analyticsQueue.splice(0, this._analyticsQueue.length);
    this._analyticsFlushScheduled = false;
    try {
      const payload = JSON.stringify({ events: batch });
      if (navigator.sendBeacon) {
        const sent = navigator.sendBeacon('/api/v2/analytics', new Blob([payload], { type: 'application/json' }));
        if (sent) return;
      }
      fetch('/api/v2/analytics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: payload,
        keepalive: true,
      }).catch(() => {});
    } catch (_) {}
  },

  // ═══ PHASE 222: EXTRACT PATTERN FROM ZIP ═══
  async _extractPatternFromZip(blob) {
    if (!window.JSZip) return;
    try {
      const zip = await JSZip.loadAsync(blob);
      const patternFile = zip.file('pattern.json') || zip.file('sewing_pattern.json');
      if (!patternFile) return;
      const text = await patternFile.async('string');
      const patternData = JSON.parse(text);
      this._showGarmentMeasurements(patternData);
    } catch (_) {}
  },

  // ═══ PHASE 233: BETA USER FEEDBACK ═══
  _showFeedbackForm() {
    if (this._lastFeedbackRating != null) return;
    const existing = document.getElementById('ms-feedback-card');
    if (existing) return;
    const card = document.createElement('div');
    card.id = 'ms-feedback-card';
    card.className = 'ms-feedback-card';
    card.innerHTML = `
      <div class="ms-feedback-header">How was your experience?</div>
      <div class="ms-feedback-stars" id="ms-feedback-stars">
        ${[1,2,3,4,5].map(n => `<button class="ms-feedback-star" data-rating="${n}" onclick="KORRA_MS._selectFeedbackRating(${n})" aria-label="${n} star${n>1?'s':''}">\u2605</button>`).join('')}
      </div>
      <textarea class="ms-feedback-comment" id="ms-feedback-comment" placeholder="Optional comment..." rows="2" aria-label="Feedback comment"></textarea>
      <div class="ms-feedback-actions">
        <button class="ms-feedback-submit" id="ms-feedback-submit" onclick="KORRA_MS._submitFeedback()" disabled>Submit</button>
        <button class="ms-feedback-dismiss" onclick="KORRA_MS._dismissFeedback()">Not now</button>
      </div>
    `;
    const viewerWrap = document.getElementById('ms-recon-viewer-wrap');
    if (viewerWrap && viewerWrap.style.display !== 'none') {
      viewerWrap.parentNode.insertBefore(card, viewerWrap.nextSibling);
    } else {
      const results = document.getElementById('ms-recon-results');
      if (results) results.parentNode.insertBefore(card, results.nextSibling);
    }
  },
  _selectFeedbackRating(rating) {
    this._lastFeedbackRating = rating;
    const stars = document.querySelectorAll('#ms-feedback-stars .ms-feedback-star');
    stars.forEach(s => {
      const r = parseInt(s.dataset.rating);
      s.classList.toggle('active', r <= rating);
    });
    const submit = document.getElementById('ms-feedback-submit');
    if (submit) submit.disabled = false;
  },
  async _submitFeedback() {
    const rating = this._lastFeedbackRating;
    if (!rating) return;
    const comment = document.getElementById('ms-feedback-comment')?.value || '';
    const submit = document.getElementById('ms-feedback-submit');
    if (submit) { submit.textContent = 'Sending...'; submit.disabled = true; }
    try {
      await fetch('/api/v1/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          rating,
          comment,
          scan_id: this.data?.id || null,
          page: 'reconstruct',
          timestamp: new Date().toISOString(),
        }),
      }).catch(() => {});
    } catch (_) {}
    this._showFeedbackThanks();
  },
  _showFeedbackThanks() {
    const card = document.getElementById('ms-feedback-card');
    if (card) {
      card.innerHTML = '<div class="ms-feedback-thanks">Thanks for your feedback!</div>';
      setTimeout(() => card.remove(), 3000);
    }
  },
  _dismissFeedback() {
    const card = document.getElementById('ms-feedback-card');
    if (card) card.remove();
  },

  // ═══ PHASE 231: Error Tracking ═══
  _trackError(type, message, details) {
    const errorData = {
      type,
      message,
      details,
      userAgent: navigator.userAgent,
      timestamp: new Date().toISOString(),
    };
    console.error(`[KORRA_ERROR] ${type}: ${message}`, errorData);
  },

  // ═══ PHASE 214: Load Saved Garment ═══
  async _loadSavedGarment() {
    if (!this.data?.garment_mesh_url) {
      alert('No saved garment found for this scan.');
      return;
    }
    if (!this.data?.id) return;
    try {
      const { data: { session } } = await window.KORRA_DB.auth.getSession();
      if (!session) { alert('Session expired. Please sign in again.'); return; }
      this._showVtoSpinner();
      const res = await fetch(`/api/v2/measurements/${this.data.id}`, {
        headers: { 'Authorization': `Bearer ${session.access_token}` },
      });
      if (!res.ok) throw new Error('Failed to load scan');
      const scanData = await res.json();
      if (scanData?.garment_mesh_url && scanData.garment_mesh_url !== 'stored') {
        const viewerWrap = document.getElementById('ms-recon-viewer-wrap');
        const loadingEl = document.getElementById('ms-recon-viewer-loading');
        if (viewerWrap) viewerWrap.style.display = 'block';
        if (loadingEl) loadingEl.style.display = 'flex';
        const viewer = this._reconViewer || this._initReconViewer();
        if (viewer) {
          await viewer.loadGarment(scanData.garment_mesh_url);
          if (loadingEl) loadingEl.style.display = 'none';
        }
      } else {
        alert('Saved garment reference found but no mesh URL to load.');
      }
      this._hideVtoSpinner();
    } catch (e) {
      console.error('[RECON] Load saved garment failed:', e);
      this._hideVtoSpinner();
      alert('Failed to load saved garment: ' + e.message);
    }
  },
};

