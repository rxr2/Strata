# ZADANIE: pełne profilowanie RX 7900 XTX pod Stratą i plan dalszej optymalizacji (stan 2026-11-02)

Jesteś inżynierem wydajności GPU. Dostajesz silnik LLM Strata (HIP) działający na jednej karcie RX 7900 XTX. Po serii zmian
dekodowanie wzrosło z 75 do ~94 tok/s. Użytkownik uważa, że jest jeszcze zapas. Twoim zadaniem jest zrobić **pełne
profilowanie na obecnym stanie**, znaleźć, gdzie naprawdę jest zapas (z liczbami), i go zaatakować tam, gdzie zysk jest
największy i bezpieczny. Nie powtarzaj rzeczy z sekcji 6 ("co już sprawdzone"). Raport po polsku, kod i komentarze po angielsku.

## 0. PRIORYTET: akceptacja szkicu i trafienia w cache ekspertów są większą dźwignią niż kernele

Nowa obserwacja z produkcji (historia zapytań w panelu Straty i log `~/harness/strata-engine.log`, linie `strata serve: prompt ...`):

| Zapytanie | Dekodowanie | Akceptacja szkicu | Trafienia w VRAM + PCIe | Czas okna |
|---|---|---|---|---|
| 15 tys. tokenów, wyjście ucięte na 256 | **161-177 tok/s** | 214 z 215 (**99,5%**), ok. 6 tokenów na okno | 98,2-98,4% + 0,1% | ok. 36 ms |
| 30 tys. tokenów, jw. | **172-174 tok/s** | 99,5% | 98,2-98,4% + 0,1% | jw. |
| 62 tys. tokenów, odpowiedź naturalna (572 tokeny) | **85,5 tok/s** | 328 z 388 (84,5%) | **79,4% + 2% PCIe** | dłuższy kontekst |
| nasze 3 stałe prompty testowe | **94 tok/s** | ok. 2,3 tokenu na okno (p3: 1,6) | ok. 87% | ok. 25-30 ms |

Wniosek: czas jednego okna jest z grubsza stały (25-36 ms), więc **tok/s ~ tokenów na okno / czas okna**. Przy ~100% akceptacji i 98%
trafień silnik robi 175 tok/s, a przy 2,3 tokenu na okno ~94. Różnica 1,85x pochodzi z akceptacji i trafień, nie z kerneli. Kernele
zostawiły już tylko pojedyncze procenty (sekcja 6), a **poprawa tokenów na okno o 10% daje ~+7-8% tok/s od ręki**. Uwaga: "Limit wyjścia" w panelu
to wyjście ucięte limitem `max_tokens` (256), nie błąd; 174 tok/s dotyczy początku odpowiedzi, który bywa bardzo przewidywalny, więc to górna granica,
nie typowa wartość. Prefill na świeżych długich promptach wynosi teraz 3200-3550 tok/s (15 tys.: ~3520, 30 tys.: ~3555, 62 tys.: 3230).

Zacznij od tych dwóch torów, zanim ruszysz kernele:

**Tor A: akceptacja szkicu (tokenów na okno).**
1. Zmierz **rozkład**: ile tokenów na okno i jaka akceptacja dla różnych klas wyjścia (kod, edycja istniejącego pliku, proza angielska, polski,
   JSON/strukturalne, powtórzenia), nie tylko dla 3 stałych promptów. Dodaj 3-4 prompty klas, których brakuje (długi kontekst z edycją kodu, wyjście
   strukturalne, powtarzalne). `trace_run.sh` ma 3 stałe prompty w skrypcie: skopiuj go i podmień listę.
2. Zbuduj z tego **krzywą kosztu okna**: czas okna (z `stages.py`) w funkcji liczby wierszy T (1..7) i wyznacz optymalne T oraz próg odcięcia drafta. Sprawdź,
   czy stały próg `--spec-min-p 0.85` jest tu optymalny (wcześniej mierzono tylko 0.5: gorzej) i czy `--spec 6` vs `--spec 8` ma sens dla klas o wysokiej akceptacji.
