# Project Proposal

Advanced Computer Architecture, Integrating Project. 1st Term, 2026–2027. Group project.

## 0. Abstract

A screen recording is often easy to compress, except for a short moment of dense text: a slide, a menu, or a paragraph. That moment can last less than a second. A check that looks at only a few frames spread through the clip can miss it. The encoder is then allowed to compress the whole file more harshly. The file gets smaller, and the text is the first thing that breaks.

This project finds the moment the picture changes by comparing each frame with the next. That comparison looks at the brightness of every pixel. It is the part that runs in parallel, in AVX2 assembly. After the change, the program waits about a quarter of a second, so the sample sits on the new picture, and uses those frames to choose how hard to compress. The comparison is the usual check, which takes a few frames spread evenly through the clip.

The course work is the comparison itself. Ordinary C and AVX2 must give the same answer, and a timing table must show the difference. A short conference paper is optional. It would report whether the text-aware choice keeps the finished file closer to a quality target than the spread-out check does.

## 1. Description

The clip is a screen recording, thirty seconds long. It shows an easy picture, cuts to a page of dense text for twenty frames, and cuts back. There is no fade. The program is not told when the text appears. It only sees the frames.

Two ways of choosing the compression are compared. One looks at eight frames spread evenly through the clip. The other looks at eight frames of the picture that settled after the cut. Each way is allowed to pick the strongest compression whose own eight frames still meet the quality target. The finished file is then judged by a score of the whole clip, harsh enough to fall inside that short text, and by the size of the file.

### a. Inputs

- One screen clip, 1920 by 1080, 30 frames per second, stopped at frame 900.
- An easy picture and a dense-text picture for that clip. The text is held for 20 frames.
- The brightness of each frame, so neighboring frames can be compared.
- A quality target. Compression is done with x264 at several strengths. A rule may pick a strength only while its own sample still meets the target.
- A written start time for the text, chosen before anyone computes which frames the spread-out sample will hit.

Later clips repeat the same inputs. The Week 10 demo needs only the first one.

### b. Process

#### i. What will run in parallel

The comparison of two frames. For each pixel, take the difference in brightness, drop the sign, and add those differences up. One frame has about two million pixels, and the clip has hundreds of frame pairs. AVX2 adds the differences of 32 pixels in one instruction. A cut is the first frame of a run whose average difference rises above a small fixed threshold.

#### ii. What already exists, and what is different here

Frame-by-frame quality scores already exist. VMAF, from Netflix, scores each frame of a compressed video against the original. An average of those scores hides a bad moment that lasts only twenty frames. This project keeps the scores and judges the file by a mark that can fall inside that moment.

Sampling a few frames spread through a clip is already a normal way to check a video. That spread-out sample is the baseline here.

Ways of asking people to rate video already exist, in ITU-T P.910 and ITU-R BT.500. A viewing session will follow those if it is run. The course demo does not depend on it.

The pixel sum itself is a standard operation, and AVX2 already has an instruction for it. This project does not add a new instruction and does not change the encoder. It runs that sum on every pair of frames, checks that the assembly matches ordinary C, and uses the cuts it finds when choosing the compression.

#### iii. How the parallel part will be built

The same sum will be written twice. One version is an ordinary loop, one pixel at a time. The other is AVX2 assembly, 32 pixels at a time, with a short ordinary loop for any pixels left over at the end of the row. Both versions run on the same frames. They must return the same total, and so the same cuts. The clock is started and stopped around this comparison only. Decoding, encoding, and scoring the video stay outside the timing table.

#### iv. What stays one step after another

Building the clip, choosing the moment the text appears, encoding the file, scoring all 900 frames, reading eight of those scores, and picking the compression strength. Each of those waits for the step before it. The only parallel work is the pixel comparison that finds the cut.

### c. Outputs

- The cuts found by ordinary C and by AVX2, and a count of any disagreement. That count should be zero.
- The frames each rule looked at.
- The compression each rule chose, how far the finished file sits from the quality target, and the size of that file.
- A timing table for the comparison alone: ordinary C beside AVX2.
- At the end of the term, a repository with the source, a short discussion of the parallel comparison, and that timing table.
- A conference paper only if the measurement result holds. The course does not require it.

## 2. Platform

Timed runs will be taken on the group machine, an AMD Ryzen 9 5900HS, which supports AVX2. The compiler is GCC. Video work uses FFmpeg, with x264 for compression and VMAF for the frame scores. No GPU is required.

## 3. Mid-project milestone

By the Week 10 demo, the following will be true:

- Ordinary C and AVX2 mark the same cuts on one clip.
- That clip exists, and the time the text appears was written down before the spread-out frame numbers were computed.
- Several compressed versions of the clip exist, from gentle to harsh.
- One full set of frame scores has been computed, and the gap from the quality target has been read from that set.

## 4. References

1. Z. Li, A. Aaron, I. Katsavounidis, A. Moorthy, and M. Manoharan, “Toward a Practical Perceptual Video Quality Metric,” Netflix Technology Blog, 2016. The VMAF implementation used here is the one shipped with FFmpeg as libvmaf. https://github.com/Netflix/vmaf
2. FFmpeg Developers, FFmpeg. https://ffmpeg.org
3. VideoLAN, x264. https://www.videolan.org/developers/x264.html
4. Intel Corporation, Intel 64 and IA-32 Architectures Software Developer’s Manual. The AVX2 sum of absolute differences is the instruction used for the parallel comparison.
5. ITU-T Recommendation P.910, Subjective video quality assessment methods for multimedia applications.
6. ITU-R Recommendation BT.500, Methodologies for the subjective assessment of the quality of television images.
