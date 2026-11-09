# Comprehensive Potential Reviewer Criticisms — *The Page Between the Samples*, Version 2

**Review context:** Hypothetical QoMEX 2027 **three-page short-paper** submission. Assessment is of this manuscript alone, assuming compression preserves its central methods and evidence. **Source:** *The page between the samples*, Version 2 (11-page supplied PDF). Page and section references below refer to that version, not to an as-yet-unwritten three-page version.

**How to read this document:** These are **possible** objections, not 44 established mistakes. A reviewer might raise only a handful. **Severity** means potential damage *if the objection is sustained*: **Critical** (could by itself motivate rejection), **Major** (substantially weakens acceptance), **Moderate** (requires qualification or additional support), **Minor** (fixable exposition or scope issue). **Basis** distinguishes **documented limitation**, **possible methodological issue**, and **editorial issue**. A direct source claim is not the same as an external validation of the claim.

## Executive summary: issues most likely to decide acceptance

| Priority | Potential objection | Severity | Best direct remedy |
|---|---|---|---|
| P1 | The synthetic clips are constructed to trigger the purported failure | Critical | Held-out, naturally occurring screen recordings; characterize prevalence |
| P1 | Encoder scene-cut disabled and clip-long GOP may amplify the effect | Critical | Rerun default scene-cut / realistic GOP conditions |
| P1 | Sampling/percentile failure is mathematically foreseeable; unclear novelty | Critical | State the exact nontrivial contribution; contrast with nearest prior work |
| P1 | VMAF degradation does not establish inability to read the page | Major | Text transcription / OCR accuracy / small human reading experiment |
| P1 | Comparison to evenly sampled frames may be a weak or straw-man baseline | Major | Add representative content-aware and scene-aware sampling baselines |
| P1 | Development-only, repeated backgrounds, no genuine held-out evaluation | Major | Freeze method, evaluate new clips and show cluster-aware uncertainty |
| P1 | Odd selected CRFs seem inconsistent with described initial ladder/step sizes | Major | Specify rung generation, search traces, and exact stopping rules |
| P2 | Selecting a CRF from eight frame-level VMAF scores may not deliver claimed compute savings | Major | Measure end-to-end workflow or explicitly restrict claim to sample selection |
| P2 | The paper's practical use case for an intentionally atypical 20-frame page is underdeveloped | Major | Give realistic application contexts and frequency/impact evidence |
| P2 | Higher size (+27% mean) is significant, and there is no rate-distortion comparison | Major | Compare equal-size or rate-distortion operating points |

---

## A. Contribution, novelty, and positioning

### C01. The central failure is largely a consequence of arithmetic
**Severity:** Critical · **Basis:** Interpretive objection · **Source:** §§1–2, pp. 1–2; §7, p. 9.

**Reviewer criticism:** Eight sample locations separated by roughly 112 frames can miss a 20-frame page. Likewise, the 45th-worst frame cannot be forced into a 20-frame bad segment, while the 9th-worst can. This geometry is immediately predictable, so showing it in data may not constitute a sufficiently new research finding. The numbers establish an instance of a known sampling problem rather than a new generalizable insight.

**Why it matters:** A short paper can be a counterexample, but it still needs an informative, non-obvious *consequence*, *interaction*, or *practical correction*. Merely verifying the design of the counterexample may be judged insufficient.

**Potential response/fix:** Emphasize the empirical CRF-selection consequence and equivalence to the full-frame quality decision; identify the exact surprise and limits, not the arithmetic itself. Cite and contrast established temporal pooling and adaptive sampling work.

### C02. The manuscript combines known ideas without clearly establishing an original technical contribution
**Severity:** Critical · **Basis:** Interpretive objection · **Source:** §3, pp. 2–3; §6.2, p. 7.

**Reviewer criticism:** Shot-boundary detection, avoiding cut-adjacent artifacts, percentile pooling, and sampling within scene segments are longstanding ideas. The proposed 'settled' selection samples after a detected cut, an intuitive heuristic. Where precisely is the novel method, evaluation insight, or previously unreported failure mode?

**Why it matters:** Reviewers may label the contribution as application-specific demonstration rather than multimedia quality research.

**Potential response/fix:** State a single precise contribution sentence. Make the paper explicitly a *counterexample/measurement* paper if there is no new algorithm. Add the strongest directly relevant prior work and explain what it did not test.

### C03. The two failed checks may be a misleading joint indictment
**Severity:** Major · **Basis:** Interpretive/methodological issue · **Source:** Abstract, p. 1; §7, p. 9.

**Reviewer criticism:** The eight-frame sample is a mechanism used for choosing CRF, whereas the 5th-percentile statistic is a separate *post-encode* reporting criterion. Their simultaneous failure does not necessarily represent a single deployed quality-control pipeline. They also fail for different reasons.

**Why it matters:** A memorable 'two checks agree and are wrong' narrative could seem contrived without evidence that systems actually pair these checks.

**Potential response/fix:** Identify real workflows that use both (if evidence exists), or position them plainly as two distinct failure modes on one constructed example. Do not imply the combined pipeline is an industry norm without documentation.

### C04. A failure demonstration is not automatically evidence that the proposed remedy is generally preferable
**Severity:** Major · **Basis:** Interpretive objection · **Source:** §§6–8, pp. 5–10.

**Reviewer criticism:** The settled method wins because every scripted clip contains precisely one difficult scene immediately after a detectable cut. That does not show scene-aligned sampling is a good general quality-control strategy when difficulty varies *within* scenes, when multiple scene types occur, or when cuts do not correlate with complexity.

**Potential response/fix:** Distinguish **diagnosis** ('uniform sampling can miss a short hard segment') from **prescription** ('settled sampling is preferable'). Either narrow the prescription or test clips with many transitions and within-scene changes.

### C05. The related-work coverage is too thin for a novelty claim
**Severity:** Major · **Basis:** Editorial/substantive gap · **Source:** §3 and references, pp. 2–3, 11.

**Reviewer criticism:** The related work mostly identifies foundational VMAF, x264, shot detection, and subjective assessment references. It does not systematically compare recent temporal quality pooling, percentile/low-tail aggregation, content-adaptive frame selection, screen-content coding, or scene-aware quality assessment.

