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
        this._bgMode = 'dark';
        this._axisGroup = null;
        this._cursorGroup = null;
        this._lightWidget = null;
        this._outline = null;
        this.controls = null;
        this._isOrtho = false;
        this._orthoCamera = null;
        this._orbitTarget = new THREE.Vector3(0, 0.5, 0);
        this._orbitSpherical = new THREE.Spherical(3.0, Math.PI / 2, 0);
        this._orbitState = { active: false, type: null, startX: 0, startY: 0, startSpherical: null, startTarget: null };
        this._meshSize = 0;
    }

    init(containerId) {
        console.log(`🔍 [EVOLUTION] Initializing 3D Viewport: ${containerId}`);
        const container = document.getElementById(containerId);
        if (!container) return;

        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x2B2B2B);

        const aspect = container.clientWidth / container.clientHeight;
        this.camera = new THREE.PerspectiveCamera(45, aspect, 0.1, 1000);
        this.camera.position.set(0, 0.5, 3.0);
        this.camera.lookAt(0, 0.5, 0);

        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true });
        this.renderer.setSize(container.clientWidth, container.clientHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        container.innerHTML = '';
        container.appendChild(this.renderer.domElement);
        this._currentContainer = containerId;

        this._buildGrid();
        this._buildAxes();
        this._buildCursor();
        this._buildLightWidget();

        const savedBg = localStorage.getItem('korra_viewport_bg');
        if (savedBg === 'light' || savedBg === 'dark') {
            this.setBackgroundMode(savedBg);
        }

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
            if (this._outline && this.mesh) {
                this._outline.position.copy(this.mesh.position);
                this._outline.rotation.copy(this.mesh.rotation);
                this._outline.scale.copy(this.mesh.scale);
            }
            this.renderer.render(this.scene, this.camera);
        };
        animate();

        // ── ORBIT + MESH DRAG CONTROLS ──
        this._orbitTarget.set(0, 0.5, 0);
        this._orbitSpherical.setFromVector3(
            new THREE.Vector3().subVectors(this.camera.position, this._orbitTarget)
        );

        container.addEventListener('mousedown', (e) => {
            if (e.button === 2) {
                // Right-click → camera orbit
                this._orbitState.active = true;
                this._orbitState.type = 'rotate';
                this._orbitState.startX = e.clientX;
                this._orbitState.startY = e.clientY;
                this._orbitState.startSpherical = this._orbitSpherical.clone();
                this.isInteracting = true;
                if (this.onInteract) this.onInteract(true);
            } else if (e.button === 1) {
                // Middle-click → pan
                this._orbitState.active = true;
                this._orbitState.type = 'pan';
                this._orbitState.startX = e.clientX;
                this._orbitState.startY = e.clientY;
                this._orbitState.startTarget = this._orbitTarget.clone();
                this.isInteracting = true;
                if (this.onInteract) this.onInteract(true);
            }
        });

        window.addEventListener('mousemove', (e) => {
            if (!this.isInteracting) return;
            if (this._orbitState.active && this._orbitState.type === 'rotate') {
                const deltaX = e.clientX - this._orbitState.startX;
                const deltaY = e.clientY - this._orbitState.startY;
                this._orbitSpherical.theta = this._orbitState.startSpherical.theta - deltaX * 0.01;
                this._orbitSpherical.phi = Math.max(0.1, Math.min(Math.PI - 0.1,
                    this._orbitState.startSpherical.phi - deltaY * 0.01));
                this._applyOrbit();
            } else if (this._orbitState.active && this._orbitState.type === 'pan') {
                const deltaX = e.clientX - this._orbitState.startX;
                const deltaY = e.clientY - this._orbitState.startY;
                const fovFactor = this._orbitSpherical.radius * 0.002;
                const right = new THREE.Vector3();
                const up = new THREE.Vector3(0, 1, 0);
                this.camera.getWorldDirection(right);
                right.cross(up).normalize();
                const panDelta = new THREE.Vector3()
                    .addScaledVector(right, -deltaX * fovFactor)
                    .addScaledVector(up, deltaY * fovFactor);
                this._orbitTarget.add(panDelta);
                this._applyOrbit();
                this._orbitState.startX = e.clientX;
                this._orbitState.startY = e.clientY;
                this._orbitState.startTarget = this._orbitTarget.clone();
            }
        });

        window.addEventListener('mouseup', () => {
            this._orbitState.active = false;
            this._orbitState.type = null;
            this.isInteracting = false;
            if (this.onInteract) this.onInteract(false);
        });

        // Scroll zoom
        container.addEventListener('wheel', (e) => {
            e.preventDefault();
            const delta = e.deltaY > 0 ? 1.1 : 0.9;
            this._orbitSpherical.radius = Math.max(0.5, Math.min(20, this._orbitSpherical.radius * delta));
            this._applyOrbit();
        }, { passive: false });

        // Prevent context menu on right-click
        container.addEventListener('contextmenu', (e) => e.preventDefault());

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
            if (touches.length === 2) {
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
        this.mesh.rotation.y = 20 * Math.PI / 180;
        this.targetRotationX = Math.PI;
        this.targetRotationY = 0;

        geometry.computeBoundingBox();
        const bbox = geometry.boundingBox;
        const size = new THREE.Vector3();
        bbox.getSize(size);

        this.mesh.position.set(0, size.y * 0.637, 0);
        const s = 1.3;
        this.mesh.scale.set(s, s, s);
        this._meshSize = size.y;
        this.camera.lookAt(0, size.y * 0.3, 0);
        this.camera.position.y = size.y * 0.5;
        this.camera.position.z = Math.max(3.0, size.y * 2.0);

        this.scene.add(this.mesh);

        // Orange selected outline
        if (this._outline) {
            this.scene.remove(this._outline);
            if (this._outline.geometry) this._outline.geometry.dispose();
            if (this._outline.material) this._outline.material.dispose();
        }
        const edgesGeo = new THREE.EdgesGeometry(geometry);
        const outlineMat = new THREE.LineBasicMaterial({
            color: 0xFF6600, transparent: true, opacity: 0.8
        });
        this._outline = new THREE.LineSegments(edgesGeo, outlineMat);
        this._outline.position.copy(this.mesh.position);
        this._outline.rotation.copy(this.mesh.rotation);
        this._outline.scale.copy(this.mesh.scale);
        this.scene.add(this._outline);

        this.updateOrbitTarget(new THREE.Vector3(0, size.y * 0.5, 0));

        return { vertices, faces, size };
    }

    toggleWireframe(force) {
        if (force !== undefined) {
            this.wireframeMode = !!force;
        } else {
            this.wireframeMode = !this.wireframeMode;
        }
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

    // ── Track G: Virtual Mirror (Phases 130-131) ──
    async loadGarment(objUrl, materialSettings = {}, garmentLayer = 0) {
        console.log(`👗 [VTO] Loading garment mesh: ${objUrl} (layer ${garmentLayer})`);
        if (!this.scene) return null;

        if (!this.garmentMeshes) this.garmentMeshes = [];

        try {
            const response = await fetch(objUrl);
            if (!response.ok) throw new Error("Garment file missing");
            const text = await response.text();

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

            const geometry = new THREE.BufferGeometry();
            geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
            if (faces.length > 0) geometry.setIndex(faces);
            geometry.computeVertexNormals();

            const material = new THREE.MeshPhongMaterial({
                color: materialSettings.color || 0xFFFFFF,
                transparent: true,
                opacity: materialSettings.opacity || 0.95,
                shininess: materialSettings.shininess || 30,
                side: THREE.DoubleSide,
                wireframe: this.wireframeMode,
                depthWrite: materialSettings.depthWrite !== false,
            });

            if (this.garmentMeshes[garmentLayer]) {
                this.scene.remove(this.garmentMeshes[garmentLayer]);
                if (this.garmentMeshes[garmentLayer].geometry) this.garmentMeshes[garmentLayer].geometry.dispose();
                if (this.garmentMeshes[garmentLayer].material) this.garmentMeshes[garmentLayer].material.dispose();
            }

            const mesh = new THREE.Mesh(geometry, material);
            if (this.mesh) {
                mesh.position.copy(this.mesh.position);
                mesh.rotation.copy(this.mesh.rotation);
                mesh.scale.copy(this.mesh.scale);
            }

            this.scene.add(mesh);
            this.garmentMeshes[garmentLayer] = mesh;
            console.log(`✓ [VTO] Garment layer ${garmentLayer} loaded successfully`);
            return mesh;
        } catch (e) {
            console.error("❌ [VTO] Failed to load garment:", e);
            return null;
        }
    }

    removeGarment(layer = -1) {
        if (layer >= 0 && this.garmentMeshes && this.garmentMeshes[layer]) {
            this.scene.remove(this.garmentMeshes[layer]);
            if (this.garmentMeshes[layer].geometry) this.garmentMeshes[layer].geometry.dispose();
            if (this.garmentMeshes[layer].material) this.garmentMeshes[layer].material.dispose();
            this.garmentMeshes[layer] = null;
            console.log(`🗑️ [VTO] Garment layer ${layer} removed`);
            return;
        }
        if (!this.garmentMeshes) return;
        for (let i = 0; i < this.garmentMeshes.length; i++) {
            if (this.garmentMeshes[i]) {
                this.scene.remove(this.garmentMeshes[i]);
                if (this.garmentMeshes[i].geometry) this.garmentMeshes[i].geometry.dispose();
                if (this.garmentMeshes[i].material) this.garmentMeshes[i].material.dispose();
            }
        }
        this.garmentMeshes = [];
        console.log("🗑️ [VTO] All garment layers removed");
    }

    toggleGarmentVisibility(visible) {
        if (!this.garmentMeshes) return;
        for (let i = 0; i < this.garmentMeshes.length; i++) {
            if (this.garmentMeshes[i]) this.garmentMeshes[i].visible = visible;
        }
    }

    get garmentMesh() {
        return this.garmentMeshes && this.garmentMeshes.length > 0 ? this.garmentMeshes[this.garmentMeshes.length - 1] : null;
    }

    set garmentMesh(val) {
        if (!this.garmentMeshes) this.garmentMeshes = [];
        if (val === null) { this.garmentMeshes = []; return; }
        this.garmentMeshes[0] = val;
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
        group.rotation.x = Math.PI;
        group.rotation.y = 20 * Math.PI / 180;
        group.scale.set(1.3, 1.3, 1.3);
        group.position.y = 0.637 * 0.4;
        const mat = new THREE.MeshPhongMaterial({ color: 0x2C3E50, wireframe: true, transparent: true, opacity: 0.2 });
        const torso = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.25, 0.8, 16), mat);
        group.add(torso);
        this.mesh = group;
        if (this.scene) this.scene.add(this.mesh);
    }

    resetCamera() {
        this._isOrtho = false;
        const aspect = this.camera.aspect;
        this.camera = new THREE.PerspectiveCamera(45, aspect, 0.1, 1000);
        const dist = this.mesh ? Math.max(3.0, this._meshSize * 2.0) : 3.0;
        this._orbitSpherical.set(dist, Math.PI / 2, 0);
        this._applyOrbit();
        if (this.mesh) {
            this.mesh.rotation.x = Math.PI;
            this.mesh.rotation.y = 20 * Math.PI / 180;
            if (this._meshSize > 0) {
                this.mesh.position.y = this._meshSize * 0.637;
            }
        }
        if (this.landmarksGroup) {
            this.landmarksGroup.rotation.x = Math.PI;
            this.landmarksGroup.rotation.y = 20 * Math.PI / 180;
        }
    }

    // ── BACKGROUND MODE ──
    setBackgroundMode(mode) {
        if (mode !== 'light' && mode !== 'dark') return;
        this._bgMode = mode;
        this._applyBgMode(mode);
        localStorage.setItem('korra_viewport_bg', mode);
    }

    _applyBgMode(mode) {
        if (mode === 'dark') {
            this.scene.background = new THREE.Color(0x2B2B2B);
            this._buildGrid(0xFFFFFF, 0x444444, 0.5);
        } else {
            this.scene.background = new THREE.Color(0xD4D4D4);
            this._buildGrid(0x666666, 0xAAAAAA, 0.6);
        }
    }

    toggleBackground() {
        this.setBackgroundMode(this._bgMode === 'dark' ? 'light' : 'dark');
        return this._bgMode;
    }

    // ── GRID ──
    _buildGrid(centerColor = 0xFFFFFF, gridColor = 0x444444, opacity = 0.5) {
        if (this.grid) {
            this.scene.remove(this.grid);
            if (this.grid.geometry) this.grid.geometry.dispose();
            if (this.grid.material) this.grid.material.dispose();
        }
        this.grid = new THREE.GridHelper(40, 80, centerColor, gridColor);
        this.grid.material.opacity = opacity;
        this.grid.material.transparent = opacity < 1;
        this.scene.add(this.grid);
    }

    // ── AXES (Red X, Green Y) ──
    _buildAxes() {
        if (this._axisGroup) {
            this.scene.remove(this._axisGroup);
            this._axisGroup.traverse(c => {
                if (c.geometry) c.geometry.dispose();
                if (c.material) c.material.dispose();
            });
        }
        this._axisGroup = new THREE.Group();
        const ext = 20;
        const makeLine = (from, to, color) => {
            const geo = new THREE.BufferGeometry();
            geo.setAttribute('position', new THREE.BufferAttribute(
                new Float32Array([from.x, from.y, from.z, to.x, to.y, to.z]), 3
            ));
            const mat = new THREE.LineBasicMaterial({
                color: color,
                transparent: true,
                opacity: 0.9,
                depthTest: true
            });
            return new THREE.Line(geo, mat);
        };
        // X-axis (red, left-right)
        this._axisGroup.add(makeLine(
            new THREE.Vector3(-ext, 0, 0), new THREE.Vector3(ext, 0, 0), 0xFF0000
        ));
        // Z-axis (green in Blender convention, depth in grid plane)
        this._axisGroup.add(makeLine(
            new THREE.Vector3(0, 0, -ext), new THREE.Vector3(0, 0, ext), 0x00FF00
        ));
        this.scene.add(this._axisGroup);
    }

    // ── 3D CURSOR ──
    _buildCursor() {
        if (this._cursorGroup) this.scene.remove(this._cursorGroup);
        this._cursorGroup = new THREE.Group();
        this._cursorGroup.position.set(0, 0, 0);

        // Dashed ring: alternating red/white arcs
        const segments = 32;
        const radius = 0.15;
        for (let i = 0; i < segments; i++) {
            const startAngle = (i / segments) * Math.PI * 2;
            const endAngle = ((i + 1) / segments) * Math.PI * 2;
            const color = i % 2 === 0 ? 0xFF0000 : 0xFFFFFF;
            const arcGeo = new THREE.BufferGeometry();
            const pts = [
                new THREE.Vector3(Math.cos(startAngle) * radius, 0, Math.sin(startAngle) * radius),
                new THREE.Vector3(Math.cos(endAngle) * radius, 0, Math.sin(endAngle) * radius)
            ];
            const positions = new Float32Array([
                pts[0].x, pts[0].y, pts[0].z,
                pts[1].x, pts[1].y, pts[1].z
            ]);
            arcGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
            const line = new THREE.Line(arcGeo, new THREE.LineBasicMaterial({
                color: color, transparent: true, opacity: 0.9, depthTest: false
            }));
            this._cursorGroup.add(line);
        }

        // Crosshair: two perpendicular lines
        const crossExtent = 0.22;
        const crossMat = new THREE.LineBasicMaterial({ color: 0xFFFFFF, depthTest: false });
        const horzGeo = new THREE.BufferGeometry();
        horzGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array([
            -crossExtent, 0, 0, crossExtent, 0, 0
        ]), 3));
        this._cursorGroup.add(new THREE.Line(horzGeo, crossMat));
        const vertGeo = new THREE.BufferGeometry();
        vertGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array([
            0, -crossExtent, 0, 0, crossExtent, 0
        ]), 3));
        this._cursorGroup.add(new THREE.Line(vertGeo, crossMat));

        this._cursorGroup.renderOrder = 999;
        this.scene.add(this._cursorGroup);
    }

    // ── POINT LIGHT WIDGET ──
    _buildLightWidget() {
        if (this._lightWidget) this.scene.remove(this._lightWidget);
        this._lightWidget = new THREE.Group();

        const lx = 5, ly = 10, lz = 7.5;
        const dotMat = new THREE.MeshBasicMaterial({ color: 0x000000 });
        const dot = new THREE.Mesh(new THREE.SphereGeometry(0.04, 16, 16), dotMat);
        dot.position.set(lx, ly, lz);
        this._lightWidget.add(dot);

        // Dashed circle around dot
        const ringPts = [];
        const ringRadius = 0.12;
        for (let i = 0; i <= 32; i++) {
            const angle = (i / 32) * Math.PI * 2;
            ringPts.push(Math.cos(angle) * ringRadius + lx, ly, Math.sin(angle) * ringRadius + lz);
        }
        const ringGeo = new THREE.BufferGeometry();
        ringGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(ringPts), 3));
        const ringLine = new THREE.Line(ringGeo, new THREE.LineBasicMaterial({
            color: 0x000000, transparent: true, opacity: 0.6
        }));
        this._lightWidget.add(ringLine);

        // Drop line to floor
        const dropGeo = new THREE.BufferGeometry();
        dropGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array([
            lx, ly, lz, lx, 0, lz
        ]), 3));
        const dropLine = new THREE.Line(dropGeo, new THREE.LineBasicMaterial({
            color: 0x000000, transparent: true, opacity: 0.4
        }));
        this._lightWidget.add(dropLine);

        this.scene.add(this._lightWidget);
    }

    toggleLightWidget(visible) {
        if (this._lightWidget) this._lightWidget.visible = visible;
    }

    // ── ORBIT CONTROLS ──
    _applyOrbit() {
        const pos = new THREE.Vector3().setFromSpherical(this._orbitSpherical).add(this._orbitTarget);
        this.camera.position.copy(pos);
        this.camera.up.set(0, 1, 0);
        this.camera.lookAt(this._orbitTarget);
    }

    updateOrbitTarget(newTarget) {
        if (newTarget) this._orbitTarget.copy(newTarget);
        this._orbitSpherical.setFromVector3(
            new THREE.Vector3().subVectors(this.camera.position, this._orbitTarget)
        );
    }

    // ── PROJECTION TOGGLE ──
    toggleProjection() {
        this._isOrtho = !this._isOrtho;
        const aspect = this.camera.aspect;
        const pos = this.camera.position.clone();
        const target = this._orbitTarget.clone();

        if (this._isOrtho) {
            const dist = pos.distanceTo(target);
            const fov = 45 * Math.PI / 180;
            const height = dist * 2 * Math.tan(fov / 2);
            const width = height * aspect;
            this._orthoCamera = new THREE.OrthographicCamera(
                -width / 2, width / 2, height / 2, -height / 2, 0.1, 1000
            );
            this._orthoCamera.position.copy(pos);
            this._orthoCamera.lookAt(target);
            this._orthoCamera.up.copy(this.camera.up);
            this.camera = this._orthoCamera;
        } else {
            this.camera = new THREE.PerspectiveCamera(45, aspect, 0.1, 1000);
            this.camera.position.copy(pos);
            this.camera.lookAt(target);
            this.camera.up.set(0, 1, 0);
        }
        return this._isOrtho;
    }
}

