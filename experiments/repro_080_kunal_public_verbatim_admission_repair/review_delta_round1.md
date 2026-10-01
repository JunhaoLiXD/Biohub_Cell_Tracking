## Delta review

- **F1 — Closed.** The explicit user-approved Tier B exception is narrowly scoped to one byte-verbatim private run and preserves all substantive safety and admission gates.
- **F2 — Not closed.** The checker does not machine-validate two required claims:
  - `validator_enabled_effective` is hard-coded to `True`; no receipt field is checked to prove validation was enabled at runtime.
  - An `experiment_tag` suffix matching the selected label does not prove the final TEST inference actually applied the selected override values. The checker must validate effective runtime overrides from a trustworthy receipt, or an equivalently binding record connecting the selected configuration to TEST execution.

VERDICT: REVISE
