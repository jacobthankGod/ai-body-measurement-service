const OUTFITS = [
  { id: '1', name: 'Classic T-Shirt', category: 'Casual', lensId: 'ccc9d825-d8ec-41ca-910a-7fd372065026', groupId: '6af97e7a-6e80-4d9e-86b7-8ffe3a6bd150', color: '#f5f5f5' },
  { id: '2', name: 'Formal Shirt', category: 'Business', lensId: 'ccc9d825-d8ec-41ca-910a-7fd372065026', groupId: '6af97e7a-6e80-4d9e-86b7-8ffe3a6bd150', color: '#3b82f6' },
  { id: '3', name: 'Traditional Agbada', category: 'Traditional', lensId: 'ccc9d825-d8ec-41ca-910a-7fd372065026', groupId: '6af97e7a-6e80-4d9e-86b7-8ffe3a6bd150', color: '#8b5cf6' },
  { id: '4', name: 'Ankara Print', category: 'Traditional', lensId: 'ccc9d825-d8ec-41ca-910a-7fd372065026', groupId: '6af97e7a-6e80-4d9e-86b7-8ffe3a6bd150', color: '#f59e0b' },
  { id: '5', name: 'Wedding Suit', category: 'Formal', lensId: 'ccc9d825-d8ec-41ca-910a-7fd372065026', groupId: '6af97e7a-6e80-4d9e-86b7-8ffe3a6bd150', color: '#1f2937' },
];

const SVG_PAUSE = '<svg viewBox="0 0 24 24"><rect x="6" y="4" width="4" height="16" rx="1"/><rect x="14" y="4" width="4" height="16" rx="1"/></svg>';
const SVG_PLAY = '<svg viewBox="0 0 24 24"><polygon points="5,3 19,12 5,21"/></svg>';

let cameraKit = null;
let captures = [];
let selectedOutfitIndex = -1;
let isPaused = false;

const loadingOverlay = document.getElementById('loading-overlay');
const loadingText = document.getElementById('loading-text');
const cameraStatus = document.getElementById('camera-status');
const outfitStrip = document.getElementById('outfit-strip');
const outfitDots = document.getElementById('outfit-dots');
const sidebarOutfitList = document.getElementById('sidebar-outfit-list');
const sidebarCaptures = document.getElementById('sidebar-captures');
const btnCapture = document.getElementById('btn-capture');
const btnPause = document.getElementById('btn-pause');
const btnRemoveLens = document.getElementById('btn-remove-lens');
const btnFlipCamera = document.getElementById('btn-flip-camera');
const btnToggleSidebar = document.getElementById('btn-toggle-sidebar');
const btnRestoreSidebar = document.getElementById('btn-restore-sidebar');

function createOutfitThumbnailSVG(outfit) {
  return '<div style="width:100%;aspect-ratio:1;background:' + outfit.color + ';display:flex;align-items:center;justify-content:center;">' +
    '<svg viewBox="0 0 64 64" width="40" height="40" fill="none" stroke="rgba(0,0,0,0.3)" stroke-width="2">' +
    '<path d="M22 18l-8 4v14l8 4h20l8-4V22l-8-4z"/>' +
    '<path d="M22 18v22"/>' +
    '<path d="M42 18v22"/>' +
    '</svg></div>';
}

function renderOutfitStrips(iconMap) {
  var stripHTML = '';
  var dotsHTML = '';

  OUTFITS.forEach(function(outfit, i) {
    var imgContent = iconMap[outfit.id]
      ? '<img class="outfit-chip-img" src="' + iconMap[outfit.id] + '" alt="' + outfit.name + '">'
      : createOutfitThumbnailSVG(outfit);

    stripHTML += '<button class="outfit-chip" data-index="' + i + '">' +
      imgContent +
      '<span class="outfit-chip-label">' + outfit.name + '</span>' +
      '</button>';

    dotsHTML += '<button class="outfit-dot" data-index="' + i + '"></button>';
  });

  outfitStrip.innerHTML = stripHTML;
  outfitDots.innerHTML = dotsHTML;

  outfitStrip.querySelectorAll('.outfit-chip').forEach(function(chip) {
    chip.addEventListener('click', function() {
      selectOutfit(parseInt(chip.dataset.index));
    });
  });

  outfitDots.querySelectorAll('.outfit-dot').forEach(function(dot) {
    dot.addEventListener('click', function() {
      selectOutfit(parseInt(dot.dataset.index));
    });
  });
}

function renderSidebar(iconMap) {
  var html = '';
  OUTFITS.forEach(function(outfit, i) {
    var thumbContent = iconMap[outfit.id]
      ? '<img src="' + iconMap[outfit.id] + '" alt="' + outfit.name + '">'
      : '<div style="width:100%;height:100%;background:' + outfit.color + ';display:flex;align-items:center;justify-content:center;">' +
        '<svg viewBox="0 0 48 64" width="32" height="42" fill="none" stroke="rgba(0,0,0,0.3)" stroke-width="2">' +
        '<path d="M16 14l-6 3v30l6 3h16l6-3V17l-6-3z"/>' +
        '</svg></div>';

    html += '<div class="sidebar-outfit-card" data-index="' + i + '">' +
      '<div class="sidebar-outfit-thumb">' + thumbContent + '</div>' +
      '<div class="sidebar-outfit-info">' +
      '<div class="sidebar-outfit-name">' + outfit.name + '</div>' +
      '<div class="sidebar-outfit-category">' + outfit.category + '</div>' +
      '</div></div>';
  });

  sidebarOutfitList.innerHTML = html;

  sidebarOutfitList.querySelectorAll('.sidebar-outfit-card').forEach(function(card) {
    card.addEventListener('click', function() {
      selectOutfit(parseInt(card.dataset.index));
    });
  });
}

