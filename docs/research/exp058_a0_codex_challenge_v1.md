# Codex Challenge v1 — exp_058 A0 Division Diagnostic Export

Reviewer: Codex (gpt-5.6-sol), read-only, 2026-09-16.
Target: `docs/research/exp058_a0_division_diagnostic_proposal.md` v1.

## Verdict: REVISE

Codex confirmed the diagnostic is genuinely novel (not redundant with diag_013/019:
those used a different lineage, disabled the production veto, saw mainly retained
candidates, and had pseudo-replication). But v1 had real design errors:

1. **Integrity sufficiency (finding 1 — capture truncated; incorporated
   conservatively).** The final-submission SHA gate alone is weak proof of
   non-perturbation. Add **shadow parity**: run instrumented vs uninstrumented
   postprocessing over the same frozen GEFFs and require byte-identical intermediate
   graphs, not only the final submission.

2. **The candidate-journey gate order in v1 is WRONG.** The real notebook order is:
   (1) source has exactly one outgoing edge; (2) orphan pool = next-frame nodes with
   no incoming edge; (3) existing child at t+1; (4) existing-child distance ≤10µm;
   (5) candidate not already linked from source; (6) parent distance ≤9µm; (7) sister
   distance ≤14µm; (8) candidate == orphan nearest to the existing child; (9) both
   daughters have exactly one valid t+2 successor; (10) divergence increase ≥2.25µm;
   (11) DeepCenter veto @0.25; (12) symmetry ≥0.6; (13) rank by
   `parent_dist + 0.15·sister_dist`; (14) global cap → frame cap → used-target/
   incoming and used-source conflicts. v1 wrongly put "mutual-NN" first and symmetry
   before DeepCenter, and omitted source/orphan construction, the 10µm existing-child
   gate, t+2 successor availability, and conflict rejection. "Mutual nearest" is a
   misnomer — the code picks the orphan nearest the existing child (one-sided).
   Also: **DeepCenter missing data is fail-OPEN** → needs a separate `missing_bypass`
   state. And **accepted safe_division edges must be traced through the later
   division-geometry filter, isolated-node pruning, short-track filter, and linefit
   smoothing** — "accepted" ≠ "final scored fork."

3. **Add a GT-centric coverage table for all 12 GT divisions.** Per-candidate
   records alone cannot explain a never-nominated true site. For each GT division,
   report whether it lacks: a matched predicted source; an eligible one-child source;
   a valid existing child; an orphan-daughter detection; a viable source/orphan pair;
   or which subsequent gate killed it. Without this, "candidate generation drops true
   sites" conflates detection, topology, and safe-division geometry.

4. **Fork accounting must be scorer-faithful.** `score_divisions` (per-GT-subgraph
   match + stage coverage + weak-connectivity + max bipartite matching) and
   `count_matched_pred_divisions` (separate full-graph match) use DIFFERENT matchings;
   official `FP = max(0, matched_pred_divisions − TP)` is an aggregate residual. A
   simple TP/FP/terminal partition is invalid. Report separately: the GT↔pred-fork
   eligibility relation; credited fork under a reproduced max-matching (flag
   ambiguity if multiple maxima); full-match eligible fork; full-match
   annotation-terminal fork; unmatched fork; mapped-to-dividing vs continuing-
   nonterminal. **Only the aggregate is official TP/FP/FN**; require exact
   reproduction of `evaluate_divisions` incl. 3/8/9. Don't call every uncredited
   eligible fork an FP. Also **add the parent v2.1's one-at-a-time official-score
   suppression/addition rescoring** (v1 dropped it).

5. **Feature analysis discipline.** Capture DeepCenter scores for **every geometric
   candidate before the veto** (incl. rejected low-score — the direction under
   investigation). Stratify native forks vs safe_division-added vs
   disappeared-downstream. With ~12 events across 2 specimens, pre-register
   descriptive effect sizes / ranks / specimen-wise results; treat AUCs/chosen
   directions as **exploratory, not framework-selection evidence** (multiple-
   comparison risk).

6. **Budget/substrate — the important one.** A full val_049-style run is ~1.17 GPU
   hr, so **1.0 hr does not cover a full rerun**. But val_049's collected artifacts
   already contain **hashable raw GEFF predictions for all 4 test + 16 val videos**.
   Reuse those frozen GEFFs and rerun **only** the postprocessor + DeepCenter checks
   + GT mapping + scorer. This is the minimal design, enables shadow parity, avoids
   repeating detector/association inference, and should fit the ceiling — but must
   carry a **measured runtime estimate and a hard stop**.

7. **Governance framing.** Post-hoc GT joining is clean w.r.t. prediction
   generation, but using those labels to pick a feature/threshold/A2 design is
   calibration on model-seen data. Record train16 as **exhausted exploratory
   calibration**; any A2 still depends on new labeled specimens or a pre-registered
   one-shot external test.

## Claude disposition

Accept REVISE. Gate parameters independently confirmed against the notebook config
(9/14/10µm, divergence 2.25, veto 0.25, symmetry 0.6); Codex's 14-step order is
consistent with the code and is adopted, with the hard requirement that the
implementation pin the instrumentation to the EXACT notebook control flow verified
at build time (not to this prose). See proposal v2.

## Round 2 (v2) — REVISE, 6/7 CLOSED

Codex confirmed shadow parity (1), GT-centric table (3), scorer-faithful accounting
(4), feature discipline (5), and governance (7) CLOSED, and **independently verified
the frozen-GEFF reuse premise is sound** (test GEFFs under `unet_transformer/split_0`,
16 train16 GEFFs under `unet_transformer_val/split_0`, read before
`filter_output_graph` → pre-postprocessing model outputs; the SHA/score/3-8-9 gates
make any mismatch diagnostic-fatal). Two precision items remained:
(a) §1's P2 summary still said "mutual-NN" and put symmetry before DeepCenter,
contradicting §3; (b) the two scorer roles + exact suppression/addition semantics
needed pinning. **Both fixed in proposal v2.1** (§1 corrected; §3c added). The design
is now substantively at CONSENSUS.
