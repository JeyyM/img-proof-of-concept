# Project Plan: Batched Outlines of Small Clusters

Advanced Computer Architecture integrating project, 1st Term 2026–2027. Group project. The course requires a data-level parallelism proof of concept. This group also wants a conference paper in submittable shape.

**Decision:** compute the convex hull of many tiny 2D clusters by placing several clusters in the same AVX2 instruction. A convex hull is the rubber-band outline around a set of dots. SciPy computes one cluster, then the next. With only eight dots, one cluster does not fill a wide register, so the wide work is across clusters.

The claim can fail. If the wide version is no faster than a tight scalar loop, the course demo still exists and the paper does not.

## 1. Scope

### In scope

- Two-dimensional hulls only.
- Fixed size: 8 points per cluster. This is the kernel that has to work.
- 16 points per cluster only after the 8-point kernel is correct and timed.
- Single-precision floating point, AVX2, eight clusters per instruction.
- Input coordinates are integers in the closed range −1024 to 1024, stored as float32. In that range the turn test is exact in float32, so a disagreement with SciPy is a bug.
- Three synthetic distributions, one random seed, committed with the code: uniform in the square, points on a circle, points inside a triangle.
- One million clusters for timing, plus a smaller count that fits in L2 cache.
- Correctness is set equality of corner indices against SciPy and against our own scalar code. Order around the outline does not have to match.

### Out of scope

- One large point cloud. That problem already has a 2025 SIMD preprint (VQhull).
- 3D hulls, approximate hulls, and clusters whose sizes differ inside one batch.
- CUDA. One thread per cluster is a different project and does not use the empty-register layout.
- OpenMP, or any parallelization that is only “many cores.”
- A collision, map, or tracking application. Those are motivation, not the evaluation.
- AVX-512 as a requirement. It is a second width only on a machine that has it.

### The rule for dots on a straight edge

Before coding, the scalar code and the wide code use the same rule: if three dots lie on one straight edge, keep the two endpoints and drop the middle. SciPy’s library (Qhull) does not always do this. The match against SciPy is required on inputs where no three dots are collinear. The straight-edge rule is tested against our scalar code, and reported separately against SciPy.

## 2. What we are deciding

Two goals, in this order:

1. A result a reviewer can accept: same corners as a known library, and a speedup against a tight scalar implementation of the same algorithm, not only against SciPy called in a loop.
2. The course proof of concept: one algorithm rewritten so the same operation applies to many clusters at once, plus sequential-versus-wide timing.

Calling SciPy a million times is slow partly because each call starts a large library. Beating that number is required for the course story and is not enough for the paper.

## 3. Course constraints

- Data-level parallelism on one platform. This plan uses AVX2. Intrinsics are the working form. Confirm with the instructor before Week 6 whether the graded kernel must be assembly.
- The same turn test and the same compare-exchange run on several clusters in one instruction.
- Proposal in Week 6, working demo in Week 10, full submission in Week 13.
- The Week 13 repository needs source, a discussion of the parallel algorithm, and sequential-versus-parallel timing.
- The proposal itself follows the expanded outline: abstract, inputs, what is parallel, prior work and the difference, the plan, what stays sequential, outputs, platform, the Week 10 milestone, references.

## 4. What a submittable paper means here

Flagship venues are out of range. The writing target is a workshop case study of about eight pages: one kernel, one CPU, code that reproduces the tables, and a comparison that could have gone the other way.

A realistic calendar target is a workshop that accepts case studies. PARMA-DITAM 2027 (papers due 16 November 2026) is that shape. Submit there only if the Week 10 numbers already exist and survive the kill criteria below. Otherwise write the paper to that standard during the course and send it to the next workshop after Week 13.

Reviewers reject this shape of paper:

- Speedup only against SciPy or only against a Python loop.
- A faster hull of one large cloud. VQhull already claims that, and it says little room remains on that problem.
- A vectorized gift-wrapping loop. A 2024 KTH thesis tried that on one cloud and the full program was slower than ordinary scalar code.

The paper needs both of these: the corner sets match, and the wide kernel beats a careful scalar loop of the same algorithm on the same machine.

## 5. Prior work, and the difference

