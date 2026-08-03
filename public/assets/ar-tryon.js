/**
 * AR Try-On Module (v16 — merged fixes)
 *
 * - Depth-based projection from landmark→world (softwear VtoPoseEngine approach)
 * - Group-level centering preserves multi-mesh GLB structure
 * - Singleton Pose + WASM warmup (no crash loop)
 * - DPR-aware canvas sizing + lerp smoothing
 * - Front-camera mirror via CSS scaleX(-1)
 * - object-fit:contain letterbox compensation
 */
(function() {
  'use strict';

  var CFG = {
    POSE_CONFIDENCE_INITIAL: 0.3,
    POSE_CONFIDENCE_STABLE: 0.6,
    FRAMES_BEFORE_STABLE: 30,
    MAX_RETRIES: 3,
    TARGET_HEIGHT: 1.7,
    REF_SIZE: 0.5,
    MIN_DEPTH: 0.5,
    MAX_DEPTH: 6.0,
    LERP_SPEED: 0.15,
    CLOTH_ITERATIONS: 3,
    LM: {
      NOSE: 0, LEFT_EYE_INNER: 1, LEFT_EYE: 2, LEFT_EYE_OUTER: 3,
      RIGHT_EYE_INNER: 4, RIGHT_EYE: 5, RIGHT_EYE_OUTER: 6,
      LEFT_EAR: 7, RIGHT_EAR: 8, MOUTH_LEFT: 9, MOUTH_RIGHT: 10,
      LEFT_SHOULDER: 11, RIGHT_SHOULDER: 12,
      LEFT_ELBOW: 13, RIGHT_ELBOW: 14,
      LEFT_WRIST: 15, RIGHT_WRIST: 16,
      LEFT_PINKY: 17, RIGHT_PINKY: 18,
      LEFT_INDEX: 19, RIGHT_INDEX: 20,
      LEFT_THUMB: 21, RIGHT_THUMB: 22,
      LEFT_HIP: 23, RIGHT_HIP: 24,
      LEFT_KNEE: 25, RIGHT_KNEE: 26,
      LEFT_ANKLE: 27, RIGHT_ANKLE: 28,
      LEFT_HEEL: 29, RIGHT_HEEL: 30,
      LEFT_FOOT_INDEX: 31, RIGHT_FOOT_INDEX: 32,
    },
    SKELETON_EDGES: [
      [0,1],[1,2],[2,3],[3,7],[0,4],[4,5],[5,6],[6,8],[9,10],[0,9],[0,10],
      [11,12],[11,23],[12,24],[23,24],
      [11,13],[13,15],[12,14],[14,16],
      [15,17],[15,19],[15,21],[17,19],[16,18],[16,20],[16,22],[18,20],
      [23,25],[25,27],[27,29],[29,31],[27,31],[24,26],[26,28],[28,30],[30,32],[28,32]
    ],
  };

  function v3dist(a, b) {
    var dx=a[0]-b[0], dy=a[1]-b[1], dz=(a[2]||0)-(b[2]||0);
    return Math.sqrt(dx*dx+dy*dy+dz*dz);
  }

  // --- CLOTH SIMULATOR ---
  function ClothSimulator(geometry) {
    this.geometry = geometry;
    var pa = geometry.attributes.position;
    this.n = pa.count;
    this.pos = new Float32Array(this.n * 3);
    this.prev = new Float32Array(this.n * 3);
    for (var i = 0; i < this.n; i++) {
      this.pos[i*3] = pa.getX(i); this.pos[i*3+1] = pa.getY(i); this.pos[i*3+2] = pa.getZ(i);
      this.prev[i*3] = this.pos[i*3]; this.prev[i*3+1] = this.pos[i*3+1]; this.prev[i*3+2] = this.pos[i*3+2];
    }
    this.constraints = [];
    this._buildEdges();
  }
  ClothSimulator.prototype._buildEdges = function() {
    var idx = this.geometry.index; if (!idx) return;
    var seen = {};
    for (var i = 0; i < idx.count; i += 3) {
      var a = idx.getX(i), b = idx.getX(i+1), c = idx.getX(i+2);
      this._edge(seen, a, b); this._edge(seen, b, c); this._edge(seen, c, a);
    }
  };
  ClothSimulator.prototype._edge = function(seen, a, b) {
    var key = Math.min(a,b)+'_'+Math.max(a,b); if (seen[key]) return; seen[key] = 1;
    var dx=this.pos[a*3]-this.pos[b*3], dy=this.pos[a*3+1]-this.pos[b*3+1], dz=this.pos[a*3+2]-this.pos[b*3+2];
    this.constraints.push({ a:a, b:b, rest: Math.sqrt(dx*dx+dy*dy+dz*dz) });
  };
  ClothSimulator.prototype.step = function() {
    var P = this.pos, V = this.prev, D = 0.96, G = -0.002;
    for (var i = 0; i < this.n; i++) {
      var ix=i*3, iy=i*3+1, iz=i*3+2;
      var vx=(P[ix]-V[ix])*D, vy=(P[iy]-V[iy])*D, vz=(P[iz]-V[iz])*D;
      V[ix]=P[ix]; V[iy]=P[iy]; V[iz]=P[iz];
      P[ix]+=vx; P[iy]+=vy+G; P[iz]+=vz;
    }
    for (var iter = 0; iter < CFG.CLOTH_ITERATIONS; iter++) {
      for (var c = 0; c < this.constraints.length; c++) {
        var con = this.constraints[c];
        var ax=con.a*3, bx=con.b*3;
        var dx=P[bx]-P[ax], dy=P[bx+1]-P[ax+1], dz=P[bx+2]-P[ax+2];
        var dd = Math.sqrt(dx*dx+dy*dy+dz*dz) || 1;
        var diff = (dd-con.rest)/dd*0.15;
        P[ax]+=dx*diff; P[ax+1]+=dy*diff; P[ax+2]+=dz*diff;
        P[bx]-=dx*diff; P[bx+1]-=dy*diff; P[bx+2]-=dz*diff;
      }
    }
    var pa = this.geometry.attributes.position;
    for (var i = 0; i < this.n; i++) pa.setXYZ(i, P[i*3], P[i*3+1], P[i*3+2]);
    pa.needsUpdate = true;
  };

  // --- SINGLETON POSE (prevents WASM crash loop) ---
  var _globalPose = null;
  var _globalPoseReady = false;
  var _globalPoseLoading = false;
  var _globalPoseRetries = 0;

  function _ensurePose() {
    if (_globalPose) return _globalPose;
    if (typeof Pose === 'undefined') return null;
    _globalPose = new Pose({
      locateFile: function(file) {
        return 'https://cdn.jsdelivr.net/npm/@mediapipe/pose@0.5.1675469404/' + file;
      }
    });
    _globalPose.setOptions({
      modelComplexity: 2, smoothLandmarks: true,
      minDetectionConfidence: CFG.POSE_CONFIDENCE_INITIAL,
      minTrackingConfidence: CFG.POSE_CONFIDENCE_INITIAL,
    });
    _globalPoseReady = false;
    _globalPoseLoading = false;
    _globalPoseRetries = 0;
    return _globalPose;
  }

  function _warmPose() {
    var pose = _ensurePose();
    if (!pose || _globalPoseReady || _globalPoseLoading) return Promise.resolve();
    _globalPoseLoading = true;
    console.log('[AR] Warming Pose WASM...');
    return new Promise(function(resolve) {
      var c = document.createElement('canvas');
      c.width = 64; c.height = 64;
      var ctx = c.getContext('2d');
      ctx.fillStyle = '#000'; ctx.fillRect(0, 0, 64, 64);
      pose.onResults(function() {
        _globalPoseReady = true;
        _globalPoseLoading = false;
        console.log('[AR] Pose WASM ready');
        pose.onResults(null);
        resolve();
      });
      pose.send({ image: c }).catch(function(e) {
        console.warn('[AR] Pose warmup failed:', e.message || e);
        _globalPoseLoading = false;
        _globalPoseRetries++;
        if (_globalPoseRetries < CFG.MAX_RETRIES) {
          _globalPose = null;
          setTimeout(function() { _globalPoseLoading = false; _warmPose().then(resolve); }, 2000);
        } else {
          resolve();
        }
      });
    });
  }

  // --- CORE ENGINE ---
  function ARTryOn() {
    this.overlay = document.getElementById('arTryOnOverlay');
    this.video = document.getElementById('arVideo');
    this.skelCanvas = document.getElementById('arSkeletonCanvas');
    this.threeCanvas = document.getElementById('arThreeCanvas');

    this.isActive = false;
    this.facingMode = 'user';
    this.stream = null;
    this._dpr = Math.min(window.devicePixelRatio || 1, 2);
    this.lastLandmarks = null;
    this._videoRect = null;
    this._stableFrames = 0;
    this._currentConfidence = CFG.POSE_CONFIDENCE_INITIAL;

    this.renderer = null;
    this.scene = null;
    this.camera3 = null;
    this.garmentMesh = null;
    this.cloth = null;
    this.clock = null;
    this.animFrame = null;
    this.cameraInstance = null;

    this._lerpPos = new THREE.Vector3(0, 0, 2);
    this._lerpScale = 1.0;
    this._savedGalleryRenderers = [];

    this._bind();
    console.log('[AR] v16 initialized');
  }

  ARTryOn.prototype._bind = function() {
    var self = this;
    var bind = function(id, fn) {
      var el = document.getElementById(id);
      if (el) el.addEventListener('click', fn);
      else console.warn('[AR] Missing element:', id);
    };

    bind('arCloseBtn', function() { self.close(); });
    bind('arSwitchBtn', function() { self.switchCamera(); });
    bind('arCaptureBtn', function() { self.capture(); });

    document.querySelectorAll('.gallery-try-btn').forEach(function(btn) {
      btn.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        var url = btn.dataset.garb || btn.dataset.glb;
        var name = btn.dataset.name || 'Garment';
        if (!url) return;
        console.log('[AR] Try-On:', name, url);
        self.open(url, name);
      });
    });
    console.log('[AR] Events bound');
  };

  ARTryOn.prototype.open = async function(url, name) {
    if (this.isActive || !url) return;
    this.isActive = true;
    this._stableFrames = 0;
    this._currentConfidence = CFG.POSE_CONFIDENCE_INITIAL;
    this.lastLandmarks = null;

    this.overlay.style.display = 'flex';
    this.overlay.style.opacity = '1';
    document.getElementById('arGarmentLabel').textContent = name;
    document.getElementById('arLoading').style.display = 'flex';
    document.getElementById('arErrorMsg').classList.remove('show');

    this._disposeGallery();

    var statusEl = document.getElementById('arStatus');
    if (statusEl) statusEl.textContent = 'Starting camera...';
    if (!await this._startCamera()) { this.close(); return; }

    this._initScene();

    if (statusEl) statusEl.textContent = 'Loading body detection...';
    await this._initPose();

    if (statusEl) statusEl.textContent = 'Loading garment...';
    var mesh = await this._loadGarment(url);
    if (mesh) {
      this.garmentMesh = mesh;
      this.scene.add(this.garmentMesh);
      var geo = this._getGeo();
      if (geo) this.cloth = new ClothSimulator(geo);
    }

    document.getElementById('arLoading').style.display = 'none';
    this.clock.start();
    this._animate();
  };

  ARTryOn.prototype.close = function() {
    this.isActive = false;
    cancelAnimationFrame(this.animFrame);

    if (this.cameraInstance) { this.cameraInstance.stop(); this.cameraInstance = null; }
    if (_globalPose) {
      try { _globalPose.onResults(null); } catch(e) {}
    }

    this._stopCamera();

    if (this.renderer) {
      try { this.renderer.renderLists.dispose(); this.renderer.dispose(); } catch(e) {}
      this.renderer = null;
    }
    if (this.garmentMesh && this.scene) {
      this.scene.remove(this.garmentMesh);
      this.garmentMesh.traverse(function(c) {
        if (c.geometry) c.geometry.dispose();
        if (c.material) {
          if (Array.isArray(c.material)) c.material.forEach(function(m) { m.dispose(); });
          else c.material.dispose();
        }
      });
      this.garmentMesh = null;
    }
    this.scene = null;
    this.camera3 = null;
    this.cloth = null;
    this.lastLandmarks = null;

    this.overlay.style.display = 'none';
    this._restoreGallery();
  };

  ARTryOn.prototype._startCamera = async function() {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: this.facingMode, width: { ideal: 1280 }, height: { ideal: 720 } }
      });
      this.video.srcObject = this.stream;
      await this.video.play();
      await this._waitForVideoReady();
      this._resize();
      return true;
    } catch(e) {
      console.error('[AR] Camera failed:', e);
      document.getElementById('arErrorTitle').textContent = 'Camera Access Needed';
      document.getElementById('arErrorDesc').textContent = 'Please allow camera access.';
      document.getElementById('arErrorMsg').classList.add('show');
      return false;
    }
  };

  ARTryOn.prototype._waitForVideoReady = function() {
    var self = this;
    return new Promise(function(resolve) {
      if (self.video.videoWidth > 0 && self.video.videoHeight > 0 && self.video.readyState >= 2) {
        resolve(); return;
      }
      var check = function() {
        if (self.video.videoWidth > 0 && self.video.videoHeight > 0 && self.video.readyState >= 2) resolve();
        else requestAnimationFrame(check);
      };
      requestAnimationFrame(check);
    });
  };

  ARTryOn.prototype._resize = function() {
    var w = this.overlay.clientWidth || window.innerWidth;
    var h = this.overlay.clientHeight || window.innerHeight;
    var dpr = this._dpr;

    this.skelCanvas.width = Math.round(w * dpr);
    this.skelCanvas.height = Math.round(h * dpr);
    this.threeCanvas.width = Math.round(w * dpr);
    this.threeCanvas.height = Math.round(h * dpr);

    var vw = this.video.videoWidth || 1280;
    var vh = this.video.videoHeight || 720;
    var vAspect = vw / vh;
    var eAspect = w / h;
    var ox = 0, oy = 0, rw = w, rh = h;
    if (eAspect > vAspect) { rw = h * vAspect; ox = (w - rw) / 2; }
    else { rh = w / vAspect; oy = (h - rh) / 2; }
    this._videoRect = { offsetX: ox, offsetY: oy, renderW: rw, renderH: rh };

    var isFront = this.facingMode === 'user';
    this.skelCanvas.style.transform = isFront ? 'scaleX(-1)' : 'none';
    this.threeCanvas.style.transform = isFront ? 'scaleX(-1)' : 'none';

    if (this.renderer && this.camera3) {
      this.renderer.setPixelRatio(dpr);
      this.renderer.setSize(w, h);
      this.camera3.aspect = w / h;
      this.camera3.updateProjectionMatrix();
    }
  };

  ARTryOn.prototype._initScene = function() {
    if (this.renderer) return;
    this.clock = new THREE.Clock();

    var w = this.overlay.clientWidth || window.innerWidth;
    var h = this.overlay.clientHeight || window.innerHeight;

    this.scene = new THREE.Scene();
    this.camera3 = new THREE.PerspectiveCamera(50, w / h, 0.01, 1000);
    this.camera3.position.set(0, 0, 2);

    this.renderer = new THREE.WebGLRenderer({ canvas: this.threeCanvas, alpha: true, antialias: true });
    this.renderer.setPixelRatio(this._dpr);
    this.renderer.setSize(w, h);

    this.scene.add(new THREE.AmbientLight(0xffffff, 1.2));
    var dl = new THREE.DirectionalLight(0xffffff, 0.8);
    dl.position.set(1, 2, 3);
    this.scene.add(dl);
    var dl2 = new THREE.DirectionalLight(0xffffff, 0.5);
    dl2.position.set(-1, 1, 2);
    this.scene.add(dl2);
  };

  ARTryOn.prototype._initPose = async function() {
    var self = this;
    await _warmPose();

    var pose = _globalPose;
    if (!pose) {
      console.error('[AR] Pose init failed');
      return;
    }

    pose.onResults(function(r) { self._onResults(r); });

    try {
      pose.setOptions({
        modelComplexity: 2, smoothLandmarks: true,
        minDetectionConfidence: this._currentConfidence,
        minTrackingConfidence: this._currentConfidence,
      });
    } catch(e) {}

    this.cameraInstance = new Camera(this.video, {
      onFrame: async function() {
        if (!self.isActive || !self.cameraInstance) return;
        if (self.video.readyState < 2 || self.video.videoWidth === 0) return;
        try { await pose.send({ image: self.video }); } catch(e) {}
      },
      width: 1280, height: 720,
    });
    this.cameraInstance.start();
  };

  ARTryOn.prototype._onResults = function(results) {
    if (!this.isActive) return;
    if (!results.poseLandmarks) return;

    var l = results.poseLandmarks;
    this.lastLandmarks = l;

    this._stableFrames++;
    if (this._stableFrames === CFG.FRAMES_BEFORE_STABLE) {
      this._currentConfidence = CFG.POSE_CONFIDENCE_STABLE;
      if (_globalPose && _globalPose.setOptions) {
        try {
          _globalPose.setOptions({
            minDetectionConfidence: this._currentConfidence,
            minTrackingConfidence: this._currentConfidence,
          });
        } catch(e) {}
      }
    }

    var ctx = this.skelCanvas.getContext('2d');
    if (!ctx) return;
    ctx.clearRect(0, 0, this.skelCanvas.width, this.skelCanvas.height);

    var vr = this._videoRect;
    if (!vr) return;
    var dpr = this._dpr;

    ctx.strokeStyle = "#76FF03";
    ctx.lineWidth = 4 * dpr;
    ctx.lineCap = "round";
    CFG.SKELETON_EDGES.forEach(function(pair) {
      var p1 = l[pair[0]], p2 = l[pair[1]];
      if (p1 && p2 && p1.visibility > 0.4 && p2.visibility > 0.4) {
        ctx.beginPath();
        ctx.moveTo((vr.offsetX + p1.x * vr.renderW) * dpr, (vr.offsetY + p1.y * vr.renderH) * dpr);
        ctx.lineTo((vr.offsetX + p2.x * vr.renderW) * dpr, (vr.offsetY + p2.y * vr.renderH) * dpr);
        ctx.stroke();
      }
    });
    ctx.fillStyle = "#76FF03";
    for (var i = 0; i < l.length; i++) {
      var p = l[i];
      if (p && p.visibility > 0.4) {
        ctx.beginPath();
        ctx.arc((vr.offsetX + p.x * vr.renderW) * dpr, (vr.offsetY + p.y * vr.renderH) * dpr, 4 * dpr, 0, 2 * Math.PI);
        ctx.fill();
      }
    }

    this._placeGarment(l);
  };

  ARTryOn.prototype._loadGarment = function(url) {
    var self = this;
    return new Promise(function(resolve) {
      var loader = new THREE.GLTFLoader();
      if (window.DRACOLoader) {
        var dr = new THREE.DRACOLoader();
        dr.setDecoderPath('/assets/draco/');
        loader.setDRACOLoader(dr);
      }
      loader.load(url, function(gltf) {
        var mesh = gltf.scene;
        mesh.traverse(function(n) {
          if (!n.isMesh) return;
          var ms = Array.isArray(n.material) ? n.material : [n.material];
          ms.forEach(function(m) {
            m.side = THREE.DoubleSide;
            m.transparent = false;
            m.opacity = 1.0;
            m.depthWrite = true;
            if (m.map) { m.map.format = THREE.RGBAFormat; m.map.type = THREE.UnsignedByteType; m.map.needsUpdate = true; }
            m.needsUpdate = true;
          });
        });

        var box = new THREE.Box3().setFromObject(mesh);
        var size = box.getSize(new THREE.Vector3());
        var center = box.getCenter(new THREE.Vector3());
        var s = CFG.TARGET_HEIGHT / (size.y || 1);
        mesh.scale.setScalar(s);
        mesh.position.set(-center.x * s, -center.y * s, -center.z * s);

        var group = new THREE.Group();
        group.add(mesh);
        resolve(group);
      }, undefined, function(err) {
        console.error('[AR] Garment load failed:', err);
        resolve(null);
      });
    });
  };

  ARTryOn.prototype._getGeo = function() {
    var g = null;
    if (this.garmentMesh) this.garmentMesh.traverse(function(n) { if (n.isMesh && !g) g = n.geometry; });
    return g;
  };

  ARTryOn.prototype._computeDepth = function(shoulderNorm) {
    var tanHalf = Math.tan(THREE.MathUtils.degToRad(this.camera3.fov / 2));
    var d = CFG.REF_SIZE / (2 * Math.max(shoulderNorm, 0.02) * tanHalf * this.camera3.aspect);
    return Math.max(CFG.MIN_DEPTH, Math.min(d, CFG.MAX_DEPTH));
  };

  ARTryOn.prototype._lmToWorld = function(nx, ny, depth) {
    var vr = this._videoRect;
    if (!vr) return [0, 0, 2];
    var w = this.overlay.clientWidth || window.innerWidth;
    var h = this.overlay.clientHeight || window.innerHeight;
    var tanHalf = Math.tan(THREE.MathUtils.degToRad(this.camera3.fov / 2));
    var halfH = tanHalf * depth;
    var halfW = halfH * this.camera3.aspect;
    var px = vr.offsetX + nx * vr.renderW;
    var py = vr.offsetY + ny * vr.renderH;
    var tx = (px / w - 0.5) * 2 * halfW;
    var ty = -(py / h - 0.5) * 2 * halfH;
    var tz = this.camera3.position.z - depth;
    return [tx, ty, tz];
  };

  ARTryOn.prototype._placeGarment = function(lm) {
    if (!this.garmentMesh || !this.camera3 || !this._videoRect) return;
    var L = CFG.LM;
    var ls = lm[L.LEFT_SHOULDER], rs = lm[L.RIGHT_SHOULDER];
    var lh = lm[L.LEFT_HIP], rh = lm[L.RIGHT_HIP];
    if (!ls || !rs || !lh || !rh) { this.garmentMesh.visible = false; return; }
    if (ls.visibility < 0.5 || rs.visibility < 0.5) { this.garmentMesh.visible = false; return; }
    this.garmentMesh.visible = true;

    var shoulderNorm = v3dist([ls.x, ls.y], [rs.x, rs.y]);
    var depth = this._computeDepth(shoulderNorm);

    var cx = (ls.x + rs.x + lh.x + rh.x) / 4;
    var cy = (ls.y + rs.y + lh.y + rh.y) / 4;
    var target = this._lmToWorld(cx, cy, depth);

    this._lerpPos.lerp(new THREE.Vector3(target[0], target[1], target[2]), CFG.LERP_SPEED);
    this.garmentMesh.position.copy(this._lerpPos);
    this.garmentMesh.rotation.z = Math.atan2(rs.y - ls.y, rs.x - ls.x);
  };

  ARTryOn.prototype._animate = function() {
    if (!this.isActive) return;
    var self = this;
    this.animFrame = requestAnimationFrame(function() { self._animate(); });

    if (this.garmentMesh && this.lastLandmarks) {
      this._placeGarment(this.lastLandmarks);
    }

    if (this.cloth) this.cloth.step();

    if (this.renderer && this.scene && this.camera3) {
      this.renderer.render(this.scene, this.camera3);
    }
  };

  ARTryOn.prototype.switchCamera = function() {
    this.facingMode = this.facingMode === 'user' ? 'environment' : 'user';
    this.lastLandmarks = null;
    this._stopCamera();
    this._startCamera();
  };

  ARTryOn.prototype._stopCamera = function() {
    if (this.stream) { this.stream.getTracks().forEach(function(t) { t.stop(); }); this.stream = null; }
    this.video.srcObject = null;
  };

  ARTryOn.prototype.capture = function() {
    var c = document.createElement('canvas');
    c.width = this.video.videoWidth || 1280;
    c.height = this.video.videoHeight || 720;
    var ctx = c.getContext('2d');
    ctx.save();
    if (this.facingMode === 'user') { ctx.translate(c.width, 0); ctx.scale(-1, 1); }
    ctx.drawImage(this.video, 0, 0, c.width, c.height);
    ctx.restore();
    ctx.drawImage(this.threeCanvas, 0, 0, c.width, c.height);
    var link = document.createElement('a');
    link.download = 'korra-tryon-' + Date.now() + '.png';
    link.href = c.toDataURL('image/png');
    link.click();
  };

  ARTryOn.prototype._disposeGallery = function() {
    this._savedGalleryRenderers = [];
    var gr = window._galleryRenderers;
    if (gr && Array.isArray(gr)) {
      for (var i = 0; i < gr.length; i++) {
        var r = gr[i];
        if (r && r.renderer && r.renderer.dispose) {
          this._savedGalleryRenderers.push(r);
          r.renderer.dispose();
        }
      }
    }
  };

  ARTryOn.prototype._restoreGallery = function() {
    for (var i = 0; i < this._savedGalleryRenderers.length; i++) {
      var r = this._savedGalleryRenderers[i];
      if (r && r.renderer) {
        try { r.renderer.forceContextRestore(); } catch(e) {}
      }
    }
    this._savedGalleryRenderers = [];
  };

  window.arTryOn = new ARTryOn();
})();
