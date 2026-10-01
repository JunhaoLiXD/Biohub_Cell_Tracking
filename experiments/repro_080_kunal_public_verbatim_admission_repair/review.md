## Findings

- **F1 — Risk tier is understated.** Relative to exp064, this enables held-out-label validation, changes selection margins, expands the sweep by seven candidates, and permits a combined configuration. Because the validation/selection protocol changes and multiple coupled post-processing choices may alter final predictions, the workflow classifies this as Tier C—not ordinary Tier B. Before launch, either:
  - reclassify as Tier C and record the required Claude strategy, independent Codex challenge, and explicit `CONSENSUS`; or
  - provide an explicit user-approved tier exception after documenting this scope.

- **F2 — Runtime gates do not prove the claimed effective validation configuration.** The notebook can fall back to the base submission when TRAIN data is absent, validation produces no stems, or the sweep is unavailable, while the structural output checker still passes. Require collection and machine validation of `ppsweep_selected.json` and associated sweep receipts, including:
  - validator enabled;
  - exactly eight held-out TRAIN stems;
  - exactly four `44b6` and four `6bba` stems;
  - no TEST-stem overlap;
  - complete candidate results;
  - selected label and overrides consistent with the recorded selection rule;
  - final submission generated using those effective overrides, or an explicitly preregistered base-fallback outcome.

The immutable notebook and helper hashes match the manifest, and the targeted smoke check passes. The source-delta audit adequately confines source changes to the declared validator settings, candidates, and empty cell. The structural submission audit is strong, but it cannot substitute for F2. Leakage boundaries otherwise appear sound: TRAIN labels are used only for disclosed post-process selection, TEST labels are not read, and the two domain prefixes are handled separately. The one-launch, three-hour budget and no-leaderboard/no-retry stop rule are proportionate, although information gain is primarily deployment reproducibility because the author’s output has already passed structural inspection.

VERDICT: REVISE