**Potential response/fix:** Add a compact nearest-neighbor comparison: baseline approach, what it measures/selects, its assumptions, and exactly how this paper differs. Verify current literature before claiming no one has studied the issue.

### C06. The research question may be too narrow for a multimedia-quality venue
**Severity:** Moderate · **Basis:** Interpretive objection · **Source:** Abstract and §8, pp. 1, 10.

**Reviewer criticism:** One codec, one preset, single-CRF encoding, scripted hard cuts, still screens, a single short page, and VMAF-only evaluation make the conclusion highly specific. A reviewer may consider this a tooling or demonstration note rather than research broadly relevant to QoMEX.

**Potential response/fix:** Focus on a general question about **rare critical intervals in temporal quality assessment**, with the encoder as a clearly limited case study. Avoid claims about all screen recordings or all encoders.

### C07. The stated benefits may be less novel because one frame suffices
**Severity:** Moderate · **Basis:** Documented result with interpretive risk · **Source:** §6.2, p. 7.

**Reviewer criticism:** The paper reports that one settled frame selects the same CRF as eight on all twelve clips. This undercuts the apparent importance of the eight-frame rule and of its chosen post-cut wait. The contribution might collapse to 'sample the difficult still instead of the easy still.'

**Potential response/fix:** Explicitly elevate this to a finding: eight frames are *not* needed on stationary content. Explain that eight was a fixed-budget controlled comparison, not an optimized algorithm.

---

## B. Experimental construction and realism

### C08. The data were constructed so uniform sampling would usually fail
**Severity:** Critical · **Basis:** Documented limitation · **Source:** §§1–2, pp. 1–2; §7, p. 9.

**Reviewer criticism:** All comparison clips contain a 20-frame dense page within a long easy hold. The paper itself calculates an 84.6% miss probability for eight evenly spaced sample centers. A test designed to create the failure does not establish that the same failure is a meaningful frequency or severity in naturally occurring content.

**Potential response/fix:** Present the experiment as a *stress test* and add independently gathered real recordings with unmodified cut locations, durations, and layouts. Report how frequently each mechanism occurs, including null results.

### C09. No held-out set validates decisions after the analysis was developed
**Severity:** Major · **Basis:** Documented limitation · **Source:** Cover note, p. 1; §§6.1, 8, pp. 5, 10.

**Reviewer criticism:** All primary estimates come from development clips. Repeated exploration of wait offsets, baselines, frame counts, and quality criteria on the same data increases the risk that conclusions are specific to observed examples, even if original page-start draws were fixed beforehand.

**Potential response/fix:** Freeze preprocessing, threshold, rules, targets, and CRF ladder; then run an independently created held-out set once. Label exploratory analyses and give held-out results separately.

### C10. Twelve comparison clips are not twelve independent conditions
**Severity:** Major · **Basis:** Documented limitation · **Source:** §4, p. 3; §6.1, p. 5.

**Reviewer criticism:** Six easy screens are each reused twice. The main contrast depends heavily on the easiness of the background and hardness of the page, so results from shared backgrounds may be correlated. The apparent sample size overstates diversity.

**Potential response/fix:** Treat six easy-background clusters as the more conservative effective unit, and include more independent base scenes. Show a hierarchical/cluster-aware analysis and avoid population-wide confidence claims.

### C11. The six boundary clips are not an independent generalization test
**Severity:** Major · **Basis:** Documented limitation · **Source:** §4, p. 3; §6.4, p. 8.

**Reviewer criticism:** The boundary clips replace the easy screen with busier screen layouts, but preserve the 20-frame dense-page construction and general scripted design. They help probe one axis of difficulty, not realistic motion, content heterogeneity, or generalization.

**Potential response/fix:** Clearly call them a *secondary synthetic stress test*. Include additional classes: mouse motion, scrolling, animations, video windows, fade cuts, repeated scene changes, and mixed layouts.

### C12. The 20-frame page duration is an extreme and unexplained prevalence assumption
**Severity:** Major · **Basis:** Interpretive objection · **Source:** §§1–2, pp. 1–2; §7, p. 9.

**Reviewer criticism:** A page visible for two-thirds of a second may not be a page a person is reasonably expected to read. The paper's motivating example could be seen as an artificial duration chosen to make uniform samples miss it.

**Potential response/fix:** Show realistic use cases (brief tooltips, quick transitions, status flashes, seekable recordings), or stop implying a viewer must read the page in real time. Test a duration distribution and explain why short segments deserve preservation, including paused playback.

### C13. All clip content consists of stills with abrupt hard cuts
**Severity:** Major · **Basis:** Documented limitation · **Source:** §4, p. 3; §8, p. 10.

**Reviewer criticism:** Real screen recordings include scrolling, cursor movement, window animations, dynamic video, notification popups, variable frame content, and editing interactions. A threshold that trivially detects pasted still-image changes might behave differently on actual captured content.

**Potential response/fix:** Test original screen recordings with authentic dynamics and measure cut-detection precision/recall before interpreting downstream sampling quality.

### C14. Only one dense segment is present, so the method is not tested as a general clip-selection system
**Severity:** Major · **Basis:** Design limitation · **Source:** §4, p. 3.

**Reviewer criticism:** The clips have an easy picture, one hard page, and a return cut. With multiple difficult segments, eight total samples cannot guarantee coverage; more cuts may also dilute per-scene sampling or force a selection strategy not specified here.

**Potential response/fix:** Include multiple hard pages of varying severity and duration; specify how the algorithm allocates eight total frames across multiple scenes and what happens when there are more scenes than samples.

### C15. No broad variation in resolution, frame rate, or clip length
**Severity:** Moderate · **Basis:** Documented setup · **Source:** §4, p. 3.

**Reviewer criticism:** Every clip is 1920×1080, 30 fps, 900 frames. The two sampling holes depend on absolute frame count, sample count, and event duration. The result may change at 60 fps, longer recordings, differing durations, or display/scaling conditions.

