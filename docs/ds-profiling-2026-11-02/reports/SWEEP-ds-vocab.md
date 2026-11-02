# Słownik szkicu: rozmiar 106k / 140k / 180k / 248k — pomiar (2026-11-02)

Cel: czy większy słownik szkicu (główny head targetu ograniczony do N tokenów) zbiera zysk pełnego słownika
przy akceptowalnym koszcie — bez treningu. Wszystko na jednej karcie, NOPROF; produkcja nietknięta.

## 1. Konfiguracja eksperymentu

- Słowniki: 106 299 (produkcyjny base), 140 000, 180 000, 248 320 (pełny vocab). Tokeny spoza base wybrane
  wg częstości z korpusu PL (Wikipedia/README.pl) + EN (README/docs) + kod (mtp/verify/kernele/tools),
  z wagami 0,4/0,3/0,3; przy remisie rosnące id. 140k/180k zawierają odpowiednio +33,7k/+73,7k tokenów
  (4 329 ma niezerową częstość w korpusie, reszta to ogon wg id).
- Silnik: fork `rx-ds-profile` (commit z diagnostyką), `--mtp-draft-vocab` na start; **bez** `STRATA_MTP_FULL_HEAD`
  (wszystkie rozmiary idą tą samą ścieżką: gather rows głównego headu + mapa słownika).
- A/B: 3 bloki; w każdym bloku losowa kolejność 106k/140k/180k/248k; w każdej parze 106k jest odniesieniem.
  10 klas × 192 tokeny, NOPROF, ten sam build. Kolejność bloków: patrz `ab_order.txt`.
- Diagnostyka (osobne przebiegi, 3 prompty: prosa EN, kod 640, polski tech 320):
  `STRATA_MTP_TOPK=16`, `STRATA_MTP_PROFILE=1`, `STRATA_DRAFT_TIMING=1`; head gemv z profilu MTP,
  top-1 p z logitów, d0 z topk. Diagnostyka spowalnia draft — **jej tok/s nie są używane**; tylko akceptacja,
  d0, p1 i koszt headu.

## 2. Koszt headu i sufit (diagnostyka)

| rozmiar | head na dysku/VRAM | head gemv / krok | krok draftu (GPU) | d0 odrzuceń | d0 w top-16 | p1<0,85 | efektywne pasmo |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 106k | 212,9 MiB | **246 µs** | 792 µs | 33 | 11 (33,3%) | 35,4% | 907 GB/s |
| 140k | 280,4 MiB | **320 µs** | 879 µs | 23 | 18 (78,3%) | 34,5% | 918 GB/s |
| 180k | 360,5 MiB | **405 µs** | 974 µs | 19 | 17 (89,5%) | 33,6% | 933 GB/s |
| 248k | 497,3 MiB | **561 µs** | 1 161 µs | 15 | 14 (93,3%) | 32,6% | 929 GB/s |

- Head to Q6_K, **2 100 B/wiersz** (2560 / 256 × 210); rozmiar = N × 2 100 B. Rzutowanie czyta cały head
  (N wierszy) na każdy krok; logits to dodatkowo N × 4 B (0,43–0,99 MB, pomijalne).
- Head jest **memory-bound na ~930 GB/s** (907–933 GB/s); czas rośnie liniowo z rozmiarem. To nie jest
  narzut launchera ani marnotrawstwo — to koszt odczytu wierszy.
- Koszt headu na **okno** = head rundy + (steps/round) × head kroku. Przy zmierzonych steps/round
  (1,50 / 1,44 / 1,61 / 1,70): **0,62 / 0,79 / 1,07 / 1,52 ms/okno** (2,3% / 2,9% / 3,9% / 5,6% okna 27 ms).
  Różnica 106k→248k to ~0,9 ms/okno (~3,3%).
- Sufit: d0 odrzucenia spadają 33→15 (−55%), a trafność top-16 przy odrzuceniu rośnie 33%→93%. **140k**
  (78% top-16) zbiera większość sufitu za +31% bajtów headu; **180k/248k** dokładają coraz mniej.
- p1<0,85 ułamek kroków spada 35,4%→32,6% — większy head jest trochę pewniejszy, ale **~1/3 kroków i tak
  ma niską pewność**; to jest przestrzeń dla dwustopniowego draftu.

### Dwa etapy — rachunek

- Etap 1: 106k (246 µs/krok). Na krokach z p1<0,85 (35,4%) dodatkowo pełny head 248k (561 µs).
- Średni koszt headu na krok: 0,246 + 0,354×0,561 = **0,445 ms** (vs 0,246 subset, 0,561 pełny).
  Per okno (1,5 kroku): ~0,67 ms vs 0,62 (subset) i 1,52 (pełny) — czyli **~1,1% okna**, a nie 5,6%.
