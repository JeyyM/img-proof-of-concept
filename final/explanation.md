# What we are doing, in plain words

This is the version to walk through with the group. The detailed rules are in `README.md`. The picture of the order is in `flow.md`.

There are three of us. The work is one pipeline. The course grades part of it. A short conference paper grades another part. We can finish the course even if the paper’s result does not hold.

## The picture to keep in mind

Imagine a 30-second screen recording. Almost all of it is an easy picture, like a plain slide. For about two-thirds of a second, the screen cuts to a page of dense text, the kind someone has to read. Then it cuts back. Thirty seconds at 30 pictures a second is 900 pictures. The text page is 20 of them.

We compress that recording with a normal encoder, x264. We pick one strength for the whole file. A harsher strength makes a smaller file. Small text is the first thing that turns muddy.

Someone has to pick that strength. A cheap way is to look at only 8 pictures spread through the 30 seconds. Those 8 land far apart, about 4 seconds apart. The text page is shorter than that gap, so the 8 pictures can all be the easy slide. The check then says the harsh strength is fine. The file is small. The text is the part that broke.

Our way looks for the moment the picture jumps, waits about a quarter of a second so we are looking at the new page, and uses 8 pictures from that page to pick the strength. The strength stays gentler. The file is larger. The text stays closer to the quality we asked for.

## Two jobs, one pipeline

The course job has two required parts. The first is the jump finder. We compare the brightness of every pixel in one picture with the next picture, add those differences up, and do it for the whole clip. We write that sum three ways:

1. Ordinary C, one pixel at a time, with the compiler’s automatic shortcut turned off.
2. The same C, with the compiler allowed to speed it up on its own.
3. AVX2 assembly, which handles 32 pixels in one instruction.

All three must get the same total, and so the same jumps. We publish those jump positions. We time only that sum, several times, and keep the middle time. We then report two speedups: how much the compiler beat ordinary C, and how much the hand-written AVX2 beat the compiler. Loading the video, compressing it, and scoring it stay out of the clock. We do not time how long the encoder takes.

The second course part is the demonstration those jumps are for. On several different clips, we show the strength each rule chose, the quality score of that file, and the file size, with the 8 spread-out pictures set beside the 8 pictures taken after the jump. The course hand-in includes this even when the conference paper stops.

The paper job is that same file result, on the 18 real clips, written for QoMEX. The jump finder only tells us where to look. The paper asks whether looking there picks a better file than looking at 8 spread-out pictures. Its table is the strength, the 9th-worst score, how far that score sits below 90 and below 80, and the file size. The timing numbers and the speedups stay in the course hand-in. A faster sum does not, by itself, make the paper true.

## Words we will keep using

**Frame.** One picture in the video. Our clips have 900.

**Cut.** The frame where the picture jumps. We call it a cut when the average brightness change from the previous frame goes above 2.

**Settled frames.** Eight frames starting eight frames after the cut. That wait is about a quarter of a second. We want the still page, after the jump has happened.

**CRF.** The encoder’s strength knob. A higher CRF compresses more. One CRF covers the whole file.

**VMAF.** A score of how close a compressed frame is to the original. Higher is closer. Our target is 90.

**Vote.** The worst VMAF among the 8 frames a rule looked at. A rule may keep a CRF only while that worst score is still at least 90. It picks the highest CRF that still passes.

**File score.** A different number from the vote. We score all 900 frames, sort them from worst to best, and take the 9th-worst. Twenty bad frames are enough for that 9th-worst frame to land inside the text. The shortfall is how far the 9th-worst sits below 90. If it sits above 90, the shortfall is zero.

**Seed.** A saved random starting point. We commit it before we build the clips, so we cannot move the text page after we see where the 8 spread-out frames landed.

## What we make, in order

### 1. Write the rules down and stop touching them

Before any result exists, we save the decisions in the repository.

- A cut is a brightness difference above 2.
- We start sampling 8 frames after the cut. If another cut arrives first, we stop.
- Each rule looks at exactly 8 frames and uses the worst score.
- The file is judged by the 9th-worst of 900.
- The paper lives or dies at VMAF 90. We also report 80.
- The main encode uses x264, medium preset, scene-cut detection off, and a group of pictures longer than the clip. Scene-cut off means the encoder does not get to insert a fresh clean frame at the jump.
- One seed picks where the text starts in each clip, somewhere between 20% and 80% of the way through.
- Clips 1 to 18 are for practice. Clips 19 to 36 are the real test, and we score them only after the practice half has already been run.
- One seed picks 8 random frames. One seed picks the 10,000 reshuffles we use for the confidence interval.

