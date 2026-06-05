# Git LFS Push Guide for ai-body-measurement-service

This guide walks you through installing Git LFS and pushing your large ML model files to GitHub.

## Prerequisites

- Homebrew must be installed: https://brew.sh

## Step 1: Install Git LFS

Open Terminal and run:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Then install Git LFS:

```bash
brew install git-lfs
git lfs install
```

## Step 2: Configure LFS Tracking

Navigate to your project and configure LFS:

```bash
cd /Users/mac/ai-body-scan-saas

# Track model checkpoint files
git lfs track "api/models/*.ckpt-*"

# Track pickle files
git lfs track "api/models/*.pkl"

# Note: Do NOT track models.tar.gz since it's already extracted
# (it was the compressed archive, now expanded)
```

## Step 3: Commit LFS Configuration

```bash
git add .gitattributes
git commit -m "chore: configure Git LFS for ML model files"
```

## Step 4: Stage and Commit Model Files

```bash
git add api/models/
git commit -m "feat: add ML model files (stored with Git LFS)"
```

## Step 5: Push to GitHub

```bash
git push origin main
```

## Files Being Tracked

| File | Size | Purpose |
|------|------|---------|
| model.ckpt-667589.data-00000-of-00001 | 364MB | TensorFlow checkpoint data |
| model.ckpt-667589.index | 31KB | Model index |
| model.ckpt-667589.meta | 28MB | Model metadata |
| neutral_smpl_with_cocoplus_reg.pkl | 39MB | SMPL model parameters |
| models.tar.gz | 431MB | ⚠️ NOT needed (was extracted) |

**Note:** `models.tar.gz` was the source archive that has now been extracted. Since it's already extracted into the individual model files, you can delete it to save space:

```bash
rm api/models/models.tar.gz
```

## After Push - Vercel Deployment

Once pushed to GitHub, Vercel will automatically:

1. Download LFS files during deployment
2. Place them in the correct directory

Your `scripts/download_models.py` can remain as a fallback mechanism.

## GitHub LFS Quota

- Free tier: 1GB storage + 1GB bandwidth/month
- Your models use ~430MB total, well within free tier

## Troubleshooting

If push fails:
```bash
# Increase buffer size
git config http.postBuffer 524288000

# Retry
git push origin main --retry
```

## Current Repository Status

- Branch: main
- Remote: https://github.com/jacobthankGod/ai-body-measurement-service
- Last push: Clean commit without model files (104KB)
- Model files: Ready to add with LFS
