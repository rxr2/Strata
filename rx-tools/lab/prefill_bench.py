"""H1 A/B: Strata RX file tier through the page cache (default) vs O_DIRECT (STRATA_UNBUFFERED_LOAD=1).
Long prompts of real, varied text (Strata's own C++/CUDA sources), a fresh slice and a unique prefix per run, so neither
the conversation cache nor a repeated expert set hides the drive. Per request: prefill tok/s, TTFT, decode tok/s, and the
bytes read from the model drive (nvme1n1 sectors) and by the engine process (/proc/PID/io).

usage: prefill_bench.py VARIANT OUT_DIR       (the server must already run with that variant's config)"""
import json, os, statistics, sys, time, uuid, urllib.request
from pathlib import Path

BASE = os.environ.get('STRATA_URL', 'http://127.0.0.1:8081')
VARIANT, OUT = sys.argv[1], Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)
SIZES = [('p12k', 12_000), ('p32k', 32_000), ('p64k', 64_000), ('p128k', 128_000)]
if os.environ.get('AB_SIZES'): SIZES = [x for x in SIZES if x[0] in os.environ['AB_SIZES'].split(',')]
REPS = int(os.environ.get("AB_REPS", "3"))
CHARS_PER_TOKEN = 3.1         # C++/CUDA with this tokenizer, corrected below from the server's own count

SRC = Path(os.environ.get('STRATA_CORPUS', Path(__file__).resolve().parents[2])) / 'src'
corpus = ''.join(p.read_text(errors='replace') for p in sorted(SRC.rglob('*'))
                 if p.suffix in ('.cpp', '.cu', '.hpp', '.cuh', '.h') and p.is_file())
cursor = 0


def take(n_chars):
    global cursor
    if cursor + n_chars > len(corpus): cursor = 0
    s = corpus[cursor:cursor + n_chars]; cursor += n_chars
    return s


def req(path, body=None, timeout=1800):
    r = urllib.request.Request(BASE + path, data=json.dumps(body).encode() if body is not None else None,
                               headers={'Content-Type': 'application/json'})
    return urllib.request.urlopen(r, timeout=timeout)


def engine_pid():
    for p in Path('/proc').iterdir():
        if p.name.isdigit():
            try:
                cmd = (p / 'cmdline').read_bytes().split(b'\0')
            except OSError:
                continue
            if cmd and cmd[0].endswith(b'llm/strata/strata') and b'--serve' in cmd: return int(p.name)
    return None


def drive_sectors():   # field 3 of /sys/block/nvme1n1/stat: sectors read (512 B)
    return int(Path('/sys/block/' + os.environ.get('STRATA_DRIVE', 'nvme1n1') + '/stat').read_text().split()[2])


def proc_read(pid):
    if not Path(f'/proc/{pid}/io').exists(): return 0
    for line in Path(f'/proc/{pid}/io').read_text().splitlines():
        if line.startswith('read_bytes:'): return int(line.split()[1])
    return 0


def latest():
    with req('/metrics?all=1') as r: m = json.load(r)
    rows = m.get('requests') if isinstance(m.get('requests'), list) else []
    return max(rows, key=lambda row: row.get('time') or 0) if rows else {}


def model_id():
    with req('/v1/models') as r: return json.load(r)['data'][0]['id']


MODEL = model_id()
PID = engine_pid()
ratio = CHARS_PER_TOKEN
results = {'variant': VARIANT, 'pid': PID, 'started': time.strftime('%F %T'), 'runs': []}
for name, tokens in SIZES:
    for i in range(REPS + 1):
        text = (f'[{VARIANT} {name} {i} {uuid.uuid4().hex}]\nPrzeczytaj poniższy kod i w trzech zdaniach powiedz, '
                f'co robi ostatnia funkcja.\n\n' + take(int(tokens * ratio)))
        body = {'model': MODEL, 'messages': [{'role': 'user', 'content': text}], 'max_tokens': 96, 'temperature': 0,
                'stream': True, 'reasoning_effort': 'none'}
        PID = engine_pid() or PID
        s0, b0 = drive_sectors(), proc_read(PID)
        t0 = time.perf_counter(); first = None; failed = None
        try:
            with req('/v1/chat/completions', body) as r:
                for line in r:
                    if not line.startswith(b'data: ') or line.strip() == b'data: [DONE]': continue
                    d = json.loads(line[6:]); ch = (d.get('choices') or [{}])[0].get('delta', {})
                    if (ch.get('content') or ch.get('reasoning_content')) and first is None: first = time.perf_counter() - t0
        except Exception as e:
            failed = repr(e)[:200]
        total = time.perf_counter() - t0
        if failed or engine_pid() != PID:   # the engine stopped (watchdog) and systemd restarts it: record, wait, go on
            row = {'size': name, 'rep': i, 'warmup': i == 0, 'failed': failed or 'engine restarted', 'total_s': round(total, 1),
                   'drive_read_mb': round((drive_sectors() - s0) * 512 / 1e6, 1)}
            results['runs'].append(row); print(json.dumps(row), flush=True)
            for _ in range(120):
                try:
                    with req('/health', timeout=5) as r:
                        if json.load(r).get('loaded'): break
                except Exception: pass
                time.sleep(5)
            time.sleep(20); PID = engine_pid(); continue
        drive_mb = (drive_sectors() - s0) * 512 / 1e6
        proc_mb = (proc_read(PID) - b0) / 1e6
        h = latest()
        pt = h.get('prompt_tokens') or 0; read = h.get('prompt_read') or (pt - (h.get('reused') or 0)); pms = h.get('prompt_ms') or 0
        if pt: ratio = ratio * tokens / pt if i == 0 else ratio   # aim the next sizes at their targets
        row = {'size': name, 'rep': i, 'warmup': i == 0, 'prompt_tokens': pt, 'reused': h.get('reused'), 'read': read,
               'prefill_tok_s': round(read / (pms / 1000), 1) if pms else None, 'ttft_s': round(first or 0, 2),
               'decode_tok_s': h.get('decode_tok_s'), 'total_s': round(total, 1),
               'drive_read_mb': round(drive_mb, 1), 'engine_read_mb': round(proc_mb, 1)}
        results['runs'].append(row)
        print(json.dumps(row), flush=True)
        (OUT / f'{VARIANT}.json').write_text(json.dumps(results, indent=1))

summary = {}
for name, _ in SIZES:
    m = [r for r in results['runs'] if r['size'] == name and not r['warmup'] and not r.get('failed')]
    if not m: continue
    summary[name] = {k: statistics.median(r[k] for r in m if r[k] is not None)
                     for k in ('prompt_tokens', 'prefill_tok_s', 'ttft_s', 'decode_tok_s', 'drive_read_mb', 'engine_read_mb')}
results['median'] = summary
(OUT / f'{VARIANT}.json').write_text(json.dumps(results, indent=1))
print(json.dumps(summary, indent=1))
