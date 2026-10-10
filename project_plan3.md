# Project Plan: Choosing Frames, Then the Encode a Viewer Sees

Advanced Computer Architecture integrating project, 1st Term 2026–2027. Group project. The course requires a data-level parallelism proof of concept. This group also wants a conference paper in submittable shape.

**Decision:** a screen recording holds an easy picture, cuts to dense small text for 20 frames, and cuts back. Eight frames spread evenly through the clip can miss that text. Eight frames taken from the settled picture, a quarter of a second after the cut, land on it. Each rule uses the minimum of its eight scores to pick an encode. The score that decides whether the rule was wrong is the 1st percentile of every frame in the file it picked. Those two numbers are not the same statistic. The minimum is the selector’s vote. The 1st percentile is the bad tail of the whole file. On a 900-frame clip the 5th percentile is about the 45th-worst frame and lands on the easy picture, past the 20 text frames. The 1st percentile is about the 9th-worst frame and sits inside that text.

The selector never sees the script. It sees luma frames. The seed, the timestamp, and which image is the text are not inputs. The same rule runs on every clip.

The recordings are not one pair of images repeated. Thirty-six scripted clips each use their own easy picture and their own dense text. Eighteen of them are held out and scored only after the pipeline is frozen. Six further screen recordings are not made from that script. They are a separate table.

The wide work is one kernel: the luma compare, many pixels in one AVX2 instruction. VMAF, x264, and the viewing protocol are existing tools. The project does not train a model and does not write a codec. Reading eight scores out of a finished VMAF log is not a faster VMAF, and the paper does not claim that it is.

The claim can fail. Target 90 is the line, on the held-out eighteen, against even spacing. If the change-based files miss that target by as much as the evenly spaced files, on the mean and on a majority of those clips, the paper ends. The course demo still exists. Target 80 is reported in the same table. A tie at 80 does not end the paper. Random frames, frames on the cut, and high-detail frames are in the same table. A tie with one of them is reported. It does not by itself end the paper. File size is in the same table. A larger file does not by itself end the paper, and it is not hidden.

The objective shortfall table is the short paper. The viewing study is on the work plan. Ratings go in if four pairs and sixteen screened viewers exist. They are not the gate. A finished viewing study can be the full-paper version.

The course grades the compare. QoMEX grades the file that was chosen. A faster compare does not get the paper in.

## 1. Scope

### In scope

- One kernel: mean absolute difference of the luma plane between consecutive frames. AVX2 and plain C. The masks match exactly.
- Thirty-six scripted screen recordings at 1920×1080 and 30 fps. Each clip has its own easy picture and its own dense text, committed in the repo. No fade. No camera of a room, no projector, no face. The pictures differ: a slide, a page of text, a table, a form, code, a labeled figure.
- Every scripted clip, and the pilot, is exactly 900 frames. That is 30 seconds at 30 fps. The fraction of the file that is text cannot drift. The text is on screen for exactly 20 frames, then the easy picture returns. The moment the text starts is drawn once, uniformly between 20% and 80% of the clip, from a seeded draw. The seed is committed before the file exists. The eight even indices are computed only after the file exists. Placing the text between those indices on purpose is not allowed.
- A split committed with the seed: clips 1–18 are the development set, clips 19–36 are held out. Held-out files are scored only after development captures have passed the input check and the pipeline has been run once. Neither half may change a locked rule.
- One pilot clip, not in either half and not in the result table.
- Six screen recordings that are not built from the 20-frame script: ordinary screen activity, still 1920×1080, 30 fps, exactly 900 frames, no camera of a room. Same selector. Separate table. Not the kill line. A recording that fails the input check is reported as a failed check.
- Two encode conditions. Condition A is the kill-line encode: libx264, preset medium, scenecut disabled, GOP longer than the clip, so the cut does not become a fresh I-frame. Condition B uses the same preset and the same CRF numbers, with x264’s default scenecut and default GOP. Condition B is reported on the held-out half. It is not the kill line. The VMAF reference is the uncompressed capture. No still-image tune in either condition.
- A CRF ladder placed so neighboring rungs fall on either side of the target. Placement uses the pilot and a frozen outward step. It does not look at which selector wins.
- Selectors, all run on saved scores from one full VMAF pass per encode:
  1. Every frame, pooled as the 1st percentile of the whole file.
  2. Eight frames on the settled picture after a cut, voted by their minimum. This is the change-based rule.
  3. Eight frames at the centers of eight equal bins, voted by their minimum.
  4. Eight frames from one random draw, seed committed before scores.
  5. Eight frames starting on the cut itself, voted by their minimum.
  6. Eight frames with the highest luma variance on the uncompressed picture, voted by their minimum.
