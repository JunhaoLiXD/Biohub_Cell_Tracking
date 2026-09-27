# exp_067 — revision acceptance v2 and CONSENSUS record

**Status: CONSENSUS (Claude Code + Codex binding amendment v1).**

Scope of this consensus: local architecture, local implementation, local validation of exp_067.
It is **not** experiment admission, **not** a snapshot, **not** READY, and it authorizes **no** remote
GPU run, **no** leaderboard submission and **no** push. Remote GPU committed remains **zero**.

- Reviewed proposal: `proposal_v1.md` (verdict REVISE).
- Binding amendment: `codex_challenge_v1.md` items 1–10.
- Accepted specification: `proposal_v1.md` **as amended by every item below**. Where this document
  and `proposal_v1.md` conflict, **this document wins**.

I accept all ten items. Four of them overturn design decisions I had made, and two of them are
factual corrections to claims I wrote. Per the project's standing rule I verified each factual claim
against the sources before accepting it; §11 records what I checked and what I found.

---

## 1. Learned symmetric division head — accepted, option 1 preserved

Implemented, not replaced. `scripts/exp067/model.py` ships `JointLineageScorer` with **two trained
heads**:

- `link_head` → a calibrated log-odds `s_e` that edge `(u,v)` is a true GT link;
- `division_head` → a calibrated log-odds `g_h` that `{a,b}` is a true sister pair from mother `u`,
  **given** both links.

Symmetry is structural, not learned: the head consumes `h_u`, `h_a + h_b`, `|h_a − h_b|` and
symmetric geometry only, so `g(u,{a,b}) ≡ g(u,{b,a})` bitwise. Tested in
`tests/test_exp067_invariants.py::test_division_head_permutation_invariant`.

My v1 §6.3 proposal to replace the head with a geometry formula plus two scalars, and the N2/N3
fallbacks of v1 §15, are **withdrawn**. `division_head=None` is no longer a shipped configuration.

Division supervision masking (`supervise.py::division_label`):

| case | label |
|---|---|
| `m(u), m(a), m(b)` all exist, `m(a) ≠ m(b)`, and GT contains both `m(u)→m(a)` and `m(u)→m(b)` | **POSITIVE** |
| all three matched, `m(u)` has ≥ 1 GT out-edge, and the GT children of `m(u)` are **not** `{m(a), m(b)}` | **NEGATIVE** (annotation establishes an incompatible triple) |
| anything else — any endpoint unmatched, or `m(u)` has no GT out-edge | **UNKNOWN**, excluded |

`insufficient_supervision` is an **explicit error**, not a warning: `train.py` raises
`Exp067InsufficientSupervision` when a fold has fewer than `min_division_positives` (default 3) or
`min_link_positives` (default 200) unmasked positives. No quality is promised anywhere.

**The 8 validator movies are not a ceiling and I am no longer treating them as one.** My v1 §5.1
capacity argument was computed from the 8 stems the notebook's own selector happens to pick, which is
an artifact of `BIOHUB_VALIDATOR_N_PER_TYPE=4` and a lexicographic sort, not a data limit. The label
exporter now takes an **explicit stem list** (`BIOHUB_EXP067_LABEL_STEMS`, comma-separated) over the
whole TRAIN directory, and the split manifest declares a **disjoint held-out** stem list. Reported
event counts stay in the metrics as a risk, not as a bound.

## 2. Injection after final filtering and smoothing — accepted, my stage-S choice withdrawn

My v1 §2.3 placed the stage before `OUTPUT_PRUNE_ISOLATED`, arguing the parent's later stages were
useful safety nets. Codex is right that this contradicts "fixed candidate universe": prune-isolated
and `filter_short_track_components` **delete nodes**, and `linefit_smooth_output_graph` **moves
coordinates**, so a stage-S decision is taken against a node set and a geometry that are not the ones
being scored, and labels built at stage S would not match the decoded graph.

The stage now runs at the **very end of `filter_output_graph`**, after
`linefit_smooth_output_graph`, immediately before `return nodes_by_id, edges, stats`. Nothing
filters, prunes or smooths after it. The decoded graph is the emitted graph.

Consequences accepted and implemented:

