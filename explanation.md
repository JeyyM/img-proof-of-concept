# How this project fits together

This file is the map of the tree as it stands. The short course handout is `src/midpoint.md`. The scene-cut-on paper is `aside/paper/the-page-between-the-samples-v3.pdf`. This page says what each part is for, which file produces the next, what the numbers mean, and which command collects them.

There are two jobs on one set of clips.

The course job is the brightness sum, written three ways and timed on clip 01. The three ways must return the same total, and so the same cuts. The clock covers that sum only, after the frames are already in memory.

The clip job is why the sum exists. Each clip is a long easy picture with a 20-frame page of dense text in the middle. One CRF is chosen for the whole file. A check that looks at eight frames spread through the 900 frames can miss that page and allow a harsher CRF. A check that looks at eight frames after the cut can keep a gentler one. The file is then judged from every frame, not from the eight that voted.

## The clip

Every clip is 1920×1080, 30 frames per second, 900 frames. That is 30 seconds. The dense page is held for 20 frames, about two-thirds of a second.

The page start is drawn once, before any clip is encoded. The draw is the first 18 outputs of Python `random.Random(20261010)`, each uniform on frames 180 through 700. Those starts are stored in `clips/log.csv`. A later run does not draw them again for a clip that is already built.

The pictures live in three folders:

- `images/simple` is an easy screen: a slide, an empty dashboard, an empty editor, a section divider, a grid, an editor desktop.
- `images/medium` is a busier screen: analytics, a blank writer, a board, a control panel, a file manager, an appearance page.
- `images/dense` is the page someone has to read: an article, source code, a protocol, specification columns, a spreadsheet, a terminal log.

Clips 01–12 are the comparison set. Each pairs one simple picture with one dense page. Clips 01–06 use the six pairs in order. Clips 07–12 use the same simple pictures with the dense page shifted by one. Clips 13–18 are the boundary set: each medium picture against a dense page, shifted by two. The boundary clips are measured and then kept out of the comparison mean.

| Clip | Set | Easy picture | Dense page | Page starts |
|---|---|---|---|---|
| 01 | comparison | agenda slide | article | 538 |
| 02 | comparison | empty dashboard | code editor | 418 |
| 03 | comparison | empty editor | protocol | 223 |
| 04 | comparison | section divider | columns | 443 |
| 05 | comparison | grid desktop | spreadsheet | 517 |
| 06 | comparison | editor desktop | terminal log | 591 |
| 07 | comparison | agenda slide | code editor | 514 |
| 08 | comparison | empty dashboard | protocol | 545 |
| 09 | comparison | empty editor | columns | 439 |
| 10 | comparison | section divider | spreadsheet | 357 |
| 11 | comparison | grid desktop | terminal log | 350 |
| 12 | comparison | editor desktop | article | 582 |
| 13 | boundary | analytics | protocol | 644 |
| 14 | boundary | blank writer | columns | 182 |
| 15 | boundary | board | spreadsheet | 481 |
| 16 | boundary | control panel | terminal log | 515 |
| 17 | boundary | file manager | article | 631 |
| 18 | boundary | appearance | code editor | 354 |

`clips/build_clips.py` builds `clips/01.mkv` through `clips/18.mkv`. The encode is lossless RGB x264 at QP 0, one group of pictures for the whole file, scene-cut off. A still screen is stored once. After each new encode the script checks that the frame count is 900, frame 0 matches the easy still, and the frame at the drawn start matches the dense still. The log records the frame count, the file size, and whether that check passed.

## What leads to what

