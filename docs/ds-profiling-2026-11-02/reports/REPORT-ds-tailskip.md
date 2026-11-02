# STRATA_ROUTE_TAIL_SKIP=7 na RX 7900 XTX — A/B (2026-11-02)

Kontekst: produkcja 0.1.52, `~/llm/strata/strata-rx.json` nietknięty, 94 tok/s na testowych promptach; 7882/24576
ekspertów w VRAM (32% wszystkich, ~87% trafień routingu), 20% chybień przez PCIe. `STRATA_ROUTE_TAIL_SKIP=7`
pomija chybionego eksperta, którego **każdy token okna** wybiera tylko na pozycji ≥7 z top-10: nie jest ani
liczony na CPU, ani czytany przez PCIe; wkład zero, bez renormalizacji. Na gfx1100 jest **wyłączone domyślnie**,
ale jawna zmienna jest czytana przez `tail_skip_rank()` bez bramki architektury. Kod:
`src/core/expert_source.cpp` (`tail_skip_rank()` ~4796-4930, 5109), `src/program/generate.cpp` ~11043-11090.

## (a) Czy działa i ile pomija

- Start: **`strata serve: STRATA_ROUTE_TAIL_SKIP=7 is ON: ...`** — potwierdzone w 3 przebiegach `EXE=prod`
  (bez „(default)”, bo zmienna jest jawna).
- Per request: `strata serve: route tail skip: N missed experts skipped (M entries) since the start` rośnie;
  11 linii na przebieg (warmup + 10 żądań).
- Pominięte eksperty: **5,1–11,6 tys. na żądanie**; udział w chybieniach, które byłyby bez skipu:
  **36,9–37,5%** (średnie przebiegów; zakres żądań 29–45%). To ponad 1/3 pracy CPU/PCIe.

## (b) A/B szybkości — randomizowany, 3 bloki, EXE=prod, NOPROF

Kolejność base/tail7 w każdym bloku losowa (b1 base→tail7, b2 tail7→base, b3 tail7→base). Delta liczona
względem base z tego samego bloku; średnia z 3, szum = SD tych 3 delt.

| klasa | base tok/s | tail7 tok/s | delta | SD | base acc | tail acc | base tok/win | tail tok/win |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| prose_en | 95,9 | 87,5 | **−8,7%** | 0,6 | 90,5 | 76,4 | 2,23 | 1,76 |
| code_py | 94,4 | 99,5 | +5,5% | 3,0 | 82,0 | 79,7 | 2,26 | 2,19 |
| polish_travel | 73,8 | 84,2 | +14,1% | 3,6 | 75,5 | 83,9 | 1,66 | 1,73 |
| file_edit | 78,6 | 90,2 | +14,7% | 0,7 | 84,0 | 81,5 | 2,79 | 2,56 |
| json | 85,9 | 89,4 | +4,9% | 10,5 | 82,0 | 77,6 | 2,80 | 2,18 |
| repeat | 99,3 | 115,7 | +16,7% | 7,1 | 76,2 | 79,6 | 3,02 | 3,03 |
| math | 88,4 | 98,5 | +11,4% | 3,2 | 89,5 | 87,6 | 2,84 | 2,81 |
| sql | 100,7 | 115,8 | +15,2% | 14,4 | 87,4 | 90,0 | 3,09 | 3,16 |
| polish_tech | 72,0 | 79,6 | +10,5% | 4,6 | 75,8 | 75,8 | 1,69 | 1,74 |
| summary | 80,2 | 88,9 | +10,9% | 15,2 | 80,4 | 83,8 | 2,46 | 2,35 |
| **średnia** | **86,94** | **94,93** | **+9,19%** | **2,79** | — | — | — | — |

Bloki: **+6,59% / +8,84% / +12,14%** — wszystkie dodatnie. To jest wynik decyzyjny (nie naprzemienny
wstępny, który dał +3,92% z parą −1,2%). Proza i JSON tracą na akceptacji/tok/win; reszta klas zyskuje.

## (c) Para z profilerem (mechanizm)

`trace_run.sh EXE=prod` + `stages.py`; profiler zniekształca czasy, więc porównanie jest względne. Kluczowe:
etap „czekanie na eksperty z CPU” (`stages.cpuexp`), wiersze PCIe (`gpu.pcie_rows`), praca puli (`host.parts.cpu_pool`),
`plan_wait`.

