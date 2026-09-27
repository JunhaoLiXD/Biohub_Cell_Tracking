## Summary

**BLOCK pending explicit consensus on the remote-trial amendment.** The export is a reasonable prerequisite for learned tracking, but does not test accuracy improvement. Snapshot config and notebook hashes match their manifest.

Review was read-only. Git diff was unavailable: the accessible environment reported no Git repository. No runtime tests were executed.

## Methodology

- The hypothesis is testable: export measured features and alternatives while preserving the parent graph.
- Eight fixed TRAIN movies cover both domains, with six training and two held-out movies. This is a within-domain movie holdout, **not cross-domain validation**; `leave_one_movie_out` is a misleading protocol name.
- Historical label enrichment and unknown backbone overlap are correctly disclosed. These exports cannot establish independent generalization.
- Earlier graph-only failures and exp055’s proxy/LB discrepancy weaken expected accuracy gains, but do not contradict this feature-export diagnostic.

## Implementation risks

- Positive findings: checkpoint/support-code hash assertions, both-role embedding eligibility, graph integrity checks, fatal propagation, sweep suppression, and Boolean controller gate.
- Representative parity reuses instrumented raw predictions. It tests postprocessing preservation, **not detector/association equivalence**.
- Cell 7 checks environment assignments before postprocessing globals resolve. Cell 15 records those globals but does not assert them against an expected parent configuration.
- Final metrics omit the observed dependency receipt and package versions promised by the revision; expected checkpoint hashes alone are incomplete provenance.

## Budget

The ledger shows **17.386695 GPU hours**, with no active reservation. A two-hour allocation is affordable; the notebook enforces a 5,400-second watchdog. The revision’s “two GPU hours reserved” statement contradicts the experiment’s `reserved: false`.

Information gain justifies one bounded export attempt after admission issues are resolved. No training, leaderboard submission, or promotion is included.

## Required changes

1. Explicitly record consensus on `admission_revision_v2.md`, including moving real-data parity from a prelaunch prerequisite into the remote acceptance gate. Existing `revision_acceptance_v2.md` expressly limits consensus to local work.
2. Assert effective predictor arguments and resolved postprocessing settings against the frozen parent, allowing only declared export differences.
3. Persist observed dependency hashes and package versions in the final metrics contract.
4. Correct the split name and reservation statement; retain the stated limitations of representative parity.
5. Complete snapshot smoke and controller reservation before launch.

## Recommendation

The Claude proposal, Codex objections, and accepted architectural revisions are recorded with explicit **local CONSENSUS**. The changed remote admission protocol is not explicitly covered. Resolve that ambiguity without weakening provenance, leakage, budget, or promotion gates.

VERDICT: BLOCK
