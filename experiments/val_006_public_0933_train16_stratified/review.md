I have what I need. Git is clean (no diff), and I've inspected the config, dependency/integrity guards, validator selection, per-specimen scoring, and the metrics contract. Here is the review.

# Review â€” `val_006_public_0933_train16_stratified`

## Summary
This is a **validation-protocol change only**: it swaps the parent's 4-video proxy (`repro_005`, two per specimen, division-first alphabetical) for a deterministic, seeded-SHA256, division-stratified **16-video** validator (8 per specimen, 4-positive/4-negative division target). Inference config, weights, and source patches are held identical to the reproduced team-fusion-v6 0.933 pipeline. It directly implements the "next gate" GOAL.md names ("eight videos per specimen (16 total) before any new detector or linker ablation"). The runtime guards verify **effective** config values (env + resolved globals) with `abs_tol=1e-12` and SHA256-pin all three model artifacts and the support-repo Python files, so the pipeline fails closed on drift. It is not a duplicate and is not contradicted by history. Budget (2.0 h, tier 1) is well within limits.

## Methodology
- **One variable / attributable:** Yes. `variables_changed: validation_sample_selection_only`; parent `repro_005`. The config guard (cell ~223) and the end-of-run contract (cell ~4368) both re-assert `DET_THRESHOLD=0.965`, `secondary_detection=0.81`, `secondary_edge/bidirectional=0.15`, `gap_close_um=5.8`, `min_track_len=6`, DeepCenter veto â€” reading live runtime values, not prose. Selection is deterministic (`sha256("public_0933_train16_v1:"+stem)`), independent of directory order.
- **Leakage:** Correctly disclosed. The validator draws from `TRAIN_DIR` and the frozen extractors saw all 199 train videos â†’ absolute scores optimistic. This is explicit in `config.yaml`, GOAL.md, and the notebook warning; decisions are delta/per-specimen only. The selection uses GT (`_stem_has_gt_division`) **only to build the eval set, never to alter predictions** (comment + code confirm). Train/test leakage is guarded: `candidates = [s for s in train_stems_all if s not in test_stem_set]`.
- **Domain split:** Enforced at runtime. The contract requires both specimens present, exactly 8 samples each, 16 total, and â‰¥1 division-positive per specimen; per-specimen `adjusted_edge_jaccard` and `division_jaccard` are reported separately. This satisfies GOAL.md's reporting rules.

## Implementation risks
1. **Stale descriptive label (main cleanup):** `BIOHUB_SCORE_AXIS = '... = validation 0.9382'` (cell ~156) carries `repro_005`'s 4-video proxy score into a 16-video experiment. It is explicitly non-authoritative and unchecked, but it is exactly the kind of stale prose that misleads a reader; it should be updated or made protocol-neutral.
2. **"4 division-positive per specimen" is a soft target, not enforced.** Given the ~125:26 division skew (84% in `6bba`), `44b6` may not have 4 division-positive videos. The selection silently backfills from `_validator_order` remainder, and the contract only checks `any(...)` division present per specimen â€” so a run with, e.g., 1â€“2 positive `44b6` videos passes while the config advertises "four-positive." Not a correctness bug (fails-open by design toward availability), but the realized stratification is only visible in the printed `n_division_selected`; it is not recorded per-specimen in the contract.
3. **Experiment-ID injection unverified by the contract.** `_CONTROLLER_EXPERIMENT_ID = "__CONTROLLER_EXPERIMENT_ID__"` relies on controller injection (`inject_experiment_id: true`); no check fails if the placeholder survives. Low risk (matches the `repro_005` mechanism), but the contract doesn't assert it.
4. **Smoke-test target vs. snapshot.** The smoke test and `source_notebook` point at `.private/current/repro_public_0933.ipynb`, while this review covers the frozen `experiments/.../snapshot/source/` copy. Git is clean, but confirm the two are byte-identical before launch so what's reviewed is what runs.

No missing output-contract fields: `metrics.json` carries `schema_version`, `experiment_id`, `primary_metric`, per-specimen `{primary, adjusted_edge_jaccard, division_jaccard, samples}`, and `metrics.validation_contract_passed` (the declared `gate_field`) with `failed_checks`/`checks`. Sample-count and config checks **fail closed** (a skipped/missing sample drops `n_samples`â‰ 16 â†’ contract fails).

## Budget
2.0 GPU-h reserved, tier 1. Remaining 26.48 h, reserve 6 h, single-experiment cap 4 h, approval threshold 4 h â†’ no user approval needed. Scaling from `repro_005` (4 train videos in 0.52 h) to 16 videos sharded across 2Ã—T4 (~8/GPU) lands near ~1â€“1.5 h; 2 h has margin. **Information gain is high and foundational:** it establishes the stable, division-stratified, per-specimen baseline that every future detector/linker ablation will be compared against â€” a prerequisite the 4-video proxy cannot provide. Worth the spend.

## Required changes
Before the **Kaggle launch** (none block local smoke):
1. Update or neutralize the stale `BIOHUB_SCORE_AXIS` "validation 0.9382" label so it doesn't assert a 4-video number under the 16-video protocol.
2. Record realized per-specimen division-positive/negative counts in `metrics.json` (and either enforce the `4/4` target or downgrade the config wording to "target, best-effort under `44b6` division scarcity") so the stratification is auditable rather than implied.
3. Confirm `.private/current/repro_public_0933.ipynb` (smoke + run target) is byte-identical to the reviewed snapshot.
4. Optional: add a contract check that the injected `experiment_id` is not the literal placeholder.

None of these change the scored outputs; the guards already fail closed on config drift, checksum mismatch, and sample-count shortfalls.

## Recommendation
Methodology is sound and matches the sanctioned next gate; the single variable is cleanly isolated; leakage and the 44b6/6bba split are handled and disclosed; guards verify effective configuration; budget is fine. The open items are prose/auditability cleanups that can be resolved during smoke testing and before the Kaggle commit.

VERDICT: PASS
