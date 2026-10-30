#!/usr/bin/env bash
# rx-tools/bench-run.sh - the body of bench-detached.sh (runs under systemd-run). Do not call directly.
set -u
# Settings (override in rx-tools/local.env, which git ignores): STRATA_CFG the server's JSON config (the strata-control
# format: exe, args, env, lib_dirs), STRATA_LOG its engine log, STRATA_UNIT the systemd --user unit that runs it,
# STRATA_URL its address, HP the TheRock ROCm install, REF the FP16 reference of lab/quality.py (see docs/RX7900XTX.md),
# STRATA_CORPUS the source tree the prompts are cut from (default: this checkout).
[ -f "$SRC/rx-tools/local.env" ] && . "$SRC/rx-tools/local.env"
CFG=${STRATA_CFG:-$HOME/llm/strata/strata-rx.json}; LOG=${STRATA_LOG:-$HOME/harness/strata-engine.log}
UNIT=${STRATA_UNIT:-strata-rx}; URL=${STRATA_URL:-http://127.0.0.1:8081}; HP=${HP:-$HOME/opt/rocm-10.1.0}
LAB=$SRC/rx-tools/lab; REF=${REF:-$LAB/ref/R_fp16.json}
export STRATA_URL=$URL STRATA_LOG=$LOG
[ -n "${STRATA_CORPUS:-}" ] && export STRATA_CORPUS
cp -p "$CFG" "$OUT/strata-rx.json.prod"
wait_up() { for _ in $(seq 1 180); do curl -s -m3 "$URL/health" | grep -q '"loaded": true' && { sleep 20; return 0; }; sleep 5; done; return 1; }
restore() { cp -p "$OUT/strata-rx.json.prod" "$CFG"; systemctl --user restart "$UNIT"; wait_up; echo "$(date +%T) production restored" >> "$OUT/RESULT.txt"; }
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
        if v == '':                # ARG--spec-split= : a flag without a value
            if flag not in a: a.append(flag)
        elif flag in a: a[a.index(flag) + 1] = v
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
systemctl --user restart "$UNIT"
if ! wait_up; then echo "FAILED: the engine did not start" >> "$OUT/RESULT.txt"; tail -n +"$mark" "$LOG" | tail -40 > "$OUT/engine-start.log"; exit 1; fi
grep -a "engine 0\.\|matrix cores\|fused int8\|file tier reads" <(tail -n +"$mark" "$LOG") | sort -u | head -6 >> "$OUT/RESULT.txt"
if [[ $MODE == prefill || $MODE == all ]]; then
  AB_SIZES=p12k,p32k,p64k AB_REPS=2 python3 "$LAB/prefill_bench.py" prefill "$OUT" > "$OUT/prefill.log" 2>&1
  python3 -c "import json;m=json.load(open('$OUT/prefill.json'))['median'];[print('prefill',k,v['prefill_tok_s'],'tok/s, TTFT',v['ttft_s'],'s') for k,v in m.items()]" >> "$OUT/RESULT.txt" 2>&1
fi
if [[ $MODE == decode || $MODE == all ]]; then
  python3 "$LAB/decode_bench.py" decode "$OUT" 2 > "$OUT/decode.log" 2>&1
  python3 -c "
import json,statistics;r=[x for x in json.load(open('$OUT/decode.json')) if not x['warmup']]
for c in ('c5k','c64k'): print('decode',c,statistics.median([x['decode_tok_s'] for x in r if x['ctx']==c]),'tok/s')" >> "$OUT/RESULT.txt" 2>&1
fi
if [[ $MODE == quality || $MODE == all ]]; then
  python3 "$LAB/quality.py" quality "$OUT" > "$OUT/quality.log" 2>&1
  if [ -f "$REF" ]; then python3 "$LAB/compare.py" "$REF" ${REF_BASE:+"$REF_BASE"} "$OUT/quality.json" >> "$OUT/RESULT.txt" 2>&1
  else echo "no FP16 reference at $REF: this run's quality.json can become it (run it with STRATA_PREFILL_MMQ=0)" >> "$OUT/RESULT.txt"; fi
fi
tail -n +"$mark" "$LOG" | grep -a "strata prefill timing\|strata decode timing\|prompt .* read in\|no progress\|error\|file tier I/O this request\|resident RAM:" > "$OUT/engine.log"
grep -o "the OS read [0-9.]* MB from storage" "$OUT/engine.log" | awk '{s+=$4; n++} END {if (n) printf "drive reads: %.1f GB in %d requests\n", s/1000, n}' >> "$OUT/RESULT.txt"
echo "$(date +%T) done" >> "$OUT/RESULT.txt"
