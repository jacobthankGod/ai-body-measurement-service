/**
 * Body Visualizer — Three.js interactive SMPL body shape viewer
 * Renders SMPL body with per-body-part vertex displacement.
 * SMPL betas run ONCE at init for base shape; sliders displace vertices directly.
 */
class BodyVisualizer {
  // Vertex indices per body part (from customBodyPoints.txt)
  static VERTEX_GROUPS = {
    chest: [749,752,1238,1434,1834,1836,2853,2854,2856,2857,2858,2860,2861,2862,2863,2864,2865,2869,2952,2953,2954,2955,2956,2957,2958,2960,3015,3075,3483,3498,4237,4238,4718,4908,4910,5295,6315,6316,6317,6318,6319,6320,6321,6322,6323,6324,6325,6327,6411,6412,6413,6414,6415,6416,6503,6879],
    waist: [1783,1785,1790,1792,1793,1795,2909,2912,3097,3100,3123,3150,3151,3152,3153,3154,3155,3156,3157,3160,5248,5253,5254,5257,5259,6368,6369,6521,6524,6543,6566,6567,6568,6569,6570,6571,6572,6573],
    belly: [1188,1189,1249,1250,1323,1324,1333,1334,1481,1482,1491,1492,2823,2832,2834,2835,2837,3024,3476,3509,4674,4675,4733,4734,4803,4804,4810,4811,4953,4954,4963,4964,6284,6293,6296,6297,6299,6874],
    hips: [862,865,912,1206,1446,1447,1454,1512,1513,3084,3116,3117,3118,3119,3128,3136,3137,3138,3510,4348,4349,4398,4400,4418,4691,4919,4920,4927,4984,4985,6509,6539,6540,6541,6557,6558,6559],
    shoulder_width: [643,680,683,743,781,782,811,1271,1288,1301,1302,1306,1809,1810,1818,1821,1822,1849,1869,1888,1891,2972,2973,4168,4169,4231,4232,4269,4271,4272,4783,4786,5272,5282,5285,5310,5327,5328,5342,5350,6432],
    thigh: [898,899,901,903,904,905,906,907,909,910,934,935,957,962,964,1365,1453],
    bicep: [635,636,1311,1399,1400,1406,1407,1860,1861,3010],
    neck: [151,207,208,210,211,214,217,256,297,424,451,3057,3164,3664,3665,3720,3721,3722,3725,3726,3727,3769,3809,3919,3942],
    wrist: [5563,5564,5565,5566,5567,5568,5570,5572,5573,5608,5609,5668,5669,5691,5696,5702],
    elbow: [1310,1613,1614,1639,1640,1653,1654,1679],
    ankle: [6575,6576,6581,6582,6585,6586,6590,6593,6594,6595,6597,6605,6720,6722,6723],
    height: [250,809,1011,3453],
  };

  // Maps each slider measurement to the vertex groups it controls
  static MEAS_TO_GROUPS = {
    chest:    ['chest'],
    waist:    ['waist', 'belly'],
    hip:      ['hips'],
    shoulder: ['shoulder_width'],
    thigh:    ['thigh'],
    bicep:    ['bicep'],
    neck:     ['neck'],
  };

  constructor() {
    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.mesh = null;
    this.smpl = null;
    this.controls = null;
    this.gender = 'male';
    this.animId = null;
    this.isRotating = true;
    this.mouseDown = false;
    this.lastMouse = { x: 0, y: 0 };
    this.spherical = { theta: 0.3, phi: 1.2, radius: 2.5 };
    this.target = new THREE.Vector3(0, 0.9, 0);
    this.baseVertices = null;
    this.groupCenters = {};
    this.groupRadii = {};
  }

  async init(canvasId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) { console.error('Canvas not found:', canvasId); return; }

