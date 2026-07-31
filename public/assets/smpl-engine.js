/**
 * SMPL Engine — browser-native SMPL body shape from measurements.
 *
 * Loads raw binary model files (no NPY parsing) + JSON weights.
 * Two-layer pipeline: MLP betas + per-measurement displacement correction.
 *
 * Public API:
 *   engine.init(basePath) → Promise<void>
 *   engine.measurementsToBetas(meas, gender) → Float32Array(10)
 *   engine.computeBodyShape(betas) → Float32Array(6890*3)
 *   engine.applyDisplacements(positions, targetMeas, actualMeas)
 *   engine.faces → Uint32Array(13776*3)
 *   engine.ready → boolean
 */
var SMPLShapeEngine = (function () {
  'use strict';

  // UI key (data-measurement) → MLP measurement_order key
  // Only 12 truly independent measurements feed the MLP.
  // All other sliders are derived/display-only and do NOT affect betas.
  var UI_TO_MLP = {
    chest: 'Chest Round',
    waist: 'Waist Round',
    hip: 'Hip Round',
    thigh: 'Thigh Round',
    bicep: 'Bicep Round',
    neck: 'Neck Round',
    shoulder: 'Shoulder',
    half_length: 'Half Length',
    waist_to_hip: 'Waist to Hip',
    trouser_length: 'Trouser Length',
    sleeve_length: 'Sleeve Length',
    bust_point: 'Bust Point',
  };

  var MLP_TO_UI = {};
  for (var ui in UI_TO_MLP) MLP_TO_UI[UI_TO_MLP[ui]] = ui;

  function Engine() {
    this.ready = false;
    this.vTemplate = null;  // Float32Array(6890*3)
    this.shapedirs = null;  // Float32Array(20670*10) = (6890*3, 10)
    this.faces = null;      // Uint32Array(13776*3)
    this.mlpWeights = null;
    this.displacements = null;
    this.MLP_TO_UI = MLP_TO_UI;
    this.UI_TO_MLP = UI_TO_MLP;
  }

  Engine.prototype.init = async function (basePath) {
    var base = basePath || '';
    var loadingEl = document.getElementById('visLoading');
    if (loadingEl) loadingEl.textContent = 'Loading body model...';

    // Load binary model files + JSON weights in parallel
    var results = await Promise.all([
      this._loadBin(base + '/models/smpl/v_template.bin'),
      this._loadBin(base + '/models/smpl/shapedirs.bin'),
      this._loadBinU32(base + '/models/smpl/faces.bin'),
      fetch(base + '/assets/smpl_mlp_weights.json').then(function(r) { return r.json(); }),
      fetch(base + '/assets/smpl_displacements.json').then(function(r) { return r.json(); }).catch(function() { return null; }),
    ]);

    this.vTemplate = results[0];   // Float32Array(20670)
    this.shapedirs = results[1];   // Float32Array(206700)
    this.faces = results[2];       // Uint32Array(41328)
    this.mlpWeights = results[3];
    this.displacements = results[4];
    this.ready = true;

    if (loadingEl) loadingEl.style.display = 'none';

    // Diagnostic logging
    var vmin = [Infinity, Infinity, Infinity], vmax = [-Infinity, -Infinity, -Infinity];
    for (var i = 0; i < 6890; i++) {
      for (var c = 0; c < 3; c++) {
        var v = this.vTemplate[i * 3 + c];
        if (v < vmin[c]) vmin[c] = v;
        if (v > vmax[c]) vmax[c] = v;
      }
    }
    console.log('[SMPL] Ready: V=6890 F=13776 betas=10 MLP=' + !!this.mlpWeights + ' disp=' + !!this.displacements);
    console.log('[SMPL] Template X=[' + vmin[0].toFixed(3) + ',' + vmax[0].toFixed(3) + '] Y=[' + vmin[1].toFixed(3) + ',' + vmax[1].toFixed(3) + '] Z=[' + vmin[2].toFixed(3) + ',' + vmax[2].toFixed(3) + ']');
    console.log('[SMPL] Template height: ' + ((vmax[1] - vmin[1]) * 100).toFixed(1) + 'cm');
  };

  /**
   * Compute body shape vertices from 10-dim betas.
   * v = v_template + shapedirs @ betas
   */
  Engine.prototype.computeBodyShape = function (betas) {
    var vt = this.vTemplate;    // (6890*3,)
    var sd = this.shapedirs;    // (6890*3, 10) = (20670, 10)
    var out = new Float32Array(6890 * 3);

    // For each vertex-component: out[i] = vt[i] + sum_k(sd[i*10+k] * betas[k])
    for (var i = 0; i < 20670; i++) {
      var row = i * 10;
      var delta = 0;
      for (var k = 0; k < 10; k++) {
        delta += sd[row + k] * betas[k];
      }
      out[i] = vt[i] + delta;
    }
    return out;
  };

  /**
   * Convert UI measurements → SMPL betas via MLP.
   * Only 12 independent measurements are used; all others are ignored.
   */
  Engine.prototype.measurementsToBetas = function (meas, gender) {
    if (!this.ready) throw new Error('Engine not ready');

    // Try MLP first
    if (this.mlpWeights && this.mlpWeights[gender]) {
      var gWeights = this.mlpWeights[gender].weights;
      var order = this.mlpWeights.measurement_order; // 12 independent measurements
      var mean = this.mlpWeights.meas_mean;
      var std = this.mlpWeights.meas_std;
      var numMeas = order.length; // 12

      var xNorm = new Float32Array(numMeas + 1); // 13 = 12 + 1 gender
      for (var i = 0; i < numMeas; i++) {
        var uiKey = MLP_TO_UI[order[i]] || order[i];
        xNorm[i] = ((meas[uiKey] || 0) - mean[i]) / std[i];
      }
      xNorm[numMeas] = gender === 'female' ? 1.0 : 0.0;

      var betas = this._mlpForward(xNorm, gWeights, numMeas + 1);
      if (betas) return betas;
    }

    return new Float32Array(10); // zero betas fallback
  };

  /**
   * MLP forward pass: N → 128 → ReLU → 64 → ReLU → 10, clamped [-1.5, 1.5].
   * N = numMeasurements + 1 (gender flag). Typically 13.
   */
  Engine.prototype._mlpForward = function (xNorm, weights, inputDim) {
    var w = weights;
    if (!w) return null;
    var nIn = inputDim || xNorm.length;

    // Layer 0: Linear(N, 128) + ReLU
    var l0w = w['net.0.weight']; // [128][N]
    var l0b = w['net.0.bias'];   // [128]
    var h0 = new Float32Array(128);
    for (var i = 0; i < 128; i++) {
      var sum = l0b[i];
      for (var j = 0; j < nIn; j++) sum += l0w[i][j] * xNorm[j];
      h0[i] = sum > 0 ? sum : 0; // ReLU
    }

    // Layer 2: Linear(128, 64) + ReLU
    var l2w = w['net.2.weight']; // [64][128]
    var l2b = w['net.2.bias'];   // [64]
    var h2 = new Float32Array(64);
    for (var i = 0; i < 64; i++) {
      var sum = l2b[i];
      for (var j = 0; j < 128; j++) sum += l2w[i][j] * h0[j];
      h2[i] = sum > 0 ? sum : 0; // ReLU
    }

    // Layer 4: Linear(64, 10), clamped
    var l4w = w['net.4.weight']; // [10][64]
    var l4b = w['net.4.bias'];   // [10]
    var out = new Float32Array(10);
    for (var i = 0; i < 10; i++) {
      var sum = l4b[i];
      for (var j = 0; j < 64; j++) sum += l4w[i][j] * h2[j];
      out[i] = Math.max(-1.5, Math.min(1.5, sum));
    }
    return out;
  };

  /**
   * Apply per-measurement displacement corrections.
   * @param {Float32Array} positions - vertex positions (6890*3), modified in-place
   * @param {Object} targetMeas - target measurements (UI keys)
   * @param {Object} actualMeas - actual measurements from mesh (UI keys)
   */
  Engine.prototype.applyDisplacements = function (positions, targetMeas, actualMeas) {
    if (!this.displacements) return;
    var ud = this.displacements.unit_deltas;
    if (!ud) return;

    for (var uiKey in targetMeas) {
      var target = targetMeas[uiKey];
      var actual = actualMeas[uiKey];
      if (target === undefined || actual === undefined) continue;
      if (actual <= 0) continue;

      var residual = target - actual;
      if (Math.abs(residual) < 0.1) continue;

      var dispKey = UI_TO_MLP[uiKey] || uiKey;
      var delta = ud[dispKey];
      if (!delta || !delta.indices || delta.indices.length === 0) continue;

      var scale = Math.max(-5, Math.min(5, residual));
      for (var i = 0; i < delta.indices.length; i++) {
        var vi = delta.indices[i];
        positions[vi * 3]     += delta.dx[i] * scale;
        positions[vi * 3 + 1] += delta.dy[i] * scale;
        positions[vi * 3 + 2] += delta.dz[i] * scale;
      }
    }
  };

  Engine.prototype._loadBin = function (url) {
    return fetch(url).then(function(r) {
      if (!r.ok) throw new Error('Failed to load ' + url + ': ' + r.status);
      return r.arrayBuffer();
    }).then(function(buf) {
      return new Float32Array(buf);
    });
  };

  Engine.prototype._loadBinU32 = function (url) {
    return fetch(url).then(function(r) {
      if (!r.ok) throw new Error('Failed to load ' + url + ': ' + r.status);
      return r.arrayBuffer();
    }).then(function(buf) {
      return new Uint32Array(buf);
    });
  };

  return Engine;
})();

window.SMPLShapeEngine = SMPLShapeEngine;