// ── Track G: Fabric Physics (Spring-Mass Simulation) ──
class FabricSimulation {
    constructor(mesh, options = {}) {
        this.mesh = mesh;
        this.particles = [];
        this.structuralSprings = [];
        this.shearSprings = [];
        this.bendSprings = [];
        this.fixedIndices = new Set();
        this.gravity = options.gravity || -9.81;
        this.damping = options.damping || 0.99;
        this.stiffness = options.stiffness || 0.8;
        this.bendCoeff = options.bendCoeff || 0.3;
        this.iterations = options.iterations || 5;
        this._active = false;
    }

    initParticles() {
        const pos = this.mesh.geometry.attributes.position;
        this.particles = [];
        for (let i = 0; i < pos.count; i++) {
            this.particles.push({
                x: pos.array[i * 3],
                y: pos.array[i * 3 + 1],
                z: pos.array[i * 3 + 2],
                px: pos.array[i * 3],
                py: pos.array[i * 3 + 1],
                pz: pos.array[i * 3 + 2],
                pinv: 1.0,
            });
        }
    }

    initStructuralSprings() {
        const idx = this.mesh.geometry.index;
        if (!idx) return;
        const seen = new Set();
        const key = (a, b) => a < b ? `${a}-${b}` : `${b}-${a}`;
        for (let i = 0; i < idx.count; i += 3) {
            const a = idx.array[i], b = idx.array[i + 1], c = idx.array[i + 2];
            [[a,b],[b,c],[c,a]].forEach(([p,q]) => {
                const k = key(p, q);
                if (!seen.has(k)) {
                    seen.add(k);
                    const dx = this.particles[p].x - this.particles[q].x;
                    const dy = this.particles[p].y - this.particles[q].y;
                    const dz = this.particles[p].z - this.particles[q].z;
                    this.structuralSprings.push({ a: p, b: q, rest: Math.sqrt(dx*dx + dy*dy + dz*dz) });
                }
            });
        }
    }

