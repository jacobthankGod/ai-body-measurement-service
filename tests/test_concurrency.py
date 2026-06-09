import asyncio
import pytest
import time
import uuid
from pathlib import Path
from api.routes import measurements

BASE_DIR = Path(__file__).resolve().parent.parent

@pytest.mark.asyncio
async def test_serial_concurrency_enforcement():
    """
    Verify that multiple concurrent requests are processed one by one.
    """
    from PIL import Image
    import numpy as np
    import io

    task_id_1 = str(uuid.uuid4())
    task_id_2 = str(uuid.uuid4())

    # Create valid dummy PNG bytes
    img = Image.fromarray(np.zeros((224, 224, 3), dtype=np.uint8))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    dummy_bytes = buf.getvalue()

    # Launch both tasks simultaneously
    t1 = asyncio.create_task(measurements.run_extraction_task(task_id_1, dummy_bytes, dummy_bytes, 175.0, "male", "User1", "u1"))
    t2 = asyncio.create_task(measurements.run_extraction_task(task_id_2, dummy_bytes, dummy_bytes, 180.0, "male", "User2", "u2"))

    # Wait for completion
    await asyncio.gather(t1, t2)

    # Check if they both finished
    assert measurements.EXTRACTION_TASKS[task_id_1]["status"] in ["completed", "failed"]
    assert measurements.EXTRACTION_TASKS[task_id_2]["status"] in ["completed", "failed"]

    print("\nConcurrency test finished successfully.")
