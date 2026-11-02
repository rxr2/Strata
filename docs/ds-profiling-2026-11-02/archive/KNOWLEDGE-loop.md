# Baza wiedzy pętli (generowana automatycznie po każdym wyniku)

## CEL NADRZĘDNY: 110 tok/s (bez profilera, średnia 3 promptów)
- speed-base: 83.2 tok/s (89.0 / 91.5 / 69.2) — 76% celu, konfiguracja QFUSE=1, MTP_HIP_PRIO=1, exe=prod
- speed-a8-normrope-qdedup: 85.6 tok/s (91.6 / 92.4 / 72.7) — 78% celu, konfiguracja QFUSE=1, MTP_HIP_PRIO=1, NORM_ROPE=1, VERIFY_QDEDUP=1, exe=prod
- speed-b10-adaptjob-cpu15: 91.4 tok/s (99.1 / 102.1 / 73.1) — 83% celu, konfiguracja QFUSE=1, MTP_HIP_PRIO=1, NORM_ROPE=1, VERIFY_QDEDUP=1, ADAPT_JOB_CPU=15, exe=prod
- speed-b12-aux-cpus-smt: 92.0 tok/s (104.6 / 96.6 / 74.9) — 84% celu, konfiguracja QFUSE=1, MTP_HIP_PRIO=1, NORM_ROPE=1, VERIFY_QDEDUP=1, ADAPT_JOB_CPU=15, AUX_CPUS=9,10,11,12,13,14, exe=prod
- CEL 2: postój GPU ≤ 5% tokenu (przerwy między kernelami + host między oknami + spin na puli CPU); teraz 28.8%

## Aktualna baza (wszystkie zaliczone zmiany, na nich idą nowe eksperymenty)
- konfiguracja: QFUSE=1, MTP_HIP_PRIO=1, NORM_ROPE=1, VERIFY_QDEDUP=1, ADAPT_JOB_CPU=15, AUX_CPUS=9,10,11,12,13,14, exe=prod (na produkcji z 5 fuzjami)
- pomiar bazy #73: p1 11826 µs/tok, żółte 2905 µs (808 przerw), host między oknami 150, spin 410 | p2 12205 µs/tok, żółte 2816 µs (778 przerw), host między oknami 140, spin 388 | p3 15598 µs/tok, żółte 3834 µs (1065 przerw), host między oknami 206, spin 601
- wykorzystanie zasobów bazy (% czasu tokenu na użyteczną pracę): p1: GPU liczy 63.5%, wypełnienie 96 CU 79.7%, wątek hosta 43.0%, pula CPU 24.4%, równowaga 43.7 | p2: GPU liczy 63.8%, wypełnienie 96 CU 80.4%, wątek hosta 47.3%, pula CPU 29.6%, równowaga 46.9 | p3: GPU liczy 59.7%, wypełnienie 96 CU 75.5%, wątek hosta 50.0%, pula CPU 33.1%, równowaga 47.6
- bilans bazy (µs/token): p1: GPU czeka na plan hosta 372 (warstwa 0: 460 µs/okno), na wiersze CPU 38, odczyt wierszy CPU 855, host czeka na GPU 6697, pula CPU pracuje 2873 | p2: GPU czeka na plan hosta 350 (warstwa 0: 484 µs/okno), na wiersze CPU 38, odczyt wierszy CPU 1079, host czeka na GPU 6166, pula CPU pracuje 3469 | p3: GPU czeka na plan hosta 549 (warstwa 0: 570 µs/okno), na wiersze CPU 52, odczyt wierszy CPU 1647, host czeka na GPU 7593, pula CPU pracuje 5023
- jakość bazy: KL 0.01813, top-1 31/32
- szum pojedynczego pomiaru: żółte σ=7.7%, czas/token σ=4.42% (z 69 powtórzonych pomiarów); próg walidacji: żółte ≤ -11.1% albo postoje ≤ -3% tokenu; awans: średnia z 3 ≤ -7.7%
- strefy: agent A: None, agent B: Z2; wyczerpane: Z1, Z3

