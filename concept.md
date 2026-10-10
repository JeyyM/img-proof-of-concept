# Concept Note: Protecting a Brief Text Hold When a Video Is Compressed

Advanced Computer Architecture integrating project, 1st Term 2026–2027. Group project. This note explains the idea for a reader who has not seen the execution plan. The locked procedure, clip counts, and kill line are in `project_plan3.md`.

## 1. Summary

A thirty-second screen recording can be easy to compress except for a brief wall of dense text. That text lasts 20 frames, about two-thirds of a second, inside a clip of 900 frames. A quality check that looks at only a few frames spread through the clip can miss it. The encoder is then allowed to compress more harshly. The file gets smaller, the text falls apart, and a score of the whole file can still look acceptable, because almost every frame was the easy picture.

This project finds the moment the picture changes, waits a quarter of a second so the sample sits on the new picture, and uses those frames to choose how hard to compress. The finished file is judged by a score harsh enough to fall inside that short text, and by the change in file size. The course work is the change finder itself: the same pixel comparison in plain code and in AVX2, with identical answers and a timing table. The conference piece is whether the text-aware choice leaves the file closer to a quality target than the usual spread-out check.

## 2. The problem

Screen video often contains one short interval that a viewer has to read. A slide, a formula, a menu, a table, or a paragraph can be the only part of the file that matters, while the rest of the recording is a simple picture. Compression uses one quality setting for the whole file. A harsher setting makes a smaller file. Fine text is the first thing that breaks.

The decision is often made from a small sample. Eight frames spread evenly through a 900-frame clip land far apart. A 20-frame hold can sit between them. The sample then shows only the easy picture, and the harsh setting is accepted.

The score used afterward can hide the same moment. A 30-second clip has 900 frames. The worst 5% is about the 45th-worst frame. Twenty bad frames are fewer than that, so the 5th-percentile mark falls back on the easy picture. The text can look poor while the published number barely moves.

The practical failure is a file that passes its check and still loses the only frames a viewer needed to read.

## 3. Why this is needed

Lecture uploads, software tutorials, recorded slides, and other screen captures are signed off with this kind of check. The viewer’s loss is concentrated in a short interval. The file’s saving is taken from the whole clip. A method that samples the easy frames will keep approving that trade.

The field already knows that an average hides the worst frames. What is still easy to miss is narrower. A sample of a few evenly spaced frames, and a tail score that sounds strict, can agree with each other and still miss a hold this short. Someone encoding screen video needs to know when that agreement is a false pass, and what a cheap change in the sample does to the file that actually ships.

The study is a stress test built so the miss can happen. A wall of text for two-thirds of a second is uncommon on purpose. If the important picture stayed up for many seconds, the usual samples would often hit it and there would be little to measure. The short hold is the case where the usual check gets the decision wrong.

## 4. What has already been done

Several pieces of this pipeline already exist. The project uses them and measures a choice they leave open.

**Per-frame quality scores.** VMAF, from Netflix and available in FFmpeg as libvmaf, already scores frames one by one. Its documentation notes that a mean hides the worst frames, and it offers tail pools such as a 5th percentile, a 10th percentile, a 20th percentile, and the minimum. On a 900-frame clip, the 5th percentile is still above a 20-frame dip. This study keeps every per-frame score from one full comparison of the uncompressed recording against the compressed file, then takes the 9th-worst score as the file’s result. That is the 1st percentile of a clip of this length, and it can sit inside the text.

**Even sampling.** Taking a handful of frames spread through a clip is already a normal way to cover a video, including in challenge setups associated with QoMEX 2026. Eight centers of equal bins are the usual check in this study. The text’s start time is drawn at random, and written down, before those centers are computed, so the text cannot be parked between the bins after the fact.

**Viewing protocols.** ITU-T P.910 describes opinion tests with a hidden reference. ITU-R BT.500 describes screening of viewers. This project uses those procedures when a viewing session is actually run. The session is part of the work plan. The short paper can be the measurement table if the session is not finished.

**Encoders that already shrink still pictures.** x264 can be tuned for still images, and FFmpeg’s mpdecimate already drops frames that barely change. Both can make a lecture recording smaller. Beating them on file size is a different project. Here the encoder is libx264 at a fixed preset. The question is which frames are allowed to set its quality knob.

**A standard pixel comparison.** The change finder is a mean absolute difference on the luma plane. AVX2 already has an instruction that sums absolute differences of 32 bytes at once. The course contribution is that comparison, applied to every pair of frames, matched exactly against plain code, and timed. It is not a new instruction and not a new codec.

## 5. The idea

Each scripted clip is a screen recording at 1920×1080 and 30 frames per second, stopped at frame 900. It shows an easy picture, cuts to a dense text picture for exactly 20 frames, and cuts back. There is no fade. Each clip has its own pair of pictures. Thirty-six clips are recorded. Eighteen are a development set. Eighteen are held out and scored only after the pipeline has already been run. A separate pilot clip places the compression ladder and does not enter the result table. Six further recordings are ordinary screen activity, without a planted text hold. They are reported aside from the main table.

The change finder compares each frame with the next. A cut is the first frame of a run whose mean absolute luma difference rises above a small threshold. The text-aware sample does not take the cut itself. The cut is the jump. The text is the still picture after the jump, and the difference between that still picture and the next frame is almost zero. The sample starts eight frames after the cut, about a quarter of a second, and takes the following frames of that same picture until it has eight. The rule sees only the frames. It is not told the script, the timestamp, or which picture is the text.

