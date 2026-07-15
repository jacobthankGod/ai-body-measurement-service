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

import os, subprocess, time, re, requests, shutil
def register_tunnel(url):
    """POST tunnel URL to EC2 proxy + write output file for rotation script."""
    if not url or not url.startswith("http"):
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
            if r.status_code == 200:
                print(f"[Tunnel] Registered with EC2 proxy (attempt {attempt+1})")
                return
            print(f"[Tunnel] EC2 proxy HTTP {r.status_code} (attempt {attempt+1})")
        except Exception as e:
            print(f"[Tunnel] EC2 proxy error (attempt {attempt+1}): {e}")
        time.sleep(5)


# Locate cloudflared binary
CLOUDFLARED = shutil.which("cloudflared") or "/kaggle/working/cloudflared"
if not os.path.exists(CLOUDFLARED):
    raise FileNotFoundError(f"cloudflared not found at {CLOUDFLARED}")

# Kill any old processes
!pkill -f api_server.py 2>/dev/null || true
!pkill -f cloudflared 2>/dev/null || true
!fuser -k 8000/tcp 2>/dev/null || true
time.sleep(2)

tunnel_url = None

def start_tunnel():
    global tunnel_url
    p = subprocess.Popen(
        [CLOUDFLARED, "tunnel", "--url", "http://localhost:8000", "--no-autoupdate"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
    )
    for line in p.stdout:
        m = re.search(r'https?://[^\s]*trycloudflare\.com[^\s]*', line.strip())
        if m:
            tunnel_url = m.group(0)
            print(f"\n{'='*60}\nTUNNEL URL: {tunnel_url}\n{'='*60}")
            break
    return p


def start_server():
    p = subprocess.Popen(
        ["python", "/kaggle/working/api_server.py"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
    )
    for line in p.stdout:
        print(f"[API] {line.strip()}")
        if "Uvicorn running" in line:
            break
    return p

# +++ FIX: Start server FIRST, then tunnel +++
s_proc = start_server()      # Blocks until port 8000 is up
t_proc = start_tunnel()      # Blocks until tunnel URL (origin now reachable)

# Wait then health check
time.sleep(3)
try:
    r = requests.get("http://localhost:8000/health", timeout=5)
    print(f"Health: {r.json()}")
except Exception as e:
    print(f"Health check: {e}")

if tunnel_url:
    print(f"\nReady! Tunnel URL: {tunnel_url}")
    register_tunnel(tunnel_url)
else:
    print(f"\nKeep watching for the Tunnel URL above...")

# === KEEP-ALIVE LOOP ===
print("\nKeep-alive running. Will print status every 5 minutes.")
import datetime as dt
while True:
    try:
        r = requests.get("http://localhost:8000/health", timeout=5)
        j = r.json()
        if tunnel_url and not tunnel_url.startswith('http'):
            tunnel_url = j.get('tunnel_url')
        now = dt.datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] Healthy | GPU: {j.get('gpu','?')} | Tunnel: {'OK' if tunnel_url else 'WAITING'}")
        if tunnel_url:
            register_tunnel(tunnel_url)
        if tunnel_url:
            register_tunnel(tunnel_url)
    except Exception as e:
        print(f"[{dt.datetime.now().strftime('%H:%M:%S')}] Server down! Restarting... ({e})")
        s_proc = start_server()
        if not tunnel_url:
            t_proc.kill()
            t_proc = start_tunnel()
    time.sleep(300)
