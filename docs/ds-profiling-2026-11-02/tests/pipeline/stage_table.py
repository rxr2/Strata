#!/usr/bin/env python3
"""stage_table.py RUN - per generated token: time per stage (kernels + the gap before each kernel), largest gaps by
the kernel they precede and the kernel before them."""
import collections, re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from pipeline_map import load, short
STAGES = [
  ('czekanie na eksperty z CPU', r'wait_copy_i32|wait_flag_ge|copy_rows_from_mapped|copy_i32_from_mapped|doorbell_publish'),
  ('eksperty na GPU (cache)', r'native_gu|native_down|fetch_blobs|swiglu_q8_1_entries|rebase_ptrs|add_hits|combine|sigmoid_scale|native_swiglu'),
  ('macierze gęste (proj. attn/GDN/shared, lm_head)', r'mmvq|mmvf|quantize_q8_1'),
  ('HC (hyper-connections)', r'^gr_|k_down|k_up'),
  ('uwaga (QSA)', r'attn|append|rope|kv_'),
  ('GDN rekurencja', r'gdn_'),
  ('router', r'^route'),
  ('normy i drobne', r'norm|apply|scale|add|mul|copy|sampler'),
  ('kopie hosta (hipMemcpy)', r'rocclr'),
]
def stage(n):
    for s, rx in STAGES:
        if re.search(rx, n): return s
    return 'inne'
wins, meta, name = load(sys.argv[1]); tpw = meta['tok_per_win']; n = len(wins)
k = collections.defaultdict(float); g = collections.defaultdict(float); gp = collections.Counter(); wall = 0
for w in wins:
    wall += (w[-1][2] - w[0][1]) / 1e3; prev = None
    for r in w:
        nm = short(r[0]); s = stage(nm); k[s] += (r[2] - r[1]) / 1e3
        if prev is not None and r[1] > prev[2]:
            gap = (r[1] - prev[2]) / 1e3; g[s] += gap
            if gap > 20: gp[(short(prev[0]), nm)] += gap
        prev = r if prev is None or r[2] > prev[2] else prev
f = 1 / (n * tpw); T = wall * f
print(f'== {sys.argv[1].split("/")[-2]}/{name}: {T:.0f} us per token ({1e6 / T:.1f} tok/s of GPU time), {tpw:.2f} tokens per window')
print(f"{'etap':48s} {'kernele':>8s} {'przerwy':>8s} {'razem':>8s} {'udział':>7s}")
for s in sorted(set(k) | set(g), key=lambda s: -(k[s] + g[s])):
    print(f'{s:48s} {k[s] * f:8.0f} {g[s] * f:8.0f} {(k[s] + g[s]) * f:8.0f} {100 * (k[s] + g[s]) * f / T:6.1f}%')
print('\nprzerwy > 20 us (przed kernelem B, po kernelu A), us na token:')
for (a, b), v in gp.most_common(8): print(f'  {v * f:7.0f}  {a} -> {b}')
