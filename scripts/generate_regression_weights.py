#!/usr/bin/env python3
"""Generate measurement-to-beta regression weights (batched, memory-efficient)."""

import json, os, numpy as np
from sklearn.linear_model import Ridge

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(PROJECT_ROOT, 'public', 'assets', 'smpl_regression_weights.json')
NUM_BETAS = 10
BATCH = 2000
TOTAL = 10000

def ellipse_circ(w, d):
    a, b = w / 2, d / 2
    denom = np.maximum(a + b, 1e-6)
    h_val = ((a - b) ** 2) / (denom ** 2)
    return np.pi * (a + b) * (1 + (3 * h_val) / (10 + np.sqrt(np.maximum(4 - 3 * h_val, 0))))

def measure_batch(vertices, all_heights):
    N = vertices.shape[0]
    v_min_y = vertices[:, :, 1].min(axis=1)
    v_max_y = vertices[:, :, 1].max(axis=1)
    v_height = v_max_y - v_min_y
    scale = all_heights / (v_height * 100)
    band = v_height * 0.03

    def at_y(y_pos):
        mask = np.abs(vertices[:, :, 1] - y_pos[:, None]) < band[:, None]
        xv = np.where(mask, vertices[:, :, 0], np.nan)
        zv = np.where(mask, vertices[:, :, 2], np.nan)
        w = (np.nanmax(xv, axis=1) - np.nanmin(xv, axis=1)) * 100 * scale
        d = (np.nanmax(zv, axis=1) - np.nanmin(zv, axis=1)) * 100 * scale
        return ellipse_circ(w, d)

    chest_y = v_min_y + v_height * 0.85
    waist_y = v_min_y + v_height * 0.70
    hip_y = v_min_y + v_height * 0.55
    thigh_y = v_min_y + v_height * 0.25

    chest = at_y(chest_y)
    waist = at_y(waist_y)
    hip = at_y(hip_y)
    thigh = at_y(thigh_y)

    # Shoulder
    sh_y = chest_y + 0.015
    sh_mask = np.abs(vertices[:, :, 1] - sh_y[:, None]) < 0.012
    sh_x = np.where(sh_mask, vertices[:, :, 0], np.nan)
    shoulder = (np.nanmax(sh_x, axis=1) - np.nanmin(sh_x, axis=1)) * 100 * scale

    # Bicep
    bicep_y = v_min_y + v_height * 0.80
    arm_mask = (np.abs(vertices[:, :, 0]) > 0.15) & (np.abs(vertices[:, :, 1] - bicep_y[:, None]) < band[:, None])
    lm = arm_mask & (vertices[:, :, 0] < 0)
    rm = arm_mask & (vertices[:, :, 0] > 0)
    lx = np.where(lm, vertices[:, :, 0], np.nan); lz = np.where(lm, vertices[:, :, 2], np.nan)
    rx = np.where(rm, vertices[:, :, 0], np.nan); rz = np.where(rm, vertices[:, :, 2], np.nan)
    bicep = (ellipse_circ((np.nanmax(lx,1)-np.nanmin(lx,1))*100*scale, (np.nanmax(lz,1)-np.nanmin(lz,1))*100*scale) +
             ellipse_circ((np.nanmax(rx,1)-np.nanmin(rx,1))*100*scale, (np.nanmax(rz,1)-np.nanmin(rz,1))*100*scale)) / 2

    return np.column_stack([chest, waist, hip, shoulder, thigh, bicep, all_heights])

def main():
    print("Loading SMPL...")
    v_template = np.load(os.path.join(PROJECT_ROOT, 'models', 'v_template.npy'))
    shapedirs = np.load(os.path.join(PROJECT_ROOT, 'models', 'shapedirs.npy'))
    sd = shapedirs.reshape(6890, 3, NUM_BETAS)

    np.random.seed(42)
    labels = ['chest', 'waist', 'hip', 'shoulder', 'thigh', 'bicep', 'height']
    all_betas_list, all_meas_list = [], []

    for start in range(0, TOTAL, BATCH):
        n = min(BATCH, TOTAL - start)
        print(f"  Batch {start//BATCH+1}: {n} shapes...")
        betas = np.random.randn(n, NUM_BETAS).clip(-3, 3)
        heights = np.random.uniform(155, 200, n)
        verts = v_template[None,:,:] + np.einsum('ijk,nk->nij', sd, betas)
        meas = measure_batch(verts, heights)
        valid = np.all(np.isfinite(meas) & (meas > 0), axis=1)
        all_betas_list.append(betas[valid])
        all_meas_list.append(meas[valid])

    all_betas = np.vstack(all_betas_list)
    all_meas = np.vstack(all_meas_list)
    print(f"Total valid: {len(all_betas)}")

    for j, l in enumerate(labels):
        print(f"  {l}: {all_meas[:,j].min():.1f} - {all_meas[:,j].max():.1f}")

    mean = all_meas.mean(0); std = all_meas.std(0); std[std<1e-6]=1
    norm = (all_meas - mean) / std

    ridge = Ridge(alpha=1.0).fit(norm, all_betas)
    print(f"R² = {ridge.score(norm, all_betas):.4f}")

    out = {
        "male": {"weights": ridge.coef_.tolist(), "bias": ridge.intercept_.tolist(),
                 "measurements_mean": mean.tolist(), "measurements_std": std.tolist()},
        "female": {"weights": ridge.coef_.tolist(), "bias": ridge.intercept_.tolist(),
                   "measurements_mean": mean.tolist(), "measurements_std": std.tolist()},
        "measurement_order": labels, "num_betas": NUM_BETAS
    }
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(out, f, indent=2)
    print(f"Saved: {OUTPUT_PATH} ({os.path.getsize(OUTPUT_PATH)} bytes)")

if __name__ == '__main__':
    main()
