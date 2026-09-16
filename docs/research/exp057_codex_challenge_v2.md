## exp_057 resolution

1. **Resolved — non-causal framing.** Sections 1–2 correctly describe repro_048 as a complete bundle, acknowledge the lineages differ, lower the additive prior, and frame exp_057 as a high-uncertainty composition probe.

2. **Partially resolved — integration specification.** v2 correctly retracts the `predict_unet_transformer.py` location, but replaces it with another inaccurate description. In the archived [repro_048 notebook](E:/Project/Biohub_CellTracking/experiments/repro_048_public_0946_exact_copy/snapshot/source/public_0946_edge_feature_tta_copy.ipynb), `motion_relink_edges` is notebook-level postprocessing code. `_patch_text` edits `scripts/predict_unet_transformer.py` for TTA/association; it does not inject the motion-relink function into the tracking repository. Section 3.2 also defers the exact function/line specification to future implementation instead of defining it now. The actual EMA port should explicitly name `motion_relink_edges`, `velocity_um`, prediction fallback, velocity update, telemetry, and `BIOHUB_MOTION_RELINK_EMA_ALPHA`.

3. **Partially resolved — integrity contract.** Same-snapshot off/on execution, normalized diff, runtime-source hash, EMA-off equality to verified SHA `0319ba6d…`, graph validity, and execution receipts are present. However, “material/non-trivial” graph change is not a deterministic gate. Predeclare an exact rule, such as at least one canonical edge addition/removal after normalized graph comparison, and define the off-switch semantics that must restore the original one-frame estimator.

4. **Resolved — displayed 0.944 handling.** It is explicitly scientifically inconclusive but operationally terminal, with no alpha sweep.

5. **Resolved — diagnostic and authorization gates.** Train16 is diagnostic-only. The proposal retains a one-submission limit, immediate remote-history and duplicate checks, tracked reservation, protected GPU reserve, explicit user authorization, fresh implementation-specific Codex review, smoke testing, and no promotion.

The notebook SHA `4eda3c3d…` and canonical repro_048 submission SHA `0319ba6d…` are independently confirmed.

## exp_058 §1b

This is an honest withdrawal, not a PASS request. It expressly rejects cancellation of `H` exposure, labels Design B contaminated, requires `H`-unexposed initialization for Design A, removes early stopping on `H`, and discloses the real training-code and four-hour constraints. The statement that its recipe must be frozen “before exp_057” conflicts with exp_057 being immediate; this should eventually say “before observing exp_057’s result” if that is the intended anti-adaptation rule.

## Remaining exp_057 changes

- Correct §3.2 to describe direct notebook-level modification of `motion_relink_edges`, not a tracking-repository text patch.
- Specify the exact EMA state, prediction, update, fallback, telemetry, environment variable, and explicit off-switch behavior.
- Replace “material/non-trivial” graph difference with a numerical canonical-diff admission threshold.

## Recommendation

Revise these narrow contract defects, then repeat the consensus challenge. No implementation, launch, or submission is authorized by this review.

VERDICT: REVISE (correct the motion-relink integration description and exact patch specification; define EMA-off semantics and a numerical canonical graph-difference gate)