3. Zbadaj, **dlaczego akceptacja jest niska** dla polskiego (1,6 tokenu na okno): jakość drafta MTP, tokenizacja, polityka odcięcia. Czy da się
   podnieść akceptację bez zmiany wyjścia (weryfikacja jest dokładna, więc wyjście greedy pozostaje takie samo).
**Tor B: trafienia w cache ekspertów.**
1. Zmierz trafienia **na warstwę i na klasę wyjścia** (log: `expert cache XX% hit (+Y% PCIe)` na zapytanie; host timeline w `stages.py` daje `vram_hits`
   i liczbę ekspertów CPU na warstwę). Zobacz, które warstwy chybiają najczęściej i czy to te same eksperty.
2. **Przekalibruj profil ekspertów na prawdziwym ruchu.** Obecny `original-expert-profile.bin` (`~/llm/Strata-data/autotune-20261015/profiles/`) pochodzi
   z wcześniejszej kalibracji i to ona dała dotąd największy skok (użytkownik: ~76 -> ~96 tok/s na prawdziwej pracy). Nowe przełączniki zmieniły koszty,
   a pracujemy głównie na zadaniach agentowych. Przeczytaj `~/llm/strata/source/tools/calibrate.py` i `collect_profile_traces.py`, zbierz profil z
   reprezentatywnych zapytań i sprawdź, czy wyższy hit rate daje szybszy tok. Kalibracja zmienia pliki produkcji: wyniki zapisuj w osobnym katalogu i NIE nadpisuj
   produkcyjnego profilu; do wdrożenia potrzebna jest zgoda użytkownika.
3. Sprawdź nieprzetestowane dźwignie VRAM: `STRATA_HC_REQ8=1` (wagi HC int8, zwalnia VRAM dla ekspertów, wymaga bramki jakości), `--kv q4_0`, niższe
   `--vram-reserve-mib` (teraz 3072), `--resident-budget-gib`, parametry adaptacji (`--adapt-decay`, `--adapt-swaps`).
Oba tory mierz na tych samych klasach wyjść; wynik liczysz w tok/s na klasę i w średniej ważonej klas (podaj, jak ważysz).

## 1. Sprzęt i środowisko

- **GPU:** AMD RX 7900 XTX, gfx1100 (RDNA3), wave32, 96 CU, 24 GB GDDR6, 96 MB Infinity Cache, pamięć podkręcona do 2754 MHz.
  Zmierzona przepustowość odczytu VRAM: ~1015 GB/s (dane gorące), ~645 GB/s (zimne, rotowane wagi).
- **PCIe 4.0 x16:** ~28,7 GB/s host->device (zmierzone). **CPU:** Ryzen 7 9800X3D (8 rdzeni / 16 wątków, Zen 5, AVX-512),
  59 GB RAM. Wątek hosta silnika na CPU 0, pula 7 wątków (eksperci na CPU) na CPU 1-7, bliźniaki SMT 8-15 prawie wolne.
- **Soft:** Ubuntu, ROCm "TheRock" 10.1.0 w `~/opt/rocm-10.1.0`. Silnik: binarka produkcyjna `~/llm/strata/strata`
  (Strata 0.1.52, release), nasz fork `~/Projekty/strata-rx7900` (HIP, gałąź bazowa `rx7900`, build `build-rx/strata`).
  Źródła: `src/core/verify.cpp` (okno weryfikacji, plan ekspertów, czekania), `src/core/mtp.cpp` (szkic MTP),
  `src/kernels/cuda/*.cu` (kernele HIP w składni CUDA), `src/kernels/cuda/native_mmvq.cu`, `iq_kernels.cu`, `fused_gr.cu`,
  `verify_kernels.cu`, `elementwise.cu`. Dokumenty: `docs/RX7900XTX.md`, `DETAILS.md`, `AMD_HIP.md` w forku.
