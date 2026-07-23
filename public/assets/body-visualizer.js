/**
 * Body Visualizer - Three.js interactive SMPL body shape viewer
 * SMPL betas for natural mesh; height via Y-scaling (head excluded).
 * Two-layer pipeline: MLP betas + per-measurement displacement correction.
 *
 * All internal keys use lowercase_underscore (matching HTML data-measurement).
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
    this._faceArray = null;
    this._partSets = null;
  }

  async init(canvasId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) { console.error('Canvas not found:', canvasId); return; }

    this.smpl = new SMPLShapeEngine();

    // Load SMPL models and face indices in parallel
    console.log('Loading SMPL models and face indices...');
    await Promise.all([
      this.smpl.init(),
      this.loadFaceIndices(),
    ]);

    // Verify face indices loaded
    if (!BodyVisualizer._faceIndices) {
      console.error('WARNING: Face indices not loaded. Mesh may render incorrectly.');
      console.error('Retrying face indices load...');
      await this.loadFaceIndices();
      if (!BodyVisualizer._faceIndices) {
        console.error('CRITICAL: Face indices failed to load after retry. Mesh will be broken.');
      }
    } else {
      console.log('Face indices ready:', BodyVisualizer._faceIndices.length / 3, 'triangles');
    }

    this._initPartSets();

    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x0B0B0C);

    this.camera = new THREE.PerspectiveCamera(35, 1, 0.1, 100);
    this._updateCamera();

    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this._resize();
    window.addEventListener('resize', () => this._resize());

    const hemi = new THREE.HemisphereLight(0xffffff, 0x666666, 1.0);
    this.scene.add(hemi);
    const dir1 = new THREE.DirectionalLight(0xffffff, 0.9);
    dir1.position.set(2, 4, 3);
    this.scene.add(dir1);
    const dir2 = new THREE.DirectionalLight(0xffffff, 0.5);
    dir2.position.set(-2, 2, -1);
    this.scene.add(dir2);
    const dir3 = new THREE.DirectionalLight(0xffffff, 0.4);
    dir3.position.set(0, 2, -3);
    this.scene.add(dir3);
    const amb = new THREE.AmbientLight(0x404040, 0.3);
    this.scene.add(amb);

    const grid = new THREE.GridHelper(4, 20, 0x333333, 0x222222);
    grid.position.y = 0;
    this.scene.add(grid);

    const defaultMeas = { chest: 95, waist: 80, hip: 95, shoulder: 45, thigh: 55, bicep: 30, height: 175, neck: 38 };
    this.currentBetas = this.smpl.measurementsToBetas(defaultMeas, this.gender);
    const vertices = this.smpl.computeBodyShape(this.currentBetas);

    const geometry = this._buildGeometry(vertices);
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

    console.log('BodyVisualizer init complete. Mesh:', this.mesh.geometry.attributes.position.count, 'vertices,',
      this.mesh.geometry.index ? (this.mesh.geometry.index.count / 3) + ' triangles' : 'NO INDEX');
  }

  _initPartSets() {
    if (window.SMPL_PARTS) {
      this._partSets = {};
      for (const key in window.SMPL_PARTS) {
        this._partSets[key] = new Set(window.SMPL_PARTS[key]);
      }
    }
  }

  _buildGeometry(vertexData) {
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(vertexData);
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    if (BodyVisualizer._faceIndices) {
      console.log('Building geometry with', BodyVisualizer._faceIndices.length / 3, 'triangles from face indices');
      geometry.setIndex(new THREE.BufferAttribute(BodyVisualizer._faceIndices, 1));
    } else {
      console.error('CRITICAL: No face indices available! Using identity fallback (mesh will look wrong)');
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
   * Two-layer update pipeline.
   * @param {Object} measurements - all measurements with UI keys (lowercase_underscore)
   */
  updateFromMeasurements(measurements) {
    if (!this.smpl || !this.smpl.ready) {
      console.warn('updateFromMeasurements: smpl not ready');
      return;
    }

    const targetHeightCm = measurements.height || 175;

    this.currentBetas = this.smpl.measurementsToBetas(measurements, this.gender);
    console.log('Betas:', Array.from(this.currentBetas).map(v => v.toFixed(3)).join(', '));
    const vertices = this.smpl.computeBodyShape(this.currentBetas);

    if (!this.mesh) return;
    const pos = this.mesh.geometry.attributes.position;

    for (let i = 0; i < vertices.length; i++) {
      pos.array[i] = vertices[i];
    }

    // Height scaling (exclude head+neck)
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

    this.mesh.geometry.computeVertexNormals();

    // Measure actual values from current mesh (returns Title Case keys)
    const actualMeas = this.computeAllMeasurements(pos);

    // Convert actual measurements from Title Case keys to UI keys
    const actualUI = {};
    for (const [mlpKey, uiKey] of Object.entries(this.smpl.MLP_TO_UI)) {
      if (actualMeas[mlpKey] !== undefined) {
        actualUI[uiKey] = actualMeas[mlpKey];
      }
    }
    // Some measurements have the same key format in both
    for (const [k, v] of Object.entries(actualMeas)) {
      if (actualUI[k] === undefined) actualUI[k] = v;
    }

    // Apply displacement corrections (both inputs use UI keys)
    this.smpl.applyDisplacements(pos.array, measurements, actualUI);

    pos.needsUpdate = true;
    this.mesh.geometry.computeVertexNormals();
    this._groundMesh();

    return actualUI;
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

  setGender(gender) {
    this.gender = gender;
  }

  async loadFaceIndices() {
    if (BodyVisualizer._faceIndices) {
      console.log('Face indices already loaded, applying to mesh');
      if (this.mesh && !this.mesh.geometry.index) {
        this.mesh.geometry.setIndex(new THREE.BufferAttribute(BodyVisualizer._faceIndices, 1));
        this.mesh.geometry.computeVertexNormals();
      }
      return;
    }
    const paths = ['/models/smpl_faces.npy', '/assets/smpl_faces.npy'];
    for (const url of paths) {
      try {
        console.log('Fetching face indices from', url, '...');
        const resp = await fetch(url);
        console.log('Response:', resp.status, resp.statusText, 'size:', resp.headers.get('content-length'));
        if (!resp.ok) { console.warn('Failed:', resp.status, 'from', url); continue; }
        const buf = await resp.arrayBuffer();
        const view = new DataView(buf);
        const magic = String.fromCharCode(view.getUint8(0), view.getUint8(1), view.getUint8(2), view.getUint8(3), view.getUint8(4), view.getUint8(5));
        if (magic !== '\x93NUMPY') { console.error('Invalid NPY magic from', url); continue; }
        const major = view.getUint8(6);
        let headerLen, headerStart;
        if (major === 1) { headerLen = view.getUint16(8, true); headerStart = 10; }
        else { headerLen = view.getUint32(8, true); headerStart = 12; }
        const dataStart = headerStart + headerLen;
        const total = 13776 * 3;
        console.log('NPY: major=' + major + ' headerLen=' + headerLen + ' dataStart=' + dataStart);
        if (buf.byteLength < dataStart + total * 4) {
          console.error('File too small:', buf.byteLength, 'need', dataStart + total * 4);
          continue;
        }
        const indices = new Uint32Array(total);
        for (let i = 0; i < total; i++) {
          indices[i] = view.getUint32(dataStart + i * 4, true);
        }
        console.log('Face indices loaded: ' + indices.length + ' values, max=' + indices.max);
        BodyVisualizer._faceIndices = indices;
        if (this.mesh) {
          this.mesh.geometry.setIndex(new THREE.BufferAttribute(indices, 1));
          this.mesh.geometry.computeVertexNormals();
          console.log('Applied face indices to existing mesh');
        }
        return;
      } catch (e) {
        console.error('Error loading from', url, ':', e);
      }
    }
    console.error('CRITICAL: Could not load face indices from any path');
  }

  /* ===== MEASUREMENT EXTRACTION ENGINE ===== */

  _getPartVerts(name) {
    if (this._partSets && this._partSets[name]) return Array.from(this._partSets[name]);
    if (window.SMPL_PARTS && window.SMPL_PARTS[name]) return window.SMPL_PARTS[name];
    if (window.CUSTOM_BODY_POINTS) {
      const key = Object.keys(window.CUSTOM_BODY_POINTS).find(k =>
        k.toLowerCase().replace(/\s+/g, '') === name.toLowerCase().replace(/\s+/g, '')
      );
      if (key) return window.CUSTOM_BODY_POINTS[key];
    }
    return [];
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

  _computeCircumference(pos, faceArr, verts, planeY, bandW, partVerts) {
    if (!verts || verts.length < 3 || !faceArr) return 0;
    const intersections = [];
    const fCount = faceArr.length / 3;
    const partSet = partVerts && partVerts.length > 0 ? new Set(partVerts) : null;

    for (let f = 0; f < fCount; f++) {
      const i0 = faceArr[f * 3], i1 = faceArr[f * 3 + 1], i2 = faceArr[f * 3 + 2];
      if (partSet) {
        if (!partSet.has(i0) && !partSet.has(i1) && !partSet.has(i2)) continue;
      }
      const edges = [[i0, i1], [i1, i2], [i2, i0]];
      for (const [a, b] of edges) {
        const ya = pos[a * 3 + 1], yb = pos[b * 3 + 1];
        if ((ya - planeY) * (yb - planeY) < 0) {
          const t = (planeY - ya) / (yb - ya);
          intersections.push([
            pos[a * 3] + t * (pos[b * 3] - pos[a * 3]),
            pos[a * 3 + 2] + t * (pos[b * 3 + 2] - pos[a * 3 + 2])
          ]);
        }
      }
    }

    if (intersections.length < 3) return 0;
    const hull = this._convexHull2D(intersections);
    if (hull.length < 3) return 0;
    let perim = 0;
    for (let i = 0; i < hull.length; i++) {
      const j = (i + 1) % hull.length;
      const dx = hull[j][0] - hull[i][0], dz = hull[j][1] - hull[i][1];
      perim += Math.sqrt(dx * dx + dz * dz);
    }
    return perim * 100;
  }

  _computeBandVerts(pos, verts, planeY, bandW) {
    if (!verts || verts.length === 0) return [];
    const result = [];
    for (const vi of verts) {
      if (Math.abs(pos[vi * 3 + 1] - planeY) <= bandW) result.push(vi);
    }
    return result.length >= 4 ? result : verts;
  }

  _centroidY(pos, verts) {
    if (!verts || verts.length === 0) return 0;
    let s = 0;
    for (const vi of verts) s += pos[vi * 3 + 1];
    return s / verts.length;
  }

  _centroid(pos, verts) {
    if (!verts || verts.length === 0) return [0, 0, 0];
    let sx = 0, sy = 0, sz = 0;
    for (const vi of verts) { sx += pos[vi * 3]; sy += pos[vi * 3 + 1]; sz += pos[vi * 3 + 2]; }
    return [sx / verts.length, sy / verts.length, sz / verts.length];
  }

  _dist(pos, vertsA, vertsB) {
    const a = this._centroid(pos, vertsA);
    const b = this._centroid(pos, vertsB);
    const dx = a[0] - b[0], dy = a[1] - b[1], dz = a[2] - b[2];
    return Math.sqrt(dx * dx + dy * dy + dz * dz) * 100;
  }

  _xSpan(pos, verts) {
    if (!verts || verts.length === 0) return 0;
    let minX = Infinity, maxX = -Infinity;
    for (const vi of verts) {
      const x = pos[vi * 3];
      if (x < minX) minX = x;
      if (x > maxX) maxX = x;
    }
    return (maxX - minX) * 100;
  }

  _circFromVerts(pos, verts, proj) {
    if (!verts || verts.length < 3) return 0;
    const pts = [];
    for (const vi of verts) {
      if (proj === 'yz') pts.push([pos[vi * 3 + 1], pos[vi * 3 + 2]]);
      else pts.push([pos[vi * 3], pos[vi * 3 + 2]]);
    }
    const hull = this._convexHull2D(pts);
    if (hull.length < 3) return 0;
    let perim = 0;
    for (let i = 0; i < hull.length; i++) {
      const j = (i + 1) % hull.length;
      const dx = hull[j][0] - hull[i][0], dz = hull[j][1] - hull[i][1];
      perim += Math.sqrt(dx * dx + dz * dz);
    }
    return perim * 100;
  }

  /**
   * Compute all measurements from current mesh positions.
   * Returns object with MLP-style Title Case keys (e.g. 'Chest Round', 'Elbow Round').
   */
  computeAllMeasurements(pos) {
    if (!pos) return {};
    const faceArr = BodyVisualizer._faceIndices;
    const M = {};

    const chestV = this._getPartVerts('spine2');
    const shoulderV = this._getPartVerts('rightShoulder').concat(this._getPartVerts('leftShoulder'));
    const waistV = this._getPartVerts('spine1');
    const stomachV = this._getPartVerts('spine');
    const hipsV = this._getPartVerts('hips');
    const neckV = this._getPartVerts('neck');
    const rArmV = this._getPartVerts('rightArm');
    const lArmV = this._getPartVerts('leftArm');
    const rForeV = this._getPartVerts('rightForeArm');
    const lForeV = this._getPartVerts('leftForeArm');
    const rLegV = this._getPartVerts('rightUpLeg');
    const lLegV = this._getPartVerts('leftUpLeg');
    const rCalfV = this._getPartVerts('rightLeg');
    const lCalfV = this._getPartVerts('leftLeg');
    const rHandV = this._getPartVerts('rightHand');
    const lHandV = this._getPartVerts('leftHand');
    const rFootV = this._getPartVerts('rightFoot');
    const lFootV = this._getPartVerts('leftFoot');
    const chestAll = chestV.concat(shoulderV);

    const chestY = this._centroidY(pos, chestAll);
    const waistY = this._centroidY(pos, waistV);
    const stomachY = stomachV.length > 0 ? this._centroidY(pos, stomachV) : (chestY + waistY) / 2;
    const hipsY = this._centroidY(pos, hipsV);
    const neckY = this._centroidY(pos, neckV);
    const rArmY = this._centroidY(pos, rArmV);
    const lArmY = this._centroidY(pos, lArmV);
    const rForeY = this._centroidY(pos, rForeV);
    const lForeY = this._centroidY(pos, lForeV);
    const foreArmY = (rForeY + lForeY) / 2;
    const rLegY = this._centroidY(pos, rLegV);
    const lLegY = this._centroidY(pos, lLegV);
    const rCalfY = this._centroidY(pos, rCalfV);
    const lCalfY = this._centroidY(pos, lCalfV);
    const calfY = (rCalfY + lCalfY) / 2;

    const ankleRaw = rCalfV.concat(rFootV);
    const ankleV = ankleRaw.filter(vi => pos[vi * 3 + 1] < -1.0);
    const ankleY = ankleV.length > 0 ? this._centroidY(pos, ankleV) : calfY - 0.12;
    const wristRaw = rForeV.concat(rHandV);
    const wristV = wristRaw.filter(vi => pos[vi * 3 + 1] < 0.19);
    const wristY = wristV.length > 0 ? this._centroidY(pos, wristV) : foreArmY - 0.15;

    const rKneeV = rCalfV.filter(vi => pos[vi * 3 + 1] > -0.8);
    const lKneeV = lCalfV.filter(vi => pos[vi * 3 + 1] > -0.8);
    const rKneeY = rKneeV.length > 0 ? this._centroidY(pos, rKneeV) : rCalfY + 0.1;
    const lKneeY = lKneeV.length > 0 ? this._centroidY(pos, lKneeV) : lCalfY + 0.1;

    const circ = (verts, y, bw, partVerts) => {
      const band = this._computeBandVerts(pos, verts, y, bw || 0.03);
      return this._computeCircumference(pos, faceArr, band, y, bw || 0.03, partVerts || verts);
    };

    const limbCirc = (verts, y, bw, proj) => {
      const band = this._computeBandVerts(pos, verts, y, bw || 0.03);
      return this._circFromVerts(pos, band, proj || 'xz');
    };

    M['Shoulder'] = Math.round(this._xSpan(pos, shoulderV) * 10) / 10;
    M['Across Shoulder'] = M['Shoulder'];
    M['Across Back'] = Math.round(M['Shoulder'] * 0.92 * 10) / 10;
    M['Across Chest'] = Math.round(M['Shoulder'] * 0.96 * 10) / 10;

    M['Chest Round']    = Math.round(circ(chestAll, chestY, 0.04) * 10) / 10;
    M['Bust Round']     = M['Chest Round'];
    M['Waist Round']    = Math.round(circ(waistV, waistY, 0.03) * 10) / 10;
    M['Stomach Round']  = stomachV.length > 0 ? Math.round(circ(stomachV, stomachY, 0.04) * 10) / 10 : M['Waist Round'];
    M['Hip Round']      = Math.round(circ(hipsV, hipsY, 0.04) * 10) / 10;
    M['Neck Round']     = Math.round(circ(neckV, neckY, 0.03) * 10) / 10;
    M['Thigh Round']    = Math.round((limbCirc(rLegV, rLegY, 0.05) + limbCirc(lLegV, lLegY, 0.05)) / 2 * 10) / 10;
    M['Knee Round']     = Math.round((limbCirc(rKneeV, rKneeY, 0.03) + limbCirc(lKneeV, lKneeY, 0.03)) / 2 * 10) / 10;
    M['Calf Round']     = Math.round((limbCirc(rCalfV, rCalfY, 0.04) + limbCirc(lCalfV, lCalfY, 0.04)) / 2 * 10) / 10;
    M['Ankle Round']    = ankleV.length > 0 ? Math.round(limbCirc(ankleV, ankleY, 0.03) * 10) / 10 : 0;
    M['Bicep Round']    = Math.round((limbCirc(rArmV, rArmY, 0.04, 'yz') + limbCirc(lArmV, lArmY, 0.04, 'yz')) / 2 * 10) / 10;
    M['Elbow Round']    = Math.round((limbCirc(rForeV, rForeY, 0.03, 'yz') + limbCirc(lForeV, lForeY, 0.03, 'yz')) / 2 * 10) / 10;
    M['Wrist Round']    = wristV.length > 0 ? Math.round(limbCirc(wristV, wristY, 0.03, 'yz') * 10) / 10 : 0;
    M['Upper Hip']      = Math.round(M['Hip Round'] * 0.92 * 10) / 10;
    M['Armhole Round']  = Math.round(M['Shoulder'] * 0.45 * 10) / 10;

    M['Half Length']    = Math.round(this._dist(pos, neckV, waistV) * 10) / 10;
    M['Full Top Length']= Math.round(this._dist(pos, neckV, hipsV) * 10) / 10;
    M['Back Waist Length']  = M['Half Length'];
    M['Front Waist Length'] = M['Half Length'];
    M['Neck to Waist']  = M['Half Length'];
    M['Shoulder to Waist'] = M['Half Length'];
    M['Waist to Hip']   = Math.round(this._dist(pos, waistV, hipsV) * 10) / 10;
    M['Crotch Depth']   = M['Waist to Hip'];
    M['Trouser Waist']  = M['Waist Round'];
    M['Trouser Length'] = Math.round(this._dist(pos, waistV, ankleV.length > 0 ? ankleV : rCalfV) * 10) / 10;
    M['Inseam']         = Math.round(M['Trouser Length'] * 0.78 * 10) / 10;
    M['Sleeve Length']  = Math.round(this._dist(pos, shoulderV, wristV.length > 0 ? wristV : rForeV) * 10) / 10;

    M['High Bust']      = Math.round(M['Bust Round'] * 0.85 * 10) / 10;
    M['Under Bust']     = Math.round(M['Bust Round'] * 0.75 * 10) / 10;
    M['Bust Point']     = Math.round(this._dist(pos, neckV, chestV.slice(0, 3)) * 10) / 10;
    M['Shoulder to Bust Point'] = Math.round(M['Bust Point'] * 1.1 * 10) / 10;
    M['Shoulder to Under Bust'] = Math.round(M['Bust Point'] * 1.3 * 10) / 10;

    return M;
  }

  dispose() {
    if (this.animId) cancelAnimationFrame(this.animId);
    if (this.renderer) this.renderer.dispose();
  }
}

window.BodyVisualizer = BodyVisualizer;
