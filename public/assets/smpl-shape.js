/**
 * SMPL Shape Engine for Browser
 * Loads .npy files and computes SMPL body shape from betas.
 * Supports both Ridge regression (legacy) and MLP neural network.
 * Also loads pre-computed displacement vectors for per-measurement fine-tuning.
 *
 * All UI keys are lowercase_underscore (matching data-measurement in HTML).
 * MLP measurement_order uses Title Case with spaces.
 * This module handles the mapping internally.
 */
class SMPLShapeEngine {
  constructor() {
    this.vTemplate = null;
    this.shapedirsFlat = null;
    this.weights = null;
    this.mlpWeights = null;
    this.displacements = null;
    this.ready = false;

    // UI key (data-measurement) → MLP measurement_order key
    this.UI_TO_MLP = {
      chest: 'Chest Round',
      bust_round: 'Bust Round',
      waist: 'Waist Round',
      stomach: 'Stomach Round',
      hip: 'Hip Round',
      neck: 'Neck Round',
      thigh: 'Thigh Round',
      knee_round: 'Knee Round',
      calf_round: 'Calf Round',
      ankle_round: 'Ankle Round',
      bicep: 'Bicep Round',
      elbow_round: 'Elbow Round',
      wrist_round: 'Wrist Round',
      upper_hip: 'Upper Hip',
      armhole_round: 'Armhole Round',
      shoulder: 'Shoulder',
      across_shoulder: 'Across Shoulder',
      across_back: 'Across Back',
      across_chest: 'Across Chest',
      half_length: 'Half Length',
      full_top_length: 'Full Top Length',
      back_waist_length: 'Back Waist Length',
      front_waist_length: 'Front Waist Length',
      neck_to_waist: 'Neck to Waist',
      shoulder_to_waist: 'Shoulder to Waist',
      waist_to_hip: 'Waist to Hip',
      crotch_depth: 'Crotch Depth',
      trouser_waist: 'Trouser Waist',
      trouser_length: 'Trouser Length',
      inseam: 'Inseam',
      sleeve_length: 'Sleeve Length',
      high_bust: 'High Bust',
      under_bust: 'Under Bust',
      bust_point: 'Bust Point',
      shoulder_to_bust: 'Shoulder to Bust Point',
      shoulder_to_under_bust: 'Shoulder to Under Bust',
    };

    // Reverse: MLP key → UI key
    this.MLP_TO_UI = {};
    for (const [ui, mlp] of Object.entries(this.UI_TO_MLP)) {
      this.MLP_TO_UI[mlp] = ui;
    }
  }

  async init() {
    const [vt, sd, rw, mlp, disp] = await Promise.all([
      this._loadNPY('/models/v_template.npy'),
      this._loadNPY('/models/shapedirs.npy'),
      fetch('/assets/smpl_regression_weights.json').then(r => r.json()),
      fetch('/assets/smpl_mlp_weights.json').then(r => r.json()).catch(() => null),
      fetch('/assets/smpl_displacements.json').then(r => r.json()).catch(() => null),
    ]);
    this.vTemplate = vt.data;
    this.shapedirsFlat = sd.data;
    this.weights = rw;
    this.mlpWeights = mlp;
    this.displacements = disp;
    this.ready = true;
    console.log(`SMPLShapeEngine ready: MLP=${!!mlp}, displacements=${!!disp}`);
  }

  /**
   * Compute body shape vertices from beta parameters.
   * @param {Float32Array|Array} betas - 10 shape coefficients
   * @returns {Float32Array} vertex positions (6890 * 3)
   */
  computeBodyShape(betas) {
    if (!this.ready) throw new Error('SMPLShapeEngine not initialized');
    const b = new Float32Array(10);
    for (let i = 0; i < 10; i++) b[i] = betas[i] || 0;

    const vt = this.vTemplate;
    const sd = this.shapedirsFlat;
    const out = new Float32Array(6890 * 3);

    for (let vc = 0; vc < 20670; vc++) {
      let delta = 0;
      const row = vc * 10;
      for (let k = 0; k < 10; k++) {
        delta += sd[row + k] * b[k];
      }
      out[vc] = vt[vc] + delta;
    }
    return out;
  }

