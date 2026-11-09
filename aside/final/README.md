# Choosing one compression strength from the frames after a cut

Juan Miguel Miranda, Jean Khladyn Stefanie Abarquez, and Kimberly Klaire Gamboa.

This folder is the project you will build and write up. The rest of the repository is earlier exploration. Those trials are not the result table, and they do not freeze any rule.

The approved proposal does two jobs with one pipeline. The course grades a brightness comparison written three ways: identical answers, a timing table, and the speedups. It also grades a working path from those cuts to a chosen compression strength, with the quality score and the file size. The paper grades only that file. A faster comparison does not, by itself, make the paper true, and the timing numbers do not go into the paper.

## What each grade measures

**Course.** Three sums of the same brightness difference: ordinary C with vectorization off, the same C with compiler optimization on, and AVX2 assembly. They must return the same totals and the same cut positions. The clock covers only that sum, after the frames are in memory, over several runs. The reported time is the median. Two speedups are required: compiler-optimized C against ordinary C, and AVX2 against the compiler-optimized C. Decoding, encoding, and VMAF stay outside the clock. Encode time is not a result. The course hand-in also includes the compression demonstration from the approved proposal: the strength each rule chose, the quality score of that file, and its size, on several clips, including spread frames against frames taken after a detected change.

**Paper.** For each held-out clip and each way of picking eight frames: the CRF chosen, the 9th-worst VMAF of that file, the shortfall below 90 and below 80, and the file size in bytes. The comparison that decides the paper is settled frames against evenly spread frames, at 90, with scene-cut off. Beside it: the confidence interval, the scene-cut-on column, and the other eight-frame rules. The 45th-worst VMAF, an MS-SSIM score pooled the same way, and a text-reading score on the 20 text frames are extra columns. They do not choose the CRF. Viewer ratings are added only if that session qualifies. Medians, speedups, and the three-way timing table stay out.

## What happens, from the first frame to the last table

A screen recording is often an easy picture with one short page that someone has to read: a slide, a menu, a formula, a table. The page in this study lasts 20 frames, about two-thirds of a second, inside a clip of 900 frames (30 seconds at 30 frames per second, 1920×1080). There is a hard cut onto that page and a hard cut back. There is no fade.

The encoder is x264, left as it is. One quality knob, CRF, is chosen for the whole file. A higher CRF compresses more and makes a smaller, rougher file. Fine text is the first thing that breaks.

Someone still has to pick the CRF. A common cheap check looks at eight frames spread evenly through the clip. Those eight frames sit about 112 frames apart. A 20-frame page fits in that gap, so the check can see only the easy picture and accept a harsh CRF. The file gets smaller. The text is the part that suffers.

This project finds the cut without being told the script. It compares each frame with the next by the mean absolute difference of pixel brightness (the luma plane). A cut is the first frame where that difference rises above 2, on 8-bit luma. The sample does not use the jump itself. It waits 8 frames, about a quarter of a second, so it sits on the new picture, then takes the next frames of that same picture until it has eight. Those eight frames vote by their worst score.

Both rules do the same thing with their vote. Each encodes the clip at several CRF values and may keep a CRF only while its own eight scores are still at least 90 on VMAF, a standard full-reference quality score. The rule picks the highest CRF that still passes. The same vote is also taken from eight random frames, from eight frames that start on the cut, and from the eight most detailed frames. All of those votes are lookups into one saved list of 900 frame scores. They do not need extra encodes.

The finished file is then judged by a stricter mark than the vote. The 900 frame scores are sorted from worst to best, and the 9th-worst is the file’s result. That is the 1st percentile of a clip this long, and it can fall inside a 20-frame page. The shortfall is how far that score sits below 90, or zero if it sits at or above 90. File size is published beside the shortfall. A closer score that came from a larger file still has to show the size.

A gentler percentile would miss the same page. The 5th percentile of 900 frames is about the 45th-worst frame. Twenty bad frames are fewer than that, so that mark can sit on the easy picture while the text is already poor. The 5th percentile is reported so this can be seen. It does not choose the CRF.

