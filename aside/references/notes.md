# Notes on the six new references

These notes cover the six papers added for the compression side of the project. They are not the Intel or Agner manuals. Each note says what the paper studies, how it does the work, what it found, and where it meets or misses this project.

This project is a thirty-second screen clip: an easy picture, a hard cut to dense text for twenty frames, then a cut back. Two checks pick one x264 strength for the whole file. One check uses frames spread through the clip. The other finds the cut from a brightness change, waits briefly, and uses the new picture. The file is judged by a score of all 900 frames that can fall inside those twenty text frames, and by file size. The encoder is not changed.

## 1. Per-title and per-segment CRF estimation

Francisco Micó-Enguídanos, Wilmer Moina-Rivera, Juan Gutiérrez-Aguado, and Miguel Garcia-Pineda, “Per-title and per-segment CRF estimation using DNNs for quality-based video coding,” *Expert Systems with Applications*, vol. 227, article 120289, 2023.

The paper asks which constant rate factor will make a short piece of video land on a chosen VMAF score. Streaming systems already cut a title into segments of a few seconds and encode each segment on its own, often at several bit rates, so a player can switch. The authors argue that one CRF for every segment is wasteful, because some segments are easy and some are hard.

They built a set from 1,212 segments of 158 videos. Each segment was encoded with the VP9 encoder at 19 CRF values, giving 23,028 encodes, and each encode was scored with VMAF. A network was trained on features taken from a 240p copy of the segment, plus the target VMAF. The features include brightness and color statistics. The network’s output is the CRF to use. On 1,840 held-out two-second segments at 1080p, and on targets of 80, 85, 90, and 95, the encoded segments landed a mean of 1.84% away from the requested VMAF. The miss was larger at the lower targets and smaller at 95. Prediction, including the downscale and the feature step, took under four seconds a segment.

The encoder steps they review are the usual ones: split the frame into blocks, predict a block from the same frame or from an earlier frame, transform the leftover error, quantize it, then entropy-code the result. A higher quantization parameter keeps fewer coefficients and makes a smaller, worse picture. CRF is the high-level knob that drives that parameter. Their point is that the right CRF depends on the pictures in that segment, not only on a target number.

This is the closest of the six to the quality half of the project. Both sides pick a CRF so that VMAF meets a target, and both sides say the right CRF changes when the pictures change. The differences are large. Their unit is a two-second segment that is encoded on its own. This project uses one strength for all 900 frames. Their score is how close the segment’s VMAF is to the target. This project cares whether a twenty-frame text page, missed by a spread-out sample, becomes the bad tail of the whole file. They use VP9 and a trained network. This project uses x264 and does not train a model. Their test videos are ordinary streaming titles, not a scripted screen cut.

## 2. Perceptual redundancy model for screen content videos

Junlin Li, Li Yu, and Hongkui Wang, “Perceptual redundancy model for compression of screen content videos,” *IET Image Processing*, vol. 16, pp. 1724–1741, 2022.

Screen content video is text, graphics, icons, and sometimes a camera picture mixed in. It is not a camera recording of a room. The authors say the eye cannot see distortion below a threshold, called just noticeable distortion, and that older models of that threshold were built for photographs. On screen content those models are too generous around sharp edges, so they allow damage the viewer does see.

Their model has three parts. Spatial redundancy splits each frame into sharp-edge areas and the rest. Text lives in the sharp-edge areas, and the damage there shows up as blur of the edge. Temporal redundancy accounts for a change in brightness between frames and for motion that can hide distortion. Foveated redundancy asks where the eye is likely to look. They class each frame from the motion between it and the previous frame: an abrupt frame, a relative-motion frame, or a static frame. An abrupt frame is a scene switch such as a slide change, a window closing, or a web page opening. In their sequences those abrupt frames show up as one frame or a few frames in a row, not as a long moving shot. Static frames and abrupt frames are more common in screen video than in camera video. Distortion on text and other high-level marks is easier to see than the same error on a photograph.

They put the model into a screen-content encoder as an adaptive quantizer. Across their tests the average bit saving was 7.42%, with a smaller drop in the viewers’ difference score than the comparison models. The comparison is against other perceptual-redundancy models, inside a codec that already has screen-content tools. It is not a comparison of two ways to sample frames before a single x264 encode.

