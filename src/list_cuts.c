/* List the cut frames from the three course kernels. Not timed. */

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <io.h>
#include <fcntl.h>

uint64_t sad_plain(const uint8_t *a, const uint8_t *b, size_t n);
uint64_t sad_autovec(const uint8_t *a, const uint8_t *b, size_t n);
uint64_t sad_avx2_asm(const uint8_t *a, const uint8_t *b, size_t n);

#define MAX_CUTS 32

static void note(int *cuts, int *count, int *in_run, int frame, int above) {
    if (above && !*in_run) {
        if (*count < MAX_CUTS) {
            cuts[(*count)++] = frame;
        }
        *in_run = 1;
    } else if (!above) {
        *in_run = 0;
    }
}

static void show(const char *name, const int *cuts, int count) {
    int i;
    printf("%s", name);
    for (i = 0; i < count; i++) {
        printf(" %d", cuts[i]);
    }
    printf("\n");
}

int main(int argc, char **argv) {
    int width;
    int height;
    size_t npix;
    uint64_t limit;
    uint8_t *prev;
    uint8_t *curr;
    int frame = 0;
    int mismatches = 0;
    int plain_cuts[MAX_CUTS], auto_cuts[MAX_CUTS], avx_cuts[MAX_CUTS];
    int plain_n = 0, auto_n = 0, avx_n = 0;
    int plain_run = 0, auto_run = 0, avx_run = 0;

    if (argc != 3) {
        fprintf(stderr, "usage: list_cuts width height < gray\n");
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
    _setmode(_fileno(stdin), _O_BINARY);
    prev = (uint8_t *)malloc(npix);
    curr = (uint8_t *)malloc(npix);
    if (!prev || !curr) {
        fprintf(stderr, "out of memory\n");
        return 2;
    }
    if (fread(prev, 1, npix, stdin) != npix) {
        fprintf(stderr, "need at least one frame\n");
        return 2;
    }
    while (fread(curr, 1, npix, stdin) == npix) {
        uint64_t plain_sad = sad_plain(prev, curr, npix);
        uint64_t auto_sad = sad_autovec(prev, curr, npix);
        uint64_t avx_sad = sad_avx2_asm(prev, curr, npix);
        uint8_t *swap;
        frame++;
        if (plain_sad != auto_sad || plain_sad != avx_sad) {
            mismatches++;
        }
        note(plain_cuts, &plain_n, &plain_run, frame, plain_sad > limit);
        note(auto_cuts, &auto_n, &auto_run, frame, auto_sad > limit);
        note(avx_cuts, &avx_n, &avx_run, frame, avx_sad > limit);
        swap = prev;
        prev = curr;
        curr = swap;
    }
    printf("pairs %d mismatches %d\n", frame, mismatches);
    show("plain_c", plain_cuts, plain_n);
    show("autovectorized_c", auto_cuts, auto_n);
    show("avx2_asm", avx_cuts, avx_n);
    free(prev);
    free(curr);
    return mismatches == 0 ? 0 : 1;
}