**Potential response/fix:** Vary 720p/1080p/1440p, 24/30/60 fps, clip length, and event duration. Express guarantees/risks in proportions of total frames as well as time.

### C16. The selected 'easy' and 'dense' pictures may confound text complexity with compressibility
**Severity:** Major · **Basis:** Possible methodological issue · **Source:** §4, p. 3; §6.4, p. 8.

**Reviewer criticism:** The difference is not only informational importance. The easy picture is often unusually flat while the dense page has high-frequency text. A quality gap might arise from texture/compressibility contrasts rather than *text importance* per se.

**Potential response/fix:** Factorially vary text density and visual complexity independently: busy non-text screens, sparse but small text, and dense text under matched spatial variance. Report what predicts shortfall.

### C17. The reference generation procedure could conceal codec-specific interactions
**Severity:** Moderate · **Basis:** Possible methodological issue · **Source:** §4, p. 3.

**Reviewer criticism:** The lossless long-GOP reference and lossy x264 comparison have different encoded structures. The paper states pixel equivalence to the stills but offers limited detail on pixel-format conversion, color matrices/range, frame alignment, and decoder consistency. Artifacts at cuts might be influenced by alignment/format rather than by the intended quality differences.

**Potential response/fix:** Document exact FFmpeg commands, color-space/range flags, matched frame indexing, decoded reference checksums, and any cut-frame anomalies.

### C18. Photographic cases do not support a broad 'screen recording' claim
**Severity:** Moderate · **Basis:** Documented negative boundary · **Source:** §8, p. 10.

**Reviewer criticism:** The authors note earlier photographic checks where both rules chose the same CRF. This suggests the mechanism is tied to a specially favorable screen-content regime. Results should not be presented as a general video-compression improvement.

**Potential response/fix:** Highlight this as a boundary and possibly report a controlled negative case in the short paper. State clearly which content categories are and are not expected to exhibit the effect.

---

## C. Encoder settings, CRF selection, and baseline fairness

### C19. Disabling scene-cut detection may cause an artificial magnitude of failure
**Severity:** Critical · **Basis:** Documented limitation · **Source:** §3, p. 3; §8, p. 10.

**Reviewer criticism:** x264 is denied the opportunity to insert a keyframe at the difficult scene transition. This can increase error propagation and the cost of representing a sudden high-detail page. A normal encode could significantly reduce or change the observed gap.

**Potential response/fix:** Run the same clips with x264 default scene-cut detection and otherwise matched settings. Report actual keyframe placement, per-frame VMAF, selection decisions, and file sizes. Do not assume the result survives until measured.

### C20. A GOP longer than the entire clip is not representative of typical deployment
**Severity:** Critical · **Basis:** Documented limitation · **Source:** §§3–4, pp. 3–4; §8, p. 10.

**Reviewer criticism:** A 900-frame clip-long GOP prevents periodic intra refresh/keyframes that many workflows use for seeking, resilience, and common encoding defaults. It may exacerbate the central defect or turn a general-seeming claim into a niche parameter artifact.

**Potential response/fix:** Sweep realistic GOP/keyint settings and keyframe policies (with and without scene-cut). Keep scene-cut and GOP effects separate so the important source of the quality gap is identifiable.

### C21. A single x264 preset, pixel format, and codec limit transferability
**Severity:** Major · **Basis:** Documented limitation · **Source:** §§3–4, pp. 3–4; §8, p. 10.

**Reviewer criticism:** Only libx264 medium/yuv420p with one CRF per clip is tested. Screen-content codecs, H.265/HEVC, AV1, different presets, lossless modes, or 4:4:4 chroma can have different quality allocation across dense text.

**Potential response/fix:** Either explicitly constrain all claims to this encoder configuration or show one contrasting codec/preset and a 4:4:4 condition; prioritize standard x264 behavior first.

### C22. One constant CRF per clip creates an inefficient global response to a local problem
**Severity:** Major · **Basis:** Documented design; interpretive objection · **Source:** §3, p. 3; §7, p. 9.

**Reviewer criticism:** To preserve a 20-frame page, the method lowers CRF across all 900 frames and enlarges the whole file. This can be an unnecessarily expensive way to protect less than 3% of the timeline, especially relative to scene-level coding or adaptive bitrate allocation.

**Potential response/fix:** Add a localized rate-control or per-segment protection comparator, or state that the study isolates *global CRF selection* rather than proposing a best-practice encoder.

### C23. The chosen baseline may be weaker than plausible production alternatives
**Severity:** Major · **Basis:** Possible baseline-design objection · **Source:** §§4, 6.2–6.3, pp. 3–4, 7–8.

**Reviewer criticism:** Eight evenly spaced frames are an intentionally naive way to handle short rare events. Practical encoders and quality monitors may use scene changes, motion/complexity cues, representative thumbnails, targeted scene samples, random sampling, or full-pass metrics. Showing an advantage over uniform centers alone is insufficient to establish practical superiority.

**Potential response/fix:** Compare against credible, documented alternatives. At minimum explain why uniform centers are the relevant benchmark rather than implying they represent the state of the art.

### C24. 'Equal eight frames' does not mean equal total computational cost
**Severity:** Major · **Basis:** Possible methodological issue · **Source:** §§3–4, pp. 3–4.

**Reviewer criticism:** Uniform sampling needs no cut detection, while settled sampling requires scanning all frames or luma changes to locate transitions. Both vote on eight frames but use different preprocessing. The study explicitly says it has not benchmarked the full pipeline.

**Potential response/fix:** Report decode, cut detection, frame selection, reference alignment, per-frame scoring, and CRF search costs. If no efficiency claim is made, remove language that suggests equal computational budgets.

### C25. The offline VMAF-score lookup may obscure actual decision costs and availability of frame scores
**Severity:** Major · **Basis:** Possible methodological issue · **Source:** §4, p. 4.

**Reviewer criticism:** The study encodes a CRF ladder, computes full 900-frame VMAF passes, then chooses CRFs by indexing saved frame scores. That is a valid *counterfactual comparison of sampling rules*, but it is not an implemented fast encode-selection system requiring only eight quality measurements. VMAF itself requires a reference and decoding/scoring operations.

