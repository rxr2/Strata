# Profilowanie RX 7900 XTX pod Stratą — stan 2026-11-02

Tor A (akceptacja szkicu) i Tor B (cache ekspertów). Wszystkie liczby są zmierzone na tej maszynie, chyba że
zaznaczono „hipoteza”. Kod i komentarze po angielsku, raport po polsku.

## 0. Wnioski w pięciu zdaniach

1. **Trzy własne ślady** (profiler, produkcja): p1 81,8 / 82,1 / 90,4 tok/s, p2 83,8 / 84,5 / 82,2, p3 66,2 / 67,0 / 64,4.
   Okno trwa 25,4–29,5 ms, akceptuje 1,69–2,48 tokenu; trafienia cache 78,8–87,4%. Bez profilera produkcja daje ~94 tok/s
   (99,9 / 107,2 / 75,4 z wcześniejszego przebiegu); profiler kosztuje 13–22% (p1 ~15%, p2 do 22%, p3 ~13%).
2. **Przerwy między kernelami to sprzętowe dno, nie software.** Pusty, zależny kernel w grafie i w strumieniu kosztuje
   **2,5–3,2 µs** (200 węzłów = 0,51 ms), a żadna z testowanych zmiennych ROCm (`AMD_DIRECT_DISPATCH`, `GPU_MAX_HW_QUEUES`,
   `HIP_FORCE_DEV_KERNARG`, `AMD_OPT_FLUSH`, `GPU_MAX_COMMAND_BUFFERS`) tego nie obniża. 3,6 µs w śladzie = dno + narzut
   profilera. Jedyny lewar to mniej węzłów; 100 węzłów mniej to ~0,25–0,3 ms/token (2–2,5%) tylko wtedy, gdy GPU nie czeka
   już na CPU (wcześniejsze fuzje 40–90 węzłów dały ~0).
3. **Tor A: 0,85–0,90 to plateau.** Obniżanie `spec_min_p` zwiększa tokeny/okno, ale okno drożeje prawie tyle samo:
   0,85→0,75 daje +5,2% tok/okno i +4,1% czasu okna (≈ +1% tok/s, szum), 0,65→0,55 daje +1,1% tok/okno i +6,5% czasu
   okna (−3,5% tok/s). Krańcowy koszt tokenu rośnie z 8,6 ms (0,85→0,75) do 65 ms (0,65→0,55) — dodatkowe wiersze są
   prawie wszystkie odrzucane i nie ma z czego amortyzować.
4. **Tor B: +1 punkt trafień nie przekłada się na tok/s.** Rezerwa 2560 MiB dała +0,81 pkt trafień i −0,5% tok/s;
   `--kv q4_0` +1,57 pkt i −3,2%; `--adapt-decay 0.9` +0,83 pkt i −0,6%. Przeprofilowanie (`--expert-profile-save`)
   zmieniło 40% par (59,6% wspólnych), ale dało **−0,9 pkt** trafień i −3,1% tok/s (szum), więc produkcyjnego profilu nie ruszamy.
5. **Prawdziwy lewar to akceptacja przy stałej liczbie wierszy**, a nie szersze okno ani kilka slotów cache. Przy 99,5%
   akceptacji (tabela produkcji, 175 tok/s) ten sam wiersz daje ~1 token zamiast ~0,3; przy 84,5% i 62 tys. tokenów
   spadek do 85 tok/s wynika z akceptacji i kontekstu, nie z trafień (79% + 2% PCIe vs nasze 78% + 2% przy 46,7 tys.).
   To wymaga lepszego draftu (MTP / polski head), nie kolejnego przełącznika. **Pomiar sufitu (CEILING-ds-mtp.md):**
   przy pierwszym odrzuceniu token targetu jest w top-16 głównego headu w 95,7% przypadków, a w top-16 headu MTP
   tylko w 31,5%; to head jest wąskim gardłem, nie target. Samo dodanie polskich tokenów do draft-vocabu nie pomogło
   (średnia tok/s bez zmian), więc potrzebny jest trening wag headu, nie szerszy vocab.

## 1. Stanowisko i metoda

- GPU: RX 7900 XTX, gfx1100, 96 CU, 24 GB, VRAM 2754 MHz; ROCm TheRock 10.1.0 (`~/opt/rocm-10.1.0`), HIP 7.16.
- Silnik: produkcja `~/llm/strata/strata` (0.1.52), konfiguracja `~/llm/strata/strata-rx.json` **niezmieniona**
  (SHA-256 `97a10dbd…`, mtime 2026-11-01 22:29). Fork: `~/Projekty/strata-rx7900`, gałąź `block-fuse` (cc21cbf4);
  eksperymenty na worktree `~/Projekty/strata-rx7900-ds`, gałąź `rx-ds-profile`.
