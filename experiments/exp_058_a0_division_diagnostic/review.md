## Summary

Execution is blocked. The diagnostic is worthwhile and the prediction path appears additively instrumented, but the required strategy consensus is absent and the implemented P2/P3 analysis still does not satisfy the v3 claims.

The v3 strategy explicitly states “NOT yet at admission CONSENSUS” ([proposal](/E:/Project/Biohub_CellTracking/docs/research/exp058_a0_division_diagnostic_proposal.md:294)). Under the project contract, that alone prohibits execution.

## Methodology

- The parent is relevant: repro_048 supplies the authenticated 0.944 submission, while val_049 supplies the exact train16 scorer baseline, 0.9310696298996892 and division 3/8/9.
- The diagnostic is not a strict duplicate of diag_013/019 because it targets the newer lineage and production veto configuration.
- Prediction leakage is controlled: GT is consumed after prediction generation.
- The panel preserves eight videos each from 44b6 and 6bba, with 5 versus 7 GT divisions. However, these are model-seen training videos. Results may describe failure anatomy only; they cannot justify an A2 feature, direction, threshold, or policy without new specimens or a preregistered external test.
- The frozen hypothesis still says “val_049 frozen GEFFs,” while the actual substrate is a full rerun ([config](/E:/Project/Biohub_CellTracking/experiments/exp_058_a0_division_diagnostic/snapshot/config.yaml:6)). This must be reconciled.

## Implementation risks

Positive findings:

- Every snapshot manifest hash matches.
- Removing telemetry-tagged lines reproduces the base val_049 function and validation cells byte-for-byte.
- The final metrics payload now contains the controller-required schema, runtime, reproducibility, specimen metrics, and gate field.

Blocking defects remain:

1. **P2 is not a valid first-missing audit.** It maps GT sources against the final postprocessed graph, so a source removed downstream can be mislabeled as never detected. Existing final forks are labeled `already_pred_fork` before distinguishing native forks from safe-division recoveries. The “first missing” value is inferred by taking the maximum terminal-stage label, and `_STAGE_ORDER` puts conflicts before caps and frame cap before global cap, contrary to execution order ([notebook](/E:/Project/Biohub_CellTracking/experiments/exp_058_a0_division_diagnostic/snapshot/source/exp058_a0_division_diagnostic.ipynb:3811), [coverage logic](/E:/Project/Biohub_CellTracking/experiments/exp_058_a0_division_diagnostic/snapshot/source/exp058_a0_division_diagnostic.ipynb:3891)).

2. **P3 is not scorer-faithful.** The inline scorer credits GT divisions through weakly connected fork components. The diagnostic reports only one-to-one node mapping and whether the mapped GT node divides; it does not reproduce credited component relations, terminal/unmatched categories, or the promised fork attribution. Its ambiguity flag checks whether multiple predicted forks share one `p2g` match, which cannot occur under the one-to-one LSAP mapping and therefore does not measure scorer ambiguity ([notebook](/E:/Project/Biohub_CellTracking/experiments/exp_058_a0_division_diagnostic/snapshot/source/exp058_a0_division_diagnostic.ipynb:3940)).

3. **Promised features are absent from fork records.** Fork rows omit DeepCenter score, distances, divergence, symmetry, confidence, and downstream class. These exist only partially in separate candidate/directionality outputs and are not reconciled into the proposed stratified fork table.

4. **Downstream tracing is incomplete.** It records only final survival, not whether an edge disappeared at geometry filtering, pruning, short-track filtering, or smoothing ([notebook](/E:/Project/Biohub_CellTracking/experiments/exp_058_a0_division_diagnostic/snapshot/source/exp058_a0_division_diagnostic.ipynb:3951)).

5. **Effective configuration is captured but not guarded.** No integrity check compares the captured values with expected values, and downstream filter settings are omitted. Thus stale or changed effective settings can pass this specific guard layer ([notebook](/E:/Project/Biohub_CellTracking/experiments/exp_058_a0_division_diagnostic/snapshot/source/exp058_a0_division_diagnostic.ipynb:4009)).

6. **Telemetry completeness is too weak.** It checks only the first 100 candidate records, does not require meaningful DeepCenter/fork/downstream reconciliation, and uses permissive JSON serialization that accepts non-standard NaN values ([notebook](/E:/Project/Biohub_CellTracking/experiments/exp_058_a0_division_diagnostic/snapshot/source/exp058_a0_division_diagnostic.ipynb:4025)).

7. The snapshotted builder documentation still claims `division_metrics` and runtime shadow parity, both withdrawn by v3. This leaves frozen provenance internally inconsistent.

## Budget

The diagnostic could be worth a corrected single run: division retains substantially more measured headroom than wrong-association repair, and the older diagnostics do not answer the exact-lineage question.

There are 26.493 GPU hours remaining, so a 1.3-hour run preserves the six-hour reserve. However:

- No reservation currently exists.
- The integrity cell accepts up to 1.4 hours although authorization/configuration says approximately 1.3.
- The runtime check is post-hoc, not a hard stop.
- A full val_049 rerun historically costs about 1.17 hours, leaving limited margin for intervention rescoring.

## Required changes

1. Produce a reconciled Claude-authored revision covering the actual full rerun and inline scorer, followed by an explicit recorded `CONSENSUS`.
2. Correct the snapshot hypothesis and stale builder documentation.
3. Build the GT coverage audit from appropriate pre-safe-division and downstream stage snapshots; report the genuine first missing/rejecting condition in actual control-flow order.
4. Implement fork/component relations that reproduce the inline scorer’s credit logic, or narrow the strategy claims to what is actually measured.
5. Join the preregistered candidate/fork features and native/safe-added/disappeared strata into the emitted analysis.
6. Record the exact downstream removal stage.
7. Make expected effective configuration and output reconciliation fail-closed.
8. Strengthen completeness and strict finite-JSON checks, add semantic synthetic tests, then rebuild the snapshot.
9. After a fresh PASS, run snapshot smoke and reserve a budget consistent with the enforced runtime ceiling. No leaderboard submission is authorized.

## Recommendation

Do not advance to controller smoke or remote launch. The missing explicit consensus is independently dispositive, and the remaining P2/P3 defects could produce confident but incorrect conclusions about where divisions fail.

VERDICT: BLOCK
