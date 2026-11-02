#!/bin/bash
set -u
cd /tmp/opencode
while read -r b s; do
  case "$s" in
    106) V="";;
    q4-140) V="ARG--mtp-draft-vocab=/tmp/opencode/draft_vocab_140k.bin ARG--mtp-q4=head";;
    q4-180) V="ARG--mtp-draft-vocab=/tmp/opencode/draft_vocab_180k.bin ARG--mtp-q4=head";;
    q4-248) V="ARG--mtp-draft-vocab=/tmp/opencode/draft_vocab_248k.bin ARG--mtp-q4=head";;
  esac
  echo "=== $s-b$b $(date +%T)" >> /tmp/opencode/q4_sweep.log
  ./suite_run.sh "${s}-b${b}" EXE=/home/rxr2/Projekty/strata-rx7900-ds/build-rx/strata $V >> /tmp/opencode/q4_sweep.log 2>&1
done < /tmp/opencode/q4_order.txt
echo "DONE $(date +%T)" >> /tmp/opencode/q4_sweep.log
