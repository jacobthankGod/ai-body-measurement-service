"""
OOTDiffusion Virtual Try-On Service | Replicate Integration
===========================================================
Wraps the Replicate API for OOTDiffusion (half-body and full-body models).
Runs on L40S hardware (~$0.06 per inference, ~60-120s).
"""
import os
import json
import logging
import time
import uuid
from pathlib import Path
from typing import Optional

logger = logging.getLogger("KORRA_TRYON")

REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN")
REPLICATE_MODEL = os.environ.get("REPLICATE_TRYON_MODEL", "viktorfa/oot_diffusion")

# Attire -> OOTDiffusion category mapping
CATEGORY_MAP = {
    "t-shirt": "upperbody",
    "shirt": "upperbody",
    "blazer": "upperbody",
    "blazer_business": "upperbody",
    "bomber_jacket": "upperbody",
    "trench_coat": "upperbody",
    "kikoy": "upperbody",
    "agbada": "dress",
    "senator": "upperbody",
    "kurta": "upperbody",
    "pant": "lowerbody",
    "skirt": "lowerbody",
    "a_line_skirt": "lowerbody",
    "pencil_skirt": "lowerbody",
    "dress": "dress",
    "kaftan": "dress",
    "jumpsuit": "dress",
    "classic_jumpsuit": "dress",
}

DEFAULT_CATEGORY = "upperbody"

# Stock garment image URLs (placeholder — replace with actual garment photos)
GARMENT_IMAGE_MAP = {
    "t-shirt": "/assets/garment-images/t-shirt.png",
    "shirt": "/assets/garment-images/shirt.png",
    "pant": "/assets/garment-images/pant.png",
    "skirt": "/assets/garment-images/skirt.png",
    "dress": "/assets/garment-images/dress.png",
}


class TryOnService:

    @staticmethod
    def run_tryon(
        person_image_url: str,
        garment_image_url: str,
        category: str = "upperbody",
        steps: int = 20,
        guidance_scale: float = 2.0,
    ) -> list:
        """Run OOTDiffusion via Replicate API.
        
        Args:
            person_image_url: Public URL of the person/full-body photo
            garment_image_url: Public URL of the garment flat-lay photo
            category: 'upperbody', 'lowerbody', or 'dress'
            steps: Inference steps (20 default)
            guidance_scale: Classifier-free guidance scale (2.0 default)
        
        Returns:
            List of output image URLs (typically 4 samples)
        """
        if not REPLICATE_API_TOKEN:
            logger.error("REPLICATE_API_TOKEN not set")
            raise ValueError("Replicate API token not configured")

        try:
            import replicate
        except ImportError:
            logger.error("replicate package not installed")
            raise ImportError("pip install replicate")

        logger.info(
            f"🧵 Running OOTDiffusion: category={category}, "
            f"steps={steps}, guidance={guidance_scale}"
        )
        logger.info(f"   person: {person_image_url}")
        logger.info(f"   garment: {garment_image_url}")

        # Choose model based on category
        model_id = REPLICATE_MODEL
        if category == "dress":
            model_id = "qiweiii/oot_diffusion_dc"

        start = time.time()
        try:
            output = replicate.run(
                model_id,
                input={
                    "model_image": person_image_url,
                    "garment_image": garment_image_url,
                    "category": category,
                    "steps": steps,
                    "guidance_scale": guidance_scale,
                }
            )
            elapsed = time.time() - start
            logger.info(f"✅ OOTDiffusion completed in {elapsed:.1f}s")

            # Replicate returns a list of FileOutput objects
            urls = []
            for item in output:
                if hasattr(item, 'url'):
                    urls.append(item.url())
                elif isinstance(item, str):
                    urls.append(item)
            logger.info(f"   Got {len(urls)} output images")
            return urls

        except Exception as e:
            logger.error(f"❌ OOTDiffusion inference failed: {e}")
            raise

    @staticmethod
    def get_stock_garment_url(attire: str, base_url: str = "") -> Optional[str]:
        """Get stock garment image URL for a given attire type."""
        image_path = GARMENT_IMAGE_MAP.get(attire)
        if image_path:
            return base_url.rstrip("/") + image_path
        return None

    @staticmethod
    def get_category(attire: str) -> str:
        """Map attire to OOTDiffusion category."""
        return CATEGORY_MAP.get(attire, DEFAULT_CATEGORY)
