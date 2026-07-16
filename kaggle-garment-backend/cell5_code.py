"""
Cell 5: Start Server + Tunnel + Keep-Alive (fp16 + OOM fix + int8 shim)
Paste this entire cell into Kaggle notebook Cell 5.
"""

# ---- vLLM compatibility layer (SHIM) ----
# Required because Garment-GPT main.py imports vllm, which isn't compatible with Kaggle P100 (sm_60).
import sys, types, torch

def _activate_vllm_shim():
    import importlib
    _orig_find_spec = importlib.util.find_spec
    def _patched_find_spec(name, *args, **kwargs):
        if name == 'vllm':
            return None
        return _orig_find_spec(name, *args, **kwargs)
    importlib.util.find_spec = _patched_find_spec

    class _HF_LLM:
        def __init__(self, model, **kwargs):
            from transformers import AutoProcessor, AutoConfig
            import torch

            use_8bit = False
            gpu_label = "cpu"
            if torch.cuda.is_available():
                cap = torch.cuda.get_device_capability()
                gpu_label = f"sm_{cap[0]}{cap[1]}"
                if cap >= (7, 0):
                    use_8bit = True

            print(f'[vllm-shim] Loading model {model} on {gpu_label}...')
            self._processor = AutoProcessor.from_pretrained(model, trust_remote_code=True)
            cfg_kwargs = dict(kwargs)
            cfg_kwargs.setdefault('trust_remote_code', True)
            cfg = AutoConfig.from_pretrained(model, **cfg_kwargs)
            if hasattr(cfg, 'vision_config'):
                try:
                    from transformers import AutoModelForVision2Seq
                    model_class = AutoModelForVision2Seq
                except ImportError:
                    from transformers import LlavaForConditionalGeneration
                    model_class = LlavaForConditionalGeneration
            else:
                from transformers import AutoModelForCausalLM
                model_class = AutoModelForCausalLM

            load_kwargs = dict(
                device_map='auto', trust_remote_code=True, torch_dtype=torch.float16,
            )
            if use_8bit:
                from transformers import BitsAndBytesConfig
                load_kwargs['quantization_config'] = BitsAndBytesConfig(
                    load_in_8bit=True, llm_int8_threshold=6.0,
                )

            self._model = model_class.from_pretrained(model, **load_kwargs)
            self._model.eval()
            print(f'[vllm-shim] Model loaded on {self._model.device}')

        def generate(self, inputs_list, sampling_params):
            results = []
            for inp in inputs_list:
                prompt = inp.get('prompt', '')
                images = inp.get('multi_modal_data', {}).get('image', [])
                if images:
                    proc = self._processor(text=prompt, images=images[0], return_tensors='pt').to(self._model.device)
                else:
                    proc = self._processor(text=prompt, return_tensors='pt').to(self._model.device)
                mt = getattr(sampling_params, 'max_tokens', 4096)
                tp = getattr(sampling_params, 'temperature', 0.1)
                with torch.no_grad():
                    out = self._model.generate(**proc, max_new_tokens=min(mt, 4096),
                        do_sample=tp > 0, temperature=max(tp, 0.01), top_p=0.9)
                gen = self._processor.decode(out[0], skip_special_tokens=False)
                class _O:
                    def __init__(self, text): self.text = text
                class _RO:
                    def __init__(self, outputs): self.outputs = outputs
                results.append(_RO(outputs=[_O(text=gen)]))
            return results

    class _HF_SamplingParams:
        def __init__(self, temperature=0.1, max_tokens=4096, skip_special_tokens=False, seed=42, stop_token_ids=None):
            self.temperature = temperature
            self.max_tokens = max_tokens
            self.skip_special_tokens = skip_special_tokens
            self.seed = seed
            self.stop_token_ids = stop_token_ids or []

    vllm_mod = types.ModuleType('vllm')
    vllm_mod.LLM = _HF_LLM
    vllm_mod.SamplingParams = _HF_SamplingParams
    sys.modules['vllm'] = vllm_mod
    print('[vllm-shim] vLLM compatibility shim installed (transformers + int8 backend)')

_activate_vllm_shim()

