"""
Garment reconstruction evaluation using the Korosteleva Zenodo dataset.

Dataset: https://doi.org/10.5281/zenodo.5267549 (NeurIPS 2021)

Usage on Kaggle (as a notebook cell):
    python scripts/evaluate_garment_zenodo.py --kaggle --download test --limit 50

Usage locally (list only):
    python scripts/evaluate_garment_zenodo.py --list

Pipeline per garment:
    1. Load GT OBJ mesh + sewing pattern from Zenodo
    2. Render front-view 2D image
    3. Run GarmentRec reconstruction
    4. Compute Chamfer distance (GT mesh vs reconstructed mesh)
    5. Save per-garment + aggregate results to JSON
"""

import argparse
import gc
import io
import json
import os
import sys
import tempfile
import zipfile
import urllib.request
from pathlib import Path
from datetime import datetime

import numpy as np
from PIL import Image

ZENODO_BASE = "https://zenodo.org/records/5267549/files"

GARMENT_SETS = {
    "test": {"test.zip": "4.0 GB"},
    "tee": {"tee_2300.zip": "9.1 GB"},
    "tee_sleeveless": {"tee_sleeveless_1800.zip": "6.7 GB"},
    "pants": {"pants_straight_sides_1000.zip": "2.1 GB"},
    "dress": {"dress_sleeveless_2550.zip": "7.4 GB"},
    "jacket": {"jacket_2200.zip": "9.9 GB"},
    "allsets": {k: v for d in [
        {"test.zip": "4.0 GB"},
        {"tee_2300.zip": "9.1 GB"},
        {"tee_sleeveless_1800.zip": "6.7 GB"},
        {"pants_straight_sides_1000.zip": "2.1 GB"},
        {"dress_sleeveless_2550.zip": "7.4 GB"},
        {"jacket_2200.zip": "9.9 GB"},
    ] for k, v in d.items()},
}


def download_zip(url: str, dest: Path):
    """Download a file from URL to dest with progress."""
    print(f"  Downloading {dest.name}...")
    urllib.request.urlretrieve(url, str(dest))
    size_mb = dest.stat().st_size / (1024 * 1024)
    print(f"  Saved {dest.name} ({size_mb:.0f} MB)")


def extract_and_index(zip_path: Path, extract_dir: Path):
    """Extract ZIP and build garment index."""
    extract_dir.mkdir(parents=True, exist_ok=True)
    garments = []

    with zipfile.ZipFile(str(zip_path), "r") as zf:
        names = zf.namelist()
        folders = set()
        for name in names:
            parts = name.strip("/").split("/")
            if len(parts) >= 2:
                folders.add("/".join(parts[:2]))
        print(f"  {zip_path.name}: {len(folders)} garments")
        zf.extractall(str(extract_dir))

    for folder in sorted(folders):
        folder_path = extract_dir / folder
        if not folder_path.is_dir():
            continue
        obj_files = sorted(folder_path.glob("*.obj"))
        json_files = sorted(folder_path.glob("*.json"))
        if obj_files:
            garments.append({
                "id": folder.replace("/", "_"),
                "folder": str(folder_path),
                "obj": [str(f) for f in obj_files],
                "json": [str(f) for f in json_files],
                "type": folder.split("/")[0],
            })

    return garments


def render_mesh(obj_path: str, resolution: int = 540) -> Image.Image:
    """Render OBJ to front-view 2D image using trimesh + pyrender."""
    try:
        import trimesh
        import pyrender
    except ImportError:
        try:
            import trimesh
            mesh = trimesh.load(obj_path)
            scene = trimesh.Scene(mesh)
            data = scene.save_image(resolution=[resolution, resolution])
            return Image.open(io.BytesIO(data)).convert("RGB")
        except Exception as e:
            print(f"    Cannot render {Path(obj_path).name}: {e}")
            return Image.new("RGB", (resolution, resolution), (128, 128, 128))

    mesh = trimesh.load(obj_path)
    centroid = mesh.vertices.mean(axis=0)
    mesh.vertices -= centroid
    scale = np.max(np.abs(mesh.vertices))
    if scale > 0:
        mesh.vertices /= scale * 1.1

    scene = pyrender.Scene()
    scene.add(pyrender.Mesh.from_trimesh(mesh))
    camera = pyrender.PerspectiveCamera(yfov=np.pi / 3.0)
    pose = np.eye(4)
    pose[2, 3] = 2.5
    scene.add(camera, pose=pose)
    scene.add(pyrender.DirectionalLight(color=[1, 1, 1], intensity=2.0), pose=pose)

    r = pyrender.OffscreenRenderer(resolution, resolution)
    color, _ = r.render(scene)
    r.delete()
    return Image.fromarray(color).convert("RGB")


