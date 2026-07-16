#!/usr/bin/env python3
"""
End-to-End Garment Reconstruction Test
Tests: proxy health -> tunnel URL valid -> auth -> upload image -> poll result

Usage:
  python scripts/e2e_garment_test.py [--token YOUR_SUPABASE_TOKEN] [--image path/to/test.jpg]
"""
import argparse
import io
import json
import sys
import time
import os
from pathlib import Path

import requests

BASE_URL = os.getenv("GARMENT_BASE_URL", "https://korra.work")
TEST_IMAGE = Path(__file__).parent.parent / "public" / "assets" / "test_garment.jpg"

def test_health():
    r = requests.get(f"{BASE_URL}/api/v2/garment/health", timeout=10)
    assert r.status_code == 200, f"Health: {r.status_code}"
    j = r.json()
    assert j["status"] == "healthy", f"Health status: {j}"
    print(f"[PASS] Proxy health: {j['kaggle_backend']} | tunnel: {j.get('tunnel_url','?')[:50]}...")
    return j

def test_tunnel_url():
    r = requests.get(f"{BASE_URL}/api/v2/garment/tunnel-url", timeout=10)
    assert r.status_code == 200, f"Tunnel URL: {r.status_code}"
    j = r.json()
    assert j["active_url"] and j["active_url"] != "not set", f"No tunnel URL: {j}"
    print(f"[PASS] Tunnel URL: {j['active_url'][:60]}... | cached: {'yes' if j.get('cached_on_disk') else 'no'}")
    return j["active_url"]

def test_tunnel_reachable(tunnel_url):
    r = requests.get(f"{tunnel_url}/health", timeout=15)
    assert r.status_code == 200, f"Tunnel health: {r.status_code}"
    j = r.json()
    print(f"[PASS] Kaggle backend reachable | GPU: {j.get('gpu','?')} | models: {j.get('rembg', False)}")
    return j

def test_reconstruct(token: str, image_path: Path):
    if not image_path.exists():
        print(f"[SKIP] Test image not found at {image_path}")
        return False

    headers = {"Authorization": f"Bearer {token}"}
    with open(image_path, "rb") as f:
        files = {"file": ("test.jpg", f, "image/jpeg")}
        data = {"include_mesh": "true", "include_pattern": "true"}
        r = requests.post(
            f"{BASE_URL}/api/v2/garment/reconstruct",
            headers=headers,
            files=files,
            params=data,
            timeout=600,
        )

    if r.status_code == 200:
        # Direct zip response (synchronous path) or stream
        content_type = r.headers.get("content-type", "")
        if "zip" in content_type:
            out = f"/tmp/garment_e2e_test_{int(time.time())}.zip"
            with open(out, "wb") as f:
                f.write(r.content)
            print(f"[PASS] Reconstruction complete: {out} ({len(r.content)} bytes)")
            return True
        else:
            # Async path: got job_id
            j = r.json()
            job_id = j.get("job_id")
            print(f"[INFO] Async job created: {job_id}")
            # Poll for result
            for _ in range(120):
                r2 = requests.get(f"{BASE_URL}/api/v2/garment/result/{job_id}", headers=headers, timeout=10)
                if r2.status_code == 200:
                    j2 = r2.json()
                    if j2.get("status") == "completed":
                        print(f"[PASS] Job {job_id} completed")
                        return True
                    elif j2.get("status") == "failed":
                        print(f"[FAIL] Job {job_id} failed: {j2.get('error', 'unknown')}")
                        return False
                time.sleep(5)
            print(f"[FAIL] Job {job_id} timed out after 600s")
            return False
    else:
        detail = ""
        try:
            detail = r.json().get("detail", r.text[:200])
        except Exception:
            detail = r.text[:200]
        print(f"[FAIL] Reconstruct returned {r.status_code}: {detail}")
        return False

def main():
    parser = argparse.ArgumentParser(description="E2E test for garment reconstruction")
    parser.add_argument("--token", help="Supabase access token")
    parser.add_argument("--image", type=Path, default=TEST_IMAGE, help="Test image path")
    args = parser.parse_args()

    print("=" * 60)
    print("E2E Garment Reconstruction Test")
    print("=" * 60)

    # 1. Health check
    health = test_health()

    # 2. Tunnel URL
    tunnel_url = test_tunnel_url()

    # 3. Tunnel reachable
    test_tunnel_reachable(tunnel_url)

    # 4. Reconstruct (requires token)
    if args.token:
        test_reconstruct(args.token, args.image)
    else:
        print("[SKIP] Reconstruct test: no --token provided")
        print("  Get a token from browser dev console:")
        print("  window.KORRA_DB.auth.getSession().then(d => console.log(d.data.session.access_token))")

    print("=" * 60)
    print("Done.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