```
images/simple, images/medium, images/dense
        │
        ▼
clips/build_clips.py ──► clips/01.mkv … clips/18.mkv
                      └──► clips/log.csv
        │
        ├─ clips/run_system.py
        │     nasm -f win64 on src/brightness_avx2.asm, links it with src/detect.c → src/detect.exe
        │     reads clips/log.csv and clips/random_frames.txt
        │     writes clips/work/NN/encodes/crf*.mp4
        │            clips/work/NN/scores/crf*.json
        │            clips/work/NN/scores/summary.csv
        │            clips/decisions.csv
        │
        ├─ clips/run_scenecut_on.py
        │     reads clips/decisions.csv for the frame lists
        │     writes clips/work/NN/encodes_b/ and scores_b/
        │            clips/decisions_scenecut.csv
        │
        ├─ src/time_table.py          (clip 01 only)
        │     compiles src/brightness_c.c twice, assembles src/brightness_avx2.asm, links src/time_kernel.c
        │     writes clips/timing.csv and clips/timing.txt
        │
        └─ src/publish_cuts.py        (clip 01 only)
              compiles src/brightness_c.c twice, assembles src/brightness_avx2.asm, links src/list_cuts.c
              writes clips/cuts.txt

src/midpoint.md quotes clips/timing.csv, clips/cuts.txt, and clips/decisions.csv.
It does not run anything.
```

`src/build/` appears when the timing script or the cut script compiles. It holds object files and executables. Deleting it loses nothing that the records do not already hold. The next run creates it again.

`src/detect.exe` is the cut finder `clips/run_system.py` compiles. The course clock does not use it.

## The brightness sum

The sum is the absolute change in luma of every pixel, added up, for one pair of frames. A frame has 2,073,600 pixels. A clip has 899 pairs.

A cut is the first frame of a run whose mean absolute difference is above 2. In integer arithmetic that is a sum above `2 × 1920 × 1080`. The run ends when a pair falls back to 2 or below. On these clips the kernel marks the jump onto the page and the jump back, 20 frames later. Clip 01 marks frames 538 and 558.

Three builds of the same loop are the course comparison:

| Name in the table | Source | How it is compiled |
|---|---|---|
| brightness_ordinary_c | `src/brightness_c.c` | `-O2`, both vectorizers off |
| brightness_compiler_c | the same file | `-O2 -mavx2`, vectorizer on |
| brightness_avx2 | `src/brightness_avx2.asm` | `nasm -f win64`, hand-written `vpsadbw`, 32 bytes at a time |

GCC widens the bytes in the compiler build. It does not emit the SAD instruction. That is why the hand-written loop is a separate step past the compiler.

`src/time_kernel.c` is the clock. FFmpeg decodes clip 01 to raw gray and pipes it in. The program reads all 900 frames, checks that the three sums agree on every pair, then times them. Each timed pass is one clock around all 899 pairs. There is one warmup pass, then five recorded passes. The table keeps the median. Reading the clip is outside that clock. Encoding is outside it. VMAF is outside it.

The current medians, from `clips/timing.csv`, are 1.259 s for plain C, 0.537 s for the compiler (2.35× against plain), and 0.137 s for AVX2 (3.91× against the compiler). Pairs 899, mismatches 0. A new run of `src/time_table.py` replaces those medians with a fresh measurement.

The same run also times one full VMAF pass of `clips/work/01/encodes/crf31.mp4`, the settled file for clip 01. That pass took 22.0 s. It includes reading both videos, on 8 threads. It is stored on the `vmaf_one_pass` row so the sum can be seen beside the score. It is not a speedup.

`src/list_cuts.c` is the same three kernels with the clock left off. `src/publish_cuts.py` runs it on clip 01 and writes `clips/cuts.txt`. All three lists are `538 558`.

`src/detect.c` is a different program. `clips/run_system.py` uses it to mark cuts on all 18 clips. Inside it are `brightness_ordinary_c`, an intrinsic AVX2 loop, and a call to `brightness_avx2`. It checks that those three agree, prints one CSV row per pair, and accumulates a per-pair time on its status line. That accumulated time is not the course table. The course table is the single clock in `time_kernel.c`.

## How a CRF is chosen

