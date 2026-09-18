# Strategy Proposal — exp_058 A0 Division Diagnostic Export (Parts 2–3)

Record type: versioned experiment proposal (diagnostic, prediction-preserving).
Author: Claude Code. Date: 2026-09-16. Status: **v3 — built, then revised after the
formal Codex ADMISSION review returned BLOCK.** User authorization: the user
authorized ONE GPU diagnostic export for A0 Parts 2–3 and expanded the budget to
~1.3 GPU hr (full re-run, no GEFF upload). GPU spend only; launch still requires
explicit `CONSENSUS` + a fresh Codex admission PASS + snapshot smoke + a tracked
budget reservation.

## Changelog v2 → v3 (formal admission BLOCK → fixes; `experiments/exp_058_.../review.md`)

The rushed v2 build was correctly BLOCKED. v3 fixes, all now reflected in the
implementation (`scripts/exp058_instrumentation.py`) and re-checked by the smoke:

* **Substrate**: full re-run (no GEFF reuse); §4/§5 rewritten accordingly.
* **Integrity redesigned to TWO-LAYER** (§4): build-time additive parity guard +
  runtime exact reproduction (SHA + 0.9310696 + 3/8/9 + exactly-12-GT +
  telemetry-complete + within-runtime-budget). The unimplemented intermediate-graph
  "shadow parity" claim is withdrawn.
* **Scorer identity reconciled** (§3a-note, §3c): the notebook's OWN inline scorer,
  not `division_metrics`. §3c corrected.
* **Real bugs fixed**: directionality now uses `p2g` (pred→gt) on the pred source;
  the DeepCenter join keys on candidate time `cand_t` (score is at t+1).
* **metrics.json is now a valid controller contract**: `schema_version:1`,
  `runtime_seconds`, `reproducible:false`, `specimen_metrics{44b6,6bba}`, gate field.
* **P2 completeness**: added source-level (existing-child, orphan pool via
  `frame_pools`), `missing_bypass`, cap/conflict outcomes, downstream tracing; GT
  table reports the **first-missing** cause and enforces **exactly 12** rows.
* **P3**: counterfactuals report **whole-panel** official `d_panel_proxy_score`;
  addition population defined = reached ≥geometric_ok but not deployed; fork
  relations descriptive-only with a matching-ambiguity flag.
* **Effective-config guards** captured into metrics; **`exp058_instrumentation.py`
  added to the snapshot** (`kaggle.extra_files`); validator adds **executable**
  checks for the p2g/join/contract bug classes (not just AST parse).

## Changelog v1 → v2 (Codex challenge v1: `exp058_a0_codex_challenge_v1.md`)

**HISTORICAL (v2 design), retained only as provenance. Every item below that mentions
frozen-GEFF reuse, "shadow parity," or `evaluate_divisions` was SUPERSEDED by v3 — see
the v2→v3 changelog above, §3a-note (inline scorer), and §4 (two-layer integrity).**

* **Budget/substrate reworked (SUPERSEDED by v3 full re-run)** — the v2 plan reused
  val_049's frozen GEFF predictions and reran only postprocessing + DeepCenter +
  GT-map + scorer (not detector/association), ~1.17 GPU hr. v3 instead does a full
  end-to-end re-run at the user-expanded ~1.3 GPU hr ceiling (§5).
* **Candidate-journey order corrected** to the actual 14-step notebook control flow;
  added the `missing_bypass` (DeepCenter fail-open) state and **downstream tracing**
  of accepted safe_division edges through division-geometry filter / isolated-node
  pruning / short-track filter / linefit smoothing (§3).
* **Shadow parity** added to the integrity gate (instrumented vs uninstrumented
  postprocessing byte-identical on intermediate graphs, not just final submission)
  (§4).
* **Fork accounting made scorer-faithful** — multiple distinct relations, only the
  aggregate is official TP/FP/FN, exact `evaluate_divisions` reproduction incl.
  3/8/9, plus one-at-a-time official-score suppression/addition rescoring (§3a).
