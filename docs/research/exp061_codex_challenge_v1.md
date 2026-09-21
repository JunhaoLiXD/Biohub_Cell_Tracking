# exp_061 — Codex strategy challenge v1 (verdict: REVISE)

Reviewer: Codex `gpt-6-astra`, low, read-only. Date: 2026-09-20.
Target: proposal v1 (`docs/research/exp061_z_reflection_deepcenter_tta_proposal.md`).
Full agent trace: scratchpad `exp061_codex_challenge_v1.log` (3432 lines).
Anchors: **P** = the proposal; **N** = `.private/current/exp060_deepcenter_safe_div_threshold_sweep.ipynb`.

## Verdict: REVISE

"The three fixed arms are defensible as an exploratory TTA experiment, but v1 does not yet
establish a feasible execution plan or sufficiently narrow interpretation. The 0.947 parent,
checkpoint lineage, and exp_060's 0.947/+11-forks result are supported by the records; they do
NOT establish that a larger representation perturbation will produce a larger or beneficial LB
change."

## Findings

1. **P1 — Replay boundary must precede GAP CLOSING, not merely safe division.** The changed
   heatmap first feeds `close_single_frame_gaps`, then `recover_strict_gap2`, THEN safe division
   (N cell2:3047–3052). exp_060's pre-safe-division snapshot would suppress part of the treatment.
   → Replay full `filter_output_graph` from immutable raw predictions, OR snapshot exactly BEFORE
   the first DeepCenter consumer. Deep-copy nodes/edges/stats/bookkeeping; reset config; preserve
   insertion order. Add **gap-veto identities/outcomes** to telemetry. Keep arm-order-invariance +
   shared-input-immutability checks via bounded local fixtures (not multiple full GPU replays).

2. **P1 — Three-arm budget unsupported; repeats exp_060's watchdog-kill failure mode.** Real cost
   for a square scored frame evaluated independently is **8 + 16 + 8 = 32 DeepCenter forwards** vs
   8 for a shared heatmap; "Z doubles the passes" describes one arm. exp_060 hit the 2.0h watchdog
   and killed thr022 even while sharing heatmaps (STATE.json:39–48). → Replace the estimate with a
   COMPONENT budget (shared inference, 3 graph replays, per-arm DeepCenter eval, telemetry,
   finalization); quantify what disabling the parent sweep saves. Fix execution order
   **xyonly → zon → xyd4**; add time checkpoints, a finalization reserve, atomic per-arm artifacts,
   explicit partial-run status; don't start an arm without enough estimated time. If reuse is
   needed, share immutable **provenance-keyed individual VIEW predictions** (not completed
   heatmaps), preserving each arm's accumulation order. If 3 arms can't credibly fit, return the
   budget/scope conflict for direction.

