"""
Initialize Database
=================
Creates data files and directories.
"""
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

for f in ["api_keys.json", "usage_log.json"]:
    filepath = DATA_DIR / f
    if not filepath.exists():
        filepath.write_text("{}")
        print(f"Created: {filepath}")

print("Database initialized.")
