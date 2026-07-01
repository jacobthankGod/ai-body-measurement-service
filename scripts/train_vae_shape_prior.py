#!/usr/bin/env python3
"""
Train VAE Shape Prior
======================
Trains a Variational Autoencoder over the 10-dim SMPL shape space.
The VAE provides a learned prior with density estimation and smooth
interpolation, complementing the GMM for more expressive shape modeling.

Structure:
- Encoder: 10 → 32 → 16 → latent (4)
- Decoder: latent (4) → 16 → 32 → 10
- Loss: β-VAE (KL + reconstruction)

Usage:
    python scripts/train_vae_shape_prior.py \
        --dataset-dir data/training_dataset/v1 \
        --output-dir api/models/priors \
        --epochs 500 \
        --version 1

Requires: torch
"""
import json
import argparse
import logging
import pickle
import numpy as np
from pathlib import Path
from typing import Tuple, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("VAE_SHAPE")

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader, TensorDataset
except ImportError:
    logger.error("PyTorch not installed. Run: pip install torch")
    exit(1)


class ShapeVAE(nn.Module):
    """β-VAE for SMPL shape space (10-dim → latent 4 → 10-dim)."""

    def __init__(self, latent_dim: int = 4, hidden_dim: int = 32):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(10, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
        )
        self.mu = nn.Linear(hidden_dim // 2, latent_dim)
        self.logvar = nn.Linear(hidden_dim // 2, latent_dim)
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 10),
        )

    def encode(self, x):
        h = self.encoder(x)
        return self.mu(h), self.logvar(h)

    def reparameterize(self, mu, logvar):
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std

    def decode(self, z):
        return self.decoder(z)

    def forward(self, x):
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        return self.decode(z), mu, logvar


def loss_fn(recon_x, x, mu, logvar, beta: float = 0.1) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """β-VAE loss: reconstruction MSE + β * KL divergence."""
    recon_loss = F.mse_loss(recon_x, x, reduction='sum')
    kl_loss = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
    return recon_loss + beta * kl_loss, recon_loss, kl_loss


def load_shapes(dataset_dir: Path, max_scans: int = None) -> np.ndarray:
    """Load all shape vectors from dataset metadata."""
    shapes = []
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
            if smpl and len(smpl.get('shape', [])) == 10:
                shapes.append(np.array(smpl['shape'], dtype=np.float32))
        except Exception:
            pass
    return np.array(shapes)


def main():
    parser = argparse.ArgumentParser(description="Train VAE shape prior")
    parser.add_argument('--dataset-dir', type=str, required=True)
    parser.add_argument('--output-dir', type=str, default='api/models/priors')
    parser.add_argument('--latent-dim', type=int, default=4)
    parser.add_argument('--hidden-dim', type=int, default=32)
    parser.add_argument('--epochs', type=int, default=500)
    parser.add_argument('--lr', type=float, default=1e-3)
    parser.add_argument('--beta', type=float, default=0.1, help='β-VAE weight')
    parser.add_argument('--batch-size', type=int, default=64)
    parser.add_argument('--max-scans', type=int)
    parser.add_argument('--version', type=int, default=1)
    parser.add_argument('--device', type=str, default='cpu')
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    device = torch.device(args.device)

    shapes = load_shapes(Path(args.dataset_dir), args.max_scans)
    logger.info(f"Loaded {len(shapes)} shape vectors")
    if len(shapes) < 10:
        logger.error("Not enough data")
        exit(1)

    mean = shapes.mean(axis=0)
    std = shapes.std(axis=0) + 1e-8
    shapes_norm = (shapes - mean) / std

    tensor_x = torch.FloatTensor(shapes_norm)
    dataset = TensorDataset(tensor_x)
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True)

    model = ShapeVAE(args.latent_dim, args.hidden_dim).to(device)
    optimizer = optim.Adam(model.parameters(), lr=args.lr)

    best_loss = float('inf')
    patience = 50
    no_improve = 0

    for epoch in range(1, args.epochs + 1):
        model.train()
        total_loss = 0
        total_recon = 0
        total_kl = 0
        for batch, in loader:
            batch = batch.to(device)
            optimizer.zero_grad()
            recon, mu, logvar = model(batch)
            loss, rl, kl = loss_fn(recon, batch, mu, logvar, args.beta)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            total_recon += rl.item()
            total_kl += kl.item()

        avg_loss = total_loss / len(shapes)
        avg_recon = total_recon / len(shapes)
        avg_kl = total_kl / len(shapes)

        if epoch % 50 == 0 or epoch == 1:
            logger.info(f"Epoch {epoch:4d}: loss={avg_loss:.4f} recon={avg_recon:.4f} kl={avg_kl:.4f}")

        if avg_loss < best_loss:
            best_loss = avg_loss
            no_improve = 0
        else:
            no_improve += 1
            if no_improve >= patience:
                logger.info(f"Early stopping at epoch {epoch}")
                break

    logger.info(f"Training complete. Best loss: {best_loss:.4f}")

    model_data = {
        'model_state_dict': model.state_dict(),
        'mean': mean.tolist(),
        'std': std.tolist(),
        'latent_dim': args.latent_dim,
        'hidden_dim': args.hidden_dim,
        'version': args.version,
        'input_dim': 10,
    }

    model_path = output_dir / "shape_vae.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(model_data, f)
    logger.info(f"VAE saved to {model_path}")

    meta = {
        'version': args.version,
        'latent_dim': args.latent_dim,
        'n_train': len(shapes),
        'best_loss': round(best_loss, 4),
        'beta': args.beta,
    }
    (output_dir / "shape_vae.json").write_text(json.dumps(meta, indent=2))
    logger.info("Done")


if __name__ == "__main__":
    main()
