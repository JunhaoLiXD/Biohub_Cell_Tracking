# exp_065 — Codex strategy challenge v2 (round 2) — REVISE

Reviewer: Codex `gpt-6-astra`, effort low, read-only sandbox. Date: 2026-09-25.
Target: `docs/research/exp065_metric_aligned_pruning_proposal_v2.md`.
Round 1: `docs/research/exp065_codex_challenge_v1.md` (REVISE, 7 blocking findings, all verified genuine).

**VERDICT: REVISE.** Round-1 findings **F1, F2 and F4 are FIXED**; F3, F5, F6, F7 **partially fixed**.
**Five new blocking `[CORRECTNESS]` findings.** No CONSENSUS.

**Claude Code's independent verification: ALL FIVE new findings are GENUINE**, re-derived from the
notebook sources and the archived CSVs. Nothing was rejected. See the verification and remediation
note at the end.

---

VERDICT: REVISE

## Verdict

V2 fixes the central notebook execution defects: the auto-attach assertion can stop execution before overrides affect inference, and the snapshot preserves the base submission at the correct location. The prefix-guard calculation also reproduces the archived results exactly. However, the new subset gate does not implement its stated rule, several withdrawals remain contradicted by active records, and measured candidate timings undermine the proposed GPU reservation. These prevent strategy-level CONSENSUS. No files were changed.

References below use zero-based notebook cells and one-based source lines. **Proposal** means `docs/research/exp065_metric_aligned_pruning_proposal_v2.md`; **vehicle** means `docs/research/public_notebook_archive/optimized-biohub-max-score.ipynb`; **analysis** means `docs/research/public_notebook_archive/amanatar_v9_sweep_telemetry/analyze_sweep_table.py`.

## Round-1 findings: fixed or not

- **F1 — fixed:** the assertions after vehicle cell 0:228 precede actual override application at cell 5:2872. The mount audit is incomplete, but the runtime guard covers successful auto-attachment from any matching input mount. Proposal:213–238.
- **F2 — fixed:** the snapshot after cell 5:2880 preserves the completed base file before the subsequent rewrite. Proposal:240–259.
- **F3 — partially fixed:** Run 1’s two changed lines and six added lines are correct; initial deadline and validator settings are correctly described. Run 2’s exact budget and applicability of the local gates remain inconsistent. Proposal:196–211, 315–332.
- **F4 — fixed:** candidate-specific weights and pooled division counts match the notebook, with zero residual in Python. Analysis:101–126. The newly added subset analysis has separate defects below.
- **F5 — partially fixed:** v2 correctly withdraws tight-distance inertness, but active summary and handoff text still assert it. Proposal:168–175; `STATE.json`:82, 698; `HANDOUT.md`:201–204.
- **F6 — partially fixed:** v2 corrects the multiplier, base ratio, and core-relative mechanism; the recon and state retain the rejected claims. Proposal:88–115; recon:74–77, 120–125, 210–219; `STATE.json`:696, 722.
- **F7 — partially fixed:** v2 correctly specifies 41 declared candidates, 29 unmeasured, and 15 eligible pruning candidates. Active records still carry the old counts and selection contract. Proposal:162–164, 354–366; recon:139; `STATE.json`:701, 719; `HANDOUT.md`:156.

## Blocking [CORRECTNESS] findings

1. **Gate 2 counts ties as losses, contrary to its specification; the reported median is also wrong.**

   Proposal:360 permits at most three **negative** subsets. Analysis:191 and 249 count `v <= 0`, including unchanged subsets. This can change PASS, MARGINAL, and rejection decisions for sparse interventions.

   The distinction already affects the archive:

   | Candidate | Negative | Exactly zero | Script’s “negative” |
   |---|---:|---:|---:|
   | `dcsd015` | 9 | 9 | 18 |
   | `tight55` | 0 | 36 | 36 |

   Consequently, proposal:160 and 376 incorrectly describe `dcsd015` as having 18 negative subsets.

   Analysis:250 reports sorted element 18 as the median of 36 values. The conventional median averages elements 17 and 18. For `ep015`, it is **+0.002796469593285137**, not **+0.00319**. Proposal:157 and `STATE.json`:737 inherit this error. Its ten negative subsets and rejection remain correct.

2. **The GPU estimate and reservation contradict the harvested timing evidence.**

   Proposal:341 budgets approximately three hours and reserves four for Run 1. The `seconds` column in `ppsweep_results.csv` records **4,652 seconds of scoring across 14 configurations**, with a median of **324.83 seconds per configuration**.

   Using the proposal’s approximately 7,000-second existing run, adding the 29 previously unmeasured candidates gives:

   `7000 + 29 × 324.83 ≈ 16,420 seconds = 4.56 hours`.

   Even extrapolating at the fastest observed configuration gives approximately **4.50 hours**. These are estimates, not guaranteed durations, but they directly contradict the claimed three-hour extrapolation and exceed the four-hour reservation.

   The preserved sweep deadline is **26,100 seconds**, not four hours, and checks occur between candidates: vehicle cell 0:107; cell 10:144–148. Neither the notebook nor this proposal establishes the reservation as an execution bound.

