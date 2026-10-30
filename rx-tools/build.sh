#!/usr/bin/env bash
# rx-tools/build.sh - build the Strata engine of this fork for the RX 7900 XTX (gfx1100) with TheRock ROCm 10.1.
#   rx-tools/build.sh            portable build (AVX2 baseline, like the official rx7900 package) -> build-rx/strata
#   rx-tools/build.sh --native   -march=native (Zen 5, AVX-512)                                   -> build-rx-native/strata
#   rx-tools/build.sh --tests    also the parity tests                                           -> build-rx-tests/
# Flags follow packaging/build_hip_linux.sh (VARIANT=rx7900). The binary finds TheRock's libraries through its RUNPATH.
# TheRock headers go first (-isystem): the system HIP 7.1 in /usr/include would otherwise win for the .cu files.
# Log: <build dir>/build.log. Exit code != 0 when the build fails.
set -euo pipefail
SRC=$(cd "$(dirname "$0")/.." && pwd)
HP=${HP:-$HOME/opt/rocm-10.1.0}
LLAMA=${LLAMA:-$HOME/Projekty/third_party/llama.cpp-3cf0325}
JOBS=${JOBS:-14}
MODE=portable; TESTS=OFF
for a in "$@"; do case "$a" in --native) MODE=native;; --tests) TESTS=ON;; *) echo "unknown option $a" >&2; exit 64;; esac; done
OUT=$SRC/build-rx; [ "$MODE" = native ] && OUT=$SRC/build-rx-native; [ "$TESTS" = ON ] && OUT=$SRC/build-rx-tests
PORT=ON; EXTRA=(); [ "$MODE" = native ] && { PORT=OFF; EXTRA=("-DCMAKE_CXX_FLAGS=-march=native" "-DCMAKE_C_FLAGS=-march=native"); }
export HIP_PLATFORM=amd HIP_COMPILER=clang HIP_RUNTIME=rocclr ROCM_PATH=$HP HIP_PATH=$HP
SYS=""; [ -d "$HP/lib/rocm_sysdeps" ] && SYS=";$HP/lib/rocm_sysdeps"
mkdir -p "$OUT"
cmake -G Ninja -S "$SRC" -B "$OUT" -DCMAKE_BUILD_TYPE=Release -DSTRATA_ENABLE_HIP=ON -DSTRATA_ENABLE_CUDA=OFF \
  -DSTRATA_BUILD_TESTS=$TESTS -DSTRATA_PREFILL_MMQ=ON -DSTRATA_PORTABLE=$PORT "-DCMAKE_HIP_ARCHITECTURES=gfx1100" \
  -DCMAKE_HIP_COMPILER="$HP/llvm/bin/clang++" -DCMAKE_HIP_COMPILER_ROCM_ROOT="$HP" "-DCMAKE_PREFIX_PATH=$HP$SYS" \
  "-DCMAKE_HIP_FLAGS=--rocm-path=$HP --rocm-device-lib-path=$HP/lib/llvm/amdgcn/bitcode -isystem $HP/include" \
  -DSTRATA_GGML_DIR="$LLAMA" -DCMAKE_C_COMPILER_LAUNCHER=ccache -DCMAKE_CXX_COMPILER_LAUNCHER=ccache \
  -DCMAKE_HIP_COMPILER_LAUNCHER=ccache "${EXTRA[@]}" \
  "-DCMAKE_EXE_LINKER_FLAGS=-Wl,-rpath,$HP/lib:$HP/lib/rocm_sysdeps/lib -Wl,--enable-new-dtags" > "$OUT/configure.log" 2>&1 \
  || { echo "configure failed: $OUT/configure.log"; tail -20 "$OUT/configure.log"; exit 1; }
T=strata; [ "$TESTS" = ON ] && T=all
start=$SECONDS
nice -n 10 cmake --build "$OUT" --target $T -j "$JOBS" > "$OUT/build.log" 2>&1 \
  || { echo "build failed after $((SECONDS-start)) s: $OUT/build.log"; grep -m 20 -E "error:|FAILED:" "$OUT/build.log"; exit 1; }
# the hipBLASLt tuning tables beside the binary (what packaging/stage_tuning.py does): without the table for this
# hipBLASLt version (TheRock 10.1: 100401) the prompt's dense GEMMs fall back to plain hipBLAS, ~5x slower (measured)
mkdir -p "$OUT/tuning" && cp -p "$SRC"/tools/hip/gfx1100-hipblaslt-*.txt "$OUT/tuning/"
echo "build ok ($MODE, tests=$TESTS) in $((SECONDS-start)) s: $OUT/strata (tuning: $(ls "$OUT/tuning" | tr '\n' ' '))"
ls -la "$OUT/strata" 2>/dev/null || true
