# Sufit draftu MTP: top-K vs token zweryfikowany (2026-11-02)

Pomiar odpowiedzi na pytanie: **czy lepszy head MTP ma w ogóle czego szukać, czy target jest nieprzewidywalny?**
Wynik: **sufit jest wysoki, a wąskim gardłem jest sam head MTP, nie target ani draft-vocab.**

## 1. Metoda

- Nowy diagnostyk `STRATA_MTP_TOPK=16` (gałąź `rx-ds-profile`, commit `541df347`, domyślnie off): po każdym kroku
  draftu kopiuje logits headu na host i liczy top-K; przy **pierwszym odrzuceniu** w oknie porównuje top-K z tokenem,
  który wybrał verifier (`outv[a]`). Zapis: `strata serve: mtp topk (K=16): dN rej R @1 .. @2 .. @4 .. @8 .. @16 ..`,
  gdzie `dN` to głębokość pierwszego odrzucenia (0 = pierwszy draft).
- 10 klas promptów (`pipeline/suite_prompts.json`) × 192 tokeny, świeży silnik, `spec_min_p=0.85`.
- Dwa ramiona, ten sam prompt/seed:
  1. **subset** — produkcyjny `draft_vocab.bin` (106 299 id) i head MTP z subsetu;
  2. **main head** — `STRATA_MTP_FULL_HEAD=1`: do draftu użyty **główny head targetu** (pełne 248k vocab), czyli górna
     granica tego, co da się wyciągnąć z hidden state.
- To nie jest porównanie „ten sam head z szerszym vocabem”: `STRATA_MTP_FULL_HEAD` podmienia **wagi headu** na główny
  head modelu. Właśnie dlatego pokazuje sufit, a nie tylko efekt draft-vocabu.

## 2. Wyniki — pierwsze odrzucenie (d0), 10 żądań

| klasa | subset: odrzuceń d0 | subset @2/@4/@8/@16 | main head: odrzuceń d0 | main head @2/@4/@8/@16 |
|---|---:|---|---:|---|
| prose_en | 6 | 2 / 4 / 4 / 5 | 1 | 0 / 1 / 1 / 1 |
| code_py | 4 | 0 / 1 / 2 / 2 | 2 | 0 / 2 / 2 / 2 |
| **polish_travel** | **10** | **1 / 1 / 1 / 1** | **4** | **2 / 2 / 3 / 3** |
| file_edit | 2 | 1 / 1 / 1 / 1 | 0 | — |
| json | 5 | 2 / 2 / 3 / 3 | 3 | 2 / 2 / 3 / 3 |
| repeat | 7 | 0 / 0 / 0 / 0 | 0 | — |
| math | 3 | 2 / 3 / 3 / 3 | 3 | 2 / 3 / 3 / 3 |
| sql | 0 | — | 0 | — |
| **polish_tech** | **15** | **0 / 0 / 0 / 0** | **7** | **2 / 4 / 6 / 7** |
| summary | 2 | 1 / 2 / 2 / 2 | 3 | 1 / 2 / 3 / 3 |
| **razem** | **54** | **9 / 14 / 16 / 17 (31,5% @16)** | **23** | **9 / 16 / 21 / 22 (95,7% @16)** |

Wszystkie głębokości razem (d0–d7):

| ramię | odrzuceń | @2 | @4 | @8 | @16 |
|---|---:|---:|---:|---:|---:|
| subset | 117 | 18,8% | 30,8% | 37,6% | **38,5%** |
| main head | 63 | 39,7% | 63,5% | 79,4% | **88,9%** |

## 3. Interpretacja

1. **Head MTP jest daleko od sufitu.** Gdy pierwszy draft jest zły, token targetu jest w top-16 tego headu tylko
   w 31,5% przypadków (wszystkie głębokości: 38,5%). Główny head targetu, na tym samym hidden state, trafia w top-16
   w **95,7%** (wszystkie głębokości: 88,9%) i **odrzuca pierwszy draft 2,3× rzadziej** (23 vs 54).
   Hidden state niesie informację; słabe są wagi małego headu MTP.
2. **Polski to skrajny przypadek.** Subset: 25 odrzuceń d0 w dwóch polskich promptach, tylko **1 token w top-16**
   (4%). Main head: 11 odrzuceń, **10 w top-16** (91%). To nie jest „polski jest nieprzewidywalny” — to head MTP
   nie umie w polski.
