"""
Auto Kaggle GPU Backend Rotation.

Monitors the EC2 proxy health endpoint. When the current Kaggle backend dies
(GPU quota exhausted, session timeout, crash), automatically rotates to the
next account: pushes the notebook, waits for the tunnel to register, verifies.

Requires:
  1. Kaggle accounts configured in kaggle_accounts.json
  2. Notebook Cell 5 modified to POST tunnel URL to EC2 proxy
  3. EC2 proxy with /api/v2/internal/tunnel endpoint (server.py)

Usage:
  python scripts/auto_kaggle_rotate.py [--daemon] [--interval 300]

  --daemon      Run continuously (for systemd/cron)
  --interval N  Check every N seconds (default 300)
  --once        Single check and rotate if needed, then exit
"""

import json, time, base64, hashlib, hmac, sys, os, subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

import requests

# --- Config ---
SCRIPT_DIR = Path(__file__).parent
ACCOUNTS_FILE = SCRIPT_DIR / "kaggle_accounts.json"
STATE_FILE = SCRIPT_DIR / "kaggle_state.json"
LOG_FILE = SCRIPT_DIR / "kaggle_rotation.log"

EC2_HOST = "korra.work"
EC2_USER = "ubuntu"
SSH_KEY = os.path.expanduser("~/Downloads/korra-ai-key.pem")
HEALTH_URL = "https://korra.work/api/v2/garment/health"
INTERNAL_TUNNEL_URL = "https://korra.work/api/v2/garment/internal/tunnel"

NOTEBOOK_PATH = SCRIPT_DIR.parent / "kaggle-garment-backend" / "notebook.ipynb"
KERNEL_META_PATH = SCRIPT_DIR.parent / "kaggle-garment-backend" / "kernel-metadata.json"

MAX_CONSECUTIVE_FAILURES = 3
POLL_STATUS_INTERVAL = 30
KERNEL_START_TIMEOUT = 600  # 10 minutes max for kernel to start
KERNEL_RUN_TIMEOUT = 900  # 15 minutes max for full setup (downloads + tunnel)
ROTATION_COOLDOWN = 600  # 10 min between rotations to avoid rapid cycling


def log(msg: str):
    timestamp = datetime.now().isoformat()
    line = f"[{timestamp}] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def load_accounts() -> list[dict]:
    if not ACCOUNTS_FILE.exists():
        log(f"ERROR: {ACCOUNTS_FILE} not found")
        sys.exit(1)
    with open(ACCOUNTS_FILE) as f:
        data = json.load(f)
    return data.get("accounts", [])


def load_state() -> dict:
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {
        "current_index": 0,
        "last_rotation": "",
        "active_kernel_slug": "",
        "active_account_email": "",
        "consecutive_failures": 0,
    }


def save_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def generate_slug(account: dict) -> str:
    h = hashlib.md5((str(time.time()) + account["email"]).encode()).hexdigest()[:8]
    return f"gr-backend-{h}"


def push_kernel(account: dict, slug: str) -> Optional[dict]:
    token = account.get("token") or account.get("api_key")
    if not token:
        log(f"  ERROR: No token for {account['email']}")
        return None

    with open(NOTEBOOK_PATH) as f:
        nb_text = f.read()

    encoded = base64.b64encode(nb_text.encode()).decode()
    headers = {"Authorization": f"Bearer {token}"}

    title = f"Garment Backend {slug.split('-')[-1]}"

    payload = {
        "id": 0,
        "slug": slug,
        "newTitle": title,
        "text": encoded,
        "language": "python",
        "kernelType": "notebook",
        "isPrivate": True,
        "enableGpu": True,
        "enableInternet": True,
        "datasetSources": [],
        "competitionSources": [],
        "kernelSources": [],
        "modelSources": [],
    }

    resp = requests.post(
        "https://www.kaggle.com/api/v1/kernels/push",
        json=payload,
        headers=headers,
        timeout=60,
    )

    if resp.status_code == 200:
        data = resp.json()
        log(f"  Pushed v{data.get('versionNumber', 1)} — kernel ID {data.get('kernelId', '?')}")
        return data
    else:
        log(f"  Push failed: {resp.status_code} {resp.text[:200]}")
        return None


