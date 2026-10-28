# Study results

Seed 20261010. Text starts were drawn before any even-frame collision was repaired.
Seeded slides: 12. Draws that landed on an even sample: 0.

Screen clips with both choices: 15. Different CRF on 15 of them.
Mean shortfall gap, including the blank frame: 12.22.
95% bootstrap interval, including the blank frame: 8.52 to 17.79.
Mean shortfall gap without the blank frame: 9.74.
95% bootstrap interval without the blank frame: 8.09 to 11.32.
Twelve generated slides, mean shortfall gap: 10.63.
Twelve generated slides, mean CRF step (spread minus text-aware): 6.25.
On screen clips where the rules differed, the text-aware file was 1.36 times the spread file, on average.
Spread-chosen screen files whose 9th-worst frame is inside the text and whose 45th-worst frame is outside it: 15 of 15.

A positive gap means the spread-out file misses 90 by more than the text-aware file.
The interval is a 10,000-draw bootstrap of that paired gap, seed 20261010, using the 2.5 and 97.5 percentiles.

Boundary clips (cat, gravel, leaves) are not in the mean above.
Boundary cat: spread CRF 28, text CRF 28, shortfall 0.00 vs 0.00, 9th frame 111, 45th frame 278.
Boundary gravel: spread CRF 28, text CRF 28, shortfall 0.00 vs 0.00, 9th frame 110, 45th frame 263.
Boundary leaves: spread CRF 28, text CRF 28, shortfall 0.00 vs 0.00, 9th frame 11, 45th frame 42.

Scene-cut rows leave x264's scene-cut detection on. Chart and news only.
Scene-cut chart-scenecut: spread CRF 35, text CRF 32, shortfall 3.21 vs 0.00, 9th frame 107.
Scene-cut news-scenecut: spread CRF 32, text CRF 32, shortfall 0.00 vs 0.00, 9th frame 17.

Hold rows use the title slide, text starting at frame 400.
An 8-frame hold ends before the quarter-second wait, so the text-aware rule has no frames.
Eight bad frames also cannot fill the 9th-worst slot, so the file score can still clear 90.
Hold 8: spread CRF 35 shortfall 0.00, text CRF none shortfall none, spread 9th frame 408.
Hold 20: spread CRF 35 shortfall 8.49, text CRF 29 shortfall 0.00, spread 9th frame 417.
Hold 60: spread CRF 35 shortfall 5.11, text CRF 31 shortfall 0.00, spread 9th frame 411.

No real screen recording was made. The clips are still pictures joined in software.

No viewers were recruited. viewer_pairs.csv lists the screen clips whose two rules chose different files.
Those files were not shown to anyone, and no opinion scores were created.

OCR is the mean, across the 20 text frames, of how much that frame's read lines up with the reference read.
The harsh row is CRF 44, kept as a check that the reader can fail. It is not a file either rule chose.
An empty OCR cell means the engine read nothing on the clean text page.

OCR chart text CRF 30: mean 1.00, worst frame 0.99
OCR chart spread CRF 34: mean 1.00, worst frame 1.00
OCR chart harsh CRF 44: mean 0.01, worst frame 0.01
OCR news text CRF 29: mean 1.00, worst frame 1.00
OCR news spread CRF 32: mean 1.00, worst frame 1.00
OCR news harsh CRF 44: mean 0.10, worst frame 0.07

See decisions.csv for every clip, including the 9th-worst and 45th-worst frame numbers.
