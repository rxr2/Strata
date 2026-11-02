#!/usr/bin/env python3
"""Join a suite_run.sh output (requests.jsonl + engine-tail.log) into one row per prompt."""
import json, re, sys, pathlib, hashlib

DEC = re.compile(r'decode timing: (\d+) windows, avg T ([\d.]+), ([\d.]+) tokens/window, ([\d.]+) ms/window = '
                 r'adapt wait ([\d.]+) \+ verify ([\d.]+) \(GPU-reach wait ([\d.]+) \+ per-layer host ([\d.]+) '
                 r'\[plan ([\d.]+) actq ([\d.]+) jobs ([\d.]+) CPU ([\d.]+)\] \+ stage ([\d.]+)\) \+ commit/emit ([\d.]+) '
                 r'\+ draft ([\d.]+) \+ adapt join ([\d.]+) \+ other ([\d.]+); per layer-window: CPU experts ([\d.]+) '
                 r'\(([\d.]+) entries\), VRAM hits ([\d.]+), PCIe ([\d.]+); ([\d.]+) swaps/window')
HIT = re.compile(r'decode expert cache hit rate: ([\d.]+)% \((\d+) hits / (\d+) lookups\)(?:; (\d+) more read by the GPU over PCIe or from another GPU \(([\d.]+)% of all \d+ routed\))?')

def parse(run):
    run = pathlib.Path(run)
    reqs = [json.loads(x) for x in (run / 'requests.jsonl').read_text().splitlines() if x.strip()]
    log = (run / 'engine-tail.log').read_text(errors='replace')
    decs = [m.groups() for m in DEC.finditer(log)]
    hits = [m.groups() for m in HIT.finditer(log)]
    # the warm-up logs one decode timing too; drop it if there is one more line than requests
    if len(decs) == len(reqs) + 1: decs = decs[1:]
    rows = []
    for i, r in enumerate(reqs):
        t = r.get('timings') or {}
        d = decs[i] if i < len(decs) else None
        h = hits[i] if i < len(hits) else None
        row = {'name': r.get('name'), 'prompt_n': (r.get('usage') or {}).get('prompt_tokens'),
               'gen_n': (r.get('usage') or {}).get('completion_tokens'),
               'tok_s': round(t.get('predicted_per_second', 0), 2),
               'drafts': t.get('draft_n'), 'accepted': t.get('draft_n_accepted'),
               'ms_tok': round(t.get('predicted_per_token_ms', 0), 3),
               'hash': hashlib.sha1(r.get('text', '').encode()).hexdigest()[:10],
               'textlen': len(r.get('text', ''))}
        if h: row.update(hit=float(h[0]), hits=int(h[1]), lookups=int(h[2]), pcie_off=int(h[3] or 0), pcie_pct=float(h[4] or 0))
        if d:
            keys = ['windows','T','tok_win','ms_win','adapt_wait','verify','gpu_reach_wait','host_layer','plan','actq','jobs',
                    'host_cpu','stage','commit','draft','adapt_join','other','cpu_exp','cpu_ent','vram_hits','pcie','swaps']
            for k, v in zip(keys, d): row[k] = float(v) if '.' in v else int(v)
            row['ms_tok'] = round(row['ms_win'] / max(row['tok_win'], 1e-9), 3)
            row['tok_s_calc'] = round(1000.0 / max(row['ms_tok'], 1e-9), 2)
        rows.append(row)
    return rows

if __name__ == '__main__':
    for run in sys.argv[1:]:
        print('==', run)
        for r in parse(run):
            if r.get('name') == 'save_flush': continue
            print(f"{r['name']:14s} {r['tok_s']:6.1f} tok/s  T {r.get('T',0):4.2f}  tok/win {r.get('tok_win',0):4.2f}  "
                  f"ms/win {r.get('ms_win',0):6.2f}  hit {r.get('hit',0):5.1f}%  pcie {r.get('pcie_pct',0):3.1f}%  "
                  f"cpu/lw {r.get('cpu_exp',0):4.2f}  vram/lw {r.get('vram_hits',0):4.2f}  drafts {r.get('accepted')}/{r.get('drafts')}  {r['hash']}")