- **Model:** Qwen3.8-Flash-Next-GSQ-RCO (abliterated) IQ3_S, MoE ~125B, **48 warstw (36 GDN + 12 QSA)**, 512 ekspertów na warstwę,
  top-10. Eksperci mieszani po warstwach: gate/up IQ2_S / IQ3_XXS / IQ3_S, down IQ4_NL (lub typ 42). Gęste: Q6_K, Q5_K, Q4_K,
  IQ4_XS, Q8_0, BF16. Hyper-connections (HC, `gr_down_q8` / `gr_up_q8_q32`) przy każdej połówce warstwy.
- **Co jest gdzie:** w VRAM jest cache 7882 ekspertów (14,95 GiB, trafienia ~87%), reszta w RAM (36 GiB zablokowane). Chybione
  eksperty liczy albo pula CPU (AVX-512), albo (20%, `--pcie-frac 0.20`) GPU czyta je przez PCIe (`fetch_blobs_kernel`).
  Spekulacja: drafter MTP, `--spec 6`, średnio 2,3 tokenu na okno (p3 polski 1,6).
- **Konfiguracja produkcji:** `~/llm/strata/strata-rx.json` (argumenty: `--spec 6 --pcie-frac 0.20 --pool-workers 7 --kv int8
  --max-context 200000 --expert-cache auto --vram-reserve-mib 3072 --resident-experts --resident-budget-gib 36 --prefill auto:24576`).
  Env produkcji: FUSE_WAIT, QFUSE_HC, ONE_TOKEN_COMMIT, FUSE_CONVAB, FUSE_HEAD_GR, QFUSE, MTP_HIP_PRIO, NORM_ROPE,
  VERIFY_QDEDUP, ADAPT_JOB_CPU=15 (wszystkie =1, ostatni =15) oraz STRATA_HC_Q8, HC_UPMIX, EXP_MODE=8, PF_GEMM, HIP_WMMA i inne.

## 2. Obecny profil (produkcja, 3 powtórzenia x 3 prompty, rocprofv3 --kernel-trace, `~/rx-perf-lab/pipeline/*final-prod-*`)

- **Czas na token (pod profilerem):** p1 opis 11,8 ms, p2 kod 12,3 ms, p3 polski 15,8 ms (średnia ~13,3 ms). Profiler kosztuje 13-16%
  tok/s. **Bez profilera: 99,9 / 107,2 / 75,4 tok/s (średnia 94,2).** Mediana z prawdziwej pracy w logach ~99,7 tok/s.
- **Podział na etapy (średnia p1-p3, % tokenu, czas kerneli + przerwy przed nimi):** macierze gęste **31,3%**, eksperty z VRAM **25,2%**,
  czekanie na eksperty z CPU **14,7%**, HC **11,2%**, uwaga QSA 5,5%, router 3,2%, GDN 3,1%, reszta ~6%.
- **Podział czasu GPU:** **63,5% GPU liczy, 24,1% stoi między kernelami (przerwy uruchomień), 7,8% czyta wiersze CPU przez PCIe,
  3,6% kręci się w pętli czekając na pulę CPU, 1,0% czeka na hosta między oknami.** ~790 kerneli na token (p1, p2), ~1110 (p3),
  średnia przerwa ~3,6 us. **Cały "postój" GPU to ~29% tokenu, z czego ~24 pkt to same przerwy między kernelami.**
- **Kernele (p1, na token):** `native_mmvq_multi_kernel` 80 wywołań, 1492 us, ~51% sufitu pasma (jedyny duży zapas wśród gęstych);
  `native_q6_k_mmvq` 85%, `native_small_mmvq` 94% (blisko sufitu). Eksperci z VRAM: `native_gu_fused` (mediana 26-33 us zależnie od typu),
  `native_down_lds<20>` 23 us, szacowane ~835-920 GB/s (80-90% sufitu). `fetch_blobs_kernel` ~540-730 us/token (22 wywołania, ścieżka PCIe,
  obsługuje ~1,3% ekspertów). `wait_copy_i32` (GPU czeka na plan ekspertów od hosta) ~600 us/token, głównie w warstwie 0 okna
  (~450 us/okno, w późnych warstwach ~6 us). HC (`gr_down` + `gr_up`) ~1,0-1,3 ms/token.