* **GT-centric coverage table** for all 12 GT divisions added (§3b).
* **Feature-analysis discipline** — pre-veto scores for all candidates; stratify fork
  types; pre-registered descriptive/exploratory framing, not selection evidence (§6).
* **Governance** — train16 recorded as exhausted exploratory calibration; A2 still
  needs new specimens or a pre-registered one-shot external test (§7).

## 1. Purpose (what question this answers)

A0 Part 1 (zero-GPU, `exp057_A0_edge_upper_bound_results.md`) established, on the
exact 0.944 lineage: edge levers are small or already-failed-to-transfer, node
pruning hurts, and **division holds the only large headroom** (+0.05–0.085 proxy
ceiling) but its failure mode is unproven and unmeasured on the exact lineage.

This diagnostic answers, on the **exact 0.944 pipeline** and against **ground truth**:

* **P2 — candidate generation:** of the ~12 true GT divisions in the 16 train16
  videos, how many are ever *nominated* as a `safe_division` candidate, and for
  those that are, **which gate stage rejects them**? The authoritative gate order is
  the 14-step short-circuit sequence in §3 (source one-outgoing-edge → orphan pool →
  existing child t+1 → existing-child ≤10µm → not-already-linked → parent ≤9µm →
  sister ≤14µm → orphan-nearest-existing-child → t+2 successors → divergence ≥2.25µm
  → **DeepCenter veto@0.25** → **symmetry ≥0.6** → ranking → caps/conflicts). Note:
  it is a **one-sided** nearest test (orphan nearest the existing child), NOT
  "mutual-NN"; DeepCenter precedes symmetry. This tests the (currently unproven)
  "geometry rarely nominates true sites" claim.
* **P3 — scoring / directionality:** enumerate the predicted fork nodes in the
  final graph and characterize them under the scorer-faithful **multi-relation**
  accounting of §3a (the flat TP/FP/terminal partition is invalid; only the
  aggregate is official). Record features (DeepCenter score, parent/sister distance,
  divergence, symmetry, confidences) and test whether **any** feature — including the
  **low-score** direction of the DeepCenter score (possible anti-selection, per
  Codex) — separates credited from uncredited forks, treating direction/AUC as
  exploratory (§6), not selection evidence.

Outcome is phrased as "actionable evidence / no actionable evidence with current
data," never "proven no signal."

## 2. Parent, lineage, and what is FROZEN

* Parent: `repro_048_public_0946_exact_copy` (Public LB 0.944, SHA
  `0319ba6d…`), evaluated on the frozen `val_008`-derived train16 16-video panel —
  identical configuration and scorer donor as `val_049_public_0944_train16`.
* **This is prediction-preserving.** No detector, association, EMA, gap/relink,
  ILP, DeepCenter checkpoint, threshold, cap, or scorer setting changes. The run
  adds **read-only telemetry only**.

## 3. Exact change (scope-locked, additive telemetry)

1. **Candidate journey — pinned to the EXACT notebook control flow** (verified at
   build time, not to this prose). The real short-circuit order is: (1) source has
   exactly one outgoing edge; (2) orphan pool = next-frame nodes with no incoming
   edge; (3) existing child at t+1; (4) existing-child ≤10µm; (5) source not already
   linked to candidate; (6) parent ≤9µm; (7) sister ≤14µm; (8) candidate == orphan
   nearest the existing child (one-sided, NOT reciprocal); (9) both daughters have
   exactly one valid t+2 successor; (10) divergence ≥2.25µm; (11) DeepCenter veto
   @0.25 (**missing DeepCenter data is fail-OPEN → record a distinct `missing_bypass`
   state**); (12) symmetry ≥0.6; (13) rank by `parent_dist + 0.15·sister_dist`; (14)
   global cap → frame cap → used-target/incoming & used-source conflicts. For each
   candidate record: identities, each gate's value + pass/fail, the **first**
   rejecting stage under this exact order, DeepCenter score, geometric features.