Those eight frames vote by their worst score. The usual check does the same with eight frames spread evenly through the clip. The same vote is also taken from eight random frames, from eight frames starting on the cut, and from the eight most detailed frames. All of them read one saved list of frame scores. They do not require separate compressions.

The quality knob is libx264’s CRF. A higher CRF compresses more. Each rule picks the highest CRF whose own vote is still at least the target. The target that decides the paper is a VMAF of 90. A target of 80 is reported in the same table. The file that was chosen is then judged by the 9th-worst of its 900 frame scores. The shortfall is how far that score sits below the target, or zero if it sits above. File size is published beside the shortfall, because a closer score may have come from a larger file.

The main encode disables scene-cut detection and uses a group of pictures longer than the clip, so the cut does not become a fresh clean keyframe. A second encode puts x264’s ordinary scene-cut and keyframe settings back, on the held-out clips only. That second table shows whether the result depends on the encoder refusing to reset the picture at the cut.

## 6. Hypotheses

The hypotheses are stated before any clip is scored. Development recordings may expose a broken capture. They may not change a hypothesis, the threshold, the delay after the cut, the number of frames, or the percentile.

**Hypothesis 1, primary.** At target 90, on the held-out eighteen clips, files chosen from the eight settled frames miss the 9th-worst-frame score by less, on average, than files chosen from eight evenly spaced frames, and they do so on a majority of those clips.

The hypothesis fails if the text-aware average shortfall is not smaller, and the text-aware shortfall is worse or equal on a majority of the held-out clips. That failure ends the short paper. The course demo remains.

**Hypothesis 2, the score.** On these 900-frame clips, harm that is confined to the 20 text frames appears in the 9th-worst frame. The 45th-worst frame, the 5th percentile, stays on the easy picture. The 5th percentile is published so that this can be seen. It does not choose the compression.

**Hypothesis 3, where to look.** Eight frames taken on the jump itself protect the text less well than eight frames taken a quarter of a second later. The jump is a baseline. It is not the method.

**Hypothesis 4, the cost.** When the text-aware choice reduces the shortfall, its file is larger than the file chosen from evenly spaced frames. The study reports that ratio. A larger file does not by itself count as success, and it does not by itself end the paper.

**Hypothesis 5, the course kernel.** The plain implementation and the AVX2 implementation mark the same cuts. The AVX2 kernel time is lower. A speedup below one and a half times does not affect Hypothesis 1. The timing table is still required, and the paper’s abstract leads with the file result.

A viewing hypothesis is optional. If at least four held-out pairs differ by ten points on the 9th-worst-frame score, and at least sixteen screened viewers remain, their readability ratings are added. The confidence interval of the readability difference has to lie entirely on the side of the higher score. A missing session leaves Hypothesis 1 standing on the measurement table.

## 7. What we will produce

The course requires three deliverables.

- A Week 6 proposal in the course outline: what goes in, what runs in parallel, what already exists, what stays sequential, what comes out, the machine, and the Week 10 milestone.
- A Week 10 demo: the two change finders agree, one recorded clip exists at its committed timestamp, the compression ladder exists, and one shortfall at target 90 has been computed from a full frame-by-frame score.
- A Week 13 repository: source, a discussion of the parallel comparison, and sequential-versus-parallel timing.

The research output, if Hypothesis 1 holds, is a short paper built around one table. Each held-out clip shows the compression each rule chose, the 9th-worst-frame score of that file, the shortfall at 90 and at 80, and the file size. The table includes the spread-out sample, the random sample, the sample on the jump, and the sample of the most detailed frames. A confidence interval covers the paired gap against the spread-out sample. A second encode, with ordinary encoder defaults, is reported for the held-out half. On the files already chosen, the paper also reports the 5th percentile, a structural similarity score pooled the same way, and a text-reading check on the 20 text frames. None of those extra numbers choose the compression.

If the viewing session meets its rule, the ratings go in that paper. If a full viewing study is finished, that is a longer version. If Hypothesis 1 fails, the paper stops and the repository still contains the course work.

## 8. How the two grades stay apart

The course grades the change finder: many pixels compared at once, exact agreement with plain code, and a timing table that excludes decoding, encoding, and VMAF. The conference grades the file that was chosen. A faster comparison does not, by itself, make the measurement result true.

What stays sequential is the recording script, the random draw, decoding, encoding, the one quality pass over all 900 frames, the lookup of eight scores, and the choice of CRF. The parallel work is the pixel comparison that finds the cut.

## 9. Limits of the claim

The clips are scripted screen recordings. They are a measurement device for a short, important interval. They are not a survey of classrooms, and they are not camera footage of a room. The method chooses one compression strength for the whole file. It does not rewrite the encoder, train a quality model, or shield text pixels inside the codec. The six unscripted recordings ask whether the same rule can be run when no text hold was planted. They are not the result that confirms Hypothesis 1.

The target meeting for the paper is QoMEX 2027, the International Conference on Quality of Multimedia Experience, listed in Shanghai and ranked B in ICORE 2026. As of 9 October 2026 the official site had not posted the paper deadline. A tracker date is not treated as the call for papers.