- Ablations on the same saved scores, pre-registered, not used to pick a new rule after the fact: cut versus settled placement, offsets 4, 8, and 16, and budgets of 1, 4, and 8 frames.
- The eight scores are indices into one full VMAF run. They are not a new video made by cutting frames together.
- The result that counts is the shortfall of the chosen file: how far its full-frame 1st percentile sits below the target. Per-clip shortfalls are published, with file size beside them.
- On the chosen held-out files only: the 5th percentile and the minimum of the 900 VMAF scores, MS-SSIM pooled as the same 9th-worst frame, and OCR accuracy on the 20 text frames. None of these pick the CRF.
- A paired difference and a bootstrap confidence interval on the held-out half.
- A viewing test, scheduled, included in the paper when at least four held-out pairs differ by 10 points on the 1st percentile and sixteen screened viewers exist. Otherwise the short paper is the shortfall table alone.
- Kernel time against plain C, and that time set next to the time of one full VMAF pass.

### Out of scope

- A new codec, a new quality model, or any trained network.
- Beating x264’s still-image tuning or FFmpeg’s `mpdecimate` on file size. Size is reported. It is not a race against those tools.
- A camera pointed at a room, a classroom, or a projected screen.
- Using the cut itself as the change-based rule. The on-the-cut selector is a baseline.
- Filling unused sample slots with the next-largest changes, as the change-based rule. That fill is an ablation.
- Treating a missing viewing session as a failed paper.
- A claim that eight indices into a finished VMAF log made VMAF faster.
- Letting MS-SSIM, OCR, the 5th percentile, or condition B replace the 1st percentile as the score that picks the CRF or ends the paper.
- CUDA, OpenMP, and AVX-512 as a requirement.

### Numbers locked before any selector is scored

The pilot may set the CRF numbers. It may not set these rules. Development scores may not set them either.

| Rule | Value |
|---|---|
| A cut is where mean absolute luma difference crosses above | 2, on 8-bit luma |
| Settled frame | 8 frames after that crossing, about a quarter of a second at 30 fps, and only if the next crossing has not already arrived |
| Unused slots | the following frames of that same new picture, still before the next crossing |
| Input check: share of easy-hold frames at or below 2 | at least 50% |
| A capture that fails the input check | replaced. The threshold is not moved. |
| Picture | 1920×1080, 30 fps, no fade |
| Scripted content | 36 distinct pairs. One easy picture and one dense text per clip. |
| Text hold | 20 frames |
| Where the text starts | one seeded uniform draw from 20% to 80% of the clip, seed committed first |
| Even indices | centers of eight equal bins, computed after the file exists |
| Random indices | eight distinct frames, one draw from a seed committed first |
| High-detail indices | the eight frames with the highest luma variance, ties broken by frame index |
| Selector budget | exactly 8 frames |
| Selector vote | the minimum of those eight per-frame scores |
| Clip length | exactly 900 frames, including the pilot and the six unscripted recordings |
| Full-file score | sort the 900 scores from worst to best and take the 9th. That is the 1st percentile on a clip of this length. It is not the minimum, and it is not the 5th percentile. |
| Kill target | 90, on the held-out 18, condition A, against even spacing |
| Reported beside it | 80. A tie at 80 does not end the paper. |
| Test clips | 18 development, 18 held out, 1 pilot, 6 unscripted |
| Ladder | five CRFs, libx264, preset medium. Condition A: scenecut off, GOP longer than the clip. Condition B: default scenecut and GOP, held-out half only. |
| Objective miss | shortfall = max(0, target − full-frame 1st percentile of the chosen file) |
| Paper ends at target 90 only if both are true | on the held-out 18, condition A, the change-based mean shortfall is not smaller than even spacing’s, and the change-based shortfall is worse or equal on a majority of those 18 |
| File size | bytes of the chosen file, and the ratio to the even-spacing file at the same target. Reported. Does not end the paper. |
| Viewing | included when at least 4 held-out pairs differ by ≥10 points on the full-file percentile and 16 viewers remain after screening. Not required to submit. |
| Viewers recruited | 24, so 16 can remain |
| Interval | percentile bootstrap, 10000 resamples, seed committed with the clip seed, on the held-out paired shortfall differences |

