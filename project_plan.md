# Project Plan: Choosing a Publishable Direction

Advanced Computer Architecture integrating project, 1st Term 2026–2027. Group project. The course requires a data-level parallelism proof of concept. This group also wants a conference paper to be the main outcome.

**Decision:** build a vectorized side-window smoothing filter. The paper’s claim is a shared-sum layout that produces all eight overlapping windows from one streaming pass, with the same pixels as the scalar definition. Platform is AVX2. AVX-512 is a second measurement only if a lab machine has it.

Gaussian blur plus Sobel stays the fallback if that claim fails the checks in section 8. The fallback still finishes the course. It does not carry a paper.

## 1. What we are deciding

Two goals, in this order for topic choice:

1. A result a reviewer can accept: a specific transform, a competent baseline, and a measurement that could have gone the other way.
2. The course proof of concept: one algorithm rewritten for SIMD or SIMT, a sequential version of the same program, and an execution-time comparison.

The course lists the paper as optional. Treating it as the main goal changes the topic. A correct, fast blur is enough for the milestones. It is not enough for a paper.

## 2. Course constraints that every direction must meet

- Data-level parallelism only. One platform: CUDA (SIMT) or AVX / AVX2 / AVX-512.
- The algorithm has to be transformed so the same operation applies to many data elements at once.
- Scope is a module or a proof of concept, finished on the course calendar: proposal in Week 6, mid-project demo in Week 10, full submission in Week 13.
- Week 13 repository needs source, a discussion of the parallel algorithm, and sequential-versus-parallel timing.
- The proposal outline still has to be written: abstract, inputs, what is parallelized, prior work and the difference, the parallelization plan, what stays sequential, outputs, platform, mid-project milestone, references.

## 3. What “publishable” means for this calendar

Flagship venues are out of range for a seven-week implementation. PPoPP, SC, ISCA, and CVPR are where stencil layout and edge-aware filters are already being published by groups with compilers, multi-machine studies, and prior systems.

A realistic target is a workshop short paper or a regional IEEE conference paper: one technique, one machine family, reproducible code, and a comparison against more than a naive loop. IEEE Access asks for a clear advance and accepts about 20% after prescreening. A course port of a known filter does not clear that bar. A small technique with an accuracy bound and a strong baseline might, after the course, if the result holds.

Reviewers reject this shape of paper:

- Speedup against a scalar pixel loop only.
- A reimplementation of a filter that OpenCV, Intel IPP, NVIDIA NPP, or a 2024–2025 paper already tunes.
- A quality improvement with no architectural transform, which belongs to a vision venue and does not satisfy this course.

The paper needs both of these numbers: speedup against a competent baseline, and proof that the output matches the scalar definition (maximum absolute error, plus PSNR or SSIM on a fixed image set).

## 4. What recent work already closed

These are the neighbors a reviewer will cite. They are why three of the four directions below are weak.

| Closed ground | Where it was closed | What that means for us |
|---|---|---|
| Vectorized fixed-weight stencils (blur, Sobel, scientific stencils) on AVX2 and AVX-512 | Jigsaw, PPoPP 2025, reports 2.31× over prior vectorized stencils by removing register-lane conflicts. SC 2021 already studied AVX-512 stencil redundancy, tiling, and frequency throttling. | A paper whose contribution is “our AVX blur beats our scalar blur” has nowhere to stand. Beating Jigsaw is not a course-sized project. |
| Stencils rewritten as matrix multiplies on GPU tensor cores | ConvStencil, PPoPP 2024. | Tensor-core convolution is a different project and a higher bar. |
| Variable-weight convolution on x86 SIMD, including bilateral-style range weights | Naganawa et al., IEEE Access 2024. Register-resident lookup tables on AVX2 and AVX-512, about 4.8× / 3.7× over direct vector computation, with PSNR reported. Code was released. | “SIMD bilateral filter” is taken. A follow-on has to beat that paper on its own benchmark, which means competing with the group that owns the method. |
| Non-local means and bilateral filters on CUDA | Multiple GPU papers since the early 2010s, including shared-memory prefetch studies. | A CUDA port that is faster than a scalar CPU loop repeats those papers. |
| Ordinary weighted median and guided median | Zhang et al., CVPR 2014 (joint-histogram weighted median). Fast Guided Median Filter ships CPU (AVX2) and CUDA code. | Median itself is an old SIMD target (branchless sorting networks). The open piece is narrower than “implement a median.” |

