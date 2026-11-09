# Midpoint demo

The course clip is `course/clip/reference.mkv`. Seed 20261010. The draw is title.png, the first draw of that seed. The text page starts at frame 538 and is held for 20 frames, through frame 557. That start was not moved. The even frames, computed after the file existed, are 56, 168, 281, 393, 506, 618, 731, and 843.

## The three sums

Each version adds the absolute brightness change of every pixel, for every pair of frames, after the frames are in memory.

- Plain C is that loop with the compiler's vectorizer off.
- Compiler C is the same loop with AVX2 auto-vectorization on. The compiler widened the bytes. It did not emit the SAD instruction.
- AVX2 is `src/sad_avx2.s`, 32 bytes per `vpsadbw`.

On this clip the three totals match. The check is 899 pairs, 0 mismatches, 2,073,600 pixels. A cut is the first frame of a run whose mean absolute difference exceeds 2. All three kernels mark the same frames: 538 and 558. The lists are in `course/clip/cuts.txt`.

The clock is that sum only. Five runs, and the table keeps the median.

| Version | Median | Speedup |
|---|---:|---:|
| Plain C | 1.022 s | 1 |
| Compiler C | 0.449 s | 2.27× against plain |
| AVX2 | 0.155 s | 2.90× against the compiler |

One full VMAF pass on this machine took 21.2 s. It is in the timing table so the sum can be seen beside the score. Encoding time is not a result, and it is not in the table. The rows are in `course/clip/timing.csv`.

## The course clip, one file score

The vote is the worst of eight VMAF scores. The file score below is the 9th-worst of all 900 frames. Shortfall is how far that score sits below 90.

| Rule | CRF | 9th-worst | Shortfall | Bytes |
|---|---:|---:|---:|---:|
| Even frames | 37 | 77.35 | 12.65 | 246,180 |
| Settled, frames 546–553 | 30 | 91.00 | 0.00 | 351,101 |

Source: `course/clip/scores/summary.csv`. The settled file is the one whose eight page frames stay at or above 90. Its 9th-worst also stays at or above 90.

## A few other pictures

Same two rules. Each row is a different easy picture. On every one of these clips, 99.8% of the easy-frame pairs sit at or below the cut threshold of 2.

| Clip | Pictures | Even CRF | Even 9th | Even shortfall | Even bytes | Settled CRF | Settled 9th | Settled shortfall | Settled bytes |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 01 | Agenda / article | 36 | 81.89 | 8.11 | 201,029 | 31 | 90.34 | 0.00 | 278,437 |
| 02 | Dashboard / source | 37 | 81.57 | 8.43 | 124,114 | 32 | 90.56 | 0.00 | 154,573 |
| 03 | Editor / protocol | 40 | 69.58 | 20.42 | 139,214 | 31 | 90.46 | 0.00 | 204,478 |
| 11 | Grid / terminal | 35 | 86.28 | 3.72 | 201,252 | 32 | 90.48 | 0.00 | 231,533 |

Source: `clips/decisions.csv`. Clip 01 is the same start, frame 538, as the course clip, on a different pair of pictures.