| prompt | base us/tok / tok/win | tail7 us/tok / tok/win | CPU experts base→tail | PCIe rows base→tail | CPU pool base→tail | plan_wait base→tail |
|---|---:|---:|---:|---:|---:|---:|
| p1 | 11 807 / 2,25 | 12 981 / 1,84 | 1 731→1 631 µs (−6%) | 935→599 µs (**−36%**) | 2 809→1 848 (−34%) | 361→511 |
| p2 | 12 545 / 2,27 | 11 716 / 2,30 | 2 063→1 493 µs (−28%) | 1 250→718 µs (**−43%**) | 3 485→2 301 (−34%) | 375→342 |
| p3 | 15 547 / 1,63 | 15 674 / 1,48 | 2 694→2 122 µs (−21%) | 1 599→938 µs (**−41%**) | 4 729→2 948 (−38%) | 499→537 |

- **Wiersze PCIe spadają o 36–43%**, praca puli o 34–38%, etap CPU o 6–28% — to jest źródło zysku NOPROF.
- **`plan_wait` nie spada** (a miejscami rośnie): tail skip usuwa eksperty po planie, a plan warstwy 0 to
  opóźnienie hosta, nie praca ekspertów. To nie jest lek na start okna.
- `us_tok`/`tok_win` pod profilerem nie są miarą szybkości, bo tail7 zmienia output (p1 krótszy, p2 dłuższy);
  decyduje NOPROF z (b).

## (d) Bramka jakości

`bench-detached.sh tail7 quality STRATA_ROUTE_TAIL_SKIP=7` (fork build; KL pierwszego tokenu vs FP16):

| zbiór | base KL / top-1 | tail7 KL / top-1 |
|---|---:|---:|
| 4k, 24 promptów | 0,01547 / 22/24 | 0,02154 / 21/24 |
| 16k, 8 promptów | 0,01922 / 8/8 | 0,02247 / 8/8 |
| **wszystkie 32** | **0,01640 / 30/32** | **0,02177 / 29/32** |

- **KL 0,02177 ≤ 0,0235 — przechodzi.** **top-1 29/32 < 30/32 — nie przechodzi o jeden prompt.**
- Zadania agentowe (znaki zgodne z referencją do pierwszej różnicy): edit 566/566 (identyczne), newcode
  761→749, explain 77→136, json 485→256. Czyli kod/edycja prawie bez zmian, **JSON wyraźnie krótszy**,
  explain inny (baza sama jest bimodalna: 77 vs 536/698 w innych przebiegach).
- Decyzja o akceptacji kompromisu jakości (top-1 29/32, proza −8,7%, JSON) należy do użytkownika.

## (e) Punkt D — pojedyncze przebiegi (nie 3 pary; szum 2–4%)

| wariant | tok/s | uwaga |
|---|---:|---|
| tail7 (R=7, pcie 0,20) | 94,93 | baza random A/B |
| R=6 | **101,64** | szybciej, ale większy skip = większe ryzyko jakości |
| R=8 | 91,97 | wolniej niż R=7 |
| pcie-frac 0,10 | 94,21 | bez zysku |
| pcie-frac 0,30 | **98,32** | +3,6% vs R=7; przy tail skip optymalny udział PCIe przesuwa się w górę |
| q4-140 samo (prod) | 92,86 | +6,8% vs base 86,94 — zgodne z sweepem q4 |
| **q4-140 + tail7** | **104,71** | +10,3% vs tail7; zyski się sumują (single) |
| reserve 3072 + tail7 | 97,89 | referencja rezerwy |
| **reserve 2048 + tail7** | **90,67** | **−7,2% — nie schodzić poniżej 3072** (2 monitory) |

- **q4-140 + tail7 = 104,71 tok/s** w jednym przebiegu — okolica celu 105–108; ale to single, nie 3 pary.
- **pcie 0,30 + tail7 = 98,32** — tani dodatek, również single.
- **R=6 = 101,64** — szybszy, ale quality gate dla R=6 nie był mierzony; R=8 wolniejszy.
- **Rezerwa 2048 szkodzi** (−7,2%); nie ruszać 3072.

## (f) Rekomendacja

**Tail skip to prawdziwa dźwignia: +9,19% ±2,79 w randomizowanym A/B (3/3 bloki dodatnie), mechanizm potwierdzony
(PCIe −36..43%, CPU pool −34..38%); quality gate przechodzi KL (0,02177 ≤ 0,0235), ale top-1 29/32 jest o jeden
prompt poniżej progu 30/32, a proza/JSON zmieniają output — więc wdrożenie do `strata-rx.json` (z kopią i zgodą)
tylko po akceptacji tego kompromisu; q4-140+tail7 (104,71, single) i pcie 0,30 (98,32, single) wymagają jeszcze
3 par i osobnej bramki KL/top-1 dla kombinacji, a rezerwy VRAM nie wolno obniżać do 2048.**

