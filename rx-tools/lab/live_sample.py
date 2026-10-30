"""Live sampling (250 ms) of GPU (amdgpu_top + sysfs), CPU (/proc/stat), RAM, NVMe reads during one 32K prompt + 512-token
decode on production. usage: python3 -I live.py OUT_DIR"""
import os, json, sys, time, threading, subprocess, urllib.request, uuid
from pathlib import Path
BASE = os.environ.get('STRATA_URL', 'http://127.0.0.1:8081')
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
AT = os.environ.get('AMDGPU_TOP', 'amdgpu_top'); DEV = '/sys/class/drm/' + os.environ.get('STRATA_DRM_CARD', 'card1') + '/device'
samples, stop, phase = [], threading.Event(), {'p': 'idle'}
def rd(p):
    try: return open(p).read()
    except Exception: return ''
def cpu():
    out = {}
    for l in rd('/proc/stat').splitlines():
        if l.startswith('cpu'):
            f = l.split(); v = list(map(int, f[1:9])); out[f[0]] = (sum(v) - v[3] - v[4], sum(v))
    return out
def disk():
    for l in rd('/proc/diskstats').splitlines():
        f = l.split()
        if f[2] == os.environ.get('STRATA_DRIVE', 'nvme1n1'): return int(f[5]) * 512
    return 0
at = {'last': {}}
def at_reader():
    p = subprocess.Popen([AT, '-J', '-s', '250'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    for line in p.stdout:
        if stop.is_set(): break
        try:
            g = json.loads(line)['devices'][0]; s = g['Sensors']; v = g['VRAM']
            at['last'] = {'gfx_pipe': g['GRBM']['Graphics Pipe']['value'], 'sclk': s['GFX_SCLK']['value'],
                          'mclk': s['GFX_MCLK']['value'], 'power': s['Average Power']['value'],
                          'vram_mib': v['Total VRAM Usage']['value'], 'gtt_mib': v['Total GTT Usage']['value']}
        except Exception: pass
    p.kill()
def sampler():
    c0, d0, t0 = cpu(), disk(), time.monotonic()
    while not stop.is_set():
        time.sleep(0.25)
        c1, d1, t1 = cpu(), disk(), time.monotonic()
        per = {k: 100 * (c1[k][0] - c0[k][0]) / max(1, c1[k][1] - c0[k][1]) for k in c1}
        mi = {l.split(':')[0]: int(l.split()[1]) for l in rd('/proc/meminfo').splitlines()}
        samples.append({'t': t1, 'phase': phase['p'], 'cpu': per['cpu'], 'cores': [per[k] for k in sorted(per) if k != 'cpu'],
                        'disk_mbs': (d1 - d0) / (t1 - t0) / 1e6, 'ram_used_gib': (mi['MemTotal'] - mi['MemAvailable']) / 2**20,
                        'gpu_busy': int(rd(DEV + '/gpu_busy_percent') or 0), 'mem_busy': int(rd(DEV + '/mem_busy_percent') or 0),
                        **at['last']})
        c0, d0, t0 = c1, d1, t1
threading.Thread(target=at_reader, daemon=True).start(); threading.Thread(target=sampler, daemon=True).start()
root = Path(os.environ.get('STRATA_CORPUS', Path(__file__).resolve().parents[2])) / 'src'
corpus = ''.join(p.read_text(errors='replace') for p in sorted(root.rglob('*')) if p.suffix in ('.cpp', '.cu', '.hpp') and p.is_file())
with urllib.request.urlopen(BASE + '/v1/models') as r: MODEL = json.load(r)['data'][0]['id']
time.sleep(3)
res = []
for rep, chars in enumerate((105_000, 105_000)):
    text = f'[tag {uuid.uuid4().hex[:8]}]\n' + corpus[900_000 + rep * 300_000:][:chars] + \
        '\n\nNa podstawie powyższego kodu napisz w C++ nową, kompletną klasę ReadLatencyStats z komentarzami. Tylko kod.'
    body = {'model': MODEL, 'messages': [{'role': 'user', 'content': text}], 'max_tokens': 512, 'temperature': 0.2,
            'stream': True, 'reasoning_effort': 'none'}
    req = urllib.request.Request(BASE + '/v1/chat/completions', json.dumps(body).encode(), {'Content-Type': 'application/json'})
    phase['p'] = f'prefill{rep}'; ts = time.monotonic(); tf = None
    with urllib.request.urlopen(req, timeout=1800) as r:
        for line in r:
            if not line.startswith(b'data: ') or line.strip() == b'data: [DONE]': continue
            ch = (json.loads(line[6:]).get('choices') or [{}])[0].get('delta', {})
            if (ch.get('content') or ch.get('reasoning_content')) and tf is None:
                tf = time.monotonic(); phase['p'] = f'decode{rep}'
    te = time.monotonic(); phase['p'] = 'idle'; time.sleep(2)
    with urllib.request.urlopen(BASE + '/metrics?all=1') as r: m = json.load(r)
    h = max(m['requests'], key=lambda x: x.get('time') or 0)
    res.append({'rep': rep, 'ttft_s': tf - ts, 'decode_s': te - tf, **h}); print(json.dumps(res[-1]), flush=True)
time.sleep(2); stop.set(); time.sleep(0.5)
(OUT / 'samples.json').write_text(json.dumps(samples)); (OUT / 'requests.json').write_text(json.dumps(res, indent=1))
# summary per phase (rep 1 only = warm)
import statistics as st
for ph in ('prefill1', 'decode1', 'idle'):
    xs = [s for s in samples if s['phase'] == ph]
    if not xs: continue
    def m_(k): v = [s[k] for s in xs if k in s]; return round(st.mean(v), 1) if v else None
    mx = lambda k: round(max(s[k] for s in xs if k in s), 1) if any(k in s for s in xs) else None
    print(ph, len(xs), {k: m_(k) for k in ('cpu', 'disk_mbs', 'ram_used_gib', 'gpu_busy', 'mem_busy', 'gfx_pipe', 'sclk', 'mclk', 'power', 'vram_mib')},
          'max', {k: mx(k) for k in ('cpu', 'disk_mbs', 'gpu_busy', 'mem_busy', 'power')},
          'cores_mean', [round(st.mean(s['cores'][i] for s in xs), 0) for i in range(len(xs[0]['cores']))])
