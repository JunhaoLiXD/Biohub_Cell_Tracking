# exp_058 A0 Division Diagnostic — Build Status

Started 2026-09-16, after 2-round Codex CONSENSUS on the design
(`exp058_a0_division_diagnostic_proposal.md` v2.1).

## Foundation laid this session (done)

* **Design at CONSENSUS** — proposal v2.1, two Codex challenge rounds recorded.
* **Config** — `configs/exp_058_a0_division_diagnostic.yaml` (parent repro_048,
  diagnostic gate `exp058_diagnostic_integrity_passed`, require_codex_review, budget
  ≤1.0 GPU hr, GEFF-reuse provenance, expected SHA/score/3-8-9 pinned).
* **Substrate confirmed** — the 20 frozen GEFFs exist in val_049 artifacts (test:
  `.../unet_transformer/split_0`; train16: `.../unet_transformer_val/split_0`),
  total artifacts 53 MB → uploadable as a small Kaggle dataset.
* **Exact instrumentation targets extracted & understood** (in the base notebook
  cell 1):
  - `add_safe_divisions_postlink` (136 lines) — the candidate journey. Its real
    control flow confirms the 14-step order and it is **already side-effect-free**
    (appends only to a `stats` dict), so telemetry can be added without perturbing
    returned edges (shadow-parity-safe by construction).
  - `deepcenter_accept_repair_point` (20 lines) — the DeepCenter veto; **missing
    data returns True (fail-OPEN)** → the `missing_bypass` state Codex required.
  - `filter_output_graph` (129 lines) — postprocessing entry; safe_division runs
    mid-pipeline, followed by single-parent repair / short-track / linefit, so
    accepted safe_division edges must be traced to final-graph membership.

## Substrate decision (made 2026-09-16)

**User chose the FULL RE-RUN path (no GEFF upload).** The notebook runs the val_049
train16 pipeline end-to-end (~1.3 GPU hr; the user expanded the budget from 1.0),
adding only additive telemetry + analysis + integrity block. No Kaggle dataset is
created or uploaded. Config updated: base = val_049 snapshot notebook, budget 1.3,
mirrors val_049's 3 dataset sources.

## Progress (done this session)

* **Config finalized** for the full-rerun path — `configs/exp_058_a0_division_diagnostic.yaml`.
* **Builder skeleton + PARITY GUARD** — `scripts/build_exp058_a0_division_diagnostic.py`:
  locates the functions cell, injects purely-additive tagged telemetry, and asserts
  that stripping every tagged line reproduces the base cell byte-for-byte (aborts
  otherwise). Cell location + all 7 planned injection anchors **verified unique** in
  the real val_049 notebook (cell index 2, 156 KB). Awaiting the companion
  `exp058_instrumentation.py`.

## VERIFIED MILESTONE (2026-09-16): telemetry instrumentation built + parity-proven

* `scripts/exp058_instrumentation.py` + the builder produce the instrumented notebook
  `.private/current/exp058_a0_division_diagnostic.ipynb`.
* **Parity guard PASSED** — 26 tagged telemetry lines injected at exact anchors in
  the functions cell (cell 2); stripping them reproduces the base cell byte-for-byte
  ⇒ provably purely additive (cannot change the graph).
* **All 8 cells parse** (ast) — instrumented cell 2 (160 KB) and the appended
  analysis cell 7 are syntactically valid.
* The 10 injection points cover the full 14-step candidate journey (parent/sister
  gates, mutual-NN, 3 divergence rejects, geometric-ok, DeepCenter veto, symmetry,
  accepted_proposal, added_final) + DeepCenter score capture.

## SCORER-IDENTITY CORRECTION (found during build)

The val_049 run scores with the notebook's **own inline scorer** (cell 5:
`match_nodes_bipartite`, `compute_division_confusion`, `score_sample`,
`aggregate_official`) — **NOT** `division_metrics.evaluate_divisions`. The official
3/8/9 and 0.9310696 come from those inline functions. The analysis cell + integrity
gate must reproduce/extend the inline scorer. Proposal corrected (§3a-note).

## FORMAL CODEX ADMISSION REVIEW: VERDICT BLOCK (2026-09-16)

The formal admission review (`experiments/exp_058_a0_division_diagnostic/review.md`)
correctly BLOCKED the rushed build. Confirmed-valid defects to fix before re-review:

**Governance**
- Proposal is ambiguous: still references GEFF reuse in places; "substantively
  CONSENSUS" vs "confirmation pending"; §3a-note (inline scorer) contradicts §3c
  (`evaluate_divisions`). → Reconcile to the actual full-rerun + inline scorer and
  record an explicit CONSENSUS from a fresh Codex confirmation.

**Implementation (real bugs / gaps)**
- **metrics.json is not a valid controller contract** — missing `schema_version`,
  `runtime_seconds`, `reproducible`, and `specimen_metrics` for 44b6/6bba. Controller
  parsing would fail before the gate. (CRITICAL)
- **Shadow parity not actually implemented** — only a build-time strip check + SHA/
  score. Either implement genuine instrumented-vs-uninstrumented intermediate-graph
  parity, or drop the claim and get consensus for the weaker (build-additive +
  runtime exact-reproduction) integrity design.
- **P2 incomplete** — no telemetry for source one-outgoing-edge eligibility, orphan-
  pool, existing-child ≤10µm, already-linked, `missing_bypass`, global/frame caps,
  target/source conflicts; no downstream tracing; GT table reports "furthest stage"
  not the required "first missing/rejecting condition"; doesn't enforce exactly 12.
