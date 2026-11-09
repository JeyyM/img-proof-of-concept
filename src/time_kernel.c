/* time_kernel.c - times the brightness sum for the speedup table.
   All the frames get loaded into memory first, so reading the video isn't
   part of the timing. We time 3 versions: plain C, C that the compiler
   auto-vectorized, and our AVX2 assembly.
   One timed pass = one clock around ALL the frame pairs (not one per pair). */

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <io.h>
#include <fcntl.h>
#include <windows.h>

#define RUNS 5

uint64_t brightness_ordinary_c(const uint8_t *a, const uint8_t *b, size_t n);
uint64_t brightness_compiler_c(const uint8_t *a, const uint8_t *b, size_t n);
uint64_t brightness_avx2(const uint8_t *a, const uint8_t *b, size_t n);

typedef uint64_t (*brightness_fn)(const uint8_t *a, const uint8_t *b, size_t n);

/* runs fn on every pair of frames next to each other */
static uint64_t pass(brightness_fn fn, const uint8_t *frames, int nframes, size_t npix) {
    uint64_t total = 0;
    for (int i = 1; i < nframes; i++) {
        const uint8_t *prev = frames + (size_t)(i - 1) * npix;
        const uint8_t *curr = frames + (size_t)i * npix;
        total += fn(prev, curr, npix);
    }
    return total;
}

static double time_pass(brightness_fn fn, const uint8_t *frames, int nframes, size_t npix, LARGE_INTEGER freq) {
    LARGE_INTEGER t0, t1;
    volatile uint64_t result; /* volatile so the compiler doesn't skip the work */

    QueryPerformanceCounter(&t0);
    result = pass(fn, frames, nframes, npix);
    QueryPerformanceCounter(&t1);

    (void)result;
    return (double)(t1.QuadPart - t0.QuadPart) / (double)freq.QuadPart;
}

static int cmp_double(const void *a, const void *b) {
    double x = *(const double *)a;
    double y = *(const double *)b;
    return (x > y) - (x < y);
}

/* one warm-up pass, then 5 timed passes. prints the median and all 5 (sorted) */
static void report(const char *name, brightness_fn fn, const uint8_t *frames, int nframes, size_t npix, LARGE_INTEGER freq) {
    double runs[RUNS];

    time_pass(fn, frames, nframes, npix, freq); /* warm-up, not counted */
    for (int i = 0; i < RUNS; i++) {
        runs[i] = time_pass(fn, frames, nframes, npix, freq);
    }
    qsort(runs, RUNS, sizeof(double), cmp_double);

    printf("%s median %.6f runs %.6f %.6f %.6f %.6f %.6f\n",
           name, runs[2], runs[0], runs[1], runs[2], runs[3], runs[4]);
}

int main(int argc, char **argv) {
    LARGE_INTEGER freq;
    int mismatches = 0;

    if (argc != 4) {
        fprintf(stderr, "usage: time_kernel width height frames\n");
        return 2;
    }
    int width = atoi(argv[1]);
    int height = atoi(argv[2]);
    int nframes = atoi(argv[3]);
    if (width <= 0 || height <= 0 || nframes < 2) {
        fprintf(stderr, "bad size\n");
        return 2;
    }

    /* read every frame from stdin into one big buffer */
    size_t npix = (size_t)width * (size_t)height;
    uint8_t *frames = malloc(npix * (size_t)nframes);
    if (!frames) {
        fprintf(stderr, "out of memory\n");
        return 2;
    }
    _setmode(_fileno(stdin), _O_BINARY);
    if (fread(frames, npix, (size_t)nframes, stdin) != (size_t)nframes) {
        fprintf(stderr, "short read\n");
        return 2;
    }

    /* make sure all 3 versions give the same answer before timing anything */
    for (int i = 1; i < nframes; i++) {
        const uint8_t *prev = frames + (size_t)(i - 1) * npix;
        const uint8_t *curr = frames + (size_t)i * npix;
        uint64_t expected = brightness_ordinary_c(prev, curr, npix);
        if (expected != brightness_compiler_c(prev, curr, npix) ||
            expected != brightness_avx2(prev, curr, npix)) {
            mismatches++;
        }
    }

    QueryPerformanceFrequency(&freq);
    printf("pairs %d mismatches %d pixels %zu\n", nframes - 1, mismatches, npix);
    report("brightness_ordinary_c", brightness_ordinary_c, frames, nframes, npix, freq);
    report("brightness_compiler_c", brightness_compiler_c, frames, nframes, npix, freq);
    report("brightness_avx2", brightness_avx2, frames, nframes, npix, freq);

    free(frames);
    return mismatches == 0 ? 0 : 1;
}
