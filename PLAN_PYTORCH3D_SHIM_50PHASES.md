# 50-Phase Plan: Industry-Standard pytorch3d Shim

**Goal**: Replace the current stub-based pytorch3d shim with a working implementation that mirrors the real pytorch3d architecture (v0.7.x), using pure PyTorch + trimesh (no CUDA/C++), enabling GarmentRec to render actual meshes on Modal.

---

## Phase 0–4: Foundation & Shim Loader

### Phase 0 — Import Heist + Package Auto-repair
- Upgrade `_patch_pytorch3d()` to handle missing subpackages (e.g., `pytorch3d.renderer.mesh` re-exports from `renderer`). 
- Add `__path__` / `__file__` attributes to all stub modules so `importlib` doesn't raise.
- Verify: `from pytorch3d import _C` raises `ImportError` gracefully (not crash).
- Reference: `pytorch3d/__init__.py` — version string, `__version__`.

### Phase 1 — Device & Tensor Properties
- Implement `TensorProperties` base class (from `pytorch3d/renderer/utils.py`):
  - `__init__`, `to()`, `clone()`, `get_cuda()`.
- Implement `make_device()` from `pytorch3d/common/datatypes.py`.
- Reference: `pytorch3d/renderer/utils.py:TensorProperties`.

### Phase 2 — `io/__init__.py` Overhaul
- Replace `load_obj()` to return `NamedTuple(verts, faces, aux)` where `aux` is `SimpleNamespace(verts_uvs, faces_uvs, texture_images, material_colors)`.
- Implement `load_objs_as_meshes()` → `Meshes` with `TexturesUV`.
- `save_obj()`: handle `verts_uvs` / `faces_uvs` / `texture_map` as torch tensors, write MTL file with texture image.
- Reference: `pytorch3d/io/__init__.py`, `pytorch3d/io/obj_io.py`.

### Phase 3 — `io/` Per-Mesh Saving
- `save_obj()` must handle the `Meshes` class directly (accept `Meshes` object, extract verts/faces/textures).
- Add `create_texture_atlas` option to `load_obj()`.
- Reference: `pytorch3d/io/obj_io.py:save_obj`.

### Phase 4 — Common Utilities
- Implement `struct_utils` submodule:
  - `list_to_padded()`, `padded_to_list()`, `list_to_packed()`, `packed_to_list()`
  - `packed_to_padded()`, `padded_to_packed()` (currently in ops, should be in structures)
- Reference: `pytorch3d/structures/utils.py`.

---

## Phase 5–10: Meshes Class (Full)

### Phase 5 — `Meshes.__init__` — List + Padded + Normals
- Accept `verts` (list or padded tensor), `faces` (list or padded tensor), `textures` (TexturesBase), `verts_normals` (list or padded tensor).
- Store `_verts_list`, `_faces_list`, `_verts_padded`, `_faces_padded`.
- Compute `_num_verts_per_mesh`, `_num_faces_per_mesh`, `_N`, `_V`, `_F`, `valid`, `equisized`.
- Call `textures.check_shapes()` if textures present.
- Reference: `pytorch3d/structures/meshes.py:Meshes.__init__`.

### Phase 6 — `_compute_packed()` — Packed Representation
- `_compute_packed(refresh=False)`:
  - Concatenate verts_list → `_verts_packed` (sum(V_n), 3).
  - Build `_verts_packed_to_mesh_idx`, `_mesh_to_verts_packed_first_idx`.
  - Concatenate faces_list with offset → `_faces_packed` (sum(F_n), 3).
  - Build `_faces_packed_to_mesh_idx`, `_mesh_to_faces_packed_first_idx`.
- Accessors: `verts_packed()`, `faces_packed()`, `verts_packed_to_mesh_idx()`, `mesh_to_faces_packed_first_idx()`.
- Reference: `pytorch3d/structures/meshes.py:Meshes._compute_packed`.