## 2. What we are deciding

Two grades, kept separate:

1. QoMEX, as a short paper: at target 90, on held-out screen recordings, files chosen from the settled picture miss the full-file 1st percentile by less than files chosen from eight even frames. The table also shows random frames, frames on the cut, high-detail frames, file size, condition B, the ablations, and the sensitivity metrics. Ratings are added when the viewing rule is met.
2. The course: the luma compare in AVX2 and in plain C, exact masks, and a timing table.

## 3. Course constraints

- Data-level parallelism on one platform. This plan uses AVX2. Intrinsics are the working form. Confirm with the instructor before Week 6 whether the graded kernel must be assembly.
- The same absolute difference and threshold apply to many pixels at once.
- Proposal in Week 6, working demo in Week 10, full submission in Week 13.
- The Week 13 repository needs source, a discussion of the parallel algorithm, and sequential-versus-parallel timing.
- The proposal follows the expanded outline: abstract, inputs, what is parallel, prior work and the difference, the plan, what stays sequential, outputs, platform, the Week 10 milestone, references.

Consent starts before Week 6 so a viewing session can still happen. The short paper does not wait on it. The thirty-six clips do not gate the Week 10 demo.

## 4. What a submittable paper means here

The target meeting is QoMEX 2027, the International Conference on Quality of Multimedia Experience. ICORE 2026 ranks it B. The conference site lists the 2027 edition in Shanghai. As of 9 October 2026 the official site had not posted the paper deadline. A deadline tracker lists 27 February 2027 and a meeting around 6 July 2027. Those dates stay unverified until the call is up.

The submission is a short paper of the shortfall table, the size column, the other selectors, and the held-out interval. If four qualifying pairs and sixteen screened viewers exist, their ratings are in that paper. If a full viewing study is finished, that is the full-paper version. The viewing study is not the gate.

These clips are screen recordings. The scripted half says so. They are not a survey of classrooms. The six unscripted recordings are the check that the selector was not handed the script.

Reviewers reject this shape of paper:

- Samples taken on the cut, where the picture jumps, instead of on the still text after it, and then described as the method.
- A text interval placed after the even indices were known, so that it sits between the bins.
- An I-frame forced at the cut, cleaner than the text frames that follow, and then ignored. Condition A turns that off so the comparison can be read. Condition B puts it back and is reported beside the main table.
- A mean over the whole hold, or the 5th percentile of the whole file used as the score that decides. That mark sits on the easy picture. The 5th percentile is published only to show that it does not move.
- Scores taken from a spliced file. VMAF’s motion term treats the joins as cuts.
- A paper that dies because the viewing session was small.
- A paper that calls eight lookups in a finished score list a faster quality metric.
- A paper that reports a quality gain and leaves out the change in file size.
- One image pair repeated until the count looks large.

## 5. Prior work, and the difference

