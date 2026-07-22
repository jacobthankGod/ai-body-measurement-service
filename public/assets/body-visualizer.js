/**
 * Body Visualizer - Three.js interactive SMPL body shape viewer
 * SMPL betas for natural mesh; height via Y-scaling (head excluded).
 * Per-part radial correction reduces slider coupling.
 */
class BodyVisualizer {
  constructor() {
    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.mesh = null;
    this.smpl = null;
    this.gender = 'male';
    this.currentBetas = new Float32Array(10);
    this.animId = null;
    this.isRotating = true;
    this.mouseDown = false;
    this.lastMouse = { x: 0, y: 0 };
    this.spherical = { theta: 0.3, phi: 1.2, radius: 2.5 };
    this.target = new THREE.Vector3(0, 0.9, 0);
    this._vertexNormals = null;
    this._partSets = null;
    this._faceArray = null;
  }

  async init(canvasId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) { console.error('Canvas not found:', canvasId); return; }

    this.smpl = new SMPLShapeEngine();
    await Promise.all([
      this.smpl.init(),
      this.loadFaceIndices(),
    ]);

    this._initPartSets();

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

    const defaultMeas = { chest: 95, waist: 80, hip: 95, shoulder: 45, thigh: 55, bicep: 30, height: 175, neck: 38 };
    this.currentBetas = this.smpl.measurementsToBetas(defaultMeas, this.gender);
    const vertices = this.smpl.computeBodyShape(this.currentBetas);

    const geometry = this._buildGeometry(vertices);
    this._computeVertexNormals(geometry);

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

