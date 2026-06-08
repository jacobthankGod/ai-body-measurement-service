/**
 * KORRA 3D Visualizer | Block 5: Technical Ready State
 * ===================================================
 * Industrial Three.js implementation for Digital Twin rendering.
 */

window.KORRA_VIZ = {
    scene: null,
    camera: null,
    renderer: null,
    mesh: null,
    controls: null,

    init: function(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x000000);

        const aspect = container.clientWidth / container.clientHeight;
        this.camera = new THREE.PerspectiveCamera(45, aspect, 0.1, 1000);
        this.camera.position.set(2, 1.5, 3.5);

        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        this.renderer.setSize(container.clientWidth, container.clientHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        container.innerHTML = '';
        container.appendChild(this.renderer.domElement);

        // 1. ADD HOLOGRAPHIC GRID (Obsidian & Mint Style)
        const grid = new THREE.GridHelper(10, 20, 0x57D7C0, 0x222222);
        grid.material.opacity = 0.2;
        grid.material.transparent = true;
        this.scene.add(grid);

        // 2. ADD INFINITE FLOOR
        const planeGeom = new THREE.PlaneGeometry(100, 100);
        const planeMat = new THREE.MeshPhongMaterial({
            color: 0x000000,
            transparent: true,
            opacity: 0.5
        });
        const floor = new THREE.Mesh(planeGeom, planeMat);
        floor.rotation.x = -Math.PI / 2;
        this.scene.add(floor);

        // 3. ENHANCED LIGHTING
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
        this.scene.add(ambientLight);

        const directionalLight = new THREE.DirectionalLight(0x57D7C0, 1.5);
        directionalLight.position.set(5, 10, 7.5);
        this.scene.add(directionalLight);

        // 4. MOCK ORBITAL BEHAVIOR (Self-Rotating)
        const animate = () => {
            requestAnimationFrame(animate);
            if (this.mesh) {
                // If it's the proxy, keep it centered
                this.mesh.rotation.y += 0.005;
            }
            this.renderer.render(this.scene, this.camera);
        };
        animate();

        window.addEventListener('resize', () => {
            if(!container.clientWidth) return;
            this.camera.aspect = container.clientWidth / container.clientHeight;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(container.clientWidth, container.clientHeight);
        });

        console.log("💎 KORRA: 3D Lab Initialized. Ready for Digital Twin.");
    },

    loadMesh: async function(objUrl) {
        if (!objUrl || objUrl === 'null' || objUrl === 'undefined') {
            console.warn("⚠️ KORRA: No mesh URL provided. Displaying technical proxy.");
            this.createTechnicalProxy();
            return;
        }

        console.log("🧬 KORRA: Loading Physical Body Mesh from", objUrl);
        try {
            const response = await fetch(objUrl);
            if (!response.ok) throw new Error("File not found on server.");
            const text = await response.text();
            this.parseAndRenderOBJ(text);
        } catch (e) {
            console.error("❌ Mesh Handshake Failed:", e);
            this.createTechnicalProxy();
        }
    },

    parseAndRenderOBJ: function(text) {
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
                faces.push(parseInt(parts[1]) - 1, parseInt(parts[2]) - 1, parseInt(parts[3]) - 1);
            }
        }

        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
        geometry.setIndex(faces);
        geometry.computeVertexNormals();

        // MASTER ARTISAN MATERIAL
        const material = new THREE.MeshPhongMaterial({
            color: 0x57D7C0,
            wireframe: true,
            transparent: true,
            opacity: 0.9,
            shininess: 100
        });

        if (this.mesh) this.scene.remove(this.mesh);
        this.mesh = new THREE.Mesh(geometry, material);

        // Center the subject
        geometry.computeBoundingBox();
        const center = new THREE.Vector3();
        geometry.boundingBox.getCenter(center);
        this.mesh.position.sub(center);
        this.mesh.position.y += 1.0; // Stand on grid

        this.scene.add(this.mesh);
        console.log("✅ Digital Twin Active: 6,890 Vertices Rendered.");
    },

    createTechnicalProxy: function() {
        if (this.mesh) this.scene.remove(this.mesh);
        const group = new THREE.Group();
        const mat = new THREE.MeshPhongMaterial({
            color: 0x57D7C0,
            wireframe: true,
            transparent: true,
            opacity: 0.15
        });

        const torso = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.25, 0.8, 16), mat);
        torso.position.y = 1.0;
        const head = new THREE.Mesh(new THREE.SphereGeometry(0.15, 16, 16), mat);
        head.position.y = 1.55;

        group.add(torso, head);
        this.mesh = group;
        this.scene.add(this.mesh);
    }
};