3. **Samo rozszerzenie draft-vocabu nie wystarcza.** Zbudowałem `draft_vocab_pl.bin`: +2 591 tokenów z korpusu
   polskiego (Wikipedia + README.pl; base pokrywał 69% wystąpień, nowy 99%). Wynik na tym samym zestawie:
   akceptacja polish_travel 78,2→80,6%, polish_tech 77,8→81,7%, ale średnia tok/s **92,8 → 92,8** (bez zmian),
   a część klas (prose, summary) spadła. Tokeny są dostępne, ale head ich nie rankuje wysoko — **liczą się wagi
   headu, nie sam vocab.** Plik został w `/tmp/opencode/draft_vocab_pl.bin` (test, nie produkcja).
4. **Main head jako drafter to nie darmowy zamiennik.** `STRATA_MTP_FULL_HEAD=1` dał w jednym przebiegu średnio
   **+2,3%** (92,8→95,0): polish_travel +3,4%, polish_tech +7,2%, repeat **+23,3%**, ale JSON **−10,4%**, prose −4,7%,
   math −2,5%, SQL −1,5%. To pojedynczy przebieg; wymaga 3 par i polityki per klasa. Główny head jest też wolniejszy
   (większa projekcja), więc netto może się nie opłacać wszędzie.

## 4. Co to znaczy dla „polskiego heada”

- **Trening/fine-tune ma sens i jest uzasadniony pomiarem.** Sufit jest wysoki (main head: 89–96% top-16), więc
  lepszy head może odzyskać większość odrzuceń; to nie jest walka z nieprzewidywalnym targetem.
- **Nie wystarczy dodać polskich tokenów do draft-vocabu** — trzeba wytrenować wagi headu (albo użyć głównego headu).
- **Realistyczny cel fine-tune’u:** akceptacja PL z 75–78% do ~85–90% (nie 99,5%), czyli +5–8% tok/s na polskim,
  ~+1–2% średnio. Główny head pokazuje, że 90%+ jest w zasięgu, ale mały head MTP może nie mieć dość pojemności.
- **Najtańszy interim:** 3-pair A/B `STRATA_MTP_FULL_HEAD=1` vs subset na prawdziwym miksie; jeśli średnia >3%
  i JSON nie spada, można rozważyć politykę „main head dla polskiego/repeat, MTP dla reszty” (per-request nie da się
  przełączyć bez nowego klucza; trzeba by dodać `strata_tune.full_head` albo wybór na starcie).
- **Zanim trenować:** zmierzyć top-k na **polskim korpusie poza promptami testowymi** (mamy 10 klas, ale to nadal
  jeden zestaw); jeśli top-16 main head jest równie wysokie, trening jest wart zachodu.

## 5. Pliki

- Diagnostyk: `STRATA_MTP_TOPK=16` w `src/core/mtp.cpp` / `generate.cpp` (commit `541df347`); `STRATA_MTP_FULL_HEAD=1`
  był już w silniku.
- Przebiegi: `~/rx-perf-lab/suite/20261102-114912-topk-subset-1` (subset),
  `~/rx-perf-lab/suite/20261102-115054-topk-full-1` (main head),
  `~/rx-perf-lab/suite/20261102-115230-fullhead-1` (NOPROF, main head),
  `~/rx-perf-lab/suite/20261102-115500-plvocab-1` (polski draft-vocab).
- Skrypt: `ds-pipeline/tools/20261102/` (ten sam zestaw); nowy `draft_vocab_pl.bin` w `/tmp/opencode/`.
- Nota wykonalności treningu: `FEASIBILITY-ds-mtp-training.md` (pamięć 24 GB, zrzut 20,5 GB/mln, gate top-K,
  PyTorch 2.13.0+rocm7.1 5,86 GB lokalnie / CUDA na wynajętym 80 GB).
- Trzecie ramię (słownik szkicu): `DRAFT-VOCAB-ds.md` — PL-specific +1,47% średnio, PL tech +11%, globalnie
  za mało; przejście do planu treningu na wynajętym GPU.
- Raport główny: `REPORT-ds-profiling.md`.

## 6. Ograniczenia

- Jedno powtórzenie na ramię (10 klas × 192 tokeny); top-k to diagnostyk hostowy, spowalnia draft, ale nie zmienia
  akceptacji. Main head vs subset to różne wagi, nie tylko vocab — to celowo górna granica.
- `d0` to pierwsze odrzucenie; dla głębszych odrzuceń ranking może się różnić (tabela „wszystkie głębokości” to
  pokazuje, ale nie ma rozbicia per klasa).
- `STRATA_MTP_FULL_HEAD=1` używa głównego headu targetu; to nie jest „head MTP po treningu”, tylko sufit.
- Draft-vocab PL zbudowany z Wikipedii + README.pl (nie z prawdziwego ruchu); wynik może się różnić na kodzie/JSON.
