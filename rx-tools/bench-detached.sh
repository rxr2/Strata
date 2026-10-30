#!/usr/bin/env bash
# rx-tools/bench-detached.sh NAME MODE [KEY=VALUE ...] - measure a fork build on the production server, detached from
# the caller (systemd-run --user): a coding agent that runs on this same RX model can start it and finish its turn.
#   NAME   a label for the run (letters, digits, -, _)
#   MODE   prefill (12K/32K/64K) | decode (5K/64K, 512 tokens) | quality (first token + agent tasks) | all
#   EXE=<path to strata>   the binary to measure (default: this fork's build-rx/strata); EXE=prod measures production
#   ARG--flag=VALUE        replace (or add) an engine argument, e.g. ARG--prefill=auto:16384
#   any other KEY=VALUE    an extra engine environment variable
# What it does: copies the production config, writes a test config (exe, TheRock libraries, env), restarts strata-rx,
# runs the benchmark, ALWAYS restores the production config and restarts strata-rx again.
# Results: ~/rx-perf-lab/experiments/fork/<time>-NAME/ (RESULT.txt when done). Status: systemctl --user status rx-bench-NAME
set -euo pipefail
NAME=${1:?NAME}; MODE=${2:?MODE}; shift 2
[[ $NAME =~ ^[A-Za-z0-9_-]+$ ]] || { echo "bad NAME"; exit 64; }
[[ $MODE =~ ^(prefill|decode|quality|all)$ ]] || { echo "bad MODE"; exit 64; }
SRC=$(cd "$(dirname "$0")/.." && pwd)
OUT=$HOME/rx-perf-lab/experiments/fork/$(date +%Y%m%d-%H%M%S)-$NAME
mkdir -p "$OUT"
printf '%s\n' "$@" > "$OUT/args.txt"
systemd-run --user --unit="rx-bench-$NAME" --collect --quiet \
  --setenv=SRC="$SRC" --setenv=OUT="$OUT" --setenv=MODE="$MODE" \
  /bin/bash "$SRC/rx-tools/bench-run.sh"
echo "started rx-bench-$NAME (detached); results will be in $OUT/RESULT.txt"
