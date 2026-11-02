#!/usr/bin/env python3
"""rep_table.py LOG - repeated traced runs (rep.log from rep_sweep.sh): per variant and prompt, us per token,
tokens per window, us per forward pass (= 48 fetch_blobs calls, the GPU speed independent of speculative acceptance),
the spread over repetitions and how many different answer texts came out."""
import collections, hashlib, statistics, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from pipeline_map import load, per_window
runs = [l.split() for l in open(sys.argv[1]) if '->' in l]
res = collections.defaultdict(list)
for parts in runs:
    name, d = parts[1], parts[-1]
    var = name.split('-', 1)[1]
    for p in (1, 2, 3):
        sub = pathlib.Path(d) / f'p{p}'
        if not (sub / 'run.json').exists(): continue
        wins, meta, _ = load(sub); k, wall, n = per_window(wins)
        tpw = meta['tok_per_win']; passes = k.get('fetch_blobs_kernel', {}).get('calls', 48) / 48
        res[(var, p)].append((wall / tpw, tpw, wall / passes, hashlib.md5(meta['text'].encode()).hexdigest()[:6]))
base = {p: statistics.mean(x[2] for x in res[('base', p)]) for p in (1, 2, 3) if res[('base', p)]}
baset = {p: statistics.mean(x[0] for x in res[('base', p)]) for p in (1, 2, 3) if res[('base', p)]}
print(f"{'variant':8s} {'prompt':6s} {'us/token (each rep)':28s} {'mean':>7s} {'vs base':>8s} | {'tok/win':>13s} | {'us/pass mean':>12s} {'sd':>5s} {'vs base':>8s} | texts")
for (var, p), xs in sorted(res.items(), key=lambda kv: (kv[0][1], kv[0][0])):
    t = [x[0] for x in xs]; ps = [x[2] for x in xs]
    print(f"{var:8s} p{p:<5d} {' '.join(f'{v:6.0f}' for v in t):28s} {statistics.mean(t):7.0f} {100 * (statistics.mean(t) / baset[p] - 1):+7.1f}% | "
          f"{' '.join(f'{x[1]:.2f}' for x in xs):13s} | {statistics.mean(ps):12.0f} {statistics.pstdev(ps):5.0f} {100 * (statistics.mean(ps) / base[p] - 1):+7.1f}% | "
          f"{len(set(x[3] for x in xs))} ({' '.join(x[3] for x in xs)})")