`clips/run_system.py` does this once per clip. The scene-cut-off encode is libx264, preset medium, yuv420p, with `-g 999 -keyint_min 999 -sc_threshold 0`. One CRF covers every frame. The coarse rungs are 28, 32, 36, 40, and 44. The ladder then steps outward by 2 until the 9th-worst score brackets 90, and it stops at CRF 18 or 42. Between the last rung whose vote still reaches 90 and the next rung that fails, the missing integers are filled. Only the even-frame vote and the settled vote are filled that way.

For each CRF the script encodes `clips/work/NN/encodes/crfXX.mp4` if that file is not already there, then runs libvmaf against the lossless clip. The JSON log is `clips/work/NN/scores/crfXX.json`. Every frame gets a score. The distorted video is the first input and the lossless clip is the second. Both are formatted to yuv420 before the score. `n_subsample` is 1, so no frame is skipped. Eight threads are used.

Five rules each look at eight frames. The vote of a rule is the worst VMAF among its eight, not the average. The rule keeps the highest CRF whose vote is still at least 90. If no rung reaches 90, that rule has no file.

| Rule | Column prefix | The eight frames |
|---|---|---|
| Even frames | `spread_` | 56, 168, 281, 393, 506, 618, 731, 843. These are `floor((i + 0.5) × 900 / 8)` for `i` from 0 to 7. They sit about 112 frames apart. A 20-frame page fits in the gap. |
| Settled | `settled_` | Eight frames starting eight frames after a cut. The wait is the jump plus about a quarter of a second. On clip 01 the cut is 538, so the frames are 546 through 553. |
| On the cut | `cut_` | Eight frames starting at the cut itself. |
| Random | `random_` | One shared draw, stored in `clips/random_frames.txt`: 196, 353, 297, 306, 110, 775, 94, 695. The draw uses seed 20261010 after the 18 page-start draws, so it does not move a page. |
| Highest detail | `detail_` | Eight frames on the plane with the higher gray-level variance, either the first frame of the clip or the first frame of the page. |

The file is then scored apart from the vote. The file score is the 9th-worst of all 900 frame scores. Shortfall is how far that score sits below 90: `max(0, 90 − 9th-worst)`. Shortfall against 80 is the same distance below 80. A vote can clear 90 while the 9th-worst frame of the file does not. That is the result the comparison is about. On the scene-cut-off table, the even-frame file misses 90 on all 12 comparison clips, mean shortfall 10.32. The settled file clears 90 on all 12. Those rows are in `src/midpoint.md` and come from `clips/decisions.csv`.

The 45th-worst frame is also stored, in `clips/work/NN/scores/summary.csv`. Forty-five frames out of 900 is the 5th percentile. It is not a column in `decisions.csv`. The paper uses it to show that a percentile of the whole file can sit outside the page while the 9th-worst frame sits inside it.

`easy_below_2` in `decisions.csv` is the fraction of the 899 pairs whose mean absolute luma difference is not above 2. On an easy screen with one short page, that fraction is close to 1.

## Scene-cut on

`clips/run_scenecut_on.py` encodes the same 18 clips a second time. It omits `-g`, `-keyint_min`, and `-sc_threshold`, so libx264's own defaults apply. The votes reuse the frame lists already stored in `clips/decisions.csv`. The script does not move a page and it does not rewrite the scene-cut-off encodes.

Output goes to `clips/work/NN/encodes_b/`, `clips/work/NN/scores_b/`, and `clips/decisions_scenecut.csv`. The column names match `decisions.csv`. `clips/work/scenecut_on_encoder.txt` records the encoder identity. `clips/work/_probe/` is the short probe that confirmed those defaults. The midpoint table does not use this pass. The v3 paper does.

## The columns

`clips/log.csv`, one row per clip, written by `build_clips.py`:

| Column | Meaning |
|---|---|
| clip | `01` through `18` |
| group | `comparison` or `boundary` |
| easy, dense | Paths of the two stills, relative to the repo root |
| start | First frame of the dense page |
| hold | Always 20 |
| frames | 900 when the build check passed |
| bytes | Size of the lossless `.mkv` |
| status | `built` when the frame count is 900 and both stills matched |

