#!/bin/bash
# suite_run.sh NAME [KEY=VALUE ...] - run a fixed prompt suite (classes) through the engine and keep per-request JSON.
#   LIVE=1        use the already running production server (do not stop/start anything)
#   EXE=<path>    engine binary for a temporary server (default: production config's exe)
#   ARG--flag=V   replace/add an engine argument (temporary server only)
#   any KEY=VALUE extra engine environment variable (temporary server only)
# Output: ~/rx-perf-lab/suite/<time>-NAME/{requests.jsonl,engine.log,run.json}
set -u
NAME=${1:?NAME}; shift
OUT=$HOME/rx-perf-lab/suite/$(date +%Y%m%d-%H%M%S)-$NAME; mkdir -p "$OUT"
printf '%s\n' "$@" > "$OUT/args.txt"
CFG=$HOME/llm/strata/strata-rx.json; HP=$HOME/opt/rocm-10.1.0
PROMPTS=$HOME/Projekty/coding-bench/pipeline/suite_prompts.json
LIVE=0; for a in "$@"; do [ "$a" = LIVE=1 ] && LIVE=1; done

if [ $LIVE = 0 ]; then
python3 - "$CFG" "$OUT/cfg.json" "$HP" "$@" <<'PY'
import json, sys
src, dst, hp, *kv = sys.argv[1:]
c = json.load(open(src)); exe = c['exe']
for x in kv:
    k, v = x.split('=', 1)
    if k == 'LIVE': continue
    if k == 'EXE': exe = v
    elif k.startswith('ARG--'):
        flag = k[3:]; a = c['args']
        if flag in a: a[a.index(flag) + 1] = v
        else: a += [flag, v]
    else: c['env'][k] = v
if exe != 'prod' and exe != c.get('exe'):
    c['exe'] = exe; c['lib_dirs'] = [f'{hp}/lib', f'{hp}/lib/rocm_sysdeps/lib']
c['env']['STRATA_DECODE_TIMING'] = '1'
c['log'] = dst.rsplit('/', 1)[0] + '/strata.log'
json.dump(c, open(dst, 'w'), indent=2)
PY
restore() { systemctl --user start strata-rx; for i in $(seq 1 90); do curl -sf -m3 http://127.0.0.1:8081/v1/models >/dev/null && break; sleep 5; done; echo "$(date +%T) production restored" >> "$OUT/run.log"; }
trap restore EXIT
systemctl --user stop strata-rx
for i in $(seq 1 60); do ss -ltn 2>/dev/null | grep -q ':8081 ' || break; sleep 2; done
if ss -ltn 2>/dev/null | grep -q ':8081 '; then echo "port 8081 still in use" >> "$OUT/run.log"; exit 1; fi
cd /tmp
LD_LIBRARY_PATH=$HOME/llm/strata setsid \
  $HOME/llm/strata-control-0.1.53/bin/strata serve --engine strata --config "$OUT/cfg.json" --host 127.0.0.1 --port 8081 \
  > "$OUT/engine.log" 2>&1 < /dev/null &
for i in $(seq 1 120); do curl -sf -m3 http://127.0.0.1:8081/v1/models >/dev/null && break; sleep 5; done
sleep 5
LOG=$OUT/strata.log
else
  LOG=$HOME/harness/strata-engine.log
  [ -f $HOME/Projekty/strata-rx7900/rx-tools/local.env ] && . $HOME/Projekty/strata-rx7900/rx-tools/local.env
  LOG=${STRATA_LOG:-$LOG}
fi
START=$(wc -l < "$LOG" 2>/dev/null || echo 0)
if [ "${MATRIX:-0}" = 1 ]; then
  STRATA_LOG="$LOG" python3 "${MATRIX_SCRIPT:-/tmp/opencode/live_matrix.py}" "$OUT" "${REPS:-3}"
else
python3 - "$OUT" "$PROMPTS" <<'PY'
import json, os, sys, time, urllib.request
out, pf = sys.argv[1], sys.argv[2]
prompts = json.load(open(pf))
def req(prompt, n):
    body = {'model': 'x', 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': n, 'temperature': 0,
            'reasoning_effort': 'none', 'seed': 7}
    r = urllib.request.Request('http://127.0.0.1:8081/v1/chat/completions', json.dumps(body).encode(),
                               {'Content-Type': 'application/json'})
    t0 = time.monotonic_ns(); d = json.load(urllib.request.urlopen(r, timeout=900)); t1 = time.monotonic_ns()
    return {'t0_ns': t0, 't1_ns': t1, 'usage': d.get('usage'), 'timings': d.get('timings'),
            'text': d['choices'][0]['message'].get('content', '')}
req(prompts[0]['prompt'], 16)   # warm-up
with open(f'{out}/requests.jsonl', 'w') as f:
    for i, p in enumerate(prompts):
        r = req(p['prompt'], p.get('max_tokens', 192)); r['name'] = p['name']; r['i'] = i
        f.write(json.dumps(r) + '\n'); f.flush()
        print(i, p['name'], (r['timings'] or {}).get('predicted_per_second'), flush=True)
    fs = os.environ.get('FINAL_SLEEP')
    if fs:
        time.sleep(float(fs))
        r = req('Reply with OK.', 1); r['name'] = 'save_flush'; r['i'] = len(prompts)
        f.write(json.dumps(r) + '\n'); f.flush()
        print('save_flush', (r['timings'] or {}).get('predicted_per_second'), flush=True)
PY
fi
cp "$LOG" "$OUT/engine-all.log" 2>/dev/null || true
tail -n +$((START + 1)) "$LOG" > "$OUT/engine-tail.log" 2>/dev/null || true
if [ $LIVE = 0 ]; then
  CP=$(pgrep -f "config $OUT/cfg.json" | head -1)
  EXEP=$(python3 -c "import json;print(json.load(open('$OUT/cfg.json'))['exe'])")
  EP=$(pgrep -P "$CP" -f "^$EXEP --serve" | head -1); [ -z "$EP" ] && EP=$(pgrep -f "^$EXEP --serve" | head -1)
  [ -n "$EP" ] && { kill -TERM "$EP"; for i in $(seq 1 45); do kill -0 "$EP" 2>/dev/null || break; sleep 2; done; kill -KILL "$EP" 2>/dev/null; }
  [ -n "$CP" ] && { kill -INT "$CP" 2>/dev/null; sleep 2; kill -KILL "$CP" 2>/dev/null; }
  echo "$OUT"
fi
