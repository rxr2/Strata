#!/usr/bin/env bash
# rx-tools/test.sh [REGEX] - run this fork's parity tests (build them first: rx-tools/build.sh --tests).
# Default: the quick GPU parity set for the kernels the fork touches. The production server keeps running, so only
# ~3 GB of VRAM is free: a test that runs out of memory is reported, not retried.
set -uo pipefail
SRC=$(cd "$(dirname "$0")/.." && pwd); B=$SRC/build-rx-tests
[ -d "$B" ] || { echo "no test build: run rx-tools/build.sh --tests"; exit 2; }
RE=${1:-'^(gr_parity|gr_multi_parity|mmvq_il_parity|mmvq_multi_parity|gdn_parity|qsa_scores_parity|qsa_slots_parity)$'}
cd "$B" && HIP_VISIBLE_DEVICES=0 ctest -R "$RE" --output-on-failure --timeout 600 -j1 2>&1 | tee "$B/ctest-last.log" | tail -40
exit "${PIPESTATUS[0]}"