  /**
   * Convert UI measurements (lowercase_underscore keys) to betas via MLP.
   * Falls back to Ridge regression if MLP unavailable.
   * @param {Object} meas - measurements with UI keys (e.g. {chest: 95, waist: 80, ...})
   * @param {string} gender - 'male' or 'female'
   * @returns {Float32Array} betas (10,)
   */
  measurementsToBetas(meas, gender = 'male') {
    if (!this.ready) throw new Error('SMPLShapeEngine not initialized');

    // Try MLP first
    if (this.mlpWeights && this.mlpWeights[gender]) {
      const mlp = this.mlpWeights;
      const gWeights = mlp[gender].weights;
      const order = mlp.measurement_order; // ['Chest Round', 'Bust Round', ...]
      const mean = mlp.meas_mean;
      const std = mlp.meas_std;

      const xNorm = new Float32Array(36);
      for (let i = 0; i < order.length; i++) {
        // Convert MLP key back to UI key to look up in meas
        const uiKey = this.MLP_TO_UI[order[i]] || order[i];
        xNorm[i] = ((meas[uiKey] || 0) - mean[i]) / std[i];
      }
      xNorm[35] = gender === 'female' ? 1.0 : 0.0;

      const betas = this._mlpForward(xNorm, gender, gWeights);
      if (betas) return betas;
    }

    // Fallback to Ridge regression
    return this._ridgeRegression(meas, gender);
  }

  /**
   * MLP forward pass: normalized measurements -> betas.
   * Architecture: 36 -> 128 -> ReLU -> 64 -> ReLU -> 10
   */
  _mlpForward(xNorm, gender, weights) {
    const w = weights || (this.mlpWeights && this.mlpWeights[gender] && this.mlpWeights[gender].weights);
    if (!w) return null;

    const l0w = w['net.0.weight'];
    const l0b = w['net.0.bias'];
    const h0 = new Float32Array(128);
    for (let i = 0; i < 128; i++) {
      let sum = l0b[i];
      for (let j = 0; j < 36; j++) sum += l0w[i][j] * xNorm[j];
      h0[i] = sum > 0 ? sum : 0;
    }

    const l3w = w['net.3.weight'];
    const l3b = w['net.3.bias'];
    const h3 = new Float32Array(64);
    for (let i = 0; i < 64; i++) {
      let sum = l3b[i];
      for (let j = 0; j < 128; j++) sum += l3w[i][j] * h0[j];
      h3[i] = sum > 0 ? sum : 0;
    }

    const l6w = w['net.6.weight'];
    const l6b = w['net.6.bias'];
    const out = new Float32Array(10);
    for (let i = 0; i < 10; i++) {
      let sum = l6b[i];
      for (let j = 0; j < 64; j++) sum += l6w[i][j] * h3[j];
      out[i] = Math.max(-2, Math.min(2, sum));
    }
    return out;
  }

  /**
   * Legacy Ridge regression: 7 measurements -> 10 betas.
   */
  _ridgeRegression(meas, gender) {
    const reg = this.weights[gender] || this.weights.male;
    const order = this.weights.measurement_order;
    const mean = reg.measurements_mean;
    const std = reg.measurements_std;
    const nMeas = order.length;

    const mNorm = new Float32Array(nMeas);
    for (let i = 0; i < nMeas; i++) {
      mNorm[i] = ((meas[order[i]] || 0) - mean[i]) / std[i];
    }

    const w = reg.weights;
    const bias = reg.bias;
    const betas = new Float32Array(10);
    for (let i = 0; i < 10; i++) {
      let sum = bias[i];
      for (let j = 0; j < nMeas; j++) {
        sum += w[i][j] * mNorm[j];
      }
      betas[i] = Math.max(-2, Math.min(2, sum));
    }
    return betas;
  }