import os, subprocess, time, re, requests, shutil, threading
def register_tunnel(url):
    """POST tunnel URL to EC2 proxy + write output file for rotation script."""
    if not url or not url.startswith("http"):
        print(f"[Tunnel] Skipping registration: invalid URL '{url}'")
        return
    from pathlib import Path
    out = Path("/kaggle/working/output")
    out.mkdir(exist_ok=True)
    out.joinpath("tunnel_url.txt").write_text(url)
    print(f"[Tunnel] Written to {out/'tunnel_url.txt'}")
    for attempt in range(5):
        try:
            import requests as _req
            r = _req.post("https://korra.work/api/v2/garment/internal/tunnel",
                          json={"url": url}, timeout=10)
            body = r.text[:500]
            if r.status_code == 200:
                print(f"[Tunnel] Registered with EC2 proxy (attempt {attempt+1}): {body[:200]}")
                return
            print(f"[Tunnel] EC2 proxy HTTP {r.status_code} (attempt {attempt+1}): {body[:200]}")
        except Exception as e:
            print(f"[Tunnel] EC2 proxy error (attempt {attempt+1}): {e}")
        time.sleep(5)


# Locate cloudflared binary
CLOUDFLARED = shutil.which("cloudflared") or "/kaggle/working/cloudflared"
if not os.path.exists(CLOUDFLARED):
    raise FileNotFoundError(f"cloudflared not found at {CLOUDFLARED}")

# Kill any old processes
os.system("pkill -f api_server.py 2>/dev/null || true")
os.system("pkill -f cloudflared 2>/dev/null || true")
os.system("fuser -k 8000/tcp 2>/dev/null || true")
time.sleep(2)

tunnel_url = None
_tunnel_start_time = None
_tunnel_restarts = 0
_server_restarts = 0
_keep_alive_backoff = 60  # initial check interval in seconds
_max_server_restarts = 10  # after this, enter degraded mode
_degraded_mode = False
_watchdog_restarts = 0
_max_watchdog_restarts = 5

def _tunnel_reader(stream):
    """Read tunnel output, print it, and watch for tunnel URL."""
    global tunnel_url, _tunnel_start_time, _tunnel_restarts
    try:
        for line in iter(stream.readline, ''):
            if line:
                line = line.rstrip("\n")
                print(f"[TUN] {line}")
                if not tunnel_url:
                    m = re.search(r'https?://[^\s]*trycloudflare\.com[^\s]*', line)
                    if m:
                        tunnel_url = m.group(0)
                        _tunnel_start_time = time.time()
                        _tunnel_restarts += 1
                        print(f"\n{'='*60}\nTUNNEL URL: {tunnel_url}\n{'='*60}")
    except ValueError:
        pass
    finally:
        try:
            stream.close()
        except Exception:
            pass


