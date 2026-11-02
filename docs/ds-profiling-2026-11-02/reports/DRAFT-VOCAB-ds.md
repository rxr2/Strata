# Trzecie ramię: główny head ograniczony do słownika szkicu (2026-11-02)

**Wniosek: to już jest produkcyjne zachowanie silnika, a nie nowe ramię.** `dhead_` w MTP jest budowany przez
`gather_rows(head_->weights(), …, dvocab_)` — czyli to **główny head targetu, ograniczony do `draft_vocab.bin`**.
Nie ma osobnego „headu MTP” do podmiany. Różnica między ramionami to **zawartość słownika szkicu**:
- subset (produkcja): 106 299 id;
- pełny główny head: 248 320 id (`STRATA_MTP_FULL_HEAD=1`);
- warianty pośrednie: base + polskie tokeny (różne selekcje).

Sprawdziłem więc, czy **lepszy słownik** daje zysk bez treningu. Wynik: **taki zysk istnieje, ale jest
klasozależny i nie przekracza progu 3% w sposób powtarzalny.**

## 1. Co zmierzyłem

10 klas promptów × 192 tokeny, świeży silnik, ten sam build, NOPROF. Każdy wariant słownika testowany na tym samym
zestawie; bazą jest produkcyjny `draft_vocab.bin`. Pary naprzemienne, z jedną parą w odwrotnej kolejności, żeby
wychwycić dryf/kolejność.

| wariant | dodane tokeny | wynik |
|---|---:|---|
| **base subset** | 0 (106 299 id) | referencja |
| pełny główny head (`FULL_HEAD=1`) | cały vocab (248 320) | 1 przebieg: +2,3% średnio; PL +3,4/+7,2%, repeat +23,3%, JSON −10,4%, proza −4,7% |
| domain PL (Wikipedia+README) | +3 002 (109 301) | 2 przebiegi: +1,1% średnio; PL +3,1/+7,2%, JSON +7,0%, proza −7,0% |
| tylko diakrytyki | +619 (106 918) | 1 przebieg: +1,0%; PL tech +1,4%, PL travel −1,3% — za mało |
| **PL-specific (likelihood ratio)** | **+1 272 (107 571)** | **4 pary: +1,47% średnio**; PL tech **+11,0%**, PL travel +2,2%, JSON +17,2% (niestabilny), repeat −5,3%, math −2,1%, file_edit −2,5%, proza −1,8% |

### PL-specific, 4 pary (średnie)

| klasa | base | PL-specific | delta |
|---|---:|---:|---:|
| polish_tech | 76,0 | 84,3 | **+11,0%** |
| polish_travel | 77,9 | 79,7 | +2,2% |
| json | 85,8 | 100,6 | +17,2% (raz +33%, raz −14%) |
| code_py | 95,0 | 95,8 | +0,9% |
| sql | 105,9 | 105,9 | 0,0% |
| prose_en | 97,5 | 95,8 | −1,8% |
| math | 93,8 | 91,8 | −2,1% |
| file_edit | 84,0 | 81,9 | −2,5% |
| repeat | 105,0 | 99,3 | −5,3% |
| summary | 83,5 | 82,6 | −1,0% |
| **średnia** | **90,44** | **91,77** | **+1,47%** |

Pierwsze 3 pary (base→wariant) dały +2,88%, ale **czwarta para w odwrotnej kolejności** (wariant→base) obniżyła
średnią do +1,47%. To pokazuje, że część „zysków” (JSON, summary) to dryf/kolejność/cache, a nie słownik.
Jedyny **powtarzalny** zysk to **polski techniczny +11%** (6,7 / 14,0 / 11,7 / 11,6% w czterech parach);
polski travel +2,2% (0,9 / 2,8 / 4,2 / 1,0%). Reszta jest w szumie lub lekko ujemna.

## 2. Interpretacja

- **Słownik jest realną dźwignią dla polskiego technicznego** — 1 272 tokeny (+1,2% rozmiaru headu) dają +11%.
  To nie wymaga treningu ani zmiany kodu, tylko nowego `draft_vocab.bin` i restartu.
