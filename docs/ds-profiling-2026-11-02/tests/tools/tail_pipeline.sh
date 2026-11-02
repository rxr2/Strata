#!/bin/bash
# Finish the tail-skip task after the randomized A/B: profiled pair, quality gate, D point if >=3%.
set -u
cd /tmp/opencode
LOG=/tmp/opencode/tail_pipeline.log
echo "PIPE start $(date +%T)" > $LOG

# 1. wait for the randomized sweep (it is a nohup child; bounded)
for i in $(seq 1 120); do
  grep -q DONE /tmp/opencode/tailr_sweep.log 2>/dev/null && break
  sleep 10
done
python3 /tmp/opencode/tailr_analyze.py > /tmp/opencode/tailr_result.txt 2>&1
cat /tmp/opencode/tailr_result.txt >> $LOG

# 2. profiled pair (base vs tail7)
cd /home/rxr2/Projekty/coding-bench/pipeline
B=$(./trace_run.sh tailbase-prof EXE=prod 2>>$LOG | tail -1)
T=$(./trace_run.sh tail7-prof EXE=prod STRATA_ROUTE_TAIL_SKIP=7 2>>$LOG | tail -1)
echo "prof base $B" >> $LOG; echo "prof tail $T" >> $LOG
for p in p1 p2 p3; do
  python3 stages.py "$B/$p" > /tmp/opencode/tail-stage-base-$p.txt 2>&1
  python3 stages.py "$T/$p" > /tmp/opencode/tail-stage-tail-$p.txt 2>&1
done

# 3. quality gate (default fork build, as the task says)
cd /home/rxr2/Projekty/strata-rx7900
./rx-tools/bench-detached.sh tail7 quality STRATA_ROUTE_TAIL_SKIP=7 > /tmp/opencode/tail-quality-start.txt 2>&1
for i in $(seq 1 120); do
  systemctl --user is-active rx-bench-tail7 | grep -q inactive && break
  sleep 5
done
Q=$(ls -dt /home/rxr2/rx-perf-lab/experiments/fork/*tail7 2>/dev/null | head -1)
cp "$Q/RESULT.txt" /tmp/opencode/tail-quality-result.txt 2>/dev/null
echo "quality $Q" >> $LOG
cat /tmp/opencode/tail-quality-result.txt >> $LOG 2>/dev/null

# 4. D point only if the randomized A/B mean is >= 3%
GAIN=$(awk '/^OVERALL/ {gsub("%","",$4); print $4}' /tmp/opencode/tailr_result.txt | head -1)
echo "gain $GAIN" >> $LOG
if awk -v g="$GAIN" 'BEGIN {exit !(g+0 >= 3.0)}'; then
  rocm-smi --showmeminfo vram > /tmp/opencode/tail-vram.txt 2>&1 || true
  bash /tmp/opencode/tail_d_sweep.sh >> $LOG 2>&1
else
  echo "SKIP D: gain $GAIN < 3" >> $LOG
fi
echo "PIPE done $(date +%T)" >> $LOG
