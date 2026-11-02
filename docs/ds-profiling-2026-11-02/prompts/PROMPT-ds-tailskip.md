# ZADANIE DLA DEEPSEEKA: A/B `STRATA_ROUTE_TAIL_SKIP` na RX 7900 XTX (po sweepie słownika q4)

Kontekst w skrócie: Strata (HIP) na RX 7900 XTX (gfx1100, 24 GB, 2 monitory na tej karcie), Ryzen 9800X3D, model Qwen3.8-Flash-Next IQ3_S (MoE,
48 warstw, 512 ekspertów, top-10). W VRAM mieści się ok. 32% ekspertów (7882 z 24576, trafienia ~87%), reszta w RAM: liczy je pula CPU
(7 wątków) albo (20%, `--pcie-frac 0.20`) czyta GPU przez PCIe. Dekodowanie: ~94 tok/s na testowych promptach (produkcja, bez profilera),
czekanie na eksperty z CPU to ~15% tokenu, wiersze CPU przez PCIe ~8%. Produkcja to binarka release `~/llm/strata/strata` (0.1.52) z konfiguracją
`~/llm/strata/strata-rx.json` (QFUSE, MTP_HIP_PRIO, NORM_ROPE, VERIFY_QDEDUP, ADAPT_JOB_CPU=15 i pięć wcześniejszych fuzji). Pełny kontekst:
`ds-pipeline/PROMPT-ds-profiling.md`, `ds-pipeline/KNOWLEDGE.md`, `REPORT-ds-profiling.md`. Raport po polsku, kod i komentarze po angielsku.

## 1. Co sprawdzamy i dlaczego

`STRATA_ROUTE_TAIL_SKIP=R` (R=7): chybiony ekspert (nie ma go w VRAM), którego **każdy token okna weryfikacji** wybiera tylko na pozycji >= R z top-10
(najmniejsze wagi), **nie jest ani kopiowany przez PCIe, ani liczony na CPU**; jego wkład to zero, bez renormalizacji. Mniej pracy CPU i PCIe, czyli
mniej czekania GPU na pulę. Odpowiednie miejsca w kodzie (do czytania, nie edycji): `src/core/expert_source.cpp` (`tail_skip_rank()`, ~4796-4930,
5109), `src/program/generate.cpp` (~11043-11090: domyślne włączenie tylko na CUDA i HIP gfx1200/gfx1201 oraz warunki `STRATA_TAIL_SKIP_MAX_CACHED`),
dokumentacja `strata/docs/DETAILS.md` (wiersz `STRATA_ROUTE_TAIL_SKIP`). Dokumentacja Straty: **IQ3_S +6..15% przy 44-52% ekspertów w cache**
(2x R9700), KL ok. +0,003..0,006, spadek akceptacji szkicu; testów na RX 7000 maintainerzy nie mają. U nas na gfx1100 jest **wyłączone domyślnie**,
ale jawnie ustawiona zmienna jest czytana przez `tail_skip_rank()` bez warunku architektury. Projekt Avalon (llama.cpp) używa tej samej reguły z domyślnym progiem 7.

## 2. Zadanie (kolejność obowiązuje)

**A. Weryfikacja, że działa.** Uruchom silnik z `STRATA_ROUTE_TAIL_SKIP=7` i potwierdź w logu: linia `STRATA_ROUTE_TAIL_SKIP=7 is ON` przy starcie i licznik
`route tail skip: N missed experts skipped (M entries) since the start` rośnie. Zapisz, jaką część chybień pomija (stosunek do wszystkich chybień).

**B. A/B szybkości.** Baza (produkcyjna konfiguracja, bez zmiennej) kontra `STRATA_ROUTE_TAIL_SKIP=7`, **3 pary, losowa kolejność, NOPROF**, ten sam zestaw 10 klas
i ten sam runner co w sweepie słownika (`~/rx-perf-lab/suite`, `ds-pipeline/SWEEP-ds-vocab.md`), binarka produkcyjna (`EXE=prod`, nie fork). Mierz: tok/s na klasę
i średnio (z szumem par), **tokeny na okno i akceptację szkicu** (tail skip może je obniżać), liczbę pominiętych ekspertów. Jedna para **z profilerem**
(`pipeline/trace_run.sh NAZWA EXE=prod [STRATA_ROUTE_TAIL_SKIP=7]`, potem `pipeline/stages.py RUN/pN`): ile spadły etapy „czekanie na eksperty z CPU”
i wiersze PCIe, oraz czas okna.

