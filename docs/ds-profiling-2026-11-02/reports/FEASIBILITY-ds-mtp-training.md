# Wykonalność treningu headu MTP — nota (2026-11-02, zaktualizowana)

**Nic nie zostało zainstalowane ani wytrenowane.** To nota decyzyjna: co trzeba by zrobić, ile to waży, ile zajmie
i gdzie są ryzyka. Decyzję o instalacji i treningu podejmuje użytkownik.

Punkt wyjścia: pomiar sufitu (`CEILING-ds-mtp.md`) pokazał, że przy pierwszym odrzuceniu token targetu jest w top-16
głównego headu w 95,7%, a w top-16 headu MTP tylko w 31,5%. Head MTP jest wąskim gardłem, nie target.

**Trzecie ramię zostało zmierzone** (`DRAFT-VOCAB-ds.md`): „główny head ograniczony do słownika szkicu” to już
produkcyjne zachowanie (`dhead_` jest zbierany z `head_->weights()`); zmieniałem **zawartość słownika**. Wynik:
+1,47% średnio w 4 parach, polski techniczny **+11%**, ale repeat −5,3%, math −2,1%, a JSON jest bimodalny.
**Globally za mało** (próg 3%), więc zgodnie z ustaloną kolejnością planujemy trening na **wynajętym GPU
z danymi publicznymi i syntetycznymi**. Ruch lokalny pozostaje opcjonalny, tylko za zgodą i po redakcji.

## 1. Ile parametrów i ile pamięci (24 GB lokalnie / 80 GB wynajęte)

MTP to **jedna warstwa MoE**: 31 tensorów, 2 607 150 848 parametrów (2,607 mld). Z tego:

| część | parametry | BF16 |
|---|---:|---:|
| dense (attention q/o, HC, fc, shared expert, router, normy) | **90 568 448** (90,6 M) | 0,181 GB |
| eksperci (512 × gate_up/down) | **2 516 582 400** (2,517 mld) | 5,033 GB |
| **razem** | **2,607 mld** | **5,214 GB** |

Wagi na dysku to q8_0/q2_0 (787 MB), ale trening liczy w BF16/FP16 — trzeba je zdequantyzować (5,2 GB).
**Główny head targetu i embedding tokenów są zamrożone**; nie są częścią 31 tensorów MTP. Główny head to
248 320 × 2560 = 635,7 M parametrów (BF16 1,27 GB; subset draft-vocab 106 299 × 2560 = 272 M, 0,54 GB).
Embedding targetu to również 635,7 M (BF16 1,27 GB; w IQ4_XS na dysku ~322 MB). Draft nie ma własnego
trenowalnego output-headu — używa głównego headu (lub jego subsetu).

### Warianty treningu

| wariant | trenowalne parametry | wagi+grady+optymalizator | zamrożone | szacunkowo razem | 24 GB? | 80 GB? |
|---|---:|---:|---|---:|---|---|
| **A. dense-only** (zamrożone eksperci) | 90,6 M | ~1,5 GB | MTP eksperci 5,03 + head 0,54–1,27 + embedding 1,27 + aktywacje 2–4 | **10–13 GB** | **tak** | tak |
| **B. dense + LoRA r=8 na ekspertach** | 90,6 + 28,8 = **119,4 M** | ~2,0 GB | jak wyżej | **11–14 GB** | **tak** | tak |
| C. pełne eksperci, AdamW FP32 | 2,607 mld | ~41,7 GB (5,2 wagi + 5,2 grady + 20,9 m/v + 10,4 master) | — | >42 GB | **nie** | **tak** |
| D. pełne eksperci, 8-bit Adam, bez master | 2,607 mld | ~26 GB + aktywacje | — | ~28–32 GB | **nie / na granicy** | tak |

Rekomendacja: **na 24 GB zacząć od A**, potem B; **na wynajętym 80 GB (A100/H100) można od razu iść w C**
(pełne eksperci, ~42 GB + aktywacje), co usuwa ograniczenie „dense-only może nie dosięgnąć sufitu”.
LoRA r=8 na wszystkich ekspertach to 28,8 M parametrów (r=4: 14,4 M, r=16: 57,7 M).

