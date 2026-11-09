/* detect.c - finds the cuts in a clip.
   For each pair of frames it adds up how much every pixel's brightness changed
   (sum of |a - b|). If the average change per pixel is above 2, that frame is
   flagged. A cut is the first flagged frame in a row of flagged frames.
   It also runs the plain C version and the AVX2 versions and checks they all
   give the same number. */

#include <immintrin.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <io.h>
#include <windows.h>

/* plain C, one pixel at a time */
static uint64_t brightness_ordinary_c(const uint8_t *a, const uint8_t *b, size_t n) {
    uint64_t sum = 0;
    for (size_t i = 0; i < n; i++) {
        int diff = (int)a[i] - (int)b[i];
        sum += (uint64_t)(diff < 0 ? -diff : diff);
    }
    return sum;
}

/* assembly version, in brightness_avx2.asm */
uint64_t brightness_avx2(const uint8_t *a, const uint8_t *b, size_t n);

/* same thing with AVX2 intrinsics, does 32 pixels per step */
static uint64_t brightness_avx2_intrinsic(const uint8_t *a, const uint8_t *b, size_t n) {
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

    /* leftover pixels if n isn't a multiple of 32 */
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
    FILE *in;
    LARGE_INTEGER freq, t0;
    int frame = 0;
    int mismatches = 0;
    double scalar_sec = 0.0, avx_sec = 0.0, asm_sec = 0.0;

    if (argc != 4) {
        fprintf(stderr, "usage: detect width height gray.raw\n");
        return 2;
    }
    int width = atoi(argv[1]);
    int height = atoi(argv[2]);
    if (width <= 0 || height <= 0) {
        fprintf(stderr, "bad size\n");
        return 2;
    }
    size_t npix = (size_t)width * (size_t)height;
    uint64_t limit = 2ull * (uint64_t)npix; /* average change of 2 per pixel */

    /* "-" means read from stdin */
    if (strcmp(argv[3], "-") == 0) {
        _setmode(_fileno(stdin), _O_BINARY);
        in = stdin;
    } else {
        in = fopen(argv[3], "rb");
        if (!in) {
            perror(argv[3]);
            return 2;
        }
    }

    uint8_t *prev = malloc(npix);
    uint8_t *curr = malloc(npix);
    if (!prev || !curr) {
        fprintf(stderr, "out of memory\n");
        return 2;
    }
    if (fread(prev, 1, npix, in) != npix) {
        fprintf(stderr, "need at least one frame\n");
        return 2;
    }

    QueryPerformanceFrequency(&freq);
    printf("frame,brightness,above\n");

    while (fread(curr, 1, npix, in) == npix) {
        frame++;

        QueryPerformanceCounter(&t0);
        uint64_t ordinary = brightness_ordinary_c(prev, curr, npix);
        scalar_sec += seconds_since(t0, freq);

        QueryPerformanceCounter(&t0);
        uint64_t intrinsic = brightness_avx2_intrinsic(prev, curr, npix);
        avx_sec += seconds_since(t0, freq);

        QueryPerformanceCounter(&t0);
        uint64_t avx = brightness_avx2(prev, curr, npix);
        asm_sec += seconds_since(t0, freq);

        if (ordinary != intrinsic || ordinary != avx) {
            mismatches++;
        }

        printf("%d,%llu,%d\n", frame, (unsigned long long)avx, avx > limit);

        /* swap so the current frame becomes the previous one */
        uint8_t *tmp = prev;
        prev = curr;
        curr = tmp;
    }

    /* these times are just a rough check, the real timing is in time_kernel.c */
    fprintf(stderr, "pairs %d mismatches %d ordinary_s %.6f intrinsic_s %.6f avx_s %.6f\n",
            frame, mismatches, scalar_sec, avx_sec, asm_sec);

    free(prev);
    free(curr);
    if (in != stdin) {
        fclose(in);
    }
    return mismatches == 0 ? 0 : 1;
}
