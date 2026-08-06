// Outfit configuration
const OUTFITS = [
  { id: '1', name: 'Classic T-Shirt', category: 'Casual', lensId: 'ccc9d825-d8ec-41ca-910a-7fd372065026', groupId: '6af97e7a-6e80-4d9e-86b7-8ffe3a6bd150' },
  { id: '2', name: 'Formal Shirt', category: 'Business', lensId: 'ccc9d825-d8ec-41ca-910a-7fd372065026', groupId: '6af97e7a-6e80-4d9e-86b7-8ffe3a6bd150' },
  { id: '3', name: 'Traditional Agbada', category: 'Traditional', lensId: 'ccc9d825-d8ec-41ca-910a-7fd372065026', groupId: '6af97e7a-6e80-4d9e-86b7-8ffe3a6bd150' },
  { id: '4', name: 'Ankara Print', category: 'Traditional', lensId: 'ccc9d825-d8ec-41ca-910a-7fd372065026', groupId: '6af97e7a-6e80-4d9e-86b7-8ffe3a6bd150' },
  { id: '5', name: 'Wedding Suit', category: 'Formal', lensId: 'ccc9d825-d8ec-41ca-910a-7fd372065026', groupId: '6af97e7a-6e80-4d9e-86b7-8ffe3a6bd150' },
];

const SVG_PAUSE = '<svg viewBox="0 0 24 24"><rect x="6" y="4" width="4" height="16" rx="1"/><rect x="14" y="4" width="4" height="16" rx="1"/></svg>';
const SVG_PLAY = '<svg viewBox="0 0 24 24"><polygon points="5,3 19,12 5,21"/></svg>';

let cameraKit = null;
let captures = [];
let selectedOutfit = null;
let isPaused = false;

const loadingOverlay = document.getElementById('loading-overlay');
const loadingText = document.getElementById('loading-text');
const cameraStatus = document.getElementById('camera-status');
const outfitStrip = document.getElementById('outfit-strip');
const capturesGrid = document.getElementById('captures-grid');
const btnCapture = document.getElementById('btn-capture');
const btnPause = document.getElementById('btn-pause');
const btnRemoveLens = document.getElementById('btn-remove-lens');
const btnFlipCamera = document.getElementById('btn-flip-camera');

async function init() {
  try {
    cameraKit = new CameraKitTryOn();
    cameraKit.statusEl = cameraStatus;

    loadingText.textContent = 'Loading Camera Kit SDK...';
    await cameraKit.initialize();

    loadingText.textContent = 'Creating camera session...';
    await cameraKit.createSession('tryon-canvas');

    loadingText.textContent = 'Starting camera...';
    const cameraStarted = await cameraKit.startCamera();

    if (!cameraStarted) {
      throw new Error('Failed to start camera');
    }

    loadingText.textContent = 'Loading augmented outfits...';
    await loadOutfits();

    loadingOverlay.classList.add('hidden');
    setupEventListeners();

  } catch (error) {
    console.error('Initialization error:', error);
    loadingText.innerHTML =
      '<div class="loading-error">' +
      '<p>Failed to initialize Camera Kit</p>' +
      '<p style="font-size: 12px; margin-top: 8px;">' + error.message + '</p>' +
      '<button class="retry-btn" id="retry-btn">Try Again</button>' +
      '</div>';
    document.getElementById('retry-btn').addEventListener('click', function() { location.reload(); });
  }
}

async function loadOutfits() {
  const outfitsWithIcons = await Promise.all(OUTFITS.map(async function(outfit) {
    try {
      const lens = await cameraKit.cameraKit.lensRepository.loadLens(outfit.lensId, outfit.groupId);
      return { ...outfit, iconUrl: lens.iconUrl };
    } catch (e) {
      return outfit;
    }
  }));

  outfitStrip.innerHTML = outfitsWithIcons.map(function(outfit) {
    const previewContent = outfit.iconUrl
      ? '<img src="' + outfit.iconUrl + '" alt="' + outfit.name + '">'
      : '<span>' + outfit.name.charAt(0) + '</span>';

    return '<button class="outfit-chip" data-id="' + outfit.id + '" data-lens-id="' + outfit.lensId + '" data-group-id="' + outfit.groupId + '">' +
      previewContent +
      '</button>';
  }).join('');

  document.querySelectorAll('.outfit-chip').forEach(function(chip) {
    chip.addEventListener('click', function() { selectOutfit(chip); });
  });
}

async function selectOutfit(chip) {
  var lensId = chip.dataset.lensId;
  var groupId = chip.dataset.groupId;

  document.querySelectorAll('.outfit-chip').forEach(function(c) { c.classList.remove('active'); });
  chip.classList.add('active');

  if (lensId && groupId) {
    await cameraKit.applyLens(lensId, groupId);
  } else {
    cameraStatus.textContent = 'Lens not configured for this outfit';
  }

  selectedOutfit = chip.dataset.id;
}

function setupEventListeners() {
  btnCapture.addEventListener('click', async function() {
    var blob = await cameraKit.capturePhoto();
    if (blob) {
      addCapture(blob);
    }
  });

  btnPause.addEventListener('click', function() {
    if (isPaused) {
      cameraKit.resume();
      btnPause.innerHTML = SVG_PAUSE;
      btnPause.classList.remove('active');
    } else {
      cameraKit.pause();
      btnPause.innerHTML = SVG_PLAY;
      btnPause.classList.add('active');
    }
    isPaused = !isPaused;
  });

  btnRemoveLens.addEventListener('click', function() {
    cameraKit.removeLens();
    document.querySelectorAll('.outfit-chip').forEach(function(c) { c.classList.remove('active'); });
    selectedOutfit = null;
  });

  btnFlipCamera.addEventListener('click', async function() {
    await cameraKit.flipCamera();
  });

  document.addEventListener('keydown', function(e) {
    if (e.code === 'Space' && !e.repeat) {
      e.preventDefault();
      btnCapture.click();
    }
  });
}

function addCapture(blob) {
  var url = URL.createObjectURL(blob);
  captures.unshift({ blob: blob, url: url, timestamp: Date.now() });
}

function downloadCapture(capture) {
  var a = document.createElement('a');
  a.href = capture.url;
  a.download = 'korra-tryon-' + capture.timestamp + '.png';
  a.click();
}

init();

window.addEventListener('beforeunload', function() {
  if (cameraKit) {
    cameraKit.destroy();
  }
});
