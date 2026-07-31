/**
 * Body Visualizer — Three.js interactive SMPL body shape viewer.
 * SMPL betas for natural mesh; height via Y-scaling (head excluded).
 * Two-layer pipeline: MLP betas + per-measurement displacement correction.
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
    this._partSets = null;
  }

  async init(canvasId) {
    var canvas = document.getElementById(canvasId);
    if (!canvas) { console.error('Canvas not found:', canvasId); return; }

    this.smpl = new SMPLShapeEngine();
    await this.smpl.init('');

    this._initPartSets();

    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x0B0B0C);

    this.camera = new THREE.PerspectiveCamera(35, 1, 0.1, 100);
    this._updateCamera();

    this.renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this._resize();
    window.addEventListener('resize', this._resize.bind(this));

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

    var grid = new THREE.GridHelper(4, 20, 0x333333, 0x222222);
    grid.position.y = 0;
    this.scene.add(grid);

    // Build face index array (SMPL faces are 0-indexed uint32)
    var faces = this.smpl.faces;

    // Initial body shape — ALL measurements provided for UI, but only 12 independent ones feed the MLP
    var defaultMeas = {
      chest: 96, waist: 84, hip: 96, thigh: 55, bicep: 32, neck: 39,
      shoulder: 43, half_length: 28, waist_to_hip: 28, trouser_length: 116,
      sleeve_length: 62, bust_point: 7,
      // Derived/display-only (not fed to MLP):
      bust_round: 96, stomach: 82, knee_round: 38, calf_round: 36, ankle_round: 24,
      elbow_round: 25, wrist_round: 17, upper_hip: 91, armhole_round: 19,
      across_shoulder: 43, across_back: 39, across_chest: 40,
      full_top_length: 55, back_waist_length: 28, front_waist_length: 28,
      neck_to_waist: 28, shoulder_to_waist: 28, crotch_depth: 28,
      trouser_waist: 84, inseam: 91, high_bust: 85, under_bust: 76,
      shoulder_to_bust: 8, shoulder_to_under_bust: 9,
      height: 175
    };
    this.currentBetas = this.smpl.measurementsToBetas(defaultMeas, this.gender);
    var vertices = this.smpl.computeBodyShape(this.currentBetas);

    // Diagnostic: log betas and vertex ranges
    console.log('[BodyVis] Betas:', Array.from(this.currentBetas).map(function(b) { return b.toFixed(3); }));
    var xmin = Infinity, xmax = -Infinity, ymin = Infinity, ymax = -Infinity, zmin = Infinity, zmax = -Infinity;
    for (var i = 0; i < vertices.length; i += 3) {
      if (vertices[i] < xmin) xmin = vertices[i];
      if (vertices[i] > xmax) xmax = vertices[i];
      if (vertices[i+1] < ymin) ymin = vertices[i+1];
      if (vertices[i+1] > ymax) ymax = vertices[i+1];
      if (vertices[i+2] < zmin) zmin = vertices[i+2];
      if (vertices[i+2] > zmax) zmax = vertices[i+2];
    }
    console.log('[BodyVis] Vertices X=[' + xmin.toFixed(3) + ',' + xmax.toFixed(3) + '] Y=[' + ymin.toFixed(3) + ',' + ymax.toFixed(3) + '] Z=[' + zmin.toFixed(3) + ',' + zmax.toFixed(3) + ']');
    console.log('[BodyVis] Height: ' + ((ymax - ymin) * 100).toFixed(1) + 'cm');

    var geometry = this._buildGeometry(vertices, faces);
    var material = new THREE.MeshStandardMaterial({
      color: 0xD4A574,
      roughness: 0.6,
      metalness: 0.05,
      flatShading: false,
      side: THREE.DoubleSide,
    });

    this.mesh = new THREE.Mesh(geometry, material);
    this._groundMesh();
    this.scene.add(this.mesh);

    this._initControls(canvas);
    this._animate();

    var loading = document.getElementById('visLoading');
    if (loading) loading.style.display = 'none';

    console.log('[BodyVis] Ready: ' + this.mesh.geometry.attributes.position.count + ' verts, ' +
      (this.mesh.geometry.index ? (this.mesh.geometry.index.count / 3) + ' tris' : 'no index'));
  }

  _initPartSets() {
    if (window.SMPL_PARTS) {
      this._partSets = {};
      for (var key in window.SMPL_PARTS) {
        this._partSets[key] = new Set(window.SMPL_PARTS[key]);
      }
    }
  }

  _buildGeometry(vertexData, faceIndices) {
    var geometry = new THREE.BufferGeometry();
    var positions = new Float32Array(vertexData);
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    if (faceIndices && faceIndices.length > 0) {
      var idx = new Uint32Array(faceIndices);
      geometry.setIndex(new THREE.BufferAttribute(idx, 1));
      console.log('[BodyVis] Indexed: ' + (idx.length / 3) + ' triangles');
    } else {
      console.error('[BodyVis] No face indices!');
    }

    geometry.computeVertexNormals();
    return geometry;
  }

  _groundMesh() {
    if (!this.mesh) return;
    this.mesh.geometry.computeBoundingBox();
    var bbox = this.mesh.geometry.boundingBox;
    this.mesh.position.set(0, -bbox.min.y, 0);
  }

  _updateCamera() {
    if (!this.camera) return;
    var theta = this.spherical.theta;
    var phi = this.spherical.phi;
    var r = this.spherical.radius;
    this.camera.position.set(
      this.target.x + r * Math.sin(phi) * Math.sin(theta),
      this.target.y + r * Math.cos(phi),
      this.target.z + r * Math.sin(phi) * Math.cos(theta)
    );
    this.camera.lookAt(this.target);
  }

  _initControls(canvas) {
    var self = this;
    canvas.addEventListener('mousedown', function(e) {
      self.mouseDown = true;
      self.lastMouse = { x: e.clientX, y: e.clientY };
      self.isRotating = false;
    });
    window.addEventListener('mouseup', function() { self.mouseDown = false; });
    window.addEventListener('mousemove', function(e) {
      if (!self.mouseDown) return;
      var dx = e.clientX - self.lastMouse.x;
      var dy = e.clientY - self.lastMouse.y;
      self.spherical.theta -= dx * 0.005;
      self.spherical.phi = Math.max(0.3, Math.min(Math.PI - 0.3, self.spherical.phi - dy * 0.005));
      self.lastMouse = { x: e.clientX, y: e.clientY };
      self._updateCamera();
    });

    canvas.addEventListener('wheel', function(e) {
      e.preventDefault();
      self.spherical.radius = Math.max(1.2, Math.min(6, self.spherical.radius + e.deltaY * 0.002));
      self._updateCamera();
    }, { passive: false });

    var touchStart = null;
    var pinchDist = null;
    canvas.addEventListener('touchstart', function(e) {
      if (e.touches.length === 1) {
        touchStart = { x: e.touches[0].clientX, y: e.touches[0].clientY };
        self.isRotating = false;
      } else if (e.touches.length === 2) {
        pinchDist = Math.hypot(
          e.touches[0].clientX - e.touches[1].clientX,
          e.touches[0].clientY - e.touches[1].clientY
        );
      }
    });
    canvas.addEventListener('touchmove', function(e) {
      e.preventDefault();
      if (e.touches.length === 1 && touchStart) {
        var dx = e.touches[0].clientX - touchStart.x;
        var dy = e.touches[0].clientY - touchStart.y;
        self.spherical.theta -= dx * 0.005;
        self.spherical.phi = Math.max(0.3, Math.min(Math.PI - 0.3, self.spherical.phi - dy * 0.005));
        touchStart = { x: e.touches[0].clientX, y: e.touches[0].clientY };
        self._updateCamera();
      } else if (e.touches.length === 2 && pinchDist !== null) {
        var newDist = Math.hypot(
          e.touches[0].clientX - e.touches[1].clientX,
          e.touches[0].clientY - e.touches[1].clientY
        );
        self.spherical.radius = Math.max(1.2, Math.min(6, self.spherical.radius * (pinchDist / newDist)));
        pinchDist = newDist;
        self._updateCamera();
      }
    }, { passive: false });
  }

  _resize() {
    if (!this.renderer || !this.camera) return;
    var canvas = this.renderer.domElement;
    var parent = canvas.parentElement;
    if (!parent) return;
    var w = parent.clientWidth;
    var h = parent.clientHeight;
    canvas.width = w * Math.min(window.devicePixelRatio, 2);
    canvas.height = h * Math.min(window.devicePixelRatio, 2);
    canvas.style.width = w + 'px';
    canvas.style.height = h + 'px';
    this.renderer.setSize(w, h);
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
  }

  _animate() {
    var self = this;
    this.animId = requestAnimationFrame(function() { self._animate(); });
    if (this.isRotating) {
      this.spherical.theta += 0.003;
      this._updateCamera();
    }
    this.renderer.render(this.scene, this.camera);
  }

  /**
   * Two-layer update: MLP betas → mesh → weighted height scaling.
   */
  updateFromMeasurements(measurements) {
    if (!this.smpl || !this.smpl.ready) {
      console.warn('[BodyVis] updateFromMeasurements: smpl not ready');
      return;
    }

    var targetHeightCm = measurements.height || 175;

    this.currentBetas = this.smpl.measurementsToBetas(measurements, this.gender);
    var vertices = this.smpl.computeBodyShape(this.currentBetas);

    if (!this.mesh) return;
    var pos = this.mesh.geometry.attributes.position;

    for (var i = 0; i < vertices.length; i++) {
      pos.array[i] = vertices[i];
    }

    // Height scaling with weighted neck transition
    var headSet = this._partSets['head'];
    var neckSet = this._partSets['neck'];
    var minY = Infinity, maxY = -Infinity;
    for (var i = 0; i < pos.count; i++) {
      if (headSet.has(i) || neckSet.has(i)) continue;
      var y = pos.array[i * 3 + 1];
      if (y < minY) minY = y;
      if (y > maxY) maxY = y;
    }
    var actualHeightM = maxY - minY;
    var targetHeightM = targetHeightCm / 100;
    var heightScale = actualHeightM > 0 ? targetHeightM / actualHeightM : 1.0;

    // Compute neck Y range for weighted scaling
    var neckMinY = Infinity, neckMaxY = -Infinity;
    for (var vi of neckSet) {
      var ny = pos.array[vi * 3 + 1];
      if (ny < neckMinY) neckMinY = ny;
      if (ny > neckMaxY) neckMaxY = ny;
    }
    var neckRange = neckMaxY - neckMinY;

    for (var i = 0; i < pos.count; i++) {
      if (headSet.has(i)) {
        continue;
      } else if (neckSet.has(i)) {
        var weight = neckRange > 0.001 ? (neckMaxY - pos.array[i * 3 + 1]) / neckRange : 0.5;
        pos.array[i * 3 + 1] *= 1.0 + (heightScale - 1.0) * weight;
      } else {
        pos.array[i * 3 + 1] *= heightScale;
      }
    }

    this.mesh.geometry.computeVertexNormals();

    pos.needsUpdate = true;
    this._groundMesh();

    return {};
  }

  _getPartSet() {
    var combined = new Set();
    if (!this._partSets) return combined;
    for (var i = 0; i < arguments.length; i++) {
      var s = this._partSets[arguments[i]];
      if (s) for (var v of s) combined.add(v);
    }
    return combined;
  }

  setGender(gender) {
    this.gender = gender;
  }

  /* ===== MEASUREMENT EXTRACTION ===== */

  _getPartVerts(name) {
    if (this._partSets && this._partSets[name]) return Array.from(this._partSets[name]);
    if (window.SMPL_PARTS && window.SMPL_PARTS[name]) return window.SMPL_PARTS[name];
    if (window.CUSTOM_BODY_POINTS) {
      var key = Object.keys(window.CUSTOM_BODY_POINTS).find(function(k) {
        return k.toLowerCase().replace(/\s+/g, '') === name.toLowerCase().replace(/\s+/g, '');
      });
      if (key) return window.CUSTOM_BODY_POINTS[key];
    }
    return [];
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

  _computeCircumference(pos, faceArr, verts, planeY, bandW, partVerts) {
    if (!verts || verts.length < 3 || !faceArr) return 0;
    var intersections = [];
    var fCount = faceArr.length / 3;
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
        if ((ya - planeY) * (yb - planeY) < 0) {
          var t = (planeY - ya) / (yb - ya);
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
    return perim * 100;
  }

  _computeBandVerts(pos, verts, planeY, bandW) {
    if (!verts || verts.length === 0) return [];
    var result = [];
    for (var vi = 0; vi < verts.length; vi++) {
      if (Math.abs(pos[verts[vi] * 3 + 1] - planeY) <= bandW) result.push(verts[vi]);
    }
    return result.length >= 4 ? result : verts;
  }

  _centroidY(pos, verts) {
    if (!verts || verts.length === 0) return 0;
    var s = 0;
    for (var vi = 0; vi < verts.length; vi++) s += pos[verts[vi] * 3 + 1];
    return s / verts.length;
  }

  _centroid(pos, verts) {
    if (!verts || verts.length === 0) return [0, 0, 0];
    var sx = 0, sy = 0, sz = 0;
    for (var vi = 0; vi < verts.length; vi++) {
      sx += pos[verts[vi] * 3];
      sy += pos[verts[vi] * 3 + 1];
      sz += pos[verts[vi] * 3 + 2];
    }
    return [sx / verts.length, sy / verts.length, sz / verts.length];
  }

  _dist(pos, vertsA, vertsB) {
    var a = this._centroid(pos, vertsA);
    var b = this._centroid(pos, vertsB);
    var dx = a[0] - b[0], dy = a[1] - b[1], dz = a[2] - b[2];
    return Math.sqrt(dx * dx + dy * dy + dz * dz) * 100;
  }

  _xSpan(pos, verts) {
    if (!verts || verts.length === 0) return 0;
    var minX = Infinity, maxX = -Infinity;
    for (var vi = 0; vi < verts.length; vi++) {
      var x = pos[verts[vi] * 3];
      if (x < minX) minX = x;
      if (x > maxX) maxX = x;
    }
    return (maxX - minX) * 100;
  }

  _circFromVerts(pos, verts, proj) {
    if (!verts || verts.length < 3) return 0;
    var pts = [];
    for (var vi = 0; vi < verts.length; vi++) {
      if (proj === 'yz') pts.push([pos[verts[vi] * 3 + 1], pos[verts[vi] * 3 + 2]]);
      else pts.push([pos[verts[vi] * 3], pos[verts[vi] * 3 + 2]]);
    }
    var hull = this._convexHull2D(pts);
    if (hull.length < 3) return 0;
    var perim = 0;
    for (var i = 0; i < hull.length; i++) {
      var j = (i + 1) % hull.length;
      var dx = hull[j][0] - hull[i][0], dz = hull[j][1] - hull[i][1];
      perim += Math.sqrt(dx * dx + dz * dz);
    }
    return perim * 100;
  }

  computeAllMeasurements(pos) {
    if (!pos) return {};
    var faceArr = this.smpl.faces;
    var M = {};

    var chestV = this._getPartVerts('spine2');
    var shoulderV = this._getPartVerts('rightShoulder').concat(this._getPartVerts('leftShoulder'));
    var waistV = this._getPartVerts('spine1');
    var stomachV = this._getPartVerts('spine');
    var hipsV = this._getPartVerts('hips');
    var neckV = this._getPartVerts('neck');
    var rArmV = this._getPartVerts('rightArm');
    var lArmV = this._getPartVerts('leftArm');
    var rForeV = this._getPartVerts('rightForeArm');
    var lForeV = this._getPartVerts('leftForeArm');
    var rLegV = this._getPartVerts('rightUpLeg');
    var lLegV = this._getPartVerts('leftUpLeg');
    var rCalfV = this._getPartVerts('rightLeg');
    var lCalfV = this._getPartVerts('leftLeg');
    var rHandV = this._getPartVerts('rightHand');
    var lHandV = this._getPartVerts('leftHand');
    var rFootV = this._getPartVerts('rightFoot');
    var lFootV = this._getPartVerts('leftFoot');
    var chestAll = chestV.concat(shoulderV);

    var chestY = this._centroidY(pos, chestAll);
    var waistY = this._centroidY(pos, waistV);
    var stomachY = stomachV.length > 0 ? this._centroidY(pos, stomachV) : (chestY + waistY) / 2;
    var hipsY = this._centroidY(pos, hipsV);
    var neckY = this._centroidY(pos, neckV);
    var rArmY = this._centroidY(pos, rArmV);
    var lArmY = this._centroidY(pos, lArmV);
    var rForeY = this._centroidY(pos, rForeV);
    var lForeY = this._centroidY(pos, lForeV);
    var foreArmY = (rForeY + lForeY) / 2;
    var rLegY = this._centroidY(pos, rLegV);
    var lLegY = this._centroidY(pos, lLegV);
    var rCalfY = this._centroidY(pos, rCalfV);
    var lCalfY = this._centroidY(pos, lCalfV);
    var calfY = (rCalfY + lCalfY) / 2;

    var ankleRaw = rCalfV.concat(rFootV);
    var ankleV = ankleRaw.filter(function(vi) { return pos[vi * 3 + 1] < -1.0; });
    var ankleY = ankleV.length > 0 ? this._centroidY(pos, ankleV) : calfY - 0.12;
    var wristRaw = rForeV.concat(rHandV);
    var wristV = wristRaw.filter(function(vi) { return pos[vi * 3 + 1] < 0.19; });
    var wristY = wristV.length > 0 ? this._centroidY(pos, wristV) : foreArmY - 0.15;

    var rKneeV = rCalfV.filter(function(vi) { return pos[vi * 3 + 1] > -0.8; });
    var lKneeV = lCalfV.filter(function(vi) { return pos[vi * 3 + 1] > -0.8; });
    var rKneeY = rKneeV.length > 0 ? this._centroidY(pos, rKneeV) : rCalfY + 0.1;
    var lKneeY = lKneeV.length > 0 ? this._centroidY(pos, lKneeV) : lCalfY + 0.1;

    var self = this;
    var circ = function(verts, y, bw, partVerts) {
      var band = self._computeBandVerts(pos, verts, y, bw || 0.03);
      return self._computeCircumference(pos, faceArr, band, y, bw || 0.03, partVerts || verts);
    };

    var limbCirc = function(verts, y, bw, proj) {
      var band = self._computeBandVerts(pos, verts, y, bw || 0.03);
      return self._circFromVerts(pos, band, proj || 'xz');
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
