# Independent review — `repro_048_public_0946_exact_copy`

## Summary
This is a full-source reproduction / LB-probe of the public `reyhanksatria/biohub-cell-tracking-0-946-lb` notebook, edited only by declared dataset-path substitutions, run under `lingxd`. It is **not** a controlled single-variable ablation, and the config says so honestly. Parent is `repro_038` (the analogous 0.941 exact-copy probe); lineage, protocol (submission-integrity + external LB), and guards mirror that accepted pattern. Notebook integrity is airtight (dual SHA256 pins + reconstruct-and-compare), edge-feature TTA is verified present, motion-EMA verified absent, and the collection guard verifies the *effective* DeepCenter checkpoint against a pinned hash. State is PROPOSED / review PENDING / smoke PENDING — this is the mandatory prelaunch review. No launch-blocking defect found.

## Methodology
- **Q1 (single variable):** Correctly *not* single-variable and disclosed — `variables_changed = full_source_reproduction … not_causal_ablation`, hypothesis explicitly disclaims component attribution. Same shape as repro_038.
- **Q2 (validation trust / leakage / 44b6-6bba split):** No local labeled metric is claimed as evidence — quality is decided only by external Public LB, so no train→claim leakage; test is unlabeled so no test leakage. `read_validator` enforces 2×44b6 + 2×6bba; `audit_submission` additionally enforces consecutive-frame, non-dangling, parent-degree ≤1 / daughter-degree ≤2 graph constraints.
- **Q5/Q7 (duplicate / parent justification):** Not a duplicate and not contradicted by history — prior REJECTs were motion-EMA-α tuning; this is an orthogonal public-frontier reproduction. `comparison_note` correctly states the candidate enables edge TTA and omits our motion EMA (the two frontier branches are currently mutually exclusive). repro_038 is the right parent for another exact-copy probe.

## Implementation risks
- **Integrity gate (smoke test) is strong:** `validate_public_0946_copy.py` pins upstream+edited SHA256, reconstructs the edit and byte-compares, asserts edge-TTA on / motion-EMA absent, rejects non-English source, ast-parses every code cell, and rejects saved error outputs.
- **Q4 (effective-config guard is real):** `collect()` re-hashes the snapshot, then gates on the runtime log line `Loaded DeepCenter add-only gate checkpoint: <path>`, path ending `/best.pt`, hash == pinned `8040999a…`, rejecting `checkpoint_last.pt`. Verifies effective state, not prose. Verified in the notebook: env sets `BIOHUB_EDGE_FEATURE_TTA=1`, correct substituted mount paths, and the eight-view flip/inverse-aligned TTA code is present.
- **Q3 (output contract):** collect payload carries `copy_execution_passed`, `submission_audit{datasets,nodes,edges,sha256}`, `actual_deepcenter_path`, `public_lb_reproduction_passed:null` — consistent with repro_038; no missing field.
- **Clarity (non-blocking):** the env block is the *full* 0.946 config (adaptive gap density, safe-div tuning, short-track rescue, ILP division weight 1.2, secondary low-margin link, det thr 0.965…), which differs from the 0.941 line in many parameters. `change.to` frames edge-feature TTA as *the* differentiator — fine for a non-causal repro, but a future reader could mis-attribute an LB gain to TTA alone.
- **Fidelity caveat:** the reyhanksatria support-pack (unversioned) maps to `pilkwang/…-50ep-v1`; if that isn't byte-identical to what upstream used, a score gap reflects substitution, not the pipeline. Inherent to path-only reproduction; recorded, not misattributed, and the pinned DeepCenter SHA fails safe (mismatch → INVALID_METRIC, never a false pass).

## Budget
Expected 2.0 GPU h; ~13.46 h usable above the 6 h reserve; repro_038 actually ran 0.60 h, so 2.0 h is conservative and under the 4.0 h cap (no extra approval). A confirmed 0.946 becomes a new frontier parent (~+0.005 over the current 0.942 candidate) and enables later combination of the edge-TTA and motion-EMA branches. Gain justifies cost.

## Required changes
None are launch-blocking. Recommended before/at launch:
1. **Re-render `STATE.json` / auto-checkpoint** — it still names `exp_046` active and says "do not launch a successor without explicit authorization." repro_048's config carries an explicit `authorization` block (2026-09-08; one execution + one LB submission; no promotion). Reconcile the single source of truth so controller state is coherent.
2. Soften `change.to` (or add a note) that the *full* 0.946 config, not edge-TTA alone, differs from the 0.941 line, to prevent single-variable mis-attribution in EXPERIMENTS.md.
3. At collection, cross-check that pinned DeepCenter SHA `8040999a…` matches the pilkwang checkpoint the 0.941 line used.

## Recommendation
Methodology and implementation are sound; integrity and effective-config guards are strong; budget, authorization, and lineage are in order; not a duplicate. Safe to proceed to smoke testing and the single authorized launch. The three items are documentation/governance hygiene.

VERDICT: PASS