def chamfer_distance(gt_verts, pred_verts):
    """Symmetric Chamfer distance via KDTree."""
    from scipy.spatial import KDTree
    d1 = KDTree(gt_verts).query(pred_verts)[0].mean()
    d2 = KDTree(pred_verts).query(gt_verts)[0].mean()
    return float(d1 + d2) / 2.0


def evaluate_one(garment: dict, render_dir: Path, models: dict) -> dict:
    """Evaluate a single garment against reconstruction models."""
    result = {
        "id": garment["id"],
        "type": garment["type"],
        "errors": [],
        "metrics": {},
    }

    gt_obj = garment["obj"][0] if garment["obj"] else None
    if not gt_obj:
        result["errors"].append("No OBJ")
        return result

    try:
        import trimesh
        gt = trimesh.load(gt_obj)
        gt_verts = gt.vertices
        result["metrics"]["gt_vertices"] = len(gt_verts)
        result["metrics"]["gt_faces"] = len(gt.faces)
    except Exception as e:
        result["errors"].append(f"Load mesh: {e}")
        return result

    # Render
    if render_dir:
        try:
            img = render_mesh(gt_obj)
            path = render_dir / f"{garment['id']}.png"
            path.parent.mkdir(parents=True, exist_ok=True)
            img.save(str(path))
        except Exception as e:
            result["errors"].append(f"Render: {e}")

    # Reconstruct with GarmentRec
    if models.get("garmentrec"):
        try:
            import torch
            import cv2
            img = render_mesh(gt_obj)
            net = models["garmentrec"]
            tmp = tempfile.mkdtemp()
            net.mesh_save_folder = tmp

            img_np = np.array(img.convert("RGB"))
            img_np = cv2.resize(img_np, (540, 540)).astype(np.float32) / 255.0
            t = torch.from_numpy(img_np).permute(2, 0, 1).unsqueeze(0).to("cpu")
            cam_k = torch.Tensor([[3.0375e03, 0.0, 270.0], [0.0, 3.0375e03, 270.0], [0.0, 0.0, 1.0]])
            names = np.array(["input.png"])
            imgs = torch.cat((t, t), 1).reshape(-1, 3, 540, 540)

            with torch.no_grad():
                up_prob, bot_prob, _, _, _ = net(t, names, gtypes=np.array([[-1, -1]]), cam_k=cam_k, imgs_perg=imgs)

            up_idx = up_prob.argmax(dim=1).item()
            bot_idx = bot_prob.argmax(dim=1).item()
            up_names = ["T-shirt", "front_open_T-shirt", "Shirt", "front_open_Shirt"]
            bot_names = ["Shorts", "Pants"]
            bi = bot_idx if bot_idx < 4 else bot_idx - 4
            result["metrics"]["predicted"] = f"{up_names[up_idx]}_{bot_names[bi]}"
            result["metrics"]["gt_type"] = garment["type"]

            up_path = os.path.join(tmp, "input_up.obj")
            if os.path.exists(up_path):
                pred = trimesh.load(up_path)
                result["metrics"]["chamfer_upper"] = chamfer_distance(gt_verts, pred.vertices)
                result["metrics"]["pred_upper_verts"] = len(pred.vertices)

            bot_path = os.path.join(tmp, "input_bottom.obj")
            if os.path.exists(bot_path):
                pred = trimesh.load(bot_path)
                result["metrics"]["chamfer_lower"] = chamfer_distance(gt_verts, pred.vertices)
                result["metrics"]["pred_lower_verts"] = len(pred.vertices)

            gc.collect()
        except Exception as e:
            result["errors"].append(f"GarmentRec: {e}")
            import traceback
            result["errors"].append(traceback.format_exc()[-300:])

    return result