**Potential response/fix:** State clearly that this is an offline retrospective experiment. If claiming efficiency, implement and time an end-to-end method that truly scores only the chosen frames, and account for all encoded rungs.

### C26. The stated CRF ladder and displayed odd-valued results are not fully reconciled
**Severity:** Major · **Basis:** Reproducibility ambiguity, not a proven error · **Source:** §4, p. 3; Table 1, p. 6.

**Reviewer criticism:** The method says the ladder starts with 28, 32, 36, 40, 44, then 'steps by 2,' while Table 1 reports selected CRFs 30, 31, 35, 37, etc. The manuscript does not fully spell out when or why odd-valued rungs were introduced. This is a material ambiguity in the main result.

**Potential response/fix:** Include precise pseudocode and one full trace per method: starting rungs, refinement stages, threshold crossing, rung insertion, and stop criterion. Make clear whether all candidate rules saw the same union of encoded CRFs.

### C27. Nonmonotone votes can invalidate a naive 'first threshold crossing' search
**Severity:** Major · **Basis:** Explicitly acknowledged possible selection defect · **Source:** §4, p. 3.

**Reviewer criticism:** The paper says eight-frame VMAF votes are not always monotone in CRF and that the search 'can miss a legal rung.' Therefore a statement that a method chooses the 'highest qualifying CRF' may be false unless every encoded candidate rung was checked or the search was exhaustive within a defined grid.

**Potential response/fix:** Distinguish **highest among rungs searched** from **highest in the complete tested ladder**. Evaluate every shared encoded rung for every method; publish candidate sets and state whether table entries change under exhaustive selection.

### C28. The 'full-pass optimum' is only optimal among encoded rungs and under one criterion
**Severity:** Moderate · **Basis:** Documented qualifier · **Source:** §6.1, p. 6.

**Reviewer criticism:** Matching the CRF selected by the full-frame 9th-worst rule is framed as evidence of correctness, but that full-frame choice is a constructed benchmark—not a uniquely optimal encode. Other objectives (readability, perceptual mean, bits, worst window, near-maximum CRF) may choose differently. The available ladder is discrete and limited.

**Potential response/fix:** Consistently say 'same as the full-frame 1st-percentile decision **among encoded rungs**'; do not call it universally optimal. Include alternative objectives as sensitivity tests.

### C29. Comparing CRF choices rather than equal-sized files can exaggerate practical benefit
**Severity:** Major · **Basis:** Experimental-design objection · **Source:** Table 1 and Fig. 5, p. 6; §7, p. 9.

**Reviewer criticism:** Settled sampling is allowed to choose a larger file, on average 27% more bytes, and therefore achieves higher quality. A reviewer may ask whether the method produces a more advantageous **rate–distortion** trade-off at equal bitrate/file size, rather than merely choosing to spend more bits.

**Potential response/fix:** Show rate–distortion curves, quality at matched size, and/or minimal bytes required to satisfy each quality target. Note that the contribution is *correctly rejecting a deficient encode*, not a same-size quality breakthrough.

### C30. The variance baseline may not represent competent complexity-based sampling
**Severity:** Moderate · **Basis:** Possible baseline-design issue · **Source:** §§4, 6.2, pp. 4, 7.

**Reviewer criticism:** Selecting the eight highest-luma-variance frames from static pictures naturally returns repeated frames from a single image and may oversample the visually busier but easier scene. A more realistic complexity strategy would enforce temporal diversity, scene coverage, edge/text features, or local encoding difficulty.

**Potential response/fix:** Describe this as a deliberately simple heuristic, not a representative modern content-aware baseline. Add stratified or scene-constrained variance selection if space permits.

### C31. The random baseline is vulnerable to finite draws and implementation-dependent sampling assumptions
**Severity:** Moderate · **Basis:** Possible methodological issue · **Source:** §6.2, p. 7.

**Reviewer criticism:** The single 'committed' draw is identical across clips, and even the 1,000-draw extension conditions on the same synthetic timing structure and CRF grid. This describes the sampled construction but does not establish random selection as intrinsically inferior across general distributions of difficult-event positions.

**Potential response/fix:** Report expected hit probability analytically and uncertainty over independently generated clips and seeds; clarify with/without replacement, frame-uniform distribution, and whether shared draws induce dependence.

---

## D. Quality measurement and meaning

### C32. VMAF 90 is not validated as a text-readability threshold
**Severity:** Major · **Basis:** Documented limitation · **Source:** §3, p. 3; §8, p. 10.

**Reviewer criticism:** The narrative concerns important text that a user must read, yet the decision threshold is a VMAF score of 90. There is no evidence in this study that VMAF 89 is unreadable, that 90 is readable, or that the reported 10-point shortfall corresponds to a meaningful recognition loss for these pages.

**Potential response/fix:** Add OCR/text recognition accuracy, a small reading task, or carefully downgrade the claim to 'VMAF-defined quality shortfall' rather than loss of readability.

### C33. No human perceptual or task-based validation
**Severity:** Major · **Basis:** Documented limitation · **Source:** §3, p. 3; §8, p. 10.

**Reviewer criticism:** No person viewed or read the clips, and no subjective method was applied. VMAF may not capture short-exposure readability, user pausing/rewinding, temporal integration, annoyance, or whether the damaged material is task-critical.

**Potential response/fix:** Conduct a targeted comprehension/transcription study or a task-based screen-content assessment, preferably comparing actual selected encodes blind at relevant viewing conditions.

### C34. VMAF's validity for screen text and abrupt transitions is not established here
**Severity:** Major · **Basis:** Possible measurement issue · **Source:** §§3, 6.2, pp. 3, 7.

**Reviewer criticism:** A perceptual video metric designed and validated for general visual quality may behave unexpectedly on high-contrast glyphs, chroma subsampling, repeated still frames, and hard-cut alignment. Extremely low cut-frame scores (including 0.0) raise questions about metric artifacts.

**Potential response/fix:** Inspect representative frame crops, verify VMAF alignment around cuts, and report at least one complementary metric (PSNR/MS-SSIM or text-specific OCR) while explaining each metric's limitations.

