# Coding plan: one clip against the hypotheses

Tonight scores the clip that already exists. It does not add clips, viewers, OCR, or the AVX2 kernel.

## What is already built

[poc/make_clip.py](poc/make_clip.py) built a 1024×576, 30 fps, 900-frame clip.

- [poc/reference.mkv](poc/reference.mkv) is the clean copy. Frames 0–99 are the blank picture, frames 100–119 are the text page, frames 120–899 are blank again.
- [poc/encodes](poc/encodes) has CRF 28, 32, 36, 40, and 44. Scene-cut detection is off. Each file has one keyframe, at the start, so the cut was not given a fresh clean frame.
- The spread-out frames on a 900-frame clip are 56, 168, 281, 393, 506, 618, 731, and 843. All of those are blank.
- The text-aware frames are 108–115, a quarter of a second after the cut at frame 100. All of those are inside the text.

The cut frame is known for this clip because we built it. Tonight’s script may use that known cut. It is a check of the scores, not a test of the change finder.

## What the code will do

Add [poc/score_clip.py](poc/score_clip.py). It uses the same FFmpeg binary as `make_clip.py`, which already includes libvmaf.

For each compressed file, run one full VMAF pass against `reference.mkv` and save every frame score. The reference is yuv444 and the compressed files are yuv420, so both sides are formatted to yuv420 before the score. The eight sample scores are read out of that saved list. Frames are not cut into a new file.

The distorted file is the first input to libvmaf and the reference is the second. One JSON log per CRF is written under `poc/scores/`.

From each list of 900 scores:

- Spread-out vote: the worst of the eight blank-frame indexes above.
- Text-aware vote: the worst of frames 108–115.
- Jump vote, only as a side column: the worst of frames 100–107. On this clip the cut is already a clean text frame, so this column may tie the text-aware vote. That does not settle Hypothesis 3.
- File score: sort the 900 scores worst to best and take the 9th. Also record that frame’s index.
- Sensitivity column: the 45th-worst score and its frame index. It does not choose a file.
- Shortfall at 90: how far the 9th-worst score sits below 90, or zero if it sits above.
- File size in bytes.

Each rule keeps the harshest CRF whose own vote is still at least 90. If no CRF clears 90, say so. That clip has no legal choice.

Print one table to the console and write the same rows to `poc/scores/summary.csv`.

## What “fits” means on this one clip

This cannot confirm the paper. It can only lean the same way.

- Hypothesis 1 leans right if the text-aware file’s shortfall at 90 is smaller than the spread-out file’s shortfall.
- Hypothesis 2 leans right if the 9th-worst frame falls inside frames 100–119 and the 45th-worst frame falls on the blank picture.
- Hypothesis 4 leans right if the text-aware file is larger than the spread-out file when its shortfall is smaller.

A tie, because both rules pick the same CRF, means this ladder did not separate them. If every file’s 9th-worst score is still at least 90, encode CRF 48 once, score it, and stop. That step is a property of the ladder. It is not a search for a friendlier result. If CRF 48 still does not separate the two votes, tonight’s result is that this clip and this ladder did not show the effect.

## Left for later

The change finder, plain and AVX2, is not in this run. Neither are the other clips, the default scene-cut encode, MS-SSIM, OCR, or viewers.