- Ślady: 3 × `pipeline/trace_run.sh prof-base-N EXE=prod` (p1/p2/p3, 320 tokenów, greedy, seed 7), rocprofv3
  `--kernel-trace`. Katalogi: `~/rx-perf-lab/pipeline/20261102-102416-prof-base-1`, `…-102708-…-2`, `…-103000-…-3`.
- Matryce: 10 klas promptów (`pipeline/suite_prompts.json`) × warianty, 3 powtórzenia, na żywym silniku lub na
  świeżym silniku tymczasowym; `strata_tune` w ciele żądania ustawia `spec_min_p` i `pcie_frac` **per request**
  (bez restartu, bez zmiany configu). Katalogi: `~/rx-perf-lab/suite/…`.
- Trafienia per warstwa: diagnostyczny `STRATA_HIT_STATS=1` (gałąź `rx-ds-profile`, commit `cbe4a12e`, domyślnie
  wyłączony) — zlicza wpisy routingu na warstwę w trzech torach: VRAM, PCIe/peer, CPU.
- Prefill: `rx-tools/bench-detached.sh prefill-ds prefill EXE=prod` (12K/32K/64K po 2 powtórzenia).
- Szum: pojedynczy przebieg 3–4%; pod profilerem ~2%. Wszystkie porównania min. 3 powtórzenia; różnice <3% uznaję
  za szum, chyba że powtarzają się w kilku klasach.

## 2. Pełny profil obecnego stanu (3 powtórzenia)

### 2.1 Token, okno, trafienia

| przebieg | p1 tok/s | p2 tok/s | p3 tok/s | p1 okno/T/tok-win | p2 | p3 | trafienia p1/p2/p3 |
|---|---|---|---|---|---|---|---|
| prof-base-1 | 81,8 | 83,8 | 66,2 | 26,44 ms / 2,39 / 2,16 | 28,71 / 2,79 / 2,41 | 25,84 / 1,91 / 1,71 | 87,4 / 84,6 / 78,9% |
| prof-base-2 | 82,1 | 84,5 | 67,0 | 26,51 / 2,42 / 2,18 | 28,04 / 2,75 / 2,37 | 25,39 / 1,91 / 1,70 | 86,9 / 85,0 / 78,9% |
| prof-base-3 | 90,4 | 82,2 | 64,4 | 27,43 / 2,67 / 2,48 | 29,49 / 2,82 / 2,42 | 26,30 / 1,90 / 1,69 | 87,1 / 84,9 / 78,8% |
| **średnia** | **84,8** | **83,5** | **65,9** | **26,8 / 2,49 / 2,27** | **28,8 / 2,79 / 2,40** | **25,8 / 1,91 / 1,70** | **87,1 / 84,8 / 78,9%** |

Bez profilera (pomiar z 01:55–02:09, ta sama konfiguracja): 99,9 / 107,2 / 75,4 tok/s, średnia 94,2. Profiler zjada
13–22% (najwięcej p2); podział etapów jest z profilera, więc bezwzględne µs są zawyżone. **Wszystkie decyzje o zyskach podejmuję z NOPROF**, ślad służy tylko do podziału.

Czas okna prawie nie zależy od promptu (25,4–29,5 ms), ale **rośnie z liczbą wierszy T**: p3 (T=1,91) 25,8 ms,
p1 (T=2,49) 26,8 ms, p2 (T=2,79) 28,8 ms. To jest ilościowy sens „okno jest prawie stałe”: stały jest narzut
na okno (~19–20 ms), a każdy wiersz dokłada ~3–5 ms (cały forward przez 48 warstw).

### 2.2 Etapy (prof-base-1, µs/token; kernel + przerwa przed nim)

| etap | p1 | % | p2 | % | p3 | % |
|---|---|---|---|---|---|---|
| macierze gęste (projekcje, shared, głowa) | 3807 | 31,0 | 3790 | 30,4 | 4703 | 30,4 |
| eksperty z VRAM | 2988 | 24,4 | 3164 | 25,4 | 3734 | 24,1 |
| czekanie na eksperty z CPU (wait/copy rows) | 1975 | 16,1 | 2054 | 16,5 | 2698 | 17,4 |
| HC (`gr_down` + `gr_up`) | 1361 | 11,1 | 1355 | 10,9 | 1687 | 10,9 |
| uwaga QSA | 669 | 5,5 | 648 | 5,2 | 846 | 5,5 |
| GDN | 379 | 3,1 | 378 | 3,0 | 470 | 3,0 |
| router + plan | 391 | 3,2 | 377 | 3,0 | 494 | 3,2 |
| sampler + logity | 165 | 1,3 | 164 | 1,3 | 210 | 1,4 |
| start okna | 72 | 0,6 | 70 | 0,6 | 90 | 0,6 |
| **razem** | **12267** | | **12447** | | **15491** | |