### Phase 7 — `_compute_padded()` + `_compute_edges_packed()`
- `_compute_padded()`: build `_verts_padded`, `_faces_padded` from lists.
- `_compute_edges_packed()`: extract unique edges from faces, sort, deduplicate.
  - `edges_packed()`, `edges_packed_to_mesh_idx()`, `faces_packed_to_edges_packed()`.
- Reference: `pytorch3d/structures/meshes.py`.

### Phase 8 — `_compute_vertex_normals()` + `_compute_face_areas_normals()`
- `_compute_vertex_normals()`: compute per-vertex normals using area-weighted face normals, `F.normalize`.
- `_compute_face_areas_normals()`: face normals via cross product (avoid `mesh_face_areas_normals` C extension).
- `verts_normals_packed()`, `faces_normals_packed()`, `faces_areas_packed()`.
- Reference: `pytorch3d/structures/meshes.py`.

### Phase 9 — Meshes: `clone()`, `detach()`, `to()`, `cpu()`, `cuda()`
- `clone()`: deep copy all internal tensors + textures.
- `detach()`: detach all tensors + textures.
- `to(device)`: move all tensors + textures, update `self.device`.
- `cpu()` / `cuda()`: convenience wrappers.
- Reference: `pytorch3d/structures/meshes.py`.

### Phase 10 — Meshes: `__getitem__`, `split()`, `offset_verts_()`, `update_padded()`
- `__getitem__`: support int, slice, list, BoolTensor → return new `Meshes` with proper textures subsetting.
- `split(split_sizes)`: return `list[Meshes]`.
- `offset_verts_(vert_offsets_packed)`: in-place add offset, recalc normals.
- `update_padded(new_verts_padded)`: replace padded verts, reset cached tensors.
- Reference: `pytorch3d/structures/meshes.py`.

---

## Phase 11–18: Software Rasterizer (Pure PyTorch)

### Phase 11 — `RasterizationSettings` Dataclass
- Full dataclass with all fields: `image_size`, `blur_radius`, `faces_per_pixel`, `bin_size`, `perspective_correct`, `clip_barycentric_coords`, `cull_backfaces`, `z_clip_value`, `cull_to_frustum`.
- Reference: `pytorch3d/renderer/mesh/rasterizer.py:RasterizationSettings`.

### Phase 12 — Edge Function + Barycentric Utilities
- `edge_function(p, v0, v1)`: signed 2D cross product.
- `barycentric_coordinates(p, v0, v1, v2)`: compute barycentric from edge functions.
- `barycentric_coordinates_clip(bary)`: clamp negatives, renormalize.
- `point_line_distance(p, v0, v1)`, `point_triangle_distance(p, v0, v1, v2)`.
- Reference: `pytorch3d/renderer/mesh/rasterize_meshes.py`.

### Phase 13 — Face Bounding Box + Frustum Culling
- Compute per-face screen-space bounding box from projected vertices.
- `cull_backfaces`: skip faces with negative area (clockwise winding).
- `cull_to_frustum`: skip faces entirely outside [-1, 1] NDC.
- `z_clip_value`: skip faces with z < epsilon.
- Reference: `pytorch3d/renderer/mesh/rasterize_meshes.py:rasterize_meshes_python`.

### Phase 14 — Naive Per-Pixel Rasterizer
- Implement `rasterize_meshes_python()` from pytorch3d:
  - Loop over meshes N.
  - Loop over pixels (H, W).
  - Loop over faces within bounding box.
  - Compute barycentric, z-buffer, distance.
  - Use `cull_backfaces`, `perspective_correct`, `clip_barycentric_coords`.
- This will be slow but correct for inference.
- Reference: `pytorch3d/renderer/mesh/rasterize_meshes.py` lines 200–380.

### Phase 15 — Vectorized Rasterizer (Optimization)
- Replace inner loops with vectorized operations:
  - Batch face bounding box checks per mesh.
  - Use tensor operations for pixel-in-triangle tests.
  - `torch.where` / `torch.stack` for output assembly.
- Target: < 10s per 540×540 image with ~10K faces (OK for inference).
- Reference: Computer graphics standard (triangle setup → edge walk).