The decision encode turns x264’s own scene-cut detection off and uses a group of pictures longer than the clip, so the cut does not become a fresh keyframe. A second encode, on the held-out clips only, puts the ordinary scene-cut and keyframe settings back. That column shows whether the result depends on the encoder refusing to reset the picture at the cut.

Thirty-six scripted clips each use their own easy picture and their own dense text. The start of the text is drawn once, from a seed, between 20% and 80% of the clip, and written down before the eight even frames are computed. The text is not parked in a gap after the fact. Eighteen clips are a development set. Eighteen are held out and scored only after the pipeline has already been run. One pilot clip places the CRF ladder and does not enter the result table. Six further recordings are ordinary screen activity, with no planted 20-frame page. They are a separate table. They do not decide the paper.

The paper’s own kill line is narrow. At VMAF 90, on the held-out eighteen, under the scene-cut-off encode, the files chosen from the settled frames must miss 90 by less, on average, than the files chosen from eight even frames, and they must do so on a majority of those clips. If both of those fail, the short paper stops. The course work remains. A target of 80 is the same table and does not end the paper. A larger file does not end the paper. A tie with the random sample, the cut sample, or the high-detail sample is reported and does not, by itself, end the paper.

## Why this is a QoMEX paper

QoMEX is the International Conference on Quality of Multimedia Experience. The 2027 meeting is in Shanghai, 6–9 July. Short papers are focused studies: 3 pages plus one page of references, due 1 May 2027, with a decision on 18 May. They are reviewed by at least two people and presented as posters. The year’s banner is generative and immersive media. The general track still includes multimedia quality and Quality of Experience, which is where this study sits.

The paper is good for that slot because it is one measurement, with a result a reader can check. Lecture uploads and software tutorials are signed off with a small sample and a single score for the file. This study shows a case those two checks can agree on and still get wrong: the sample misses a short page, a 5th-percentile score also misses it, and a score tight enough to land inside the page does not. The fix under test is cheap and uses tools the field already trusts. The cut finder is a brightness comparison, which is the standard easy case for a hard cut. The compressor is not rewritten. The quality model is not trained. One CRF still covers the whole file. What changes is which eight frames are allowed to set that CRF.

That is a counter-example to a usual check, which is the kind of short paper this meeting accepts. The claim stays inside the clips that create the miss: a short dense page in a long easy stretch, no fade, one strength for the file. The table has to show the cost in bytes, the scene-cut-on column, and the cases where the two rules tie (a page too short to move the 9th-worst frame, a picture that is already hard, a page long enough that the spread hits it). The six ordinary recordings, and any row where the first settled page is the easy one, stay outside the kill line and inside the paper. A reader can see where the result stops.

A viewing session makes the paper stronger, and it is not required to submit. It is added only when at least four held-out pairs differ by 10 points on the 9th-worst score and at least sixteen screened viewers remain. The question that matters is whether the text is easy to read. The confidence interval of that difference has to lie entirely on the side of the higher score. If the session is missing, the short paper is the measurement table.

The abstract leads with the file result. The timing table is the course chapter. QoMEX is not being asked to care how fast the brightness sum ran.

## What you build

On one machine, an AMD Ryzen 9 5900HS with 16 GB of RAM, Windows 10, and GCC:

1. Ordinary C, one pixel at a time, with automatic vectorization turned off.
2. The same C, with compiler optimization on, so GCC may vectorize it itself.
3. AVX2 assembly that handles 32 bytes at a time, with a short ordinary loop for the leftover pixels.

All three see the same decoded frames, on the course machine. They must return the same totals and the same cuts. The clock covers only that sum, after the frames are in memory. Decoding, encoding, and VMAF stay outside the clock. Each version is run several times. The reported time is the median. The course table includes the two speedups: compiler-optimized C against ordinary C, and AVX2 against compiler-optimized C.

Everything else is sequential: choosing when the text appears, decoding, encoding, scoring all 900 frames, reading eight scores, and picking one CRF.

## Steps

Do them in this order. Development clips may show a broken capture. They may not change the threshold, the 8-frame wait, the budget of eight, the percentile, or the target.

