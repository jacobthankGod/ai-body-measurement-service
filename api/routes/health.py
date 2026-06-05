"""
Health Routes
============
"""
from fastapi import APIRouter
from datetime import datetime
import os
from pathlib import Path

router = APIRouter()

# Check module availability
BASE_DIR = Path(__file__).parent.parent.parent

def check_modules():
    """Check which measurement modules are available."""
    modules = {
        'hmr_3d': (BASE_DIR / 'api' / 'services' / 'extract_measurements.py').exists(),
        'mediapipe': (BASE_DIR / 'api' / 'services' / 'mediapipe_measurement_engine.py').exists(),
        'ratios': True,  # Always available as fallback
    }
    
# Check for models - multiple naming patterns
    models_dir = BASE_DIR / 'models'
    if models_dir.exists():
        hmr_patterns = [
            models_dir / 'hmr_model.ckpt.index',
            models_dir / 'model.ckpt-667589.index',
        ]
        modules['hmr_models'] = any(p.exists() for p in hmr_patterns)
    else:
        modules['hmr_models'] = False
    
    return modules

@router.get("/health")
async def health_check():
    """Health check endpoint with cascade status."""
    modules = check_modules()
    
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "cascade": {
            "enabled": True,
            "priority": ["hmr_3d", "mediapipe", "ratios"],
            "available": modules,
            "accuracies": {
                "hmr_3d": "±1-2cm",
                "mediapipe": "±3-5cm", 
                "ratios": "±5-10cm"
            }
        },
        "api_version": "v2"
    }