- **P3 bugs**: directionality uses `g2p` on a PRED source id (must use `p2g`);
  geometric candidates logged at source time `t` but DeepCenter scores at candidate
  time `t+1` → join keys mismatch; fork relations not scorer-faithful (no matching-
  ambiguity); counterfactuals report per-sample Δadj not whole-panel official Δscore;
  addition tests cover only deepcenter/symmetry rejects.
- **Effective-config guards missing** (safe_div enablement, radii, divergence, NN,
  caps, downstream filters).
- **Snapshot omits `exp058_instrumentation.py`** though the builder/validator import
  it → incomplete/unbuildable provenance (add to `kaggle.extra_files`).
- No hard runtime stop; smoke only AST-parses the analysis cell (needs executable
  synthetic tests that would have caught the p2g/join bugs).

Honest note: the "write it all in one go" analysis cell was rushed and shipped real
bugs; the admission gate did its job. This is a substantial revision, not a polish.

## Remaining build checklist (ordered) — SUPERSEDED by the BLOCK fix-list above

1. **Cell-5 graph-stashing injection** (additive): during the validator loop, stash
   per-stem `(pred_nodes_plain, pred_edges_plain, gt_nodes_plain, gt_edges_plain,
   row)` into `_EXP058_LOG['graphs']` so the appended analysis cell has them.
2. **Full `ANALYSIS_INTEGRITY_CELL`** (replace the current skeleton): using the
   notebook's inline scorer — GT-centric coverage table for all 12 GT divisions;
   scorer-faithful fork relations; one-at-a-time suppression/addition rescoring via
   `score_sample`; shadow parity; reproduce official 3/8/9 + 0.9310696 + test SHA;
   native-int JSON; emit `exp058_diagnostic_integrity_passed` metrics.json.
3. **`scripts/validate_exp058_notebook.py`** (local smoke): deterministic rebuild +
   parity guard + all-cells-parse + native-int serialization regression.
4. **Snapshot smoke + fresh Codex admission review** (require_codex_review), budget
   reservation (~1.3 hr, six protected preserved), then ONE launch. No LB submission.

The runtime **SHA + 0.9310696 + 3/8/9 + exactly-12-GT** integrity gate remains the
decisive non-perturbation proof; local smoke proves only additive-only + deterministic
build (it cannot execute the GPU pipeline).

## v3 REVISION COMPLETE (2026-09-17) — all admission-BLOCK findings addressed

The BLOCK fix-list above is now implemented and reconciled. Status:

**Implementation (`scripts/exp058_instrumentation.py`, rebuilt notebook, validator)**
- **metrics.json is now a valid controller contract** — `schema_version:1`,
  `runtime_seconds`, `reproducible:false`, `specimen_metrics{44b6,6bba}`, gate field.
- **Shadow parity WITHDRAWN, replaced by an honest TWO-LAYER integrity design** —
  (a) build-time purely-additive parity guard (strip telemetry ⇒ base cells byte-for-
  byte) + (b) runtime exact reproduction of test SHA `0319ba6d…`, inline
  `aggregate_official` proxy `0.9310696`, division `3/8/9`, exactly-12-GT, telemetry-
  complete, native-int JSON, within-runtime-budget.
- **P2 completed** — source-level gates, `frame_pools` (orphan/eligibility counts),
  `missing_bypass`, global/frame caps, target/source conflicts, downstream tracing;
  GT table reports the **first-missing** cause and enforces **exactly 12** rows.
- **P3 bugs fixed** — directionality uses `_p2g.get(source_id)` (pred→gt); DeepCenter
  join keys on candidate time `cand_t` (t+1); fork relations scorer-faithful w/ a
  matching-ambiguity flag; counterfactuals report **whole-panel** official
  `d_panel_proxy_score`; addition population = reached ≥`geometric_ok` but not deployed.
- **Effective-config guards** captured into metrics; **`exp058_instrumentation.py`
  added to `kaggle.extra_files`**; **`validate_exp058_notebook.py` adds EXECUTABLE
  checks** for the p2g/join/contract/telemetry-completeness bug classes (not just AST).

**Governance / docs reconciled**
- `docs/research/exp058_a0_division_diagnostic_proposal.md` → **v3**: duplicated/
  truncated v1→v2 changelog repaired and marked HISTORICAL/SUPERSEDED; §3a, §5, §7, §8
  rewritten to the actual **full re-run + inline scorer (`aggregate_official`, NOT
  `evaluate_divisions`)**; §8 no longer claims "substantively at CONSENSUS" — it records
  the admission BLOCK and states admission CONSENSUS is **not yet reached**.
- `configs/exp_058_a0_division_diagnostic.yaml` `validation.warning` rewritten to the
  two-layer integrity + inline scorer (removed shadow-parity + `evaluate_divisions`).
- `STATE.json` `exp058_build` updated to **v3 REVISION COMPLETE**.

**Local smoke: PASS** — deterministic rebuild byte-identical, purely-additive parity on
both instrumented cells, all cells parse, native-int regression, 41 telemetry markers,
executable bug-class checks all green.

**Still remaining (unchanged, needs external/GPU actions):** a FRESH Codex admission
review of the v3 snapshot; on PASS, snapshot smoke + a tracked ~1.3 GPU hr reservation,
then ONE launch (no LB). Nothing is launched by this record.