| Work | What it did | Difference |
|---|---|---|
| VMAF, Netflix, in FFmpeg as libvmaf | Per-frame scores. A mean hides the worst frames. A 5th percentile over 900 frames is still above a 20-frame dip. | The selector votes with the minimum of eight frames from one full run. The file is judged by the 9th-worst frame, the 1st percentile of 900. The 5th percentile is a column, not the decision. |
| Even sampling of a handful of frames | Used to cover a clip, including in the QoMEX 2026 challenge setup. | The text lasts 20 frames inside a clip of exactly 900. Eight bin centers can miss it. The start time is drawn before those centers exist. |
| ITU-T P.910 and ITU-R BT.500 | Ratings with a hidden reference, and screening. | Run when four held-out pairs and sixteen screened viewers exist. The shortfall table is submitted either way. |
| MS-SSIM, as exposed by FFmpeg | A frame score with a different construction from VMAF. | Computed on the chosen held-out files and pooled as the same 9th-worst frame. It does not pick the CRF. |

The pictures and the seed are part of the method, so a reviewer can rebuild the clip. The selector’s inputs are the frames alone, so a reviewer can run it on another recording.

## 6. The method

### What the selector is allowed to see

Luma frames, in order. It is not given the seed, the drawn timestamp, the names of the images, or the length of the text hold. Those belong to the script that builds the scripted clips. Threshold, offset, and budget are the locked constants. They are not refit per clip.

### The script

For each of the thirty-six clips, play that clip’s easy picture. At the drawn timestamp, cut to that clip’s dense-text picture, hold it for 20 frames, and cut back. No fade. Record at 1920×1080, 30 fps, and stop at frame 900. The uncompressed capture is the VMAF reference.

The draw is uniform on 20% to 80% of those 900 frames. One seed, committed in the repo, produces the thirty-six timestamps, the pilot timestamp, the random-frame draws, and the bootstrap seed. Recording follows those timestamps. The eight even indices are computed later, as the centers of eight equal bins: frame floor((i + 0.5) × 900 / 8) for i from 0 through 7.

Clips 1–18 may be recorded and scored first. Clips 19–36 wait until that pipeline has been run and the locked rules are unchanged. A broken capture in the development half is replaced. The threshold, the offset, the budget, and the percentile are not edited to suit it.

The six unscripted recordings are ordinary screen activity, stopped at frame 900. They have no planted 20-frame hold. They use the same selector and condition A. They do not enter the kill table.

### The compare

For each pair of consecutive frames:

1. Decode to 8-bit luma. Outside the kernel.
2. Mean absolute difference of the luma plane.
3. A crossing is the first frame of a run whose mean is above 2.

Luma is bytes. AVX2’s sum-of-absolute-differences instruction handles 32 bytes at once. The row tail is scalar and its time is included in the kernel time, labeled as the tail. Integer arithmetic. A mask mismatch is a bug.

On the easy hold, most frames sit at or below 2. That is the 50% input check. The six unscripted recordings face the same check. Failing it removes the recording from the selector table and leaves a row that says the check failed.

### The eight settled frames

Walk the crossings in time order.

- If the frame eight frames after a crossing still comes before the next crossing, that frame is on the new picture, not on the cut.
- Then take the following frames of that same picture, still before the next crossing, until eight frames have been chosen or the picture ends.
- Stop at eight. Do not fill the rest with the largest remaining differences.

On a scripted clip the first crossing is the cut onto the text. Eight frames later is still inside the 20-frame hold. The next frames of that picture fill the budget with text frames. The cut back to the easy picture is not used to fill those slots. The selector does not use the fact that the hold is 20 frames. If the new picture ends sooner, the budget stops.

### The other eight-frame rules

Each of these is computed without the shortfall in hand.

- Even: the eight bin centers above.
- Random: eight distinct frame indices from the committed draw.
- On the cut: start at the crossing and take the following frames until eight have been taken or the next crossing arrives. This is the rule the method is not. It is in the table so the cut and the settled picture can be compared.
- High detail: variance of the luma plane on the uncompressed frame. The eight largest variances. Ties break toward the earlier frame.

### Where the eight scores come from

