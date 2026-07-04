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
    this.compareHistory = (window.masterHistory || []).filter(s => s.client_name === data.client_name);
    // Preload mesh IMMEDIATELY — starts fetch while HTML renders
    const meshUrl = data.mesh_storage_url || data.mesh_url;
    if (meshUrl && window.KORRA_VIZ) {
      window.KORRA_VIZ.preloadMesh(meshUrl);
    }
    this.render();
    if (this.sideBySide) {
      const root = document.querySelector('#view-scanresult .ms-root');
      if (root) {
        root.classList.add('ms-side-by-side');
        this._wrapRightCol();
      }
    }
    // Suppress page scroll — only sheet body scrolls
    document.querySelector('main').style.overflow = 'hidden';

    // Full-viewport: hide sidebar, remove margin/padding so content is flush
    if (window.innerWidth <= 900) {
      const bottomNav = document.querySelector('.sidebar-nav');
      if (bottomNav) bottomNav.style.display = 'none';
      const mainContent = document.querySelector('.main-content');
      if (mainContent) {
        mainContent.style.marginLeft = '0';
        mainContent.style.padding = '0';
      }
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
              <div class="ms-scan-title">${name}</div>
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
          <div class="ms-controls-buttons">
            <button class="ms-share-btn" onclick="KORRA_MS.openShareScan()" title="Share scan">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>
              Share
            </button>
            <button class="ms-header-btn" onclick="KORRA_MS.exportPDF()" title="Export PDF">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
            </button>
            <button class="ms-header-btn" onclick="KORRA_MS.downloadOBJ()" title="Download OBJ">
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
      default: content = this.buildMetricsGrid();
    }
    if (this.viewMode === 'ai') return content;
    return content + this.buildNotesHTML();
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
    if (this.viewMode !== 'ai') content += this.buildNotesHTML();
    body.innerHTML = content;
    void body.scrollHeight; // force reflow for correct scroll extent
    if (this.viewMode === 'compare') this.initCompareViewers();
    this.updateBadge();
  },

  // ═══ VIEW MODE ═══
  switchView(mode) {
    if (mode === 'ai' && this.viewMode !== mode) this._previousView = this.viewMode;
    this.viewMode = mode;
    document.querySelectorAll('#view-scanresult .ms-tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`#view-scanresult .ms-tab[onclick*="${mode}"]`)?.classList.add('active');
    const body = document.getElementById('ms-sheet-body');
    if (body) {
      if (mode === 'ai' || mode === 'pattern') {
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
           else sheet.classList.remove('ai-active');
        }

        document.querySelectorAll('#view-scanresult .ms-header-btn, #view-scanresult .ms-share-btn').forEach(btn => {
          btn.style.display = 'none';
        });

        if (mode === 'ai') document.body.classList.add('ai-mode');
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
        if (sheet) sheet.classList.remove('ai-active');

        if (window.innerWidth > 900) {
          // const bottomNav = document.querySelector('.sidebar-nav');
          // if (bottomNav) bottomNav.style.display = '';
        }

        document.querySelectorAll('#view-scanresult .ms-header-btn, #view-scanresult .ms-share-btn').forEach(btn => {
          btn.style.display = '';
        });

        document.body.classList.remove('ai-mode');
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
      this._hideVtoSpinner();
      const vtoControls = document.getElementById('ms-vto-controls');
      if (vtoControls) vtoControls.style.display = 'none';
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

  // ═══ CRAFTSMAN NOTES ═══
  async saveNotes() {
    const notes = document.getElementById('ms-notes-input')?.value;
    if (notes == null) return;
    const btn = document.querySelector('.ms-notes-save');
    if (btn) { btn.disabled = true; btn.textContent = 'SAVING...'; }
    try {
      const { error } = await window.KORRA_DB.from('measurements').update({ notes }).eq('id', this.data.id);
      if (error) throw error;
      this.data.notes = notes;
      if (btn) { btn.textContent = 'SAVED'; setTimeout(() => { btn.textContent = 'Save Notes'; }, 1500); }
    } catch(e) {
      if (btn) { btn.textContent = 'FAILED'; setTimeout(() => { btn.textContent = 'Save Notes'; }, 1500); }
    } finally { if (btn) btn.disabled = false; }
  },
  buildNotesHTML() {
    const notes = this.data?.notes || '';
    return `
      <div class="ms-notes-section">
        <div class="ms-notes-label">CRAFTSMAN NOTES</div>
        <textarea class="ms-notes-input" id="ms-notes-input"
          placeholder="Enter patterns, fabrics, or specific tailoring requirements...">${notes}</textarea>
        <button class="ms-notes-save" onclick="KORRA_MS.saveNotes()">Save Notes</button>
      </div>`;
  },

  // ═══ EXPORT ═══
  exportPDF() {
    if (window.KORRA_EXPORT && window.KORRA_EXPORT.pdf) {
      window.KORRA_EXPORT.pdf(this.data.client_name, this.data.measurements, this.data.gender, this.data.height);
    }
  },
  async downloadOBJ() {
    if (!this.data?.mesh_url) return;
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
    this.closeSideMenu();
    document.getElementById('ms-side-menu')?.remove();
    document.getElementById('ms-side-menu-backdrop')?.remove();

    // Phase 112: Restore Navigation and Layout
    if (window.innerWidth <= 900) {
      const bottomNav = document.querySelector('.sidebar-nav');
      if (bottomNav) bottomNav.style.display = '';

      const content = document.querySelector('.main-content');
      if (content) {
        content.style.marginLeft = '';
        content.style.padding = '';
      }
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
};

