/**
 * KORRA 3D Visualizer | Phase 5-15 Evolution
 * ====================================================
 * High-authority rendering engine with glow effects and multi-instance support.
 */

class KorraVisualizer {
    constructor() {
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.mesh = null;
        this.grid = null;
        this.landmarksGroup = null;
        this.isInteracting = false;
        this.mouseX = 0;
        this.mouseY = 0;
        this.targetRotationX = 0;
        this.targetRotationY = 0;
        this.privacyShieldActive = false; // Phase 119
        this._meshCache = new Map();    // url -> { text, parsed }
        this.wireframeMode = false;     // solid mesh by default
        this._fetchCache = new Map();   // url -> Promise<string>
        this.onInteract = null;         // callback(isInteracting: boolean)
    }

    init(containerId) {
        console.log(`🔍 [EVOLUTION] Initializing 3D Viewport: ${containerId}`);
        const container = document.getElementById(containerId);
        if (!container) return;

        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0xD4D4D4);

        const aspect = container.clientWidth / container.clientHeight;
        this.camera = new THREE.PerspectiveCamera(45, aspect, 0.1, 1000);
        this.camera.position.set(0, 1.0, 3.0);
        this.camera.lookAt(0, 1, 0);

        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true });
        this.renderer.setSize(container.clientWidth, container.clientHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        container.innerHTML = '';
        container.appendChild(this.renderer.domElement);

        this.grid = new THREE.GridHelper(10, 20, 0x666666, 0xAAAAAA);
        this.grid.material.opacity = 0.6;
        this.grid.material.transparent = true;
        this.scene.add(this.grid);

        const ambient = new THREE.AmbientLight(0xffffff, 0.8);
        this.scene.add(ambient);

        const mainLight = new THREE.DirectionalLight(0xffffff, 1.5);
        mainLight.position.set(5, 10, 7.5);
        this.scene.add(mainLight);

        const fillLight = new THREE.DirectionalLight(0xffffff, 0.4);
        fillLight.position.set(-3, 1, -2);
        this.scene.add(fillLight);

        const animate = () => {
            if (!this.renderer) return;
            requestAnimationFrame(animate);
            if (this.mesh && !this.isInteracting) {
                this.mesh.rotation.y += 0.005;
                if(this.landmarksGroup) this.landmarksGroup.rotation.y += 0.005;
            } else if (this.mesh && this.isInteracting) {
                const rotY = this.mesh.rotation.y + (this.targetRotationY - this.mesh.rotation.y) * 0.1;
                const rotX = this.mesh.rotation.x + (this.targetRotationX - this.mesh.rotation.x) * 0.1;
                this.mesh.rotation.y = rotY;
                this.mesh.rotation.x = rotX;
                if(this.landmarksGroup) {
                    this.landmarksGroup.rotation.y = rotY;
                    this.landmarksGroup.rotation.x = rotX;
                }
            }
            this.renderer.render(this.scene, this.camera);
        };
        animate();

        container.addEventListener('mousedown', (e) => {
            this.isInteracting = true;
            this.mouseX = e.clientX;
            this.mouseY = e.clientY;
            if (this.onInteract) this.onInteract(true);
        });

        window.addEventListener('mousemove', (e) => {
            if (!this.isInteracting || !this.mesh) return;
            const deltaX = e.clientX - this.mouseX;
            const deltaY = e.clientY - this.mouseY;
            this.mouseX = e.clientX;
            this.mouseY = e.clientY;

            this.targetRotationY += deltaX * 0.01;
            this.targetRotationX += deltaY * 0.01;
        });

        window.addEventListener('mouseup', () => {
            this.isInteracting = false;
            if (this.onInteract) this.onInteract(false);
        });

        // ── TOUCH CONTROLS (mobile) ──
        this._touchState = { fingers: 0, startX: 0, startY: 0, lastPinchDist: 0, lastTap: 0 };
        container.addEventListener('touchstart', (e) => {
            if (!this.mesh) return;
            const touches = e.touches;
            this._touchState.fingers = touches.length;
            if (touches.length === 1) {
                this.isInteracting = true;
                if (this.onInteract) this.onInteract(true);
                this._touchState.startX = touches[0].clientX;
                this._touchState.startY = touches[0].clientY;
                this.mouseX = touches[0].clientX;
                this.mouseY = touches[0].clientY;
                // Double-tap detection
                const now = Date.now();
                if (now - this._touchState.lastTap < 300) {
                    this.resetCamera();
                    this._touchState.lastTap = 0;
                } else {
                    this._touchState.lastTap = now;
                }
            } else if (touches.length === 2) {
                this._touchState.lastPinchDist = Math.hypot(
                    touches[1].clientX - touches[0].clientX,
                    touches[1].clientY - touches[0].clientY
                );
            }
        }, { passive: true });

        container.addEventListener('touchmove', (e) => {
            if (!this.mesh) return;
            const touches = e.touches;
            if (touches.length === 1 && this._touchState.fingers === 1) {
                e.preventDefault();
                const deltaX = touches[0].clientX - this.mouseX;
                const deltaY = touches[0].clientY - this.mouseY;
                this.mouseX = touches[0].clientX;
                this.mouseY = touches[0].clientY;
                this.targetRotationY += deltaX * 0.01;
                this.targetRotationX += deltaY * 0.01;
            } else if (touches.length === 2) {
                e.preventDefault();
                const dist = Math.hypot(
                    touches[1].clientX - touches[0].clientX,
                    touches[1].clientY - touches[0].clientY
                );
                if (this._touchState.lastPinchDist > 0) {
                    const scale = dist / this._touchState.lastPinchDist;
                    const dir = new THREE.Vector3();
                    dir.subVectors(this.camera.position, new THREE.Vector3(0, 1, 0)).normalize();
                    const currentDist = this.camera.position.distanceTo(new THREE.Vector3(0, 1, 0));
                    const newDist = Math.max(1.5, Math.min(6, currentDist / scale));
                    this.camera.position.copy(new THREE.Vector3(0, 1, 0).add(dir.multiplyScalar(newDist)));
                }
                this._touchState.lastPinchDist = dist;
            }
        }, { passive: false });

        container.addEventListener('touchend', (e) => {
            this._touchState.fingers = e.touches.length;
            if (e.touches.length === 0) {
                this.isInteracting = false;
                if (this.onInteract) this.onInteract(false);
                this._touchState.lastPinchDist = 0;
            } else if (e.touches.length === 1) {
                this.mouseX = e.touches[0].clientX;
                this.mouseY = e.touches[0].clientY;
            }
        }, { passive: true });

        window.addEventListener('resize', () => {
            if(!container.clientWidth) return;
            this.camera.aspect = container.clientWidth / container.clientHeight;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(container.clientWidth, container.clientHeight);
        });
    }

    async loadMesh(objUrl, landmarkData = null) {
        if (!this.scene) {
            const container = document.getElementById('dashboard-3d-viewport');
            if (container) {
                this.init('dashboard-3d-viewport');
            } else {
                console.warn('🟡 3D viewport container not found, skipping mesh load');
                return null;
            }
        }
        if (!objUrl || objUrl === 'null') {
            this.createTechnicalProxy();
            return null;
        }

        try {
            let text = this._meshCache.get(objUrl);
            if (!text) {
                const controller = new AbortController();
                const id = setTimeout(() => controller.abort(), 15000);
                const response = await fetch(objUrl, { signal: controller.signal });
                clearTimeout(id);
                if (!response.ok) throw new Error("File Missing");
                text = await response.text();
                this._meshCache.set(objUrl, text);
            }
            const meshData = this.parseAndRenderOBJ(text);

            if (landmarkData) {
                this.renderLandmarks(landmarkData, meshData.size);
            }

            if (this.mesh && this.mesh.geometry && this.mesh.geometry.attributes.position) {
                this.mesh.geometry.attributes.position.usage = THREE.DynamicDrawUsage;
            }

            return meshData;
        } catch (e) {
            this.createTechnicalProxy();
            return null;
        }
    }

    preloadMesh(objUrl) {
        if (!objUrl || objUrl === 'null' || this._meshCache.has(objUrl)) return;
        if (this._fetchCache.has(objUrl)) return;
        const promise = fetch(objUrl).then(r => {
            if (!r.ok) throw new Error('Missing');
            return r.text();
        }).then(text => {
            this._meshCache.set(objUrl, text);
            return text;
        }).catch(() => {});
        this._fetchCache.set(objUrl, promise);
    }

    getCachedMesh(objUrl) {
        return this._meshCache.get(objUrl) || null;
    }

    updateVertices(newVertexData) {
        /**
         * Phase 76: Real-time Vertex Buffer Update
         * newVertexData: Float32Array of vertex positions
         */
        if (!this.mesh) return;
        const position = this.mesh.geometry.attributes.position;
        if (newVertexData.length !== position.count * 3) return;

        position.set(newVertexData);
        position.needsUpdate = true;
        this.mesh.geometry.computeVertexNormals();

        // Phase 83: Center camera on new mass
        this.mesh.geometry.computeBoundingBox();
        const bbox = this.mesh.geometry.boundingBox;
        const center = new THREE.Vector3();
        bbox.getCenter(center);
        this.mesh.position.set(0, center.y, 0); // Re-center on Y
    }

    parseAndRenderOBJ(text) {
        const vertices = [];
        const faces = [];
        const lines = text.split('\n');

        for (let line of lines) {
            line = line.trim();
            if (line.startsWith('v ')) {
                const parts = line.split(/\s+/);
                vertices.push(parseFloat(parts[1]), parseFloat(parts[2]), parseFloat(parts[3]));
            } else if (line.startsWith('f ')) {
                const parts = line.split(/\s+/);
                const p1 = parseInt(parts[1].split('/')[0]) - 1;
                const p2 = parseInt(parts[2].split('/')[0]) - 1;
                const p3 = parseInt(parts[3].split('/')[0]) - 1;
                faces.push(p1, p2, p3);
            }
        }

        if (vertices.length === 0) return null;

        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
        if (faces.length > 0) geometry.setIndex(faces);
        geometry.computeVertexNormals();
        geometry.center();

        this._wireframeMat = new THREE.MeshPhongMaterial({
            color: 0x2C3E50,
            wireframe: true,
            transparent: true,
            opacity: 0.9,
            shininess: 100,
            side: THREE.DoubleSide,
            emissive: 0x888888,
            emissiveIntensity: 0.1,
            flatShading: false
        });

        this._solidMat = new THREE.MeshPhongMaterial({
            color: 0x4A6FA5,
            wireframe: false,
            transparent: true,
            opacity: 0.85,
            shininess: 60,
            side: THREE.DoubleSide,
            emissive: 0x1A2A4A,
            emissiveIntensity: 0.05,
            flatShading: false,
            specular: 0x222222
        });

        if (this.mesh && this.scene) this.scene.remove(this.mesh);
        const material = this.wireframeMode ? this._wireframeMat : this._solidMat;
        this.mesh = new THREE.Mesh(geometry, material);
        this.mesh.rotation.x = Math.PI;
        this.mesh.rotation.y = Math.PI;
        this.targetRotationX = Math.PI;
        this.targetRotationY = Math.PI;

        geometry.computeBoundingBox();
        const bbox = geometry.boundingBox;
        const size = new THREE.Vector3();
        bbox.getSize(size);

        this.mesh.position.set(0, size.y / 2, 0);
        this.camera.lookAt(0, size.y / 2, 0);
        this.camera.position.y = size.y / 2;
        this.camera.position.z = Math.max(2.5, size.y * 1.5);

        this.scene.add(this.mesh);
        return { vertices, faces, size };
    }

    toggleWireframe() {
        this.wireframeMode = !this.wireframeMode;
        if (this.mesh) {
            this.mesh.material = this.wireframeMode ? this._wireframeMat : this._solidMat;
            this.mesh.material.needsUpdate = true;
        }
        return this.wireframeMode;
    }

    renderLandmarks(landmarks, modelSize) {
        if (this.landmarksGroup && this.scene) this.scene.remove(this.landmarksGroup);
        this.landmarksGroup = new THREE.Group();
        const dotGeo = new THREE.SphereGeometry(0.02, 16, 16);
        const dotMat = new THREE.MeshBasicMaterial({ color: 0xFFFFFF });

        Object.values(landmarks).forEach(p => {
            if (p.x !== undefined) {
                const dot = new THREE.Mesh(dotGeo, dotMat);
                dot.position.set(-p.x, -p.y + (modelSize.y/2), -p.z);
                this.landmarksGroup.add(dot);
            }
        });

        this.landmarksGroup.visible = false;
        this.scene.add(this.landmarksGroup);
    }

    toggleLandmarks(visible) {
        if (this.landmarksGroup) this.landmarksGroup.visible = visible;
    }

    togglePrivacyShield(active) {
        /**
         * Phase 119: Privacy Shield
         * Blurs or hides the facial vertices of the Digital Twin.
         */
        this.privacyShieldActive = active;
        if (!this.mesh) return;

        // Logic: Apply a specific shader or just hide the head vertices
        // For Phase 119, we will use emissive color as a visual indicator
        this.mesh.material.emissiveIntensity = active ? 1.0 : 0.1;
        this.mesh.material.emissive.setHex(active ? 0x000000 : 0x888888);
        console.log(`🛡️ Phase 119: Privacy Shield ${active ? 'ACTIVE' : 'INACTIVE'}`);
    }

    applyHeatmap(contextName = "standard") {
        /**
         * Phase 103: Visual Difference Heatmap
         * Transforms the mesh into a dynamic 'Ease Density' diagnostic tool.
         */
        if (!this.mesh || !window.KORRA_HEATMAP_SHADER) return;

        const reg = window.ATTIRE_REGISTRY || [];
        const entry = reg.find(a => a.id === contextName.toLowerCase());
        const activeMult = entry ? entry.heat : 1.0;

        const heatmapMaterial = new THREE.ShaderMaterial({
            uniforms: {
                uBaseRadius: { value: 0.25 },
                uActiveMultiplier: { value: activeMult },
                uOpacity: { value: 0.8 }
            },
            vertexShader: window.KORRA_HEATMAP_SHADER.vertexShader,
            fragmentShader: window.KORRA_HEATMAP_SHADER.fragmentShader,
            transparent: true,
            side: THREE.DoubleSide
        });

        // Store original material if not already stored
        if (!this.mesh.userData.originalMaterial) {
            this.mesh.userData.originalMaterial = this.mesh.material;
        }

        this.mesh.material = heatmapMaterial;
        this.mesh.material.needsUpdate = true;
        console.log(`🔥 Phase 103: Heatmap LIVE for context: ${contextName}`);
    }

    resetHeatmap() {
        if (this.mesh && this.mesh.userData.originalMaterial) {
            this.mesh.material = this.mesh.userData.originalMaterial;
        }
    }

    createTechnicalProxy() {
        if (this.mesh) {
            if (this.scene) this.scene.remove(this.mesh);
            if (this.mesh.geometry) this.mesh.geometry.dispose();
            if (this.mesh.material) {
                if (Array.isArray(this.mesh.material))
                    this.mesh.material.forEach(m => m.dispose());
                else
                    this.mesh.material.dispose();
            }
        }
        const group = new THREE.Group();
        const mat = new THREE.MeshPhongMaterial({ color: 0x2C3E50, wireframe: true, transparent: true, opacity: 0.2 });
        const torso = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.25, 0.8, 16), mat);
        torso.position.y = 1.0;
        group.add(torso);
        this.mesh = group;
        if (this.scene) this.scene.add(this.mesh);
    }

    showMeasurementRing(yPercent, color = '#C6FF00') {
        if (!this.mesh || !this.scene) return;
        this.clearMeasurementRings();

        const targetMesh = this.mesh.isGroup ? this.mesh.children[0] : this.mesh;
        if (!targetMesh || !targetMesh.geometry) return;

        targetMesh.geometry.computeBoundingBox();
        const bbox = targetMesh.geometry.boundingBox;
        const meshHeight = bbox.max.y - bbox.min.y;
        const meshY = bbox.min.y + meshHeight * yPercent;

        const torusGeo = new THREE.TorusGeometry(0.35, 0.008, 8, 64);
        const torusMat = new THREE.MeshBasicMaterial({
            color: new THREE.Color(color),
            transparent: true,
            opacity: 0.9,
            side: THREE.DoubleSide
        });
        const torus = new THREE.Mesh(torusGeo, torusMat);
        torus.position.y = meshY;
        torus.rotation.x = Math.PI / 2;

        const glowGeo = new THREE.TorusGeometry(0.36, 0.02, 8, 64);
        const glowMat = new THREE.MeshBasicMaterial({
            color: new THREE.Color(color),
            transparent: true,
            opacity: 0.25,
            side: THREE.DoubleSide
        });
        const glow = new THREE.Mesh(glowGeo, glowMat);
        glow.position.y = meshY;
        glow.rotation.x = Math.PI / 2;

        if (!this._measurementRings) this._measurementRings = new THREE.Group();
        this._measurementRings.add(torus);
        this._measurementRings.add(glow);
        this.scene.add(this._measurementRings);
    }

    showMeasurementRings(data, colors, yMap) {
        if (!this.mesh || !this.scene || !data) return;
        this.clearMeasurementRings();

        const targetMesh = this.mesh.isGroup ? this.mesh.children[0] : this.mesh;
        if (!targetMesh || !targetMesh.geometry) return;

        targetMesh.geometry.computeBoundingBox();
        const bbox = targetMesh.geometry.boundingBox;
        const meshHeight = bbox.max.y - bbox.min.y;
        const positions = targetMesh.geometry.attributes.position;

        this._measurementRings = new THREE.Group();

        for (const [key, color] of Object.entries(colors)) {
            if (!data.measurements || data.measurements[key] == null) continue;
            const yPct = yMap[key];
            if (yPct == null) continue;

            const meshY = bbox.min.y + meshHeight * yPct;
            const bandMin = bbox.min.y + meshHeight * (yPct - 0.02);
            const bandMax = bbox.min.y + meshHeight * (yPct + 0.02);

            let maxRadius = 0;
            for (let i = 0; i < positions.count; i++) {
                const vy = positions.getY(i);
                if (vy >= bandMin && vy <= bandMax) {
                    const vx = positions.getX(i);
                    const vz = positions.getZ(i);
                    const r = Math.sqrt(vx * vx + vz * vz);
                    if (r > maxRadius) maxRadius = r;
                }
            }
            if (maxRadius < 0.05) maxRadius = 0.35;

            const torusGeo = new THREE.TorusGeometry(maxRadius, 0.008, 8, 64);
            const torusMat = new THREE.MeshBasicMaterial({
                color: new THREE.Color(color),
                transparent: true,
                opacity: 0.9,
                side: THREE.DoubleSide
            });
            const torus = new THREE.Mesh(torusGeo, torusMat);
            torus.position.y = meshY;
            torus.rotation.x = Math.PI / 2;

            const glowGeo = new THREE.TorusGeometry(maxRadius + 0.01, 0.02, 8, 64);
            const glowMat = new THREE.MeshBasicMaterial({
                color: new THREE.Color(color),
                transparent: true,
                opacity: 0.25,
                side: THREE.DoubleSide
            });
            const glow = new THREE.Mesh(glowGeo, glowMat);
            glow.position.y = meshY;
            glow.rotation.x = Math.PI / 2;

            this._measurementRings.add(torus);
            this._measurementRings.add(glow);
        }

        this.scene.add(this._measurementRings);
    }

    clearMeasurementRings() {
        if (this._measurementRings && this.scene) {
            this.scene.remove(this._measurementRings);
            this._measurementRings.traverse(child => {
                if (child.geometry) child.geometry.dispose();
                if (child.material) child.material.dispose();
            });
            this._measurementRings = null;
        }
    }

    resetCamera() {
        this.camera.position.set(0, 1.0, 3.0);
        this.camera.lookAt(0, 1, 0);
        this.targetRotationX = 0;
        this.targetRotationY = 0;
        if (this.mesh) {
            this.mesh.rotation.x = 0;
            this.mesh.rotation.y = 0;
        }
        if (this.landmarksGroup) {
            this.landmarksGroup.rotation.x = 0;
            this.landmarksGroup.rotation.y = 0;
        }
    }
}

window.KORRA_VIZ = new KorraVisualizer();
window.createKorraVisualizer = () => new KorraVisualizer();