  _initPartSets() {
    if (!window.SMPL_PARTS) {
      console.warn('SMPL_PARTS not loaded, using Y-range fallback');
      this._partSets = null;
      return;
    }
    this._partSets = {};
    for (const key in window.SMPL_PARTS) {
      this._partSets[key] = new Set(window.SMPL_PARTS[key]);
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

  _computeVertexNormals(geometry) {
    const pos = geometry.attributes.position;
    const idx = geometry.index;
    const nv = pos.count;
    const normals = new Float32Array(nv * 3);

    if (!idx) {
      for (let i = 0; i < nv * 3; i++) normals[i] = 0;
      this._vertexNormals = normals;
      this._faceArray = null;
      return;
    }

    const faceCount = idx.count / 3;
    const faceNormals = new Float32Array(faceCount * 3);

    for (let f = 0; f < faceCount; f++) {
      const i0 = idx.array[f * 3];
      const i1 = idx.array[f * 3 + 1];
      const i2 = idx.array[f * 3 + 2];

      const ax = pos.array[i1 * 3] - pos.array[i0 * 3];
      const ay = pos.array[i1 * 3 + 1] - pos.array[i0 * 3 + 1];
      const az = pos.array[i1 * 3 + 2] - pos.array[i0 * 3 + 2];
      const bx = pos.array[i2 * 3] - pos.array[i0 * 3];
      const by = pos.array[i2 * 3 + 1] - pos.array[i0 * 3 + 1];
      const bz = pos.array[i2 * 3 + 2] - pos.array[i0 * 3 + 2];

      let nx = ay * bz - az * by;
      let ny = az * bx - ax * bz;
      let nz = ax * by - ay * bx;
      const len = Math.sqrt(nx * nx + ny * ny + nz * nz) || 1e-8;
      nx /= len; ny /= len; nz /= len;

      faceNormals[f * 3] = nx;
      faceNormals[f * 3 + 1] = ny;
      faceNormals[f * 3 + 2] = nz;

      for (let j = 0; j < 3; j++) {
        const vi = idx.array[f * 3 + j];
        normals[vi * 3] += nx;
        normals[vi * 3 + 1] += ny;
        normals[vi * 3 + 2] += nz;
      }
    }

    for (let i = 0; i < nv; i++) {
      const nx = normals[i * 3];
      const ny = normals[i * 3 + 1];
      const nz = normals[i * 3 + 2];
      const len = Math.sqrt(nx * nx + ny * ny + nz * nz) || 1e-8;
      normals[i * 3] = nx / len;
      normals[i * 3 + 1] = ny / len;
      normals[i * 3 + 2] = nz / len;
    }

    this._vertexNormals = normals;
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
   * 1. Compute betas → natural mesh
   * 2. Height via Y-scaling (head excluded)
   * 3. Per-part radial correction for measurement accuracy
   */
  updateFromMeasurements(measurements) {
    if (!this.smpl || !this.smpl.ready) return;

    const targetHeightCm = measurements.height || 175;
    this.currentBetas = this.smpl.measurementsToBetas(measurements, this.gender);
    const vertices = this.smpl.computeBodyShape(this.currentBetas);

    if (!this.mesh) return;
    const pos = this.mesh.geometry.attributes.position;

    // Step 1: Write beta-computed vertices
    for (let i = 0; i < vertices.length; i++) {
      pos.array[i] = vertices[i];
    }

    // Step 2: Height scaling — exclude head+neck vertices
    let minY = Infinity, maxY = -Infinity;
    const headNeck = this._getPartSet('head', 'neck');
    for (let i = 0; i < pos.count; i++) {
      if (headNeck.has(i)) continue;
      const y = pos.array[i * 3 + 1];
      if (y < minY) minY = y;
      if (y > maxY) maxY = y;
    }
    const actualHeightM = maxY - minY;
    const targetHeightM = targetHeightCm / 100;
    const heightScale = actualHeightM > 0 ? targetHeightM / actualHeightM : 1.0;

    for (let i = 0; i < pos.count; i++) {
      if (headNeck.has(i)) continue;
      pos.array[i * 3 + 1] *= heightScale;
    }

    // Step 3: Recompute normals after height scaling
    this.mesh.geometry.computeVertexNormals();
    this._computeVertexNormals(this.mesh.geometry);

    // Step 4: Per-part radial correction
    this._applyPartCorrections(pos, measurements);

    pos.needsUpdate = true;
    this.mesh.geometry.computeVertexNormals();
    this._groundMesh();
  }

  _getPartSet(...names) {
    const combined = new Set();
    if (!this._partSets) return combined;
    for (const name of names) {
      const s = this._partSets[name];
      if (s) for (const v of s) combined.add(v);
    }
    return combined;
  }

  /**
   * Apply per-body-part radial correction to reduce slider coupling.
   * For each measurement, compute actual circumference from mesh,
   * then displace part vertices to match target.
   */
  _applyPartCorrections(pos, measurements) {
    if (!this._partSets || !this._vertexNormals) return;

    const corrections = [
      { key: 'chest',    parts: ['spine2', 'rightShoulder', 'leftShoulder'], band: 0.04 },
      { key: 'waist',    parts: ['spine1'],                                  band: 0.03 },
      { key: 'hip',      parts: ['hips', 'rightUpLeg', 'leftUpLeg'],        band: 0.04 },
      { key: 'shoulder', parts: ['rightArm', 'leftArm'],                     band: 0.06 },
      { key: 'thigh',    parts: ['rightUpLeg', 'leftUpLeg'],                 band: 0.05 },
      { key: 'bicep',    parts: ['rightArm', 'leftArm'],                     band: 0.04 },
      { key: 'neck',     parts: ['neck'],                                     band: 0.03 },
    ];

    for (const corr of corrections) {
      const target = measurements[corr.key];
      if (!target) continue;

      const partVerts = this._getPartSet(...corr.parts);
      if (partVerts.size === 0) continue;

      const { circumference, centerY } = this._measurePartCircumference(pos, partVerts, corr.band);
      if (circumference < 1) continue;

      const ratio = target / circumference;
      if (Math.abs(ratio - 1) < 0.01) continue;

      const strength = Math.min(Math.abs(ratio - 1), 0.3);
      const sign = ratio > 1 ? 1 : -1;
      const displacement = sign * strength * 0.01;

      for (const vi of partVerts) {
        const nx = this._vertexNormals[vi * 3];
        const ny = this._vertexNormals[vi * 3 + 1];
        const nz = this._vertexNormals[vi * 3 + 2];

        pos.array[vi * 3]     += nx * displacement;
        pos.array[vi * 3 + 1] += ny * displacement;
        pos.array[vi * 3 + 2] += nz * displacement;
      }
    }
  }

  /**
   * Measure approximate circumference of a body part from its vertices.
   * Uses convex hull of XZ-projection of nearby vertices.
   */
  _measurePartCircumference(pos, partVerts, bandWidth) {
    let sumY = 0;
    for (const vi of partVerts) sumY += pos.array[vi * 3 + 1];
    const centerY = sumY / partVerts.size;

    const nearVerts = [];
    for (const vi of partVerts) {
      const y = pos.array[vi * 3 + 1];
      if (Math.abs(y - centerY) <= bandWidth) {
        nearVerts.push([pos.array[vi * 3], pos.array[vi * 3 + 2]]);
      }
    }

    if (nearVerts.length < 6) {
      for (const vi of partVerts) {
        nearVerts.push([pos.array[vi * 3], pos.array[vi * 3 + 2]]);
      }
    }

    if (nearVerts.length < 3) return { circumference: 0, centerY };

    const hull = this._convexHull2D(nearVerts);
    if (hull.length < 3) return { circumference: 0, centerY };

    let perimeter = 0;
    for (let i = 0; i < hull.length; i++) {
      const next = (i + 1) % hull.length;
      const dx = hull[next][0] - hull[i][0];
      const dz = hull[next][1] - hull[i][1];
      perimeter += Math.sqrt(dx * dx + dz * dz);
    }

    return { circumference: perimeter, centerY };
  }

  _convexHull2D(points) {
    const pts = points.slice().sort((a, b) => a[0] - b[0] || a[1] - b[1]);
    const n = pts.length;
    if (n <= 1) return pts;

    const cross = (O, A, B) =>
      (A[0] - O[0]) * (B[1] - O[1]) - (A[1] - O[1]) * (B[0] - O[0]);

    const lower = [];
    for (const p of pts) {
      while (lower.length >= 2 && cross(lower[lower.length - 2], lower[lower.length - 1], p) <= 0) {
        lower.pop();
      }
      lower.push(p);
    }

    const upper = [];
    for (let i = pts.length - 1; i >= 0; i--) {
      const p = pts[i];
      while (upper.length >= 2 && cross(upper[upper.length - 2], upper[upper.length - 1], p) <= 0) {
        upper.pop();
      }
      upper.push(p);
    }

    lower.pop();
    upper.pop();
    return lower.concat(upper);
  }

  setGender(gender) {
    this.gender = gender;
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
