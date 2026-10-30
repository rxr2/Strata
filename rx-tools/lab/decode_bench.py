"""P2: decode at 5K and 64K tokens of context: a code slice + a task that asks for long code, temperature 0.2 (the agents'),
512 tokens; the unique tag at the end. Client-side CLOCK_MONOTONIC marks of each request's decode (first to last token) for
cutting a rocprofv3 trace. usage: decode_bench.py VARIANT OUT_DIR REPS"""
import os, json, sys, time, uuid, urllib.request
from pathlib import Path
BASE = os.environ.get('STRATA_URL', 'http://127.0.0.1:8081')
VARIANT, OUT, REPS = sys.argv[1], Path(sys.argv[2]), int(sys.argv[3]); OUT.mkdir(parents=True, exist_ok=True)
root = Path(os.environ.get('STRATA_CORPUS', Path(__file__).resolve().parents[2])) / 'src'
corpus = ''.join(p.read_text(errors='replace') for p in sorted(root.rglob('*')) if p.suffix in ('.cpp', '.cu', '.hpp') and p.is_file())
TASK = ('\n\nNa podstawie powyższego kodu napisz w C++ nową, kompletną klasę ReadLatencyStats (nagłówek i implementację), '
        'która zbiera histogram opóźnień odczytów, z komentarzami. Tylko kod.')
with urllib.request.urlopen(BASE + '/v1/models') as r: MODEL = json.load(r)['data'][0]['id']
def latest():
    with urllib.request.urlopen(BASE + '/metrics?all=1') as r: m = json.load(r)
    rows = m.get('requests') if isinstance(m.get('requests'), list) else []
    return max(rows, key=lambda x: x.get('time') or 0) if rows else {}
res = []
for ctx, chars in (('c5k', 16_000), ('c64k', 205_000)):
    for rep in range(REPS + 1):
        off = 300_000 + rep * 250_000
        text = corpus[off:off + chars] + TASK + f'\n[tag {uuid.uuid4().hex[:8]}]'
        body = {'model': MODEL, 'messages': [{'role': 'user', 'content': text}], 'max_tokens': 512, 'temperature': 0.2,
                'seed': 11 + rep, 'stream': True, 'reasoning_effort': 'none'}
        req = urllib.request.Request(BASE + '/v1/chat/completions', json.dumps(body).encode(), {'Content-Type': 'application/json'})
        t_first = t_last = None
        with urllib.request.urlopen(req, timeout=1800) as r:
            for line in r:
                if not line.startswith(b'data: ') or line.strip() == b'data: [DONE]': continue
                ch = (json.loads(line[6:]).get('choices') or [{}])[0].get('delta', {})
                if ch.get('content') or ch.get('reasoning_content'):
                    t_last = time.monotonic_ns(); t_first = t_first or t_last
        h = latest()
        row = {'ctx': ctx, 'rep': rep, 'warmup': rep == 0, 'prompt_tokens': h.get('prompt_tokens'), 'out': h.get('output_tokens'),
               'decode_tok_s': h.get('decode_tok_s'), 'mono_first_ns': t_first, 'mono_last_ns': t_last}
        res.append(row); print(json.dumps(row), flush=True)
(OUT / f'{VARIANT}.json').write_text(json.dumps(res, indent=1))
