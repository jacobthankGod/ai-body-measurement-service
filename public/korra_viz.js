/**
 * KORRA 3D Visualizer | Block 3: Frontend Infrastructure
 * ======================================================
 * Industrial Three.js implementation for Digital Twin rendering.
 * Optimized for Obsidian & Mint aesthetic.
 */

window.KORRA_VIZ = {
    scene: null,
    camera: null,
    renderer: null,
    controls: null,
    mesh: null,

    init: function(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        // 1. Scene & Camera
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x000000); // Obsidian Base

        const fov = 45;
        const aspect = container.clientWidth / container.clientHeight;
        this.camera = new THREE.PerspectiveCamera(fov, aspect, 0.1, 1000);
        this.camera.position.set(0, 1.5, 3); // Positioned for body height

        // 2. Renderer
        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        this.renderer.setSize(container.clientWidth, container.clientHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        container.appendChild(this.renderer.domElement);

        // 3. Lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
        this.scene.add(ambientLight);

        const directionalLight = new THREE.DirectionalLight(0x57D7C0, 1); // Mint Light
        directionalLight.position.set(5, 10, 7.5);
        this.scene.add(directionalLight);

        // 4. Grid Floor (Artisan Guide)
        const grid = new THREE.GridHelper(10, 20, 0x57D7C0, 0x111111);
        grid.material.opacity = 0.2;
        grid.material.transparent = true;
        this.scene.add(grid);

        // 5. Animation Loop
        const animate = () => {
            requestAnimationFrame(animate);
            if (this.mesh) {
                this.mesh.rotation.y += 0.005; // Gentle rotation for "Wow" factor
            }
            this.renderer.render(this.scene, this.camera);
        };
        animate();

        window.addEventListener('resize', () => {
            this.camera.aspect = container.clientWidth / container.clientHeight;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(container.clientWidth, container.clientHeight);
        });

        console.log("✅ KORRA 3D Engine: Primed.");
    },

    loadMesh: function(objPath) {
        // Placeholder for OBJ loader in Phase 16
        // For Block 3 verification, we create an "Artisan Proxy" (A simple body-shaped column)
        if (this.mesh) this.scene.remove(this.mesh);

        const geometry = new THREE.CylinderGeometry(0.3, 0.2, 1.8, 32);
        const material = new THREE.MeshPhongMaterial({
            color: 0x57D7C0,
            wireframe: true,
            transparent: true,
            opacity: 0.8
        });

        this.mesh = new THREE.Mesh(geometry, material);
        this.mesh.position.y = 0.9;
        this.scene.add(this.mesh);

        console.log("💎 KORRA: Digital Twin Handshake Success.");
    }
};
