/**
 * MakeHuman Body Visualizer — Three.js interactive body shape viewer.
 *
 * Morph-target pipeline: measurements → morph influences → blended mesh.
 * Replaces the SMPL-based BodyVisualizer with per-body-part atomic control.
 *
 * Public API:
 *   vis.init(canvasId) → Promise<void>
 *   vis.updateFromMeasurements(measurements) → {}
 *   vis.computeAllMeasurements(pos) → { measurementName: valueCm, ... }
 *   vis.setGender(gender) → void
 *   vis.dispose() → void
 */
class MakeHumanBodyVisualizer {
  constructor() {
    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.mesh = null;
    this.engine = null;
    this.gender = 'male';
    this.animId = null;
    this.isRotating = true;
    this.mouseDown = false;
    this.lastMouse = { x: 0, y: 0 };
    this.spherical = { theta: 0.3, phi: 1.1, radius: 42.0 };
    this.target = new THREE.Vector3(0, 7.0, 0);
    this._lastMeasurements = null;
    this._initDone = false;
    this._switching = false;
    this._pendingGender = null;
    this.garmentMorphCtrl = new GarmentMorphController();
  }

  async init(canvasId) {
    var canvas = document.getElementById(canvasId);
    if (!canvas) { console.error('[MakeHumanVis] Canvas not found:', canvasId); return; }

    try {
      this.engine = new MakeHumanEngine();
      await this.engine.init('', this.gender);
    } catch (err) {
      console.error('[MakeHumanVis] Engine init FAILED:', err);
      var el = document.getElementById('visLoading');
      if (el) { el.textContent = 'Failed to load body model: ' + err.message; el.style.color = '#ff4444'; }
      return;
    }

    try {
      this.scene = new THREE.Scene();
      this.scene.background = new THREE.Color(0x0B0B0C);

      this.camera = new THREE.PerspectiveCamera(35, 1, 0.1, 100);
      this._updateCamera();

      this.renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true });
      this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      this._resize();
      window.addEventListener('resize', this._resize.bind(this));

      // Lighting
      var hemi = new THREE.HemisphereLight(0xffffff, 0x666666, 1.0);
      this.scene.add(hemi);
      var dir1 = new THREE.DirectionalLight(0xffffff, 0.9);
      dir1.position.set(2, 4, 3);
      this.scene.add(dir1);
      var dir2 = new THREE.DirectionalLight(0xffffff, 0.5);
      dir2.position.set(-2, 2, -1);
      this.scene.add(dir2);
      var dir3 = new THREE.DirectionalLight(0xffffff, 0.4);
      dir3.position.set(0, 2, -3);
      this.scene.add(dir3);
      var amb = new THREE.AmbientLight(0x404040, 0.3);
      this.scene.add(amb);

      var grid = new THREE.GridHelper(40, 40, 0x333333, 0x222222);
      grid.position.y = 0;
      this.scene.add(grid);

      // Create geometry from engine
      this.engine.computeVertices();
      this.engine.computeNormals();

      this._rebuildMesh();

      this._initControls(canvas);
      this._animate();
      this._initDone = true;