- **Globalnie to za mało:** +1,47% średnio, poniżej progu 3%; repeat/math/file_edit tracą, a JSON jest bimodalny.
  Globalna podmiana słownika na PL-specific nie jest więc oczywistym wdrożeniem.
- **Per-class policy** (PL-specific dla polskiego/JSON, base dla reszty) mogłaby zebrać +11% na polskim bez strat,
  ale silnik ma **jeden** `draft_vocab.bin` na start; potrzebny byłby drugi head (kolejne ~272 MB) i klucz
  per-request (`strata_tune.draft_vocab`). To kod, nie trening — ale poza zakresem „trzeciego ramienia”.
- **Pełny główny head** daje większy średni zysk (+2,3%) i ratuje repeat (+23%), ale psuje JSON (−10,4%) i prozę
  (−4,7%); również nie przekracza progu w sposób powtarzalny (1 przebieg).
- **Wniosek:** trzecie ramię **nie wystarcza jako globalna zmiana**. Zostaje albo per-class policy (tania, ale
  wymaga kodu i drugiego headu), albo **trening** — zgodnie z ustaloną kolejnością przechodzimy do planu treningu
  na wynajętym GPU z danymi publicznymi i syntetycznymi.

## 3. Pliki

- Słowniki (test, nie produkcja): `~/rx-perf-lab/profiles/20261102-ds/`:
  `draft_vocab_pl_domain.bin` (109 301), `draft_vocab_pl_specific.bin` (106 918), `draft_vocab_pl_lr.bin` (107 571).
- Przebiegi: `~/rx-perf-lab/suite/20261102-1222…-pldomain-1`, `…-1224…-subset-2`, `…-1225…-pldomain-2`,
  `…-1227…-plspec-1`, `…-1229…-pllr-1`, `…-1232…-pllr-2`, `…-1234…-subset-4`, `…-1235…-pllr-3`,
  `…-1237…-pllr-4`, `…-1239…-subset-5` (pełne logi w `strata.log`).
- Skrypt: `ds-pipeline/tools/20261102/` (te same narzędzia); selekcja PL-specific: tokeny spoza base, które
  mają diakrytyk albo częstość PL ≥5 i stosunek PL/EN ≥4 (korpus: Wikipedia PL + README.pl vs README.md + docs).
- Produkcja nietknięta; żaden słownik nie został podmieniony.

## 4. Ograniczenia

- 10 klas × 192 tokeny, 4 pary; szum per klasa 3–4%, a JSON/summary są bimodalne (różne teksty przy różnych
  cache/acceptance). Średnia +1,47% jest obarczona tym szumem.
- Test na promptach suite, nie na prawdziwym ruchu; słownik PL-specific zbudowany z Wikipedii/README, nie z ruchu.
- Pełny head mierzony raz; nie ma 4 par, więc jego +2,3% też nie jest twarde.
- Kolejność par wpływa na wynik (termika/cache); dlatego raportuję osobno 3 pary base→wariant (+2,88%) i 4. parę
  odwrotną (obniża do +1,47%). To nie jest „dowód”, że słownik nie działa — to dowód, że **globalny** efekt jest
  mały i klasozależny.

## 5. Rozmiar słownika (uzupełnienie)

Osobny sweep `SWEEP-ds-vocab.md`: 106k/140k/180k/248k, 3 bloki losowe, NOPROF. **140k** to najlepszy punkt netto:
+2,80% ±1,88 (106k 90,79 → 140k 93,32); 180k +2,80% ±2,63; 248k +1,64% ±1,37. Head Q6_K 2100 B/wiersz:
212,9/280,4/360,5/497,3 MiB; head gemv 246/320/405/561 µs; ~930 GB/s. 248k gubi zysk na koszcie headu;
dwa etapy (106k + pełny head przy p1<0,85) to hipoteza ~1,1% okna zamiast 5,6%.
