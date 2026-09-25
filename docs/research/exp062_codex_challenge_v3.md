# exp_062 — Codex strategy challenge v3 — CONSENSUS

Reviewer: Codex `gpt-6-astra`, effort low, read-only sandbox. Date: 2026-09-24.
Target: `docs/research/exp062_mutual_best_edge_association_proposal_v3.md`.

**VERDICT: PASS — strategy-level CONSENSUS** for one unchanged mutual-best β = 0.20 probe.
This PASS does **not** authorize launch or leaderboard submission.

---

## Verdict

**Strategy-level CONSENSUS** for one unchanged mutual-best **β = 0.20** probe. The two outstanding design corrections are resolved. The redundancy interpretation needs qualification, but does not block this experiment.

Review was strictly read-only. The referenced round-2 review file is absent from `docs/research`; I used your supplied round-2 findings and checked them against v3 and the parent source.

VERDICT: PASS

## Round-2 findings: fixed or not

- **Cache isolation: fixed at strategy level.** Both variables enter the inference signature, with fresh-state enforcement and executable discrimination tests specified. [v3:298](E:/Project/Biohub_CellTracking/docs/research/exp062_mutual_best_edge_association_proposal_v3.md:298)
- **Calibration account: fixed.** Source-axis reduction gives per-target statistics; ratio clamps are distinguished from scale floors; secondary blending precedes final `raw`. Stage-separated telemetry is specified. [v3:154](E:/Project/Biohub_CellTracking/docs/research/exp062_mutual_best_edge_association_proposal_v3.md:154)
- **Parent-SHA guard: fixed.** Candidate mode actively clears and asserts absence of the variable while retaining current-input integrity checks. [v3:321](E:/Project/Biohub_CellTracking/docs/research/exp062_mutual_best_edge_association_proposal_v3.md:321)

Previously closed findings remain closed.

## Newly introduced defects

**No blocking [CORRECTNESS] defects.**

**[VERIFICATION-DEPTH, nonblocking]** “Largely redundant” remains an efficacy hypothesis. A null tests the **whole weighted intervention**, not the isolated contribution of target competition. It cannot establish that row/mutual information failed or that a row-weighted successor is preferable. Keep §8’s designated density-adaptive successor. [v3:184–193](E:/Project/Biohub_CellTracking/docs/research/exp062_mutual_best_edge_association_proposal_v3.md:184)

## Ruling on the cache-isolation fix

**Yes: append immediately after the list definition and before the first hash computation.**

I traced the [parent notebook](E:/Project/Biohub_CellTracking/experiments/repro_059_public_0947_exact_copy/snapshot/source/biohub-repro059-public-0947-exact-copy.ipynb), **cell 2 source lines**:

- **1669–1672:** extended list → test signature → inference-reuse decision.
- **3171–3172:** base/final-output reuse also requires that test signature.
- **3290, 3686, 3723:** test signature → validator prediction → validator base and PP-sweep signatures.
- **3783:** final signature includes test, postprocessing and sweep signatures.

Two signatures do **not** inherit the keys: standalone postprocessing (**289–296**) and disabled-validator sentinel (**3345**). Neither creates an uncovered candidate-reuse path: output reuse separately checks the test signature, and sweep reuse requires enabled validation.

Implementation details for the already-planned admission review: reject unknown legacy state fail-closed; measure actual elapsed time, because **1675 restores historical `predict_seconds` on a cache hit**.

## Ruling on the col_best redundancy reading

**Correct as a description of reused ranking information; not mathematical redundancy.**

Under the frozen `low_margin_consensus` configuration, blending occurs only when both models share the column winner; otherwise its weight is zero. The convex blend preserves a strict shared winner, and temperature is 1. Thus the final column winner ordinarily matches the previously computed winner. Ties and numerical effects qualify exact identity. Parent cell 2: **996–1004, 1211–1232**.

However, **gating a model blend and explicitly boosting a winner are different transformations**. The column bonus still changes probability concentration and potentially candidate admission. Row competition is the new ranking relation, not new independent evidence.

**Retain β = 0.20 and the published weights.** This finding does not justify redesigning the first probe.
