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
  compareHistory: [],
  compareBaselineIdx: 0,
  vBaseline: null,
  vLatest: null,
  baselineData: null,
  latestData: null,

  // ═══ ENTRY POINT ═══
  open(data) {
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
        <div class="ms-header">
          <div class="ms-header-left">
            <button class="ms-back-btn" onclick="KORRA_MS.handleBack()">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
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
            <div class="ms-ease-toggle" onclick="KORRA_MS.toggleEase()" title="Toggle between body and garment measurements">
              <span class="ms-ease-label ${!this.showEased ? 'active' : ''}">Body</span>
              <div class="ms-ease-track ${this.showEased ? 'active' : ''}">
                <div class="ms-ease-thumb ${this.showEased ? 'right' : ''}"></div>
              </div>
              <span class="ms-ease-label ${this.showEased ? 'active' : ''}">Garment</span>
            </div>
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
        </div>
        <div class="ms-sheet" id="ms-sheet">
          <div class="ms-sheet-handle" id="ms-sheet-handle"></div>
          <div class="ms-sheet-body" id="ms-sheet-body">${this.buildSheetContent()}</div>
        </div>
        <button class="ms-ai-fab" onclick="KORRA_MS.switchView('ai')" title="Ask AI">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
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
    const d = this.data || {};
    const summaryBar = `<div class="ms-summary-bar">
      <div class="ms-summary-item"><div class="ms-summary-label">HEIGHT</div><div class="ms-summary-value">${d.height ? d.height + ' cm' : '—'}</div></div>
      <div class="ms-summary-item"><div class="ms-summary-label">SHAPE</div><div class="ms-summary-value">${d.body_shape || 'Standard'}</div></div>
      <div class="ms-summary-item"><div class="ms-summary-label">SIZE REC</div><div class="ms-summary-value">${d.size_recommendation || 'M'}</div></div>
    </div>`;
    let content;
    switch (this.viewMode) {
      case 'avatar': content = this.buildMetricsGrid(); break;
      case 'sizes': content = this.buildSizesGrid(); break;
      case 'shape': content = this.buildShapeCard(); break;
      case 'compare': content = this.buildCompareView(); break;
      case 'ai': content = this.buildAIView(); break;
      default: content = this.buildMetricsGrid();
    }
    if (this.viewMode === 'ai') return content;
    return summaryBar + content + this.buildNotesHTML();
  },

  buildAIView() {
    return `<div class="ms-ai-view">
      <div class="ms-ai-topbar">
        <button class="ms-ai-back" onclick="KORRA_MS.closeAI()">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
          Back to Measurements
        </button>
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
            return `<div class="ms-metric-cell${active}" onclick="KORRA_MS.selectMeasurement('${k}')">
              <div class="ms-metric-name">${k}</div>
              <div class="ms-metric-val">${val}${factor === 1 ? 'cm' : 'in'}</div>
              ${easeLabel ? `<div class="ms-metric-ease">${easeLabel}</div>` : ''}
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
      <div class="ms-material-section">
        <div class="ms-material-label">FABRIC</div>
        <div class="ms-material-rail">
          <button class="ms-material-btn ${mat === 'woven' ? 'active' : ''}" onclick="KORRA_MS.setMaterial('woven')">Woven</button>
          <button class="ms-material-btn ${mat === 'knit' ? 'active' : ''}" onclick="KORRA_MS.setMaterial('knit')">Knit</button>
          <button class="ms-material-btn ${mat === 'starch_bazin' ? 'active' : ''}" onclick="KORRA_MS.setMaterial('starch_bazin')">Starch Bazin</button>
          <button class="ms-material-btn ${mat === 'technical' ? 'active' : ''}" onclick="KORRA_MS.setMaterial('technical')">Technical</button>
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
    const summaryBar = `<div class="ms-summary-bar">
      <div class="ms-summary-item"><div class="ms-summary-label">HEIGHT</div><div class="ms-summary-value">${this.data?.height ? this.data.height + ' cm' : '—'}</div></div>
      <div class="ms-summary-item"><div class="ms-summary-label">SHAPE</div><div class="ms-summary-value">${this.data?.body_shape || 'Standard'}</div></div>
      <div class="ms-summary-item"><div class="ms-summary-label">SIZE REC</div><div class="ms-summary-value">${this.data?.size_recommendation || 'M'}</div></div>
    </div>`;
    let content;
    switch (this.viewMode) {
      case 'avatar': content = this.buildMetricsGrid(); break;
      case 'sizes': content = this.buildSizesGrid(); break;
      case 'shape': content = this.buildShapeCard(); break;
      case 'compare': content = this.buildCompareView(); break;
      default: content = this.buildMetricsGrid();
    }
    body.innerHTML = summaryBar + content;
    if (this.viewMode === 'compare') this.initCompareViewers();
    this.updateBadge();
  },

  // ═══ VIEW MODE ═══
  switchView(mode) {
    if (mode === 'ai' && this.viewMode !== 'ai') this._previousView = this.viewMode;
    this.viewMode = mode;
    document.querySelectorAll('#view-scanresult .ms-tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`#view-scanresult .ms-tab[onclick*="${mode}"]`)?.classList.add('active');
    const body = document.getElementById('ms-sheet-body');
    if (body) {
      if (mode === 'ai') {
        body.style.overflow = 'hidden';
        body.style.display = 'flex';
        body.style.flexDirection = 'column';
        body.style.padding = '0 20px';

        const title = document.querySelector('.ms-scan-title');
        const subtitle = document.querySelector('.ms-scan-subtitle');
        if (title) title.textContent = 'AI Assistant';
        if (subtitle) subtitle.textContent = 'Ask anything about your measurements';

        const unitToggle = document.querySelector('.ms-unit-toggle');
        const easeToggle = document.querySelector('.ms-ease-toggle');
        if (unitToggle) unitToggle.style.display = 'none';
        if (easeToggle) easeToggle.style.display = 'none';

        const attire = document.querySelector('.ms-attire-selector-container');
        const tabs = document.querySelector('.ms-tabs');
        if (attire) attire.style.display = 'none';
        if (tabs) tabs.style.display = 'none';
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

        const attire = document.querySelector('.ms-attire-selector-container');
        const tabs = document.querySelector('.ms-tabs');
        if (attire) attire.style.display = '';
        if (tabs) tabs.style.display = '';
      }
      const rightCol = document.querySelector('.ms-right-col');
      if (rightCol) rightCol.style.overflow = mode === 'ai' ? 'visible' : '';
      body.innerHTML = this.buildSheetContent();
    }
    const fab = document.querySelector('#view-scanresult .ms-ai-fab');
    if (fab) fab.style.display = mode === 'ai' ? 'none' : '';
    if (mode === 'compare') this.initCompareViewers();
  },

  // ═══ MEASUREMENT SELECTION ═══
  selectMeasurement(key) {
    this.selectedMeasurement = key;
    this.updateBadge();
    if (this.viewerInstance) {
      this.viewerInstance.clearMeasurementRings();
      const yPct = MEASUREMENT_Y[key] || 0.5;
      const color = MEASUREMENT_COLORS[key] || '#C6FF00';
      this.viewerInstance.showMeasurementRing(yPct, color);
    }
    document.querySelectorAll('#view-scanresult .ms-metric-cell').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('#view-scanresult .ms-metric-cell').forEach(el => {
      if (el.querySelector('.ms-metric-name')?.textContent === key) el.classList.add('active');
    });
    if (window.innerWidth <= 900) this.collapseSheet();
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
    if (this.viewerInstance) {
      if (this.overlaysVisible) {
        this.viewerInstance.showMeasurementRings(this.data, MEASUREMENT_COLORS, MEASUREMENT_Y);
      } else {
        this.viewerInstance.clearMeasurementRings();
      }
    }
  },

  _wrapRightCol() {
    const root = document.querySelector('#view-scanresult .ms-root');
    if (!root || root.querySelector('.ms-right-col')) return;
    const tabs = root.querySelector('.ms-tabs');
    const sheet = root.querySelector('.ms-sheet');
    const attire = root.querySelector('#ms-attire-selector');
    if (!tabs || !sheet) return;
    const rc = document.createElement('div');
    rc.className = 'ms-right-col';
    root.insertBefore(rc, sheet);
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
  expandSheet() {
    this.sheetExpanded = true;
    document.getElementById('ms-sheet')?.classList.add('expanded');
  },
  collapseSheet() {
    this.sheetExpanded = false;
    document.getElementById('ms-sheet')?.classList.remove('expanded');
  },
  bindSheetDrag() {
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
        if (this.overlaysVisible && this.viewerInstance) {
          this.viewerInstance.showMeasurementRings(this.data, MEASUREMENT_COLORS, MEASUREMENT_Y);
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
    } else {
      if (this.overlaysVisible && this.viewerInstance) {
        this.viewerInstance.showMeasurementRings(this.data, MEASUREMENT_COLORS, MEASUREMENT_Y);
      }
    }
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
          gender: this.data?.gender
        })
      });
      const data = await res.json();
      document.getElementById('ms-ai-loading')?.remove();
      body.insertAdjacentHTML('beforeend', `<div class="ms-ai-message assistant">${data.response || 'No response available.'}</div>`);
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
    document.getElementById('ms-ai-input')?.focus();
  },

  // ═══ EASE MULTIPLIERS ═══
  getEase(key) {
    const reg = window.ATTIRE_REGISTRY || [];
    const entry = reg.find(a => a.id === this.activeContext);
    const base = entry ? entry.mult : 1.035;
    const materialCoeffs = {
      woven: 1.0, knit: 0.85, starch_bazin: 1.1, technical: 0.9
    };
    const mat = materialCoeffs[this.activeMaterial] || 1.0;
    const result = base * mat;
    console.log(`  getEase("${key}") → ctx="${this.activeContext}" entry=${!!entry} base=${base} mat=${mat} result=${result}`);
    return result;
  },

  setContext(ctx) {
    console.log(`▶ setContext("${ctx}")`);
    this.activeContext = ctx;
    if ("vibrate" in navigator) navigator.vibrate(50);
    if (window.KORRA_VIZ) window.KORRA_VIZ.applyHeatmap(ctx);
    if (this._attireSelector) this._attireSelector.select(ctx);
    this.renderMeasurements();
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
    document.querySelector('main').style.overflow = '';
    this.active = false;
    this.data = null;
    if (this.viewerInstance && this.viewerInstance !== window.KORRA_VIZ) {
      this.viewerInstance.clearMeasurementRings?.();
    }
    this.viewerInstance = null;
    this.sheetExpanded = false;
    this._aiLoading = false;
    if (this._aiAbort) { this._aiAbort.abort(); this._aiAbort = null; }
  }
};