Each encode is scored once, uncompressed reference against the encode, every frame, in order. The per-frame scores are saved. Every eight-frame vote is the minimum of the scores at its indices. The every-frame vote, and the number the shortfall uses, is the 9th-worst of the 900 scores. Cutting the eight frames into a new file is not allowed.

Extra selectors do not add encodes. They read the saved list.

### The ladder

The pilot is the same script, also exactly 900 frames, and is not in the result table. It is encoded at CRF 20 through 40, step 1, under condition A. The pilot finds where the full-file 1st percentile crosses 90 and where it crosses 80.

The test ladder is five CRFs around the tighter crossing: two below, the crossing, and two above, taken from CRFs the pilot encoded. If a test clip’s own full-file sweep has every rung on one side of a target, step outward by 2 CRF. Stop when one rung is above and one is below, or at CRF 18 or CRF 42. That sweep is a property of the ladder. It is not a selector, and it is not repeated after shortfalls are known.

Condition B reuses those CRF numbers on the held-out clips. It does not grow its own ladder after the shortfalls are known.

Each selector then chooses the highest CRF whose vote is still at least the target. The every-frame selector’s vote is the full-file 1st percentile. The other votes are minima of eight scores.

### The number that counts

Shortfall is how far the chosen file’s full-file 1st percentile sits below the target, or zero if it sits above. Publish every clip. Beside each shortfall, publish the file size in bytes and the ratio of that size to the even-spacing file at the same target. The discussion states whether a smaller shortfall came with a larger file.

The kill line is target 90 only, on the held-out eighteen, under condition A, and only when the change-based mean shortfall fails to beat even spacing and a majority of those eighteen fail the same way. Target 80 is the same columns in the same table. The development half is published and cannot reopen the rules. Condition B, the random selector, the on-the-cut selector, and the high-detail selector are published. A loss to one of those three selectors narrows what the abstract may claim. It is not a second kill line.

For each held-out clip, form the paired difference: change-based shortfall minus even-spacing shortfall, at target 90, condition A. Report the mean and a 95% percentile-bootstrap interval from 10000 resamples. Also report the count of clips where the change-based shortfall is smaller, tied, or larger. The same paired count is reported against random, on-the-cut, and high-detail.

The every-frame selector sees the same full-file percentile the shortfall uses. If its shortfall is large, the ladder failed to bracket the target. That clip is a ladder failure, not a selector win.

### Ablations

Same saved scores. Same vote, the minimum of the frames actually taken. A short run is allowed here when the picture ends. The primary rule is still offset 8 and budget 8.

- Placement: the on-the-cut baseline against offset 8.
- Offset: 4, 8, and 16, each filled forward until the budget or the next crossing.
- Budget: 1, 4, and 8 frames from offset 8.
- Detection: crossings at threshold 2 against taking only the single largest jump in the clip.

These rows say which piece moved the shortfall. They are not a search for a better offset after the scores exist.

### Other scores on the chosen files

On the held-out files already chosen, and only those files:

- VMAF 5th percentile, the 45th-worst of the 900, and the minimum of the 900. The expectation on this script is that the 5th percentile stays on the easy picture. Publishing it shows that.
- MS-SSIM, pooled as the 9th-worst of its 900 frame scores.
- OCR on the 20 text frames of a scripted clip, against the known text picture. The engine is pinned before scores. If the engine cannot read the uncompressed reference, that clip’s OCR cell is empty. The VMAF row stays.

None of these choose a CRF.

### The viewing test

On the work plan. Consent starts before Week 6. Run it when ethics has cleared and at least four held-out clips have change-based and even-spacing files differing by at least 10 points on the full-file 1st percentile. Include the ratings only when at least sixteen viewers remain after ITU-R BT.500 screening. Recruit 24. The stimulus is about 10 seconds around the text, not the whole hold. ITU-T P.910 with a hidden reference. Two questions: overall quality, and whether the text is easy to read. The readability difference is the one reported. Its confidence interval has to lie entirely on the side of the higher percentile. An interval that contains zero is left out of the claim.

If those pairs or those viewers are missing, submit the shortfall table anyway.

### Time

