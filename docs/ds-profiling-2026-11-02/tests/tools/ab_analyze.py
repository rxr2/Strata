#!/usr/bin/env python3
"""Analyze the draft-vocabulary A/B sweep (3 blocks x 106k/140k/180k/248k, random order within a block)."""
import glob, statistics, sys
sys.path.insert(0, '/tmp/opencode')
import suite_analyze as sa

SIZES = [106, 140, 180, 248]

def find(block, size):
    xs = sorted(glob.glob(f'/home/rxr2/rx-perf-lab/suite/*-ab{size}-b{block}'))
    return xs[-1] if xs else None

def rows(D):
    return {r['name']: r for r in sa.parse(D) if r.get('name') != 'save_flush'}

data = {}
for b in (1, 2, 3):
    for s in SIZES:
        D = find(b, s)
        if D: data[(b, s)] = rows(D)

if not data:
    print('no runs found'); sys.exit(1)
classes = list(next(iter(data.values())).keys())

def acc(r):
    d = r.get('drafts') or 0
    return 100.0 * (r.get('accepted') or 0) / d if d else float('nan')

print('== tok/s per class (mean of 3 blocks)')
print(f"{'class':14s}" + ''.join(f" {s:>6}k" for s in SIZES) + f" {'d248':>7s} {'sd248':>6s}")
for c in classes:
    means = {s: statistics.mean(data[(b, s)][c]['tok_s'] for b in (1, 2, 3) if (b, s) in data and c in data[(b, s)]) for s in SIZES}
    d = []
    for b in (1, 2, 3):
        if (b, 106) in data and (b, 248) in data and c in data[(b, 106)] and c in data[(b, 248)]:
            d.append(100.0 * (data[(b, 248)][c]['tok_s'] / data[(b, 106)][c]['tok_s'] - 1.0))
    print(f"{c:14s}" + ''.join(f" {means[s]:7.1f}" for s in SIZES) +
          f" {100*(means[248]/means[106]-1):+6.1f}% {(statistics.stdev(d) if len(d) > 1 else 0):6.1f}")

print('\n== acceptance % (draft accepted / offered, mean of 3 blocks)')
print(f"{'class':14s}" + ''.join(f" {s:>6}k" for s in SIZES))
for c in classes:
    means = {s: statistics.mean(acc(data[(b, s)][c]) for b in (1, 2, 3) if (b, s) in data and c in data[(b, s)]) for s in SIZES}
    print(f"{c:14s}" + ''.join(f" {means[s]:6.1f}" for s in SIZES))

print('\n== paired delta vs 106k in the same block (mean of 3, SD across the 3)')
print(f"{'class':14s}" + ''.join(f" {s:>8}k" for s in SIZES))
for c in classes:
    out = []
    for s in SIZES:
        d = []
        for b in (1, 2, 3):
            if (b, 106) in data and (b, s) in data and c in data[(b, 106)] and c in data[(b, s)]:
                d.append(100.0 * (data[(b, s)][c]['tok_s'] / data[(b, 106)][c]['tok_s'] - 1.0))
        out.append(f"{statistics.mean(d):+6.1f}±{(statistics.stdev(d) if len(d) > 1 else 0):4.1f}" if d else '   -   ')
    print(f"{c:14s} " + ' '.join(out))

print('\n== overall mean tok/s per run')
for b in (1, 2, 3):
    line = []
    for s in SIZES:
        if (b, s) in data:
            line.append(f"{s}k {statistics.mean(x['tok_s'] for x in data[(b, s)].values()):6.1f}")
    print(f'  b{b}: ' + '  '.join(line))
print('\n== overall mean and paired delta')
for s in SIZES:
    vals = [statistics.mean(x['tok_s'] for x in data[(b, s)].values()) for b in (1, 2, 3) if (b, s) in data]
    d = []
    for b in (1, 2, 3):
        if (b, 106) in data and (b, s) in data:
            d.append(100.0 * (statistics.mean(x['tok_s'] for x in data[(b, s)].values()) /
                              statistics.mean(x['tok_s'] for x in data[(b, 106)].values()) - 1.0))
    print(f"  {s}k: mean {statistics.mean(vals):6.2f}  SD {statistics.stdev(vals) if len(vals)>1 else 0:5.2f}  "
          f"delta {statistics.mean(d) if d else 0:+6.2f}%  SD {statistics.stdev(d) if len(d)>1 else 0:5.2f}")
