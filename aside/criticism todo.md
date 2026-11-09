# Criticism todo

Answers that can be given from the 18 clips and the scores already saved. Nothing here asks for a new picture, a held-out clip, or a viewer.

The open items are the ones that still need a run. The checked items are answered.

Numbers that wait for new clips or for viewers: 3, 5 (a measured hold sweep), 6, 7, 10, 11, 13, 16, 18, 19, 20, 22, 23, 24, 27, 41, 59, 60, 66, 71. The miss curve for other hold lengths is already calculated. Measuring those holds would be a new clip.

## Open

- [ ] **40.** OCR the 20 text frames of the spread file and of the settled file. The draft now says VMAF 90 is not a reading score. That sentence does not replace the check.

Runs that would widen the claim, not required for the draft to stay honest: scene-cut on and a shorter GOP (1, 2, 51), another preset or two-pass encode (14, 15), a 4:4:4 encode (47), MS-SSIM or PSNR (45), a denser CRF grid (55), a threshold sweep (61), a full-path timing (12, 62, 63, 65), and per-page zones (68).

## Closed in the draft by limiting the claim

- [x] **1, 2, 51.** The result is scene-cut off and a GOP longer than the clip. Shorter keyframe intervals were not tried. The limits and the conclusion say so.
- [x] **12, 62, 63, 65.** The paper does not claim the frame choice is fast. The kernel times and one VMAF pass are named as not a pipeline benchmark.
- [x] **14, 15, 68.** The result is libx264, preset medium, one CRF. No other codec, rate control, or per-page zone is claimed.
- [x] **37, 45.** VMAF 90 is the score that was used. MS-SSIM, PSNR, and a reading check were not run.
- [x] **47.** The settings are named: yuv420p on both VMAF sides, preset medium, scene-cut off, GOP longer than the clip. A 4:4:4 comparison is not claimed.
- [x] **55, 61.** The search steps by 2, and several even-frame votes are not perfectly monotone. The cut threshold is 2 and was not swept. The planted cuts sit well above it.

## Answered from the saved scores

Checked against `clips/decisions.csv` and `clips/work/*/scores/` for the 12 comparison clips. A choice below is the highest CRF already encoded whose own vote is still at least 90. It cannot see a CRF that was never encoded.

- [x] **8, 31.** Waiting 1, 2, 4, 8, 12, or 16 frames after the cut all hold the file at shortfall 0. On 11 of the 12 clips they pick the same CRF as the 8-frame wait. Clip 08 picks CRF 30 at a wait of 1 or 2, and CRF 31 at a wait of 4 or more. The wait of 8 is not a tuned optimum on these stills. The failure is the jump frame itself: clips 04 and 08 score that frame 0.0, and clip 11 scores it 2.65, while the page a few frames later is a normal soft picture.
- [x] **9.** One frame, eight frames after the cut, picks the same CRF as eight settled frames on all 12 clips. On a still page the extra seven samples add no new vote.
- [x] **25, 53.** The 84.6% figure is geometry for starts drawn from frame 180 through 700 against the eight even centers. It is not a rate observed in real recordings. The same count can be repeated for any other start interval without a new clip.
- [x] **28, 32.** One frame from each of the two pictures (frame 0 and the frame eight after the cut) picks the same CRF as the settled rule on all 12. On a clip with exactly two pictures, that is the scene-aware sample, and it matches.
- [x] **29.** One thousand fresh 8-frame draws per clip, scored on the CRFs already encoded. A draw hits the 20-frame page on about 15% to 18% of tries. The mean shortfall of those draws is 6 to 9 points on ten clips, and 15.7 and 17.0 on clips 03 and 09. The single committed draw (9.00 on average) is one sample from that spread, not the method.
- [x] **30.** Highest luma variance is a weak stand-in for “find the text.” On these clips it matches the settled file only when the page is the busier picture (clips 01 and 02). The scene-pair above is the stronger simple baseline, and it matches settled.
- [x] **34, 35.** The file-score oracle, the highest encoded CRF whose 9th-worst of all 900 is still at least 90, matches the settled CRF on all 12 clips. The even-frame CRF is harsher than that oracle on all 12. The settled gain is a closer decision, paid for with more bytes. It is not a claim of better quality at the same size. The ladder already stored is the rate-distortion table: CRF, 9th-worst, and bytes, in each `summary.csv`.
- [x] **36, 38, 54.** Changing the even-frame budget does not remove the hole by itself. At 8 frames the shortfall is the published one. At 16 frames, seven clips fall to shortfall 0 and five do not (01, 04, 07, 08, 09). At 32 frames, clips 04, 10, and 12 are still short, and clip 10 is short again after being clear at 16, because the sample locations move. A single even center sometimes lands inside the page and sometimes does not. The 9th-versus-45th contrast is specific to a 20-frame page in a 900-frame file, and the paper should keep saying so.
- [x] **44.** Target 80 is already scored. Four of the twelve spread files still miss it (03, 09, 10, 12). The settled files miss neither 90 nor 80. Other targets can be read from the same `summary.csv` vote columns.
- [x] **46.** On clip 04 the jump frame’s pixels are the page, with about the same error as the frames beside it, and VMAF still scores that frame 0. The 0 is the metric on the cut, not a mismatched frame number.
- [x] **49.** Resampling the six easy pictures, both clips of each picture together, 10,000 times, seed 20261010, puts the mean gap between 7.35 and 14.74. The clip-level interval was 7.83 to 13.31. Both stay above 0. Neither is a population interval.
- [x] **50.** The twelve shortfalls run from 3.72 (clip 11) to 20.69 (clip 09). The median is 8.47. The mean of 10.32 is pulled up by clips 03 and 09. Table 1 already has every clip.
- [x] **52.** All 12 even-frame samples miss the page. Separately, the 9th-worst frame of the file they chose is inside the page on all 12, and it is never one of the eight sampled frames. The miss and the damage are both reported.
- [x] **57.** On the cut, 9 of 12 comparison clips have a file and their mean shortfall is 0. Clips 04, 08, and 11 have no file. Highest detail has a file on 10 of 12, mean shortfall 10.13 on those 10. The coverage and the mean stay together.
- [x] **58.** The settled vote is taken on the page, so those eight frames clearing 90 is by the rule. The file score is not. The 9th-worst frame of the settled file is outside those eight frames on 8 of the 12 clips, and the oracle above still matches the settled CRF. The frames the vote did not use are what the 9th-worst is checking.