The 8 spread-out frames are not random. They are the middles of 8 equal slices of the clip. We compute them only after the video file exists. The text’s start time is already written down by then.

If a practice clip is a bad recording, we can record it again. We do not change the 2, the 8-frame wait, or the target of 90 because a score disappointed us.

### 2. Write the three brightness sums

Same frames go into all three, on the course machine. The number of mismatched totals must be zero, and the jump lists must match. Then we time them and keep the middle run. We compute the two speedups, compiler against ordinary C, and AVX2 against the compiler. We also time one full VMAF pass once, so the table shows how small the brightness sum is next to the quality score. This table is finished for the course whether or not the paper is written.

### 3. Make one practice clip and pick the strength ladder

This clip is 900 frames and does not go in the result table. We encode it at five strengths. The five numbers should have some results above 90 and some below, so we can see the step where a rule has to stop. We freeze those five numbers. Later clips use the same five.

### 4. Make the real clips

Thirty-six clips. Each one has its own easy picture and its own page of dense text. The text is on screen for exactly 20 frames. No fade. The start time comes from the seed we already saved. Eighteen are the practice half. Eighteen wait.

Then six more recordings of ordinary screen activity, also 900 frames, with no planted text page. Same checks. Separate table. They do not decide whether the paper continues.

### 5. Check that a clip is usable

On the easy stretch, at least half of the frame-to-frame brightness changes should be 2 or less. The easy part really is sitting still. If a clip fails that, we replace the clip. We do not lower the number 2.

### 6. Run the practice half

For each of the 18:

1. Find the cuts.
2. Encode the five strengths with scene-cut off.
3. Score every frame of every encode with VMAF.
4. From that one list of scores, take five groups of 8 frames: settled frames, spread-out frames, random frames, frames that start on the jump, and the 8 most detailed frames.
5. Each group votes. Write down the CRF it chose, the 9th-worst score of that file, the shortfall at 90 and at 80, and the file size.

### 7. Run the real half the same way

Clips 19 to 36 use the same steps and the same five strengths. This table is the one the paper stands on.

On this half only, we encode once more with the encoder’s normal scene-cut setting turned back on, at the same CRF numbers. We report that beside the main table. It does not, on its own, end the paper.

On the files we already chose, we add three extra columns. They do not pick the strength. They only describe the file: a looser percentile (about the 45th-worst frame), a second kind of picture score pooled the same way, and a text-reading check on the 20 text frames.

Then we compare, clip by clip, how far the settled-frame file missed 90 with how far the spread-out file missed 90. We report the average gap, how many clips went each way, and a confidence interval from 10,000 reshuffles of that comparison.

### 8. Ask people only if the files are far enough apart

This part is optional. We do it when at least four real-half pairs differ by 10 points on the 9th-worst score. We invite 24 people so that 16 can remain after a short screening. Each person sees about 10 seconds around the text, including a hidden original. They are not told which file is which. They say how the video looks, and whether the text is easy to read. The readability answers are the ones we care about. We add them to the paper only if the gap clearly favors the higher score.

### 9. Hand in the course work either way

The course hand-in stands on its own. It needs:

- The source for all three sums, and a short discussion of how the parallel version works.
- The jump positions from each version, which must match.
- The middle time of each version, and the two speedups.
- The compression demonstration: for the clips already scored, the strength each rule chose, the 9th-worst score, the shortfall, and the file size, with spread-out frames beside settled frames.

The mid-project demo is that pipeline on a small scale. The three sums agree. One clip is at its saved start time. The five strengths exist. A first timing table, with speedups, exists. One shortfall at 90 has been computed from all 900 frame scores. A few clips with different pictures have been run, enough to show that the jump finder and the strength choice both finish.

### 10. Write the paper only if the real half says so

The paper continues when, at target 90, with scene-cut off, the settled-frame files miss 90 by less than the spread-out files, on average, and on most of the 18 real-half clips.

The paper is 3 pages plus a page of references, for QoMEX 2027 in Shanghai. The meeting is 6–9 July 2027. The short-paper deadline is 1 May 2027. It would be a poster.

The table shows the strength each rule chose, the 9th-worst score, the shortfall at 90 and at 80, and the file size. It includes the other ways of picking 8 frames, the confidence interval, the scene-cut-on column, and the rows where the two main rules tie. The opening paragraph says what the clips are: scripted screen recordings, one strength for the whole file, and a text page short enough to hide from 8 spread-out frames.

If that test fails, we stop at the course hand-in. The course work is still complete.
