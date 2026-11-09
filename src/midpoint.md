# Midpoint demo

The course piece is the brightness sum, run three ways on the official clips. Those clips are built from `images/simple`, `images/medium`, and `images/dense`. Clip 01, the agenda slide and the article, is the file used for the timing and the cut check. The compression table uses all eighteen.

## What is parallelized

The sum is the absolute brightness change of every pixel, for every pair of frames, after the frames are in memory. Finding a cut is the first frame of a run whose mean absolute difference exceeds 2. That cut decides which eight frames may vote on the CRF. Encoding and VMAF stay outside the clock.

- `brightness_ordinary_c` is that loop with the compiler's vectorizer off. Source: `src/brightness_c.c`.
- `brightness_compiler_c` is the same source with AVX2 auto-vectorization on. The compiler widened the bytes. It did not emit the SAD instruction.
- `brightness_avx2` is `src/brightness_avx2.asm`, 32 bytes per `vpsadbw`.

## Execution time

Clip 01 is 1920×1080, 900 frames, 899 pairs, 2,073,600 pixels. The three totals match: 0 mismatches. All three kernels mark frames 538 and 558. The lists are in `clips/cuts.txt`.

The clock is the sum only. Five runs, and the table keeps the median.

| Version | Median | Speedup |
|---|---:|---:|
| brightness_ordinary_c | 1.259 s | 1 |
| brightness_compiler_c | 0.537 s | 2.35× against ordinary |
| brightness_avx2 | 0.137 s | 3.91× against the compiler |

Encoding time is not in the table. The rows are in `clips/timing.csv`.

## The official clips

The vote is the worst of eight VMAF scores. The file score is the 9th-worst of all 900 frames. Shortfall is how far that score sits below 90. Scene-cut is off in this table, and one CRF covers the whole file.

On all twelve comparison clips the even-frame file misses 90. The mean shortfall is 10.32. The settled file, eight frames starting eight after the cut, clears 90 on all twelve.

| Clip | Pictures | Even CRF | Even 9th | Even shortfall | Even bytes | Settled CRF | Settled 9th | Settled bytes |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 01 | Agenda / article | 36 | 81.89 | 8.11 | 201,029 | 31 | 90.34 | 278,437 |
| 02 | Dashboard / source | 37 | 81.57 | 8.43 | 124,114 | 32 | 90.56 | 154,573 |
| 03 | Editor / protocol | 40 | 69.58 | 20.42 | 139,214 | 31 | 90.46 | 204,478 |
| 04 | Divider / columns | 36 | 81.49 | 8.51 | 178,174 | 31 | 91.37 | 213,734 |
| 05 | Grid / spreadsheet | 35 | 82.77 | 7.23 | 218,852 | 30 | 90.80 | 260,575 |
| 06 | Editor desktop / terminal | 37 | 82.16 | 7.84 | 194,150 | 32 | 90.55 | 226,663 |
| 07 | Agenda / source | 37 | 81.74 | 8.26 | 138,572 | 32 | 90.22 | 181,171 |
| 08 | Dashboard / protocol | 36 | 80.47 | 9.53 | 182,951 | 31 | 90.05 | 217,530 |
| 09 | Editor / columns | 40 | 69.31 | 20.69 | 127,336 | 31 | 91.35 | 179,759 |
| 10 | Divider / spreadsheet | 36 | 79.69 | 10.31 | 175,860 | 30 | 91.17 | 225,225 |
| 11 | Grid / terminal | 35 | 86.28 | 3.72 | 201,252 | 32 | 90.48 | 231,533 |
| 12 | Editor desktop / article | 37 | 79.23 | 10.77 | 229,937 | 31 | 90.24 | 288,887 |

Source: `clips/decisions.csv`. The easy pictures are in `images/simple`. The pages are in `images/dense`.

The six medium clips, `images/medium` against the same kind of page, are clips 13–18. Settled shortfall is 0 on all six. Even-frame shortfall averages 4.07. They stay out of the 10.32 mean.
