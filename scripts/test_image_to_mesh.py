#!/usr/bin/env python3
"""Full image-to-TailorNet-mesh pipeline test.

Usage:
    python scripts/test_image_to_mesh.py [image_path] [height_cm] [gender]

If no image provided, uses UniData S001_front.jpg as default.
"""
import os, sys, time, json, numpy as np
os.environ['OMP_NUM_THREADS'] = '1'

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, 'api', 'services'))

from pathlib import Path

def main():
    image_path = sys.argv[1] if len(sys.argv) > 1 else 'data/unidata/S001_front.jpg'
    height_cm = float(sys.argv[2]) if len(sys.argv) > 2 else 175.0
    gender = sys.argv[3] if len(sys.argv) > 3 else 'male'

    print('=' * 60)
    print(' IMAGE -> TAILORNET MESH PIPELINE')
    print('=' * 60)
    print('  Image:', image_path)
    print('  Height:', height_cm, 'cm')
    print('  Gender:', gender)

    if not os.path.exists(image_path):
        print('  ERROR: Image not found:', image_path)
        sys.exit(1)

    # Step 1: HMR extraction
    print('\n--- Step 1: HMR Body Parameter Extraction ---')
    from PIL import Image
    img = Image.open(image_path)
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    image_array = np.array(img)
    t0 = time.time()
    from extract_measurements import extract_measurements_from_hmr
    result = extract_measurements_from_hmr(image_array, height_cm, gender)
    hmr_time = time.time() - t0

    measurements, vertices, landmarks, body_shape, size_rec, error, mesh_tpose, smpl_params, joints3d = result

    if error:
        print('  HMR WARNING:', error)

    print('  HMR time: %.1fs' % hmr_time)
    print('  Measurements:', len(measurements), 'values')
    if smpl_params:
        shape = smpl_params.get('shape', [])
        print('  SMPL shape:', [round(x, 4) for x in shape[:5]])
        has_betas300 = smpl_params.get('betas_300') is not None
        print('  SMPL betas_300:', 'yes' if has_betas300 else 'no')

    # Step 2: Prepare betas
    print('\n--- Step 2: Prepare Betas ---')
    if smpl_params and smpl_params.get('betas_300') is not None:
        betas = np.array(smpl_params['betas_300'], dtype=np.float32)
        print('  Using 300-dim betas from projection')
    elif smpl_params and smpl_params.get('shape'):
        raw = smpl_params['shape']
        betas = np.zeros(300, dtype=np.float32)
        betas[:min(len(raw), 10)] = np.array(raw[:10], dtype=np.float32)
        print('  Using 10-dim betas (padded to 300)')
    else:
        betas = np.zeros(300, dtype=np.float32)
        print('  No SMPL params - using zero betas')

    print('  betas[:10]:', betas[:10].round(4).tolist())

    # Step 3: TailorNet body mesh
    print('\n--- Step 3: TailorNet Body Mesh (SMPL4Garment) ---')
    t0 = time.time()
    from tailornet.models.smpl4garment import SMPL4Garment
    import trimesh

    smpl = SMPL4Garment(gender, body_only=True)
    body_m, _ = smpl.run(beta=betas)
    body_time = time.time() - t0

    body_verts = np.array(body_m.v, dtype=np.float32)
    body_faces = np.array(body_m.f, dtype=np.int32)
    print('  Body mesh:', body_verts.shape, 'verts,', body_faces.shape, 'faces')
    print('  Time: %.1fs' % body_time)
    print('  BBox X: [%.3f, %.3f]' % (body_verts[:,0].min(), body_verts[:,0].max()))
    print('  BBox Y: [%.3f, %.3f]' % (body_verts[:,1].min(), body_verts[:,1].max()))
    print('  BBox Z: [%.3f, %.3f]' % (body_verts[:,2].min(), body_verts[:,2].max()))

    out_dir = Path('public/meshes/test')
    out_dir.mkdir(parents=True, exist_ok=True)
    body_path = out_dir / 'test_tailornet_body.obj'
    bm = trimesh.Trimesh(vertices=body_verts, faces=body_faces, process=False)
    bm.export(str(body_path))
    print('  Saved:', body_path, '(%d bytes)' % body_path.stat().st_size)

    # Step 4: TailorNet garment mesh
    print('\n--- Step 4: TailorNet Garment Mesh (t-shirt) ---')
    t0 = time.time()
    from tailornet_bridge import run_tailornet

    garment_result = run_tailornet('t-shirt', gender, betas=betas)
    garment_time = time.time() - t0

    if garment_result['success']:
        gv = garment_result['garment_verts']
        gf = garment_result['garment_faces']
        print('  Garment mesh:', gv.shape, 'verts,', gf.shape, 'faces')
        print('  Time: %.1fs' % garment_time)

        gar_path = out_dir / 'test_tailornet_garment.obj'
        gm = trimesh.Trimesh(vertices=gv, faces=gf, process=False)
        gm.export(str(gar_path))
        print('  Saved:', gar_path, '(%d bytes)' % gar_path.stat().st_size)
    else:
        print('  Garment FAILED:', garment_result['error'][:200])

    # Step 5: Measurements from extracted body
    print('\n--- Step 5: Key Measurements ---')
    for k in ['Chest Round', 'Waist Round', 'Hip Round', 'Shoulder', 'Neck Round', 'Thigh Round']:
        v = measurements.get(k, 0)
        print('  %s: %.1f cm' % (k, v))

    # Summary
    print('\n--- Pipeline Summary ---')
    print('  HMR extraction: %.1fs' % hmr_time)
    print('  TailorNet body: %.1fs' % body_time)
    print('  TailorNet garment: %.1fs' % garment_time)
    print('  Total: %.1fs' % (hmr_time + body_time + garment_time))
    print()
    print('  Output files:')
    print('   ', body_path)
    if garment_result['success']:
        print('   ', gar_path)
    print()
    print('DONE')

if __name__ == '__main__':
    main()
