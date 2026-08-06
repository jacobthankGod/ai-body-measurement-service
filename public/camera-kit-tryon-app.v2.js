// Outfit configuration
const OUTFITS = [
  { id: '1', name: 'Classic T-Shirt', category: 'Casual', lensId: 'ccc9d825-d8ec-41ca-910a-7fd372065026', groupId: '6af97e7a-6e80-4d9e-86b7-8ffe3a6bd150' },
  { id: '2', name: 'Formal Shirt', category: 'Business', lensId: 'ccc9d825-d8ec-41ca-910a-7fd372065026', groupId: '6af97e7a-6e80-4d9e-86b7-8ffe3a6bd150' },
  { id: '3', name: 'Traditional Agbada', category: 'Traditional', lensId: 'ccc9d825-d8ec-41ca-910a-7fd372065026', groupId: '6af97e7a-6e80-4d9e-86b7-8ffe3a6bd150' },
  { id: '4', name: 'Ankara Print', category: 'Traditional', lensId: 'ccc9d825-d8ec-41ca-910a-7fd372065026', groupId: '6af97e7a-6e80-4d9e-86b7-8ffe3a6bd150' },
  { id: '5', name: 'Wedding Suit', category: 'Formal', lensId: 'ccc9d825-d8ec-41ca-910a-7fd372065026', groupId: '6af97e7a-6e80-4d9e-86b7-8ffe3a6bd150' },
];

let cameraKit = null;
let captures = [];
let selectedOutfit = null;
let isPaused = false;

const loadingOverlay = document.getElementById('loading-overlay');
const loadingText = document.getElementById('loading-text');
const cameraStatus = document.getElementById('camera-status');
const outfitList = document.getElementById('outfit-list');
const capturesGrid = document.getElementById('captures-grid');
const btnCapture = document.getElementById('btn-capture');
const btnPause = document.getElementById('btn-pause');
const btnRemoveLens = document.getElementById('btn-remove-lens');

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

    loadOutfits();
    loadingOverlay.classList.add('hidden');
    setupEventListeners();

  } catch (error) {
    console.error('Initialization error:', error);
    loadingText.innerHTML =
      '<div class="loading-error">' +
      '<p>Failed to initialize Camera Kit</p>' +
      '<p style="font-size: 12px; margin-top: 8px;">' + error.message + '</p>' +
      '<button class="retry-btn" onclick="location.reload()">Try Again</button>' +
      '</div>';
  }
}

function loadOutfits() {
  outfitList.innerHTML = OUTFITS.map(function(outfit) {
    return '<div class="outfit-card" data-id="' + outfit.id + '" data-lens-id="' + outfit.lensId + '" data-group-id="' + outfit.groupId + '">' +
      '<div class="outfit-preview">' + outfit.name + '</div>' +
      '<div class="outfit-name">' + outfit.name + '</div>' +
      '<div class="outfit-category">' + outfit.category + '</div>' +
      '</div>';
  }).join('');

  document.querySelectorAll('.outfit-card').forEach(function(card) {
    card.addEventListener('click', function() { selectOutfit(card); });
  });
}

async function selectOutfit(card) {
  var lensId = card.dataset.lensId;
  var groupId = card.dataset.groupId;

  document.querySelectorAll('.outfit-card').forEach(function(c) { c.classList.remove('active'); });
  card.classList.add('active');

  if (lensId && groupId) {
    await cameraKit.applyLens(lensId, groupId);
  } else {
    cameraStatus.textContent = 'Lens not configured for this outfit';
  }

  selectedOutfit = card.dataset.id;
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
      btnPause.textContent = '\u23F8 Pause';
      btnPause.classList.remove('active');
    } else {
      cameraKit.pause();
      btnPause.textContent = '\u25B6 Resume';
      btnPause.classList.add('active');
    }
    isPaused = !isPaused;
  });

  btnRemoveLens.addEventListener('click', function() {
    cameraKit.removeLens();
    document.querySelectorAll('.outfit-card').forEach(function(c) { c.classList.remove('active'); });
    selectedOutfit = null;
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
  updateCapturesGrid();
}

function updateCapturesGrid() {
  capturesGrid.innerHTML = captures.slice(0, 9).map(function(capture, i) {
    return '<div class="capture-thumb" data-index="' + i + '">' +
      '<img src="' + capture.url + '" alt="Capture ' + (i + 1) + '">' +
      '</div>';
  }).join('');

  document.querySelectorAll('.capture-thumb').forEach(function(thumb) {
    thumb.addEventListener('click', function() {
      var index = parseInt(thumb.dataset.index);
      downloadCapture(captures[index]);
    });
  });
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