### C35. The selected 1st-percentile score is itself a tunable and potentially fragile tail criterion
**Severity:** Major · **Basis:** Methodological objection · **Source:** §3, pp. 2–3; §6.1, p. 6.

**Reviewer criticism:** The paper criticizes 5th-percentile pooling for hiding a 20-frame event, then makes 1st-percentile pooling the ground truth because it captures that event. But choosing the percentile after considering the designed event duration can appear tailored to the desired finding; an isolated bad transition frame can also dominate such a low percentile.

**Potential response/fix:** Analyze a family of percentile thresholds and duration-aware pooling rules. Justify the evaluation criterion from application needs or pre-specified minimum event duration, not solely the demonstration.

### C36. The two-percentile comparison may be apples-to-oranges with the frame-selection vote
**Severity:** Moderate · **Basis:** Potential conceptual ambiguity · **Source:** §§3, 6–7, pp. 3, 5–9.

**Reviewer criticism:** The voting rule uses the **minimum of eight sampled VMAF scores**, while the reference evaluation is the **9th-worst of 900** and the misleading summary is the **45th-worst**. A reviewer may question why these three different risk criteria belong in one comparison and whether changes in criterion, rather than sampling location alone, explain the result.

**Potential response/fix:** Explicitly define the decision rule, post-encode comparator, and reporting diagnostic in a compact methods table. Explain why each is appropriate and what is or is not held constant.

### C37. Abrupt-cut metric artifacts may contaminate the argument about 'settling'
**Severity:** Moderate · **Basis:** Possible measurement concern · **Source:** §6.2, p. 7.

**Reviewer criticism:** Scores of 0.0 at jump frames on multiple clips suggest potential reference alignment, frame buffering, or cut-edge behavior that is qualitatively different from ordinary compression blur. Waiting eight frames may simply avoid a scoring artifact, not identify a generally better scene sample.

**Potential response/fix:** Examine decoded/reference frame pairs around the cut; verify indexing and timestamps; rerun metrics with boundary exclusions and document why a wait is necessary.

### C38. The result depends on an arbitrary threshold and target-dependent CRF optimization
**Severity:** Moderate · **Basis:** Design limitation · **Source:** §4, p. 3; Table 1, p. 6.

**Reviewer criticism:** CRFs are selected to cross VMAF 90, so the settled method necessarily gravitates toward that threshold. The target-80 check is useful but limited; different quality levels or task goals may change relative selection and costs.

**Potential response/fix:** Show a compact threshold sweep (e.g., several realistic values), distribution of selected CRFs, and sensitivity to percentile choice. Keep target choice fixed before held-out evaluation.

---

## E. Statistical inference and evidence strength

### C39. The 95% bootstrap intervals do not imply population-wide reliability
**Severity:** Major · **Basis:** Documented limitation · **Source:** Abstract, p. 1; §6.1, p. 5.

**Reviewer criticism:** A bootstrap of twelve constructed development clips estimates variability under resampling those examples, not uncertainty for natural screen recordings. The manuscript acknowledges this, but headline confidence intervals may still give an unjustified aura of generality.

**Potential response/fix:** Label all intervals as descriptive/resampling intervals *for this constructed set* and emphasize the cluster-bootstrap variant. Derive generalization claims only from independently sampled held-out content.

### C40. Conditional sampling can make the all-missed result appear stronger than it is
**Severity:** Major · **Basis:** Possible selection/interpretation issue · **Source:** §2, p. 2; §4, p. 3.

**Reviewer criticism:** All eighteen selected starts missed the even centers, despite a reported per-start miss probability of 84.6%. That outcome is possible but selected starts may not represent an unbiased estimate of hit frequency when all reported clips exhibit the failure. The construction and exclusion rules need to be auditable.

**Potential response/fix:** Publish all draws and generator code; report the theoretical 84.6% miss rate as primary for the design and do not treat 18/18 as a real-world frequency estimate. Clarify whether any trials were excluded or rerun.

### C41. Reporting many variations on the same examples risks exploratory overinterpretation
**Severity:** Moderate · **Basis:** Possible analysis concern · **Source:** §§6.2–6.4, pp. 7–8.

**Reviewer criticism:** Waits of 1/2/4/8/12/16, sample budgets of 1/8/16/32, multiple quality targets, random seeds, and several baselines are all explored on a small development sample. Even without formal p-hacking, readers may over-read robustness when the same examples have informed many design choices.

**Potential response/fix:** Separate pre-specified primary comparison from exploratory sensitivity checks. Reconfirm key choices on held-out data, and make no unwarranted inferential claims from descriptive sweeps.

### C42. Effect sizes are summarized over an intentionally heterogeneous but tiny set
**Severity:** Moderate · **Basis:** Documented pattern · **Source:** §6.1/Table 1, pp. 5–6.

**Reviewer criticism:** Two editor-related clips show gaps around 20 points, while others are far smaller; the mean shortfall 10.32 is partly driven by these cases. Averaging treats distinct page/background combinations as equivalent and may obscure what really controls performance.

**Potential response/fix:** Report median and range (already partly done), subgroup patterns, leave-one-background-out sensitivity, and predictors such as source-page complexity. Avoid headline generalization from the mean alone.

### C43. No uncertainty estimate for practical cost/benefit under new clips
**Severity:** Moderate · **Basis:** Evidence gap · **Source:** Table 1 and Fig. 5, p. 6.

**Reviewer criticism:** The paper gives average extra bytes and a 15–47% file-size range but does not establish expected cost under realistic screen-content distributions or provide an appropriately clustered uncertainty estimate for size trade-offs.

**Potential response/fix:** Report paired distributions and cluster-resampled intervals as descriptive statistics; estimate deployment costs only with a representative held-out dataset.

---

## F. Implementation and reproducibility

### C44. The end-to-end method is not completely defined for real recordings
**Severity:** Major · **Basis:** Design/implementation gap · **Source:** §3, p. 3; §4, p. 4; §8, p. 10.

**Reviewer criticism:** The simple cut rule detects a brightness jump, then waits eight frames and selects the next eight frames of the same picture. It is unclear how this becomes an eight-frame **total** budget on clips containing many cuts, near-duplicate scenes, short shots, or no cuts at all. 'Stopping if the picture changes again' does not specify fallback or sample reallocation.