### Phase 16 — `Fragments` Named Tuple
- Implement `Fragments` dataclass: `pix_to_face`, `zbuf`, `bary_coords`, `dists`.
- Add `detach()` method.
- Reference: `pytorch3d/renderer/mesh/rasterizer.py:Fragments`.

### Phase 17 — `MeshRasterizer` Transform + Forward
- `MeshRasterizer.__init__(cameras, raster_settings)`.
- `transform(meshes_world)`: apply world→view→NDC transform using cameras.
  - `get_world_to_view_transform()`, `get_ndc_camera_transform()`, `try_get_projection_transform()`.
- `forward(meshes_world)`: transform + rasterize → return `Fragments`.
- Reference: `pytorch3d/renderer/mesh/rasterizer.py:MeshRasterizer`.

### Phase 18 — `rasterize_meshes` Public API
- Public `rasterize_meshes()` function matching pytorch3d signature.
- Handle `image_size` as int or tuple.
- Handle `bin_size` selection heuristic.
- Return 4-tuple `(pix_to_face, zbuf, bary_coords, dists)`.
- Reference: `pytorch3d/renderer/mesh/rasterize_meshes.py:rasterize_meshes`.

---

## Phase 19–25: Textures

### Phase 19 — `TexturesBase` Abstract Base Class
- `isempty()`, `to(device)`, `clone()`, `detach()`, `__getitem__()`, `sample_textures()`.
- Reference: `pytorch3d/renderer/mesh/textures.py:TexturesBase`.

### Phase 20 — `TexturesVertex` Full Implementation
- Store `verts_features_packed`, `verts_features_list`, `verts_features_padded`.
- `sample_textures(fragments)`: interpolate vertex features using barycentric coords.
- Requires `interpolate_face_attributes()` from `pytorch3d.ops`.
- Reference: `pytorch3d/renderer/mesh/textures.py:TexturesVertex` (now in the truncated source).

### Phase 21 — `TexturesUV` Full Implementation
- Constructor: `maps`, `faces_uvs`, `verts_uvs`, `maps_ids`, `align_corners`, `padding_mode`, `sampling_mode`.
- Internal: list + padded representations for maps, verts_uvs, faces_uvs.
- `verts_uvs_padded()`, `faces_uvs_padded()`, `maps_padded()`.
- Reference: `pytorch3d/renderer/mesh/textures.py:TexturesUV` (full ~400 lines).

### Phase 22 — `TexturesUV.sample_textures()` — UV Interpolation
- Interpolate vertex UVs using barycentric coords → `pixel_uvs`.
- `F.grid_sample()` on texture maps using `pixel_uvs`.
- Handle `maps_ids` for multi-map textures.
- Handle `align_corners`, `padding_mode`, `sampling_mode`.
- Reference: `pytorch3d/renderer/mesh/textures.py:TexturesUV.sample_textures`.

### Phase 23 — `TexturesUV` Clone / Detach / To / Extend / GetItem
- `clone()`: clone all internal list + padded tensors.
- `detach()`: detach everything.
- `to(device)`: move all tensors.
- `extend(N)`: repeat textures N times.
- `__getitem__(index)`: subset batch, return new `TexturesUV`.
- Reference: `pytorch3d/renderer/mesh/textures.py`.

### Phase 24 — `TexturesAtlas` Implementation
- Store atlas as (N, F, R, R, C).
- `sample_textures()`: nearest-neighbor from barycentric coords.
- `clone()` / `detach()` / `to()`.
- Reference: `pytorch3d/renderer/mesh/textures.py:TexturesAtlas`.

### Phase 25 — `interpolate_face_attributes()` Ops
- Implement `interpolate_face_attributes(pix_to_face, bary_coords, face_attributes)`:
  - Gather face attributes using `pix_to_face`.
  - Weight by barycentric coords.
  - Return `(N, H, W, K, D)`.
- Reference: `pytorch3d/ops/interpolate_face_attributes.py`.

---

## Phase 26–32: Renderer Pipeline