3. **P1 — Fixing only the inner cache key doesn't close cache+resume leakage.** Inner cache key
   `(dataset,t)` (N cell2:2093) AND an outer persistent wrapper with the same key that can return
   before the inner runs (N cell3:258–269). Separately, `_postprocess_resume_signature` hashes
   selected GLOBALS, not env vars (N cell2:318–325), so adding `BIOHUB_DEEPCENTER_TTA_ZREFLECT`
   alone need NOT invalidate base/final submission-resume records (cell2:3198–3203, 3814–3817).
   → Enumerate every cache layer + derived resume artifact; a genuinely fresh isolated dict per
   arm is sufficient for heatmaps; define a canonical TTA **signature** (ordered transforms,
   multiplicities, aggregation semantics, impl version, bound to checkpoint/input provenance);
   reject legacy artifacts lacking it; share only verified upstream predictions; negative tests
   for wrong-arm / missing-signature / stale-version reuse. (P:86's "resume artifacts cache
   heatmaps" needs a real artifact anchor or should be narrowed to submission-resume records.)

4. **P2 — `xyd4` under-specified; "in-distribution" unproven.** ADDING the missing reflection to
   the existing 8 gives 9 evals and keeps the duplicate's extra weight; a uniform 8-view D4 must
   **REPLACE** the duplicate (the anti-transpose at N cell2:2125–2126). → Give ordered
   forward/inverse transform lists + weights for all 3 arms; xyd4 replaces the duplicated X-flip
   slot with the anti-diagonal reflection; keep the square-XY condition, define nonsquare
   behavior; verify transforms+inverses on an asymmetric coordinate fixture. Call xyd4
   "geometrically better motivated," NOT in-distribution.

5. **P2 — Mechanism guard conflates a valid null with implementation failure.** Requiring a
   nonzero zon−xyonly heatmap diff can reject a correctly-executed reflection-equivariant model,
   and has no xyd4 execution check. → Separate **execution validity** (intended transforms,
   inverses, view counts, finite outputs, cache provenance) from **observed response**
   (matched-frame logit/score diffs, gate crossings, final-graph diffs). A verified zero response
   = mechanism NULL (prevent duplicate submission), not an implementation failure. Control SHA
   identity requires a **freshly computed** control, not a resumed parent CSV; keep the remote SHA
   gate without demanding remote GPU parity as a prerequisite to the run that measures it.

6. **P2 — Scientific interpretation exceeds what the arms identify.** DeepCenter is a pass/fail
   **veto** (N cell2:2731–2732); surviving proposals are ranked by `parent_dist + 0.15*sister_dist`
   (2740–2746) — the heatmap does not replace daughter ranking; it changes eligibility and, via
   earlier gap repair, graph structure. The Z-exclusion comment is at
   `experiments/repro_003_public_0933_kaggle_slug/remote_output/tracking_repo/scripts/predict_unet_transformer.py`:381–384
   (the root-level path cited in P is absent) and is a DETECTION-model comment, not proof the
   DeepCenter checkpoint treats Z reflections as OOD (a Z reflection preserves axial spacing).
   → Reframe as a **shared repair-heatmap intervention** (affects gaps AND divisions); Z is an
   uncertain symmetry assumption. Remove "must exceed the threshold experiment's effect" and
   "+11 forks is necessarily below LB resolution" (unknown public-subset membership/denominators).

7. **P2 — Interpretation matrix overclaims mechanism; selection rule incomplete.** Opposing arm
   scores don't prove "OOD-Z hurt"; two ties don't prove the whole representation layer is
   LB-insensitive; both-improving is unhandled. → Limit conclusions to "Z averaging regressed" /
   "D4 reweighting improved" / "no displayed difference"; treat OOD as possible not identified;
   pre-register a fixed tie preference when both improve; prohibit unplanned neighbor probes;
   LB selection is tuning, not generalization proof.

8. **P2 — Route from 3 CSVs to 2 LB measurements missing from the budget.** exp_060 ultimately
   needed a SEPARATE GPU notebook rerun per arm (the `safediv018-lb-submit` notebook); three CSVs
   from one run don't establish both arms can be LB-submitted from one execution. → Specify the
   authorized submission route per distinct output (canonical `submission.csv` handling, exact SHA
   verification, extra runtime). Don't resubmit byte-identical outputs.

## Non-blocking

- P:24 overstates universal gating — missing model/data/score paths bypass the veto (N
  cell2:2166–2178).
- P:185–186 should promise **prediction equivalence**, not notebook byte identity.
- Update stale two-arm / optional-arm language and the already-resolved §8 user decision.

## Minimal changes for CONSENSUS

Specify the pre-gap replay boundary + complete cache/resume contract; define exact transforms +
valid-null checks; provide a credible three-arm timing + submission budget with protected
completion order; narrow the scientific/selection claims. **No new train16 study, extra arm, or
proof of improvement is required.**

## Status

Strategy REVISE (round 1). Next: Claude revises the proposal to v2 addressing all P1+P2 findings,
then re-challenges. No build until CONSENSUS.
