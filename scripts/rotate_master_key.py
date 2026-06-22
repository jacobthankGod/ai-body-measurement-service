import os
import secrets
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KORRA_SECURITY")

def rotate_keys():
    """
    Phase 183: Master Key Rotation
    Automates the generation of a new platform master secret.
    """
    try:
        new_secret = secrets.token_urlsafe(32)
        env_path = Path(".env")

        if env_path.exists():
            with open(env_path, 'r') as f:
                lines = f.readlines()

            with open(env_path, 'w') as f:
                for line in lines:
                    if line.startswith("KORRA_MASTER_SECRET="):
                        f.write(f"KORRA_MASTER_SECRET={new_secret}\n")
                        logger.info("🔑 Phase 183: KORRA_MASTER_SECRET rotated successfully.")
                    else:
                        f.write(line)
        else:
            with open(env_path, 'w') as f:
                f.write(f"KORRA_MASTER_SECRET={new_secret}\n")
            logger.info("📄 Phase 183: Initial .env created with Master Secret.")

        print(f"NEW_MASTER_SECRET={new_secret}")
        return True
    except Exception as e:
        logger.error(f"❌ Phase 183 Rotation Failure: {e}")
        return False

if __name__ == "__main__":
    rotate_keys()
