#!/bin/bash
set -u
cd /tmp/opencode
while read -r b s; do
  if [ "$s" = "106" ]; then V=""; else V="ARG--mtp-draft-vocab=/tmp/opencode/draft_vocab_${s}k.bin"; fi
  echo "=== ab${s}-${b} $(date +%T)" >> /tmp/opencode/ab_sweep.log
  ./suite_run.sh "ab${s}-${b}" EXE=/home/rxr2/Projekty/strata-rx7900-ds/build-rx/strata $V >> /tmp/opencode/ab_sweep.log 2>&1
done < /tmp/opencode/ab_order.txt
echo "DONE $(date +%T)" >> /tmp/opencode/ab_sweep.log