3. **The claimed correction across current records did not happen completely.**

   Proposal:11–15, 27–29 claims propagated corrections, including withdrawal “everywhere.” Contradictions remain in documents explicitly presented as current:

   - `STATE.json`:82 still says pruning is universally profitable and tight-distance settings are inert.
   - `STATE.json`:716–719 still specifies the crashed-run preservation argument, exactly one authored line, and selection across all 41 using leave-one-out.
   - `STATE.json`:696, 701 retains the incomplete multiplier description and 27 unmeasured candidates.
   - `docs/research/lb_recon_2026-09-25_amanatar_sweep.md`:124, 139, 213, 218 retains the wrong base ratio, count, and unsupported count-target rationale.
   - `HANDOUT.md`:176–191 still presents v1 as the live challenge and promises the control without its snapshot; lines 201–204 still disqualify tight-distance interventions.

   The appended correction fields are valuable, but coexist with contradictory operational fields without consistently identifying those fields as superseded. This is an ambiguous handoff, not merely preserved historical evidence.

4. **The executable analysis gate reports validation failures without enforcing them.**

   Proposal:331–332 requires exact archived prefix reproduction before analysis is used for selection. Analysis:118–126 merely prints `MATCH` or `MISMATCH`, accepts residuals below `1e-9` rather than requiring zero, and returns normally. `main()` continues to selection at lines 167–224 regardless.

   The current archive passes exactly; that does not make this a fail-closed gate for later inputs. Its data checks also establish only that configurations present share the base stem set—not that there are four stems per prefix or that all required candidates were measured. A deadline-truncated sweep can therefore reach selection without an explicitly defined incomplete-measurement disposition.

5. **Run 2’s claimed exact authored-line budget is not valid for every eligible candidate.**

   Proposal:207–211 counts one changed line per selected key. But `seg040L6` specifies `SEG_PRUNE_MAX_LEN=6`, already the vehicle default: cell 0:110 and cell 10:65. Two override keys therefore do not necessarily mean two changed lines.

   Moreover, proposal:318–330 describes Run 1-specific checks—validator enabled, levers off, fast tier zero—without defining their Run 2 applicability. Run 1’s source-line budget is correct and mechanically assertable; a universal two-run “exact” gate is not yet specified consistently.

## Non-blocking findings

- **[DESIGN] The max-three rule is strict but not impossible.** A broadly positive candidate can pass all 36 subsets. There is no evidence that every unmeasured pruning candidate must fail. However, three is a risk-tolerance choice, not a statistically calibrated error rate. These overlapping subsets are dependent; “28% of draws lose” is an empirical subset fraction, not an estimated hidden-test loss probability.

- **[DESIGN] MARGINAL is coherent only as an explicit exception.** Escalation to the user avoids automatic author discretion. A marginal candidate nevertheless has not passed the registered gate. Subsequent authorization would be a documented exception or revised decision, not a Gate 2 PASS. Rejecting `ep015` also does not establish that thresholds were not reverse-engineered, contrary to proposal:380–382.

- **[DESIGN] Fifteen eligible candidates versus 41 measured candidates is logically coherent.** The explicit family excludes generated combinations and unrelated interventions from selection. The concern is cost: the extra rows are not demonstrably cheap given the recorded timings, and their future interpretation must remain separate from this experiment’s eligibility.

- **[RISK] Run 2 substantially reduces hidden-rerun exposure.** Disabling validation and sweeping removes the largest added workload. It does not establish identical runtime: selected pruning, the additional snapshot, and time-dependent repair behavior remain. Proposal §5.1 appropriately limits byte equality, but §3.1:129 still overstates it as establishing that “the vehicle is the parent.”

- **[RISK] The provenance and weighting qualifications are appropriate.** Hashes establish archived bytes, not training exclusion or execution provenance. The 37.329%/62.671% mixture is correctly identified as predicted-node-based modelling. Fixed base weights within each prefix are an additional analysis choice; candidate-specific weighting remains correctly reserved for reproducing the author’s guard.

- **[SCOPE] Bounded measurement remains defensible; the stated three-hour scope does not.** At most one separately authorized submission is reasonable. Approximately four days does not inherently preclude this work, but scope must be judged against the evidence-based runtime and an explicit resource bound.

## What I verified and found correct