For this project the useful part is the description of screen video, not the quantizer. A slide change or a page opening is an abrupt frame, it is short, and the sharp edges of text are the part a viewer notices. Their saving comes from compressing the less visible parts harder inside the codec. This project does not do that. It still uses one strength for the whole file. Their result is a warning as well as a support: if the text is only a few frames, a model that hides distortion during an abrupt change can treat that moment as less visible, which is the opposite of protecting it.

## 3. Scene change detection by audio and video clues

Shu-Ching Chen, Mei-Ling Shyu, Wenhui Liao, and Chengcui Zhang, “Scene change detection by audio and video clues,” *IEEE International Conference on Multimedia and Expo*, 2002.

This paper detects scene boundaries in movies and television news so that a long video can be split for indexing. A shot is a run of frames from one camera setup. A scene is a larger unit and may contain several shots. The authors say audio alone or picture alone is unreliable, because the sound can change before the picture, or a speaker can change at a shot boundary that is not a new scene.

The picture step comes first. Consecutive frames are compared at pixel level. If the difference is large enough, the frame is marked as a shot boundary. If not, they compare segmented regions, then track objects. Shots shorter than five frames are merged into the previous shot before the audio step, because hard cuts, fades, and dissolves can leave tiny fragments. Audio features are then taken over each whole shot, not over a one-second window at the boundary. A scene boundary is declared if any one of three audio distances exceeds its own threshold. On five test videos the average precision was 0.92 and the average recall was 0.89. Those numbers are for scene boundaries, not for every shot cut.

Almost none of the audio machinery applies to a silent screen recording. What does apply is the first test: a pixel comparison of neighboring frames is already a standard way to mark a hard cut. Their decision to throw away shots shorter than five frames is the opposite of this project. A twenty-frame text page is long enough to keep. An eight-frame page would be in the range they merge away, and this project’s wait of about a quarter of a second would also miss it. Their clips contain fades and dissolves. This project’s clip has none.

## 4. Seven years of TRECVid shot boundary detection

Alan F. Smeaton, Paul Over, and Aiden R. Doherty, “Video shot boundary detection: seven years of TRECVid activity,” preprint, 2009. The work covers the TRECVid shot-boundary task from 2001 through 2007.

Shot boundary detection is the step of finding where one shot ends and the next begins. From 2001 to 2007, TRECVid gave many groups the same videos, the same labels, and the same scoring. Fifty-seven groups took part. The video was mostly broadcast news and archive film, about six or seven hours a year. Transitions were labeled as hard cuts, dissolves, fades, or other. In the news years, roughly half to seventy percent of the transitions were hard cuts. Gradual transitions were often around ten frames. A gradual of five frames or less was sometimes scored as a cut.

The paper’s review of methods says a hard cut is straightforward: compare neighboring frames and look for a jump. Gradual transitions need a window of several frames, and they are harder. In 2005 the best systems had an F-score above 0.9 on cuts, clearly better than on graduals. Simple comparisons were among the methods that worked. Later, newer classifiers did not keep raising the best scores. The task was dropped after 2007 because the best systems were already good and were no longer improving.

This is background for the cut finder, not for the compression choice. On a hard cut with no fade, a comparison of neighboring frames is a solved and simple problem. That supports using a brightness difference to find the text page. It does not say what to do after the cut is found, and it does not say that the frame of the cut is the right frame to judge. The TRECVid video is edited television. A screen recording’s “cut” is a slide or a window replacing the previous picture, which is closer to their hard cut than to a dissolve. Their warning still matters: if the change is a fade rather than a cut, the simple jump test is the case their benchmark found hardest.

## 5. No-reference quality of rendered video

Sipeng Yang, Jiayu Ji, Qingchuan Zhu, Zhiyao Yang, and Xiaogang Jin, “No-reference rendered video quality assessment: dataset and metrics,” arXiv:2510.13349, 2025.

The paper is about video that a game or a graphics engine draws, not about a compressed slide. Full-reference scores such as SSIM and PSNR need the original and the test picture to line up exactly. In a game, the camera and the objects often do not line up across two renders, so those scores fail. Camera-video metrics also fail for another reason: rendered pictures are hurt by flicker and crawling edges, and people are very sensitive to that kind of change over time.

They collected ReVQ-2k, 2,000 rendered videos with 57,450 viewer scores for overall quality and for temporal stability, on phone screens and on desktop monitors. Their metric has two parts. One is an existing no-reference image model, FAST-VQA, for sharpness and still artifacts. The other estimates motion, differences the aligned frames at more than one time scale, and scores whether the picture is stable over time. They report that FAST-VQA alone gives too high a score to a clip that looks sharp but flickers. Adding the stability score fixes that. A clip can also be stable and still look bad for other reasons, so both parts are kept.