Gaussian blur, Sobel, bilateral filtering, and generic stencil vectorization are demonstration topics. They are poor paper topics in 2026.

## 5. Directions compared

Scores are publication potential if the group executes the evaluation properly. 1 means a course report. 5 means a plausible workshop or regional-conference paper. None of these scores mean a flagship paper.

| Direction | Course fit | Finishes by Week 13 | Publication potential | Why |
|---|---|---|---|---|
| A. Gaussian blur and Sobel, AVX or CUDA | Strong | Easy | 1 | The required course comparison, and a solved research problem. Keep as the fallback demo. |
| B. AVX2 versus AVX-512 separable convolution, with shuffle, gather, and boundary masks | Strong | Medium | 2 | The interesting effects (lane conflicts, AVX-512 frequency loss, gather cost) are already measured by Jigsaw and the SC 2021 stencil paper. High chance of rediscovering a known result. |
| C. Bilateral or non-local means, faster than our scalar code | Strong | Medium | 2 | CUDA versions are numerous. The CPU SIMD version was published in IEEE Access in 2024 with a stronger baseline than “scalar.” |
| **D. Side-window smoothing with a shared-sum vector layout** | **Strong** | **Medium** | **4** | The filter is still a per-pixel stencil, so it satisfies the course. The eight windows overlap, so a layout that reuses sums is a real transform. No AVX study of that reuse showed up in a search of the current literature. The claim can fail, which is what makes it a result. |
| E. A module of an existing thesis | Depends on the thesis | Depends | 3 to 5 | Best option if the group already has an open thesis claim whose hot loop is data-parallel. There is no thesis topic on record in this folder, so E is unavailable until someone names one. |

Direction D is the one to write the proposal around.

## 6. Recommended direction

### The filter

Side-window filtering (Yin, Gong, and Qiu, CVPR 2019) smooths a pixel using a window that sits beside the pixel, on the same side of an edge, instead of a window centered on the pixel. For each pixel the algorithm:

1. Builds eight windows (left, right, up, down, and four corners) of radius \(r\).
2. Computes a box mean in each window, plus the variance.
3. Writes the mean of the window with the smallest variance.

Centered blur mixes colors across edges. The side-window rule is an attempt to avoid that. The original paper is about image quality. This project is about the data-parallel form of the same definition.

### The claim

A centered blur is one window per pixel. Side-window smoothing is eight. Those eight rectangles overlap, and each needs a sum and a sum of squares.

The claim to test:

> Eight side-window means and variances can be produced from one pair of separable streaming sums (sum and sum of squares), vectorized across each row, so the edge-preserving result matches the scalar definition and costs less than eight independent stencil passes and less than a compiler-vectorized scalar implementation.

That sentence is the paper. If the shared layout is no faster than eight simple vectorized passes, the result is still reportable and the course demo still exists. The paper gets weaker. Section 8 says when to drop the paper goal.

### Why this can be a paper and blur cannot

- The operation on each pixel is the same, which is the course requirement.
- The transform is specific: shared separable sums, vector width, border handling, then an element-wise argmin. It is not “we added AVX.”
- Output equality is checkable. The parallel code must match the scalar code bit for bit, or within a stated rounding tolerance.
- Prior work a reviewer will accept as different: the CVPR 2019 filter paper (quality), Jigsaw (fixed-weight stencils), and Naganawa et al. 2024 (variable weights via register lookup tables). This project is fixed box sums with an eight-way selection.
- The pictures make the Week 10 demo.

### What is parallel, and what stays sequential

Parallel:

- Row-wise streaming sums and sums of squares, several pixels per AVX2 register.
- The eight rectangle reductions derived from those sums.
- Per-pixel variance and argmin across the eight windows.

Sequential:

- Image read, grayscale conversion, and write.
- Choice of radius and any timing harness setup.
- A scalar remainder when the row width is not a multiple of the vector width, reported separately so it is not hidden inside the kernel time.

### Platform

AVX2 on a CPU the group already has. Intrinsics are acceptable for development. The inner streaming sum should be written so the AVX2 instructions are visible, and the final version can be assembly if the course staff expect assembly rather than intrinsics. Confirm that with the instructor before Week 6.

AVX-512 is optional and only as a second width on a machine that actually supports it. Many laptops do not. The paper must not depend on it.

CUDA is a valid course platform for the same algorithm (a tile in shared memory, eight partial sums, an argmin). It is the second choice. CUDA box filters and integral images are common teaching samples, so the same claim is harder to distinguish from coursework. Use CUDA only if the group has a reliable NVIDIA GPU and no AVX2 machine, which is unlikely.

