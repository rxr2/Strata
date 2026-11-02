# Knowledge base: Strata decode pipeline on the RX 7900 XTX (state 2026-11-01 17:30)

Everything here is measured unless marked "hypothesis". Files are relative to this directory.

## 1. Hardware and model
- GPU: AMD Radeon RX 7900 XTX, gfx1100 (RDNA3), wave32, 96 CUs, 24 GB VRAM, 96 MB Infinity Cache.
  VRAM clock raised to 2754 MHz. Measured read bandwidth: ~1015 GB/s peak (hot), ~645 GB/s with cold rotating weights.
- PCIe 4.0 x16, ~28.7 GB/s measured host->device. CPU: Zen 5 with AVX-512 (7 pool workers for CPU experts), 36 GiB of
  experts held resident in RAM.
- Model: Qwen3.8-Flash-Next-GSQ-RCO (abliterated), IQ3_S, ~125B-class MoE, 48 layers. Layers are a mix of
  GDN (gated delta net, recurrent) mixers and QSA (attention) mixers, each followed by an MoE FFN half
  (router, shared expert, routed experts). Hyper-connections (HC, `gr_down`/`gr_up` kernels) mix the residual streams
  at every half.
- The experts do not all fit in VRAM: a GPU expert cache holds 7882 experts (14.95 GiB). Experts that miss are either
  computed on the CPU (AVX-512 pool) from RAM, with their output rows read back by the GPU through mapped host memory,
  or (a fraction set by `--pcie-frac 0.20`) streamed over PCIe. Cache hit rate in the traces: ~87%.
- Speculative decoding: MTP drafter (`--spec 6`, `--mtp ...`), so one verify pass ("window") accepts several tokens.

## 2. Engine
- Source snapshot (read-only copy of the fork at commit cc21cbf4): `strata/src`, `strata/docs`, `strata/rx-tools`.
  Most useful docs: `strata/docs/HOW_IT_WORKS.md`, `DETAILS.md`, `AMD_HIP.md`, `AMD_HIP_PERFORMANCE.md`, `RX7900XTX.md`.
- Decode code: `src/core/verify.cpp` (the verify window, expert plan, waits), `src/core/mtp.cpp` (drafter, HIP graphs
  captured per round/step), `src/kernels/cuda/*.cu` (HIP kernels; CUDA syntax compiled with HIP).
- Production config: `data/prod-config.json` (engine args + env). Production binary is the release build
  `~/llm/strata/strata`; the fork build `build-rx/strata` (same switches) measured ~5% faster per token (section 5).
- All 658 environment switches with source location, source comment, doc line and production value: `kb/SWITCHES.md`.
  Many fusions are default-on only for gfx12 (RDNA4) and opt-in on gfx1100.

## 3. Measurement tools (all exist and work)
- `kb/trace_run.sh NAME [KEY=VALUE ...] [EXE=prod|path]`: stops production, runs the engine under
  `rocprofv3 --kernel-trace` with the production config + given env, sends a warm-up and then 3 fixed prompts
  (greedy, seed 7, 320 tokens each: p1 ring all-reduce explanation, p2 Python LRU cache code, p3 Polish prose),
  writes `trace.db` + `pN/run.json`, restarts production. ~3 min per run.
- `kb/pipeline_map.py RUN/pN`: per decode window (cut at `gdn_step_commit_layers_kernel`): kernels vs gaps, layer halves,
  per kernel: calls, median us, us/window, gap before it, grid x workgroup, VGPR, SGPR, LDS, scratch.
- `kb/pipeline_map.py A/pN B/pN`: A/B per generated token, kernel by kernel (kernel us and gap us).
- `kb/stage_table.py RUN/pN`: per token time per stage + the largest gaps (which kernel pair they sit between).
- `kb/rep_table.py LOG`: repeated runs: us/token per rep, tokens per window, us per forward pass, number of distinct texts.
- Quality: `strata/rx-tools/bench-detached.sh NAME quality [KEY=VALUE]`: KL of the first token vs an FP16 reference
  over 32 prompts + 4 agent tasks (characters equal to the reference). ~4 min.
- Noise: run-to-run spread of us/token ~1-2% (an occasional outlier of +10% on the first rep). Always compare the same
  prompt, and check that the answer text is the same (different text => different speculative acceptance =>
  per-token time not comparable; per-pass time still is).