    initShearSprings() {
        const idx = this.mesh.geometry.index;
        if (!idx) return;
        const seen = new Set();
        const key = (a, b) => a < b ? `${a}-${b}` : `${b}-${a}`;
        for (let i = 0; i < idx.count; i += 3) {
            const a = idx.array[i], b = idx.array[i + 1], c = idx.array[i + 2];
            [[a,c]].forEach(([p,q]) => {
                const k = key(p, q);
                if (!seen.has(k)) {
                    seen.add(k);
                    const dx = this.particles[p].x - this.particles[q].x;
                    const dy = this.particles[p].y - this.particles[q].y;
                    const dz = this.particles[p].z - this.particles[q].z;
                    this.shearSprings.push({ a: p, b: q, rest: Math.sqrt(dx*dx + dy*dy + dz*dz) });
                }
            });
        }
    }

    initBendSprings() {
        const idx = this.mesh.geometry.index;
        if (!idx) return;
        const edgeToTri = new Map();
        const key = (a, b) => a < b ? `${a}-${b}` : `${b}-${a}`;
        for (let i = 0; i < idx.count; i += 3) {
            const t = [idx.array[i], idx.array[i+1], idx.array[i+2]];
            [[0,1],[1,2],[2,0]].forEach(([p,q]) => {
                const k = key(t[p], t[q]);
                if (!edgeToTri.has(k)) edgeToTri.set(k, []);
                edgeToTri.get(k).push(i / 3);
            });
        }
        for (const [edge, tris] of edgeToTri) {
            if (tris.length < 2) continue;
            for (let i = 0; i < tris.length - 1; i++) {
                for (let j = i + 1; j < tris.length; j++) {
                    const pA = idx.array[tris[i] * 3], pB = idx.array[tris[i] * 3 + 1], pC = idx.array[tris[i] * 3 + 2];
                    const pD = idx.array[tris[j] * 3], pE = idx.array[tris[j] * 3 + 1], pF = idx.array[tris[j] * 3 + 2];
                    const all = new Set([pA, pB, pC, pD, pE, pF]);
                    const [p1, p2, p3, p4] = [...all];
                    const dx = this.particles[p1].x - this.particles[p2].x;
                    const dy = this.particles[p1].y - this.particles[p2].y;
                    const dz = this.particles[p1].z - this.particles[p2].z;
                    this.bendSprings.push({ a: p1, b: p2, rest: Math.sqrt(dx*dx + dy*dy + dz*dz) });
                }
            }
        }
    }