## Ścieżka krytyczna okna (pomiar Claude, baza QFUSE + MTP_HIP_PRIO, p1, 01.11 20:10) — PRZECZYTAJ
- Token pod profilerem: 13 006 µs. Cel 110 tok/s bez profilera ≈ 9 090 µs (≈ 10 000 µs pod profilerem).
- GPU nie robi postępu (µs na token): przerwy między kernelami 3 094 (23,8%) — nikt nie blokuje, pomaga tylko mniej kerneli (fuzja); czeka na plan ekspertów od hosta 581 (4,5%); czyta wiersze CPU przez PCIe z czekaniem na spóźnione 819 (6,3%); host buduje następne okno 639 (4,9%); czeka na wiersze puli 38 (0,3%).
- W tym samym czasie HOST CZEKA BEZCZYNNIE NA GPU 7 289 µs na token, a pula CPU liczy tylko 3 009 µs na token. Host i pula mają czas, żeby zrobić swoją pracę wcześniej.
- Do odzyskania przez PRZESUNIĘCIE pracy hosta/puli wcześniej (bez nowych zależności): ≈ 1 150 µs na token (plan 470 + spóźnione wiersze 677) → ≈ −8,8% czasu tokenu.
- Do odzyskania przez NAKŁADANIE okien (start okna K+1 zanim host skończy budować okno, spekulacyjnie): ≈ 640 µs → razem ≈ −13,8%.
- Najgorsze miejsce: START OKNA, warstwa 0. GPU czeka ~345–455 µs na okno na plan, bo host na początku okna robi wszystko naraz (zbiera szkic MTP, PLE gather w warstwie 0, tick adaptacji, plan); pula stoi pusta, aż plan wyjdzie. W późnych warstwach to samo czekanie trwa ~6 µs.
- Kierunek: odciążyć hosta na starcie okna (przenieść PLE / adaptację / przygotowanie na czas, gdy host czeka na GPU; priorytet wątku hosta STRATA_ENGINE_NICE=0; mniej konkurencji o rdzeń 0 — pula 7 wątków + wątki silnika na bliźniakach SMT), a nie dociążać GPU.
- Panel: sekcja „Ścieżka krytyczna okna” (przycisk „start okna”) pokazuje to na osi czasu GPU / host / pula.

## Jakość — co naprawdę mierzy bramka (01.11 20:40)
- Decyduje KL pierwszego tokenu i top-1 na 32 promptach względem FP16 (nie gorsze niż jakość aktualnej bazy).
- Zadania agentowe („znaki zgodne do 1. różnicy”) są tylko informacyjne: mierzą, gdzie tekst zaczyna się różnić, nie czy jest gorszy. Sama baza daje w zadaniu explain 77 / 321 / 536 znaków. Porównanie odpowiedzi a8 (NORM_ROPE + VERIFY_QDEDUP) z bazą: obie poprawne, inne sformułowania.
- ścieżka krytyczna aktualnej bazy (µs/token, p1 / p2 / p3): przerwy między kernelami 2905 / 2816 / 3834; czekanie na plan hosta 372 / 350 / 549; odczyt wierszy CPU 855 / 1079 / 1647; host buduje okno 150 / 140 / 206; do ukrycia przesunięciem 980 / 1190 / 1854; do ukrycia nakładaniem okien 150 / 140 / 206; host czeka na GPU 6697 / 6166 / 7593

## Historia awansów do bazy
- 01.11 19:14: QFUSE=1 — żółte średnio -2.5%, postój razem -0.7% tokenu z 3 pomiarów, czas/token -3.3%, żółte -5.1% (-246 µs/tok), postój razem -166 µs/tok (-1.1% tokenu), czas/token -4.8%, KL 0.01671 vs baza 0.01671, top-1 31 vs 31, zadania agentowe 1877/1877 znaków (najgorsze 100%)
- 01.11 20:03: MTP_HIP_PRIO=1 — żółte średnio -1.6%, postój razem -6.2% tokenu z 3 pomiarów, czas/token -7.9%, żółte -0.3% (-32 µs/tok), wykorzystanie zasobów +5.1 pkt, postój razem -1041 µs/tok (-6.6% tokenu), czas/token -9.0%, KL 0.01671 vs baza 0.01671, top-1 31 vs 31, zadania agentowe 1877/1877 znaków (najgorsze 100%)
- 01.11 20:47: NORM_ROPE=1, VERIFY_QDEDUP=1 — żółte średnio -5.8%, postój razem -1.7% tokenu z 3 pomiarów, czas/token -3.2%, żółte -5.9% (-197 µs/tok), wykorzystanie zasobów +0.2 pkt, postój razem -296 µs/tok (-2.1% tokenu), czas/token -4.0%, KL 0.01813 vs baza 0.01812, top-1 31 vs 31, zadania agentowe 1591/2121 znaków do 1. różnicy (informacyjnie)
- 01.11 21:27: ADAPT_JOB_CPU=15 — żółte średnio -1.0%, postój razem -5.3% tokenu z 3 pomiarów, czas/token -5.8%, żółte +0.2% (+5 µs/tok), wykorzystanie zasobów +1.5 pkt, postój razem -591 µs/tok (-4.3% tokenu), czas/token -3.9%, KL 0.01894 vs baza 0.01813, top-1 31 vs 31, zadania agentowe 1648/1877 znaków do 1. różnicy (informacyjnie)
- 01.11 22:58: AUX_CPUS=9,10,11,12,13,14 — żółte średnio -15.5%, postój razem -10.9% tokenu z 3 pomiarów, czas/token -9.1%, żółte -15.9% (-893 µs/tok), wykorzystanie zasobów +4.2 pkt, postój razem -1651 µs/tok (-10.8% tokenu), czas/token -9.8%, KL 0.01817 vs baza 0.01813, top-1 31 vs 31, zadania agentowe 1591/1817 znaków do 1. różnicy (informacyjnie)