Bilans GPU (µs/token): p1 = praca 7618 + przerwy 2953 + wiersze PCIe 987 + spin na puli 582 + host 133.
p2 = 7855 + 2809 + 1183 + 484 + 121. p3 = 9320 + 3854 + 1483 + 679 + 162. Przerwy to 24–25% czasu, ale mieszczą
się w sprzętowym dnie (patrz §5).

Największe kernele p1 (na token): `native_mmvq_multi` 80 wywołań / 1624 µs, `native_gu_fused` 20,4 / 782,
`copy_rows_from_mapped` 20,4 / 740, `native_down_lds` 20,4 / 589, `gr_up_q8_q32` 40,8 / 528, `fetch_blobs` 20,4 / 557,
`native_q6_k_mmvq` 15,8 / 543, `gr_down_q8` 40,8 / 405, `wait_copy_i32` 20,4 / 441, `native_small_mmvq` 23,4 / 292.
Suma tych dziesięciu to ~6,5 ms z 12,3 ms.

„Kto na kogo czeka” (p1, µs/token):
- GPU czeka na plan ekspertów od hosta: **441** (z tego warstwa 0 ~710 µs/okno, warstwy ≥10 ~6 µs/okno).
- GPU czeka na wiersze CPU: **42** (pula prawie nigdy nie jest spóźniona); samo czytanie wierszy przez PCIe: **740**.
- GPU czeka na hosta między oknami: **133**; host czeka bezczynnie na GPU: **6719**; pula pracuje: **2898**.
- Host ma zapas (6,7 ms/token bezczynności), pula ma zapas (25% zajętości); wąskim gardłem nie jest ani host, ani pula,
  tylko zależności w grafie i akceptacja.

## 3. Tor A — akceptacja szkicu i ekonomia okna

### 3.1 Krzywa kosztu okna (matryca 4 progów, 10 klas × 3 powtórzenia, świeży silnik, ten sam profil)

| wariant | tok/s | T | tok/okno | ms/okno | ms/token | trafienia | zmiana tok/s |
|---|---|---|---|---|---|---|---|
| base 0,85 | 91,18 | 2,81 | 2,50 | 27,27 | 10,91 | 76,5% | — |
| 0,75 | 92,14 | 3,14 | 2,63 | 28,39 | 10,79 | 78,0% | +1,0% |
| 0,65 | 91,96 | 3,55 | 2,77 | 29,99 | 10,83 | 78,5% | +0,9% |
| 0,55 | 87,98 | 3,92 | 2,80 | 31,93 | 11,40 | 78,4% | −3,5% |

(Base w tej matrycy to 91,2 tok/s; w matrycy dźwigni z §4.3 ten sam zestaw dał 92,8 — inne przebiegi, szum 3–4%.)
Wszystkie trzy pierwsze warianty są w szumie (różnica ~1%, szum pojedynczej klasy 3–4%). **Próg 0,85 nie jest zły,
ale 0,65–0,75 jest co najwyżej o ~1% lepszy — poniżej progu opłacalności wdrożenia.**

Ekonomia krańcowa (ta sama matryca):

| krok | Δ ms/okno | Δ tok/okno | krańcowy ms/token | werdykt |
|---|---|---|---|---|
| 0,85→0,75 | +1,12 | +0,13 | **8,6 ms** | minimalnie opłacalny (średnia 10,9) |
| 0,75→0,65 | +1,60 | +0,14 | **11,4 ms** | neutralny |
| 0,65→0,55 | +1,94 | +0,03 | **64,7 ms** | bardzo zły — wiersze prawie wszystkie odrzucone |

To jest bezpośrednia odpowiedź na tezę „+10% tokenów/okno = +7–8% szybkości”: **nie zachodzi**, bo dodatkowe wiersze
nie są darmowe. Przy 0,85→0,65 tokenów/okno rośnie o 10,8%, ale okno o 10,0%; szybkość +0,9%. Zysk pojawia się tylko
wtedy, gdy dodatkowy wiersz jest **akceptowany** (99,5% przypadku), a nie gdy dokładamy niepewne drafty.

`--spec` nie był zmieniany: w matrycy T nie przekroczyło 4,87 przy `--spec 6`, więc sufit 6 nie wiąże. Większy `--spec`
nie zmieni okna przy progu 0,85, a przy niższym progu tylko zwiększy liczbę odrzucanych wierszy — ekonomia jest już
zmierzona powyżej.

Osobny przebieg od strony wysokiej (base 94,06 tok/s): **0,90 → 94,99 (+1,0%), 0,95 → 93,50 (−0,6%)**; T 2,61/2,44,
tok/win 2,40/2,30, ms/win 25,07/24,52. Czyli plateau 0,85–0,90, a 0,95 zaczyna ciąć zbyt wcześnie. Per klasa 0,90
pomaga polskiemu (travel +4,5%, tech +2,6%), SQL (+4,5%), file_edit (+3,8%), ale szkodzi prozie (−4,6%), code (−1,9%),
repeat (−3,4%) — to szum 3–4% na klasę; globalnie +1,0%.