- All six archived SHA256 manifest entries match.
- The telemetry contains **112 rows: 14 configurations × 8 stems**.
- Running the analysis with Python reproduced **zero residual** for both the aggregate proxy identity and published prefix guards.
- Independent arithmetic reproduced `ep015` aggregate **+0.0023641441**, prefix regression **−0.0084938752**, ten negative subsets, minimum **−0.0058415097**, and maximum **+0.0137077229**.
- The 36 subsets enumerate every two-of-four pairing from each prefix and preserve the stated prefix mixture.
- A nonexistent explicit preset path would raise at cell 0:215. The proposed assertions occur after loading but before application to inference.
- The glob is nonrecursive and does not search `/kaggle/working`. It can search the competition mount, which the four-dataset audit omits; a usable hit still triggers the runtime assertion.
- Between the successful base write and proposed snapshot, the `finally` block only restores globals. `WORKING_DIR` resolves to `/kaggle/working` on Kaggle; the snapshot is a separate file, unaffected by later writes to `submission.csv`.
- Run 1’s proposed **two changed plus six added source lines** and their insertion locations are correct.
- No measured eligible candidate qualifies under either interpretation of the subset tie rule.

## What I could not verify

I did not inspect live Kaggle mounts or dataset versions, execute GPU inference, establish actual base-byte equality, retrieve a newly created snapshot, or authenticate current budgets, standings, and submission history. Snapshot retrieval is supported by its output location but has not been demonstrated for this proposed run. Hidden-test composition, training provenance, and equivalence to an independently retrieved official scorer remain unverified.

The shell tool failed to initialize. Filesystem inspection, hashing, and read-only Python calculations were completed through Node access. No implementation, launch, or submission occurred.

---

## Claude Code's verification and immediate remediation (2026-09-25)

All five re-derived independently. **All five genuine.**

1. **Ties counted as losses; median wrong — CONFIRMED.** My script used `v <= 0`, so an *unchanged*
   subset counted as a loss. Measured: `dcsd015` is **9 strictly negative + 9 exactly zero** (script
   said 18); `tight55` is **0 negative + 36 zero** (script said 36 — absurd, it is identical to
   base). `ep015` is 10 either way, so its rejection stands. Median: 36 values, `sorted(v)[18]` is
   not a median; `ep015`'s true median is **+0.002796470**, not +0.00319.
   **FIXED NOW:** the script counts strictly-negative and reports `unchanged` in its own column, and
   uses `statistics.median`.

2. **GPU reservation contradicts the timing evidence — CONFIRMED, and this is the one that changes
   the plan.** `ppsweep_results.csv` `seconds`: 14 configs, sum **4652 s**, median **324.83 s**,
   min 316.77, max 386.26. So `7000 + 29 × 324.83 = 16,420 s = 4.56 h`, and even at the fastest
   observed configuration **4.50 h** — against v2's 4.0 h reservation. Codex's arithmetic is exact.
   Also correct that `SWEEP_DEADLINE_S = 26100 s` (7.25 h) is the notebook's own bound, checked
   *between* candidates, so nothing stops the run at our reservation. **v3 must raise the reservation
   and state an enforced bound.**

3. **The corrections did not fully propagate — CONFIRMED on every citation.** I appended correction
   fields while leaving the original operational fields intact and contradictory:
   `STATE.json` still asserted tight-distance inertness, "exactly one authored line", the crashed-run
   preservation argument, leave-one-out selection over all 41, the imprecise multiplier and 27
   unmeasured; the recon document still carried 0.752 and 27; `HANDOUT.md` still presented v1 as live,
   promised the control without its snapshot, and disqualified `tight_um`.
   **FIXED NOW:** those fields were **rewritten**, not annotated. Superseded operational fields were
   removed from `exp065_proposal` and replaced with `*_current` keys.

4. **The analysis gate reported without enforcing — CONFIRMED.** It printed `MATCH`/`MISMATCH`,
   accepted residuals under `1e-9`, and `main()` continued to selection regardless. Its data checks
   also established only a shared stem set, not four stems per prefix nor that the eligible family was
   measured. **FIXED NOW:** both validations `raise SystemExit`; a stem-shape check raises; and a
   missing-candidate check sets `SELECTION_ALLOWED = False` so a deadline-truncated table is reported
   as evidence but **refuses selection**. On the current archive it correctly refuses — 13 of the 15
   eligible pruning candidates are absent.

5. **Run 2's line budget is not valid per candidate — CONFIRMED.** `seg040L6` sets
   `SEG_PRUNE_MAX_LEN = 6`, already the cell 0 line 110 default, so two override keys need not mean
   two changed lines. v2's per-run gate wording also does not say which §6 checks apply to Run 2.
   **v3 must state the Run 2 budget per candidate.**

Non-blocking findings accepted as written, and two of them require v3 text changes: §3.1 still says
Gate 1 establishes "the vehicle **is** the parent" where §5.1 correctly limits it, and the claim that
rejecting `ep015` proves the thresholds were not reverse-engineered is withdrawn — it is evidence
about one candidate, not about the rule's construction.
