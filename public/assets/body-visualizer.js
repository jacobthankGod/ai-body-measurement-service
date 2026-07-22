/**
 * Body Visualizer — Three.js interactive SMPL body shape viewer
 * Renders an A-pose SMPL body with real-time slider updates.
 */
class BodyVisualizer {
  constructor() {
    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.mesh = null;
    this.garmentMesh = null;
    this.garmentVisible = false;
    this.smpl = null;
    this.controls = null;
    this.gender = 'male';
    this.currentBetas = new Float32Array(10);
    this.animId = null;
    this.isRotating = true;
    this.mouseDown = false;
    this.lastMouse = { x: 0, y: 0 };
    this.spherical = { theta: 0.3, phi: 1.2, radius: 2.5 };
    this.target = new THREE.Vector3(0, 0.9, 0);
  }

  async init(canvasId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) { console.error('Canvas not found:', canvasId); return; }

    // Init SMPL engine and load face topology
    this.smpl = new SMPLShapeEngine();
    await Promise.all([
      this.smpl.init(),
      this.loadFaceIndices(),
    ]);

    // Load faces for geometry
    const facesResp = await fetch('/models/smpl_faces.npy');
    // Faces not needed for vertex-only rendering (we use the known topology)
    // SMPL faces are pre-defined: 13776 triangles from 6890 vertices

    // Scene
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x0B0B0C);

    // Camera
    this.camera = new THREE.PerspectiveCamera(35, 1, 0.1, 100);
    this._updateCamera();

    // Renderer
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this._resize();
    window.addEventListener('resize', () => this._resize());

    // Lighting
    const hemi = new THREE.HemisphereLight(0xffffff, 0x444444, 0.8);
    this.scene.add(hemi);
    const dir1 = new THREE.DirectionalLight(0xffffff, 0.7);
    dir1.position.set(2, 4, 3);
    this.scene.add(dir1);
    const dir2 = new THREE.DirectionalLight(0xffffff, 0.3);
    dir2.position.set(-2, 2, -1);
    this.scene.add(dir2);

    // Ground grid
    const grid = new THREE.GridHelper(4, 20, 0x333333, 0x222222);
    grid.position.y = 0;
    this.scene.add(grid);

    // Compute default shape (average male)
    const defaultMeas = { chest: 95, waist: 80, hip: 95, shoulder: 45, thigh: 55, bicep: 30, height: 175 };
    this.currentBetas = this.smpl.measurementsToBetas(defaultMeas, this.gender);
    const vertices = this.smpl.computeBodyShape(this.currentBetas);

    // Build geometry
    const geometry = this._buildGeometry(vertices);

    // Material — skin tone
    const material = new THREE.MeshStandardMaterial({
      color: 0xD4A574,
      roughness: 0.6,
      metalness: 0.05,
      flatShading: false,
    });

    this.mesh = new THREE.Mesh(geometry, material);
    // Center and ground
    this._groundMesh();
    this.scene.add(this.mesh);

    // Load garment mesh (static t-shirt OBJ)
    this._loadGarment('/meshes/garments/ssp3d_subj_1_garment.obj');

    // Mouse controls
    this._initControls(canvas);

    // Start render loop
    this._animate();

    // Hide loading
    const loading = document.getElementById('visLoading');
    if (loading) loading.style.display = 'none';
  }

  _buildGeometry(vertexData) {
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(vertexData);
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    if (BodyVisualizer._faceIndices) {
      geometry.setIndex(new THREE.BufferAttribute(BodyVisualizer._faceIndices, 1));
    } else {
      // Fallback: generate sequential face indices (will look wrong but won't crash)
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
    const center = new THREE.Vector3();
    bbox.getCenter(center);
    // Ground feet at Y=0
    this.mesh.position.set(0, -bbox.min.y, 0);
  }

  async _loadGarment(url) {
    try {
      const resp = await fetch(url);
      if (!resp.ok) return;
      const text = await resp.text();
      const lines = text.split('\n');
      const verts = [], faces = [];
      for (const line of lines) {
        if (line.startsWith('v ')) {
          const parts = line.split(/\s+/);
          verts.push(parseFloat(parts[1]), parseFloat(parts[2]), parseFloat(parts[3]));
        } else if (line.startsWith('f ')) {
          const parts = line.split(/\s+/);
          faces.push(parseInt(parts[1])-1, parseInt(parts[2])-1, parseInt(parts[3])-1);
        }
      }
      if (verts.length === 0 || faces.length === 0) return;
      const geom = new THREE.BufferGeometry();
      geom.setAttribute('position', new THREE.BufferAttribute(new Float32Array(verts), 3));
      geom.setIndex(new THREE.BufferAttribute(new Uint32Array(faces), 1));
      geom.computeVertexNormals();
      const mat = new THREE.MeshStandardMaterial({
        color: 0x4488cc, roughness: 0.7, metalness: 0.0,
        transparent: true, opacity: 0.85, side: THREE.DoubleSide,
      });
      this.garmentMesh = new THREE.Mesh(geom, mat);
      this.garmentMesh.visible = false;
      // Apply same grounding as body
      if (this.mesh) {
        this.garmentMesh.position.copy(this.mesh.position);
      }
      this.scene.add(this.garmentMesh);
    } catch (e) {
      console.warn('Could not load garment:', e);
    }
  }

  updateGarment() {
    if (this.garmentMesh) {
      this.garmentMesh.visible = this.garmentVisible;
    }
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
    // Mouse rotate
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

    // Scroll zoom
    canvas.addEventListener('wheel', (e) => {
      e.preventDefault();
      this.spherical.radius = Math.max(1.2, Math.min(6, this.spherical.radius + e.deltaY * 0.002));
      this._updateCamera();
    }, { passive: false });

    // Touch controls
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

    // Auto-rotate
    if (this.isRotating) {
      this.spherical.theta += 0.003;
      this._updateCamera();
    }

    this.renderer.render(this.scene, this.camera);
  }

  /**
   * Update body shape from measurement values.
   * @param {Object} measurements - { chest, waist, hip, shoulder, thigh, bicep, height }
   */
  updateFromMeasurements(measurements) {
    if (!this.smpl || !this.smpl.ready) return;

    this.currentBetas = this.smpl.measurementsToBetas(measurements, this.gender);
    const vertices = this.smpl.computeBodyShape(this.currentBetas);

    // Update vertex buffer
    if (this.mesh) {
      const pos = this.mesh.geometry.attributes.position;
      for (let i = 0; i < vertices.length; i++) {
        pos.array[i] = vertices[i];
      }
      pos.needsUpdate = true;
      this.mesh.geometry.computeVertexNormals();
      this._groundMesh();
    }
  }

  /**
   * Switch gender and recompute with current measurements.
   */
  setGender(gender) {
    this.gender = gender;
  }

  /**
   * Load face indices from SMPL model (async).
   */
  async loadFaceIndices() {
    try {
      const resp = await fetch('/models/smpl_faces.npy');
      if (!resp.ok) return;
      const buf = await resp.arrayBuffer();
      const view = new DataView(buf);
      // Parse NPY header
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