## Przetestowane zmiany (względem bazy z chwili testu)
| # | agent/strefa | zmiana | werdykt | żółte | postój µs/tok | czas/token | plan hosta µs/tok (p1) | wykorzystanie pkt | jakość |
|---|---|---|---|---|---|---|---|---|---|
| 3 | -/- | exp e1-fork: exe=fork | neutral | 1.3% | -71 | -2.7% | 553 | 2.2 | KL 0.01195 top1 31 |
| 4 | -/- | rep e1-fork-r2: exe=fork | neutral | 1.4% | -97 | -2.8% | 491 | 2.5 | KL 0.01193 top1 31 |
| 5 | -/- | rep e1-fork-r3: exe=fork | neutral | -0.1% | -101 | -3.4% | 457 | 2.5 | KL 0.01075 top1 31 |
| 7 | -/- | exp e2-mtp-prio: MTP_HIP_PRIO=1 | WIN | -0.3% | -1041 | -9.0% | 616 | 5.1 | KL 0.01671 top1 31 |
| 8 | -/- | rep e2-mtp-prio-r2: MTP_HIP_PRIO=1 | WIN | -5.0% | -1112 | -9.5% | 576 | 4.2 | KL 0.01671 top1 31 |
| 9 | -/- | rep e2-mtp-prio-r3: MTP_HIP_PRIO=1 | WIN | 0.4% | -792 | -5.2% | 945 | 3.4 | KL 0.01671 top1 31 |
| 13 | A/- | exp qfuse: QFUSE=1 | neutral | -5.1% | -166 | -4.8% | 746 | 1.2 | KL 0.01671 top1 31 |
| 14 | A/- | rep qfuse-r2: QFUSE=1 | neutral | -0.7% | 48 | -0.8% | 726 | 1.2 | KL 0.01671 top1 31 |
| 15 | A/- | rep qfuse-r3: QFUSE=1 | neutral | -1.7% | -213 | -4.2% | 591 | 2.3 | KL 0.01671 top1 31 |
| 19 | B/- | exp e3-qfuse-lfuse: QFUSE=1, LFUSE=1 | neutral | 0.4% | 54 | +0.3% | 665 | -0.2 | KL 0.01671 top1 31 |
| 20 | A/- | exp e5-side-mixer: SIDE_MIXER=2 | engine failed: re released but the GPU d | % |  |  |  |  |  |
| 23 | B/- | exp e6-fuse-hits: FUSE_HITS=1 | neutral | -1.7% | -8 | +0.0% | 577 | 0.4 | KL 0.01671 top1 31 |
| 24 | A/- | exp e6-sh-stream: SH_STREAM=1 | engine failed: ere released but the GPU  | % |  |  |  |  |  |
| 27 | B/- | exp e7-qdedup-fusehits: VERIFY_QDEDUP=1, FUSE_HITS=1 | neutral | -4.3% | -113 | -0.5% | 605 | 0.5 | KL 0.01812 top1 31 |
| 37 | A/Z1 | exp a8-normrope-qdedup: NORM_ROPE=1, VERIFY_QDEDUP=1 | neutral | -5.9% | -296 | -4.0% | 635 | 0.2 | KL 0.01813 top1 31 |
| 39 | A/Z1 | rep a8-normrope-qdedup-r2: NORM_ROPE=1, VERIFY_QDEDUP=1 | neutral | -5.7% | -192 | -2.5% | 657 | 0.2 | KL 0.01813 top1 31 |
| 40 | A/Z1 | rep a8-normrope-qdedup-r3: NORM_ROPE=1, VERIFY_QDEDUP=1 | neutral | -5.7% | -254 | -3.1% | 731 | 0.2 | KL 0.01813 top1 31 |
| 46 | B/Z2 | exp b9-aux-cpus: AUX_CPUS=auto | FAIL-speed | 1.3% | 251 | +3.7% | 347 | 0.6 | KL 0.01791 top1 31 |
| 48 | A/Z1 | exp a9-fusehits-dfple: FUSE_HITS=1, DF_PLE=1 | neutral | -1.8% | 25 | +0.2% | 573 | 0.1 | KL 0.01779 top1 31 |
| 50 | B/Z2 | exp b10-adaptjob-cpu15: ADAPT_JOB_CPU=15 | WIN | 0.2% | -591 | -3.9% | 434 | 1.5 | KL 0.01894 top1 31 |
| 51 | B/Z2 | rep b10-adaptjob-cpu15-r2: ADAPT_JOB_CPU=15 | WIN | -3.0% | -859 | -8.5% | 315 | 1.8 | KL 0.01894 top1 31 |
| 52 | B/Z2 | rep b10-adaptjob-cpu15-r3: ADAPT_JOB_CPU=15 | WIN | -0.2% | -724 | -4.9% | 356 | 1.4 | KL 0.01894 top1 31 |
| 57 | A/Z1 | exp a10-lookup-chain: --lookup-chain 2 | FAIL-speed | 1.0% | 222 | +4.7% | 504 | 0.4 | KL 0.01813 top1 31 |
| 61 | B/Z2 | exp b11-adapt-every2: --adapt-every 2 | neutral | -1.1% | 0 | -0.3% | 368 | 0.3 | KL 0.01667 top1 31 |
| 63 | A/Z3 | exp a11-spec-cost: SPEC_COST=1 | neutral | -9.9% | -344 | -1.0% | 264 | 3.8 | KL 0.01813 top1 31 |
| 64 | A/Z3 | rep a11-spec-cost-r2: SPEC_COST=1 | neutral | -10.9% | -201 | +0.8% | 522 | 3.7 | KL 0.01813 top1 31 |
| 65 | A/Z3 | rep a11-spec-cost-r3: SPEC_COST=1 | FAIL-speed | 25.4% | 1310 | +17.9% | 564 | -1.7 | KL 0.01813 top1 31 |
| 70 | B/Z2 | exp b12-aux-cpus-smt: AUX_CPUS=9,10,11,12,13,14 | WIN | -15.9% | -1651 | -9.8% | 426 | 4.2 | KL 0.01817 top1 31 |
| 71 | B/Z2 | rep b12-aux-cpus-smt-r2: AUX_CPUS=9,10,11,12,13,14 | WIN | -15.2% | -1685 | -9.6% | 388 | 4.1 | KL 0.01817 top1 31 |
| 72 | B/Z2 | rep b12-aux-cpus-smt-r3: AUX_CPUS=9,10,11,12,13,14 | WIN | -15.3% | -1637 | -8.0% | 384 | 4.7 | KL 0.01817 top1 31 |
| 78 | A/Z3 | exp a12-spec-minp-05: --spec-min-p 0.5 | FAIL-speed | -7.9% | -265 | +7.4% | 356 | 5.2 | KL 0.01813 top1 31 |
| 80 | B/Z2 | exp b13-host-core-sibling: HOST_CORE=sibling | FAIL-speed | 19.2% | 1249 | +16.0% | 492 | -2.9 | KL 0.01813 top1 31 |
| 82 | A/Z3 | exp a13-spec-cost-b: SPEC_COST=1 | FAIL-speed | -2.1% | 13 | +4.3% | 448 | 2.2 | KL 0.01779 top1 31 |
| 86 | B/Z2 | exp b14-adapt-swaps48: --adapt-swaps 48 | FAIL-speed | 1.5% | 235 | +9.0% | 402 | 1.3 | KL 0.01507 top1 31 |

