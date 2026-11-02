# STRATA_* switches read by the engine (auto-generated from ~/Projekty/strata-rx7900/src)
658 switches. PROD = value in the RX production config. The comment is the source comment next to the read.
Look in the source (file:line) for the exact default and behaviour; many have gfx12-only defaults.

## src/core
- **STRATA_ADAPT_ASYNC** — src/core/adapt_async_default_test.cpp:46
  `{ AdaptAsyncAuto a = good(); a.env = 0; CHECK(!strata::core::adapt_async_self_decides(a, &why)); CHECK(why && std::strstr(why, "STRATA_ADAPT_ASYNC")); }`
- **STRATA_ARENA_LOCK** — src/core/pinned.cu:512 (+4 more reads)
  `const char* env = std::getenv("STRATA_ARENA_LOCK");`
  // Plan v0.3 P0.1: keep it RESIDENT instead. Unpinned, Windows trims the arena under memory pressure and the CPU pool's rate then depends on the OS; locking it through the working set needs no special privilege. STRATA_ARENA_LOCK=0 is the A/B arm.
- **STRATA_ARENA_MMAP** — src/program/generate.cpp:2893 (+4 more reads) docs: DETAILS.md
  `if (std::getenv("STRATA_ARENA_MMAP") && std::getenv("STRATA_ARENA_MMAP")[0] == '1')`
  // pages in place (a GPU userptr), and keeps them - so every expert the VRAM fill copied from the mapped experts.bin stayed resident, the release of the VRAM-held ones was undone by the driver at once, and a 32 GB PC ran with ~0.3 GB free: the kernel swapped, and a turn's checkpoint took 25-80 s.  Above this size ROCclr stages through its own pinned buffers instead; decode is unchanged (49.06 vs 49.1
  doc (DETAILS.md): - Linux, opt-in: `STRATA_ARENA_MMAP=1` maps a native pack's expert arena read-only from `experts.bin` instead of reading
- **STRATA_ARENA_PIN_GIB** — src/core/pinned.cu:347 (+1 more reads) docs: AMD_HIP.md, BATCHING.md, DETAILS.md, MULTI_GPU.md, PREFILL_HEAD_ALIAS.md, SECOND_GPU.md, STRIX_HALO.md
  `const char* e = std::getenv("STRATA_ARENA_PIN_GIB");`
  doc (DETAILS.md): `STRATA_ARENA_PIN_GIB` (29 by default on Windows) instead of the first ~30 GiB.
- **STRATA_ARENA_THP** — src/core/pinned.cu:298
  `} else if (std::getenv("STRATA_NO_LARGEPAGES") == nullptr && std::getenv("STRATA_ARENA_THP") == nullptr &&`
- **STRATA_BATCH_ATTN_ROWS** — src/core/verify.cpp:1944 docs: BATCHING.md
  `const char* v = std::getenv("STRATA_BATCH_ATTN_ROWS");`
  doc (BATCHING.md): | `STRATA_BATCH_ATTN_ROWS=1` | block scores, top-k and decode attention of all the window's rows (up to 8) in one launch each. Not with KV streaming (a slot with `kv_mode` 1 keeps the per-row launches). |
- **STRATA_BATCH_GDN_GROUPS** — src/core/verify.cpp:1640 (+1 more reads) docs: BATCHING.md
  `const char* v = std::getenv("STRATA_BATCH_GDN_GROUPS");`
  doc (BATCHING.md): | `STRATA_BATCH_GDN_GROUPS=1` | the GDN recurrence in the window, and the commit of 1-row groups, for all slots in one launch. The conv commits stay per slot. |
- **STRATA_BATCH_SELF_COMMIT** — src/core/verify.cpp:330 (+1 more reads) docs: BATCHING.md
  `const bool g_batch_self_commit = env_on("STRATA_BATCH_SELF_COMMIT");`
  // as a one-token window does (record_window): the GDN conv histories and states advance inside the window graph, and no commit graph runs after it.  Such a window's commit is unconditional (each slot keeps its one row), and the rest of the commit graph only repeats what the window wrote: the indexer tails are put back and appended again from the same rows, the PLE histories are put back to the windo
  doc (BATCHING.md): | `STRATA_BATCH_SELF_COMMIT=1` | a one-row-per-slot window advances the GDN state itself, no commit graph |
- **STRATA_CKPT_ASYNC** — src/core/conversation_state.cpp:212 docs: DETAILS.md
  `static const bool on = [] { const char* v = std::getenv("STRATA_CKPT_ASYNC"); return v != nullptr && v[0] == '1'; }();`
  doc (DETAILS.md): Where the card sits behind a slow host link, the conversation cache's copies are on the critical path of the next request. A turn checkpoint copies the DeltaNet state (118 MB on Qwen3.8-Flash-Next) from the card to the host. Parking a conversation copies its K/V and its checkpoints before the next p
- **STRATA_CKPT_GATHER** — src/core/conversation_state.cpp:228 docs: DETAILS.md
  `static const bool on = [] { const char* v = std::getenv("STRATA_CKPT_GATHER"); return v != nullptr && v[0] == '1'; }();`
  doc (DETAILS.md): Where the card sits behind a slow host link, the conversation cache's copies are on the critical path of the next request. A turn checkpoint copies the DeltaNet state (118 MB on Qwen3.8-Flash-Next) from the card to the host. Parking a conversation copies its K/V and its checkpoints before the next p
- **STRATA_CKPT_VRAM_SLOTS** — src/core/conversation_state.cpp:189 docs: DETAILS.md
  `static const int n = [] { const char* v = std::getenv("STRATA_CKPT_VRAM_SLOTS"); return v ? std::max(0, std::min(16, std::atoi(v))) : 0; }();`
  doc (DETAILS.md): | `STRATA_CKPT_VRAM_SLOTS=N` (0-16, with `STRATA_CKPT_ASYNC=1`) | The last N saved states also stay in VRAM (N x 118 MB, only while 1.5 GB stay free). A restore from one copies card-to-card. | restore 114-126 -> 28-47 ms |
- **STRATA_COLD_OVERLAP** — src/core/expert_source.cpp:2204 (+3 more reads) docs: DETAILS.md, release-notes-0.2.0.md
  `const char* v = std::getenv("STRATA_COLD_OVERLAP");`
  doc (DETAILS.md): | Zero-copy | `STRATA_COLD_OVERLAP=4` (`0` = off) | An expert whose three tensors' pages are all in the page cache is computed straight from the mapping, with no staging copy. |
- **STRATA_COMMIT_BATCH** — src/core/verify.cpp:2787
  `static const bool commit_batch = [] { const char* e = std::getenv("STRATA_COMMIT_BATCH"); return !e || e[0] != '0'; }();`
- **STRATA_COMMIT_SYNC** — src/core/verify.cpp:3637
  `void Verifier::set_commit_async(bool on) { g_commit_async = on && std::getenv("STRATA_COMMIT_SYNC") == nullptr; }`
- **STRATA_COMMIT_TIMING** — src/core/verify.cpp:3661
  `CommitTiming() { const char* v = std::getenv("STRATA_COMMIT_TIMING"); on = v != nullptr && v[0] == '1'; }`
- **STRATA_COPY_HIP_PRIO** — src/core/verify.cpp:1122
  `static const bool cp = [] { const char* v = std::getenv("STRATA_COPY_HIP_PRIO"); return v != nullptr && std::atoi(v) != 0; }();`
