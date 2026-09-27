# exp_068_ep015_single_probe — strategy proposal v1

Author: Claude Code (strategy author). **STRATEGY: PROPOSED** — not reviewed, not admitted. Nothing built, pushed, launched or submitted. No repo files touched; the text below is for Codex to persist and critique. (A copy sits in the plan file, outside the repo.)

## Context

`GOAL.md` top authorization (2026-09-26) reports 30 GPU h and accepts, within a bounded scope: ONE ep015 run, ONE LB probe after the existing strategy/review/smoke/output gates, plus ONE zero-GPU division scoring-potential diagnostic. It supersedes the closeout's ep015-OFF instruction only inside that scope. exp064 submission 56535761 (0.953) stays the final choice. No second probe, no exp067 training, no broader export, no public push, no final re-selection. Daily LB cap: use the conservative 3-per-New-York-day and check remote history first — the ledger records a later 5/day ruling and the conflict is unresolved, so take the lower number.

---

## Part A — the GPU probe

**Parent (behaviour):** `exp_064_x138_verbatim_repro`, Public LB 0.953, output sha256 `d52a5da2ae5cb0d1b22499f6ca51a00838a6c32ae9a1986ec756ea72e7909e03`.

**Vehicle:** `docs/research/public_notebook_archive/optimized-biohub-max-score.ipynb`, sha256 `371fc1f9f4f20f692e0586616ff7d3eab4621d167f6c78516d3243c5a4fddfab` — the same immutable archive exp_066 cx03 used, whose base pass is byte-verified (exp_065 Gate 1) to reproduce `d52a5da2`.

**Exact change:** one active lever, `BIOHUB_OUTPUT_MIN_EDGE_PROB` `0.0 → 0.15`. `BIOHUB_COUNT_EXCESS_FRAC` stays `0.0`; every other v5 lever stays `0.0`; `BIOHUB_VALIDATOR_ENABLE` `1 → 0`, so no validator, no sweep, no runtime re-selection, no preset auto-attach. The base pass **is** the arm, so the notebook's own output is the submittable artefact.

**Hypothesis (one, falsifiable):** dropping output edges with predicted probability below 0.15 from the x138 final graph raises Public LB strictly above 0.953 at displayed precision, i.e. ≥0.954. Reject at ≤0.952. 0.953 is a **registered null at displayed precision**, not proof of zero delta.

### Evidence, and why it is weak

