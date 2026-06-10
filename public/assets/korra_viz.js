/**
 * KORRA 3D Visualizer | Block 6: Deep Forensic Debugging
 * ====================================================
 * High-authority rendering engine with extreme console tracing.
 */

window.KORRA_VIZ = {
    scene: null,
    camera: null,
    renderer: null,
    mesh: null,
    grid: null,
    isInteracting: false,
    mouseX: 0,
    mouseY: 0,
    targetRotationX: 0,
    targetRotationY: 0,

    init: function(containerId) {
        console.log(`🔍 [FORENSIC] Initializing 3D Lab for container: ${containerId}`);
        const container = document.getElementById(containerId);
        if (!container) {
            console.error("❌ [FORENSIC] Container not found!");
            return;
        }

        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x000000);

        const aspect = container.clientWidth / container.clientHeight;
        this.camera = new THREE.PerspectiveCamera(45, aspect, 0.1, 1000);
        this.camera.position.set(0, 1.0, 3.0); // Balanced starting zoom
        this.camera.lookAt(0, 1, 0);

        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        this.renderer.setSize(container.clientWidth, container.clientHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        container.innerHTML = '';
        container.appendChild(this.renderer.domElement);

        // 1. ADD HOLOGRAPHIC GRID
        this.grid = new THREE.GridHelper(10, 20, 0x57D7C0, 0x222222);
        this.grid.material.opacity = 0.2;
        this.grid.material.transparent = true;
        this.scene.add(this.grid);

        // 2. LIGHTING (Hero directionality)
        const ambient = new THREE.AmbientLight(0xffffff, 0.5);
        this.scene.add(ambient);

        const mainLight = new THREE.DirectionalLight(0x57D7C0, 2.0);
        mainLight.position.set(5, 10, 7.5);
        this.scene.add(mainLight);

        const fillLight = new THREE.PointLight(0xffffff, 1.0);
        fillLight.position.set(-5, 5, -5);
        this.scene.add(fillLight);

        const animate = () => {
            requestAnimationFrame(animate);
            if (this.mesh && !this.isInteracting) {
                this.mesh.rotation.y += 0.005;
            } else if (this.mesh && this.isInteracting) {
                this.mesh.rotation.y += (this.targetRotationY - this.mesh.rotation.y) * 0.1;
                this.mesh.rotation.x += (this.targetRotationX - this.mesh.rotation.x) * 0.1;
            }
            this.renderer.render(this.scene, this.camera);
        };
        animate();

        // 3. ADD INTERACTION (FORENSIC HARDENING)
        container.addEventListener('mousedown', (e) => {
            this.isInteracting = true;
            this.mouseX = e.clientX;
            this.mouseY = e.clientY;
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
        });

        container.addEventListener('wheel', (e) => {
            e.preventDefault();
            this.camera.position.z += e.deltaY * 0.01;
            this.camera.position.z = Math.max(1.5, Math.min(10, this.camera.position.z));
        }, { passive: false });

        window.addEventListener('resize', () => {
            if(!container.clientWidth) return;
            this.camera.aspect = container.clientWidth / container.clientHeight;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(container.clientWidth, container.clientHeight);
        });

        console.log("💎 KORRA: 3D Lab Ready.");
    },

    loadMesh: async function(objUrl) {
        console.log(`🧬 [FORENSIC] loadMesh handshake initiated: ${objUrl}`);
        if (!objUrl || objUrl === 'null') {
            console.warn("⚠️ [FORENSIC] Invalid URL. Drawing Technical Proxy.");
            this.createTechnicalProxy();
            return;
        }

        try {
            const start = performance.now();
            const response = await fetch(objUrl);
            if (!response.ok) throw new Error(`HTTP ${response.status} - File Missing on Server`);

            const text = await response.text();
            console.log(`📦 [FORENSIC] Downloaded OBJ (${text.length} chars) in ${Math.round(performance.now() - start)}ms`);

            // Check first 100 chars to verify it's a real OBJ, not HTML
            if (text.trim().startsWith('<!doctype html>')) {
                throw new Error("Corruption: Received HTML instead of 3D data. Routing failure.");
            }

            this.parseAndRenderOBJ(text);
        } catch (e) {
            console.error("❌ [FORENSIC] 3D Handshake Failed:", e.message);
            this.createTechnicalProxy();
        }
    },

    parseAndRenderOBJ: function(text) {
        console.log("🛠️ [FORENSIC] Parsing vertex buffers...");
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
                // Handle complex OBJ indices (e.g. 1/1/1)
                const p1 = parseInt(parts[1].split('/')[0]) - 1;
                const p2 = parseInt(parts[2].split('/')[0]) - 1;
                const p3 = parseInt(parts[3].split('/')[0]) - 1;
                faces.push(p1, p2, p3);
            }
        }

        console.log(`📊 [FORENSIC] Stats: Vertices=${vertices.length / 3}, Faces=${faces.length / 3}`);

        if (vertices.length === 0) {
            console.error("❌ [FORENSIC] Zero vertices parsed! Data is empty.");
            return;
        }

        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
        if (faces.length > 0) geometry.setIndex(faces);
        geometry.computeVertexNormals();

        // CLEAN CENTERING
        geometry.center();

        const material = new THREE.MeshPhongMaterial({
            color: 0x57D7C0,
            wireframe: true,
            transparent: true,
            opacity: 0.9,
            shininess: 100,
            side: THREE.DoubleSide
        });

        if (this.mesh) this.scene.remove(this.mesh);
        this.mesh = new THREE.Mesh(geometry, material);

        // FORENSIC FIX: Rotate upright
        this.mesh.rotation.x = Math.PI;
        this.mesh.rotation.y = Math.PI;

        // Sync interaction targets
        this.targetRotationX = Math.PI;
        this.targetRotationY = Math.PI;

        // Calculate Size & Stand on Ground
        geometry.computeBoundingBox();
        const bbox = geometry.boundingBox;
        const size = new THREE.Vector3();
        bbox.getSize(size);

        console.log(`📐 [FORENSIC] Bounding Box: Width=${size.x.toFixed(2)}, Height=${size.y.toFixed(2)}, Depth=${size.z.toFixed(2)}`);

        // Stand perfectly on ground (Y=0)
        this.mesh.position.set(0, size.y / 2, 0);

        // Adjust camera to look at center of height
        this.camera.lookAt(0, size.y / 2, 0);
        this.camera.position.y = size.y / 2; // Perfectly vertical alignment
        this.camera.position.z = Math.max(2.5, size.y * 1.5); // Dynamic zoom based on height

        this.scene.add(this.mesh);
        console.log("✅ [FORENSIC] Digital Twin materialization success.");
    },

    createTechnicalProxy: function() {
        console.log("🛡️ [FORENSIC] Materializing technical proxy model.");
        if (this.mesh) this.scene.remove(this.mesh);
        const group = new THREE.Group();
        const mat = new THREE.MeshPhongMaterial({ color: 0x57D7C0, wireframe: true, transparent: true, opacity: 0.1 });
        const torso = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.25, 0.8, 16), mat);
        torso.position.y = 1.0;
        group.add(torso);
        this.mesh = group;
        this.scene.add(this.mesh);
    }
};
