# Raport: stan potoku dekodowania i plan optymalizacji — Strata na RX 7900 XTX

Data: 2026-11-01. Silnik: snapshot forka `strata/src` (commit cc21cbf4) + binarka produkcyjna `~/llm/strata/strata`
(upstream 0.1.52 HIP). Model: Qwen3.8-Flash-Next-GSQ-RCO (abliterated) IQ3_S, ~125B-class MoE, 48 warstw
(GDN + QSA + FFN z routerem/ekspertami, hyper-connections przy każdej połówce). GPU: RX 7900 XTX (gfx1100),
96 CU, 24 GB VRAM, PCIe 4.0 x16, CPU Zen 5 AVX-512 (7 wątków puli), 36 GiB ekspertów w RAM.
Konfiguracja: `data/prod-config.json` + 5 przełączników fuzyjnych (FUSE_WAIT, QFUSE_HC, ONE_TOKEN_COMMIT,
FUSE_CONVAB, FUSE_HEAD_GR).

Konwencja: **fakt zmierzony** piszę wprost z odnośnikiem do pliku z pomiarami; **hipotezę** oznaczam jawnie
słowem „hipoteza". Cytaty kodu: `plik:linia`.

---

## 1. Stan obecny

### 1.1 Liczby na token (produkcja, `data/prod-now-pN-*.txt`, pomiar rocprofv3 20261101-172414)

| prompt | us/token | tok/s (czas GPU) | tokenów/okno | kerneli/okno | kerneli/token |
|---|---|---|---|---|---|
| p1 ring all-reduce (EN) | 13 679 | 73,1 | 3,81 | 3260 | ~856 |
| p2 kod Python (EN) | 15 283 | 65,4 | 3,52 | 3001 | ~853 |
| p3 polska proza | 18 786 | 53,2 | 3,08 | 3717 | ~1207 |

Okno p1 = 52 111 us = kernele 35 153 us (67%) + przerwy 16 958 us (33%) (`data/prod-now-p1-map.txt`).
Przerwy na token = 16 958 / 3,81 ≈ 4 450 us, z czego ~3 us/kernel to narzut uruchomienia (KNOWLEDGE.md §4).

Rozkład etapowy na token (p1; `stage_table.py`, `data/prod-now-p1-stages.txt`):

| etap | kernele us | przerwy us | razem us | udział |
|---|---|---|---|---|
| macierze gęste (proj. attn/GDN/shared, lm_head; mmvq/mmvf + kwantyzacja q8_1) | 3006 | 820 | 3826 | 28,0% |
| eksperty na GPU (cache hit: gu_fused, down_lds, fetch_blobs, combine…) | 2211 | 821 | 3032 | 22,2% |
| czekanie na eksperty z CPU | 1694 | 393 | 2087 | 15,3% |
| normy i drobne | 234 | 1700 | 1934 | 14,1% |
| HC (hyper-connections) | 1024 | 307 | 1331 | 9,7% |
| uwaga (QSA) | 378 | 118 | 496 | 3,6% |
| GDN rekurencja | 311 | 111 | 422 | 3,1% |
| router | 248 | 73 | 321 | 2,3% |
| inne | 122 | 107 | 229 | 1,7% |

p2 i p3 mają tę samą strukturę (p2: eksperty GPU 28,3%, gęste 25,8%, CPU 14,4%; p3: gęste 26,7%, GPU 21,1%,
CPU 18,1%, normy 14,3%) — `data/prod-now-p2-stages.txt`, `data/prod-now-p3-stages.txt`.

### 1.2 Oś czasu jednego okna dekodowania (kolejność i kto co robi)

Okno jest cięte na `gdn_step_commit_layers_kernel` (`kb/pipeline_map.py:26`). Kolejność zdarzeń na GPU i CPU,
z czasami z p1 (us/token, o ile nie podano inaczej):

1. **Kopie tieru adaptacyjnego** — `__amd_rocclr_copyBuffer` (hipMemcpyAsync, 2,4 wywołania/okno, mediana 4,8 us):
   kopie swapów ekspertów do cache, wydawane przez tick asynchronicznego tieru na początku iteracji pętli
   (`generate.cpp:16645`; wywołania a_choose/a_copy_in `generate.cpp:11734-11739`).
2. **Start okna weryfikującego** — `cudaGraphLaunch` grafu okna (`verify.cpp:3159`); pierwszy kernel grafu to
   `copy_i32_from_mapped` (`verify.cpp:1310`). Przerwa copyBuffer → copy_i32 = **59 us/token** (p1, p2; p3: 115) —
   narzut uruchomienia grafu o ~3000 węzłach na ROCm.
3. **Okno weryfikujące** (graf HIP, ~3260 kerneli): embedding → na warstwę: odczyt HC (`gr_down_q8_kernel`) →
   mixer (uwaga QSA `attn_chunk_kernel`/`attn_merge_kernel` albo rekurencja GDN `gdn_step_norm_multi_kernel`,
   `gdn_conv_ab_kernel`) → FFN: router (`route_multi`, `route`) → plan + doorbell (`doorbell_publish_res_kernel`)
   → shared expert (mmvq/mmvf) → eksperci kierowani: cache-hit na GPU (`native_gu_fused_kernel`,
   `native_down_lds_kernel`, `fetch_blobs_kernel`) albo wiersze z CPU (patrz 1.3.2) → combine
   (`combine_k10_vec4`, `add_hits_kernel`) → HC up (`gr_up_q8_q32_kernel`) → … → głowa
   (`native_q6_k_mmvq_kernel`, `bf16_f32_mmvf_multi_kernel`) → sampler (`sampler_greedy_kernel`,
   `logits_nonfinite_kernel`).