Uwaga: „polski head” w praktyce oznacza **warstwę MTP** (dense + router + ewentualnie LoRA ekspertów), a nie
osobny output-head. Output to zamrożony główny head targetu; trening uczy MTP tak, żeby jego hidden state
po tym headzie dawał polski token. To jest zgodne z tym, co robi silnik.

## 2. Rozmiar zrzutu stanów ukrytych i sposób zbiórki

Wejście MTP to `Rin_`: **HC=4 strumienie × 2560 = 10 240 wartości BF16 na token** (20 480 B = 20,5 KB/token).
Do tego 8 B na token (id wejściowy + id etykiety). Zrzut:

| tokeny | rozmiar (BF16, 4 strumienie) | FP8 | 1 strumień (niezalecane) |
|---:|---:|---:|---:|
| 1 mln | **20,5 GB** | 10,2 GB | 5,1 GB |
| 3 mln | 61,4 GB | 30,7 GB | 15,4 GB |
| 10 mln | 204,8 GB | 102,4 GB | 51,2 GB |

**Dysk na tej maszynie:** root ma **79 GB wolnego**, dysk modelu **13 GB** (99% zajęty). Czyli:
1 mln tokenów — mieści się; 3 mln — ledwo (61 GB z 79 GB); 10 mln — **nie**. Na większy zrzut potrzebny jest
zewnętrzny NVMe albo AC922 (256 GB RAM, ale trzeba sprawdzić dysk). Alternatywa: FP8 (10,2 GB/mln) albo
strumieniowanie/trening online na maszynie z 96 GB (AC922), gdzie target i head mogą współistnieć.

### Jak zbierać z silnika

- Dodać hook `STRATA_MTP_DUMP=<path>` (domyślnie off) w `MtpDrafter::prefill` / `stage_source_R`, tam gdzie
  `Rin_` (T×HC×N) jest już przygotowany dla MTP. Zapis: nagłówek (model hash, tokenizer hash, HC, N, liczba tokenów)
  + per token: `int32 tok_in`, `int32 tok_label`, `bf16 Rin[4*2560]`. Format sekwencyjny, chunkowany, bez random access.
- **Prefill** targetu to ~3 tys. tok/s: 1 mln tokenów ≈ 6 min, 10 mln ≈ 1 h. To najlepszy sposób na korpus publiczny.
- **Decode** z prawdziwego ruchu to ~94 tok/s: 1 mln tokenów ≈ 3 h. Nadaje się do próbki rzeczywistego ruchu
  (np. 10–20% żądań), nie do całego korpusu.
- Hook musi być bitowo neutralny dla produkcji (tylko odczyt po stronie hosta); test parity: ten sam tekst
  z hookiem i bez, ten sam hash. Dump zawiera tokeny i stany ukryte — dane wrażliwe (patrz §3).
- Do treningu potrzebny jest też embedding następnego tokenu (target, zamrożony) i główny head; można je wyciąć
  z GGUF (repo ma `tools/mtp_fetch.py` i `gguf`), albo dumpować `e2_` (embedded next token, +5 KB/token, czyli
  +5 GB/mln) i nie ładować embeddingu. Lepiej: token id + tabela embeddingu (1,27 GB BF16, stała).
- Etykieta: MTP dostaje `h_t` i embedding `t+1`, przewiduje `t+2` (tak jak w `mtp.cpp`); hook musi zapisać oba
  tokeny. Dokładny offset potwierdzić testem parity na 1 tokenie z silnikiem.

## 3. Jakie dane, proporcje, długi kontekst, prywatność

### Klasy i proporcje (punkt startowy; docelowo zmierzyć z logów produkcji)