    this.smpl = new SMPLShapeEngine();
    await Promise.all([
      this.smpl.init(),
      this.loadFaceIndices(),
    ]);

    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x0B0B0C);

    this.camera = new THREE.PerspectiveCamera(35, 1, 0.1, 100);
    this._updateCamera();

    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this._resize();
    window.addEventListener('resize', () => this._resize());

    const hemi = new THREE.HemisphereLight(0xffffff, 0x444444, 0.8);
    this.scene.add(hemi);
    const dir1 = new THREE.DirectionalLight(0xffffff, 0.7);
    dir1.position.set(2, 4, 3);
    this.scene.add(dir1);
    const dir2 = new THREE.DirectionalLight(0xffffff, 0.3);
    dir2.position.set(-2, 2, -1);
    this.scene.add(dir2);

    const grid = new THREE.GridHelper(4, 20, 0x333333, 0x222222);
    grid.position.y = 0;
    this.scene.add(grid);

    // Compute base body from SMPL betas (default male average)
    const defaultMeas = { chest: 95, waist: 80, hip: 95, shoulder: 45, thigh: 55, bicep: 30, height: 175, neck: 38 };
    const betas = this.smpl.measurementsToBetas(defaultMeas, this.gender);
    const vertices = this.smpl.computeBodyShape(betas);

    // Store base vertices — the reference shape
    this.baseVertices = new Float32Array(vertices);

    // Precompute group centers and average radii from base vertices
    this._computeGroupGeometry();

    const geometry = this._buildGeometry(this.baseVertices);

    const material = new THREE.MeshStandardMaterial({
      color: 0xD4A574,
      roughness: 0.6,
      metalness: 0.05,
      flatShading: false,
    });

    this.mesh = new THREE.Mesh(geometry, material);
    this._groundMesh();
    this.scene.add(this.mesh);

    this._initControls(canvas);
    this._animate();

    const loading = document.getElementById('visLoading');
    if (loading) loading.style.display = 'none';
  }

  _computeGroupGeometry() {
    for (const [name, indices] of Object.entries(BodyVisualizer.VERTEX_GROUPS)) {
      let cx = 0, cy = 0, cz = 0;
      const validIndices = indices.filter(i => i * 3 + 2 < this.baseVertices.length);
      for (const idx of validIndices) {
        cx += this.baseVertices[idx * 3];
        cy += this.baseVertices[idx * 3 + 1];
        cz += this.baseVertices[idx * 3 + 2];
      }
      const n = validIndices.length || 1;
      const center = { x: cx / n, y: cy / n, z: cz / n };
      this.groupCenters[name] = center;

      let totalRadius = 0;
      for (const idx of validIndices) {
        const dx = this.baseVertices[idx * 3] - center.x;
        const dz = this.baseVertices[idx * 3 + 2] - center.z;
        totalRadius += Math.sqrt(dx * dx + dz * dz);
      }
      this.groupRadii[name] = totalRadius / n;
    }
  }

  _buildGeometry(vertexData) {
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(vertexData);
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    if (BodyVisualizer._faceIndices) {
      geometry.setIndex(new THREE.BufferAttribute(BodyVisualizer._faceIndices, 1));
    } else {
      const nv = positions.length / 3;
      const idx = new Uint32Array(nv);
      for (let i = 0; i < nv; i++) idx[i] = i;
      geometry.setIndex(new THREE.BufferAttribute(idx, 1));
    }

    geometry.computeVertexNormals();
    return geometry;
  }

  _groundMesh() {
    if (!this.mesh) return;
    this.mesh.geometry.computeBoundingBox();
    const bbox = this.mesh.geometry.boundingBox;
    this.mesh.position.set(0, -bbox.min.y, 0);
  }

  _updateCamera() {
    if (!this.camera) return;
    const { theta, phi, radius } = this.spherical;
    this.camera.position.set(
      this.target.x + radius * Math.sin(phi) * Math.sin(theta),
      this.target.y + radius * Math.cos(phi),
      this.target.z + radius * Math.sin(phi) * Math.cos(theta)
    );
    this.camera.lookAt(this.target);
  }

  _initControls(canvas) {
    canvas.addEventListener('mousedown', (e) => {
      this.mouseDown = true;
      this.lastMouse = { x: e.clientX, y: e.clientY };
      this.isRotating = false;
    });
    window.addEventListener('mouseup', () => { this.mouseDown = false; });
    window.addEventListener('mousemove', (e) => {
      if (!this.mouseDown) return;
      const dx = e.clientX - this.lastMouse.x;
      const dy = e.clientY - this.lastMouse.y;
      this.spherical.theta -= dx * 0.005;
      this.spherical.phi = Math.max(0.3, Math.min(Math.PI - 0.3, this.spherical.phi - dy * 0.005));
      this.lastMouse = { x: e.clientX, y: e.clientY };
      this._updateCamera();
    });

    canvas.addEventListener('wheel', (e) => {
      e.preventDefault();
      this.spherical.radius = Math.max(1.2, Math.min(6, this.spherical.radius + e.deltaY * 0.002));
      this._updateCamera();
    }, { passive: false });

    let touchStart = null;
    let pinchDist = null;
    canvas.addEventListener('touchstart', (e) => {
      if (e.touches.length === 1) {
        touchStart = { x: e.touches[0].clientX, y: e.touches[0].clientY };
        this.isRotating = false;
      } else if (e.touches.length === 2) {
        pinchDist = Math.hypot(
          e.touches[0].clientX - e.touches[1].clientX,
          e.touches[0].clientY - e.touches[1].clientY
        );
      }
    });
    canvas.addEventListener('touchmove', (e) => {
      e.preventDefault();
      if (e.touches.length === 1 && touchStart) {
        const dx = e.touches[0].clientX - touchStart.x;
        const dy = e.touches[0].clientY - touchStart.y;
        this.spherical.theta -= dx * 0.005;
        this.spherical.phi = Math.max(0.3, Math.min(Math.PI - 0.3, this.spherical.phi - dy * 0.005));
        touchStart = { x: e.touches[0].clientX, y: e.touches[0].clientY };
        this._updateCamera();
      } else if (e.touches.length === 2 && pinchDist !== null) {
        const newDist = Math.hypot(
          e.touches[0].clientX - e.touches[1].clientX,
          e.touches[0].clientY - e.touches[1].clientY
        );
        this.spherical.radius = Math.max(1.2, Math.min(6, this.spherical.radius * (pinchDist / newDist)));
        pinchDist = newDist;
        this._updateCamera();
      }
    }, { passive: false });
  }

  _resize() {
    if (!this.renderer || !this.camera) return;
    const canvas = this.renderer.domElement;
    const parent = canvas.parentElement;
    if (!parent) return;
    const w = parent.clientWidth;
    const h = parent.clientHeight;
    canvas.width = w * Math.min(window.devicePixelRatio, 2);
    canvas.height = h * Math.min(window.devicePixelRatio, 2);
    canvas.style.width = w + 'px';
    canvas.style.height = h + 'px';
    this.renderer.setSize(w, h);
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
  }

  _animate() {
    this.animId = requestAnimationFrame(() => this._animate());
    if (this.isRotating) {
      this.spherical.theta += 0.003;
      this._updateCamera();
    }
    this.renderer.render(this.scene, this.camera);
  }

  /**
   * Update body shape from measurement values.
   * Each slider displaces ONLY its own vertex group radially.
   * SMPL betas do NOT re-run — base shape is fixed.
   * @param {Object} measurements - { chest, waist, hip, shoulder, thigh, bicep, neck, height }
   * @param {Object} baseDefaults - the default measurement values used at init
   */
  updateFromMeasurements(measurements, baseDefaults) {
    if (!this.baseVertices || !this.mesh) return;
    if (!baseDefaults) baseDefaults = { chest: 95, waist: 80, hip: 95, shoulder: 45, thigh: 55, bicep: 30, neck: 38 };

    const pos = this.mesh.geometry.attributes.position;

    // Copy base vertices as starting point
    for (let i = 0; i < this.baseVertices.length; i++) {
      pos.array[i] = this.baseVertices[i];
    }

    // Apply per-body-part radial displacement
    for (const [measKey, groupNames] of Object.entries(BodyVisualizer.MEAS_TO_GROUPS)) {
      const targetVal = measurements[measKey];
      const baseVal = baseDefaults[measKey];
      if (targetVal === undefined || baseVal === undefined) continue;

      const scale = targetVal / baseVal;
      if (Math.abs(scale - 1.0) < 0.001) continue;

      for (const groupName of groupNames) {
        const indices = BodyVisualizer.VERTEX_GROUPS[groupName];
        const center = this.groupCenters[groupName];
        if (!indices || !center) continue;

        for (const idx of indices) {
          const vi = idx * 3;
          if (vi + 2 >= pos.array.length) continue;

          // Radial displacement from group center (XZ plane)
          const dx = pos.array[vi] - center.x;
          const dz = pos.array[vi + 2] - center.z;
          pos.array[vi]     = center.x + dx * scale;
          pos.array[vi + 2] = center.z + dz * scale;

          // Also scale Y slightly for shoulder/neck (vertical expansion)
          if (groupName === 'shoulder_width' || groupName === 'neck') {
            const dy = pos.array[vi + 1] - center.y;
            pos.array[vi + 1] = center.y + dy * scale;
          }
        }
      }
    }

    // Height: Y-scale only (independent of all other measurements)
    const targetHeightCm = measurements.height || 175;
    const baseHeightCm = baseDefaults.height || 175;
    const heightScale = targetHeightCm / baseHeightCm;
    if (Math.abs(heightScale - 1.0) > 0.001) {
      for (let i = 1; i < pos.array.length; i += 3) {
        pos.array[i] *= heightScale;
      }
    }

    pos.needsUpdate = true;
    this.mesh.geometry.computeVertexNormals();
    this._groundMesh();
  }

  setGender(gender) {
    this.gender = gender;
    this._recomputeBase();
  }

  _recomputeBase() {
    if (!this.smpl || !this.smpl.ready) return;
    const defaultMeas = this.gender === 'female'
      ? { chest: 89, waist: 72, hip: 97, shoulder: 39, thigh: 54, bicep: 27, height: 163, neck: 34 }
      : { chest: 95, waist: 80, hip: 95, shoulder: 45, thigh: 55, bicep: 30, height: 175, neck: 38 };
    const betas = this.smpl.measurementsToBetas(defaultMeas, this.gender);
    const vertices = this.smpl.computeBodyShape(betas);
    this.baseVertices = new Float32Array(vertices);
    this._computeGroupGeometry();
    if (this.mesh) {
      const pos = this.mesh.geometry.attributes.position;
      for (let i = 0; i < this.baseVertices.length; i++) {
        pos.array[i] = this.baseVertices[i];
      }
      pos.needsUpdate = true;
      this.mesh.geometry.computeVertexNormals();
      this._groundMesh();
    }
  }

  async loadFaceIndices() {
    try {
      const resp = await fetch('/models/smpl_faces.npy');
      if (!resp.ok) return;
      const buf = await resp.arrayBuffer();
      const view = new DataView(buf);
      const major = view.getUint8(6);
      let headerLen, headerStart;
      if (major === 1) { headerLen = view.getUint16(8, true); headerStart = 10; }
      else { headerLen = view.getUint32(8, true); headerStart = 12; }
      const dataStart = headerStart + headerLen;
      const total = 13776 * 3;
      const indices = new Uint32Array(total);
      for (let i = 0; i < total; i++) {
        indices[i] = view.getUint32(dataStart + i * 4, true);
      }
      BodyVisualizer._faceIndices = indices;
      if (this.mesh) {
        this.mesh.geometry.setIndex(new THREE.BufferAttribute(indices, 1));
        this.mesh.geometry.computeVertexNormals();
      }
    } catch (e) {
      console.warn('Could not load face indices:', e);
    }
  }

  dispose() {
    if (this.animId) cancelAnimationFrame(this.animId);
    if (this.renderer) this.renderer.dispose();
  }
}

window.BodyVisualizer = BodyVisualizer;