### 3.2 Klasy wyjścia (base 0,85; średnia z 3 powtórzeń)

| klasa | tok/s | T | tok/okno | ms/okno | akceptacja draftu | trafienia | PCIe |
|---|---|---|---|---|---|---|---|
| SQL | 104,2 | 3,36 | 3,12 | 30,0 | 89,7% | 77,1% | 2,7% |
| math | 100,8 | 3,15 | 2,84 | 28,2 | 87,7% | 78,3% | 2,2% |
| repeat | 97,8 | 3,59 | 3,00 | 30,8 | 78,3% | 77,4% | 2,5% |
| code_py | 97,4 | 2,51 | 2,21 | 22,7 | 80,9% | 85,0% | 1,1% |
| JSON | 93,4 | 3,61 | 3,24 | 34,3 | 85,3% | 69,2% | 3,7% |
| summary | 92,9 | 2,92 | 2,56 | 27,6 | 84,2% | 76,4% | 2,5% |
| prose_en | 90,1 | 2,17 | 1,97 | 21,8 | 83,7% | 83,8% | 1,2% |
| file_edit | 84,1 | 3,06 | 2,81 | 33,7 | 88,2% | 62,6% | 4,5% |
| polish_tech | 76,3 | 1,86 | 1,64 | 21,5 | 74,7% | 79,2% | 1,5% |
| polish_travel | 74,8 | 1,86 | 1,65 | 22,1 | 76,5% | 75,9% | 1,7% |

Korelacje w tej samej matrycy: tok/s vs T **0,68**, vs akceptacja **0,66**, vs trafienia cache **0,33**. Czyli na
krótkim kontekście szybkość idzie za liczbą wierszy/akceptacją, a nie za trafieniami. Wysokie T (SQL, JSON, repeat)
amortyzuje stały narzut okna; niskie T (polski) płaci 13,1–13,4 ms/token przy 9,6–10,6 ms/token w SQL/JSON.

To rozróżnienie jest ważne: **między klasami** teza „więcej tokenów/okno = szybciej” jest prawdziwa (SQL/JSON mają
3,1–3,2 tok/okno i 93–104 tok/s przy 30–34 ms okna), ale **w obrębie jednej klasy** nie da się jej zrealizować samym
progiem — próg dokłada wiersze, a każdy kosztuje 3–5 ms, więc token/okno rośnie razem z czasem okna. Potrzebny jest
drafter, który zwiększa *akceptację* przy tym samym T.

### 3.3 Polski: dlaczego 1,6–1,7 tokenu na okno

- T=1,86, tok/okno 1,64–1,65, akceptacja 74,7–76,5% — drafter MTP jest po prostu mniej pewny w polskim.
- Obniżenie progu do 0,75 daje 76,2 tok/s (+1,9%) i T≈2,0; do 0,65 nic nie daje (74,8); do 0,55 +1,9% (76,2).
  Czyli **nie ma szerokiego okna do wygrania progiem**; dodatkowe drafty są w większości odrzucane.
- `--lookup-chain 1` (prompt-lookup) dał średnio **−1,0%**, w polskim −1,0% (travel) i −0,9% (tech). Sufiksowe drafty
  wchodzą tylko w 2–6 oknach na ~130 i nie zmieniają ekonomii; MTP już wypełnia okno.
- Wniosek: dla polskiego potrzebny jest **lepszy drafter** (osobny head / więcej danych PL), a nie zmiana progu.

### 3.4 Co dałoby 99,5% akceptacji

Przy T≈2,8 i 99,5% akceptacji okno 27 ms daje ~2,8 tokenu zamiast 2,5 → **+12% tok/s przy tym samym czasie okna**.
Do tego 98% trafień zamiast 87% skraca czekanie CPU. To jest cała różnica między 94 a 175 tok/s; nie wynika z kerneli.
Nasza matryca pokazuje, że próg 0,85 jest już blisko optimum *przy obecnym drafterze*; jedyna droga to podniesienie
akceptacji przy tym samym T (lepszy draft), albo skrócenie czasu okna (mniej węzłów — patrz §5).

## 4. Tor B — cache ekspertów

### 4.1 Trafienia per warstwa (świeży silnik, 10 klas, `STRATA_HIT_STATS=1`)

Zbiorczo po 10 klasach (48 warstw, każda tyle samo wpisów routingu — 23 970):