4. **Commit** — graf commita, `gdn_step_commit_layers_kernel` (1/okno, 247 us/okno = ~65 us/token;
   ONE_TOKEN_COMMIT ogranicza liczbę commitów, `verify.cpp:497`).
5. **Drafter MTP** — `mtp.draft` (`generate.cpp:16760`): kopie D2D `stage_source_R` (`mtp.cpp:1654`), potem
   graf „round" (catch-up K/V + pierwszy draft, `capture_round` `mtp.cpp:1318-1364`) i do 5 grafów „step"
   (`capture_step` `mtp.cpp:1368-1394`); każdy krok kończy `mtp_select_kernel`, który zapisuje draft do
   mapped host memory (`mtp.cpp:1359, 1389`). Całość draftera ≈ 3 ms/okno (~10%) — pomiar z
   `strata/docs/RX7900XTX.md:82-85` (sprzed 5 przełączników).
6. **Round-trip hosta po drafterze** — host dospinowuje drafty z mapped memory (`mtp.cpp:1687-1699`,
   wariant min-p `1724-1733`), robi `cudaStreamSynchronize` (`mtp.cpp:1700`), PLE-prefetch, księgowość pętli
   (`policy.observe`, `pcie_auto_step`), `stage_inputs` — zapis tokenów/pozycji do mapped stagingu
   (`verify.cpp:2893-2922`) — i `cudaGraphLaunch` następnego okna. W tym czasie GPU **nic nie robi**:
   **1428 us/token (10,5%) w p1 i p2, 2002 us/token (10,7%) w p3** — przerwa
   `mtp_select_kernel -> __amd_rocclr_copyBuffer` (`data/prod-now-pN-stages.txt`).

### 1.3 Mechanizmy dużych pozycji (ze źródła)

#### 1.3.1 Przerwa po `mtp_select_kernel` (host round-trip, 1428/1415/2002 us/token)

To największy pojedynczy punkt jałowy GPU. Mechanizm (fakt z kodu, rozmiar z pomiaru):
- Drafty są produkowane na GPU i czytane przez **hosta spinem po mapped memory**: `while
  (((volatile int32_t*) h_out_)[j] < 0) … strata_cpu_pause()` (`mtp.cpp:1687-1694`; `h_out_`/`m_out_` to
  bufor mapped, `verify.cpp:878`). Każdy odczyt to round-trip PCIe; po ostatnim kroku host czeka na
  `cudaStreamSynchronize(cs_)` (`mtp.cpp:1700`).
- Potem pętla serwująca buduje następne okno: akceptacja zachodzi **na hoście** przez porównanie tokenów
  (`while (a < T-1 && window[a+1] == outv[a]) ++a;` `generate.cpp:16696`), następuje księgowość i
  `stage_inputs` (host pisze do mapped, bez kopii GPU, `verify.cpp:2893-2922`).
- **Hipoteza o różnicy p3:** p3 ma większe okna (3717 kerneli/okno vs 3260 w p1 — więcej wierszy, bo drafter
  w polszczyźnie rzadziej spada poniżej `--spec-min-p 0.85` i łańcuch dobiega końca) i mniejszą akceptację
  (3,08 vs 3,81), więc przerwa na okno rośnie (6166 vs 5415 us/okno), a na token dodatkowo dzieli się przez
  mniej tokenów. Niezależnie od przyczyny: koszt jest per-okno, zysk z jego redukcji największy w p3.
- Składowe tej przerwy widać też osobno: `logits_nonfinite -> sampler_greedy` 25-35 us/token i
  `sampler_greedy -> copy_i32_from_mapped` 16-23 us/token — punkt synchronizacji samplera z hostem
  (`data/prod-now-p1-stages.txt`).

#### 1.3.2 Czekanie na eksperty z CPU (2087 us/token p1 = 15,3%; p3: 3402 = 18,1%)