| klasa | udział | uwagi |
|---|---:|---|
| kod / edycja pliku | 35% | najczęstszy ruch agentowy; akceptacja 80–88% |
| JSON / SQL / tool calls | 20% | strukturalne, wysokie T; dobry draft daje dużo |
| polska proza / technika | 20% | obecnie najsłabszy (75–78% akceptacji); to główny cel |
| angielska proza / summary | 15% | regresja EN musi być ≤2 pkt |
| matematyka / rozumowanie | 5% | niskie T, ale wrażliwe na złe drafty |
| powtórzenia / listy / formaty | 5% | wysokie T; pełny head dawał +23% |

Długi kontekst: **70% <4k, 20% 4–16k, 10% 16–64k**, w tym min. 5% >32k. MTP widzi hidden state per token, ale
rozkład hidden state przy 32–64k jest inny (attention/KV); użytkownik ma przypadek 62k/85 tok/s, więc warto go pokryć.
Nie trenować wyłącznie na krótkich promptach z suite — to zbyt wąskie.

Objętość: **1–3 mln tokenów** na pierwszy dense-only run; 5–10 mln na LoRA/pełne eksperci. 1 mln tokenów tekstu
to ~4–6 MB (BPE ~4–5 znaków/token), więc sam tekst jest tani; drogi jest zrzut hidden states (20,5 GB/mln).

### Źródła (zgodnie z decyzją: publiczne + syntetyczne)

1. **Publiczny polski** (Wikipedia, Wolne Lektury, dokumentacja techniczna) — pierwsza iteracja, zero ryzyka
   prywatności; wystarczy do sprawdzenia, czy head w ogóle się uczy.
2. **Syntetyczne** — prompty i odpowiedzi generowane przez target na publicznych dokumentach (self-distillation:
   kod, JSON/SQL, listy, streszczenia, polska technika). Hidden state zawsze z targetu, więc rozkład jest zgodny
   z silnikiem; nie trzeba prawdziwego ruchu.
3. **Suite promptów** — tylko regresja i porównanie z baseline, nie trening (za mało i zbyt specyficzne).
4. **Prawdziwy ruch** — opcjonalnie, dopiero po pierwszym cyklu, za zgodą, próbka 10–20%, po redakcji i na
   zaszyfrowanym wolumenie; nie jest potrzebny do startu.

### Prywatność (dotyczy tylko opcjonalnego ruchu lokalnego)

- **Publiczne/syntetyczne dane nie zawierają ruchu użytkownika** — to domyślna ścieżka; można je wysłać na wynajęty
  GPU bez ryzyka prywatności (nadal bez sekretów w plikach).
- Jeśli kiedyś dojdzie prawdziwy ruch: wszystko lokalnie, zero uploadu/telemetrii; dump i checkpointy w `chmod 700`
  na zaszyfrowanym wolumenie (LUKS/age/gpg); redakcja kluczy/e-maili/ścieżek przed dumpem; hidden state nadal
  traktować jak dane osobowe (10 240 floatów/token); próbka 10–20%, zgoda, split po żądaniu/rozmowie, usunięcie
  surowych dumpów po treningu.
- **Rozdzielenie zbiorów**: split po **żądaniu/rozmowie**, nie po tokenie; 80/10/10; osobny publiczny test PL
  i suite regresyjny.

## 4. Ocena offline przez top-K i próg wejścia w A/B

### Metryki offline (held-out, nie trening)

Użyć diagnostyki `STRATA_MTP_TOPK=16` (albo jej odpowiednika w PyTorch na logits headu) na **200+ oknach na klasę**:

| metryka | teraz (subset) | próg wejścia | sufit (main head) |
|---|---:|---:|---:|
| odrzucenia pierwszego draftu (d0) | 54 / 10 żądań | **−25%** | 23 / 10 |
| top-16 @ d0 | 31,5% | **≥75%** | 95,7% |
| top-16 wszystkie głębokości | 38,5% | **≥65%** | 88,9% |
| akceptacja PL (draft accepted/offered) | 75–78% | **≥85%** | 88–93% |
| regresja EN/JSON | — | **≤2 pkt** | — |
| koszt kroku draftu | baseline | **≤+10%** | — |