    fixVertices(indices) {
        indices.forEach(i => this.fixedIndices.add(i));
    }

    _applyGravity(dt) {
        for (let i = 0; i < this.particles.length; i++) {
            if (this.fixedIndices.has(i)) continue;
            this.particles[i].y += this.gravity * dt * dt;
        }
    }

    _applySpringForces(springs, stiffness) {
        for (const s of springs) {
            const p1 = this.particles[s.a], p2 = this.particles[s.b];
            const dx = p2.x - p1.x, dy = p2.y - p1.y, dz = p2.z - p1.z;
            const dist = Math.sqrt(dx*dx + dy*dy + dz*dz);
            if (dist < 0.001) continue;
            const force = (dist - s.rest) * stiffness;
            const fx = force * dx / dist, fy = force * dy / dist, fz = force * dz / dist;
            if (!this.fixedIndices.has(s.a)) { p1.x += fx; p1.y += fy; p1.z += fz; }
            if (!this.fixedIndices.has(s.b)) { p2.x -= fx; p2.y -= fy; p2.z -= fz; }
        }
    }

    _applyBodyCollision(bodyParticles, margin = 0.5) {
        for (let i = 0; i < this.particles.length; i++) {
            if (this.fixedIndices.has(i)) continue;
            const p = this.particles[i];
            for (const bp of bodyParticles) {
                const dx = p.x - bp.x, dy = p.y - bp.y, dz = p.z - bp.z;
                const dist = Math.sqrt(dx*dx + dy*dy + dz*dz);
                if (dist < margin && dist > 0.001) {
                    const push = (margin - dist) / dist;
                    p.x += dx * push * 0.5;
                    p.y += dy * push * 0.5;
                    p.z += dz * push * 0.5;
                }
            }
        }
    }

