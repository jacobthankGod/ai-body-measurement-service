/**
 * MeasurementToWeight — Maps user measurements to morph target weights.
 *
 * Uses Inverse-Distance Weighting (IDW) in 3D measurement space.
 * 9 anchor sizes define the space; user measurements are interpolated
 * continuously across all anchors.
 *
 * Usage:
 *   var weights = MeasurementToWeight.computeWeights({ chest: 98, waist: 86, hip: 98 });
 *   // weights = { XXS: 0.0, XS: 0.05, S: 0.15, M: 0.45, ML: 0.25, L: 0.1, XL: 0.0, XXL: 0.0, 3XL: 0.0 }
 */
var MeasurementToWeight = (function() {
  'use strict';

  // 9 anchor sizes — must match config.py SIZES exactly
  var ANCHORS = [
    { name: 'XXS', chest: 82,  waist: 70,  hip: 82,  height: 160 },
    { name: 'XS',  chest: 88,  waist: 76,  hip: 88,  height: 165 },
    { name: 'S',   chest: 94,  waist: 82,  hip: 94,  height: 170 },
    { name: 'M',   chest: 100, waist: 88,  hip: 100, height: 175 },
    { name: 'ML',  chest: 106, waist: 94,  hip: 106, height: 178 },
    { name: 'L',   chest: 112, waist: 100, hip: 112, height: 180 },
    { name: 'XL',  chest: 118, waist: 106, hip: 118, height: 183 },
    { name: 'XXL', chest: 124, waist: 112, hip: 124, height: 185 },
    { name: '3XL', chest: 130, waist: 118, hip: 130, height: 188 },
  ];

  // Morph target names in the GLB (base is identity, not stored)
  var MORPH_NAMES = ['draped_XS', 'draped_S', 'draped_M', 'draped_ML',
                     'draped_L', 'draped_XL', 'draped_XXL', 'draped_3XL'];

  // Measurement ranges for normalization
  var RANGES = { chest: 48, waist: 48, hip: 48 }; // 130 - 82 = 48

  /**
   * Compute morph weights from user measurements using IDW.
   *
   * @param {Object} m - { chest: cm, waist: cm, hip: cm }
   * @returns {Object} { XXS: weight, XS: weight, ..., 3XL: weight }
   *   Base (XXS) weight = 1 - sum(other weights)
   */
  function computeWeights(m) {
    var chest = m.chest || m['Chest Round'] || m.chest_circ || 100;
    var waist = m.waist || m['Waist Round'] || 88;
    var hip   = m.hip   || m['Hip Round']   || m.hip_circ || 100;

    // Compute normalized Euclidean distance to each anchor
    var distances = [];
    for (var i = 0; i < ANCHORS.length; i++) {
      var a = ANCHORS[i];
      var dx = (chest - a.chest) / RANGES.chest;
      var dy = (waist - a.waist) / RANGES.waist;
      var dz = (hip - a.hip) / RANGES.hip;
      distances.push(Math.sqrt(dx * dx + dy * dy + dz * dz));
    }

    // IDW with p=2 (standard exponent)
    var epsilon = 0.001; // Prevent division by zero
    var rawWeights = [];
    for (var i = 0; i < distances.length; i++) {
      rawWeights.push(1.0 / ((distances[i] + epsilon) * (distances[i] + epsilon)));
    }

    // The first anchor (XXS) is the base identity — its weight is implicit
    // Normalize remaining weights to sum to <= 1.0
    var sumOthers = 0;
    for (var i = 1; i < rawWeights.length; i++) {
      sumOthers += rawWeights[i];
    }

    var result = {};
    if (sumOthers < 1e-6) {
      // Exact match or very close to XXS
      result['XXS'] = 1.0;
      for (var i = 1; i < ANCHORS.length; i++) {
        result[ANCHORS[i].name] = 0.0;
      }
    } else {
      // Normalize: morph weight for anchor i = rawWeight_i / sumOthers
      // But clamp total to 1.0 (XXS gets the remainder)
      var totalMorph = 0;
      var morphWeights = [];
      for (var i = 1; i < rawWeights.length; i++) {
        var w = rawWeights[i] / sumOthers;
        w = Math.max(0, Math.min(1, w));
        morphWeights.push(w);
        totalMorph += w;
      }

      // If total morph > 1.0, scale down
      if (totalMorph > 1.0) {
        for (var i = 0; i < morphWeights.length; i++) {
          morphWeights[i] /= totalMorph;
        }
        totalMorph = 1.0;
      }

      // XXS weight = 1 - sum of morphs
      result['XXS'] = Math.max(0, 1.0 - totalMorph);
      for (var i = 0; i < morphWeights.length; i++) {
        result[ANCHORS[i + 1].name] = morphWeights[i];
      }
    }

    return result;
  }

  /**
   * Convert weight dict to array for morphTargetInfluences.
   * Array order matches MORPH_NAMES: [XS, S, M, ML, L, XL, XXL, 3XL]
   *
   * @param {Object} weights - from computeWeights()
   * @returns {Float32Array} morph influences array
   */
  function toMorphArray(weights) {
    var arr = new Float32Array(MORPH_NAMES.length);
    for (var i = 0; i < MORPH_NAMES.length; i++) {
      var sizeName = MORPH_NAMES[i].replace('draped_', '');
      arr[i] = weights[sizeName] || 0;
    }
    return arr;
  }

  /**
   * Get the dominant (nearest) anchor name.
   */
  function getNearestAnchor(m) {
    var weights = computeWeights(m);
    var best = 'XXS';
    var bestW = 0;
    for (var name in weights) {
      if (weights[name] > bestW) {
        bestW = weights[name];
        best = name;
      }
    }
    return best;
  }

  return {
    ANCHORS: ANCHORS,
    MORPH_NAMES: MORPH_NAMES,
    computeWeights: computeWeights,
    toMorphArray: toMorphArray,
    getNearestAnchor: getNearestAnchor,
  };
})();

window.MeasurementToWeight = MeasurementToWeight;