## 4. Current state (production, 5 fusion switches on), files `data/prod-now-pN-*.txt`
| prompt | us/token | tok/s (GPU time) | tokens per window | kernels per window |
|---|---|---|---|---|
| p1 explain | 13 679 | 73.1 | 3.81 | 3260 |
| p2 code | 15 283 | 65.4 | 3.52 | 3001 |
| p3 Polish | 18 786 | 53.2 | 3.08 | 3717 |

Per token, p1 (see `data/prod-now-p1-stages.txt`; "gap" = idle GPU time before the kernel):
| stage | kernels us | gaps us | total | share |
|---|---|---|---|---|
| dense matmuls (attn/GDN projections, shared expert, lm_head; mmvq/mmvf + q8 quantize) | 3006 | 820 | 3826 | 28% |
| routed experts on GPU (cache hits: gu_fused, down_lds, fetch_blobs, combine...) | 2211 | 821 | 3032 | 22% |
| waiting for CPU experts (wait_copy_i32, copy_rows_from_mapped, doorbell) | 1694 | 393 | 2087 | 15% |
| host copy after the MTP draft (gap mtp_select_kernel -> __amd_rocclr_copyBuffer) | ~0 | 1428 | ~1430 | 10.5% |
| HC (gr_down/gr_up) | 1024 | 307 | 1331 | 10% |
| attention, GDN recurrence, router, norms, other | | | ~1950 | 14% |
- ~860 kernels per generated token; ~33% of the window is idle GPU between kernels (~3 us launch gap each).
- The single largest idle point: after `mtp_select_kernel` the GPU idles 1.4 ms (p1, p2) to 2.0 ms (p3) per token
  before a host `copyBuffer` (hipMemcpy). See `src/core/mtp.cpp` around `capture_round`/`capture_step` and the code
  that launches the drafter graphs (hypothesis: the host waits for the draft tokens before it can launch the next
  verify window).
- Per-stage bandwidth table (older, before the switches): `data/stage-bandwidth.txt` (dense gemv 60-85% of the VRAM
  ceiling, VRAM expert hits ~55%, small kernels 9-14% = launch bound).

## 5. What has been done and measured
- HC kernel rewrite (agents, a day of work): 1.195x faster in isolation, only ~1-2% in the engine (HC is ~10% of a token).
  Lesson: measure the whole pipeline and compute the maximum gain (share x achievable speedup) before choosing a target.
- Switch sweep (`data/switch-sweep-report.md`, `data/rep-series-fork.txt`):
  FUSE_WAIT -2.4%, QFUSE_HC -2.3%, ONE_TOKEN_COMMIT -3.9%, FUSE_CONVAB ~-1%, FUSE_HEAD_GR ~-1%, FUSE_HITS 0,
  VERIFY_DEVICE_PLAN +1.9% (worse). All five together: -3.2..-6.5% per token, KL unchanged (0.0120 vs 0.0129, top-1 31/32).
  Now on in production.
- Fork build vs release build (same config): fork ~5% faster per token (p1 13 033 vs 13 679 us with the 5 switches).
  Not yet explained, not yet deployed.
- Example of a kernel-by-kernel diff: `data/example-diff-fuse-wait.txt`.

## 6. Rules (safety, hard)
- Never write kernels that spin-wait on global memory written by another kernel/block, grid barriers or cooperative
  launches: one such kernel hung the GPU (MES reset failed, hard reboot).
- Production config changes only with a backup and the user's consent. Never push to upstream repositories.
- Do not test models smaller than the Flash-Next class. No secrets in files or output.

## 2026-11-02: Tor A (akceptacja) i Tor B (cache) — wyniki (raport: REPORT-ds-profiling.md)

- 3 własne ślady: p1 84,8 / p2 83,5 / p3 65,9 tok/s pod profilerem (bez: ~94). Profiler 13–22%, najwięcej p2.
  Okno 25,4–29,5 ms; T 1,90–2,82; trafienia 78,8–87,4%.
- Przerwy: pusty zależny kernel 2,5–3,2 µs (graf = strumień; 200 węzłów = 0,51 ms). `AMD_DIRECT_DISPATCH`,
  `GPU_MAX_HW_QUEUES`, `HIP_FORCE_DEV_KERNARG`, `AMD_OPT_FLUSH`, `GPU_MAX_COMMAND_BUFFERS` nic nie zmieniają.
  100 węzłów mniej = 0,25–0,3 ms/token tylko, gdy GPU nie czeka; wcześniejsze fuzje ~0.