function selectOutfit(index) {
  if (index < 0 || index >= OUTFITS.length) return;

  selectedOutfitIndex = index;
  var outfit = OUTFITS[index];

  document.querySelectorAll('.outfit-chip').forEach(function(c, i) {
    c.classList.toggle('active', i === index);
  });
  document.querySelectorAll('.outfit-dot').forEach(function(d, i) {
    d.classList.toggle('active', i === index);
  });
  document.querySelectorAll('.sidebar-outfit-card').forEach(function(c, i) {
    c.classList.toggle('active', i === index);
  });

  var chip = outfitStrip.querySelectorAll('.outfit-chip')[index];
  if (chip) chip.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });

  cameraKit.applyLens(outfit.lensId, outfit.groupId);
}

function updateCapturesDisplay() {
  if (captures.length === 0) {
    sidebarCaptures.innerHTML = '<div style="padding: 8px; font-size: 12px; color: #525252;">No captures yet</div>';
    return;
  }
  sidebarCaptures.innerHTML = captures.slice(0, 12).map(function(c, i) {
    return '<div class="sidebar-capture-thumb" data-index="' + i + '">' +
      '<img src="' + c.url + '" alt="Capture">' +
      '</div>';
  }).join('');

  sidebarCaptures.querySelectorAll('.sidebar-capture-thumb').forEach(function(thumb) {
    thumb.addEventListener('click', function() {
      downloadCapture(captures[parseInt(thumb.dataset.index)]);
    });
  });
}

function downloadCapture(capture) {
  var a = document.createElement('a');
  a.href = capture.url;
  a.download = 'korra-tryon-' + capture.timestamp + '.png';
  a.click();
}

async function init() {
  try {
    cameraKit = new CameraKitTryOn();
    cameraKit.statusEl = cameraStatus;

    loadingText.textContent = 'Loading Camera Kit SDK...';
    await cameraKit.initialize();

    loadingText.textContent = 'Creating camera session...';
    await cameraKit.createSession('tryon-canvas');

    loadingText.textContent = 'Starting camera...';
    var cameraStarted = await cameraKit.startCamera();
    if (!cameraStarted) throw new Error('Failed to start camera');

    loadingText.textContent = 'Loading augmented outfits...';
    var iconMap = {};
    for (var i = 0; i < OUTFITS.length; i++) {
      try {
        var lens = await cameraKit.cameraKit.lensRepository.loadLens(OUTFITS[i].lensId, OUTFITS[i].groupId);
        iconMap[OUTFITS[i].id] = lens.iconUrl;
      } catch (e) { /* use fallback thumbnail */ }
    }

    renderOutfitStrips(iconMap);
    renderSidebar(iconMap);

    loadingOverlay.classList.add('hidden');
    setupEventListeners();

  } catch (error) {
    console.error('Initialization error:', error);
    loadingText.innerHTML =
      '<div style="text-align:center;">' +
      '<p>Failed to initialize Camera Kit</p>' +
      '<p style="font-size:12px;margin-top:8px;color:#737373;">' + error.message + '</p>' +
      '<button onclick="location.reload()" style="margin-top:12px;padding:8px 20px;background:#c6ff00;color:#000;border:none;border-radius:8px;font-weight:600;cursor:pointer;">Try Again</button>' +
      '</div>';
  }
}

function setupEventListeners() {
  btnCapture.addEventListener('click', async function() {
    var blob = await cameraKit.capturePhoto();
    if (blob) {
      captures.unshift({ blob: blob, url: URL.createObjectURL(blob), timestamp: Date.now() });
      updateCapturesDisplay();
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
    selectedOutfitIndex = -1;
    document.querySelectorAll('.outfit-chip').forEach(function(c) { c.classList.remove('active'); });
    document.querySelectorAll('.outfit-dot').forEach(function(d) { d.classList.remove('active'); });
    document.querySelectorAll('.sidebar-outfit-card').forEach(function(c) { c.classList.remove('active'); });
  });

  btnFlipCamera.addEventListener('click', async function() {
    await cameraKit.flipCamera();
  });

  btnToggleSidebar.addEventListener('click', async function() {
    var sidebar = document.querySelector('.sidebar');
    var main = document.querySelector('.main-container');
    var isCollapsing = !sidebar.classList.contains('collapsed');

    sidebar.classList.toggle('collapsed');
    main.classList.toggle('sidebar-collapsed');

    if (isCollapsing) {
      await cameraKit.changeResolution(1280, 720);
    } else {
      await cameraKit.changeResolution(640, 480);
    }
  });

  btnRestoreSidebar.addEventListener('click', async function() {
    document.querySelector('.sidebar').classList.remove('collapsed');
    document.querySelector('.main-container').classList.remove('sidebar-collapsed');
    await cameraKit.changeResolution(640, 480);
  });

  document.addEventListener('keydown', function(e) {
    if (e.code === 'Space' && !e.repeat) {
      e.preventDefault();
      btnCapture.click();
    }
  });
}

init();

window.addEventListener('beforeunload', function() {
  if (cameraKit) cameraKit.destroy();
});