`clips/decisions.csv` and `clips/decisions_scenecut.csv`, one row per clip. The second file is the scene-cut-on encode. Shared columns:

| Column | Meaning |
|---|---|
| cuts | Frames the kernel marked, such as `538 558` |
| easy_below_2 | Share of pairs at or below the cut threshold |
| settled_frames, detail_frames | The eight frame numbers those two rules used |
| `spread_crf`, `settled_crf`, `cut_crf`, `random_crf`, `detail_crf` | Highest CRF whose eight-frame vote was still at least 90 |
| `_ninth` | 9th-worst VMAF of all 900 frames at that CRF |
| `_ninth_frame` | The frame that holds that 9th-worst score |
| `_shortfall` | `max(0, 90 − ninth)` |
| `_shortfall80` | `max(0, 80 − ninth)` |
| `_bytes` | Size of that CRF's `.mp4` |

`clips/work/NN/scores/summary.csv` is the ladder before a rule picks one rung. Each row is one CRF. `spread`, `settled`, `cut`, `random`, and `detail` on that row are the worst of the eight frame scores. `ninth` and `fortyfifth` are the 9th-worst and 45th-worst of the whole file, with the frame numbers beside them.

`clips/timing.csv` has one row per method. `median_s` is the middle of the five sorted runs. `runs_s` is those five times. `speedup_vs_ordinary` divides the ordinary median by this median. `speedup_vs_compiler` divides the compiler median by this median. The VMAF row leaves both speedups empty.

`clips/cuts.txt` is the three cut lists for clip 01 and the mismatch count.

## How to run it

Run the commands from the repo root. The scripts expect this FFmpeg and this GCC:

- `C:\Users\asus\AppData\Local\Programs\Python\Python313\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe`
- `C:\winlibs\mingw64\bin\gcc.exe`

`build_clips.py` also needs Pillow.

```
python clips/build_clips.py
python clips/run_system.py
python clips/run_scenecut_on.py
python src/publish_cuts.py
python src/time_table.py
```

What a second run does:

- `build_clips.py` keeps a clip whose `.mkv` exists and whose log row says `built`. It encodes only a clip that is missing or not marked built. The page start in the log stays.
- `run_system.py` compiles `detect.exe`, then skips any clip already present in `decisions.csv`. It does not rewrite that table unless it measures a clip that was not in it. Existing `crf*.mp4` and `crf*.json` files are reused.
- `run_scenecut_on.py` skips clips already present in `decisions_scenecut.csv`.
- `publish_cuts.py` decodes clip 01 and overwrites `clips/cuts.txt`.
- `time_table.py` decodes clip 01, retimes the three kernels, retimes the one VMAF pass, and overwrites `clips/timing.csv` and `clips/timing.txt`. The new medians will not match the old ones digit for digit.

The viewer is optional and parked. From the repo root:

```
python -m streamlit run aside/ui/app.py
```

Watch a clip plays the lossless original beside two chosen CRF files. Build a clip makes a new 900-frame file under `aside/ui/built/` from two uploaded pictures. That upload path is not one of the 18 clips, and the midpoint does not use it.

## What is parked

`aside/` is earlier writing and the paper, not the course path.

- `aside/paper/` holds the draft, v2, and v3 of the QoMEX paper. v3 is the scene-cut-on version. Its numbers come from `clips/decisions_scenecut.csv` set beside `clips/decisions.csv`.
- `aside/ui/` is the viewer.
- The other files in `aside/` are old plans, proposals, and criticism notes. They describe earlier layouts. The paths in this file are the ones that exist now.

`.gitignore` ignores video: `.mkv`, `.mp4`, and raw frames. A checkout without those files still has the scripts, the stills, and the CSV records. `build_clips.py` can rebuild the 18 lossless clips from `images/`. The CRF files and the VMAF JSON in `clips/work/` are the measurements behind `decisions.csv`. They are large, and the decision tables are the records the midpoint and the paper quote.