This is not a compression paper and it does not study screen text. Two points still touch the project. First, a score built for camera video, and a score that ignores how the picture changes over time, misranks rendered graphics. Second, a short-lived temporal defect can dominate what people think of the clip even when most frames look fine. That is the same shape as a twenty-frame text failure inside a thirty-second easy picture. Their fix is a learned no-reference metric. This project keeps a full-reference VMAF score and changes which frames are allowed to choose the strength.

## 6. AIM 2025 challenge on screen-content video quality

Nikolay Safonov, Mikhail Rakhmanov, Dmitry Vatolin, Radu Timofte, and the participating teams, “AIM 2025 challenge on screen-content video quality assessment: methods and results,” ICCV Workshops, 2025.

The challenge asks how to predict a viewer’s score for screen video after it has been sent through a real video-call application. The content is slides, documents, code, and interface graphics: static areas, sharp edges, and dense text. One hundred fifty source videos were sent through conferencing tools under packet loss and limited bandwidth, producing compression damage and dropped frames. About 2,400 distorted videos were scored by pairwise votes from more than 8,000 people. Voters who failed two obvious control pairs were dropped. The public set and the votes are at https://github.com/msu-video-group/AIM25_SC_Quality_Assessment.

Full-reference scores, including PSNR, SSIM, and VMAF, need every distorted frame lined up with the original. Dropped and delayed frames break that lineup, so those scores need a repair step and still may not match viewers. No-reference models trained on camera video also transfer poorly, because a screen is still for long stretches and then changes in sharp jumps.

Five teams finished with checked code. On the reported test of 30 sequences, the leading system had a Spearman correlation of 0.9045 with the viewer ranking, then 0.8471, 0.8402, 0.8198, and 0.7648. The leader did not look at every frame. It kept a key frame when the SSIM between neighbors fell below a threshold, aiming for 8 to 12 key frames, and ran a text reader on those frames so the score would reflect whether the letters were still readable. A separate branch looked at change over time.

This is evidence that screen-call quality is a different problem from movie quality, and that a practical screen score looks harder at the frames where the picture actually changed and at the text on those frames. It is not a method for choosing x264’s CRF. The distortions are whatever a conferencing app did on a bad network, including missing frames. This project compares two clean encodes of a known original, frame for frame, so VMAF can be used. Their key-frame rule is also different from a spread through the clip: they sample the changes, which is nearer to finding the cut than to eight evenly spaced frames.

## Key findings for this project

**Micó-Enguídanos et al., 2023.** A CRF can be chosen so that a segment’s VMAF meets a target, and the right CRF depends on what is in the segment. Their error on held-out segments was a mean of 1.84%. They change the CRF from segment to segment. This project still has to show that one CRF, chosen from a few frames, is enough for a whole file that contains a short text page.

**Li, Yu, and Wang, 2022.** On screen video, sharp text is the part people notice, and a slide change, a closed window, or a new web page is a short abrupt frame, often one frame or a few. A perceptual quantizer saved about 7.42% of the bits inside a screen codec. That saving is not available to a project that leaves the encoder alone and uses one strength everywhere.

**Chen et al., 2002.** A pixel comparison of neighboring frames is the usual first test for a cut. They then discard shots shorter than five frames. A text page has to last longer than that, and longer than this project’s wait, or the check never sees it.

**Smeaton, Over, and Doherty, 2009.** Hard cuts are reliably found by comparing neighboring frames. The best 2005 systems scored above 0.9 on cuts. Fades and dissolves are the hard case. This project’s clip has no fade, so the cut finder is the easy case those benchmarks already solved. The open question is what the frames after the cut do to the chosen strength.

**Yang et al., 2025.** A quality score that ignores a short temporal defect overrates a clip whose frames look fine one by one. Rendered and graphical video is not what a camera metric was built for. The lesson is about the score of the whole clip, not about a new no-reference model.

**Safonov et al., 2025.** After real screen-call compression, the systems that tracked viewers best looked at frames where the picture changed and read the text there. The leader’s agreement with the viewer ranking was 0.9045. VMAF remains usable here only because this project keeps the original and does not drop frames. Sampling the changes, rather than sampling evenly, is the comparison this project is built to test.
