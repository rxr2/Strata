// Isolated benchmark of the CPU-row copy (copy_rows_from_mapped): mapped host -> VRAM, per-row blocks.
// Measures the current 128-thread shape and wider / split-row variants. Data values are irrelevant here.
#include <hip/hip_runtime.h>
#include <cstdio>
#include <cstdlib>
#include <vector>
#include <algorithm>

#define CK(x) do { hipError_t e = (x); if (e != hipSuccess) { std::printf("ERR %s: %s\n", #x, hipGetErrorString(e)); std::exit(1); } } while (0)

__global__ void rows_kernel(float4* __restrict__ dst, const volatile float4* src, int64_t row4,
                            const int32_t* __restrict__ hit_rows, const int32_t* __restrict__ count) {
    const int row = blockIdx.x;
    __shared__ int hit;
    if (threadIdx.x == 0) {
        int h = 0;
        const int c = *count;
        for (int i = 0; i < c; ++i) h |= hit_rows[i] == row;
        hit = h;
    }
    __syncthreads();
    float4* d = dst + (int64_t) row * row4;
    if (hit) {
        for (int64_t i = threadIdx.x; i < row4; i += blockDim.x) d[i] = make_float4(0.f, 0.f, 0.f, 0.f);
    } else {
        const volatile float4* sr = src + (int64_t) row * row4;
        for (int64_t i = threadIdx.x; i < row4; i += blockDim.x) d[i] = const_cast<const float4*>(sr)[i];
    }
}

// split: B blocks per row, each block handles a contiguous slice of the row.
__global__ void rows_split_kernel(float4* __restrict__ dst, const volatile float4* src, int64_t row4,
                                  const int32_t* __restrict__ hit_rows, const int32_t* __restrict__ count, int B) {
    const int row = blockIdx.x / B, part = blockIdx.x % B;
    __shared__ int hit;
    if (threadIdx.x == 0) {
        int h = 0;
        const int c = *count;
        for (int i = 0; i < c; ++i) h |= hit_rows[i] == row;
        hit = h;
    }
    __syncthreads();
    const int64_t per = (row4 + B - 1) / B;
    const int64_t lo = part * per, hi = min(row4, lo + per);
    float4* d = dst + (int64_t) row * row4;
    if (hit) {
        for (int64_t i = lo + threadIdx.x; i < hi; i += blockDim.x) d[i] = make_float4(0.f, 0.f, 0.f, 0.f);
    } else {
        const volatile float4* sr = src + (int64_t) row * row4;
        for (int64_t i = lo + threadIdx.x; i < hi; i += blockDim.x) d[i] = const_cast<const float4*>(sr)[i];
    }
}


__global__ void rows_multi_kernel(float4* __restrict__ dst, const volatile float4* src, int64_t row4, int rows,
                                  const int32_t* __restrict__ hit_rows, const int32_t* __restrict__ count) {
    const int c = *count;
    for (int row = blockIdx.x; row < rows; row += gridDim.x) {
        __shared__ int hit;
        if (threadIdx.x == 0) {
            int h = 0;
            for (int i = 0; i < c; ++i) h |= hit_rows[i] == row;
            hit = h;
        }
        __syncthreads();
        float4* d = dst + (int64_t) row * row4;
        if (hit) {
            for (int64_t i = threadIdx.x; i < row4; i += blockDim.x) d[i] = make_float4(0.f, 0.f, 0.f, 0.f);
        } else {
            const volatile float4* sr = src + (int64_t) row * row4;
            for (int64_t i = threadIdx.x; i < row4; i += blockDim.x) d[i] = const_cast<const float4*>(sr)[i];
        }
        __syncthreads();
    }
}

// plain contiguous copy for the achievable mapped-read bandwidth
__global__ void flat_kernel(float4* __restrict__ dst, const volatile float4* src, int64_t n4) {
    for (int64_t i = (int64_t)blockIdx.x * blockDim.x + threadIdx.x; i < n4; i += (int64_t)gridDim.x * blockDim.x)
        dst[i] = const_cast<const float4*>(src)[i];
}

