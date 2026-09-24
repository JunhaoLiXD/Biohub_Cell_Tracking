## Summary

**REVISE: strategy consensus is verified, but the snapshot is incompatible with the next controller stage.**

The Claude-authored v3 proposal and Codex challenges v1–v3 record objections, revisions, and explicit **CONSENSUS**. All seven snapshot hashes match; removing marked injections reproduces the parent code exactly. Review remained read-only; no state-changing tests ran. Initial git checks returned no changes.

## Methodology

The fixed β=0.20 intervention is testable and sufficiently isolated. Earlier downstream edge failures do not directly contradict this upstream intervention, but neither the parent’s 0.947 nor public provenance establishes likely improvement.

The inherited validator selects division-prioritized training videos within both specimen prefixes; it is **not leave-one-specimen-out validation**. Frozen-model training exposure and adaptive PP selection prevent interpreting its scores as independent generalization evidence. Retaining that selection policy is consistent with the agreed experiment, whose quality endpoint is explicitly Public LB.

## Implementation risks

- **Controller configuration fails validation.** `success.regression_threshold` is missing. Moreover, top-level `gate` is ignored by `decide()`: without `evaluation.mode: gate`, evaluation defaults to comparison and fails against the incompatible legacy baseline.
- **Manifest format is incompatible.** The snapshot stores `files` as a path-to-hash mapping; `verify_snapshot()` expects a list of objects containing `path` and `sha256`. Correct hashes do not prevent this failure.
- **Default smoke rejects the notebook.** It requires the final code cell to contain the `metrics.json` contract. That literal appears in the earlier module-definition cell, while the final cell only calls `finalize()`.
- **Telemetry is not reliably tied to the current run.** Statistics append to a fixed file without clearing it or recording run/mode/dataset identity. Malformed records are skipped and activation is overwritten by the last record. Stale or partial evidence can therefore satisfy aggregate execution checks.
- Calibration statistics describe **post-bonus** logits and omit the promised per-dataset distributions and probability/candidate changes. The NumPy shim also differs from PyTorch in precision, tie sorting, and standard deviation; its tests do not establish numerical parity.

The rank formula, signature-key extension, candidate SHA-guard clearing, model hashes, and inherited lineage-degree/time checks are present.

## Budget

The recorded 20.398674 hours supports a 3-hour reservation while preserving six protected hours. Information gain is reasonable for one bounded probe, without automatic escalation.

The config’s “5/day” wording must not override the project’s **three submissions per New York day** limit.

## Required changes

1. Correct config validation fields, explicit gate evaluation, manifest schema, and snapshot smoke integration.
2. Make execution telemetry fresh and attributable to each subprocess; reject incomplete, conflicting, or nonfinite evidence.
3. Restore the agreed activity/calibration contract or explicitly record a narrowed contract.
4. Remove inherited candidate-report claims of already-verified 0.947 quality; distinguish parent provenance from candidate evidence.
5. Preserve prior review history, snapshot the corrections, and obtain a scoped review before smoke, reservation, or launch.

## Recommendation

Retain the agreed strategy, but do not advance this snapshot. These are concrete controller and evidence-contract defects, independent of speculative efficacy.

VERDICT: REVISE