**Potential response/fix:** Provide algorithm pseudocode, clip-level budget logic, fallback cases, and deterministic tie-breaking. Test multi-shot videos to confirm that implementation matches the described budget.

### C45. Cut detection threshold is not validated beyond near-trivial hard cuts
**Severity:** Major · **Basis:** Documented limitation · **Source:** §3, p. 3; §8, p. 10.

**Reviewer criticism:** Mean absolute luma difference above 2 finds planted hard transitions between stills. This does not establish robustness to motion, fades, UI animations, frame drops, gradual scrolling, flicker, or brightness effects. False detections could waste samples or omit the important moment.

**Potential response/fix:** Measure precision/recall on a labeled screen-video set, sweep thresholds, and report downstream quality sensitivity to detection errors.

### C46. Full reproducibility requires public artifacts, commands, and exact score definitions
**Severity:** Major · **Basis:** Reproducibility gap · **Source:** §§4–6, pp. 3–8; references, p. 11.

**Reviewer criticism:** The manuscript names `clips/decisions.csv`, `clips/log.csv`, VMAF JSON paths, a seed, encoder settings, and some sample indices. These are helpful, but the PDF itself does not establish that the input clips, scripts, score arrays, exact command lines, versions, and generation source images are publicly accessible.

**Potential response/fix:** Release or archive a reproducibility package with checksums, all 18 clips or generators, media rights, scripts, encodes/score dumps, system/FFmpeg/libvmaf/x264 versions, and rerun instructions. Cite its persistent location in the submission.

### C47. Frame-index conventions and cut timing require precision
**Severity:** Moderate · **Basis:** Possible ambiguity · **Source:** Fig. 1 and §3, pp. 2–3; §6.2, p. 7.

**Reviewer criticism:** A cut at frame 538, a 20-frame hold spanning 538–557, and a settled sample at 546–553 are clear in the example, but exact convention matters: first changed frame vs. difference pair, zero- vs. one-based indexing, and whether waiting N frames includes the cut frame. Ambiguity can change cut-frame inclusion and pathological VMAF minima.

**Potential response/fix:** Define indexing once, give precise pseudocode and a unit test/trace for clip 01.

### C48. The brightness-difference comparison could depend on color and image preprocessing
**Severity:** Moderate · **Basis:** Possible implementation gap · **Source:** §§3–4, pp. 3–4.

**Reviewer criticism:** The threshold 'above 2 on 8-bit levels' is tied to luma computation and input scaling. Color-range conversion, subsampling, dithering, and compression artifacts can change mean luma differences. An identical numerical threshold is not automatically portable.

**Potential response/fix:** State whether differences are measured on source or compressed frames, exact luma/range pipeline, scaling normalization, and stability across codecs/encodes.

### C49. AVX2 timing and agreement are tangential to the paper's research claim
**Severity:** Minor–Moderate · **Basis:** Editorial scope issue · **Source:** §4, p. 4.

**Reviewer criticism:** Three cut-finding implementations match, but the paper disclaims speed as a contribution and does not benchmark the whole system. Even a brief architectural aside costs scarce short-paper space and might confuse reviewers about the actual contribution.

**Potential response/fix:** Omit or move implementation details to supplementary material unless they substantiate reproducibility. Do not describe the assembly implementation as a multimedia-quality innovation.

### C50. The claimed sample-budget comparisons lack clarity about 'one frame per scene' versus a fixed eight-frame total
**Severity:** Moderate · **Basis:** Potential conceptual ambiguity · **Source:** §§4, 6.2, pp. 4, 7.

**Reviewer criticism:** The test has one short difficult picture, so 'take eight frames after the cut' uses eight samples total. In a longer clip with many changes, either sampling eight per cut exceeds the budget or restricting to eight globally requires a nontrivial cut-prioritization rule absent from the paper.

**Potential response/fix:** Specify the domain as one-event clips or introduce a budgeted scene-selection policy. Do not equate eight-per-event with eight-per-clip.

---

## G. Practical implications and interpretive honesty

### C51. Detecting a short quality failure does not establish the user's action is improved
**Severity:** Major · **Basis:** External-validity objection · **Source:** Abstract, §7, pp. 1, 9.

**Reviewer criticism:** The proposed check chooses a larger file, but the study does not establish improved user outcomes: accurate reading, task completion, comprehension, fewer pauses, or subjective preference. The practical benefit remains inferred from a metric threshold.

**Potential response/fix:** Connect the objective score to a task-level endpoint or explicitly avoid practical usability claims.

### C52. Sampling after cuts will not necessarily find *the hardest* page
**Severity:** Major · **Basis:** Generalization limitation · **Source:** §§3–4, pp. 3–4; §8, p. 10.

**Reviewer criticism:** The method assumes the important hard page appears immediately after a detectable cut. Real difficulty can emerge after scrolling, tooltips, typing, zooming, animation, or within a stable scene. An after-cut frame is not universally representative of the low-quality tail.

**Potential response/fix:** Test within-scene content changes and include event-aware selection or hardness scoring inside scenes. Limit guarantees to the constructed two-picture setup.

### C53. The relationship between sampling strategy and compression itself is easy to overstate
**Severity:** Moderate · **Basis:** Interpretation issue · **Source:** §§3–4, pp. 3–4; §7, p. 9.

**Reviewer criticism:** The methods select among files produced by the same encoder; they do not directly improve coding efficiency or the quality of a fixed encode. The principal change is which existing CRF/file is accepted. Phrasing such as 'protects the page' could be read as introducing localized protection or a better codec.

**Potential response/fix:** Use precise language: 'scene-aligned sparse *selection* rejects excessive CRF' rather than 'improves compression' or 'recovers quality for free.'

### C54. File-size percentage may exaggerate or understate meaningful cost for broader footage
**Severity:** Moderate · **Basis:** Scope limitation · **Source:** Abstract, Table 1, pp. 1, 6.

