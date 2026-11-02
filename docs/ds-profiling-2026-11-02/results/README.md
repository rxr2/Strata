# Results — summary tables and logs

The detailed tables and the interpretation are in `../reports/`. This directory keeps the analyzer outputs
and the gate results so a number can be checked without re-running the engine.

| file | what |
|---|---|
| `ab_result.txt` | q6 draft-vocabulary sweep 106k/140k/180k/248k, 3 random blocks, per class and overall |
| `q4_result.txt` | q4 head sweep 106k/q4-140/q4-180/q4-248, 3 blocks, acceptance/deltas |
| `tailr_result.txt` | `STRATA_ROUTE_TAIL_SKIP=7` randomized 3-block A/B: **86.94 → 94.93 tok/s (+9.19% ±2.79)** |
| `tail_final_result.txt` | the tail-skip collector: random A/B, profiled stages, quality, D runs |
| `quality-tail7.txt` | tail skip alone, 32-prompt KL/top-1 (KL 0.02177, top-1 29/32) |
| `quality-tail-combined.txt` / `.json` | deployed q4-140 + tail7, 32 prompts (KL 0.01747, top-1 29/32) |
| `prefill-ds.txt` / `.json` | prefill 12K/32K/64K (2679/2951/3057 tok/s) |
| `tail-stage-base-p1..p3.txt` | profiled base, stages |
| `tail-stage-tail-p1..p3.txt` | profiled tail7, stages (PCIe rows −36..43%, CPU pool −34..38%) |
| `tail-vram.txt` | `rocm-smi` VRAM snapshot before the reserve test |
| `microbench-launch.txt` | empty dependent-kernel floor, graph/stream, ROCm env variants, copy-rows shapes |

Raw runner logs (names/timestamps, not the 150 MB profiler traces): `../tests/logs/`.
Raw per-request JSON and engine logs are local under `~/rx-perf-lab/suite/<time>-NAME/` (not in this repo).