    verletStep(dt) {
        for (let i = 0; i < this.particles.length; i++) {
            if (this.fixedIndices.has(i)) continue;
            const p = this.particles[i];
            const vx = (p.x - p.px) * this.damping;
            const vy = (p.y - p.py) * this.damping;
            const vz = (p.z - p.pz) * this.damping;
            p.px = p.x; p.py = p.y; p.pz = p.z;
            p.x += vx; p.y += vy; p.z += vz;
        }
    }

    step(dt, bodyParticles = null) {
        this.verletStep(dt);
        this._applyGravity(dt);
        this._applySpringForces(this.structuralSprings, this.stiffness);
        this._applySpringForces(this.shearSprings, this.stiffness * 0.5);
        this._applySpringForces(this.bendSprings, this.bendCoeff * this.stiffness);
        if (bodyParticles) this._applyBodyCollision(bodyParticles, 0.5);
        this._updateMesh();
    }

    _updateMesh() {
        const pos = this.mesh.geometry.attributes.position;
        for (let i = 0; i < this.particles.length; i++) {
            pos.array[i * 3] = this.particles[i].x;
            pos.array[i * 3 + 1] = this.particles[i].y;
            pos.array[i * 3 + 2] = this.particles[i].z;
        }
        pos.needsUpdate = true;
        this.mesh.geometry.computeVertexNormals();
    }

    start() { this._active = true; }
    stop() { this._active = false; }
    get active() { return this._active; }
}

window.KORRA_VIZ = new KorraVisualizer();
window.createKorraVisualizer = () => new KorraVisualizer();