**Reviewer criticism:** The clips compress extremely well because most frames repeat one still. A 46 KB increase and 27% relative increase may behave very differently in hour-long screen recordings, lectures with motion, or mixed content. Neither number can be extrapolated without accounting for scene distribution.

**Potential response/fix:** Report absolute and per-minute bitrate changes, duration-normalized results, and representative content compositions. Explain why percentage and absolute bytes tell different stories.

### C55. The demonstration may be more about pathological short-duration content than about typical service quality
**Severity:** Moderate · **Basis:** Scope objection · **Source:** §§2, 7–8, pp. 2, 9–10.

**Reviewer criticism:** The authors openly acknowledge that longer pages would likely be sampled and that the study is a stress test. A reviewer may question the operational relevance if users rarely need to read a full page shown for 0.67 seconds.

**Potential response/fix:** Justify the rare-event stakes (critical transient screens, pausing/rewinding, accessibility) without claiming prevalence; measure real short-event duration distributions where possible.

---

## H. Manuscript presentation and three-page compression

### C56. A three-page version may sacrifice the methodological detail required to assess validity
**Severity:** Major · **Basis:** Submission-format risk · **Source:** Multiple sections across the supplied 11 pages.

**Reviewer criticism:** The current paper uses figures and tables to explain sampling geometry, frame-level VMAF, CRF/size outcomes, competing samplers, temporal-budget sensitivity, and boundary cases. Compressing all of that may result in an oversimplified claim with insufficient details to check selection methodology.

**Potential response/fix:** Retain one timeline/quality visualization, a compact primary results table, a precise algorithm description, and the critical scene-cut/GOP limitation. Move secondary sweeps and individual rows to supplement/repository where allowed.

### C57. The abstract leads with a colorful scenario before clearly defining the scientific contribution
**Severity:** Moderate · **Basis:** Editorial issue · **Source:** Abstract, p. 1.

**Reviewer criticism:** The opening is memorable, but the main paper type, decision rule, measured endpoint, and novelty may be unclear to reviewers scanning quickly. It takes time to identify that the contribution is a controlled counterexample for sparse CRF selection and percentile pooling.

**Potential response/fix:** Put the research gap and contribution in the first two abstract sentences; then state the 12-clip result, size cost, and major scope condition.

### C58. The paper risks using 'quality passed' as a stronger statement than the actual score comparison
**Severity:** Moderate · **Basis:** Wording precision · **Source:** §§5–7, pp. 4–9.

**Reviewer criticism:** Phrases like 'the file passes' or 'would not be shipped' can obscure that passing means meeting a particular VMAF percentile criterion, not subjective perceptual acceptability or reading success.

**Potential response/fix:** Always name the evaluator: 'passes 5th-percentile VMAF 90' or 'fails 1st-percentile VMAF 90.' Avoid treating metric thresholds as user acceptance standards.

### C59. Several nearby numerical quantities invite confusion
**Severity:** Minor–Moderate · **Basis:** Editorial issue · **Source:** Abstract and Table 1, pp. 1, 6.

**Reviewer criticism:** The manuscript discusses mean 'gap' 10.32, per-clip 'gap,' actual settled-minus-even 9th-worst VMAF differences, settled CRF shifts, percent bytes, and fifth-percentile values. A reader could confuse **even shortfall below 90** with **difference between the even and settled scores** (these are not the same; e.g., clip 01: 90−81.9≈8.1, while 90.3−81.9≈8.4).

**Potential response/fix:** Rename Table 1 'Gap' to 'Even shortfall to 90' and define each quantity in a table footnote. Distinguish threshold shortfall from paired metric improvement.

### C60. 'The settled CRF is 5.7 steps lower' is imprecise
**Severity:** Minor · **Basis:** Editorial issue · **Source:** Table 1 caption/text, p. 6.

**Reviewer criticism:** Table 1's CRF values differ by an average of roughly 5.7 **CRF units**, not necessarily 5.7 search-ladder steps if the ladder uses coarse-to-fine increments of 2 or 4. 'Steps' can be technically ambiguous.

**Potential response/fix:** Say '5.7 CRF units lower on average' and separately define the search resolution.

### C61. References may not be sufficient or ideally primary
**Severity:** Moderate · **Basis:** Editorial/scholarly issue · **Source:** References, p. 11.

**Reviewer criticism:** Foundational references include a company blog for VMAF, GitHub documentation, and FFmpeg wiki material. Useful operational sources, but they do not substitute for primary published research establishing evaluation validity, temporal pooling comparisons, or current screen-content quality literature.

**Potential response/fix:** Cite primary peer-reviewed VMAF/perceptual-quality and temporal-sampling work as applicable, alongside implementation documentation, with current links and consistent citation style.

### C62. The paper's key conditional claim may be diluted by too many auxiliary comparisons
**Severity:** Moderate · **Basis:** Editorial issue · **Source:** §§6.2–6.4, pp. 7–8.

**Reviewer criticism:** Random seeds, variance selection, several waits, more evenly spaced centers, 80-point secondary threshold, boundary clips, and implementation notes create a lot of material around one core phenomenon. In three pages, the take-home could become hard to identify.

**Potential response/fix:** Prioritize: counterexample geometry → main CRF/metric result → size cost → crucial validity threats. Keep a few high-value robustness checks rather than all exploratory findings.

### C63. The title is evocative but may not adequately advertise the technical focus
**Severity:** Minor · **Basis:** Editorial issue · **Source:** Title, p. 1.

**Reviewer criticism:** *The page between the samples* is memorable but does not identify screen-content video, sparse quality sampling, temporal pooling, or CRF selection. Searchability and quick reviewer classification may suffer.

**Potential response/fix:** Consider a descriptive subtitle, e.g. 'When Sparse Frame Sampling Misses Short Text Segments in Screen-Video Quality Assessment.'

### C64. Front-matter notes that it is development-only may be unsuitable in the submitted format
**Severity:** Minor · **Basis:** Submission polish · **Source:** Front matter, p. 1.

**Reviewer criticism:** 'Version 2. Development clips only. ... Not a conference submission' is helpful for an internal report but plainly should not appear as-is in conference proceedings. The limitations should be integrated into the scientific text instead.