Ważne: oceniać **spakowany model q2_0** (`mtp_pack.py`), nie tylko PyTorch — kwantyzacja ekspertów może zjeść zysk.
Jeśli q2_0 psuje wynik, sprawdzić q4_0 (1,42 GB) albo zostawić dense BF16.

### Próg wejścia w A/B w silniku

Dopiero po przejściu offline:

1. 3 pary naprzemiennie (baza, nowy head, baza, …) na tych samych promptach, **NOPROF**, ten sam build.
2. Średnia tok/s **≥+3%** i powtarzalna (3/3 albo 2/3 z jasnym efektem); tokeny/okno ≥+5%.
3. Tekst **identyczny** (drafter jest lossless; jeśli się różni, to błąd weryfikacji, nie „jakość”).
4. Brak regresji >2% na EN/JSON; jeśli jest, zawęzić trening (polski + kod) albo wrócić do dense-only.
5. Jeśli offline przeszedł, a A/B nie — stop; koszt draftu/kwantyzacja zjadły zysk.

Top-K to szybka iteracja; A/B w silniku jest decyzją. Próg 3% jest taki sam jak w całym raporcie (szum 3–4%).

## 5. Wymagania programowe (bez instalacji)

### Wariant R (rekomendowany): wynajęty GPU 80 GB, CUDA

- **PyTorch 2.13.0+cu129** (albo +cu130), Linux, `cp314`/`cp312`: wheel `torch` ~0,93 GB + biblioteki NVIDIA
  (`nvidia-cublas`, `cudnn`, …) ~2–3 GB; **razem ~3–4 GB**. Nie używa ROCm; `torch.cuda.is_bf16_supported()`
  na A100/H100 jest prawdziwe.
- **Dane**: tylko publiczne/syntetyczne, więc upload na wynajęty GPU nie niesie ruchu użytkownika. Zrzut 1M tokenów
  to 20,5 GB; przy 1 Gb/s ~3 min, przy 100 Mb/s ~30 min. Checkpoint MTP po treningu ~0,8–1,5 GB do pobrania.
- **Dysk**: 100–200 GB na 5–10 mln tokenów + checkpointy; na wynajętym zwykle jest.
- **Kod**: PyTorch, własna implementacja 31 tensorów MTP z `mtp.cpp` (shapes w `dense.txt`), loader BF16,
  tokenizer/embedding/head z GGUF, `mtp_pack.py` do formatu silnika; test parity 1 token PyTorch vs silnik.
  Nie potrzeba `transformers`, `bitsandbytes`, `deepspeed`, `flash-attn`.

### Wariant L (lokalny pre-test): RX 7900 XTX 24 GB, ROCm

- **PyTorch ROCm 7.1, 2.13.0+rocm7.1** (albo 2.12.1+rocm7.1), `cp314`: wheel **5,86 GB** z bundlowanym ROCm 7.1
  (`https://download.pytorch.org/whl/rocm7.1`); zależności ~0,2 GB; razem **~6,1 GB**.
- Wheel **nie używa TheRock 10.1**; potrzebny kompatybilny sterownik jądra `amdgpu`. Test: `torch.cuda.is_available()`,
  `get_device_name()`, `is_bf16_supported()`, mały matmul. Jeśli nie działa — kontener ROCm 7.1, AC922 albo
  build pod ROCm 10.1 (długo, niezalecane).
- **Dysk**: 6,1 GB wheel + 20,5 GB zrzut 1M + 2–5 GB checkpointy = **~30–35 GB**; root ma 79 GB, więc 1M
  się mieści. Większe zrzuty → zewnętrzny NVMe/AC922.
- Ten wariant służy do **dense-only/LoRA** i szybkich testów parity; pełny trening na 80 GB jest czystszy.

### Wspólne