## Answered in the writing

These do not need a run. They need to stay in the 3-page cut.

- [x] **4, 21.** The 12 are the stress test: a flat screen, then a dense page. The six busier screens go the same way by less, mean shortfall 4.07, and stay out of the 10.32. An earlier check on fur, gravel, and leaves did not separate the two rules. The claim is screen graphics.
- [x] **26, 85.** The seed is 20261010. Starts are in `clips/log.csv`. Even frames were computed after the files existed: 56, 168, 281, 393, 506, 618, 731, 843. The build and score scripts are `clips/build_clips.py` and `clips/run_system.py`. Still to add when the package is packed: the x264 and libvmaf versions, in one place.
- [x] **33, 56.** Fairness here is eight VMAF reads against eight VMAF reads. The settled rule also spends a brightness pass to find the cut. The full 900 scores are how the experiment measured the file. They are not an input to the vote.
- [x] **39, 42, 43, 80.** Eight even frames plus a 5th-percentile score is a stand-in for a small sample and one file score. It is not a cited product. The task is a page someone may pause on. That page is 20 of 900 frames. The paper should not call this an industry approval step.
- [x] **47.** Decision encodes are libx264, preset medium, yuv420p, scene-cut off, GOP 999. VMAF sees both sides as yuv420p. The reference file is lossless RGB.
- [x] **48.** The 7.83 to 13.31 interval resamples these 12 development clips. It is not a confidence interval for screen video in general.
- [x] **64.** The three kernels match, and the speedups are course work. They are not the conference claim.
- [x] **67, 69, 70.** The cost to print is 27% more bytes on average, from 15% to 47%, about 46 KB on these stills. The 46 KB is small because a still screen compresses tightly. CRF is the knob. Bytes and the 9th-worst score are the result.
- [x] **72, 73, 75, 76, 79.** The geometry is obvious, and the cut finder is not new. The result is the file that gets shipped: the even-frame vote misses the page, the 9th-worst frame of that file lands inside it, and the 45th-worst frame stays outside it and above 90.
- [x] **74, 77, 78.** The draft’s references do not cover current screen-content coding or adaptive sampling. The recommendation that fits the evidence is narrow: on a short dense page in a long easy stretch, eight settled frames pick a file the full-frame 9th-worst also accepts, and eight even frames do not. How often that page occurs is not known.
- [x] **81, 82, 83, 84, 86.** The short paper keeps one picture of the dip, Table 1, the 9th-versus-45th sentence, the size, the busier-screen line, and one limits paragraph (scene-cut off, development set, no viewer). It does not keep the course timing or the extra figures.