def check_kernel_status(account: dict, slug: str) -> str:
    token = account.get("token") or account.get("api_key")
    if not token:
        return "error"

    headers = {"Authorization": f"Bearer {token}"}
    username = account.get("username") or account["email"].split("@")[0]

    try:
        resp = requests.get(
            f"https://www.kaggle.com/api/v1/kernels/status/{username}/{slug}",
            headers=headers,
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json().get("status", "unknown")
        return "unknown"
    except Exception as e:
        log(f"  Status check failed: {e}")
        return "unknown"

def get_tunnel_url_from_kernel(
    account: dict, slug: str
) -> Optional[str]:
    """
    Uses the Kaggle CLI to download kernel output files and reads tunnel_url.txt.
    Falls back to trying the EC2 proxy health endpoint if CLI is not available.
    """
    username = account.get("username") or account["email"].split("@")[0]
    kernel_ref = f"{username}/{slug}"

    try:
        result = subprocess.run(
            ["kaggle", "kernels", "output", kernel_ref, "-p", "/tmp/kaggle_output", "-q"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            tunnel_file = Path("/tmp/kaggle_output/tunnel_url.txt")
            if tunnel_file.exists():
                url = tunnel_file.read_text().strip()
                if url.startswith("http"):
                    log(f"  Tunnel URL extracted from kernel output: {url}")
                    return url
        else:
            log(f"  CLI output failed: {result.stderr[:200]}")
    except FileNotFoundError:
        log("  Kaggle CLI not installed")
    except Exception as e:
        log(f"  CLI error: {e}")

    return None


def update_ec2_tunnel(tunnel_url: str) -> bool:
    cmd = (
        f'sudo sed -i "s|KAGGLE_TUNNEL_URL=.*|KAGGLE_TUNNEL_URL={tunnel_url}|" '
        f"/etc/systemd/system/garment-proxy.service && "
        f"sudo systemctl daemon-reload && "
        f"sudo systemctl restart garment-proxy"
    )
    try:
        result = subprocess.run(
            ["ssh", "-i", SSH_KEY, "-o", "StrictHostKeyChecking=no",
             f"{EC2_USER}@{EC2_HOST}", cmd],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            log(f"  EC2 proxy updated to {tunnel_url}")
            return True
        else:
            log(f"  SSH failed: {result.stderr[:200]}")
            return False
    except Exception as e:
        log(f"  SSH error: {e}")
        return False


def health_check() -> bool:
    try:
        resp = requests.get(HEALTH_URL, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("kaggle_backend") == "connected":
                return True
            log(f"  Health: backend disconnected ({data.get('tunnel_url', '?')})")
            return False
        log(f"  Health: HTTP {resp.status_code}")
        return False
    except requests.RequestException as e:
        log(f"  Health check failed: {e}")
        return False


def rotate(accounts: list[dict], state: dict) -> bool:
    log("=== ROTATION STARTED ===")

    old_idx = state.get("current_index", 0)
    new_idx = (old_idx + 1) % len(accounts)
    account = accounts[new_idx]
    slug = generate_slug(account)

    log(f"  Account: {account['email']} (index {old_idx} -> {new_idx})")
    log(f"  Slug: {slug}")

    # 1. Push notebook
    push_result = push_kernel(account, slug)
    if not push_result:
        log("  Push failed, trying next account...")
        state["current_index"] = new_idx + 1
        save_state(state)
        return False

    kernel_ref = push_result.get("ref", "")
    log(f"  Kernel: https://www.kaggle.com{kernel_ref}")

    # 2. Wait for kernel to start running
    log(f"  Waiting for kernel to start (max {KERNEL_START_TIMEOUT}s)...")
    deadline = time.time() + KERNEL_START_TIMEOUT
    started = False
    while time.time() < deadline:
        status = check_kernel_status(account, slug)
        if status == "running":
            log(f"  Kernel status: running")
            started = True
            break
        elif status == "error":
            log(f"  Kernel status: error — trying next account")
            state["current_index"] = new_idx + 1
            state["consecutive_failures"] = 0
            save_state(state)
            return False
        time.sleep(POLL_STATUS_INTERVAL)

    if not started:
        log(f"  Kernel did not start in {KERNEL_START_TIMEOUT}s — trying next account")
        return False

    # 3. Wait for tunnel URL and health
    log(f"  Waiting for tunnel + server (max {KERNEL_RUN_TIMEOUT}s)...")
    deadline = time.time() + KERNEL_RUN_TIMEOUT
    tunnel_obtained = False

    while time.time() < deadline:
        # Try to get tunnel URL from kernel output
        tunnel_url = get_tunnel_url_from_kernel(account, slug)
        if tunnel_url:
            if update_ec2_tunnel(tunnel_url):
                tunnel_obtained = True
                break

        # Also check health (notebook may have POSTed the URL already)
        if health_check():
            tunnel_obtained = True
            log("  Health check passed — tunnel registered")
            break

        log(f"  Still waiting... ({(deadline - time.time()) / 60:.0f}m remaining)")
        time.sleep(POLL_STATUS_INTERVAL)

    if not tunnel_obtained:
        log(f"  Tunnel not obtained in {KERNEL_RUN_TIMEOUT}s — trying next account")
        return False

    # 4. Final verification
    time.sleep(10)
    if not health_check():
        log("  Verification failed after rotation")
        return False

    # 5. Update state
    state["current_index"] = new_idx
    state["last_rotation"] = datetime.now(timezone.utc).isoformat()
    state["active_kernel_slug"] = slug
    state["active_account_email"] = account["email"]
    state["consecutive_failures"] = 0
    save_state(state)

    # Also update kernel-metadata.json
    if KERNEL_META_PATH.exists():
        try:
            with open(KERNEL_META_PATH) as f:
                meta = json.load(f)
            username = account.get("username") or account["email"].split("@")[0]
            meta["id"] = f"{username}/{slug}"
            with open(KERNEL_META_PATH, "w") as f:
                json.dump(meta, f, indent=2)
        except Exception as e:
            log(f"  Warning: could not update kernel-metadata.json: {e}")

    log(f"=== ROTATION COMPLETE -> {account['email']} / {slug} ===")
    return True


def run_once():
    accounts = load_accounts()
    if not accounts:
        log("ERROR: No accounts configured")
        return

    state = load_state()

    # Check cooldown
    if state.get("last_rotation"):
        elapsed = time.time() - datetime.fromisoformat(state["last_rotation"]).timestamp()
        if elapsed < ROTATION_COOLDOWN:
            return  # Too soon, skip

    # Check health
    healthy = health_check()
    if healthy:
        state["consecutive_failures"] = 0
        save_state(state)
        return

    state["consecutive_failures"] = state.get("consecutive_failures", 0) + 1
    save_state(state)

    if state["consecutive_failures"] < MAX_CONSECUTIVE_FAILURES:
        log(f"Health check failed ({state['consecutive_failures']}/{MAX_CONSECUTIVE_FAILURES}) — waiting")
        return

    log(f"Health check failed {state['consecutive_failures']} consecutive times — rotating")
    rotate(accounts, state)


def run_daemon(interval: int = 300):
    log(f"Daemon mode: checking every {interval}s")
    while True:
        run_once()
        time.sleep(interval)


if __name__ == "__main__":
    if "--daemon" in sys.argv:
        idx = sys.argv.index("--daemon")
        ival = int(sys.argv[idx + 1]) if idx + 1 < len(sys.argv) and sys.argv[idx + 1].isdigit() else 300
        run_daemon(ival)
    elif "--once" in sys.argv:
        run_once()
    else:
        run_once()
