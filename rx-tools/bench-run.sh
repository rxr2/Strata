#!/usr/bin/env bash
# rx-tools/bench-run.sh - the body of bench-detached.sh (runs under systemd-run). Do not call directly.
set -u
CFG=$HOME/llm/strata/strata-rx.json; LOG=$HOME/harness/strata-engine.log; HP=$HOME/opt/rocm-10.1.0
LAB=$HOME/rx-perf-lab/experiments
cp -p "$CFG" "$OUT/strata-rx.json.prod"
wait_up() { for _ in $(seq 1 180); do curl -s -m3 127.0.0.1:8081/health | grep -q '"loaded": true' && { sleep 20; return 0; }; sleep 5; done; return 1; }
restore() { cp -p "$OUT/strata-rx.json.prod" "$CFG"; systemctl --user restart strata-rx; wait_up; echo "$(date +%T) production restored" >> "$OUT/RESULT.txt"; }
trap restore EXIT
mapfile -t KV < "$OUT/args.txt"
python3 - "$OUT/strata-rx.json.prod" "$CFG" "$SRC" "$HP" "${KV[@]}" <<'PY'
import json, sys
src, dst, fork, hp, *kv = sys.argv[1:]
c = json.load(open(src)); exe = f'{fork}/build-rx/strata'
for x in kv:
    if not x: continue
    k, v = x.split('=', 1)
    if k == 'EXE': exe = v
    elif k.startswith('ARG--'):   # ARG--prefill=auto:16384: replace (or add) an engine argument
        flag, a = k[3:], c['args']
        if flag in a: a[a.index(flag) + 1] = v
        else: a += [flag, v]
    else: c['env'][k] = v
if exe != 'prod':
    c['exe'] = exe
    c['lib_dirs'] = [f'{hp}/lib', f'{hp}/lib/rocm_sysdeps/lib']
c['env'].update({'STRATA_PREFILL_TIMING': '1', 'STRATA_DECODE_TIMING': '1'})
json.dump(c, open(dst, 'w'), indent=2)
print('exe', c['exe'])
PY
mark=$(wc -l < "$LOG")
echo "$(date +%T) start $MODE $(python3 -c "import json;print(json.load(open('$CFG'))['exe'])")" > "$OUT/RESULT.txt"
systemctl --user restart strata-rx
if ! wait_up; then echo "FAILED: the engine did not start" >> "$OUT/RESULT.txt"; tail -n +"$mark" "$LOG" | tail -40 > "$OUT/engine-start.log"; exit 1; fi
grep -a "engine 0\.\|matrix cores\|fused int8\|file tier reads" <(tail -n +"$mark" "$LOG") | sort -u | head -6 >> "$OUT/RESULT.txt"
if [[ $MODE == prefill || $MODE == all ]]; then
  AB_SIZES=p12k,p32k,p64k AB_REPS=2 python3 "$LAB/P1-prefill/ab_p1b.py" prefill "$OUT" > "$OUT/prefill.log" 2>&1
  python3 -c "import json;m=json.load(open('$OUT/prefill.json'))['median'];[print('prefill',k,v['prefill_tok_s'],'tok/s, TTFT',v['ttft_s'],'s') for k,v in m.items()]" >> "$OUT/RESULT.txt" 2>&1
fi
if [[ $MODE == decode || $MODE == all ]]; then
  python3 "$LAB/P2-decode/decode_bench.py" decode "$OUT" 2 > "$OUT/decode.log" 2>&1
  python3 -c "
import json,statistics;r=[x for x in json.load(open('$OUT/decode.json')) if not x['warmup']]
for c in ('c5k','c64k'): print('decode',c,statistics.median([x['decode_tok_s'] for x in r if x['ctx']==c]),'tok/s')" >> "$OUT/RESULT.txt" 2>&1
fi
if [[ $MODE == quality || $MODE == all ]]; then
  python3 "$LAB/K1K2-fp16ref/quality2.py" quality "$OUT" > "$OUT/quality.log" 2>&1
  python3 "$LAB/K1K2-fp16ref/compare2.py" "$LAB/K1K2-fp16ref/R_fp16.json" "$LAB/K1K2-fp16ref/K_both.json" "$OUT/quality.json" >> "$OUT/RESULT.txt" 2>&1
fi
tail -n +"$mark" "$LOG" | grep -a "strata prefill timing\|strata decode timing\|prompt .* read in\|no progress\|error" > "$OUT/engine.log"
echo "$(date +%T) done" >> "$OUT/RESULT.txt"