2. **Downstream tracing.** Every *accepted* safe_division edge is followed through
   the later division-geometry filter, isolated-node pruning, short-track filter,
   and linefit smoothing, recording where (if anywhere) it is dropped —
   "accepted by safe_division" ≠ "present as a final scored fork."
3. **GT join** (post-hoc, diagnostic labeling only) via the scorer's own
   `extract_divisions` / `DistanceMatching(7µm)`: candidates and final fork nodes
   carry `maps_gt_division` / `maps_gt_predivision` / matched-GT-id (or none).
4. Serialize with **native Python ints/floats** (explicit conversion + regression
   test — the diag_044 failure mode) and strict UTF-8. Preserve **raw** candidate-
   node and fork-node populations; any physical-site dedup is an added analysis view,
   never an input to official counts.
5. Nothing in the prediction path changes.

## 3a. Fork accounting — scorer-faithful (fixes challenge-v1 finding 4)

A flat TP/FP/terminal partition is invalid: `score_divisions` (per-GT-subgraph match
+ stage coverage + weak-connectivity + max bipartite matching) and
`count_matched_pred_divisions` (separate full-graph match; forks whose matched GT
node has ≥1 child) use different matchings, and official
`FP = max(0, matched_pred_divisions − TP)` is an aggregate residual. Report as
**separate relations**: (a) GT↔pred-fork eligibility used by `score_divisions`;
(b) credited fork under a reproduced maximum matching, **flagging ambiguity** if
multiple maxima exist; (c) full-match eligible fork; (d) full-match annotation-
terminal fork; (e) unmatched fork; (f) mapped-to-dividing vs continuing-nonterminal.
**Only the aggregate is official TP/FP/FN**, and the diagnostic must **reproduce the
notebook's inline `aggregate_official` exactly, including aggregate 3/8/9** (see
§3a-note; `evaluate_divisions` is NOT the scorer this run uses). Additionally run the
parent-plan's **one-at-a-time official-score suppression/addition** rescoring (remove
one fork / add one candidate, rerun the official scorer, record ΔTP/FP/FN and
Δscore).

## 3b. GT-centric coverage table (fixes challenge-v1 finding 3)

For **all 12 GT divisions**, a row stating the first thing it lacks, in order:
matched predicted source → eligible one-outgoing-edge source → valid existing child
(≤10µm) → orphan-daughter detection → viable source/orphan pair → and then which of
gates (6)–(14) rejected it. This separates detection failure from upstream topology
from safe_division geometry — without it, "geometry rarely nominates true sites"
would conflate three different causes.

## 3a-note. SCORER IDENTITY CORRECTION (found during build, 2026-09-16)

Building the notebook revealed that the val_049 run does **NOT** score with
`biohub_tracking.division_metrics.evaluate_divisions`. It uses the notebook's **own
inline scorer** in cell 5: `match_nodes_bipartite` (bipartite LSAP node matching @7µm),
`compute_division_confusion` (union-find fork components + lineage/anchor matching),
`score_sample`, `aggregate_official`. **These inline functions produce the official
3/8/9 and 0.9310696** (validator_results.csv). Therefore every §3a/§3c/§4 reference to
"`evaluate_divisions`" is superseded: the analysis cell reproduces and extends the
**notebook's inline scorer** (already in scope), and the integrity gate reproduces
`score_sample`/`aggregate_official`, not `division_metrics`. `division_metrics.py` is a
separate reference implementation not used by this run. (This is exactly the kind of
wrong assumption — shared by the v1/v2 reviews — that building surfaced.)

## 3c. Two scorer roles + intervention semantics (fixes challenge-v2 finding 2)

Two distinct scorer roles are pinned and must not be conflated (all the notebook's
OWN inline scorer per §3a-note; `division_metrics` is NOT used):

* **Parity role** — val_049's inline `aggregate_official` over the 16 stashed per-
  stem rows is used ONLY for the integrity gate (§4): reproduce
  `0.9310696298996892` and aggregate division `3/8/9`. Not used for per-event claims.
