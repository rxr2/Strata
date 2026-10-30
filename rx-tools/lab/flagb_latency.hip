// T05: latency of "an expert upload landed" on ROCm: hipLaunchHostFunc (the engine's flag B today) vs
// hipStreamWriteValue32 into mapped host memory, after a 2.1 MiB pinned H2D copy. usage: ./flagb [iters]
#include <hip/hip_runtime.h>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <vector>
#include <algorithm>
#include <atomic>
#define CK(x) do { hipError_t e = (x); if (e != hipSuccess) { std::printf("%s: %s\n", #x, hipGetErrorString(e)); return 1; } } while (0)
using C = std::chrono::steady_clock;
static std::atomic<uint32_t> g_flag{0};
static void host_fn(void* p) { g_flag.store((uint32_t) (uintptr_t) p, std::memory_order_release); }
int main(int argc, char** argv) {
    const int iters = argc > 1 ? std::atoi(argv[1]) : 200;
    const size_t bytes = 2200000;
    void *h, *d; uint32_t* hflag; void* dflag;
    CK(hipHostMalloc(&h, bytes, hipHostMallocDefault));
    CK(hipMalloc(&d, bytes));
    CK(hipHostMalloc((void**) &hflag, 64, hipHostMallocMapped | hipHostMallocCoherent));
    CK(hipHostGetDevicePointer(&dflag, hflag, 0));
    hipStream_t s; CK(hipStreamCreateWithFlags(&s, hipStreamNonBlocking));
    std::vector<double> copy_only, hf, wv;
    for (int mode = 0; mode < 3; ++mode)
        for (int i = 0; i < iters + 10; ++i) {
            *(volatile uint32_t*) hflag = 0; g_flag.store(0);
            const uint32_t want = i + 1;
            auto t0 = C::now();
            CK(hipMemcpyAsync(d, h, bytes, hipMemcpyHostToDevice, s));
            if (mode == 0) { CK(hipStreamSynchronize(s)); }
            else if (mode == 1) { CK(hipLaunchHostFunc(s, host_fn, (void*) (uintptr_t) want)); while (g_flag.load(std::memory_order_acquire) != want) {} }
            else { CK(hipStreamWriteValue32(s, dflag, want, 0)); while (*(volatile uint32_t*) hflag != want) {} }
            const double us = std::chrono::duration<double, std::micro>(C::now() - t0).count();
            if (i >= 10) (mode == 0 ? copy_only : mode == 1 ? hf : wv).push_back(us);
            CK(hipStreamSynchronize(s));
        }
    auto rep = [](const char* n, std::vector<double> v) {
        std::sort(v.begin(), v.end());
        std::printf("%-28s median %7.1f us  p10 %7.1f  p90 %7.1f\n", n, v[v.size() / 2], v[v.size() / 10], v[v.size() * 9 / 10]);
    };
    rep("copy + stream sync", copy_only); rep("copy + hipLaunchHostFunc", hf); rep("copy + hipStreamWriteValue32", wv);
    return 0;
}
