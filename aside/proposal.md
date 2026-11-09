# Project Proposal

Advanced Computer Architecture, Integrating Project. 1st Term, 2026–2027. Group project.

## 0. Abstract

THE COURSE WORK IS THE SPEED OF THE BRIGHTNESS COMPARISON. THE SAME COMPARISON WILL BE WRITTEN THREE TIMES: ORDINARY C, THE SAME C AFTER THE COMPILER SPEEDS IT UP, AND AVX2 ASSEMBLY. THE COMPILER ALREADY REMOVES A LARGE PART OF THE TIME. THE ASSEMBLY IS FASTER THAN THAT AND RETURNS THE SAME CUTS. THE CLOCK COVERS THIS COMPARISON ONLY. THE RUNS ARE REPEATED, AND THE REPORTED TIME IS THE MIDDLE ONE.

A screen recording is often easy to compress, except for a short flash of dense text, such as a slide, a menu, or a paragraph. That moment may last less than a second. A check that looks at only a few frames spread through the clip can miss it. The encoder may then compress the whole file more harshly, and that text is the part most likely to lose quality first.

This project will look for the moment the picture changes by comparing the characteristics of each frame with the next such as the brightness of the pixels. THAT COMPARISON IS THE PART THAT RUNS IN PARALLEL.

After a change is detected, the check waits briefly so the frames it looks at are the new picture. It then chooses the strongest compression those frames still allow while meeting a quality target which will then be used for the file. THE COMPRESSION TEST IS THE REASON THE COMPARISON MATTERS. FRAMES TAKEN AFTER THE CHANGE ARE WHAT CHOOSE THE STRENGTH FOR THE FILE.

## 1. Description

The clip is thirty seconds long. It shows a simple still picture, such as a plain slide, cuts to a page of dense text for twenty frames, and cuts back. There is no fade. The program is not told when the text appears. It only sees the frames.

The way for choosing how to compress the file could be through a regular interval or through the analysis of the next image detected. Each way picks a compression strength that still meets a quality target. The finished file is then judged by a score of the whole clip to be able to analyze the quality and size of the file.

### a. Inputs

- One screen clip, 1920 by 1080px at 30 frames per second for a total of 900 frames.
- An easy picture and a dense-text picture for that clip. The text is held for 20 frames.
- The characteristics of each frame, so neighboring frames can be compared.
- A quality target. Compression is done with different strengths. A rule may pick a strength only while its making sure it still meets a target.



### b. Process



#### i. What will run in parallel

The comparison of two neighboring frames is the part intended to run in parallel. For each pixel, the characteristics such as brightness would be compared, and those comparisons combine into one result meaning that the frame has changed. Since a frame could have millions of pixels, the operation would be applied to many pixels at once, using AVX2, with the aim of doing that work faster. THE SAME COMPARISON WILL ALSO BE WRITTEN AS ORDINARY C AND AS THE SAME C AFTER THE COMPILER SPEEDS IT UP. THE COMPILER ALREADY REMOVES A LARGE PART OF THE TIME. THE ASSEMBLY IS FASTER THAN THAT, AND THE THREE VERSIONS MUST GIVE THE SAME CUTS.

#### ii. What already exists, and what is different here

A scorer for compressed video already exists. It compares each compressed frame with the original and gives that frame one score. A higher score means the frame is closer to the original. Based on the work of Yang et al. (2025), a short bad moment can matter even when most of the clip looks fine. This matters because not all frames of a video are equally important and dense or informative segments could have the most important data. Meanwhile getting an average score of the whole clip can obscure the damage done to a key portion. This project will keep a score of the finished file that can still see that flashed image as well as a check that looks at a few frames spread through the clip will be used for the comparison.

Currently a scorer for compressed video already exists. It compares each compressed frame with the original and gives that frame one score. A higher score means the frame is closer to the original. Based on the work of Yang et al. (2025), a short bad moment can matter even when most of the clip looks fine. Not every frame is equally important, and a short dense page can hold the part a viewer needs. An average over the whole clip can hide the damage on that segment. This project will keep a score of the finished file that can still see that short page. A separate check, looking at a few frames spread through the clip, will be the comparison.

There is existing work in choosing how hard to compress a video, while still meeting a quality target. Based on the work of Micó-Enguídanos et al. (2023), a video can be split into short pieces, and each piece can be given its own strength so that the piece still meets a chosen quality. Li, Yu, and Wang (2022) save space by changing the compressor itself, so that sharp text and a sudden change of page are treated more carefully than the rest. For the scope of this research, the compressor will not be changed and one compression strength will be assigned to the whole file that is chosen when a new picture appears.

