#!/usr/bin/env python3
"""
Train Shape Prior from Dataset SMPL Parameters
================================================
Learns a Gaussian Mixture Model over the 10-dim SMPL shape space.
The GMM is used at inference time to:
  1. Compute log-likelihood of predicted shapes
  2. Shrink implausible shapes toward nearest cluster mean
  3. Flag anomalous predictions

Usage:
    python scripts/train_shape_prior.py \\
        --dataset-dir data/training_dataset/v1 \\
        --output-dir api/models/priors \\
        --version 1 \\
        --plot

Output:
    shape_prior_gmm.pkl       — GMM model (pickle)
    shape_scaler.pkl          — StandardScaler (pickle)
    shape_scaler.json         — Scaler params (JSON, human-readable)
    shape_prior_gmm.json      — GMM params (JSON, inspection)
"""
import os
import sys
import json
import argparse
import logging
import pickle
from pathlib import Path
from typing import List, Tuple, Optional

import numpy as np
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("SHAPE_PRIOR")


def load_shape_vectors(dataset_dir: Path, max_scans: int = None,
                        require_gender: bool = False) -> Tuple[np.ndarray, List[str], List[str]]:
    """Load all SMPL shape vectors from dataset metadata.
    Returns (shapes_array, scan_ids, genders)."""
    shapes: List[np.ndarray] = []
    scan_ids: List[str] = []
    genders: List[str] = []

    scan_dirs = sorted(dataset_dir.glob("scan_*"))
    if max_scans:
        scan_dirs = scan_dirs[:max_scans]

    for scan_dir in scan_dirs:
        meta_path = scan_dir / "metadata.json"
        if not meta_path.exists():
            continue
        try:
            meta = json.loads(meta_path.read_text())
            smpl = meta.get('smpl_params')
            if smpl and smpl.get('shape') and len(smpl['shape']) == 10:
                shape_vec = np.array(smpl['shape'], dtype=np.float64)
                if np.all(np.abs(shape_vec) < 4.0):
                    shapes.append(shape_vec)
                    scan_ids.append(meta['scan_id'])
                    genders.append(meta.get('gender', 'unknown'))
        except Exception as e:
            logger.warning(f"Error reading {meta_path}: {e}")

    if not shapes:
        logger.error("No valid shape vectors found!")
        sys.exit(1)

    logger.info(f"Loaded {len(shapes)} shape vectors from {dataset_dir}")
    return np.array(shapes), scan_ids, genders


def find_optimal_gmm(shapes: np.ndarray, max_components: int = 16,
                      cv: bool = False) -> Tuple[GaussianMixture, int, List[float]]:
    """Find optimal GMM components using BIC. Optionally cross-validates."""
    best_bic = np.inf
    best_gmm = None
    best_k = None
    bics = []

    for k in range(2, max_components + 1):
        gmm = GaussianMixture(n_components=k, covariance_type='full',
                              random_state=42, n_init=10)
        gmm.fit(shapes)
        bic = gmm.bic(shapes)
        bics.append(bic)
        logger.info(f"  K={k}: BIC={bic:.1f}")

        if bic < best_bic:
            best_bic = bic
            best_gmm = gmm
            best_k = k

    logger.info(f"Optimal K={best_k} (BIC={best_bic:.1f})")
    return best_gmm, best_k, bics


def evaluate_gmm(gmm: GaussianMixture, scaler: StandardScaler,
                  shapes_val: np.ndarray, genders_val: List[str]):
    """Evaluate GMM on validation set with per-gender analysis."""
    shapes_val_std = scaler.transform(shapes_val)
    log_likelihoods = gmm.score_samples(shapes_val_std)

    logger.info(f"Validation set: {len(shapes_val)} scans")
    logger.info(f"  Mean log-likelihood: {np.mean(log_likelihoods):.3f}")
    logger.info(f"  Std log-likelihood:  {np.std(log_likelihoods):.3f}")
    logger.info(f"  Min: {np.min(log_likelihoods):.3f}")
    logger.info(f"  Max: {np.max(log_likelihoods):.3f}")

    for gender in set(genders_val):
        idx = [i for i, g in enumerate(genders_val) if g == gender]
        if idx:
            ll = log_likelihoods[idx]
            logger.info(f"  {gender} ({len(idx)}): mean={np.mean(ll):.3f}")

    threshold = np.percentile(log_likelihoods, 5)
    n_anomalous = np.sum(log_likelihoods < threshold)
    logger.info(f"  Bottom 5% threshold: {threshold:.3f} ({n_anomalous} scans)")