Kernel time is the compare only. Decode, encode, and VMAF are outside it. Also time one full VMAF pass on one 900-frame encode, on the same machine. The paper may say how the compare’s time sits next to that pass. It may not say that the eight-frame vote skipped that pass. The shortfall needs all 900 scores.

### What is parallel

- Absolute difference and horizontal sum, 32 bytes per AVX2 instruction.
- One divide per frame to form the mean.

### What stays sequential

- The script, the seeded draw, decode, encode, the one VMAF pass, indexing, and the CRF decision.
- The pilot, the outward step, and condition B.
- The variance sort for the high-detail baseline, the bootstrap, MS-SSIM, and OCR.
- Viewing sessions.
- The row tail.

### Platform

AVX2 on one CPU the group can remeasure. The proposal names the model, caches, and base clock. Intrinsics are the working form. Assembly is a transcription if the instructor requires it. One platform. The rating display is named if the viewing session runs.

## 7. Baselines

The course requires the first. The paper requires the third and the shortfall on the chosen file. The fourth, fifth, and sixth are the stronger frame rules. The seventh is the encoder with its defaults put back.

1. Plain C of the same compare and threshold. Masks match AVX2 exactly.
2. That C file built with auto-vectorization and AVX2 enabled.
3. Eight bin centers, minimum of those eight scores, same ladder.
4. Eight random frames, one committed draw.
5. Eight frames starting on the cut.
6. Eight highest-variance frames.
7. Condition B, default scenecut and GOP, on the held-out half, same CRF numbers.
8. Viewers, only when four held-out pairs and sixteen screened viewers exist.

Kernel time excludes decode, encode, and VMAF.

## 8. Inputs and outputs

**Inputs**

- Thirty-six easy pictures and thirty-six text pictures in the repo, one pair per scripted clip, plus the pilot pair.
- One committed seed and the timestamps, the random draws, and the bootstrap seed drawn from it.
- The committed split: clips 1–18 development, clips 19–36 held out.
- Recordings at 1920×1080, 30 fps, exactly 900 frames. Scripted text held for 20 frames, no fade.
- Six unscripted 900-frame screen recordings.
- The 50% easy-hold check must pass before a clip enters a selector table.
- Pinned FFmpeg, libx264, the VMAF model name, the MS-SSIM filter, and the OCR engine. Reference is the uncompressed capture.
- Consent forms if the viewing session runs. Ratings stored without names.

**Outputs**

- Masks and a mismatch count. The count must be zero.
- The settled, even, random, on-the-cut, and high-detail indices per clip.
- Pilot CRFs and the final ladder, including outward steps.
- Per scripted clip, at 90 and at 80, condition A: each selector’s vote, the CRF chosen, the full-file 1st percentile, the shortfall, the file size, the size ratio to even spacing.
- The same columns for condition B on the held-out half.
- Held-out mean paired difference against even spacing, the bootstrap interval, and win, tie, and loss counts against each eight-frame rule.
- Ablation rows for offset, budget, placement, and detection.
- On chosen held-out files: VMAF 5th percentile, VMAF minimum, MS-SSIM 9th-worst, OCR on the 20 text frames.
- The six unscripted clips as their own table, or a failed-check row.
- Opinion scores only when section 1’s viewing rule is met.
- Kernel timing: plain C, auto-vectorized C, AVX2, and one full VMAF pass on the same machine.

## 9. How this maps onto the proposal