- **Node set and coordinates are exactly `exp_064`'s final ones.** The stage may not add, delete or
  move a node. `audit.py::assert_node_set_preserved` enforces it on every call.
- **Provenance, not guessing.** `build_graph`'s own `bulk_add_nodes` return is captured by
  `hook_graph_node_ids` and exported as `det_row → graph_node_id`. Final-node classification comes
  from the node dicts' own `readmitted` / `gap_synthetic` flags (cell 5:1291-1292, 948, 1451), never
  from coordinate nearest-neighbour matching and never from the id alone. A final node flagged as a
  detector node but absent from the captured map is a **hard error**, reported with its id.
- **Reconsiderable set R** = final nodes with `origin == detector`, a valid `det_row`, and both
  embedding roles resolvable. Everything else — readmitted peaks without measured embeddings and all
  `gap_synthetic` interpolated midpoints — is held **fixed**: its incident parent edges are constants
  in the program and consume in/out-degree capacity in every constraint. Stated as a limitation in
  `§10 Known limits`, not implied.
- **Labels are built on the final graph.** `hook_labels` matches GT against the *final* node
  coordinates via the notebook's own `match_nodes_bipartite`, so the label coordinates are the
  coordinates being decoded.

## 3. The 0.48 pool is not sufficient coverage — accepted, "complete" withdrawn

My v1 §F1 called `admitted` "the complete above-threshold candidate pool" and then leaned on it as
the alternative pool. The first half is accurate; using it as the alternative source is not, because
a true link whose softmax-over-sources probability is below 0.48 is invisible — exactly the
fragmented-edge population the experiment targets. **I withdraw the word "complete" everywhere.**

The exporter now captures alternatives from the **full pre-threshold, pre-cap probability matrix**,
inside the pair loop, before `candidates = sorted(...)`:

- top-`k` targets per source (row-wise) **and** top-`k` sources per target (column-wise), `k = 4`
  (`BIOHUB_EXP067_TOPK`), unioned and deduplicated, with an `origin` bitmask recording which rule
  produced each entry;
