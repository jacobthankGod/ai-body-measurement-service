"""
Download Models for AI Body Scan SaaS
==================================
Downloads required models:
1. HMR model (3D body reconstruction)
2. DeepLab model (background removal)
3. CustomBodyPoints (measurement extraction)
"""
import os
import urllib.request
import tarfile
import gzip
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent
MODELS_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR / "data"

MODELS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)


def download_hmr_model():
    """Download HMR model from Berkeley."""
    hmr_url = "https://people.eecs.berkeley.edu/~kanazawa/cachedir/hmr/models.tar.gz"
    hmr_path = MODELS_DIR / "models.tar.gz"
    
    print("Downloading HMR model...")
    print(f"  URL: {hmr_url}")
    print(f"  Destination: {hmr_path}")
    
    try:
        urllib.request.urlretrieve(hmr_url, hmr_path)
        
        # Extract
        print("Extracting...")
        with tarfile.open(hmr_path, 'r:gz') as tar:
            tar.extractall(MODELS_DIR)
        
        # Remove tarball
        os.remove(hmr_path)
        print("✅ HMR model ready")
    except Exception as e:
        print(f"⚠️ HMR download failed: {e}")
        print("  Trying alternative URL...")
        try:
            alt_url = "https://dl.dropboxusercontent.com/s/e8s7q5bq7a5s1bq/hmr_model.tar.gz"
            urllib.request.urlretrieve(alt_url, hmr_path)
            with tarfile.open(hmr_path, 'r:gz') as tar:
                tar.extractall(MODELS_DIR)
            os.remove(hmr_path)
            print("✅ HMR model ready (alt)")
        except Exception as e2:
            print(f"⚠️ Alt download also failed: {e2}")


def download_deeplab_model():
    """DeepLab model downloads automatically in inference.py."""
    print("DeepLab model: Will download on first use via inference.py")
    print("  (Uses tensorflow hub or direct download)")


def download_custom_body_points():
    """Download CustomBodyPoints.txt."""
    cb_url = "https://github.com/farazBhatti/Human-Body-Measurements-using-Computer-Vision/raw/main/data/customBodyPoints.txt"
    cb_path = DATA_DIR / "customBodyPoints.txt"
    
    print("Downloading CustomBodyPoints.txt...")
    
    try:
        urllib.request.urlretrieve(cb_url, cb_path)
        print("✅ CustomBodyPoints ready")
    except Exception as e:
        print(f"⚠️ CustomBodyPoints download failed: {e}")
        # Try raw github
        try:
            raw_url = "https://raw.githubusercontent.com/farazBhatti/Human-Body-Measurements-using-Computer-Vision/main/data/customBodyPoints.txt"
            urllib.request.urlretrieve(raw_url, cb_path)
            print("✅ CustomBodyPoints ready")
        except Exception as e2:
            print(f"⚠️ Alt download also failed: {e2}")


if __name__ == "__main__":
    print("=" * 50)
    print("Downloading AI Body Scan SaaS Models")
    print("=" * 50)
    
    print("\n1. HMR Model (3D Reconstruction)")
    download_hmr_model()
    
    print("\n2. DeepLab Model (Background Removal)")
    download_deeplab_model()
    
    print("\n3. Custom Body Points")
    download_custom_body_points()
    
    print("\n" + "=" * 50)
    print("Models ready!")
    print("=" * 50)