      var loading = document.getElementById('visLoading');
      if (loading) loading.style.display = 'none';
    } catch (err) {
      console.error('[MakeHumanVis] Scene/renderer setup FAILED:', err);
      var el = document.getElementById('visLoading');
      if (el) { el.textContent = '3D setup failed: ' + err.message; el.style.color = '#ff4444'; }
    }
  }

  _getVertexYMin() {
    var e = this.engine; if (!e || !e.vertices) return 0;
    var min = Infinity;
    for (var i = 0; i < e.vertCount; i++) { var y = e.vertices[i * 3 + 1]; if (y < min) min = y; }
    return min;
  }
  _getVertexYMax() {
    var e = this.engine; if (!e || !e.vertices) return 0;
    var max = -Infinity;
    for (var i = 0; i < e.vertCount; i++) { var y = e.vertices[i * 3 + 1]; if (y > max) max = y; }
    return max;
  }

  /**
   * Build non-indexed BufferGeometry with skin material (textured or solid color).
   */
  _rebuildMesh() {
    var e = this.engine;
    var F = e.faceCount;

    var posArr = new Float32Array(F * 9);
    var normArr = new Float32Array(F * 9);
    var uvArr = new Float32Array(F * 6);  // 3 verts × 2 UV coords

    for (var f = 0; f < F; f++) {
      var vi0 = e.faces[f * 3];
      var vi1 = e.faces[f * 3 + 1];
      var vi2 = e.faces[f * 3 + 2];

      posArr[f * 9]     = e.vertices[vi0 * 3];
      posArr[f * 9 + 1] = e.vertices[vi0 * 3 + 1];
      posArr[f * 9 + 2] = e.vertices[vi0 * 3 + 2];
      posArr[f * 9 + 3] = e.vertices[vi1 * 3];
      posArr[f * 9 + 4] = e.vertices[vi1 * 3 + 1];
      posArr[f * 9 + 5] = e.vertices[vi1 * 3 + 2];
      posArr[f * 9 + 6] = e.vertices[vi2 * 3];
      posArr[f * 9 + 7] = e.vertices[vi2 * 3 + 1];
      posArr[f * 9 + 8] = e.vertices[vi2 * 3 + 2];

      if (e.normals) {
        normArr[f * 9]     = e.normals[vi0 * 3];
        normArr[f * 9 + 1] = e.normals[vi0 * 3 + 1];
        normArr[f * 9 + 2] = e.normals[vi0 * 3 + 2];
        normArr[f * 9 + 3] = e.normals[vi1 * 3];
        normArr[f * 9 + 4] = e.normals[vi1 * 3 + 1];
        normArr[f * 9 + 5] = e.normals[vi1 * 3 + 2];
        normArr[f * 9 + 6] = e.normals[vi2 * 3];
        normArr[f * 9 + 7] = e.normals[vi2 * 3 + 1];
        normArr[f * 9 + 8] = e.normals[vi2 * 3 + 2];
      }

      // UV mapping: look up UV indices for this face, then get UV coords
      if (e.uvs && e.faceUVIndices) {
        var uvi0 = e.faceUVIndices[f * 3];
        var uvi1 = e.faceUVIndices[f * 3 + 1];
        var uvi2 = e.faceUVIndices[f * 3 + 2];
        uvArr[f * 6]     = e.uvs[uvi0 * 2];
        uvArr[f * 6 + 1] = 1.0 - e.uvs[uvi0 * 2 + 1];  // flip V for WebGL
        uvArr[f * 6 + 2] = e.uvs[uvi1 * 2];
        uvArr[f * 6 + 3] = 1.0 - e.uvs[uvi1 * 2 + 1];
        uvArr[f * 6 + 4] = e.uvs[uvi2 * 2];
        uvArr[f * 6 + 5] = 1.0 - e.uvs[uvi2 * 2 + 1];
      }
    }

    if (this.mesh) {
      this.scene.remove(this.mesh);
      if (this.mesh.geometry) this.mesh.geometry.dispose();
      if (this.mesh.material) {
        if (Array.isArray(this.mesh.material)) {
          this.mesh.material.forEach(function(m) { m.dispose(); });
        } else {
          this.mesh.material.dispose();
        }
      }
    }

    var geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(posArr, 3));
    geometry.setAttribute('normal', new THREE.BufferAttribute(normArr, 3));
    if (e.uvs && e.faceUVIndices) {
      geometry.setAttribute('uv', new THREE.BufferAttribute(uvArr, 2));
    }

    // Create skin material — textured if texture available, else solid color
    var skinMaterial;
    if (e.texturePath) {
      var textureLoader = new THREE.TextureLoader();
      var tex = textureLoader.load(e.texturePath);
      tex.colorSpace = THREE.SRGBColorSpace;
      skinMaterial = new THREE.MeshStandardMaterial({
        map: tex,
        roughness: 0.6,
        metalness: 0.05,
        flatShading: false,
        side: THREE.FrontSide,
      });
    } else {
      skinMaterial = new THREE.MeshStandardMaterial({
        color: 0xD4A574,
        roughness: 0.6,
        metalness: 0.05,
        flatShading: false,
        side: THREE.FrontSide,
      });
    }

    this.mesh = new THREE.Mesh(geometry, skinMaterial);
    this._groundMesh();
    this.scene.add(this.mesh);
  }

  /**
   * Update non-indexed geometry from current engine state (after morph + height scaling).
   */
  _updateMeshGeometry() {
    var e = this.engine;
    var F = e.faceCount;
    var pos = this.mesh.geometry.attributes.position;
    var norm = this.mesh.geometry.attributes.normal;

    for (var f = 0; f < F; f++) {
      var vi0 = e.faces[f * 3];
      var vi1 = e.faces[f * 3 + 1];
      var vi2 = e.faces[f * 3 + 2];

      pos.array[f * 9]     = e.vertices[vi0 * 3];
      pos.array[f * 9 + 1] = e.vertices[vi0 * 3 + 1];
      pos.array[f * 9 + 2] = e.vertices[vi0 * 3 + 2];
      pos.array[f * 9 + 3] = e.vertices[vi1 * 3];
      pos.array[f * 9 + 4] = e.vertices[vi1 * 3 + 1];
      pos.array[f * 9 + 5] = e.vertices[vi1 * 3 + 2];
      pos.array[f * 9 + 6] = e.vertices[vi2 * 3];
      pos.array[f * 9 + 7] = e.vertices[vi2 * 3 + 1];
      pos.array[f * 9 + 8] = e.vertices[vi2 * 3 + 2];

      if (e.normals) {
        norm.array[f * 9]     = e.normals[vi0 * 3];
        norm.array[f * 9 + 1] = e.normals[vi0 * 3 + 1];
        norm.array[f * 9 + 2] = e.normals[vi0 * 3 + 2];
        norm.array[f * 9 + 3] = e.normals[vi1 * 3];
        norm.array[f * 9 + 4] = e.normals[vi1 * 3 + 1];
        norm.array[f * 9 + 5] = e.normals[vi1 * 3 + 2];
        norm.array[f * 9 + 6] = e.normals[vi2 * 3];
        norm.array[f * 9 + 7] = e.normals[vi2 * 3 + 1];
        norm.array[f * 9 + 8] = e.normals[vi2 * 3 + 2];
      }
    }

    pos.needsUpdate = true;
    norm.needsUpdate = true;
    this.mesh.geometry.computeBoundingSphere();
    this.mesh.geometry.computeBoundingBox();
    this._groundMesh();
    this._morphsDirty = true; // Flag body BVH for refit

    var bb = this.mesh.geometry.boundingBox;
    var modelHeight = bb.max.y - bb.min.y;

    this._updateCamera();
  }

  /**
   * Update mesh from measurements.
   */
  updateFromMeasurements(measurements) {
    if (!this.engine || !this.engine.ready || !this.mesh) {
      var reason = !this.engine ? 'no engine' : !this.engine.ready ? 'engine not ready' : 'no mesh';
      console.warn('[MakeHumanVis] updateFromMeasurements BLOCKED:', reason);
      return {};
    }
    if (!this._initDone) {
      console.warn('[MakeHumanVis] updateFromMeasurements BLOCKED: _initDone=false');
      return {};
    }

    this._lastMeasurements = measurements;
    this._updateCount = (this._updateCount || 0) + 1;

    var targetHeightCm = measurements.height || 175;
    var e = this.engine;

    // Map measurements to morph influences
    this._applyMeasurementMappings(measurements);

    // Temporarily zero out the height morph — _applyHeightScaling handles height
    var heightMorphIdx = e.morphNames.indexOf('height');
    var savedHeightInfl = 0;
    if (heightMorphIdx >= 0) {
      savedHeightInfl = e.morphInfluences[heightMorphIdx];
      e.morphInfluences[heightMorphIdx] = 0;
    }

    // Compute blended vertices (without height morph)
    e.computeVertices();

    // Restore height morph influence (not used, but kept for reference)
    if (heightMorphIdx >= 0) {
      e.morphInfluences[heightMorphIdx] = savedHeightInfl;
    }

    // Debug: ?debug_raw skips post-morph processing to isolate distortion
    var skipPost = new URLSearchParams(window.location.search).has('debug_raw');
    var skipHeight = new URLSearchParams(window.location.search).has('debug_no_height');
    var skipDisp = new URLSearchParams(window.location.search).has('debug_no_disp');

    // Apply height scaling to e.vertices (before copy to Three.js)
    if (!skipPost && !skipHeight) {
      this._applyHeightScaling(targetHeightCm, e.vertices);
    }

    // Vertex displacements DISABLED — body_points indices don't match rebuilt mesh
    // (13,334 verts vs original 19,158). Causes massive distortion when enabled.
    // Morph targets already handle: chest, waist, hip, neck, shoulder, bicep,
    // wrist, thigh, calf, ankle, knee, across_chest, arm_length, lowerleg_length,
    // hip_height, neckheight, stomach_form

    // Recompute normals from morphed+heighted vertices
    e.computeNormals();

    // Update non-indexed geometry from engine state
    this._updateMeshGeometry();

    // Update garment morph targets if loaded
    if (this.garmentMorphCtrl && this.garmentMorphCtrl.loaded) {
      this.garmentMorphCtrl.updateFromMeasurements(measurements);
      this.garmentMorphCtrl.syncPosition(this.mesh.position);
    }

    return {};
  }

  /**
   * Switch gender: reload engine with new gender's binary files,
   * then re-apply the last measurements.
   */
  async setGender(gender) {
    if (!this.engine || !this._initDone) return;
    if (gender === this.gender) return;

    this.gender = gender;

    // Re-init engine with new gender's binary files
    try {
      await this.engine.init('', gender);
    } catch (err) {
      console.error('[MakeHumanVis] Engine re-init FAILED for', gender, ':', err);
      return;
    }

    // Swap skin texture based on gender
    var textureMap = {
      male: '/models/makehuman/textures/male_diffuse.png',
      female: '/models/makehuman/textures/female_diffuse.png'
    };
    if (textureMap[gender]) {
      this.setSkinTexture(textureMap[gender]);
    }

    // Re-apply measurements with gender-specific mappings
    if (this._lastMeasurements) {
      this.updateFromMeasurements(this._lastMeasurements);
    }
  }

  /**
   * Switch skin texture without reloading the mesh.
   * @param {string} textureUrl — path to diffuse texture PNG
   */
  setSkinTexture(textureUrl) {
    if (!this.mesh) return;
    var loader = new THREE.TextureLoader();
    var tex = loader.load(textureUrl);
    tex.colorSpace = THREE.SRGBColorSpace;
    this.mesh.material.map = tex;
    this.mesh.material.needsUpdate = true;
  }

  /**
   * Map UI measurement keys to MakeHuman morph target influences.
   */
  _applyMeasurementMappings(m) {
    var e = this.engine;
    var g = this.gender;

    // Reset all influences
    for (var i = 0; i < e.morphCount; i++) {
      e.morphInfluences[i] = 0;
    }

    if (g === 'male') {
      this._applyMaleMappings(m);
    } else if (g === 'female') {
      this._applyFemaleMappings(m);
    } else {
      this._applyChildMappings(m);
    }
  }

  _applyMaleMappings(m) {
    var e = this.engine;
    var direct = [
      ['height', m.height || 175],
      ['chest', m.chest || 96],
      ['bust_girth', m.chest_circ || 86],
      ['neck', m.neck || m['Neck Round'] || m.neck_round || 37],
      ['neckheight', m.half_length || m.neckheight || m['Half Length'] || 28],
      ['shoulders', m.shoulder || m['Shoulder'] || m.across_shoulder || 43],
      ['waist', m.waist || m['Waist Round'] || 84],
      ['hips', m.hip || m['Hip Round'] || 96],
      ['thigh_girth', m.thigh || m['Thigh Round'] || 55],
      ['calf_girth', m.calf || m.calf_round || m['Calf Round'] || 36],
      ['armgirth', m.bicep || m['Bicep Round'] || 32],
      ['wrist_girth', m.wrist || m.wrist_round || m['Wrist Round'] || 17],
      ['arm_length', m.sleeve_length || m['Sleeve Length'] || 62],
      ['lowerleg_length', m.trouser_length || m['Trouser Length'] || 116],
      ['hip_height', m.waist_to_hip || m['Waist to Hip'] || 28],
      ['ankle_round', m.ankle_round || m['Ankle Round'] || 24],
      ['across_chest', m.across_chest || m['Across Chest'] || 41],
      ['knee_round', m.knee_round || m['Knee Round'] || 38],
      ['across_back', m.across_back || 39],
      ['across_shoulder', m.across_shoulder || 42],
      ['elbow_round', m.elbow_round || 25],
      ['inseam', m.inseam || 91],
      ['trouser_waist', m.trouser_waist || 84],
      ['crotch_depth', m.crotch_depth || 28],
      ['bust_point', m.bust_point || 7],
      ['shoulder_to_bust', m.shoulder_to_bust || 8],
      // NEW morphs (34 total)
      ['back_waist_length', m.back_waist_length || 28],
      ['front_waist_length', m.front_waist_length || 28],
      ['high_bust', m.high_bust || 85],
      ['under_bust', m.under_bust || 76],
      ['armhole_round', m.armhole_round || 19],
      // Stomach form: driven directly by stomach slider (was incorrectly coupled to waist ratio)
      ['stomach_form', m.stomach || 82],
    ];

    for (var i = 0; i < direct.length; i++) {
      var morphName = direct[i][0];
      var value = direct[i][1];
      var idx = e.morphNames.indexOf(morphName);
      if (idx >= 0) {
        e.morphInfluences[idx] = e.measurementToInfluence(value, idx);
      }
    }

    // upper_hip: approximate via hips morph (circumference at upper hip region)
    var upperHipIdx = e.morphNames.indexOf('hips');
    if (upperHipIdx >= 0) {
      var upperHipVal = m.upper_hip || 91;
      var upperHipInfl = e.measurementToInfluence(upperHipVal, upperHipIdx);
      e.morphInfluences[upperHipIdx] = Math.max(e.morphInfluences[upperHipIdx], upperHipInfl);
    }

    // shoulder_slope: use limits-based influence
    if (m.shoulder_slope !== undefined) {
      var idx = e.morphNames.indexOf('shoulder_slope');
      if (idx >= 0) {
        e.morphInfluences[idx] = e.measurementToInfluence(m.shoulder_slope, idx);
      }
    }
  }

  _applyFemaleMappings(m) {
    var e = this.engine;
    var direct = [
      ['height', m.height || 165],
      ['neckheight', m.half_length || m.neckheight || m['Half Length'] || 28],
      ['neck', m.neck || m['Neck Round'] || m.neck_round || 31],
      ['shoulders', m.shoulder || m['Shoulder'] || m.across_shoulder || 43],
      ['chest', m.chest || m['Chest Round'] || 85],
      ['bust_girth', m.chest_circ || m.bust_round || m['Bust Round'] || 66],
      ['arm_length', m.sleeve_length || m['Sleeve Length'] || 62],
      ['armgirth', m.bicep || m['Bicep Round'] || 27],
      ['wrist_girth', m.wrist || m.wrist_round || m['Wrist Round'] || 14],
      ['waist', m.waist || m['Waist Round'] || 75],
      ['hips', m.hip || m['Hip Round'] || 100],
      ['hip_height', m.waist_to_hip || m['Waist to Hip'] || 82],
      ['thigh_girth', m.thigh || m['Thigh Round'] || 58],
      ['calf_girth', m.calf || m.calf_round || m['Calf Round'] || 36],
      ['lowerleg_length', m.trouser_length || m['Trouser Length'] || 45],
      ['ankle_round', m.ankle_round || m['Ankle Round'] || 23],
      ['across_chest', m.across_chest || m['Across Chest'] || 33],
      ['knee_round', m.knee_round || m['Knee Round'] || 36],
      ['across_back', m.across_back || 34],
      ['across_shoulder', m.across_shoulder || 38],
      ['elbow_round', m.elbow_round || 23],
      ['inseam', m.inseam || 86],
      ['trouser_waist', m.trouser_waist || 72],
      ['crotch_depth', m.crotch_depth || 26],
      ['bust_point', m.bust_point || 23],
      ['shoulder_to_bust', m.shoulder_to_bust || 25],
      // NEW morphs (34 total)
      ['back_waist_length', m.back_waist_length || 26],
      ['front_waist_length', m.front_waist_length || 26],
      ['high_bust', m.high_bust || 83],
      ['under_bust', m.under_bust || 73],
      ['armhole_round', m.armhole_round || 17],
      // Stomach form: driven directly by stomach slider (was incorrectly coupled to waist ratio)
      ['stomach_form', m.stomach || m['Stomach Round'] || 82],
      // Female-specific morphs (36 total for female)
      ['breast_size', m.breast_size !== undefined ? m.breast_size : 50],
      ['buttocks_size', m.buttocks_size !== undefined ? m.buttocks_size : 50],
    ];

    for (var i = 0; i < direct.length; i++) {
      var morphName = direct[i][0];
      var value = direct[i][1];
      var idx = e.morphNames.indexOf(morphName);
      if (idx >= 0) {
        e.morphInfluences[idx] = e.measurementToInfluence(value, idx);
      }
    }

    // shoulder_slope: use limits-based influence (lo=default=1 → 0 influence at default)
    if (m.shoulder_slope !== undefined) {
      var idx = e.morphNames.indexOf('shoulder_slope');
      if (idx >= 0) e.morphInfluences[idx] = e.measurementToInfluence(m.shoulder_slope, idx);
    }
  }

  _applyChildMappings(m) {
    var e = this.engine;
    var direct = [
      ['height', m.height || 120],
      ['neck_height', m.half_length || m.neckheight || 8],
      ['neck_circumference', m.neck || m['Neck Round'] || m.neck_round || 28],
      ['shoulders', m.shoulder || m['Shoulder'] || m.across_shoulder || 10],
      ['chest', m.chest || m['Chest Round'] || m.bust_round || 70],
      ['underbust', m.bust || m['Bust Round'] || m.bust_round || 60],
      ['upperarm_girth', m.bicep || m['Bicep Round'] || 20],
      ['lowerarm_length', m.sleeve_length || m['Sleeve Length'] || 18],
      ['wrist', m.wrist || m.wrist_round || m['Wrist Round'] || 11],
      ['waist', m.waist || m['Waist Round'] || 59],
      ['hip_height', m.waist_to_hip || m['Waist to Hip'] || 26],
      ['hips', m.hip || m['Hip Round'] || 73],
      ['thigh_girth', m.thigh || m['Thigh Round'] || 40],
      ['calf_girth', m.calf || m.calf_round || m['Calf Round'] || 23],
      ['lowerleg_length', m.trouser_length || m['Trouser Length'] || 39],
      ['ankle_round', m.ankle_round || m['Ankle Round'] || 18],
      ['across_chest', m.across_chest || m['Across Chest'] || 25],
      ['knee_round', m.knee_round || m['Knee Round'] || 25],
    ];

    for (var i = 0; i < direct.length; i++) {
      var morphName = direct[i][0];
      var value = direct[i][1];
      var idx = e.morphNames.indexOf(morphName);
      if (idx >= 0) {
        e.morphInfluences[idx] = e.measurementToInfluence(value, idx);
      }
    }

    // shoulder_slope: use limits-based influence (lo=default=1 → 0 influence at default)
    if (m.shoulder_slope !== undefined) {
      var idx = e.morphNames.indexOf('shoulder_slope');
      if (idx >= 0) e.morphInfluences[idx] = e.measurementToInfluence(m.shoulder_slope, idx);
    }
  }

  /**
   * Apply height scaling to match target height in cm.
   * Model coordinates are in decimeters (17.3 dm = 173cm).
   * X/Z ratios verified from MakeHuman height morph target data:
   *   Body: X/Y=0.33, Z/Y=0.22
   *   Head: X/Y=0.07, Z/Y=0.07
   */
  _applyHeightScaling(targetHeightCm, vertices) {
    var V = this.engine.vertCount;

    var yValues = new Float32Array(V);
    for (var i = 0; i < V; i++) {
      yValues[i] = vertices[i * 3 + 1];
    }
    var sorted = yValues.slice().sort();
    var bodyMinY = sorted[0];
    var bodyMaxY = sorted[V - 1];
    var bodyHeightDm = bodyMaxY - bodyMinY;

    if (bodyHeightDm <= 0) return;

    var bodyHeightCm = bodyHeightDm * 10;
    var heightScale = targetHeightCm / bodyHeightCm;

    // Scale all vertices relative to feet (minY stays fixed)
    for (var i = 0; i < V; i++) {
      var y = vertices[i * 3 + 1];
      vertices[i * 3 + 1] = bodyMinY + (y - bodyMinY) * heightScale;

      // Scale X/Z proportionally (33% X, 22% Z per MakeHuman data)
      var relY = (y - bodyMinY) / bodyHeightDm;
      var sx = 1.0 + (heightScale - 1.0) * 0.33 * relY;
      var sz = 1.0 + (heightScale - 1.0) * 0.22 * relY;
      vertices[i * 3]     *= sx;
      vertices[i * 3 + 2] *= sz;
    }
  }

  /* ===== MEASUREMENT EXTRACTION ===== */

  computeAllMeasurements(pos) {
    if (!pos) return {};
    var faceArr = this.engine.faces;
    var M = {};

    var pts = window.MAKEHUMAN_POINTS || {};
    var neckV = pts.neck || [];
    var chestV = pts.chest || [];
    var waistV = pts.waist || [];
    var stomachV = pts.stomach || [];
    var hipsV = pts.hips || [];
    var thighV = pts.thigh || [];
    var calfV = pts.calf || [];
    var bicepV = pts.bicep || [];
    var wristV = pts.wrist || [];
    var shoulderV = pts.shoulder || [];

    var self = this;
    var circ = function(verts, bw) {
      if (!verts || verts.length < 3) return 0;
      var band = self._computeBandVerts(pos, verts, bw || 0.03);
      return self._computeCircumference(pos, faceArr, band, bw || 0.03, verts);
    };

    var limbCirc = function(verts, bw) {
      if (!verts || verts.length < 3) return 0;
      var band = self._computeBandVerts(pos, verts, bw || 0.03);
      return self._circFromVerts(pos, band);
    };

    var xspan = function(verts) {
      if (!verts || verts.length === 0) return 0;
      var minX = Infinity, maxX = -Infinity;
      for (var i = 0; i < verts.length; i++) {
        var x = pos[verts[i] * 3];
        if (x < minX) minX = x;
        if (x > maxX) maxX = x;
      }
      return (maxX - minX) * 100;
    };

    var dist = function(vA, vB) {
      if (!vA || !vB || vA.length === 0 || vB.length === 0) return 0;
      var a = self._centroid(pos, vA);
      var b = self._centroid(pos, vB);
      var dx = a[0] - b[0], dy = a[1] - b[1], dz = a[2] - b[2];
      return Math.sqrt(dx * dx + dy * dy + dz * dz) * 100;
    };

    // Direct measurements
    M['Shoulder'] = Math.round(xspan(shoulderV) * 10) / 10;
    M['Chest Round'] = Math.round(circ(chestV, 0.04) * 10) / 10;
    M['Bust Round'] = M['Chest Round'];
    M['Waist Round'] = Math.round(circ(waistV, 0.03) * 10) / 10;
    M['Stomach Round'] = stomachV.length > 0 ? Math.round(circ(stomachV, 0.04) * 10) / 10 : M['Waist Round'];
    M['Hip Round'] = Math.round(circ(hipsV, 0.04) * 10) / 10;
    M['Neck Round'] = Math.round(circ(neckV, 0.03) * 10) / 10;
    M['Thigh Round'] = Math.round(limbCirc(thighV, 0.05) * 10) / 10;
    M['Calf Round'] = Math.round(limbCirc(calfV, 0.04) * 10) / 10;
    M['Bicep Round'] = Math.round(limbCirc(bicepV, 0.04) * 10) / 10;
    M['Wrist Round'] = Math.round(limbCirc(wristV, 0.03) * 10) / 10;

    // Derived measurements
    M['Across Chest'] = Math.round(M['Shoulder'] * 0.96 * 10) / 10;
    M['Across Back'] = Math.round(M['Shoulder'] * 0.92 * 10) / 10;
    M['Knee Round'] = Math.round(M['Thigh Round'] * 0.73 * 10) / 10;
    M['Ankle Round'] = Math.round(M['Calf Round'] * 0.44 * 10) / 10;
    M['Elbow Round'] = Math.round(M['Bicep Round'] * 0.79 * 10) / 10;
    M['Upper Hip'] = Math.round(M['Hip Round'] * 0.92 * 10) / 10;
    M['Armhole Round'] = Math.round(M['Shoulder'] * 0.45 * 10) / 10;
    M['High Bust'] = Math.round(M['Bust Round'] * 0.85 * 10) / 10;
    M['Under Bust'] = Math.round(M['Bust Round'] * 0.75 * 10) / 10;
    M['Trouser Waist'] = M['Waist Round'];

    // Length measurements (from vertex landmarks)
    M['Half Length'] = neckV.length > 0 && waistV.length > 0 ?
      Math.round(dist(neckV, waistV) * 10) / 10 : 28;
    M['Full Top Length'] = neckV.length > 0 && hipsV.length > 0 ?
      Math.round(dist(neckV, hipsV) * 10) / 10 : 55;
    M['Back Waist Length'] = M['Half Length'];
    M['Front Waist Length'] = M['Half Length'];
    M['Neck to Waist'] = M['Half Length'];
    M['Shoulder to Waist'] = M['Half Length'];
    M['Waist to Hip'] = waistV.length > 0 && hipsV.length > 0 ?
      Math.round(dist(waistV, hipsV) * 10) / 10 : 28;
    M['Sleeve Length'] = shoulderV.length > 0 && wristV.length > 0 ?
      Math.round(dist(shoulderV, wristV) * 10) / 10 : 62;
    M['Trouser Length'] = waistV.length > 0 ?
      Math.round(dist(waistV, calfV.length > 0 ? calfV : thighV) * 10) / 10 : 116;
    M['Inseam'] = Math.round(M['Trouser Length'] * 0.78 * 10) / 10;
    M['Crotch Depth'] = M['Waist to Hip'];

    M['Bust Point'] = Math.round(M['Half Length'] * 0.5 * 10) / 10;
    M['Shoulder to Bust Point'] = Math.round(M['Bust Point'] * 1.1 * 10) / 10;
    M['Shoulder to Under Bust'] = Math.round(M['Bust Point'] * 1.3 * 10) / 10;

    return M;
  }

  /* ===== GEOMETRY HELPERS ===== */

  _centroid(pos, verts) {
    if (!verts || verts.length === 0) return [0, 0, 0];
    var sx = 0, sy = 0, sz = 0;
    for (var i = 0; i < verts.length; i++) {
      sx += pos[verts[i] * 3];
      sy += pos[verts[i] * 3 + 1];
      sz += pos[verts[i] * 3 + 2];
    }
    return [sx / verts.length, sy / verts.length, sz / verts.length];
  }

  _convexHull2D(points) {
    var pts = points.slice().sort(function(a, b) { return a[0] - b[0] || a[1] - b[1]; });
    var n = pts.length;
    if (n <= 1) return pts;

    var cross = function(O, A, B) {
      return (A[0] - O[0]) * (B[1] - O[1]) - (A[1] - O[1]) * (B[0] - O[0]);
    };

    var lower = [];
    for (var i = 0; i < n; i++) {
      while (lower.length >= 2 && cross(lower[lower.length - 2], lower[lower.length - 1], pts[i]) <= 0) lower.pop();
      lower.push(pts[i]);
    }

    var upper = [];
    for (var i = n - 1; i >= 0; i--) {
      while (upper.length >= 2 && cross(upper[upper.length - 2], upper[upper.length - 1], pts[i]) <= 0) upper.pop();
      upper.push(pts[i]);
    }

    lower.pop();
    upper.pop();
    return lower.concat(upper);
  }

  _computeBandVerts(pos, verts, bandW) {
    if (!verts || verts.length === 0) return [];
    var sumY = 0;
    for (var i = 0; i < verts.length; i++) {
      sumY += pos[verts[i] * 3 + 1];
    }
    var centroidY = sumY / verts.length;

    var result = [];
    for (var i = 0; i < verts.length; i++) {
      if (Math.abs(pos[verts[i] * 3 + 1] - centroidY) <= bandW) {
        result.push(verts[i]);
      }
    }
    return result.length >= 3 ? result : verts;
  }

  _computeCircumference(pos, faceArr, verts, bandW, partVerts) {
    if (!verts || verts.length < 3 || !faceArr) return 0;
    var intersections = [];
    var fCount = faceArr.length / 3;
    var centroidY = 0;
    for (var i = 0; i < verts.length; i++) centroidY += pos[verts[i] * 3 + 1];
    centroidY /= verts.length;

    var partSet = partVerts && partVerts.length > 0 ? new Set(partVerts) : null;

    for (var f = 0; f < fCount; f++) {
      var i0 = faceArr[f * 3], i1 = faceArr[f * 3 + 1], i2 = faceArr[f * 3 + 2];
      if (partSet) {
        if (!partSet.has(i0) && !partSet.has(i1) && !partSet.has(i2)) continue;
      }
      var edges = [[i0, i1], [i1, i2], [i2, i0]];
      for (var e = 0; e < 3; e++) {
        var a = edges[e][0], b = edges[e][1];
        var ya = pos[a * 3 + 1], yb = pos[b * 3 + 1];
        if ((ya - centroidY) * (yb - centroidY) < 0) {
          var t = (centroidY - ya) / (yb - ya);
          intersections.push([
            pos[a * 3] + t * (pos[b * 3] - pos[a * 3]),
            pos[a * 3 + 2] + t * (pos[b * 3 + 2] - pos[a * 3 + 2])
          ]);
        }
      }
    }

    if (intersections.length < 3) return 0;
    var hull = this._convexHull2D(intersections);
    if (hull.length < 3) return 0;
    var perim = 0;
    for (var i = 0; i < hull.length; i++) {
      var j = (i + 1) % hull.length;
      var dx = hull[j][0] - hull[i][0], dz = hull[j][1] - hull[i][1];
      perim += Math.sqrt(dx * dx + dz * dz);
    }
    return perim;
  }

  _circFromVerts(pos, verts) {
    if (!verts || verts.length < 3) return 0;
    var pts = [];
    for (var i = 0; i < verts.length; i++) {
      pts.push([pos[verts[i] * 3], pos[verts[i] * 3 + 2]]);
    }
    var hull = this._convexHull2D(pts);
    if (hull.length < 3) return 0;
    var perim = 0;
    for (var i = 0; i < hull.length; i++) {
      var j = (i + 1) % hull.length;
      var dx = hull[j][0] - hull[i][0], dz = hull[j][1] - hull[i][1];
      perim += Math.sqrt(dx * dx + dz * dz);
    }
    return perim;
  }

  /* ===== SCENE MANAGEMENT ===== */

  _groundMesh() {
    if (!this.mesh) return;
    this.mesh.geometry.computeBoundingBox();
    var bb = this.mesh.geometry.boundingBox;
    this.mesh.position.y = -bb.min.y;
  }

  _updateCamera() {
    var pos = new THREE.Vector3();
    pos.x = this.spherical.radius * Math.sin(this.spherical.phi) * Math.sin(this.spherical.theta);
    pos.y = this.spherical.radius * Math.cos(this.spherical.phi);
    pos.z = this.spherical.radius * Math.sin(this.spherical.phi) * Math.cos(this.spherical.theta);
    this.camera.position.copy(this.target).add(pos);
    this.camera.lookAt(this.target);
  }

  _resize() {
    if (!this.renderer || !this.camera) return;
    var w = window.innerWidth, h = window.innerHeight;
    this.renderer.setSize(w, h);
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
  }

  _initControls(canvas) {
    var self = this;
    canvas.addEventListener('mousedown', function(e) {
      self.mouseDown = true;
      self.lastMouse.x = e.clientX;
      self.lastMouse.y = e.clientY;
    });
    canvas.addEventListener('mousemove', function(e) {
      if (!self.mouseDown) return;
      var dx = e.clientX - self.lastMouse.x;
      var dy = e.clientY - self.lastMouse.y;
      self.spherical.theta -= dx * 0.005;
      self.spherical.phi = Math.max(0.1, Math.min(Math.PI - 0.1, self.spherical.phi + dy * 0.005));
      self.lastMouse.x = e.clientX;
      self.lastMouse.y = e.clientY;
      self._updateCamera();
    });
    canvas.addEventListener('mouseup', function() { self.mouseDown = false; });
    canvas.addEventListener('mouseleave', function() { self.mouseDown = false; });
    canvas.addEventListener('wheel', function(e) {
      e.preventDefault();
      self.spherical.radius = Math.max(15, Math.min(80, self.spherical.radius + e.deltaY * 0.02));
      self._updateCamera();
    }, { passive: false });

    var lastTouch = null;
    canvas.addEventListener('touchstart', function(e) {
      if (e.touches.length === 1) {
        lastTouch = { x: e.touches[0].clientX, y: e.touches[0].clientY };
      }
    });
    canvas.addEventListener('touchmove', function(e) {
      e.preventDefault();
      if (e.touches.length === 1 && lastTouch) {
        var dx = e.touches[0].clientX - lastTouch.x;
        var dy = e.touches[0].clientY - lastTouch.y;
        self.spherical.theta -= dx * 0.005;
        self.spherical.phi = Math.max(0.1, Math.min(Math.PI - 0.1, self.spherical.phi + dy * 0.005));
        lastTouch = { x: e.touches[0].clientX, y: e.touches[0].clientY };
        self._updateCamera();
      }
    }, { passive: false });
    canvas.addEventListener('touchend', function() { lastTouch = null; });
  }

  // ========== VERTEX DISPLACEMENT HELPERS ==========

  _computeRingCircumference(verts, indices) {
    if (!indices || indices.length < 3) return 0;
    var points = [];
    for (var i = 0; i < indices.length; i++) {
      var idx = indices[i];
      if (idx < verts.length / 3) {
        points.push([verts[idx * 3], verts[idx * 3 + 2]]);
      }
    }
    if (points.length < 3) return 0;
    var cx = 0, cy = 0;
    for (var i = 0; i < points.length; i++) { cx += points[i][0]; cy += points[i][1]; }
    cx /= points.length; cy /= points.length;
    points.sort(function(a, b) {
      return Math.atan2(a[1] - cy, a[0] - cx) - Math.atan2(b[1] - cy, b[0] - cx);
    });
    var perim = 0;
    for (var i = 0; i < points.length; i++) {
      var j = (i + 1) % points.length;
      var dx = points[j][0] - points[i][0];
      var dy = points[j][1] - points[i][1];
      perim += Math.sqrt(dx * dx + dy * dy);
    }
    return perim * 10;
  }

  _radialScale(verts, indices, targetCm) {
    if (!indices || indices.length < 3) return;
    var cx = 0, cz = 0;
    for (var i = 0; i < indices.length; i++) {
      var idx = indices[i];
      cx += verts[idx * 3]; cz += verts[idx * 3 + 2];
    }
    cx /= indices.length; cz /= indices.length;
    var currentCm = this._computeRingCircumference(verts, indices);
    if (currentCm < 1) return;
    var scale = targetCm / currentCm;
    for (var i = 0; i < indices.length; i++) {
      var idx = indices[i];
      verts[idx * 3] = cx + (verts[idx * 3] - cx) * scale;
      verts[idx * 3 + 2] = cz + (verts[idx * 3 + 2] - cz) * scale;
    }
  }

  _xScaleRegion(verts, indices, targetCm) {
    if (!indices || indices.length < 2) return;
    var minX = Infinity, maxX = -Infinity;
    for (var i = 0; i < indices.length; i++) {
      var idx = indices[i];
      var x = Math.abs(verts[idx * 3]);
      if (x < minX) minX = x;
      if (x > maxX) maxX = x;
    }
    var currentWidth = (maxX - minX) * 2 * 10;
    if (currentWidth < 1) return;
    var scale = targetCm / currentWidth;
    for (var i = 0; i < indices.length; i++) {
      var idx = indices[i];
      verts[idx * 3] *= scale;
    }
  }

  _yStretchZone(verts, indices, targetCm) {
    if (!indices || indices.length < 2) return;
    var minY = Infinity, maxY = -Infinity;
    for (var i = 0; i < indices.length; i++) {
      var idx = indices[i];
      var y = verts[idx * 3 + 1];
      if (y < minY) minY = y;
      if (y > maxY) maxY = y;
    }
    var currentHeight = (maxY - minY) * 10;
    if (currentHeight < 1) return;
    var scale = targetCm / currentHeight;
    var midY = (minY + maxY) / 2;
    for (var i = 0; i < indices.length; i++) {
      var idx = indices[i];
      verts[idx * 3 + 1] = midY + (verts[idx * 3 + 1] - midY) * scale;
    }
  }

  _applyVertexDisplacements() {
    if (!this.engine || !this.engine.vertices) return;
    var verts = this.engine.vertices;
    var m = this._lastMeasurements || {};
    var points = window.MAKEHUMAN_POINTS || {};

    // Only for sliders WITHOUT morph targets.
    // Morphs handle: chest, waist, hip, neck, shoulder, bicep/wrist, thigh, calf,
    // ankle, knee, across_chest, arm_length, lowerleg_length, hip_height, neckheight, stomach_form

    // Circumference (no morph)
    if (m.elbow_round != null && points.elbow && points.elbow.length >= 3)
      this._radialScale(verts, points.elbow, m.elbow_round);
    if (m.upper_hip != null && points.upper_hip && points.upper_hip.length >= 3)
      this._radialScale(verts, points.upper_hip, m.upper_hip);
    if (m.high_bust != null && points.high_bust && points.high_bust.length >= 3)
      this._radialScale(verts, points.high_bust, m.high_bust);
    if (m.under_bust != null && points.under_bust && points.under_bust.length >= 3)
      this._radialScale(verts, points.under_bust, m.under_bust);
    if (m.bust_point != null && points.bust_point && points.bust_point.length >= 3)
      this._radialScale(verts, points.bust_point, m.bust_point);
    if (m.armhole_round != null && points.armhole && points.armhole.length >= 3)
      this._radialScale(verts, points.armhole, m.armhole_round);
    if (m.trouser_waist != null && points.waist && points.waist.length >= 3)
      this._radialScale(verts, points.waist, m.trouser_waist);

    // Width (no morph)
    if (m.across_back != null && points.chest && points.chest.length >= 2)
      this._xScaleRegion(verts, points.chest, m.across_back);
    if (m.across_shoulder != null && points.shoulder && points.shoulder.length >= 2)
      this._xScaleRegion(verts, points.shoulder, m.across_shoulder);

    // Length (no morph)
    if (m.back_waist_length != null && points.waist && points.waist.length >= 2)
      this._yStretchZone(verts, points.waist, m.back_waist_length);
    if (m.front_waist_length != null && points.stomach && points.stomach.length >= 2)
      this._yStretchZone(verts, points.stomach, m.front_waist_length);
    if (m.neck_to_waist != null && points.chest && points.chest.length >= 2)
      this._yStretchZone(verts, points.chest, m.neck_to_waist);
    if (m.crotch_depth != null && points.hips && points.hips.length >= 2)
      this._yStretchZone(verts, points.hips, m.crotch_depth);
    if (m.inseam != null && points.thigh && points.thigh.length >= 2)
      this._yStretchZone(verts, points.thigh, m.inseam);
    if (m.shoulder_to_bust != null && points.bust_point && points.bust_point.length >= 2)
      this._yStretchZone(verts, points.bust_point, m.shoulder_to_bust);
  }

  // ===== CLOTH DRAPING SYSTEM =====

  /**
   * Initialize the body collision proxy (call after engine is ready and mesh is created)
   */
  _initBodyCollider() {
    if (!this.engine || !this.engine.vertices) return;
    var verts = this.engine.vertices;
    var faces = this.engine.faces;
    var bodyVerts = new Float32Array(verts.length);
    bodyVerts.set(verts);
    var bodyIndices = new Uint32Array(faces.length);
    bodyIndices.set(faces);
    // Body vertices are in decimeters (dm). Convert to meters for physics: dm * 0.1 = m
    for (var i = 0; i < bodyVerts.length; i++) bodyVerts[i] *= 0.1;
    this._bodyColliderVerts = bodyVerts;
    this._bodyCollider = new XPBD.BodyCollider(bodyVerts, bodyIndices);
    this._morphsDirty = true;
  }

  /**
   * Get body bounding box for garment scaling
   */
  _getBodyBoundingBox() {
    if (!this.engine || !this.engine.vertices) return { min: { x: 0, y: 0, z: 0 }, max: { x: 1, y: 1.8, z: 1 } };
    var verts = this.engine.vertices;
    var minX = Infinity, minY = Infinity, minZ = Infinity;
    var maxX = -Infinity, maxY = -Infinity, maxZ = -Infinity;
    for (var i = 0; i < verts.length; i += 3) {
      var x = verts[i] * 0.1, y = verts[i + 1] * 0.1, z = verts[i + 2] * 0.1;
      if (x < minX) minX = x; if (x > maxX) maxX = x;
      if (y < minY) minY = y; if (y > maxY) maxY = y;
      if (z < minZ) minZ = z; if (z > maxZ) maxZ = z;
    }
    return { min: { x: minX, y: minY, z: minZ }, max: { x: maxX, y: maxY, z: maxZ } };
  }

  /**
   * Load a garment GLB with morph targets for measurement-based draping.
   * @param {string} glbUrl - URL of the morphed garment GLB
   * @returns {Promise<{ok: boolean, error?: string}>}
   */
  async loadGarment(glbUrl) {
    this.removeGarment();
    if (!glbUrl) return { ok: true };

    try {
      var loaded = await this.garmentMorphCtrl.load(glbUrl, this.scene);
      if (loaded) {
        // Sync position with body mesh
        this.garmentMorphCtrl.syncPosition(this.mesh.position);
        // Apply current measurements if available
        if (this._lastMeasurements) {
          this.garmentMorphCtrl.updateFromMeasurements(this._lastMeasurements);
        }
      }
      return { ok: true };
    } catch (err) {
      console.error('[Cloth] Failed:', err);
      return { ok: false, error: err.message || 'Failed to load GLB' };
    }
  }

  /**
   * Remove current garment and stop cloth simulation
   */
  removeGarment() {
    this.garmentMorphCtrl.dispose(this.scene);
    if (this._clothRenderMesh) {
      this.scene.remove(this._clothRenderMesh);
      if (this._clothRenderMesh.geometry) this._clothRenderMesh.geometry.dispose();
      if (this._clothRenderMesh.material) this._clothRenderMesh.material.dispose();
      this._clothRenderMesh = null;
    }
    this._clothSolver = null;
    this._clothMeshData = null;
  }

  /**
   * Set cloth simulation quality
   * @param {'low'|'medium'|'high'} preset
   */
  setClothQuality(preset) {
    this._clothQualityPreset = preset;
    if (this._clothSolver) {
      var params = this._getClothQualityParams();
      this._clothSolver.setSolverIterations(params.substeps, params.iterations);
      this._clothSolver.params.damping = params.damping;
      this._clothSolver.params.selfCollisionRadius = params.selfCollisionRadius;
      this._clothSolver.params.selfCollisionStiffness = params.selfCollisionStiffness;
    }
  }

  _getClothQualityParams() {
    var presets = {
      low:    { gravity: 9.8, damping: 0.99, substeps: 1, iterations: 4, dt: 1/60, groundY: -1.0, maxVelocity: 8, selfCollisionRadius: 0, selfCollisionStiffness: 0, sewingTime: 0 },
      medium: { gravity: 9.8, damping: 0.99, substeps: 2, iterations: 6, dt: 1/60, groundY: -1.0, maxVelocity: 8, selfCollisionRadius: 0, selfCollisionStiffness: 0, sewingTime: 0 },
      high:   { gravity: 9.8, damping: 0.99, substeps: 3, iterations: 10, dt: 1/60, groundY: -1.0, maxVelocity: 8, selfCollisionRadius: 0.005, selfCollisionStiffness: 0.5, sewingTime: 0 },
    };
    return presets[this._clothQualityPreset || 'medium'];
  }

  /**
   * Called each frame from _animate() — steps cloth solver and updates render mesh
   */
  _updateCloth() {
    if (!this._clothSolver || !this._clothMeshData) return;

    // Refit body BVH if morphs changed
    if (this._morphsDirty && this._bodyCollider && this.engine && this.engine.vertices) {
      var verts = this.engine.vertices;
      for (var i = 0; i < this._bodyColliderVerts.length && i < verts.length; i++) {
        this._bodyColliderVerts[i] = verts[i] * 0.1; // dm → m
      }
      this._bodyCollider.refit();
      this._morphsDirty = false;
    }

    // Build collision snapshot
    var snapshot = this._bodyCollider ? this._bodyCollider.buildSnapshot() : null;

    // Step solver (solver works in meters)
    var frame = this._clothSolver.step(snapshot);

    // Convert solver positions from meters to scene units (cm) for rendering
    var posAttr = this._clothRenderMesh.geometry.attributes.position;
    var src = frame.positions;
    var dst = posAttr.array;
    for (var i = 0; i < src.length; i++) {
      dst[i] = src[i] * 10; // m → dm (scene units)
    }
    posAttr.needsUpdate = true;
    this._clothRenderMesh.geometry.computeVertexNormals();
    this._clothRenderMesh.geometry.computeBoundingSphere();
  }

  // ===== END CLOTH DRAPING SYSTEM =====

  _animate() {
    this.animId = requestAnimationFrame(this._animate.bind(this));
    this._updateCloth();
    this.renderer.render(this.scene, this.camera);
  }

  dispose() {
    this.removeGarment();
    if (this.animId) cancelAnimationFrame(this.animId);
    if (this.renderer) this.renderer.dispose();
  }
}

window.MakeHumanBodyVisualizer = MakeHumanBodyVisualizer;