| warstwa | trafienia | sloty w profilu | warstwa | trafienia | sloty w profilu |
|---|---|---|---|---|---|
| **0** | **63,2%** | 217 | 15 | **81,0%** | 116 |
| 1 | 69,2% | 215 | 16 | 80,2% | 143 |
| 2 | 67,7% | 203 | 31 | 79,9% | 119 |
| 7 | 66,8% | 190 | 32 | 78,5% | 136 |
| 18 | 68,2% | 186 | 9 | 77,6% | 175 |
| 28 | 67,3% | 155 | 39 | 77,1% | 131 |
| 34 | 68,7% | 181 | 25 | 76,8% | 163 |

Najgorsze: 0, 7, 28, 2, 18, 34, 1, 22, 30, 21. Najlepsze: 15, 16, 31, 32, 9, 39, 25, 43, 44, 47.
Wszystkie 48 warstw (kolejność 0…47, %): 63 69 68 72 75 72 71 67 73 78 71 75 71 74 73 81 80 74 68 72 74 71 70 72
73 77 71 73 67 75 70 80 78 72 69 73 74 73 71 77 73 73 73 76 77 73 74 75.
**Liczba slotów nie tłumaczy trafień**: warstwa 0 ma najwięcej slotów (217) i najgorszy wynik (63%), a warstwa 15
ma najmniej (116) i najlepszy (81%). To różnica **różnorodności routingu** (layer 0 routuje najwięcej różnych ekspertów
na żądanie), a nie zaniedbanie alokacji. Profil już daje warstwie 0 maksimum; dalsze przesuwanie slotów z 15/16 do 0
dałoby w najlepszym razie ~0,1–0,5 pkt globalnie, bo każda warstwa to 1/48 wpisów.

Trafienia per klasa (ten sam przebieg, zimny start): prose 83,7%, code 82,5%, Polish travel 69,3%, file_edit 64,2%,
JSON 64,6%, repeat 76,1%, math 70,6%, SQL 72,3%, Polish tech 77,0%, summary 68,7%. Produkcja na krótkim kontekście
ma 87%, bo jest rozgrzana; nasz świeży silnik startuje z 73–76% i dogrzewa się w trakcie.

### 4.2 Przeprofilowanie na „prawdziwym” ruchu

- `--expert-profile-save` + `--expert-profile-save-every 0.1` na 10 klasach; wynik:
  `~/rx-perf-lab/profiles/20261102-ds/trained-suite.bin` (**osobny katalog, produkcja nietknięta**).
- Nowy profil: 40% par innych niż oryginał (4711/7903 = 59,6% wspólnych), ale **alokacja per warstwa identyczna** (±1 slot):
  nadal 217 dla warstwy 0 i 116 dla 15. Adaptacyjny tier sortuje najpierw rezydentów, więc odtwarza bieżącą rezydencję,
  a nie optymalizuje różnorodności.
- Pomiar A/B (ten sam silnik, ten sam zestaw, ta sama kolejność, oryginał vs nowy): trafienia **72,93% → 71,99%**
  (−0,9 pkt), tok/s 92,8 → 90,0 (−3,1%, szum). **Nie wdrażać.** Poprzedni skok 76→96 był najpewniej skutkiem
  dużo gorszego profilu startowego, a nie tego, że „każde przeprofilowanie pomaga”.

### 4.3 Dźwignie VRAM i adaptacji (świeży silnik, ten sam zestaw, 3 powtórzenia)

| wariant | sloty | VRAM cache | trafienia | tok/s | wniosek |
|---|---|---|---|---|---|
| base (reserve 3072) | 7903 | 14,99 GiB | 72,93% | 92,8 | referencja |
| `--vram-reserve-mib 2560` | 8144 | 15,44 GiB | 73,74% (+0,81) | 92,3 (−0,5%) | brak zysku; +241 slotów nie pomaga |
| `--kv q4_0` | 8015 | 15,20 GiB | 74,50% (+1,57) | 89,8 (−3,2%) | brak zysku + ryzyko jakości |
| `--adapt-decay 0.9` | 7933 | 15,04 GiB | 73,76% (+0,83) | 92,3 (−0,6%) | brak zysku |
| `STRATA_HC_REQ8=1` | — | — | — | — | **nie startuje** z `STRATA_HC_Q8=1`: „blk.0.hc_attn_down.weight is not a bf16 matrix”. HC_Q8 już trzyma HC w int8 (675 MiB), więc REQ8 nie uwalnia dodatkowego VRAM. |
| `--pcie-frac 0` (per request) | — | — | — | 87,45 (−6,2%) | za mało PCIe, pula nie nadąża |
| `--pcie-frac 0.4` | — | — | — | 89,36 (−4,2%) | za dużo PCIe |

Wspólny wzorzec: **+0,8–1,6 pkt trafień daje 0 do −3% tok/s**. Przy 73–87% trafień to nie jest już wąskie gardło;
wąskim gardłem jest czas okna i akceptacja. `--kv q4_0` dodatkowo zmienia tekst (KV q4), więc bez bramki KL nie ma
podstaw do wdrożenia; przy KL 0,01813 vs limit 0,0185 ryzyko jest zbyt duże.