From `experiments/exp_065_metric_aligned_pruning/collection/ppsweep_results.csv` (amanatar's held-out sweep, n_samples = 8 over 2 movie prefixes):

- base proxy 0.9554890 → ep015 0.9606148; adjusted-edge Jaccard 0.9340604 → 0.9391862.
- `ep010`/`ep015`/`ep020` are **bit-identical on every column**, so 0.15 sits on a plateau, not a knife edge — edge-probability mass is quantised below ~0.2. ep015 also absorbs `cx06` and the whole `prune_pack` (identical rows), so within that family it is the only lever that moves anything.
- Per prefix the gain is not uniform: `6bba` 0.9680814 → 0.9779762 (+0.0099), `44b6` 0.9209579 → 0.9124640 (**−0.0085**). The aggregate is one movie carrying the other.
- My reweighted proxy delta is **+0.00236**, which I regard as **optimistic**; worst per-prefix case is that 0.0085 regression. There is **no reliable transfer forecast** from a 2-movie proxy to the hidden test set; ~0.955 is neither expectation nor upper bound.
- Mechanism is a precision/recall trade against the one-sided count penalty: spurious predicted nodes 180922 → 174790, but `edges_lost_to_detection` 67 → 121 and `edges_recovered` 5560 → 5512. Division TP/FP/FN is unchanged at 3/2/9 — **this lever does not touch divisions.**

### Build — a minimal, isolated wrapper

`scripts/build_exp068_probe.py`, a **new** file. Do not modify `scripts/build_exp066_probe.py` and do not overwrite `experiments/exp_066_probe_*/kaggle_kernel`; those are historical receipts. The new script is that builder with: `ARMS` reduced to the single `ep015` entry; output to `experiments/exp_068_ep015_single_probe/kaggle_kernel/biohub-exp068-ep015.ipynb`; kernel id `lingxd/biohub-exp068-ep015`; `exp_066` labels renamed to `exp_068`. Retained unchanged: the vehicle-sha refusal, the authored-line budget assert (3 removed / 17 added), the `must_hold` untouched-settings gate, the "every other v5 lever is still 0.0" gate, the fail-closed auto-attach asserts (`_V9_AUTO_SET_ENV` empty, `FROZEN_PRESET_OVERRIDES is None`), the arm snapshot, and per-cell compile. Kernel metadata copies exp_064/exp_066 verbatim: 4 dataset sources, pinned docker digest, T4, internet off, private.

`configs/exp_068_ep015_single_probe.yaml` in the `configs/exp_064_x138_verbatim_repro.yaml` format: parent `exp_064_x138_verbatim_repro`; `change.component: output_edge_probability_floor`, from `0.0` to `0.15`; `admission.require_codex_review: true`, `reviewer_provider: codex`; `local.smoke_test` running `scripts/validate_notebook.py` on the built notebook; `gate: ep015_probe_integrity_passed`.

### Config and collection parity checks

1. **Activation** — output sha256 ≠ `d52a5da2…`. If identical the lever did not fire: **VOID, not null**, and no submission follows.
2. **Distinctness** — ≠ every recorded prior submission hash (parent, cx03, exp_062 k1/k2).
3. **Config echo** — kernel log shows `VALIDATOR_ENABLE=0`, `OUTPUT_MIN_EDGE_PROB=0.15`, all other v5 levers `0.0`, both fail-closed asserts passing.
4. **Graph integrity** — unique `(dataset,node_id)`, finite non-negative coordinates, integral ids/times on node rows (−1 sentinels only on edge rows), in-degree ≤1, out-degree ≤2, strictly forward adjacency, dynamic dataset discovery rather than four assumed names.
5. **Degradation** — the five exp_064 silent-degradation signatures absent; V1284 positively executed in candidate mode; DeepCenter checkpoint sha matches.
6. **Direction sanity** — edge count must move in the pruning direction versus the parent; an increase means something other than the lever moved.

The notebook's own `ground_truth_accessed: False` and compliance fields are hardcoded assertions and are **not** evidence.

### Budget and its honest limit

Expected ~0.5 h (a cx03-class pass measured ≈0.26 h; full exp_064 measured 1.727 h, so 0.5 h is a target, not a floor). **Planned reservation 1.0 h** against 30 h reported remaining. Limitation, plainly: the unchanged vehicle keeps its own `BIOHUB_REPAIR_DEADLINE_S=27000`, and Kaggle exposes no CLI cancel. With the validator off no sweep runs, but the repair path is not capped at 1 h. So 1.0 h is **budgeting intent enforced only by an attended watchdog** (5-minute status poll, fires at 0 h 50 m, tolerant of queued/initializing) plus human cancellation in the UI. I prefer that to editing the deadline, which adds authored lines and breaks byte-comparability with the exp_066 build. **No automatic retry** on timeout, error or hidden-rerun failure; any further run needs fresh authorization.

Gate order before launch: CONSENSUS on this record → fresh experiment-specific Codex admission PASS → controller snapshot + smoke PASS → reservation recorded → ONE user-authorized launch → wait for the user's completion notice (**never poll**) → one collection.

### Leaderboard rule

At most **ONE** submission, separately authorized, only if checks 1–6 all pass and a remote history check shows the New-York-day cap permits. Record it in `SUBMISSION_BUDGET.json` with an authenticated `score_source`. 56535761 stays the selected final entry regardless of outcome; **no re-selection** under this authorization. ≥0.954 is a displayed-precision improvement on the public split only and implies nothing certain about the private score.

---

## Part B — zero-GPU division scoring-potential diagnostic

**Question:** under the most favourable *direct-edge* repair we could hope for, how much scorer division credit is even available?

**Gate 0 (STOP):** the unchanged, no-op path over the eight frozen final graphs and labels must reproduce the collected per-movie validator TP/FP/FN **3/2/9** through the existing `scripts/exp067/parent_scorer.py` `compute_division_confusion`. Any mismatch, or any graph-invariant audit failure, stops the diagnostic and is reported as the result. No repair, no silent fix.

**Edit family** over the ≤7 fully matched direct-edge deficits: keep every node and coordinate; insert the true mother→daughter edges for the chosen subset; remove only conflicting edges — the daughter's existing incoming edge (in-degree ≤1) and outgoing continuations in excess of 2 at the mother; leave every unrelated edge untouched; re-audit in-degree ≤1, out-degree ≤2, strictly forward adjacency, no self or duplicate edges after every edit.

**Enumeration:** all subsets of the ≤7 deficits — 2^7 = **128** combinations, hard cap; per-movie equivalents acceptable. Score every combination with the **exact existing scorer**, no reimplementation.

**Report per combination:** TP/FP/FN, adjusted-edge Jaccard, proxy, per-prefix proxies, inserted edges, removed edges, edges lost. Losses get equal prominence: removing a daughter's incoming edge deletes a true edge and can split a component, so a division TP can be *lost* — `44b6_2a2eff9f` is already a scorer TP without the direct edges and is exactly the case at risk.

**Framing:** the attainable counterfactual **under this restricted edit family, using ground truth**. Not a global upper bound, not a deployable score, not a policy. GT is never used in TEST inference or any deployable rule. This is **not** an exp067 training authorization and does not reopen exp067.

### Self-critique: what this edit-family restriction can miss

It is deliberately narrow and can understate real headroom. (1) It touches only the ≤7 *fully matched* deficits, so divisions whose mother or a daughter was never detected are invisible — a detection-side fix cannot appear. (2) `compute_division_confusion` credits a component containing an anchor plus matched descendants of both daughter lineages and **any** fork, so gains may be reachable by edits nowhere near the true mother-daughter pair; restricting to true edges tests the intuitive repair, not the metric-optimal one. (3) It forbids node insertion, coordinate change and re-matching, yet `pred_to_gt` matching gates everything downstream, so a matching-side change could dominate this whole family. (4) Preserved Q1 reports 6/7 raw reachability and 0/7 actionable events from a script that indexes hypotheses by node ID in row-indexed lookups; copying its deficit list inherits that unreliability, so the list must be **re-derived** from the frozen graphs and labels. (5) Interactions outside the 128 subsets (a deficit repair combined with a segment merge) are excluded. A null here means "this repair shape has little to offer", not "divisions are unimprovable".

---

## Risks and rollback

The main research risk is overfitting the public split on 2-movie proxy evidence with a single probe; it is unmitigated, and the `44b6` −0.0085 regression is its concrete shape. Rollback is complete and cheap: the vehicle is immutable, the build lands in a new isolated directory, exp_066 receipts are untouched, and the retained submission does not change.

## Not claimed

No CONSENSUS. No admission PASS. No smoke result. No reviewer role played by me. No transfer forecast.

**STRATEGY: PROPOSED**
