/**
 * KORRA 3D Visualizer | Phase 3: Heatmap Analytics
 * ====================================================
 * High-authority rendering engine with support for volumetric comparisons.
 */

class KorraVisualizer {
    constructor() {
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.mesh = null;
        this.grid = null;
        this.isInteracting = false;
        this.mouseX = 0;
        this.mouseY = 0;
        this.targetRotationX = 0;
        this.targetRotationY = 0;
    }

    init(containerId) {
        console.log(`🔍 [PHASE 3] Initializing 3D Viewport: ${containerId}`);
        const container = document.getElementById(containerId);
        if (!container) return;

        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x000000);

        const aspect = container.clientWidth / container.clientHeight;
        this.camera = new THREE.PerspectiveCamera(45, aspect, 0.1, 1000);
        this.camera.position.set(0, 1.0, 3.0);
        this.camera.lookAt(0, 1, 0);

        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        this.renderer.setSize(container.clientWidth, container.clientHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        container.innerHTML = '';
        container.appendChild(this.renderer.domElement);

        this.grid = new THREE.GridHelper(10, 20, 0x57D7C0, 0x222222);
        this.grid.material.opacity = 0.2;
        this.grid.material.transparent = true;
        this.scene.add(this.grid);

        const ambient = new THREE.AmbientLight(0xffffff, 0.5);
        this.scene.add(ambient);

        const mainLight = new THREE.DirectionalLight(0x57D7C0, 2.0);
        mainLight.position.set(5, 10, 7.5);
        this.scene.add(mainLight);

        const animate = () => {
            if (!this.renderer) return;
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

        window.addEventListener('resize', () => {
            if(!container.clientWidth) return;
            this.camera.aspect = container.clientWidth / container.clientHeight;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(container.clientWidth, container.clientHeight);
        });
    }

    async loadMesh(objUrl) {
        if (!objUrl || objUrl === 'null') {
            this.createTechnicalProxy();
            return null;
        }

        try {
            const response = await fetch(objUrl);
            if (!response.ok) throw new Error("File Missing");
            const text = await response.text();
            if (text.trim().startsWith('<!doctype html>')) throw new Error("Corruption");
            return this.parseAndRenderOBJ(text);
        } catch (e) {
            this.createTechnicalProxy();
            return null;
        }
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

    /**
     * PHASE 3: VOLUMETRIC HEATMAP ENGINE
     * Compares this instance's current mesh to a new set of data.
     */
    applyHeatmap(baselineData, latestData) {
        if (!baselineData || !latestData) return;

        const baselineArr = baselineData.vertices;
        const latestArr = latestData.vertices;

        // Safety: Topologies must match (HMR/SMPL standard)
        if (baselineArr.length !== latestArr.length) {
            console.error("❌ [HEATMAP] Topology mismatch. Comparison aborted.");
            return;
        }

        const count = baselineArr.length / 3;
        const colors = new Float32Array(baselineArr.length);

        for (let i = 0; i < count; i++) {
            const idx = i * 3;
            // Calculate Euclidean Distance difference (Simplified for Z-expansion/Physical volume)
            // In a professional clinical app, we calculate the signed distance along the surface normal.
            // For KORRA v1, we use radial distance from center.
            const bX = baselineArr[idx], bY = baselineArr[idx+1], bZ = baselineArr[idx+2];
            const lX = latestArr[idx], lY = latestArr[idx+1], lZ = latestArr[idx+2];

            const distB = Math.sqrt(bX*bX + bZ*bZ);
            const distL = Math.sqrt(lX*lX + lZ*lZ);
            const diff = distL - distB; // Positive = Growth, Negative = Loss

            if (diff > 0.005) { // Expansion (Red)
                colors[idx] = 1.0; colors[idx+1] = 0.3; colors[idx+2] = 0.3;
            } else if (diff < -0.005) { // Reduction (Mint)
                colors[idx] = 0.34; colors[idx+1] = 0.84; colors[idx+2] = 0.75;
            } else { // Static (White/Glass)
                colors[idx] = 0.8; colors[idx+1] = 0.8; colors[idx+2] = 0.8;
            }
        }

        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position', new THREE.Float32BufferAttribute(latestArr, 3));
        geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
        if (latestData.faces) geometry.setIndex(latestData.faces);
        geometry.computeVertexNormals();
        geometry.center();

        const material = new THREE.MeshPhongMaterial({
            vertexColors: true,
            wireframe: false,
            transparent: true,
            opacity: 0.8,
            side: THREE.DoubleSide
        });

        if (this.mesh) this.scene.remove(this.mesh);
        this.mesh = new THREE.Mesh(geometry, material);
        this.mesh.rotation.x = Math.PI;
        this.mesh.rotation.y = Math.PI;

        const size = latestData.size;
        this.mesh.position.set(0, size.y / 2, 0);
        this.scene.add(this.mesh);
    }

    createTechnicalProxy() {
        if (this.mesh) this.scene.remove(this.mesh);
        const group = new THREE.Group();
        const mat = new THREE.MeshPhongMaterial({ color: 0x57D7C0, wireframe: true, transparent: true, opacity: 0.1 });
        const torso = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.25, 0.8, 16), mat);
        torso.position.y = 1.0;
        group.add(torso);
        this.mesh = group;
        this.scene.add(this.mesh);
    }
}

window.KORRA_VIZ = new KorraVisualizer();
window.createKorraVisualizer = () => new KorraVisualizer();