- both `alt_prob` (the parent's `softmax(raw, dim=0)`, i.e. normalised over **sources**) and
  `alt_logit` (the post-fusion raw logit, direction-neutral) are exported, because a row-wise top-k
  over a source-normalised distribution is not itself a distribution over targets. Stating the
  asymmetry rather than papering over it;
- **every parent edge of the graph being decoded is unioned in at inference**, whether or not it
  survived any threshold or top-k rule;
- **geometric alternatives** (nearest R-nodes within `OUTPUT_EDGE_MAX_UM` in the next frame) are added
  with `prob_available = False`; the model receives an availability flag and a masked-out value, never
  a fabricated probability.

An empty learned pool is a **valid** state: single-frame movies, movies with one frame pair and no
alternatives, and missing-alternative transitions all take a **reasoned bypass** that returns the
parent graph with a receipt reason. No crash. Tested in
`tests/test_exp067_degenerate.py`.

## 4. Window builder must guarantee the endpoints it scores — accepted

My v1 §5.2 built tokens from the block's nodes plus the nearest 24 per frame, which does not
guarantee that a scored edge's far target or a division's second daughter is present. Corrected:

1. **Required set first.** For a source batch, the required tokens are every source in the batch,
   every candidate target of those sources, and both daughters of every candidate event. Assembled
   before anything optional.
2. **Deterministic batch splitting.** Sources are taken in `(t, node_id)` order and added while the
   required-token count stays ≤ `required_cap`. A source whose own required set exceeds
   `required_cap` raises `Exp067WindowOverflow` — an event that cannot fit **fails**, it is not
   silently dropped.
3. **Optional context last.** Remaining capacity up to `total_cap` is filled with the nearest R-nodes
   in frames `[t−3, t+3]` by µm distance to the batch centroid, ties broken by `(t, node_id)`.
4. Seven-frame, source-owned scoring. Each candidate edge is scored exactly once, in the batch owning
   its source; `hypotheses.py` asserts that ownership is a partition. No full-movie attention.

Tested for dense frames, an adversarially distant but required candidate, and both border frames
(`t = 0`, `t = T−1`) in `tests/test_exp067_windows.py`.

## 5. Decomposition by transition, using the real factor graph — accepted; this was a real defect

My v1 §7.5 made variables adjacent "when they share a node". That is wrong and Codex's consequence is
correct: node `v` appears in the in-degree constraint of transition `t−1→t` and the out-degree
constraint of `t→t+1`, so sharing a node identity would chain every transition into one movie-wide
component, blow through `MAX_COMPONENT_VARS`, and force a movie-wide fallback on every movie. The
design would have been inert.

The real factor graph: with a fixed node set and adjacency-only edges, **every** constraint (in-degree
at the target frame, out-degree / division coupling / fork gating at the source frame) is confined to
a single transition. The program therefore decomposes **exactly** by transition, and within a
transition into connected components of the bipartite competitor graph. `decode.py` builds the
components from the **actual constraint incidence** — two variables are adjacent only when they
appear together in some constraint row — so the decomposition is derived from the program, not
asserted. Tested in `tests/test_exp067_decompose.py::test_transitions_do_not_couple`.

Also implemented per item 5:

- within a transition, a component carries **all** competitors, all hyperedges and the capacity
  consumed by fixed edges at its boundary;
- **every parent fork is representable**: for each parent source with two outgoing edges an event is
  synthesised into `D` even when geometry or top-k would exclude it, so the parent assignment is
  always feasible. Without this the solver could be unable to return the parent and the fallback would
  be the only option;
- fixed endpoints coexist with reconsiderable edges — a fixed edge consumes capacity but does not
  freeze the other competitors at its endpoints. `tests/test_exp067_decompose.py::
  test_fixed_edge_does_not_freeze_competitors` pins this;
- every incumbent is validated and every fallback is applied **atomically per component** with a
  receipt row;
- the deadline covers **model scoring plus solving**, checked in one budget
  (`Exp067Deadline`), not solver time alone;
- **`scipy.optimize.milp` only.** My v1 §7.5 custom branch-and-bound is deleted; there is no
  production fallback solver.

## 6. Coherent event objective, no held-out tuning, no parity-by-limit claim — accepted

Objective, maximised per component:

```
Σ_{e ∈ H} (s_e − τ0 + β0 · 1[e is a parent edge]) · x_e   +   Σ_{h ∈ D} (g_h − μ0) · d_h
```

- `s_e` is the **learned** link log-odds; `g_h` is the **learned** symmetric sister-pair log-odds.
- `τ0`, `μ0`, `β0` are **fixed declared constants** in `configs/exp_067_temporal_joint_lineage.yaml`,
  defaults `0.0, 0.0, 0.0`. `τ0 = 0` is the link head's own decision boundary and is the single
  declared continuity / birth-death baseline: a node with no selected incoming edge pays nothing, so
  `τ0` is the log-odds an incoming edge must beat. **No grid search over `τ0` / `β0` / `μ0` on
  held-out data**, and my v1 §6.3/§7.2 "selected on held-out movies" wording is withdrawn.
- My v1 §7.2 claim that **`β → ∞` gives exact parity is withdrawn as unsound**: an incumbency bonus
  on parent edges makes parent edges maximally attractive but does not forbid *additional* edges at
  free capacity, so it cannot reproduce the parent graph. The only exact-parity mechanism is the
  bypass, which is exact by construction (the stage is not called). `tests/test_exp067_bypass.py`
  tests the bypass, and the `β → ∞` test of v1 §12.5 is deleted rather than weakened.
- **Zero-new-evidence control** with a precisely defined selection rule, implemented as
  `mode = "parent"`: the stage returns the parent node dict and edge list unchanged, by identity, and
  records `exp067_active = false`. This is the control arm; it is not the bypass.
- **No double counting.** Semantics are declared: a selected edge contributes its own link evidence
  exactly once, whether or not it belongs to a division; `g_h` is the **increment** for the pair being
  sisters *given* both links. The division head is trained **only** against `division_label` and never
  against link labels, and the link head is trained **only** against `link_label`. Both heads share
  the encoder, which is stated, and the two losses are summed with fixed declared weights.

## 7. No held-out selection reported as untouched; provenance stated as unknown — accepted

- **Fixed training schedule.** `train.py` runs a declared number of epochs with a declared LR
  schedule. There is **no** early stopping, **no** checkpoint selection, **no** calibration and
  **no** hyperparameter search against the held-out manifest. The held-out set is scored **once**,
  after training ends. Any future tuning must use an inner split of the TRAIN stems only; the CLI
  exposes `--inner-val-frac` for that and it draws from training stems exclusively.
- **Normalisation** statistics come from the training stems only, are stored in the checkpoint, and
  are never recomputed at inference. `infer.py` contains no statistics computation; asserted by source
  inspection in `tests/test_exp067_supervision.py`.
- **Groups are movie-level and disjoint**, validated by `supervise.py::load_splits`, which raises on
  a stem in both lists, a stem in neither, a TEST stem anywhere, or a prefix missing from training.
  Prefix-held-out is offered as an **optional** protocol and the validator does **not** require every
  prefix in train when that protocol is selected — the two rules are mutually exclusive by flag, so
  they cannot conflict.
- **Backbone provenance is `UNKNOWN / POSSIBLE_OVERLAP`.** My v1 §9.3 asserted the frozen backbone and
  the V1284 head "were trained on the competition TRAIN split, which includes all 8 validator stems".
  I could not substantiate that for either the third-party Pilkwang checkpoints or the V1284 head from
  anything in this repository. The claim is withdrawn and replaced by the literal string
  `POSSIBLE_OVERLAP_UNKNOWN_PROVENANCE` emitted in every metrics file, with the standing conclusion
  unchanged: this is **not** independent external validation, and the Public LB remains the only
  genuinely held-out signal.
- **Inference cannot access labels.** Structural (separate module, separate flag, separate directory)
  and tested by monkeypatching the label reader to raise while inference succeeds.
- **The parent scorer keeps its own partial-label semantics.** `parent_scorer.py` is verbatim cell 8,
  verified **byte-for-byte after AST extraction** by
  `tests/test_exp067_scorer_parity.py`. The stricter training mask lives only in `supervise.py` and is
  never substituted into the aggregate.

## 8. Factual overclaims — corrected, each checked first

| v1 claim | verdict after checking | correction |
|---|---|---|
| post-process safe division "cannot merge fragmented components" (v1 §F5) | **Codex is right.** cell 5:1509 excludes targets with an *incoming* edge, but a target with no incoming edge may still have outgoing edges, i.e. be the root of its own component. Linking to it merges components. | Corrected to: safe division **can** join components at a **free start**; what it cannot do is **reclaim an occupied target**. That narrower gap is the whole justification for exp_067. |
| "219 of the 220 FPs are edges **from** a matched node with GT structure **to** an unlabelled node" (v1 §F6) | **Codex is right.** cell 8:60-62 is a disjunction: `mt` matched with a GT parent **or** `ms` matched with GT children. The unlabelled endpoint can be the **source**. | Corrected to: 219 of 220 FPs have **at least one unmatched endpoint**, direction unresolved from the aggregate. The qualitative point — the FP mass is not both-matched mis-pairing, so deletion alone cannot fix it — survives. |
| the +0.0209 … +0.0410 "oracle relink ceiling" (v1 §F6) | **Codex is right that it is not a realisable additive bound.** It assumes every fragmented edge is fixable, that fixing one removes an FP, and that node counts are unchanged, and it ignores that the fixes interact through the degree constraints. | Retained **only** as a qualitative statement that the fragmented-edge population is large relative to the pruning family. Deleted as a number from all forward-looking text; it must not be quoted as a bound. |
| `exp_055` scored +0.0148537 "on this exact local proxy" (v1 §14.2) | **Codex is right.** exp_055 ran against the ~0.942-era parent under an earlier validation setting, not the 8-movie `exp_065` proxy on the x138 parent. | Corrected to a qualitative caution: a joint cut-and-reconnect repair once produced a clear local-proxy gain and a 0.000 Public LB delta, on a different parent and a different proxy. The caution stands; the comparability does not. |

## 9. Isolated environment — accepted

`.private/runtime/exp067_cpu/Scripts/python.exe`, verified in this session:
Python 3.12.14, **torch 2.14.0+cpu, scipy 1.18.1, numpy 2.5.3**, pytest 9.1.1,
`scipy.optimize.milp` importable.

- All tests run under that interpreter. `.venv` is **not** modified and `.venv` is not used.
- **No skipped smoke test**: the CPU train → save → load → infer → decode cycle runs for real.
- The **numpy duplicate forward** of v1 §5.4 is **deleted** — it existed only to work around the
  absent torch and is now dead weight and a second source of truth.
- The **custom fallback solver** of v1 §7.5 is **deleted**.
- `requirements-exp067-cpu.txt` pins the four packages; `scripts/exp067/runtime.py::
  assert_environment()` asserts the torch/scipy/numpy major-minor versions at import of the training
  and decode entry points and raises with the observed versions on mismatch.

## 10. Real runnable end-to-end paths — accepted

| stage | entry point | status |
|---|---|---|
| builder | `scripts/build_exp067_notebook.py` | **locally tested.** SHA-pinned to the `exp_064` snapshot notebook; fail-closed anchor counts; strip-parity back to the parent byte-for-byte |
| feature / alternative / final-graph / label export | `scripts/exp067/export_hooks.py` | **hook functions locally tested on realistic arrays**; the Kaggle artifact itself is **unverified** — no run has happened |
| supervised cache | `python -m scripts.exp067.supervise` | locally tested on fixtures |
| train | `python -m scripts.exp067.train` | locally tested, real torch CPU |
| inference / decode | `python -m scripts.exp067.infer` | locally tested, real scipy MILP |
| evaluation | `python -m scripts.exp067.evaluate` | locally tested against verbatim cell-8 scorer |

- **Disabled inference is an exact parent passthrough** (`BIOHUB_EXP067_ENABLE=0` ⇒ the stage is not
  called at all).
- **Export flags are independent** of the decode flag: `BIOHUB_EXP067_EXPORT`,
  `BIOHUB_EXP067_LABELS`, `BIOHUB_EXP067_ENABLE` are three separate switches.
- **Export failure propagates.** This needed care, because `write_test_submission` wraps
  `filter_output_graph` in `try/except` and falls back to `fallback_output_graph` (cell 5:2120-2132),
  which would silently swallow an exp_067 failure and emit a parent-ish graph with every gate green.
  The injected code therefore records `runtime.FATAL` and a **second** injected check immediately
  after that `try/except` block re-raises, outside the parent's handler. Tested in
  `tests/test_exp067_builder.py::test_fatal_propagation_anchor` and
  `tests/test_exp067_bypass.py::test_fatal_flag_raises_outside_parent_handler`.
- **Integration tests replay the actual patch chain** — the exporter and decode anchors are located in
  `predict_unet_transformer.py` and notebook cell 5 **after** replaying cell 4's real patch sequence —
  and then **execute the real hook functions on realistic arrays**. They are not string-presence
  tests.
- **"Locally tested" vs "real Kaggle artifact unverified"** is stated per row above and repeated in
  `dev_log.md`.

---

## 11. What I verified before accepting

Checked directly against sources rather than taken on the reviewer's word:

1. cell 5:1509 `candidate_ids` excludes only nodes with an **incoming** edge → item 8 claim 1 holds.
2. cell 8:60-62 `is_fp` is a disjunction over either endpoint → item 8 claim 2 holds.
3. `filter_output_graph`'s tail order — `filter_short_track_components` (cell 5:2058) deletes nodes,
   `linefit_smooth_output_graph` (cell 5:2061) moves coordinates, both **after** my v1 stage-S point →
   item 2 is a genuine defect in v1.
4. Constraint incidence really is per-transition: in-degree at `v` involves only edges from frame
   `t(v)−1`; out-degree / division coupling at `u` only edges to `t(u)+1` → item 5's decomposition is
   correct and v1's node-sharing rule was a genuine defect.
5. `write_test_submission` cell 5:2120-2132 `try/except` would swallow a raising stage → item 10's
   propagation requirement is real.
6. The isolated interpreter has the stated versions.

Nothing in the amendment was found to be wrong, and no item is impossible. **CONSENSUS recorded.**
Implementation proceeds in the same call, bounded to exp_067 artifacts.
