#!/usr/bin/env python3
"""Collect the tail-skip results after the pipeline: random A/B, profiled pair, quality, D runs."""
import glob, json, os, re, statistics, sys
sys.path.insert(0, '/tmp/opencode')
import suite_analyze as sa

def latest(pat):
    xs = sorted(glob.glob(pat))
    return xs[-1] if xs else None

def rows(D):
    return {r['name']: r for r in sa.parse(D) if r.get('name') != 'save_flush'}

def mean(D):
    return statistics.mean(x['tok_s'] for x in rows(D).values()) if D else None

print('== randomized tail7 A/B')
if os.path.exists('/tmp/opencode/tailr_result.txt'):
    print(open('/tmp/opencode/tailr_result.txt').read())
else:
    print('missing tailr_result.txt')

print('\n== profiled pair (stages.json)')
for arm in ('tailbase-prof', 'tail7-prof'):
    d = latest(f'/home/rxr2/rx-perf-lab/pipeline/*-{arm}')
    if not d:
        print(arm, 'missing'); continue
    for p in ('p1', 'p2', 'p3'):
        f = f'{d}/{p}/stages.json'
        if not os.path.exists(f): continue
        j = json.load(open(f))
        b = j.get('balance', {}).get('per_token', {})
        g = j.get('gpu', {})
        h = j.get('host', {})
        print(f"{arm} {p}: us_tok {j.get('us_tok'):.0f} tok_win {j.get('tok_win'):.2f} "
              f"gpu_work {g.get('work'):.0f} pcie_rows {g.get('pcie_rows'):.0f} launch_gap {g.get('launch_gap'):.0f} "
              f"plan_wait {b.get('plan_wait',0):.0f} rows_read {b.get('rows_read',0):.0f} pcie {b.get('pcie',0):.0f} "
              f"cpu_pool {h.get('cpu_pool',0):.0f}")

print('\n== quality')
q = latest('/home/rxr2/rx-perf-lab/experiments/fork/*tail7')
if q and os.path.exists(q + '/RESULT.txt'):
    print(open(q + '/RESULT.txt').read())
else:
    print('missing quality RESULT')

print('\n== D runs (single)')
base = None
for name in ('tailr6-1','tailr8-1','tailp10-1','tailp30-1','tailq4-1','tailq4t-1','tailres3072-1','tailres2048-1'):
    d = latest(f'/home/rxr2/rx-perf-lab/suite/*-{name}')
    if d:
        print(name, round(mean(d), 2))
    else:
        print(name, 'missing')