## Odrzucone propozycje
- brak

## Wnioski agentów
- [-] Baza #1 to sam pomiar referencyjny (brak diffu z definicji): p1 13 305 zgodne z dokumentacją, ale p3 19 412 = +3,3% vs 18 786 — pojedynczy przebieg potrafi odjechać o ~3%, więc próg 2% i powtórki 3x obowiązują, a bazą jest ten przebieg, nie liczby z raportu.
- [-] Fork daje realne -2..-5% (najwięcej p3), ale przez zmianę numeryki: tokens/window 4,16->3,76 i 3,27->2,88, tekst niedeterministyczny miedzy repami (r2 inny hash), a agent json 485/709 -> 256/709 przy KL 0,011 - brama KL jest slepa na te regresje, wiec forka nie wdrazamy.
- [A] LFUSE/LFUSE_PAIR są w tym configu martwe: bramkuje je ar_on() = all_resident_ || device_plan_ (oba fałsz przy ~13% missów i VERIFY_DEVICE_PLAN=0), dlatego zestawy z gfx1151 nie trzymały się nad szumem; dźwignia żółtego to przełączniki bez bramki ar_on, a największa jednorodna populacja launchy to 189 kwantyzacji q8_1/okno (QFUSE).
- [B] Żółte w bazie = 3,2 us × 745 launchy/token (mediana przerwy taka sama dla każdego kernela), więc redukcja liczby launchy to jedyny dźwignik: 16 launchy/token = -2% żółtego. Najliczniejsze do usunięcia: quantize_q8_1 43/token (QFUSE) i klaster ścieżki ekspertów ~18/token na kernel.
- [A] Przeplot (SIDE_MIXER) nie zmienia liczby launchy, więc żółte spadnie tylko tam, gdzie kernel boczny realnie wchodzi w przerwę strumienia głównego - patrzeć na liczbe par (A->B) i ich czasy w diffie, nie na sumę kerneli.
- [B] LFUSE/LFUSE_* są u nas martwe (ar_on()=0), a zadanie agentowe 'explain' jest bimodalne (77 vs 536/698 znaków przy identycznym KL 0.01671) — bramę jakości przegrywają wszystkie zmiany zmieniające tekst, także te promowane; dlatego opłaca się wybierać wyłącznie bitwise redukcje liczby launchy, gdzie bramka w ogóle nie startuje.
- [A] SIDE_MIXER=2 to nie szum: graf okna z własnymi strumieniami zawiesza HIP na pierwszym launchu (timeout layer 0, 0 tok). SH_STREAM=1 to bezpieczna wersja tej samej idei — sprawdzić, czy przeniesienie ~66 launchy/token shared experta na strumień boczny realnie zmniejsza żółte, czy tylko dokłada kernele obok.
- [B] QDEDUP usuwa kwantyzację wejścia shared experta (-48 launchy/okno) bo GR-read z QFUSE już pisze ten obraz q8_1; FUSE_HITS zwija add_hits tylko w 28/48 warstw (n>1 + combine_hits_supported), stąd tylko -1,7%; STRATA_BATCH_*/QSA_SLOTS są u nas martwe (batch_rec_ tylko w capture_batch), a FAIL-quality pojedynczego przebiegu nic nie dowodzi (explain 77 vs 536 w samej bazie).
- [A] Ostatni q8_1 na połówkę FFN (kwantyzacja wejścia shared experta) da się usunąć bitwise przez VERIFY_QDEDUP, bez bramki ar_on() — inaczej niż całe LFUSE; a wszystkie przełączniki ze strumieniem bocznym (SH_STREAM, SH_FORK_LATE, SIDE_MIXER, DF_BRANCH) na tej karcie nie kończą pierwszego grafu (timeout 5 s), więc żółte trzeba zbijać liczbą launchy, nie przeplotem.
- [B] Host jest sam na CPU 0, pula na 1-7 (--pool-workers i ENGINE_NICE bez mechanizmu); plan_wait warstwy 0 = 455-517 us/okno przy dnie 6 us w warstwach >=10, a najwiekszym postojem Z2 pozostaje gap_host 1577 us/tok - MTP_HIP_PRIO=1 zbijal go do ~550 us/tok w 3 przebiegach i przepadl tylko na losowej bramie zadania 'explain'.
- [A] STRATA_NORM_ROPE=1 to ostatnia fuzja launchy w Z1 na gfx1100 (norm+apply + split q/gate = ~-46 launchy/okno, bitwise); reszta żółtego warstwy to puste launche ścieżki PCIe (fetch_blobs+rebase_ptrs+gu_multi+swiglu_q8_1+down_multi = 240/okno, nieusuwalne przełącznikiem, bo plan żyje na GPU w przechwyconym grafie) oraz rozbity shared expert (LFUSE martwy przez ar_on()); EXPERT_V2 dodałby launch, bo native_gu_fused już zwija SwiGLU+q8_1.
- [A] Żółte da się zbijać tylko sumą fuzji: NORM_ROPE (norm+rope+split q/gate = -4 launchy na warstwę QSA) plus QDEDUP (-1 quantize na połówkę FFN) to ~-144 launchy/okno, pierwszy zestaw w Z1, który przekracza próg -3,5%; pojedynczo każdy z nich jest pod szumem.
- [B] Watek adaptacji (strata-adapt-jo) domyslnie NIE jest przypiety na Linuksie (smt_spare_cpu()=-1) i siada na rdzeniu hosta zabierajac mu 6.8% czasu (~0.9 ms/token) akurat w ticku przed startem okna - czesc plan_wait warstwy 0 (476 us/okno) to nie praca planu (0.07 ms/okno), tylko wysiedlenie watku hosta.
- [A] NORM_ROPE (~-4 launchy na warstwe QSA) + VERIFY_QDEDUP (~-48 launchy/okno) to jedyny pozostaly zestaw launchy w Z1; GU_SWIGLU/HIP_SWIGLU_FUSED sa na gfx1100 martwe (em0==8 / #if GFX906), FUSED_SWIGLU_Q81 jest domyslnie wlaczony.
- [B] Adapt-tick to nie plan, a czekanie: ~1 ms/okno wystawionego postoju hosta (STRATA_ADAPT_ASYNC_WAIT=1 czeka na kopie) plus watek strata-adapt-jo nieprzypiety na cpu 0 - oba obciazaja rdzen hosta dokladnie przed startem okna.
- [A] Para NORM_ROPE+VERIFY_QDEDUP daje -41 launchy/token i -5,9% zoltego przy KL w tolerancji i top-1 rownym bazie - jedyny zestaw Z1 powyzej progu; stara brama zadan agentowych (znaki do 1. roznicy, bimodalna: explain 77..536 w samej bazie) zdyskwalifikowala go bez powodu, wiec nie wolno na niej opierac werdyktu. FUSE_WAIT/FUSE_ROWS sa w naszej konfiguracji martwe przez m_bal_ (--pcie-frac 0.20), LFUSE przez ar_on(), a ATTN_LANECELL rozwidla uwage na launch na wiersz.
- [B] STRATA_ENGINE_NICE nie jest czytany przez zadna binarke w tym harnessie (strings: strata, strata-control, build-rx) - proces priority jest tu niemym kluczem; realna dzwignia na rdzen hosta jest STRATA_AUX_CPUS (domyslnie off), bo watek adapt-jo i watki drivera dziedzicza maske hosta (CPU 0).
- [A] Z1 na env-ach jest prawie wyczerpane: zostają tylko FUSE_HITS (-12,6 węzła/token) i DF_PLE (-7); największy klaster (6 pustych launchy PCIe na warstwę = 131 węzłów/token, 445 us = 12,7% żółtego) wymaga --pcie-mode dma/direct, a LFUSE_PAIR (-22,8 węzła) blokuje ar_on() = 100% ekspertów w VRAM.
- [B] AUX_CPUS=auto szkodzi, bo sadza watki pomocnicze na blizniaku rdzenia hosta (CPU 8) - +833 us/token na copy_i32_from_mapped; wolne i bezpieczne sa dopiero blizniaki rdzeni puli (9-15), wiec izolowac trzeba pojedynczo (STRATA_ADAPT_JOB_CPU), nie hurtem.
- [A] Liczba launchy na okno jest stała (~1780) niezależnie od liczby tokenów w oknie (p1 1791/2,21 tok vs p3 1773/1,64 tok), więc żółte na token skaluje się jak 1/(tokeny/okno): p3 płaci 1080 launchy/token, p1 817 — po wyczerpaniu fuzji w Z1 dźwignią jest amortyzacja okna (akceptacja), nie kolejny kernel.
- [B] Tick adaptacji z --adapt-every 1 płaci się w każdym oknie na rdzeniu hosta tuż przed planem; częstotliwość ticku to bezpośrednia dźwignia na plan_wait warstwy 0, ale trzeba pilnować hit rate (wzrost rows_read).
- [A] Z1 na env-ach jest wyczerpana: żółte to 3,6 us x 810 launchy/token i wszystkie pozostałe klastry (5 pustych launchy ścieżki missów na połówkę FFN, epilog shared experta pod martwym LFUSE przez ar_on(), 192 launche HC) są nieusuwalne przełącznikiem - EXPERT_V2 w naszej geometrii (gu 21 / down 20 / n_embd 2560 / n_ff 640) dokłada launch (2->3), a HC_PERSIST jest odrzucany na gfx11 (brak s_memrealtime).
- [A] Weryfikacja jest płaska względem liczby wierszy (23,13 ms przy T=2,37 vs 23,22 ms przy T=1,90), a próg --spec-min-p 0,85 przycina łańcuch na 1,37 draftu przy 89% akceptacji - stały próg tnie okna w miejscu, gdzie koszt krańcowy wiersza jest bliski zeru.
- [B] Watki, ktore dziedzicza rdzen hosta (driver HIP, io, lookahead), to nie ten sam problem co pula: b9 pokazal, ze na CPU 8 (blizniak hosta) kosztuja +833 us/token, wiec izolowac je trzeba jawnie na blizniaki rdzeni puli (9-14), nie przez auto.
- [A] SPEC_COST przegrał w r3 nie na polityce (tok_win 2.76/2.62/1.79 bez zmian, KL identyczny), a na globalnym spowolnieniu maszyny potwierdzonym następną bazą (p3 20160 us, spin 2122, plan_wait 2069) — jego model kosztów dokłada zmienność tam, gdzie maszyna i tak jest niestabilna, więc szerokość okna lepiej ustawiać stałym progiem --spec-min-p.
- [A] Liczba launchy na okno jest stala (1792: 1662 weryfikacja + 130 strumien draftu = 60/token), wiec w Z3 jedyna realna dzwignia zoltego jest amortyzacja okna; dokumentowy wynik 'min-p 0.85 bije 0.5-0.7' pochodzi z kontekstow 5-64K, gdzie wiersz jest drogi — przy krotkim kontekscie (weryfikacja plaska wzgledem T) prog 0.85 tnie okno za wczesnie.
- [A] W Z3 zostały tylko okna: liczba launchy na okno jest stała, a tok_win 2,21/2,32/1,65 dyktuje żółte na token; bramka 0.85 trzyma okno na ~1,4 draftu z 5 możliwych.
- [B] Po AUX_CPUS=9-14 i ADAPT_JOB_CPU=15 wszystkie rdzenie 0-7 są w 100% zajęte (pula i host spinują), a jedynym wątkiem dzielącym rdzeń z konkurentem jest host na CPU 0 razem z przerwaniami GPU - zostaje STRATA_HOST_CORE=sibling (host na CPU 8, rdzeń 0 tylko dla IRQ).
- [A] Szerokość okna w Z3 trzeba wybierać polityką kosztową (SPEC_COST: tokeny/ms, EMA kosztu rundy per T), a nie progiem min-p: min-p 0.5 dało T 2.37->3.63 i akceptację 89%->57% (dodatkowe wiersze prawie wszystkie odrzucone), czyli +17.9% czasu okna za +12% tokenów, a żółte tylko -7.9%.
- [B] Watki adaptacji (async tier, nie-arena) dokladaja ~132 MB/okno ruchu PCIe/RAM - tyle samo co cala praca ekspertow puli; --adapt-every 2 bylo neutralne, bo nie obniza szczytu ruchu w oknie, wiec jedynym testem tej hipotezy jest --adapt-swaps.
- [A] Z3 domknięte: okno 2,2 tok przy min-p 0,85 to optimum, bo dodatkowy wiersz jest płaski na GPU, ale obciąża nasyconą pulę CPU i tasuje rezydencję ekspertów (a13: +46,5 mmvq_multi/token, +4,3% czasu przy żółtym -2,1%); sampler=1 launch, commit zbatchowany, GRAPH_PRIO martwy na HIP — zostaje draft (1,6 ms/token) i węzły grafu okna, czyli kod, nie przełączniki.
- [B] Drain puli per warstwa (133 us) to 39-56 us czekania GPU ukrytego w copy_rows_from_mapped; sprawdzic, czy skaluje sie z liczba watkow (wtedy bliźniaki SMT 8-15 sa darmowe) czy z pasmem RAM (wtedy zostaje tylko mniej bajtow).
