/**
 * AR Try-On Module (v4 — Dashboard-proven MediaPipe)
 *
 * Uses EXACTLY the same MediaPipe implementation as dashboard.html
 * which is confirmed working:
 *   - @mediapipe/pose@0.5.1675469404 (legacy API, NOT Vision Tasks)
 *   - @mediapipe/camera_utils@0.3.1675466862/camera_utils.js
 *   - modelComplexity: 2, smoothLandmarks: true
 *   - Camera utility handles frame loop
 *   - onResults callback for landmark processing
 *   - Canvas sized to clientWidth/clientHeight (not video dimensions)
 *   - Visibility > 0.5 gate for drawing
 *   - No extra smoothing layers (MediaPipe handles it internally)
 */
(function() {
  'use strict';

  var CFG = {
    POSE_CONFIDENCE: 0.6,
    CLOTH_ITERATIONS: 4,
    CLOTH_GRAVITY: -0.003,
    CLOTH_DAMPING: 0.97,
    CLOTH_STIFFNESS: 0.35,
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
    // Same skeleton connections as dashboard.html
    SKELETON_EDGES: [
      [0,1],[1,2],[2,3],[3,7],[0,4],[4,5],[5,6],[6,8],[9,10],[0,9],[0,10],
      [11,12],[11,23],[12,24],[23,24],
      [11,13],[13,15],[12,14],[14,16],
      [15,17],[15,19],[15,21],[17,19],[16,18],[16,20],[16,22],[18,20],
      [23,25],[25,27],[27,29],[29,31],[27,31],[24,26],[26,28],[28,30],[30,32],[28,32]
    ],
  };

  // ======================== MATH ========================
  function v3dist(a, b) {
    var dx=a[0]-b[0], dy=a[1]-b[1], dz=(a[2]||0)-(b[2]||0);
    return Math.sqrt(dx*dx+dy*dy+dz*dz);
  }
  function v3lerp(a, b, t) {
    return [a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t, (a[2]||0)+((b[2]||0)-(a[2]||0))*t];
  }
  function lm3(lm, idx) {
    var l = lm[idx];
    return l ? [l.x, l.y, l.z || 0] : null;
  }

  // ======================== BODY ESTIMATOR ========================
  function BodyEstimator() {
    this.shoulderWidth = 0.4;
    this.hipWidth = 0.3;
    this.torsoLength = 0.5;
    this.bodyCenter = [0.5, 0.5, 0];
    this.bodyScale = 1.0;
    this.joints = {};
    this._prevCenter = null;
    this._valid = false;
  }

  BodyEstimator.prototype.update = function(landmarks) {
    if (!landmarks) { this._valid = false; return; }
    var L = CFG.LM;
    var ls = lm3(landmarks, L.LEFT_SHOULDER);
    var rs = lm3(landmarks, L.RIGHT_SHOULDER);
    var lh = lm3(landmarks, L.LEFT_HIP);
    var rh = lm3(landmarks, L.RIGHT_HIP);

    if (!ls || !rs || !lh || !rh) { this._valid = false; return; }
    this._valid = true;

    var le = lm3(landmarks, L.LEFT_ELBOW);
    var re = lm3(landmarks, L.RIGHT_ELBOW);
    var lw = lm3(landmarks, L.LEFT_WRIST);
    var rw = lm3(landmarks, L.RIGHT_WRIST);
    var lk = lm3(landmarks, L.LEFT_KNEE);
    var rk = lm3(landmarks, L.RIGHT_KNEE);
    var la = lm3(landmarks, L.LEFT_ANKLE);
    var ra = lm3(landmarks, L.RIGHT_ANKLE);
    var nose = lm3(landmarks, L.NOSE);

    this.joints = {
      neck: v3lerp(ls, rs, 0.5),
      leftShoulder: ls, rightShoulder: rs,
      leftElbow: le, rightElbow: re,
      leftWrist: lw, rightWrist: rw,
      leftHip: lh, rightHip: rh,
      hipCenter: v3lerp(lh, rh, 0.5),
      leftKnee: lk, rightKnee: rk,
      leftAnkle: la, rightAnkle: ra,
      nose: nose,
    };

    this.shoulderWidth = v3dist(ls, rs);
    this.hipWidth = v3dist(lh, rh);
    this.torsoLength = v3dist(ls, lh);

    var center = v3lerp(v3lerp(ls, rs, 0.5), v3lerp(lh, rh, 0.5), 0.5);
    if (this._prevCenter) center = v3lerp(center, this._prevCenter, 0.4);
    this.bodyCenter = center;
    this._prevCenter = center.slice();
    this.bodyScale = Math.max(0.3, Math.min(this.shoulderWidth / 0.35, 2.5));
  };

  // ======================== GARMENT BINDER ========================
  var BIND_JOINTS = [
    'neck', 'leftShoulder', 'rightShoulder',
    'leftElbow', 'rightElbow',
    'leftWrist', 'rightWrist',
    'hipCenter', 'leftHip', 'rightHip',
    'leftKnee', 'rightKnee',
  ];

  function GarmentBinder() {
    this.weights = null;
    this.jointIdx = null;
    this.restPositions = null;
    this.nVerts = 0;
    this.built = false;
  }

  GarmentBinder.prototype.build = function(geometry, bodyJoints) {
    var pos = geometry.attributes.position;
    this.nVerts = pos.count;
    var INF = 4;
    this.weights = new Float32Array(this.nVerts * INF);
    this.jointIdx = new Int32Array(this.nVerts * INF);
    this.restPositions = new Float32Array(this.nVerts * 3);

    var jp = [];
    for (var j = 0; j < BIND_JOINTS.length; j++) {
      var p = bodyJoints[BIND_JOINTS[j]];
      jp.push(p || [0,0,0]);
    }

    for (var i = 0; i < this.nVerts; i++) {
      var gx = pos.getX(i), gy = pos.getY(i), gz = pos.getZ(i);
      this.restPositions[i*3] = gx;
      this.restPositions[i*3+1] = gy;
      this.restPositions[i*3+2] = gz;

      var dists = [];
      for (var j = 0; j < jp.length; j++) {
        var dx = gx - jp[j][0], dy = gy - jp[j][1], dz = gz - jp[j][2];
        dists.push({ idx: j, d: Math.sqrt(dx*dx+dy*dy+dz*dz) });
      }
      dists.sort(function(a,b) { return a.d - b.d; });

      var top = dists.slice(0, INF);
      var total = 0;
      for (var k = 0; k < top.length; k++) { top[k].w = 1/(top[k].d + 0.001); total += top[k].w; }
      for (var k = 0; k < INF; k++) {
        var wi = i * INF + k;
        if (k < top.length) {
          this.weights[wi] = top[k].w / total;
          this.jointIdx[wi] = top[k].idx;
        } else {
          this.weights[wi] = 0;
          this.jointIdx[wi] = 0;
        }
      }
    }
    this.built = true;
  };

  GarmentBinder.prototype.apply = function(geometry, bodyJoints) {
    if (!this.built) return;
    var pos = geometry.attributes.position;
    var INF = 4;
    for (var i = 0; i < this.nVerts; i++) {
      var bx = this.restPositions[i*3];
      var by = this.restPositions[i*3+1];
      var bz = this.restPositions[i*3+2];
      var dx = 0, dy = 0, dz = 0;
      for (var k = 0; k < INF; k++) {
        var wi = i * INF + k;
        var w = this.weights[wi];
        if (w < 0.001) continue;
        var jp = bodyJoints[BIND_JOINTS[this.jointIdx[wi]]];
        if (!jp) continue;
        dx += w * jp[0] * 0.08;
        dy += w * jp[1] * 0.08;
        dz += w * (jp[2] || 0) * 0.08;
      }
      pos.setXYZ(i, bx + dx, by + dy, bz + dz);
    }
    pos.needsUpdate = true;
  };

  // ======================== CLOTH SIMULATOR ========================
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
    var idx = this.geometry.index;
    var seen = {};
    if (idx) {
      for (var i = 0; i < idx.count; i += 3) {
        var a = idx.getX(i), b = idx.getX(i+1), c = idx.getX(i+2);
        _edge(seen, this.constraints, a, b, this.pos);
        _edge(seen, this.constraints, b, c, this.pos);
        _edge(seen, this.constraints, c, a, this.pos);
      }
    }
    if (this.constraints.length > 8000) {
      var step = Math.ceil(this.constraints.length / 8000);
      var sub = [];
      for (var i = 0; i < this.constraints.length; i += step) sub.push(this.constraints[i]);
      this.constraints = sub;
    }
  };

  function _edge(seen, arr, a, b, pos) {
    var key = Math.min(a,b)+'_'+Math.max(a,b);
    if (seen[key]) return; seen[key] = 1;
    var dx=pos[a*3]-pos[b*3], dy=pos[a*3+1]-pos[b*3+1], dz=pos[a*3+2]-pos[b*3+2];
    arr.push({ a:a, b:b, rest: Math.sqrt(dx*dx+dy*dy+dz*dz) });
  }

  ClothSimulator.prototype.step = function() {
    var P = this.pos, V = this.prev, D = CFG.CLOTH_DAMPING, G = CFG.CLOTH_GRAVITY;
    for (var i = 0; i < this.n; i++) {
      var ix=i*3, iy=i*3+1, iz=i*3+2;
      var vx = (P[ix]-V[ix])*D, vy = (P[iy]-V[iy])*D, vz = (P[iz]-V[iz])*D;
      V[ix]=P[ix]; V[iy]=P[iy]; V[iz]=P[iz];
      P[ix]+=vx; P[iy]+=vy+G; P[iz]+=vz;
    }
    var S = CFG.CLOTH_STIFFNESS;
    for (var iter = 0; iter < CFG.CLOTH_ITERATIONS; iter++) {
      for (var c = 0; c < this.constraints.length; c++) {
        var con = this.constraints[c];
        var ax=con.a*3, bx=con.b*3;
        var dx=P[bx]-P[ax], dy=P[bx+1]-P[ax+1], dz=P[bx+2]-P[ax+2];
        var dist = Math.sqrt(dx*dx+dy*dy+dz*dz);
        if (dist < 1e-6) continue;
        var diff = (dist-con.rest)/dist*S*0.5;
        var ox=dx*diff, oy=dy*diff, oz=dz*diff;
        P[ax]+=ox; P[ax+1]+=oy; P[ax+2]+=oz;
        P[bx]-=ox; P[bx+1]-=oy; P[bx+2]-=oz;
      }
    }
    var pa = this.geometry.attributes.position;
    for (var i = 0; i < this.n; i++) {
      pa.setXYZ(i, P[i*3], P[i*3+1], P[i*3+2]);
    }
    pa.needsUpdate = true;
    this.geometry.computeVertexNormals();
  };

  // ======================== MAIN AR TRY-ON ========================
  function ARTryOn() {
    this.overlay = document.getElementById('arTryOnOverlay');
    this.video = document.getElementById('arVideo');
    this.skelCanvas = document.getElementById('arSkeletonCanvas');
    this.threeCanvas = document.getElementById('arThreeCanvas');
    this.closeBtn = document.getElementById('arCloseBtn');
    this.switchBtn = document.getElementById('arSwitchBtn');
    this.captureBtn = document.getElementById('arCaptureBtn');
    this.garmentLabel = document.getElementById('arGarmentLabel');
    this.loadingEl = document.getElementById('arLoading');
    this.statusEl = document.getElementById('arStatus');
    this.errorEl = document.getElementById('arErrorMsg');

    this.stream = null;
    this.facingMode = 'user';
    this.isActive = false;

    // MediaPipe — same as dashboard.html
    this.poseModel = null;
    this.cameraInstance = null;
    this.lastLandmarks = null;

    this.body = new BodyEstimator();
    this.binder = new GarmentBinder();
    this.cloth = null;

    // Three.js
    this.renderer = null;
    this.scene = null;
    this.camera3 = null;
    this.garmentMesh = null;
    this.clock = null;
    this.animFrame = null;

    this._bind();
  }

  ARTryOn.prototype._bind = function() {
    var self = this;
    this.closeBtn.addEventListener('click', function() { self.close(); });
    this.switchBtn.addEventListener('click', function() { self.switchCamera(); });
    this.captureBtn.addEventListener('click', function() { self.capture(); });
    document.querySelectorAll('.gallery-try-btn').forEach(function(btn) {
      btn.addEventListener('click', function() {
        var url = btn.dataset.garb || btn.dataset.glb;
        if (!url) return;
        self.open(url, btn.dataset.name || 'Garment');
      });
    });
  };

  // ---- OPEN / CLOSE ----
  ARTryOn.prototype.open = async function(glbUrl, name) {
    if (this.isActive) return;
    this.isActive = true;
    this.overlay.classList.add('active');
    this.overlay.style.display = 'flex';
    this.overlay.style.opacity = '1';
    this.loadingEl.style.display = 'flex';
    this.errorEl.classList.remove('show');
    this.garmentLabel.textContent = name;

    this.statusEl.textContent = 'Starting camera...';
    if (!await this._startCamera()) { this.close(); return; }

    this._initScene();

    this.statusEl.textContent = 'Loading body detection...';
    this._initPose();

    this.statusEl.textContent = 'Loading garment...';
    var mesh = await this._loadGarment(glbUrl);
    if (mesh) {
      this.garmentMesh = mesh;
      this.scene.add(this.garmentMesh);
      var geo = this._getGeo();
      if (geo) this.cloth = new ClothSimulator(geo);
    }

    this.loadingEl.style.display = 'none';
    this.clock.start();
    this._animate();
  };

  ARTryOn.prototype.close = function() {
    this.isActive = false;
    cancelAnimationFrame(this.animFrame);

    // Stop MediaPipe camera (same as dashboard closeCamera)
    if (this.cameraInstance) { this.cameraInstance.stop(); this.cameraInstance = null; }

    this._stopCamera();
    this.body = new BodyEstimator();
    this.binder = new GarmentBinder();
    this.cloth = null;
    this.lastLandmarks = null;
    if (this.garmentMesh && this.scene) { this.scene.remove(this.garmentMesh); this.garmentMesh = null; }
    this.overlay.classList.remove('active');
    this.overlay.style.opacity = '0';
    var self = this;
    setTimeout(function() { self.overlay.style.display = 'none'; }, 300);
  };

  // ---- CAMERA (same as dashboard.html) ----
  ARTryOn.prototype._startCamera = async function() {
    try {
      // Match dashboard: 1280x720
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: this.facingMode, width: { ideal: 1280 }, height: { ideal: 720 } }
      });
      this.video.srcObject = this.stream;
      await this.video.play();

      // Size skeleton canvas to displayed size (like dashboard: canvas.width = canvas.clientWidth)
      this._resizeCanvases();

      return true;
    } catch(e) {
      this._showError('Camera Access Needed', 'Please allow camera access.');
      return false;
    }
  };

  ARTryOn.prototype._resizeCanvases = function() {
    // Match dashboard pattern: canvas.width = canvas.clientWidth
    var sw = this.skelCanvas.clientWidth || window.innerWidth;
    var sh = this.skelCanvas.clientHeight || window.innerHeight;
    this.skelCanvas.width = sw;
    this.skelCanvas.height = sh;
    var tw = this.threeCanvas.clientWidth || window.innerWidth;
    var th = this.threeCanvas.clientHeight || window.innerHeight;
    this.threeCanvas.width = tw;
    this.threeCanvas.height = th;
  };

  ARTryOn.prototype._stopCamera = function() {
    if (this.stream) { this.stream.getTracks().forEach(function(t){t.stop();}); this.stream = null; }
    this.video.srcObject = null;
  };

  ARTryOn.prototype.switchCamera = function() {
    this.facingMode = this.facingMode === 'user' ? 'environment' : 'user';
    this._stopCamera();
    this._startCamera();
  };

  // ---- MEDIAPIPE (EXACT dashboard.html pattern) ----
  ARTryOn.prototype._initPose = function() {
    var self = this;
    // Same as dashboard: new Pose({ locateFile: ... })
    this.poseModel = new Pose({
      locateFile: function(file) {
        return 'https://cdn.jsdelivr.net/npm/@mediapipe/pose@0.5.1675469404/' + file;
      }
    });
    // Same options as dashboard: modelComplexity 2, smoothLandmarks true, confidence 0.6
    this.poseModel.setOptions({
      modelComplexity: 2,
      smoothLandmarks: true,
      minDetectionConfidence: CFG.POSE_CONFIDENCE,
      minTrackingConfidence: CFG.POSE_CONFIDENCE,
    });
    // Same callback pattern as dashboard
    this.poseModel.onResults(function(results) { self._onPoseResults(results); });

    // Same as dashboard: new Camera(video, { onFrame: ..., width: 1280, height: 720 })
    this.cameraInstance = new Camera(this.video, {
      onFrame: async function() {
        if (self.poseModel && self.isActive) {
          await self.poseModel.send({ image: self.video });
        }
      },
      width: 1280,
      height: 720,
    });
    this.cameraInstance.start();
  };

  // ---- POSE RESULTS (same pattern as dashboard onPoseResults) ----
  ARTryOn.prototype._onPoseResults = function(results) {
    if (!this.isActive) return;

    var canvas = this.skelCanvas;
    var ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Match dashboard: resize canvas to displayed size each frame
    var cw = canvas.clientWidth || window.innerWidth;
    var ch = canvas.clientHeight || window.innerHeight;
    if (canvas.width !== cw || canvas.height !== ch) {
      canvas.width = cw;
      canvas.height = ch;
    }

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!results.poseLandmarks) return;

    var l = results.poseLandmarks;
    this.lastLandmarks = l;

    // Update body estimator
    this.body.update(l);

    // Draw skeleton — EXACT same pattern as dashboard.html
    var clr = "#76FF03";
    ctx.strokeStyle = clr; ctx.lineWidth = 5; ctx.lineCap = "round";
    CFG.SKELETON_EDGES.forEach(function(pair) {
      var p1 = l[pair[0]], p2 = l[pair[1]];
      if (p1.visibility > 0.5 && p2.visibility > 0.5) {
        ctx.beginPath();
        ctx.moveTo(p1.x * canvas.width, p1.y * canvas.height);
        ctx.lineTo(p2.x * canvas.width, p2.y * canvas.height);
        ctx.stroke();
      }
    });
    // Joint nodes — same as dashboard
    ctx.fillStyle = clr;
    for (var i = 0; i < l.length; i++) {
      var p = l[i];
      if (p.visibility > 0.5) {
        ctx.beginPath();
        ctx.arc(p.x * canvas.width, p.y * canvas.height, 5, 0, 2 * Math.PI);
        ctx.fill();
        ctx.strokeStyle = '#000'; ctx.lineWidth = 1.5; ctx.stroke();
      }
    }
  };

  // ---- THREE.JS SCENE ----
  ARTryOn.prototype._initScene = function() {
    if (this.renderer) return;
    this.clock = new THREE.Clock();
    var vw = this.video.videoWidth || 1280;
    var vh = this.video.videoHeight || 720;
    this.renderer = new THREE.WebGLRenderer({ canvas: this.threeCanvas, alpha: true, antialias: false });
    this.renderer.setPixelRatio(1);
    this.renderer.setSize(vw, vh);

    this.scene = new THREE.Scene();
    this.camera3 = new THREE.PerspectiveCamera(50, vw/vh, 0.01, 100);
    this.camera3.position.set(0, 0, 2);

    this.scene.add(new THREE.AmbientLight(0xffffff, 0.7));
    this.scene.add(new THREE.HemisphereLight(0xffffff, 0x444444, 0.5));
    var d = new THREE.DirectionalLight(0xffffff, 0.8);
    d.position.set(1, 2, 3);
    this.scene.add(d);
  };

  ARTryOn.prototype._loadGarment = function(url) {
    var self = this;
    return new Promise(function(resolve, reject) {
      var loader = new THREE.GLTFLoader();
      if (window.DRACOLoader) {
        var dr = new THREE.DRACOLoader();
        dr.setDecoderPath('/assets/draco/');
        loader.setDRACOLoader(dr);
      }
      loader.load(url, function(gltf) {
        var mesh = gltf.scene;
        mesh.traverse(function(c) {
          if (c.isMesh) {
            c.material.transparent = false;
            c.material.opacity = 1;
            c.material.side = THREE.DoubleSide;
            c.material.depthWrite = true;
            c.material.needsUpdate = true;
          }
        });
        resolve(mesh);
      }, undefined, function(err) {
        console.error('[AR] Garment load failed:', err);
        resolve(null);
      });
    });
  };

  ARTryOn.prototype._getGeo = function() {
    if (!this.garmentMesh) return null;
    var g = null;
    this.garmentMesh.traverse(function(c) { if (c.isMesh && !g) g = c.geometry; });
    return g;
  };

  // ---- ANIMATION LOOP ----
  ARTryOn.prototype._animate = function() {
    if (!this.isActive) return;
    var self = this;
    this.animFrame = requestAnimationFrame(function() { self._animate(); });

    var l = this.lastLandmarks;
    if (!l || !this.body._valid) {
      this.renderer.render(this.scene, this.camera3);
      return;
    }

    // Position garment
    if (this.garmentMesh) this._placeGarment(l);

    // Build LBS binding (once)
    if (this.garmentMesh && !this.binder.built) {
      var geo = this._getGeo();
      if (geo) {
        var wj = this._bodyJointsToWorld(this.body.joints);
        this.binder.build(geo, wj);
      }
    }

    // Apply LBS
    if (this.binder.built && this.garmentMesh) {
      var geo = this._getGeo();
      if (geo) {
        var wj = this._bodyJointsToWorld(this.body.joints);
        this.binder.apply(geo, wj);
      }
    }

    // Cloth sim
    if (this.cloth) this.cloth.step();

    this.renderer.render(this.scene, this.camera3);
  };

  ARTryOn.prototype._placeGarment = function(lm) {
    if (!this.garmentMesh || !lm) return;
    var L = CFG.LM;
    var ls = lm[L.LEFT_SHOULDER], rs = lm[L.RIGHT_SHOULDER];
    var lh = lm[L.LEFT_HIP], rh = lm[L.RIGHT_HIP];
    if (!ls || !rs || !lh || !rh) return;

    var cx = (ls.x+rs.x+lh.x+rh.x)/4;
    var cy = (ls.y+rs.y+lh.y+rh.y)/4;
    var cz = ((ls.z||0)+(rs.z||0)+(lh.z||0)+(rh.z||0))/4;

    // Convert MediaPipe normalized coords to Three.js world space
    var tx = (cx - 0.5) * 2;
    var ty = -(cy - 0.5) * 2;
    var tz = -1.5 - cz * 0.3;

    // Scale from shoulder width
    var vw = this.video.videoWidth || 1280;
    var vh = this.video.videoHeight || 720;
    var sw = Math.sqrt(Math.pow((rs.x-ls.x)*vw, 2) + Math.pow((rs.y-ls.y)*vh, 2));
    var scale = sw / 250;
    scale = Math.max(0.3, Math.min(scale, 1.8));

    var angle = Math.atan2(rs.y-ls.y, rs.x-ls.x);

    this.garmentMesh.position.set(tx, ty, tz);
    this.garmentMesh.scale.setScalar(scale);
    this.garmentMesh.rotation.z = angle;
  };

  ARTryOn.prototype._bodyJointsToWorld = function(joints) {
    var out = {};
    for (var name in joints) {
      var j = joints[name];
      if (!j) continue;
      out[name] = [(j[0]-0.5)*2, -(j[1]-0.5)*2, -1.5-(j[2]||0)*0.3];
    }
    return out;
  };

  // ---- CAPTURE ----
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

  ARTryOn.prototype._showError = function(t, d) {
    document.getElementById('arErrorTitle').textContent = t;
    document.getElementById('arErrorDesc').textContent = d;
    this.errorEl.classList.add('show');
  };

  // ======================== INIT ========================
  window.arTryOn = new ARTryOn();
})();