def save_model(gmm: GaussianMixture, scaler: StandardScaler,
               output_dir: Path, version: int):
    """Save trained model to disk in multiple formats."""
    output_dir.mkdir(parents=True, exist_ok=True)

    gmm_path = output_dir / "shape_prior_gmm.pkl"
    with open(gmm_path, 'wb') as f:
        pickle.dump(gmm, f)
    logger.info(f"GMM saved to {gmm_path}")

    scaler_path = output_dir / "shape_scaler.pkl"
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
    logger.info(f"Scaler saved to {scaler_path}")

    scaler_json = {
        'mean': scaler.mean_.tolist(),
        'scale': scaler.scale_.tolist(),
    }
    (output_dir / "shape_scaler.json").write_text(json.dumps(scaler_json, indent=2))

    gmm_json = {
        'n_components': gmm.n_components,
        'version': version,
        'weights': gmm.weights_.tolist(),
        'means': gmm.means_.tolist(),
        'covariances': [c.tolist() for c in gmm.covariances_],
        'n_features': gmm.n_features_in_,
        'bic': float(gmm.bic(np.zeros((1, gmm.n_features_in_)))),
    }
    json_path = output_dir / f"shape_prior_gmm_v{version}.json"
    json_path.write_text(json.dumps(gmm_json, indent=2))
    logger.info(f"GMM params saved to {json_path}")


def print_cluster_analysis(gmm: GaussianMixture, shapes_std: np.ndarray, scaler: StandardScaler):
    """Print anthropometric interpretation of each cluster."""
    logger.info("=" * 60)
    logger.info("CLUSTER ANALYSIS")

    labels = gmm.predict(shapes_std)
    for i in range(gmm.n_components):
        cluster_size = int(np.sum(labels == i))
        center_std = gmm.means_[i]
        center_orig = scaler.inverse_transform(center_std.reshape(1, -1))[0]
        logger.info(f"Cluster {i}: {cluster_size} scans ({cluster_size/len(labels)*100:.1f}%)")
        logger.info(f"  Standardized center: {np.round(center_std, 3)}")
        logger.info(f"  Original center:     {np.round(center_orig, 3)}")

        if center_orig[0] > 0.5:
            logger.info(f"  Interpretation: Larger/taller frame")
        elif center_orig[0] < -0.5:
            logger.info(f"  Interpretation: Smaller/shorter frame")

    corr = np.corrcoef(shapes_std, rowvar=False)
    logger.info("Shape dimension correlation matrix:")
    for i in range(10):
        row = "  ".join(f"{corr[i, j]:.2f}" for j in range(10))
        logger.info(f"  Beta{i}: {row}")


def main():
    parser = argparse.ArgumentParser(description="Train shape prior GMM from dataset")
    parser.add_argument('--dataset-dir', type=str, required=True,
                        help='Dataset directory (e.g., data/training_dataset/v1)')
    parser.add_argument('--output-dir', type=str, default='api/models/priors',
                        help='Output directory for trained models')
    parser.add_argument('--max-scans', type=int, help='Max scans to use')
    parser.add_argument('--max-components', type=int, default=16,
                        help='Max GMM components to try')
    parser.add_argument('--version', type=int, default=1, help='Model version')
    parser.add_argument('--plot', action='store_true', help='Generate visualization')
    args = parser.parse_args()

    dataset_dir = Path(args.dataset_dir)
    output_dir = Path(args.output_dir)

    shapes, scan_ids, genders = load_shape_vectors(dataset_dir, args.max_scans)
    logger.info(f"Loaded {len(shapes)} shape vectors from {dataset_dir}")

    shapes_train, shapes_val, genders_train, genders_val = train_test_split(
        shapes, genders, test_size=0.1, random_state=42
    )
    logger.info(f"Train: {len(shapes_train)}, Val: {len(shapes_val)}")

    scaler = StandardScaler()
    shapes_train_std = scaler.fit_transform(shapes_train)
    logger.info("Shape standardized")

    gmm, best_k, bics = find_optimal_gmm(shapes_train_std, args.max_components)
    evaluate_gmm(gmm, scaler, shapes_val, genders_val)
    print_cluster_analysis(gmm, shapes_train_std, scaler)
    save_model(gmm, scaler, output_dir, args.version)

    # Plot if requested
    if args.plot:
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt

            fig, axes = plt.subplots(2, 5, figsize=(15, 6))
            axes = axes.ravel()
            for i in range(10):
                axes[i].hist(shapes[:, i], bins=50, alpha=0.7, color='steelblue')
                axes[i].set_title(f"Shape Dim {i}")
                axes[i].axvline(np.mean(shapes[:, i]), color='red', linestyle='--')
            plt.tight_layout()
            plot_path = output_dir / "shape_distributions.png"
            plt.savefig(str(plot_path), dpi=100)
            logger.info(f"Distribution plot saved to {plot_path}")

            plt.figure(figsize=(10, 8))
            plt.plot(range(2, args.max_components + 1), bics, marker='o')
            plt.axvline(best_k, color='red', linestyle='--', label=f'Optimal K={best_k}')
            plt.xlabel('Components (K)')
            plt.ylabel('BIC')
            plt.title('BIC vs GMM Components')
            plt.legend()
            plt.grid(True, alpha=0.3)
            bic_path = output_dir / "bic_curve.png"
            plt.savefig(str(bic_path), dpi=100)
            logger.info(f"BIC curve saved to {bic_path}")
        except ImportError:
            logger.warning("matplotlib not available — skipping plots")

    logger.info(f"Model v{args.version} trained. Run next:")
    logger.info(f"  Deploy: cp {output_dir}/shape_prior_gmm.pkl api/models/priors/")
    logger.info(f"  Deploy: cp {output_dir}/shape_scaler.pkl api/models/priors/")


if __name__ == "__main__":
    main()