- Warunek opłacalności: pełny head musi na tych 35% kroków odzyskać wystarczająco dużo akceptacji.
  d0 top-16 93% vs 33% sugeruje, że jest co zbierać, ale **to nie jest zmierzone bez implementacji**;
  rachunek jest hipotezą do prototypu, nie obietnicą.

### Tańsze kwantowanie headu

- **Zmierzone** `--mtp-q4=head`, 248k: Q6_K 2 100 B/wiersz → Q4_0 **1 440 B/wiersz (0,686×)**, head **341,0 MiB**
  (było 497,3), head gemv **373 µs/krok** (było 561), krok draftu 969 µs (było 1 161). Na okno: **0,98 ms**
  zamiast 1,52 ms (−0,54 ms, ~2% okna).
- Jakość draftu przy q4: d0 18 odrzuceń (q6: 15), top-16 przy d0 16/18 = 89% (q6: 93%), p1<0,85 33,1%
  (q6: 32,6%). Czyli q4 **nie psuje draftu dramatycznie**; różnice są w szumie diagnostyki.
- **3 pary q4 (106k / q4-140 / q4-180 / q4-248, losowa kolejność):** 106k 88,13; **q4-140 94,02
  (+6,75% ±3,47)**, **q4-180 94,01 (+6,76% ±4,15)**, q4-248 91,59 (+3,96% ±1,49). Czyli q4-140 i q4-180
  są najlepsze; q4-248 gubi na koszcie większego headu. Per klasa (q4-140 / q4-180 / q4-248 vs 106k):
  PL tech +10,6/+11,8/+9,6%, PL travel +4,7/+4,6/+3,9%, JSON +15,8/+17,7/+6,1%, repeat +15,3/+18,2/+18,2%,
  code +4,4/+6,5/+3,6%, file_edit +9,2/+7,1/+4,4%, SQL +6,6/+5,4/−0,2%, math +5,4/+3,4/+0,6%,
  proza −2,1/−3,6/−1,7%, summary 0,0/−2,1/−3,6%.
- **q4-140 to nowy najlepszy punkt:** +6,75% średnio, a head q4-140 (~192 MiB, ~210 µs/krok) jest **tańszy
  niż q6 106k** (212,9 MiB, 246 µs). q4-180 ma ten sam średni zysk, ale większy szum; q4-248 jest gorszy netto.
- To jest zmiana **tylko draftu** (główny head targetu nadal Q6_K w verifierze), więc tekst wyjściowy jest
  lossless; q4 nie wymaga bramki KL. (Hash tekstu może się różnić przez cache/adaptację, nie przez q4.)
- Dwa etapy z q4: subset 106k (246 µs) + q4 pełny head na p1<0,85 (35,4%) = 0,246+0,354×0,373 = **0,378 ms/krok**;
  na okno ~0,57 ms vs 0,62 (subset) i 0,98 (q4 pełny) — prawie darmowe. Jeśli q4 pełny head zachowa akceptację,
  to jest najlepszy wariant: sufit 248k przy koszcie bliskim 106k. Wymaga implementacji, nie tylko przełącznika.

## 3. A/B 3 pary (10 klas, NOPROF)

3 bloki; w każdym bloku losowa kolejność 106k/140k/180k/248k; delta liczona względem **106k z tego samego bloku**,
średnia z 3 par, szum = SD tych 3 delt.

| rozmiar | średnia tok/s | delta vs 106k | szum (SD par) |
|---|---:|---:|---:|
| 106k | 90,79 | — | — |
| **140k** | **93,32** | **+2,80%** | ±1,88 |
| **180k** | **93,33** | **+2,80%** | ±2,63 |
| 248k | 92,27 | +1,64% | ±1,37 |
| **q4-140** | **94,02** | **+6,75%** | ±3,47 |
| **q4-180** | **94,01** | **+6,76%** | ±4,15 |
| q4-248 | 91,59 | +3,96% | ±1,49 |

(q4 wiersze: osobny sweep 3 bloków, baza 106k w tych blokach 88,13; nie mieszaj z q6 — inne przebiegi.)

Per klasa (delta vs 106k; 140k / 180k / 248k):

| klasa | 106k tok/s | 140k | 180k | 248k | SD 140/180/248 |
|---|---:|---:|---:|---:|---|
| polish_tech | 75,7 | **+8,2%** | **+7,8%** | **+8,1%** | 4,5 / 0,3 / 2,8 |
| polish_travel | 76,1 | +4,9% | +3,9% | +1,9% | 1,2 / 0,9 / 0,5 |
| json | 87,0 | +13,5% | +9,8% | +11,4% | 7,6 / 12,8 / 8,2 |
| repeat | 103,6 | +8,6% | +14,1% | +15,3% | 3,0 / 4,7 / 3,3 |
| code_py | 96,3 | +0,2% | +2,6% | −0,3% | 1,7 / 3,2 / 4,6 |
| sql | 105,5 | +2,9% | +1,4% | −2,8% | 2,1 / 3,8 / 4,5 |
| math | 91,7 | +0,3% | −2,8% | −2,6% | 4,0 / 2,5 / 1,1 |
| file_edit | 86,1 | −2,5% | −0,1% | −1,0% | 5,5 / 2,8 / 3,7 |
| prose_en | 98,1 | −4,1% | −2,6% | −6,5% | 9,3 / 7,2 / 3,6 |
| summary | 87,8 | −2,3% | −5,4% | −5,5% | 2,2 / 7,6 / 4,9 |