- **Prefill** (czytanie promptu, z logów): ~2000 tok/s (3-8 tys. tokenów), 2700-2850 tok/s (powyżej 8 tys.), szczyty 3500-3600.
  Prawdopodobnie ograniczony PCIe i RAM (14,9 z 46,8 GiB ekspertów w VRAM); nie był profilowany.

## 3. Jak do tego doszliśmy (skrót)

Pełny ślad okna -> tabela etapów -> sprawdzenie przełączników `STRATA_*` (658 w `ds-pipeline/kb/SWITCHES.md`) -> kod. Przełączniki dały +25%
(prod 75 -> 94). Kod: 4 sesje (host, PCIe, LFUSE, gęste kernele) nie dały użytecznego zysku (sekcja 6).

## 4. Narzędzia (wszystko istnieje i działa; katalog `~/Projekty/coding-bench/`)

- `pipeline/trace_run.sh NAZWA [KEY=VALUE ...] [EXE=prod|ścieżka] [NOPROF=1] [ARG--flaga=WARTOŚĆ]`: zatrzymuje produkcję, uruchamia silnik z
  konfiguracją produkcji + zmiany, wysyła 3 stałe prompty (p1 opis ring all-reduce, p2 kod LRU cache, p3 polski poradnik, greedy, seed 7, 320
  tokenów), zapisuje `~/rx-perf-lab/pipeline/<czas>-NAZWA/{p1,p2,p3}/` i **zawsze przywraca produkcję**. `NOPROF=1`: bez profilera, tylko tok/s
  (to ono decyduje). Bez NOPROF: ślad `trace.db` + `pN/cpu.json` (obciążenie rdzeni i wątków).
- `pipeline/pipeline_map.py RUN/pN` (kernel po kernelu, rejestry, LDS) i `pipeline_map.py A/pN B/pN` (różnica A/B na token),
  `pipeline/stages.py RUN/pN` (etapy, bilans warstwa po warstwie `balance`, ścieżka krytyczna `critical`, wykorzystanie `util`),
  `pipeline/rep_table.py`. Panel (tylko odczyt): http://127.0.0.1:8792/ (schemat potoku, postoje, bilans warstw, ścieżka krytyczna, rdzenie CPU).
- Jakość: `~/Projekty/strata-rx7900/rx-tools/bench-detached.sh NAZWA quality KEY=VALUE` (KL pierwszego tokenu względem FP16 na 32 promptach).
  **Bramka: KL <= 0,0185 i top-1 >= 31/32** (baza: KL 0,01813, 31/32). Dla zmian bitowo identycznych tekst greedy ma być taki sam.
- Prefill: `rx-tools/bench-detached.sh NAZWA prefill` (12K / 32K / 64K).
- Stanowisko do pojedynczego kernela: `~/Projekty/coding-bench/dense/` (harness z poprawnością bitową i zimnym pomiarem, wzorzec do kopiowania).
- Wiedza: `ds-pipeline/loop/knowledge.md`, `ds-pipeline/REPORT-ds-pro.md` (stary raport, część nieaktualna), `ds-pipeline/kb/SWITCHES.md`.

## 5. Zasady pomiaru (nauczone na błędach, bezwzględne)