### Phase 26 — `PerspectiveCameras` Full Implementation
- Store `R`, `T`, `focal_length`, `principal_point`, `image_size`, `in_ndc`.
- `get_world_to_view_transform()` → returns `Transform3d` with R|T.
- `get_ndc_camera_transform()` → NDC normalization.
- `transform_points_screen(points)` → NDC → screen pixel coords.
- `is_perspective()`, `get_znear()`, `get_zfar()`.
- `get_camera_center()` for specular lighting.
- Reference: `pytorch3d/renderer/cameras.py:PerspectiveCameras`.

### Phase 27 — `Transform3d` Class
- Composible transforms: `compose()`, `transform_points()`.
- Support `Translate`, `Scale`, `Rotate`, `RotateAxisAngle`.
- Reference: `pytorch3d/renderer/transforms.py`.

### Phase 28 — `PointLights` Implementation
- `__init__(ambient_color, diffuse_color, specular_color, location, device)`.
- `ambient(normals=...)`, `diffuse(normals=..., points=...)`, `specular(normals=..., points=..., camera_position=..., shininess=...)`.
- Reference: `pytorch3d/renderer/lighting.py:PointLights`.

### Phase 29 — `Materials` Implementation
- `ambient_color`, `diffuse_color`, `specular_color`, `shininess`.
- Reference: `pytorch3d/renderer/materials.py:Materials`.

### Phase 30 — `BlendParams` + Blending Functions
- `BlendParams` dataclass: `sigma`, `gamma`, `background_color`.
- `softmax_rgb_blend(colors, fragments, blend_params, znear, zfar)` — soft blending using alpha from dists.
- `sigmoid_alpha_blend(colors, fragments, blend_params)` — silhouette blending.
- `hard_rgb_blend(colors, fragments, blend_params)` — hard z-buffer.
- Reference: `pytorch3d/renderer/blending.py`.

### Phase 31 — `MeshRenderer` Correct Chain
- `__init__(rasterizer, shader)`.
- `forward(meshes_world)`: `fragments = self.rasterizer(meshes_world)` → `images = self.shader(fragments, meshes_world)`.
- `to(device)`: move rasterizer + shader.
- Reference: `pytorch3d/renderer/mesh/renderer.py:MeshRenderer`.

### Phase 32 — `MeshRendererWithFragments`
- Same as MeshRenderer but returns `(images, fragments)` tuple.
- Reference: `pytorch3d/renderer/mesh/renderer.py:MeshRendererWithFragments`.

---

## Phase 33–38: Shaders

### Phase 33 — `ShaderBase`
- `__init__(device, cameras, lights, materials, blend_params)`.
- `_get_cameras()` helper.
- `to(device)`.
- Reference: `pytorch3d/renderer/mesh/shader.py:ShaderBase`.

### Phase 34 — `SoftPhongShader.forward()` — Per-Pixel Lighting
- `forward(fragments, meshes)`:
  1. Get cameras, lights, materials.
  2. `texels = meshes.sample_textures(fragments)`.
  3. `phong_shading(meshes, fragments, texels, lights, cameras, materials)`.
  4. `softmax_rgb_blend(colors, fragments, blend_params)`.
- Reference: `pytorch3d/renderer/mesh/shader.py:SoftPhongShader`.

### Phase 35 — `SoftSilhouetteShader.forward()` — Silhouette
- `forward(fragments, meshes)`:
  1. `colors = torch.ones_like(fragments.bary_coords)`.
  2. `sigmoid_alpha_blend(colors, fragments, blend_params)`.
- Returns RGBA where alpha = silhouette probability.
- Reference: `pytorch3d/renderer/mesh/shader.py:SoftSilhouetteShader`.

### Phase 36 — `phong_shading()` Implementation
- `phong_shading(meshes, fragments, texels, lights, cameras, materials)`:
  1. Interpolate vertex normals via `interpolate_face_attributes`.
  2. Interpolate vertex positions (camera space).
  3. Compute ambient + diffuse + specular via `_apply_lighting`.
  4. `colors = (ambient + diffuse) * texels + specular`.
- Reference: `pytorch3d/renderer/mesh/shading.py:phong_shading`.

