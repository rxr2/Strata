"""Quality against a reference: first-token top-20 for 24 prompts ~4K and 8 prompts ~16K tokens (fixed text), and the 4 agent
tasks of H5 at temperature 0 (192 tokens, the text kept). usage: quality2.py VARIANT OUT_DIR"""
import os, json, sys, time, urllib.request
from pathlib import Path
BASE = os.environ.get('STRATA_URL', 'http://127.0.0.1:8081')
VARIANT, OUT = sys.argv[1], Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
root = Path(os.environ.get('STRATA_CORPUS', Path(__file__).resolve().parents[2]))
corpus = ''.join(p.read_text(errors='replace') for p in sorted((root / 'src').rglob('*')) if p.suffix in ('.cpp', '.cu', '.hpp') and p.is_file())
QS = ['Co robi ostatnia funkcja w tym kodzie? Odpowiedz jednym zdaniem.', 'Wypisz nazwę pierwszej klasy lub struktury z tego kodu.',
      'Czy w tym kodzie jest błąd? Odpowiedz tak albo nie i dlaczego.', 'Summarize the purpose of this code in one sentence.']
with urllib.request.urlopen(BASE + '/v1/models') as r: MODEL = json.load(r)['data'][0]['id']
def chat(text, max_tokens, top):
    body = {'model': MODEL, 'messages': [{'role': 'user', 'content': text}], 'max_tokens': max_tokens, 'temperature': 0, 'reasoning_effort': 'none'}
    if top: body |= {'logprobs': True, 'top_logprobs': 20}
    req = urllib.request.Request(BASE + '/v1/chat/completions', json.dumps(body).encode(), {'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=900) as r: return json.load(r)
first = []
for i in range(32):
    n = 13_000 if i < 24 else 52_000
    off = 200_000 + i * 60_000 if i < 24 else 1_800_000 + (i - 24) * 400_000
    d = chat(corpus[off:off + n] + '\n\n' + QS[i % 4], 1, True)
    lp = d['choices'][0]['logprobs']['content'][0]
    first.append({'i': i, 'len': '16k' if i >= 24 else '4k', 'prompt_tokens': d.get('usage', {}).get('prompt_tokens'),
                  'top': [[t['token'], t['logprob']] for t in lp['top_logprobs']]})
    print('first', i, first[-1]['prompt_tokens'], first[-1]['top'][0], flush=True)
ctx_a = (root / 'src/platform/direct_file.cpp').read_text(errors='replace')[:16000]
ctx_b = (root / 'include/strata/program/prefill_plan.hpp').read_text(errors='replace')[:16000]
TASKS = {'edit': ctx_a + '\n\nZwróć CAŁĄ funkcję DirectFile::open w nowej wersji: dodaj sprawdzanie, czy plik ma rozmiar podzielny przez 4096, i komunikat błędu. Tylko kod.',
         'newcode': ctx_b + '\n\nNapisz w Pythonie narzędzie CLI, które czyta JSON z wynikami benchmarku (lista obiektów size, prefill_tok_s, decode_tok_s) i drukuje tabelę median oraz różnice procentowe między dwoma plikami. Tylko kod.',
         'explain': ctx_b + '\n\nWyjaśnij po polsku, krok po kroku, jak planer wybiera rozmiar chunka i ring. Podaj wzór na koszt.',
         'json': ctx_a + '\n\nZwróć wyłącznie JSON: {"files": [...], "steps": [{"file":..., "change":..., "why":...}]} z planem dodania licznika opóźnień odczytu do DirectFile.'}
tasks = {k: chat(t, 192, False)['choices'][0]['message']['content'] for k, t in TASKS.items()}
(OUT / f'{VARIANT}.json').write_text(json.dumps({'first': first, 'tasks': tasks}, ensure_ascii=False, indent=1))
print('done', VARIANT)