1. **Profiler zniekształca**: `AUX_CPUS` dawał -9% pod profilerem i -0,5% bez. Zysk liczysz z `NOPROF=1`, profiler służy do diagnozy.
2. **Szum jednego przebiegu bez profilera to 3-4%** (ta sama konfiguracja: 90-97 tok/s), pod profilerem ~2%. Każde porównanie: **min. 3 pary
   naprzemiennie (baza, wariant, baza, ...)**, na tym samym buildzie. Zysk liczy się dopiero powyżej ~3% i gdy się powtórzy.
3. Przebieg **zakłócony z zewnątrz** (przerwy między kernelami >30% dłuższe przy tej samej pracy kerneli) powtórz.
4. Eksperymenty z kodem tylko za przełącznikiem `STRATA_...` (domyślnie WYŁĄCZONYM), na własnym drzewie roboczym:
   `git -C ~/Projekty/strata-rx7900 worktree add ~/Projekty/strata-rx7900-ds -b rx-ds-profile`; build przez `rx-tools/build.sh`.
5. **GPU**: każda praca na GPU tylko przez `flock ~/Projekty/coding-bench/.grade.lock <polecenie>`, jedna naraz. Nigdy nie zostawiaj
   produkcji zatrzymanej. Procesy zabijaj po pid, nigdy szerokim `pkill -f`.
6. **ZABRONIONE** (zawiesiło GPU, wymagało twardego restartu): spin-wait na pamięci globalnej zapisywanej przez inny blok/kernel, bariery siatki,
   cooperative launch. Nowy kernel/strumień testuj najpierw z krótkim timeoutem.
7. **Nie zmieniaj** `~/llm/strata/strata-rx.json` ani binarki produkcyjnej (wymaga kopii i zgody użytkownika). Nic nie wypychaj do żadnego zdalnego
   repozytorium. Żadnych sekretów w plikach.

## 6. Co już sprawdzone (NIE powtarzaj; wyniki bez profilera)

Wdrożone i działa: QFUSE, MTP_HIP_PRIO, NORM_ROPE+VERIFY_QDEDUP, ADAPT_JOB_CPU=15 (+25% razem z wcześniejszymi pięcioma).
Bez efektu lub gorsze: `AUX_CPUS=9-14` (-0,5%), `--adapt-every 2`, `--adapt-swaps 48`, `--lookup-chain 2` (gorzej), `--spec-min-p 0.5` (+7% czasu),
`HOST_CORE=sibling` (+16% czasu), `SPEC_COST` (szum), `FUSE_HITS`, `DF_PLE`, `STRATA_ENGINE_NICE` (nie jest czytany),
`HOST_EARLY` (host nie jest wąskim gardłem bez profilera, +1,2%), `LFUSE_ANY` (43 uruchomienia mniej, czas w szumie),
`PCIE_FUSE` (~0), `PCIE_SIDE` (boczny strumień dla `fetch_blobs`: **-20%**, przyczyna niewyjaśniona), `DENSE_CAND` (kernel wieloskolumnowy
z pętli DeepSeeka, bitowo identyczny, w silniku ~+1%). HC obu połówek w jednym launchu odpada (wymaga bariery siatki). Kernele ekspertów z VRAM
są już na 80-90% sufitu pasma, więc technika "rozwinięcia znaków" z projektu Maya nic tu nie da.

## 7. Gdzie jeszcze może być zapas (hipotezy do zmierzenia, od najbardziej obiecujących)

1. **Przerwy między kernelami (24% tokenu, ~790 x 3,6 us).** Sprawdź, czy 3,6 us to koszt węzła grafu HIP (graf okna ma ~3000 węzłów) i czy da się go
   obniżyć: warianty uruchamiania (strumienie zamiast grafu dla niektórych odcinków, kolejność/rozmiar grafu, zmienne środowiskowe uruchamiania w tym ROCm
   - zweryfikuj, że istnieją w ROCm 10.1.0, np. dotyczące argumentów kernela w pamięci urządzenia, liczby kolejek sprzętowych, serializacji), albo
   połączyć po kilka małych kerneli jednej połówki FFN (router + plan + shared expert + combine + normy) w mniej uruchomień. Zmierz najpierw, ile kosztuje
   jeden pusty węzeł grafu w tym środowisku (mikro-test), żeby wiedzieć, ile można maksymalnie odzyskać.
