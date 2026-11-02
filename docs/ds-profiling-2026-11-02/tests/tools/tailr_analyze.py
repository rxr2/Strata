#!/usr/bin/env python3
"""Randomized 3-block tail7 A/B: per class and overall; prints OVERALL for the shell."""
import glob, statistics, sys
sys.path.insert(0, '/tmp/opencode')
import suite_analyze as sa

def find(block, arm):
    xs = sorted(glob.glob(f'/home/rxr2/rx-perf-lab/suite/*-tailr-{arm}-b{block}'))
    return xs[-1] if xs else None

def rows(D):
    return {r['name']: r for r in sa.parse(D) if r.get('name') != 'save_flush'}

data = {}
for b in (1, 2, 3):
    for arm in ('base', 'tail7'):
        D = find(b, arm)
        if D: data[(b, arm)] = rows(D)
if not data:
    print('no random runs'); sys.exit(1)
classes = list(next(iter(data.values())).keys())

print('== randomized tail7 A/B (3 blocks)')
print(f"{'class':14s} {'base':>7s} {'tail7':>7s} {'delta':>7s} {'sd':>5s}")
allb = []; allt = []
for c in classes:
    b = statistics.mean(data[(i, 'base')][c]['tok_s'] for i in (1, 2, 3) if (i, 'base') in data)
    t = statistics.mean(data[(i, 'tail7')][c]['tok_s'] for i in (1, 2, 3) if (i, 'tail7') in data)
    d = [100 * (data[(i, 'tail7')][c]['tok_s'] / data[(i, 'base')][c]['tok_s'] - 1) for i in (1, 2, 3)
         if (i, 'base') in data and (i, 'tail7') in data]
    print(f"{c:14s} {b:7.1f} {t:7.1f} {statistics.mean(d) if d else 0:+6.1f}% {statistics.stdev(d) if len(d)>1 else 0:5.1f}")
    allb.append(b); allt.append(t)

bm = statistics.mean(allb); tm = statistics.mean(allt)
deltas = []
for i in (1, 2, 3):
    if (i, 'base') in data and (i, 'tail7') in data:
        b = statistics.mean(x['tok_s'] for x in data[(i, 'base')].values())
        t = statistics.mean(x['tok_s'] for x in data[(i, 'tail7')].values())
        deltas.append(100 * (t / b - 1))
print(f"OVERALL {bm:.2f} {tm:.2f} {100*(tm/bm-1):+.2f} {statistics.stdev(deltas) if len(deltas)>1 else 0:.2f}")
print('per-block deltas', [round(x, 2) for x in deltas])