* **Official-relation role** — the inline `match_nodes_bipartite` +
  `compute_division_confusion` + `score_sample` (7µm LSAP matching) are the SOLE
  source of GT↔fork relations and every intervention Δ. Fork classification is
  reported as **descriptive** relations with a matching-ambiguity flag; **only the
  aggregate 3/8/9 is official**. The scorer-faithful per-event signal comes from the
  suppression/addition deltas, which call the real `score_sample`/`aggregate_official`.

**Suppression/addition semantics (explicit, as implemented).** Interventions edit the
**final predicted edge list directly and then call the inline scorer** (`score_sample`
on the edited stem, then `aggregate_official` over all 16) — they do NOT re-enter
downstream postprocessing (which would cascade and confound single-event attribution).
Suppression = remove one surviving safe_division-added edge (only if it survived to the
final graph). Addition population = candidates that reached ≥`geometric_ok` but were NOT
deployed (added_final); add the `(source,candidate)` edge. Each edit is applied to a
fresh copy, one at a time, and the reported Δ is the **whole-panel official proxy-score
delta** (`d_panel_proxy_score`) plus ΔTP/FP/FN against the unedited 16-video baseline.

## 4. Fail-closed integrity gate (proves telemetry did not perturb) — TWO-LAYER

The over-promised "byte-identical intermediate-graph shadow parity" is **withdrawn**
(it was never implemented). Non-perturbation is instead proven by two layers, which
together are decisive:

* **(a) Build-time purely-additive parity guard** — stripping every
  `__EXP058_TELEMETRY__`-tagged line from each instrumented cell reproduces the base
  val_049 cell **byte-for-byte** (enforced by the builder + re-checked by the smoke).
  Telemetry only appends to a separate `_EXP058_LOG`; it cannot mutate graph state.
* **(b) Runtime exact reproduction** — `exp058_diagnostic_integrity_passed` requires
  ALL of: test `submission.csv` SHA256 == `0319ba6d…`; inline `aggregate_official`
  over the 16 stems reproduces proxy `0.9310696298996892` and division **3/8/9**
  exactly; all 16 stems present; **exactly 12 GT divisions**; telemetry complete +
  native-int JSON; and `within_runtime_budget` (runtime ≤ 1.4 h — a soft hard-stop
  flag; the Kaggle kernel time limit + controller reservation are the hard bounds).

If any check fails the run is REMOTE_FAILED (diagnostic void), not interpreted. The
controller gate is integrity-only; there is no quality decision (no LB).

## 5. Validation, budget, artifacts

* Protocol: `public_0944_train16_division_diagnostic_v1`, same 16 videos / frozen
  scorer as val_049.
* **Substrate = FULL RE-RUN (user decision 2026-09-16, no GEFF upload).** The
  notebook is val_049's train16 pipeline run end-to-end (detector + association +
  postprocessing + inline scorer), with only additive telemetry + the appended
  analysis/integrity cell. `runtime_seconds` is measured and emitted; the integrity
  gate flags any overrun of the 1.4 h ceiling.
* Budget: a full val_049-style end-to-end rerun is ~1.17–1.3 GPU hr; the user
  **expanded the authorization to ~1.3 GPU hr**. Reserve ~1.3 GPU hr; the integrity
  gate emits measured `runtime_seconds` and flags any overrun of the 1.4 h ceiling
  (the Kaggle kernel time limit + the controller reservation are the hard bounds).
  DeepCenter veto uses CUDA, so this is low-GPU, not zero-GPU. Six protected hours +
  ≥10% weekly allowance preserved. No LB submission (diagnostic).
* Artifacts (tracked under the experiment record + `docs/research/`): per-video
  candidate JSONL, the GT-centric coverage table, the scorer-faithful fork relations,
  suppression/addition rescoring, integrity metrics.json, written analysis. The test
  `submission.csv` SHA256 (== `0319ba6d…`) is the frozen non-perturbation anchor.

## 6. Expected signal / decision rule (pre-registered)

