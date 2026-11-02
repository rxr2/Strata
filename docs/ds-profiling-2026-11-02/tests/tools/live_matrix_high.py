#!/usr/bin/env python3
"""Sweep per-request spec_min_p / pcie_frac on the live Strata server (strata_tune), with the fixed class suite.
Records API timings, text hash and the engine log lines of each request. No restart, no profiler."""
import json, os, random, re, sys, time, urllib.request, hashlib, pathlib

URL = 'http://127.0.0.1:8081/v1/chat/completions'
LOG = os.environ.get('STRATA_LOG') or os.path.expanduser('~/harness/strata-engine.log')
PROMPTS = os.path.expanduser('~/Projekty/coding-bench/pipeline/suite_prompts.json')
OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '/tmp/opencode/matrix')
REPS = int(sys.argv[2]) if len(sys.argv) > 2 else 2
OUT.mkdir(parents=True, exist_ok=True)

DEC = re.compile(r'decode timing: (\d+) windows, avg T ([\d.]+), ([\d.]+) tokens/window, ([\d.]+) ms/window = .*?'
                 r'per layer-window: CPU experts ([\d.]+) \(([\d.]+) entries\), VRAM hits ([\d.]+), PCIe ([\d.]+); ([\d.]+) swaps/window')
HIT = re.compile(r'decode expert cache hit rate: ([\d.]+)% \((\d+) hits / (\d+) lookups\)(?:; (\d+) more read by the GPU over PCIe or from another GPU \(([\d.]+)% of all \d+ routed\))?')

VARIANTS = [
    ('base',   {'spec_min_p': 0.85, 'pcie_frac': 0.2}),
    ('minp090',{'spec_min_p': 0.90, 'pcie_frac': 0.2}),
    ('minp095',{'spec_min_p': 0.95, 'pcie_frac': 0.2}),
]

def log_pos():
    try: return os.path.getsize(LOG)
    except OSError: return 0

def log_since(pos):
    try:
        with open(LOG, 'rb') as f:
            f.seek(pos); return f.read().decode('utf-8', 'replace')
    except OSError:
        return ''

def chat(prompt, n, tune):
    body = {'model': 'x', 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': n,
            'temperature': 0, 'reasoning_effort': 'none', 'seed': 7, 'strata_checkpoint': False,
            'strata_tune': tune}
    r = urllib.request.Request(URL, json.dumps(body).encode(), {'Content-Type': 'application/json'})
    t0 = time.monotonic_ns(); d = json.load(urllib.request.urlopen(r, timeout=600)); t1 = time.monotonic_ns()
    return d, t0, t1

def parse(slice_text):
    dec = list(DEC.finditer(slice_text)); hit = list(HIT.finditer(slice_text))
    row = {}
    if dec:
        g = dec[-1].groups()
        for k, v in zip(['windows','T','tok_win','ms_win','cpu_exp','cpu_ent','vram_hits','pcie','swaps'], g):
            row[k] = float(v) if '.' in v else int(v)
        row['ms_tok'] = row['ms_win'] / max(row['tok_win'], 1e-9)
    if hit:
        g = hit[-1].groups()
        row.update(hit=float(g[0]), hits=int(g[1]), lookups=int(g[2]), pcie_off=int(g[3] or 0), pcie_pct=float(g[4] or 0))
    return row

prompts = json.load(open(PROMPTS))
# warm-up: one base request per class, discarded
for p in prompts:
    try: chat(p['prompt'], p.get('max_tokens', 192), VARIANTS[0][1])
    except Exception as e: print('warmup failed', p['name'], e, flush=True)

tasks = [(p, v) for p in prompts for v in VARIANTS for _ in range(REPS)]
random.Random(7).shuffle(tasks)
out = open(OUT / 'matrix.jsonl', 'w')
for i, (p, (label, tune)) in enumerate(tasks):
    pos = log_pos()
    d, t0, t1 = chat(p['prompt'], p.get('max_tokens', 192), tune)
    sl = log_since(pos)
    tim = d.get('timings') or {}
    pred = (d.get('usage') or {}).get('completion_tokens') or 0
    acc = tim.get('draft_n_accepted') or 0
    win = pred - acc if pred > acc else 0
    row = {'i': i, 'name': p['name'], 'variant': label, 'tune': tune,
           'tok_s': tim.get('predicted_per_second'), 'ms_tok': tim.get('predicted_per_token_ms'),
           'drafts': tim.get('draft_n'), 'accepted': tim.get('draft_n_accepted'),
           'windows': win, 'tok_win': (pred / win) if win else 0, 'ms_win': (tim.get('predicted_ms') or 0) / win if win else 0,
           'prompt_n': (d.get('usage') or {}).get('prompt_tokens'),
           'cached_n': ((d.get('usage') or {}).get('prompt_tokens_details') or {}).get('cached_tokens'),
           'gen_n': (d.get('usage') or {}).get('completion_tokens'),
           'hash': hashlib.sha1(d['choices'][0]['message'].get('content', '').encode()).hexdigest()[:10],
           'textlen': len(d['choices'][0]['message'].get('content', '')),
           't0': t0, 't1': t1, **parse(sl)}
    out.write(json.dumps(row) + '\n'); out.flush()
    print(f"{i:3d} {p['name']:14s} {label:8s} {row.get('tok_s') or 0:6.1f} tok/s  T {row.get('T',0):4.2f}  "
          f"tok/win {row.get('tok_win',0):4.2f}  hit {row.get('hit',0):5.1f}%  pcie {row.get('pcie_pct',0):3.1f}%", flush=True)
out.close()
print('saved', OUT / 'matrix.jsonl')
