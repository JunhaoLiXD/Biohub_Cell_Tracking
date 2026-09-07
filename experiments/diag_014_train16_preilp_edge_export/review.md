I have enough to write the review. The picture is complete: the pre-ILP export is a read-only, env-gated instrumentation patched into the real support-pack `predict_unet_transformer.py`, the gate enforces exact per-specimen reproduction of the diag_013/val_008 baseline at `abs_tol=1e-12`, and a local smoke test executes the patch against upstream source and checks stage ordering.

---

# Review â€” `diag_014_train16_preilp_edge_export`

## Summary
Tier-1 diagnostic export. It enables `BIOHUB_PREILP_EDGE_AUDIT=1`, which injects a read-only block into the support-pack `predict_unet_transformer.py` just after `probs = torch.sigmoid(raw)` and *before* `candidates = sorted(...)`, writing gzip-JSONL evidence (fused logit/probability, parent/child rank, parent/child margin, distance_um, source/target ids, stage tag `post_fusion_pre_threshold_pre_graph_pre_ilp`) for the top-4 parents-per-target âˆª top-4 children-per-source within 12 Âµm, for all 20 test+val datasets. It is the sanctioned **v9 Phase 0 enabler** (pre-ILP rank/margin/logit evidence feeding the A/B/C counterfactual oracle) named in `GOAL.md`, not a duplicate. The DeepCenter scalar-threshold branch that this line replaced is correctly recorded as closed (`exp_011` reject, `diag_012`/`diag_013` KEEP).

## Methodology
- **Single variable â€” yes, and enforced structurally.** `variables_changed: diagnostic_instrumentation_only`, and the runtime contract requires `baseline_output_preserved` and `baseline_specimen_outputs_preserved` to match `0.9252519785518039` / `44b6=0.9036583711â€¦` / `6bba=0.9329497722â€¦` at `abs_tol=1e-12`. Any behavioral leakage from the instrumentation fails the gate, so attribution is guaranteed by construction. The injected code uses `np.delete`/argsort copies and never mutates `probs`/`raw` or the downstream `candidates`.
- **Validation trustworthy for its purpose.** Protocol matches the parent (`public_0933_embedded_train16_stratified_proxy_v1`, 8/specimen, both `44b6` and `6bba` checked separately, sample-count-exact). The train-leakage caveat (frozen extractors saw train videos) is acknowledged and, importantly, does **not** bias this gate: the gate scores exact reproduction + export completeness, not a new metric improvement. The `success` thresholds correctly encode "reproduce exactly" (`minimum_improvement 0.0`, `regression_threshold â‰ˆ -1e-12`, `per_specimen_max_regression 0.0`).
- **Guards verify effective config, not prose.** The config guard cell diff-checks live env vars (incl. the safe-div and `BIOHUB_PREILP_EDGE_AUDIT_MAX_UM=12.0` knobs) at `abs_tol=1e-12` and raises before expensive work; the contract re-checks `det_threshold 0.965`, weights `0.81/0.15/0.15`, `gap 5.8`, veto disabled, audit enabled. Injection uses `count==1` assertions so it fails loudly if upstream source drifts.

## Implementation risks
- **gzip `sha256` is intra-run only, not cross-run reproducible (minor).** The summary hashes `_preilp_path.read_bytes()` of a `gzip.open(..., "wt")` file, whose header embeds mtime â†’ the `.jsonl.gz` sha differs run-to-run. `hashes_match` only verifies the recorded sha equals the on-disk file *within the same run*, which passes. The word "hash-verified" in the hypothesis should not be read as byte-identical cross-run export. If cross-run byte-identity is ever wanted, write with a fixed `mtime=0`.
- **Dense-frame cost (watch, non-blocking).** Per frame-pair it adds a full-matrix argsort plus a per-audit-pair `np.max(np.delete(...))` (â‰ˆ `topkÂ·(n_src+n_tgt)` pairs Ã— O(n)). On dense `44b6` frames this is the one place runtime could grow; diag_013 ran in 1.13 h against a 2.0 h tier-1 reservation, so there is headroom, but confirm at smoke time.
- **Output contract:** `preilp_export_passed` gate field is present and wired (`= validation_contract_passed`), and the `preilp_edge_audit_{datasets_exact(=20),rows_nonempty,stage_exact,hashes_match}` checks are all in `_controller_failed_checks`. No missing contract fields found.

## Budget
2.0 GPU-h reserved, tier-1. Remaining 20.0 h, reserve 6.0 h, per-experiment cap 4.0 h â€” within policy, no user approval needed. Information gain is high relative to cost: without this evidence the A/B/C oracle ceiling (the mandatory Phase 0 gate before any classifier/training spend) cannot be computed, and the export is label-free/reusable. Worth the spend.

## Required changes
None blocking. Before launch:
1. Run the local smoke test `scripts/validate_preilp_edge_export.py` (it execs the patch against the real `predict_unet_transformer.py`, checks required snippets, and asserts `audit < candidates < writer < return` ordering) and confirm it passes â€” it needs the gitignored `references/biohub-tracking-support-pack/` source present locally.
2. At smoke time, confirm per-specimen reproduction hits `1e-12` and note wall-clock on the densest `44b6` shard against the 2 h reservation.
3. (Optional) Document that `.jsonl.gz` sha256 is intra-run integrity only, or set fixed gzip mtime if byte-identical re-export is desired.

## Recommendation
On-plan, single-variable, self-protecting via exact per-specimen reproduction, with a genuine executing smoke test and a present gate field. Minor caveats are non-blocking.

VERDICT: PASS