1. **Freeze the rules in the repository before any held-out score exists.** Cut threshold 2. Settled sample starts 8 frames after the cut and stops if the next cut arrives sooner. Vote is the minimum of the eight VMAF scores. File score is the 9th-worst of 900. Kill target is 90. Decision encode is libx264, preset medium, scene-cut off, group of pictures longer than the clip. Commit the seed for the text start times, the random-frame draw, and the bootstrap.

2. **Write the three brightness comparisons and prove they match.** Run them on the same frames. The count of disagreeing totals is zero, so the cuts match. Publish the cut positions from each version. Time them by the median. Compute the two speedups. Put one full VMAF pass in the same table so the sum can be seen next to the score. This table is a course requirement even when the paper goes ahead.

3. **Make one pilot clip and place the CRF ladder on it.** The pilot is 900 frames and is not in the result table. Five CRF rungs are enough if neighbors fall on either side of 90. The ladder is frozen before anyone looks at which rule wins.

4. **Draw the thirty-six clips, then build them.** Eighteen development, eighteen held out, each with its own easy picture and its own dense text, exactly 20 frames, start time from the seed between 20% and 80% of the clip. Compute the eight even-frame centers only after the file exists. Add six ordinary screen recordings of 900 frames with no planted page.

5. **Check each capture before scoring it.** On the easy hold, at least half the frame-to-frame brightness differences should be at or below 2. A capture that fails is replaced. The threshold is not moved.

6. **Run the pipeline on the development half.** Detect cuts. Encode the frozen ladder with scene-cut off. Score every frame of every encode with VMAF against the uncompressed clip. From that one list, compute every rule: settled frames, even frames, random frames, frames on the cut, and the eight most detailed frames. Record the CRF each rule chose, the 9th-worst score of that file, the shortfall at 90 and at 80, and the file size.

7. **Leave the rules alone.** If a development clip is broken, replace the capture. Do not retune the wait, the threshold, or the percentile because of a score.

8. **Run the same pipeline on the held-out half.** This is the table the paper stands on. Add the scene-cut-on encode for these eighteen only, using the same CRF numbers, and report it beside the main table. It is not a second kill line.

9. **On the files already chosen, add the checks that do not pick the CRF.** The 5th percentile and the minimum of the 900 VMAF scores, MS-SSIM pooled as the same 9th-worst frame, and a text-reading score on the 20 text frames.

10. **Compute the held-out interval.** For each held-out clip, subtract the even-frame shortfall from the settled-frame shortfall at target 90. Report the mean, how many clips are better, tied, or worse, and a 95% bootstrap interval from 10,000 resamples of that paired difference.

11. **Run the viewing session only if it qualifies.** Recruit 24 people. Include the ratings only when at least four held-out pairs differ by 10 points on the 9th-worst score and sixteen viewers remain after the usual screening. Show about ten seconds around the text, with a hidden reference. Ask about overall quality and whether the text is easy to read. Report the readability difference.

12. **Write the course repository either way.** This hand-in does not wait on the paper. It contains the source, a discussion of the parallel sum, the three cut lists, the median times, and the two speedups. It also contains the compression demonstration: on the clips already scored, the strength each rule chose, the 9th-worst score, the shortfall, and the file size, with spread frames set beside settled frames. The Week 10 demo is the same pipeline in miniature: the three comparisons agree, one clip exists at its committed start time, the ladder exists, a preliminary timing table with speedups exists, and one shortfall at 90 has been computed from a full frame-by-frame score. Several clips with different pictures are part of that demo, enough to show that the cut finder and the strength choice both finish.

13. **Write the short paper only if the kill line holds.** Three pages plus references. One table of the held-out clips: CRF, 9th-worst score, shortfall at 90 and at 80, file size, for the settled sample and the even sample, with the other samples in the same table. The interval, the scene-cut-on column, and the boundary rows go in. The abstract states the file result and the fence around it: scripted screen clips, one strength for the whole file, a page short enough to hide from eight spread frames.

If the kill line fails, stop at step 12. The course submission is complete without the paper.
