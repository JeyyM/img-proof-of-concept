/* Mean absolute luma difference. Scalar and AVX2 must agree.
   A crossing is the first frame of a run whose mean is above 2. */

#include <immintrin.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <windows.h>

static uint64_t sad_scalar(const uint8_t *a, const uint8_t *b, size_t n) {
    uint64_t sum = 0;
    size_t i;
    for (i = 0; i < n; i++) {
        int diff = (int)a[i] - (int)b[i];
        sum += (uint64_t)(diff < 0 ? -diff : diff);
    }
    return sum;
}

uint64_t sad_avx2_asm(const uint8_t *a, const uint8_t *b, size_t n);

static uint64_t sad_avx2(const uint8_t *a, const uint8_t *b, size_t n) {
    size_t i = 0;
    __m256i acc = _mm256_setzero_si256();
    uint64_t lanes[4];
    uint64_t sum;
    for (; i + 32 <= n; i += 32) {
        __m256i va = _mm256_loadu_si256((const __m256i *)(a + i));
        __m256i vb = _mm256_loadu_si256((const __m256i *)(b + i));
        acc = _mm256_add_epi64(acc, _mm256_sad_epu8(va, vb));
    }
    _mm256_storeu_si256((__m256i *)lanes, acc);
    sum = lanes[0] + lanes[1] + lanes[2] + lanes[3];
    for (; i < n; i++) {
        int diff = (int)a[i] - (int)b[i];
        sum += (uint64_t)(diff < 0 ? -diff : diff);
    }
    return sum;
}

static double seconds_since(LARGE_INTEGER start, LARGE_INTEGER freq) {
    LARGE_INTEGER now;
    QueryPerformanceCounter(&now);
    return (double)(now.QuadPart - start.QuadPart) / (double)freq.QuadPart;
}

int main(int argc, char **argv) {
    int width;
    int height;
    size_t npix;
    uint64_t limit;
    FILE *in;
    uint8_t *prev;
    uint8_t *curr;
    int frame = 0;
    int mismatches = 0;
    int above = 0;
    LARGE_INTEGER freq, t0;
    double scalar_sec = 0.0;
    double avx_sec = 0.0;
    double asm_sec = 0.0;

    if (argc != 4) {
        fprintf(stderr, "usage: detect width height gray.raw\n");
        return 2;
    }
    width = atoi(argv[1]);
    height = atoi(argv[2]);
    if (width <= 0 || height <= 0) {
        fprintf(stderr, "bad size\n");
        return 2;
    }
    npix = (size_t)width * (size_t)height;
    limit = 2ull * (uint64_t)npix;
    in = fopen(argv[3], "rb");
    if (!in) {
        perror(argv[3]);
        return 2;
    }
    prev = (uint8_t *)malloc(npix);
    curr = (uint8_t *)malloc(npix);
    if (!prev || !curr) {
        fprintf(stderr, "out of memory\n");
        return 2;
    }
    if (fread(prev, 1, npix, in) != npix) {
        fprintf(stderr, "need at least one frame\n");
        return 2;
    }
    QueryPerformanceFrequency(&freq);
    printf("frame,sad,above\n");
    while (fread(curr, 1, npix, in) == npix) {
        uint64_t scalar_sad;
        uint64_t avx_sad;
        uint64_t asm_sad;
        int flag;
        frame++;
        QueryPerformanceCounter(&t0);
        scalar_sad = sad_scalar(prev, curr, npix);
        scalar_sec += seconds_since(t0, freq);
        QueryPerformanceCounter(&t0);
        avx_sad = sad_avx2(prev, curr, npix);
        avx_sec += seconds_since(t0, freq);
        QueryPerformanceCounter(&t0);
        asm_sad = sad_avx2_asm(prev, curr, npix);
        asm_sec += seconds_since(t0, freq);
        if (scalar_sad != avx_sad || scalar_sad != asm_sad) {
            mismatches++;
        }
        flag = asm_sad > limit;
        printf("%d,%llu,%d\n", frame, (unsigned long long)asm_sad, flag);
        {
            uint8_t *swap = prev;
            prev = curr;
            curr = swap;
        }
        (void)above;
    }
    fprintf(stderr, "pairs %d mismatches %d scalar_s %.6f avx_s %.6f asm_s %.6f\n",
            frame, mismatches, scalar_sec, avx_sec, asm_sec);
    free(prev);
    free(curr);
    fclose(in);
    return mismatches == 0 ? 0 : 1;
}
