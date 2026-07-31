/**
 * GarmentMorphController — Loads garment GLB with morph targets
 * and applies measurement-based blending in real-time.
 *
 * v4 - NUCLEAR MATERIAL FIX
 * - Forces identity formats on ALL textures in the scene.
 * - Disables mipmapping entirely to prevent glGenerateMipmap errors.
 * - Forces LinearFilter for maximum compatibility.
 */
var GarmentMorphController = (function() {
  'use strict';

  function Controller() {
    this.garmentMesh = null;
    this.garmentRoot = null;
    this.morphIndexMap = {};
    this.loaded = false;
    this._lastWeights = null;
  }

  /**
   * Load a garment GLB with morph targets.
   */
  Controller.prototype.load = async function(glbUrl, scene) {
    var self = this;
    return new Promise(function(resolve, reject) {
      var loader = new THREE.GLTFLoader();

      loader.load(glbUrl, function(gltf) {
        var mesh = null;
        gltf.scene.traverse(function(child) {
          if (child.isMesh && child.geometry && !mesh) {
            mesh = child;
          }
        });

        if (!mesh) {
          reject(new Error('No mesh found in garment GLB'));
          return;
        }

        // 1. Morph target setup
        if (mesh.morphTargetDictionary) {
          self.morphIndexMap = mesh.morphTargetDictionary;
        } else {
          self.morphIndexMap = {};
          var names = MeasurementToWeight.MORPH_NAMES;
          for (var i = 0; i < names.length; i++) {
            self.morphIndexMap[names[i]] = i;
          }
        }
        var morphCount = Object.keys(self.morphIndexMap).length;
        if (!mesh.morphTargetInfluences || mesh.morphTargetInfluences.length !== morphCount) {
          mesh.morphTargetInfluences = new Float32Array(morphCount);
        }
        if (mesh.geometry.morphAttributes.position) {
          mesh.geometry.morphTargetsRelative = true;
        }

        // 2. NUCLEAR MATERIAL NORMALIZATION
        gltf.scene.traverse(function(node) {
          if (node.isMesh && node.material) {
            var m = node.material;
            m.side = THREE.DoubleSide; // Visibility fix

            // Standard slots + custom ones
            var mapSlots = ['map', 'normalMap', 'roughnessMap', 'metalnessMap', 'emissiveMap', 'aoMap', 'specularMap'];

            mapSlots.forEach(function(slot) {
              var tex = m[slot];
              if (!tex) return;

              // FORCE COMPATIBILITY
              tex.format = THREE.RGBAFormat;
              tex.type = THREE.UnsignedByteType;

              // DISABLE MIPMAPS (The source of 0x0000 and generation errors)
              tex.generateMipmaps = false;
              tex.minFilter = THREE.LinearFilter;
              tex.magFilter = THREE.LinearFilter;

              // Only base color should be sRGB
              if (slot === 'map' || slot === 'emissiveMap') {
                tex.colorSpace = THREE.SRGBColorSpace;
              } else {
                tex.colorSpace = THREE.NoColorSpace;
              }

              tex.needsUpdate = true;
            });
            m.needsUpdate = true;
          }
        });

        // 3. SCENE INTEGRATION
        self.garmentMesh = mesh;
        self.garmentRoot = gltf.scene;

        // Scale x10 (m -> dm) for MakeHuman body scene
        self.garmentRoot.scale.set(10, 10, 10);

        scene.add(self.garmentRoot);
        self.loaded = true;

        console.log('[GarmentMorph] v4 - Loaded:', glbUrl);
        console.log('[GarmentMorph] Morph targets:', Object.keys(self.morphIndexMap).length);
        resolve(true);

      }, undefined, function(err) {
        console.error('[GarmentMorph] Loader Error:', err);
        reject(err);
      });
    });
  };

  /**
   * Update garment morph weights from user measurements.
   */
  Controller.prototype.updateFromMeasurements = function(measurements) {
    if (!this.loaded || !this.garmentMesh) return;
    var weights = MeasurementToWeight.computeWeights(metrics(measurements));
    var morphArr = MeasurementToWeight.toMorphArray(weights);
    var influences = this.garmentMesh.morphTargetInfluences;
    if (!influences) return;

    var changed = false;
    for (var i = 0; i < morphArr.length; i++) {
      if (Math.abs(influences[i] - morphArr[i]) > 0.001) {
        influences[i] = morphArr[i];
        changed = true;
      }
    }
    if (changed) {
      this.garmentMesh.geometry.morphTargetsNeedUpdate = true;
      this._lastWeights = weights;
    }
  };

  Controller.prototype.syncPosition = function(bodyPosition) {
    if (this.garmentRoot && bodyPosition) {
      this.garmentRoot.position.copy(bodyPosition);
    }
  };

  Controller.prototype.dispose = function(scene) {
    if (this.garmentRoot) {
      scene.remove(this.garmentRoot);
      this.garmentRoot.traverse(function(node) {
        if (node.isMesh) {
          if (node.geometry) node.geometry.dispose();
          if (node.material) {
            var materials = Array.isArray(node.material) ? node.material : [node.material];
            materials.forEach(function(m) {
              ['map', 'normalMap', 'roughnessMap', 'metalnessMap', 'emissiveMap', 'aoMap'].forEach(function(t) {
                if(m[t]) { m[t].dispose(); m[t] = null; }
              });
              m.dispose();
            });
          }
        }
      });
      this.garmentMesh = null;
      this.garmentRoot = null;
      this.loaded = false;
      this._lastWeights = null;
    }
  };

  function metrics(m) {
    return {
      chest: m.chest || m['Chest Round'] || m.chest_circ || 100,
      waist: m.waist || m['Waist Round'] || 88,
      hip:   m.hip   || m['Hip Round']   || m.hip_circ || 100,
    };
  }

  return Controller;
})();

window.GarmentMorphController = GarmentMorphController;
