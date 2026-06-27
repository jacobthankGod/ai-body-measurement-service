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
    this.active = true;
    this.viewMode = 'avatar';
    this.selectedMeasurement = 'Chest Round';
    this.unit = window.CURRENT_UNIT || 'cm';
    this.overlaysVisible = true;
    this.sheetExpanded = false;
    this.aiOpen = false;
    this._viewerInitialized = false;
    this._previousTab = document.querySelector('.tab-view.active')?.id?.replace('view-', '') || 'vault';
    this.render();
    this.initViewer();
    this.bindSheetDrag();
    window.switchTab('scanresult');
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
        <div class="ms-viewer" id="ms-viewer">
          <div class="ms-viewer-canvas" id="ms-viewer-canvas"></div>
          <div class="ms-viewer-badge" id="ms-viewer-badge">${this.buildBadge()}</div>
        </div>
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
        <div class="ms-sheet" id="ms-sheet">
          <div class="ms-sheet-handle" id="ms-sheet-handle"></div>
          <div class="ms-sheet-header">
            <div class="ms-sheet-title" id="ms-sheet-title">Measurements</div>
          </div>
          <div class="ms-sheet-body" id="ms-sheet-body">${this.buildSheetContent()}</div>
        </div>
        <button class="ms-ai-fab" onclick="KORRA_MS.openAI()" title="Ask AI">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
        </button>
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
      </div>`;
  },

  // ═══ BADGE ═══
  buildBadge() {
    const m = this.data?.measurements || {};
    const val = m[this.selectedMeasurement];
    const factor = this.unit === 'in' ? 0.393701 : 1;
    const displayVal = val != null ? (val * factor).toFixed(1) : '—';
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
    switch (this.viewMode) {
      case 'avatar': case 'metrics': return this.buildMetricsList();
      case 'sizes': return this.buildSizesGrid();
      case 'shape': return this.buildShapeCard();
      case 'compare': return this.buildCompareView();
      default: return this.buildMetricsList();
    }
  },

  buildMetricsList() {
    const m = this.data?.measurements || {};
    const gender = (this.data?.gender || 'male').toLowerCase();
    const factor = this.unit === 'in' ? 0.393701 : 1;
    const keys = gender === 'female' ? FEMALE_KEYS : MALE_KEYS;
    return '<div class="ms-meas-list">' + keys.map(k => {
      const val = m[k];
      const dv = val != null ? (val * factor).toFixed(1) : '—';
      const color = MEASUREMENT_COLORS[k] || '#C6FF00';
      const active = k === this.selectedMeasurement ? ' active' : '';
      return `<div class="ms-meas-item${active}" onclick="KORRA_MS.selectMeasurement('${k}')">
        <div class="ms-meas-item-left">
          <div class="ms-meas-dot" style="background:${color}"></div>
          <div class="ms-meas-name">${k}</div>
        </div>
        <div class="ms-meas-value">${dv}${val != null ? this.unit : ''}</div>
      </div>`;
    }).join('') + '</div>';
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
    return '<div class="ms-size-grid">' + Object.entries(items).map(([label, size]) =>
      `<div class="ms-size-card">
        <div class="ms-size-label">${label}</div>
        <div class="ms-size-value">${size}</div>
        ${m[label] ? `<div class="ms-size-cm">${(m[label] * factor).toFixed(1)} ${this.unit}</div>` : ''}
      </div>`
    ).join('') + '</div>';
  },

  buildShapeCard() {
    const shape = this.data?.body_shape || 'Standard';
    const info = BODY_SHAPE_INFO[shape] || BODY_SHAPE_INFO['Standard'];
    const m = this.data?.measurements || {};
    const chest = m['Chest Round'] || 0;
    const waist = m['Waist Round'] || 1;
    const ratio = waist > 0 ? (chest / waist).toFixed(2) : '—';
    return `<div class="ms-shape-card">
      <div class="ms-shape-icon" style="font-size:28px">${info.icon}</div>
      <div class="ms-shape-name">${shape}</div>
      <div class="ms-shape-desc">${info.desc}</div>
      <div class="ms-shape-desc" style="margin-top:8px; color:var(--Mint)">${info.advice}</div>
      <div class="ms-shape-ratio">
        <div class="ms-ratio-label">Chest / Waist Ratio</div>
        <div class="ms-ratio-value">${ratio}</div>
      </div>
    </div>`;
  },

  buildCompareView() {
    const clientName = this.data?.client_name;
    const scans = (window.masterHistory || []).filter(s => s.client_name === clientName && s !== this.data);
    if (scans.length === 0) {
      return `<div class="ms-empty">
        <div class="ms-empty-icon">📊</div>
        <div class="ms-empty-title">No previous scans</div>
        <div class="ms-empty-desc">Take another scan to see changes over time.</div>
      </div>`;
    }
    const baseline = scans[scans.length - 1];
    const m1 = baseline.measurements || baseline.biometrics || {};
    const m2 = this.data?.measurements || {};
    const factor = this.unit === 'in' ? 0.393701 : 1;
    const allKeys = [...new Set([...Object.keys(m1), ...Object.keys(m2)])];
    let deltaHTML = '';
    for (const key of allKeys) {
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
    return `<div class="ms-compare-grid">
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

  // ═══ VIEW MODE ═══
  switchView(mode) {
    this.viewMode = mode;
    document.querySelectorAll('#view-scanresult .ms-tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`#view-scanresult .ms-tab[onclick*="${mode}"]`)?.classList.add('active');
    const body = document.getElementById('ms-sheet-body');
    const title = document.getElementById('ms-sheet-title');
    if (body) body.innerHTML = this.buildSheetContent();
    if (title) {
      const titles = { avatar: 'Measurements', sizes: 'Size Chart', metrics: 'All Metrics', shape: 'Body Shape', compare: 'Compare Scans' };
      title.textContent = titles[mode] || 'Measurements';
    }
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
    document.querySelectorAll('#view-scanresult .ms-meas-item').forEach(el => el.classList.remove('active'));
    const items = document.querySelectorAll('#view-scanresult .ms-meas-item');
    items.forEach(el => { if (el.querySelector('.ms-meas-name')?.textContent === key) el.classList.add('active'); });
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
        const yPct = MEASUREMENT_Y[this.selectedMeasurement] || 0.5;
        const color = MEASUREMENT_COLORS[this.selectedMeasurement] || '#C6FF00';
        this.viewerInstance.showMeasurementRing(yPct, color);
      } else {
        this.viewerInstance.clearMeasurementRings();
      }
    }
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
    const meshUrl = this.data?.mesh_url;
    if (meshUrl) {
      const lm = this.data?.landmarks;
      const lm3d = lm ? Object.fromEntries(Object.entries(lm).map(([k, v]) => [k, { x: v[0], y: v[1], z: 0 }])) : null;
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 15000);
      fetch(meshUrl, { signal: controller.signal })
        .then(r => { clearTimeout(timeout); if (!r.ok) throw new Error('Missing'); return r.text(); })
        .then(text => {
          const meshData = this.viewerInstance.parseAndRenderOBJ(text);
          if (meshData && lm3d) this.viewerInstance.renderLandmarks(lm3d, meshData.size);
          if (meshData) {
            this.viewerInstance.mesh.geometry.attributes.position.usage = THREE.DynamicDrawUsage;
            setTimeout(() => {
              if (this.overlaysVisible && this.viewerInstance) {
                const yPct = MEASUREMENT_Y[this.selectedMeasurement] || 0.5;
                const color = MEASUREMENT_COLORS[this.selectedMeasurement] || '#C6FF00';
                this.viewerInstance.showMeasurementRing(yPct, color);
              }
            }, 300);
          }
        })
        .catch(() => {});
    } else {
      setTimeout(() => {
        if (this.overlaysVisible && this.viewerInstance) {
          const yPct = MEASUREMENT_Y[this.selectedMeasurement] || 0.5;
          const color = MEASUREMENT_COLORS[this.selectedMeasurement] || '#C6FF00';
          this.viewerInstance.showMeasurementRing(yPct, color);
        }
      }, 600);
    }
  },

  initCompareViewers() {
    const baselineViz = window.createKorraVisualizer?.();
    const currentViz = window.createKorraVisualizer?.();
    if (baselineViz) baselineViz.init('ms-compare-baseline');
    if (currentViz) currentViz.init('ms-compare-current');
    const clientName = this.data?.client_name;
    const scans = (window.masterHistory || []).filter(s => s.client_name === clientName && s !== this.data);
    if (scans.length > 0) {
      const baseline = scans[scans.length - 1];
      if (baseline.mesh_url && baselineViz) {
        fetch(baseline.mesh_url).then(r => r.ok ? r.text() : null).then(t => { if (t) baselineViz.parseAndRenderOBJ(t); }).catch(() => {});
      }
      if (this.data?.mesh_url && currentViz) {
        fetch(this.data.mesh_url).then(r => r.ok ? r.text() : null).then(t => { if (t) currentViz.parseAndRenderOBJ(t); }).catch(() => {});
      }
    }
  },

  // ═══ AI ═══
  openAI() {
    this.aiOpen = true;
    document.getElementById('ms-ai-drawer')?.classList.add('open');
  },
  closeAI() {
    this.aiOpen = false;
    document.getElementById('ms-ai-drawer')?.classList.remove('open');
  },
  async askAI(prompt) {
    if (!prompt?.trim()) return;
    const body = document.getElementById('ms-ai-body');
    const input = document.getElementById('ms-ai-input');
    if (!body) return;
    body.insertAdjacentHTML('beforeend', `<div class="ms-ai-message user">${prompt}</div>`);
    if (input) input.value = '';
    body.scrollTop = body.scrollHeight;
    body.insertAdjacentHTML('beforeend', `<div class="ms-ai-message assistant" id="ms-ai-loading" style="animation:msPulse 1s infinite">Thinking...</div>`);
    body.scrollTop = body.scrollHeight;
    try {
      const res = await fetch('/api/v2/ai/assist', {
        method: 'POST',
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
      document.getElementById('ms-ai-loading')?.remove();
      body.insertAdjacentHTML('beforeend', `<div class="ms-ai-message assistant">AI assistant unavailable. Please try again later.</div>`);
    }
    body.scrollTop = body.scrollHeight;
  },

  // ═══ NAVIGATION ═══
  goBack() {
    this.cleanup();
    window.switchTab(this._previousTab || 'vault');
  },

  cleanup() {
    this.active = false;
    this.data = null;
    if (this.viewerInstance && this.viewerInstance !== window.KORRA_VIZ) {
      this.viewerInstance.clearMeasurementRings?.();
    }
    this.viewerInstance = null;
    const aiDrawer = document.getElementById('ms-ai-drawer');
    if (aiDrawer) aiDrawer.classList.remove('open');
    this.aiOpen = false;
    this.sheetExpanded = false;
  }
};