  /**
   * Apply displacement vectors to mesh vertices.
   * @param {Float32Array} positions - vertex positions (6890 * 3), modified in-place
   * @param {Object} measurements - UI-key measurements (e.g. {chest: 95, elbow_round: 22})
   * @param {Object} actualMeasurements - actual values from mesh (UI keys)
   */
  applyDisplacements(positions, measurements, actualMeasurements) {
    if (!this.displacements) return;
    const ud = this.displacements.unit_deltas;
    const disp = this.displacements.displacements;
    if (!ud || !disp) return;

    for (const uiKey of Object.keys(measurements)) {
      const target = measurements[uiKey];
      const actual = actualMeasurements[uiKey];
      if (target === undefined || actual === undefined) continue;
      if (actual <= 0) continue;

      const residual = target - actual;
      if (Math.abs(residual) < 0.1) continue;

      // Convert UI key to displacement key (Title Case)
      const dispKey = this.UI_TO_MLP[uiKey] || uiKey;
      const delta = ud[dispKey];
      if (!delta || !delta.indices || delta.indices.length === 0) continue;

      const d = disp[dispKey];
      let scale = residual;

      scale = Math.max(-5, Math.min(5, scale));

      for (let i = 0; i < delta.indices.length; i++) {
        const vi = delta.indices[i];
        positions[vi * 3]     += delta.dx[i] * scale;
        positions[vi * 3 + 1] += delta.dy[i] * scale;
        positions[vi * 3 + 2] += delta.dz[i] * scale;
      }
    }
  }

  async _loadNPY(url) {
    const resp = await fetch(url);
    if (!resp.ok) throw new Error(`Failed to load ${url}: ${resp.status}`);
    const buf = await resp.arrayBuffer();
    const view = new DataView(buf);

    const magic = String.fromCharCode(view.getUint8(0), view.getUint8(1),
      view.getUint8(2), view.getUint8(3), view.getUint8(4), view.getUint8(5));
    if (magic !== '\x93NUMPY') throw new Error(`Invalid NPY magic in ${url}`);

    const major = view.getUint8(6);
    let headerLen, headerStart;
    if (major === 1) {
      headerLen = view.getUint16(8, true);
      headerStart = 10;
    } else {
      headerLen = view.getUint32(8, true);
      headerStart = 12;
    }

    const headerStr = new TextDecoder().decode(
      new Uint8Array(buf, headerStart, headerLen)
    );

    const dtypeMatch = headerStr.match(/'descr':\s*'([^']+)'/);
    if (!dtypeMatch) throw new Error(`Cannot parse dtype in ${url}`);
    const dtypeStr = dtypeMatch[1];

    const shapeMatch = headerStr.match(/'shape':\s*\(([^)]+)\)/);
    if (!shapeMatch) throw new Error(`Cannot parse shape in ${url}`);
    const shape = shapeMatch[1].split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n));

    const dataStart = headerStart + headerLen;
    const normDtype = dtypeStr.replace(/^<[>]?/, '').replace(/^>/, '');
    let elemSize, getter, TypedArray;

    if (normDtype.includes('float64') || normDtype === 'f8' || normDtype === 'double') {
      elemSize = 8; TypedArray = Float64Array;
      getter = (off) => view.getFloat64(off, true);
    } else if (normDtype.includes('float32') || normDtype === 'f4' || normDtype === 'single') {
      elemSize = 4; TypedArray = Float32Array;
      getter = (off) => view.getFloat32(off, true);
    } else if (normDtype.includes('int32') || normDtype === 'i4') {
      elemSize = 4; TypedArray = Int32Array;
      getter = (off) => view.getInt32(off, true);
    } else if (normDtype.includes('uint32') || normDtype === 'u4') {
      elemSize = 4; TypedArray = Uint32Array;
      getter = (off) => view.getUint32(off, true);
    } else {
      throw new Error(`Unsupported dtype: ${dtypeStr}`);
    }

    const total = shape.reduce((a, b) => a * b, 1);

    if (normDtype.includes('float64') || normDtype === 'f8') {
      const arr = new Float64Array(total);
      for (let i = 0; i < total; i++) {
        arr[i] = getter(dataStart + i * elemSize);
      }
      return { data: new Float32Array(arr), shape };
    }

    const arr = new TypedArray(total);
    for (let i = 0; i < total; i++) {
      arr[i] = getter(dataStart + i * elemSize);
    }
    return { data: arr, shape };
  }
}

window.SMPLShapeEngine = SMPLShapeEngine;