**Potential response/fix:** Remove internal-version notes and standardize authorship, abstract, keywords, formatting, and references to the official call/template.

---

## I. Extra adversarial questions a skeptical reviewer might ask

These are **questions to test** rather than statements that the PDF is wrong:

1. **Why choose the 1st percentile as ground truth?** Would a duration-weighted low-tail mean, bottom-k pooling, or worst contiguous 20-frame window produce the same conclusion?
2. **Is the 9th-worst frame always within the page because the page itself is persistently difficult, or because of a metric-alignment artifact?** Inspect distributions across all 20 frames.
3. **Would a scene-change detector working on a pre-existing lossy input find the same cuts?** The reference is generated from stills, not an original noisy capture.
4. **Does a keyframe inserted exactly at the page start erase most of the difference?** Report actual keyframe indexes, not only flags.
5. **Would standard encoder rate control automatically devote more bits to the page without changing global CRF?** Compare actual QP and bit allocation at the page.
6. **What happens when the most difficult frame is not eight frames after a cut?** Try delayed hard events and gradually increasing detail.
7. **What happens when there are more than eight scene changes?** Clarify the total sample budget and prioritization.
8. **How many extra bits are needed to protect page readability rather than VMAF 90?** The two need not align.
9. **Are sampled frame-level VMAF scores available cheaply enough in a real workflow?** Count reference access, decoding, repeated encodes, and metric passes.
10. **Can a different content-aware sampler select the same CRF using fewer total computations?** The study does not establish optimality among adaptive methods.
11. **If the chosen settled CRF equals the full-pass CRF in 12/12, does this survive repeated easy scenes and new page styles?** A held-out test is essential.
12. **Does the 27% size penalty persist when the clip has ordinary motion?** The measured source structure is unusually compressible.
13. **Could the study generate similar VMAF failures with *non-text* high-detail content?** This probes whether the mechanism is text-specific or simply content-complexity-driven.
14. **Are there settings in which settled sampling is worse than uniform sampling?** For example a hard page long before any cut, or multiple difficult regions.
15. **Does turning on scene-cut change CRF ordering and introduce nonmonotonic size/quality tradeoffs?** The report already observes some nonmonotonicity.
16. **Are the quality scores robust to VMAF model version, feature flags, and phone/desktop viewing assumptions?** No version sensitivity is reported.
17. **What precisely is measured by the mean gap?** The current 'Gap' column is a threshold shortfall, not a paired improvement.
18. **Why is the cut-frame score sometimes exactly zero?** Rule out off-by-one errors before claiming transition buffering or settling.
19. **Does the reported 84.6% miss probability apply to the same start-generation support used in all experiments?** Supply the exact generator and support boundaries.
20. **What is the minimum scientifically defensible contribution after removing claims unsupported by human tests and real videos?** This should be explicit in the conclusion.

---

## J. Prioritized mitigation plan (without turning this into a different paper)

### Must address before submission if possible

1. **Run realistic x264 conditions.** At a minimum: scene-cut on/off × realistic/clip-long GOP, on the existing clips. This is the strongest challenge to external validity.
2. **Fix CRF-ladder ambiguity and nonmonotone search.** Supply exhaustive encoded-rung logic, including why odd CRFs appear and which rungs were shared. This is the strongest immediately fixable reproducibility issue.
3. **Add a truly held-out experiment.** The same frozen rule on new backgrounds, page locations, and at least some authentic motion or screen captures. State failures as well as wins.
4. **Precisely delimit the main claim.** The present evidence supports a failure **in scripted short hard-cut screen clips with specific x264 settings under VMAF-defined acceptance**, not an established universal readability or coding-efficiency improvement.
5. **Make the novelty claim defensible.** Either clearly position a rigorously measured counterexample or supply comparison to nearest prior temporal-sampling research.

### Strong additions if time and space permit

6. Add a lightweight text-recognition or controlled human reading check; avoid treating VMAF 90 as a readability guarantee.
7. Compare a stronger scene-aware/content-aware baseline and report equal-size or rate–distortion behavior.
8. Give a few negative cases where the settled method does not help; they are scientifically valuable and prevent overclaiming.
9. Release exact data, script, encoder, frame-index, and metric instructions for reproduction.
10. Report full computational cost only if the paper intends to make an efficiency claim.

### Suggested three-page evidence hierarchy

- **Abstract:** Specific failure and conditional result, not a universal generalization.
- **Introduction/prior work:** Why a *rare-event* quality-assessment counterexample merits attention; what nearest work already established.
- **Methods:** 900 frames/30 fps, short page, eight centers, settled frames, 9th/45th-worst evaluation, full CRF-ladder logic, exact x264 flags.
- **Primary result:** One concise timeline/VMAF figure plus compact mean/median/range, 12/12 decision outcome, +27% bytes, cluster caveat.
- **Robustness:** Highest-value held-out and normal-encoder conditions, even if abbreviated in a single small table.
- **Limitations:** Synthetic content; no readability study; no broad codec/general-domain claim.

---

## K. Honest overall severity assessment

**Likely rejection drivers:** **C01/C02** (novelty), **C08/C12/C13** (constructed/non-realistic scenarios), **C19/C20** (encoder choices), **C23** (weak baseline), and **C32/C33** (quality metric versus claimed relevance). **C26/C27** (CRF methodology) could become rejection drivers if an actual error, rather than an exposition gap, is revealed.

**Most fixable without major new research:** **C26, C27, C36, C47, C59, C60, C64** (definition, consistency, labeling, and clarity). More experiments are needed for generalization, readability, and standard-encoder claims.

**Important positive counterweight:** The source paper *does* state several of its own caveats, report larger file sizes, analyze alternatives, distinguish boundary clips from the main mean, and avoid claiming a complete system speedup. These are strengths and should be preserved. A limitation is not automatically a fatal flaw when the paper claims only what it directly tested.

**Bottom line:** The best reviewer defense is **not** to pretend every objection is solved. It is to ensure that (1) the key result survives normal encoder settings, (2) the CRF-selection path is auditable, (3) the novelty is framed as a bounded and useful counterexample, and (4) claims about readability and general deployment do not exceed the evidence.