- Próg: 0,85 w optimum. 0,75 +1,0% (szum), 0,65 +0,9%, 0,55 −3,5%. Krańcowy koszt tokenu 8,6 / 11,4 / 64,7 ms.
  Między klasami tok/win koreluje z tok/s (0,68), ale próg dokłada wiersze w tej samej klasie i okno drożeje 1:1.
  Prawdziwy lewar: akceptacja przy stałym T (99,5% case = 175 tok/s).
- Polski: T 1,86, tok/win 1,65, akceptacja 75–77%; próg 0,75 daje +1,9%, `--lookup-chain 1` −1,0%. Potrzebny lepszy
  drafter, nie próg.
- Trafienia per warstwa: 63–81%; najgorsza 0 (63,2%, 217 slotów), najlepsze 15/16/31/32 (80–81%, 116–143 slotów).
  Liczba slotów nie tłumaczy trafień — różnorodność routingu. Przeprofilowanie: 40% par innych, trafienia −0,9 pkt,
  tok/s −3,1%; nie podmieniać profilu. `--vram-reserve-mib 2560` +0,81 pkt, −0,5%; `--kv q4_0` +1,57 pkt, −3,2%;
  `--adapt-decay 0.9` +0,83 pkt, −0,6%; `HC_REQ8` nie startuje z `HC_Q8=1`; `--pcie-frac` 0/0,4 = −6,2/−4,2%.
- Kontekst 46,7K: 76,2 tok/s, akceptacja 68%, trafienia 78,2% + 2,2% PCIe. Tabela 62K (85 tok/s, 84,5%, 79%) różni
  się akceptacją, nie trafieniami.
- Prefill: 2679/2951/3057 tok/s (12/32/64K), GPU timeline = wall; 18 GB/żądanie z NVMe, „waiting for each chunk”
  1,3–2,6 s (6–12%); polityka lend/evict to max ~2,5 s/64K.
- Kod: branch `rx-ds-profile` (commit cbe4a12e) tylko `STRATA_HIT_STATS=1`. Profil: `~/rx-perf-lab/profiles/20261102-ds/`.
- **Sufit draftu (2026-11-02, CEILING-ds-mtp.md):** przy pierwszym odrzuceniu token targetu jest w top-16
  głównego headu w 95,7% (23 odrzucenia/10 żądań), a w top-16 headu MTP tylko w 31,5% (54 odrzucenia);
  wszystkie głębokości: 88,9% vs 38,5%. Główny head odrzuca pierwszy draft 2,3× rzadziej. Polski: subset
  25 odrzuceń d0/1 w top-16, main head 11/10. Samo +2 591 polskich tokenów do draft-vocabu (Wikipedia+README,
  pokrycie 99%) dało 92,8→92,8 tok/s; liczą się wagi headu, nie vocab. `STRATA_MTP_FULL_HEAD=1` (główny head
  jako drafter) +2,3% średnio, PL +3,4/+7,2%, repeat +23,3%, JSON −10,4%, proza −4,7% (1 przebieg; wymaga 3 par).
  Diagnostyk: `STRATA_MTP_TOPK=16`, commit 541df347.
- **Nota wykonalności treningu MTP (2026-11-02, FEASIBILITY-ds-mtp-training.md):** MTP 2,607 mld param.
  (dense 90,6 M + eksperci 2,517 mld); dense-only/LoRA r8 (119 M) mieści się w 24 GB (~10–14 GB), pełne eksperci
  nie (41,7 GB z AdamW). Zrzut Rin 10 240 BF16/token = 20,5 KB → 20,5 GB/mln; root 79 GB wolny (1M tak, 3M ledwo,
  10M nie); prefill ~3k tok/s (1M ≈ 6 min), decode 94 tok/s. Dane: 35% kod, 20% JSON/SQL, 20% PL, 15% EN, 5% math,
  5% repeat; 10% >16k. Prywatność: lokalnie, szyfrowanie, redakcja, split po żądaniu. Gate offline: top-16 @d0 ≥75%
  (teraz 31,5%, sufit 95,7%), PL akceptacja ≥85%; potem A/B 3 pary ≥+3%. PyTorch 2.13.0+rocm7.1 cp314 5,86 GB
  (wheel ma ROCm 7.1, nie TheRock 10.1). Czas 3–5 tygodni; go/no-go po 2 tyg. Nic nie zainstalowano/nie trenowano.
