I have enough to write the review. The parent-diff was decisive on several points (single-variable confirmed; checkpoint config identical to a run that already succeeded). Here is my review.

---

# Independent Review â€” `exp_009_train16_deepcenter_div_veto`

## Summary
A clean, single-variable probe: flip `BIOHUB_DEEPCENTER_SAFE_DIV_VETO` `0 â†’ 1` so the frozen DeepCenter model confirms (at appearance score â‰¥ 0.12) each geometric safe-division proposal before it is added, on the fixed 16-video stratified validator. I diffed the full env block against the parent `val_008` snapshot: **the only functional change is line 192** (plus a descriptive `BIOHUB_SCORE_AXIS` label). Every other knob â€” `SAFE_DIV_MAX_UM=7.0`, frac caps, `ILP_DIVISION_WEIGHT=1.2`, DeepCenter checkpoint/epoch â€” is byte-identical to the parent. The hypothesis is testable and attributable. The newly-activated code path reuses `deepcenter_accept_repair_point`, the same function the (parent-active) gap veto already exercised, so machinery risk is low. The change is purely subtractive (rejection just `continue`s past the addition), which moves in the *safer* direction relative to the historical Version-7 "added division edge = edge-FP on dense GT" landmine.

## Methodology
- **Single variable:** Confirmed by parent diff. âœ…
- **Validation trust:** Train-derived 16-video validator (8/specimen, Â±division stratified, seeded SHA256 order). Leakage is real (frozen extractors saw all train videos) but explicitly acknowledged; `evaluation.mode: compare` against `val_008` with identical seed/env â†’ the same 16 videos are selected, so the paired delta is valid. Per-specimen metrics (`specimen_metrics` â†’ adj + div_J for `44b6`/`6bba`) and stratification flags are emitted, satisfying the promotion/regression gates. Baseline per-specimen values are hardcoded (`0.9037` 44b6 / `0.9329` 6bba), which is fine given the identical selection but would silently mislead if the validator ever drifted.
- **Power / expectations:** The effect is div_J-dominated, and the baseline safe-division stats are ~TP 3 / FP 45 on the whole set. Cutting FPs could lift div_J by ~+0.02 â†’ ~+0.002 score â€” right at `minimum_improvement`. With only ~3 division TPs and 84% of divisions in `6bba`, statistical power is low and `44b6` (few divisions) is the more likely place for a spurious regression. The **decision must lean on the raw division TP/FP/FN counts and per-specimen consistency, not the 4th-decimal score.** Instrumentation supports this: `safe_division_geometric_candidates` (pre-veto) + `deepcenter_safe_div_{checked,accepted,rejected,missing}` counters exist.
- **Not a duplicate:** Old rule-based divisions were closed on the *0.844* pipeline; this is a precision *filter* on the *0.912/0.933* learned-graph base and is consistent with the active v9 division direction. Complementary to (not contradicted by) exp_001/exp_002.

## Implementation risks
- **Config guard does not cover the changed variable (the important one).** The guard cell (`_EXPECTED_NUMERIC/_TEXT`) asserts only the *frozen* params (det 0.965, disappear 2.0, gap 5.8, min-track 6, bidir 0.15, harmonic mode). It never asserts `BIOHUB_DEEPCENTER_SAFE_DIV_VETO=1` or the 0.12 threshold, so the markdown claim that "runtime guards verify the exact effective values" is only half-true for *this* experiment. The env is set correctly in this snapshot (verified line 192), so the run itself is fine â€” but the guard would not catch drift on the variable under test.
- **Stale guard prose.** The guard prints `"Single model-level change: harmonic mutual-support association fusion"` / `"Reverse-time association weight: 0.200"` / `"public LB 0.913"` (lines 261â€“263) â€” copied verbatim from the parent and describing a *different* experiment. Misleading in logs/`CLAUDE_REVIEW` capture.
- **Misleading checkpoint comment (not a blocker).** Line 1007 comment says the pinned SHA is `best.pt (epoch 2), not checkpoint_last.pt (epoch 500)`, while the env pins the checkpoint to `checkpoint_last.pt` and `EXPECTED_EPOCH=500`. On static reading this looks like a hard-fail (SHA vs epoch contradiction), but the **parent ran to completion (0.9252) with byte-identical DeepCenter config**, so the integrity+epoch guards empirically pass; the SHA `8040â€¦` in practice corresponds to the epoch-500 file and the comment is simply wrong. Worth correcting to prevent a future false alarm.
- **Fail-open veto:** `deepcenter_accept_repair_point` returns *accept* if the bundle is missing, but `REQUIRE_DEEPCENTER_VETO=1` forces the model to load, so the veto genuinely applies. No missing-output-contract fields found; contract emits `score`, `adjusted_edge_jaccard`, `division_jaccard`, per-specimen and aggregate.

## Budget
2.0 GPU-h (tier 1) vs 25.3 h remaining and a 6 h reserve â†’ well within budget and under the 4 h approval ceiling. Needs a full inference pass (DeepCenter scoring is inside post-processing), so it is not a pure CPU replay, but 2 h on T4Ã—2 for 16 videos is reasonable. Information gain is a clean, attributable data point for the v9 division track; the low expected effect size is the main caveat, not the cost.

## Required changes (before launch)
1. **Extend the config guard** to assert the experiment's actual variable: `BIOHUB_DEEPCENTER_SAFE_DIV_VETO == "1"` and `BIOHUB_DEEPCENTER_SAFE_DIV_THRESHOLD == 0.12`. This is the one change that matters for methodology integrity.
2. **Fix the stale guard prints** (lines 261â€“263) to describe the DeepCenter safe-division veto, not harmonic fusion.
3. **Correct the misleading checkpoint comment** (line 1007) so the SHA/epoch identity is unambiguous (cosmetic, but prevents a future false hard-fail diagnosis).
4. **Confirm the printed diagnostics surface** `safe_division_geometric_candidates` and `deepcenter_safe_div_{checked,accepted,rejected}` so the decision can be made on division counts, and read the per-specimen `44b6` delta as the regression guard.

None of these threaten the correctness of the run; they are cheap and can be folded into the local smoke-test loop.

## Recommendation
Single-variable, leakage-aware paired protocol, per-specimen contract present, proven machinery, subtractive (low-risk) edit, affordable. The defects are guard-coverage/prose hygiene, not run correctness. Manage expectations: the likely outcome is a marginal or null score delta dominated by a handful of division events â€” judge it on TP/FP/FN and cross-specimen consistency, not the aggregate 4th decimal. Safe to enter local smoke testing after the guard/prose fixes.

VERDICT: PASS
