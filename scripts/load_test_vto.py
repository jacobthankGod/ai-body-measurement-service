#!/usr/bin/env python3
"""
Phase 207: VTO Load Test Runner
===============================
Python-based load test for VTO endpoints. Uses asyncio + httpx for concurrency.
No external dependencies beyond what's already in the project.

Usage:
    python scripts/load_test_vto.py [--url URL] [--concurrency N] [--duration S] [--endpoint PATH]

Examples:
    python scripts/load_test_vto.py --url http://localhost:8001 --concurrency 5 --duration 30
    python scripts/load_test_vto.py --url https://korra.work --concurrency 10 --endpoint /api/v2/garment/vto/synthesize
"""
import asyncio
import argparse
import time
import io
import struct
import zlib
import json
from dataclasses import dataclass, field
from typing import Optional

try:
    import httpx
except ImportError:
    print("ERROR: httpx required. Install with: pip install httpx")
    exit(1)


def create_tiny_png(width=64, height=64, color=(200, 150, 100)) -> bytes:
    """Create a minimal valid PNG file in memory."""
    def chunk(chunk_type: bytes, data: bytes) -> bytes:
        c = chunk_type + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    header = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)

    raw_data = b""
    for y in range(height):
        raw_data += b"\x00"  # filter none
        for x in range(width):
            raw_data += bytes(color)

    compressed = zlib.compress(raw_data)

    return header + chunk(b"IHDR", ihdr) + chunk(b"IDAT", compressed) + chunk(b"IEND", b"")


@dataclass
class LoadTestConfig:
    base_url: str = "http://localhost:8001"
    concurrency: int = 5
    duration_sec: int = 30
    endpoint: str = "/api/v2/garment/vto/tryon"
    api_key: str = "supersecrettoken"
    ramp_up_sec: int = 3  # seconds to ramp up to full concurrency


