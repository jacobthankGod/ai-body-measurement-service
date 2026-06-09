import os
import sys
import psutil
import pytest
import time
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

def get_process_memory():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)  # MB

def test_tensorflow_not_loaded_on_import():
    """Verify that importing the main router doesn't load TensorFlow into RAM."""
    initial_mem = get_process_memory()
    print(f"\nInitial Memory: {initial_mem:.2f} MB")

    # Import the router that used to trigger TF load
    from api.routes import measurements

    post_import_mem = get_process_memory()
    print(f"Post-Import Memory: {post_import_mem:.2f} MB")

    # Check if 'tensorflow' is in sys.modules
    tf_loaded = 'tensorflow' in sys.modules
    print(f"TensorFlow in sys.modules: {tf_loaded}")

    # It shouldn't be loaded at the top level anymore
    assert not tf_loaded, "TensorFlow was loaded into the main process on import!"

    # Memory increase should be minimal (mostly FastAPI/Pydantic/PIL)
    # 100MB is a safe upper bound for a lean FastAPI app
    assert post_import_mem < 150, f"Memory usage too high after import: {post_import_mem:.2f} MB"

@pytest.mark.asyncio
async def test_subprocess_memory_release():
    """Verify that running an AI task doesn't bloat the main process memory."""
    from api.routes.measurements import run_extraction_subprocess_cli
    import numpy as np
    from PIL import Image
    import uuid

    # Create a dummy image
    task_id = str(uuid.uuid4())
    tmp_dir = BASE_DIR / "data" / "tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    f_path = str(tmp_dir / f"test_f_{task_id}.png")
    s_path = str(tmp_dir / f"test_s_{task_id}.png")

    dummy_img = Image.fromarray(np.zeros((224, 224, 3), dtype=np.uint8))
    dummy_img.save(f_path)
    dummy_img.save(s_path)

    mem_before = get_process_memory()
    print(f"Memory before AI Task: {mem_before:.2f} MB")

    # Run the subprocess task (it will likely fail or use fallback if weights missing,
    # but we want to see if the MAIN process stays lean)
    result = await run_extraction_subprocess_cli(task_id, f_path, s_path, 175.0, "male", "Test", "user_123")

    mem_after = get_process_memory()
    print(f"Memory after AI Task: {mem_after:.2f} MB")

    # Verify TF still not in main process
    assert 'tensorflow' not in sys.modules, "TensorFlow leaked into main process during task execution!"

    # Memory should remain relatively stable
    assert mem_after - mem_before < 50, f"Main process memory bloated by {mem_after - mem_before:.2f} MB"
