"""How much the prefill reads from the drive per prompt length: prompts of ~4K/12K/30K/34K/64K tokens, 1 output token,
then the engine log's 'file tier I/O this request' line and /proc/diskstats for nvme1n1. usage: python3 -I drive_probe.py"""
import os, json, time, uuid, urllib.request, subprocess
from pathlib import Path
BASE = os.environ.get('STRATA_URL', 'http://127.0.0.1:8081')
LOG = Path(os.environ.get('STRATA_LOG', Path.home() / 'harness/strata-engine.log'))
root = Path(os.environ.get('STRATA_CORPUS', Path(__file__).resolve().parents[2])) / 'src'
corpus = ''.join(p.read_text(errors='replace') for p in sorted(root.rglob('*')) if p.suffix in ('.cpp', '.cu', '.hpp') and p.is_file())
with urllib.request.urlopen(BASE + '/v1/models') as r: MODEL = json.load(r)['data'][0]['id']
def disk():
    for l in open('/proc/diskstats'):
        f = l.split()
        if f[2] == os.environ.get('STRATA_DRIVE', 'nvme1n1'): return int(f[5]) * 512
for i, chars in enumerate((13_000, 40_000, 98_000, 108_000, 205_000)):
    text = f'[tag {uuid.uuid4().hex[:8]}]\n' + corpus[200_000 + i * 220_000:][:chars] + '\n\nStreść ten kod jednym zdaniem.'
    body = {'model': MODEL, 'messages': [{'role': 'user', 'content': text}], 'max_tokens': 1, 'temperature': 0, 'reasoning_effort': 'none'}
    n0 = sum(1 for _ in open(LOG, errors='replace')); d0 = disk(); t0 = time.monotonic()
    req = urllib.request.Request(BASE + '/v1/chat/completions', json.dumps(body).encode(), {'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=1800) as r: u = json.load(r).get('usage', {})
    dt = time.monotonic() - t0; time.sleep(2)
    new = open(LOG, errors='replace').read().splitlines()[n0:]
    io = [l for l in new if 'file tier I/O this request' in l or 'resident RAM:' in l or 'expert tiers' in l]
    print(json.dumps({'prompt_tokens': u.get('prompt_tokens'), 's': round(dt, 1), 'tok_s': round((u.get('prompt_tokens') or 0) / dt),
                      'disk_GB': round((disk() - d0) / 1e9, 2)}), flush=True)
    for l in io: print('   ', l[:260], flush=True)
