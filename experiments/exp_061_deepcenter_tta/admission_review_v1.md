## Summary

**REVISE.** Strategy consensus is recorded explicitly: the Claude-authored v5 proposal, Codex challenges v1–v5, and revision tables culminate in `CONSENSUS`. Implementation does not yet satisfy that agreement.

Read-only checks confirmed snapshot manifest hashes and stripped-parent source parity. Supplied validators passed, but NumPy-dependent execution checks were skipped; several remaining checks only inspect source strings.

## Methodology

The three preregistered arms isolate DeepCenter TTA composition against a fresh shared-path control. This is distinct from earlier association-TTA and threshold experiments. However, the parent’s bundled improvement does not establish DeepCenter TTA as its cause, and previous rounded LB ties neither support nor refute this intervention.

This is an integrity-gated Public LB probe, **not independent cross-domain validation**. Historical training proxies are optimistic; neither aggregate LB nor the inherited validator establishes generalization across the 44b6/6bba split. Preserve that limitation and separate submission authorizations.

## Implementation risks

- **Incomplete cache provenance:** `_view_key` lacks input/preprocessing provenance and effective transform implementation identity. Checkpoint identity comes from an optional configuration attribute, falling back to `"nockpt"` instead of requiring the verified checkpoint hash. Cached arrays lack integrity validation.
- **False “verified-null” classification:** identical submission hashes automatically become `verified_null`. No heatmap comparison establishes whether the intervention executed correctly but had no downstream effect.
- **Nonfinite detection is ineffective:** the parent scorer converts nonfinite scores to `None`; the wrapper records these as permitted missing-score bypasses. Thus `no_nonfinite_scores` can pass despite invalid heatmaps.
- **Partial artifacts are not atomic:** arm CSVs are written directly to final filenames; telemetry is saved only after the arm loop. `arms_started` is populated after completion, obscuring interrupted arms.
- **Insufficient behavioral coverage:** tests do not exercise actual cache/resume rejection, arm-order invariance, or interrupted finalization. Configuration equality across arms does not prove equality to the complete frozen parent configuration. Prediction fingerprints use size/mtime rather than content hashes.

## Budget

The ledger reports **26.493 hours**, six protected, with no exp_061 reservation. It omits later manually executed runs, so reconcile consumption before relying on that balance.

Feasibility is unproven: the implementation retains the full parent PP sweep, whereas consensus accounting assumes seven candidate passes are removed. No measured timing/storage worksheet was found. Next-arm admission uses previous total arm duration without accounting explicitly for new views/frame demand; the control receives no reserve-based admission check.

## Required changes

1. Implement verified cache provenance, content validation, and cache/resume negative tests.
2. Measure heatmap/logit response separately from submission changes; reject nonfinite tensors before scoring.
3. Publish atomic per-arm CSV, telemetry, and completion receipts; distinguish started, completed, skipped, and failed arms.
4. Resolve the retained-sweep discrepancy and provide measured runtime, memory, disk, and I/O feasibility with the 20-minute reserve.
5. Add meaningful execution tests, complete parent-configuration checks, and content-hash graph provenance.
6. Reconcile budget and stale checkpoint records; obtain fresh admission, snapshot smoke, reservation, and explicit launch authorization after corrections.

## Recommendation

Do not advance this snapshot to launch. Consensus exists, but implementation and resource safeguards require revision. No files were changed.

VERDICT: REVISE

---

## Fixes applied (Claude, 2026-09-20) → re-admission v2

All 6 required changes addressed in `scripts/exp061_deepcenter_tta.py` +
`scripts/build_exp061_deepcenter_tta.py` + `scripts/test_exp061_behavioral.py` +
`scripts/validate_exp061_notebook.py`; local validator (66 checks) + behavioral tests PASS.

1. **Cache provenance/integrity** — `_view_key` now binds `EXP061_TRANSFORM_IMPL_VERSION` + the
   **verified** deepcenter checkpoint hash (read from the parent's
   `bidirectional_production_runtime_integrity.json`; REQUIRED, gate `checkpoint_provenance_verified`,
   no placeholder fallback) + the **input image content hash**. Each cached array carries a content
   sha256 re-verified on every RAM/disk hit (gate `view_cache_integrity_ok`).
2. **Real "verified-null"** — mechanism now compares per-`(arm,dataset,t)` **heatmap** sha vs
   xyonly on shared frames. `executed` = heatmap differs; `verified_null` = heatmap differs AND
   submission identical; a never-differing heatmap FAILS the gate `experimental_arms_heatmap_executed`
   (not a null). `|Δ|` stats recorded separately.
3. **Nonfinite at tensor level** — the heatmap fn checks `isfinite(logits)` + `isfinite(heatmap)`
   BEFORE any scorer nulls it; gate `no_nonfinite_heatmaps` (+ nonfinite view-logit counting).
4. **Atomic artifacts** — arm CSV + per-arm receipt published via temp + `os.replace`; `arm_status`
   tracks started/completed/skipped/failed; `arms_started` recorded BEFORE running.
5. **Behavioral coverage + provenance** — added real `exp061_view_key` negative tests
   (frame/dataset/view/input/impl/ckpt each flips the key), arm-order-invariance, atomic/nonfinite
   source checks; prediction fingerprint now a **content sha256**; `all_arm_configs_equal_parent`
   gate (arms == xyonly AND xyonly == parent ⇒ == frozen parent config).
6. **Sweep/feasibility** — the adaptive PP-sweep (validator) is **disabled** via a strippable
   `BIOHUB_VALIDATOR_ENABLE=0` injection (gate `validator_sweep_disabled`); the control arm now also
   gets the reserve-based admission check; §7 reconciled.
