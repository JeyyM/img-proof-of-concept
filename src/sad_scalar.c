/* Same brightness sum as detect.c. Compiled twice: once with the
   vectorizer off, once with AVX2 auto-vectorization on. */

#include <stddef.h>
#include <stdint.h>

#ifndef SAD_NAME
#define SAD_NAME sad_scalar
#endif

uint64_t SAD_NAME(const uint8_t *a, const uint8_t *b, size_t n) {
    uint64_t sum = 0;
    size_t i;
    for (i = 0; i < n; i++) {
        int diff = (int)a[i] - (int)b[i];
        sum += (uint64_t)(diff < 0 ? -diff : diff);
    }
    return sum;
}
