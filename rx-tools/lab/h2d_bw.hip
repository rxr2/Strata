// H2: host<->device bandwidth on the RX 7900 XTX, the way Strata copies experts (pinned host memory, async copies).
// build: hipcc -O2 --offload-arch=gfx1100 h2d_bw.hip -o h2d_bw      run: ./h2d_bw [MiB=256] [reps=8]
#include <hip/hip_runtime.h>
#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <vector>

#define CK(x) do { hipError_t e = (x); if (e != hipSuccess) { std::printf("%s: %s\n", #x, hipGetErrorString(e)); std::exit(1); } } while (0)

static double run(void* dst, const void* src, size_t bytes, hipMemcpyKind kind, int reps, hipStream_t s, size_t chunk) {
    hipEvent_t a, b;
    CK(hipEventCreate(&a)); CK(hipEventCreate(&b));
    std::vector<double> gbs;
    for (int r = 0; r < reps + 1; ++r) {          // first rep: warm-up
        CK(hipEventRecord(a, s));
        for (size_t off = 0; off < bytes; off += chunk)
            CK(hipMemcpyAsync((char*) dst + off, (const char*) src + off, std::min(chunk, bytes - off), kind, s));
        CK(hipEventRecord(b, s)); CK(hipEventSynchronize(b));
        float ms = 0; CK(hipEventElapsedTime(&ms, a, b));
        if (r) gbs.push_back(bytes / (ms * 1e6));
    }
    std::sort(gbs.begin(), gbs.end());
    CK(hipEventDestroy(a)); CK(hipEventDestroy(b));
    return gbs[gbs.size() / 2];
}

int main(int argc, char** argv) {
    const size_t mib = argc > 1 ? std::atoi(argv[1]) : 256, bytes = mib << 20;
    const int reps = argc > 2 ? std::atoi(argv[2]) : 8;
    hipDeviceProp_t p; CK(hipGetDeviceProperties(&p, 0));
    std::printf("device 0: %s (%s), buffer %zu MiB, median of %d\n", p.name, p.gcnArchName, mib, reps);
    void *d, *hp, *hu; hipStream_t s;
    CK(hipMalloc(&d, bytes)); CK(hipHostMalloc(&hp, bytes, hipHostMallocDefault)); CK(hipStreamCreate(&s));
    hu = std::malloc(bytes);
    for (size_t i = 0; i < bytes; i += 4096) { ((char*) hp)[i] = 1; ((char*) hu)[i] = 1; }
    const size_t chunks[] = {bytes, 16u << 20, 4u << 20, 1u << 20, 256u << 10};   // whole buffer, 16 MiB .. 256 KiB copies
    std::printf("%-28s %10s %10s\n", "copy size", "H2D GB/s", "D2H GB/s");
    for (size_t c : chunks) {
        const double h2d = run(d, hp, bytes, hipMemcpyHostToDevice, reps, s, c);
        const double d2h = run(hp, d, bytes, hipMemcpyDeviceToHost, reps, s, c);
        std::printf("pinned, %8zu KiB copies   %10.2f %10.2f\n", c >> 10, h2d, d2h);
    }
    std::printf("pageable, whole buffer        %10.2f %10.2f\n", run(d, hu, bytes, hipMemcpyHostToDevice, reps, s, bytes),
                run(hu, d, bytes, hipMemcpyDeviceToHost, reps, s, bytes));
    return 0;
}
