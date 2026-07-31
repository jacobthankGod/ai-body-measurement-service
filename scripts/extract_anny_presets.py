#!/usr/bin/env python3
"""
Extract Anny body model presets for browser runtime.

Generates:
  - Preset binaries (anny_model.json + anny_model.bin) for each body type
  - Sparse phenotype deltas (anny_deltas.json) for slider interpolation

Output: public/models/anny/
"""

import json
import sys
import time
import numpy as np
from pathlib import Path

import anny
import torch


PRESETS = {
    "baby": {
        "gender": 0.5, "age": -0.2, "weight": 0.3, "muscle": 0.3,
        "height": 0.1, "proportions": 0.5, "cupsize": 0.5, "firmness": 0.5,
        "african": 0.0, "asian": 0.0, "caucasian": 1.0,
    },
    "child": {
        "gender": 0.5, "age": 0.0, "weight": 0.3, "muscle": 0.4,
        "height": 0.2, "proportions": 0.5, "cupsize": 0.5, "firmness": 0.5,
        "african": 0.0, "asian": 0.0, "caucasian": 1.0,
    },
    "male_slim": {
        "gender": 0.0, "age": 0.3, "weight": 0.25, "muscle": 0.6,
        "height": 0.55, "proportions": 0.5, "cupsize": 0.5, "firmness": 0.5,
        "african": 0.0, "asian": 0.0, "caucasian": 1.0,
    },
    "male_avg": {
        "gender": 0.0, "age": 0.3, "weight": 0.45, "muscle": 0.5,
        "height": 0.55, "proportions": 0.5, "cupsize": 0.5, "firmness": 0.5,
        "african": 0.0, "asian": 0.0, "caucasian": 1.0,
    },
    "male_heavy": {
        "gender": 0.0, "age": 0.3, "weight": 0.70, "muscle": 0.4,
        "height": 0.55, "proportions": 0.5, "cupsize": 0.5, "firmness": 0.5,
        "african": 0.0, "asian": 0.0, "caucasian": 1.0,
    },
    "male_xl": {
        "gender": 0.0, "age": 0.3, "weight": 0.85, "muscle": 0.35,
        "height": 0.55, "proportions": 0.5, "cupsize": 0.5, "firmness": 0.5,
        "african": 0.0, "asian": 0.0, "caucasian": 1.0,
    },
    "male_xxl": {
        "gender": 0.0, "age": 0.3, "weight": 0.95, "muscle": 0.30,
        "height": 0.55, "proportions": 0.5, "cupsize": 0.5, "firmness": 0.5,
        "african": 0.0, "asian": 0.0, "caucasian": 1.0,
    },
    "female_slim": {
        "gender": 1.0, "age": 0.3, "weight": 0.20, "muscle": 0.4,
        "height": 0.50, "proportions": 0.5, "cupsize": 0.3, "firmness": 0.5,
        "african": 0.0, "asian": 0.0, "caucasian": 1.0,
    },
    "female_avg": {
        "gender": 1.0, "age": 0.3, "weight": 0.40, "muscle": 0.3,
        "height": 0.50, "proportions": 0.5, "cupsize": 0.5, "firmness": 0.5,
        "african": 0.0, "asian": 0.0, "caucasian": 1.0,
    },
    "female_heavy": {
        "gender": 1.0, "age": 0.3, "weight": 0.65, "muscle": 0.25,
        "height": 0.50, "proportions": 0.5, "cupsize": 0.6, "firmness": 0.5,
        "african": 0.0, "asian": 0.0, "caucasian": 1.0,
    },
    "female_pregnant": {
        "gender": 1.0, "age": 0.3, "weight": 0.50, "muscle": 0.25,
        "height": 0.50, "proportions": 0.5, "cupsize": 0.5, "firmness": 0.5,
        "african": 0.0, "asian": 0.0, "caucasian": 1.0,
        "_local_changes": {"stomach-pregnant-incr": 0.8},
    },
    "female_xl": {
        "gender": 1.0, "age": 0.3, "weight": 0.80, "muscle": 0.20,
        "height": 0.50, "proportions": 0.5, "cupsize": 0.7, "firmness": 0.5,
        "african": 0.0, "asian": 0.0, "caucasian": 1.0,
    },
    "female_xxl": {
        "gender": 1.0, "age": 0.3, "weight": 0.92, "muscle": 0.15,
        "height": 0.50, "proportions": 0.5, "cupsize": 0.75, "firmness": 0.5,
        "african": 0.0, "asian": 0.0, "caucasian": 1.0,
    },
}


def build_blendshape_coeffs(model, params):
    pheno_kwargs = {k: float(v) for k, v in params.items() if k != "_local_changes"}
    with torch.no_grad():
        coeffs = model.get_phenotype_blendshape_coefficients(**pheno_kwargs)
    return coeffs