### Phase 37 — `cleanShader` for Normal Rendering
- Already in `code/renderer.py:cleanShader` — verify it works with our fragments.
- It calls `meshes.sample_textures(fragments)` → `softmax_rgb_blend(texels, fragments, blend_params)`.
- Must ensure `meshes.sample_textures` works with our `TexturesVertex` for normal rendering.
- Reference: `code/renderer.py:cleanShader`.

### Phase 38 — `HardPhongShader`, `HardGouraudShader`, `HardFlatShader`
- Stub implementations that call `hard_rgb_blend` instead of `softmax_rgb_blend`.
- Hard silhouette: `HardGouraudShader` with `TexturesVertex`.
- Reference: `pytorch3d/renderer/mesh/shader.py`.

---

## Phase 39–45: Ops + Loss

### Phase 39 — `SubdivideMeshes` Real Implementation
- Current stub returns meshes unchanged.
- Replace with loop subdivision (midpoint scheme) using pure pytorch.
  - For each face, create 4 sub-faces by bisecting edges.
  - Update vertex positions.
- This is needed for GarmentRec's `use_detail` path.
- Reference: `pytorch3d/ops/subdivide_meshes.py`.

### Phase 40 — `knn_points` with Actual Nearest Neighbor
- Current returns all zeros.
- Replace with brute-force KNN using `torch.cdist`:
  - `dists = torch.cdist(query, cloud)` → sort → top-K.
- Sufficient for GarmentRec's loss computation (batch size ~4, points ~6890).
- Reference: `pytorch3d/ops/knn.py`.

### Phase 41 — `mesh_laplacian_smoothing` + `mesh_normal_consistency`
- `mesh_laplacian_smoothing(meshes)`:
  - Compute Laplacian from `meshes.laplacian_packed()`.
  - `loss = (laplacian @ verts_packed).norm(dim=1).mean()`.
- `mesh_normal_consistency(meshes)`:
  - Compute normal consistency loss from face normals of adjacent faces.
- Reference: `pytorch3d/loss/__init__.py`, `pytorch3d/loss/mesh_laplacian_smoothing.py`, `pytorch3d/loss/mesh_normal_consistency.py`.

### Phase 42 — `mesh_face_areas_normals` (Pure PyTorch)
- Avoid C extension dependency.
- Compute face normals via cross product, areas via norm.
- `mesh_face_areas_normals(verts_packed, faces_packed)` → `(areas, normals)`.
- Used by `Meshes._compute_face_areas_normals()` and `Evaluator.py` (if called).
- Reference: `pytorch3d/ops/mesh_face_areas_normals.py`.

### Phase 43 — `packed_to_padded` / `padded_to_packed` in ops
- Move these from current ad-hoc implementations to match `pytorch3d/ops/__init__.py`.
- Reference: `pytorch3d/ops/__init__.py`.

### Phase 44 — `sample_textures_from_meshes` (if used)
- Some GarmentRec paths may call `meshes.sample_textures(fragments)` directly.
- Ensure this is delegated to `self.textures.sample_textures(fragments)`.
- Reference: not in real pytorch3d — `Meshes` delegates to `TexturesBase.sample_textures`.

### Phase 45 — TorchScript / JIT Stubs for Ops
- Add `@torch.jit.script` decorators to critical ops (edge_function, barycentric_coordinates) for performance.
- Not strictly required but helps if called repeatedly.

---

## Phase 46–49: Integration & Edge Cases

### Phase 46 — `renderer/mesh/__init__.py` Re-exports
- Ensure `pytorch3d.renderer.mesh` re-exports: `MeshRasterizer`, `MeshRenderer`, `RasterizationSettings`, `rasterize_meshes`, `SoftPhongShader`, `SoftSilhouetteShader`, `TexturesUV`, `TexturesVertex`, `TexturesAtlas`, `Fragments`.
- Reference: `pytorch3d/renderer/mesh/__init__.py`.

### Phase 47 — `np.float` Deprecation Fix in SMPL.py
- Replace the `sed` patch with a robust version guard in `SMPL.py`:
  ```python
  try:
      np.float  # NumPy >= 1.24 raises AttributeError
  except AttributeError:
      np.float = float
  ```