* If **candidate generation** already drops most true sites (few GT divisions ever
  nominated) → the lever is *upstream* (candidate geometry / a learned proposal);
  a gate re-scoring cannot help; A2 would be a detector/proposal change (big,
  high-risk) — likely gated on new labeled specimens (A1).
* If true sites **are** nominated but killed by a specific gate (e.g. DeepCenter
  veto or a cap), and a feature (incl. low-score direction) separates them →
  a bounded, pre-registered gate/scoring A2 has a real basis (still transfer-risky).
* If neither → "no actionable evidence with current data"; B stands; A closes.

**Feature-analysis discipline (pre-registered).** Capture DeepCenter scores for
**every geometric candidate before the veto** (incl. rejected low-score — the
direction under investigation). **Stratify** native forks vs safe_division-added vs
disappeared-downstream (orphan-daughter features are undefined for native forks).
With ~12 events on 2 specimens, report **descriptive effect sizes, ranks, and
specimen-wise** results and pre-register them; any AUC / chosen direction is
**exploratory, not framework-selection evidence** (multiple-comparison risk).

## 7. Risks, governance, and honest limits

* **Telemetry perturbs prediction** → §4 two-layer gate (build-time purely-additive
  parity guard + runtime exact reproduction of SHA / 0.9310696 / 3-8-9), fail-closed;
  telemetry via a side channel (`_EXP058_LOG`) that cannot mutate graph state.
* **NumPy-int JSON crash** (diag_044) → explicit native-int conversion + regression
  test in smoke.
* **Fork mis-accounting** → §3a/§3c scorer-faithful relations via the notebook's
  inline scorer; only the aggregate is official; exact `aggregate_official`
  reproduction incl. 3/8/9; raw populations preserved (dedup is a view only).
* **Runtime over-ceiling** → §5 measured `runtime_seconds` + 1.4 h ceiling flag; the
  Kaggle kernel limit + controller reservation are the hard bounds.
* **Governance / leakage:** post-hoc GT joining is clean w.r.t. prediction
  generation, but using these labels to pick a feature/threshold/A2 design is
  **calibration on model-seen data**. Record train16 as **exhausted exploratory
  calibration**; any A2 remains dependent on new labeled specimens or a
  pre-registered one-shot external test. All conclusions are feasibility/anatomy
  only; they do not authorize a launch or LB submission.
* **Controller/portability failure is not an algorithmic result** → preserve the
  receipt, isolate the smallest fix, re-review.

## 8. Review status

* **Codex challenge v1 → REVISE** (`exp058_a0_codex_challenge_v1.md`), 7 findings.
* **Codex challenge v2 → REVISE**, 6 of 7 CLOSED; the design reached CONSENSUS on the
  full-rerun substrate and the inline-scorer identity (§3a-note pins the notebook's
  own `match_nodes_bipartite`/`compute_division_confusion`/`score_sample`/
  `aggregate_official` as the sole official scorer; `division_metrics.evaluate_divisions`
  is NOT used by this run).
* **Formal Codex ADMISSION review (2026-09-16) → BLOCK**
  (`experiments/exp_058_a0_division_diagnostic/review.md`). The rushed v2 build shipped
  real analysis bugs (`p2g` direction, `cand_t`/DeepCenter join), an invalid metrics
  contract, an unimplemented "shadow parity" claim, incomplete P2/P3 telemetry, and a
  snapshot missing `exp058_instrumentation.py`.
* **v3 (this record) fixes all admission findings** — see the v2→v3 changelog and
  §§3a-note/3c/4/5/7. The implementation (`scripts/exp058_instrumentation.py`) is in
  place and the local smoke (`scripts/validate_exp058_notebook.py`) **PASSES** with
  executable checks for the exact bug classes the admission caught (p2g/join/contract/
  telemetry-completeness).
* **Status: NOT yet at admission CONSENSUS.** Next: a fresh Codex admission review of
  the v3 snapshot; on PASS, snapshot smoke + a tracked ~1.3 GPU hr budget reservation,
  then ONE launch. No LB submission (diagnostic). Nothing is launched by this record.