Przepływ missa (fakt z kodu):
1. Router wybiera top-K ekspertów; plan dzieli je na: cache-hit (GPU), CPU pool, udział PCIe
   (`expert_source.cpp:3088-3099` — „the misses in routing order (first appearance), the PCIe share = the last
   (n_miss * pcie_num / 256)"; `--pcie-frac 0.20`).
2. `doorbell_publish_res_kernel` publikuje aktywacje i id ekspertów do puli (`verify.cpp:2137-2149`).
3. CPU pool (7 wątków AVX-512, `--pool-workers 7`) liczy wiersze IQ3_S z RAM; host obsługujący okno czeka
   flagę planu warstwa po warstwie (`verify.cpp:3260-3313`).
4. GPU czeka: `wait_copy_i32_kernel` spinuje na fladze planu (`verify_kernels.cu:1524-1538`), potem
   `copy_rows_from_mapped_kernel` czyta wiersze CPU z **mapped host memory przez PCIe**
   (`elementwise.cu:238-261`: blok = wiersz, wątek 0 opcjonalnie czeka flagę i liczy hit_rows, reszta kopiuje
   float4; wariant z czekaniem złożonym w kopię: `copy_rows_from_mapped_after` `elementwise.cu:289-298`,
   włączony przez STRATA_FUSE_WAIT).
- Udziały kerneli (p1, us/okno): `copy_rows_from_mapped_kernel` 3268 (6,8% okna, 80,8 wywołań — średnio
  40,4 us, mediana 7,1 us → gruby ogon), `wait_copy_i32_kernel` 2654 (5,6%), `doorbell_publish_res_kernel` 343.
- Pula jest **na suficie DRAM** (~58 GB/s, pomiar RX7900XTX.md:30): ~2,8 missa/warstwę
  (RX7900XTX.md:82-85), „CPU branch runs beside the GPU's VRAM experts but is longer, so the GPU waits ~3 ms
  per window". Dlatego sama optymalizacja AVX już nic nie daje (T03, RX7900XTX.md:72). Ścieżka PCIe jest
  ~98% wolna, ale wolniejsza na eksperta: ~85 us szeregowo vs ~3 eksperty/0,13 ms pulą (RX7900XTX.md:69,84).

#### 1.3.3 Macierze gęste (3826 us/token = 28%)

`native_mmvq_multi_kernel` (6001 us/okno, 13,5% okna, grid 124160×128; `native_mmvq.cu:1240`, na HIP
jeden wavefront na wiersz + 64-lane butterfly — MMVQ_WAVE `native_mmvq.cu:2333-2334`),
`native_q6_k_mmvq_kernel` (2130 us/okno, 4,5%; grid 106 299×128), `native_small_mmvq_kernel` (1226, 3,0%),
`native_iq4_xs_mmvq_kernel`, `bf16_f32_mmvf_multi_kernel` + `bf16_f32_mmvf_kernel` (628+384, 3,3%),
`native_quantize_q8_1_kernel` (251 + przerwy 612, 1,7%). Audyt pasma (`data/stage-bandwidth.txt`, sprzed
przełączników): gemv gęste 60-85% sufitu 1015 GB/s (head 85%, q8+qkv 72%, out-proj 60%) — częściowo już
ograniczone pasmem, częściowo (shared+quant 14%) launch-bound.

#### 1.3.4 Eksperty na GPU (3032 us/token = 22,2%)

Cache-hit: `native_gu_fused_kernel` (2974 us/okno, 6,2%, grid 1000×256, mode 8 zgrupowany —
`iq_kernels.cu:6146-6148`, `STRATA_EXP_MODE=8`; układ AMD `iq_kernels.cu:5553`), `native_down_lds_kernel`
(2248, 4,9%), `fetch_blobs_kernel` (2178, 4,7%), `combine_k10_vec4`, `add_hits_kernel`, `swiglu_q8_1_entries`,
`sigmoid_scale_rows_vec4`. Pasmo: VRAM hits 54-57% sufitu (stage-bandwidth.txt) — jest zapas, ale wzrost
hit-rate ogranicza pojemność cache (patrz 2.).

#### 1.3.5 HC (1331 us/token = 9,7%)

`gr_up_q8_q32_kernel` (1994 us/okno, 4,8%, grid 80×512) i `gr_down_q8_kernel` (1523, 3,9%, grid 176×256),
wagi Q8 (`STRATA_HC_Q8=1`, `native_dense.cpp:51`), up z kwantyzacją scalony (QFUSE_HC). Pasmo: hc up/down
tylko 22-29% sufitu (stage-bandwidth.txt) — launch-bound, nie pasmo. Przepisanie kerneli HC dało 1,195x w
izolacji, ale tylko ~1-2% w silniku (udział 10%, KNOWLEDGE.md §5) — klasyczny Amdahl.

#### 1.3.6 Gdzie GPU jest jałowy i dlaczego (podsumowanie)

| przyczyna jałowości | us/token (p1) | udział | natura |
|---|---|---|---|
| host round-trip po drafterze (1.3.1) | 1428 | 10,5% | host serializuje okna |
| przerwy launchowe ~860 kerneli × ~3 us | ~2600 | ~19% | narzut uruchomień ROCm (część idzie na redukcję fuzyjną) |
| zależności od CPU pool (flagi planu, wiersze) | ~1000+ | ~7%+ | pool na suficie DRAM |
| start grafu okna + drobne sync (sampler, logits) | ~100 | ~0,7% | fixed cost |

Uwaga: kolumny się nie sumują wprost do 33% — przerwy launchowe częściowo zawierają czekania na CPU
(przerwa przed kernelem czekającym liczona jest jako jego „gap").

---

## 2. Mapa celów

„Max zysk" = udział × osiągalne przyspieszenie tej części (Amdahl) — górna granica, przy założeniu że reszta
nie zmienia się. Sortowane po zysk/wysiłek.

| # | Cel | Udział (p1) | Osiągalne przysp. części | Max zysk na token | Wysiłek | Ryzyko |
|---|---|---|---|---|---|---|
| 1 | **fork vs release** — wyjaśnić i wdrożyć build forka (p1 13 033 vs 13 679 us) | 100% (różnica 4,7%) | — | **+4,7%** (już zmierzone) | eksperyment + wdrożenie configu (zgoda, kopia) | niskie; nieznana przyczyna = ryzyko ukrytej zmiany numeryki? (teksty identyczne w pomiarze) |
| 2 | **przerwa po mtp_select (host round-trip)** | 10,5% (p3 10,7%) | 1,5–2,2× (MTP_HIP_PRIO, mniej synców, mniejsze okna wg kosztu) | **−3,5…−5%** (p3: −4…−5,5%) | przełącznik + mały kod (usunięcie nadmiarowych synców) | hang (kolejki priorytetowe ROCm), jakość (zmiana doboru okna) |
| 3 | **akceptacja spekulacji** — 3,81/3,52/3,08 tok/okno; koszty stałe na okno dzielą się przez akceptację | p3: efekt dźwigni ~20% | +0,3…+0,7 tok/okno (GUMBEL, TOP2, SPEC_COST, min-p) | **p1/p2: −2…−5%; p3: −6…−12%** | przełącznik | jakość/tekst (inna akceptacja = inny podział tekstu na okna; greedy output bez zmian, ale trzeba sprawdzić identyczność) |
| 4 | **luki launchowe ~860 kerneli/token, 33% okna jałowe** — fuzje dalszych małych kerneli (QFUSE/LFUSE/EXPERT_V2/TSUM, „normy i drobne" 14,1%) | 14–19% | 1,2–1,4× na części launch-bound | **−2…−4%** | przełączniki / mały kod | jakość (QFUSE zmienia zaokrąglenia), regresje kombinacji (RX7900XTX.md:73) |
| 5 | **cache ekspertów** — hit 87% (7882 ekspertów, 14,95 GiB); +1% hitu ≈ −7,7% missów ≈ −1,2% tokena | 15,3% (etap CPU) | hit 87→90%: −23% etapu CPU | **−2…−3,5%** (ograniczone VRAM) | config (`--adapt-decay/swaps`, HC_REQ8, `--kv q4_0`) | jakość (HC_REQ8 zaokrągla, q4_0 KV), wydajność cache może spaść przy złych parametrach |
| 6 | **czekanie na CPU experts i pula** — DRAM-sufit ~58 GB/s, 7 wątków; każdy ekspert poza GPU kosztuje ~43 us pulą | 15,3% | 1,05–1,15× (bilansowanie linią PCIe, spin_us) | **−1…−2%** | config / mały kod | brak (bitwise) lub jakość (eksperty PCIe zaokrąglają inaczej) |
| 7 | **mapped-reads wierszy CPU (`copy_rows_from_mapped`)** — odczyty PCIe 6,8% okna (3268 us/okno, 80,8 wywołań) | ~5% kerneli etapu CPU | 1,1–1,3× (większe partie, kopiowanie tylko niezerowych, prefetch) | **−0,5…−1%** | mały kod | niskie (bitwise, o ile ta sama kolejność sum) |
| 8 | **gęste gemv (28%)** — 60–85% sufitu pasma | 28% | 1,1–1,3× (WMMA/persistent/swizzle, lepszy re-use wag) | **−3…−8%** | nowy kernel | jakość (zaokrąglenia), duży nakład, ryzyko wiszącego kernela (reguły KNOWLEDGE §6) |
| 9 | **HC (9,7%)** — gr_up/gr_down na 22–29% pasma | 9,7% | 1,1–1,2× (GR_V3 split, GR_DOWN_MAX4) | **−1…−2%** | przełącznik | jakość (GR_V3 zaokrągla kolejność sum) |
| 10 | **sampler/logits gap** (25+16+8 us/token) + start grafu (59 us) | ~0,9% | 1,5–2× | **−0,4…−0,6%** | mały kod | niskie |
| 11 | **linia PCIe dla missów** (~98% wolna; PCIE_MIN1, balans) | — | — | **0…−1,5%** | przełącznik | jakość (eksperty PCIe liczone na GPU zaokrąglają inaczej niż AVX) |

Wnioski: cele 1-4 dają łącznie teoretycznie ~15% na p1/p2 i ~25% na p3, ale tylko przy zachowaniu akceptacji;
realnie oczekuję 8-12% (p1/p2) i 15-20% (p3) po wyczerpaniu dźwigni z sekcji 3, zanim wejdzie nowy kod (5.).

---

## 3. Darmowe dźwignie (nietestowane przełączniki i argumenty)

Oznaczenia: **[gfx12]** = domyślne tylko na RDNA4 (gfx1200/1201), **[gfx1151]** = domyślne na Strix Halo,
**[sm120]** = domyślne na RTX 50. Wszystkie na gfx1100 są opt-in. Test: `kb/trace_run.sh NAZWA KEY=VALUE…`
→ `kb/stage_table.py RUN/pN` (µs/token, największe przerwy) / `kb/pipeline_map.py BAZA/pN RUN/pN`
(diff kernel po kernelu) → brama jakości `strata/rx-tools/bench-detached.sh NAZWA quality KEY=VALUE…`
(KL pierwszego tokenu vs referencja FP16, 32 prompty + 4 zadania agentowe; próg: KL śr ≤ 0,013, top-1 ≥ 31/32).

| Przełącznik / argument | Źródło (file:line) | Co robi | Oczekiwany efekt na gfx1100 | Ryzyko jakości |
|---|---|---|---|---|
| `STRATA_MTP_HIP_PRIO=1` **[gfx12]** | `mtp.cpp:482-489` | Strumień draftera na najwyższym priorytecie → osobna kolejka sprzętowa ROCm; draft biegnie obok commita okna | skrócenie round-tripu i czasu draftu; −2…−5% | brak (bitwise) |
| `STRATA_SPEC_GUMBEL=1` | `sampler.cu:1133` | Próbkowanie draftów z korektą Gumbela; „raise the accepted-draft rate on some machines" | +0,2…+0,6 tok/okno (głównie p3); −2…−6% | tekst identyczny (weryfikacja greedy), ale sprawdzić |
| `STRATA_SPEC_COST=1` | `generate.cpp:18074-18128` | Okno MTP wg oczekiwanych tok/ms (DraftPolicy::keep_draft) zamiast stałego min-p; **wymaga `--pcie-frac 0`** (inaczej silnik zostaje przy starej regule) | adaptacyjny rozmiar okna → −2…−5% | wybór okna zmienia podział tekstu; brama jakości obowiązkowa |
| `STRATA_MTP_TOP2=1` | `mtp.cpp:552` | Tree-draft: runner-up jako drugi draft (diagnostyczny) | wyższa akceptacja kosztem wiersza; +0,1…+0,3 tok/okno | niskie |
| `STRATA_MTP_CATCHUP_ALL=1` | `mtp.cpp:69-72, 1623-1625` | K/V draftera dogania całe okno (odrzucone wiersze włącznie) | lepsze drafty po odrzuceniach; +0,1 tok/okno | niskie |
| `STRATA_HEAD_MIX_MULTI=1` | `mtp.cpp:1117` | Multi-kernel mixu głowy draftera (HIP: opt-in) | −0,3…−0,5% (głowa) | brak (bitwise) |
| `STRATA_TSUM=1` **[gfx12]** | `iq_kernels.cu:6270` | Sumy częściowe jako jeden transponowany butterfly na warp (bitwise); wariant też w mmvq (`native_mmvq.cu:1564-1571`) | na R9700 +1,9%; u nas wcześniej solo +2-7%; −1…−3% | brak (bitwise) |
| `STRATA_ATTN_LANECELL=1` + `STRATA_ATTN_MERGE_V2=1` **[gfx12]** | `qsa_decode_attn.cu:1151, 929` | Scory uwagi po komórce na wątek + merge v2 | para +1,9% na R9700; udział uwagi 3,6% → −0,5…−1% | brak (bitwise) |
| `STRATA_QFUSE=1` **[gfx1151]** | `verify.cpp:298-300, 208` | Aktywacje q8_1 pisane przez producentów (norma wyjściowa GDN); projekcje gęste 2-4 tokenów czytają interleaved kopię | mniej kerneli kwantyzacji (189 wywołań/okno); −1…−2% | zaokrąglenia — brama jakości |
| `STRATA_LFUSE=1` **[gfx1151]** | `verify.cpp:104, 1272-1276` | Fuzje gate/scale shared experta, mniej launchy wokół KV append (warunki: ar_on, n 2..8, bf16 shared) | −0,5…−1,5% | niskie (bitwise przy spełnionych warunkach) |
| `STRATA_EXPERT_V2=1` **[gfx1151]** | `iq_kernels.cu:6267` | Zgrupowane kernele decode: IQ3_S gate/up + IQ4_NL down | wcześniej solo +2-7%; −1…−3% | sprawdzić parzystością/tekstem |
| `STRATA_GDN_SPLIT=1` **[gfx1151]** | `verify_kernels.cu:1098` | Krok GDN na 4 bloki na head (S25/S26) | udział GDN 3,1% → −0,3…−0,6% | niskie |
| `STRATA_GR_V3=1` **[sm120]** | `gr_parity.cpp:342` (+ `fused_gr.cu`) | Odczyt HC rozdzielony na dwa kernele (suma w innej kolejności) | +1,2% decode na RTX PRO 5000; HC 9,7% → −0,5…−1% | zaokrąglenia — brama jakości |
| `STRATA_GR_DOWN_MAX4` / `STRATA_GR_UP_WIDE` | `fused_gr.cu:1251, 455` | Warianty kerneli HC | −0,3…−0,5% | niskie |
| `STRATA_PCIE_MIN1=1` | `expert_source.cpp:4916` | Przy ≥2 missach linia PCIe dostaje co najmniej 1 eksperta (inaczej zaokrągla do 0) | −0,5…−1,5% (odciąża pulę) | eksperty PCIe liczone na GPU — inna numeryka tych wierszy |
| `STRATA_DOORBELL_STORE=1` | `verify.cpp:320, 2137-2138` | Ring doorbella STORE zamiast inkrementacji przez PCIe (A/B #649) | mniej ruchu PCIe w pierścieniu planu; −0,5…−1% | niskie |
| `STRATA_QSA_ROWS=1` | `qsa_select.cu:2098` | Block-scores okna z zapytaniami w rejestrach (≤4 query; te same bity; default na sm_86) | −0,3…−0,6% | brak |
| `STRATA_SCORES_THREAD=1` | `qsa_select.cu:2059` | Scorer thread-per-head (działa na każdej karcie) | −0,2…−0,5% | niskie |
| `STRATA_SAMPLER_ONE_BLOCK=1` | `sampler.cu:1139` | Sampler jednowariantowy bez scratcha (krótsza ścieżka) | skraca przerwy 25+16 us przy samplerze; −0,3…−0,5% | niskie |
| `STRATA_Q6P_GRID=N` | `native_mmvq.cu:2619` | Ręczny grid kernela q6_k (obecnie 106 299×128) | strojenie 4,5% okna; −0,5…−1% | niskie |
| `STRATA_HC_REQ8=1` | `generate.cpp:4442` | Wagi HC jako int8 + skala/32 (~0,56× bajtów) → zwolnione VRAM idzie do cache ekspertów | +1-2% hit-rate → −1…−2% | zaokrąglenia — brama jakości |
| `STRATA_MMVQ_IL_ROWS="typ:n:r0,…"` | `native_mmvq.cu:3736` (+ `MMVQ_IL_TABLE.md`) | Ręczna tabela interleaved mmvq (bez rebuildów) | strojenie 13,5% okna | niskie (bitwise warianty) |
| `--spec 8` / `--spec-min-p` sweep | arg (RX7900XTX.md:59) | Większe okna / inny próg łańcucha (0.85 zmierzone +5% vs 0.5-0.7) | −1…−3% (amortyzacja kosztów stałych; ryzyko marnowanych wierszy) | tekst może się zmienić — test przez `bench-detached.sh` z `ARG--spec=8` |
| `--lookup-chain N` (prompt-lookup) | `generate.cpp:15724` (HOW_IT_WORKS.md:44-46) | Sufiksy z kontekstu jako drafty (gated proposal) | +6-11% na edycjach kodu (p2!); na prozie polskiej mniej, ale >0 | wyjście bez zmian (weryfikacja) |
| `--kv q4_0` | arg (obecnie `--kv int8`) | Połowa bajtów KV w VRAM → więcej slotów cache | +1-2% hit-rate → −1…−2% | KL KV — brama jakości |
| `--adapt-decay` / `--adapt-swaps` sweep (0.9-0.99 / 80-320) | arg (`generate.cpp`; obecnie 0.95/160) | Polityka adaptacji cache | +0-2% hit-rate → −0,5…−2% | niskie (ryzyko regresji cache) |

Nieużyteczne na tym sprzęcie (udokumentowane, żeby nie tracić czasu): `STRATA_POOL_UMWAIT` (tylko MSVC,
`pool.cpp:38-51`), `STRATA_FS_SLOTS` (predykcja routera pokrywa 36% missów, RX7900XTX.md:68),
`STRATA_ADAPT_OVERLAP` (wykluczony przez `--adapt-async 1`, DETAILS.md), `STRATA_PARTIAL_PIN` (wolniejsze +
inna numeryka, UNSLOTH_Q4.md), `STRATA_GRAPH_PRIO` („priority range 0..0" na tej karcie — `verify.cpp:222`).

---

## 4. Plan eksperymentów (kolejne 10)

Konwencja: baza porównawcza = `20261101-172414-prod-fuse5` (p1 13 679 / p2 15 283 / p3 18 786 us/token).
Każdy eksperyment: 1 przebieg trace (3 prompty w środku), decyzja na medianie µs/token z `stage_table.py`
+ identyczności tekstu (`run.json`), a dla wariantów zmieniających numerykę — brama jakości
`bench-detached.sh … quality`. Szum run-to-run 1-2% (KNOWLEDGE.md §3): akceptuję tylko efekty >2% z
pojedynczego przebiegu albo powtarzam 3× (reguła RX7900XTX.md:123-132).

**E1. Wyjaśnienie różnicy fork vs release (warunek wdrożenia +4,7%).**
```
kb/trace_run.sh e1-prod-a EXE=prod ; kb/trace_run.sh e1-prod-b EXE=prod ; kb/trace_run.sh e1-prod-c EXE=prod
kb/trace_run.sh e1-fork-a ; kb/trace_run.sh e1-fork-b ; kb/trace_run.sh e1-fork-c
kb/trace_run.sh e1-prod-h2d EXE=prod STRATA_H2D_GBPS=28.7
kb/pipeline_map.py e1-prod-a/p1 e1-fork-a/p1    (oraz p2, p3)
```
Liczba decyzyjna: różnica median µs/token ≥ 4% i identyczny tekst; jeśli `e1-prod-h2d` domyka różnicę →
przyczyną jest planner (domyślne 12.0 GB/s zamiast zmierzonych 28.4, `generate.cpp:8638`) i wdrożenie jest
środowiskowe; jeśli nie — hipoteza build/toolchain (TheRock 10.1 vs oficjalny ROCm) i wdrożyć binarkę forka.
Oczekiwany wynik: potwierdzenie −4,7% (p1 13 033 vs 13 679, KNOWLEDGE.md §5). Produkcja dopiero po zgodzie
użytkownika + kopia configu (reguła KNOWLEDGE.md §6).

**E2. MTP_HIP_PRIO (round-trip, −2…−5%).**
```
kb/trace_run.sh e2-mtp-prio STRATA_MTP_HIP_PRIO=1
kb/stage_table.py e2-mtp-prio/p1
```
Liczba decyzyjna: µs/token −2%+ na ≥2 z 3 promptów i przerwa `mtp_select -> __amd_rocclr_copyBuffer` wyraźnie
krótsza; sprawdzić `engine.log` (priorytety/hang). Oczekiwane: p1 ≤ 13 300, p3 ≤ 18 100.

**E3. SPEC_GUMBEL (akceptacja, p3).**
```
kb/trace_run.sh e3-gumbel STRATA_SPEC_GUMBEL=1
```
Liczba decyzyjna: tok/okno ↑ (p3: 3,08 → ≥3,3) i µs/token ↓ −2%+; teksty identyczne z bazą.
Oczekiwane: p3 −3…−6%.

**E4. Zestaw bitwise z gfx12 (TSUM + ATTN_LANECELL + ATTN_MERGE_V2).**
```
kb/trace_run.sh e4-gfx12 STRATA_TSUM=1 STRATA_ATTN_LANECELL=1 STRATA_ATTN_MERGE_V2=1
```
Liczba decyzyjna: −2%+ bez zmiany tekstu (na R9700 razem +3,5%, md5 identyczne — `arch_defaults.cpp:30-33`).
Oczekiwane: −2…−4%.

**E5. QFUSE + LFUSE (fuzje launch-bound, brama jakości obowiązkowa).**
```
kb/trace_run.sh e5-qfuse STRATA_QFUSE=1 STRATA_LFUSE=1
strata/rx-tools/bench-detached.sh e5-q quality STRATA_QFUSE=1 STRATA_LFUSE=1
```
Liczba decyzyjna: µs/token −1,5%+ ORAZ KL śr ≤ 0,013, top-1 ≥ 31/32, zadania agentowe tej długości.
Oczekiwane: −1…−2% (wcześniej solo +2-7%, kombinacje nie utrzymały się — RX7900XTX.md:73).

**E6. EXPERT_V2 (cache-hity).**
```
kb/trace_run.sh e6-expv2 STRATA_EXPERT_V2=1
strata/rx-tools/bench-detached.sh e6-q quality STRATA_EXPERT_V2=1
```
Liczba decyzyjna: −1%+ i jakość OK. Oczekiwane: −1…−3% (native_gu_fused/down_lds to 11% okna).

**E7. GR_V3 (HC, zaokrąglenia).**
```
kb/trace_run.sh e7-grv3 STRATA_GR_V3=1
strata/rx-tools/bench-detached.sh e7-q quality STRATA_GR_V3=1
```
Liczba decyzyjna: −0,5%+ i KL OK. Oczekiwane: −0,5…−1%.

**E8. PCIE_MIN1 (odciążenie puli CPU).**
```
kb/trace_run.sh e8-pciemin1 STRATA_PCIE_MIN1=1
strata/rx-tools/bench-detached.sh e8-q quality STRATA_PCIE_MIN1=1
```
Liczba decyzyjna: −0,5%+ na p1/p3 (etap CPU 15-18%) i jakość OK. Oczekiwane: −0,5…−1,5%.

**E9. DOORBELL_STORE (ruch PCIe planu).**
```
kb/trace_run.sh e9-doorbell STRATA_DOORBELL_STORE=1
```
Liczba decyzyjna: −0,5%+ i identyczny tekst. Oczekiwane: −0,5…−1%.

**E10. SPEC_COST + zdjęcie --pcie-frac (adaptacyjny rozmiar okna; wymaga zmiany argumentu → bench-detached).**
```
strata/rx-tools/bench-detached.sh e10-spec-cost decode STRATA_SPEC_COST=1 ARG--pcie-frac=0
strata/rx-tools/bench-detached.sh e10-spec-cost-q quality STRATA_SPEC_COST=1 ARG--pcie-frac=0
```
Liczba decyzyjna: decode tok/s +2%+ przy 5K/64K i jakość OK. Oczekiwane: −2…−5%; jeżeli wygra —
przed wdrożeniem zmierzyć osobno skutek zdjęcia `--pcie-frac` (balans CPU/PCIe) jednym trace_runem z EXE
domyślnym i `--pcie-frac` niezmienionym jako kontrolą.

Po E1-E10: kombinacja zwycięzców jako jeden wariant (3 powtórzenia × 3 prompty, `kb/rep_table.py`), potem
jakość, potem produkcja z kopią configu i zgodą (KNOWLEDGE.md §6).

---

## 5. Twoja propozycja — jak przebudować potok

**(a) Akceptacja i budowa następnego okna po stronie GPU (redesign; szacuję −7…−10% na token, więcej w p3).**
Dziś każdy token płaci ~1,4-2,0 ms host round-tripu: host spina drafty z mapped, syncuje, porównuje tokeny,
składa okno, uruchamia graf. Propozycja: po samplerze weryfikator na GPU (w tym samym grafie) porównuje
`out` z draftami i sam składa wiersze następnego okna; host tylko asynchronicznie odbiera gotowe tokeny do
wypisania. Eliminuje to niemal całe 10,5% (cel 2) i część luki startu grafu (59 us/okno). Ograniczenia:
pętla „kto jest w cache" nadal wymaga hosta (plan ekspertów i doorbell) — trzeba wydzielić wątek
obsługujący doorbelle niezależnie od budowy okien; wariant mniejszy: sterowanie oknem w osobnym wątku hosta,
żeby spin na draftach nie blokował serwowania planu. Zgodne z regułą bezpieczeństwa: bez spin-kerneli
międzyblokowych (KNOWLEDGE.md §6).

**(b) Spekulacyjny start round-grafu draftera (mały-redesign; −2…−3%).**
Round-graf draftera dla okna K+1 zależy tylko od tokenów okna K (znanych od razu po samplerze okna K,
`capture_round` `mtp.cpp:1318-1364`), a nie od wyniku commita. Uruchomienie go od razu po samplerze (obok
commita, na osobnej kolejce — MTP_HIP_PRIO z E2) ukrywa czas draftera pod commitem i skraca round-trip o
czas round-grafu. Kroki „step" pozostają po akceptacji (zależą od wiersza a).

**(c) Drugi drafter prompt-lookup dla polskiego (config+mały kod; −10…−15% na p3).**
p3 płaci ~18,8 ms/token przy oknach 3,08 tok. Sufiksy z kontekstu (`--lookup-chain`, HOW_IT_WORKS.md:44-46)
to drafty prawie darmowe (sam lookup), a polska proza powtarza frazy; w p2 (kod, edycje) to zmierzone
+6-11% upstreamu. Oczekiwany wzrost akceptacji p3 do ~4 tok/okno przy koszcie per-okno prawie bez zmian →
~−15% na p3. Brama jakości obowiązkowa (gated proposal nie zmienia wyjścia, ale trzeba to zmierzyć).

**(d) Mega-fuzja FFN (nowy kernel; −5…−8%).**
Router + plan + shared expert + eksperci + combine + normy = dziś ~24 kernele/połówkę FFN, w większości
launch-bound („normy i drobne" 14,1% to głównie przerwy). Jeden kernel na połówkę FFN (odczyt HC down do
zapisu przed HC up) usuwa kilkaset z ~860 kerneli/token i ich przerwy. Największy zysk poza celami 1-3,
ale i największe ryzyko (nowy kod, reguły KNOWLEDGE §6) — robić po wyczerpaniu sekcji 3.

**(e) Trzecia „linia" PCIe z dynamicznym udziałem (mały kod; −1…−2%).**
PCIe jest ~98% wolne w decode (RX7900XTX.md:84), a pula CPU na suficie DRAM. Zamiast stałego
`--pcie-frac 0.20`: udział per warstwa wg długości kolejki puli (dane już są: `bal_p_`/`bal_nc_`,
`verify.cpp:3282-3286), żeby linia PCIe przejmowała missy dokładnie wtedy, gdy pula jest przeciążona.
Ograniczenie zmierzone: ekspert przez PCIe ~85 us szeregowo — musi lecieć z prefetchem, nie na krytycznej
ścieżce.

**(f) Priorytetyzacja wdrożeń w liczbach.** Łączny realny potencjał: E1+E2+E3+E4 (przełączniki) ≈
−8…−12% (p1/p2), −15…−20% (p3); potem (a)+(b) ≈ dalsze −8…−12%; (c) na p3 ≈ −15%; (d)+(e) na końcu.
Szacunek całkowity: 73 → 82-88 tok/s (p1), 53 → 63-68 tok/s (p3) — z czego ~połowa bez nowego kodu.

---

## Załącznik: pliki źródłowe i pomiarowe użyte w raporcie

- Pomiary: `data/prod-now-p1/p2/p3-map.txt`, `-stages.txt`, `data/stage-bandwidth.txt`,
  `data/switch-sweep-report.md`, `data/rep-series-fork.txt`, `data/example-diff-fuse-wait.txt`.
- Kod: `strata/src/core/verify.cpp`, `mtp.cpp`, `expert_source.cpp`, `arch_defaults.cpp`,
  `strata/src/kernels/cuda/{verify_kernels,elementwise,native_mmvq,iq_kernels,sampler,qsa_select,qsa_decode_attn,fused_gr}.cu`,
  `strata/src/kernels/cpu/pool.cpp`, `strata/src/program/generate.cpp`.
- Docs: `strata/docs/RX7900XTX.md`, `HOW_IT_WORKS.md`, `DETAILS.md`, `AMD_HIP.md`, `MMVQ_IL_TABLE.md`.
- Narzędzia: `kb/trace_run.sh`, `kb/pipeline_map.py`, `kb/stage_table.py`, `kb/rep_table.py`,
  `strata/rx-tools/bench-detached.sh`.