| Work | What it did | Difference |
|---|---|---|
| Andrew, 1979, monotone chain | Standard 2D hull: sort by x, then build the upper and lower chains with a turn test | We keep this algorithm. The change is that several clusters take each step together. |
| Qhull (Barber, Dobkin, Huhdanpaa, 1996), used by `scipy.spatial.ConvexHull` | One point set per call, built for clouds of many sizes | Correctness baseline. A poor speed baseline, because a million tiny calls pay startup every time. |
| VQhull, arXiv:2510.09417, 10 Oct 2025, preprint | AVX-512 inside one Quickhull on a large cloud. About 1.6× to 16× versus a benchmark suite on that problem | Different input. We do not claim to be faster than VQhull on a large cloud. |
| Eriksson and Grindsäter, KTH bachelor’s thesis, 2024 | AVX-512 gift wrapping on one set. Inner loop about 3.5×, whole program about half the speed of scalar code, limited by memory traffic | We do not vectorize gift wrapping. Clusters are tiled so each tile stays in L1. |

GPU hull papers, including filter-then-hull work in the Journal of Parallel and Distributed Computing (2024), also attack one large set. They are context, not a baseline we must beat.

## 6. The method

### Algorithm

Andrew’s monotone chain, for every cluster:

1. Sort the eight points by x, and break ties by y.
2. Walk left to right to build the lower chain. Walk right to left to build the upper chain.
3. A dot is a corner when the turn it makes with the two dots before it is the required direction. The turn is the 2D cross product \((x_2-x_1)(y_3-y_1) - (x_3-x_1)(y_2-y_1)\).

The sort is a fixed sorting network, not a data-dependent quicksort. Every cluster executes the same compare-exchanges. The chain uses a mask: a cluster that does not need to pop its stack leaves its lanes unchanged. No cluster branches while another cluster continues.

### Layout

Points are stored so that one load gathers the same slot from eight clusters. Slot 0’s x coordinates for clusters 0–7 sit in one AVX2 register. The y coordinates sit in the next.

All eight points do not fit in the sixteen AVX2 registers at once (eight x registers and eight y registers, and then no room for the compare). The sort loads a pair of slots, compare-exchanges inside the lanes, and stores the pair back. Clusters are processed in tiles that stay in L1, so those reloads are not trips to DRAM. The full million-cluster array is about 64 MB and does not stay in cache. Timing reports a tiled run. An untiled run is reported only as a negative result if we measure one.

Sixteen-point clusters use the same layout and will spill harder. They are a second table, not the claim.

### What is parallel

- Compare-exchange of the sorting network, eight clusters at a time.
- The cross-product turn test, eight clusters at a time.
- Masked pops and pushes on the chain, eight clusters at a time.

### What stays sequential

- Generating points, checking the coordinate bound, and writing results.
- The choice of tile size.
- Clusters left over when the count is not a multiple of eight. Their time is reported separately.
- The one-time check that float32 turns match a 64-bit integer turn on the test set.

### Platform

AVX2 on one CPU the group can remeasure. The proposal names the exact model, cache sizes, and base clock once that machine is chosen. The kernel is written with intrinsics so the AVX2 instructions are visible. Assembly is a transcription of that kernel if the instructor requires it.

Do not implement CUDA in parallel. One platform.

## 7. Baselines

The course requires the first. The paper requires the first three. The fourth is context.

1. Scalar C of the same monotone chain and the same sorting network, same compiler, optimizations on. This is the speed claim.
2. That scalar file compiled with auto-vectorization and AVX2 enabled, so the paper shows the hand-written layout beating the compiler.
3. The wide AVX2 kernel.
4. `scipy.spatial.ConvexHull` in a loop over the same clusters. This checks corners. Its runtime is reported and is not the speedup quoted in the abstract.

Report kernel time without generating points and without writing the output file. Distributions are timed separately. The circle case makes every dot a corner. The triangle case makes most dots fall inside.

## 8. Inputs and outputs

**Inputs**

- `N` clusters, `N` in {10^5, 10^6} for the tables. 10^5 is the cache-resident check; 10^6 is the main number.
- 8 points per cluster, float32, integer coordinates in [−1024, 1024].
- A seed and the distribution name.

**Outputs**