| Outline item | Content |
|---|---|
| 0. Abstract | Eight frames a quarter-second after a cut select an x264 rung. The selector sees luma, not the script. On held-out 900-frame screen recordings the file’s 1st-percentile VMAF misses target 90 by less than eight bin centers do. Size, random frames, the cut, and high-detail frames are in the same table. |
| 1a. Inputs | Thirty-six picture pairs, 1920×1080, 30 fps, 20-frame text cut, seed committed first, eighteen clips held out. |
| 1b.i What is parallel | Mean absolute luma difference, 32 bytes per instruction. |
| 1b.ii Existing work | VMAF; even sampling; P.910; MS-SSIM as a sensitivity score. Difference: sample the settled picture, vote with the minimum, judge the file with the 1st percentile of 900 frames, draw the cut before the bins exist, and do not hand the script to the selector. |
| 1b.iii Plan | Exact masks, pilot ladder, held-out shortfall table, size, extra selectors, ablations. Ratings added only if four pairs and sixteen screened viewers exist. |
| 1b.iv Not parallel | Script, encode, VMAF, indexing, CRF choice, viewing, row tail, MS-SSIM, OCR. |
| 1c. Outputs | Masks, indices, per-clip shortfalls and sizes, paired interval, optional ratings, kernel timing. |
| 2. Platform | AVX2 CPU. Display named if viewers are run. |
| 3. Mid-project milestone | Week 10: masks match, seed and the first pictures are in the repo, pilot ladder exists, shortfall on one development clip at target 90 from one full VMAF run. Even indices computed only after that file existed. |
| 4. References | Section 5. Add the QoMEX 2027 call when it is posted. |

## 10. Kill criteria

The short paper ends if any of these is true.

- Any mask mismatch between plain C and AVX2.
- The threshold, the offset, the budget, or the percentile was edited after any clip was scored.
- The text start was chosen after the even indices were computed, or was placed to fall between bins.
- The random draw was replaced after scores were known.
- Held-out clips were scored before the development pipeline had been run, and a locked rule was then changed.
- Condition A left scenecut on, or used a GOP short enough to put an I-frame on the cut.
- Scores came from a spliced eight-frame file.
- The change-based frames are the largest jumps, or unused slots were filled with later jumps.
- At target 90, on the held-out eighteen, under condition A, the change-based mean shortfall is not smaller than even spacing’s, and the change-based shortfall is worse or equal on a majority of those eighteen.

A tie or a loss at target 80 does not end the paper. A missing viewing session does not end the paper. A tie with the random, on-the-cut, or high-detail rule does not end the paper. Condition B does not end the paper. An empty OCR cell does not end the paper. A larger file does not end the paper.

If the ladder does not bracket 90 and the outward step was skipped or was aimed after looking at selector shortfalls, that clip is a ladder failure and is not counted as a win.

A kernel speedup under 1.5× does not end the shortfall claim. The abstract does not lead with speed in that case. The timing table is still required. The timing table may not describe the eight-frame index as a VMAF speedup.

## 11. Milestones

| When | Course requirement | Research requirement |
|---|---|---|
| Before Week 6 | — | Confirm AVX2. Ask whether intrinsics count. Pin FFmpeg, x264, the VMAF model, MS-SSIM, and OCR. Lock the picture pairs and the seed. Draw the timestamps and the random indices. Start consent. |
| Week 6 | Proposal in the expanded outline | This scope, the CPU, the capture script. |
| Week 10 | Working demo | Exact masks. One development clip at its committed timestamp. Pilot ladder. Shortfall at target 90 from one full VMAF run. Even indices computed only after that file existed. |
| Weeks 11–12 | — | The rest of the development half, then the held-out half. Condition B on the held-out half. Viewing if four held-out pairs already differ by ≥10 points and ethics has cleared. |
| Week 13 | GitHub: source, algorithm discussion, sequential vs parallel timing | Per-clip shortfall and size table at 90 and at 80. Paired interval. Ablations and sensitivity columns. Unscripted table. Short-paper draft if section 10 was not hit. Ratings inside it only if the viewing rule was met. |

Build order:

1. Commit the pictures and the seed. Draw the timestamps and the random indices. Do not compute even indices yet.
2. Plain C compare. Threshold 2. Dump the crossings.
3. AVX2 compare. Masks identical.
4. Timing harness, kernel only.
5. Record one development clip at its timestamp. Confirm the settled-frame rule lands inside the 20-frame text, not on the cut.
6. Pilot sweep under condition A. Freeze the ladder.
7. One VMAF pass per rung. Minimum of eight for each selector. Full-file 1st percentile, the 9th-worst of 900. Shortfall and file size.
8. The rest of the development half. Replace captures that fail the input check. Do not edit locked rules.
9. Only then the held-out half, then condition B on that half, then MS-SSIM and OCR on the chosen files. Viewers last, and only if the pairs exist.