- **STRATA_DBG_NAN** — src/prefill/prefill.cpp:4715 (+4 more reads) docs: AMD_HIP.md, INTEL.md
  `static const bool ws_dbg = std::getenv("STRATA_DBG_NAN") != nullptr;`
  // are read where they lie in the expert cache (offsets from its base).  Only where both products beat the per-group MMQ at this layer's rows per expert, H can be q8_1 in one pass (no Hadamard, NVFP4 or FP4 rows; not STRATA_DBG_NAN, which reads H in floats), and not the fused layout (its Hq holds stream_all_min() - 1 tokens' rows).
  doc (AMD_HIP.md): | `STRATA_HIP_PROMPT_F16=1` | Runs the 16-bit prompt GEMMs FP16 in and out (the engine prints a tip on gfx103x). `STRATA_F16_RANGE=1` prints, per prompt, the largest value that entered or left FP16 (FP16 ends at 65504); `STRATA_DBG_NAN=1` counts non-finite FP16 outputs. Checks: [2026-10-04-rdna2-fp1
- **STRATA_DEC_BATCH** — src/core/expert_source.cpp:5022 (+2 more reads)
  `static const bool dec_batch = [] { const char* v = std::getenv("STRATA_DEC_BATCH"); return v == nullptr || std::atoi(v) != 0; }();`
- **STRATA_DEFERRED_REGISTER** — src/core/expert_source.cpp:5902
  `const char* defer_env = std::getenv("STRATA_DEFERRED_REGISTER");`
- **STRATA_DF2_FORK** — src/core/dflash2.cpp:451
  `static const bool fork_on = [] { const char* e = std::getenv("STRATA_DF2_FORK"); return e && e[0] ? e[0] == '1' : fork_default; }();`
- **STRATA_DF2_PRIO** — src/core/dflash2.cpp:199 (+1 more reads)
  `static const bool hi_prio = [] { const char* e = std::getenv("STRATA_DF2_PRIO"); return e && e[0] == '1'; }();`
- **STRATA_DF2_PROFILE** — src/core/dflash2.cpp:218
  `if (const char* e = std::getenv("STRATA_DF2_PROFILE"); e && e[0] == '1') prof_ = new Prof();`
- **STRATA_DF2_SKIP** — src/core/dflash2.cpp:79
  `static const std::string list = [] { const char* e = std::getenv("STRATA_DF2_SKIP"); return std::string(e ? e : ""); }();`
- **STRATA_DF2_TIMING** — src/core/dflash2.cpp:219
  `if (const char* e = std::getenv("STRATA_DF2_TIMING"); e && e[0] == '1') {`
- **STRATA_DF_BRANCH** — src/core/verify.cpp:1148
  `const char* v = std::getenv("STRATA_DF_BRANCH");`
  // stage's window with the branches stopped inside its graph when an NVML query (nvidia-smi) came between requests (2x RTX 3090 and 2x RTX 2080 Ti, #905); never seen on Windows.  0 / unset: one stream, as before
- **STRATA_DF_PLE** — src/core/verify.cpp:1431
  `const char* e = std::getenv("STRATA_DF_PLE");`
- **STRATA_DF_QB_Q4** — src/core/verify.cpp:1718
  `const char* e = std::getenv("STRATA_DF_QB_Q4");`
- **STRATA_DOORBELL_STORE** — src/core/verify.cpp:320
  `const bool g_doorbell_store = env_on("STRATA_DOORBELL_STORE");`
- **STRATA_DRAFT_TIMING** — src/prefill/prefill.cpp:1998 (+1 more reads)
  `static const bool timing = std::getenv("STRATA_DRAFT_TIMING") != nullptr;   // debug: where this pass's time goes`
  // debug: where this pass's time goes
- **STRATA_DUMMY_NODES** — src/core/verify.cpp:1503
  `static const int dummy = [] { const char* e = std::getenv("STRATA_DUMMY_NODES"); return e != nullptr ? std::atoi(e) : 0; }();`
- **STRATA_EMBED_VRAM** — src/core/native_head.cpp:155 docs: DETAILS.md
  `if (const char* ev = std::getenv("STRATA_EMBED_VRAM"); ev != nullptr && ev[0] == '1') {`
  // bytes, read by the same gather kernels through dev_ (bitwise the same rows); what changes is where a prompt's scattered row reads go: over a PCIe Gen2 x4 link they cost more than the table's size in VRAM is worth. Taken only with the table plus 512 MiB free; otherwise, or when the upload fails, the mapped placement below is used as before (and the fallback is said).
  doc (DETAILS.md): | `STRATA_PLE_COMPACT=1`, `STRATA_PLE_COPY_STREAM=1`, `STRATA_EMBED_VRAM=1`, `STRATA_DEQUANT_SIDE=1` | The PLE rows go up raw and are dequantized on the card, on their own stream; the token-embedding table in VRAM; the dense dequant on a side stream (CUDA only). All bitwise. | prompts +2.2 % to +2.6
- **STRATA_EXCHANGE_ROTATE** — src/kernels/cpu/pool.cpp:633 (+5 more reads) docs: DETAILS.md, EXCHANGE_ROTATION.md
  `const char* rotate = std::getenv("STRATA_EXCHANGE_ROTATE");`
  // the expert source's own reading of it (expert_source.cpp): exactly "1"
  doc (DETAILS.md): - `STRATA_EXCHANGE_ROTATE=1` (opt-in): an adaptive swap hands buffer ownership over instead of copying the evicted blob into
- **STRATA_FETCH_PVM** — src/core/expert_source.cpp:2370
  `const char* v = std::getenv("STRATA_FETCH_PVM");`
- **STRATA_FILE_CACHE_OLD_RULE** — src/core/expert_source.cpp:892 docs: AMD_HIP.md
  `if (const char* r = std::getenv("STRATA_FILE_CACHE_OLD_RULE"); r != nullptr && r[0] != '\0') old_rule = r[0] != '0';`
  doc (AMD_HIP.md): | `STRATA_FILE_CACHE_OLD_RULE` | gfx906 keeps the old file-tier cache rule; `=1` forces it on any Linux build, `=0` the current one |
- **STRATA_FILE_RELEASE** — src/core/expert_source.cpp:3414 docs: DETAILS.md
  `const char* v = std::getenv("STRATA_FILE_RELEASE");`
  doc (DETAILS.md): - Windows, opt-in: `STRATA_FILE_RELEASE=1` trims the file-backed pages of experts after their GPU uploads. It is a
- **STRATA_FILE_TIER_PROBE** — src/core/expert_source.cpp:908 docs: release-notes-0.2.1.md
  `const char* pe = std::getenv("STRATA_FILE_TIER_PROBE");`
  doc (release-notes-0.2.1.md): - **Linux, models read in place: a drive probe decides between the file cache and unbuffered reads (#3237).** The room rule picks the file cache when RAM seems to have room, which was 2x slower in prompts and 3 to 4x slower in decode for a reporter with a PCIe 5 drive (about 8 GB/s). When the rule s
- **STRATA_FS_ADMIT** — src/core/expert_source.cpp:6414
  `f->admit = env_int("STRATA_FS_ADMIT", 1, 1);`
- **STRATA_FS_BUDGET** — src/core/expert_source.cpp:6413
  `f->budget = env_int("STRATA_FS_BUDGET", 32, 1);`
- **STRATA_FS_DEPTH** — src/core/expert_source.cpp:6415
  `f->depth = env_int("STRATA_FS_DEPTH", 4, 2);`
- **STRATA_FS_SLOTS** — src/program/generate.cpp:7647 (+2 more reads) docs: BATCHING.md, DETAILS.md, OLDER_GPUS.md, RX7900XTX.md
  `const bool fs_ahead = srcp != nullptr && [] { const char* v = std::getenv("STRATA_FS_SLOTS"); return v != nullptr && std::atoi(v) > 0; }() &&`
  // #1348, one prefetch design: with the Foresight swap space on (STRATA_FS_SLOTS) the look-ahead also runs on the pinned-RAM tiers, where there are no pages to warm, and feeds its predictions to the swap space (STRATA_FS_AHEAD=0: not)
  doc (DETAILS.md): | `STRATA_FS_SLOTS=N` | CUDA | Foresight swap space: N VRAM slots per layer refilled with missed and predicted experts. | The smaller cache cost more than the slots returned in every box measured. Left off. |
- **STRATA_FS_VERIFY** — src/core/expert_source.cpp:6416
  `f->verify = env_int("STRATA_FS_VERIFY", 0, 0) != 0;`
- **STRATA_FUSE_CONVAB** PROD=1 — src/core/verify.cpp:469
  `static const bool on = [] { const char* v = std::getenv("STRATA_FUSE_CONVAB"); return v != nullptr && std::atoi(v) != 0; }();`
- **STRATA_FUSE_HEAD_GR** PROD=1 — src/core/mtp.cpp:1112 (+1 more reads)
  `const char* v = std::getenv("STRATA_FUSE_HEAD_GR");`
- **STRATA_FUSE_HITS** — src/core/verify.cpp:479
  `static const int env = [] { const char* v = std::getenv("STRATA_FUSE_HITS"); return v != nullptr ? (std::atoi(v) != 0 ? 1 : 0) : -1; }();`
- **STRATA_FUSE_WAIT** PROD=1 — src/core/verify.cpp:451 (+2 more reads) docs: DETAILS.md, OLDER_GPUS.md
  `static const int env = [] { const char* v = std::getenv("STRATA_FUSE_WAIT"); return v != nullptr ? std::atoi(v) : -1; }();`
  // CUDA: STRATA_FUSE_WAIT=1 folds both waits (the plan's and the CPU rows'), =2 only the plan's, =0 neither.  Turing default 2 (RTX 2080 Ti, Flash-Next Q2_0, two runs each: +0.6..+1.4 % decode); the rows' version makes every row block of the copy poll the flag over PCIe and was -1.5 % there, so it stays opt-in.
  doc (DETAILS.md): `STRATA_TOPK_SPLIT`, `STRATA_TOPK_SAMPLE`, `STRATA_ATTN_V3`, `STRATA_Q2_WARP`, `STRATA_FUSE_WAIT=2`, `STRATA_QIL`,
- **STRATA_GDN_PP** — src/prefill/kernels.cu:2707 (+1 more reads) docs: RADEON_780M.md, STRIX_HALO.md
  `static const int pp = [] { const char* v = std::getenv("STRATA_GDN_PP"); return v ? std::atoi(v) : 0; }();`
  doc (STRIX_HALO.md): | `STRATA_GDN_HEAD`, `STRATA_GDN_PP=2`, `STRATA_GDN_CONVL2`, `STRATA_GDN_NOY` | The prompt's gated-delta-net recurrence: four lanes per column, two columns per lane, convolution and norms fused. |
- **STRATA_GFX1151_DEFAULTS** — src/core/arch_defaults.cpp:56 (+1 more reads) docs: STRIX_HALO.md, STRIX_HALO_WINDOWS.md
  `const char* off = std::getenv("STRATA_GFX1151_DEFAULTS");`
  doc (STRIX_HALO.md): `STRATA_GFX1151_DEFAULTS=0` turns the whole table off, and the start-up line names what was set. Every one of them gave
- **STRATA_GFX12_DEFAULTS** — src/core/arch_defaults.cpp:38 (+2 more reads) docs: DETAILS.md
  `const char* off12 = std::getenv("STRATA_GFX12_DEFAULTS");`
  // STRATA_HCD_EXACT is left out: it needs the gfx1151 hipBLASLt tuning table, finds none on gfx12, says so on every start and does nothing (measured: with and without it identical, 0.0 to +0.1%). STRATA_GDN_CONVL2 is AMD-only on purpose: it is not bitwise on CUDA 13.3 sm_120 (#1522), and this table is never consulted by a CUDA build.
  doc (DETAILS.md): | Bare `--prefill auto` takes 16384-token chunks | gfx12, Linux | `STRATA_GFX12_CHUNK=0` or `STRATA_GFX12_DEFAULTS=0` | An explicit `--prefill N`, `auto:N` or `STRATA_PREFILL_AUTO_MAX` is untouched. |
- **STRATA_GRAPH_PRIO** — src/core/verify.cpp:222 docs: DETAILS.md
  `static const bool on = [] { const char* v = std::getenv("STRATA_GRAPH_PRIO"); return v != nullptr && std::atoi(v) != 0; }();`
  doc (DETAILS.md): | `STRATA_GRAPH_PRIO=1` | The verify window graph's kernel nodes run at their capturing stream's priority (`cudaGraphInstantiateFlagUseNodePriority`): the GDN gates and the QSA indexer branch at the highest, the shared expert at the lowest. Nothing changes on a card whose priority range is 0..0. | b
- **STRATA_HC_Q8** PROD=1 — src/core/native_dense.cpp:51 docs: AMD_HIP.md, MAC.md, QUANTS.md, RX7900XTX.md, STRIX_HALO.md, STRIX_HALO_WINDOWS.md, UNSLOTH_Q4.md, release-notes-0.2.3.md
  `const char* v = std::getenv("STRATA_HC_Q8");`
  doc (AMD_HIP.md): | `STRATA_HC_Q8` | gfx12, gfx1151 | On | 8-bit hyper-connection weights; `=0` restores the bf16 read ([below](#strix-halo-8-bit-hyper-connection-weights-default-on-gfx1151)) |
- **STRATA_HC_Q8_INJECT** — src/core/native_dense.cpp:402
  `static const bool q8_inject = [] { const char* v = std::getenv("STRATA_HC_Q8_INJECT"); return v && v[0] == '1'; }();`
  // S25: the F32 inject rows hold BF16-exact values: the read takes the pack's BF16 rows unless STRATA_HC_Q8_INJECT=1 asks for a Q8_0 copy
- **STRATA_HC_UPMIX** PROD=1 — src/prefill/prefill.cpp:471 (+2 more reads) docs: AMD_HIP.md, DETAILS.md, RADEON_780M.md, RX7900XTX.md, STRIX_HALO.md
  `static const bool v = [] { const char* e = std::getenv("STRATA_HC_UPMIX"); return e != nullptr && e[0] == '1'; }();`
  doc (DETAILS.md): | `STRATA_HC_UPMIX=1` | Hyper-connection up projection and `gr_mix_r` in one kernel (sm_80+) | Exact |
- **STRATA_HEAD_MIX_MULTI** — src/core/mtp.cpp:1117 (+3 more reads)
  `const char* v = std::getenv("STRATA_HEAD_MIX_MULTI");   // HIP: opt-in (=1)`
  // HIP: opt-in (=1)
- **STRATA_HIP_VMM** — src/core/vmm.cpp:192 docs: DETAILS.md
  `const char* off = std::getenv("STRATA_HIP_VMM");`
  doc (DETAILS.md): | `--kv-grow` (or `STRATA_KV_GROW=1`; `--no-kv-grow` turns it off) | The KV takes VRAM only for the cells the requests reach; the expert cache holds the rest and gives slots back as the context grows. Needs one GPU, an expert profile, the whole KV in VRAM and every expert in RAM. Otherwise the engin
- **STRATA_IGPU_DEFAULTS** — src/core/arch_defaults.cpp:100 docs: AMD_HIP.md
  `const char* off = std::getenv("STRATA_IGPU_DEFAULTS");`
  doc (AMD_HIP.md): off switch. `STRATA_IGPU_DEFAULTS=0` turns the set off whatever else is set. The same code applies on Windows but was not
- **STRATA_IGPU_PROMPT_SET** — src/core/arch_defaults.cpp:102 docs: AMD_HIP.md, RADEON_780M.md, STRIX_HALO.md, release-notes-0.2.1.md
  `const char* e = std::getenv("STRATA_IGPU_PROMPT_SET");`
  doc (AMD_HIP.md): `STRATA_IGPU_PROMPT_SET=0` turns the whole set off, `=1` turns it on where it is not the default. Each switch keeps `=0` as its
- **STRATA_IO_PF_AHEAD** — src/core/expert_source.cpp:1137 docs: DETAILS.md
  `if (const char* v = std::getenv("STRATA_IO_PF_AHEAD")) io_ahead_ = std::atoi(v) != 0;`
  doc (DETAILS.md): | io prefetch | `STRATA_IO_PREFETCH=1` (`0` = off) | I/O threads read the layer's uncached experts and the router-predicted ones of the next layers with whole-blob `pread`s into the page cache. Tunables: `STRATA_LOOKAHEAD_K`, `STRATA_IO_PREFETCH_DEPTH` (2), `STRATA_IO_PF_THREADS` (8), `STRATA_IO_PF_
- **STRATA_IO_PF_BUDGET_FRAC** — src/core/expert_source.cpp:1150
  `if (const char* m = std::getenv("STRATA_IO_PF_BUDGET_FRAC")) io_budget_frac_ = std::clamp(std::atof(m), 0.01, 4.0);`
- **STRATA_IO_PF_BUDGET_MB** — src/core/expert_source.cpp:1149
  `if (const char* m = std::getenv("STRATA_IO_PF_BUDGET_MB")) io_budget_fixed_ = (uint64_t) std::max(0.0, std::atof(m) * 1048576.0);`
- **STRATA_IO_PF_GATE** — src/core/expert_source.cpp:1153 docs: DETAILS.md, release-notes-0.2.0.md
  `if (const char* m = std::getenv("STRATA_IO_PF_GATE"); m != nullptr && m[0] != '\0') gate_on_ = std::atoi(m) != 0;`
  doc (DETAILS.md): | Decode gate | `STRATA_IO_PF_GATE=1` (`0` = off) | Every 16 decode windows the read-ahead is judged. It runs only while the page cache has room for the experts (off below 0.55, on above 0.65: `STRATA_IO_PF_GATE_LO` and `_HI`) and while it pays (`STRATA_IO_PF_GATE_USEFUL`). |
- **STRATA_IO_PF_GATE_HI** — src/core/expert_source.cpp:1155
  `if (const char* m = std::getenv("STRATA_IO_PF_GATE_HI")) gate_hi_ = std::clamp(std::atof(m), gate_lo_, 1.0);`
- **STRATA_IO_PF_GATE_LO** — src/core/expert_source.cpp:1154 docs: DETAILS.md
  `if (const char* m = std::getenv("STRATA_IO_PF_GATE_LO")) gate_lo_ = std::clamp(std::atof(m), 0.0, 1.0);`
  doc (DETAILS.md): | Decode gate | `STRATA_IO_PF_GATE=1` (`0` = off) | Every 16 decode windows the read-ahead is judged. It runs only while the page cache has room for the experts (off below 0.55, on above 0.65: `STRATA_IO_PF_GATE_LO` and `_HI`) and while it pays (`STRATA_IO_PF_GATE_USEFUL`). |
- **STRATA_IO_PF_GATE_USEFUL** — src/core/expert_source.cpp:1156 docs: DETAILS.md
  `if (const char* m = std::getenv("STRATA_IO_PF_GATE_USEFUL")) gate_min_useful_ = std::clamp(std::atof(m), 0.0, 1.0);`
  doc (DETAILS.md): | Decode gate | `STRATA_IO_PF_GATE=1` (`0` = off) | Every 16 decode windows the read-ahead is judged. It runs only while the page cache has room for the experts (off below 0.55, on above 0.65: `STRATA_IO_PF_GATE_LO` and `_HI`) and while it pays (`STRATA_IO_PF_GATE_USEFUL`). |
- **STRATA_IO_PF_MINCONF** — src/core/expert_source.cpp:1148
  `if (const char* m = std::getenv("STRATA_IO_PF_MINCONF")) io_minconf_ = (float) std::clamp(std::atof(m), 0.0, 1.0);`
- **STRATA_IO_PF_SCHED** — src/core/expert_source.cpp:1146
  `const char* v = std::getenv("STRATA_IO_PF_SCHED");`
- **STRATA_IO_PF_STAGE** — src/core/expert_source.cpp:1139 (+1 more reads) docs: DETAILS.md
  `const char* v = std::getenv("STRATA_IO_PF_STAGE");`
  doc (DETAILS.md): | io prefetch | `STRATA_IO_PREFETCH=1` (`0` = off) | I/O threads read the layer's uncached experts and the router-predicted ones of the next layers with whole-blob `pread`s into the page cache. Tunables: `STRATA_LOOKAHEAD_K`, `STRATA_IO_PREFETCH_DEPTH` (2), `STRATA_IO_PF_THREADS` (8), `STRATA_IO_PF_
- **STRATA_IO_PF_TARGET** — src/core/expert_source.cpp:1151
  `if (const char* m = std::getenv("STRATA_IO_PF_TARGET")) io_target_ = std::clamp(std::atof(m), 0.0, 1.0);`
- **STRATA_KV_HOST_REGISTER** — src/core/layer.cpp:596 docs: DETAILS.md
  `const char* e = std::getenv("STRATA_KV_HOST_REGISTER");`
  doc (DETAILS.md): `STRATA_KV_HOST_REGISTER=1` forces the KV host copy to be pinned with `cudaHostRegister` (the order WSL2 uses
- **STRATA_KV_MAIN_OFF** — src/core/layer.cpp:746
  `static const bool main_off = std::getenv("STRATA_KV_MAIN_OFF") != nullptr;`
- **STRATA_KV_RING_OFF** — src/core/layer.cpp:745
  `static const bool ring_off = std::getenv("STRATA_KV_RING_OFF") != nullptr;`
  // A/B only: STRATA_KV_RING_OFF keeps the drafter fully resident, STRATA_KV_MAIN_OFF the main layers
- **STRATA_LFUSE** — src/core/verify.cpp:104 docs: RADEON_780M.md, RX7900XTX.md, STRIX_HALO.md
  `inline bool g_lfuse() { static const bool on = [] { const char* v = std::getenv("STRATA_LFUSE"); return v != nullptr && v[0] == '1'; }(); return on; }`
  doc (RX7900XTX.md): | `STRATA_EXPERT_V2`, `STRATA_TSUM`, `STRATA_ATTN_LANECELL`+`MERGE_V2`, `STRATA_GDN_SPLIT`, `STRATA_LFUSE`/`QFUSE`, the gfx12 default set | single runs looked +2-7%, combinations did not hold above the decode noise |
- **STRATA_LFUSE_GATE** — src/core/verify.cpp:167
  `inline bool g_lfuse_gate() { static const bool on = [] { const char* v = std::getenv("STRATA_LFUSE_GATE"); return v == nullptr || v[0] != '0'; }(); return on; }`
- **STRATA_LFUSE_PAIR** — src/core/verify.cpp:168
  `inline bool g_lfuse_pair() { static const bool on = [] { const char* v = std::getenv("STRATA_LFUSE_PAIR"); return v == nullptr || v[0] != '0'; }(); return on; }`
- **STRATA_LOGITS_DUMP** — src/core/verify.cpp:3435 docs: KVA.md
  `if (const char* logits_path = std::getenv("STRATA_LOGITS_DUMP")) {`
  // AFTER the window (the stream is synchronised above and the graph capture is over, so a plain copy is legal - the same place STRATA_DBG_NAN copies from).  One record is {int32 magic, int32 T, int32 n_vocab, int32 record, int64 position}, then T * n_vocab FP32 rows; row 0 is the window's first position (the last prompt token of a prefill), which is what a KL comparison wants.
  doc (KVA.md): | `STRATA_LOGITS_DUMP` | — | debug (not KVA-specific): write every verify window's sampler logits to `path`, for KL / top-1 between two runs |
- **STRATA_LOGPOS_TOPK** — src/core/verify.cpp:3619 docs: QUANTS.md, UNSLOTH_Q4.md
  `const char* v = std::getenv("STRATA_LOGPOS_TOPK");`
  doc (UNSLOTH_Q4.md): log-probabilities. Strata used its verify windows (`STRATA_LOGPOS` with `STRATA_LOGPOS_TOPK=20`), llama.cpp used
- **STRATA_MMVQ_IL** — src/core/verify.cpp:173 docs: MMVQ_IL_TABLE.md, NVIDIA_V100.md, OLDER_GPUS.md
  `inline bool g_mmvq_il() { static const bool on = [] { const char* v = std::getenv("STRATA_MMVQ_IL"); return v == nullptr || v[0] != '0'; }(); return on; }`
  // S26 STRATA_QFUSE=1: activation q8_1 images written by their producers (the GDN output norm) - the same bytes fork F4 (Eddoursul): 2-4 token dense projections read an interleaved copy of the q8_1 activations (bitwise the same outputs); STRATA_MMVQ_IL=0 keeps native_mmvq's multi-column kernels
  doc (OLDER_GPUS.md): | The interleaved small-batch matvec with a P40 table (`kIlRows_61`) | `native_mmvq` | on; `STRATA_SM61_TABLE=0` (or `STRATA_MMVQ_IL=0`) |
- **STRATA_MTP_CATCHUP_ALL** — src/core/mtp.cpp:72
  `const char* v = std::getenv("STRATA_MTP_CATCHUP_ALL");`
- **STRATA_MTP_FULL_HEAD** — src/core/mtp.cpp:546 (+1 more reads)
  `static const bool on = [] { const char* v = std::getenv("STRATA_MTP_FULL_HEAD"); return v && v[0] == '1'; }();`
- **STRATA_MTP_HIP_PRIO** — src/core/mtp.cpp:489
  `if (const char* v = std::getenv("STRATA_MTP_HIP_PRIO"); v != nullptr && *v != 0) return std::atoi(v) != 0;`
- **STRATA_MTP_PREFILL_SYNC** — src/core/mtp.cpp:1427
  `if (const char* e = std::getenv("STRATA_MTP_PREFILL_SYNC")) return std::atoi(e) != 0;`
- **STRATA_MTP_PRIORITY** — src/core/mtp.cpp:475
  `static const bool hi_prio = [] { const char* v = std::getenv("STRATA_MTP_PRIORITY"); return v == nullptr || std::atoi(v) != 0; }();`
- **STRATA_MTP_PROFILE** — src/core/mtp.cpp:811
  `const char* e = std::getenv("STRATA_MTP_PROFILE");`
- **STRATA_MTP_Q8_SM60** — src/core/mtp.cpp:82 docs: release-notes-0.2.7.md
  `const char* v = std::getenv("STRATA_MTP_Q8_SM60");`
  doc (release-notes-0.2.7.md): - Opt-in switches from pull requests, each checked for exactness or by unit tests and builds, not for speed on your card: a bigger Pascal (GP100) set (`STRATA_DOWN_WS=1`, `STRATA_MTP_Q8_SM60=1`, `STRATA_MMQ_WS=1`, `STRATA_PATTN_SM60=1`, `STRATA_EXPERT_NIBBLE=1`), `STRATA_PF_FUSED_Q2N=1` for the Q2_0
- **STRATA_MTP_SHARED_BRANCH** — src/core/mtp.cpp:1130
  `const char* v = std::getenv("STRATA_MTP_SHARED_BRANCH");`
- **STRATA_MTP_SIDE_STREAM** — src/core/mtp.cpp:521 docs: AMD_HIP.md
  `if (const char* v = std::getenv("STRATA_MTP_SIDE_STREAM"); v != nullptr && *v != 0) on = std::atoi(v) != 0;`
  doc (AMD_HIP.md): | `STRATA_MTP_SIDE_STREAM` | Off on HIP, on for gfx103x | `=0` turns it off on gfx103x, `=1` creates it on another HIP card |
- **STRATA_MTP_TOP2** — src/core/mtp.cpp:552
  `static const bool on = [] { const char* v = std::getenv("STRATA_MTP_TOP2"); return v && v[0] == '1'; }();`
- **STRATA_NAN_GUARD** — src/core/verify.cpp:4716 docs: DETAILS.md
  `const char* v = std::getenv("STRATA_NAN_GUARD");`
  doc (DETAILS.md): A started reply ends as `"length"`, and a second hit on the retry returns an error. `STRATA_NAN_GUARD=0` turns the check off;
- **STRATA_NAN_INJECT** — src/core/verify.cpp:4727 docs: DETAILS.md
  `if (const char* e = std::getenv("STRATA_NAN_INJECT"))`
  doc (DETAILS.md): `STRATA_NAN_INJECT=<n>[,<n>...]` flags the n-th checked window to test the path. The one-shot command line and the
- **STRATA_NO_ARENA_THP** — src/core/pinned.cu:290 (+1 more reads) docs: TROUBLESHOOTING.md
  `const bool skip_thp_request = std::getenv("STRATA_NO_ARENA_THP") != nullptr || thp_mode == "always";`
  doc (TROUBLESHOOTING.md): on top (a fragmented machine spent minutes compacting memory, #771); `STRATA_NO_ARENA_THP=1` skips that request on any setting.
- **STRATA_NO_BATCH_KV_STEP** — src/core/verify.cpp:324 (+1 more reads)
  `const bool g_no_batch_kv = env_on("STRATA_NO_BATCH_KV_STEP");   // #783 PR-d: per-token K/V and indexer appends again`
  // #783 PR-d: per-token K/V and indexer appends again
- **STRATA_NO_LARGEPAGES** — src/core/pinned.cu:239 (+5 more reads)
  `if (std::getenv("STRATA_NO_LARGEPAGES") != nullptr) {`
  // STRATA_NO_LARGEPAGES=1 is the same-run A/B switch the Windows branch documents; honor it here too, so the large-page path can be compared without changing the pool or rebooting.
- **STRATA_NO_MULTI_GR** — src/core/verify.cpp:323 (+3 more reads)
  `const bool g_no_multi_gr = env_on("STRATA_NO_MULTI_GR");   // #783 PR-g: per-token GR reads/writes and generic-T kernels again`
  // #783 PR-g: per-token GR reads/writes and generic-T kernels again
- **STRATA_ONE_TOKEN_COMMIT** PROD=1 — src/core/verify.cpp:497 (+1 more reads)
  `const char* v = std::getenv("STRATA_ONE_TOKEN_COMMIT");   // HIP: opt-in (=1)`
  // HIP: opt-in (=1)
- **STRATA_PARK_ASYNC** — src/core/conversation_snapshot.cpp:235 (+1 more reads) docs: DETAILS.md
  `static const bool on = [] { const char* v = std::getenv("STRATA_PARK_ASYNC"); return v != nullptr && v[0] == '1'; }();`
  doc (DETAILS.md): Where the card sits behind a slow host link, the conversation cache's copies are on the critical path of the next request. A turn checkpoint copies the DeltaNet state (118 MB on Qwen3.8-Flash-Next) from the card to the host. Parking a conversation copies its K/V and its checkpoints before the next p
- **STRATA_PARK_TRACE** — src/core/conversation_snapshot.cpp:145 (+4 more reads) docs: DETAILS.md
  `bool park_trace() { static const bool on = std::getenv("STRATA_PARK_TRACE") != nullptr; return on; }`
  doc (DETAILS.md): | `STRATA_PARK_TRACE=1` | Diagnostic: the park's joins and timers on stderr. | - |
- **STRATA_PARK_VRAM_MIB** — src/core/conversation_snapshot.cpp:139 docs: DETAILS.md
  `const char* v = std::getenv("STRATA_PARK_VRAM_MIB");`
  doc (DETAILS.md): | `STRATA_PARK_VRAM_MIB=N` (with `STRATA_PARK_ASYNC=1`) | A park also keeps the K/V in VRAM slots (64 MiB granules, up to N MiB, only while 1.5 GB stay free). Switching back restores it card-to-card. | second and later restores of a run 33-51 -> 7-13 ms; the first is not faster |
- **STRATA_PARTIAL_PIN** — src/core/expert_source.cpp:3858 docs: UNSLOTH_Q4.md
  `const char* v = std::getenv("STRATA_PARTIAL_PIN");`
  doc (UNSLOTH_Q4.md): | `STRATA_PARTIAL_PIN=1` | Registers the hottest part of the RAM budget (up to `STRATA_PARTIAL_PIN_GIB`, default 24) with the GPU driver, so the GPU computes a share of the misses over PCIe (`--pcie-frac`). Measured no faster, and it changes the numerics of those experts, so off. |
- **STRATA_PARTIAL_PIN_GIB** — src/core/expert_source.cpp:3864 docs: UNSLOTH_Q4.md
  `const char* v = std::getenv("STRATA_PARTIAL_PIN_GIB");`
  doc (UNSLOTH_Q4.md): | `STRATA_PARTIAL_PIN=1` | Registers the hottest part of the RAM budget (up to `STRATA_PARTIAL_PIN_GIB`, default 24) with the GPU driver, so the GPU computes a share of the misses over PCIe (`--pcie-frac`). Measured no faster, and it changes the numerics of those experts, so off. |
- **STRATA_PCIE_MIN1** — src/core/expert_source.cpp:4916
  `static const bool pcie_min1 = [] { const char* v = std::getenv("STRATA_PCIE_MIN1"); return v && std::atoi(v) != 0; }();`
  // STRATA_PCIE_MIN1 (opt-in): the share rounds to 0 for 1-2 misses per layer, so the PCIe lane idles on the typical decode step; with >= 2 misses give it at least one (the last in routing order).  It only flies if its blob is pinned (the fetch below checks), else it stays a CPU miss exactly as before.  Read once.
- **STRATA_PEER_DIRECT** — src/core/peer_experts.cpp:246
  `static const bool direct_env = [] { const char* v = std::getenv("STRATA_PEER_DIRECT"); return v == nullptr || std::atoi(v) != 0; }();`
- **STRATA_PEER_NO_P2P** — src/core/peer_experts.cpp:144 docs: SECOND_GPU.md
  `if (const char* np = std::getenv("STRATA_PEER_NO_P2P"); np != nullptr && std::atoi(np) != 0) a = 0;   // test knob: pretend the pair has no P2P`
  // test knob: pretend the pair has no P2P
  doc (SECOND_GPU.md): says so and the prompt path uses the host route (activations and rows through mapped host memory). `STRATA_PEER_NO_P2P=1` asks
- **STRATA_PIN_GUARD** — src/core/expert_source.cpp:3748 docs: TROUBLESHOOTING.md
  `const char* v = std::getenv("STRATA_PIN_GUARD");`
  doc (TROUBLESHOOTING.md): `STRATA_PIN_GUARD=0` turns this off, `STRATA_PIN_RESERVE_GIB=N` sets the RAM that must stay free (default:
- **STRATA_PIN_RESERVE_GIB** — src/core/expert_source.cpp:3741 docs: TROUBLESHOOTING.md
  `const char* v = std::getenv("STRATA_PIN_RESERVE_GIB");`
  doc (TROUBLESHOOTING.md): `STRATA_PIN_GUARD=0` turns this off, `STRATA_PIN_RESERVE_GIB=N` sets the RAM that must stay free (default:
- **STRATA_PIN_RESERVE_MIB** — src/core/pin_budget_test.cpp:24 docs: DETAILS.md
  `SETENV("STRATA_PIN_RESERVE_MIB", "32");   // soft 32 MiB, hard 64 MiB (a quarter of 32 is below the 64 MiB floor)`
  // soft 32 MiB, hard 64 MiB (a quarter of 32 is below the 64 MiB floor)
  doc (DETAILS.md): - Windows CUDA keeps 640 MiB then 160 MiB of page-lockable memory free while the arena pins (`STRATA_PIN_RESERVE_MIB=N`, `0`
- **STRATA_PIPED_CONCURRENT** — src/core/verify.cpp:1096 (+1 more reads) docs: AMD_HIP.md, BATCHING.md
  `const char* v = std::getenv("STRATA_PIPED_CONCURRENT");`
  doc (AMD_HIP.md): `STRATA_HIP_ADAPT_KERNEL_COPY`, `STRATA_PREFILL_CPU_SHARE`, `STRATA_PIPED_CONCURRENT`, `STRATA_PREFILL_STREAM_MIN`, `STRATA_IO_THREADS`, a rocBLAS
- **STRATA_PIPED_CONCURRENT_PRIO** — src/core/verify.cpp:1097 docs: BATCHING.md
  `const char* p = std::getenv("STRATA_PIPED_CONCURRENT_PRIO");`
  doc (BATCHING.md): own streams (the windows' at the device's highest priority on CUDA; `STRATA_PIPED_CONCURRENT_PRIO=0` keeps the default),
- **STRATA_PLE_BATCH** — src/core/verify.cpp:1396 (+3 more reads) docs: RADEON_780M.md, STRIX_HALO.md
  `static const bool ple_batch = [] { const char* e = std::getenv("STRATA_PLE_BATCH"); return e && e[0] == '1'; }();`
  // S25 (STRATA_PLE_BATCH=1): the key and value projections depend only on each row's n-gram embedding, so the group's rows run through the multi-row forms of the same kernels (the weights read once); every row's arithmetic is the single-row call's. The history-dependent rest stays row by row.
  doc (STRIX_HALO.md): | `STRATA_GDN_SPLIT`, `STRATA_QFUSE`, `STRATA_PLE_BATCH` | The GDN step over four blocks per head, activation images written by their producers, the PLE key / value projections of a verify window at once. |
- **STRATA_POOL_TRACE** — src/core/expert_source.cpp:4841
  `static const bool ptrace = std::getenv("STRATA_POOL_TRACE") != nullptr;`
- **STRATA_QFUSE** — src/core/verify.cpp:298 (+2 more reads) docs: RADEON_780M.md, STRIX_HALO.md, release-notes-0.2.7.md
  `inline bool g_qfuse() { static const bool on = [] { const char* v = std::getenv("STRATA_QFUSE"); return v != nullptr && std::atoi(v) != 0; }(); return on; }`
  doc (release-notes-0.2.7.md): - Engine, found by reading the code and the pull requests: a failed read in the per-layer table reader no longer leaves the next request waiting for ever (#3602; the reporter's NaN did not reproduce here, `STRATA_PLE_CHECK=1` re-reads a suspect row and prints it); a conversation restore that would h
- **STRATA_QFUSE_HC** PROD=1 — src/core/verify.cpp:204
  `const char* v = std::getenv("STRATA_QFUSE_HC");`
- **STRATA_QIL** — src/core/verify.cpp:1518 docs: DETAILS.md
  `static const int qil_env = [] { const char* v = std::getenv("STRATA_QIL"); return v != nullptr ? std::atoi(v) : -1; }();`
  doc (DETAILS.md): `STRATA_TOPK_SPLIT`, `STRATA_TOPK_SAMPLE`, `STRATA_ATTN_V3`, `STRATA_Q2_WARP`, `STRATA_FUSE_WAIT=2`, `STRATA_QIL`,
- **STRATA_QSA_SLOTS** — src/core/verify.cpp:335 docs: BATCHING.md
  `const bool g_qsa_slots = env_on("STRATA_QSA_SLOTS");`
  // STRATA_QSA_SLOTS=1 (opt-in): in a batch window, a QSA layer's block scores, top-k and attention run as one launch each over the window's rows (up to 8 per launch, each row reading its own slot's indexer keys and K/V) instead of one call per row; every row is computed by the same kernel with the same arithmetic as its own call.  Not with a streamed KV cache (a row's block resolve could evict the bl
  doc (BATCHING.md): | `STRATA_QSA_SLOTS=1` | a window's QSA block scores, top-k and attention run as one launch over its rows |
- **STRATA_QSA_SPLIT_ATTN** — src/core/verify.cpp:2031 (+1 more reads) docs: DETAILS.md
  `static const bool split_attn = [] { const char* v = std::getenv("STRATA_QSA_SPLIT_ATTN"); return v != nullptr && std::atoi(v) != 0; }();`
  // STRATA_QSA_SPLIT_ATTN=1: the split tensor-core attention where it applies (int8 KV, sm_80+)
  doc (DETAILS.md): | `STRATA_QSA_SPLIT_ATTN=1` | Decode attention split across blocks on the int8 mma path (sm_80+, int8 KV) | Rounding level |
- **STRATA_RAM_ADAPT_QUEUE** — src/core/expert_source.cpp:4410
  `const char* v = std::getenv("STRATA_RAM_ADAPT_QUEUE");`
- **STRATA_REMOTE_SPIN** — src/core/remote_experts.cpp:86 (+1 more reads)
  `const char* spin = std::getenv("STRATA_REMOTE_SPIN");`
- **STRATA_REMOTE_ZEROCOPY** — src/core/remote_experts.cpp:234
  `const char* zc = std::getenv("STRATA_REMOTE_ZEROCOPY");`
  // Zero-copy: the helper reads its input from, and writes its compact rows into, the pinned host buffers directly - two copies fewer per layer, each of which is a PCIe round trip.  STRATA_REMOTE_ZEROCOPY=0 copies.
- **STRATA_ROUTE_PER_TOKEN** — src/core/layer.cpp:447 docs: AMD_HIP.md
  `!std::getenv("STRATA_ROUTE_PER_TOKEN");`
  doc (AMD_HIP.md): | Verify-window routing | The window's tokens in one multi-column BF16 projection and one top-k | `STRATA_ROUTE_PER_TOKEN=1` |
- **STRATA_ROUTE_PRIOR** — src/core/verify.cpp:280 (+1 more reads) docs: DETAILS.md, release-notes-0.2.0.md, release-notes-0.2.7.md
  `static const char* const env_s = std::getenv("STRATA_ROUTE_PRIOR");`
  doc (DETAILS.md): | `STRATA_ROUTE_PRIOR`, `STRATA_ROUTE_RESIDENT`, `STRATA_ROUTE_RESIDENT_MTP` | CUDA | Routing changes that add speed and also add KL. | Not recommended, except that 0.2.7 turns `STRATA_ROUTE_PRIOR=1.5` on by itself on a discrete NVIDIA card of 13 GiB or less (the owner approved the quality trade for
- **STRATA_ROUTE_PROJ_PER_TOKEN** — src/core/layer.cpp:459
  `if (std::getenv("STRATA_ROUTE_PROJ_PER_TOKEN"))`
- **STRATA_ROUTE_RESIDENT** — src/program/generate.cpp:9904 (+2 more reads) docs: DETAILS.md
  `if (use_mtp && stages.empty() && thits.d_res != nullptr && std::getenv("STRATA_ROUTE_RESIDENT") != nullptr &&`
  // STRATA_ROUTE_RESIDENT_MTP=1 (EXPERIMENTAL, with STRATA_ROUTE_RESIDENT=<margin>; changes the output): the MTP draft's router gets the same residency bias, with the last layer's residency row as its table (single GPU)
  doc (DETAILS.md): | `STRATA_ROUTE_PRIOR`, `STRATA_ROUTE_RESIDENT`, `STRATA_ROUTE_RESIDENT_MTP` | CUDA | Routing changes that add speed and also add KL. | Not recommended, except that 0.2.7 turns `STRATA_ROUTE_PRIOR=1.5` on by itself on a discrete NVIDIA card of 13 GiB or less (the owner approved the quality trade for
- **STRATA_ROUTE_RESIDENT_RANKS** — src/core/verify.cpp:161 (+1 more reads)
  `if (const char* v = std::getenv("STRATA_ROUTE_RESIDENT_RANKS")) std::sscanf(v, "%d-%d", &c.lo, &c.hi);`
- **STRATA_ROUTE_STATS** — src/core/verify.cpp:1044
  `if (const char* rs = std::getenv("STRATA_ROUTE_STATS"); rs != nullptr && rs[0] == '1') {`
- **STRATA_ROUTE_TAIL_SKIP** — src/core/expert_source.cpp:4803 (+1 more reads) docs: DETAILS.md, NVFP4.md, OLDER_GPUS.md, QUANTS.md, UNSLOTH_Q4.md
  `const char* v = std::getenv("STRATA_ROUTE_TAIL_SKIP");`
  doc (DETAILS.md): | `STRATA_ROUTE_TAIL_SKIP` (7) | CUDA, and HIP gfx1200/gfx1201; one GPU or a layer split | `STRATA_ROUTE_TAIL_SKIP=0` | A missed expert that every token of a verify window routes at rank 7 or lower is neither copied nor computed. Not applied when every expert is in VRAM, with `--batch` slots, with a
- **STRATA_SELECT_LONG** — src/core/verify.cpp:181 docs: OLDER_GPUS.md, release-notes-0.2.7.md
  `const char* v = std::getenv("STRATA_SELECT_LONG");`
  doc (release-notes-0.2.7.md): - Opt-in switches from pull requests, each checked for exactness or by unit tests and builds, not for speed on your card: a bigger Pascal (GP100) set (`STRATA_DOWN_WS=1`, `STRATA_MTP_Q8_SM60=1`, `STRATA_MMQ_WS=1`, `STRATA_PATTN_SM60=1`, `STRATA_EXPERT_NIBBLE=1`), `STRATA_PF_FUSED_Q2N=1` for the Q2_0
- **STRATA_SELECT_LONG_AT** — src/core/verify.cpp:195 docs: OLDER_GPUS.md
  `const char* v = std::getenv("STRATA_SELECT_LONG_AT");`
  doc (OLDER_GPUS.md): `STRATA_SELECT_LONG_AT` cells (default 65,536) a decode window's QSA select runs a top-k over several CTAs a query (six kernels)
- **STRATA_SESSION_BUFFERED** — src/core/conversation_file.cpp:340 (+3 more reads)
  `const char* e = std::getenv("STRATA_SESSION_BUFFERED");`
- **STRATA_SESSION_GOLDEN_PRINT** — src/core/conversation_file_test.cpp:180
  `const char* golden = std::getenv("STRATA_SESSION_GOLDEN_PRINT");`
- **STRATA_SH_FORK_LATE** — src/core/verify.cpp:2065 docs: AMD_HIP.md
  `const char* e = std::getenv("STRATA_SH_FORK_LATE");`
  doc (AMD_HIP.md): off only after the doorbell is published (`STRATA_SH_FORK_LATE`, `src/core/verify.cpp`), so it runs while the GPU would otherwise wait for the
- **STRATA_SH_STREAM** — src/core/verify.cpp:358 (+9 more reads) docs: AMD_HIP.md, RADEON_780M.md, STRIX_HALO.md, STRIX_HALO_WINDOWS.md
  `if (const char* v = std::getenv("STRATA_SH_STREAM")) return v[0] != '0';`
  doc (AMD_HIP.md): | `STRATA_SH_STREAM=1` | Off on HIP, except the gfx1151 table | Shared-expert fork on its own stream. Output is identical; speed goes both ways by PC. `./setup.sh --calibrate` measures it and writes it to the config's `"env"` only when it wins by more than 3%. |
- **STRATA_SIDE_MIXER** — src/core/verify.cpp:252 docs: DETAILS.md, OLDER_GPUS.md
  `static const int env = [] { const char* v = std::getenv("STRATA_SIDE_MIXER"); return v ? std::max(0, std::min(2, std::atoi(v))) : -1; }();`
  doc (DETAILS.md): | `STRATA_SIDE_MIXER=1/2` | The mixer's input-only work on graph branches | Exact; on by default on sm_86, sm_60 and 12.0 |
- **STRATA_SPEC_ADAPT_SM86** — src/core/nv_defaults.cpp:81
  `if (const char* v = std::getenv("STRATA_SPEC_ADAPT_SM86"); v == nullptr || v[0] != '1') return;`
- **STRATA_SPLIT_WAIT_MS** — src/core/verify.cpp:592 docs: MULTI_GPU.md
  `const char* e = std::getenv("STRATA_SPLIT_WAIT_MS");`
  doc (MULTI_GPU.md): it is off beside `--pipeline-windows`. The wait is bounded by `STRATA_SPLIT_WAIT_MS` (default 30000, `0` = no bound); on timeout
- **STRATA_STAGE_PIN** — src/core/expert_source.cpp:1837 docs: DETAILS.md
  `static const int pin_mode = [] { const char* v = std::getenv("STRATA_STAGE_PIN"); return v == nullptr ? -1 : (std::atoi(v) != 0 ? 1 : 0); }();`
  // the transfer rate, on the calling thread.  A failure falls back to pageable for this buffer. STRATA_STAGE_PIN: 0 keeps them pageable (as before 0.1.41), 1 always tries to pin, unset (the default) pins while the host has kStagePinFloor of RAM to spare beside this buffer (the pool grows to ~257 buffers, 0.4-0.6 GiB): a low-RAM box keeps pageable ones instead of paying for the pinning (recommend, nev
  doc (DETAILS.md): | `STRATA_STAGE_PIN=1` | GGUF read in place | Page-locks the stage buffers the cache fill copies from. Unset, it stays off: with it on, IQ3_S decode was corrupted after a 4096-token prompt in an earlier release gate. | Keep off until that is fixed. |
- **STRATA_STARTUP_UNBUFFERED** — src/core/expert_source.cpp:2583
  `if (const char* v = std::getenv("STRATA_STARTUP_UNBUFFERED"); v != nullptr && v[0] != '\0' && std::atoi(v) == 0) {`
- **STRATA_TAP_FILE** — src/core/verify.cpp:892
  `const char* tap_path = std::getenv("STRATA_TAP_FILE");`
  // DFlash2 taps: set_taps (the drafter) or STRATA_TAP_FILE (the research dump); off, and nothing is allocated or captured, otherwise
- **STRATA_TAP_LAYERS** — src/core/verify.cpp:899
  `const char* tl = std::getenv("STRATA_TAP_LAYERS");`
- **STRATA_TEST_BIG_GDN** — src/core/conversation_snapshot_test.cpp:134
  `if (std::getenv("STRATA_TEST_BIG_GDN")) { g.ssm_state_size=64; g.ssm_v_heads=64; }   // a GDN state over 1 MiB: the async checkpoint path`
  // a GDN state over 1 MiB: the async checkpoint path
- **STRATA_TEST_COPY_FAIL_AT** — src/core/conversation_copy.hpp:120
  `static const long v = [] { const char* e = std::getenv("STRATA_TEST_COPY_FAIL_AT"); return e ? std::atol(e) : 0L; }();`
- **STRATA_TEST_HANDOFF_DROP** — src/core/verify.cpp:598
  `const char* e = std::getenv("STRATA_TEST_HANDOFF_DROP");`
- **STRATA_TEST_PIN_BUDGET_MIB** — src/core/pin_budget_test.cpp:23
  `SETENV("STRATA_TEST_PIN_BUDGET_MIB", "100");`
  // the singleton reads its environment on first use: set everything first
- **STRATA_TEST_SLOW_COPY_US** — src/core/conversation_copy.hpp:163
  `static const long v = [] { const char* e = std::getenv("STRATA_TEST_SLOW_COPY_US"); return e ? std::atol(e) : 0L; }();`
- **STRATA_TEST_UNMAP_GGUF** — src/core/expert_source.cpp:2564
  `const char* t = std::getenv("STRATA_TEST_UNMAP_GGUF");`
  // Linux's page cache has no such lock: only the tests close the GGUF views (STRATA_TEST_UNMAP_GGUF=1), to run the unmapped path the Windows file tier takes
- **STRATA_TEST_VERIFY_STALL** — src/core/verify.cpp:585
  `const char* e = std::getenv("STRATA_TEST_VERIFY_STALL");`
- **STRATA_TG_FLUSH_US** — src/core/session.cpp:935
  `const char* e = std::getenv("STRATA_TG_FLUSH_US");`
- **STRATA_TSUM** — src/kernels/cuda/iq_kernels.cu:6270 (+6 more reads) docs: RADEON_780M.md, RX7900XTX.md, STRIX_HALO.md
  `static const bool ts = [] { const char* v = std::getenv("STRATA_TSUM"); return v && v[0] == '1'; }();`
  // S26 STRATA_TSUM=1: the sums as one transposed butterfly per warp (s26_tsum.cuh; bitwise the same values)
  doc (RX7900XTX.md): | `STRATA_EXPERT_V2`, `STRATA_TSUM`, `STRATA_ATTN_LANECELL`+`MERGE_V2`, `STRATA_GDN_SPLIT`, `STRATA_LFUSE`/`QFUSE`, the gfx12 default set | single runs looked +2-7%, combinations did not hold above the decode noise |
- **STRATA_UMA_HEADROOM_GIB** — src/core/expert_cache.cpp:125 docs: STRIX_HALO.md
  `const char* h = std::getenv("STRATA_UMA_HEADROOM_GIB");`
  doc (STRIX_HALO.md): and the memory plan use) counts what Linux can give back (`MemAvailable` less 6 GiB for the system; `STRATA_UMA_HEADROOM_GIB`
- **STRATA_UMA_REGISTER** — src/core/arch_defaults.cpp:110 docs: STRIX_HALO.md
  `const char* reg = std::getenv("STRATA_UMA_REGISTER");`
  doc (STRIX_HALO.md): working-set lock, and the expert cache gets its normal slots. `STRATA_ARENA_PIN_GIB=N` (or `0`) or `STRATA_UMA_REGISTER=1`
- **STRATA_UNBUFFERED_LOAD** PROD=1 — src/core/expert_source.cpp:872 (+3 more reads) docs: QUANTS.md, RX7900XTX.md, TROUBLESHOOTING.md
  `if (const char* env = std::getenv("STRATA_UNBUFFERED_LOAD"); env != nullptr && env[0] != '\0') {`
  doc (RX7900XTX.md): | `STRATA_UNBUFFERED_LOAD=1` | the file tier reads with O_DIRECT, not through the page cache | **removes the hangs**: with 64 GB RAM, page-cache reads triggered memory reclaim and `svm_range_restore_work` stalls of the GPU queues, 5 of 11 long prompts hung, 0 of 16 after | bitwise |
- **STRATA_VERIFY_ALL_RESIDENT** — src/core/verify.cpp:1166
  `const char* v_ar = std::getenv("STRATA_VERIFY_ALL_RESIDENT");`
- **STRATA_VERIFY_ARENA** — src/core/expert_source.cpp:5968
  `if (std::getenv("STRATA_VERIFY_ARENA") != nullptr) {   // tests: the loaded arena's checksum, any loader`
  // tests: the loaded arena's checksum, any loader
- **STRATA_VERIFY_ASYNC_LAUNCH** — src/core/verify.cpp:3152 docs: DETAILS.md
  `const char* value = std::getenv("STRATA_VERIFY_ASYNC_LAUNCH");`
  doc (DETAILS.md): | `STRATA_VERIFY_ASYNC_LAUNCH=1` | CUDA, single-request verifier | Runs the CUDA graph launch of a verify window on a separate host thread so the caller keeps serving CPU expert doorbells. A diagnostic for Compute Sanitizer runs. | |
- **STRATA_VERIFY_COHERENT** — src/core/verify.cpp:319
  `const bool g_coherent = env_on("STRATA_VERIFY_COHERENT");`
- **STRATA_VERIFY_COMPLEMENT** — src/core/expert_source.cpp:4094 (+1 more reads)
  `if (std::getenv("STRATA_VERIFY_COMPLEMENT") != nullptr && host != nullptr && bytes > 0) {`
- **STRATA_VERIFY_DEBUG** — src/core/verify.cpp:103
  `const bool g_dbg = std::getenv("STRATA_VERIFY_DEBUG") != nullptr;`
- **STRATA_VERIFY_DEVICE_PLAN** — src/core/expert_source.cpp:5025 (+2 more reads) docs: INTEL.md, INTEL_ARC.md
  `static const bool device_plan = [] { const char* v = std::getenv("STRATA_VERIFY_DEVICE_PLAN"); return v != nullptr && std::atoi(v) != 0; }();`
  // the GPU's copy_rows_from_mapped zeroes the rows it computed itself (dec_batch); STRATA_VERIFY_DEVICE_PLAN's copy_or_zero_from_mapped copies every row, so there the host still zeroes them
  doc (INTEL_ARC.md): `ZES_ENABLE_SYSMAN=1` and `STRATA_VERIFY_DEVICE_PLAN=1`, then run `build-sycl-aot/strata` or `sycl/serve/server_intel.py`
- **STRATA_VERIFY_EARLY_PLE_FLAG** — src/core/verify.cpp:378 docs: release-notes-0.2.2.md
  `if (const char* v = std::getenv("STRATA_VERIFY_EARLY_PLE_FLAG")) return std::atoi(v) < 0 ? 0 : std::min(2, std::atoi(v));`
  doc (release-notes-0.2.2.md): - **Speculative decoding.** A rare hang of the first verify window on the HIP engine is fixed: about 1 run in 5 on a Strix Halo with IQ3_S stopped after the first window (8 of 41 runs without the fix, 0 of 46 with it). The cause was a GPU launch that waited for a flag the host raised only after the 
- **STRATA_VERIFY_NODES** — src/core/verify.cpp:2681 (+3 more reads)
  `if (std::getenv("STRATA_VERIFY_NODES") != nullptr) {   // what the window graph holds`
  // what the window graph holds
- **STRATA_VERIFY_PROFILE** — src/core/verify.cpp:1043 docs: A770_SPEED_SPEC.md, DETAILS.md, OLDER_GPUS.md, QUANTS.md
  `prof_on_ = std::getenv("STRATA_VERIFY_PROFILE") != nullptr;`
  doc (DETAILS.md): Profiling: start the server with `STRATA_DECODE_TIMING=1` (and `STRATA_VERIFY_PROFILE=1` for the GPU side). After each request
- **STRATA_VERIFY_QDEDUP** — src/core/verify.cpp:169
  `inline bool g_qdedup() { static const bool on = [] { const char* v = std::getenv("STRATA_VERIFY_QDEDUP"); return v != nullptr && std::atoi(v) != 0; }(); return `
- **STRATA_VERIFY_TRACE** — src/core/verify.cpp:322
  `const bool g_trace = env_on("STRATA_VERIFY_TRACE");`
- **STRATA_VRAM_FREE** — src/core/expert_cache.cpp:141 docs: DETAILS.md, release-notes-0.2.7.md
  `const char* v = std::getenv("STRATA_VRAM_FREE");`
  doc (DETAILS.md): | `STRATA_VRAM_FREE=device` (Windows, NVIDIA, #1911) | RTX 5090 (WDDM), Core i7-13700K, 64 GB, 128K context, image encoder loaded, `--expert-cache auto` | The switch reads the free VRAM of the whole card through NVML: with 6 GiB held by another process CUDA still read 30,994 MiB free where NVML read
- **STRATA_WDDM_BUDGET** — src/core/device.cu:195 docs: AMD_HIP.md
  `const char* v = std::getenv("STRATA_WDDM_BUDGET");`
  doc (AMD_HIP.md): the free figure by what Windows' video memory budget for the process withholds (logged once). `STRATA_WDDM_BUDGET=0` turns

## src/dsv41
- **STRATA_DENSE_PFGEMM** — src/dsv41/ds4_model.cu:3162
  `static const bool pf = strata::ds4::dense_pfgemm_default(env_tri("STRATA_DENSE_PFGEMM"), defaults_026());`
- **STRATA_DS4_A_MB** — src/dsv41/ds4_model.cu:3045
  `const char* v = std::getenv("STRATA_DS4_A_MB");`
- **STRATA_DS4_DISK_SKIP_FROM** — src/dsv41/ds4_model.cu:1088
  `const char* v = std::getenv("STRATA_DS4_DISK_SKIP_FROM");`
- **STRATA_DS4_DISK_SKIP_W** — src/dsv41/ds4_model.cu:1084
  `const char* v = std::getenv("STRATA_DS4_DISK_SKIP_W");`
- **STRATA_DS4_DSPARK_CUM** — src/dsv41/ds4_main.cpp:161
  `static const char* const e = std::getenv("STRATA_DS4_DSPARK_CUM");`
- **STRATA_DS4_LANE_FREE** — src/dsv41/ds4_model.cu:5105
  `const char* v = std::getenv("STRATA_DS4_LANE_FREE");`
- **STRATA_DS4_NO_LIGHT** — src/dsv41/ds4_iq.cu:1225
  `const char* v = std::getenv("STRATA_DS4_NO_LIGHT");`
- **STRATA_DS4_NO_TC** — src/dsv41/ds4_gguf.cu:995 (+2 more reads)
  `const char* v = std::getenv("STRATA_DS4_NO_TC");`
- **STRATA_DS4_PROMPT_SKIP** — src/dsv41/ds4_model.cu:8453
  `if (v == nullptr) v = std::getenv("STRATA_DS4_PROMPT_SKIP");`
- **STRATA_DS4_RAM_TIER** — src/dsv41/ds4_model.cu:1076 (+1 more reads)
  `bool ram_tier = std::getenv("STRATA_DS4_RAM_TIER") != nullptr && std::atoi(std::getenv("STRATA_DS4_RAM_TIER")) != 0;`
- **STRATA_DS4_REUSE** — src/dsv41/ds4_main.cpp:351 (+1 more reads)
  `const bool reuse = std::getenv("STRATA_DS4_REUSE") == nullptr || std::atoi(std::getenv("STRATA_DS4_REUSE")) != 0;`
- **STRATA_DS4_SLOT_CAP** — src/dsv41/ds4_main.cpp:352
  `int slot_max = slot_keep ? std::max(0, (int) env_num("STRATA_DS4_SLOT_CAP", 4)) : 0;`
- **STRATA_DS4_SLOT_DAYS** — src/dsv41/ds4_main.cpp:354
  `const double slot_days = env_num("STRATA_DS4_SLOT_DAYS", 7);`
- **STRATA_DS4_SLOT_DIR** — src/dsv41/ds4_main.cpp:580 (+1 more reads)
  `slot_dir = std::getenv("STRATA_DS4_SLOT_DIR") ? std::filesystem::path(std::getenv("STRATA_DS4_SLOT_DIR"))`
- **STRATA_DS4_SLOT_GB** — src/dsv41/ds4_main.cpp:355 docs: DEEPSEEK41.md
  `const uint64_t slot_budget = (uint64_t) (env_num("STRATA_DS4_SLOT_GB", 16) * 1073741824.0);`
  doc (DEEPSEEK41.md): (`STRATA_DS4_SLOT_GB`) and are removed after a week. The system prompt and tools shared by an agent
- **STRATA_DS4_SLOT_KEEP** — src/dsv41/ds4_main.cpp:350 (+1 more reads) docs: DEEPSEEK41.md
  `std::getenv("STRATA_DS4_SLOT_KEEP") != nullptr && std::atoi(std::getenv("STRATA_DS4_SLOT_KEEP")) != 0;`
  doc (DEEPSEEK41.md): and its sub-agents are kept as a checkpoint too. `STRATA_DS4_SLOT_KEEP=0` and `STRATA_DS4_AUTO_PIN=0` turn this off.
- **STRATA_DS4_SLOT_MIN** — src/dsv41/ds4_main.cpp:353
  `const size_t slot_min = (size_t) std::max(1.0, env_num("STRATA_DS4_SLOT_MIN", 1024));`
- **STRATA_DS4_TQ_WORDS** — src/dsv41/ds4_tq.cu:472
  `const char* e = std::getenv("STRATA_DS4_TQ_WORDS");`
- **STRATA_FORCE_AVX2** — src/dsv41/vendor/exl3_cpu.cpp:1024 (+2 more reads)
  `const char* f = std::getenv("STRATA_FORCE_AVX2");`
- **STRATA_GLM_EXL3_DECODE** — src/dsv41/vendor/exl3.cu:1280
  `const char* v = std::getenv("STRATA_GLM_EXL3_DECODE");`

## src/kernels
- **STRATA_ACT_DUMP** — src/kernels/cpu/native_expert.cpp:261
  `const char* p = std::getenv("STRATA_ACT_DUMP");`
- **STRATA_ACT_DUMP_COV** — src/kernels/cpu/native_expert.cpp:264 (+1 more reads)
  `cov = std::getenv("STRATA_ACT_DUMP_COV") != nullptr && std::atoi(std::getenv("STRATA_ACT_DUMP_COV")) != 0;`
- **STRATA_ACT_DUMP_LAYERS** — src/kernels/cpu/native_expert.cpp:265
  `if (const char* l = std::getenv("STRATA_ACT_DUMP_LAYERS")) {`
- **STRATA_ARGMAX_MULTI** — src/kernels/cuda/sampler.cu:1277 (+1 more reads) docs: DETAILS.md
  `const char* v = std::getenv("STRATA_ARGMAX_MULTI");`
  doc (DETAILS.md): | 0.1.36 (#136) | RTX 5070, Q2_0, fused int8 kernels (RTX 30 and newer) | Prompt 4K 1,294 -> 1,570, 32K 2,170 -> 2,653, 128K 2,123 -> 2,468 tok/s (+16-22%), teacher-forced KL 0.009 at 32K vs 0.012 before. Decode on thread-block clusters (RTX 50, sm_90+): Q2_0 output 4K 89 -> 93.5, 128K 64.5 -> 76.4 
- **STRATA_ARGMAX_ROWS_SM70** — src/kernels/cuda/verify_kernels.cu:993 docs: NVIDIA_V100.md
  `const char* e = std::getenv("STRATA_ARGMAX_ROWS_SM70");`
  doc (NVIDIA_V100.md): | `STRATA_ARGMAX_ROWS_SM70=1` | The multi-block greedy pick on sm_7x (#2357), bitwise the one-block pick. |
- **STRATA_ATTN_DAILY** — src/kernels/cuda/qsa_decode_attn.cu:843 docs: DETAILS.md
  `const char* v = std::getenv("STRATA_ATTN_DAILY");`
  doc (DETAILS.md): | `STRATA_ATTN_DAILY=1` | Decode attention, two cells per step | Exact; on by default on sm_86 and 12.0 |
- **STRATA_ATTN_LANECELL** — src/kernels/cuda/qsa_decode_attn.cu:1151 (+2 more reads) docs: RADEON_780M.md, RX7900XTX.md, STRIX_HALO.md
  `static const bool lane_cell_rows = [] { const char* v = std::getenv("STRATA_ATTN_LANECELL"); return v && v[0] == '1'; }();`
  // The plain kernel is what qsa_decode_attn_batch runs unless one of its variants is on (lane-cell scoring, the pre-sm_75 / gfx103x kernel, the gfx906 swizzle): there each row goes through that call, one launch per row.
  doc (RX7900XTX.md): | `STRATA_EXPERT_V2`, `STRATA_TSUM`, `STRATA_ATTN_LANECELL`+`MERGE_V2`, `STRATA_GDN_SPLIT`, `STRATA_LFUSE`/`QFUSE`, the gfx12 default set | single runs looked +2-7%, combinations did not hold above the decode noise |
- **STRATA_ATTN_MERGE_V2** — src/kernels/cuda/qsa_decode_attn.cu:929
  `const char* v = std::getenv("STRATA_ATTN_MERGE_V2");`
- **STRATA_ATTN_PRE75** — src/kernels/cuda/qsa_decode_attn.cu:868 docs: NVIDIA_V100.md, OLDER_GPUS.md
  `const char* e = std::getenv("STRATA_ATTN_PRE75");`
  doc (OLDER_GPUS.md): | RX 6800 / 6900 series | gfx1030 | setup (`--backend hip`), unvalidated. The #540 attention kernel is the default there (`STRATA_ATTN_PRE75=0` runs the standard kernel). See [AMD_HIP.md](AMD_HIP.md#rdna2-gfx1030) |
- **STRATA_ATTN_V3** — src/kernels/cuda/qsa_decode_attn.cu:440 docs: DETAILS.md
  `static const int env = [] { const char* v = std::getenv("STRATA_ATTN_V3"); return v ? (v[0] == '0' ? 0 : 1) : -1; }();`
  doc (DETAILS.md): `STRATA_TOPK_SPLIT`, `STRATA_TOPK_SAMPLE`, `STRATA_ATTN_V3`, `STRATA_Q2_WARP`, `STRATA_FUSE_WAIT=2`, `STRATA_QIL`,
- **STRATA_B6_MMVQ_ROWS** — src/kernels/cuda/native_mmvq.cu:1228 docs: DETAILS.md, OLDER_GPUS.md
  `int b6_rows_mode() { if (g_b6_rows < 0) { const char* v = std::getenv("STRATA_B6_MMVQ_ROWS"); g_b6_rows = v ? std::atoi(v) : 0; } return g_b6_rows; }`
  doc (DETAILS.md): | `STRATA_B6_MMVQ_ROWS=1` | Exact multi-column MMVQ reusing the activation fragment across rows | Exact; on by default on sm_86 and sm_60 |
- **STRATA_BENCH_QMIXED** — src/kernels/fused_gr_bench.cpp:231
  `const bool with_q = std::getenv("STRATA_BENCH_QMIXED") != nullptr;`
- **STRATA_CPU_IQ_ALL_EXACT1** — src/kernels/cpu/native_expert.cpp:399 docs: DETAILS.md
  `const char* v = std::getenv("STRATA_CPU_IQ_ALL_EXACT1");`
  doc (DETAILS.md): | `STRATA_CPU_IQ_ALL_EXACT1=1` | AVX2 CPUs without AVX-512 | Strata's AVX-2 decode for one-token i-quant gate/up rows, with ggml's float order, so the output does not change. On by default on sm_86. | End to end +0.4 to +2.5%, so left off elsewhere. |
- **STRATA_CPU_YMM** — src/kernels/cpu/expert.cpp:151
  `static const bool kZmm = std::getenv("STRATA_CPU_YMM") == nullptr;`
  // over 64 activations, ONE convert and ONE FMA whose per-chunk scales come from a permute of a vector of scale products built for eight blocks at a time; the weight-independent correction is one FMA per eight blocks. The sum order differs from the 256-bit kernel (last-bit differences); the verify window and plain decode both use this kernel, so speculative decode still reproduces plain decode exactl
- **STRATA_DBG_GDN** — src/kernels/cuda/verify_kernels.cu:1100 (+1 more reads)
  `const char* dbg = std::getenv("STRATA_DBG_GDN");`
- **STRATA_DEQUANT_WIDE** — src/kernels/cuda/dequant_bf16.cu:287 docs: DETAILS.md, OLDER_GPUS.md, release-notes-0.2.7.md
  `static const int env = [] { const char* v = std::getenv("STRATA_DEQUANT_WIDE"); return v != nullptr && v[0] != '\0' ? (std::atoi(v) != 0 ? 1 : 0) : -1; }();`
  doc (DETAILS.md): `STRATA_DEQUANT_WIDE` (wide dequantization of Q4_K, Q5_K, Q6_K and IQ4_XS for the prompt's dense weights) is on by default on
- **STRATA_DF_PDL** — src/kernels/cuda/verify_kernels.cu:1695 (+2 more reads)
  `static const int mode = [] { const char* v = std::getenv("STRATA_DF_PDL"); return v ? std::atoi(v) : 1; }();`
  // every node the next captured node will depend on is a kernel (CUDA allows a programmatic edge only between two kernel nodes): never after a memcpy, memset, host or event node.  A join of branches gives several kernels, a programmatic edge from each; STRATA_DF_PDL=2 allows a single predecessor only.
- **STRATA_DOWN_WS** — src/kernels/cuda/iq_kernels.cu:4571 docs: OLDER_GPUS.md, release-notes-0.2.7.md
  `static const bool env = env_on("STRATA_DOWN_WS");`
  doc (release-notes-0.2.7.md): - Opt-in switches from pull requests, each checked for exactness or by unit tests and builds, not for speed on your card: a bigger Pascal (GP100) set (`STRATA_DOWN_WS=1`, `STRATA_MTP_Q8_SM60=1`, `STRATA_MMQ_WS=1`, `STRATA_PATTN_SM60=1`, `STRATA_EXPERT_NIBBLE=1`), `STRATA_PF_FUSED_Q2N=1` for the Q2_0
- **STRATA_EXPDEC** — src/kernels/cuda/iq_kernels.cu:4062 docs: DETAILS.md, EXPERTDEC.md
  `int expdec_mode() { if (g_expdec < 0) g_expdec = env_on("STRATA_EXPDEC") ? 1 : 0; return g_expdec; }`
  doc (DETAILS.md): | `STRATA_EXPDEC=1` ([EXPERTDEC.md](EXPERTDEC.md)) | Gate/up of the window's resident experts with the q8_1 rows in shared memory | Exact |
- **STRATA_EXPDEC_D20** — src/kernels/cuda/iq_kernels.cu:4066 docs: EXPERTDEC.md
  `int g_expdec_d20 = env_int_or("STRATA_EXPDEC_D20", 0);      // 1: EXPDEC also for the IQ4_NL down (bench: no gain, default kernel)`
  // 1: EXPDEC also for the IQ4_NL down (bench: no gain, default kernel)
  doc (EXPERTDEC.md): Q2_0 at n_ff 640; IQ4_NL with `STRATA_EXPDEC_D20=1`) instead:
- **STRATA_EXPDEC_DOWN** — src/kernels/cuda/iq_kernels.cu:4070 docs: EXPERTDEC.md
  `int g_expdec_down = env_int_or("STRATA_EXPDEC_DOWN", 0);`
  // 1: EXPDEC for the down too (Q2_0; IQ4_NL with _D20).  Default 0: in the engine (nsys of a 131k decode) the Q2_0 down with EXPDEC was ~10% slower than the default kernel although the bench alone had it at 0.78, so by default EXPDEC takes the gate/up only (-20/-23% at T >= 2 on an RTX 2080 Ti in the engine).
  doc (EXPERTDEC.md): the multi kernels off. The down is behind `STRATA_EXPDEC_DOWN=1`: in the engine the Q2_0 down with EXPDEC was about
- **STRATA_EXPDEC_DR** — src/kernels/cuda/iq_kernels.cu:4064 docs: EXPERTDEC.md
  `int g_expdec_dr = env_int_or("STRATA_EXPDEC_DR", 4);        // down rows per lane: 1, 2, 4 (Q2_0: R=4 wins on both cards)`
  // down rows per lane: 1, 2, 4 (Q2_0: R=4 wins on both cards)
  doc (EXPERTDEC.md): - compute R rows per lane (`STRATA_EXPDEC_R`, 1 or 2 for gate/up, default 1; `STRATA_EXPDEC_DR` 1/2/4 for down,
- **STRATA_EXPDEC_DRB** — src/kernels/cuda/iq_kernels.cu:4072
  `int g_expdec_drb = env_int_or("STRATA_EXPDEC_DRB", 0);      // down rows per block (0 = auto)`
  // down rows per block (0 = auto)
- **STRATA_EXPDEC_MINB** — src/kernels/cuda/iq_kernels.cu:4065 docs: EXPERTDEC.md
  `int g_expdec_minb = env_int_or("STRATA_EXPDEC_MINB", STRATA_EXPDEC_MINB);   // gate/up __launch_bounds__ min blocks: 2 (<= 128 regs) or 4 (<= 64)`
  // gate/up __launch_bounds__ min blocks: 2 (<= 128 regs) or 4 (<= 64)
  doc (EXPERTDEC.md): - gate/up `__launch_bounds__(256, STRATA_EXPDEC_MINB)`, default 4 (up to 64 registers, 4 blocks per SM like the
- **STRATA_EXPDEC_MINBLK** — src/kernels/cuda/iq_kernels.cu:4073 docs: EXPERTDEC.md
  `int g_expdec_minblk = env_int_or("STRATA_EXPDEC_MINBLK", 800);   // auto: the most rows per block that keep this many blocks`
  // auto: the most rows per block that keep this many blocks
  doc (EXPERTDEC.md): - take `rb` rows per block instead of 16 (`STRATA_EXPDEC_RB` / `_DRB`; 0 = the most that keep `STRATA_EXPDEC_MINBLK`,
- **STRATA_EXPDEC_R** — src/kernels/cuda/iq_kernels.cu:4063 docs: EXPERTDEC.md
  `int g_expdec_r = env_int_or("STRATA_EXPDEC_R", 1);          // gate/up rows per lane: 1, 2 (bench: R=1 wins on the 2080 Ti)`
  // gate/up rows per lane: 1, 2 (bench: R=1 wins on the 2080 Ti)
  doc (EXPERTDEC.md): - compute R rows per lane (`STRATA_EXPDEC_R`, 1 or 2 for gate/up, default 1; `STRATA_EXPDEC_DR` 1/2/4 for down,
- **STRATA_EXPDEC_RB** — src/kernels/cuda/iq_kernels.cu:4071 docs: EXPERTDEC.md
  `int g_expdec_rb = env_int_or("STRATA_EXPDEC_RB", 0);        // gate/up rows per block (0 = auto)`
  // gate/up rows per block (0 = auto)
  doc (EXPERTDEC.md): - take `rb` rows per block instead of 16 (`STRATA_EXPDEC_RB` / `_DRB`; 0 = the most that keep `STRATA_EXPDEC_MINBLK`,
- **STRATA_EXPERT_V2** — src/kernels/cuda/iq_kernels.cu:6267 docs: OLDER_GPUS.md, RADEON_780M.md, RX7900XTX.md, STRIX_HALO.md
  `static const bool v2 = [] { const char* v = std::getenv("STRATA_EXPERT_V2"); return v && v[0] == '1'; }();`
  // STRATA_EXPERT_NIBBLE (nib_layout): only the gate/up step below takes another kernel (launch_gu_nib, in place of launch_gu); SwiGLU, the q8_1 quantization and the down rows (GGUF, at L.down_off) are the layout's own
  doc (RX7900XTX.md): | `STRATA_EXPERT_V2`, `STRATA_TSUM`, `STRATA_ATTN_LANECELL`+`MERGE_V2`, `STRATA_GDN_SPLIT`, `STRATA_LFUSE`/`QFUSE`, the gfx12 default set | single runs looked +2-7%, combinations did not hold above the decode noise |
- **STRATA_EXPERT_V2K** — src/kernels/cuda/iq_kernels.cu:6285 docs: QUANTS.md, QWEN36.md
  `const char* v = std::getenv("STRATA_EXPERT_V2K");`
  doc (QWEN36.md): the new kernels off. Gate/up for Q4_K experts uses the V2K kernels (`STRATA_EXPERT_V2K`, the default on gfx12).
- **STRATA_EXP_MODE** PROD=8 — src/kernels/cuda/iq_kernels.cu:6148 (+1 more reads) docs: AMD_HIP.md, NVIDIA_V100.md, OLDER_GPUS.md, RX7900XTX.md
  `static const int m = [] { const char* v = std::getenv("STRATA_EXP_MODE"); return v ? std::atoi(v) : -1; }();`
  doc (AMD_HIP.md): | Grouped native experts | Mode 7: signs as `dp4a(g ^ m, u) - dp4a(m, u)`, grids and activations in LDS. IQ formats only (K-quant / Q5_1 / Q8_0 experts take the CUDA layout). | `STRATA_EXP_MODE=2` |
- **STRATA_FORCE_ISA** — src/kernels/cpu/expert_layout.cpp:30
  `const char* f = std::getenv("STRATA_FORCE_ISA");`
- **STRATA_FUSED_SWIGLU_Q81** — src/kernels/cuda/shared_expert.cu:208
  `const char* v = std::getenv("STRATA_FUSED_SWIGLU_Q81");`
- **STRATA_GDN_CHUNK** — src/prefill/kernels.cu:2733 (+2 more reads) docs: NVIDIA_V100.md
  `const char* chunk_v = std::getenv("STRATA_GDN_CHUNK");`
  // v100/gdn-chunk: the chunked recurrence (src/prefill/gdn_chunk.cu) on Volta, where the token chain is the cost.  STRATA_GDN_CHUNK=0 forces the recurrence, =1 forces the chunked path (the parity test's A/B switch); unset: cc == 7.0 only, every other architecture keeps the recurrence bit-for-bit as before.  Read per call on purpose - cheap next to the work, and the tests flip it between two launches.
  doc (NVIDIA_V100.md): | `STRATA_GDN_REC_WARP=2` | The chain-split DeltaNet recurrence of the prompt (#1098). Changes the FP32 summation order, so the default stays the pipelined kernel. `1` is the bit-exact sync-free variant; `STRATA_GDN_CHUNK=1` the chunked path. |
- **STRATA_GDN_COMMIT_SPLIT** — src/kernels/cuda/verify_kernels.cu:1099 (+1 more reads)
  `const char* cs = std::getenv("STRATA_GDN_COMMIT_SPLIT");`
- **STRATA_GDN_PARITY_TRACE** — src/kernels/gdn_parity.cpp:513
  `if (std::getenv("STRATA_GDN_PARITY_TRACE")) std::printf("    trace: T=%d '%s' with a q8_1 destination\n", T, c.name);`
- **STRATA_GDN_REC_WARP** — src/prefill/kernels.cu:2744 (+1 more reads) docs: NVIDIA_V100.md
  `const char* warp_v = std::getenv("STRATA_GDN_REC_WARP");`
  // the old pipelined kernel bit-for-bit. STRATA_GDN_REC_WARP (Volta only, opt-in): unset or 0 -> the pipelined kernel (the default; the chain split changes the summation order, so it is not the default without a V100 check here), 2 -> the chain-split kernel (measured +6..9%, FP32-level), the old pipelined kernel bit-for-bit is 0, 1 -> the sync-free bit-exact control.
  doc (NVIDIA_V100.md): | `STRATA_GDN_REC_WARP=2` | The chain-split DeltaNet recurrence of the prompt (#1098). Changes the FP32 summation order, so the default stays the pipelined kernel. `1` is the bit-exact sync-free variant; `STRATA_GDN_CHUNK=1` the chunked path. |
- **STRATA_GDN_SPLIT** — src/kernels/cuda/verify_kernels.cu:1098 (+1 more reads) docs: RADEON_780M.md, RX7900XTX.md, STRIX_HALO.md
  `const char* sp = std::getenv("STRATA_GDN_SPLIT");`
  doc (RX7900XTX.md): | `STRATA_EXPERT_V2`, `STRATA_TSUM`, `STRATA_ATTN_LANECELL`+`MERGE_V2`, `STRATA_GDN_SPLIT`, `STRATA_LFUSE`/`QFUSE`, the gfx12 default set | single runs looked +2-7%, combinations did not hold above the decode noise |
- **STRATA_GFX1151_EXP8** — src/kernels/cuda/iq_kernels.cu:6134
  `const char* v = std::getenv("STRATA_GFX1151_EXP8");`
- **STRATA_GFX906_ATTN_QUERY_SWIZZLE** — src/kernels/cuda/qsa_decode_attn.cu:967 (+1 more reads) docs: AMD_HIP.md
  `const char* v = std::getenv("STRATA_GFX906_ATTN_QUERY_SWIZZLE"); return v && v[0] == '1';`
  doc (AMD_HIP.md): gfx906 and nothing more. The attention switches `STRATA_GFX906_ATTN_QUERY_SWIZZLE=1` and `STRATA_GFX906_ATTN_REDUCE12=1` are
- **STRATA_GFX906_ATTN_QUERY_SWIZZLE_TRACE** — src/kernels/cuda/qsa_decode_attn.cu:971
  `static const bool query_swizzle_trace = std::getenv("STRATA_GFX906_ATTN_QUERY_SWIZZLE_TRACE") != nullptr;`
- **STRATA_GFX906_ATTN_REDUCE12** — src/kernels/cuda/qsa_decode_attn.cu:995 docs: AMD_HIP.md
  `const char* v = std::getenv("STRATA_GFX906_ATTN_REDUCE12");`
  doc (AMD_HIP.md): gfx906 and nothing more. The attention switches `STRATA_GFX906_ATTN_QUERY_SWIZZLE=1` and `STRATA_GFX906_ATTN_REDUCE12=1` are
- **STRATA_GFX906_ATTN_REDUCE12_TRACE** — src/kernels/cuda/qsa_decode_attn.cu:1002
  `const char* v = std::getenv("STRATA_GFX906_ATTN_REDUCE12_TRACE");`
- **STRATA_GROUPED_PAIR_MIN_HITS** — src/kernels/cuda/s2_expert_grouped.cu:546
  `const char* e = std::getenv("STRATA_GROUPED_PAIR_MIN_HITS");`
- **STRATA_GROUPED_V1** — src/kernels/cuda/iq_kernels.cu:6211
  `bool g_grouped_v1 = env_on("STRATA_GROUPED_V1");`
- **STRATA_GRP_KEEP_GOING** — src/kernels/gr_parity.cpp:473
  `const bool keep_going = std::getenv("STRATA_GRP_KEEP_GOING") != nullptr;`
- **STRATA_GRP_REPS** — src/kernels/gr_parity.cpp:472 (+1 more reads)
  `const int REPS = std::getenv("STRATA_GRP_REPS") ? std::max(1, std::atoi(std::getenv("STRATA_GRP_REPS"))) : 200;`
  // (STRATA_GRP_REPS=N more repetitions, STRATA_GRP_KEEP_GOING=1 counts every failure instead of stopping at the first: to measure a rare one)
- **STRATA_GR_DOWN_MAX4** — src/kernels/cuda/fused_gr.cu:1251
  `const char* v = std::getenv("STRATA_GR_DOWN_MAX4");`
- **STRATA_GR_DOWN_TG** — src/kernels/cuda/fused_gr.cu:1311 docs: DETAILS.md
  `static const int env = [] { const char* v = std::getenv("STRATA_GR_DOWN_TG"); return v ? std::atoi(v) : -1; }();`
  doc (DETAILS.md): that wins in both directions: `STRATA_SM75_IL`, `STRATA_SM75_EXP`, `STRATA_GR_UP75` / `STRATA_GR_DOWN_TG`, `STRATA_SCORES_HALVE`,
- **STRATA_GR_FAST** — src/kernels/cuda/fused_gr.cu:2293 docs: AMD_HIP.md, NVIDIA_V100.md, OLDER_GPUS.md
  `static const int env = [] { const char* v = std::getenv("STRATA_GR_FAST"); return v ? (std::atoi(v) != 0 ? 1 : 0) : -1; }();`
  doc (AMD_HIP.md): | Hyper-connection read | Norm loads in flight, 8 lanes per row for `up` | `STRATA_GR_FAST=0` |
- **STRATA_GR_NORM_FAST** — src/kernels/cuda/fused_gr.cu:1273 (+1 more reads) docs: DETAILS.md, NVIDIA_V100.md
  `static const bool on = [] { const char* e = std::getenv("STRATA_GR_NORM_FAST"); return e != nullptr && std::atoi(e) != 0; }();`
  // CUDA: opt-in with STRATA_GR_NORM_FAST=1 (measured on sm_70 only)
  doc (DETAILS.md): `STRATA_GR_NORM_FAST`, `STRATA_RAM_ADAPT`, `STRATA_KV_HOST_REGISTER`, `STRATA_HOST_CORE`, `STRATA_GR_DOWN_TG` (sm_86),
- **STRATA_GR_SPLIT** — src/kernels/cuda/fused_gr.cu:2439 (+1 more reads) docs: AMD_HIP.md
  `static const bool split_on = std::getenv("STRATA_GR_SPLIT") && std::string(std::getenv("STRATA_GR_SPLIT")) == "1";`
  // gfx906, opt-in STRATA_GR_SPLIT=1: the latency-hidden norm/up (STRATA_GR_FAST) with the K-split down (~3% faster per verify window).  Its fixed-order finish sums the K slices in another order than the single-token fused_gr_read, so the multi-token read is then no longer bitwise equal to T single-token calls (gr_parity's contract); off by default for that reason.
  doc (AMD_HIP.md): | `gr_down_multi`, opt-in | Split along K, about 3% per window; sums in another order | `STRATA_GR_SPLIT=1` |
- **STRATA_GR_UP75** — src/kernels/cuda/fused_gr.cu:1289 docs: DETAILS.md, OLDER_GPUS.md
  `static const int env = [] { const char* v = std::getenv("STRATA_GR_UP75"); return v ? (std::atoi(v) != 0 ? 1 : 0) : -1; }();`
  doc (DETAILS.md): that wins in both directions: `STRATA_SM75_IL`, `STRATA_SM75_EXP`, `STRATA_GR_UP75` / `STRATA_GR_DOWN_TG`, `STRATA_SCORES_HALVE`,
- **STRATA_GR_UP_WIDE** — src/kernels/cuda/fused_gr.cu:455
  `const char* v = std::getenv("STRATA_GR_UP_WIDE");`
- **STRATA_GR_V3** — src/kernels/gr_parity.cpp:342 (+9 more reads) docs: DETAILS.md
  `static const bool v3 = [] { const char* v = std::getenv("STRATA_GR_V3"); return v != nullptr && std::atoi(v) != 0; }();`
  // the split read (STRATA_GR_V3=1) sums in another order than the single-token kernel: equal within float rounding, not to the bit, so it is compared with a relative tolerance; the default kernels bit for bit
  doc (DETAILS.md): | `STRATA_GR_V3` | The hyper-connection read split over two kernels | Rounding level. On by default since 0.2.7 on a discrete compute capability 12.0 card (RTX 50, RTX PRO Blackwell) with more than 13 GiB (RTX PRO 5000: +1.2% decode with identical tokens); slower on sm_86, so off there. `=0` / `=1` 
- **STRATA_GU_SWIGLU** — src/kernels/cuda/iq_kernels.cu:4233 docs: DETAILS.md
  `static const int env = [] { const char* v = std::getenv("STRATA_GU_SWIGLU"); return v != nullptr ? (std::atoi(v) != 0 ? 1 : 0) : -1; }();`
  doc (DETAILS.md): | sm_86 (RTX 3050-3090, RTX A2000-A6000) | `STRATA_ADAPT_NOWAIT=1`, `STRATA_ADAPT_LAG=2`, `STRATA_CPU_IQ_ALL_EXACT1=1`, `STRATA_SIDE_MIXER=2`, `STRATA_ATTN_DAILY=1`, `STRATA_GR_UP75=1`, `STRATA_GU_SWIGLU=1`, `STRATA_QSA_ROWS=1`, `STRATA_B6_MMVQ_ROWS=1` | `STRATA_SM86_PERF=0` |
- **STRATA_HC_PERSIST** — src/kernels/cuda/fused_gr.cu:3040 (+3 more reads) docs: AMD_HIP.md
  `static const bool dp = [] { const char* v = std::getenv("STRATA_HC_PERSIST"); return v != nullptr && std::atoi(v) == 3; }();`
  doc (AMD_HIP.md): without `--kv-resident`, the same setup answered normally. Removing the other switches one at a time (`STRATA_HIP_PROMPT_F16`, `STRATA_HC_PERSIST`,
- **STRATA_HC_SPLIT** — src/kernels/cuda/fused_gr.cu:2678 (+1 more reads)
  `const char* e = std::getenv("STRATA_HC_SPLIT");`
  // not checked on this card: the plain read, unless STRATA_HC_SPLIT names a variant (a test such as gr_parity)
- **STRATA_HIP_ROUTER_FAST** — src/kernels/cuda/router_top10.cu:429
  `static const bool old = std::getenv("STRATA_HIP_ROUTER_FAST") == nullptr;`
  // gfx906 (wave64): the one-wavefront kernel below stays the default; the S6 kernel is wave32-shaped and only runs here on request (STRATA_HIP_ROUTER_FAST=1) until it is measured on this card
- **STRATA_HIP_ROUTER_OLD** — src/kernels/cuda/router_top10.cu:431 docs: AMD_HIP.md
  `static const bool old = std::getenv("STRATA_HIP_ROUTER_OLD") != nullptr;`
  doc (AMD_HIP.md): | `STRATA_HIP_ROUTER_OLD=1` | all HIP | Off | Run the portable MoE router kernel instead of the fast one |
- **STRATA_HIP_SWIGLU_FUSED** — src/kernels/cuda/iq_kernels.cu:6426
  `static const bool sw_fused = env_on("STRATA_HIP_SWIGLU_FUSED");`
  // gfx906: the separate SwiGLU and q8_1 passes stay the default (the A/B baseline); the RDNA one-pass kernel (bitwise the same) with STRATA_HIP_SWIGLU_FUSED=1
- **STRATA_HIP_WMMA** PROD=1 — src/kernels/cuda/qsa_prompt_attn.cu:2190 (+2 more reads) docs: AMD_HIP.md, RADEON_780M.md, RX7900XTX.md, STRIX_HALO.md, release-notes-0.2.0.md
  `const char* e = std::getenv("STRATA_HIP_WMMA");`
  doc (AMD_HIP.md): - **WMMA prompt attention** is opt-in on Windows (`STRATA_HIP_WMMA=1`); it is the default on gfx12 on Linux.
- **STRATA_HIP_WMMA_MIN_CAP** — src/kernels/cuda/qsa_prompt_attn.cu:2229
  `static const int64_t min_cap = [] { const char* e = std::getenv("STRATA_HIP_WMMA_MIN_CAP"); return e ? (int64_t) std::atoll(e) : (int64_t) 0; }();`
- **STRATA_HIP_WMMA_MIN_Q** — src/kernels/cuda/qsa_prompt_attn.cu:2228 docs: AMD_HIP.md
  `static const int64_t min_q = [] { const char* e = std::getenv("STRATA_HIP_WMMA_MIN_Q"); return e ? (int64_t) std::atoll(e) : (int64_t) 64; }();`
  doc (AMD_HIP.md): | `STRATA_HIP_WMMA` | gfx12; gfx11 on request | gfx12 Linux: on with int8 KV. Windows and gfx11: `=1` | QSA prompt attention on the matrix cores. `=0` off; `=auto` takes it only for batches of `STRATA_HIP_WMMA_MIN_Q` (64) or more queries. Not bitwise: greedy text can differ from about token 50 on. |
- **STRATA_IQ256_GATHER** — src/kernels/cpu/expert_layout.cpp:249 (+1 more reads)
  `const char* v = std::getenv("STRATA_IQ256_GATHER");`
- **STRATA_IQ3S_MT1** — src/kernels/cpu/native_expert.cpp:365 docs: DETAILS.md
  `static const bool iq3s_one = env == nullptr && std::getenv("STRATA_IQ3S_MT1") != nullptr && cpu_avx2_ok() && std::getenv("STRATA_NO_IQ256") == nullptr &&`
  // of the window.  So IQ3_S takes it for every group, and those rows no longer depend on the drafting.  A machine- wide rule, not a per-core one: every core rounds an expert the same.  Every probe here is in expert_layout.cpp and cpu_avx2_ok() comes first, so no AVX2 code runs before the check.  STRATA_IQ_MT_MIN set keeps its rule. Opt-in (STRATA_IQ3S_MT1=1): it changes a lone token's IQ3_S rounding 
  doc (DETAILS.md): | `STRATA_IQ_MT_MIN=1`, `STRATA_IQ3S_MT1=1` | CPU | See [Draft layer](#draft-layer) (reproducible output; the second gives IQ3_S the multi-token kernel for one token on Alder Lake and later without AVX-512). | |
- **STRATA_IQ_GATHER** — src/kernels/cpu/iq_avx512.cpp:43
  `const char* v = std::getenv("STRATA_IQ_GATHER");`
- **STRATA_IQ_MT_MIN** — src/kernels/cpu/native_expert.cpp:356 (+5 more reads) docs: BATCHING.md, DETAILS.md, OLDER_GPUS.md, RESEARCH_RUNS.md, SPLIT_SERVE.md
  `static const char* env = std::getenv("STRATA_IQ_MT_MIN");`
  // #152: from how many tokens the multi-token kernels run (ggml's vec_dot below that).  The default 2 is the measured-fastest rule, but a token's expert rows then round differently alone than in a group, so greedy output can depend on how many drafts a verify window held.  STRATA_IQ_MT_MIN=1 (opt-in, 0.1.30) uses the multi-token kernels for every group: output independent of the drafting, at a measur
  doc (DETAILS.md): differ. `STRATA_IQ_MT_MIN=1` uses the multi-token kernels for every group, so the answer no longer depends on drafting (IQ3_S
- **STRATA_IQ_PREFETCH** — src/kernels/cpu/iq_avx1.cpp:138 (+3 more reads)
  `const char* v = std::getenv("STRATA_IQ_PREFETCH");`
- **STRATA_IQ_STAGE_GRID** — src/kernels/cuda/iq_kernels.cu:3404 docs: GYRO.md, release-notes-0.2.2.md
  `const char* v = std::getenv("STRATA_IQ_STAGE_GRID");`
  doc (release-notes-0.2.2.md): - **Gyro decodes faster on NVIDIA cards.** The gate/up and down kernels for agentionai's trellis experts now keep the codebook in shared memory and take four rows per warp. On an RTX 3060 (12 GB) Gyro-S went from 54.3 to 62.5 tokens per second (+15%) and Gyro-M from 50.2 to 54.8 (+9%), 5 interleaved
- **STRATA_IQ_STAGE_GRID_MMVQ** — src/kernels/cuda/iq_kernels.cu:3411
  `const char* v = std::getenv("STRATA_IQ_STAGE_GRID_MMVQ");`
- **STRATA_IQ_STAGE_TABLES** — src/kernels/cuda/iq_kernels.cu:3422 docs: OLDER_GPUS.md
  `const char* v = std::getenv("STRATA_IQ_STAGE_TABLES");`
  doc (OLDER_GPUS.md): | `STRATA_IQ_STAGE_TABLES=1` | Pascal | off | IQ3_XXS / IQ3_S tables staged in shared memory (bitwise the same output). |
- **STRATA_KQ256** — src/kernels/cpu/native_expert.cpp:435 (+1 more reads) docs: QUANTS.md, UNSLOTH_Q4.md
  `static const bool kq = [] { const char* v = std::getenv("STRATA_KQ256"); return cpu_avx2_ok() && v != nullptr && std::atoi(v) != 0; }();`
  // Unsloth UD-Q4_K_XL's Q4_K gate/up: the multi-token kernel is bit-exact against ggml's per-token dot (any group size, no #152 rule).  Opt-in, STRATA_KQ256=1: measured no faster in the engine (a window's expert groups hold ~1.4 tokens and the weights stay in L1 across ggml's per-token calls; 1.01-1.13x in native_expert_parity).
  doc (UNSLOTH_Q4.md): | `STRATA_KQ256=1` | Multi-token AVX2 kernels for the Q4_K / Q5_1 / Q8_0 experts. Bit-exact with ggml's, but measured no faster, so off. |
- **STRATA_KQ_SPLIT** — src/kernels/cuda/iq_kernels.cu:907
  `inline bool g_kq_split = [] { const char* v = std::getenv("STRATA_KQ_SPLIT"); return v != nullptr && v[0] == '1'; }();`
- **STRATA_MMVF_ROWS** — src/kernels/cuda/native_bf16.cu:272 (+2 more reads) docs: A770_SPEED_SPEC.md, RADEON_780M.md, STRIX_HALO.md
  `static const bool rows = [] { const char* v = std::getenv("STRATA_MMVF_ROWS"); return v && v[0] == '1'; }();`
  doc (A770_SPEED_SPEC.md): `STRATA_MMVF_ROWS=1`. The latter is already implemented in
- **STRATA_MMVQ_IL_120** — src/kernels/cuda/native_mmvq.cu:3790 docs: DETAILS.md, MMVQ_IL_TABLE.md
  `static const bool own120 = il_env_on("STRATA_MMVQ_IL_120");   // 147-verify: =0 gives a big 12.0 card the shared table again`
  // 147-verify: =0 gives a big 12.0 card the shared table again
  doc (DETAILS.md): and, on cards with 80 or more SMs, its own 2-4 token table. `STRATA_MMVQ_IL_WIDE=0` and `STRATA_MMVQ_IL_120=0` turn them off.
- **STRATA_MMVQ_IL_89** — src/kernels/cuda/native_mmvq.cu:3714 (+1 more reads) docs: DETAILS.md, MMVQ_IL_TABLE.md, release-notes-0.2.7.md
  `static const bool on = strata::mmvq_il_89_resolve(std::getenv("STRATA_MMVQ_IL_89"), false, 89, strata::qwen_defaults_026());`
  doc (DETAILS.md): on an RTX 40 card by us (same output bit for bit): `STRATA_MMVQ_IL_89=0` or `STRATA_DEFAULTS=026` turns them off.
- **STRATA_MMVQ_IL_PF** — src/kernels/cuda/native_mmvq.cu:2195 docs: DETAILS.md, MMVQ_IL_TABLE.md
  `static const int env = [] { const char* v = std::getenv("STRATA_MMVQ_IL_PF"); return v ? std::atoi(v) : 0; }();`
  doc (DETAILS.md): | `STRATA_MMVQ_IL_PF=1` | Hoisted-load, exact-integer kernels for the interleaved small-batch matvec where the sm_80 table picks them (Q6_K only so far, [MMVQ_IL_TABLE.md](MMVQ_IL_TABLE.md)). On a card that is not sm_80 the value 1 does nothing. `=2` to `=6` force one variant everywhere (A/B only). 
- **STRATA_MMVQ_IL_Q3K** — src/kernels/cuda/native_mmvq.cu:3708
  `bool il_q3k_on() { static const bool on = il_env_on("STRATA_MMVQ_IL_Q3K"); return on; }`
- **STRATA_MMVQ_IL_ROWS** — src/kernels/cuda/native_mmvq.cu:3736 docs: MMVQ_IL_TABLE.md
  `const char* e = std::getenv("STRATA_MMVQ_IL_ROWS");`
  doc (MMVQ_IL_TABLE.md): 4. To try a table without rebuilding, set `STRATA_MMVQ_IL_ROWS="type:ncols:r0,r1,r2,r3,r4;..."`, for example
- **STRATA_MMVQ_IL_SM80** — src/kernels/cuda/native_mmvq.cu:3813 docs: DETAILS.md, MMVQ_IL_TABLE.md, release-notes-0.2.7.md
  `if (cc[dev] == 80 && !strata::sm80_default_on(std::getenv("STRATA_MMVQ_IL_SM80"), strata::qwen_defaults_026())) cc[dev] = 81;   // =0 or STRATA_DEFAULTS=026`
  // STRATA_MMVQ_IL_SM80=0: an sm_80 card takes the shared table as before kIlRows_80 (A/B) =0 or STRATA_DEFAULTS=026
  doc (DETAILS.md): Two sm_80 defaults come with the same change and are on without a switch, only on a compute capability 8.0 card: the wide dense dequant kernels (`STRATA_DEQUANT_WIDE=0` turns them off) and the sm_80 rows tables of the interleaved matvec (`STRATA_MMVQ_IL_SM80=0` turns them off). Both are bitwise. The
- **STRATA_MMVQ_IL_T1** — src/kernels/cuda/native_mmvq.cu:3707
  `bool il_t1_on() { static const bool on = il_env_on("STRATA_MMVQ_IL_T1"); return on; }`
- **STRATA_MMVQ_IL_WIDE** — src/kernels/cuda/native_mmvq.cu:3768 docs: DETAILS.md, MMVQ_IL_TABLE.md
  `static const bool wide = il_env_on("STRATA_MMVQ_IL_WIDE");`
  doc (DETAILS.md): and, on cards with 80 or more SMs, its own 2-4 token table. `STRATA_MMVQ_IL_WIDE=0` and `STRATA_MMVQ_IL_120=0` turn them off.
- **STRATA_MMVQ_WAVE** — src/kernels/cuda/native_mmvq.cu:2334 (+3 more reads) docs: AMD_HIP.md
  `bool g_wave_off = std::getenv("STRATA_MMVQ_WAVE") && std::string(std::getenv("STRATA_MMVQ_WAVE")) == "0";`
  // 64 lanes exactly as the CUDA kernels stride them over a block (kbx = lane / T, stride 64 / T), and a 64-lane butterfly instead of the LDS partials and __syncthreads of the one-block-per-row layout: on gfx906 a block per 2 KB row spent most of its time being launched and joined.  The SAME kernel serves every column count 1..8, so a column's sums do not depend on how many columns (verify tokens) rid
  doc (AMD_HIP.md): | MMVQ | One wavefront per row, 64-lane butterfly, no LDS | `STRATA_MMVQ_WAVE=0` |
- **STRATA_MULTI_BLOCK_ARGMAX** — src/kernels/cuda/verify_kernels.cu:976
  `const char* v = std::getenv("STRATA_MULTI_BLOCK_ARGMAX");`
- **STRATA_NIB_GU_PROTO** — src/kernels/cuda/iq_kernels.cu:4920 docs: OLDER_GPUS.md
  `const char* e = std::getenv("STRATA_NIB_GU_PROTO");`
  doc (OLDER_GPUS.md): - **Opt-in `STRATA_NIB_GU_PROTO=1`** (with `STRATA_EXPERT_NIBBLE=1`): the 4-bit gate/up runs `nibx_gu_kernel`
- **STRATA_NORM_ROPE** — src/kernels/cuda/native_rope.cu:180
  `const char* v = std::getenv("STRATA_NORM_ROPE");   // AMD: opt in until rope_parity check 6 passes there`
  // AMD: opt in until rope_parity check 6 passes there
- **STRATA_NO_AVXVNNI** — src/kernels/cpu/expert_layout.cpp:300 (+1 more reads) docs: DETAILS.md
  `if (const char* v = std::getenv("STRATA_NO_AVXVNNI"); v != nullptr && std::atoi(v) != 0) return false;`
  doc (DETAILS.md): | `STRATA_NO_AVXVNNI=1` | CPUs with AVX-VNNI | Turns the AVX-VNNI row forms off (they give the same bits, 4-25% faster rows). | A diagnostic. |
- **STRATA_NO_IQ128** — src/kernels/cpu/native_expert.cpp:394 (+2 more reads)
  `static const bool avx1 = !cpu_avx2_ok() && cpu_avx1_ok() && std::getenv("STRATA_NO_IQ128") == nullptr;`
  // cpu_avx1_ok().  Measured on an E5-2470 v2 (iq_avx1_parity --bench): 1.2-3.1x ggml's dot from two tokens on, at one token ggml's auto-vectorized generic loop matches the 128-bit kernel - so the same #152 mt_min rule as the AVX-2 kernels, and STRATA_IQ_MT_MIN=1 takes the kernel for one token too (its rows are then independent of the drafting: iq_avx1_parity checks every width bit for bit).
- **STRATA_NO_IQ256** — src/kernels/cpu/native_expert.cpp:365 (+2 more reads)
  `static const bool iq3s_one = env == nullptr && std::getenv("STRATA_IQ3S_MT1") != nullptr && cpu_avx2_ok() && std::getenv("STRATA_NO_IQ256") == nullptr &&`
  // of the window.  So IQ3_S takes it for every group, and those rows no longer depend on the drafting.  A machine- wide rule, not a per-core one: every core rounds an expert the same.  Every probe here is in expert_layout.cpp and cpu_avx2_ok() comes first, so no AVX2 code runs before the check.  STRATA_IQ_MT_MIN set keeps its rule. Opt-in (STRATA_IQ3S_MT1=1): it changes a lone token's IQ3_S rounding 
- **STRATA_NO_IQ4NL** — src/kernels/cpu/native_expert.cpp:521
  `static const bool iq4nl_mt = std::getenv("STRATA_NO_IQ4NL") == nullptr;`
  // IQ4_NL down rows: the AVX-2 multi-token kernel decodes the nibbles and absolutises the weights once per block instead of once per token; ggml-cpu's dot is single-token.  STRATA_NO_IQ4NL falls back to it.
- **STRATA_NO_IQ512** — src/kernels/cpu/native_expert.cpp:378
  `static const bool avx512 = cpu_avx512_ok() && std::getenv("STRATA_NO_IQ512") == nullptr;`
  // at one (all are bound by the codebook lookups, ~5 GB/s per core), measured by native_expert_parity.  AVX-512 first, then the AVX-2 one (Zen 2/3, Intel 12th-14th gen).  STRATA_NO_IQ512 drops an AVX-512 CPU to the AVX-2 kernel, STRATA_NO_IQ256 drops the AVX-2 kernel; ggml-cpu's single-token vec_dot is reached only with both set (and on a CPU without AVX-512, STRATA_NO_IQ512 changes nothing).
- **STRATA_NO_IQ512X1** — src/kernels/cpu/native_expert.cpp:415
  `static const bool x512_one = avx512 && iq512_gather_on() && std::getenv("STRATA_NO_IQ512X1") == nullptr;`
  // 0.2.5 (AVX-512 CPUs where a gather is cheap: Intel Sapphire Rapids and later): ONE token of an IQ3_XXS / IQ3_S expert on the 512-bit exact rows, ggml-cpu's single-token AVX2 dot bit for bit with the grid words gathered: 1.3x ggml's dot on a Xeon 8468 (x512_bench), the same output.  Where the multi-token rule (#152) already sends one token to the multi-token kernel (STRATA_IQ_MT_MIN=1) that stays; 
- **STRATA_NO_MMVQ_ROWS2** — src/kernels/cuda/native_mmvq.cu:1369 (+1 more reads)
  `const char* v = std::getenv("STRATA_NO_MMVQ_ROWS2");`
- **STRATA_NO_NORM_ROPE** — src/kernels/cuda/native_rope.cu:177
  `const char* off = std::getenv("STRATA_NO_NORM_ROPE");`
- **STRATA_NO_NVFP4_256** — src/kernels/cpu/native_expert.cpp:496 (+1 more reads) docs: NVFP4.md
  `static const bool nvfp4_256 = cpu_avx2_ok() && std::getenv("STRATA_NO_NVFP4_256") == nullptr;`
  // Without AVX-512: the same rows in 256-bit lanes, bit-equal to ggml-cpu's AVX2 dot below; 2.0-2.4x it at 4-8 tokens, 2x under DRAM load with 6 threads (nvfp4_avx512_parity). STRATA_NO_NVFP4_256 falls back to ggml-cpu.
  doc (NVFP4.md): 7 265). `STRATA_NO_NVFP4_256=1` falls back to ggml-cpu. An NVFP4 pack is a native pack (its folder holds
- **STRATA_NO_NVFP4_512** — src/kernels/cpu/native_expert.cpp:489 (+1 more reads) docs: NVFP4.md
  `static const bool nvfp4_512 = cpu_avx512_ok() && std::getenv("STRATA_NO_NVFP4_512") == nullptr;`
  // NVFP4 in 512-bit lanes: ggml's arithmetic, blocks decoded once per window; 1.8x at one token, 3.7x at seven (nvfp4_avx512_parity). STRATA_NO_NVFP4_512 falls back to ggml-cpu.
  doc (NVFP4.md): `nvfp4_avx512_parity`). `STRATA_NO_NVFP4_512=1` falls back to ggml-cpu.
- **STRATA_NO_Q8K_AVX1** — src/kernels/cpu/native_expert.cpp:238
  `static const bool on = !cpu_avx2_ok() && cpu_avx1_ok() && std::getenv("STRATA_NO_Q8K_AVX1") == nullptr;`
- **STRATA_NO_Q8K_AVX2** — src/kernels/cpu/native_expert.cpp:232
  `static const bool on = cpu_avx2_ok() && std::getenv("STRATA_NO_Q8K_AVX2") == nullptr;`
- **STRATA_NO_SUB16_GU** — src/kernels/cuda/iq_kernels.cu:3401
  `bool g_no_sub16_gu = env_on("STRATA_NO_SUB16_GU");`
- **STRATA_NO_TQ_KERNELS** — src/kernels/cpu/tq_cpu.cpp:179 docs: GYRO.md
  `if (const char* e = std::getenv("STRATA_NO_TQ_KERNELS"); e != nullptr && std::atoi(e) != 0) return false;`
  doc (GYRO.md): (`build/tq_cpu_parity --bench` measures them on your CPU). `STRATA_NO_TQ_KERNELS=1` goes back to ggml-cpu.
- **STRATA_NUMA_POOL** — src/kernels/cpu/pool.cpp:755 (+5 more reads) docs: DETAILS.md, release-notes-0.2.2.md
  `const NumaPoolPick pool_pick = pick_numa_pool(std::getenv("STRATA_NUMA_POOL"), env, numa_nodes);`
  doc (DETAILS.md): - `STRATA_NUMA_POOL=0` turns it off (also `off`, `false`, `no`) and wins over `STRATA_NUMA_SPLIT=1`. `STRATA_NUMA_SPLIT=1` asks for
- **STRATA_NUMA_SPLIT** — src/kernels/cpu/pool.cpp:753 (+14 more reads) docs: DETAILS.md, release-notes-0.2.2.md
  `const char* env = std::getenv("STRATA_NUMA_SPLIT");`
  // STRATA_NUMA_SPLIT, read here for the worker count (the split itself is decided below, once the count is known). 0.2.2: with 2 or more NUMA nodes and neither variable set the split is tried by itself, and STRATA_NUMA_POOL=0 turns that off (numa_pool.hpp).  One node: pick_numa_pool says Unchanged and nothing below differs from the pool before the split.
  doc (DETAILS.md): - `STRATA_NUMA_POOL=0` turns it off (also `off`, `false`, `no`) and wins over `STRATA_NUMA_SPLIT=1`. `STRATA_NUMA_SPLIT=1` asks for
- **STRATA_NVFP4_PREFETCH** — src/kernels/cpu/nvfp4_avx2.cpp:51 (+2 more reads)
  `const char* e = std::getenv("STRATA_NVFP4_PREFETCH");`
- **STRATA_OLD_GROUPED** — src/kernels/cuda/s2_expert_grouped.cu:533
  `const char* e = std::getenv("STRATA_OLD_GROUPED");`
- **STRATA_OLD_IQ_MMVQ** — src/kernels/cuda/iq_kernels.cu:3400 docs: EXPERTDEC.md
  `bool g_old_kernels = env_on("STRATA_OLD_IQ_MMVQ");`
  // STRATA_OLD_IQ_MMVQ=1 keeps the per-column kernels (bitwise equal to the new ones; kept for A/B timing)
  doc (EXPERTDEC.md): Formats outside the list keep the default kernel for that role; `STRATA_OLD_IQ_MMVQ=1` turns EXPDEC off as it turns
- **STRATA_OLD_SAMPLER** — src/kernels/cuda/sampler.cu:1138
  `static const SampledPath path = env_flag("STRATA_OLD_SAMPLER")         ? SampledPath::Old`
- **STRATA_PARITY_DUMP** — src/kernels/route_resident_parity.cu:218
  `if (std::getenv("STRATA_PARITY_DUMP") && dumped < 2) {`
- **STRATA_PATTN_SM60** — src/kernels/cuda/qsa_pattn.cu:37 docs: OLDER_GPUS.md, release-notes-0.2.7.md
  `const char* v = std::getenv("STRATA_PATTN_SM60");`
  doc (release-notes-0.2.7.md): - Opt-in switches from pull requests, each checked for exactness or by unit tests and builds, not for speed on your card: a bigger Pascal (GP100) set (`STRATA_DOWN_WS=1`, `STRATA_MTP_Q8_SM60=1`, `STRATA_MMQ_WS=1`, `STRATA_PATTN_SM60=1`, `STRATA_EXPERT_NIBBLE=1`), `STRATA_PF_FUSED_Q2N=1` for the Q2_0
- **STRATA_PA_FAST** PROD=1 — src/kernels/cuda/qsa_prompt_attn.cu:2249 docs: AMD_HIP.md, RADEON_780M.md, RX7900XTX.md, STRIX_HALO.md
  `static const bool fast = [] { const char* e = std::getenv("STRATA_PA_FAST"); return e != nullptr && e[0] == '1'; }();`
  doc (AMD_HIP.md): | `STRATA_PA_FAST=1` | Prompt attention with single FP16 q and p |
- **STRATA_PA_V1_PREFETCH** — src/kernels/cuda/qsa_prompt_attn.cu:2419 docs: DETAILS.md
  `static const int pf_env = [] { const char* e = std::getenv("STRATA_PA_V1_PREFETCH"); return e ? (std::atoi(e) != 0 ? 1 : 0) : -1; }();`
  // #1821 (xrip): v1 with the next chunk's rows prefetched in registers and K/V sharing one buffer (two blocks an SM), the same bits.  STRATA_PA_V1_PREFETCH=0 / 1 forces it off / on; unset: a Turing card with STRATA_SM75_PERF=1.
  doc (DETAILS.md): `STRATA_TC_SM75`, `STRATA_PA_V1_PREFETCH`, `STRATA_SCORES_THREAD` (a thread-per-head block scorer; `=1` works on any CUDA card).
- **STRATA_PA_V2T** — src/kernels/cuda/qsa_prompt_attn.cu:2414 docs: DETAILS.md
  `static const bool v2t = [] { const char* e = std::getenv("STRATA_PA_V2T"); return e != nullptr && e[0] == '1'; }();`
  // Turing: v2 with register staging instead of cp.async, opt-in (STRATA_PA_V2T=1) until measured
  doc (DETAILS.md): Options that change answers stay separate: `STRATA_SELECT_SIMT=1|2`, `STRATA_PA_V2T=1`, `STRATA_PF_FUSED=1 STRATA_PF_FUSED_SM75=1`
- **STRATA_PF_SWITCH_MIN_T** — src/prefill/prefill.cpp:467 (+3 more reads) docs: AMD_HIP.md, STRIX_HALO.md
  `static const int64_t v = [] { const char* e = std::getenv("STRATA_PF_SWITCH_MIN_T"); return e ? (int64_t) std::atoll(e) : (int64_t) 0; }();`
  // N or more tokens (shorter prompts keep the default numerics, and their outputs; the switches pay on long ones)
  doc (AMD_HIP.md): STRATA_PF_SWITCH_MIN_T=4096` 925 -> 1,092 tok/s; `--resident-experts` 1,092 -> 2,503 tok/s; `--prefill auto:32768` +23% at 74K.
- **STRATA_PF_WMMA2** — src/kernels/cuda/iq_kernels.cu:6998 docs: NVIDIA_V100.md
  `static const bool v = [] { const char* e = std::getenv("STRATA_PF_WMMA2"); return e && e[0] == '1'; }();`
  doc (NVIDIA_V100.md): | `STRATA_PF_WMMA2=1` | A second prompt-expert kernel for IQ2_S gate/up and IQ4_NL down (#2356). |
- **STRATA_PLE_CHECK** — src/kernels/ngram.cpp:254 docs: release-notes-0.2.7.md
  `static const bool on = [] { const char* v = std::getenv("STRATA_PLE_CHECK"); return v != nullptr && std::atoi(v) != 0; }();`
  doc (release-notes-0.2.7.md): - Engine, found by reading the code and the pull requests: a failed read in the per-layer table reader no longer leaves the next request waiting for ever (#3602; the reporter's NaN did not reproduce here, `STRATA_PLE_CHECK=1` re-reads a suspect row and prints it); a conversation restore that would h
- **STRATA_PLE_GGUF** — src/kernels/ple_parity.cpp:257 (+1 more reads)
  `std::string gguf = std::getenv("STRATA_PLE_GGUF") ? std::getenv("STRATA_PLE_GGUF")`
  // --gguf, else $STRATA_PLE_GGUF, else the development layout (run from the engine root)
- **STRATA_POOL_SPIN_US** — src/kernels/cpu/pool.cpp:748 (+2 more reads)
  `if (const char* e = std::getenv("STRATA_POOL_SPIN_US"))   // a test knob; see kSpinBeforeSleep`
  // a test knob; see kSpinBeforeSleep
- **STRATA_POOL_UMWAIT** — src/kernels/cpu/pool.cpp:45
  `const char* e = std::getenv("STRATA_POOL_UMWAIT");`
- **STRATA_POOL_UMWAIT_C02** — src/kernels/cpu/pool.cpp:63
  `static const unsigned s = [] { const char* e = std::getenv("STRATA_POOL_UMWAIT_C02"); return e && *e == '1' ? 0u : 1u; }();`
- **STRATA_POOL_UMWAIT_ESC** — src/kernels/cpu/pool.cpp:69
  `static const uint64_t c = [] { const char* e = std::getenv("STRATA_POOL_UMWAIT_ESC"); return e ? (uint64_t) (std::max)(0LL, std::atoll(e)) : (uint64_t) 0; }();`
- **STRATA_PROMPT_ATTN_IMMA** — src/kernels/cuda/qsa_prompt_attn.cu:2429 docs: DETAILS.md
  `const char* v = std::getenv("STRATA_PROMPT_ATTN_IMMA");`
  doc (DETAILS.md): | `STRATA_PROMPT_ATTN_IMMA` | Int8-KV prompt attention on INT8 tensor cores | Rounding level. On by default since 0.2.7 on NVIDIA Ampere and newer (+1.1% to +1.8% prompt at 8K/16K on an RTX PRO 5000 and 2x RTX A4000); `=0` brings the 0.2.6 kernel back. |
- **STRATA_PROMPT_ATTN_Q4** — src/kernels/cuda/qsa_prompt_attn.cu:2389
  `const char* v = std::getenv("STRATA_PROMPT_ATTN_Q4");`
- **STRATA_PROMPT_ATTN_Q4_TC** — src/kernels/cuda/qsa_prompt_attn.cu:2395
  `const char* v = std::getenv("STRATA_PROMPT_ATTN_Q4_TC");`
- **STRATA_PROMPT_ATTN_V1** — src/kernels/cuda/qsa_prompt_attn.cu:2411
  `static const bool v1 = std::getenv("STRATA_PROMPT_ATTN_V1") != nullptr;`
  // STRATA_PROMPT_ATTN_V1=1 (debug): the first version, same accuracy, another summation order - the control for how far the model amplifies an FP32-level change.  Turing always takes it: v2's cp.async does not exist before sm_80.
- **STRATA_Q2_BITPLANE** — src/kernels/cpu/q2_avx1.cpp:179 (+1 more reads) docs: DETAILS.md
  `const char* e = std::getenv("STRATA_Q2_BITPLANE");`
  doc (DETAILS.md): | `STRATA_Q2_BITPLANE=1` | AVX2 CPUs without AVX-512 | A bit-plane row kernel for Q2_0. Changes the last bits. | |
- **STRATA_Q2_WARP** — src/kernels/cuda/native_mmvq.cu:3131 docs: DETAILS.md
  `static const int env = [] { const char* v = std::getenv("STRATA_Q2_WARP"); return v ? (v[0] == '0' ? 0 : 1) : -1; }();`
  doc (DETAILS.md): `STRATA_TOPK_SPLIT`, `STRATA_TOPK_SAMPLE`, `STRATA_ATTN_V3`, `STRATA_Q2_WARP`, `STRATA_FUSE_WAIT=2`, `STRATA_QIL`,
- **STRATA_Q6P_GRID** — src/kernels/cuda/native_mmvq.cu:2619
  `const char* v = std::getenv("STRATA_Q6P_GRID");`
- **STRATA_Q6P_SELFTEST** — src/kernels/cuda/native_mmvq.cu:2912
  `if (const char* v = std::getenv("STRATA_Q6P_SELFTEST"); v && (v[0] == '1' || v[0] == '2')) {`
  // STRATA_Q6P_SELFTEST=1: bitwise check against the GGUF-layout kernels (1..4 columns) and paired timings
- **STRATA_Q6_PACKED** — src/kernels/cuda/native_mmvq.cu:2874 docs: RADEON_780M.md, STRIX_HALO.md
  `const char* v = std::getenv("STRATA_Q6_PACKED");`
  doc (STRIX_HALO.md): | `STRATA_Q8_PACKED`, `STRATA_Q6_PACKED`, `STRATA_MMVF_ROWS`, `STRATA_ATTN_LANECELL` | Decode layouts and kernels: packed Q8_0 / Q6_K weights, 4-row BF16 GEMV, one-cell-per-thread attention scores. |
- **STRATA_Q8_GATHER_WIDE** — src/kernels/cuda/kv_q8.cu:160 docs: NVIDIA_V100.md
  `const char* e = std::getenv("STRATA_Q8_GATHER_WIDE");`
  doc (NVIDIA_V100.md): | `STRATA_Q8_GATHER_WIDE=0` | Turns off the 8-wide int8 KV gather (#1095) that the experimental build uses below compute capability 7.5. |
- **STRATA_Q8_PACKED** — src/qwen35/q36_engine.cu:3787 (+3 more reads) docs: OLDER_GPUS.md, RADEON_780M.md, STRIX_HALO.md
  `setenv("STRATA_Q8_PACKED", "1", 0);   // the packed Q8_0 decode copy unless STRATA_Q8_PACKED is set otherwise`
  // the packed Q8_0 decode copy unless STRATA_Q8_PACKED is set otherwise
  doc (STRIX_HALO.md): | `STRATA_Q8_PACKED`, `STRATA_Q6_PACKED`, `STRATA_MMVF_ROWS`, `STRATA_ATTN_LANECELL` | Decode layouts and kernels: packed Q8_0 / Q6_K weights, 4-row BF16 GEMV, one-cell-per-thread attention scores. |
- **STRATA_Q8_SM60** — src/kernels/cuda/native_mmvq.cu:2447 docs: OLDER_GPUS.md
  `const char* v = std::getenv("STRATA_Q8_SM60");`
  doc (OLDER_GPUS.md): | Tesla P100 | 6.0 | the CUDA 12 engine | `__dp4a` emulated (bit-exact); BF16 projections through fp32; seven scheduling switches on by default ([below](#tesla-p100-sm_60)); opt-in `STRATA_Q8_SM60=1` ([below](#pascal-gp100-a-q8_0-decode-kernel-opt-in)) |
- **STRATA_Q8_SM60_BPS** — src/kernels/cuda/q8_sm60.cuh:89
  `const char* e = std::getenv("STRATA_Q8_SM60_BPS");`
- **STRATA_QFUSE_HC_LOCAL** — src/kernels/cuda/fused_gr.cu:1280
  `static const bool on = [] { const char* e = std::getenv("STRATA_QFUSE_HC_LOCAL"); return e == nullptr || std::atoi(e) != 0; }();`
- **STRATA_QSA_CLUSTER** — src/kernels/decode_cluster_parity.cpp:378 (+1 more reads) docs: DETAILS.md
  `set_env("STRATA_QSA_CLUSTER", "0");     // the dispatchers: the one-CTA kernels (the cluster ones called directly)`
  // the dispatchers: the one-CTA kernels (the cluster ones called directly)
  doc (DETAILS.md): | 0.1.36 (#136) | RTX 5070, Q2_0, fused int8 kernels (RTX 30 and newer) | Prompt 4K 1,294 -> 1,570, 32K 2,170 -> 2,653, 128K 2,123 -> 2,468 tok/s (+16-22%), teacher-forced KL 0.009 at 32K vs 0.012 before. Decode on thread-block clusters (RTX 50, sm_90+): Q2_0 output 4K 89 -> 93.5, 128K 64.5 -> 76.4 
- **STRATA_QSA_EARLY_EXIT** — src/kernels/cuda/qsa_select.cu:1553 (+2 more reads)
  `static const bool on = [] { const char* v = std::getenv("STRATA_QSA_EARLY_EXIT"); return v == nullptr || std::atoi(v) != 0; }();`
- **STRATA_QSA_ROWS** — src/kernels/cuda/qsa_select.cu:2098 (+1 more reads) docs: DETAILS.md, QSAROWS.md
  `static const bool rows_env = [] { const char* v = std::getenv("STRATA_QSA_ROWS"); return v != nullptr && v[0] == '1' && v[1] == '\0'; }();`
  // QSAROWS: STRATA_QSA_ROWS=1 (exactly) takes block_scores_rows_kernel for calls of up to 4 queries - the same bits
  doc (DETAILS.md): | `STRATA_QSA_ROWS=1` ([QSAROWS.md](QSAROWS.md)) | Block scores of a verify window with queries in registers | Exact; on by default on sm_86 |
- **STRATA_QSA_WARP** — src/kernels/cuda/qsa_prompt_attn.cu:2365 (+1 more reads)
  `const char* w = std::getenv("STRATA_QSA_WARP");`
  // STRATA_QSA_WARP=1|attn (an A/B arm): the pre-sm_80 kernels on any card that has the Turing MMA (sm_75 and newer), as RTX 20 runs them.  A card below sm_75 has no m16n8k8: its builds hold a __trap() in those kernels, so forcing them there killed the engine ("prefill copy_i32: unspecified launch failure" on a Tesla P100); such a card ignores the switch and keeps the kernel it runs without it.
- **STRATA_ROPE_TABLE** — src/kernels/cuda/native_rope.cu:154
  `const char* e = std::getenv("STRATA_ROPE_TABLE");`
- **STRATA_ROUTER_BLOCK** — src/kernels/cuda/router_top10.cu:462
  `if (n_expert <= 64 * RW_PER && !std::getenv("STRATA_ROUTER_BLOCK")) {`
- **STRATA_S2_SWIGLU_Q8** — src/kernels/cuda/s2_expert_grouped.cu:1193
  `const char* e = std::getenv("STRATA_S2_SWIGLU_Q8");`
- **STRATA_SAMPLER_ONE_BLOCK** — src/kernels/cuda/sampler.cu:1139
  `: env_flag("STRATA_SAMPLER_ONE_BLOCK") ? SampledPath::OneBlock`
- **STRATA_SCORES_DX** — src/kernels/cuda/qsa_select.cu:2971 (+1 more reads) docs: OLDER_GPUS.md
  `const char* v = std::getenv("STRATA_SCORES_DX");`
  doc (OLDER_GPUS.md): the threshold. `STRATA_TOPK_MULTI=0` and `STRATA_SCORES_DX=0` turn one half off. The author measured, on four GP100 dies with
- **STRATA_SCORES_HALVE** — src/kernels/cuda/qsa_select.cu:2074 docs: DETAILS.md
  `static const int env = [] { const char* v = std::getenv("STRATA_SCORES_HALVE"); return v ? (std::atoi(v) != 0 ? 1 : 0) : -1; }();`
  doc (DETAILS.md): that wins in both directions: `STRATA_SM75_IL`, `STRATA_SM75_EXP`, `STRATA_GR_UP75` / `STRATA_GR_DOWN_TG`, `STRATA_SCORES_HALVE`,
- **STRATA_SCORES_MULTI** — src/kernels/cuda/qsa_select.cu:1548 (+2 more reads)
  `static const bool on = [] { const char* v = std::getenv("STRATA_SCORES_MULTI"); return v == nullptr || std::atoi(v) != 0; }();`
- **STRATA_SCORES_THREAD** — src/kernels/cuda/qsa_select.cu:2059 (+5 more reads) docs: AMD_HIP.md, DETAILS.md
  `static const int env = [] { const char* v = std::getenv("STRATA_SCORES_THREAD"); return v ? (std::atoi(v) != 0 ? 1 : 0) : -1; }();`
  doc (DETAILS.md): `STRATA_TC_SM75`, `STRATA_PA_V1_PREFETCH`, `STRATA_SCORES_THREAD` (a thread-per-head block scorer; `=1` works on any CUDA card).
- **STRATA_SCORES_THREAD_TRACE** — src/kernels/cuda/qsa_select.cu:2136 docs: AMD_HIP.md
  `if (!logged && (thread_env == -1 || std::getenv("STRATA_SCORES_THREAD_TRACE"))) {`
  doc (AMD_HIP.md): `STRATA_SCORES_THREAD_TRACE=1` prints an engagement line.
- **STRATA_SELECT_SIMT** — src/kernels/cuda/qsa_select.cu:2217 (+1 more reads) docs: AMD_HIP.md, DETAILS.md, OLDER_GPUS.md
  `const char* v = std::getenv("STRATA_SELECT_SIMT");`
  doc (DETAILS.md): Options that change answers stay separate: `STRATA_SELECT_SIMT=1|2`, `STRATA_PA_V2T=1`, `STRATA_PF_FUSED=1 STRATA_PF_FUSED_SM75=1`
- **STRATA_SELECT_WMMA** — src/kernels/cuda/qsa_select.cu:2211 docs: AMD_HIP.md, RADEON_780M.md, STRIX_HALO.md
  `const char* v = std::getenv("STRATA_SELECT_WMMA");`
  doc (AMD_HIP.md): | `STRATA_SELECT_WMMA=1` | gfx12 | Off | Matrix-core block scorer for the QSA top-k; selects slightly differently |
- **STRATA_SIMT2_TILE** — src/kernels/cuda/qsa_select.cu:2267
  `static const int tile = [] { const char* v = std::getenv("STRATA_SIMT2_TILE"); return v ? std::atoi(v) : 1; }();`
  // STRATA_SIMT2_TILE=2: 64 x 64 tiles (measured slower: 400K 3.00 vs 2.82 ms)
- **STRATA_SM60_TABLE** — src/kernels/cuda/iq_kernels.cu:6167 (+1 more reads) docs: OLDER_GPUS.md
  `const char* sm60 = std::getenv("STRATA_SM60_TABLE");`
  // Pascal GP100 (sm_60): mode 8 too, on by default (Tesla P100: bitwise equal on the model's layers, the down projection 116 -> 94 us and IQ3_S gate/up 360 -> 229 us in a 28-group VRAM call); STRATA_SM60_TABLE=0 keeps the CUDA layout
  doc (OLDER_GPUS.md): in the CUDA layout (`STRATA_SM60_TABLE=0`). Both need a GP100.
- **STRATA_SM61_TABLE** — src/kernels/cuda/iq_kernels.cu:6172 (+1 more reads) docs: OLDER_GPUS.md
  `const char* sm61 = std::getenv("STRATA_SM61_TABLE");`
  // Pascal with dp4a (sm_61): mode 8 as well, on by default (Tesla P40, native_expert_bench on the IQ3_S pack's layers, an 18-group call at 2 tokens: IQ3_S 390 -> 255 us, IQ3_XXS 345 -> 252 us, IQ2_S 290 -> 238 us, IQ4_XS 328 -> 261 us, bitwise equal); STRATA_SM61_TABLE=0 keeps the CUDA layout
  doc (OLDER_GPUS.md): | `STRATA_SM61_TABLE=0` | sm_61 | on | Back to the CUDA expert layout and `native_mmvq`. |
- **STRATA_SM70_TABLE** — src/kernels/cuda/native_mmvq.cu:3840 (+2 more reads) docs: COMMUNITY_BENCHMARKS.md, NVIDIA_V100.md
  `bool sm70_opt_in() { const char* v = std::getenv("STRATA_SM70_TABLE"); return v != nullptr && std::atoi(v) != 0; }`
  // sm_80 and newer (measured on sm_86 and sm_120), Volta (sm_70) and Pascal (sm_60, sm_61), each with its own table above; Turing keeps native_mmvq's kernels unless STRATA_SM75_PERF=1 (kIlRows_75) Volta (PR 1401): opt-in with STRATA_SM70_TABLE=1 until the author confirms on a V100 with the final code
  doc (COMMUNITY_BENCHMARKS.md): (`STRATA_SM70_TABLE=1`) that [NVIDIA_V100.md](NVIDIA_V100.md) asks a V100 owner to check: decode
- **STRATA_SPEC_GUMBEL** — src/kernels/cuda/sampler.cu:1133 docs: DETAILS.md
  `static const bool on = env_flag("STRATA_SPEC_GUMBEL");`
  doc (DETAILS.md): `STRATA_SPEC_GUMBEL=1` raise the accepted-draft rate on some machines; `STRATA_SPEC_PROB=1` is speculative rejection
- **STRATA_TEST_SYSFS_ROOT** — src/kernels/cpu/pool.cpp:597 (+3 more reads)
  `const char* e = std::getenv("STRATA_TEST_SYSFS_ROOT");`
- **STRATA_TOPK_ACTIVE_ANY** — src/kernels/cuda/qsa_select.cu:2912 (+2 more reads)
  `static const bool any_card = [] { const char* v = std::getenv("STRATA_TOPK_ACTIVE_ANY"); return v && v[0] == '1'; }();`
  // STRATA_TOPK_ACTIVE_ANY=1 (tests): the Turing dispatch on any CUDA card, so qsa_topk_active_parity checks it on whatever card runs the tests (the kernels are the same on every architecture)
- **STRATA_TOPK_CAPACITY_GUARD** — src/kernels/cuda/qsa_select.cu:2909
  `static const bool capacity_guard = std::getenv("STRATA_TOPK_CAPACITY_GUARD") != nullptr;`
  // Turing: --max-context 262144 makes the stride 65538, even while a 131K prompt's active blocks fit in TK_T * TK_PER registers. Use the prefill bound on sm_75, keeping max_blocks as the score-row stride. Other CUDA devices keep 0.1.32's capacity rule: #337 was measured on RDNA4, and RTX 5070 64K prompts were 1-3% slower. Decode/captured graphs omit the bound and never query the device here.
- **STRATA_TOPK_MULTI** — src/kernels/cuda/qsa_select.cu:3036 (+1 more reads) docs: OLDER_GPUS.md
  `const char* v = std::getenv("STRATA_TOPK_MULTI");`
  doc (OLDER_GPUS.md): the threshold. `STRATA_TOPK_MULTI=0` and `STRATA_SCORES_DX=0` turn one half off. The author measured, on four GP100 dies with
- **STRATA_TOPK_MULTI_N** — src/kernels/cuda/qsa_select.cu:3058 (+2 more reads)
  `static const int n_env = [] { const char* v = std::getenv("STRATA_TOPK_MULTI_N"); return v ? std::atoi(v) : 0; }();`
  // CTAs per query from the capacity (the grid is fixed in a captured graph; each CTA's share follows n_bid): one per 2,048 blocks, at most MT_NMAX. STRATA_TOPK_MULTI_N: a fixed count (tests)
- **STRATA_TOPK_OLD** — src/kernels/cuda/qsa_select.cu:2878 (+1 more reads) docs: AMD_HIP.md
  `static const bool old = std::getenv("STRATA_TOPK_OLD") != nullptr;`
  // keys in registers when every query's blocks fit (contexts up to ~135K cells), else (CUDA) the same threads reading them from memory; the same ids. STRATA_TOPK_OLD=1: the original kernel
  doc (AMD_HIP.md): | `STRATA_TOPK_OLD=1`, `STRATA_TOPK_STREAM=0` | HIP | Off | Run the original top-k kernel, or the register kernel in the 90K-135K band |
- **STRATA_TOPK_REG_MIN_BLOCKS** — src/kernels/cuda/qsa_select.cu:2922 docs: STRIX_HALO.md
  `const char* v = std::getenv("STRATA_TOPK_REG_MIN_BLOCKS");`
  doc (STRIX_HALO.md): | `STRATA_TOPK_REG_MIN_BLOCKS=4096` | The prompt's QSA top-k uses the register kernel from 16K cells of context instead of 28K. The selected cells are identical (`qsa_topk_parity`). |
- **STRATA_TOPK_SAMPLE** — src/kernels/cuda/qsa_select.cu:2859 docs: DETAILS.md
  `static const int env = [] { const char* v = std::getenv("STRATA_TOPK_SAMPLE"); return v ? (std::atoi(v) != 0 ? 1 : 0) : -1; }();`
  doc (DETAILS.md): `STRATA_TOPK_SPLIT`, `STRATA_TOPK_SAMPLE`, `STRATA_ATTN_V3`, `STRATA_Q2_WARP`, `STRATA_FUSE_WAIT=2`, `STRATA_QIL`,
- **STRATA_TOPK_SPLIT** — src/kernels/cuda/qsa_select.cu:2627 docs: DETAILS.md
  `static const int env = [] { const char* v = std::getenv("STRATA_TOPK_SPLIT"); return v ? (std::atoi(v) != 0 ? 1 : 0) : -1; }();`
  doc (DETAILS.md): `STRATA_TOPK_SPLIT`, `STRATA_TOPK_SAMPLE`, `STRATA_ATTN_V3`, `STRATA_Q2_WARP`, `STRATA_FUSE_WAIT=2`, `STRATA_QIL`,
- **STRATA_TOPK_STREAM** — src/kernels/cuda/qsa_select.cu:2946 docs: AMD_HIP.md, DETAILS.md, TROUBLESHOOTING.md
  `const char* v = std::getenv("STRATA_TOPK_STREAM");`
  doc (DETAILS.md): | `STRATA_KEEP_EMPTY_TURNS=1`, `STRATA_TOPK_STREAM=0` | | See [TROUBLESHOOTING.md](TROUBLESHOOTING.md). | |
- **STRATA_TQ_ISA** — src/kernels/cpu/tq_cpu.cpp:49 docs: GYRO.md
  `const char* e = std::getenv("STRATA_TQ_ISA");`
  doc (GYRO.md): `STRATA_TQ_ISA=avx2` or `scalar` caps the instruction set.
- **STRATA_TQ_ROWCH** — src/kernels/cuda/iq_kernels.cu:3472
  `const char* v = std::getenv("STRATA_TQ_ROWCH");`
- **STRATA_TQ_STAGE** — src/kernels/cuda/iq_kernels.cu:3433 (+1 more reads) docs: GYRO.md, release-notes-0.2.2.md
  `static const int env = [] { const char* v = std::getenv("STRATA_TQ_STAGE"); return v != nullptr && v[0] != '\0' ? (v[0] != '0' ? 1 : 0) : -1; }();`
  doc (release-notes-0.2.2.md): - **Gyro decodes about 30% faster on a Tesla P100 (compute capability 6.0).** On a P100, Gyro-S ran at about 70% of the speed of the Q2_0 file of similar size: 30 / 36 / 33 tok/s against 41 / 51 / 48 (story / code / facts, median of 5 interleaved pairs, default flags). On compute capability 6.0 the 
- **STRATA_TQ_SUB8** — src/kernels/cuda/iq_kernels.cu:3463 docs: release-notes-0.2.2.md
  `v = std::getenv("STRATA_TQ_SUB8");`
  doc (release-notes-0.2.2.md): - **Gyro decodes faster on NVIDIA cards.** The gate/up and down kernels for agentionai's trellis experts now keep the codebook in shared memory and take four rows per warp (8 lanes per row), on every CUDA card above Pascal. On an RTX 3060 (12 GB) Gyro-S went from 53.6 to 62.8 tokens per second (+17%

## src/platform
- **STRATA_IO_THREADS** — src/platform/direct_file.cpp:64 docs: AMD_HIP.md, AMD_HIP_PERFORMANCE.md
  `const char* v = std::getenv("STRATA_IO_THREADS");`
  doc (AMD_HIP.md): `STRATA_HIP_ADAPT_KERNEL_COPY`, `STRATA_PREFILL_CPU_SHARE`, `STRATA_PIPED_CONCURRENT`, `STRATA_PREFILL_STREAM_MIN`, `STRATA_IO_THREADS`, a rocBLAS
- **STRATA_READ_AHEAD** — src/platform/memory.cpp:207 docs: DETAILS.md, TROUBLESHOOTING.md
  `const char* v = std::getenv("STRATA_READ_AHEAD");`
  doc (DETAILS.md): steps), which matters on a slow drive: `STRATA_READ_AHEAD=0` turns it off, `STRATA_FILL_AHEAD=N` sets how many fill pairs

## src/prefill
- **STRATA_AUX_STAGER** — src/prefill/prefill.cpp:626 docs: DETAILS.md
  `static const bool keep = [] { const char* v = std::getenv("STRATA_AUX_STAGER"); return v != nullptr && std::atoi(v) == 0; }();`
  doc (DETAILS.md): adaptive tier's job thread. `STRATA_AUX_STAGER=0` leaves the prefill copy threads where they started.
- **STRATA_BF16_TC** — src/prefill/gemm.cu:831 docs: DETAILS.md, NVIDIA_V100.md, OLDER_GPUS.md
  `const char* v = std::getenv("STRATA_BF16_TC");`
  doc (DETAILS.md): `STRATA_BF16_TC=1` with `STRATA_XN_F16`.
- **STRATA_COLD_TRACE** — src/prefill/prefill.cpp:2678 docs: AMD_HIP.md
  `ColdTrace() { const char* e = std::getenv("STRATA_COLD_TRACE"); on = e != nullptr && e[0] == '1'; }`
  doc (AMD_HIP.md): arena loads so the first request does not carry them (`STRATA_COLD_TRACE=1` times them).
- **STRATA_CVEC_FUSE** — src/prefill/prefill.cpp:503 docs: RADEON_780M.md, STRIX_HALO.md
  `static const bool v = [] { const char* e = std::getenv("STRATA_CVEC_FUSE"); return e && e[0] == '1'; }();`
  doc (STRIX_HALO.md): | `STRATA_CVEC_FUSE`, `STRATA_PF_PAD` | A steered layer's write, control vector and next norm in one pass; padded GEMM row strides. |
- **STRATA_CVEC_FUSE_CHECK** — src/prefill/prefill.cpp:5558
  `static int checks = [] { const char* e = std::getenv("STRATA_CVEC_FUSE_CHECK"); return e ? std::atoi(e) : 0; }();`
  // STRATA_CVEC_FUSE_CHECK=N: on the first N fused writes, also run the three-kernel path on a copy of R and report whether R, the row scales and the BF16 image are bit-identical
- **STRATA_DBG_CPU_GATE** — src/prefill/prefill.cpp:4425
  `if (static const bool dbg = std::getenv("STRATA_DBG_CPU_GATE") != nullptr; dbg)`
  // debug: STRATA_DBG_CPU_GATE=1 prints each reading and what the next layers do
- **STRATA_DBG_FEAT** — src/prefill/prefill.cpp:5969 (+1 more reads)
  `if (std::getenv("STRATA_DBG_FEAT") || std::getenv("STRATA_DBG_ROUTE_OVERRIDE") || std::getenv("STRATA_PREFILL_DUMP_R_ALL")) {`
  // run_impl's debug hooks on the routing and the rows have no layer-major form
- **STRATA_DBG_FEAT_LAYERS** — src/prefill/prefill.cpp:4112
  `const char* e = std::getenv("STRATA_DBG_FEAT_LAYERS");`
- **STRATA_DBG_FORCE_SLOW_LAYER** — src/prefill/prefill.cpp:4216
  `static const bool force_slow = [] { const char* e = std::getenv("STRATA_DBG_FORCE_SLOW_LAYER"); return e && e[0] == '1'; }();`
  // that never returns (the first ck() to see it is `prefill mmq: iota`, one prompt later).  fused_layout() and fused_ring() keep the shrink and this decision in step; this is the backstop for anything that drifts: a clear error, never a hang. STRATA_DBG_FORCE_SLOW_LAYER=1 (a test of the backstop): layer 0 counts as one the fused path does not take
- **STRATA_DBG_ROUTE_OVERRIDE** — src/prefill/prefill.cpp:5969 (+2 more reads)
  `if (std::getenv("STRATA_DBG_FEAT") || std::getenv("STRATA_DBG_ROUTE_OVERRIDE") || std::getenv("STRATA_PREFILL_DUMP_R_ALL")) {`
  // run_impl's debug hooks on the routing and the rows have no layer-major form
- **STRATA_DENSE_F32** — src/prefill/gemm.cu:879 docs: COMMUNITY_BENCHMARKS.md, OLDER_GPUS.md
  `const char* v = std::getenv("STRATA_DENSE_F32");`
  doc (COMMUNITY_BENCHMARKS.md): a 565-token prompt 205 -> 255 tok/s, decode 34-35 -> 37-38 tok/s, and with the opt-in `STRATA_DENSE_F32=1` a 7K prompt 360-432 -> 464-474 tok/s. Short and 7K prompts only; cuBLAS 12.4 only.
- **STRATA_DENSE_MMQ** — src/prefill/gemm.cu:1256 docs: AMD_HIP.md, DETAILS.md
  `const char* e = std::getenv("STRATA_DENSE_MMQ");`
  doc (DETAILS.md): | HIP `STRATA_DENSE_MMQ=1`, `STRATA_HIP_ADAPT_KERNEL_COPY=1` | HIP | See [AMD_HIP.md](AMD_HIP.md#model-and-serving-configuration). | |
- **STRATA_DEQUANT_SIDE** — src/prefill/gemm.cu:634 docs: DETAILS.md
  `static const bool on = [] { const char* v = std::getenv("STRATA_DEQUANT_SIDE"); return v && v[0] == '1'; }();`
  doc (DETAILS.md): | `STRATA_PLE_COMPACT=1`, `STRATA_PLE_COPY_STREAM=1`, `STRATA_EMBED_VRAM=1`, `STRATA_DEQUANT_SIDE=1` | The PLE rows go up raw and are dequantized on the card, on their own stream; the token-embedding table in VRAM; the dense dequant on a side stream (CUDA only). All bitwise. | prompts +2.2 % to +2.6
- **STRATA_DUMP_MOE_INPUT** — src/prefill/prefill.cpp:4564 docs: NVFP4.md
  `static const char* dump_moe = std::getenv("STRATA_DUMP_MOE_INPUT");`
  // Diagnostics: STRATA_DUMP_MOE_INPUT=path, STRATA_DUMP_MOE_LAYER=l - the first chunk's MoE input of layer l ({T, N, K} int64, T x N floats, T x K expert ids) for testing products on real rows
  doc (NVFP4.md): `STRATA_DUMP_MOE_INPUT` with `mmq_nvfp4_parity --real` tests one product on a real prompt's rows: layer 20, its 12
- **STRATA_DUMP_MOE_LAYER** — src/prefill/prefill.cpp:4566 (+1 more reads)
  `if (dump_moe && !dumped_moe && l == std::atoi(std::getenv("STRATA_DUMP_MOE_LAYER") ? std::getenv("STRATA_DUMP_MOE_LAYER") : "0")) {`
- **STRATA_EMB_REUSE_ACCOUNT** — src/prefill/prefill.cpp:337 docs: DETAILS.md
  `static const bool on = [] { const char* v = std::getenv("STRATA_EMB_REUSE_ACCOUNT"); return v != nullptr && v[0] == '1'; }();`
  doc (DETAILS.md): | `STRATA_EMB_REUSE_ACCOUNT=1` | CUDA | The planner counts the VRAM saved because the half-output buffer `bo` reuses the embedding buffer `emb`, so the auto chunk can grow. Changes prompt rounding. | Prompt about +3.9% on an RTX 3060, no KL measurement yet. |
- **STRATA_F16_RANGE** — src/prefill/prefill.cpp:1742 (+1 more reads) docs: AMD_HIP.md
  `static const bool f16_range = std::getenv("STRATA_F16_RANGE") != nullptr;   // what reaches FP16's range`
  // what reaches FP16's range
  doc (AMD_HIP.md): | `STRATA_HIP_PROMPT_F16=1` | Runs the 16-bit prompt GEMMs FP16 in and out (the engine prints a tip on gfx103x). `STRATA_F16_RANGE=1` prints, per prompt, the largest value that entered or left FP16 (FP16 ends at 65504); `STRATA_DBG_NAN=1` counts non-finite FP16 outputs. Checks: [2026-10-04-rdna2-fp1
- **STRATA_GDN_CHUNKED** PROD=1 — src/prefill/kernels.cu:1194 (+3 more reads) docs: AMD_HIP.md, DETAILS.md, RX7900XTX.md
  `static const bool any_sms = [] { const char* v = std::getenv("STRATA_GDN_CHUNKED"); return v != nullptr && std::atoi(v) >= 2; }();`
  // STRATA_GDN_CHUNKED=2 skips the SM-count test (measurement on a card under 128 SMs: the scan then runs in several waves and is expected to be slower than the default kernel; the architecture and shared-memory tests stay)
  doc (DETAILS.md): | `STRATA_GDN_CHUNKED=1` | CUDA, 128 or more SMs by itself (`=2` forces it); HIP gfx1100-gfx1102, gfx1150, gfx1151 | The DeltaNet recurrence of the prompt in chunks of 32 tokens (CUDA) or 16-token WMMA chunks (HIP). Changes rounding. | 1.8x on the recurrence on an RTX 5090; slower on smaller cards. 
- **STRATA_GDN_CHUNK_PROF** — src/prefill/gdn_chunk.cu:584
  `static const bool prof = std::getenv("STRATA_GDN_CHUNK_PROF") != nullptr;`
  // STRATA_GDN_CHUNK_PROF=1: per-stage milliseconds over the whole call (a dev tool, not a hot path)
- **STRATA_GDN_CONVL2** — src/prefill/kernels.cu:2652 docs: RADEON_780M.md, RX7900XTX.md, STRIX_HALO.md
  `static const bool fused = [] { const char* v = std::getenv("STRATA_GDN_CONVL2"); return v && std::atoi(v) != 0; }();`
  doc (RX7900XTX.md): | `STRATA_GDN_CONVL2=1` | +0.3% |
- **STRATA_GDN_CONV_SERIAL** — src/prefill/kernels.cu:2648
  `static const bool serial = std::getenv("STRATA_GDN_CONV_SERIAL") != nullptr;   // the old walk (A/B)`
  // the old walk (A/B)
- **STRATA_GDN_HEAD** — src/prefill/kernels.cu:2805 (+1 more reads) docs: RADEON_780M.md, STRIX_HALO.md
  `static const bool head = [] { const char* v = std::getenv("STRATA_GDN_HEAD"); return v != nullptr && std::atoi(v) != 0; }();`
  // Aurora (S23): four lanes per column + the grid-stride norm, the same bits (tests/hip/gdn_rec_head.cpp); STRATA_GDN_HEAD=1 (on by default on gfx1151; off with STRATA_GDN_HEAD=0 or STRATA_GDN_REC_HEADS) takes them (AMD builds only; the arch defaults set STRATA_GDN_HEAD=1 on gfx1151 and leave other cards on the earlier kernels)
  doc (STRIX_HALO.md): | `STRATA_GDN_HEAD`, `STRATA_GDN_PP=2`, `STRATA_GDN_CONVL2`, `STRATA_GDN_NOY` | The prompt's gated-delta-net recurrence: four lanes per column, two columns per lane, convolution and norms fused. |
- **STRATA_GDN_KEYHEAD** — src/prefill/kernels.cu:849 docs: INTEL.md
  `static const bool off = [] { const char* v = std::getenv("STRATA_GDN_KEYHEAD"); return v != nullptr && std::atoi(v) == 0; }();`
  doc (INTEL.md): | #413 | DeltaNet recurrence per key head | 8% slower prompt: off (`STRATA_GDN_KEYHEAD=1`) |
- **STRATA_GDN_NOY** — src/prefill/kernels.cu:2714 docs: RADEON_780M.md, STRIX_HALO.md
  `static const bool noy = [] { const char* v = std::getenv("STRATA_GDN_NOY"); return v && std::atoi(v) != 0; }();`
  doc (STRIX_HALO.md): | `STRATA_GDN_HEAD`, `STRATA_GDN_PP=2`, `STRATA_GDN_CONVL2`, `STRATA_GDN_NOY` | The prompt's gated-delta-net recurrence: four lanes per column, two columns per lane, convolution and norms fused. |
- **STRATA_GDN_PIPELINE** — src/prefill/kernels.cu:2771
  `static const bool pipe = [] { const char* v = std::getenv("STRATA_GDN_PIPELINE"); return v == nullptr || std::atoi(v) != 0; }();`
- **STRATA_GDN_REC_HEADS** — src/prefill/kernels.cu:2673 (+2 more reads) docs: AMD_HIP.md
  `static const bool serial = std::getenv("STRATA_GDN_REC_HEADS") != nullptr;   // the one-block-per-head kernel (A/B)`
  // the one-block-per-head kernel (A/B)
  doc (AMD_HIP.md): shorter chunks, an output row stride not divisible by eight, and `STRATA_GDN_REC_HEADS` use the existing recurrence. Speed
- **STRATA_GDN_TC** — src/prefill/kernels.cu:2779 docs: DETAILS.md
  `static const bool tc = [] { const char* v = std::getenv("STRATA_GDN_TC"); return v != nullptr && std::atoi(v) != 0; }();`
  // STRATA_GDN_TC=1 (opt-in): the chunked recurrence with the scan on the tensor cores (gdn_tc.cuh) for prompt chunks of kGdnTcMin+ tokens: within 1e-4 of the kernels below (gdn_rec_parity), 3.75x gdn_rec_kh_kernel on a CMP 170HX; a shorter chunk, a card it does not fit or a failed scratch allocation takes the kernels below
  doc (DETAILS.md): Also from PR #3779, measured by its author on the same CMP 170HX; none of the figures was measured here. `STRATA_PF_FUSED_NT=256` and `STRATA_PF_BATCH=N` keep every output bit. `STRATA_PF_FUSED_F16=1`, `STRATA_PF_FUSED_WS=1` and `STRATA_GDN_TC=1` change the output at rounding level: the author's tea
- **STRATA_GROUP_COPY** — src/prefill/prefill.cpp:1667
  `const char* gc = std::getenv("STRATA_GROUP_COPY");`
- **STRATA_GR_UNFUSED** — src/prefill/prefill.cpp:529
  `static const bool v = [] { const char* e = std::getenv("STRATA_GR_UNFUSED"); return e && e[0] == '1'; }();`
- **STRATA_HANDOFF_PIPE** — src/prefill/prefill.cpp:399 docs: BATCHING.md
  `const char* e = std::getenv("STRATA_HANDOFF_PIPE");`
  doc (BATCHING.md): | `STRATA_HANDOFF_PIPE=P` | a layer split hands a prompt chunk to the next card in P pieces (2..16), gated by events, on a persistent thread |
- **STRATA_HANDOFF_PIPE_WORKER** — src/prefill/prefill.cpp:416
  `static const bool v = [] { const char* e = std::getenv("STRATA_HANDOFF_PIPE_WORKER"); return !e || std::atoi(e) != 0; }();`
- **STRATA_HCD_EXACT** — src/prefill/prefill.cpp:498 docs: RADEON_780M.md, STRIX_HALO.md
  `static const bool v = [] { const char* e = std::getenv("STRATA_HCD_EXACT"); return e && e[0] == '1'; }();`
  doc (STRIX_HALO.md): | `STRATA_HCD_EXACT` | The hyper-connection down projection (N 320, K 10240) in a WMMA kernel that reproduces hipBLASLt solution 1176 / 1177's summation order (`hip_prefill_hcd_exact_parity` checks it bit for bit). It runs only where the table makes hipBLASLt pick one of those two, and says once if 
- **STRATA_HC_UPMIX_CHECK** — src/prefill/prefill.cpp:3749
  `static int checks = [] { const char* e = std::getenv("STRATA_HC_UPMIX_CHECK"); return e ? std::atoi(e) : 0; }();`
- **STRATA_HIPBLASLT_TABLE** — src/prefill/gemm.cu:276 docs: AMD_HIP.md, release-notes-0.2.1.md
  `const char* sw = std::getenv("STRATA_HIPBLASLT_TABLE");     // the launcher's switch: off / 0 / false = never the packaged table`
  // the launcher's switch: off / 0 / false = never the packaged table
  doc (AMD_HIP.md): | `STRATA_HIPBLASLT_TABLE=on` (or `"hipblaslt_table": true` in the run config) | Use the packaged table when it matches |
- **STRATA_HIPBLASLT_TUNING** — src/prefill/gemm.cu:273 docs: AMD_HIP.md, AMD_HIP_PERFORMANCE.md, RADEON_780M.md, STRIX_HALO.md
  `const char* path = std::getenv("STRATA_HIPBLASLT_TUNING");`
  doc (AMD_HIP.md): | `STRATA_HIPBLASLT_TUNING=<file>` | Use this table file; always kept |
- **STRATA_HIPBLASLT_VERBOSE** — src/prefill/gemm.cu:208 (+2 more reads) docs: AMD_HIP.md
  `if (std::getenv("STRATA_HIPBLASLT_VERBOSE")) {`
  doc (AMD_HIP.md): copy the tables that match the bundled hipBLASLt into the package's `tuning/` folder. `STRATA_HIPBLASLT_VERBOSE=1` reports
- **STRATA_HIP_PROMPT_F16** — src/prefill/gemm.cu:590 docs: AMD_HIP.md
  `const char* e = std::getenv("STRATA_HIP_PROMPT_F16");`
  // Opt-in (#835): only STRATA_HIP_PROMPT_F16=1 turns it on.  It changes the prompt path's numbers (an FP16 rounding of each 16-bit GEMM's output), so no card gets it unasked.  On gfx103x it is ~2x faster, so we say so once.
  doc (AMD_HIP.md): without `--kv-resident`, the same setup answered normally. Removing the other switches one at a time (`STRATA_HIP_PROMPT_F16`, `STRATA_HC_PERSIST`,
- **STRATA_IDX_FP16_CHECK** — src/prefill/prefill.cpp:3989
  `if (static const bool f16chk = std::getenv("STRATA_IDX_FP16_CHECK") != nullptr; f16chk) {`
  // STRATA_IDX_FP16_CHECK: would FP16 pooled indexer keys select the same cells? (the KV-streaming design's last question). Every query is selected again from the pooled keys and `dead` rounded to fp16 (exactly what an fp16 store reads back); the agreement with the fp32 selection is printed cumulatively after each chunk's last QSA layer. Debug: syncs per layer.
- **STRATA_INDEXER_PER_TOKEN** — src/prefill/prefill.cpp:3923 (+1 more reads)
  `static const bool per_token = std::getenv("STRATA_INDEXER_PER_TOKEN") != nullptr;`
- **STRATA_KVA_GDN_NORM** — src/prefill/prefill.cpp:3802 docs: KVA.md
  `const char* v = std::getenv("STRATA_KVA_GDN_NORM");`
  doc (KVA.md): | `STRATA_KVA_GDN_NORM` | off | keep the full GDN recurrence (the A/B control for the state-only one) |
- **STRATA_KV_HOST_DMA** — src/prefill/prefill.cpp:3873 (+1 more reads) docs: TROUBLESHOOTING.md
  `static const bool kv_host_dma = [] { const char* e = std::getenv("STRATA_KV_HOST_DMA"); return e && e[0] == '1'; }();`
  doc (TROUBLESHOOTING.md): 3. **`"STRATA_KV_HOST_DMA": "1"`** in the same `"env"` block: no GPU kernel writes the RAM copy of the K/V during a
- **STRATA_KV_PREFETCH** — src/prefill/prefill.cpp:2980 docs: KV_PREFETCH.md
  `const char* e = std::getenv("STRATA_KV_PREFETCH");`
  doc (KV_PREFETCH.md): Set `STRATA_KV_PREFETCH=1` before starting the engine. It is off by default.
- **STRATA_KV_STAGE_OWN** — src/prefill/prefill.cpp:1171
  `bool stage_own() { static const bool v = std::getenv("STRATA_KV_STAGE_OWN") != nullptr; return v; }`
  // the staging pool of a streamed session: every page of one layer (same sequence in init and bytes_needed) STRATA_KV_STAGE_OWN (A/B only): the staging pool gets its own allocation instead of borrowed expert slots, so a streamed run lends the prompt path exactly the slots a resident one does (a lent expert runs on the CPU, which rounds differently: without this an A/B compares two expert placements a
- **STRATA_LM_PREFETCH** — src/prefill/prefill.cpp:6238
  `static const bool pf_on = [] { const char* e = std::getenv("STRATA_LM_PREFETCH"); return e == nullptr || e[0] != '0'; }();`
  // every streamed expert of layer l, in id order, to the stager - started with the layer's attention halves, so the NVMe / page-cache reads overlap them (at a super-chunk's size nearly every expert is routed)
- **STRATA_MMQ_DIRECT** — src/prefill/moe_mmq.cu:621 docs: BATCHING.md, DETAILS.md, OLDER_GPUS.md
  `const char* v = std::getenv("STRATA_MMQ_DIRECT");`
  doc (DETAILS.md): | `STRATA_MMQ_DIRECT=1` | CUDA, native packs; needs a build with `-DSTRATA_MMQ_TAB=ON` (off by default because it costs 36-38 MiB of VRAM per GPU) | The prompt's MMQ reads resident experts in their cache slots instead of copying them. Same bits. | Faster "read in" time with every expert resident. |
- **STRATA_MMQ_DIRECT_LOG** — src/prefill/prefill.cpp:7134
  `static const bool log = [] { const char* v = std::getenv("STRATA_MMQ_DIRECT_LOG"); return v && std::atoi(v) != 0; }();`
- **STRATA_MMQ_GROUP_SORT** — src/prefill/mmq_resident_sort.hpp:28 docs: BATCHING.md
  `static const bool on = mmq_resident_sort_flag(std::getenv("STRATA_MMQ_GROUP_SORT"));`
  doc (BATCHING.md): | `STRATA_MMQ_DIRECT=1`, `STRATA_MMQ_GROUP_SORT=1` | CUDA, needs the build option `-DSTRATA_MMQ_TAB=ON`: the prompt MMQ reads resident experts in their cache slots; full MMQ groups sorted by row count (docs/DETAILS.md) |
- **STRATA_MMQ_KQ** — src/qwen35/q36_engine.cu:3788 (+4 more reads) docs: QUANTS.md, UNSLOTH_Q4.md, UNSLOTH_Q6.md
  `setenv("STRATA_MMQ_KQ", "1", 0);      // the K-quant MMQ prompt kernels (every expert of this family is a K-quant)`
  // the K-quant MMQ prompt kernels (every expert of this family is a K-quant)
  doc (UNSLOTH_Q4.md): keeps `STRATA_MMQ_KQ` opt-in.
- **STRATA_MMQ_RESIDENT_SORT_NE** — src/prefill/mmq_resident_sort.hpp:18
  `static const bool on = mmq_resident_sort_flag(std::getenv("STRATA_MMQ_RESIDENT_SORT_NE"));`
- **STRATA_MMQ_WS** — src/prefill/moe_ws.cu:58 docs: OLDER_GPUS.md, release-notes-0.2.7.md
  `const char* e = std::getenv("STRATA_MMQ_WS");   // opt-in`
  // opt-in
  doc (release-notes-0.2.7.md): - Opt-in switches from pull requests, each checked for exactness or by unit tests and builds, not for speed on your card: a bigger Pascal (GP100) set (`STRATA_DOWN_WS=1`, `STRATA_MTP_Q8_SM60=1`, `STRATA_MMQ_WS=1`, `STRATA_PATTN_SM60=1`, `STRATA_EXPERT_NIBBLE=1`), `STRATA_PF_FUSED_Q2N=1` for the Q2_0
- **STRATA_MTP_BATCH** — src/prefill/prefill.cpp:1926
  `static const bool off = [] { const char* v = std::getenv("STRATA_MTP_BATCH"); return v != nullptr && v[0] == '0'; }();`
- **STRATA_MTP_BATCH_F16** — src/prefill/prefill.cpp:1967
  `static const bool f16_only = [] { const char* v = std::getenv("STRATA_MTP_BATCH_F16"); return v && v[0] == '1'; }();`
  // per row: emb/e2 (N), en16 (N half), hn/h2/Rm/gated (HCN), hn16/xn16 (HCN half), lo (LR) + lo16, grs, mixed (N) + mixed_h, K and V (KV each), the token id E-9: the drafter's Q8_0 matrices through Q8_1 x Q8_0 MMQ - its own pass's integer dot products (mmvq), so its K/V stay close to what the drafter computes itself; STRATA_MTP_BATCH_F16=1: FP16 GEMMs (the A/B)
- **STRATA_MTP_BATCH_RING** — src/prefill/prefill.cpp:1931
  `static const bool ring_ok = [] { const char* v = std::getenv("STRATA_MTP_BATCH_RING"); return v == nullptr || v[0] != '0'; }();`
  // A ring (KV streaming: the drafter's window, page p in slot p % n_slots over a host copy) takes the same appends with its own page table and host copy, as a streamed main layer does; the cells written are those the window can still reach (r0 below), which the ring holds, so no two of them share a slot.  STRATA_MTP_BATCH_RING=0: the drafter's own pass for a ring (the A/B).
- **STRATA_PF_BATCH** — src/prefill/prefill.cpp:4259 docs: DETAILS.md
  `const char* v = std::getenv("STRATA_PF_BATCH");`
  doc (DETAILS.md): Also from PR #3779, measured by its author on the same CMP 170HX; none of the figures was measured here. `STRATA_PF_FUSED_NT=256` and `STRATA_PF_BATCH=N` keep every output bit. `STRATA_PF_FUSED_F16=1`, `STRATA_PF_FUSED_WS=1` and `STRATA_GDN_TC=1` change the output at rounding level: the author's tea
- **STRATA_PF_BK64** — src/prefill/wmma_gemm.cu:696
  `static const bool bk64 = [] { const char* v = std::getenv("STRATA_PF_BK64"); return !v || v[0] != '0'; }();`
  // STRATA_PF_BK64=0: the BK 32 kernel for the wide shapes too (the A/B; the same bits)
- **STRATA_PF_F16** PROD=1 — src/prefill/moe_f16_common.cuh:56 docs: RX7900XTX.md, STRIX_HALO.md
  `const char* v = std::getenv("STRATA_PF_F16");`
  doc (RX7900XTX.md): | `STRATA_PF_F16=1 STRATA_PA_FAST=1 STRATA_HC_UPMIX=1` | FP16 prompt path pieces, faster prompt attention, HC up+mix fused | **prefill +7-10%** (each alone +1-3%) | rounding (KL in noise) |
- **STRATA_PF_F16_BN** — src/prefill/moe_f16_common.cuh:68
  `const char* v = std::getenv("STRATA_PF_F16_BN");`
- **STRATA_PF_FUSED** PROD=1 — src/prefill/moe_fused.cu:681 (+2 more reads) docs: AMD_HIP.md, DETAILS.md, MULTI_GPU.md, OLDER_GPUS.md, RADEON_780M.md, RX7900XTX.md, STRIX_HALO.md, release-notes-0.2.0.md
  `const char* v = std::getenv("STRATA_PF_FUSED");`
  doc (DETAILS.md): | Fused int8 prompt experts | gfx12 (R9700): IQ3_S and IQ3_XXS packs. 12.0 NVIDIA cards with 80 or more SMs: IQ2_S, IQ3_XXS, IQ3_S, IQ4_XS gate/up | `STRATA_PF_FUSED=0` | Replaces the MMQ prompt kernels. `STRATA_PF_FUSED=1` opts in every covered format on other cards (on HIP gfx11 and gfx1200/gfx120
- **STRATA_PF_FUSED_F16** — src/prefill/moe_fused_iq.cu:1694 docs: DETAILS.md
  `static const bool on = [] { const char* v = std::getenv("STRATA_PF_FUSED_F16"); return v != nullptr && v[0] == '1'; }();`
  doc (DETAILS.md): Also from PR #3779, measured by its author on the same CMP 170HX; none of the figures was measured here. `STRATA_PF_FUSED_NT=256` and `STRATA_PF_BATCH=N` keep every output bit. `STRATA_PF_FUSED_F16=1`, `STRATA_PF_FUSED_WS=1` and `STRATA_GDN_TC=1` change the output at rounding level: the author's tea
- **STRATA_PF_FUSED_KQ** — src/prefill/moe_fused_iq.cu:1835 docs: QUANTS.md, STRIX_HALO.md
  `const char* v = std::getenv("STRATA_PF_FUSED_KQ");`
  doc (QUANTS.md): | Q4_K (gate/up) | yes | FP16 path; MMQ with `STRATA_MMQ_KQ=1` | ggml AVX2 dot; multi-token AVX2 (`STRATA_KQ256=1`) | yes (CUDA layout; `STRATA_EXPERT_V2K=1` bitwise) | FP16 path; MMQ with `STRATA_MMQ_KQ=1`; gfx11 fused (`STRATA_PF_FUSED_KQ=1`) | kernels built, not run with these files | FP16 path |
- **STRATA_PF_FUSED_NATIVE** — src/prefill/moe_fused_iq.cu:1924 docs: AMD_HIP.md, DETAILS.md
  `const char* v = std::getenv("STRATA_PF_FUSED_NATIVE");`
  doc (DETAILS.md): `STRATA_PF_FUSED=1` keeps its bits, and `STRATA_PF_FUSED=0` or `STRATA_PF_FUSED_NATIVE=0` still turn it off. Unset, the engine
- **STRATA_PF_FUSED_NT** — src/prefill/moe_fused_iq.cu:1698 docs: DETAILS.md
  `static const bool on = [] { const char* v = std::getenv("STRATA_PF_FUSED_NT"); return v != nullptr && std::atoi(v) == 256; }();`
  doc (DETAILS.md): Also from PR #3779, measured by its author on the same CMP 170HX; none of the figures was measured here. `STRATA_PF_FUSED_NT=256` and `STRATA_PF_BATCH=N` keep every output bit. `STRATA_PF_FUSED_F16=1`, `STRATA_PF_FUSED_WS=1` and `STRATA_GDN_TC=1` change the output at rounding level: the author's tea
- **STRATA_PF_FUSED_Q2N** — src/prefill/moe_fused_iq.cu:1807 docs: DETAILS.md, release-notes-0.2.7.md
  `static const bool q2n = [] { const char* v = std::getenv("STRATA_PF_FUSED_Q2N"); return v != nullptr && v[0] == '1'; }();`
  // STRATA_PF_FUSED_Q2N=1: the native Q2_0 pack's Q2_0 gate/up on these kernels here too (what #2145 took with STRATA_PF_FUSED=1 on every CUDA card until b6443f3a kept it to Turing).  Its own variable, so STRATA_PF_FUSED=1 keeps its bits: unset, the kernel is not set up and the Q2_0 layers keep MMQ.  A failed setup leaves occ as it was.
  doc (DETAILS.md): (Q2_0 pack, 7.5 card only), `STRATA_PF_FUSED_Q2N=1` (the native Q2_0 pack's prompt experts on sm_80+, below) and
- **STRATA_PF_FUSED_SM75** — src/prefill/moe_fused.cu:651 (+1 more reads) docs: DETAILS.md
  `static const bool sm75 = [] { const char* v = std::getenv("STRATA_PF_FUSED_SM75"); return v != nullptr && v[0] == '1'; }();`
  // Turing (sm_75): the same kernels with plain copies and m8n8k16 MMAs, opt-in (STRATA_PF_FUSED_SM75=1)
  doc (DETAILS.md): Options that change answers stay separate: `STRATA_SELECT_SIMT=1|2`, `STRATA_PA_V2T=1`, `STRATA_PF_FUSED=1 STRATA_PF_FUSED_SM75=1`
- **STRATA_PF_FUSED_TILE** — src/prefill/moe_fused_iq.cu:1911
  `const char* v = std::getenv("STRATA_PF_FUSED_TILE");`
- **STRATA_PF_FUSED_WS** — src/prefill/moe_fused_iq.cu:1702 docs: DETAILS.md
  `static const bool on = [] { const char* v = std::getenv("STRATA_PF_FUSED_WS"); return v != nullptr && v[0] == '1'; }();`
  doc (DETAILS.md): Also from PR #3779, measured by its author on the same CMP 170HX; none of the figures was measured here. `STRATA_PF_FUSED_NT=256` and `STRATA_PF_BATCH=N` keep every output bit. `STRATA_PF_FUSED_F16=1`, `STRATA_PF_FUSED_WS=1` and `STRATA_GDN_TC=1` change the output at rounding level: the author's tea
- **STRATA_PF_GEMM** PROD=1 — src/prefill/gemm.cu:1170 (+2 more reads) docs: AMD_HIP.md, RADEON_780M.md, RX7900XTX.md, STRIX_HALO.md, release-notes-0.2.2.md
  `static const bool pf_on = [] { const char* v = std::getenv("STRATA_PF_GEMM"); return v && v[0] == '1'; }();`
  doc (AMD_HIP.md): | `STRATA_PF_GEMM`, `STRATA_PF_PAD` | gfx11 only | Off | RDNA4 runs neither; the engine does not pad where no kernel reads the stride |
- **STRATA_PF_HCDOWN** — src/prefill/prefill.cpp:490 docs: RX7900XTX.md
  `static const bool v = [] { const char* e = std::getenv("STRATA_PF_HCDOWN"); return e && e[0] == '1'; }();`
  doc (RX7900XTX.md): | `STRATA_PF_HCDOWN=1` | +1.3% prefill, but first-token KL at 16K doubled (one prompt 0.22): not used |
- **STRATA_PF_OCC** — src/prefill/moe_fused.cu:610 (+1 more reads)
  `const char* v = std::getenv("STRATA_PF_OCC");`
- **STRATA_PF_OCC_W** — src/prefill/moe_fused_iq.cu:1739
  `const char* v = std::getenv("STRATA_PF_OCC_W");`
- **STRATA_PF_PAD** PROD=1 — src/prefill/gemm.cu:1351 (+1 more reads) docs: AMD_HIP.md, RADEON_780M.md, RX7900XTX.md, STRIX_HALO.md, release-notes-0.2.2.md
  `static const bool pad_on = [] { const char* v = std::getenv("STRATA_PF_PAD"); return v && v[0] == '1'; }();`
  // S23 (opt-in STRATA_PF_PAD=1, with STRATA_PF_GEMM=1 on chunks of STRATA_PF_SWITCH_MIN_T+ tokens): the weight dequantized into the scratch with row stride K + 64 halves, so no 4 KB-multiple stride camps on the memory channels (gemm_probe8: K 6144 19 -> 29 TFLOPS from W alone, 35 with X padded too).  Bitwise the same products.
  doc (AMD_HIP.md): | `STRATA_PF_GEMM`, `STRATA_PF_PAD` | gfx11 only | Off | RDNA4 runs neither; the engine does not pad where no kernel reads the stride |
- **STRATA_PF_PEER_COMPACT** — src/prefill/prefill.cpp:2295
  `const char* v = std::getenv("STRATA_PF_PEER_COMPACT");`
- **STRATA_PF_PEER_F16** — src/prefill/prefill.cpp:2340
  `const char* v = std::getenv("STRATA_PF_PEER_F16");`
- **STRATA_PF_PEER_GATHER** — src/prefill/prefill.cpp:2343
  `const char* gv = std::getenv("STRATA_PF_PEER_GATHER");`
- **STRATA_PF_PEER_HOST** — src/prefill/prefill.cpp:2242
  `const bool host_route_ok = [] { const char* v = std::getenv("STRATA_PF_PEER_HOST"); return v == nullptr || std::atoi(v) != 0; }();`
  // Without P2P the activations and the result rows take the mapped host route of the layer split's helper (STRATA_PF_PEER_HOST=0: refuse as before, the prompt path then stays on the primary)
- **STRATA_PF_PEER_OUT_PIPE** — src/prefill/prefill.cpp:2279
  `const char* v = std::getenv("STRATA_PF_PEER_OUT_PIPE");   // =0: one copy after the last group (the A/B)`
  // =0: one copy after the last group (the A/B)
- **STRATA_PF_PEER_RING** — src/prefill/prefill.cpp:2313
  `if (const char* pr = std::getenv("STRATA_PF_PEER_RING"); pr != nullptr) pp->RP = std::atoi(pr);`
- **STRATA_PF_PEER_STREAM** — src/prefill/prefill.cpp:2309
  `const char* fs = std::getenv("STRATA_PF_PEER_STREAM");`
- **STRATA_PF_PEER_SUMS** — src/prefill/prefill.cpp:2336
  `const char* v = std::getenv("STRATA_PF_PEER_SUMS");`
- **STRATA_PF_PEER_XSTREAM** — src/prefill/prefill.cpp:2264
  `const char* xv = std::getenv("STRATA_PF_PEER_XSTREAM");`
- **STRATA_PF_STEP_SYNC** — src/prefill/prefill.cpp:3602 docs: TROUBLESHOOTING.md
  `static const bool step_sync = [] { const char* e = std::getenv("STRATA_PF_STEP_SYNC"); return e && e[0] == '1'; }();`
  // #579 #613 (opt-in diagnosis, STRATA_PF_STEP_SYNC=1): the compute and copy streams are waited for after each step named below, a step that took over 250 ms is logged, and a stall's report names the step it is in. Slower (a sync per step); the bytes are the same.
  doc (TROUBLESHOOTING.md): 2. **Find the step that hangs:** add `"STRATA_PF_STEP_SYNC": "1"` to the `"env"` block of the model's run config (`strata-<model>.json`
- **STRATA_PF_WMMA** — src/prefill/prefill.cpp:1335 docs: NVIDIA_V100.md
  `const char* e = std::getenv("STRATA_PF_WMMA");`
  doc (NVIDIA_V100.md): | MoE experts | MMQ by default. Opt-in `STRATA_PF_WMMA=1` (only when every visible card is compute capability 7 or newer): `gemm_iq_f16_grouped`, a group of experts per launch on the FP16 tensor cores. FP16 activations instead of MMQ's q8_1, so answers differ. |
- **STRATA_PLE_COMPACT** — src/prefill/prefill.cpp:157 docs: DETAILS.md
  `static const bool on = [] { const char* v = std::getenv("STRATA_PLE_COMPACT"); return v != nullptr && v[0] == '1'; }();`
  doc (DETAILS.md): | `STRATA_PLE_COMPACT=1`, `STRATA_PLE_COPY_STREAM=1`, `STRATA_EMBED_VRAM=1`, `STRATA_DEQUANT_SIDE=1` | The PLE rows go up raw and are dequantized on the card, on their own stream; the token-embedding table in VRAM; the dense dequant on a side stream (CUDA only). All bitwise. | prompts +2.2 % to +2.6
- **STRATA_PLE_COPY_STREAM** — src/prefill/prefill.cpp:163 docs: DETAILS.md
  `static const bool on = [] { const char* v = std::getenv("STRATA_PLE_COPY_STREAM"); return v != nullptr && v[0] == '1'; }();`
  doc (DETAILS.md): | `STRATA_PLE_COMPACT=1`, `STRATA_PLE_COPY_STREAM=1`, `STRATA_EMBED_VRAM=1`, `STRATA_DEQUANT_SIDE=1` | The PLE rows go up raw and are dequantized on the card, on their own stream; the token-embedding table in VRAM; the dense dequant on a side stream (CUDA only). All bitwise. | prompts +2.2 % to +2.6
- **STRATA_PREFILL_BF16X2** — src/prefill/prefill.cpp:383
  `const char* e = std::getenv("STRATA_PREFILL_BF16X2");`
- **STRATA_PREFILL_COPY_EVENT_EVERY** — src/prefill/prefill.cpp:3482
  `const char* v = std::getenv("STRATA_PREFILL_COPY_EVENT_EVERY");`
- **STRATA_PREFILL_COPY_WAIT_DEDUPE** — src/prefill/prefill.cpp:3486
  `const char* v = std::getenv("STRATA_PREFILL_COPY_WAIT_DEDUPE");`
- **STRATA_PREFILL_CPU_SHARE** — src/prefill/prefill.cpp:244 (+1 more reads) docs: AMD_HIP.md, DETAILS.md, OLDER_GPUS.md
  `const char* e = std::getenv("STRATA_PREFILL_CPU_SHARE");`
  doc (DETAILS.md): | `STRATA_PREFILL_CPU_SHARE` (`auto`, cap `STRATA_PREFILL_CPU_SHARE_MAX=1024`) | CUDA, one GPU, no `--batch`, prompt chunks under 1,024 tokens | `STRATA_PREFILL_CPU_SHARE=0` | The CPU pool computes the experts few of the chunk's tokens route to, while the GPU works on the rest. `auto` measures per l
- **STRATA_PREFILL_CPU_SHARE_MAX** — src/prefill/prefill.cpp:261 (+1 more reads) docs: DETAILS.md
  `const char* e = std::getenv("STRATA_PREFILL_CPU_SHARE_MAX");`
  doc (DETAILS.md): | `STRATA_PREFILL_CPU_SHARE` (`auto`, cap `STRATA_PREFILL_CPU_SHARE_MAX=1024`) | CUDA, one GPU, no `--batch`, prompt chunks under 1,024 tokens | `STRATA_PREFILL_CPU_SHARE=0` | The CPU pool computes the experts few of the chunk's tokens route to, while the GPU works on the rest. `auto` measures per l
- **STRATA_PREFILL_DUMP_R** — src/prefill/prefill.cpp:5671 (+1 more reads)
  `if (const char* dump = std::getenv("STRATA_PREFILL_DUMP_R")) {   // debug: the final residuals, every 64th`
  // debug: the final residuals, every 64th
- **STRATA_PREFILL_DUMP_R_ALL** — src/prefill/prefill.cpp:5969 (+1 more reads)
  `if (std::getenv("STRATA_DBG_FEAT") || std::getenv("STRATA_DBG_ROUTE_OVERRIDE") || std::getenv("STRATA_PREFILL_DUMP_R_ALL")) {`
  // run_impl's debug hooks on the routing and the rows have no layer-major form
- **STRATA_PREFILL_GROUP_GATHER** — src/prefill/prefill.cpp:5071 docs: DETAILS.md
  `const char* v = std::getenv("STRATA_PREFILL_GROUP_GATHER");`
  doc (DETAILS.md): | `STRATA_QUANT_GATHER=1`, `STRATA_PREFILL_GROUP_GATHER=0` | Per-row gather for the MoE input quantization; the short-prompt grouped gather off | No gain measured; keep the defaults |
- **STRATA_PREFILL_HELP** — src/prefill/prefill.cpp:2096 (+1 more reads) docs: BATCHING.md, GYRO.md, MULTI_GPU.md
  `static const bool v = [] { const char* e = std::getenv("STRATA_PREFILL_HELP"); return e != nullptr && std::atoi(e) != 0; }();`
  doc (BATCHING.md): - Off, said once, where the read's thread would allocate or free (`STRATA_PREFILL_HELP=1`, `STRATA_SPLIT_MTP_BATCH=1`),
- **STRATA_PREFILL_HELP_FRAC** — src/prefill/prefill.cpp:2108 docs: MULTI_GPU.md
  `const char* e = std::getenv("STRATA_PREFILL_HELP_FRAC");`
  doc (MULTI_GPU.md): | `STRATA_PREFILL_HELP=1` | The idle card computes a share of the streamed experts of a one-chunk prompt. `STRATA_PREFILL_HELP_FRAC=f` fixes the share. | Helps prompts up to about 3.3K tokens on slow links only; not bit-identical; native packs on the MMQ prompt path only. |
- **STRATA_PREFILL_ISSUER** — src/prefill/prefill.cpp:3459
  `const char* v = std::getenv("STRATA_PREFILL_ISSUER");`
- **STRATA_PREFILL_LAYER_MAJOR** — src/prefill/prefill.cpp:5880 docs: release-notes-0.2.7.md
  `static const char* const e = std::getenv("STRATA_PREFILL_LAYER_MAJOR");`
  doc (release-notes-0.2.7.md): - **Two NVIDIA cards read long prompts much sooner on a layer split.** On a layer split over two CUDA cards the prompt is now read layer by layer in large pieces (layer-major prefill, on by default), so each layer's experts are read once per piece instead of once per 8,192 tokens. On two RTX A4000 (
- **STRATA_PREFILL_LM_EVEN** — src/prefill/prefill.cpp:5886
  `static const bool v = [] { const char* e = std::getenv("STRATA_PREFILL_LM_EVEN"); return !(e && e[0] == '0'); }();`
- **STRATA_PREFILL_LM_MARGIN_MIB** — src/prefill/prefill.cpp:5907
  `const char* e = std::getenv("STRATA_PREFILL_LM_MARGIN_MIB");`
- **STRATA_PREFILL_LM_R** — src/prefill/prefill.cpp:5896
  `const char* e = std::getenv("STRATA_PREFILL_LM_R");`
- **STRATA_PREFILL_LM_TOKENS** — src/prefill/prefill.cpp:5891
  `static const int64_t v = [] { const char* e = std::getenv("STRATA_PREFILL_LM_TOKENS"); return e ? (int64_t) std::atoll(e) : (int64_t) 0; }();`
- **STRATA_PREFILL_MMQ** PROD=1 — src/prefill/prefill.cpp:1352 docs: AMD_HIP.md, AMD_HIP_PERFORMANCE.md, GYRO.md, INTEL.md, INTEL_INT8_EXPERTS.md, OLDER_GPUS.md, ORCA_Q4_K_S.md, RADEON_780M
  `const char* env = std::getenv("STRATA_PREFILL_MMQ");`
  doc (AMD_HIP.md): - **Build and tests:** `-DCMAKE_HIP_ARCHITECTURES=gfx1201 -DSTRATA_BUILD_TESTS=ON -DSTRATA_PREFILL_MMQ=ON`. On an R9700,
- **STRATA_PREFILL_NVFP4** — src/prefill/mmq_expert_bench.cpp:112 (+2 more reads) docs: NVFP4.md
  `const char* mode = std::getenv("STRATA_PREFILL_NVFP4");`
  doc (NVFP4.md): `STRATA_PREFILL_NVFP4` picks how the batched prompt path multiplies the experts:
- **STRATA_PREFILL_PIPE** — src/prefill/prefill.cpp:2453 docs: MULTI_GPU.md
  `const char* v = std::getenv("STRATA_PREFILL_PIPE");`
  doc (MULTI_GPU.md): | `--prefill-pipe R` (or `STRATA_PREFILL_PIPE=R`) | Reads each prompt in the chunk count with the least pipeline time for b/a = R tokens. `1` evens out today's chunk count. | Opt-in. `./setup.sh --calibrate` measures it per PC and writes it to the config. |
- **STRATA_PREFILL_RING** PROD=256 — src/prefill/prefill.cpp:351 docs: AMD_HIP_PERFORMANCE.md, DETAILS.md, RX7900XTX.md
  `const char* v = std::getenv("STRATA_PREFILL_RING");`
  doc (DETAILS.md): `--prefill N` and `STRATA_PREFILL_RING` always win.
- **STRATA_PREFILL_STREAM_AHEAD** — src/prefill/prefill.cpp:184
  `const char* v = std::getenv("STRATA_PREFILL_STREAM_AHEAD");`
- **STRATA_PREFILL_STREAM_MIN** — src/prefill/prefill.cpp:223 docs: AMD_HIP.md, STRIX_HALO.md
  `static const int64_t env = [] { const char* e = std::getenv("STRATA_PREFILL_STREAM_MIN"); return e ? (int64_t) std::atoll(e) : (int64_t) -1; }();`
  doc (AMD_HIP.md): `STRATA_HIP_ADAPT_KERNEL_COPY`, `STRATA_PREFILL_CPU_SHARE`, `STRATA_PIPED_CONCURRENT`, `STRATA_PREFILL_STREAM_MIN`, `STRATA_IO_THREADS`, a rocBLAS
- **STRATA_PREFILL_TIMING** — src/prefill/prefill.cpp:2743 (+1 more reads) docs: OLDER_GPUS.md
  `bool on = std::getenv("STRATA_PREFILL_TIMING") != nullptr;`
  doc (OLDER_GPUS.md): Profiling switches: `STRATA_PREFILL_TIMING=1`, `STRATA_DECODE_TIMING=1`, `STRATA_VERIFY_PROFILE=1`.
- **STRATA_PREFILL_WARM** — src/prefill/prefill.cpp:1475 (+2 more reads) docs: AMD_HIP.md, release-notes-0.2.1.md
  `static const bool off = [] { const char* e = std::getenv("STRATA_PREFILL_WARM"); return e != nullptr && e[0] == '0'; }();`
  doc (AMD_HIP.md): | `STRATA_PREFILL_WARM=0` | all | On | Turn off the warm-up BF16 and FP16 products run while the expert arena loads |
- **STRATA_PROMPT_ATTN_OLD** — src/prefill/prefill.cpp:4065 (+1 more reads) docs: NVIDIA_V100.md, OLDER_GPUS.md
  `static const bool old_attn = std::getenv("STRATA_PROMPT_ATTN_OLD") != nullptr;`
  // perf-review D-1: the whole chunk on tensor cores, one block per (query, KV head), FP32-level accuracy but not bitwise (qsa_prompt_attn.hpp). Q4_0 KV, or STRATA_PROMPT_ATTN_OLD=1: the decode kernel, 32 queries at a time (K8V4 runs the tensor kernel's mode 3: INT8 K, V dequantized from its q4_0 blocks to fp16 at gather)
  doc (OLDER_GPUS.md): | `STRATA_PROMPT_ATTN_OLD=1` | Volta | off | The decode kernel for prompts instead of the Volta kernel. |
- **STRATA_QSA_DUMP** — src/prefill/prefill.cpp:4037
  `if (static const char* dump = std::getenv("STRATA_QSA_DUMP"); dump != nullptr) {`
  // STRATA_QSA_DUMP_LAST (4096) positions - records of int32 {qsa layer, pos0, T, cap} + T*cap cells, for tools/qsa_locality.py (how local the sparse attention's reads are: the KV-streaming question). STRATA_QSA_DUMP_LAYER=i: QSA layer i only; STRATA_QSA_DUMP_STEPS=1: each record then ends with the T * kStepCount steps too (tests/cuda/pa_bench.cpp replays such a record)
- **STRATA_QSA_DUMP_LAST** — src/prefill/prefill.cpp:4038 (+1 more reads)
  `static const long long last = std::getenv("STRATA_QSA_DUMP_LAST")`
- **STRATA_QSA_DUMP_LAYER** — src/prefill/prefill.cpp:4040 (+1 more reads)
  `static const int only = std::getenv("STRATA_QSA_DUMP_LAYER") ? std::atoi(std::getenv("STRATA_QSA_DUMP_LAYER")) : -1;`
- **STRATA_QSA_DUMP_STEPS** — src/prefill/prefill.cpp:4049
  `if (std::getenv("STRATA_QSA_DUMP_STEPS")) {`
- **STRATA_QUANT_GATHER** — src/prefill/moe_mmq.cu:455 docs: DETAILS.md
  `static const bool gather = [] { const char* e = std::getenv("STRATA_QUANT_GATHER"); return e != nullptr && std::atoi(e) != 0; }();`
  doc (DETAILS.md): | `STRATA_QUANT_GATHER=1`, `STRATA_PREFILL_GROUP_GATHER=0` | Per-row gather for the MoE input quantization; the short-prompt grouped gather off | No gain measured; keep the defaults |
- **STRATA_RDNA2_SGEMM** — src/prefill/gemm.cu:966 docs: AMD_HIP.md
  `const char* v = std::getenv("STRATA_RDNA2_SGEMM");`
  doc (AMD_HIP.md): | `STRATA_RDNA2_SGEMM=1` | Widens both GEMM inputs to FP32 (exact) and runs SGEMM, no 65504 limit. `=all` forces it on any AMD card. With `STRATA_HIP_PROMPT_F16=1` the FP16 route runs first and SGEMM takes the products it leaves. Slower than the FP16 route. |
- **STRATA_RING_BYTES** — src/prefill/prefill.cpp:341 docs: DETAILS.md
  `static const bool on = [] { const char* v = std::getenv("STRATA_RING_BYTES"); return v == nullptr || v[0] != '0'; }();`
  doc (DETAILS.md): full. `STRATA_RING_BYTES=0` restores the earlier ring, loan and chunk choice.
- **STRATA_ROCBLAS_TUNING** — src/prefill/gemm.cu:470 docs: AMD_HIP.md
  `const char* path = std::getenv("STRATA_ROCBLAS_TUNING");`
  doc (AMD_HIP.md): | `STRATA_ROCBLAS_TUNING=<file or dir>` | A rocBLAS solution table for the FP16 route; setup points the engine at the directory when a table for the architecture exists. The log says `rocBLAS tuning enabled (... rows ...)` or why not. See [rocBLAS table](#rocblas-table-gfx103x). |
- **STRATA_ROCBLAS_VERBOSE** — src/prefill/gemm.cu:461 (+2 more reads) docs: AMD_HIP.md
  `if (std::getenv("STRATA_ROCBLAS_VERBOSE")) {`
  doc (AMD_HIP.md): `STRATA_ROCBLAS_VERBOSE=1` prints the solution picked per shape and a `tuned_launches=... fallbacks=...` summary at exit. A
- **STRATA_SELECT_OLD** — src/prefill/prefill.cpp:3956 (+1 more reads)
  `static const bool old_sel = std::getenv("STRATA_SELECT_OLD") != nullptr;`
  // the scores on tensor cores (3xTF32: FP32-level, not bitwise), below sm_80 the FP32 tiled kernel with STRATA_SELECT_SIMT=1; STRATA_SELECT_OLD=1: the warp kernel
- **STRATA_SEL_OVERLAP** — src/prefill/prefill.cpp:3967
  `if (static const bool ovl = std::getenv("STRATA_SEL_OVERLAP") != nullptr; ovl && qsa_index == 0) {`
  // STRATA_SEL_OVERLAP (debug, D-1's question): how much do neighbouring queries' selections share? Per tile of 16 queries: the union of their selected cells against the sum of their widths.
- **STRATA_STAGER_BATCH** — src/prefill/prefill.cpp:1643
  `const char* bv = std::getenv("STRATA_STAGER_BATCH");`
- **STRATA_STAGER_RING** — src/prefill/prefill.cpp:605 (+1 more reads) docs: UNSLOTH_Q4.md
  `if (const char* v = std::getenv("STRATA_STAGER_RING")) kRing = std::clamp(std::atoi(v), 2, 256);`
  doc (UNSLOTH_Q4.md): | `STRATA_FETCH_THREADS=N` | Threads that read the experts from the GGUF while it answers (default 8). The prompt path has its own: `STRATA_STAGER_THREADS` (default 32 here) and `STRATA_STAGER_RING` (128). |
- **STRATA_STAGER_SLEEP** — src/prefill/prefill.cpp:204 docs: DETAILS.md
  `const char* e = std::getenv("STRATA_STAGER_SLEEP");`
  doc (DETAILS.md): `STRATA_STAGER_SLEEP=1` makes the prompt-staging threads sleep while they wait on Windows too (they sleep on Linux and spin on
- **STRATA_STAGER_SSD** — src/prefill/prefill.cpp:1631 docs: DETAILS.md
  `const char* ev = std::getenv("STRATA_STAGER_SSD");   // 1 / 0: force the profile (A/B, support)`
  // 1 / 0: force the profile (A/B, support)
  doc (DETAILS.md): | `STRATA_STAGER_SSD` | Linux | `STRATA_STAGER_SSD=1`/`0` forces a profile | A GGUF read in place copies experts with 4 threads when its pages are in the page cache (checked with `mincore` at the first prompt) and with 32 threads and a 128-deep ring when they are on an SSD. `STRATA_STAGER_THREADS` w
- **STRATA_STAGER_THREADS** — src/prefill/prefill.cpp:1619 docs: DETAILS.md, INTEL.md, UNSLOTH_Q4.md
  `const char* stv = std::getenv("STRATA_STAGER_THREADS");   // D-5: the host copy threads of unpinned blobs`
  // D-5: the host copy threads of unpinned blobs
  doc (DETAILS.md): | `STRATA_STAGER_SSD` | Linux | `STRATA_STAGER_SSD=1`/`0` forces a profile | A GGUF read in place copies experts with 4 threads when its pages are in the page cache (checked with `mincore` at the first prompt) and with 32 threads and a 128-deep ring when they are on an SSD. `STRATA_STAGER_THREADS` w
- **STRATA_STATE_HASH_GDN** — src/prefill/prefill.cpp:5843 (+1 more reads)
  `if (std::getenv("STRATA_STATE_HASH_GDN") != nullptr) {   // debug: the GDN states as the prompt path leaves them`
  // debug: the GDN states as the prompt path leaves them
- **STRATA_TEST_PAGEABLE** — src/prefill/prefill.cpp:195
  `static const bool v = [] { const char* e = std::getenv("STRATA_TEST_PAGEABLE"); return e != nullptr && e[0] == '1'; }();`
- **STRATA_TRACE** — src/program/generate.cpp:10728 (+3 more reads) docs: BATCHING.md, DETAILS.md
  `const bool ckpt_trace = std::getenv("STRATA_TRACE") != nullptr;`
  // STRATA_TRACE: what each checkpoint cost - the device syncs, the copies into RAM (the vectors' first fill included), the eviction that frees one - one line per checkpoint; with the prompt's read parts summed per request for a batch admission's line (below, at BADM)
  doc (DETAILS.md): The serve loop's `strata trace:` lines (`STRATA_TRACE`) now end with `@<ms>`, a steady-clock timestamp.
- **STRATA_WMMA_BF16** — src/prefill/gemm.cu:1044
  `static const bool bf16_on = [] { const char* v = std::getenv("STRATA_WMMA_BF16"); return !v || (v[0] != 0 && v[0] != '0'); }();`
- **STRATA_WMMA_GEMM** — src/prefill/gemm.cu:1043 (+1 more reads)
  `static const bool wmma_on = [] { const char* v = std::getenv("STRATA_WMMA_GEMM"); return v && v[0] != 0 && v[0] != '0'; }();`
  // #313 (opt-in STRATA_WMMA_GEMM=1; STRATA_WMMA_BF16=0 excludes bf16): RDNA3 / RDNA3.5 WMMA dense GEMM, before hipBLASLt; it returns false for shapes it does not take (and off gfx11) and this falls through
- **STRATA_WS_FAST** — src/prefill/moe_ws.cu:83 docs: OLDER_GPUS.md
  `const char* e = std::getenv("STRATA_WS_FAST");   // opt-in`
  // opt-in
  doc (OLDER_GPUS.md): MMQ's bits. Every other layer keeps its path. `STRATA_WS_FAST=1` adds a down kernel for the IQ4_NL 32-token tier with fewer
- **STRATA_XN_F16** — src/prefill/prefill.cpp:1746 docs: DETAILS.md
  `static const bool xn_env = [] { const char* e = std::getenv("STRATA_XN_F16"); return e == nullptr || e[0] != '0'; }();`
  // the hyper-connection's xn16 straight as the FP16 the tensor-core GEMM reads (its two readers then skip the conversion pass; the same values): STRATA_XN_F16=0 keeps the BF16 image
  doc (DETAILS.md): `STRATA_BF16_TC=1` with `STRATA_XN_F16`.

## src/program
- **STRATA_ADAPT_ASYNC_BATCH** — src/program/generate.cpp:11609
  `const size_t a_batch = a_arena ? (size_t) std::max(0, a_env("STRATA_ADAPT_ASYNC_BATCH", 0)) : 0;`
- **STRATA_ADAPT_ASYNC_WAIT** — src/program/generate.cpp:11608
  `const bool a_wait = a_arena && a_env("STRATA_ADAPT_ASYNC_WAIT", 1) != 0;`
- **STRATA_ADAPT_CALLBACK_WARMUP** — src/program/generate.cpp:6708 docs: DETAILS.md
  `if (const char* e = std::getenv("STRATA_ADAPT_CALLBACK_WARMUP"); !(e && e[0] == '0')) {`
  // 0.1.43.1: on by default (STRATA_ADAPT_CALLBACK_WARMUP=0 turns it off).  Linux threads inherit the creator's CPU mask, and the host pins itself to one CPU later; a callback thread the driver creates lazily after that would run on the host's CPU and fight the host's spin-wait (985 us instead of 4 us per callback, #1964 #1975).  Windows CPU Sets are per thread and not inherited.
  doc (DETAILS.md): | `STRATA_ADAPT_CALLBACK_WARMUP` | Linux | `=0` | Starts the GPU host-callback thread before the CPU pool pins the host thread. |
- **STRATA_ADAPT_CHECKRES** — src/program/generate.cpp:17860 (+1 more reads)
  `const bool res_checking = std::getenv("STRATA_ADAPT_CHECKRES") != nullptr && d_res != nullptr;`
  // before every window: the device's table follows the host's (the tier's evictions while its copies are in flight - see the serve path); the hook's captures live in this block, so it is taken off the verifier when the block ends
- **STRATA_ADAPT_EVICT_SYNC** — src/program/generate.cpp:1654
  `static const bool v = [] { const char* e = std::getenv("STRATA_ADAPT_EVICT_SYNC"); return e == nullptr || std::atoi(e) != 0; }();`
- **STRATA_ADAPT_JOB_CPU** — src/program/generate.cpp:1810 docs: DETAILS.md
  `const char* c = std::getenv("STRATA_ADAPT_JOB_CPU");`
  doc (DETAILS.md): `/proc/self/task` once the pool exists and again at the start of each request. An explicit `STRATA_ADAPT_JOB_CPU` wins for the
- **STRATA_ADAPT_LAG** — src/program/generate.cpp:1629 docs: DETAILS.md, OLDER_GPUS.md
  `static const int v = [] { const char* e = std::getenv("STRATA_ADAPT_LAG"); return e ? std::max(1, std::atoi(e)) : 1; }();`
  doc (DETAILS.md): | `STRATA_ADAPT_OVERLAP=1` | One GPU, the whole arena in RAM, no `--adapt-async`, `--pipeline-windows`, `STRATA_ADAPT_LAG`, `STRATA_ADAPT_NOWAIT`, `STRATA_DMA_BATCH`; never on a layer split | The adaptive tier's copies land while the next window runs, with the same tokens. The startup log names the 
- **STRATA_ADAPT_NOWAIT** — src/program/generate.cpp:1619 docs: DETAILS.md, OLDER_GPUS.md
  `static const bool v = [] { const char* e = std::getenv("STRATA_ADAPT_NOWAIT"); return e && e[0] == '1'; }();`
  doc (DETAILS.md): | `STRATA_ADAPT_OVERLAP=1` | One GPU, the whole arena in RAM, no `--adapt-async`, `--pipeline-windows`, `STRATA_ADAPT_LAG`, `STRATA_ADAPT_NOWAIT`, `STRATA_DMA_BATCH`; never on a layer split | The adaptive tier's copies land while the next window runs, with the same tokens. The startup log names the 
- **STRATA_ADAPT_OVERLAP** — src/program/generate.cpp:11219 (+1 more reads) docs: DETAILS.md, OLDER_GPUS.md
  `else if (std::getenv("STRATA_ADAPT_OVERLAP") != nullptr)   // the env var was set: say what stopped it`
  // the env var was set: say what stopped it
  doc (DETAILS.md): | `STRATA_ADAPT_OVERLAP=1` | One GPU, the whole arena in RAM, no `--adapt-async`, `--pipeline-windows`, `STRATA_ADAPT_LAG`, `STRATA_ADAPT_NOWAIT`, `STRATA_DMA_BATCH`; never on a layer split | The adaptive tier's copies land while the next window runs, with the same tokens. The startup log names the 
- **STRATA_ADAPT_OVERLAP_RESIDENT** — src/program/generate.cpp:11175 (+1 more reads)
  `: src.complement_ready() && !(std::getenv("STRATA_ADAPT_OVERLAP_RESIDENT") &&`
  // the resident RAM mode is exact too (soft_commit_exchanges) but not a win everywhere: RTX A4000 +7.0% (5/5 pairs), RTX 3060 on a 46 GB box -2.6% (0/5; the CPU experts and the copies share the RAM bandwidth)
- **STRATA_ADAPT_OVERLAP_SLOW_US** — src/program/generate.cpp:11444
  `static const int slow_us = [] { const char* e = std::getenv("STRATA_ADAPT_OVERLAP_SLOW_US"); return e ? std::atoi(e) : 0; }();`
  // test hook (STRATA_ADAPT_OVERLAP_SLOW_US=N): a slow link, to make the windows wait for the copies
- **STRATA_ADAPT_PICK_INLINE** — src/program/generate.cpp:11607
  `const bool a_inline = a_arena && a_env("STRATA_ADAPT_PICK_INLINE", 1) != 0;`
  // arena only (the other modes keep their steps as they were): the choice on this thread (STRATA_ADAPT_PICK_INLINE), the wait for the copies (STRATA_ADAPT_ASYNC_WAIT), the copies in flight per tick (STRATA_ADAPT_ASYNC_BATCH, 0 = all)
- **STRATA_ADAPT_SIGNAL** — src/program/generate.cpp:11190 docs: DETAILS.md
  `const char* asig = std::getenv("STRATA_ADAPT_SIGNAL");`
  // #2188: on Windows the default is the host function.  Under WDDM a stream's work sits in the driver's command buffer until something flushes it, and nothing does while the host only spins on the pinned int: the first request stopped with "copies for layer 45 never landed".  STRATA_ADAPT_SIGNAL=copy asks for the stream-ordered copy there too (the enqueue then flushes the stream), =host everywhere.
  doc (DETAILS.md): | `STRATA_ADAPT_SIGNAL` | CUDA | `host` / `copy` | The overlap's per-layer "landed" signal is a stream-ordered copy into pinned memory on Linux and a host function on Windows. |
- **STRATA_ADMIT_MERGE_FIRST** — src/program/generate.cpp:253 docs: BATCHING.md
  `const char* v = std::getenv("STRATA_ADMIT_MERGE_FIRST");`
  doc (BATCHING.md): | `STRATA_ADMIT_MERGE_FIRST=1` | an admission reads its last prompt tokens and its first token in one window (all experts resident only) |
- **STRATA_ARENA_RELEASE** — src/program/generate.cpp:8280 (+1 more reads)
  `static const bool keep = std::getenv("STRATA_ARENA_RELEASE") && std::getenv("STRATA_ARENA_RELEASE")[0] == '0';`
- **STRATA_AUX_CPUS** — src/program/generate.cpp:3456 docs: DETAILS.md
  `if (const char* e = std::getenv("STRATA_AUX_CPUS")) ac = e;`
  doc (DETAILS.md): - `--aux-cpus auto` (or `STRATA_AUX_CPUS=auto`): the SMT siblings of the host's core first, then the CPUs of physical cores
- **STRATA_BATCH_DECODE_SHARE** — src/program/generate.cpp:14952 docs: BATCHING.md
  `const char* v = std::getenv("STRATA_BATCH_DECODE_SHARE");`
  doc (BATCHING.md): 2048-8192 tokens) they decode for half as long as the chunk took (`STRATA_BATCH_DECODE_SHARE`, default 0.5), so
- **STRATA_BATCH_GROUPS_NV_SERIAL** — src/program/generate.cpp:5962 docs: BATCHING.md, release-notes-0.2.1.md, release-notes-0.2.7.md
  `bin.nv_serial_faster = strata::program::batch_groups::nv_serial_wanted(std::getenv("STRATA_BATCH_GROUPS_NV_SERIAL"),`
  // NVIDIA, 2 cards: the pipelined groups by default (0.2.7); one serial group, the 0.2.1-0.2.6 default, with STRATA_BATCH_GROUPS_NV_SERIAL=1 or STRATA_DEFAULTS=026 (batch_groups.hpp nv_serial_wanted)
  doc (release-notes-0.2.7.md): - **Two NVIDIA cards share several chats faster.** On two or more NVIDIA cards with a batch of slots, the engine now runs the cards as a pipeline by default; the serial way of 0.2.1 to 0.2.6 was slower at two and four chats. Two RTX A6000 (Qwen IQ3_S, no drafting): two chats +17% (125.7 against 107.
- **STRATA_BATCH_MTP** — src/program/generate.cpp:5968 (+2 more reads) docs: BATCHING.md
  `const char* batch_mtp_env = std::getenv("STRATA_BATCH_MTP");`
  doc (BATCHING.md): With MTP (`--mtp` and `--spec`), `--batch-mtp` (in the config's `args`, or `STRATA_BATCH_MTP=1` in the server's
- **STRATA_BATCH_MTP_SERIAL** — src/program/generate.cpp:5958 docs: BATCHING.md
  `{ const char* ms = std::getenv("STRATA_BATCH_MTP_SERIAL"); bin.mtp_serial = ms != nullptr && ms[0] != '\0' && ms[0] != '0'; }`
  doc (BATCHING.md): engine (0.1.43.1) pipelines and leaves `--batch-mtp` off, and says so (0.1.42/0.1.43 ran one serial group with it: 4 streams on 2x A4000 aggregated 63.9 tok/s against 91.8 pipelined, 85.8 pipelined without `--batch-mtp`; #2038). `--batch-groups 1` or `STRATA_BATCH_MTP_SERIAL=1` keeps `--batch-mtp` w
- **STRATA_BATCH_TELEMETRY** — src/program/generate.cpp:12459
  `const char* batch_telemetry_env = std::getenv("STRATA_BATCH_TELEMETRY");`
- **STRATA_BATCH_YIELD_CHUNKS** — src/program/generate.cpp:15022 docs: BATCHING.md
  `const char* v = std::getenv("STRATA_BATCH_YIELD_CHUNKS");`
  doc (BATCHING.md): the same read goes in `STRATA_BATCH_YIELD_CHUNKS` pieces then).
- **STRATA_CACHE_MESSAGE_BOUNDARY** — src/program/generate.cpp:15548 docs: MESSAGE_BOUNDARY_CACHE.md, PROMPT_CACHE_TAIL.md
  `const char* e = std::getenv("STRATA_CACHE_MESSAGE_BOUNDARY");`
  doc (MESSAGE_BOUNDARY_CACHE.md): Set `STRATA_CACHE_MESSAGE_BOUNDARY=1` before starting the engine.
- **STRATA_CKPT_POOL** — src/program/generate.cpp:268 docs: BATCHING.md, DETAILS.md
  `const char* v = std::getenv("STRATA_CKPT_POOL");`
  doc (DETAILS.md): | `STRATA_CKPT_POOL_READY=N` (1-16, with `STRATA_CKPT_POOL=1`) | The checkpoint pool keeps N ready checkpoints, sized at start and topped up in the background, so a save never faults in a fresh vector. It holds N x 118 MB of host memory from start-up. `STRATA_CKPT_POOL=1` alone is unchanged: it reus
- **STRATA_CKPT_POOL_READY** — src/program/generate.cpp:279 docs: DETAILS.md
  `const char* v = std::getenv("STRATA_CKPT_POOL_READY");`
  doc (DETAILS.md): | `STRATA_CKPT_POOL_READY=N` (1-16, with `STRATA_CKPT_POOL=1`) | The checkpoint pool keeps N ready checkpoints, sized at start and topped up in the background, so a save never faults in a fresh vector. It holds N x 118 MB of host memory from start-up. `STRATA_CKPT_POOL=1` alone is unchanged: it reus
- **STRATA_CKPT_REREAD** — src/program/generate.cpp:14594 (+1 more reads) docs: KVA.md, PROMPT_CACHE_TAIL.md
  `static const bool no_short = std::getenv("STRATA_CKPT_REREAD") != nullptr;`
  // not in VRAM over PCIe), and it borrows slots it must refill after (~180 ms); a window costs ~16 ms a token, with the misses on the CPU.  Each part below is decided on its own, so a long first message is read batched and its header still goes through the windows.  Picture rows need the batched path. STRATA_CKPT_REREAD compares a restored checkpoint with a batched re-read, so it keeps every read bat
  doc (PROMPT_CACHE_TAIL.md): is split into runs. What cuts a read into runs is the list of places where a read has to stop and start again: a re-read (`STRATA_CKPT_REREAD`),
- **STRATA_CKPT_THREADS** — src/program/generate.cpp:292 docs: BATCHING.md
  `const char* v = std::getenv("STRATA_CKPT_THREADS");`
  doc (BATCHING.md): | `STRATA_CKPT_POOL=1`, `STRATA_CKPT_THREADS=1` | a checkpoint is saved into the vectors of a dropped one; a split's stage parts are saved at once |
- **STRATA_DECODE_TIMING** — src/program/generate.cpp:15749 docs: AMD_HIP.md, DETAILS.md, MULTI_GPU.md, OLDER_GPUS.md, QUANTS.md
  `static const bool dec_timing = std::getenv("STRATA_DECODE_TIMING") != nullptr;`
  // STRATA_DECODE_TIMING=1: where a request's decode time goes (one line per request)
  doc (DETAILS.md): Profiling: start the server with `STRATA_DECODE_TIMING=1` (and `STRATA_VERIFY_PROFILE=1` for the GPU side). After each request
- **STRATA_DF2_WAITCOMMIT** — src/program/generate.cpp:18188
  `static const bool wait_commit_first = std::getenv("STRATA_DF2_WAITCOMMIT") != nullptr;   // measurement: no overlap with the async commit`
  // measurement: no overlap with the async commit
- **STRATA_DISJOINT_ADAPT** — src/program/generate.cpp:7625 docs: DISJOINT_EXPERT_CACHE.md
  `const bool disjoint_adapt = [] { const char* v = std::getenv("STRATA_DISJOINT_ADAPT"); return v != nullptr && std::atoi(v) != 0; }();`
  // #731 (opt-in, STRATA_DISJOINT_ADAPT=1): the adaptive tiers leave an expert a helper GPU holds out of the primary's promotion candidates (it would sit in both caches).  Asked live, from the helper's own cache (RemoteExperts::holds, #854), so an expert the helper's tier swaps in or out later is followed - never a copy taken at load.
  doc (DISJOINT_EXPERT_CACHE.md): Set `STRATA_DISJOINT_ADAPT=1` before starting the engine. It is off by default.
- **STRATA_DUMP_FIRST_LOGITS** — src/program/generate.cpp:18364 (+1 more reads)
  `if (const char* fl = std::getenv("STRATA_DUMP_FIRST_LOGITS")) {`
  // Diagnostics: the first window runs the prompt's last token over the state the prompt path left (keys, values, recurrent state), so its logits carry whatever that path did. A native pack never runs the per-token loop --dump-logits reads; this is where prompt paths can be compared by output.
- **STRATA_EARLY_REMOTE_CONTEXTS** — src/program/generate.cpp:4128
  `const char* early_env = std::getenv("STRATA_EARLY_REMOTE_CONTEXTS");`
  // STRATA_EARLY_REMOTE_CONTEXTS=1: create EVERY secondary context here, like CUDA1's.  Under WSL2 the driver's pinned/mapped host budget (dxg gpadl, ~1 GiB) is spent by CUDA0's weights and MTP before the later loop runs, and a new context then fails with cudaErrorMemoryAllocation (CUDA2: "cudaSetDevice(2) failed: out of memory").
- **STRATA_FETCH_THREADS** — src/program/generate.cpp:6465 docs: UNSLOTH_Q4.md
  `if (const char* v = std::getenv("STRATA_FETCH_THREADS"); v != nullptr && std::atoi(v) > 0)`
  doc (UNSLOTH_Q4.md): | `STRATA_FETCH_THREADS=N` | Threads that read the experts from the GGUF while it answers (default 8). The prompt path has its own: `STRATA_STAGER_THREADS` (default 32 here) and `STRATA_STAGER_RING` (128). |
- **STRATA_FILL_AHEAD** — src/program/generate.cpp:7210 docs: DETAILS.md
  `const char* v = std::getenv("STRATA_FILL_AHEAD");`
  doc (DETAILS.md): steps), which matters on a slow drive: `STRATA_READ_AHEAD=0` turns it off, `STRATA_FILL_AHEAD=N` sets how many fill pairs
- **STRATA_FS_AHEAD** — src/program/generate.cpp:7648
  `[] { const char* v = std::getenv("STRATA_FS_AHEAD"); return v == nullptr || std::atoi(v) != 0; }();`
- **STRATA_GFX1151_CHUNK** — src/program/generate.cpp:3368 docs: STRIX_HALO.md, release-notes-0.2.3.md
  `const char* c1 = std::getenv("STRATA_GFX1151_CHUNK");`
  doc (release-notes-0.2.3.md): - **Strix Halo (Ryzen AI Max) is faster.** Three changes, all on by default. The hyper-connection weights are read as 8-bit. A prompt is read in chunks of 8192 tokens again on Windows. The engine now finds its own tuning table, so a start that did not go through the launcher still gets it. Measured 
- **STRATA_GFX12_CHUNK** — src/program/generate.cpp:3402 (+1 more reads) docs: DETAILS.md
  `const char* c0 = std::getenv("STRATA_GFX12_CHUNK");`
  // gfx1200 / gfx1201 (RDNA4, Linux): a bare `--prefill auto` may reach 16384 instead of 8192 (R9700, IQ3_S / Q2_0, 16K / 32K / 64K prompts: +0.5 .. +5.8%, residuals identical to 8192).  The fit scan still picks a smaller chunk when the expert cache cannot lend the buffers.  An explicit --prefill N, auto:N or STRATA_PREFILL_AUTO_MAX is never touched (prefill_auto_bare is false then). STRATA_GFX12_DEFA
  doc (DETAILS.md): | Bare `--prefill auto` takes 16384-token chunks | gfx12, Linux | `STRATA_GFX12_CHUNK=0` or `STRATA_GFX12_DEFAULTS=0` | An explicit `--prefill N`, `auto:N` or `STRATA_PREFILL_AUTO_MAX` is untouched. |
- **STRATA_H2D_GBPS** — src/program/generate.cpp:8638 docs: RX7900XTX.md
  `const char* h2d_env = std::getenv("STRATA_H2D_GBPS");`
  // T01: an explicit --pcie-frac skips the probe up the stack, which left the planner on the 12.0 default while this box copies pinned host->device at 28.4 GB/s.  STRATA_H2D_GBPS is the operator's figure; else probe once here if no probe ran yet; 12.0 only when the probe cannot run either.  The source goes into the log line.
  doc (RX7900XTX.md): (this fork's planner probes PCIe once: `STRATA_H2D_GBPS` overrides).
- **STRATA_HC_REQ8** — src/program/generate.cpp:4442 (+1 more reads) docs: DETAILS.md
  `const bool hc_req8_env = std::getenv("STRATA_HC_REQ8") != nullptr && std::atoi(std::getenv("STRATA_HC_REQ8")) != 0;`
  // STRATA_HC_REQ8=1 (opt-in, changes the output): the hyper-connection projections are not loaded as BF16; load_hc_q8 below requantizes them to int8 + an fp32 scale per 32 values (~0.56x the bytes), and the freed VRAM goes to the expert cache like any other.  (Upstream's STRATA_HC_Q8 is a different thing: the GGUF's Q8_0 bytes.)
  doc (DETAILS.md): | `STRATA_HC_REQ8=1` | Hyper-connection projections as int8 plus a scale per 32 (more expert-cache slots) | Rounding level |
- **STRATA_HIP_ADAPT_KERNEL_COPY** — src/program/generate.cpp:348 docs: AMD_HIP.md, DETAILS.md
  `const char* e = std::getenv("STRATA_HIP_ADAPT_KERNEL_COPY");`
  doc (DETAILS.md): | HIP `STRATA_DENSE_MMQ=1`, `STRATA_HIP_ADAPT_KERNEL_COPY=1` | HIP | See [AMD_HIP.md](AMD_HIP.md#model-and-serving-configuration). | |
- **STRATA_HIP_QUEUE_PRIME** — src/program/generate.cpp:2715 docs: AMD_HIP.md, release-notes-0.2.1.md, release-notes-0.2.2.md
  `const char* env = std::getenv("STRATA_HIP_QUEUE_PRIME");`
  doc (AMD_HIP.md): | `STRATA_HIP_QUEUE_PRIME=0` | gfx1200, gfx1201, Linux | On | Turn off the ordered opening of two GPU queues at start (it avoids slow starts) |
- **STRATA_HOST_CORE** — src/program/generate.cpp:3436 docs: DETAILS.md
  `if (const char* e = std::getenv("STRATA_HOST_CORE")) hc = e;`
  doc (DETAILS.md): | `STRATA_HOST_CORE=last\|sibling` (or `--host-core`) | Windows | `last` puts the host thread on the last physical core, away from the core that gets the GPU's interrupts. `sibling` keeps it on the first core's other hardware thread, so the workers keep every core. The default `first` leaves a hybri
- **STRATA_IO_PF_THREADS** — src/program/generate.cpp:6516 docs: DETAILS.md
  `const char* th = std::getenv("STRATA_IO_PF_THREADS");`
  doc (DETAILS.md): | io prefetch | `STRATA_IO_PREFETCH=1` (`0` = off) | I/O threads read the layer's uncached experts and the router-predicted ones of the next layers with whole-blob `pread`s into the page cache. Tunables: `STRATA_LOOKAHEAD_K`, `STRATA_IO_PREFETCH_DEPTH` (2), `STRATA_IO_PF_THREADS` (8), `STRATA_IO_PF_
- **STRATA_IO_PREFETCH** — src/program/generate.cpp:6507 docs: BATCHING.md, DETAILS.md, RADEON_780M.md, release-notes-0.2.0.md, release-notes-0.2.1.md
  `const char* io_pf_env = std::getenv("STRATA_IO_PREFETCH");`
  // ahead on I/O threads while the current layer computes (see FileExpertSource::set_io_prefetch).  0.2.0: on by default on Linux, with the decode gate (STRATA_IO_PF_GATE) and zero-copy page-cached experts (STRATA_COLD_OVERLAP=4); STRATA_IO_PREFETCH=0 / STRATA_IO_PF_GATE=0 / STRATA_COLD_OVERLAP=0 turn them off. io prefetch + the gate: the GGUF read in place and (0.2.1) an experts.bin pack; zero-copy o
  doc (DETAILS.md): | io prefetch | `STRATA_IO_PREFETCH=1` (`0` = off) | I/O threads read the layer's uncached experts and the router-predicted ones of the next layers with whole-blob `pread`s into the page cache. Tunables: `STRATA_LOOKAHEAD_K`, `STRATA_IO_PREFETCH_DEPTH` (2), `STRATA_IO_PF_THREADS` (8), `STRATA_IO_PF_
- **STRATA_IO_PREFETCH_DEPTH** — src/program/generate.cpp:7667 docs: DETAILS.md
  `if (const char* dv = std::getenv("STRATA_IO_PREFETCH_DEPTH"); dv != nullptr && std::atoi(dv) > 0)`
  doc (DETAILS.md): | io prefetch | `STRATA_IO_PREFETCH=1` (`0` = off) | I/O threads read the layer's uncached experts and the router-predicted ones of the next layers with whole-blob `pread`s into the page cache. Tunables: `STRATA_LOOKAHEAD_K`, `STRATA_IO_PREFETCH_DEPTH` (2), `STRATA_IO_PF_THREADS` (8), `STRATA_IO_PF_
- **STRATA_IO_STATS** — src/program/generate.cpp:6555 (+1 more reads)
  `} else if (const char* sv = std::getenv("STRATA_IO_STATS"); sv != nullptr && std::atoi(sv) != 0) {`
- **STRATA_KEEP_MAPPING** — src/program/generate.cpp:9223
  `if (srcp == &src && src.unbuffered() && std::getenv("STRATA_KEEP_MAPPING") == nullptr) {`
  // pp-opt: with the file tier unbuffered, the mapped view of experts.bin is only a fallback from here on - and while it exists NTFS serves the unbuffered reads one at a time (drop_mapping).  STRATA_KEEP_MAPPING=1 keeps it (A/B).
- **STRATA_KV_GROW** — src/program/generate.cpp:5864 docs: DETAILS.md
  `const char* ev = std::getenv("STRATA_KV_GROW");`
  doc (DETAILS.md): | `--kv-grow` (or `STRATA_KV_GROW=1`; `--no-kv-grow` turns it off) | The KV takes VRAM only for the cells the requests reach; the expert cache holds the rest and gives slots back as the context grows. Needs one GPU, an expert profile, the whole KV in VRAM and every expert in RAM. Otherwise the engin
- **STRATA_KV_GROW_FLOOR** — src/program/generate.cpp:8749
  `if (const char* v = std::getenv("STRATA_KV_GROW_FLOOR"); v != nullptr && std::atoll(v) > 0) kvg.floor = std::atoll(v);`
  // tests: the cache keeps this many slots (its size: the K/V grows into new VRAM only)
- **STRATA_KV_GROW_HOLD** — src/program/generate.cpp:14469
  `static const bool hold_on = [] { const char* v = std::getenv("STRATA_KV_GROW_HOLD"); return v != nullptr && std::atoi(v) != 0; }();`
  // STRATA_KV_GROW_HOLD=1 (opt-in): keep the K/V as long as the longest parked conversation; default: trim to this request alone, as 0.1.40
- **STRATA_KV_GROW_INIT** — src/program/generate.cpp:5876
  `const char* iv = std::getenv("STRATA_KV_GROW_INIT");`
- **STRATA_KV_GROW_STEP** — src/program/generate.cpp:8747
  `if (const char* v = std::getenv("STRATA_KV_GROW_STEP"); v != nullptr && std::atoll(v) > 0) kvg.step = std::atoll(v);`
- **STRATA_KV_ROT** — src/program/generate.cpp:3735 (+1 more reads) docs: DETAILS.md, SPLIT_SERVE.md
  `const char* kv_rot = std::getenv("STRATA_KV_ROT");`
  // STRATA_KV_ROT=1: INT8 K/V through the Hadamard rotation --kv q4_0 already uses. Opt-in: first-token KL to fp16 K/V improved on an NVFP4 pack (0.0066 -> 0.0051) but not on IQ2_XS (0.0022 -> 0.0054)
  doc (DETAILS.md): the cells mean (engine version, CUDA or HIP, `--kv`, `STRATA_KV_ROT`, `--kv-resident`, `--max-context`, `--mtp-window`, the
- **STRATA_LAYER_SPLIT_GATE** — src/program/generate.cpp:5482
  `static const bool gate_dbg = std::getenv("STRATA_LAYER_SPLIT_GATE") != nullptr;`
- **STRATA_LAYER_SPLIT_PROBE** — src/program/generate.cpp:7467
  `const char* v = std::getenv("STRATA_LAYER_SPLIT_PROBE");`
- **STRATA_LOGPOS** — src/program/generate.cpp:14728 (+2 more reads) docs: QUANTS.md, RX7900XTX.md, UNSLOTH_Q4.md
  `if (pipe && n_stages == 2 && pl_pw >= 1 && std::getenv("STRATA_LOGPOS") == nullptr) return read_windows_pl(a, b, e);`
  // (STRATA_LOGPOS reads every window's logits: the serial loop) the pipelined prompt read stays two-stage (three or more stages read serially; only the decode overlaps)
  doc (RX7900XTX.md): **Quality reference.** `STRATA_LOGPOS` only covers tokens read by verify windows, not prefill, so prompt kernels are
- **STRATA_LOGPOS_EXTRA** — src/program/generate.cpp:14766
  `const char* p = std::getenv("STRATA_LOGPOS_EXTRA");`
- **STRATA_LOOKAHEAD** — src/program/generate.cpp:7652 docs: UNSLOTH_Q4.md
  `[] { const char* v = std::getenv("STRATA_LOOKAHEAD"); return v == nullptr || std::atoi(v) != 0; }()) {`
  doc (UNSLOTH_Q4.md): | `STRATA_LOOKAHEAD=0` | Turns off the routing-aware prefetch (on by default in this mode). While the CPU works on a layer, a thread applies the next layer's router to this layer's input and asks the OS to read the predicted experts' pages. Pages only; the answers are the same. `STRATA_LOOKAHEAD_K` 
- **STRATA_LOOKAHEAD_K** — src/program/generate.cpp:7663 docs: DETAILS.md, UNSLOTH_Q4.md
  `const char* kv = std::getenv("STRATA_LOOKAHEAD_K");`
  doc (DETAILS.md): | io prefetch | `STRATA_IO_PREFETCH=1` (`0` = off) | I/O threads read the layer's uncached experts and the router-predicted ones of the next layers with whole-blob `pread`s into the page cache. Tunables: `STRATA_LOOKAHEAD_K`, `STRATA_IO_PREFETCH_DEPTH` (2), `STRATA_IO_PF_THREADS` (8), `STRATA_IO_PF_
- **STRATA_LOOKAHEAD_STATS** — src/program/generate.cpp:7650 docs: DETAILS.md
  `const bool la_stats = srcp != nullptr && [] { const char* v = std::getenv("STRATA_LOOKAHEAD_STATS"); return v != nullptr && std::atoi(v) != 0; }();`
  // STRATA_LOOKAHEAD_STATS=1 (measurement only): run the predictor on any tier and score it against the real routing
  doc (DETAILS.md): decoding a little: use it to compare, not to measure speed. `STRATA_LOOKAHEAD_STATS=1` scores the next-layer expert
- **STRATA_LOOKUP_CHAIN_FIXED** — src/program/generate.cpp:15740 (+1 more reads)
  `static const bool chain_fixed = std::getenv("STRATA_LOOKUP_CHAIN_FIXED") != nullptr;   // no policy gate`
  // no policy gate
- **STRATA_MEMORY_LIMIT_MIB** — src/program/generate.cpp:3467 docs: DETAILS.md
  `const char* env = std::getenv("STRATA_MEMORY_LIMIT_MIB");`
  doc (DETAILS.md): | `--memory-limit-mib N` (or `STRATA_MEMORY_LIMIT_MIB`) | Total RAM this engine's container may use, for when a container cannot see its own limit. Config `args`: `"--memory-limit-mib", "102400"`. `0` = none. |
- **STRATA_MTP_STAGE0** — src/program/generate.cpp:4945 (+1 more reads) docs: MULTI_GPU.md
  `const char* e0 = std::getenv("STRATA_MTP_STAGE0");`
  // #2637: the default (above) takes two stages only with the draft layer on the first card (mtp_first); asked for by hand it was taken without a word.  Recommend, never force: it stays on as asked, and the line says what it costs.
  doc (MULTI_GPU.md): chain starts. `STRATA_MTP_STAGE0=0` keeps the old place.
- **STRATA_OWNED_PRICE** — src/program/generate.cpp:6782 docs: DETAILS.md
  `static const bool exact = [] { const char* v = std::getenv("STRATA_OWNED_PRICE"); return v != nullptr && std::string(v) == "exact"; }();`
  doc (DETAILS.md): | `STRATA_OWNED_PRICE=exact` | CUDA | The cache sizing prices the prompt path's own buffers by their real allocation. | |
- **STRATA_PCIE_AUTO_CANON** — src/program/generate.cpp:4160
  `const char* pac = std::getenv("STRATA_PCIE_AUTO_CANON");`
  // Windows: opt-in (STRATA_PCIE_AUTO_CANON=1); an RTX 5070 decoded a short Q2_0 answer 3% slower with it, code 2.5% faster
- **STRATA_PCIE_AUTO_SPLIT** — src/program/generate.cpp:2102 docs: DETAILS.md
  `static const bool on = [] { const char* v = std::getenv("STRATA_PCIE_AUTO_SPLIT"); return v != nullptr && std::atoi(v) != 0; }();   // opt-in until measured (HI`
  // opt-in until measured (HIP)
  doc (DETAILS.md): | PCIe share from the CPU's speed | CUDA, one GPU, no `--pcie-frac` | `--pcie-frac N` always wins; `STRATA_PCIE_FRAC_DEFAULT=old` keeps the probe-only rule | The share starts at the probe's value and is refined in the first decode windows from the CPU pool's time per missed expert: `L / (L + 1.85 R)
- **STRATA_PCIE_BALANCE** — src/program/generate.cpp:4200 docs: DETAILS.md, RX7900XTX.md
  `const char* e = std::getenv("STRATA_PCIE_BALANCE");`
  doc (DETAILS.md): | `STRATA_PCIE_BALANCE=1` | CUDA, one GPU, no `--batch`, no `--pcie-frac` | Each verify layer reads over PCIe the number of its missed experts that balances the two sides. | Helps an RTX A4000 arena (+5.6%), hurts others slightly. |
- **STRATA_PCIE_FRAC_DEFAULT** — src/program/generate.cpp:2152 (+1 more reads) docs: AMD_HIP.md, DETAILS.md
  `const char* pfd = std::getenv("STRATA_PCIE_FRAC_DEFAULT");`
  doc (DETAILS.md): | PCIe share from the CPU's speed | CUDA, one GPU, no `--pcie-frac` | `--pcie-frac N` always wins; `STRATA_PCIE_FRAC_DEFAULT=old` keeps the probe-only rule | The share starts at the probe's value and is refined in the first decode windows from the CPU pool's time per missed expert: `L / (L + 1.85 R)
- **STRATA_PEER_HOT** — src/program/generate.cpp:5091
  `const char* ph = std::getenv("STRATA_PEER_HOT");`
- **STRATA_PEER_HOT_AT** — src/program/generate.cpp:5093
  `const char* pa = std::getenv("STRATA_PEER_HOT_AT");`
- **STRATA_PIN_BY_NEED** — src/program/generate.cpp:6587 docs: DETAILS.md, DOCKER.md, TERMINAL_LAUNCH.md
  `if (const char* pn = std::getenv("STRATA_PIN_BY_NEED"); pn != nullptr && pn[0] != '\0' && pn[0] != '0') {`
  doc (DETAILS.md): - Windows, opt-in: `STRATA_PIN_BY_NEED=1` (arena on one GPU) registers the profile's non-GPU-resident experts by rank up to
- **STRATA_PIN_BY_NEED_SKIP** — src/program/generate.cpp:6598
  `if (const char* sk = std::getenv("STRATA_PIN_BY_NEED_SKIP"); sk != nullptr && sk[0] != '\0') {`
- **STRATA_PIPED_CONCURRENT_UNPIN** — src/program/generate.cpp:15123
  `const char* v = std::getenv("STRATA_PIPED_CONCURRENT_UNPIN");`
- **STRATA_PIPED_DECODE_MAX_MS** — src/program/generate.cpp:15340 docs: BATCHING.md
  `const char* v = std::getenv("STRATA_PIPED_DECODE_MAX_MS");`
  doc (BATCHING.md): the pipeline for `STRATA_BATCH_DECODE_SHARE` x the piece's time, at most `STRATA_PIPED_DECODE_MAX_MS` and at least
- **STRATA_PIPED_DECODE_MIN_MS** — src/program/generate.cpp:15344 docs: BATCHING.md
  `const char* v = std::getenv("STRATA_PIPED_DECODE_MIN_MS");`
  doc (BATCHING.md): `STRATA_PIPED_DECODE_MIN_MS`, and every group in flight finishes before the next piece, as before any prompt read.
- **STRATA_PIPED_MTP** — src/program/generate.cpp:5965 (+1 more reads) docs: BATCHING.md, release-notes-0.2.7.md
  `{ const char* mp = std::getenv("STRATA_PIPED_MTP"); bin.mtp_piped = mp != nullptr && mp[0] != '\0' && mp[0] != '0'; }`
  doc (release-notes-0.2.7.md): - **Pipelined drafts for batch slots** (`STRATA_PIPED_MTP=1` with `--batch-mtp`, #4121 by @wannagoxuf). The draft model also runs for the slots of a batch on a two-card layer split. On two RTX A6000 with a batch of slots, five paired runs before the merge: two streams +15.4% (five of five pairs), fo
- **STRATA_PIPED_READ_PIECE** — src/program/generate.cpp:15336 docs: BATCHING.md
  `const char* v = std::getenv("STRATA_PIPED_READ_PIECE");`
  doc (BATCHING.md): - `STRATA_PIPED_READ_PIECE=N`: a prompt read on the pipelined groups goes in pieces of N tokens, rounded down to whole
- **STRATA_PIPELINE_ADAPT_ASYNC** — src/program/generate.cpp:8980
  `const char* v = std::getenv("STRATA_PIPELINE_ADAPT_ASYNC");`
- **STRATA_PIPELINE_AGREE** — src/program/generate.cpp:16063
  `const char* v = pipe_dbg_env("STRATA_PIPELINE_AGREE");`
- **STRATA_PIPELINE_AUTO** — src/program/generate.cpp:4908 docs: MULTI_GPU.md
  `static const char* ae = std::getenv("STRATA_PIPELINE_AUTO");`
  doc (MULTI_GPU.md): `--pipeline-windows 0` or `STRATA_PIPELINE_AUTO=0` turns it off. NVIDIA builds keep it opt-in (`--pipeline-windows 2`).
- **STRATA_PIPELINE_AUTO_MIN_STAGES** — src/program/generate.cpp:4909
  `static const char* am = std::getenv("STRATA_PIPELINE_AUTO_MIN_STAGES");`
- **STRATA_PIPELINE_DEBUG** — src/program/generate.cpp:422 docs: MULTI_GPU.md
  `static const bool on = [] { const char* v = std::getenv("STRATA_PIPELINE_DEBUG"); return v != nullptr && v[0] != 0 && v[0] != '0'; }();`
  doc (MULTI_GPU.md): The `STRATA_PIPELINE_*` tuning and test variables are read only with `STRATA_PIPELINE_DEBUG=1`.
- **STRATA_PIPELINE_DOOM_SKIP** — src/program/generate.cpp:15892
  `static const bool doom_skip = [] { const char* e = pipe_dbg_env("STRATA_PIPELINE_DOOM_SKIP"); return e == nullptr || std::atoi(e) != 0; }();`
  // a doomed window (its guess was wrong) gets empty plans: no expert work on the CPU or the GPU for its remaining layers, so it frees stage 0 and the pool sooner (its rows are discarded and the undo restores everything it wrote).  STRATA_PIPELINE_DOOM_SKIP=0: served in full.
- **STRATA_PIPELINE_FORCE_MISS** — src/program/generate.cpp:14618
  `const char* v = pipe_dbg_env("STRATA_PIPELINE_FORCE_MISS");`
- **STRATA_PIPELINE_LOG** — src/program/generate.cpp:15819
  `static const bool pl_log = pipe_dbg_env("STRATA_PIPELINE_LOG") != nullptr;`
- **STRATA_PIPELINE_LOOKUP_PON** — src/program/generate.cpp:16012
  `const char* v = pipe_dbg_env("STRATA_PIPELINE_LOOKUP_PON");`
- **STRATA_PIPELINE_PRESTAGE** — src/program/generate.cpp:16059
  `const char* v = pipe_dbg_env("STRATA_PIPELINE_PRESTAGE");`
- **STRATA_PIPELINE_SNAP_OVERLAP** — src/program/generate.cpp:10209
  `pl_snap_overlap = [] { const char* v = pipe_dbg_env("STRATA_PIPELINE_SNAP_OVERLAP"); return v == nullptr || std::atoi(v) != 0; }();`
- **STRATA_PIPELINE_SPEC_DEPTH** — src/program/generate.cpp:16219
  `const char* v = pipe_dbg_env("STRATA_PIPELINE_SPEC_DEPTH");`
- **STRATA_PIPELINE_SWITCH** — src/program/generate.cpp:14621
  `if (static const char* sw = pipe_dbg_env("STRATA_PIPELINE_SWITCH"); sw != nullptr && pipe) {`
- **STRATA_PIPELINE_THETA** — src/program/generate.cpp:14614
  `const char* v = pipe_dbg_env("STRATA_PIPELINE_THETA");`
- **STRATA_PIPELINE_TRACE** — src/program/generate.cpp:15876
  `static const char* pl_trace_path = pipe_dbg_env("STRATA_PIPELINE_TRACE");`
  // STRATA_PIPELINE_TRACE=<file>: every event of the loop with its time (appended per request)
- **STRATA_PIPE_ADAPT_EVERY** — src/program/generate.cpp:13109 (+1 more reads) docs: BATCHING.md, release-notes-0.2.7.md
  `const int pipe_adapt_every = strata::program::batch_groups::pipe_adapt_every(std::getenv("STRATA_PIPE_ADAPT_EVERY"));`
  // finish, and runs one round there as batch_step runs it between serial windows (nothing in flight reads a cache slot; the swapped-in experts land before the next launch), then goes on.  Never while a prompt is read beside the slots (its loan of cache slots), nor with --adapt-async (its own ticks). (the rule: batch_groups.hpp pipe_adapt_every / pipe_adapt_due, tested in batch_groups_test)
  doc (release-notes-0.2.7.md): - Opt-in switches from pull requests, each checked for exactness or by unit tests and builds, not for speed on your card: a bigger Pascal (GP100) set (`STRATA_DOWN_WS=1`, `STRATA_MTP_Q8_SM60=1`, `STRATA_MMQ_WS=1`, `STRATA_PATTN_SM60=1`, `STRATA_EXPERT_NIBBLE=1`), `STRATA_PF_FUSED_Q2N=1` for the Q2_0
- **STRATA_PIPE_BYIELD_NODRAIN** — src/program/generate.cpp:241 docs: BATCHING.md
  `const char* v = std::getenv("STRATA_PIPE_BYIELD_NODRAIN");`
  doc (BATCHING.md): | `STRATA_PIPE_BYIELD_NODRAIN=1` | a BYIELD that reaches a pipelined batch is dropped without draining the groups |
- **STRATA_PLE_AUTO_MMAP** — src/program/generate.cpp:4721 docs: DETAILS.md
  `if (const char* am = std::getenv("STRATA_PLE_AUTO_MMAP"); am == nullptr || std::atoi(am) == 0) auto_mmap = false;`
  doc (DETAILS.md): | `--ple-io direct` | all | `--ple-io ram` or `mmap` | The n-gram table is read unbuffered from the SSD. A startup probe warns when direct reads are slow (under 15K rows/s) but never switches by itself. `STRATA_PLE_AUTO_MMAP=1` brings back the automatic switch to `mmap`. On a rotational disk setup a
- **STRATA_PLE_AUTO_RAM** — src/program/generate.cpp:4673 docs: AMD_HIP.md
  `const char* auto_ram = std::getenv("STRATA_PLE_AUTO_RAM");`
  doc (AMD_HIP.md): | `STRATA_PLE_AUTO_RAM=0` | all | On where the RAM fits | Keep the n-gram table in RAM when `--ple-io` was not given (RDNA4: 8K prompt +22.5%, see [RDNA4](#rdna4-gfx1201)); `=0` keeps the direct reads |
- **STRATA_PLE_PROBE** — src/program/generate.cpp:4710
  `if (pio.mode == strata::kernels::PleIo::Direct && std::getenv("STRATA_PLE_PROBE") == nullptr) {`
  // Recommend, never force: when the default direct reads measure slow, switch to the mapped reads (40-100x faster on the reporters' drives); an explicit --ple-io direct is kept and only warned about.
- **STRATA_POOL_CORES** — src/program/generate.cpp:3444 docs: DETAILS.md, release-notes-0.2.2.md
  `if (const char* e = std::getenv("STRATA_POOL_CORES")) pc = e;`
  doc (DETAILS.md): `--pool-cores LIST` (or `STRATA_POOL_CORES=LIST`, `"pool_cores": "2,4,6,8"` in the config, or `strata launch --pool-cores 2,4,6,8`)
- **STRATA_PREFILL_AUTO_MAX** — src/program/generate.cpp:3118 docs: DETAILS.md
  `const char* env_max = std::getenv("STRATA_PREFILL_AUTO_MAX");`
  // #282: auto:N (N = 16384 or 32768) or STRATA_PREFILL_AUTO_MAX lets auto take chunks above 8192
  doc (DETAILS.md): | Bare `--prefill auto` takes 16384-token chunks | gfx12, Linux | `STRATA_GFX12_CHUNK=0` or `STRATA_GFX12_DEFAULTS=0` | An explicit `--prefill N`, `auto:N` or `STRATA_PREFILL_AUTO_MAX` is untouched. |
- **STRATA_PREFILL_EQUAL** — src/program/generate.cpp:8426 docs: DETAILS.md
  `static const bool equal_chunks = [] { const char* e = std::getenv("STRATA_PREFILL_EQUAL"); return e != nullptr && e[0] == '1'; }();`
  // is its number of such chunks and equal chunks borrow no more slots than that count needs.  A last chunk below stream_all_min_tokens() stays as it is (it moves only the experts its own tokens route to).  Used ONLY where a segment's chunk is chosen (the serve lend, generate's prompt); `request_chunk` is unchanged because STRATA_SPLIT_SMALL_OWN uses it too.  The chunk geometry changes the rounding, s
  doc (DETAILS.md): | `STRATA_PREFILL_EQUAL=1` | CUDA | A prompt segment is read in chunks of equal size, not full chunks and a short last one. Changes rounding. | |
- **STRATA_PREFILL_HELPER_SOURCE** — src/program/generate.cpp:9287
  `if (const char* hv = std::getenv("STRATA_PREFILL_HELPER_SOURCE"); hv != nullptr && std::atoi(hv) != 0 &&`
- **STRATA_PREFILL_HOST_PLAN** — src/program/generate.cpp:8622 docs: DETAILS.md, release-notes-0.2.0.md
  `const char* off = std::getenv("STRATA_PREFILL_HOST_PLAN");`
  doc (DETAILS.md): and on Windows. `STRATA_PREFILL_HOST_PLAN=0` turns it off; `STRATA_SSD_GBPS` overrides the drive speed;
- **STRATA_PREFILL_LEND_PCT** — src/program/generate.cpp:5341 (+2 more reads)
  `const char* v = std::getenv("STRATA_PREFILL_LEND_PCT");`
- **STRATA_PREFILL_PLAN_TOKS** — src/program/generate.cpp:8659
  `if (const char* e = std::getenv("STRATA_PREFILL_PLAN_TOKS"); e != nullptr && std::atof(e) > 0.0)`
- **STRATA_PRIMARY_DEVICE** — src/program/generate.cpp:2717 (+1 more reads) docs: SECOND_GPU.md
  `const char* pv = std::getenv("STRATA_PRIMARY_DEVICE");`
  doc (SECOND_GPU.md): ## Choosing the primary device on Windows (`STRATA_PRIMARY_DEVICE`)
- **STRATA_PROMPT_DIRECT** — src/program/generate.cpp:9210 docs: QUANTS.md
  `if (!ub && [] { const char* v = std::getenv("STRATA_PROMPT_DIRECT"); return v != nullptr && v[0] == '1'; }()) {`
  // MODEL-UPDATE round 2 (opt-in STRATA_PROMPT_DIRECT=1): the prompt path's batched reads unbuffered while decode keeps the file cache (z440, UD-Q4_K_XL, 39 GiB budget: all-unbuffered doubled the 6K prompt but cost decode 9-13%).  The same bytes either way.
  doc (QUANTS.md): llama.cpp on the same PC and file 14.8-16.5 / 117-123. `STRATA_PROMPT_DIRECT=1` (Linux, opt-in) reads the prompt
- **STRATA_RAM_ADAPT** — src/program/generate.cpp:16531 docs: DETAILS.md, release-notes-0.2.7.md
  `const char* e = std::getenv("STRATA_RAM_ADAPT");`
  doc (DETAILS.md): - `STRATA_RAM_ADAPT=<n>` (opt-in, `--serve`, one GPU, needs `--adapt-every`): the RAM copy also follows the conversation.
- **STRATA_RAM_ADAPT2** — src/program/generate.cpp:9305
  `const char* v = std::getenv("STRATA_RAM_ADAPT2");`
- **STRATA_RAM_ADAPT_CACHED_W** — src/program/generate.cpp:9308
  `if (const char* w = std::getenv("STRATA_RAM_ADAPT_CACHED_W")) ram_adapt2.cached_w = (float) std::clamp(std::atof(w), 0.0, 1.0);`
- **STRATA_RAM_ADAPT_PER_LAYER** — src/program/generate.cpp:9309
  `if (const char* w = std::getenv("STRATA_RAM_ADAPT_PER_LAYER")) ram_adapt2.per_layer = std::max(1, std::atoi(w));`
- **STRATA_RAM_ADAPT_PROMPT_W** — src/program/generate.cpp:9307
  `if (const char* w = std::getenv("STRATA_RAM_ADAPT_PROMPT_W")) ram_adapt2.prompt_w = (float) std::max(0.0, std::atof(w));`
- **STRATA_RAM_ADAPT_SKIP_TOP** — src/program/generate.cpp:9310
  `if (const char* w = std::getenv("STRATA_RAM_ADAPT_SKIP_TOP")) ram_adapt2.skip_top = std::max(0, std::atoi(w));`
- **STRATA_REFILL_BLOCKING** — src/program/generate.cpp:412
  `static const bool v = std::getenv("STRATA_REFILL_BLOCKING") != nullptr;`
- **STRATA_REFILL_PARTS** — src/program/generate.cpp:14794 docs: STRIX_HALO.md
  `static const bool refill_parts = [] { const char* v = std::getenv("STRATA_REFILL_PARTS"); return v != nullptr && std::atoi(v) != 0; }();`
  // stage's cache holding an expert it does not own, which is silent and produces plausible tokens. (split in two halves so a layer split can queue every stage's copies before it waits for any: #340) STRATA_REFILL_PARTS=1 (gfx1151's table): a lent slot of a GGUF read in place is refilled from the pieces in the mapping. The default assembles the blob in a staging buffer first (a 4 MB copy on this threa
  doc (STRIX_HALO.md): | `STRATA_REFILL_PARTS=1` (exact; HIP and CUDA, a GGUF read in place) | Refills the expert-cache slots a prompt borrowed straight from the GGUF mapping instead of through an assembled 4 MB copy per expert. Only gfx1151 has measured it. |
- **STRATA_REFILL_SERIAL** — src/program/generate.cpp:14835
  `static const bool refill_serial = std::getenv("STRATA_REFILL_SERIAL") != nullptr;`
  // #340: with several stages every stage's copies go out first (each card on its own link), then each is waited for - the same copies into the same slots, so the same cache; one stage: refill_one exactly. STRATA_REFILL_SERIAL=1: stage after stage, as 0.1.30/0.1.31.
- **STRATA_RESIDENT_HEADROOM_GIB** PROD=8 — src/program/generate.cpp:3304 (+1 more reads) docs: AMD_HIP.md, DETAILS.md, RX7900XTX.md, TROUBLESHOOTING.md
  `if (const char* v = std::getenv("STRATA_RESIDENT_HEADROOM_GIB"); v != nullptr && std::atof(v) >= 0.0)`
  doc (DETAILS.md): - The resident variant keeps 4 GB of the RAM it finds free (`STRATA_RESIDENT_HEADROOM_GIB`). When even the missing experts do
- **STRATA_RESIDENT_PIN** PROD=1 — src/program/generate.cpp:3302 (+1 more reads) docs: DETAILS.md, RX7900XTX.md, TROUBLESHOOTING.md, UNSLOTH_Q4.md
  `if (const char* v = std::getenv("STRATA_RESIDENT_PIN"); v != nullptr && std::string(v) == "0")`
  // A/B arms: STRATA_RESIDENT_PIN=0 keeps the copy pageable (the --resident-cpu-experts form); STRATA_RESIDENT_HEADROOM_GIB=N leaves N GiB of the available RAM free instead of 4
  doc (DETAILS.md): `STRATA_RESIDENT_PIN=0`) gives the mapped mode's exact tokens.
- **STRATA_ROUTE_RESIDENT_MTP** — src/program/generate.cpp:9905 (+1 more reads) docs: DETAILS.md
  `std::getenv("STRATA_ROUTE_RESIDENT_MTP") != nullptr && std::atoi(std::getenv("STRATA_ROUTE_RESIDENT_MTP")) != 0) {`
  doc (DETAILS.md): | `STRATA_ROUTE_PRIOR`, `STRATA_ROUTE_RESIDENT`, `STRATA_ROUTE_RESIDENT_MTP` | CUDA | Routing changes that add speed and also add KL. | Not recommended, except that 0.2.7 turns `STRATA_ROUTE_PRIOR=1.5` on by itself on a discrete NVIDIA card of 13 GiB or less (the owner approved the quality trade for
- **STRATA_RSS_TRACE** — src/program/generate.cpp:398
  `static const bool on = std::getenv("STRATA_RSS_TRACE") != nullptr;`
- **STRATA_SLOT_CKPT_MOVE** — src/program/generate.cpp:305 docs: BATCHING.md
  `const char* v = std::getenv("STRATA_SLOT_CKPT_MOVE");`
  doc (BATCHING.md): | `STRATA_SLOT_CKPT_MOVE=1` | the admission's turn checkpoint moves into the slot (no 112 MB copy); it also keeps the dropped checkpoints' storage, as `STRATA_CKPT_POOL` does; a session SAVE or parked conversation taken right after an admission lacks the moved checkpoint (the slot holds it) |
- **STRATA_SLOT_COPY_BATCHSYNC** — src/program/generate.cpp:316 docs: BATCHING.md
  `const char* v = std::getenv("STRATA_SLOT_COPY_BATCHSYNC");`
  doc (BATCHING.md): | `STRATA_SLOT_COPY_BATCHSYNC=1` | with the above: queue the ~116 copies and synchronize each device once |
- **STRATA_SLOT_COPY_DIRECT** — src/program/generate.cpp:12488 docs: BATCHING.md
  `const char* v = std::getenv("STRATA_SLOT_COPY_DIRECT");`
  doc (BATCHING.md): | `STRATA_SLOT_COPY_DIRECT=1` | an admission (and a slot's resume) copies the running state and the QSA K/V device to device, instead of through host images |
- **STRATA_SNAPSHOT_FULL_CAPTURE** — src/program/generate.cpp:14436 docs: DETAILS.md
  `if (std::getenv("STRATA_SNAPSHOT_FULL_CAPTURE") == nullptr) {`
  doc (DETAILS.md): stage. Parked snapshots are not kept across restarts; session files are. `STRATA_SNAPSHOT_FULL_CAPTURE=1` disables K/V
- **STRATA_SNAPSHOT_VERIFY** — src/program/generate.cpp:10940 (+1 more reads)
  `if (use_mtp && std::getenv("STRATA_SNAPSHOT_VERIFY") != nullptr)`
- **STRATA_SPEC_ADAPT_EVERY** — src/program/generate.cpp:3765
  `const char* e = std::getenv("STRATA_SPEC_ADAPT_EVERY");`
- **STRATA_SPEC_ADAPT_WARM** — src/program/generate.cpp:3766
  `const char* w = std::getenv("STRATA_SPEC_ADAPT_WARM");`
- **STRATA_SPEC_COST** — src/program/generate.cpp:18074 (+1 more reads) docs: DETAILS.md
  `const bool spec_cost = [] { const char* v = std::getenv("STRATA_SPEC_COST"); return v != nullptr && v[0] == '1'; }();`
  // STRATA_SPEC_TRACE=<file> (bench only, off by default): one line per round, "T a sfx ms p1 p2 ..." (window rows, drafts accepted, lookup window, round ms, the MTP draft probabilities), for offline window-length policy studies STRATA_SPEC_COST=1 (A/B arm, bench): the MTP window by expected tokens per ms at this machine's measured row costs (DraftPolicy::keep_draft, step by step) instead of "draft pr
  doc (DETAILS.md): --pcie-frac 0` and without `STRATA_SPEC_COST`; otherwise the engine says so once and keeps the older rule. This is a
- **STRATA_SPEC_COST_TABLE** — src/program/generate.cpp:18122
  `if (const char* tab = std::getenv("STRATA_SPEC_COST_TABLE"); spec_cost && tab != nullptr && tab[0] != '\0') {`
- **STRATA_SPEC_DEPTH** — src/program/generate.cpp:17321 docs: DETAILS.md
  `if (std::getenv("STRATA_SPEC_DEPTH") != nullptr)`
  doc (DETAILS.md): sampling. `STRATA_SPEC_DEPTH=1` prints acceptance by draft depth and `STRATA_SPEC_MIN_TEMP=0.9` limits sampled drafting
- **STRATA_SPEC_TRACE** — src/program/generate.cpp:18077
  `if (const char* tf = std::getenv("STRATA_SPEC_TRACE"); tf != nullptr && tf[0] != '\0') spec_trace = std::fopen(tf, "w");`
- **STRATA_SPEC_T_CYCLE** — src/program/generate.cpp:18062
  `if (const char* tc = std::getenv("STRATA_SPEC_T_CYCLE"); tc != nullptr && tc[0] != '\0') {`
- **STRATA_SPEC_WATCH** — src/program/generate.cpp:18163 docs: release-notes-0.2.2.md
  `if (const char* sw = std::getenv("STRATA_SPEC_WATCH"); sw != nullptr && std::atoi(sw) > 0) {`
  // STRATA_SPEC_WATCH=<seconds> (diagnostics, off by default): the serve watchdog for this loop.  A run whose verify windows and prompt chunks stop beating for that long prints the stage it is in and the stall report, then ends.
  doc (release-notes-0.2.2.md): - **Speculative decoding.** A rare hang of the first verify window on the HIP engine is fixed: about 1 run in 5 on a Strix Halo with IQ3_S stopped after the first window (8 of 41 runs without the fix, 0 of 46 with it). The cause was a GPU launch that waited for a flag the host raised only after the 
- **STRATA_SPLIT_CHUNK16K** — src/program/generate.cpp:8468 docs: MULTI_GPU.md
  `static const char* keep16 = std::getenv("STRATA_SPLIT_CHUNK16K");`
  doc (MULTI_GPU.md): | `STRATA_SPLIT_CHUNK16K=1` | Keeps the 16384-token auto chunk on AMD gfx12 splits (default 8192). | |
- **STRATA_SPLIT_COVER_B** — src/program/generate.cpp:5324 (+2 more reads)
  `const bool coverage_curve = ns >= 4 || std::getenv("STRATA_SPLIT_COVER_B") != nullptr;`
  // Up to 3 GPUs the 0.1.39 curve (r+1)^-1.2 is kept, so 2- and 3-GPU placements do not move (the new curve is a fit to a 4-way rig and was not measured on them); STRATA_SPLIT_COVER_B asks for the coverage curve at any GPU count.
- **STRATA_SPLIT_LINK_ABS** — src/program/generate.cpp:5282
  `static const bool link_abs = [] { const char* v = std::getenv("STRATA_SPLIT_LINK_ABS"); return v && v[0] == '1'; }();`
  // #2007: relative to the fastest stage's link and only from a 4x gap on (split_rules::link_miss_scale): a symmetric rig, or a moderate gap, keeps the fitted formula.  STRATA_SPLIT_LINK_ABS=1: 0.1.41's 20 GB/s rule. STRATA_SPLIT_UNIFORM=1: no per-link scaling at all (the pre-0.1.41 uniform miss cost), for A/B on links where any scaling moves auto off the balanced placement.
- **STRATA_SPLIT_MISS_MS** — src/program/generate.cpp:5292 (+1 more reads)
  `const double miss_ms = std::getenv("STRATA_SPLIT_MISS_MS") ? std::atof(std::getenv("STRATA_SPLIT_MISS_MS")) : 190.0;`
- **STRATA_SPLIT_MTP_BATCH** — src/program/generate.cpp:10911 (+1 more reads) docs: BATCHING.md, MULTI_GPU.md
  `static const bool split_mtp_batch = strata::program::draft_kv::split_env_on(std::getenv("STRATA_SPLIT_MTP_BATCH"));`
  // STRATA_SPLIT_MTP_BATCH=1 (default off): the layer split's drafter is on the last stage, so E-9 (Prefill::draft_kv) runs there, on the Prefill that ran the chunk, instead of the drafter's own per-8-row pass.  The drafts' K/V come from Q8_1 x Q8_0 MMQ rather than mmvq: drafts may differ, the target's tokens never.
  doc (BATCHING.md): - Off, said once, where the read's thread would allocate or free (`STRATA_PREFILL_HELP=1`, `STRATA_SPLIT_MTP_BATCH=1`),
- **STRATA_SPLIT_NEAR_TIE_PCT** — src/program/generate.cpp:5772 (+1 more reads)
  `const double near_pct = std::getenv("STRATA_SPLIT_NEAR_TIE_PCT") ? std::atof(std::getenv("STRATA_SPLIT_NEAR_TIE_PCT")) : 4.0;`
- **STRATA_SPLIT_OVERLAP** — src/program/generate.cpp:9979 docs: MULTI_GPU.md
  `const char* v = std::getenv("STRATA_SPLIT_OVERLAP");`
  doc (MULTI_GPU.md): | `STRATA_SPLIT_OVERLAP=1` | Overlapped hand-off between stages on different cards. | Helps AMD; no gain on NVIDIA. See [below](#overlapped-hand-off). |
- **STRATA_SPLIT_OWN** — src/program/generate.cpp:3635 docs: MULTI_GPU.md
  `const char* own_env = std::getenv("STRATA_SPLIT_OWN");`
  // split's output differs from 0.1.31's; the default borrows as 0.1.31 did - with the concurrent refill and the 96-blob split ring that alone gave 2K +27%, 16K +5% over 0.1.31, decode unchanged, output identical. STRATA_SPLIT_OWN=auto: the 12% rule above; 1: own buffers on any cards; unset/0: borrow. --split-skip-if-fits keeps the loans (it can fall back to one GPU, which must stay as it is).
  doc (MULTI_GPU.md): | `STRATA_SPLIT_OWN=1` or `auto` | Gives every card its own prompt buffers. `auto` does it only where the buffers are at most 12% of each card's VRAM. | Output differs from the default's (stable and coherent). |
- **STRATA_SPLIT_OWN_BUFFERS** — src/program/generate.cpp:9065 (+1 more reads)
  `const char* v = std::getenv("STRATA_SPLIT_OWN_BUFFERS");`
- **STRATA_SPLIT_OWN_PLACE** — src/program/generate.cpp:5217
  `const char* v = std::getenv("STRATA_SPLIT_OWN_PLACE");`
- **STRATA_SPLIT_RING** — src/program/generate.cpp:9015 docs: MULTI_GPU.md
  `const int ring = strata::program::split_ring_slots(std::getenv("STRATA_SPLIT_RING"), res_share);`
  doc (MULTI_GPU.md): | `STRATA_SPLIT_RING=N` | Sets the prompt path's streamed ring to N slots (`0`: the pinned-share rule). A split uses 96 when at least 75% of the (layer, expert) pairs sit in some card's cache. | The startup line `lend sizing: ...` shows the result. |
- **STRATA_SPLIT_SMALL_MAX** — src/program/generate.cpp:9858
  `const char* vm = std::getenv("STRATA_SPLIT_SMALL_MAX");`
- **STRATA_SPLIT_SMALL_OWN** — src/program/generate.cpp:9856
  `const char* v = std::getenv("STRATA_SPLIT_SMALL_OWN");`
- **STRATA_SPLIT_SPEED_SCALE** — src/program/generate.cpp:5258
  `if (const char* sc = std::getenv("STRATA_SPLIT_SPEED_SCALE"); sc != nullptr && *sc) {`
  // STRATA_SPLIT_SPEED_SCALE="1,0.55": each stage's speed times this factor (a test seam: an unequal pair, e.g. the 4060 Ti + 3060 of #2644, on two equal cards); unset = nothing changes.
- **STRATA_SPLIT_TIMING** — src/program/generate.cpp:17292
  `if (static const bool st_timing = std::getenv("STRATA_SPLIT_TIMING") != nullptr; st_timing)`
  // STRATA_SPLIT_TIMING: where each verify stage's host time went, cumulative per window since the start (waiting for its GPU to ring a layer, the CPU pool and plan per layer, staging the window)
- **STRATA_SPLIT_UNIFORM** — src/program/generate.cpp:5283 docs: MULTI_GPU.md
  `static const bool split_uniform = [] { const char* v = std::getenv("STRATA_SPLIT_UNIFORM"); return v && v[0] == '1'; }();`
  doc (MULTI_GPU.md): `STRATA_SPLIT_UNIFORM=1` (with `"gpu_order": "as_given"`) prices every link the same.
- **STRATA_SSD_GBPS** — src/program/generate.cpp:1479 docs: DETAILS.md
  `if (const char* e = std::getenv("STRATA_SSD_GBPS"); e != nullptr && std::atof(e) > 0.0) {`
  doc (DETAILS.md): and on Windows. `STRATA_PREFILL_HOST_PLAN=0` turns it off; `STRATA_SSD_GBPS` overrides the drive speed;
- **STRATA_SSD_KEEPALIVE** — src/program/generate.cpp:4649
  `const char* ka = std::getenv("STRATA_SSD_KEEPALIVE");`
- **STRATA_SSD_KEEPALIVE_WINDOW** — src/program/generate.cpp:4650
  `const char* kw = std::getenv("STRATA_SSD_KEEPALIVE_WINDOW");`
- **STRATA_STAGE_TRIM** — src/program/generate.cpp:4400 docs: BATCHING.md, MULTI_GPU.md
  `const char* v = std::getenv("STRATA_STAGE_TRIM");`
  doc (BATCHING.md): | `--trim-stage-weights` | with an **explicit** `--layer-split` (e.g. `12,24,36`, not `auto`): every GPU loads only the dense weights of its own layers instead of the whole model's (the same as `STRATA_STAGE_TRIM=1`, PR #639). The VRAM this frees goes to the expert cache. Useful without `--batch` to
- **STRATA_STATE_HASH** — src/program/generate.cpp:16910 docs: SPLIT_SERVE.md
  `static const bool state_hash = std::getenv("STRATA_STATE_HASH") != nullptr;`
  doc (SPLIT_SERVE.md): "State fingerprint" is the engine's `STRATA_STATE_HASH`: the whole session (running state, K/V of every layer, the draft layer's K/V) hashed after
- **STRATA_TAIL_SKIP_MAX_CACHED** — src/program/generate.cpp:11063 docs: DETAILS.md
  `const char* mcs = std::getenv("STRATA_TAIL_SKIP_MAX_CACHED");`
  doc (DETAILS.md): | `STRATA_ROUTE_TAIL_SKIP` (7) | CUDA, and HIP gfx1200/gfx1201; one GPU or a layer split | `STRATA_ROUTE_TAIL_SKIP=0` | A missed expert that every token of a verify window routes at rank 7 or lower is neither copied nor computed. Not applied when every expert is in VRAM, with `--batch` slots, with a
- **STRATA_TEST_BELL_SLEEP_US** — src/program/generate.cpp:15210 docs: BATCHING.md
  `const char* t = std::getenv("STRATA_TEST_BELL_SLEEP_US");`
  doc (BATCHING.md): tick on Windows: the same build with `STRATA_TEST_BELL_SLEEP_US=50` gave the streams 64-67 tok/s during the reads
- **STRATA_TEST_CACHE_FAIL** — src/program/generate.cpp:7101 (+1 more reads)
  `int fake_fails = std::getenv("STRATA_TEST_CACHE_FAIL") ? std::atoi(std::getenv("STRATA_TEST_CACHE_FAIL")) : 0;`
  // high.  A cache sized from it filled the card to 0 MiB, the driver then paged, and a request that needed a page back while the verify graph spun on a host flag never finished.  So the slots are zeroed and the free figure read again; while it is short of the reserve the cache is reopened smaller. STRATA_TEST_CACHE_FAIL=N: the first N opens fail as an out-of-commit cudaMalloc does (tests the retry)
- **STRATA_TEST_CONC_ON_HOST_CPU** — src/program/generate.cpp:15127
  `static const bool conc_on_host = std::getenv("STRATA_TEST_CONC_ON_HOST_CPU") != nullptr;`
- **STRATA_TEST_PINNED_SHARE** — src/program/generate.cpp:8383
  `if (const char* t = std::getenv("STRATA_TEST_PINNED_SHARE")) share = std::atof(t);   // tests: the Windows-like ring rule`
  // tests: the Windows-like ring rule
- **STRATA_TRACE_ADAPT** — src/program/generate.cpp:17961 (+1 more reads)
  `static const bool trace_adapt = std::getenv("STRATA_TRACE_ADAPT") != nullptr;`
  // STRATA_TRACE_ADAPT: why an adapt round did or did not swap.  Default off, one getenv, and it reports the only thing that can make an adapt round a coin flip: whether the PREVIOUS round's asynchronous expert copies had landed by the time this round started.
- **STRATA_WATCHDOG_IO_S** — src/program/generate.cpp:12209
  `const char* wio = std::getenv("STRATA_WATCHDOG_IO_S");`
  // #1407: while the OS is still reading the file tier (major faults / bytes read advance), a silent step is slow, not stuck; it gets up to STRATA_WATCHDOG_IO_S (default 10 x the limit) of such time. 0 = no allowance.
- **STRATA_WATCHDOG_S** — src/program/generate.cpp:12205 docs: DETAILS.md
  `const char* ws = std::getenv("STRATA_WATCHDOG_S");`
  doc (DETAILS.md): | A request ends with `no progress for ... s ... (issue #29)`, with a stall report under it | A request that stops moving ends with an error after 2 minutes, and the next request starts the engine again. `STRATA_WATCHDOG_S` sets the time in seconds (`0` turns it off). Open an issue with the line, th

## src/qwen35
- **STRATA_Q36_BLAS_F32** — src/qwen35/q36_engine.cu:1539
  `static const bool blas_f32 = std::getenv("STRATA_Q36_BLAS_F32") != nullptr;   // the hipBLAS / cuBLAS SGEMM (A/B)`
  // the hipBLAS / cuBLAS SGEMM (A/B)
- **STRATA_Q36_CHUNK** — src/qwen35/q36_engine.cu:3845 docs: QWEN36.md
  `if (const char* cv = std::getenv("STRATA_Q36_CHUNK")) chunk = std::max(256, std::min(4096, std::atoi(cv)));   // force a chunk (512: the old default)`
  // force a chunk (512: the old default)
  doc (QWEN36.md): slower). `--prefill 512` (or `STRATA_Q36_CHUNK=512`) gives the 512 size, and then the text is the base engine's, bit
- **STRATA_Q36_DRAFT_VOCAB** — src/qwen35/q36_engine.cu:3871 (+1 more reads)
  `if (draft_vocab < 0 && std::getenv("STRATA_Q36_DRAFT_VOCAB") != nullptr) draft_vocab = std::atoi(std::getenv("STRATA_Q36_DRAFT_VOCAB"));`
- **STRATA_Q36_FIXED_SLOTS** — src/qwen35/q36_engine.cu:2300 docs: QWEN36.md
  `static const bool off = std::getenv("STRATA_Q36_FIXED_SLOTS") != nullptr;   // the slots as placed (tests)`
  // the slots as placed (tests)
  doc (QWEN36.md): different rounding. With the slot tables fixed (`STRATA_Q36_FIXED_SLOTS=1`, a test setting) every slot equals its solo
- **STRATA_Q36_KEEP_PACKED** — src/qwen35/q36_engine.cu:2827
  `std::getenv("STRATA_Q36_KEEP_PACKED") == nullptr) {`
- **STRATA_Q36_NO_EXT** — src/qwen35/q36_engine.cu:2007
  `const bool ext = one || (fast_k && std::getenv("STRATA_Q36_NO_EXT") == nullptr && !verify_k && T <= kGemmT && g.n_expert == 256 && Kp == 8);`
  // a decode batch of up to 8 rows takes the router and the shared expert's gate in one product too (rows of 257) when the fused router follows; the prompt chunks and the checks keep the separate products
- **STRATA_Q36_NO_MMQ** — src/qwen35/q36_engine.cu:1374
  `use_mmq = MMQ::built() && std::getenv("STRATA_Q36_NO_MMQ") == nullptr;`
- **STRATA_Q36_NO_MTP_CPU** — src/qwen35/q36_engine.cu:2824 (+1 more reads)
  `const bool mtp_cpu_ok = m.has_mtp && std::getenv("STRATA_Q36_NO_MTP_CPU") == nullptr;`
- **STRATA_Q36_OLD_KERNELS** — src/qwen35/q36_engine.cu:1577 docs: QWEN36.md
  `bool fast_k = std::getenv("STRATA_Q36_OLD_KERNELS") == nullptr;`
  // ---- decode kernels of this engine (q36_kernels.cuh), each the old kernel's bits (STRATA_Q36_VERIFY=1 compares)
  doc (QWEN36.md): kernel beside each new one on the real activations and compares them bit for bit. `STRATA_Q36_OLD_KERNELS=1` switches
- **STRATA_Q36_PLACE_DEBUG** — src/qwen35/q36_engine.cu:3846
  `if (std::getenv("STRATA_Q36_PLACE_DEBUG"))`
- **STRATA_Q36_READ_WINDOWS** — src/qwen35/q36_engine.cu:3181 docs: QWEN36.md
  `if (const char* v = std::getenv("STRATA_Q36_READ_WINDOWS")) read_windows = std::max(0, std::min(64, std::atoi(v)));`
  doc (QWEN36.md): `STRATA_Q36_READ_WINDOWS=4` lets the decoding slots produce more tokens during a long prompt read, at the cost of a
- **STRATA_Q36_STREAM_ALL** — src/qwen35/q36_engine.cu:2181
  `static const bool all = std::getenv("STRATA_Q36_STREAM_ALL") != nullptr;`
  // the experts with a VRAM slot come from it (device to device, at VRAM speed), only the others over PCIe; runs of consecutive experts from the same source in one copy each.  STRATA_Q36_STREAM_ALL=1: the whole layer from host memory (the first version: PCIe-bound)
- **STRATA_Q36_VDEBUG** — src/qwen35/q36_engine.cu:1639
  `if (v_bad != before && std::getenv("STRATA_Q36_VDEBUG") && v_by[what] <= 2) {   // a mismatching block, on the host`
  // a mismatching block, on the host
- **STRATA_Q36_VERIFY** — src/qwen35/q36_engine.cu:1578 docs: QWEN36.md
  `bool verify_k = std::getenv("STRATA_Q36_VERIFY") != nullptr;`
  doc (QWEN36.md): Every change on the decode path gives the old kernels' bits. `STRATA_Q36_VERIFY=1 strata ... --no-graph` runs the old