def start_tunnel():
    global tunnel_url
    print(f"[TUN] Starting cloudflared from {CLOUDFLARED}...")
    p = subprocess.Popen(
        [CLOUDFLARED, "tunnel", "--url", "http://localhost:8000", "--no-autoupdate"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
    )
    # Drain tunnel logs in background thread (prevents pipe buffer blocking)
    t = threading.Thread(target=_tunnel_reader, args=(p.stdout,), daemon=True)
    t.start()
    # Wait for tunnel URL (up to 90s)
    deadline = time.time() + 90
    while time.time() < deadline:
        if tunnel_url:
            break
        if p.poll() is not None:
            print(f"[TUN] cloudflared died (code {p.returncode}), restarting...")
            return start_tunnel()
        time.sleep(2)
    return p


def _pipe_drainer(stream, prefix, log_file=None):
    """Read from a subprocess pipe continuously and print to stdout."""
    try:
        for line in iter(stream.readline, ''):
            if line:
                print(f"{prefix} {line.strip()}")
                if log_file:
                    log_file.write(line)
                    log_file.flush()
    except ValueError:
        pass  # closed stream
    finally:
        stream.close()
        if log_file:
            log_file.close()


def start_server():
    log_file = open("/kaggle/working/server_logs.txt", "a", buffering=1)
    p = subprocess.Popen(
        ["python", "/kaggle/working/api_server.py"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
    )
    t = threading.Thread(target=_pipe_drainer, args=(p.stdout, "[API]", log_file), daemon=True)
    t.start()
    # Wait for server to be ready (up to 60s)
    deadline = time.time() + 60
    while time.time() < deadline:
        try:
            r = requests.get("http://localhost:8000/health", timeout=3)
            if r.status_code < 500:
                print("[API] Server ready")
                break
        except Exception:
            time.sleep(1)
            continue
    return p


def kill_server(proc):
    """Gracefully kill server: SIGTERM -> wait 5s -> SIGKILL. Frees CUDA memory."""
    if proc is None:
        return
    pid = proc.pid
    if pid is None:
        return
    try:
        os.kill(pid, 0)  # Check if process exists
    except OSError:
        return  # Already dead
    print(f"[KEEP] Sending SIGTERM to server (PID {pid})...")
    try:
        proc.terminate()  # SIGTERM
        proc.wait(timeout=8)
        print(f"[KEEP] Server PID {pid} terminated gracefully")
    except subprocess.TimeoutExpired:
        print(f"[KEEP] Server PID {pid} didn't exit in 8s, sending SIGKILL...")
        proc.kill()  # SIGKILL
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print(f"[KEEP] Server PID {pid} still alive after SIGKILL, moving on")
    except Exception as e:
        print(f"[KEEP] Error killing server PID {pid}: {e}")
        try:
            proc.kill()
        except Exception:
            pass
    # Force CUDA memory cleanup after kill
    import gc
    gc.collect()

# Start tunnel first (blocking until URL), then server
t_proc = start_tunnel()
s_proc = start_server()

# Wait then health check
time.sleep(3)
try:
    r = requests.get("http://localhost:8000/health", timeout=5)
    print(f"Health: {r.json()}")
except Exception as e:
    print(f"Health check: {e}")

# Wait up to 90s for tunnel URL
for _wait in range(30):
    if tunnel_url:
        break
    time.sleep(3)
    print(f"[Tunnel] Waiting for URL... ({_wait*3+3}s)")
    if t_proc.poll() is not None:
        print(f"[Tunnel] cloudflared died (code {t_proc.returncode}), restarting...")
        t_proc = start_tunnel()

if tunnel_url:
    print(f"\nReady! Tunnel URL: {tunnel_url}")
    register_tunnel(tunnel_url)
else:
    print(f"\nTunnel URL not yet available — will retry in keep-alive loop")

# === STARTUP TIMEOUT (Phase 44) ===
_STARTUP_TIMEOUT = 120  # max seconds to wait for server + tunnel
_startup_deadline = time.time() + _STARTUP_TIMEOUT
while time.time() < _startup_deadline:
    # Check server health
    try:
        r = requests.get("http://localhost:8000/health", timeout=5)
        j = r.json()
        server_up = True
        print(f"Health: {j}")
    except Exception as e:
        server_up = False
        print(f"Startup health check: {e}")

    if tunnel_url and server_up:
        print(f"\nReady! Tunnel URL: {tunnel_url}")
        register_tunnel(tunnel_url)
        break

    # Check tunnel
    if t_proc.poll() is not None:
        print(f"[Tunnel] cloudflared died (code {t_proc.returncode}), restarting...")
        t_proc = start_tunnel()

    # Check server
    if s_proc.poll() is not None:
        print(f"[Server] api_server died (code {s_proc.returncode}), restarting...")
        s_proc = start_server()

    time.sleep(5)

if not tunnel_url:
    print(f"\nTunnel URL not yet available — will retry in keep-alive loop")
if not server_up:
    print(f"\nServer not responding — will retry in keep-alive loop")

# === KEEP-ALIVE LOOP (Phases 41-45) ===
print(f"\nKeep-alive running. Initial interval: {_keep_alive_backoff}s.")
import datetime as dt
_health_fails = 0
_tunnel_fails = 0

# === PHASE 45: WATCHDOG-MANAGED KEEP-ALIVE LOOP ===
def _keep_alive_loop():
    """Core keep-alive loop. Runs forever unless an exception escapes."""
    global _health_fails, _tunnel_fails, _server_restarts, _degraded_mode
    global _keep_alive_backoff, t_proc, s_proc, tunnel_url, _tunnel_start_time
    _health_fails = 0
    _tunnel_fails = 0
    while True:
        try:
            # Local health check
            r = requests.get("http://localhost:8000/health", timeout=10)
            j = r.json()
            _health_fails = 0
            # Phase 41: reset backoff on success
            _keep_alive_backoff = max(60, _keep_alive_backoff * 0.75)

            # Update tunnel_url from health if needed
            if tunnel_url and not tunnel_url.startswith('http'):
                tunnel_url = j.get('tunnel_url')

            # Phase 43: Tunnel health check via Cloudflare
            tunnel_alive_via_cloudflare = False
            if tunnel_url:
                try:
                    hr = requests.get(f"{tunnel_url}/health", timeout=10)
                    tunnel_alive_via_cloudflare = hr.status_code == 200
                except Exception:
                    pass

            tunnel_uptime = time.time() - _tunnel_start_time
            now = dt.datetime.now().strftime("%H:%M:%S")
            tu_label = (tunnel_url or 'WAITING')[-55:]
            alive_flag = 'CF' if tunnel_alive_via_cloudflare else 'LOCAL'
            gpu_ok = j.get('gpu_ok', True)
            mode_flag = 'DEGRADED' if _degraded_mode else 'ACTIVE'
            print(f"[{now}] {mode_flag} | GPU: {j.get('gpu','?')} ok={gpu_ok} | Tunnel: {tu_label} [{alive_flag}] up={tunnel_uptime/60:.0f}m | tunnel_restarts={_tunnel_restarts} server_restarts={_server_restarts}")

            if tunnel_url and tunnel_alive_via_cloudflare:
                register_tunnel(tunnel_url)
                _tunnel_fails = 0
            elif tunnel_url and not tunnel_alive_via_cloudflare:
                _tunnel_fails += 1
                print(f"[KEEP] Tunnel URL set but NOT reachable via Cloudflare ({_tunnel_fails}/3). Checking cloudflared process...")
                if t_proc.poll() is not None:
                    print(f"[KEEP] cloudflared died (code {t_proc.returncode}), restarting...")
                    t_proc = start_tunnel()
                    register_tunnel(tunnel_url)
                    _tunnel_start_time = time.time()
                elif _tunnel_fails >= 3:
                    print(f"[KEEP] 3 consecutive tunnel fails — killing cloudflared for fresh tunnel")
                    t_proc.kill()
                    t_proc = start_tunnel()
                    register_tunnel(tunnel_url)
                    _tunnel_start_time = time.time()
                    _tunnel_fails = 0
            elif t_proc.poll() is not None:
                print(f"[KEEP] cloudflared died (code {t_proc.returncode}), restarting...")
                t_proc = start_tunnel()
                register_tunnel(tunnel_url)
                _tunnel_start_time = time.time()
            else:
                _tunnel_fails += 1
                if _tunnel_fails >= 6:
                    print(f"[KEEP] Tunnel still waiting after ~30 min, restarting...")
                    t_proc.kill()
                    t_proc = start_tunnel()
                    register_tunnel(tunnel_url)
                    _tunnel_start_time = time.time()
                    _tunnel_fails = 0

        except Exception as e:
            now = dt.datetime.now().strftime("%H:%M:%S")
            _health_fails += 1
            # Phase 41: exponential backoff on failure
            _keep_alive_backoff = min(600, _keep_alive_backoff * 2.0)

            if _degraded_mode:
                print(f"[{now}] DEGRADED MODE: health fail ({_health_fails}/3), server restart SKIPPED (max restarts {_max_server_restarts} reached)")
                continue

            if _health_fails >= 3:
                _server_restarts += 1
                # Phase 42: max restart limit
                if _server_restarts > _max_server_restarts:
                    _degraded_mode = True
                    print(f"[{now}] Entering DEGRADED MODE after {_server_restarts} server restarts. Tunnel will stay up for manual recovery.")
                    continue

                print(f"[{now}] Health fail {_health_fails}/3 — restarting server ({_server_restarts}/{_max_server_restarts})")
                kill_server(s_proc)
                s_proc = start_server()
                _health_fails = 0
            else:
                print(f"[{now}] Health fail ({_health_fails}/3): {type(e).__name__}: {e} — not restarting yet")

        # Phase 41: adaptive sleep interval
        time.sleep(int(_keep_alive_backoff))


def _watchdog_main():
    """Watchdog wrapper: restarts _keep_alive_loop if it crashes."""
    global _watchdog_restarts, _keep_alive_backoff, _degraded_mode
    while True:
        try:
            _keep_alive_loop()
        except Exception as e:
            _watchdog_restarts += 1
            if _watchdog_restarts > _max_watchdog_restarts:
                print(f"[WATCHDOG] Max restarts ({_max_watchdog_restarts}) reached. Giving up.")
                break
            _keep_alive_backoff = min(600, _keep_alive_backoff * 2.0)
            wait = int(_keep_alive_backoff)
            print(f"[WATCHDOG] Keep-alive crashed ({type(e).__name__}: {e}). Restarting in {wait}s... (attempt {_watchdog_restarts}/{_max_watchdog_restarts})")
            time.sleep(wait)
            _degraded_mode = False
            # Kill and restart tunnel + server from scratch
            if t_proc: t_proc.kill()
            if s_proc: kill_server(s_proc)
            time.sleep(3)
            t_proc = start_tunnel()
            s_proc = start_server()


_watchdog_main()