**C. Bramka jakości.** `~/Projekty/strata-rx7900/rx-tools/bench-detached.sh NAZWA quality STRATA_ROUTE_TAIL_SKIP=7` (KL pierwszego tokenu względem FP16
na 32 promptach, top-1, zadania agentowe). Baza: **KL 0,01813, top-1 31/32**. Oczekiwany koszt jakości ok. +0,003..0,006 KL. Raportuj liczby i oceń,
czy przekracza KL 0,0235 albo top-1 < 30/32; **decyzję o akceptacji kompromisu jakości podejmuje użytkownik**. Dodaj porównanie tekstu greedy bazy
i wariantu dla klas kod/JSON/edycja (czy odpowiedzi różnią się merytorycznie, nie tylko słowami).

**D. Jeśli zysk >= 3% powtarzalnie (3 pary):** (1) próg R=6 i R=8 (jedna para każdy), żeby znaleźć kompromis zysk/jakość; (2) ponowny sweep `--pcie-frac`
(0,10; 0,20; 0,30), bo przy mniejszej liczbie chybień optymalny udział PCIe może się przesunąć (jawnie `ARG--pcie-frac=` w `trace_run.sh`);
(3) jedna para z najlepszym słownikiem szkicu z twojego sweepu (140k lub 180k q4) i `TAIL_SKIP=7` razem, żeby sprawdzić, czy zyski się sumują;
(4) jedna para z `--vram-reserve-mib 2048` zamiast 3072 (**uwaga: na tej karcie są 2 monitory, nie schodź poniżej 1500**, sprawdź w `amd-smi`, ile VRAM zajmuje pulpit).

**E. Jeśli zysk < 3% albo jakość nie do przyjęcia:** powiedz to wprost z liczbami i zatrzymaj się; nie szukaj na siłę innych wariantów.

## 3. Zasady (bezwzględne)

1. Wynik liczysz z **NOPROF** (profiler zniekształca: `AUX_CPUS` dawał -9% pod nim, -0,5% bez). Szum jednej pary ~2-3%, zysk dopiero powyżej ~3% i powtarzalny.
2. Każda praca na GPU tylko pod `flock ~/Projekty/coding-bench/.grade.lock <polecenie>`, jedna naraz. Produkcję zatrzymuje i przywraca `trace_run.sh`; nie zostawiaj jej zatrzymanej.
   Zakłócony przebieg (przerwy między kernelami >30% dłuższe przy tej samej pracy kerneli) powtórz.
3. **Nie zmieniaj** `~/llm/strata/strata-rx.json`, binarki produkcyjnej ani plików profilu; żadnego kodu silnika w tym zadaniu (tylko zmienne środowiskowe i argumenty). Nic nie wypychaj.
   Procesy zabijaj po pid, nie szerokim `pkill -f`. Żadnych sekretów w plikach.
4. Zabronione w razie jakiegokolwiek kodu: spin-wait na pamięci globalnej, bariery siatki, cooperative launch (zawiesiły GPU).
5. Maks. ~25 przebiegów GPU. Po 3 nieudanych próbach tego samego podejścia zatrzymaj się i opisz blokadę (dalej koduje Claude).

## 4. Co dostarczyć

`REPORT-ds-tailskip.md` w `~/Projekty/coding-bench/ds-pipeline/`, po polsku: (a) potwierdzenie, że funkcja działa i ile pomija; (b) tabela A/B (tok/s na klasę i średnio, szum, tokeny na okno,
akceptacja); (c) wynik jednej pary profilowanej (jak zmieniło się czekanie na CPU i PCIe); (d) bramka jakości z liczbami i rekomendacja; (e) wyniki z punktu D, jeśli były;
(f) jednozdaniowa rekomendacja: wdrożyć jako dodatek do `strata-rx.json` (z kopią i zgodą użytkownika) albo nie. Odróżniaj fakt zmierzony od hipotezy.