2. **Czekanie na eksperty z CPU + PCIe (14,7% + 7,8%)**: poprawa trafień w cache ekspertów (obecnie 87%; ok. +1% trafień = ~-1,2% tokenu wg wcześniejszego
   szacunku): `STRATA_HC_REQ8=1` (wagi HC int8, ~0,56x bajtów), `--kv q4_0` (mniej VRAM na KV), `--vram-reserve-mib` niżej niż 3072, `--resident-budget-gib`,
   `--adapt-decay`; to NIE było mierzone (wymaga bramki jakości przy HC_REQ8 i KV). Zmierz też rozkład: ile chybień przypada na które warstwy.
3. **Szerokość okna / akceptacja spekulacji**: tokenów na okno 2,3 (p3 1,6). Każdy koszt stały okna dzieli się przez tę liczbę. Sprawdź `--spec 8`,
   alternatywne progi, drafter dla polskiego (prompt-lookup był gorszy, ale sprawdź przyczynę).
4. **Eksperci z VRAM (25%)**: kernele są blisko sufitu, ale sprawdź liczbę uruchomień i to, czy `native_gu_fused` + `native_down_lds` + `combine` można
   połączyć w jedno uruchomienie na warstwę bez zmiany sum.
5. **PCIe**: `fetch_blobs` ~540-730 us/token dla ~1,3% ekspertów to nieproporcjonalnie dużo; ustal przyczynę (wąskie wywołanie? synchronizacja? kolejka kopii?)
   i dlaczego boczny strumień dał -20% (to samo okno, więc kolizja z czymś: DMA, kolejki, pamięć zablokowana). Jeśli da się to tanio zdiagnozować, zrób.
6. **Prefill** (osobny tor, po dekodowaniu): zrób ten sam pomiar etapów dla promptu 12K/32K (ślad GPU, PCIe, RAM), potwierdź hipotezę, że ogranicza go PCIe/RAM.

## 8. Co dostarczyć

1. **Raport `REPORT-ds-profiling.md`** (po polsku) w katalogu `~/Projekty/coding-bench/ds-pipeline/`: (a) Twój własny pełny profil obecnego stanu z liczbami (3 powtórzenia),
   z mapą "czas -> kto czeka na kogo"; (b) tabela celów: udział w tokenie x realnie osiągalne przyspieszenie = maksymalny zysk, wysiłek, ryzyko, posortowana
   po zysku/wysiłku; (c) wyniki każdego eksperymentu A/B (tok/s bez profilera, 3 pary, tekst identyczny lub KL/top-1); (d) rekomendacja: co wdrożyć, czego nie.
2. **Kod** tylko jako gałąź `rx-ds-profile` z przełącznikami domyślnie wyłączonymi; commit z opisem. Nic na produkcję.
3. Mów wprost, jeśli cel daje kilka procent albo mniej; nie przesadzaj z szacunkami; rozróżniaj fakt zmierzony od hipotezy.

## 9. Budżet i wyjście awaryjne

Maks. ~30 przebiegów GPU (każdy ~3-4 min pod blokadą) i ~40 prób kodu. Po 3 nieudanych próbach tego samego podejścia (brak poprawy, błędy budowania,
odrzucenie przez straż bezpieczeństwa) **zatrzymaj się i opisz blokadę**: wtedy dalej koduje Claude (układ: Ty piszesz kod, Claude projektuje, recenzuje i przejmuje,
gdy utkniesz). **Kolejność: najpierw sekcja 0 (tory A i B: akceptacja szkicu, trafienia w cache, kalibracja profilu), potem sekcja 7 punkt 1 (przerwy między
kernelami).** Sekcja 7 punkty 2 i 3 pokrywają się z sekcją 0, więc robisz je tam.