### 4.4 Kontekst 46,7 tys. tokenów (walidacja tabeli produkcji)

Jedno żądanie na żywej produkcji: prompt 46 660 tokenów, prefill 2775 tok/s (16,8 s), decode **76,2 tok/s**,
61 tokenów, drafty 36/53 = **68%**, trafienia **78,2% + 2,2% PCIe**. Tabela użytkownika dla 62 tys.:
85 tok/s, akceptacja 84,5%, trafienia 79% + 2% PCIe. **Trafienia się zgadzają (78–79%); różnicę 76 vs 85 robi
akceptacja (68% vs 84,5%) i długość/kontekst**, nie cache. To potwierdza wniosek z §3: akceptacja jest lewarem.

## 5. Przerwy między kernelami i graf (hipoteza §7.1)

Mikrotest (`dflash2_launch_bench 200`, ten sam GPU, bez profilera):

| kształt | 1 blok | 64 bloki | 256 bloków | 1024 bloki |
|---|---|---|---|---|
| graf, 200 zależnych kerneli | 2,98–3,19 µs/kernel | 2,52 | 2,51 | 2,99 |
| strumień, 200 zależnych kerneli | 2,94 | 2,88 | 2,95 | 3,86 |
| jedno uruchomienie grafu (200 kerneli) | 0,51–0,52 ms | 0,51 | 0,51 | 0,66 |

Graf i strumień kosztują tyle samo; narzut **hipGraphLaunch** jest znikomy (0,51 ms na 200 węzłów = 2,55 µs/węzeł,
czyli cały koszt to zależność między węzłami, nie host). Zmienne ROCm: `AMD_DIRECT_DISPATCH=0/1` 3,22/3,22,
`GPU_MAX_HW_QUEUES=1/4` 3,31/3,24, `HIP_FORCE_DEV_KERNARG=1` 3,17, `AMD_OPT_FLUSH=1` 3,12,
`GPU_MAX_COMMAND_BUFFERS=4` 3,21 — **żadna nie obniża dna** (różnice ≤3%, w szumie).

W śladzie średnia przerwa 3,6 µs × 825 = 2953 µs/token. Dno 2,5–3,0 µs × 825 = 2,1–2,5 ms; nadwyżka to narzut
profilera: bez profilera token jest o ~1,4 ms krótszy (p1). **Nie ma tu 24% do odzyskania przez „lepsze uruchamianie”**;
jest ~0,5–0,9 ms/token (4–7%) tylko wtedy, gdyby każdy kernel zszedł do dna, a i tak część jest ukryta przez
oczekiwanie na CPU. 100 węzłów mniej = ~0,25–0,3 ms/token (2–2,5%) w idealnym przypadku; wcześniejsze fuzje
40–90 węzłów (FUSE_WAIT, QDEDUP, NORM_ROPE, LFUSE, PCIE_FUSE) dały 0–5%, bo GPU i tak czekał. Klastry do usunięcia:
240 węzłów/okno ścieżki PCIe (bezwarunkowe, `--pcie-frac 0` ich nie usuwa) i 192 węzły HC (wymagają bariery siatki —
zakazane). To temat zamknięty bez nowego, dużego kernela.

## 6. Prefill (osobny tor)

`bench-detached.sh prefill-ds prefill EXE=prod` (mediany z 2 powtórzeń, prompt z korpusu kodu):

| rozmiar | prefill tok/s | TTFT | odczyt z dysku |
|---|---|---|---|
| 12K | 2679 | 4,23 s | ~3,7–4,2 GB |
| 32K | 2951 | 11,17 s | ~10,4–13,7 GB |
| 64K | 3057 | 22,26 s | ~17,4–20,8 GB |

Łącznie **160,9 GB odczytu z dysku w 9 żądań** (średnio 17,9 GB/żądanie). Timing z `engine.log` pokazuje jednak,
że **prefill jest nadal ograniczony GPU**, nie dyskiem: GPU timeline = wall (10,83 s dla 35,2K, 17,65 s dla 62,8K,
20,72 s dla 67,4K), a host staging (z odczytami NVMe) prawie całkowicie się pod tym chowa. Widoczne okno kosztu
dysku to „waiting for each chunk”: 1,33 s (35K), 2,23 s (63K), 2,57 s (67K), czyli 6–12% wall. Przyczyną są
pożyczone sloty cache (1344) i brak kopii wywłaszczonych ekspertów w RAM (odczyt unbuffered, 2,5 GB/s).
`--prefill auto:24576` już to łagodzi. Dalszy zysk (hipoteza, nietestowany): nie pożyczać slotów bez kopii w RAM
albo trzymać wywłaszczone eksperty w RAM podczas prefillu; **górna granica ~2,5 s na 64K (~11%)**, nie 20–30%,
bo reszta odczytów jest ukryta pod GPU. To zmiana polityki cache, nie przełącznik.

