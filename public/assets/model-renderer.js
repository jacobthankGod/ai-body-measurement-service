(function() {
  'use strict';
  console.log('[ModelRenderer] IIFE executing');

  function ModelRenderer(containerId, options) {
    options = options || {};
    var container = typeof containerId === 'string'
      ? document.getElementById(containerId)
      : containerId;

    if (!container) { return null; }
    if (container._modelRenderer) { container._modelRenderer.destroy(); }

    container.innerHTML = '';
    container.style.background = '#000';
    container.style.border = 'none';
    container.style.outline = 'none';

    var w = container.clientWidth || 600;
    var h = container.clientHeight || 600;

    var scene = new THREE.Scene();
    scene.background = new THREE.Color(0x000000);

    var camera = new THREE.PerspectiveCamera(40, w / h, 0.1, 100);

    var renderer = new THREE.WebGLRenderer({
      antialias: true,
      powerPreference: 'high-performance'
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(w, h);
    renderer.setClearColor(0x000000, 1);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.5;
    container.appendChild(renderer.domElement);

    var hemi = new THREE.HemisphereLight(0xffffff, 0x666666, 0.8);
    scene.add(hemi);

    var ambient = new THREE.AmbientLight(0xffffff, 0.3);
    scene.add(ambient);

    var lights = [
      { pos: [5, 8, 6], intensity: 1.0 },
      { pos: [-5, 6, -6], intensity: 0.7 },
      { pos: [6, -2, 4], intensity: 0.6 },
      { pos: [0, -4, 8], intensity: 0.5 }
    ];

    lights.forEach(function(l) {
      var d = new THREE.DirectionalLight(0xffffff, l.intensity);
      d.position.set(l.pos[0], l.pos[1], l.pos[2]);
      scene.add(d);
    });

    var group = new THREE.Group();
    scene.add(group);

    var rotationSpeed = options.rotationSpeed || 0.008;
    var isDragging = false;
    var prevMouse = { x: 0, y: 0 };
    var dragRot = { x: 0, y: 0 };

    // ALWAYS provide DRACOLoader if available to prevent "No DRACOLoader instance provided" errors
    var loader = new THREE.GLTFLoader();
    if (THREE.DRACOLoader) {
      var dracoLoader = new THREE.DRACOLoader();
      dracoLoader.setDecoderPath('/assets/draco/');
      loader.setDRACOLoader(dracoLoader);
    }

    function onModelLoaded(gltf) {
      var model = gltf.scene;

      model.traverse(function(child) {
        if (child.isMesh && child.material) {
          var mats = Array.isArray(child.material) ? child.material : [child.material];
          mats.forEach(function(mat) {
            ['map', 'emissiveMap', 'normalMap', 'roughnessMap', 'metalnessMap', 'aoMap'].forEach(function(key) {
              if (mat[key]) {
                mat[key].format = THREE.RGBAFormat;
                mat[key].needsUpdate = true;
              }
            });
          });
        }
      });

      var box = new THREE.Box3().setFromObject(model);
      var center = box.getCenter(new THREE.Vector3());
      var size = box.getSize(new THREE.Vector3());

      model.position.sub(center);

      var fovRad = camera.fov * Math.PI / 180;
      var aspect = w / h;
      var distY = size.y / (2 * Math.tan(fovRad / 2));
      var distX = size.x / (2 * Math.tan(fovRad / 2) * aspect);
      var dist = Math.max(distY, distX) * 1.05;
      camera.position.set(0, 0, dist);
      camera.lookAt(0, 0, 0);

      group.add(model);
    }

    var preFetchPromise = options.preFetchPromise;
    var fallbackUrl = options.glbPath || '/api/v2/garment-models/agbada';

    if (preFetchPromise) {
      preFetchPromise.then(function(buffer) {
        loader.parse(buffer, '', onModelLoaded, function(err) {
          console.warn('[ModelRenderer] Parse failed, falling back to URL load:', err);
          loader.load(fallbackUrl, onModelLoaded);
        });
      }).catch(function(err) {
        console.warn('[ModelRenderer] Fetch failed, falling back to URL load:', err);
        loader.load(fallbackUrl, onModelLoaded);
      });
    } else {
      loader.load(fallbackUrl, onModelLoaded);
    }

    var ro = new ResizeObserver(function() {
      var w2 = container.clientWidth;
      var h2 = container.clientHeight;
      camera.aspect = w2 / h2;
      camera.updateProjectionMatrix();
      renderer.setSize(w2, h2);
    });
    ro.observe(container);

    container.style.cursor = 'grab';
    container.addEventListener('mousedown', function(e) {
      isDragging = true;
      container.style.cursor = 'grabbing';
      prevMouse = { x: e.clientX, y: e.clientY };
    });
    window.addEventListener('mousemove', function(e) {
      if (!isDragging) return;
      var dx = e.clientX - prevMouse.x;
      var dy = e.clientY - prevMouse.y;
      dragRot.y += dx * 0.005;
      dragRot.x += dy * 0.005;
      dragRot.x = Math.max(-Math.PI / 3, Math.min(Math.PI / 3, dragRot.x));
      prevMouse = { x: e.clientX, y: e.clientY };
    });
    window.addEventListener('mouseup', function() {
      isDragging = false;
      container.style.cursor = 'grab';
    });

    container.addEventListener('touchstart', function(e) {
      if (e.touches.length === 1) {
        isDragging = true;
        prevMouse = { x: e.touches[0].clientX, y: e.touches[0].clientY };
      }
    }, { passive: true });
    container.addEventListener('touchmove', function(e) {
      if (!isDragging || e.touches.length !== 1) return;
      var dx = e.touches[0].clientX - prevMouse.x;
      var dy = e.touches[0].clientY - prevMouse.y;
      dragRot.y += dx * 0.005;
      dragRot.x += dy * 0.005;
      dragRot.x = Math.max(-Math.PI / 3, Math.min(Math.PI / 3, dragRot.x));
      prevMouse = { x: e.touches[0].clientX, y: e.touches[0].clientY };
    }, { passive: true });
    container.addEventListener('touchend', function() { isDragging = false; });

    var aid = null;
    function animate() {
      aid = requestAnimationFrame(animate);
      if (!isDragging) {
        group.rotation.y += rotationSpeed;
      } else {
        group.rotation.y = dragRot.y;
        group.rotation.x = dragRot.x;
      }
      renderer.render(scene, camera);
    }
    animate();

    container._modelRenderer = {
      destroy: function() {
        cancelAnimationFrame(aid);
        ro.disconnect();
        renderer.dispose();
        scene.clear();
        container.innerHTML = '';
        delete container._modelRenderer;
      }
    };
    return container._modelRenderer;
  }

  window.ModelSerializer = ModelRenderer;
})();
