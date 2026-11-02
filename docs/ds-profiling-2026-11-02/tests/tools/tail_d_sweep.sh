#!/bin/bash
# D-point runs for STRATA_ROUTE_TAIL_SKIP, after the randomized 3-block A/B. Run only if tail7 >= 3%.
set -u
cd /tmp/opencode
R="STRATA_ROUTE_TAIL_SKIP"
# (1) R=6 and R=8, one pair each against the tail7=7 mean
./suite_run.sh tailr6-1  EXE=prod $R=6 >> /tmp/opencode/tail_d.log 2>&1
./suite_run.sh tailr8-1  EXE=prod $R=8 >> /tmp/opencode/tail_d.log 2>&1
# (2) pcie-frac 0.10 and 0.30 (0.20 is the tail7 base)
./suite_run.sh tailp10-1 EXE=prod $R=7 ARG--pcie-frac=0.10 >> /tmp/opencode/tail_d.log 2>&1
./suite_run.sh tailp30-1 EXE=prod $R=7 ARG--pcie-frac=0.30 >> /tmp/opencode/tail_d.log 2>&1
# (3) q4-140 with and without tail7 (sum check; production binary)
./suite_run.sh tailq4-1  EXE=prod ARG--mtp-draft-vocab=/tmp/opencode/draft_vocab_140k.bin ARG--mtp-q4=head >> /tmp/opencode/tail_d.log 2>&1
./suite_run.sh tailq4t-1 EXE=prod ARG--mtp-draft-vocab=/tmp/opencode/draft_vocab_140k.bin ARG--mtp-q4=head $R=7 >> /tmp/opencode/tail_d.log 2>&1
# (4) reserve 2048 vs 3072 with tail7, back to back (NOT below 1500; 2 monitors)
./suite_run.sh tailres3072-1 EXE=prod $R=7 >> /tmp/opencode/tail_d.log 2>&1
./suite_run.sh tailres2048-1 EXE=prod $R=7 ARG--vram-reserve-mib=2048 >> /tmp/opencode/tail_d.log 2>&1
echo DONE >> /tmp/opencode/tail_d.log