- Applied at import time in the notebook's install cell.

### Phase 48 — External Deps: `torch_scatter`, `openmesh`, `pymeshlab`, `torch_geometric`
- `torch_scatter`: used in `utils.py:2` — install via `pip install torch-scatter` matching torch version.
- `openmesh`: used for mesh processing — install via `pip install openmesh-python`.
- `pymeshlab`: used in `subdivide_mesh_by_meshlab` — install via `pip install pymeshlab`.
- `torch_geometric`: not directly used by inference path — skip unless needed.
- Add pip install commands to Cell 0 of notebook.

### Phase 49 — Non-square Image Handling
- `parse_image_size()`: handle `image_size` as int vs tuple.
- `non_square_ndc_range()`: adjust NDC range for non-square images.
- `pix_to_non_square_ndc()`: convert pixel coords to NDC for non-square.
- Reference: `pytorch3d/renderer/mesh/rasterize_meshes.py`.

---

## Phase 50: Deployment & Validation

### Phase 50 — End-to-End Test on Modal
1. Deploy updated notebook to Modal.
2. Load GarmentRec model.
3. Run reconstruction on a test image.
4. Verify:
   - `save_obj` produces valid OBJ + MTL + texture PNG.
   - `Renderer.forward(mesh)` returns non-zero images.
   - `Renderer.get_mask(mesh)` returns correct silhouette.
   - `Rendernderer.render_normal(mesh)` returns correct normal map.
5. Profile: measure inference time vs prior shim.
6. If rasterizer is too slow, add trimesh-based fallback:
   - Use `trimesh.scene.Scene` + `pyrender.OffscreenRenderer` for actual rendering.
   - Convert to tensor and return expected format.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    GarmentRec                            │
│  renderer.py  |  ImageReconstructModel.py  |  loss.py    │
└──────────┬──────────────────────────────┬────────────────┘
           │ pytorch3d imports            │ pytorch3d ops
           ▼                              ▼
┌─────────────────────────────────────────────────────────┐
│                    PyTorch3D Shim                         │
├──────────────┬──────────┬──────────┬─────────────────────┤
│ structures/  │ io/      │ renderer/│ ops/ + loss/         │
│ Meshes       │ load_obj │ MeshRast │ SubdivideMeshes      │
│ Textures     │ save_obj │ Shaders  │ knn_points           │
│ utils        │          │ Lighting │ laplacian            │
├──────────────┴──────────┴──────────┴─────────────────────┤
│           trimesh (fallback rasterizer)                   │
│           Pure PyTorch (primary rasterizer)               │
└─────────────────────────────────────────────────────────┘
```

## Key Design Decisions

1. **No CUDA dependencies**: All ops in pure PyTorch. The software rasterizer is slower than C++ but works on any GPU.
2. **trimesh fallback**: If pure-PyTorch rasterizer is too slow (>30s per frame), fall back to `pyrender.OffscreenRenderer` with osmesa.
3. **Lazy computation**: Meshes uses lazy `_compute_*` methods (matching pytorch3d) to avoid redundant computation.
4. **Subpackage re-exports**: `pytorch3d.renderer.mesh` re-exports from `pytorch3d.renderer` (not separate file) to match import patterns like `from pytorch3d.renderer.mesh import rasterize_meshes`.

## Success Criteria

| Criterion | Target |
|-----------|--------|
| `Renderer.forward(mesh)` | Non-zero RGBA image |
| `Renderer.get_mask(mesh)` | Correct silhouette (face pixels = 1, background = 0) |
| `save_obj()` | Valid OBJ + MTL + texture PNG |
| `SubdivideMeshes` | Actually subdivides (not identity) |
| `knn_points` | Returns real nearest-neighbor distances |
| `load_obj()` | Returns `(verts, faces, aux)` with correct UV data |
| `Meshes.clone()/to()/detach()` | Deep copy works without shared pointers |
| Inference time | < 60s per image (on T4 with soft rasterizer) |
