#!/usr/bin/env python3
"""stages.py - per generated token: every kernel (calls, kernel us, gap us before it) and the pipeline stages they
belong to, for one traced request (RUN/pN). The gap before a kernel is idle GPU time; a gap > 20 us after the MTP drafter or a
host copy, or before the next window's first kernel, is the host round trip between windows and gets its own stage. Results are cached in pN/stages.json.

  stages.py RUN/pN      print the stage table
"""
import collections, json, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from pipeline_map import load, short

# order = order on the pipeline diagram (one decode window: start, 48 layers, head, commit, drafter, host)
STAGES = [
    ('start', 'Start okna (host → GPU)', r'^copy_i32_from_mapped|^embed|copy_indexed|copy_from_mapped_multi|^stage'),
    ('hc', 'HC (hyper-connections)', r'^gr_|^k_down|^k_up|copy_row_to_first'),
    ('qsa', 'Uwaga QSA', r'attn|^append|rope|kv_|qsa|block_scores'),
    ('gdn', 'GDN rekurencja', r'^gdn_(?!step_commit)|conv_residual'),
    ('router', 'Router + plan ekspertów', r'^route|plan|resolve_kernel|group_resident|history_advance'),
    ('dense', 'Macierze gęste (projekcje, shared, głowa)', r'mmvq|mmvf|quantize_q8_1'),
    ('gpuexp', 'Eksperty na GPU (cache)', r'native_gu|native_down|gu_grouped|down_grouped|^gate|fetch_blobs|swiglu_q8_1_entries|rebase_ptrs|add_hits|combine|sigmoid_scale|native_swiglu'),
    ('cpuexp', 'Czekanie na eksperty z CPU', r'wait_copy_i32|wait_flag_ge|copy_rows_from_mapped|doorbell_publish'),
    ('sampler', 'Sampler + logity', r'sampler|logits|argmax|topk|row_top_prob'),
    ('commit', 'Commit okna', r'step_commit'),
    ('mtp', 'Drafter MTP (kernele)', r'^mtp_|head_mix|force_token'),
    ('host', 'Host między oknami (GPU stoi)', None),
    ('copy', 'Kopie hosta (hipMemcpy)', r'rocclr'),
    ('small', 'Normy i drobne', r'norm|apply|scale|add|mul|copy|silu|swiglu|sigmoid'),
    ('other', 'Inne', r''),
]
LABEL = {k: l for k, l, _ in STAGES}
N_CU = 96                                                     # RX 7900 XTX compute units

def stage_of(name):
    for k, _, rx in STAGES:
        if rx is not None and re.search(rx, name): return k
    return 'other'

DT = re.compile(r'strata decode timing: (\d+) windows, avg T ([\d.]+), ([\d.]+) tokens/window, ([\d.]+) ms/window = '
                r'adapt wait ([\d.]+) \+ verify ([\d.]+) \(GPU-reach wait ([\d.]+) \+ per-layer host ([\d.]+) '
                r'\[plan ([\d.]+) actq ([\d.]+) jobs ([\d.]+) CPU ([\d.]+)\] \+ stage ([\d.]+)\) \+ commit/emit ([\d.]+) \+ '
                r'draft ([\d.]+) \+ adapt join ([\d.]+) \+ other ([\d.]+); per layer-window: CPU experts ([\d.]+) '
                r'\(([\d.]+) entries\), VRAM hits ([\d.]+), PCIe ([\d.]+)')

def host_timeline(sub):
    """The engine's own host-side decode timing (STRATA_DECODE_TIMING) for this request, in us per token: what the
    host thread spends each window on. Line order in RUN/strata.log: warm-up, p1, p2, p3."""
    log = pathlib.Path(sub).parent / 'strata.log'
    if not log.exists(): return None
    lines = [m for m in map(DT.search, log.read_text(errors='ignore').splitlines()) if m]
    idx = int(pathlib.Path(sub).name[1:]) - 4          # p1 -> the third line from the end
    if len(lines) < 3 or -idx > len(lines): return None
    g = [float(x) for x in lines[idx].groups()]
    tw = g[2]; k = 1000.0 / tw                        # ms per window -> us per token
    return {'windows': g[0], 'avg_T': g[1], 'tok_win': tw, 'ms_window': g[3], 'us_tok': g[3] * k,
            'parts': {'adapt_wait': g[4] * k, 'gpu_reach_wait': g[6] * k, 'cpu_pool': g[11] * k,
                      'plan_jobs': max(0.0, g[7] - g[11]) * k, 'stage': g[12] * k, 'commit_emit': g[13] * k,
                      'draft': g[14] * k, 'adapt_join': g[15] * k, 'other': g[16] * k,
                      'verify_rest': max(0.0, (g[5] - g[6] - g[7] - g[12]) * k)},
            'per_layer': {'cpu_experts': g[17], 'cpu_entries': g[18], 'vram_hits': g[19], 'pcie': g[20]}}

