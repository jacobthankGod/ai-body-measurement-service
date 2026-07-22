/**
 * SMPL Shape Engine for Browser
 * Loads .npy files and computes SMPL body shape from betas.
 * No backend needed — pure frontend math.
 */
class SMPLShapeEngine {
  constructor() {
    this.vTemplate = null;   // Float32Array (6890 * 3)
    this.shapedirs = null;   // Float32Array (6890 * 3 * 10)
    this.weights = null;     // regression weights
    this.ready = false;
  }

  async init() {
    const [vt, sd, rw] = await Promise.all([
      this._loadNPY('/models/v_template.npy'),
      this._loadNPY('/models/shapedirs.npy'),
      fetch('/assets/smpl_regression_weights.json').then(r => r.json()),
    ]);
    this.vTemplate = vt.data;
    this.shapedirsFlat = sd.data;
    this.weights = rw;
    this.ready = true;
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
    const sd = this.shapedirsFlat; // (20670, 10)
    const out = new Float32Array(6890 * 3);

    // v = v_template + shapedirs @ betas
    // For each vertex (i), for each coord (c):
    //   out[i*3+c] = vt[i*3+c] + sum_k(sd[(i*3+c)*10 + k] * b[k])
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
   * Convert measurements (cm) to beta parameters.
   * Height is excluded — handled by direct Y-scaling in the visualizer.
   * @param {Object} meas - { chest, waist, hip, shoulder, thigh, bicep, neck }
   * @param {string} gender - 'male' or 'female'
   * @returns {Float32Array} betas (10,)
   */
  measurementsToBetas(meas, gender = 'male') {
    if (!this.ready) throw new Error('SMPLShapeEngine not initialized');
    const reg = this.weights[gender] || this.weights.male;
    const order = this.weights.measurement_order;
    const mean = reg.measurements_mean;
    const std = reg.measurements_std;
    const nMeas = order.length;

    // Normalize measurements
    const mNorm = new Float32Array(nMeas);
    for (let i = 0; i < nMeas; i++) {
      mNorm[i] = ((meas[order[i]] || 0) - mean[i]) / std[i];
    }

    // Ridge regression (linear = predictable)
    const w = reg.weights;   // (10, nMeas)
    const bias = reg.bias;   // (10,)
    const betas = new Float32Array(10);
    for (let i = 0; i < 10; i++) {
      let sum = bias[i];
      for (let j = 0; j < nMeas; j++) {
        sum += w[i][j] * mNorm[j];
      }
      betas[i] = Math.max(-3, Math.min(3, sum));
    }
    return betas;
  }

  /**
   * Parse a numpy .npy file (little-endian, version 1.0/2.0/3.0).
   * Returns { data: Float32Array, shape: number[] }
   */
  async _loadNPY(url) {
    const resp = await fetch(url);
    if (!resp.ok) throw new Error(`Failed to load ${url}: ${resp.status}`);
    const buf = await resp.arrayBuffer();
    const view = new DataView(buf);

    // Validate magic: \x93NUMPY
    const magic = String.fromCharCode(view.getUint8(0), view.getUint8(1),
      view.getUint8(2), view.getUint8(3), view.getUint8(4), view.getUint8(5));
    if (magic !== '\x93NUMPY') throw new Error(`Invalid NPY magic in ${url}`);

    const major = view.getUint8(6);
    const minor = view.getUint8(7);

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

    // Parse dtype — NPY header uses 'descr': '<f8' format
    const dtypeMatch = headerStr.match(/'descr':\s*'([^']+)'/);
    if (!dtypeMatch) throw new Error(`Cannot parse dtype in ${url}: ${headerStr.substring(0, 100)}`);
    const dtypeStr = dtypeMatch[1];

    // Parse shape
    const shapeMatch = headerStr.match(/'shape':\s*\(([^)]+)\)/);
    if (!shapeMatch) throw new Error(`Cannot parse shape in ${url}`);
    const shape = shapeMatch[1].split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n));

    const dataStart = headerStart + headerLen;
    const rawBytes = new Uint8Array(buf, dataStart);

    // Normalize dtype: strip endianness marker (<, >, |) and match common aliases
    const normDtype = dtypeStr.replace(/^<[>]?/, '').replace(/^>/, '');
    // Determine bytes per element
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
    } else if (normDtype.includes('int64') || normDtype === 'i8') {
      elemSize = 8; TypedArray = BigInt64Array;
      // Can't use DataView for BigInt64 in all browsers, use manual
      const total = shape.reduce((a, b) => a * b, 1);
      const arr = new Float32Array(total);
      for (let i = 0; i < total; i++) {
        const lo = view.getUint32(dataStart + i * 8, true);
        const hi = view.getUint32(dataStart + i * 8 + 4, true);
        arr[i] = lo + hi * 4294967296; // approximate
      }
      return { data: arr, shape };
    } else if (normDtype.includes('uint32') || normDtype === 'u4') {
      elemSize = 4; TypedArray = Uint32Array;
      getter = (off) => view.getUint32(off, true);
    } else {
      throw new Error(`Unsupported dtype: ${dtypeStr}`);
    }

    const total = shape.reduce((a, b) => a * b, 1);

    // If dtype is float64, read as float64 then convert to float32 for Three.js
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

// Export as global
window.SMPLShapeEngine = SMPLShapeEngine;
