#!/usr/bin/env node
/**
 * Validate morph system integrity.
 * Run after every phase to ensure nothing is broken.
 *
 * Checks:
 * 1. model_config.json morph_names count matches binary morph count
 * 2. morph_limits arrays have correct length
 * 3. No duplicate morph names
 * 4. Binary file sizes are consistent
 * 5. No NaN/Infinity in morph deltas
 * 6. Limits are sane (low < high for non-boolean morphs)
 */
const fs = require('fs');
const path = require('path');

const CONFIG = JSON.parse(fs.readFileSync('public/models/makehuman/model_config.json', 'utf8'));
const V = 14444;
const V3 = V * 3;
const MORPH_BYTES = V3 * 4; // 173,328 bytes per morph

let errors = 0;
let warnings = 0;

const BOOLEAN_MORPHS = ['shoulder_slope', 'shoulder_angle', 'shoulder_drop', 'stomach_form'];

function check(gender) {
  const mc = CONFIG.models[gender];
  const binPath = `public/models/makehuman/${gender}/${gender}_morphs.bin`;

  if (!fs.existsSync(binPath)) {
    console.error(`❌ ${gender}: binary file not found: ${binPath}`);
    errors++;
    return;
  }

  const binSize = fs.statSync(binPath).size;
  const expectedMorphs = binSize / MORPH_BYTES;

  // Check 1: morph_count matches binary
  if (mc.morph_count !== expectedMorphs) {
    console.error(`❌ ${gender}: morph_count ${mc.morph_count} != binary ${expectedMorphs}`);
    errors++;
  } else {
    console.log(`✅ ${gender}: morph_count ${mc.morph_count} matches binary`);
  }

  // Check 2: morph_names length matches morph_count
  if (mc.morph_names.length !== mc.morph_count) {
    console.error(`❌ ${gender}: morph_names length ${mc.morph_names.length} != morph_count ${mc.morph_count}`);
    errors++;
  } else {
    console.log(`✅ ${gender}: morph_names length ${mc.morph_names.length} matches`);
  }

  // Check 3: morph_limits arrays have correct length
  for (const key of ['low', 'high', 'default']) {
    if (mc.morph_limits[key].length !== mc.morph_count) {
      console.error(`❌ ${gender}: morph_limits.${key} length ${mc.morph_limits[key].length} != morph_count ${mc.morph_count}`);
      errors++;
    } else {
      console.log(`✅ ${gender}: morph_limits.${key} length ${mc.morph_limits[key].length} matches`);
    }
  }

  // Check 4: no duplicate morph names
  const dupes = mc.morph_names.filter((n, i) => mc.morph_names.indexOf(n) !== i);
  if (dupes.length > 0) {
    console.error(`❌ ${gender}: duplicate morph names: ${dupes.join(', ')}`);
    errors++;
  } else {
    console.log(`✅ ${gender}: no duplicate morph names`);
  }

  // Check 5: binary contains no NaN
  const buf = fs.readFileSync(binPath);
  const floats = new Float32Array(buf.buffer, buf.byteOffset, buf.byteLength / 4);
  let nanCount = 0;
  for (let i = 0; i < floats.length; i++) {
    if (isNaN(floats[i]) || !isFinite(floats[i])) nanCount++;
  }
  if (nanCount > 0) {
    console.error(`❌ ${gender}: ${nanCount} NaN/Infinity values in morph binary`);
    errors++;
  } else {
    console.log(`✅ ${gender}: morph binary clean (no NaN)`);
  }

  // Check 6: limits are sane
  for (let i = 0; i < mc.morph_count; i++) {
    const name = mc.morph_names[i];
    if (!BOOLEAN_MORPHS.includes(name)) {
      if (mc.morph_limits.low[i] >= mc.morph_limits.high[i]) {
        console.warn(`⚠️  ${gender}: morph[${i}] ${name} low(${mc.morph_limits.low[i]}) >= high(${mc.morph_limits.high[i]})`);
        warnings++;
      }
    }
  }
}

console.log('=== Morph System Validation ===\n');
check('male');
console.log('');
check('female');
console.log('');
check('child');
console.log(`\n=== Result: ${errors} errors, ${warnings} warnings ===`);
process.exit(errors > 0 ? 1 : 0);