The extra selectors and the ablations read the score list from step 7. They do not multiply the encodes. Condition B does.

## 12. Decision log

| Item | Choice | Status |
|---|---|---|
| Research goal | QoMEX short paper of the shortfall table. Full paper only if the viewing study is actually finished. | Adopted |
| What the eight frames are | The settled picture, 8 frames after a crossing of 2, then the next frames of that picture | Adopted. Replaces “eight largest changes,” which land on the cut. The on-the-cut rule remains as a baseline. |
| Stimulus | 36 scripted clips, each its own picture pair, 20-frame text hold, 1920×1080, 30 fps, seeded start in 20–80%. Plus 6 unscripted 900-frame screen recordings in a separate table. | Adopted. Replaces twelve clips of one repeated pair. |
| Selector inputs | Luma frames only. The seed and the script are not inputs. | Adopted |
| Encode | Condition A: scenecut off, GOP longer than the clip. Condition B: x264 default scenecut and GOP, held-out half, same CRF numbers, reported only. Reference is the uncompressed capture. | Adapted. Default scenecut can put an I-frame on the cut. That setting is in the paper. It is not the setting that decides the claim. |
| File size | Bytes, and the ratio to the even-spacing file, beside every shortfall. | Adopted as a column. Not a kill line, and not a race against still-image tuning. |
| Other frame rules | Random, on the cut, highest luma variance. Same saved scores. | Adopted. The kill line stays even spacing. A tie with another rule narrows the abstract and stays in the table. |
| Viewing | On the work plan. 4 held-out pairs, not 8. Missing viewers do not block the short paper. | Adapted. The study is scheduled. It is still not the submission gate. |
| Other metrics | On chosen held-out files: VMAF 5th percentile, VMAF minimum, MS-SSIM as the 9th-worst, OCR on the 20 text frames. | Adopted as sensitivity. None of them pick the CRF. The 5th percentile stays off the decision because it lands on the easy picture. |
| Sparse VMAF | Not a result. Kernel time is reported next to one full VMAF pass. | Not adopted. Eight indices in a finished log do not skip the pass the shortfall needs. |
| Statistics | Held-out 18. Paired shortfall against even spacing. 95% percentile bootstrap, 10000 resamples, seed committed first. Win, tie, and loss counts against each eight-frame rule. | Adopted |
| Ablations | Placement, offset 4/8/16, budget 1/4/8, threshold-2 runs versus the single largest jump. Pre-registered. Same scores. | Adopted. They do not change the primary rule after scores exist. |
| Selector vote vs file score | Minimum of the eight. 1st percentile of the 900-frame file, the 9th-worst score. The 5th percentile is a sensitivity column. | Adopted |
| Working estimate after the 12-clip lock | About 45% for that earlier design. | Superseded. The clip count, the baselines, and the held-out split have changed. No new rate is entered here. |
| Clip length | Exactly 900 frames for the pilot, every scripted clip, and every unscripted recording | Adopted |
| Kill line | Target 90, held-out 18, condition A, and only if both the mean and a majority fail against even spacing | Adopted |
| Target 80 | Same table. Does not kill. | Adopted |
| Kernel | AVX2 mean absolute luma difference, threshold 2 | Adopted. Graded by the course, not by QoMEX. |
| Rejected | Sampling the cut as the method, filling with dust peaks as the method, placing the text between known bins, a 0.3 tie called agreement, camera footage of a room, a faster-VMAF claim | Adopted as rejections |
| Previous candidate | Batched 8-point convex hulls, in `project_plan2.md` | Set aside |
| Platform | AVX2 | Proposed until the CPU is named |
| Venue | QoMEX 2027, Shanghai, ICORE 2026 B. Deadline not yet on the official site. | Holding until the call for papers is posted |
