## Summary

**REVISE.** The export is a reasonable, bounded prerequisite for learned temporal association, but its controller contract is incompatible and its implementation differs from the accepted specification.

Explicit **CONSENSUS is verified**: Claude’s `proposal_v1.md`, Codex’s ten binding objections, and Claude’s `revision_acceptance_v2.md` record the agreement. That agreement covers local development, not remote admission.

## Methodology

- Export-only scope is testable; it makes no accuracy claim. The reproduced exp064 parent is appropriate, although its leaderboard score does not establish benefit from the proposed learned model.
- The six-training/two-holdout movie split represents both `44b6` and `6bba`. It tests within-prefix movie transfer, **not cross-domain transfer**. Historical label enrichment and unknown backbone overlap prevent pristine-validation claims.
- Earlier graph-repair failures caution against proxy optimism but do not directly contradict this measured-feature approach.
- “Complete candidate alternatives” overstates the bounded top-k export and conflicts with the consensus’s explicit withdrawal of completeness claims.

## Implementation risks

1. **Controller evaluation will fail.** Snapshot config specifies `evaluation.mode: diagnostic`; `experiment_controller/metrics.py::decide` supports only `gate` and `compare`. The final metrics cell also lacks a Boolean gate result.
2. **Reconsiderable-node semantics differ from consensus.** The agreement requires both embedding roles; the bundled `provenance.reconcile` uses `emb_src_valid | emb_tgt_valid`. Accepting either role expands the reconsiderable set.
3. **Identity integrity does not establish parent parity.** Final checks reconcile exported identities and verify hashes, but do not compare the resulting graph against an uninstrumented parent control. The earlier implementation review explicitly left representative export/parity validation outstanding.
4. **Provenance is incomplete for the preservation claim.** Predictor exports record observed primary/secondary/coordinate-head hashes, but this is not an expected-parent hash assertion. Final metrics omit the agreed backbone-overlap warning and a complete resolved-configuration receipt.

Snapshot config and notebook hashes match their manifest. TEST prediction and sweep execution are explicitly skipped; label export is restricted to selected TRAIN stems.

## Budget

The requested **2 GPU hours** fits the recorded **17.386695 hours** remaining. The 5,400-second watchdog bounds the attempt and kills descendants. Information gain is reasonable after the contract fixes; runtime and memory remain unverified.

No reservation exists yet. Leaderboard submission and promotion remain excluded.

## Required changes

- Use supported `evaluation.mode: gate` and emit an explicit integrity-gate Boolean after all checks.
- Restore the agreed both-role requirement, or record and independently review a precise amendment.
- Describe alternatives as bounded top-k; document that implementation ranks by logits.
- Complete the recorded export/parity prerequisite and bind acceptance to expected parent dependencies, effective configuration, and provenance.
- Regenerate the snapshot after corrections, then obtain fresh admission review, smoke PASS, and budget reservation.

## Recommendation

Do not launch this snapshot. These are correctable implementation and evidence gaps, not missing strategy consensus.

Review was read-only; no tests or state-changing commands were run. Git diff inspection was unavailable because the accessible process reported “not a git repository.”

VERDICT: REVISE
