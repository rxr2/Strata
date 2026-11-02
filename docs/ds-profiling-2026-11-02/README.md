# RX 7900 XTX / Strata — profiling and tuning (2026-11-02)

This directory is the evidence package for the Strata (HIP) decode work on one Radeon RX 7900 XTX (gfx1100, 24 GB),
Qwen3.8-Flash-Next IQ3_S (MoE, 48 layers, 512 experts, top-10), TheRock ROCm 10.1, engine 0.1.52. It contains the
reports, the test harness, the raw summary tables and the production config snapshot. The long raw traces are **not**
included (see [Raw data](#raw-data)).

## Current production state (after the tests)

`~/llm/strata/strata-rx.json` was changed on 2026-11-02 with a backup and the owner's instruction:

- `env.STRATA_ROUTE_TAIL_SKIP=7`
- `--mtp-draft-vocab /home/rxr2/llm/Strata-data/mtp/vocab/draft_vocab_140k.bin` (the q4 head vocabulary)
- `--mtp-q4 head`
- unchanged: `--pcie-frac 0.20`, `--vram-reserve-mib 3072`, `--spec-min-p 0.85`, the rest.

Measured on the production server after the change (3 fixed prompts, 320 tokens, greedy, seed 7):

| prompt | tok/s | old config |
|---|---:|---:|
| p1 explain | 96.9 | 99.9 |
| p2 code | 112.7 | 107.2 |
| p3 Polish | 87.6 | 75.4 |
| **mean** | **99.07** | **94.2** |

Suite (10 classes × 192 tokens) with q4-140 + tail skip: **104.71 tok/s** in one run (single, not 3 pairs).
Combined quality gate (prod, 32 prompts): **KL 0.01747**, **top-1 29/32** (base 0.01640 / 30/32).
The top-1 is one prompt below the 30/32 gate; this is the accepted trade (owner decision).

Rollback:

```sh
cp -p ~/llm/strata/strata-rx.json.bak-20261102-143040 ~/llm/strata/strata-rx.json
systemctl --user restart strata-rx
```

The before/after snapshots are in `config/` (`strata-rx.before.json` SHA-256 `97a10dbd…`, `strata-rx.after.json`
`66583d89…`). The vocabulary used by the config is `assets/draft_vocab_140k.bin`.

## Key results

| lever | measured effect | confidence |
|---|---:|---|
| Full profile (3 traces, profiler) | p1 84.8 / p2 83.5 / p3 65.9 tok/s; window 25.8–28.8 ms; 87 / 85 / 79% cache | measured |
| Graph node floor | 2.5–3.2 µs per dependent kernel; graph = stream; no ROCm env lowers it | measured |
| `spec_min_p` 0.85 → 0.65–0.90 | ±1% (plateau); 0.55 −3.5% | measured |
| Draft vocabulary 106k → 140k/180k (q6) | +2.80% ±1.88 / +2.80% ±2.63; 248k +1.64% | 3 blocks |
| **q4 head, 140k/180k** | **+6.75% ±3.47 / +6.76% ±4.15**; q4-248 +3.96% | 3 blocks |
| **`STRATA_ROUTE_TAIL_SKIP=7`** | **+9.19% ±2.79** (3/3 blocks +6.59/+8.84/+12.14); skips 37% of would-be misses | 3 blocks |
| Tail skip quality | KL 0.02177 (base 0.01640) ≤ 0.0235; top-1 29/32 < 30/32; prose −8.7%, JSON output shorter | measured |
| q4-140 + tail7 | 104.71 tok/s (single); q4-140 alone 92.86, tail7 alone 94.93 | single |
| pcie-frac 0.30 + tail7 | 98.32 (single) vs 94.93 at 0.20; 0.10 94.21 | single |
| R=6 / R=8 | 101.64 / 91.97 (single; R=6 quality not gated) | single |
| reserve 2048 + tail7 | 90.67 vs 97.89 at 3072 → **do not lower** | single |
| Prefill 12K/32K/64K | 2679 / 2951 / 3057 tok/s; 160.9 GB drive reads / 9 requests | measured |
| Training MTP head | not done (owner decision: no rental/training); feasibility in `reports/FEASIBILITY-ds-mtp-training.md` | note |

## Contents

- `reports/`
  - `REPORT-ds-profiling.md` — full current profile, stage/kernel tables, Tor A (acceptance), Tor B (cache).
  - `REPORT-ds-tailskip.md` — the tail-skip A/B, profiled mechanism, quality gate, D runs, **deployment**.
  - `SWEEP-ds-vocab.md` — 106k/140k/180k/248k q6 + q4 head sweeps, head cost/bytes, two-stage estimate.
  - `CEILING-ds-mtp.md` — top-K of the draft head vs the verified token; the ceiling.
  - `DRAFT-VOCAB-ds.md` — the third arm (main head restricted to the draft vocabulary).
  - `FEASIBILITY-ds-mtp-training.md` — memory, dump size, data/privacy, PyTorch ROCm/CUDA, time.
  - `KNOWLEDGE.md` — the running knowledge base (the ds pipeline).
- `prompts/` — the two task prompts (`PROMPT-ds-profiling.md`, `PROMPT-ds-tailskip.md`).
- `reference/SWITCHES.md` — the 658 Strata switches with source locations (the harness KB).
- `archive/` — the earlier `REPORT-ds-pro.md`, the loop knowledge and the experiment ledger.
- `tests/` — the harness used for every number:
  - `tests/tools/` — `suite_run.sh` (temporary engine + 10-class suite), `live_matrix*.py` (per-request
    `strata_tune`), analyzers (`ab_analyze.py`, `q4_analyze.py`, `tailr_analyze.py`, `tail_final_analyze.py`),
    the sweep runners, the order files.
  - `tests/pipeline/` — `trace_run.sh`, `stages.py`, `pipeline_map.py`, `rep_table.py`, `stage_table.py`,
    `suite_prompts.json`.
  - `tests/logs/` — the runner logs (not the 150 MB profiler traces).
- `results/` — the analyzer outputs, quality results, prefill result, profiled stage tables, VRAM snapshot.
- `config/` — the production config before/after the deployment and notes.
- `assets/` — the draft vocabularies used/tested (140k, 180k, 248k, PL-specific) and the trained profile test.

## Reproduction

Prerequisites: the RX 7900 XTX, TheRock ROCm 10.1, Strata 0.1.52 + the fork, the model pack, and the harness at
`~/Projekty/coding-bench` + `~/rx-perf-lab`. The scripts contain the original local paths; adapt them.

```sh
# A/B on the 10-class suite (temp engine, NOPROF; restores production)
PROMPTS=.../suite_prompts.json tests/tools/suite_run.sh NAME EXE=prod [ARG--flag=value] [STRATA_KEY=1]
# profile one pair
tests/pipeline/trace_run.sh NAME EXE=prod [STRATA_ROUTE_TAIL_SKIP=7]
python3 tests/pipeline/stages.py ~/rx-perf-lab/pipeline/<time>-NAME/p1
# quality gate (the fork's rx-tools)
~/Projekty/strata-rx7900/rx-tools/bench-detached.sh NAME quality STRATA_ROUTE_TAIL_SKIP=7
# analyzers
python3 tests/tools/ab_analyze.py ; python3 tests/tools/q4_analyze.py
python3 tests/tools/tailr_analyze.py ; python3 tests/tools/tail_final_analyze.py
```

The q4 vocabulary must be passed as `ARG--mtp-draft-vocab=<assets/draft_vocab_140k.bin>` and
`ARG--mtp-q4=head`; the production binary supports both (0.1.52). `suite_run.sh` starts a temporary server,
stops/restores production, and writes `~/rx-perf-lab/suite/<time>-NAME/` (`requests.jsonl`, `strata.log`,
`engine-tail.log`).

**Raw data:** the profiler traces (`trace.db` 150–166 MB each, three runs) and the per-run engine logs are local
at `~/rx-perf-lab/pipeline/20261102-1024…-prof-base-1..3` and `~/rx-perf-lab/suite/…`; they are not in this repo
(size). The summary tables in `results/` and the reports are derived from them.

## Caveats

- All A/B are 3 blocks/10 classes/192 tokens unless stated; D runs are single (noise 2–4%).
- The q4 head changed the end-to-end text in 6–8/10 classes (cache/adaptation path); the combined quality gate
  was measured after deployment (KL 0.01747, top-1 29/32). The q4 head is a drafter; the verifier stays on the
  target's Q6_K head.
- The tail skip changes the output by design (skips low-rank missed experts); prose loses ~9%, JSON output is
  shorter; the top-1 gate is missed by one prompt. The owner accepted the trade when asking to deploy.
- No engine code was changed for the tail skip; the only code in this branch is the **diagnostics**
  (`STRATA_HIT_STATS`, `STRATA_MTP_TOPK`), default off. The production binary/config change is the tail skip +
  q4 vocab/head.
- The training note is a feasibility study only; nothing was trained or rented.

## Code

Branch `rx-ds-profile` (this branch), commits:

- `cbe4a12e` — `STRATA_HIT_STATS=1`: routed entries per layer by lane.
- `541df347` — `STRATA_MTP_TOPK=K`: the draft head's top-K vs the verified token.
- `ae2f3fdb` — top-1 probability histogram for the two-stage draft estimate.

Diagnostics are off by default and do not touch the production path.
