# How the three of us split the work

Put a name on each seat at the start. The seats are meant to run together and to land at about the same amount of work. Swap seats if someone is already stronger at assembly, at making clips, or at the scoring scripts. The rules and the seeds are agreed by all three before any of that work counts.

A few steps have to wait. Those are marked. Everything else can move at the same time.

## Seat 1. The brightness sum

This seat carries the course grade.

- Ordinary C, one pixel at a time, with automatic vectorization turned off.
- The same C with compiler optimization on.
- AVX2 assembly, 32 bytes at a time, plus a short loop for the leftover pixels.
- One small program that runs all three on the same frames and counts mismatches. That count must be zero.
- The cut positions from all three versions. They must be the same list.
- The timing table: several runs of each version, the median of each, and one full VMAF pass beside them so the sum can be seen next to the score. The clock covers only the sum. Encode time is not recorded.
- The two speedups: compiler-optimized C against ordinary C, and AVX2 against compiler-optimized C.
- The course write-up: how the three sums work, the matching cut lists, the medians, and the speedups.

This is the hardest code, and it finishes before the clip list does. When the three sums match, Seat 1 takes one third of the encode queue below and runs the cut finder on every clip.

## Seat 2. The clips

This seat makes the files everyone else measures.

- The clip builder: 1920 by 1080, 30 frames a second, exactly 900 frames, a hard cut, no fade.
- The throwaway clip, then the picture pairs for all 36 scripted clips. Each pair is its own easy picture and its own dense text page. The text lasts exactly 20 frames.
- The start time of each page, taken from the shared seed, written down before the eight spread frames are computed.
- The six ordinary screen recordings, 900 frames each, with no planted text page.
- The stillness check. On the easy stretch, at least half the frame-to-frame brightness changes are 2 or less. A clip that fails is replaced. The number 2 does not move.
- A log of every clip: name, which half it belongs to, start frame, and whether the stillness check passed.

The practice half is clips 1 to 18. The real half is clips 19 to 36. Both halves can be built as soon as the seed exists. Only the scoring of 19 to 36 has to wait.

## Seat 3. The scores

This seat carries the paper’s evidence.

- Encode one clip at five strengths with x264, medium preset, scene-cut off, and a group of pictures longer than the clip.
- Score every frame of every encode with VMAF against the uncompressed clip.
- From that one list, compute the five votes: settled frames, spread frames, random frames, frames on the cut, and the eight most detailed frames. Each vote is the worst of its eight scores. The strength that ships is the highest of the five whose vote is still at least 90.
- Write one result row per clip: the strength each rule chose, the 9th-worst score of that file, the shortfall at 90 and at 80, and the file size.
- On the real half only, the same rows with scene-cut left on.
- The extra columns that do not pick the strength: the 45th-worst score, MS-SSIM pooled the same way, and a text-reading score on the 20 text frames.
- The confidence interval: 10,000 reshuffles of the 18 real-half gaps, from the shared seed.

Seat 3 can build and test all of this on the throwaway clip while the other clips are still being made.

## Together, before anyone splits off

One short sitting, all three:

- Freeze the rules: cut threshold 2, wait of 8 frames, vote of 8 frames, file score is the 9th-worst of 900, target 90, scene-cut off for the main encode.
- Save the seeds: page start times, the eight random frames, and the 10,000 reshuffles. Clips 1 to 18 are practice. Clips 19 to 36 are the real test.
- Agree the brightness-sum inputs and outputs, so Seat 1’s three versions can be compared.
- Agree the clip file layout, so Seat 2’s files drop straight into Seat 3’s scorer.

## The throwaway clip

Seat 2 builds it. Seat 3 encodes it at a spread of strengths. All three look at where the scores sit around 90, and together pick the five strengths that bracket that line. Those five numbers are then frozen. Later clips use the same five. The throwaway clip does not enter the result table.

## While the practice clips are being made

| Seat 1 | Seat 2 | Seat 3 |
| --- | --- | --- |
| Finish the three sums until the mismatch count is zero | Build clips 1 to 18 and run the stillness check | Get the scorer working on the throwaway clip |
| Time them and fill the timing table | Keep the clip log | Produce one full result row from the throwaway clip |
| Start the cut finder on each practice clip as it passes the stillness check | Start clips 19 to 36 and the six ordinary recordings | Score each practice clip as soon as its file and its cuts exist |

Practice scores may show a broken clip. That clip goes back to Seat 2 to be replaced. A practice score does not change the threshold, the wait, the 9th-worst rule, or the target.

## The encode queue

Scoring a 1080p clip at five strengths is the long wait. Once the scorer works and a clip has passed the stillness check, any of the three can run it. Split the list into three piles of equal size, including the six ordinary recordings.

Each person runs their pile: five strengths with scene-cut off, then VMAF, then the result row. Seat 3 checks that every row has the same columns. Seat 1’s cut list is the one the row uses, because that list came from the sums that were shown to match.

On the real half, add a second encode with scene-cut left on, at the same five strengths. Split those 18 the same way.

## The gate before the real scores

Clips 19 to 36 can already exist. Their scores wait until all three of these are true:

1. Clips 1 to 18 have result rows.
2. The group has looked at those rows only to find broken captures.
3. Nobody has edited the threshold, the wait, the percentile, the five strengths, or the seeds.

Then the same scorer runs on clips 19 to 36. Seat 3 builds the average gap, the count of better, tied, and worse, and the confidence interval. That table decides the paper.

## The mid-project demo

This needs one piece from each seat, so it is a shared deadline:

- Seat 1: the three sums agree on one clip, and a first timing table exists with both speedups.
- Seat 2: that clip is at the start time the seed already wrote down, and a few clips with different pictures have already passed the stillness check.
- Seat 3: the five strengths exist, and one shortfall at 90 has been computed from all 900 frame scores, with the file size beside it.

## Writing

Two documents, written while the real half is encoding.

**Course hand-in, Seat 1 leads.** This is required even when the paper goes ahead, and it is still required if the paper stops. Seat 1 writes the source, the discussion of the three sums, the matching cut lists, the median times, and the two speedups. Seats 2 and 3 add the compression demonstration the course also requires: on the clips already scored, the strength each rule chose, the 9th-worst score, the shortfall, and the file size, with spread frames beside settled frames. Encode times stay out. The medians and the speedups stay in this hand-in and out of the QoMEX paper. Seats 2 and 3 read the discussion for any file claim the table does not support.

**Short paper, only if the real half says so.** Three pages plus references.

- Seat 2 drafts what the clips are: 900 frames, a 20-frame text page, the seed, the practice half and the real half.
- Seat 3 drafts the table and the interval: strength, 9th-worst score, shortfall at 90 and at 80, file size, the other ways of picking eight frames, scene-cut on, and the rows where the rules tie.
- Seat 1 drafts the short method note that the cut is a brightness difference above 2. The medians and the speedups stay out of this paper.
- All three edit the abstract. It states the file result and the fence around it: scripted screen clips, one strength for the whole file, a page short enough to hide from eight spread frames.

If the real half does not favor the settled frames, the paper stops. The course hand-in still happens.

## If the viewing session qualifies

This is extra, and it is shared. It happens only when at least four real-half pairs differ by 10 points on the 9th-worst score.

- Seat 2 prepares the 10-second excerpts around the text, with the hidden original.
- Seat 3 prepares the answer sheet: overall quality, and whether the text is easy to read.
- All three recruit. The aim is 24 people, so 16 remain after screening.
- One person runs the session. The other two log the answers.
- Seat 3 adds the readability gap only if its confidence interval stays entirely on the side of the higher score.
