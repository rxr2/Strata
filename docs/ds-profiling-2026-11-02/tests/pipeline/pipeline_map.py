#!/usr/bin/env python3
"""Pipeline map of a Strata decode from a rocprofv3 kernel trace (trace_run.sh): microseconds up to seconds.

  pipeline_map.py RUN_DIR                 report: answer -> decode window -> layer half -> kernel (us), gaps, registers
  pipeline_map.py RUN_A RUN_B             A/B: per kernel and per gap, the change in us per window, summed up to tok/s

Windows are cut at gdn_step_commit_layers_kernel (one per decode window); layer halves start at each HC read
(gr_down*/k_down: the mixer half and the FFN half of every layer). Kernel names are merged over template arguments.
"""
import collections, json, pathlib, re, sqlite3, statistics, sys

def short(n):
    n = n.replace('(anonymous namespace)::', '').replace('strata::kernels::', '').replace('void ', '')
    return re.sub(r'<.*', '', re.sub(r'\(.*', '', n)).strip()

def load(run):
    run = pathlib.Path(run)
    db = run / 'trace.db'
    if not db.exists(): db = next(run.rglob('*.db'))
    c = sqlite3.connect(db)
    rows = c.execute('select name, start, "end", stream_id, grid_x*grid_y*grid_z, workgroup_x*workgroup_y*workgroup_z, '
                     'vgpr_count, sgpr_count, lds_size, scratch_size from kernels order by start').fetchall()
    meta = json.loads((run / 'run.json').read_text()) if (run / 'run.json').exists() else {}
    if meta.get('t0_ns'):
        rows = [r for r in rows if meta['t0_ns'] <= r[1] <= meta['t1_ns']] or rows
    commits = [i for i, r in enumerate(rows) if 'gdn_step_commit_layers' in r[0]]
    wins = [rows[commits[i] + 1:commits[i + 1] + 1] for i in range(len(commits) - 1)]
    n_all = len(wins)
    wins = wins[len(wins) // 10:]          # skip the first 10 % (prefill tail, warm caches)
    toks = (meta.get('usage') or {}).get('completion_tokens')
    meta['tok_per_win'] = toks / n_all if toks and n_all else None   # tokens accepted per window (speculative decoding)
    return wins, meta, run.name

def per_window(wins):
    """For each kernel name: calls, kernel us, gap-before us (per window); window wall / busy / idle."""
    agg = collections.defaultdict(lambda: {'calls': 0, 'us': 0.0, 'gap': 0.0, 'durs': [], 'grid': 0, 'wg': 0, 'vgpr': 0, 'sgpr': 0, 'lds': 0, 'scratch': 0})
    wall = busy = 0.0
    for w in wins:
        wall += (w[-1][2] - w[0][1]) / 1e3
        prev_end = None
        for r in w:
            k = agg[short(r[0])]
            d = (r[2] - r[1]) / 1e3
            k['calls'] += 1; k['us'] += d; k['durs'].append(d)
            k['grid'], k['wg'], k['vgpr'], k['sgpr'], k['lds'], k['scratch'] = r[4], r[5], r[6], r[7], r[8], r[9]
            if prev_end is not None and r[1] > prev_end: k['gap'] += (r[1] - prev_end) / 1e3
            prev_end = max(prev_end or 0, r[2])
            busy += d
    n = len(wins)
    return {k: {**v, 'calls': v['calls'] / n, 'us': v['us'] / n, 'gap': v['gap'] / n,
                'med': statistics.median(v['durs']) if v['durs'] else 0} for k, v in agg.items()}, wall / n, n

def halves(wins):
    """us per layer half (kernels + gaps), averaged over windows, split by mixer type (GDN / QSA) and FFN."""
    out = collections.defaultdict(list)
    for w in wins:
        starts = [i for i, r in enumerate(w) if re.search(r'gr_down|k_down', r[0])]
        for j in range(len(starts) - 1):
            seg = w[starts[j]:starts[j + 1]]
            names = ' '.join(short(r[0]) for r in seg)
            kind = 'FFN (router, shared, experts)' if 'route' in names else ('QSA mixer (attention)' if 'attn' in names else 'GDN mixer (recurrent)')
            out[kind].append(((seg[-1][2] - seg[0][1]) / 1e3, sum((r[2] - r[1]) / 1e3 for r in seg), len(seg)))
    return {k: (statistics.mean(x[0] for x in v), statistics.mean(x[1] for x in v), statistics.mean(x[2] for x in v), len(v) / len(wins))
            for k, v in out.items()}

def report(run):
    wins, meta, name = load(run)
    k, wall, n = per_window(wins)
    busy = sum(v['us'] for v in k.values()); gaps = sum(v['gap'] for v in k.values())
    toks = (meta.get('usage') or {}).get('completion_tokens')
    tpw = (toks / (n / 0.9)) if toks else None
    print(f'== {name}: {n} decode windows measured')
    print(f'answer: {toks} tokens' + (f', ~{tpw:.2f} tokens per window -> {1e6 * tpw / wall:.1f} tok/s from the window time' if tpw else ''))
    print(f'window: {wall:.0f} us = kernels {busy:.0f} us ({100 * busy / wall:.0f}%) + gaps {gaps:.0f} us ({100 * gaps / wall:.0f}%), '
          f'{sum(v["calls"] for v in k.values()):.0f} kernels')
    print('\nlayer halves (per occurrence): wall us | kernel us | kernels | per window')
    for kind, (w, b, c, per) in sorted(halves(wins).items()):
        print(f'  {kind:32s} {w:7.1f} | {b:7.1f} | {c:5.1f} | x{per:.0f}')
    print(f"\n{'kernel':34s} {'calls/w':>8s} {'med us':>7s} {'us/w':>8s} {'gap/w':>7s} {'share':>6s}  grid x wg  vgpr sgpr lds scr")
    for nm, v in sorted(k.items(), key=lambda kv: -(kv[1]['us'] + kv[1]['gap']))[:40]:
        print(f"{nm[:34]:34s} {v['calls']:8.1f} {v['med']:7.1f} {v['us']:8.0f} {v['gap']:7.0f} {100 * (v['us'] + v['gap']) / wall:5.1f}%  "
              f"{v['grid'] // max(v['wg'], 1)}x{v['wg']}  {v['vgpr']} {v['sgpr']} {v['lds']} {v['scratch']}")

def diff(a, b):
    """A/B per generated token: windows hold a different number of tokens when the numerics change speculative
    acceptance or the commit is cut differently, so per-window time alone can mislead."""
    wa, ma, na = load(a); wb, mb, nb = load(b)
    ka, walla, _ = per_window(wa); kb, wallb, _ = per_window(wb)
    pa, pb = ma['tok_per_win'], mb['tok_per_win']
    print(f'== A {na}  vs  B {nb}')
    print(f'window: {walla:.0f} -> {wallb:.0f} us ({100 * (wallb - walla) / walla:+.1f}%), tokens per window {pa:.2f} -> {pb:.2f}')
    ta, tb = walla / pa, wallb / pb
    print(f'per token: {ta:.0f} -> {tb:.0f} us ({tb - ta:+.0f} us, {100 * (tb - ta) / ta:+.1f}%)  ->  {1e6 / ta:.1f} -> {1e6 / tb:.1f} tok/s of GPU time')
    if ma.get('text') is not None and mb.get('text') is not None:
        same = next((i for i, (x, y) in enumerate(zip(ma['text'], mb['text'])) if x != y), min(len(ma['text']), len(mb['text'])))
        print(f'answer text identical for the first {same} characters of {len(ma["text"])} / {len(mb["text"])}')
    rows = []
    z = {'calls': 0, 'us': 0, 'gap': 0}
    for nm in set(ka) | set(kb):
        x, y = ka.get(nm, z), kb.get(nm, z)
        rows.append((nm, x['calls'] / pa, y['calls'] / pb, y['us'] / pb - x['us'] / pa, y['gap'] / pb - x['gap'] / pa))
    print(f"\n{'kernel (per token)':34s} {'calls A->B':>13s} {'d kern us':>10s} {'d gap us':>9s} {'d total':>8s}")
    for nm, ca, cb, du, dg in sorted(rows, key=lambda r: abs(r[3] + r[4]), reverse=True)[:25]:
        print(f'{nm[:34]:34s} {ca:6.1f}->{cb:<6.1f} {du:10.1f} {dg:9.1f} {du + dg:8.1f}')
    print(f"\nsum of the rows: {sum(r[3] + r[4] for r in rows):+.0f} us per token")

if __name__ == '__main__':
    if len(sys.argv) == 2: report(sys.argv[1])
    elif len(sys.argv) == 3: diff(sys.argv[1], sys.argv[2])
    else: print(__doc__)
