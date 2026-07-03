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
  // Phases 10-13: Pattern system state
  patternViewMode: '2d',
  activePattern: null,
  simulationActive: false,
  downloadFormat: 'dxf',
  showEased: true,
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
    if (data.freesewing_data && !data.freesewing) data.freesewing = data.freesewing_data;
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

    // Remove main-content padding so viewport is flush against sidebar
    const mainContent = document.querySelector('.main-content');
    if (mainContent) { mainContent.style.padding = '0'; }

    // Phase 112: Desktop Sidebar Visibility Fix
    // Only hide navigation and reset margins on mobile
    if (window.innerWidth <= 900) {
      const bottomNav = document.querySelector('.sidebar-nav');
      if (bottomNav) bottomNav.style.display = 'none';
      if (mainContent) { mainContent.style.marginLeft = '0'; }
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
            <svg class="ms-tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 6h16M4 12h16M4 18h16"/><rect x="2" y="3" width="20" height="18" rx="2"/></svg>
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
      case 'ai': content = this.buildAIView(); break;
      case 'pattern': content = this.buildPatternView(); break;
      default: content = this.buildMetricsGrid();
    }
    if (this.viewMode === 'ai') return content;
    if (this.viewMode === 'pattern') return content;
    return content + this.buildNotesHTML();
  },

  buildAIView() {
    return `<div class="ms-ai-view">
      <div class="ms-ai-topbar">
        <button class="ms-ai-back" onclick="KORRA_MS.closeAI()">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
          Back to Measurements
        </button>
      </div>
      <div class="ms-ai-header">
        <div class="ms-ai-title">AI Assistant</div>
        <div class="ms-ai-subtitle">Ask anything about your measurements</div>
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

  // ═══ PATTERN VIEW (Phases 29-36) ═══
  buildPatternView() {
    return `<div class="ms-pattern-view">
      <div class="ms-pattern-backbar">
        <button class="ms-pattern-back-btn" onclick="KORRA_MS.closePattern()">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
          Back to Measurements
        </button>
      </div>
      <div class="ms-pattern-topbar">
        <div class="ms-pattern-title">Pattern Draft</div>
        <div class="ms-pattern-controls">
          <button class="ms-pattern-btn" onclick="KORRA_MS.patternZoomIn()" title="Zoom in">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/></svg>
          </button>
          <button class="ms-pattern-btn" onclick="KORRA_MS.patternZoomOut()" title="Zoom out">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="8" y1="11" x2="14" y2="11"/></svg>
          </button>
          <button class="ms-pattern-btn" onclick="KORRA_MS.patternReset()" title="Reset view">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
          </button>
          <button class="ms-pattern-btn" onclick="KORRA_MS.renderPattern()" title="Regenerate pattern">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 4v6h6M23 20v-6h-6"/><path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"/></svg>
          </button>
        </div>
      </div>
      <div class="ms-pattern-canvas-wrap" id="ms-pattern-canvas-wrap">
        <div class="ms-pattern-canvas" id="ms-pattern-canvas"></div>
        <div class="ms-pattern-zoom-indicator" id="ms-pattern-zoom-indicator">100%</div>
      </div>
      <div class="ms-pattern-footer">
        <span class="ms-pattern-footer-label">${this.activeContext.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())} · ${window.getAttire(this.activeContext)?.patternType || 'N/A'}</span>
        <button class="ms-pattern-download-btn" onclick="KORRA_MS.openPatternDownloadModal()">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          Download
        </button>
      </div>
    </div>`;
  },

  // ═══ PATTERN ZOOM/PAN (Phase 35) ═══
  _patternZoom: 1,
  _patternPanX: 0,
  _patternPanY: 0,
  _patternPanning: false,
  _patternPanStartX: 0,
  _patternPanStartY: 0,
  _patternPanStartPanX: 0,
  _patternPanStartPanY: 0,

  _getPatternCanvas() {
    return document.getElementById('ms-pattern-canvas');
  },

  _updatePatternZoom() {
    const canvas = this._getPatternCanvas();
    const ind = document.getElementById('ms-pattern-zoom-indicator');
    if (!canvas) return;
    canvas.style.transform = `translate(${this._patternPanX}px, ${this._patternPanY}px) scale(${this._patternZoom})`;
    if (ind) ind.textContent = Math.round(this._patternZoom * 100) + '%';
  },

  patternZoomIn() {
    this._patternZoom = Math.min(this._patternZoom * 1.2, 5);
    this._updatePatternZoom();
  },

  patternZoomOut() {
    this._patternZoom = Math.max(this._patternZoom / 1.2, 0.2);
    this._updatePatternZoom();
  },

  patternReset() {
    this._patternZoom = 1;
    this._patternPanX = 0;
    this._patternPanY = 0;
    this._updatePatternZoom();
  },

  _initPatternPan() {
    const wrap = document.getElementById('ms-pattern-canvas-wrap');
    if (!wrap) return;
    wrap.addEventListener('mousedown', (e) => {
      if (e.button !== 0) return;
      this._patternPanning = true;
      this._patternPanStartX = e.clientX;
      this._patternPanStartY = e.clientY;
      this._patternPanStartPanX = this._patternPanX;
      this._patternPanStartPanY = this._patternPanY;
      wrap.style.cursor = 'grabbing';
    });
    window.addEventListener('mousemove', (e) => {
      if (!this._patternPanning) return;
      this._patternPanX = this._patternPanStartPanX + (e.clientX - this._patternPanStartX);
      this._patternPanY = this._patternPanStartPanY + (e.clientY - this._patternPanStartY);
      this._updatePatternZoom();
    });
    window.addEventListener('mouseup', () => {
      if (!this._patternPanning) return;
      this._patternPanning = false;
      const wrap = document.getElementById('ms-pattern-canvas-wrap');
      if (wrap) wrap.style.cursor = 'grab';
    });
    wrap.addEventListener('wheel', (e) => {
      e.preventDefault();
      if (e.deltaY > 0) this.patternZoomOut();
      else this.patternZoomIn();
    }, { passive: false });
    wrap.style.cursor = 'grab';
  },

  // ═══ PATTERN RENDER — Server-backed with client fallback ═══
  _PATTERN_API_BASE: '/api/pattern',

  _buildMeasurementsDict() {
    // Prefer pre-computed Freesewing dict (mm) from Python backend
    const fs = this.data?.freesewing;
    if (fs && typeof fs === 'object' && fs.chest != null) {
      return { ...fs, _source: 'freesewing' };
    }
    // Fall back to KORRA keys (cm) from scan measurements
    const mKeys = ['Across Shoulder','Neck to Waist','Waist to Hip','Sleeve Length','Inseam',
                   'Chest Round','Waist Round','Hip Round','Shoulder','Neck Round',
                   'Thigh Round','Calf Round','Bicep Round','Wrist Round'];
    const measurements = {};
    mKeys.forEach(k => { measurements[k] = this.getPatternMeasurements(k); });
    measurements._source = 'korra';
    return measurements;
  },

  async _fetchServerPattern(pType, measurements) {
    const isFS = measurements._source === 'freesewing';
    const body = { patternType: pType };
    if (isFS) {
      const { _source, ...fsData } = measurements;
      body.freesewing = fsData;
    } else {
      body.measurements = measurements;
    }
    const res = await fetch(`${this._PATTERN_API_BASE}/draft`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`Server returned ${res.status}`);
    return res.json();
  },

  async _fetchServerDXF(pType, measurements) {
    const isFS = measurements._source === 'freesewing';
    const body = { patternType: pType, format: 'dxf' };
    if (isFS) {
      const { _source, ...fsData } = measurements;
      body.freesewing = fsData;
    } else {
      body.measurements = measurements;
    }
    const res = await fetch(`${this._PATTERN_API_BASE}/export?format=dxf`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`Server returned ${res.status}`);
    return res.blob();
  },

  async renderPattern() {
    const canvas = this._getPatternCanvas();
    if (!canvas) return;
    const attire = window.getAttire(this.activeContext);
    const pType = attire?.patternType || 'shirt';
    const measurements = this._buildMeasurementsDict();
    // Show loading state
    canvas.innerHTML =
      `<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#888;font:14px/1.4 Inter,sans-serif;flex-direction:column;gap:12px">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="animation:ms-spin 1s linear infinite"><circle cx="12" cy="12" r="10" stroke-dasharray="40" stroke-dashoffset="30"/></svg>
        Drafting pattern…
      </div>`;
    try {
      const result = await this._fetchServerPattern(pType, measurements);
      // Embed server SVG; patch styles to match dark theme
      let serverSvg = result.svg;
      // Override svg width/height to fill canvas, keep viewBox
      const w = canvas.clientWidth || 800;
      const h = canvas.clientHeight || 600;
      serverSvg = serverSvg.replace(/<svg/, `<svg width="${w}" height="${h}"`);
      // Inject dark-theme overrides
      const darkStyle = `
      <style>
        .p-outline, .fabric { fill: rgba(198, 255, 0, 0.05); stroke: var(--Mint, #C6FF00); stroke-width: 1.5; }
        .p-seam, .seam { stroke: rgba(255,255,255,0.2); stroke-width: 0.8; stroke-dasharray: 4,3; fill: none; }
        .p-grain, .grainline { stroke: rgba(255,255,255,0.15); stroke-width: 0.5; }
        .p-dart, .dart { fill: rgba(255,200,100,0.15); }
        text { fill: rgba(255,255,255,0.5); font-family: Inter, sans-serif; font-size: 9px; text-anchor: middle; }
        .p-notch, .notch { fill: var(--Mint, #C6FF00); }
      </style>`;
      serverSvg = serverSvg.replace(/<\/svg>/, `${darkStyle}</svg>`);
      canvas.innerHTML = serverSvg;
    } catch (err) {
      console.warn('Pattern server unavailable, falling back to client templates:', err.message);
      this._renderPatternFallback(canvas, pType, measurements);
    }
    this._initPatternPan();
  },

  _renderPatternFallback(canvas, pType, measurements) {
    const template = this.PATTERN_TEMPLATES[pType];
    const pieceNames = template?.pieces || ['shirt_front', 'shirt_back'];
    const width = canvas.clientWidth || 400;
    const height = canvas.clientHeight || 400;
    const svgNS = 'http://www.w3.org/2000/svg';
    let svg = `<svg xmlns="${svgNS}" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}">
      <rect width="${width}" height="${height}" fill="none"/>
      <style>
        .p-outline { fill: rgba(198, 255, 0, 0.05); stroke: var(--Mint, #C6FF00); stroke-width: 1.5; }
        .p-seam { stroke: rgba(255,255,255,0.2); stroke-width: 0.8; stroke-dasharray: 4,3; fill: none; }
        .p-grain { stroke: rgba(255,255,255,0.15); stroke-width: 0.5; }
        .p-dart { fill: rgba(255,200,100,0.15); }
        .p-label { fill: rgba(255,255,255,0.5); font-size: 9px; font-family: 'Inter', sans-serif; text-anchor: middle; white-space: pre-line; }
        .p-notch { fill: var(--Mint, #C6FF00); }
      </style>`;
    const baseScale = 2.5;
    PatternDraft.init(baseScale);
    const cols = Math.min(pieceNames.length, 2);
    const rows = Math.ceil(pieceNames.length / cols);
    const pad = 15;
    const cellW = (width - pad * (cols + 1)) / cols;
    const cellH = (height - pad * (rows + 1)) / rows;
    pieceNames.forEach((piece, i) => {
      const col = i % cols;
      const row = Math.floor(i / cols);
      const sectionKey = piece.replace(/-/g, '_');
      const fnName = PatternDraft.sectionTemplate(sectionKey);
      const fabricPreset = this.FABRIC_PRESETS[this.activeMaterial] || this.FABRIC_PRESETS.woven;
      const K = fabricPreset.K ?? 0.8;
      const easeCm = K >= 0.85 ? 0.9 : K >= 0.5 ? 1.5 : 2.0;
      const seamAllow = this.SEAM_ALLOWANCE_DEFAULTS[pType] || 1.0;
      let pieceSvg = '';
      let pw = 50, ph = 50;
      if (fnName && PatternTemplates[fnName]) {
        const result = PatternTemplates[fnName](measurements, { ease: easeCm });
        pieceSvg = result.svg;
        pw = result.size.w;
        ph = result.size.h;
        PatternDraft.init(baseScale);
        pieceSvg += PatternDraft.drawSeamAllowance(0, 0, pw, ph, seamAllow, {stroke:'rgba(255,255,255,0.12)'});
      } else {
        pw = cellW / baseScale * 0.8;
        ph = cellH / baseScale * 0.8;
        pieceSvg = PatternDraft.drawRect(2, 2, pw-4, ph-4, {rx:4, class:'p-outline', stroke:'#fff'})
          + PatternDraft.drawLabel(piece.replace(/_/g,' ').replace(/\b\w/g,l=>l.toUpperCase()), pw/2, ph/2, {color:'#fff'});
      }
      const s = Math.min(cellW / (pw * baseScale), cellH / (ph * baseScale), 2);
      const ox = pad + col * (cellW + pad) + (cellW - pw * baseScale * s) / 2;
      const oy = pad + row * (cellH + pad) + (cellH - ph * baseScale * s) / 2;
      svg += `<g transform="translate(${ox}, ${oy}) scale(${s})">${pieceSvg}</g>`;
    });
    svg += '</svg>';
    canvas.innerHTML = svg;
  },

  // ═══ PATTERN DOWNLOAD MODAL (Phases 42-43) ═══
  openPatternDownloadModal() {
    const m = document.getElementById('downloadPatternModal');
    if (!m) return;
    const attire = window.getAttire(this.activeContext);
    const attireInput = document.getElementById('downloadPatternAttire');
    const matInput = document.getElementById('downloadPatternMaterial');
    const seamInput = document.getElementById('downloadPatternSeam');
    if (attireInput) attireInput.value = attire?.name || 'Standard';
    if (matInput) matInput.value = this.FABRIC_PRESETS[this.activeMaterial]?.name || 'Woven';
    if (seamInput) {
      const def = this.SEAM_ALLOWANCE_DEFAULTS[attire?.patternType || 'shirt'] || 1.0;
      seamInput.value = def;
    }
    this.downloadFormat = 'dxf';
    document.querySelectorAll('.ss-format-pill').forEach(b => b.classList.remove('active'));
    document.getElementById('ss-fmt-dxf')?.classList.add('active');
    m.style.display = 'flex';
    document.body.classList.add('modal-open');
  },

  closePatternDownloadModal() {
    const m = document.getElementById('downloadPatternModal');
    if (m) {
      m.style.display = 'none';
      document.body.classList.remove('modal-open');
    }
  },

  // ═══ PATTERN EXPORT (future Phases 86-100) ═══
  exportPattern() {
    const fmt = this.downloadFormat;
    if (fmt === 'dxf') this.exportPatternDXF();
    else this.exportPatternPDF();
  },

  async exportPatternDXF() {
    const attire = window.getAttire(this.activeContext);
    const name = (attire?.name || 'pattern').replace(/\s+/g, '_');
    const pType = attire?.patternType || 'shirt';
    const measurements = this._buildMeasurementsDict();
    try {
      const blob = await this._fetchServerDXF(pType, measurements);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${name}_pattern.dxf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.warn('DXF server unavailable, falling back to client generation:', err.message);
      const dxf = this._generateDXF();
      const blob = new Blob([dxf], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${name}_pattern.dxf`;
      a.click();
      URL.revokeObjectURL(url);
    }
    this.closePatternDownloadModal();
  },

  exportPatternPDF() {
    const attire = window.getAttire(this.activeContext);
    const name = (attire?.name || 'pattern').replace(/\s+/g, '_');
    const svgEl = this._getPatternCanvas()?.querySelector('svg');
    if (!svgEl) return;
    const svgData = new XMLSerializer().serializeToString(svgEl);
    const blob = new Blob([svgData], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${name}_pattern.svg`;
    a.click();
    URL.revokeObjectURL(url);
    this.closePatternDownloadModal();
  },

  // ── Phase 86-99: DXF-AAMA Industrial Export ──
  _dxfPt(v) { return PatternDraft.cm(v); },

  _dxfLWPolyline(points, layer, opts = {}) {
    const closed = opts.closed !== false;
    let d = `0\nLWPOLYLINE\n8\n${layer}\n90\n${points.length}\n70\n${closed ? 1 : 0}\n43\n${opts.width || 0.25}\n`;
    points.forEach(p => { d += `10\n${this._dxfPt(p.x)}\n20\n${this._dxfPt(p.y)}\n`; });
    return d;
  },

  _dxfLine(x1, y1, x2, y2, layer) {
    return `0\nLINE\n8\n${layer}\n10\n${this._dxfPt(x1)}\n20\n${this._dxfPt(y1)}\n11\n${this._dxfPt(x2)}\n21\n${this._dxfPt(y2)}\n`;
  },

  _dxfText(text, x, y, h, layer, opts = {}) {
    return `0\nTEXT\n8\n${layer}\n10\n${this._dxfPt(x)}\n20\n${this._dxfPt(y)}\n40\n${h}\n1\n${text}\n72\n1\n11\n${this._dxfPt(x)}\n21\n${this._dxfPt(y)}\n`;
  },

  _dxfCircle(cx, cy, r, layer) {
    return `0\nCIRCLE\n8\n${layer}\n10\n${this._dxfPt(cx)}\n20\n${this._dxfPt(cy)}\n40\n${this._dxfPt(r)}\n`;
  },

  _sampleBezier(p0, p1, steps = 20) {
    const pts = [];
    for (let t = 0; t <= steps; t++) {
      const s = t / steps;
      const x = (1-s)*(1-s)*(1-s)*p0.x + 3*(1-s)*(1-s)*s*(p1.cpx1||p0.x) + 3*(1-s)*s*s*(p1.cpx2||p0.x) + s*s*s*p1.x;
      const y = (1-s)*(1-s)*(1-s)*p0.y + 3*(1-s)*(1-s)*s*(p1.cpy1||p0.y) + 3*(1-s)*s*s*(p1.cpy2||p0.y) + s*s*s*p1.y;
      pts.push({ x, y });
    }
    return pts;
  },

  _dxfPieceOutline(pieceName, measurements, ease, baseX, baseY) {
    const fnName = PatternDraft.sectionTemplate(pieceName);
    if (!fnName || !PatternTemplates[fnName]) return '';
    const result = PatternTemplates[fnName](measurements, { ease });
    if (!result.svg) return '';
    // Parse the SVG paths to extract geometry
    const parser = new DOMParser();
    const doc = parser.parseFromString(`<svg xmlns="http://www.w3.org/2000/svg">${result.svg}</svg>`, 'image/svg+xml');
    const paths = doc.querySelectorAll('path');
    let dxf = '';
    paths.forEach(path => {
      const cls = path.getAttribute('class') || '';
      const d = path.getAttribute('d') || '';
      if (!d) return;
      const isSeam = cls.includes('p-seam');
      const isDart = cls.includes('p-dart');
      const layer = isSeam ? 'SEAM' : isDart ? 'INTERNAL' : 'CUTTING';
      // Parse SVG path 'd' into polyline
      const cmds = d.match(/[MmLlCcZz][^MmLlCcZz]*/g) || [];
      const pts = [];
      let cx = 0, cy = 0;
      let first = null;
      let closePath = false;
      cmds.forEach(cmd => {
        const op = cmd[0];
        const args = cmd.slice(1).trim().split(/[\s,]+/).map(Number);
        if (op === 'M' || op === 'm') {
          if (pts.length > 0) { /* new subpath, flush previous */ }
          cx = args[0]; cy = args[1];
          first = { x: cx + baseX, y: cy + baseY };
          pts.push(first);
        } else if (op === 'L' || op === 'l') {
          cx = args[0]; cy = args[1];
          pts.push({ x: cx + baseX, y: cy + baseY });
        } else if (op === 'C' || op === 'c') {
          const p0 = { x: cx, y: cy };
          const p1 = { x: args[4], y: args[5], cpx1: args[0], cpy1: args[1], cpx2: args[2], cpy2: args[3] };
          const sampled = this._sampleBezier(p0, p1, 12);
          sampled.forEach((p, i) => { if (i > 0) pts.push({ x: p.x + baseX, y: p.y + baseY }); });
          cx = args[4]; cy = args[5];
        } else if (op === 'Z' || op === 'z') {
          closePath = true;
        }
      });
      if (pts.length >= 2) {
        dxf += this._dxfLWPolyline(pts, layer, { closed: closePath, width: isSeam ? 0.15 : 0.3 });
      }
    });
    // Seam allowance overlay (from SVG)
    const rect = doc.querySelector('rect.p-seam');
    if (rect) {
      // Already rendered as path with p-seam class
    }
    // Grainlines
    const lines = doc.querySelectorAll('line');
    lines.forEach(line => {
      if (line.classList.contains('p-grain')) {
        const x1 = parseFloat(line.getAttribute('x1')) + baseX;
        const y1 = parseFloat(line.getAttribute('y1')) + baseY;
        const x2 = parseFloat(line.getAttribute('x2')) + baseX;
        const y2 = parseFloat(line.getAttribute('y2')) + baseY;
        dxf += this._dxfLine(x1 / PatternDraft.scale, y1 / PatternDraft.scale,
                              x2 / PatternDraft.scale, y2 / PatternDraft.scale, 'GRAIN');
      }
    });
    // Notches
    const notches = doc.querySelectorAll('path.p-notch');
    notches.forEach(n => {
      const d = n.getAttribute('d') || '';
      const m = d.match(/M\s+([\d.-]+)\s+([\d.-]+)/);
      if (m) {
        dxf += this._dxfCircle(
          (parseFloat(m[1]) + baseX) / PatternDraft.scale,
          (parseFloat(m[2]) + baseY) / PatternDraft.scale,
          0.2, 'NOTCH'
        );
      }
    });
    // Label
    const texts = doc.querySelectorAll('text');
    texts.forEach(t => {
      const tx = parseFloat(t.getAttribute('x') || '0');
      const ty = parseFloat(t.getAttribute('y') || '0');
      const content = t.textContent || '';
      if (content && !content.includes('FOLD')) {
        dxf += this._dxfText(content, (tx + baseX) / PatternDraft.scale,
                              (ty + baseY) / PatternDraft.scale, 0.5, 'LABEL');
      }
    });
    return dxf;
  },

  _generateDXF() {
    const attire = window.getAttire(this.activeContext);
    const pType = attire?.patternType || 'shirt';
    const template = this.PATTERN_TEMPLATES[pType];
    const pieceNames = template?.pieces || ['shirt_front', 'shirt_back'];
    // Build measurements
    const mKeys = ['Across Shoulder','Neck to Waist','Waist to Hip','Sleeve Length','Inseam',
                   'Chest Round','Waist Round','Hip Round','Shoulder','Neck Round',
                   'Thigh Round','Calf Round','Bicep Round','Wrist Round'];
    const measurements = {};
    mKeys.forEach(k => { measurements[k] = this.getPatternMeasurements(k); });
    const baseScale = 2.5;
    PatternDraft.init(baseScale);
    const easeCm = 1.5;
    // DXF-AAMA header
    let dxf = '0\nSECTION\n2\nHEADER\n9\n$ACADVER\n1\nAC1009\n9\n$INSUNITS\n70\n4\n9\n$MEASUREMENT\n70\n1\n0\nENDSEC\n';
    // LAYER table
    dxf += '0\nSECTION\n2\nTABLES\n0\nTABLE\n2\nLAYER\n70\n6\n';
    const layers = [
      ['CUTTING', '7', 'CONTINUOUS'],
      ['SEAM', '8', 'DASHED'],
      ['GRAIN', '3', 'CONTINUOUS'],
      ['NOTCH', '6', 'CONTINUOUS'],
      ['LABEL', '2', 'CONTINUOUS'],
      ['INTERNAL', '5', 'DASHED'],
    ];
    layers.forEach(([name, color, ltype]) => {
      dxf += `0\nLAYER\n2\n${name}\n70\n0\n62\n${color}\n6\n${ltype}\n`;
    });
    dxf += '0\nENDTAB\n0\nENDSEC\n';
    // ENTITIES section
    dxf += '0\nSECTION\n2\nENTITIES\n';
    const cols = Math.min(pieceNames.length, 2);
    const spacing = 60;
    let maxW = 0, maxH = 0;
    // First pass: measure pieces
    const sizes = pieceNames.map(pn => {
      const fnName = PatternDraft.sectionTemplate(pn);
      if (fnName && PatternTemplates[fnName]) {
        const r = PatternTemplates[fnName](measurements, { ease: easeCm });
        maxW = Math.max(maxW, r.size.w);
        maxH = Math.max(maxH, r.size.h);
        return r.size;
      }
      return { w: 100, h: 100 };
    });
    // Second pass: draw entities
    let cursorX = 30, cursorY = 30;
    pieceNames.forEach((piece, i) => {
      const size = sizes[i];
      // Column wrap
      if (i > 0 && i % cols === 0) { cursorX = 30; cursorY += maxH * baseScale + spacing; }
      else if (i > 0) { cursorX += maxW * baseScale + spacing; }
      const baseX = cursorX;
      const baseY = cursorY;
      // Scale base coordinates to cm (DXF stores in mm but we use cm units)
      dxf += `0\nINSERT\n2\n${piece}\n8\n0\n10\n0\n20\n0\n0\nSEQEND\n`;
      const pieceDxf = this._dxfPieceOutline(piece, measurements, easeCm, baseX, baseY);
      dxf += pieceDxf;
      // Piece bounding box
      const pw = size.w * baseScale;
      const ph = size.h * baseScale;
      dxf += `0\nLINE\n8\nCUTTING\n10\n${baseX}\n20\n${baseY}\n11\n${baseX + pw}\n21\n${baseY}\n`;
      dxf += `0\nLINE\n8\nCUTTING\n10\n${baseX}\n20\n${baseY + ph}\n11\n${baseX + pw}\n21\n${baseY + ph}\n`;
    });
    dxf += '0\nENDSEC\n0\nEOF\n';
    return dxf;
  },

  buildNotesHTML() {
    const d = this.data || {};
    return `<div class="ms-notes-section">
      <div class="ms-notes-label">CRAFTSMAN NOTES</div>
      <textarea class="ms-notes-input" id="ms-notes-input" placeholder="Patterns, fabrics, or tailoring requirements..." oninput="this.style.height='auto';this.style.height=Math.min(this.scrollHeight,200)+'px'">${d.notes || ''}</textarea>
      <button class="ms-notes-save" onclick="KORRA_MS.saveNotes()">Save Notes</button>
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
    if ((mode === 'ai' || mode === 'pattern') && this.viewMode !== mode) this._previousView = this.viewMode;
    this.viewMode = mode;
    document.querySelectorAll('#view-scanresult .ms-tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`#view-scanresult .ms-tab[onclick*="${mode}"]`)?.classList.add('active');
    const body = document.getElementById('ms-sheet-body');
    if (body) {
      if (mode === 'ai') {
        body.style.overflow = '';
        body.style.display = 'flex';
        body.style.flexDirection = 'column';
        body.style.padding = '0 20px 100px';

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
        if (sheet) sheet.classList.add('ai-active');

        document.querySelectorAll('#view-scanresult .ms-header-btn, #view-scanresult .ms-share-btn').forEach(btn => {
          btn.style.display = 'none';
        });

        document.body.classList.add('ai-mode');
      } else if (mode === 'pattern') {
        body.style.padding = '0';
        body.style.overflow = 'hidden';
        body.style.display = 'flex';
        body.style.flexDirection = 'column';

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
        if (sheet) sheet.classList.add('pattern-active');

        document.querySelectorAll('#view-scanresult .ms-header-btn, #view-scanresult .ms-share-btn').forEach(btn => {
          btn.style.display = 'none';
        });
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
        if (sheet) { sheet.classList.remove('ai-active'); sheet.classList.remove('pattern-active'); }

        if (window.innerWidth > 900) {
          const bottomNav = document.querySelector('.sidebar-nav');
          if (bottomNav) bottomNav.style.display = '';
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
  closePattern() {
    this.switchView(this._previousView || 'avatar');
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

  // ═══ PATTERN TEMPLATES (Phase 20) ═══
  PATTERN_TEMPLATES: {
    shirt:    { pieces: ['shirt_front','shirt_back','shirt_sleeve','shirt_collar'], baseEase: 0.08 },
    jacket:   { pieces: ['jacket_front','jacket_back','jacket_sleeve','shirt_collar'], baseEase: 0.12 },
    skirt:    { pieces: ['skirt_front','skirt_back'], baseEase: 0.06 },
    tunic:    { pieces: ['shirt_front','shirt_back','shirt_sleeve'], baseEase: 0.10 },
    coat:     { pieces: ['jacket_front','jacket_back','jacket_sleeve','shirt_collar'], baseEase: 0.15 },
    dress:    { pieces: ['dress_front','dress_back'], baseEase: 0.08 },
    full_body:{ pieces: ['full_body'], baseEase: 0.08 },
    wrap:     { pieces: ['dress_front'], baseEase: 0.20 },
    headwear: { pieces: ['shirt_collar'], baseEase: 0.02 },
    pants:    { pieces: ['pants_front','pants_back'], baseEase: 0.06 },
  },

  // ═══ SEAM ALLOWANCE DEFAULTS (Phase 21) ═══
  SEAM_ALLOWANCE_DEFAULTS: {
    shirt: 1.0, jacket: 1.5, skirt: 1.0, tunic: 1.2, coat: 1.5,
    dress: 1.0, full_body: 1.0, wrap: 2.0, headwear: 0.8, pants: 1.0,
  },

  // ═══ PATTERN PIECE CATALOG (Phase 22) ═══
  PATTERN_PIECE_CATALOG: {
    shirt_front:    { type:'bodice', side:'front', draftFn:'_draftShirtFront' },
    shirt_back:     { type:'bodice', side:'back',  draftFn:'_draftShirtBack' },
    sleeve:         { type:'sleeve', side:'both',  draftFn:'_draftSleeve' },
    collar:         { type:'collar', side:'both',  draftFn:'_draftCollar' },
    cuff:           { type:'cuff',   side:'both',  draftFn:'_draftCuff' },
    rib_band:       { type:'band',   side:'both',  draftFn:'_draftBand' },
    waistband:      { type:'band',   side:'both',  draftFn:'_draftWaistband' },
    belt:           { type:'belt',   side:'both',  draftFn:'_draftBelt' },
    storm_flap:     { type:'flap',   side:'front', draftFn:'_draftStormFlap' },
    epaulette:      { type:'strap',  side:'both',  draftFn:'_draftEpaulette' },
    jacket_front:   { type:'bodice', side:'front', draftFn:'_draftJacketFront' },
    jacket_back:    { type:'bodice', side:'back',  draftFn:'_draftJacketBack' },
    skirt_front:    { type:'skirt',  side:'front', draftFn:'_draftSkirtFront' },
    skirt_back:     { type:'skirt',  side:'back',  draftFn:'_draftSkirtBack' },
    pants_front:    { type:'pants',  side:'front', draftFn:'_draftPantsFront' },
    pants_back:     { type:'pants',  side:'back',  draftFn:'_draftPantsBack' },
    bodice_front:   { type:'bodice', side:'front', draftFn:'_draftBodiceFront' },
    bodice_back:    { type:'bodice', side:'back',  draftFn:'_draftBodiceBack' },
    tunic_front:    { type:'tunic',  side:'front', draftFn:'_draftTunicFront' },
    tunic_back:     { type:'tunic',  side:'back',  draftFn:'_draftTunicBack' },
    coat_front:     { type:'coat',   side:'front', draftFn:'_draftCoatFront' },
    coat_back:      { type:'coat',   side:'back',  draftFn:'_draftCoatBack' },
    neckband:       { type:'band',   side:'both',  draftFn:'_draftNeckband' },
    facing:         { type:'facing', side:'front', draftFn:'_draftFacing' },
    wrap_panel:     { type:'wrap',   side:'both',  draftFn:'_draftWrap' },
    crown:          { type:'crown',  side:'both',  draftFn:'_draftCrown' },
    brim:           { type:'brim',   side:'both',  draftFn:'_draftBrim' },
    band:           { type:'band',   side:'both',  draftFn:'_draftBand' },
    chest_pocket:   { type:'pocket', side:'front', draftFn:'_draftPocket' },
  },

  // ═══ PATTERN MEASUREMENT ACCESSOR (Phase 15) ═══
  getPatternMeasurements(key) {
    const mType = {
      'Across Shoulder': 'shoulderWidth',
      'Neck to Waist': 'neckToWaist',
      'Waist to Hip': 'waistToHip',
      'Sleeve Length': 'sleeveLength',
      'Inseam': 'inseam',
      'Chest Round': 'chestWidth',
      'Waist Round': 'waistWidth',
      'Hip Round': 'hipWidth',
      'Shoulder': 'shoulderWidth',
      'Neck Round': 'neckCirc',
      'Thigh Round': 'thighCirc',
      'Calf Round': 'calfCirc',
      'Bicep Round': 'bicepCirc',
      'Wrist Round': 'wristCirc',
    };
    const dim = mType[key];
    if (!dim) return this.getEase(key);
    const measurements = this.data?.measurements || this.data?.biometrics || {};
    return measurements[key] || 0;
  },

  // ── Track G: Virtual Mirror (Phases 141-144) ──
  async _updateGarmentForContext() {
    /**
     * Phase 143: _updateGarmentForContext()
     * Calls TailorNet API, loads into viewer.
     */
    if (this.activeContext === 'standard') {
      if (this.viewerInstance) this.viewerInstance.removeGarment();
      return;
    }

    if (!this.data || !this.viewerInstance) return;

    // Show loading spinner in badge or somewhere?
    console.log(`👗 [VTO] Generating garment for context: ${this.activeContext}`);

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
      if (result.garment_mesh_url) {
        const matPreset = this.FABRIC_PRESETS[this.activeMaterial] || this.FABRIC_PRESETS.woven;
        const matSettings = {
          color: matPreset.color ? parseInt(matPreset.color.replace('#', '0x')) : 0xFFFFFF,
          opacity: this.activeMaterial === 'silk' ? 0.6 : 0.95,
          shininess: this.activeMaterial === 'silk' ? 80 : 30
        };
        await this.viewerInstance.loadGarment(result.garment_mesh_url, matSettings);
      }
    } catch (e) {
      console.warn("Garment generation skipped or failed:", e.message);
      if (this.viewerInstance) this.viewerInstance.removeGarment();
    }
  },

  setContext(ctx) {
    console.log(`▶ setContext("${ctx}")`);
    this.activeContext = ctx;
    if ("vibrate" in navigator) navigator.vibrate(50);
    if (window.KORRA_VIZ) window.KORRA_VIZ.applyHeatmap(ctx);
    if (this._attireSelector) this._attireSelector.select(ctx);
    this.renderMeasurements();
    if (this.viewMode === 'pattern') this.renderPattern();

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
    if (this.viewMode === 'pattern') this.renderPattern();

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

  // ═══ SHARE ═══
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
    const bottomNav = document.querySelector('.sidebar-nav');
    if (bottomNav) bottomNav.style.display = '';

    const content = document.querySelector('.main-content');
    if (content) {
      content.style.marginLeft = '';
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
};

// ═══════════════════════════════════════════════════════════
// PATTERN DRAFT ENGINE — SVG Primitives (Track C: Phases 51-85)
// ═══════════════════════════════════════════════════════════

const PatternDraft = {
  // ── STATE ──
  origin: { x: 0, y: 0 },
  scale: 1,
  seamAllowance: 1.0,
  _idCounter: 0,

  // ── Phase 51: Coordinate System ──
  init(cmScale = 1) {
    this.scale = cmScale;
    this.origin = { x: 0, y: 0 };
    this._idCounter = 0;
  },

  _nextId() {
    this._idCounter++;
    return 'pd-' + this._idCounter;
  },

  cm(v) {
    return v * this.scale;
  },

  // ── Phase 52: Rectangle ──
  drawRect(x, y, w, h, opts = {}) {
    const id = this._nextId();
    const rx = opts.rx || 0;
    const cls = opts.class || 'p-outline';
    const stroke = opts.stroke || null;
    const fill = opts.fill || null;
    let extra = '';
    if (stroke) extra += ` stroke="${stroke}"`;
    if (fill) extra += ` fill="${fill}"`;
    if (opts.dash) extra += ` stroke-dasharray="${opts.dash}"`;
    return `<rect id="${id}" class="${cls}" x="${this.cm(x)}" y="${this.cm(y)}" width="${this.cm(w)}" height="${this.cm(h)}" rx="${rx}"${extra}/>`;
  },

  // ── Phase 53: Bezier Curve ──
  drawCurve(points, opts = {}) {
    if (points.length < 2) return '';
    const id = this._nextId();
    const cls = opts.class || 'p-outline';
    let d = `M ${this.cm(points[0].x)} ${this.cm(points[0].y)}`;
    for (let i = 1; i < points.length; i++) {
      const p = points[i];
      if (p.cpx1 != null && p.cpy1 != null) {
        const cpx2 = p.cpx2 != null ? p.cpx2 : p.cpx1;
        const cpy2 = p.cpy2 != null ? p.cpy2 : p.cpy1;
        d += ` C ${this.cm(p.cpx1)} ${this.cm(p.cpy1)}, ${this.cm(cpx2)} ${this.cm(cpy2)}, ${this.cm(p.x)} ${this.cm(p.y)}`;
      } else {
        d += ` L ${this.cm(p.x)} ${this.cm(p.y)}`;
      }
    }
    if (opts.close) d += ' Z';
    let extra = '';
    if (opts.stroke) extra += ` stroke="${opts.stroke}"`;
    if (opts.fill) extra += ` fill="${opts.fill}"`;
    if (opts.dash) extra += ` stroke-dasharray="${opts.dash}"`;
    return `<path id="${id}" class="${cls}" d="${d}"${extra}/>`;
  },

  // ── Phase 54: Arc ──
  drawArc(cx, cy, r, startAngle, endAngle, opts = {}) {
    const id = this._nextId();
    const cls = opts.class || 'p-outline';
    const startRad = (startAngle * Math.PI) / 180;
    const endRad = (endAngle * Math.PI) / 180;
    const x1 = cx + r * Math.cos(startRad);
    const y1 = cy + r * Math.sin(startRad);
    const x2 = cx + r * Math.cos(endRad);
    const y2 = cy + r * Math.sin(endRad);
    const largeArc = endAngle - startAngle > 180 ? 1 : 0;
    const rCm = this.cm(r);
    const d = `M ${this.cm(x1)} ${this.cm(y1)} A ${rCm} ${rCm} 0 ${largeArc} 1 ${this.cm(x2)} ${this.cm(y2)}`;
    let extra = '';
    if (opts.stroke) extra += ` stroke="${opts.stroke}"`;
    if (opts.fill) extra += ` fill="${opts.fill}"`;
    if (opts.dash) extra += ` stroke-dasharray="${opts.dash}"`;
    return `<path id="${id}" class="${cls}" d="${d}"${extra}/>`;
  },

  // ── Phase 55: Dart ──
  drawDart(x, y, width, depth, angle, opts = {}) {
    const rad = (angle * Math.PI) / 180;
    const tipX = x + depth * Math.cos(rad);
    const tipY = y - depth * Math.sin(rad);
    const halfW = width / 2;
    const perpRad = rad + Math.PI / 2;
    const lx = x + halfW * Math.cos(perpRad);
    const ly = y - halfW * Math.sin(perpRad);
    const rx = x - halfW * Math.cos(perpRad);
    const ry = y + halfW * Math.sin(perpRad);
    const cls = opts.class || 'p-dart';
    const d = `M ${this.cm(lx)} ${this.cm(ly)} L ${this.cm(tipX)} ${this.cm(tipY)} L ${this.cm(rx)} ${this.cm(ry)} Z`;
    let extra = '';
    if (opts.fill) extra += ` fill="${opts.fill}"`;
    else extra += ' fill="rgba(198,255,0,0.15)"';
    return `<path id="${this._nextId()}" class="${cls}" d="${d}"${extra}/>`;
  },

  // ── Phase 56: Grainline ──
  drawGrainline(x, y, length, angle = 0, opts = {}) {
    const id = this._nextId();
    const rad = (angle * Math.PI) / 180;
    const cosA = Math.cos(rad);
    const sinA = Math.sin(rad);
    const halfL = length / 2;
    const x1 = x - halfL * cosA;
    const y1 = y - halfL * sinA;
    const x2 = x + halfL * cosA;
    const y2 = y + halfL * sinA;
    const cls = opts.class || 'p-grain';
    let extra = '';
    if (opts.stroke) extra += ` stroke="${opts.stroke}"`;
    const arrowSize = Math.min(4, length * 0.12);
    const ax1 = x2 - arrowSize * cosA - arrowSize * 0.4 * sinA;
    const ay1 = y2 + arrowSize * sinA - arrowSize * 0.4 * cosA;
    const ax2 = x2 - arrowSize * cosA + arrowSize * 0.4 * sinA;
    const ay2 = y2 + arrowSize * sinA + arrowSize * 0.4 * cosA;
    return `<g id="${id}" class="${cls}">
      <line x1="${this.cm(x1)}" y1="${this.cm(y1)}" x2="${this.cm(x2)}" y2="${this.cm(y2)}"${extra}/>
      <polygon points="${this.cm(x2)},${this.cm(y2)} ${this.cm(ax1)},${this.cm(ay1)} ${this.cm(ax2)},${this.cm(ay2)}"${extra}/>
    </g>`;
  },

  // ── Phase 57: Seam Allowance ──
  drawSeamAllowance(x, y, w, h, allowance, opts = {}) {
    const a = allowance != null ? allowance : this.seamAllowance;
    const cls = opts.class || 'p-seam';
    return this.drawRect(x + a, y + a, w - a * 2, h - a * 2, {
      ...opts, class: cls, dash: '4,3', stroke: opts.stroke || 'rgba(255,255,255,0.2)'
    });
  },

  // ── Phase 58: Notch ──
  drawNotch(x, y, size = 4, angle = 0, opts = {}) {
    const id = this._nextId();
    const rad = (angle * Math.PI) / 180;
    const h = size;
    const w = size * 0.6;
    const tipX = x + h * Math.cos(rad);
    const tipY = y - h * Math.sin(rad);
    const perpRad = rad + Math.PI / 2;
    const lx = x + w * Math.cos(perpRad);
    const ly = y - w * Math.sin(perpRad);
    const rx = x - w * Math.cos(perpRad);
    const ry = y + w * Math.sin(perpRad);
    const cls = opts.class || 'p-notch';
    const d = `M ${this.cm(lx)} ${this.cm(ly)} L ${this.cm(tipX)} ${this.cm(tipY)} L ${this.cm(rx)} ${this.cm(ry)} Z`;
    let extra = '';
    if (opts.fill) extra += ` fill="${opts.fill}"`;
    return `<path id="${id}" class="${cls}" d="${d}"${extra}/>`;
  },

  // ── Phase 59: Label ──
  drawLabel(text, x, y, opts = {}) {
    const id = this._nextId();
    const cls = opts.class || 'p-label';
    const fontSize = opts.fontSize || 9;
    const anchor = opts.anchor || 'middle';
    let extra = ` font-size="${fontSize}px" text-anchor="${anchor}"`;
    if (opts.color) extra += ` fill="${opts.color}"`;
    if (opts.bold) extra += ' font-weight="700"';
    return `<text id="${id}" class="${cls}" x="${this.cm(x)}" y="${this.cm(y)}"${extra}>${text}</text>`;
  },

  // ── Phase 75: patternType→template mapping ──
  sectionTemplate(section) {
    const map = {
      shirt_front: 'ShirtFront',
      shirt_back: 'ShirtBack',
      shirt_sleeve: 'ShirtSleeve',
      shirt_collar: 'ShirtCollar',
      jacket_front: 'JacketFront',
      jacket_back: 'JacketBack',
      jacket_sleeve: 'JacketSleeve',
      skirt_front: 'SkirtFront',
      skirt_back: 'SkirtBack',
      pants_front: 'PantsFront',
      pants_back: 'PantsBack',
      dress_front: 'DressFront',
      dress_back: 'DressBack',
      full_body: 'FullBody',
    };
    return map[section] || null;
  },
};

// ═══════════════════════════════════════════════════════════
// PATTERN TEMPLATES (Phases 60-73)
// ═══════════════════════════════════════════════════════════

const PatternTemplates = {
  // Normalize measurement keys to pattern-ready values.
  // Accepts Freesewing keys (mm), KORRA keys (cm), or camelCase (cm).
  _prep(m) {
    const get = (fsKey, korraKey, camelKey, fallback, divisor = 1) => {
      let v = fallback;
      if (m[fsKey] != null) v = m[fsKey] / 10;       // Freesewing mm → cm
      else if (m[korraKey] != null) v = m[korraKey];  // KORRA cm
      else if (m[camelKey] != null) v = m[camelKey];  // camelCase cm
      return v / divisor;
    };
    const nc = m.neckCircumference != null ? m.neckCircumference / 10 :
               m['Neck Round'] != null ? m['Neck Round'] :
               m.neckCirc || 40;
    return {
      sw:  get('shoulderToShoulder', 'Across Shoulder', 'shoulderWidth', 42, 2),
      ntW: get('shoulderToWaist', 'Neck to Waist', 'neckToWaist', 44, 1),
      wtH: get('waistToHips', 'Waist to Hip', 'waistToHip', 20, 1),
      slL: get('shoulderToWrist', 'Sleeve Length', 'sleeveLength', 60, 1),
      ins: get('inseam', 'Inseam', 'inseam', 78, 1),
      chW: get('chest', 'Chest Round', 'chestWidth', 100, 4),
      chWF: get('chest', 'Chest Round', 'chestWidth', 100, 2),
      waW: get('waist', 'Waist Round', 'waistWidth', 90, 4),
      waWF: get('waist', 'Waist Round', 'waistWidth', 90, 2),
      hiW: get('hips', 'Hip Round', 'hipWidth', 102, 4),
      hiWF: get('hips', 'Hip Round', 'hipWidth', 102, 2),
      nkW: nc / 6,
      nkD: nc / 8 + 1,
      biW: get('bicepsCircumference', 'Bicep Round', 'bicepCirc', 32, 2),
      wrW: get('wristCircumference', 'Wrist Round', 'wristRound', 16, 2),
      thW: get('thighCircumference', 'Thigh Round', 'thighCirc', 56, 2),
      cd:  get('waistToHips', 'Waist to Hip', 'crotchDepth', 28, 1),
    };
  },

  // ── Phase 60: Shirt Front ──
  ShirtFront(m, opts = {}) {
    const P = PatternDraft, s = this._prep(m);
    const ease = opts.ease || 1.5;
    const w = s.chW + ease;
    const h = s.ntW + s.wtH + 3;
    const shDrop = s.sw * 0.18;
    const ah = s.chW * 0.22; // armhole depth factor
    const pts = [
      {x:0, y:s.nkD},                                    // CF neck
      {x:s.nkW, y:0},                                    // neck/shoulder
      {x:s.sw + 1, y:shDrop + 1},                        // shoulder tip
      {x:s.sw + 3, y:shDrop + 5,                        // armhole top
        cpx1: s.sw+3, cpy1: shDrop+2, cpx2: s.sw, cpy2: shDrop+4},
      {x:w, y:shDrop + ah,                              // armhole bottom
        cpx1: w+1, cpy1: shDrop + ah*0.3, cpx2: w+1, cpy2: shDrop + ah*0.7},
      {x:w, y:s.ntW,                                     // side at waist
        cpx1: w+1, cpy1: s.ntW*0.5, cpx2: w+1, cpy2: s.ntW},
      {x:w-1, y:h},                                       // side at hip
      {x:0, y:h},                                         // CF hem
    ];
    let svg = P.drawCurve(pts, {close:1, class:'p-outline', stroke:'#fff'});
    // neckline dip
    const nl = [
      {x:0, y:s.nkD},
      {x:s.nkW*0.4, y:s.nkD*0.7, cpx1:0, cpy1:s.nkD*0.7, cpx2:s.nkW*0.2, cpy2:s.nkD},
      {x:s.nkW, y:0},
    ];
    svg += P.drawCurve(nl, {class:'p-outline', stroke:'#fff'});
    // bust dart
    svg += P.drawDart(w*0.35, s.ntW*0.55, 2.5, 10, 0, {});
    // grainline
    svg += P.drawGrainline(2, h*0.35, 10, 0, {stroke:'rgba(198,255,0,0.6)'});
    // notches
    svg += P.drawNotch(w, s.ntW, 4, 0, {fill:'#fff'});
    svg += P.drawNotch(w-0.5, s.ntW+s.wtH, 4, 0, {fill:'#fff'});
    // label
    svg += P.drawLabel('Shirt Front ×2', w*0.5, h-0.7, {fontSize:8, bold:1, color:'#fff'});
    return {svg, size:{w, h}};
  },

  // ── Phase 61: Shirt Back ──
  ShirtBack(m, opts = {}) {
    const P = PatternDraft, s = this._prep(m);
    const ease = opts.ease || 1.5;
    const w = s.chW + ease;
    const h = s.ntW + s.wtH + 3;
    const shDrop = s.sw * 0.16;
    const ah = s.chW * 0.22;
    const pts = [
      {x:0, y:0.8},                                      // CB neck
      {x:s.nkW, y:0.3,                                   // neck/shoulder
        cpx1:0, cpy1:0.3, cpx2:s.nkW*0.4, cpy2:0},
      {x:s.sw + 1, y:shDrop + 1},                         // shoulder tip
      {x:s.sw + 3, y:shDrop + 5,                         // armhole
        cpx1: s.sw+3, cpy1: shDrop+2, cpx2: s.sw, cpy2: shDrop+4},
      {x:w, y:shDrop + ah,                               // armhole bottom
        cpx1: w+1, cpy1: shDrop + ah*0.3, cpx2: w+1, cpy2: shDrop + ah*0.7},
      {x:w, y:s.ntW,                                     // side waist
        cpx1: w+1, cpy1: s.ntW*0.5, cpx2: w+1, cpy2: s.ntW},
      {x:w-1, y:h},                                       // side hip
      {x:0, y:h},                                         // CB hem
    ];
    let svg = P.drawCurve(pts, {close:1, class:'p-outline', stroke:'#fff'});
    // shoulder dart
    const dartCx = s.sw * 0.5;
    const dartCy = shDrop * 0.65;
    svg += P.drawDart(dartCx, dartCy, 1.8, 8, -25, {fill:'rgba(255,200,100,0.15)'});
    svg += P.drawGrainline(2, h*0.35, 10, 0, {stroke:'rgba(198,255,0,0.6)'});
    svg += P.drawNotch(w, s.ntW, 4, 0, {fill:'#fff'});
    svg += P.drawLabel('Shirt Back ×2', w*0.5, h-0.7, {fontSize:8, bold:1, color:'#fff'});
    svg += P.drawLabel('FOLD', 0.5, 0.5, {fontSize:6, color:'rgba(255,255,255,0.4)'});
    return {svg, size:{w, h}};
  },

  // ── Phase 62: Shirt Sleeve ──
  ShirtSleeve(m, opts = {}) {
    const P = PatternDraft, s = this._prep(m);
    const ease = opts.ease || 1;
    const w = s.biW + ease;
    const h = s.slL + 2;
    const wrist = s.wrW + ease * 0.5;
    const capH = s.biW * 0.45;
    const pts = [
      {x:w*0.3, y:0},                                     // cap left
      {x:w*0.5, y:-capH*0.3,                             // cap top
        cpx1: w*0.35, cpy1: -capH*0.15, cpx2: w*0.4, cpy2: -capH*0.25},
      {x:w*0.7, y:0},                                    // cap right
      {x:w, y:capH,                                      // bicep
        cpx1: w, cpy1: capH*0.3, cpx2: w+1, cpy2: capH*0.7},
      {x:wrist + 1, y:h},                                 // wrist
      {x:0.5, y:h},                                       // hem
      {x:0, y:capH,                                      // underarm
        cpx1: -0.5, cpy1: capH*0.7, cpx2: 0, cpy2: capH*0.3},
    ];
    let svg = P.drawCurve(pts, {close:1, class:'p-outline', stroke:'#fff'});
    svg += P.drawGrainline(w*0.5, h*0.3, 8, 0, {stroke:'rgba(198,255,0,0.6)'});
    svg += P.drawNotch(w, capH, 3.5, 0, {fill:'#fff'});
    svg += P.drawLabel('Sleeve ×2', w*0.5, h-0.7, {fontSize:8, bold:1, color:'#fff'});
    return {svg, size:{w, h}};
  },

  // ── Phase 63: Shirt Collar ──
  ShirtCollar(m, opts = {}) {
    const P = PatternDraft, s = this._prep(m);
    const neck = (s.nkW * 6) / 2; // half neck for half-collar
    const collarW = 4;
    const h = collarW + 2;
    const curve = s.nkW * 0.3;
    const pts = [
      {x:0, y:0},
      {x:neck, y:0,
        cpx1: neck*0.3, cpy1: -curve, cpx2: neck*0.7, cpy2: -curve},
      {x:neck, y:collarW,
        cpx1: neck*0.7, cpy1: collarW - curve, cpx2: neck*0.3, cpy2: collarW - curve},
      {x:0, y:collarW},
    ];
    let svg = P.drawCurve(pts, {close:1, class:'p-outline', stroke:'#fff'});
    svg += P.drawGrainline(neck*0.5, collarW*0.5, 3, 90, {stroke:'rgba(198,255,0,0.6)'});
    svg += P.drawLabel('Collar ×2', neck*0.5, collarW*0.5, {fontSize:7, bold:1, color:'#fff'});
    return {svg, size:{w:neck, h}};
  },

  // ── Phase 64: Jacket Front ──
  JacketFront(m, opts = {}) {
    const P = PatternDraft, s = this._prep(m);
    const ease = opts.ease || 4;
    const w = s.chW + ease;
    const h = s.ntW + s.wtH + 5;
    const shDrop = s.sw * 0.18;
    const ah = s.chW * 0.25;
    const pts = [
      {x:1.5, y:s.nkD},                                  // CF neck (lapel starts)
      {x:s.nkW + 1, y:0.5},                              // neck/shoulder
      {x:s.sw + 2, y:shDrop + 1.5},                       // shoulder tip
      {x:s.sw + 4, y:shDrop + 6,                         // armhole
        cpx1: s.sw+4, cpy1: shDrop+3, cpx2: s.sw+1, cpy2: shDrop+5},
      {x:w, y:shDrop + ah,                               // armhole bottom
        cpx1: w+2, cpy1: shDrop + ah*0.2, cpx2: w+2, cpy2: shDrop + ah*0.6},
      {x:w, y:s.ntW,                                     // side waist
        cpx1: w+2, cpy1: s.ntW*0.5, cpx2: w+2, cpy2: s.ntW},
      {x:w-1, y:h},                                       // side hip
      {x:0, y:h},                                         // CF hem
      {x:0, y:s.ntW*0.3},                                // lapel bottom
      {x:1.5, y:s.nkD},                                  // lapel to CF neck
    ];
    let svg = P.drawCurve(pts, {close:1, class:'p-outline', stroke:'#fff'});
    svg += P.drawGrainline(2, h*0.4, 12, 0, {stroke:'rgba(198,255,0,0.6)'});
    svg += P.drawNotch(w, s.ntW, 4, 0, {fill:'#fff'});
    svg += P.drawNotch(w-1, s.ntW+s.wtH, 4, 0, {fill:'#fff'});
    svg += P.drawLabel('Jacket Front ×2', w*0.5, h-0.7, {fontSize:8, bold:1, color:'#fff'});
    svg += P.drawLabel('LAPEL', 0.3, s.ntW*0.15, {fontSize:6, color:'rgba(255,255,255,0.5)'});
    return {svg, size:{w, h}};
  },

  // ── Phase 65: Jacket Back ──
  JacketBack(m, opts = {}) {
    const P = PatternDraft, s = this._prep(m);
    const ease = opts.ease || 4;
    const w = s.chW + ease;
    const h = s.ntW + s.wtH + 5;
    const shDrop = s.sw * 0.16;
    const ah = s.chW * 0.25;
    const pts = [
      {x:0, y:1},
      {x:s.nkW + 0.5, y:0.5,
        cpx1:0, cpy1:0.5, cpx2:s.nkW*0.3, cpy2:0},
      {x:s.sw + 2, y:shDrop + 1.5},
      {x:s.sw + 4, y:shDrop + 6,
        cpx1: s.sw+4, cpy1: shDrop+3, cpx2: s.sw+1, cpy2: shDrop+5},
      {x:w, y:shDrop + ah,
        cpx1: w+2, cpy1: shDrop + ah*0.2, cpx2: w+2, cpy2: shDrop + ah*0.6},
      {x:w, y:s.ntW,
        cpx1: w+2, cpy1: s.ntW*0.5, cpx2: w+2, cpy2: s.ntW},
      {x:w-1, y:h},
      {x:0.5, y:h},
    ];
    let svg = P.drawCurve(pts, {close:1, class:'p-outline', stroke:'#fff'});
    // CB waist suppression (back curve)
    const cbCurve = [
      {x:0.5, y:1},
      {x:0, y:s.ntW*0.4, cpx1:0.3, cpy1:s.ntW*0.2, cpx2:0, cpy2:s.ntW*0.3},
      {x:0.5, y:s.ntW},
    ];
    svg += P.drawCurve(cbCurve, {class:'p-outline', stroke:'#fff', dash:'4,3'});
    svg += P.drawGrainline(2, h*0.35, 12, 0, {stroke:'rgba(198,255,0,0.6)'});
    svg += P.drawLabel('Jacket Back ×2', w*0.5, h-0.7, {fontSize:8, bold:1, color:'#fff'});
    return {svg, size:{w, h}};
  },

  // ── Phase 66: Jacket Sleeve (two-piece simplified) ──
  JacketSleeve(m, opts = {}) {
    const P = PatternDraft, s = this._prep(m);
    const ease = opts.ease || 2;
    const w = s.biW + ease;
    const h = s.slL + 2;
    const wrist = s.wrW + ease * 0.3;
    const capH = s.biW * 0.5;
    const pts = [
      {x:w*0.2, y:0},
      {x:w*0.5, y:-capH*0.35,
        cpx1: w*0.3, cpy1: -capH*0.15, cpx2: w*0.35, cpy2: -capH*0.3},
      {x:w*0.8, y:0},
      {x:w+1, y:capH,
        cpx1: w+1, cpy1: capH*0.2, cpx2: w+2, cpy2: capH*0.6},
      {x:wrist + 1.5, y:h},
      {x:1, y:h},
      {x:0, y:capH,
        cpx1: -1, cpy1: capH*0.6, cpx2: 0, cpy2: capH*0.2},
    ];
    let svg = P.drawCurve(pts, {close:1, class:'p-outline', stroke:'#fff'});
    // elbow dart
    svg += P.drawDart(w*0.4, h*0.55, 2, 7, 10, {fill:'rgba(255,200,100,0.15)'});
    svg += P.drawGrainline(w*0.5, h*0.3, 10, 0, {stroke:'rgba(198,255,0,0.6)'});
    svg += P.drawLabel('Sleeve ×2', w*0.5, h-0.7, {fontSize:8, bold:1, color:'#fff'});
    return {svg, size:{w, h}};
  },

  // ── Phase 67: Skirt Front ──
  SkirtFront(m, opts = {}) {
    const P = PatternDraft, s = this._prep(m);
    const ease = opts.ease || 2;
    const w = s.waW + ease;
    const h = s.wtH + (s.ntW * 0.15) + 2; // skirt length from waist
    const hemW = w * (opts.silhouette === 'a-line' ? 1.4 : opts.silhouette === 'pencil' ? 0.85 : 1);
    const pts = [
      {x:0, y:1},
      {x:w, y:1,
        cpx1: w*0.3, cpy1: 0.3, cpx2: w*0.7, cpy2: 0.3},
      {x:hemW, y:h},
      {x:0, y:h},
    ];
    let svg = P.drawCurve(pts, {close:1, class:'p-outline', stroke:'#fff'});
    // waist darts
    svg += P.drawDart(w*0.35, 1.5, 2, 9, -90, {});
    svg += P.drawDart(w*0.65, 1.5, 2, 8, -90, {});
    svg += P.drawGrainline(1.5, h*0.4, 8, 0, {stroke:'rgba(198,255,0,0.6)'});
    svg += P.drawNotch(w, 2, 3.5, 0, {fill:'#fff'});
    svg += P.drawLabel('Skirt Front ×2', w*0.5, h-0.7, {fontSize:8, bold:1, color:'#fff'});
    return {svg, size:{w, h}};
  },

  // ── Phase 68: Skirt Back ──
  SkirtBack(m, opts = {}) {
    const P = PatternDraft, s = this._prep(m);
    const ease = opts.ease || 2.5;
    const w = s.waW + ease;
    const h = s.wtH + (s.ntW * 0.15) + 2;
    const hemW = w * (opts.silhouette === 'a-line' ? 1.5 : opts.silhouette === 'pencil' ? 0.83 : 1);
    const pts = [
      {x:0, y:1.5},
      {x:w, y:1.5,
        cpx1: w*0.3, cpy1: 0.5, cpx2: w*0.7, cpy2: 0.5},
      {x:hemW, y:h},
      {x:0, y:h},
    ];
    let svg = P.drawCurve(pts, {close:1, class:'p-outline', stroke:'#fff'});
    svg += P.drawDart(w*0.4, 2, 2.5, 11, -90, {});
    svg += P.drawDart(w*0.7, 2, 2, 9, -90, {});
    svg += P.drawGrainline(1.5, h*0.4, 8, 0, {stroke:'rgba(198,255,0,0.6)'});
    svg += P.drawLabel('Skirt Back ×2', w*0.5, h-0.7, {fontSize:8, bold:1, color:'#fff'});
    svg += P.drawLabel('FOLD', 0.5, 0.5, {fontSize:6, color:'rgba(255,255,255,0.4)'});
    return {svg, size:{w, h}};
  },

  // ── Phase 69: Pants Front ──
  PantsFront(m, opts = {}) {
    const P = PatternDraft, s = this._prep(m);
    const ease = opts.ease || 2;
    const w = s.waW + ease;           // quarter waist
    const hipW = s.hiW + ease;        // quarter hip
    const h = s.ins + s.cd + 4;       // total length
    const kneeY = s.cd + s.ins * 0.45;
    const kneeW = s.thW * 0.85;
    const hemW = s.thW * 0.6;
    const crotchExt = s.hiW * 0.25;   // crotch extension
    const pts = [
      {x:0, y:1.5},                                      // CF waist
      {x:w, y:1.5,                                       // side waist
        cpx1: w*0.3, cpy1: 0.5, cpx2: w*0.7, cpy2: 0.5},
      {x:w, y:s.cd,                                      // side hip
        cpx1: w, cpy1: s.cd*0.4, cpx2: w+1, cpy2: s.cd*0.7},
      {x:kneeW+1, y:kneeY,                                // side knee
        cpx1: w+1, cpy1: s.cd + (kneeY-s.cd)*0.3, cpx2: w, cpy2: s.cd + (kneeY-s.cd)*0.6},
      {x:hemW+1, y:h-2},                                  // side hem
      {x:1, y:h-2},                                       // inseam hem
      {x:1, y:kneeY,                                      // inseam knee
        cpx1: 0.5, cpy1: s.cd + (kneeY-s.cd)*0.6, cpx2: 0.5, cpy2: s.cd + (kneeY-s.cd)*0.3},
      {x:crotchExt, y:s.cd,                               // crotch
        cpx1: crotchExt*0.5, cpy1: s.cd - 2, cpx2: crotchExt*0.2, cpy2: s.cd - 1},
      {x:0, y:s.cd - 1},                                  // CF crotch
    ];
    let svg = P.drawCurve(pts, {close:1, class:'p-outline', stroke:'#fff'});
    svg += P.drawDart(w*0.4, 2, 1.5, 7, -90, {});
    svg += P.drawGrainline(2, h*0.35, 10, 0, {stroke:'rgba(198,255,0,0.6)'});
    svg += P.drawNotch(w, s.cd, 3.5, 0, {fill:'#fff'});
    svg += P.drawNotch(1, kneeY, 3, 0, {fill:'#fff'});
    svg += P.drawLabel('Pants Front ×2', w*0.5, h-0.7, {fontSize:8, bold:1, color:'#fff'});
    return {svg, size:{w, h}};
  },

  // ── Phase 70: Pants Back ──
  PantsBack(m, opts = {}) {
    const P = PatternDraft, s = this._prep(m);
    const ease = opts.ease || 3.5;
    const w = s.waW + ease;
    const hipW = s.hiW + ease + 1;
    const h = s.ins + s.cd + 4;
    const kneeY = s.cd + s.ins * 0.45;
    const kneeW = s.thW * 0.9;
    const hemW = s.thW * 0.62;
    const crotchExt = s.hiW * 0.35;
    const pts = [
      {x:0, y:2.5},                                      // CB waist (higher)
      {x:w, y:1.5,                                       // side waist
        cpx1: w*0.3, cpy1: 0.8, cpx2: w*0.7, cpy2: 0.5},
      {x:w+1, y:s.cd+1,                                  // side hip
        cpx1: w+1, cpy1: s.cd*0.3, cpx2: w+2, cpy2: s.cd*0.6},
      {x:kneeW+1.5, y:kneeY,                              // side knee
        cpx1: w+1.5, cpy1: s.cd+(kneeY-s.cd)*0.3, cpx2: w+0.5, cpy2: s.cd+(kneeY-s.cd)*0.6},
      {x:hemW+1.5, y:h-2},                                // side hem
      {x:1.5, y:h-2},                                     // inseam hem
      {x:1.5, y:kneeY,                                    // inseam knee
        cpx1: 1, cpy1: s.cd+(kneeY-s.cd)*0.6, cpx2: 1, cpy2: s.cd+(kneeY-s.cd)*0.3},
      {x:crotchExt + 1, y:s.cd + 1,                       // crotch (deeper)
        cpx1: crotchExt*0.5+1, cpy1: s.cd-1, cpx2: crotchExt*0.2+1, cpy2: s.cd-0.5},
      {x:0, y:s.cd},                                      // CB crotch
    ];
    let svg = P.drawCurve(pts, {close:1, class:'p-outline', stroke:'#fff'});
    svg += P.drawDart(w*0.35, 2.5, 2, 9, -90, {});
    svg += P.drawDart(w*0.65, 2.5, 1.5, 7, -90, {});
    svg += P.drawGrainline(2, h*0.35, 10, 0, {stroke:'rgba(198,255,0,0.6)'});
    svg += P.drawLabel('Pants Back ×2', w*0.5, h-0.7, {fontSize:8, bold:1, color:'#fff'});
    svg += P.drawLabel('FOLD', 0.5, 0.5, {fontSize:6, color:'rgba(255,255,255,0.4)'});
    return {svg, size:{w, h}};
  },

  // ── Phase 71: Dress Front ──
  DressFront(m, opts = {}) {
    const P = PatternDraft, s = this._prep(m);
    const ease = opts.ease || 2;
    const bw = s.chW + ease;          // bodice width
    const sw = s.waW + ease;          // skirt width at waist
    const skLen = s.wtH * 2 + 5;      // skirt length
    const h = s.ntW + skLen + 3;
    const shDrop = s.sw * 0.18;
    const ah = s.chW * 0.22;
    const hemW = sw * 1.3;
    const pts = [
      {x:0, y:s.nkD},
      {x:s.nkW, y:0},
      {x:s.sw + 1, y:shDrop + 1},
      {x:s.sw + 3, y:shDrop + 5,
        cpx1: s.sw+3, cpy1: shDrop+2, cpx2: s.sw, cpy2: shDrop+4},
      {x:bw, y:shDrop + ah,
        cpx1: bw+1, cpy1: shDrop+ah*0.3, cpx2: bw+1, cpy2: shDrop+ah*0.7},
      {x:sw, y:s.ntW,                                     // waist
        cpx1: bw, cpy1: s.ntW*0.5, cpx2: sw, cpy2: s.ntW},
      {x:hemW, y:h},                                       // hem
      {x:0, y:h},                                         // CF hem
    ];
    let svg = P.drawCurve(pts, {close:1, class:'p-outline', stroke:'#fff'});
    const nl = [
      {x:0, y:s.nkD},
      {x:s.nkW*0.4, y:s.nkD*0.7, cpx1:0, cpy1:s.nkD*0.7, cpx2:s.nkW*0.2, cpy2:s.nkD},
      {x:s.nkW, y:0},
    ];
    svg += P.drawCurve(nl, {class:'p-outline', stroke:'#fff'});
    svg += P.drawDart(bw*0.35, s.ntW*0.55, 2.5, 10, 0, {});
    // waist seam
    svg += P.drawCurve([
      {x:0, y:s.ntW},
      {x:sw, y:s.ntW}
    ], {class:'p-seam', stroke:'rgba(255,255,255,0.15)', dash:'4,2'});
    svg += P.drawGrainline(2, h*0.35, 10, 0, {stroke:'rgba(198,255,0,0.6)'});
    svg += P.drawLabel('Dress Front ×2', Math.max(bw, hemW)*0.5, h-0.7, {fontSize:8, bold:1, color:'#fff'});
    return {svg, size:{w:Math.max(bw, hemW), h}};
  },

  // ── Phase 72: Dress Back ──
  DressBack(m, opts = {}) {
    const P = PatternDraft, s = this._prep(m);
    const ease = opts.ease || 2;
    const bw = s.chW + ease;
    const sw = s.waW + ease;
    const skLen = s.wtH * 2 + 5;
    const h = s.ntW + skLen + 3;
    const shDrop = s.sw * 0.16;
    const ah = s.chW * 0.22;
    const hemW = sw * 1.3;
    const pts = [
      {x:0, y:0.8},
      {x:s.nkW, y:0.3,
        cpx1:0, cpy1:0.3, cpx2:s.nkW*0.4, cpy2:0},
      {x:s.sw + 1, y:shDrop + 1},
      {x:s.sw + 3, y:shDrop + 5,
        cpx1: s.sw+3, cpy1: shDrop+2, cpx2: s.sw, cpy2: shDrop+4},
      {x:bw, y:shDrop + ah,
        cpx1: bw+1, cpy1: shDrop+ah*0.3, cpx2: bw+1, cpy2: shDrop+ah*0.7},
      {x:sw, y:s.ntW,
        cpx1: bw, cpy1: s.ntW*0.5, cpx2: sw, cpy2: s.ntW},
      {x:hemW, y:h},
      {x:0, y:h},
    ];
    let svg = P.drawCurve(pts, {close:1, class:'p-outline', stroke:'#fff'});
    svg += P.drawDart(s.sw*0.5, shDrop*0.65, 1.8, 8, -25, {fill:'rgba(255,200,100,0.15)'});
    svg += P.drawCurve([
      {x:0, y:s.ntW},
      {x:sw, y:s.ntW}
    ], {class:'p-seam', stroke:'rgba(255,255,255,0.15)', dash:'4,2'});
    svg += P.drawGrainline(2, h*0.35, 10, 0, {stroke:'rgba(198,255,0,0.6)'});
    svg += P.drawLabel('Dress Back ×2', Math.max(bw, hemW)*0.5, h-0.7, {fontSize:8, bold:1, color:'#fff'});
    return {svg, size:{w:Math.max(bw, hemW), h}};
  },

  // ── Phase 73: Full Body (Jumpsuit / One-piece) ──
  FullBody(m, opts = {}) {
    const P = PatternDraft, s = this._prep(m);
    const ease = opts.ease || 3;
    const bw = s.chW + ease;
    const ww = s.waW + ease;
    const hw = s.hiW + ease;
    const tw = s.thW + ease;
    const h = s.ntW + s.wtH + s.ins + s.cd + 4;
    const shDrop = s.sw * 0.18;
    const ah = s.chW * 0.22;
    const kneeY = s.ntW + s.wtH + s.cd + s.ins * 0.45;
    const hemW = tw * 0.6;
    const crotchExt = s.hiW * 0.25;
    const pts = [
      {x:0, y:s.nkD},                                      // CF neck
      {x:s.nkW, y:0},
      {x:s.sw+1, y:shDrop+1},
      {x:s.sw+3, y:shDrop+5, cpx1:s.sw+3,cpy1:shDrop+2, cpx2:s.sw,cpy2:shDrop+4},
      {x:bw, y:shDrop+ah, cpx1:bw+1,cpy1:shDrop+ah*0.3,cpx2:bw+1,cpy2:shDrop+ah*0.7},
      {x:ww, y:s.ntW, cpx1:bw,cpy1:s.ntW*0.5,cpx2:ww,cpy2:s.ntW},    // waist
      {x:hw, y:s.ntW+s.wtH, cpx1:ww,cpy1:s.ntW+s.wtH*0.4,cpx2:hw,cpy2:s.ntW+s.wtH*0.7}, // hip
      {x:tw+1, y:s.ntW+s.wtH+s.cd, cpx1:hw+1,cpy1:s.ntW+s.wtH+s.cd*0.5,cpx2:tw+1,cpy2:s.ntW+s.wtH+s.cd*0.8}, // crotch level
      {x:hemW+1, y:h-2},
      {x:1, y:h-2},
      {x:1, y:kneeY, cpx1:0.5,cpy1:s.ntW+s.wtH+s.cd+(kneeY-s.ntW-s.wtH-s.cd)*0.6,cpx2:0.5,cpy2:s.ntW+s.wtH+s.cd+(kneeY-s.ntW-s.wtH-s.cd)*0.3},
      {x:crotchExt, y:s.ntW+s.wtH+s.cd, cpx1:crotchExt*0.5,cpy1:s.ntW+s.wtH+s.cd-2,cpx2:crotchExt*0.2,cpy2:s.ntW+s.wtH+s.cd-1},
      {x:0, y:s.ntW+s.wtH+s.cd-1},
    ];
    let svg = P.drawCurve(pts, {close:1, class:'p-outline', stroke:'#fff'});
    const nl = [
      {x:0, y:s.nkD},
      {x:s.nkW*0.4, y:s.nkD*0.7, cpx1:0,cpy1:s.nkD*0.7,cpx2:s.nkW*0.2,cpy2:s.nkD},
      {x:s.nkW, y:0},
    ];
    svg += P.drawCurve(nl, {class:'p-outline', stroke:'#fff'});
    svg += P.drawDart(bw*0.35, s.ntW*0.55, 2.5, 10, 0, {});
    svg += P.drawGrainline(2, h*0.35, 10, 0, {stroke:'rgba(198,255,0,0.6)'});
    svg += P.drawLabel('Full Body ×2', Math.max(bw, hemW)*0.5, h-0.7, {fontSize:8, bold:1, color:'#fff'});
    return {svg, size:{w:Math.max(bw, hemW), h}};
  },
};