Akceptacja (draft accepted/offered, średnia z 3 bloków):

| klasa | 106k | 140k | 180k | 248k |
|---|---:|---:|---:|---:|
| polish_tech | 77,3% | 84,7% | 85,4% | **89,5%** |
| polish_travel | 73,4% | **87,1%** | **87,4%** | 85,7% |
| json | 80,1% | 90,7% | 91,0% | 91,5% |
| repeat | 77,2% | 89,3% | 97,3% | 97,5% |
| code_py | 80,2% | 83,8% | 84,8% | 83,4% |
| sql | 89,9% | 92,2% | 93,4% | 90,8% |
| math | 87,1% | 88,5% | 90,7% | 91,0% |
| file_edit | 87,4% | 87,8% | 91,0% | 92,5% |
| prose_en | 87,5% | 89,7% | 85,4% | 84,0% |
| summary | 88,2% | 82,7% | 82,1% | 83,0% |

### Interpretacja

- **140k to najlepszy punkt netto:** +2,80% średnio przy najniższym koszcie headu (0,79 ms/okno) i najmniejszym
  szumie; 180k daje ten sam średni zysk, ale kosztuje 1,07 ms/okno i ma większy rozrzut. **248k jest gorszy netto**
  (+1,64%), bo head 1,52 ms/okno zjada akceptację.
- Zysk jest **klasozależny i powtarzalny** na polskim technicznym (+8% w każdym rozmiarze), polskim travel
  (+2–5%) i repeat (+9–15%); JSON jest dodatni, ale z dużym szumem. Tracą proza (−3–6%), summary (−2–6%),
  math/SQL w okolicy zera.
- **+2,80% jest poniżej progu 3%**, ale blisko; SD par 1,9–2,6 oznacza, że to nie jest jeszcze „pewne 3%”.
  Jeśli miks produkcji jest polsko/JSON-owy, 140k może być wart wdrożenia; jeśli proza/summary dominują — nie.
- **Head jest memory-bound na ~930 GB/s** — większy słownik to przede wszystkim większy odczyt, nie narzut
  launchera. Dlatego 248k nie wygrywa: akceptacja rośnie, ale koszt rośnie szybciej.
- **Dwa etapy** (106k + pełny head przy p1<0,85) to jedyny sposób, by mieć 93% top-16 bez płacenia 5,6% okna:
  szacunkowo ~1,1% okna zamiast 5,6%, ale wymaga implementacji i pomiaru, czy pełny head na tych 35% krokach
  rzeczywiście odzyskuje akceptację. To hipoteza, nie wynik.
- **Tańsze kwantowanie** (Q4_0 head) obniżyłoby 248k do ~322 MiB i ~363 µs/krok (~0,99 ms/okno); czy akceptacja
  się utrzyma — test `--mtp-q4=head` w toku (wynik dopiszę, gdy się skończy).

## 4. Pliki

- Słowniki: `/tmp/opencode/draft_vocab_{140k,180k,248k}.bin`; base: `~/llm/Strata-data/mtp/rt/draft_vocab.bin`.
- Diagnostyka: `~/rx-perf-lab/suite/20261102-125757-diag2-106`, `…-125345-diag2-140`, `…-125500-diag2-180`,
  `…-125616-diag2-248`.
- A/B: `~/rx-perf-lab/suite/*-ab{106,140,180,248}-b{1,2,3}`.
- Q4: `~/rx-perf-lab/suite/20261102-131819-diag-q4-248` (diagnostyka), `…-ab-q4-248`, `…-ab-q4-180`;
  3-pair q4 w `*-q4-{140,180,248}-b{1,2,3}` (w toku).
- Skrypt analizy: `/tmp/opencode/ab_analyze.py`.

### Ważne: q4 nie jest bitowo identyczny w praktyce

Porównanie tekstów q4-140 vs 106k w tych samych blokach: tylko 2–4 z 10 klas mają identyczny hash; reszta się różni.
To nie musi być wina samego q4 (to drafter; verifier zostaje na Q6_K) — równie dobrze zmiana czasu draftu przestawia
adaptację/cache i tor CPU/GPU, a stąd rounding. Ale **nie wolno zakładać, że q4 jest darmowy jakościowo**:
przed połączeniem q4-140/180 z tail skipem trzeba zmierzyć KL/top-1 dla **całej kombinacji**, nie tylko tail skipu.
Sam q4 jest kandydatem na +6,75%, ale z bramką jakości.