There is already a standard way to find a sudden change by comparing one frame with the next. Based on the work of Chen et al. (2002), that comparison is the first step. If the new picture lasts only a few frames, they count it as still belonging to the picture before it. Based on the work of Smeaton, Over, and Doherty (2009), a hard jump can be found reliably this way, while a slow fade is harder. This project will use that simple brightness check, and it will not claim a new way to find cuts. The clip planned here has no fade, and the text has to stay on screen long enough for the check to see it.

The difference is in which frames are allowed to choose the compression. This project will wait until a sudden change has settled on the new picture, and those frames will choose one strength for the whole file. A few frames spread through the clip are the comparison, because that spread can miss a short page of dense text and then compress the whole file as if the page were as easy as the rest. The finished file will be judged by a score of the whole clip that still counts the short page. The scorer, the compressor, and the way of finding the cut will use the methods that already exist.

#### iii. How the parallel part will be built

The frame brightness comparison will be written THREE TIMES. One version is an ordinary loop, one pixel at a time. THE SECOND IS THE SAME C AFTER THE COMPILER SPEEDS IT UP. The other is AVX2 assembly, many pixels at a time, with a short ordinary loop for any pixels left over at the end. ALL THREE VERSIONS WILL RUN ON THE SAME FRAMES. THEY HAVE TO RETURN THE SAME BRIGHTNESS TOTAL, AND SO THE SAME CUTS. THE COMPILER ALREADY REMOVES A LARGE PART OF THE TIME. THE ASSEMBLY IS FASTER THAN THAT. THE CLOCK COVERS THIS COMPARISON ONLY. THE RUNS ARE REPEATED, AND THE REPORTED TIME IS THE MIDDLE ONE. The decoding, encoding, and scoring of the videos will stay outside the timing table.

#### iv. What stays one step after another

These steps will stay in this order. Each one waits for the step before it.

1. The moment the text appears will be chosen and written down.
2. The clip will be built from that choice.
3. The file will be encoded.
4. All frames will be scored.
5. The compression strength will be picked based on the scores.

The only parallel work is the brightness comparison that finds the cut to the next image.

### c. Outputs

- The cuts found by ORDINARY C, BY THE COMPILER-SPED C, AND BY AVX2, and a count of any disagreement in results which should be zero.
- Regular interval of frames used across the video chosen for analysis.
- The compression strength chosen for the video and how it compares to a quality target as well as the resulting file sizes.
- A TIMING TABLE FOR THE BRIGHTNESS COMPARISON OF ORDINARY C, COMPILER-SPED C, AND AVX2. THE CLOCK COVERS THE COMPARISON ONLY. THE RUNS ARE REPEATED, AND THE REPORTED TIME IS THE MIDDLE ONE.
- Final source code and discussion of the parallel comparison's timing table.



## 2. Platform

Timed runs will be taken on the group laptop, an AMD Ryzen 9 5900HS with 16 GB of memory, running 64-bit Windows 10. The processor supports AVX2. The compiler is GCC. Video work uses FFmpeg, with x264 for compression and VMAF for the frame scores. No GPU is required.

## 3. Mid-project milestone

BY THE WEEK 10 DEMO, THE FOLLOWING WILL BE TRUE FOR ONE CLIP.

- THE CLIP SHOWS AN EASY PICTURE, CUTS BRIEFLY TO A PAGE OF DENSE TEXT, AND CUTS BACK.
- ORDINARY C, THE COMPILER-SPED C, AND AVX2 MARK THE SAME CUTS ON IT.
- A TIMING TABLE FOR THE THREE VERSIONS IS DONE. THE CLOCK COVERS THE COMPARISON ONLY, THE RUNS ARE REPEATED, AND THE REPORTED TIME IS THE MIDDLE ONE.
- THE CUT IS USED TO PICK THE FRAMES THAT CHOOSE THE COMPRESSION STRENGTH.



## 4. References

1. S. Yang, J. Ji, Q. Zhu, Z. Yang, and X. Jin, “No-reference rendered video quality assessment: dataset and metrics,” arXiv:2510.13349, 2025.
2. F. Micó-Enguídanos, W. Moina-Rivera, J. Gutiérrez-Aguado, and M. Garcia-Pineda, “Per-title and per-segment CRF estimation using DNNs for quality-based video coding,” Expert Systems with Applications, vol. 227, article 120289, 2023.
3. J. Li, L. Yu, and H. Wang, “Perceptual redundancy model for compression of screen content videos,” IET Image Processing, vol. 16, pp. 1724–1741, 2022.
4. S.-C. Chen, M.-L. Shyu, W. Liao, and C. Zhang, “Scene change detection by audio and video clues,” IEEE International Conference on Multimedia and Expo, 2002.
5. A. F. Smeaton, P. Over, and A. R. Doherty, “Video shot boundary detection: seven years of TRECVid activity,” preprint, 2009.
6. N. Safonov, M. Rakhmanov, D. Vatolin, R. Timofte, and participating teams, “AIM 2025 challenge on screen-content video quality assessment: methods and results,” ICCV Workshops, 2025.

