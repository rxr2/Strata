#!/bin/bash
set -u
cd /tmp/opencode
while read -r b s; do
  if [ "$s" = "base" ]; then V=""; N="tailr-base-${b}"; else V="STRATA_ROUTE_TAIL_SKIP=7"; N="tailr-tail7-${b}"; fi
  echo "=== $N $(date +%T)" >> /tmp/opencode/tailr_sweep.log
  ./suite_run.sh "$N" EXE=prod $V >> /tmp/opencode/tailr_sweep.log 2>&1
done < /tmp/opencode/tailr_order.txt
echo "DONE $(date +%T)" >> /tmp/opencode/tailr_sweep.log