## 7. Tabela celów (udział × realny zysk = maksimum; posortowana po zysk/wysiłek)

| cel | udział w tokenie | realny zysk | wysiłek | ryzyko | werdykt |
|---|---|---|---|---|---|
| Lepszy drafter (akceptacja 90→99% przy tym samym T) | cały token | **+10–15%** (z 94 do ~105); sufit main head: top-16 95,7% odrzuceń | duży (nowy head/trening) | jakość, tekst | jedyny duży lewar; pomiar sufitu w CEILING-ds-mtp.md |
| Próg `spec_min_p` 0,85→0,65–0,90 | okno | **±1%** (szum; 0,95 −0,6%) | mały | tekst/akceptacja | nie wdrażać teraz |
| Mniej węzłów grafu (fuzje) | 24% przerw | max 2–2,5%, zmierzone ~0 | duży | zawieszenia | nie; dno sprzętowe |
| Prefill: polityka lend/evict | prefill | hipoteza ≤~11% (2,5 s/64K) | średni | decode cache | osobny temat, wart pomiaru |
| +1 pkt trafień cache | 16% CPU | 0 do −0,5% (zmierzone) | mały | OOM | nie; nie jest gardłem |
| Przeprofilowanie profilu | trafienia | −0,9 pkt (zmierzone) | mały | overfit | nie; zostaw oryginał |
| `--kv q4_0` | KV/VRAM | −3,2% | mały | KL | nie |
| `--vram-reserve-mib 2560` | VRAM | −0,5% | mały | OOM | nie |
| `--pcie-frac` 0 / 0,4 | PCIe/CPU | −6,2% / −4,2% | mały | — | zostaw 0,2 |
| `STRATA_HC_REQ8` | VRAM | 0 (konflikt z HC_Q8) | — | — | nie |

## 8. Rekomendacja

**Wdrożyć:** nic z konfiguracji — żaden mierzony wariant nie przekroczył progu 3% i nie powtórzył się w 3 parach.
Produkcyjny `strata-rx.json` pozostaje bez zmian.

**Nie wdrażać:** `--kv q4_0`, `--vram-reserve-mib 2560`, `--adapt-decay 0.9`, nowy profil, `--pcie-frac 0/0.4`,
`--lookup-chain 1`, `STRATA_HC_REQ8` (konflikt), kolejne fuzje launchy.

**Następny krok o największym stosunku zysku do wysiłku:** poprawa akceptacji draftu przy stałym T.
Pomiar sufitu (`CEILING-ds-mtp.md`) rozstrzygnął, że **head MTP jest wąskim gardłem, a nie target**:
przy pierwszym odrzuceniu token targetu jest w top-16 głównego headu w 95,7%, a w top-16 MTP w 31,5%;
główny head odrzuca pierwszy draft 2,3× rzadziej. Samo rozszerzenie draft-vocabu o 2 591 polskich tokenów
nie zmieniło średniej (92,8→92,8) — liczą się wagi headu. Dlatego:
(a) fine-tune headu MTP na polskich hidden states (uzasadniony, cel +5–8% akceptacji PL);
(b) równolegle 3-pair A/B `STRATA_MTP_FULL_HEAD=1` (główny head jako drafter: jeden przebieg +2,3% średnio,
    PL +3,4/+7,2%, repeat +23,3%, ale JSON −10,4% i proza −4,7% — wymaga polityki per klasa);
(c) dopiero potem kerneli. Drugi temat: prefill i polityka lend/evict (~2,5 s/64K).

**Najtańszy eksperyment do rozstrzygnięcia przed (a):** klient (harness) może ustawiać `strata_tune.spec_min_p`
per typ zadania — API już to przyjmuje bez restartu. Z tabel per-klasa: coding/math/repeat 0,85–0,90, proza/JSON/SQL
0,65–0,90, polski techniczny 0,75–0,90. To potencjał +2–5% na mieszance, ale liczby per klasa mają 3 powtórzenia i szum
3–4%; **najpierw A/B na prawdziwym miksie, potem wdrożenie.** Nie zmieniać globalnego progu w configu.

## 9. Co dostarczono

- **Raport:** ten plik, `~/Projekty/coding-bench/ds-pipeline/REPORT-ds-profiling.md`.
- **Pomiar sufitu draftu:** `~/Projekty/coding-bench/ds-pipeline/CEILING-ds-mtp.md` (top-K headu MTP vs token
  zweryfikowany; subset 31,5% @16, główny head 95,7% @16 na pierwszym odrzuceniu).