- For each cluster, the original indices of the corners.
- A mismatch count against the scalar kernel (must be zero) and against SciPy on the non-collinear set (must be zero).
- A timing table: clusters per second, and time per cluster, for scalar, auto-vectorized, and AVX2.

## 9. How this maps onto the proposal

| Outline item | Content |
|---|---|
| 0. Abstract | Many 8-point hulls computed together in AVX2. Corners match SciPy. Speed is against a tight scalar monotone chain. |
| 1a. Inputs | `N` clusters, 8 integer coordinates in [−1024, 1024], three distributions. |
| 1b.i What is parallel | Sorting-network compare-exchange, turn tests, masked chain updates, eight clusters per instruction. |
| 1b.ii Existing work | Andrew 1979; Qhull / SciPy; VQhull preprint (one large cloud); KTH 2024 thesis (gift wrapping, slower than scalar). Difference: fixed tiny clusters, across-cluster layout, L1 tiles. |
| 1b.iii Plan | Scalar reference and SciPy check first. Then the same control flow in AVX2. Then the timing table. |
| 1b.iv Not parallel | Generation, I/O, leftover clusters, the integer-turn audit. |
| 1c. Outputs | Corner indices, mismatch counts, timing table. |
| 2. Platform | AVX2. Name the CPU in the proposal. |
| 3. Mid-project milestone | Week 10: scalar and AVX2 both match SciPy on one distribution, plus a first timing against the scalar loop. |
| 4. References | Section 5. |

## 10. Kill criteria

Apply these at the Week 10 demo. Any one of them ends the paper claim. The course submission continues with whatever is correct.

- Any mismatch of corner sets on the non-collinear test, or any mismatch against the scalar code.
- The AVX2 kernel is under 1.5× the tight scalar loop on the uniform million-cluster run.
- The AVX2 kernel is slower than the auto-vectorized scalar build.
- The only clear speedup is against SciPy-in-a-loop.
- A published or preprinted paper turns up that already batches fixed-size tiny hulls across AVX lanes. VQhull does not trigger this. A paper that does the across-cluster layout does.

Week 10 is the decision point. After that, either the paper has evidence or the remaining weeks go into a clean course submission.

## 11. Milestones

| When | Course requirement | Research requirement |
|---|---|---|
| Before Week 6 | — | Confirm the CPU has AVX2. Ask the instructor whether intrinsics count. Re-run the “batched convex hull SIMD” search once. |
| Week 6 | Proposal in the expanded outline | This document, trimmed to the outline, with the machine name filled in. |
| Week 10 | Working demo | Scalar and AVX2 on 8-point clusters. Zero mismatches on the non-collinear uniform set. One timing table. Apply section 10. |
| Week 13 | GitHub: source, algorithm discussion, sequential vs parallel timing | All three distributions, both input sizes, scalar / auto-vectorized / AVX2. 16-point table only if 8-point survived. Draft paper if section 10 was not hit. |

Build order inside the implementation, and do not skip ahead:

1. Scalar monotone chain and sorting network. Match SciPy on 10,000 non-collinear clusters.
2. Integer-turn audit on that same set. Every float32 turn sign matches the 64-bit integer cross product.
3. AVX2 kernel, same network, L1 tiles. Match the scalar indices on all `N`.
4. Timing harness. Then, and only then, the 16-point variant.

## 12. Decision log

| Item | Choice | Status |
|---|---|---|
| Research goal | A submittable workshop case study, with the course project as the implementation | Adopted |
| Kernel | 2D convex hull, 8 points, many clusters per AVX2 instruction | Adopted for the proposal |
| Algorithm | Andrew’s monotone chain plus a sorting network | Adopted |
| Correctness | Corner-index sets. SciPy on non-collinear inputs. Scalar code everywhere, including straight edges | Adopted |
| Speed baseline that matters | Tight scalar C of the same algorithm | Adopted |
| Rejected | Lecture-frame dropping, reranker prefilter, speck deletion, one large hull, CUDA | Adopted as rejections |
| Platform | AVX2 | Proposed until the CPU is named |
| 16-point clusters | Second table | Only after Week 10 says the 8-point claim survived |
| Venue | PARMA-DITAM 2027 if numbers exist before 16 Nov 2026; otherwise the next workshop after Week 13 | Holding |