def main():
    parser = argparse.ArgumentParser(description="Evaluate garment reconstruction on Zenodo dataset")
    parser.add_argument("--kaggle", action="store_true", help="Kaggle mode: auto-download, no prompts")
    parser.add_argument("--download", choices=list(GARMENT_SETS.keys()) + ["none"], default="none")
    parser.add_argument("--data-dir", type=str, default=None)
    parser.add_argument("--output-dir", type=str, default=None)
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--garmentrec-dir", type=str, default="/kaggle/working/GarmentRec")
    parser.add_argument("--zip", type=str, default=None)

    args = parser.parse_args()

    if args.list:
        print("Available garment sets:")
        for name, files in GARMENT_SETS.items():
            sizes = ", ".join(f"{k} ({v})" for k, v in files.items())
            print(f"  {name}: {sizes}")
        return

    if args.kaggle:
        data_dir = Path(args.data_dir or "/kaggle/working/zenodo_data")
        output_dir = Path(args.output_dir or "/kaggle/working")
    else:
        data_dir = Path(args.data_dir or "/tmp/zenodo_garments")
        output_dir = Path(args.output_dir or "/tmp/zenodo_eval")

    output_dir.mkdir(parents=True, exist_ok=True)
    render_dir = output_dir / "renders"

    # Load GarmentRec model
    models = {}
    if Path(args.garmentrec_dir).exists():
        print("Loading GarmentRec...")
        sys.path.insert(0, str(Path(args.garmentrec_dir) / "code"))
        sys.path.insert(0, str(Path(args.garmentrec_dir)))
        from module.ImageReconstructModel import ImageReconstructModel
        from module.SkinWeightModel import SkinWeightNet
        import pickle as pkl
        import torch

        gar_dir = Path(args.garmentrec_dir) / "code"
        smpl_path = gar_dir.parent / "smpl_pytorch" / "model" / "neutral_smpl_with_cocoplus_reg.txt"
        midpairs = pkl.load(open(gar_dir.parent / "data" / "midpairs.pkl", "rb"))
        dense_midpairs = pkl.load(open(gar_dir.parent / "data" / "dense_midpairs.pkl", "rb"))

        net = ImageReconstructModel(
            SkinWeightNet(4, True), with_classification=True,
            tran_mean=[0.0, 0.0, 0.0],
            garments=["T-shirt", "front_open_T-shirt", "Shirt", "front_open_Shirt", "Shorts", "Pants"],
            garmentvnums=[1954, 1954, 2468, 2468, 678, 1180],
            upper_type_num=4, pca_folder=str(gar_dir.parent / "data" / "tmps"), pca_dim=64,
            smpl_model_path=str(smpl_path), midpairs=midpairs,
            infer_camera=True, infer_tex=True, inferring=True, use_detail=True,
            mesh_save_folder=None, vis_save_folder=None,
            dense_template_folder=str(gar_dir.parent / "data"),
            displacement_scale=0.005, upsample_dismap=False, use_neighbor=True,
            device="cpu",
        )
        state = torch.load(str(gar_dir.parent / "models" / "mrf_0.1_shading_0.1" / "mrf_0.1_shading_0.1_pca64_ep100_bth0.pth"), map_location="cpu")
        net.load_state_dict(state, strict=False)
        net.eval()
        models["garmentrec"] = net
        print("  GarmentRec loaded")
    else:
        print(f"  GarmentRec not found at {args.garmentrec_dir}, will skip reconstruction")

    # Download dataset
    if args.download != "none":
        files = GARMENT_SETS.get(args.download, {})
        for fname, _ in files.items():
            zip_path = data_dir / fname
            if zip_path.exists():
                print(f"  {fname} already exists, skipping download")
                continue
            zip_path.parent.mkdir(parents=True, exist_ok=True)
            download_zip(f"{ZENODO_BASE}/{fname}?download=1", zip_path)

    # Extract
    garments = []
    if args.zip:
        zip_path = Path(args.zip)
        if zip_path.exists():
            garments = extract_and_index(zip_path, data_dir / zip_path.stem)
    elif args.download != "none":
        for fname in GARMENT_SETS.get(args.download, {}):
            zip_path = data_dir / fname
            if zip_path.exists():
                garments.extend(extract_and_index(zip_path, data_dir / zip_path.stem))

    if not garments:
        print("No garments found. Use --download or --zip.")
        return

    if args.limit > 0:
        garments = garments[:args.limit]

    print(f"Evaluating {len(garments)} garments...")
    all_results = []
    for i, g in enumerate(garments):
        if args.kaggle:
            print(f"  [{i+1}/{len(garments)}] {g['id']}...")
        else:
            print(f"  [{i+1}/{len(garments)}] {g['id']}")
        r = evaluate_one(g, render_dir, models)
        all_results.append(r)

        if r["metrics"]:
            for k, v in r["metrics"].items():
                if isinstance(v, float):
                    print(f"    {k}: {v:.4f}")
        for err in r["errors"][:2]:
            print(f"    ERR: {err[:120]}")

    # Aggregate
    print("\n=== AGGREGATE ===")
    keys = set()
    for r in all_results:
        keys.update(r["metrics"].keys())
    agg = {}
    for key in sorted(keys):
        vals = [r["metrics"][key] for r in all_results if key in r["metrics"] and isinstance(r["metrics"][key], (int, float))]
        if vals:
            agg[key] = {
                "mean": float(np.mean(vals)),
                "std": float(np.std(vals)),
                "min": float(np.min(vals)),
                "max": float(np.max(vals)),
                "n": len(vals),
            }
            print(f"  {key}: {agg[key]['mean']:.4f} +/- {agg[key]['std']:.4f}  [{agg[key]['min']:.4f}, {agg[key]['max']:.4f}]  (n={agg[key]['n']})")

    # Save
    output = {
        "timestamp": datetime.utcnow().isoformat(),
        "args": vars(args),
        "n_garments": len(all_results),
        "n_errors": sum(1 for r in all_results if r["errors"]),
        "aggregate": agg,
        "per_garment": all_results,
    }
    out_path = output_dir / "eval_results.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