- **Nota wykonalności treningu:** `~/Projekty/coding-bench/ds-pipeline/FEASIBILITY-ds-mtp-training.md`
  (parametry/pamięć 24 GB, zrzut 20,5 GB na 1 mln tokenów, dane publiczne/syntetyczne, gate top-K,
  PyTorch ROCm 7.1 5,86 GB lokalnie / CUDA ~3–4 GB na wynajętym 80 GB).
- **Trzecie ramię (słownik szkicu):** `~/Projekty/coding-bench/ds-pipeline/DRAFT-VOCAB-ds.md` — główny head
  ograniczony do draft-vocabu to już produkcja; PL-specific +1 272 tokeny dały +1,47% średnio w 4 parach,
  PL techniczny +11%, ale globalnie za mało (próg 3%) → plan treningu na wynajętym GPU.
- **Sweep rozmiaru słownika:** `~/Projekty/coding-bench/ds-pipeline/SWEEP-ds-vocab.md` — 106k/140k/180k/248k,
  3 bloki losowe, NOPROF: 140k +2,80% ±1,88, 180k +2,80% ±2,63, 248k +1,64% ±1,37; **q4 head: 140k/180k
  +6,75% ±3,5/4,2**, q4-248 +3,96% ±1,49; head Q6_K 246/320/405/561 µs, q4-248 373 µs; 140k najlepszy netto.
- **Tail skip:** `~/Projekty/coding-bench/ds-pipeline/REPORT-ds-tailskip.md` — `STRATA_ROUTE_TAIL_SKIP=7` pomija
  37% chybień; random A/B **+9,19% ±2,79** (3/3 bloki), PCIe rows −36..43%, CPU pool −34..38%; quality KL
  0,02177 ≤ 0,0235, ale top-1 **29/32 < 30/32**; q4-140+tail7 104,71 tok/s (single), pcie 0,30 98,32 (single),
  reserve 2048 gorszy. **Wdrożono 2026-11-02 zgodnie z instrukcją użytkownika:** tail=7 + q4-140 + q4 head
  (backup `strata-rx.json.bak-20261102-143040`); combined KL 0,01747 / top-1 29/32; smoke 3 promptów 99,07 śr.
  (+5,2% vs 94,2; p1 96,9, p2 112,7, p3 87,6).
- **Kod:** gałąź `rx-ds-profile` w `~/Projekty/strata-rx7900-ds`, commity `cbe4a12e` (`STRATA_HIT_STATS=1`) i
  `541df347` (`STRATA_MTP_TOPK=K`, sufitu draftu) — oba diagnostyczne, domyślnie wyłączone, zero wpływu na produkcję.
  Niczego nie wypchnięto.
- **Profil:** `~/rx-perf-lab/profiles/20261102-ds/trained-suite.bin` (osobny katalog; produkcja nietknięta).
- **Surowe dane:** ślady w `~/rx-perf-lab/pipeline/20261102-1024…-prof-base-1..3`; matryce i przebiegi w
  `~/rx-perf-lab/suite/`; prefill w `~/rx-perf-lab/experiments/fork/20261102-112207-prefill-ds/RESULT.txt`.
- **Skrypty odtwarzające:** `~/Projekty/coding-bench/ds-pipeline/tools/20261102/` (`suite_run.sh`, `live_matrix.py`,
  `live_matrix_spec.py`, `suite_analyze.py`, `profile_info.py`, `copy_rows_bench.cu`).

## 10. Ograniczenia i uczciwe zastrzeżenia

- Zestaw klas to 10 promptów × 192 tokeny; to nie jest rozkład prawdziwego ruchu. Per-klasa 3 powtórzenia, szum
  pojedynczej klasy 3–4%; różnice ~1% w matrycy progów są w szumie.
- Świeży silnik startuje z zimnym cache (73–76% trafień) i dogrzewa się; produkcja ma 87%. Wnioski o *kierunku*
  (więcej slotów nie daje tok/s) są spójne między rezerwą, KV i decay, ale bezwzględne tok/s są niższe niż produkcja.
- Tekst greedy zmieniał się między wariantami (nawet przy samym progu), bo zmiana T zmienia arytmetykę weryfikacji
  i rezydencję; dlatego porównuję tok/s end-to-end, a nie „ten sam tekst”. Bramka KL nie była potrzebna, bo żadna
  zmiana nie przeszła progu zysku.
- Profil per warstwa pochodzi z builda forka z diagnostyką; routing jest ten sam, ale fork może mieć inne fuzje.
  Liczby trafień są z tego samego builda dla wszystkich wariantów, więc porównania A/B są ważne.
- Prefill mierzony na korpusie kodu (nie na polskim); 12K/32K/64K to mediany z 2 powtórzeń, odczyty dysku z
  `drive_read_mb` (unbuffered, więc realne).
