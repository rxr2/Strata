#!/bin/bash
# trace_run.sh NAME [KEY=VALUE ...] - a deterministic decode of the production config under rocprofv3 --kernel-trace.
#   EXE=<path>  engine binary (default: the fork's build-rx/strata; EXE=prod keeps the production binary)
#   NOPROF=1  run without rocprofv3: only the server's tok/s of the 3 prompts (no trace.db)
#   ARG--flag=VALUE  replace (or add) an engine argument (e.g. ARG--spec=8)
#   any other KEY=VALUE  an extra engine environment variable (e.g. STRATA_FUSE_WAIT=1)
# Workload: one fixed prompt, greedy (temperature 0), 320 tokens, reasoning off - the same token stream every run
# unless the numerics change. Production strata-rx is stopped for the run and always restarted afterwards.
# Output: ~/rx-perf-lab/pipeline/<time>-NAME/{trace.db, run.json, engine.log}
set -u
NAME=${1:?NAME}; shift
OUT=$HOME/rx-perf-lab/pipeline/$(date +%Y%m%d-%H%M%S)-$NAME; mkdir -p "$OUT"
CFG=$HOME/llm/strata/strata-rx.json; HP=$HOME/opt/rocm-10.1.0; FORK=$HOME/Projekty/strata-rx7900
printf '%s\n' "$@" > "$OUT/args.txt"
PROF=1; for a in "$@"; do [ "$a" = NOPROF=1 ] && PROF=0; done   # NOPROF=1: no profiler, only the tok/s of the 3 prompts
python3 - "$CFG" "$OUT/cfg.json" "$FORK" "$HP" "$@" <<'PY'
import json, sys
src, dst, fork, hp, *kv = sys.argv[1:]
c = json.load(open(src)); exe = f'{fork}/build-rx/strata'
for x in kv:
    k, v = x.split('=', 1)
    if k == 'NOPROF': continue
    if k == 'EXE': exe = v
    elif k.startswith('ARG--'):            # ARG--flag=VALUE: replace (or add) an engine argument
        flag = k[3:]; a = c['args']
        if flag in a: a[a.index(flag) + 1] = v
        else: a += [flag, v]
    else: c['env'][k] = v
if exe != 'prod':
    c['exe'] = exe; c['lib_dirs'] = [f'{hp}/lib', f'{hp}/lib/rocm_sysdeps/lib']