- **Trzecie ramię — słownik szkicu (2026-11-02, DRAFT-VOCAB-ds.md):** `dhead_` to już główny head targetu
  ograniczony do `draft_vocab.bin` (`gather_rows(head_->weights())`), więc „trzecie ramię” = zawartość słownika.
  Baza 106 299 id. PL-specific (base + 1 272 tokeny z LR PL/EN) w 4 parach: +1,47% średnio, PL tech +11,0%,
  PL travel +2,2%, JSON +17,2% (bimodalny), repeat −5,3%, math −2,1%, file_edit −2,5%, proza −1,8%.
  3 pary base→wariant dały +2,88%, ale odwrotna para obniżyła do +1,47% — efekt globalny za mały (próg 3%).
  Pełny main head: 1 przebieg +2,3%, PL +3,4/+7,2%, repeat +23,3%, JSON −10,4%, proza −4,7%.
  Decyzja: trening na wynajętym GPU z danymi publicznymi/syntetycznymi; nic nie zainstalowano.
- **Sweep rozmiaru słownika (2026-11-02, SWEEP-ds-vocab.md):** 106k/140k/180k/248k, 3 bloki losowe, NOPROF.
  Head Q6_K 2100 B/wiersz: 212,9/280,4/360,5/497,3 MiB; head gemv 246/320/405/561 µs; krok draftu 792/879/974/1161 µs;
  ~930 GB/s (memory-bound). d0: 33/23/19/15; top-16 przy d0: 33/78/90/93%. A/B: 106k 90,79; 140k 93,32 (+2,80% ±1,88);
  180k 93,33 (+2,80% ±2,63); 248k 92,27 (+1,64% ±1,37). Per klasa 140k: PL tech +8,2%, PL travel +4,9%, JSON +13,5%,
  repeat +8,6%, proza −4,1%, summary −2,3%. 140k najlepszy netto; 248k gubi na koszcie headu (1,52 ms/okno).
  Dwa etapy: 106k + pełny head przy p1<0,85 (~35% kroków) ~0,445 ms/krok vs 0,246/0,561; hipoteza ~1,1% okna.
  Q4 head test w toku; wynik dopisać.
- **Tail skip (2026-11-02, REPORT-ds-tailskip.md):** `STRATA_ROUTE_TAIL_SKIP=7` na gfx1100 (jawna zmienna) jest ON;
  pomija 36,9–37,5% chybień (5–12 tys. ekspertów/żądanie). Random A/B 3 bloki, EXE=prod, NOPROF:
  86,94 → 94,93 tok/s = **+9,19% ±2,79** (bloki +6,59/+8,84/+12,14). PCIe rows −36/−43/−41%, CPU pool −34/−38%,
  cpuexp −6/−28/−21%; plan_wait nie spada. Quality: KL 0,02177 (base 0,01640) ≤0,0235, top-1 29/32 (base 30/32);
  proza −8,7%, JSON acc 82,0→77,6/tok_win 2,80→2,18; edit identyczny, newcode 761→749, json 485→256.
  D single: R=6 101,64, R=8 91,97; pcie 0,10 94,21, 0,30 98,32; q4-140 92,86, q4-140+tail7 **104,71**;
  reserve 3072+tail7 97,89, reserve 2048+tail7 90,67 (nie schodzić). Rekomendacja: tail skip warunkowo
  (top-1 29/32 do akceptacji użytkownika); q4+tail i pcie 0,30 wymagają 3 par i osobnej bramki KL.
- **WDROŻONE 2026-11-02 (na polecenie użytkownika):** `strata-rx.json` = tail skip 7 + `--mtp-draft-vocab`
  140k + `--mtp-q4 head`; backup `strata-rx.json.bak-20261102-143040` (SHA 97a10dbd…). Combined quality:
  KL 0,01747 (base 0,01640), top-1 29/32 (base 30/32); 4k 0,01990/21/24, 16k 0,01021/8/8. Smoke 3 stałe
  prompty: p1 96,9 / p2 112,7 / p3 87,6, średnia 99,07 (+5,2% vs 94,2); p1 traci (proza), p3 +16%. Suite
  q4+tail 104,71 (single). Nie wdrożono pcie 0,30, R=6, reserve 2048. Rollback: kopia + restart.