@dataclass
class LoadTestResults:
    total_requests: int = 0
    success: int = 0
    rate_limited: int = 0
    errors: int = 0
    timeouts: int = 0
    latencies: list = field(default_factory=list)
    status_codes: dict = field(default_factory=dict)
    start_time: float = 0
    end_time: float = 0

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

    @property
    def rps(self) -> float:
        return self.total_requests / max(self.duration, 0.001)

    @property
    def avg_latency(self) -> float:
        return sum(self.latencies) / max(len(self.latencies), 1)

    @property
    def p50(self) -> float:
        if not self.latencies:
            return 0
        s = sorted(self.latencies)
        return s[len(s) // 2]

    @property
    def p95(self) -> float:
        if not self.latencies:
            return 0
        s = sorted(self.latencies)
        return s[int(len(s) * 0.95)]

    @property
    def p99(self) -> float:
        if not self.latencies:
            return 0
        s = sorted(self.latencies)
        return s[int(len(s) * 0.99)]

    def print_report(self):
        print("═" * 50)
        print("  VTO LOAD TEST RESULTS")
        print("═" * 50)
        print(f"  Endpoint:      {config.endpoint}")
        print(f"  Concurrency:   {config.concurrency}")
        print(f"  Duration:      {self.duration:.1f}s")
        print(f"  Total Requests:{self.total_requests}")
        print(f"  RPS:           {self.rps:.2f} req/s")
        print(f"  Success:       {self.success} ({self.success / max(self.total_requests, 1) * 100:.1f}%)")
        print(f"  Rate Limited:  {self.rate_limited}")
        print(f"  Errors:        {self.errors}")
        print(f"  Timeouts:      {self.timeouts}")
        print(f"  Latency avg:   {self.avg_latency * 1000:.1f}ms")
        print(f"  Latency p50:   {self.p50 * 1000:.1f}ms")
        print(f"  Latency p95:   {self.p95 * 1000:.1f}ms")
        print(f"  Latency p99:   {self.p99 * 1000:.1f}ms")
        print(f"  Status Codes:  {self.status_codes}")
        print("═" * 50)


config = LoadTestConfig()
results = LoadTestResults()


async def send_request(client: httpx.AsyncClient, worker_id: int):
    """Send a single VTO request."""
    png_bytes = create_tiny_png(64, 64, (100 + worker_id * 20, 150, 200))
    multipart = httpx.MultipartStream(
        fields={
            "file": ("test.png", io.BytesIO(png_bytes), "image/png"),
            "angle": "front",
            "garment_type": "tshirt",
            "garment_color": "#3366cc",
            "scan_id": "",
        }
    )

    t0 = time.monotonic()
    try:
        resp = await client.post(
            config.endpoint,
            content=multipart.read(),
            headers={
                "Content-Type": multipart.content_type,
                "Authorization": f"Bearer {config.api_key}",
            },
            timeout=60.0,
        )
        elapsed = time.monotonic() - t0
        results.latencies.append(elapsed)
        results.total_requests += 1
        status = resp.status_code
        results.status_codes[status] = results.status_codes.get(status, 0) + 1

        if status in (200, 202):
            results.success += 1
        elif status == 429:
            results.rate_limited += 1
        else:
            results.errors += 1
    except httpx.TimeoutException:
        results.timeouts += 1
        results.total_requests += 1
    except Exception as e:
        results.errors += 1
        results.total_requests += 1


async def worker(client: httpx.AsyncClient, worker_id: int, stop_event: asyncio.Event):
    """Continuous request worker."""
    # Ramp up delay
    await asyncio.sleep(worker_id * (config.ramp_up_sec / max(config.concurrency, 1)))

    while not stop_event.is_set():
        await send_request(client, worker_id)
        # Small delay to avoid overwhelming
        await asyncio.sleep(0.1)


async def run_load_test():
    """Run the full load test."""
    print(f"Starting load test: {config.concurrency} workers × {config.duration_sec}s")
    print(f"Target: {config.base_url}{config.endpoint}")

    results.start_time = time.time()
    stop_event = asyncio.Event()

    async with httpx.AsyncClient(base_url=config.base_url) as client:
        # Health check first
        try:
            health = await client.get("/health", timeout=5.0)
            print(f"Health check: {health.status_code}")
            if health.status_code != 200:
                print("WARNING: Target is not healthy!")
        except Exception as e:
            print(f"WARNING: Health check failed: {e}")

        # Start workers
        tasks = []
        for i in range(config.concurrency):
            tasks.append(asyncio.create_task(worker(client, i, stop_event)))

        # Wait for duration
        await asyncio.sleep(config.duration_sec)
        stop_event.set()

        # Wait for all workers to finish
        await asyncio.gather(*tasks, return_exceptions=True)

    results.end_time = time.time()
    results.print_report()

    # Save report
    report = {
        "endpoint": config.endpoint,
        "concurrency": config.concurrency,
        "duration_sec": config.duration_sec,
        "total_requests": results.total_requests,
        "rps": round(results.rps, 2),
        "success": results.success,
        "rate_limited": results.rate_limited,
        "errors": results.errors,
        "timeouts": results.timeouts,
        "latency_avg_ms": round(results.avg_latency * 1000, 1),
        "latency_p50_ms": round(results.p50 * 1000, 1),
        "latency_p95_ms": round(results.p95 * 1000, 1),
        "latency_p99_ms": round(results.p99 * 1000, 1),
        "status_codes": results.status_codes,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    with open("load_test_report.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport saved to load_test_report.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VTO Load Test Runner")
    parser.add_argument("--url", default="http://localhost:8001", help="Base URL")
    parser.add_argument("--concurrency", type=int, default=5, help="Concurrent workers")
    parser.add_argument("--duration", type=int, default=30, help="Test duration (seconds)")
    parser.add_argument("--endpoint", default="/api/v2/garment/vto/tryon", help="API endpoint path")
    args = parser.parse_args()

    config.base_url = args.url
    config.concurrency = args.concurrency
    config.duration_sec = args.duration
    config.endpoint = args.endpoint

    asyncio.run(run_load_test())
