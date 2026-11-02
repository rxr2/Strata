# Test harness used for the RX 7900 XTX numbers

These are the exact scripts used on the machine (2026-11-02). They contain the original local paths
(`~/Projekty/coding-bench`, `~/rx-perf-lab`, `/tmp/opencode`); adapt them for another box. The engine, model,
ROCm and the production `strata-rx.json` are not included.

## Tools

- `tools/suite_run.sh NAME [EXE=prod|<path>] [ARG--flag=value] [KEY=VALUE] [LIVE=1] [MATRIX=1 ...]`
  Stops production, starts a temporary server from a copy of the production config, sends `PROMPTS`
  (default `tests/pipeline/suite_prompts.json`: 10 classes × 192 tokens), writes `~/rx-perf-lab/suite/<time>-NAME/`
  (`requests.jsonl`, `strata.log`, `engine-tail.log`, `cfg.json`) and **always restores production**.
  `NOPROF` is implicit (the server's own timings); `LIVE=1` uses the running server; `MATRIX=1` runs
  `live_matrix.py` (`MATRIX_SCRIPT` selects another matrix, `REPS=3`).
- `tools/live_matrix.py`, `live_matrix_spec.py`, `live_matrix_high.py` — per-request `strata_tune.spec_min_p` /
  `pcie_frac` on the live server; no restart.
- `tools/suite_analyze.py` — joins `requests.jsonl` with `engine-tail.log` (tok/s, T, tokens/window, acceptance,
  hit rate).
- `tools/ab_analyze.py`, `q4_analyze.py`, `tailr_analyze.py`, `tail_final_analyze.py` — the size/q4/tail A/B
  summaries (`OVERALL`, per-class, SD).
- `tools/ab_sweep.sh`, `q4_sweep.sh`, `tailr_sweep.sh`, `tail_d_sweep.sh`, `tail_pipeline.sh` — the run orders
  and the post-processing; adapt the names/paths.
- `pipeline/trace_run.sh NAME [EXE=prod] [ARG--flag=value] [KEY=VALUE]` — the same 3 fixed prompts under
  `rocprofv3 --kernel-trace`; stops/restores production.
- `pipeline/stages.py RUN/p1` — stage/balance table from a trace; `pipeline_map.py`, `rep_table.py`,
  `stage_table.py` — kernel/layer maps and repeated-run tables.

## Typical commands

```sh
# size sweep (106k = no arg; 140k/180k/248k from assets)
tests/tools/suite_run.sh s140-b1 EXE=prod ARG--mtp-draft-vocab=assets/draft_vocab_140k.bin
# q4 head
tests/tools/suite_run.sh q4-140-b1 EXE=prod ARG--mtp-draft-vocab=assets/draft_vocab_140k.bin ARG--mtp-q4=head
# tail skip
tests/tools/suite_run.sh tail7-b1 EXE=prod STRATA_ROUTE_TAIL_SKIP=7
# profiled pair
tests/pipeline/trace_run.sh tail7-prof EXE=prod STRATA_ROUTE_TAIL_SKIP=7
python3 tests/pipeline/stages.py ~/rx-perf-lab/pipeline/<time>-tail7-prof/p1
# quality gate (fork's rx-tools)
~/Projekty/strata-rx7900/rx-tools/bench-detached.sh NAME quality STRATA_ROUTE_TAIL_SKIP=7
```

The scripts assume the server on `127.0.0.1:8081`, the systemd unit `strata-rx`, and the model/config paths
of the original machine. The `flock ~/Projekty/coding-bench/.grade.lock` is used by the microbenchmarks; the
`trace_run.sh`/`suite_run.sh` stop production instead.

## Result layout

`requests.jsonl` has one JSON per prompt (`timings`, `usage`, `text`); `strata.log` is the engine log with the
`decode timing` lines, cache hits, `route tail skip` counters and, when enabled, `mtp topk` lines. The analyzer
scripts drop the warm-up request and print the tables used in the reports.