## Pliki i ograniczenia

- Raport: ten plik. A/B: `~/rx-perf-lab/suite/*tailr-*`, `*-tail7-*`, `*-tailbase-*`; profiler:
  `~/rx-perf-lab/pipeline/*-tailbase-prof`, `*-tail7-prof`; quality: `~/rx-perf-lab/experiments/fork/*tail7`.
- D: `~/rx-perf-lab/suite/*-tailr6-1`, `*-tailr8-1`, `*-tailp10-1`, `*-tailp30-1`, `*-tailq4-1`, `*-tailq4t-1`,
  `*-tailres3072-1`, `*-tailres2048-1`.
- Ograniczenia: D to pojedyncze przebiegi (szum 2–4%); random A/B to 10 klas × 192 tokeny, nie prawdziwy miks;
  quality gate mierzy pierwszy token i zadania agentowe, nie pełny KL całych odpowiedzi; q4+tail nie ma
  własnej bramki jakości (q4 zmienia teksty w 6–8/10 klas — cache/adaptacja, niekoniecznie sam q4).
- Produkcja nietknięta; `strata-rx.json` bez zmian; nic nie wypchnięto.

## (g) Wdrożenie (2026-11-02, zgodnie z instrukcją użytkownika)

**Zmieniono `~/llm/strata/strata-rx.json`** (kopia: `strata-rx.json.bak-20261102-143040`, SHA-256
`97a10dbd…` — oryginał; nowy config: `66583d89…`):
- `env.STRATA_ROUTE_TAIL_SKIP=7`;
- `--mtp-draft-vocab /home/rxr2/llm/Strata-data/mtp/vocab/draft_vocab_140k.bin` (kopia z sweepu 140k);
- `--mtp-q4 head`;
- **bez zmian:** `--pcie-frac 0.20`, `--vram-reserve-mib 3072`, `--spec-min-p 0.85`, reszta configu.
Rollback: `cp -p ~/llm/strata/strata-rx.json.bak-20261102-143040 ~/llm/strata/strata-rx.json && systemctl --user restart strata-rx`.

Start potwierdzony w logu: `STRATA_ROUTE_TAIL_SKIP=7 is ON`; `draft head over 140000 tokens as Q4_0
(192.3 MiB read per step, was 280.4)`; cache 7881 slotów / 14.94 GiB.

### Bramka jakości całej kombinacji (prod, 32 prompty)

| zbiór | base KL / top-1 | tail+q4 KL / top-1 |
|---|---:|---:|
| 4k (24) | 0,01547 / 22/24 | 0,01990 / 21/24 |
| 16k (8) | 0,01922 / 8/8 | **0,01021** / 8/8 |
| **32** | **0,01640 / 30/32** | **0,01747 / 29/32** |

- **KL 0,01747 ≤ 0,0235 — przechodzi** (i jest lepszy niż sam tail skip 0,02177; q4 pomógł na 16k).
- **top-1 29/32 < 30/32 — nadal o jeden prompt poniżej progu.**
- Agent: edit 566/566 (identyczne), newcode 761→749, explain 77→321, json 485→256.

### Smoke na produkcji (3 stałe prompty, 320 tokenów, live)

| prompt | nowy config | stary config (94,2 śr.) |
|---|---:|---:|
| p1 explain | 96,9 | 99,9 |
| p2 code | 112,7 | 107,2 |
| p3 polski | 87,6 | 75,4 |
| **średnia** | **99,07** | **94,2** |

- +5,2% na 3 stałych promptach; p3 +16,2%, p2 +5,1%, **p1 −3,0%** (proza płaci za tail skip).
- Hit rate 91,1 / 87,4 / 85,6%; tail skip 9,6k / 21,3k / 36,8k ekspertów (narastająco).
- To **nie** jest 105–108: suite q4+tail dał 104,71 w jednym przebiegu, ale 3 stałe prompty dają 99,07.
  Różnica to miks klas (proza p1 traci) i pojedynczy charakter przebiegu.

### Czego nie wdrożono

- `--pcie-frac 0.30` (single 98,32) — wymaga 3 par i kombinacji z q4+tail;
- R=6 (single 101,64) — szybszy, ale bez bramki jakości dla R=6;
- `--vram-reserve-mib 2048` — single 90,67, **gorzej**; zostaje 3072;
- q4-180/248 — 180k ten sam średni zysk, większy szum; 248k gorszy netto.