Do not implement both. One platform, one claim.

### Baselines the paper has to beat

The course requires the first. The paper requires all four.

1. Scalar C of the same eight-window definition, same compiler, optimizations on.
2. That scalar code compiled with auto-vectorization enabled, so the paper shows the hand-written layout beating the compiler.
3. Eight independent vectorized passes, the obvious SIMD version without shared sums.
4. A library box or stack blur only as context for throughput. It is a different filter, so it is not the correctness baseline.

Report kernel time separately from file I/O. Use several image sizes, including one that fits in L2 and one that does not. Fix the radius and also sweep it, because overlap reuse matters more as \(r\) grows.

### Inputs and outputs

- Inputs: grayscale 8-bit images, a small fixed set committed to the repo, plus radius \(r\).
- Outputs: the smoothed image, an edge-difference image against centered blur (for the demo), a timing table, and an error table against the scalar result.

## 7. How this maps onto the proposal

The Week 6 document can follow the expanded outline directly.

| Outline item | Content |
|---|---|
| 0. Abstract | Side-window smoothing rewritten as shared vector sums. Claim as in section 6. |
| 1a. Inputs | Grayscale images and radius. |
| 1b.i What is parallel | Streaming sums, eight window reductions, argmin. |
| 1b.ii Existing work | CVPR 2019 side-window filter; separable box filters; Jigsaw; Naganawa et al. 2024. Difference: those either study quality, fixed centered stencils, or variable weights. |
| 1b.iii Plan | Scalar reference, then shared-sum AVX2, then the obvious eight-pass AVX2 version used as an ablation. |
| 1b.iv Not parallel | I/O, setup, width remainder. |
| 1c. Outputs | Image, timings, error against scalar. |
| 2. Platform | AVX2 CPU. Name the exact CPU in the proposal once the group picks the measurement machine. |
| 3. Mid-project milestone | Week 10: scalar and one correct AVX2 kernel on one image, plus a first timing. State this explicitly; the brief requires it. |
| 4. References | The papers in section 4 and section 6. |

## 8. Checks before this is locked, and kill criteria

Do these before the proposal is submitted.

1. Search again for an AVX, CUDA, or integral-image implementation of side-window filtering published after 2019. The decision assumes that gap. If a paper already reports shared box sums for this filter on x86, switch the claim or switch the direction.
2. Confirm the measurement CPU supports AVX2 and record the model, base clocks, and cache sizes.
3. Ask the instructor whether intrinsics satisfy “AVX assembly,” or whether the graded kernel must be written as assembly.

Kill the paper claim, and fall back to direction A for the course grade, if any of these is true at the Week 10 demo:

- The shared-sum kernel does not match the scalar output within the stated tolerance.
- It is under about 1.2× the eight independent vectorized passes at the radii that matter. A layout with no gain is not a paper.
- The kernel is slower than compiler auto-vectorization of the scalar code.
- The group cannot name a baseline beyond its own first implementation.

Week 10 is the decision point. After that, either the paper has evidence or the remaining weeks go into a clean course submission.

## 9. Milestones

| When | Course requirement | Research requirement |
|---|---|---|
| Week 6 | Proposal in the expanded outline | Claim, platform, baselines, and the literature gap written down |
| Week 10 | Working demo and the milestone named in the proposal | Scalar, shared-sum AVX2, correctness table, first timing. Apply section 8. |
| Week 13 | GitHub: source, algorithm discussion, sequential vs parallel timing | Ablation (scalar, auto-vectorized, eight-pass SIMD, shared-sum), radius sweep, two image sizes, draft paper if the kill criteria were not hit |

## 10. Decision log

| Item | Choice | Status |
|---|---|---|
| Research goal | A submittable short paper, with the course project as the implementation | Adopted |
| Direction | D. Side-window smoothing, shared-sum vector layout | Proposed. Lock after the section 8 search and the instructor’s assembly rule. |
| Rejected for the paper | A blur/Sobel demo, B an AVX-512 stencil bake-off, C a bilateral or non-local-means port | Adopted as rejections |
| Fallback if D fails by Week 10 | A. Gaussian blur and Sobel in AVX2, course submission only | Adopted |
| Platform | AVX2 | Proposed |
| Thesis module (direction E) | None named | Open. If a group member has a thesis hot loop, reopen this before Week 6. |
