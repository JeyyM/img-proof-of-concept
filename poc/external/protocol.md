# External screen-recording test

Locked on 10 October 2026, before any clip from these sets is encoded. This file is a generalization table. It does not enter the kill line of the 36-clip study, and it does not change the threshold, the wait, the budget, or the percentile used there.

## What is being asked

On a real screen recording, with no planted text page, does the text-aware sample still choose a gentler file than eight frames spread through the clip? The encodes beside that question are a normal scene-cut and x264’s screen preset.

## Clips

Two sources, used as references and re-encoded here.

- MSU screen-content set. Lossless `orig.mkv` only. 1920×1080, 30 fps, about 7–10 seconds. Meet and Teams copies are left out. They are not aligned frame for frame with the reference.
- SCVD references only. Raw 1920×1080, 30 fps, 10 seconds. The distortion archive is not part of this test.

Clips keep their real length. They are not padded or looped to 900 frames. They are not scaled.

## Constants that stay as they are

- A crossing is the first frame of a run whose mean absolute luma difference is above 2.
- The text-aware sample walks crossings in time order. If the frame eight frames after a crossing is still before the next crossing, take that frame and the following frames of the same picture until eight frames are chosen or the picture ends. Stop at eight. Do not fill leftover slots from later pages.
- If that sample is empty, the text-aware rule has no choice on that clip.
- The spread-out sample is eight frames, at `floor((i + 0.5) × N / 8)` for `i` from 0 through 7, where `N` is the clip’s real frame count. The formula does not look at the picture.
- A vote is the minimum of the frames that rule actually holds. The frames are read from one full score list. They are not cut into a new file.
- The file score is the `k`-th worst frame, with `k = max(1, ceil(0.01 × N))`. On a 900-frame clip this is the 9th-worst frame, the same rank as the main study. On a 300-frame clip it is the 3rd-worst. On a 210-frame clip it is the 3rd-worst.
- The sensitivity column is the `k5`-th worst frame, with `k5 = max(1, ceil(0.05 × N))`. It does not choose the compression.
- Target 90. Shortfall is how far the chosen file’s file score sits below 90, or zero if it sits above.
- A clip fails the input check when fewer than half of its frame pairs sit at or below 2. That clip is a row in the table and is left out of the mean.

## Encodes

Coarse ladder, chosen to match the screen pilot: CRF 28, 32, 36, 40, and 44. libx264, preset medium, yuv420. If every file score on that ladder is still at least 90, add CRF 48 once. If the highest legal rung and the next failing rung have integers between them, encode those integers. That fill is mechanical. It is not aimed after comparing the two rules.

Three settings, same CRF numbers:

- Scene-cut off: `-g 999 -keyint_min 999 -sc_threshold 0`. This is the setting the main study uses.
- Scene-cut on: x264 defaults for GOP and scene-cut. No tune flag.
- Screen preset: `-tune animation`, with x264’s default scene-cut left on. This is the industry-style encode, not a fourth selector.

## Order

SCVD pilot names, and only these, may be encoded first: Slides, Software Installation, Word Documents, Webpage, Online Education, Game, Animation. Game and Animation are the boundary. A missing name is recorded as missing. Another clip is not swapped in because it looks easier.

MSU references are sorted by filename. The first eight are the pipeline check. The rest wait until those eight have been encoded under the rules above. A label such as “slides” or “game” is written down. It does not move a file into or out of the first eight.

The threshold, the eight-frame wait, the budget, and the percentile formula are not edited after a score from this file exists. A change suggested by the table is written in a separate note and tried on clips that were not used to suggest it.

## What a row records

Name, source, frame count, whether the input check passed, cut times, frames each rule held, CRF chosen by the spread-out sample and by the text-aware sample, shortfall of each chosen file, file size, the frame index of the file score and of the sensitivity score, and the same CRF and shortfall under scene-cut on and under the screen preset.

The mean gap is computed only on clips that passed the input check and where both rules had a choice. The failed-check rows stay in the table and out of that mean.
