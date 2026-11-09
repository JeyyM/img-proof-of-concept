# Project Proposal

Advanced Computer Architecture, Integrating Project. 1st Term, 2026–2027. Group project. The course grades a parallel pixel comparison. A short conference paper is the other aim. The two stay separate. A faster comparison does not get the paper in.

## 0. Abstract

A screen recording can hold an easy picture for most of a clip, cut to a short page of dense text, and cut back. That page may last well under a second. A check that looks at eight frames spread through the clip can miss it and allow a harsh compression strength for the whole file. The worst frames of that file then fall inside the text. A check with the same budget of eight frames, taken after the picture has settled, lands on the text and keeps a gentler strength. The file is larger. The text stays closer to the quality target.

The comparison that finds the cut is the parallel part. It is the sum of absolute brightness differences, written in ordinary C and in AVX2 assembly. The two must return the same total. The clock covers that sum only.

The paper is about when that short page is missed, under a fixed budget of frames, and what that miss does to the finished file. It is not a new scene detector, and it is not a new encoder. One strength is used for the whole file. Giving each picture its own strength is out of this paper.

## 1. Description

The scripted clip is 30 seconds: 1920×1080, 30 frames per second, exactly 900 frames. It shows an easy still picture, cuts to dense text for 20 frames, and cuts back. There is no fade. The program is not told when the text appears. It sees brightness frames only.

Eight frames spread evenly through the clip are the baseline. Eight frames taken eight frames after the cut, still on the new picture, are the comparison. Both use the minimum of their eight scores to choose the strongest x264 CRF that still meets the target. The finished file is judged by a harsher mark than that vote: the 1st percentile of all 900 frame scores, which on this length is the 9th-worst frame. On a 20-frame text page that mark can fall inside the text. A 5th-percentile mark, about the 45th-worst frame, usually sits on the easy picture and is reported only to show that it does not move. File size is reported beside the score. A larger file does not by itself end the paper, and it is not hidden.

Thirty-six scripted clips each use their own easy picture and their own text. The start of the text is drawn once, from a seed, between 20% and 80% of the clip, before anyone computes which frames the spread check will hit. Placing the text in a gap on purpose is not allowed. Eighteen clips are scored first. Eighteen are held out and scored only after the rules are frozen. The paper stands or falls on the held-out half, at a VMAF target of 90, against the spread check, with scene-cut turned off and the GOP longer than the clip. Target 80 is the same table and does not end the paper. Scene-cut left on, which is what many recorders already do, is reported on the held-out half. Early checks found that it shrinks or ties the gap, so the claim is the scene-cut-off encode, and the scene-cut-on column is part of the paper.

The scope is the short dense page inside a long easy stretch. Two boundaries are reported so that scope is visible. On the development clips, one hold is too short to move the 9th-worst frame, and one hold is longer than the gap between the spread samples, about 112 frames. The short hold can be missed without changing the file. The long hold is a page the spread check already hits. Among six ordinary screen recordings, which are not the kill line, one is a tutorial in which hard pages keep arriving. On a recording of that kind the first settled page can be an easy one, and using it for the whole file is worse than spreading the eight frames. That row is shown. It does not enter the kill line. A download that is already compressed is never the reference. Scores are against the uncompressed capture.

A calculated figure, labeled as calculated, shows how often eight even samples miss a page of a given length inside 900 frames. It is the reason for the study. The result is the change in the chosen strength and in the file’s worst frames.

Early checks on rendered slides, including one 1080p clip, went the way the claim describes: the spread check’s worst frames fell inside the text, and the settled check held the target at a larger file size. Photos did not separate. Those checks are not the held-out table.

### a. Inputs

- Scripted clips, each 1920×1080, 30 fps, exactly 900 frames. One easy picture and one dense-text picture. The decision hold is 20 frames. Development clips also include a shorter hold and a hold longer than the spread-sample gap.
- A seeded start time for the text, written down before the spread-sample frames are computed.
- Brightness of each frame. The cut is a mean absolute difference above 2.
- A quality target of 90. The strength is an x264 CRF. A rule may take a CRF only while its own eight frames still meet the target.
- Six uncompressed screen recordings of ordinary activity, one of them a frequent-hard tutorial. Separate table.
- The encoder settings: libx264, preset medium. The decision encode turns scene-cut off. The reported encode leaves scene-cut on.

### b. Process

#### i. What will run in parallel

The comparison of two neighboring frames is the parallel part. For each pixel the absolute difference in brightness is added into one total. A 1080p frame has about two million of those pixels. AVX2 does 32 bytes in one instruction. An ordinary C loop of the same sum is kept beside it. The two must return the same total, and so the same cuts. Python is the harness that launches the tools. It is not the timed source of truth.

#### ii. What already exists, and what is different here

