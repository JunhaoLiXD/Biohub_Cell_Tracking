## Admission review

Tier B authorization, prediction-neutral scope, source reconstruction, leakage boundary, output contract, one-launch limit, and no-leaderboard rule are adequately specified. The runtime receipt design binds the selected configuration to the final artifact and fails closed on mismatches.

Required changes:

- **R081-TEST-001 — Missing executed test receipts.** The packet describes successful positive and negative tests but provides no immutable command, exit status, or concise output receipt. Moreover, `local.smoke_test` runs only `smoke_repro081.py`; it does not execute `test_repro081_runtime_receipt.py` or the three collection auditors. Record deterministic PASS receipts for source reconstruction, runtime positive/negative tests, sweep audit fixture, and structural-output audit fixture before launch.

- **R081-BUDGET-001 — Reservation is asserted but not evidenced.** The packet says 3.0 GPU hours are reserved and more than six hours remain, while the supplied configuration contains only an expected-hours declaration. Provide the controller/budget receipt showing the reservation, concurrent diag078 reservation, and remaining balance.

- **R081-PARENT-001 — Parent eligibility needs explicit exception binding.** The supplied parent record remains `MANUAL_REVIEW_REQUIRED`, with `REVISE` and smoke `PENDING`, so it is not a verified Tier B parent under the normal rule. The claimed user-approved exception must be recorded in repro081’s immutable experiment record, explicitly authorizing repro081 to supersede the unlaunched parent while preserving its already-resolved admission findings.

No launch is admissible until these evidence gaps are closed. Because this is the initial substantive review after an infrastructure-only failure, one delta-only review may address these IDs.

VERDICT: REVISE