int main(int argc, char** argv) {
    const int rows = argc > 1 ? atoi(argv[1]) : 40;
    const int misses = argc > 2 ? atoi(argv[2]) : 4;
    const int W = 2560;
    const int64_t row4 = W / 4;
    float4* dst; float4* hsrc;
    CK(hipMalloc((void**)&dst, (size_t)rows * W * 4));
    CK(hipHostMalloc((void**)&hsrc, (size_t)rows * W * 4, hipHostMallocMapped | hipHostMallocPortable));
    volatile float4* src = hsrc;
    for (int r = 0; r < rows; ++r)
        for (int i = 0; i < W; ++i) reinterpret_cast<float*>(hsrc)[r * W + i] = (float)(r + i);
    int32_t* dhit; int32_t* dcount;
    CK(hipMalloc((void**)&dhit, 64 * 4)); CK(hipMalloc((void**)&dcount, 4));
    std::vector<int32_t> hit(misses);
    for (int i = 0; i < misses; ++i) hit[i] = i;   // first `misses` rows are hits (zeros), the rest come over PCIe
    CK(hipMemcpy(dhit, hit.data(), misses * 4, hipMemcpyHostToDevice));
    CK(hipMemcpy(dcount, &misses, 4, hipMemcpyHostToDevice));
    hipStream_t s; CK(hipStreamCreate(&s));
    hipEvent_t a, b; CK(hipEventCreate(&a)); CK(hipEventCreate(&b));

    auto run = [&](const char* name, int threads, int B) {
        for (int i = 0; i < 20; ++i) {
            if (B == 1) rows_kernel<<<rows, threads, 0, s>>>(dst, src, row4, dhit, dcount);
            else rows_split_kernel<<<rows * B, threads, 0, s>>>(dst, src, row4, dhit, dcount, B);
        }
        CK(hipStreamSynchronize(s));
        CK(hipEventRecord(a, s));
        const int it = 300;
        for (int i = 0; i < it; ++i) {
            if (B == 1) rows_kernel<<<rows, threads, 0, s>>>(dst, src, row4, dhit, dcount);
            else rows_split_kernel<<<rows * B, threads, 0, s>>>(dst, src, row4, dhit, dcount, B);
        }
        CK(hipEventRecord(b, s)); CK(hipEventSynchronize(b));
        float ms = 0; CK(hipEventElapsedTime(&ms, a, b));
        const double us = 1000.0 * ms / it;
        const double gb = (double)(misses * W * 4) / (us * 1e-6) / 1e9;
        std::printf("%-18s threads=%4d B=%d: %8.2f us/call  %6.2f GB/s (miss rows)\n", name, threads, B, us, gb);
    };
    for (int t : {128, 256, 512, 1024}) run("row-block", t, 1);
    for (int t : {128, 256, 512}) run("split", t, 2);
    for (int t : {128, 256}) run("split", t, 4);
    auto run_multi = [&](int threads, int G) {
        for (int i = 0; i < 20; ++i) rows_multi_kernel<<<G, threads, 0, s>>>(dst, src, row4, rows, dhit, dcount);
        CK(hipStreamSynchronize(s));
        CK(hipEventRecord(a, s));
        for (int i = 0; i < 300; ++i) rows_multi_kernel<<<G, threads, 0, s>>>(dst, src, row4, rows, dhit, dcount);
        CK(hipEventRecord(b, s)); CK(hipEventSynchronize(b));
        float ms = 0; CK(hipEventElapsedTime(&ms, a, b));
        const double us = 1000.0 * ms / 300;
        std::printf("%-18s threads=%4d G=%d: %8.2f us/call  %6.2f GB/s (miss rows)\n", "multi-row", threads, G, us,
                    (double)(misses * W * 4) / (us * 1e-6) / 1e9);
    };
    for (int G : {4, 8, 12, 16, 24}) { run_multi(128, G); run_multi(256, G); }
    run_multi(512, 8); run_multi(512, 16);
    // flat copy of the same miss bytes, for the link's ceiling
    {
        const int64_t n4 = (int64_t)misses * row4;
        const int blocks = (int)((n4 + 255) / 256);
        for (int i = 0; i < 20; ++i) flat_kernel<<<blocks, 256, 0, s>>>(dst, src, n4);
        CK(hipStreamSynchronize(s));
        CK(hipEventRecord(a, s));
        for (int i = 0; i < 300; ++i) flat_kernel<<<blocks, 256, 0, s>>>(dst, src, n4);
        CK(hipEventRecord(b, s)); CK(hipEventSynchronize(b));
        float ms = 0; CK(hipEventElapsedTime(&ms, a, b));
        const double us = 1000.0 * ms / 300;
        std::printf("%-18s threads=%4d     : %8.2f us/call  %6.2f GB/s (flat, %d blocks)\n", "flat", 256, us,
                    (double)(misses * W * 4) / (us * 1e-6) / 1e9, blocks);
    }
    return 0;
}
