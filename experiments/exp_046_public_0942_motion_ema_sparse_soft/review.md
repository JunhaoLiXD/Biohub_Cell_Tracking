Here is my independent review.

---

# Independent Review — `exp_046_public_0942_motion_ema_sparse_soft`

## Summary

exp_046 keeps fixed motion-relink EMA alpha 0.4 for ordinary updates and applies a milder-than-rejected alpha 0.6 to the ~1.18% of frozen-validation updates (~1.16% of test) that simultaneously satisfy a label-free guard: normalized velocity innovation > 1.25, source track age ≥ 3, a finite second-best assignment candidate, and selected-assignment margin ≥ 0.5. Parent is terminal KEEP `repro_041_public_0941_motion_ema` (0.9387332376874039; user-reported Public LB 0.942). The change is a single, cleanly isolated variable, correctly implemented, honestly instrumented, and strictly gated. The one real weakness is expected effect size, not correctness.

## Methodology

- **One variable (Q1).** Only the effective alpha on the guarded subset changes (0.4→0.6). `EMA_ALPHA=0.4`, `VELOCITY_WEIGHT=0.5`, `LEARNED_BONUS=1.0` are all pinned via env in the setup cell — the `0.75` learned-bonus fallback (nb:243) is never reached because nb:49 pins it to `1.0`. Checkpoints, detector/association/ILP/gap-closing/division logic, frozen train16 samples, strata, and scorer are unchanged.
- **Validation protocol (Q2).** Frozen train16 stratified proxy, 8 samples/specimen, 4 division-positive each, 44b6/6bba split preserved, scored against the exact parent. Leakage (frozen models saw training videos) is acknowledged and, being identical on both sides of the paired delta, does not bias the comparison. The guard is genuinely label-free — I confirmed in code it reads only `innovation_ratio`, `source_track_age`, and `assignment_margin`; no specimen/video/ground-truth dependency.
- **Parent justification & non-duplication (Q5/Q7).** This is exactly the follow-up the exp_043 analysis recommended ("calibrate a genuinely rare label-free soft-update gate") after global alpha 0.6 (exp_042, REJECT −0.00105) and the alpha-1.0 hard reset (exp_043, REJECT, 39.3% reset) both failed. Distinct from both.
- **Sparsity claim is supported by recorded evidence (Q7).** From diag_045 test telemetry, guarded_gt_1250 = 149+106+10+1010 = 1275 over eligible = 109,993 → 0.011592, matching the recorded `test_guarded_fraction_at_1_25 = 0.0115916`; validation 0.0118181 is consistent.

## Implementation risks

- **Correctly wired (Q3/Q4).** `assignment_margin` = min(finite alternative costs) − selected cost, computed from runtime costs *before* the velocity update (nb:959–962) and passed into `_use_sparse_soft_alpha` (nb:1019–1020). Nonfinite margins → NaN → rejected by the `np.isfinite` guard. Innovation = `‖step − prior_ema‖ / max(‖step‖,‖prior‖,1e-6)` (nb:1016–1018), matching the config. Strict `>1.25`, age `≥3`, margin `≥0.5` all match spec.
- **Self-consistent contract (Q3).** Enforces `soft == guarded_gt_1250`, `soft + base == eligible`, `finite + nonfinite == eligible`, threshold monotonicity/nesting, and both specimens exercised (nb:2457–2481, 3322–3325). A runtime config-verification block compares effective `soft_alpha / innovation_threshold / min_assignment_margin` against expected constants (nb:2518–2525) — it verifies effective config, not stale prose (Q4).
- **Gates are parent-relative and meaningful.** aggregate ≥ parent + 0.0001; per-specimen adjusted-edge ≥ −0.001; worst-video delta ≥ −0.002; div TP≥4 / **FP≤8** / FN≤8 (nb:3327–3338). FP≤8 equals the parent, so any new false division fails.
- **Diff scope.** Working-tree changes are bookkeeping only (GOAL/AGENTS/STATE/GPU_BUDGET/results, etc.); no edits to scorer, controller, or training code. Purely additive.

## Budget (Q6)

2.0 GPU-h planned; ~14.57 h usable after the 6.0 h reserve; within the 4.0 h single-experiment cap. This bounded review is the single authorized model call. Cost is proportionate — even a null result definitively closes the alpha-0.6 branch.

## Caveat (non-blocking)

Expected gain is asymmetric: global alpha 0.6 was net-negative, and the hypothesis bets the sign flips on this confident, high-innovation subset. The telemetry supports *sparsity* but, as the config states, is "not event-level causal evidence of benefit," and a 0.0001 floor over ~1.18% of updates is a small target — a marginal/null outcome is plausible. That is a reason to expect a possible REJECT, not to block a cheap, correctly-isolated test. Any positive result is still a paired proxy screen and would require reproduction before promotion (none authorized).

## Required changes

None.

## Recommendation

Safe to proceed: run snapshot smoke, and on smoke PASS launch exactly once on Kaggle for validation only. No leaderboard submission, promotion, milestone v06, reproduction, or successor is authorized.

VERDICT: PASS