def extract_preset(model, name, params, out_dir):
    print(f"  {name} ...", end=" ", flush=True)
    t0 = time.time()

    with torch.no_grad():
        coeffs = build_blendshape_coeffs(model, params)
        rest_verts = model.get_rest_vertices(coeffs)
        _, _, rest_bone_poses = model.get_rest_bone_poses(coeffs)

    rest_verts_np = rest_verts[0].cpu().numpy().astype(np.float32)
    rest_bone_poses_np = rest_bone_poses[0].cpu().numpy().astype(np.float32)
    faces_np = model.faces.cpu().numpy().astype(np.int32)
    weights_np = model.vertex_bone_weights.cpu().numpy().astype(np.float32)
    indices_np = model.vertex_bone_indices.cpu().numpy().astype(np.int32)
    bone_parents = list(model.bone_parents)
    bone_labels = list(model.bone_labels)

    arrays = {
        "rest_vertices":   rest_verts_np,
        "faces":           faces_np,
        "bone_weights":    weights_np,
        "bone_indices":    indices_np,
        "rest_bone_poses": rest_bone_poses_np,
    }

    preset_dir = out_dir / name
    preset_dir.mkdir(parents=True, exist_ok=True)
    bin_path = preset_dir / "anny_model.bin"
    manifest_path = preset_dir / "anny_model.json"

    offset = 0
    manifest_arrays = {}
    chunks = []
    for arr_name, arr in arrays.items():
        raw = arr.tobytes()
        manifest_arrays[arr_name] = {
            "dtype": arr.dtype.str,
            "shape": list(arr.shape),
            "offset": offset,
            "bytes": len(raw),
        }
        chunks.append(raw)
        offset += len(raw)

    with open(bin_path, "wb") as f:
        for chunk in chunks:
            f.write(chunk)

    manifest = {
        "version": 1,
        "bone_count": model.bone_count,
        "vert_count": int(rest_verts_np.shape[0]),
        "face_count": int(faces_np.shape[0]),
        "max_bones_per_vert": int(weights_np.shape[1]),
        "arrays": manifest_arrays,
        "bone_parents": bone_parents,
        "bone_labels": bone_labels,
        "baked_params": {k: v for k, v in params.items() if k != "_local_changes"},
    }
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    elapsed = time.time() - t0
    print(f"done ({offset // 1024} KB, {elapsed:.1f}s)")


def extract_deltas(model, out_dir):
    print("Extracting sparse phenotype deltas ...", flush=True)
    t0 = time.time()

    base_params = {k: 0.5 for k in model.phenotype_labels}
    base_params["age"] = 0.3
    base_params["african"] = 0.0
    base_params["asian"] = 0.0
    base_params["caucasian"] = 1.0

    with torch.no_grad():
        base_coeffs = build_blendshape_coeffs(model, base_params)
        base_verts = model.get_rest_vertices(base_coeffs)[0]

    deltas = {}
    for param_name in model.phenotype_labels:
        if param_name in ["african", "asian", "caucasian"]:
            continue

        for value in [0.0, 1.0]:
            test_params = base_params.copy()
            test_params[param_name] = value
            with torch.no_grad():
                test_coeffs = build_blendshape_coeffs(model, test_params)
                test_verts = model.get_rest_vertices(test_coeffs)[0]

            delta = test_verts - base_verts
            max_per_vert = delta.abs().max(dim=1).values
            mask = max_per_vert > 0.0001
            indices = mask.nonzero(as_tuple=False).squeeze(1)

            if indices.numel() == 0:
                continue

            sparse_delta = delta[indices]
            key = f"{param_name}_{value}"
            deltas[key] = {
                "indices": indices.cpu().numpy().tolist(),
                "dx": sparse_delta[:, 0].cpu().numpy().tolist(),
                "dy": sparse_delta[:, 1].cpu().numpy().tolist(),
                "dz": sparse_delta[:, 2].cpu().numpy().tolist(),
            }
            print(f"  {param_name}={value}: {indices.numel()} verts")

    delta_path = out_dir / "anny_deltas.json"
    with open(delta_path, "w") as f:
        json.dump(deltas, f)

    elapsed = time.time() - t0
    print(f"Wrote {delta_path} ({delta_path.stat().st_size // 1024} KB, {elapsed:.1f}s)")


def main():
    out_dir = Path(__file__).parent.parent / "public" / "models" / "anny"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Creating Anny fullbody model ...", flush=True)
    t0 = time.time()
    model = anny.create_fullbody_model(
        all_phenotypes=True, triangulate_faces=True, local_changes=True
    ).to(dtype=torch.float32)
    print(f"  bones={model.bone_count}  verts={model.template_vertices.shape[0]}"
          f"  faces={model.faces.shape[0]}  ({time.time()-t0:.1f}s)")

    print(f"\nExtracting {len(PRESETS)} presets ...")
    for name, params in PRESETS.items():
        extract_preset(model, name, params, out_dir)

    extract_deltas(model, out_dir)

    print(f"\nAll done! Files in {out_dir}/")


if __name__ == "__main__":
    main()