c['env']['STRATA_DECODE_TIMING'] = '1'
c['log'] = dst.rsplit('/', 1)[0] + '/strata.log'      # this run's own engine log (decode timing lines per request)
json.dump(c, open(dst, 'w'), indent=2)
PY
restore() { systemctl --user start strata-rx; for i in $(seq 1 90); do curl -sf -m3 http://127.0.0.1:8081/v1/models >/dev/null && break; sleep 5; done; echo "$(date +%T) production restored" >> "$OUT/run.log"; }
trap restore EXIT
systemctl --user stop strata-rx
for i in $(seq 1 60); do ss -ltn 2>/dev/null | grep -q ':8081 ' || break; sleep 2; done
if ss -ltn 2>/dev/null | grep -q ':8081 '; then echo "port 8081 still in use, abort" >> "$OUT/run.log"; exit 1; fi
cd /tmp
WRAP=(); [ $PROF = 1 ] && WRAP=("$HP/bin/rocprofv3" --kernel-trace -d "$OUT/prof" -o trace --)
LD_LIBRARY_PATH=$HOME/llm/strata setsid "${WRAP[@]}" \
  $HOME/llm/strata-control-0.1.53/bin/strata serve --engine strata --config "$OUT/cfg.json" --host 127.0.0.1 --port 8081 \
  > "$OUT/engine.log" 2>&1 < /dev/null &
for i in $(seq 1 120); do curl -sf -m3 http://127.0.0.1:8081/v1/models >/dev/null && break; sleep 5; done
sleep 10
pgrep -f "config $OUT/cfg.json" >/dev/null || { echo 'traced server did not start' >> "$OUT/run.log"; exit 1; }
# Three fixed prompts (prose+numbers, code, Polish prose); each one is cut into its own sub-run OUT/pN (run.json + a link
# to the shared trace.db), so pipeline_map.py OUT/p2 maps only that request.
python3 - "$OUT" <<'PY2'
import json, os, sys, time, urllib.request
out = sys.argv[1]
prompts = [
  'Explain step by step how a ring all-reduce works across 6 GPUs. Give a worked example with numbers for 6 ranks and 12 chunks, then C++ pseudocode with comments.',
  'Write a complete Python module implementing an LRU cache with TTL expiry, thread safety and type hints, plus pytest unit tests covering eviction order, expiry and concurrent access.',
  'Napisz po polsku wyczerpujacy poradnik, jak zaplanowac tygodniowa wyprawe rowerowa po Mazurach: trasa dzien po dniu, sprzet, budzet, noclegi i bezpieczenstwo.',
]
def req(prompt, n):
    body = {'model': 'x', 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': n, 'temperature': 0,
            'reasoning_effort': 'none', 'seed': 7}
    r = urllib.request.Request('http://127.0.0.1:8081/v1/chat/completions', json.dumps(body).encode(), {'Content-Type': 'application/json'})
    t0 = time.monotonic_ns(); d = json.load(urllib.request.urlopen(r, timeout=900)); t1 = time.monotonic_ns()
    return {'t0_ns': t0, 't1_ns': t1, 'usage': d.get('usage'), 'timings': d.get('timings'),
            'text': d['choices'][0]['message'].get('content', '')}
import glob, threading
def engine_pid():
    exe = json.load(open(f'{out}/cfg.json'))['exe']
    for d in glob.glob('/proc/[0-9]*'):
        try:
            a = open(d + '/cmdline', 'rb').read().split(b'\0')
            if a and a[0].decode() == exe and b'--serve' in a: return int(d[6:])
        except Exception: pass
class CpuSampler(threading.Thread):
    # every 100 ms: busy time of every logical CPU (/proc/stat) and of every engine thread (/proc/PID/task/*/stat,
    # with the CPU it last ran on), so the load per core and per thread can be compared
    def __init__(self, pid):
        super().__init__(daemon=True); self.pid = pid; self.stop = threading.Event(); self.samples = []
    def snap(self):
        cpus = {}
        for l in open('/proc/stat'):
            if l.startswith('cpu') and l[3].isdigit():
                f = l.split(); v = list(map(int, f[1:9])); cpus[f[0][3:]] = (sum(v) - v[3] - v[4], sum(v))
        th = {}
        for t in glob.glob(f'/proc/{self.pid}/task/*'):
            try:
                st = open(t + '/stat').read(); comm = st[st.index('(') + 1:st.rindex(')')]; f = st[st.rindex(')') + 2:].split()
                th[t.rsplit('/', 1)[1]] = (comm, int(f[11]) + int(f[12]), int(f[36]))
            except Exception: pass
        return time.monotonic_ns(), cpus, th
    def run(self):
        while not self.stop.is_set():
            self.samples.append(self.snap()); time.sleep(0.1)
def cpu_summary(samples, t0, t1):
    s = [x for x in samples if t0 <= x[0] <= t1]
    if len(s) < 2: return None
    a, b = s[0], s[-1]; hz = os.sysconf('SC_CLK_TCK'); wall = (b[0] - a[0]) / 1e9
    cores = {c: round(100 * (b[1][c][0] - a[1][c][0]) / max(1, b[1][c][1] - a[1][c][1]), 1) for c in b[1] if c in a[1]}
    threads = []
    for tid, (comm, ticks, cpu) in b[2].items():
        if tid not in a[2]: continue
        busy = 100 * (ticks - a[2][tid][1]) / hz / wall
        where = {}
        for x in s:
            if tid in x[2]: where[x[2][tid][2]] = where.get(x[2][tid][2], 0) + 1
        if busy >= 1: threads.append({'tid': tid, 'name': comm, 'cpu_pct': round(busy, 1), 'cores': {str(k): v for k, v in sorted(where.items(), key=lambda kv: -kv[1])[:3]}})
    threads.sort(key=lambda x: -x['cpu_pct'])
    return {'wall_s': round(wall, 2), 'cores': cores, 'threads': threads[:40]}
req(prompts[0], 16)                       # warm-up (kernels compiled, caches primed)
smp = None
try:
    pid = engine_pid()
    if pid: smp = CpuSampler(pid); smp.start()
except Exception: smp = None
for i, p in enumerate(prompts, 1):
    r = req(p, 320); os.makedirs(f'{out}/p{i}', exist_ok=True)
    if smp:
        try:
            cs = cpu_summary(smp.samples, r['t0_ns'], r['t1_ns'])
            if cs: json.dump(cs, open(f'{out}/p{i}/cpu.json', 'w'), indent=1)
        except Exception as ex: print('cpu sampler:', ex)
    json.dump(r, open(f'{out}/p{i}/run.json', 'w'), indent=1)
    if i == 1: json.dump(r, open(f'{out}/run.json', 'w'), indent=1)
    os.symlink('../trace.db', f'{out}/p{i}/trace.db')
    print(f'p{i} tokens', r['usage']['completion_tokens'], 'tok/s', (r['timings'] or {}).get('predicted_per_second'))
PY2
# stop order matters: the engine (not the wrapper) holds the kernel trace and writes it only on its own clean exit.
# Pause the wrapper so it cannot kill or restart the engine, stop the engine, wait for the trace, then end the wrapper.
CP=$(pgrep -f "config $OUT/cfg.json" | head -1)
EXE=$(python3 -c "import json;print(json.load(open('$OUT/cfg.json'))['exe'])")
EP=$(pgrep -P "$CP" -f "^$EXE --serve" | head -1); [ -z "$EP" ] && EP=$(pgrep -f "^$EXE --serve" | head -1)
echo "$(date +%T) wrapper $CP engine $EP" >> "$OUT/run.log"
[ -n "$CP" ] && kill -STOP "$CP"
if [ -n "$EP" ]; then
  kill -TERM "$EP"          # the engine ignores INT; TERM ends it and rocprofv3 writes the trace
  for i in $(seq 1 45); do kill -0 "$EP" 2>/dev/null || break; sleep 2; done
  kill -0 "$EP" 2>/dev/null && { echo "engine still alive after TERM, KILL (trace may be lost)" >> "$OUT/run.log"; kill -KILL "$EP"; sleep 3; }
fi
[ -n "$CP" ] && { kill -CONT "$CP"; kill -INT "$CP"; sleep 3; kill -0 "$CP" 2>/dev/null && kill -TERM "$CP"; }
for i in $(seq 1 30); do find "$OUT/prof" -name '*.db' 2>/dev/null | grep -q . && break; sleep 2; done
mv "$(find "$OUT/prof" -name '*.db' | head -1)" "$OUT/trace.db" 2>/dev/null
echo "$(date +%T) trace: $(du -h "$OUT/trace.db" 2>/dev/null | cut -f1)" >> "$OUT/run.log"
echo "$OUT"
