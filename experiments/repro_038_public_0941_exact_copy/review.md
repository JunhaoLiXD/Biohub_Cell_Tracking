I have everything needed. The notebook, adapter, validator, config, budget, and history are all consistent. Here is the review.

---

## Summary

`repro_038_public_0941_exact_copy` runs a **byte-identical** copy of the archived `analyticaobscura/biohub-lb-941` notebook (SHA256 `24253caeâ€¦225389`, enforced by both the smoke test and the collection adapter) under the `lingxd` account, attaching the three declared pilkwang datasets on a T4Ã—2, internet-off, to produce a valid submission and probe the advertised Public LB 0.941. It is explicitly a **full-source reproduction / LB probe**, not a single-variable ablation, and the research director authorized exactly this one-off in `GOAL.md` (2026-09-05). It carries one authorized leaderboard submission. Verdict field `public_lb_reproduction_passed` is deliberately left `None`; the adapter marks `reproducible=False` and defers the real verdict to the separately recorded remote LB. Parent is `repro_036_train16_motion_ema` (reproduced 0.933 milestone).

## Methodology

- **Testable but not single-variable â€” by design.** The one-variable rule is deliberately waived here (`variables_changed: full_source_snapshot_reproduction_not_causal_ablation`), matching the explicit `GOAL.md` authorization. No mechanistic attribution can or should be drawn from this run â€” its purpose is provenance and a reproduced ceiling above our 0.933, which `GOAL.md`/`public_solution_review` justify (the advertised 0.940/0.941 forks differ from our isolated EMA via one-frame motion + wider division geometry + sister-symmetry gate). The parent legitimately motivates it.
- **Validation protocol is trustworthy for its limited purpose.** The upstream 4-video validator (`VALIDATOR_ENABLE` defaults on; `by_prefix` groups by specimen, division-first, `N_PER_TYPE=2` â†’ 2Ã—44b6 + 2Ã—6bba) is **leaky and thin**: the frozen detector/transformer/DeepCenter saw all 199 train videos, so absolute train4 scores are optimistic. This is flagged everywhere (config warning, adapter `warning`, `reproducible=False`) and is explicitly *not* used as the verdict. The validator correctly **excludes the 4 test-copy movies** from its held-out candidates. Per-specimen 44b6/6bba metrics are emitted, satisfying the domain-split reporting rule. Not comparable with train16 â€” and the config says so.
- **Duplicate/contradicted check: clean.** No prior experiment reproduced the 0.941 full config; `exp_037` (velocityÃ—1.0 EMA, REJECT) is a different mechanism and does not contradict this.

## Implementation risks

- **Provenance gap (the `GOAL.md` concern) is resolved by the source itself.** The notebook hard-enforces `_deepcenter_expected_sha256 = "8040999aâ€¦7edafe2a0"  # best.pt (epoch 2), not checkpoint_last.pt (epoch 500)` and raises on mismatch. The collect adapter *independently* re-verifies via `bidirectional_production_runtime_integrity.json` (path ends `/best.pt`, sha equals `DEEPCENTER_SHA256`) **and** the run log (requires the exact "Loaded DeepCenter add-only gate checkpoint:" line and rejects any `checkpoint_last.pt` load). The earlier checkpoint_last/epoch-500 fallback was in our train16 loader, which is not on this path. This is effective-config verification, not stale prose.
- **Output contract is faithful.** Adapter `aggregate()` mirrors upstream `aggregate_official()`: `weight = edge tp+fp+fn` (edge-union count, confirmed â€” **not** division count), so the `weight<=0` guard is safe; divisions pooled. `read_validator` requires exactly `stem, weight, adjusted_edge_jaccard, div_tp, div_fp, div_fn` â€” all present in the notebook's per-sample row. `audit_submission` enforces the full 10-column schema, 4 test movies (2/specimen), consecutive-frame edges, parent-degree â‰¤1 / daughter-degree â‰¤2, and no dup/dangling edges.
- **Collection is strict â†’ fragile on environment, but fails safe.** If the validator produced â‰ 4 rows / not 2-per-specimen, if `validator_results.csv` were absent, or if Kaggle's log JSON didn't surface the DeepCenter print line into `event["data"]`, `collect()` raises â†’ `INVALID_METRIC` and consumes budget. These are hard-fails, **not false passes**; the established repro_036 pattern parsed logs successfully, so risk is low but non-zero.
- **Highest external dependency:** the attached DeepCenter dataset must actually contain `best.pt` with the expected sha (the candidate search lists `checkpoint_last.pt` first). If it resolves the wrong file, the notebook's own checksum guard aborts the run cleanly â€” again fail-safe, not a silent wrong result.
- The notebook is unmodified (no experiment-ID injection, no metrics cell); all added logic lives in the external adapter/validator, which never executes the notebook. Upstream algorithm preserved.

## Budget

Tier-1, 2.0 GPU-h reserved. Remaining 14.11 h minus 6.0 h reserve â‰ˆ 8.1 h usable; 2.0 â‰¤ `max_single_experiment_hours` 4.0 â†’ within policy, no user approval needed. One authorized LB submission (of 3/day); `remote_history_required_immediately_before_submit: true` is set. Information gain (does 0.941 reproduce under our account; is the 0.940/0.941 config family the right next direction) is high relative to a single 2-h run.

## Required changes

None blocking. Recommended cheap (non-GPU) pre-launch confirmations:
1. Confirm the attached `pilkwang/biohub-deepcenter-unet3d-center-prior-v1` contains `best.pt` matching `8040999aâ€¦7edafe2a0` (otherwise the run hard-fails â€” acceptable, but wastes the slot).
2. Keep the smoke test (`validate_public_0941_copy.py`) as the local gate; note it is static-only (sha + `ast.parse` + no-CJK) and does not exercise the 4-row/2-per-specimen validator or the log-line guard â€” so treat the first collection as the contract test.
3. At submit time, honor the config's immediate remote-history check and the 3/day cap; record in `SUBMISSION_BUDGET.json`.

## Recommendation

The experiment has one explicit (reproduction) hypothesis, an explicit change, a parent, a passing static smoke test, sufficient budget, and â€” critically â€” runtime + collection guards that verify the effective configuration (checksums, log-line, submission graph) rather than trusting notebook prose. Its train4 proxy is honestly labeled leaky and non-verdict; the real judgment defers to the remote LB with `public_lb_reproduction_passed=None`. It is explicitly authorized and non-duplicate. Safe to proceed.

VERDICT: PASS