def balance(wins, tpw):
    """Per MoE layer, from the GPU trace alone: the layer's FFN half is cut at doorbell_publish (the plan request goes
    to the host); then GPU works on the shared expert, waits for the host's expert PLAN (wait_copy_i32), runs the VRAM
    experts, waits for the CPU pool's ROWS (wait_flag_ge), runs the PCIe experts, reads the CPU rows over PCIe, combines.
    cpu_budget = time the CPU pool had (doorbell end -> rows-wait end). Returns per token totals and per layer means."""
    keys = ('shared', 'plan_wait', 'vram', 'rows_wait', 'pcie', 'rows_read', 'combine', 'budget', 'gaps')
    per_layer = collections.defaultdict(lambda: collections.defaultdict(float)); n_win = 0; tot = collections.defaultdict(float)
    kind_of = {}
    for w in wins:
        names = [short(r[0]) for r in w]
        bells = [i for i, n in enumerate(names) if n.startswith('doorbell_publish')]
        if not bells: continue
        n_win += 1
        prev_end = 0
        for L, i in enumerate(bells):
            j_end = next((j for j in range(i + 1, len(w)) if names[j].startswith('combine')), None)
            if j_end is None: break
            seg = range(i + 1, j_end + 1)
            mix = names[prev_end:i]; kind_of[L] = 'QSA' if any('attn' in x for x in mix) else 'GDN'
            prev_end = j_end + 1
            jw = next((j for j in seg if names[j].startswith('wait_copy_i32')), None)
            jf = next((j for j in seg if names[j].startswith('wait_flag_ge')), None)
            d = lambda j: (w[j][2] - w[j][1]) / 1e3
            acc = per_layer[L]
            for j in seg:
                nm = names[j]; dur = d(j)
                gap = max(0.0, (w[j][1] - w[j - 1][2]) / 1e3)
                acc['gaps'] += gap
                if nm.startswith('wait_copy_i32'): acc['plan_wait'] += dur
                elif nm.startswith('wait_flag_ge'): acc['rows_wait'] += dur
                elif nm.startswith('copy_rows_from_mapped'): acc['rows_read'] += dur
                elif re.match(r'fetch_blobs|native_gu_multi|native_down_multi|swiglu_q8_1_entries|rebase_ptrs', nm): acc['pcie'] += dur
                elif re.match(r'native_gu_fused|native_down_lds|gu_grouped|down_grouped', nm): acc['vram'] += dur
                elif re.match(r'add_hits|combine', nm): acc['combine'] += dur
                elif jw is None or j < jw: acc['shared'] += dur
                else: acc['vram'] += dur
            if jf is not None: acc['budget'] += (w[jf][2] - w[i][2]) / 1e3
    if not n_win: return None
    layers = []
    for L in sorted(per_layer):
        a = per_layer[L]; layers.append({'layer': L, 'kind': kind_of.get(L, '?'), **{k: round(a[k] / n_win, 2) for k in keys}})
        for k in keys: tot[k] += a[k]
    f = 1.0 / (n_win * tpw)
    return {'per_token': {k: round(tot[k] * f, 1) for k in keys}, 'layers': layers, 'windows': n_win}

