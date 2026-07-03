const KORRA_TO_FS = {
  'Chest Round': 'chest',
  'Waist Round': 'waist',
  'Hip Round': 'hips',
  'Neck Round': 'neckCircumference',
  'Across Shoulder': 'shoulderToShoulder',
  'Shoulder': 'shoulderToShoulder',
  'Neck to Waist': 'shoulderToWaist',
  'Waist to Hip': 'waistToHips',
  'Bicep Round': 'bicepsCircumference',
  'Wrist Round': 'wristCircumference',
  'Sleeve Length': 'shoulderToWrist',
  'Inseam': 'inseam',
  'Thigh Round': 'thighCircumference',
  'Calf Round': 'calfCircumference',
  'Half Length': 'waistToHem',
  'Full Top Length': 'shoulderToHem',
};

const FS_TO_KORRA_LIST = {};
for (const [korraKey, fsKey] of Object.entries(KORRA_TO_FS)) {
  if (!FS_TO_KORRA_LIST[fsKey]) FS_TO_KORRA_LIST[fsKey] = [];
  FS_TO_KORRA_LIST[fsKey].push(korraKey);
}

const REQUIRED_BY_PATTERN = {
  shirt: ['chest', 'waist', 'hips', 'neckCircumference', 'shoulderToShoulder', 'shoulderToWaist', 'waistToHips', 'bicepsCircumference', 'shoulderToWrist', 'wristCircumference'],
  jacket: ['chest', 'waist', 'hips', 'neckCircumference', 'shoulderToShoulder', 'shoulderToWaist', 'waistToHips', 'bicepsCircumference', 'shoulderToWrist', 'wristCircumference'],
  pants: ['waist', 'hips', 'inseam', 'thighCircumference', 'calfCircumference', 'shoulderToWaist', 'waistToHips'],
  skirt: ['waist', 'hips', 'waistToHips'],
  dress: ['chest', 'waist', 'hips', 'neckCircumference', 'shoulderToShoulder', 'shoulderToWaist', 'waistToHips'],
};

export function korraToFreesewing(korraMeasurements, gender) {
  const fs = {};
  const m = korraMeasurements || {};
  for (const [korraKey, fsKey] of Object.entries(KORRA_TO_FS)) {
    if (m[korraKey] != null) {
      fs[fsKey] = m[korraKey] * 10;
    }
  }
  return fs;
}

export function freesewingToKorra(fsMeasurements) {
  const korra = {};
  const m = fsMeasurements || {};
  for (const [fsKey, val] of Object.entries(m)) {
    const names = FS_TO_KORRA_LIST[fsKey];
    if (names && names.length > 0) {
      korra[names[0]] = val / 10;
    }
  }
  return korra;
}

export function getRequiredFreesewingMeasurements(patternType) {
  return REQUIRED_BY_PATTERN[patternType] || REQUIRED_BY_PATTERN.shirt;
}

export function getRequiredKorraMeasurements(patternType) {
  const fsKeys = getRequiredFreesewingMeasurements(patternType);
  return fsKeys
    .map(k => (FS_TO_KORRA_LIST[k] || [])[0])
    .filter(Boolean);
}

function hasAnyKey(obj, keys) {
  return keys ? keys.some(k => obj[k] != null) : false;
}

export function validateMeasurements(korraMeasurements, patternType) {
  const fsKeys = getRequiredFreesewingMeasurements(patternType);
  const missing = [];
  for (const fsKey of fsKeys) {
    const korraNames = FS_TO_KORRA_LIST[fsKey] || [];
    const found = korraNames.some(k => korraMeasurements[k] != null);
    if (!found) {
      missing.push(korraNames[0] || fsKey);
    }
  }
  return {
    valid: missing.length === 0,
    missing,
    provided: fsKeys.length - missing.length,
    total: fsKeys.length,
  };
}

export const PATTERN_EASE = {
  shirt: { chest: 25, waist: 20, hips: 15, biceps: 12, wrist: 8 },
  jacket: { chest: 50, waist: 40, hips: 30, biceps: 25, wrist: 18 },
  pants: { waist: 20, hips: 30, thigh: 30, calf: 20 },
  skirt: { waist: 10, hips: 20 },
  dress: { chest: 30, waist: 20, hips: 20 },
};