VMAF scores each frame of a compressed video against the original. An average of those scores hides a bad moment of twenty frames. This project keeps the scores and judges the file by the 9th-worst frame.

Spreading a few frames through a clip is a normal way to check a video. That spread is the baseline. Tools already search for one CRF by scoring detected scenes of several seconds. Per-segment CRF estimation already exists. This project does not claim that using a cut to choose a CRF is new. The open case is a page shorter than those scene samples, under a budget of eight frames, and a file score that can fall inside that page.

Hard cuts in ordinary video are a solved detection problem. The cut test here is a simple brightness threshold. Fades are out of scope.

Ways of asking people to rate video already exist, in ITU-T P.910 and ITU-R BT.500. A viewing session is included if four held-out pairs differ by at least 10 points on the file score and sixteen screened viewers remain. The short paper does not depend on it.

The pixel sum is a standard operation, and AVX2 already has an instruction for it. This project does not add an instruction and does not change the encoder.

#### iii. How the parallel part will be built

The same sum is written twice. One version is an ordinary loop, one pixel at a time. The other is AVX2 assembly, 32 pixels at a time, with a short ordinary loop for the pixels left over. Both run on the same frames. They must return the same total. The clock starts and stops around this comparison only, after the frames are in memory. Decoding, encoding, and scoring stay outside that clock. One full VMAF pass is timed once so the table shows how small the sum is beside the score.

#### iv. What stays one step after another

Building the clip, drawing the moment the text appears, encoding the file, scoring all 900 frames, reading eight of those scores, and picking one strength for the whole file. Each waits for the step before it. The only parallel work is the pixel comparison that finds the cut.

### c. Outputs

- The cuts found by ordinary C and by AVX2, and a count of any disagreement. That count should be zero.
- The frames each rule looked at, including the spread check, the settled check, a random draw, frames on the cut, and eight high-detail frames. A tie with one of the extra rules is reported. It does not by itself end the paper.
- The strength each rule chose, how far the finished file’s 9th-worst frame sits below 90, and the size of that file.
- The same table with scene-cut left on.
- The duration boundaries and the frequent-hard recording, outside the kill line.
- A timing table for the comparison alone: ordinary C, the compiler’s own vectorized build, and AVX2, next to the time of one VMAF pass.
- At the end of the term, a repository with the source, a short discussion of the parallel comparison, and that timing table.
- A conference paper only if the held-out result holds. The course does not require it.

## 2. Platform

Timed runs are taken on the group machine, an AMD Ryzen 9 5900HS, which supports AVX2. The compiler is GCC. Video work uses FFmpeg, with x264 for compression and VMAF for the frame scores. No GPU is required.

## 3. Mid-project milestone

By the Week 10 demo, on one official clip:

- Ordinary C and AVX2 mark the same cuts.
- The time the text appears was written down before the spread-sample frames were computed.
- Several compressed versions exist, from gentle to harsh, with scene-cut off.
- One full set of frame scores has been computed, and the gap from the quality target has been read for both the spread check and the settled check.
- The timing table for the comparison exists, set next to one VMAF pass.

The thirty-six clips and the held-out table are the paper. They are not the Week 10 demo.

## 4. References

1. Z. Li, A. Aaron, I. Katsavounidis, A. Moorthy, and M. Manoharan, “Toward a Practical Perceptual Video Quality Metric,” Netflix Technology Blog, 2016. The VMAF implementation used here is the one shipped with FFmpeg as libvmaf. https://github.com/Netflix/vmaf
2. FFmpeg Developers, FFmpeg. https://ffmpeg.org
3. VideoLAN, x264. https://www.videolan.org/developers/x264.html
4. Intel Corporation, Intel 64 and IA-32 Architectures Software Developer’s Manual. The AVX2 sum of absolute differences is the instruction used for the parallel comparison.
5. ITU-T Recommendation P.910, Subjective video quality assessment methods for multimedia applications.
6. ITU-R Recommendation BT.500, Methodologies for the subjective assessment of the quality of television images.
7. D. Micó-Enguídanos, J. Gutiérrez-Aguado, and M. Garcia-Pineda, “Per-title and per-segment CRF estimation using DNNs for quality-based video coding,” Expert Systems with Applications, vol. 227, 2023. Picking a CRF to hit a VMAF target, including per segment, already exists. This project uses one CRF for the file.
8. T. Vigil, dynamic-crf. A tool that searches for one CRF to hit a VMAF target and scores detected scenes of about 2 to 10 seconds rather than the whole file. https://github.com/terranvigil/dynamic-crf
9. A. F. Smeaton, P. Over, and A. R. Doherty, “Video shot boundary detection: a review,” and the TRECVid shot-boundary results summarized therein. Hard cuts are a solved detection task. This project uses a simple brightness test and does not treat cut detection as the contribution.