def critical(wins, tpw, host):
    """Critical path of the decode windows: three lanes (GPU measured; host and CPU pool inferred from the GPU's
    meeting points) and how much of the GPU's idle time could be hidden.
    GPU idle while waiting for the HOST: the gap between windows (host builds the next window) and the plan waits
    (wait_copy_i32: the host has not published the layer's expert plan). GPU idle while waiting for the CPU POOL:
    wait_flag_ge (rows). GPU idle between two kernels with nobody to wait for: launch gaps (only fusion/graphs help).
    Hideable by moving work earlier (no new dependency): the plan waits beyond a ~5 us reaction floor, rows waits beyond
    a ~2 us floor, because the host and the pool are idle long enough earlier in the same window (host idle =
    GPU-reach wait). Hideable only by overlapping windows (speculative start of window K+1): the host gap."""
    F_PLAN, F_ROWS = 5.0, 2.0
    acc = collections.defaultdict(float); lens = []
    for w in wins:
        lens.append(w[-1][2] - w[0][1])
        prev = None
        for r in w:
            nm = short(r[0]); d = (r[2] - r[1]) / 1e3
            gap = max(0.0, (r[1] - prev[2]) / 1e3) if prev is not None else 0.0
            pn = short(prev[0]) if prev is not None else ''
            between = gap > 20 and (pn.startswith('mtp_') or 'rocclr' in pn or stage_of(nm) == 'start')
            if between: acc['host_gap'] += gap
            else: acc['launch'] += gap
            if nm.startswith('wait_copy_i32'): acc['plan'] += d; acc['plan_hide'] += max(0.0, d - F_PLAN)
            elif nm.startswith('wait_flag_ge'): acc['rows'] += d; acc['rows_hide'] += max(0.0, d - F_ROWS)
            elif nm.startswith('copy_rows_from_mapped'): acc['rows_read'] += d; acc['rows_read_hide'] += max(0.0, d - 8.0)
            if prev is None or r[2] > prev[2]: prev = r
    n = len(wins); f = 1.0 / (n * tpw)
    out = {k: round(v * f, 1) for k, v in acc.items()}
    out['host_idle'] = round(host['parts']['gpu_reach_wait'], 1) if host else None
    out['pool_busy'] = round(host['parts']['cpu_pool'], 1) if host else None
    out['hide_shift'] = round(out.get('plan_hide', 0) + out.get('rows_hide', 0) + out.get('rows_read_hide', 0), 1)
    out['hide_overlap'] = out.get('host_gap', 0)
    # one representative window (median length) for the drawing: GPU kernels + idle, host and pool lanes inferred
    order = sorted(range(n), key=lambda i: lens[i]); w = wins[order[n // 2]]; t0 = w[0][1]
    gpu, hostl, pool = [], [], []
    names = [short(r[0]) for r in w]
    for i, r in enumerate(w):
        gpu.append([round((r[1] - t0) / 1e3, 1), round((r[2] - r[1]) / 1e3, 2), stage_of(names[i]),
                    'wait_plan' if names[i].startswith('wait_copy_i32') else 'wait_rows' if names[i].startswith('wait_flag_ge') else ''])
    bells = [i for i, nm in enumerate(names) if nm.startswith('doorbell_publish')]
    for i in bells:
        jw = next((j for j in range(i + 1, min(len(w), i + 40)) if names[j].startswith('wait_copy_i32')), None)
        jr = next((j for j in range(i + 1, min(len(w), i + 60)) if names[j].startswith('copy_rows_from_mapped')), None)
        if jw is None: continue
        hostl.append([round((w[i][2] - t0) / 1e3, 1), round((w[jw][2] - w[i][2]) / 1e3, 1), 'plan'])
        if jr is not None: pool.append([round((w[jw][2] - t0) / 1e3, 1), round((w[jr][2] - w[jw][2]) / 1e3, 1), 'rows'])
    prev = None
    for i, r in enumerate(w):
        if prev is not None and (r[1] - prev[2]) / 1e3 > 20:
            hostl.append([round((prev[2] - t0) / 1e3, 1), round((r[1] - prev[2]) / 1e3, 1), 'window'])
        if prev is None or r[2] > prev[2]: prev = r
    out['window'] = {'len_us': round((w[-1][2] - t0) / 1e3, 1), 'gpu': gpu, 'host': hostl, 'pool': pool}
    return out

def compute(sub):
    sub = pathlib.Path(sub); cache = sub / 'stages.json'
    if cache.exists():
        c = json.loads(cache.read_text())
        if 'critical' in c: return c                         # older caches lack the newer views
    wins, meta, _ = load(sub); tpw = meta['tok_per_win']; n = len(wins)
    kern = collections.defaultdict(lambda: [0.0, 0.0, 0.0]); st = collections.defaultdict(lambda: [0.0, 0.0]); wall = 0.0
    gapn = [0]; fill = [0.0, 0.0]; low = collections.defaultdict(float)
    for w in wins:
        wall += (w[-1][2] - w[0][1]) / 1e3; prev = None
        for r in w:
            nm = short(r[0]); s = stage_of(nm); d = (r[2] - r[1]) / 1e3
            kern[nm][0] += 1; kern[nm][1] += d; st[s][0] += d
            if not re.match(r'wait_copy_i32|wait_flag_ge', nm):          # CU fill of the kernels that do work
                nwg = (r[4] or 0) / max(1, r[5] or 1)
                fill[0] += d * min(1.0, nwg / N_CU); fill[1] += d
                if nwg < N_CU / 4: low[nm] += d
            if prev is not None and r[1] > prev[2]:
                gap = (r[1] - prev[2]) / 1e3; kern[nm][2] += gap
                pn = short(prev[0])
                between = gap > 20 and (pn.startswith('mtp_') or 'rocclr' in pn or s == 'start')
                st['host' if between else s][1] += gap
                if not between: gapn[0] += 1
            if prev is None or r[2] > prev[2]: prev = r
    f = 1.0 / (n * tpw)
    # GPU time per token split by what the GPU is doing: computing, spinning on a flag the CPU pool raises, copying the
    # CPU rows over PCIe, idle while the host builds the next window, idle between two kernels of the same window
    spin = sum(v[1] for k, v in kern.items() if re.match(r'wait_copy_i32|wait_flag_ge', k))
    rows = sum(v[1] for k, v in kern.items() if k.startswith('copy_rows_from_mapped'))
    busy = sum(v[1] for v in kern.values())
    host_gap = st['host'][1] if 'host' in st else 0.0
    gaps = sum(v[1] for v in st.values())
    ngap = gapn[0]
    gpu = {'work': (busy - spin - rows) * f, 'spin_cpu': spin * f, 'pcie_rows': rows * f, 'host_gap': host_gap * f,
           'launch_gap': (gaps - host_gap) * f, 'n_gaps': ngap * f, 'avg_gap_us': (gaps - host_gap) / max(ngap, 1)}
    host = host_timeline(sub); cpu = None
    if (sub / 'cpu.json').exists():
        try: cpu = json.loads((sub / 'cpu.json').read_text())
        except Exception: cpu = None
    util = {'gpu_work': 100 * gpu['work'] / (wall * f) if wall else None,
            'gpu_fill': 100 * fill[0] / fill[1] if fill[1] else None,
            'gpu_low_fill_us': {k: round(v * f, 1) for k, v in sorted(low.items(), key=lambda kv: -kv[1])[:12]}}
    if host:
        util['host_busy'] = 100 * (1 - host['parts']['gpu_reach_wait'] / host['us_tok'])
        util['cpu_pool'] = 100 * host['parts']['cpu_pool'] / host['us_tok']
    if cpu:
        util['cores'] = cpu['cores']; util['threads'] = cpu['threads'][:16]
    parts = [util[k] for k in ('gpu_work', 'host_busy', 'cpu_pool') if util.get(k) is not None]
    util['balance'] = sum(parts) / len(parts) if parts else None
    try: crit = critical(wins, tpw, host)
    except Exception as ex: crit = {'error': str(ex)}
    out = {'critical': crit, 'util': util, 'gpu': gpu, 'host': host, 'balance': balance(wins, tpw),'us_tok': wall * f, 'tok_win': tpw, 'windows': n, 'kernels_tok': sum(v[0] for v in kern.values()) * f,
           'gap_tok': sum(v[1] for v in st.values()) * f,
           'stages': {k: {'kern': st[k][0] * f, 'gap': st[k][1] * f} for k, _, _ in STAGES if k in st},
           'kernels': {k: {'calls': v[0] * f, 'us': v[1] * f, 'gap': v[2] * f, 'stage': stage_of(k)} for k, v in kern.items()}}
    cache.write_text(json.dumps(out))
    return out

if __name__ == '__main__':
    o = compute(sys.argv[1])
    print('GPU:', {k: round(v, 1) for k, v in o['gpu'].items()})
    print('host:', o['host'] and {k: round(v) for k, v in o['host']['parts'].items()}, o['host'] and o['host']['per_layer'])
    print(f"{o['us_tok']:.0f} us/token, {o['tok_win']:.2f} tokens/window, {o['kernels_tok']:.0f} kernels/token")
    for k, _, _ in STAGES:
        if k in o['stages']:
            s = o['stages'][k]; print(f"{LABEL[k]:44s} {s['kern']:7.0f} {s['gap']:7.0f} {s['kern'] + s['gap']:7.0f} {100 * (s['kern'] + s['gap']) / o['us_tok']:5.1f}%")