- **Kod treningowy**: PyTorch, implementacja MTP (attention, HC, 512 ekspertów, router, shared expert) z `mtp.cpp`;
  loader surowych BF16; tokenizer/embedding/head z GGUF; `mtp_pack.py` do formatu silnika. Test parity: 1 token
  w PyTorch vs silnik (te same logits/top-1).
- **Format**: trenować w BF16/FP16, scalić LoRA, spakować q2_0 (albo q4_0) i **zmierzyć spakowany model** —
  kwantyzacja może zjeść zysk.
- **Nic nie instalujemy teraz**; wybór wariantu R/L i zgoda należą do użytkownika.

## 6. Ryzyka i szacowany czas

| ryzyko | wpływ | ograniczenie |
|---|---|---|
| dense-only/LoRA nie dosięgnie progu top-16 ≥75% | średni–wysoki | na wynajętym 80 GB od razu pełne eksperci (41,7 GB) |
| kwantyzacja q2_0 zjada zysk | średni | mierzyć po `mtp_pack.py`; q4_0 albo dense BF16 |
| publiczne/syntetyczne dane nie pokryją realnego miksu | średni | klasy z produkcji + opcjonalny ruch później, za zgodą |
| format/loader MTP (31 tensorów) | średni | `mtp_pack.py` + test parity; zmiany architektury = loader |
| koszt/dostępność wynajętego GPU | średni | 1–2 dni na pełny run; budżet na 3–5 runów |
| upload 20,5 GB/mln tokenów | niski | publiczne dane; kompresja/FP8; 1 Gb/s ~3 min/M |
| prywatność (tylko opcjonalny ruch) | wysoki | publiczne/syntetyczne domyślnie; ruch lokalnie, szyfrowanie, redakcja |
| czas/niepewność | wysoki | gate offline po fazie 0/1; stop, jeśli nie przejdzie |

**Szacowany czas (part-time, wynajęty 80 GB):**

- Faza 0: hook dump + 1 mln tokenów publicznych/syntetycznych + implementacja MTP w PyTorch + parity — **1,5–2 tygodnie**.
- Faza 1: pełne eksperci (2,607 mld) na A100/H100 80 GB, 1–3 mln tokenów, **1–2 dni/run**, 3–5 runów — **1 tydzień**.
  (Opcja budżetowa: dense-only/LoRA na lokalnym 24 GB, 2–12 h/run, 1 tydzień — ale może nie dosięgnąć progu.)
- Faza 2: pack q2_0/q4_0, offline top-K na spakowanym, A/B 3 pary — **3–5 dni**.
- **Razem 3–4 tygodnie** (z wynajmem); pierwsza decyzja go/no-go po fazie 0, druga po top-K na spakowanym modelu.

**Czego ta nota nie obiecuje:** że publiczne/syntetyczne dane wystarczą do +10% na prawdziwym ruchu. Sufit jest
wysoki (main head 95,7% @16), ale trenowalna część i kwantyzacja mogą ograniczyć zysk; dlatego gate jest po
fazie 0/1, a nie po całości.

## 7. Decyzja

- **Trzecie ramię zmierzone:** +1,47% średnio w 4 parach, polski techniczny +11%, ale repeat/math tracą i JSON
  jest bimodalny. **Globally za mało** (próg 3%), więc przechodzimy do treningu na wynajętym GPU z danymi
  publicznymi i syntetycznymi.
- **Nic nie instaluję i nie trenuję bez zgody.** Pierwszy krok to hook `STRATA_MTP_DUMP` + 1 mln tokenów
  publicznych/syntetycznych + PyTorch parity, bez ruszania produkcji.
- Po top-K gate (top-16 @d0 ≥75%, PL akceptacja ≥85%, EN/JSON regresja ≤2 pkt) decydujemy, czy wynajmować
  80 GB i iść w pełne eksperci, czy wystarczy dense-only/LoRA.
- Jeśli użytkownik chce najpierw tańszy test bez wynajmu: dense-only na lokalnym 24 GB (Faza 1A) — ale wynik
  może być poniżej progu; to tylko pre-test.
