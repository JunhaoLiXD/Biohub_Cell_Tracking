# exp_067 — Learned local-temporal evidence with a joint continuation/division decoder

**Proposal v1 — for Codex independent challenge. NOT a consensus record. NOT admission. NOT READY.**

| | |
|---|---|
| Author | Claude Code (strategy author / implementation lead) |
| Written | 2026-09-25 |
| Parent | `exp_064_x138_verbatim_repro`, Public LB **0.953** (submission 56535761), output sha `d52a5da2ae5cb0d1b22499f6ca51a00838a6c32ae9a1986ec756ea72e7909e03` |
| Authorization covered by this document | architecture design + local implementation + local validation only |
| Authorization NOT covered | remote GPU launch, leaderboard submission, promotion, `git push` |
| Local cost | 0 GPU h |
| Remote cost if ever authorized | ~4.0 GPU h in two runs + 1 LB slot — **UNCOMMITTED**, see §13 |
| GPU pool at time of writing | 17.386695 h (`GPU_BUDGET.json`) |
| `admission.require_codex_review` | `true` (kept, §12.8) |

Verification note: every `cell N:L` citation below refers to the snapshot notebook
`experiments/exp_064_x138_verbatim_repro/snapshot/source/biohub-x138.ipynb`, cell `N` (0-indexed),
line `L` within that cell's joined source. Reproduce the dumps with:

```bash
python -c "import json,pathlib; nb=json.load(open('experiments/exp_064_x138_verbatim_repro/snapshot/source/biohub-x138.ipynb',encoding='utf-8')); out=pathlib.Path('scratchpad/exp067_inspect'); out.mkdir(parents=True,exist_ok=True); [ (out/f'cell{i:02d}.py').write_text(''.join(c['source']),encoding='utf-8') for i,c in enumerate(nb['cells']) ]"
```

---

## 1. What I found in the parent before designing anything

The brief asked for an executable design rather than a named architecture. Seven findings from
reading the parent changed the design materially. All are checkable at the cited lines.

### F1 — The complete pre-ILP candidate pool is **already exported** on every run, but one of its two channels is dead code

`BIOHUB_CACHE_DIR = /kaggle/working/edge_cache` (cell 0:104) activates a patch chain (cell 4:488)
that writes one `edge_cache/{stem}.npz` per movie containing `coords`, `edge_src`, `edge_tgt`,
`edge_prob`, `admitted`, `low_coords`, `low_score`.

- `edge_src/edge_tgt/edge_prob` are gated on `probs > _CACHE_THRESHOLD` with
  `BIOHUB_CACHE_EDGE_THRESHOLD = "1.0"` (cell 0:105). `probs` is a softmax output in `[0, 1]`, so the
  condition is **never true** and those three arrays are always empty. This is the eighth recorded
  instance in this project of wired machinery that does nothing.
- `admitted = np.asarray(edges, dtype=np.float64)` is **not** gated. `edges` is `all_edges` from
  `predict_video`, i.e. every `(src_idx, tgt_idx, prob, dist)` with `prob > cfg.threshold`. Because
  `--use-ilp` is on (cell 2:45, `USE_ILP` default `1`), `PredictConfig.__post_init__` leaves
  `max_parents_per_node` and `max_children_per_node` as `None`
  (`references/biohub-tracking-support-pack/repo/scripts/predict_unet_transformer.py:85-93`), so the
  greedy degree caps never fire and `all_edges` **is** the complete above-threshold candidate pool.
  `cfg.threshold` is `0.48` (cell 3:663, `BIOHUB_DUAL_SEED_EDGE_THRESHOLD`), in softmax-over-sources
  space.

**Consequence:** the "complete alternative pool" this experiment needs mostly exists already. The new
export surface is per-node backbone embeddings, a verified index↔node-id map, and a schema/manifest.
Risk drops a lot, and §12.7's "real exporter, not a toy" requirement becomes a small patch.

### F2 — Motion re-link really does see only retained-edge probabilities

`filter_output_graph` builds `learned_edge_probs` by iterating `edges` — the graph edges that
survived the ILP and the length filter — and nothing else (cell 5:1931-1942), then passes that dict
into `motion_relink_edges` (cell 5:1943). The candidate pool is never consulted. The brief's claim is
confirmed at line level.

### F3 — The occupied-daughter bottleneck is one line

`add_safe_divisions_postlink` builds `candidate_ids` as
`[node_id for node_id in child_frame_ids if node_id not in incoming and node_id not in used_targets]`
(cell 5:1509). A node that already has **any** incoming edge can never be proposed as a second
daughter, whatever the evidence. `source_ids` additionally requires out-degree exactly 1
(cell 5:1508). So `P → {A, B}` is unreachable whenever some `Q → B` already exists — even when
`Q → B` is the weaker hypothesis. This is the single capability gap exp_067 exists to close.

### F4 — Sparse labels are not a compromise here; the official scorer masks exactly the same way

`compute_edge_confusion` (cell 8:41-66) counts a predicted edge as TP only when both endpoints are
matched and the GT edge exists, and as FP only when the matched endpoint has GT structure
(`mt in gt_incoming_source` or `gt_outgoing.get(ms)` non-empty). An edge between two unmatched
predicted nodes is **neither TP nor FP — it is free**. Unmatched predicted nodes cost only through
`adjusted_jaccard`'s one-sided node-count factor (cell 8:74-77).

So "unmatched ⇒ UNKNOWN, never a negative" is not a concession to label sparsity; it is a faithful
reproduction of the metric. The training mask and the scorer mask can be *the same predicate*, and
§9.2 makes them literally the same function.

### F5 — Division credit is component-level, and that is what makes a joint decoder a different lever

`compute_division_confusion` (cell 8:100-187) awards a TP when one weakly-connected component
contains (a) a node matched to the anchor (GT parent *or its* parent), (b) a matched node from each
daughter lineage, and (c) **any** node of out-degree ≥ 2. The fork does not have to sit on the right
node. `docs/research/step0_division_audit_reconciliation_2026-09-25.md` established that the 9
division FNs fail this *looser* test, and that the failure modes include the two daughter lineages
sitting in **different components**, which the post-process division levers cannot merge.

Reassigning a parent merges components. That is the mechanism by which exp_067 is not a fourth
division-gate arc: `PLAN.md` closed the gate-tuning family, not parent reassignment.

### F6 — The dominant labelled error is mis-assignment among competitors, not spurious extra links

Summing the `base` rows of `experiments/exp_065_metric_aligned_pruning/collection/validator_results.csv`
(8 held-out TRAIN movies; arithmetic in `scratchpad/exp067_inspect/ceiling.py`, which reproduces the
archived aggregate to 7 decimals):

| | |
|---|---|
| labelled edge TP / FP / FN | **5560 / 220 / 191** |
| FN split | **124 fragmented** (both endpoints detected, link missing) + **67 detection-lost** |
| `wrong_association_edges` (both endpoints matched, wrong pair) | **1** |
| division TP / FP / FN | 3 / 2 / 9 (12 GT events) |
| matched vs total predicted nodes | 180,922 `spurious_pred_nodes` — labels cover ≈3% of nodes |

`wrong_association_edges = 1` against `edge_fp = 220` means **219 of the 220 FPs are edges from a
matched node with GT structure to an unlabelled node.** The fix for those is not deletion — it is
moving the edge to the correct matched partner. TP-gain and FP-removal are therefore the *same*
operation, and 124 fragmented GT edges are the reachable population.

Oracle ceiling if every fragmented GT edge were relinked, node counts held fixed:

| variant | `adjusted_edge_jaccard` | proxy | Δ proxy |
|---|---|---|---|
| actual base | 0.9340604 | 0.9554890 | — |
| pessimistic (no FP removed) | 0.9549543 | 0.9763829 | **+0.0208939** |
| optimistic (one FP removed per fix) | 0.9750397 | 0.9964683 | **+0.0409793** |

For scale, the best candidate in the whole harvested pruning sweep (`ep015`) is **+0.0051** proxy.

⚠ This is an **oracle ceiling on a 3%-labelled subset of 8 in-sample-backbone movies**, not an
expected gain. §14 states why I expect a small fraction of it at most, and `exp_055` is the
governing precedent: a joint cut-and-reconnect repair scored **+0.0148537** on this same local proxy
and moved the Public LB **0.000**.

### F7 — Four mechanical facts that constrain the schema

1. **Two embeddings per node, not one.** `window_size = 2` with stride 1, so frame `t` is encoded in
   window `(t-1, t)` as target and in window `(t, t+1)` as source, from *different* UNet forward
   passes (and with `BIOHUB_EDGE_FEATURE_TTA=1`, cell 4:287, from different 8-view averages). The
   source-role and target-role embeddings of the same node differ. The schema carries both, with
   explicit coverage: `emb_src` exists for `t ∈ [0, T-2]`, `emb_tgt` for `t ∈ [1, T-1]`.
2. **`admitted`'s distance column is unusable.** `dist` is computed on `coords_so_far`
   (`predict_unet_transformer.py:482-485`), which is in *downsampled* grid units with anisotropic
   axes, before the `*= ds_arr` rescale. All geometry must be recomputed in µm from `coords` with
   `VOXEL_SCALE_UM = (1.625, 0.40625, 0.40625)` (cell 5:9).
3. **Coordinates are float, not int.** The V1284 patch deletes `coords = coords.astype(np.int16)`
   (cell 4:527-528), so `coords` keeps sub-voxel refined positions in original-resolution voxel units.
4. **Node provenance is already recorded on the node dicts.** Gap-filled nodes carry
   `gap_synthetic: 1` (cell 5:948, 1451); readmitted detector peaks carry `readmitted: 1`
   (cell 5:1291-1292). Original detections carry neither. No geometric guessing is needed to classify
   a node.

---

## 2. Hypothesis, exact change, and what would falsify it

### 2.1 The one hypothesis

> **H1.** On the frozen `exp_064` pipeline, replacing the final association decision for
> *originally-detected* nodes with a joint mutually-exclusive selection over adjacency-continuation
> and mother→two-daughter hypotheses — scored from local 7-frame learned evidence over the **complete**
> pre-ILP candidate pool rather than only the retained edges — increases the held-out proxy
> (`adjusted_edge_jaccard + 0.1 · division_jaccard`, cell 8:300-318) by **≥ +0.002** on the 8-movie
> validator set, with **no embryo prefix regressing by more than 0.001**, and does so primarily by
> converting fragmented GT edges into true positives.

Pre-registered readings, decided before any number is looked at:

| held-out proxy Δ vs base 0.9554890 | prefix constraint | reading |
|---|---|---|
| ≥ +0.005 | both prefixes ≥ −0.001 | strong; consider one LB probe (still needs separate authorization) |
| +0.002 … +0.005 | both prefixes ≥ −0.001 | weak positive; **do not submit** on this alone |
| any Δ with a prefix regression > 0.001 | — | fails, same anti-overfit rule the notebook author uses and `ep015` failed |
| < +0.002 | — | **falsified.** Close exp_067, keep `exp_064` |

The mechanism claim is separately falsifiable and must be checked *first*: if `edges_fragmented`
does not fall, any proxy change came from somewhere else and H1 is not supported even if the number
is positive.

### 2.2 The exact change (three artifacts, nothing else)

1. **Exporter patch** (`scripts/exp067_export_patch.py`, injected by the builder into notebook cell 4
   after the existing patch chain): adds per-node backbone embeddings, an index↔node-id map, and a
   manifest to the *already existing* `edge_cache/{stem}.npz`. Also fixes `edge_prob`'s dead gate by
   writing the pool from `admitted` explicitly rather than relying on `_CACHE_THRESHOLD`. Changes no
   prediction value.
2. **Label builder patch** (same builder, notebook cell 8 region, runs only when
   `BIOHUB_EXP067_LABELS=1`): after the existing validator match, writes
   `exp067_labels/{stem}.npz` using the notebook's own `match_nodes_bipartite`. Touches GT; is a
   separate file, a separate flag, and is never read by the inference path.
3. **Decoder stage** (`scripts/exp067_joint_decode.py`, one call site in notebook cell 5): inserted in
   `filter_output_graph` **after** the `OUTPUT_DIVISION_GEOMETRY_FILTER` block (cell 5:2015-2047) and
   **before** `OUTPUT_PRUNE_ISOLATED` (cell 5:2049). Gated on `BIOHUB_EXP067_ENABLE`; default `0`.

### 2.3 Why that stage, precisely

| property | why this insertion point |
|---|---|
| node universe is final | every node-creating stage (readmit, single-frame gap close, gap2, low-detection fill) has already run, so v1 never has to invent a node |
| coordinates untouched | `linefit_smooth_output_graph` (cell 5:2061) runs after us and is unchanged |
| our decisions are not silently undone | the division-geometry filter has already run; putting the stage after it means nothing rewrites our edges |
| the parent's safety nets still run | prune-isolated, short-track filtering and line-fit smoothing all run after us and only remove or smooth — they never relink |
| bypass is trivially exact | `BIOHUB_EXP067_ENABLE=0` ⇒ the call is not made ⇒ byte-identical parent output |

**Raw candidate universe vs final graph nodes — the distinction the brief asked for:**

- **U (raw candidate universe):** the rows of `coords` in `edge_cache/{stem}.npz`, i.e. every
  detector peak above `BIOHUB_DET_THRESHOLD = 0.965`. These are the `.geff` nodes. These have
  embeddings.
- **L (low-detection pool):** `low_coords`/`low_score`, peaks above `BIOHUB_LOWDET_THRESHOLD = 0.3`.
  Optionally given embeddings by the exporter (flag `BIOHUB_EXP067_EXPORT_LOWDET_EMB`).
- **V (final graph nodes at stage S):** survivors of U, plus `readmitted: 1` nodes drawn from L, plus
  `gap_synthetic: 1` nodes that are *interpolated midpoints* and therefore have no detector identity
  at all.
- **R (reconsiderable set) = V ∩ (U ∪ L-with-embeddings).** Only nodes in R generate new hypotheses.
  Edges incident to `V \ R` are **frozen**: fixed to their stage-S value, still counted in every
  degree constraint. v1 therefore cannot re-link synthetic gap nodes, and §14 lists that as a stated
  limitation, not an omission.

---

## 3. Package and file layout

```
scripts/
  exp067/
    __init__.py
    schema.py          # EXPORT_SCHEMA_VERSION, dtype/unit/field contracts, validators
    export_patch.py    # the notebook-side exporter source, as text + anchors (fail-closed)
    label_patch.py     # the notebook-side GT-join source, as text + anchors (fail-closed)
    features.py        # window assembly, token ordering, feature spec, normalisation
    model.py           # SparseLocalLineageScorer (torch) + numpy reference forward
    hypotheses.py       # candidate continuation edges + division triples, deterministic
    decode.py          # objective assembly, component split, solver backends, validation
    supervise.py       # label cache -> masked training tensors; split manifests
    train.py           # CLI: fixed seed, bounded epochs/walltime, train-only normalisation
    infer.py           # CLI + the in-notebook entry point exp067_joint_decode()
    evaluate.py        # calls the parent's own scorer functions; per-video + aggregate + audit
    audit.py           # graph invariant checks + receipt emission
    solver_ref.py      # dependency-free exact branch-and-bound (reference + fallback)
  build_exp067_notebook.py   # builder: parent notebook -> exp_067 variant, parity-guarded
  validate_exp067_notebook.py# structural validator (anchor uniqueness, patch/strip parity)
  test_exp067_*.py           # the local test suite of §12

experiments/exp_067_temporal_joint_lineage/
  architecture_brief_v1.md   # Codex's brief (present)
  proposal_v1.md             # this document
  dev_log.md                 # local development record (NOT STATE.json)
  fixtures/                  # tiny hand-built NPZ fixtures for the tests
  snapshot/                  # created only at admission time, not now
configs/exp_067_temporal_joint_lineage.yaml
```

Nothing in `scripts/exp067/` imports anything from the notebook. The notebook imports *it*, so the
whole module is testable locally.

---

## 4. Data schema (the export contract)

`schema.py` defines `EXPORT_SCHEMA_VERSION = 1` and validates every field on both write and read.
Any missing or malformed field is a hard error, never a substitution.

### 4.1 `edge_cache/{stem}.npz` — additions (inference-only, label-free)

| key | dtype | shape | units / meaning |
|---|---|---|---|
| `exp067_schema` | `<i4` | `()` | export schema version; reader refuses on mismatch |
| `exp067_node_ids` | `<i8` | `(N,)` | graph node id of `coords[i]`, captured from `build_graph`'s own `bulk_add_nodes` return — **not assumed to equal `i`** |
| `exp067_emb_src` | `<f2` | `(N, C)` | source-role backbone embedding, `C` read from the weights' `config.json` (`unet_out_channels`, 32 in the mounted checkpoint) |
| `exp067_emb_tgt` | `<f2` | `(N, C)` | target-role backbone embedding |
| `exp067_emb_src_valid` | `bool` | `(N,)` | false for `t = T-1` |
| `exp067_emb_tgt_valid` | `bool` | `(N,)` | false for `t = 0` |
| `exp067_det_score` | `<f4` | `(N,)` | `sigmoid(det_logit)` at the peak |
| `exp067_pool_src` | `<i4` | `(M,)` | candidate pool source **row index** into `coords` |
| `exp067_pool_tgt` | `<i4` | `(M,)` | candidate pool target row index |
| `exp067_pool_prob` | `<f4` | `(M,)` | post-fusion `softmax(raw, dim=0)` probability, normalised over sources |
| `exp067_low_emb` | `<f2` | `(N_low, C)` | present only when `BIOHUB_EXP067_EXPORT_LOWDET_EMB=1` |
| `exp067_manifest` | `<U` json | `()` | see below |

`exp067_manifest` (json string) carries: `stem`, `schema`, `voxel_scale_um`, `downsample`,
`window_size`, `emb_channels`, `emb_dtype`, `pool_threshold` (`cfg.threshold` as actually resolved),
`det_threshold`, `lowdet_threshold`, `n_nodes`, `n_pool`, `T`, `coords_sha256`, `pool_sha256`,
`emb_src_sha256`, `emb_tgt_sha256`, `weights_sha256` (primary and secondary),
`predict_source_sha256` (the patched `predict_unet_transformer.py`), `split` (`"test"` or `"val"`),
`ground_truth_accessed: false`, `created_at_utc`.

Units are stated once and never re-derived: `coords[:, 0]` is integer frame index; `coords[:, 1:]` is
original-resolution voxel `(z, y, x)`, float32; µm = voxel × `(1.625, 0.40625, 0.40625)`.

### 4.2 `exp067_labels/{stem}.npz` — GT join, training only

| key | dtype | shape | meaning |
|---|---|---|---|
| `schema` | `<i4` | `()` | label schema version |
| `matched_pred` | `<i8` | `(K,)` | predicted **stage-S node id** matched to GT |
| `matched_gt` | `<i8` | `(K,)` | its GT node id |
| `gt_edge_src/gt_edge_tgt` | `<i8` | `(G,)` | GT edge list |
| `gt_out_degree` | `<i4` | `(n_gt,)` | per GT node, for the FP predicate |
| `gt_has_parent` | `bool` | `(n_gt,)` | per GT node, for the FP predicate |
| `gt_node_t` | `<i4` | `(n_gt,)` | GT frame index |
| `match_radius_um` | `<f4` | `()` | `VALIDATOR_MATCH_RADIUS_UM`, 7.0 |
| `manifest` | `<U` json | `()` | `stem`, `prefix`, `stage` (`"S"`), `pred_graph_sha256`, `gt_geff_path`, `scorer_fn_sha256`, `created_at_utc` |

Two separations the brief required, made structural rather than promised:

- different directories, different env flags, different patches;
- `infer.py` contains no import of `supervise.py` and no path containing `label`. §12.3 asserts this
  by source inspection *and* by running inference with the label reader monkeypatched to raise.

### 4.3 Checkpoint schema

`{format_version, state_dict, feature_spec, norm_mean, norm_scale, hyperparams, seed,
train_manifest_sha256, export_schema_version, model_code_sha256, created_at_utc}`.
`infer.py` refuses to run unless `feature_spec` equals the live `features.py` spec **elementwise**
(name, index, unit) and `export_schema_version` matches the npz. A mismatch is a hard error with the
differing field named — never a silent re-order.

---

## 5. The model: sparse local 7-frame evidence

### 5.1 Scope, and the capacity argument

F6 gives ~5,560 labelled positive edges, **411 labelled error sites** (220 FP + 191 FN) across
**8 movies and 2 embryo prefixes**. That is the entire supervision budget. It supports a *tiny*
model and nothing else. v1 therefore fixes:

- token dim `d = 48`, 2 encoder layers, 2 heads, MLP ratio 2, no dropout on such a small set but
  weight decay `1e-2`; **≈ 40k parameters** total;
- the head emits a **residual** `Δ` in log-odds on top of the parent's own pool probability, scaled by
  a learned scalar `α` initialised to 0 (§6.1). A useless head therefore degrades toward "the parent's
  own probabilities, re-decided jointly", which is a meaningful and separately measurable ablation
  rather than noise.

### 5.2 Tokens and windows

For a movie and a frame `t`, nodes of frame `t` in R are partitioned into **spatial blocks** of ≤32
by a deterministic fixed-size voxel grid (grid pitch from `OUTPUT_EDGE_MAX_UM`; ties broken by
`(t, node_id)` ascending). For each block:

- **window** = frames `[t-3, t+3]` ∩ `[0, T-1]` (7 frames, "future context permitted because inference
  is offline over the whole movie", per the brief);
- **tokens** = the block's nodes, plus for each frame in the window the `k = 24` nearest R-nodes in µm
  to the block centroid, deduplicated, capped at 256 tokens, ordered by `(t, node_id)` ascending;
- one forward pass per block scores every candidate edge whose **source** is in the block.

This is the brief's "score in overlapping windows, then solve a coherent graph" option, and there is
no aggregation ambiguity to resolve: windows overlap in *context* but each candidate edge is scored
**exactly once**, in the pass owning its source node. `hypotheses.py` asserts that ownership is a
partition (§12.4). Frames outside `[0, T-1]` contribute no tokens and are absent from the attention
mask — they are never zero-padded into the token set.

### 5.3 Per-token features (the `feature_spec`, fixed order, units stated)

| group | fields | unit |
|---|---|---|
| backbone | `emb_src[C]`, `emb_tgt[C]`, `emb_src_valid`, `emb_tgt_valid` | dimensionless, fp16→fp32 |
| geometry | `(z, y, x)` minus the block centroid | µm |
| time | `t − t_block`, and its sin/cos at 3 frequencies | frames |
| detection | `det_score`, `is_low_detection` | probability, flag |
| parent-graph role (inference-consistent, no GT) | `has_parent_edge_at_S`, `out_degree_at_S`, `is_readmitted`, `is_gap_synthetic`, `in_current_block` | flags/ints |
| disagreement | `parent_pool_prob` of the node's stage-S incoming edge; `max_pool_prob` over its incoming pool entries; their difference | probability |
| availability | one explicit mask bit per optional group above | flag |

**Fail-closed rule.** `features.py` raises `Exp067FeatureUnavailable` when a feature that the schema
says *must* exist is absent (e.g. an R-node with no embedding row). Features that are legitimately
absent for a whole class of node (no `emb_tgt` at `t = 0`; no pool entry below the 0.48 threshold) are
represented by an explicit **mask bit plus a value that the mask multiplies out**, and the model
never sees an unmasked fabricated number. There are no random and no zero stand-ins for missing
*required* features. §12.4 tests both branches.

### 5.4 Two forward implementations

Torch is the training and deployment path. A **numpy reference forward** in `model.py` computes the
identical function from the same `state_dict`. Rationale, stated plainly: the local dev environment is
**numpy 2.5.3 only — no torch, no scipy** (verified). Without the numpy reference, none of the
mask/permutation/determinism tests in §12 can run locally at all, and the architecture would be
accepted on unexecuted code, which is exactly the failure mode this project has recorded eight times.
Cost ≈ 200 lines. When torch *is* importable, §12.6 asserts torch-vs-numpy agreement to `1e-5`.

If Codex judges the double implementation not worth it, §15 gives the narrower alternative.

---

## 6. Hypothesis generation

Let `S` be the stage snapshot: nodes `V` with frames `t(v)`, edges `E_S`.

### 6.1 Continuation hypotheses `H`

`(u, v)` with `t(v) = t(u) + 1`, both in `V`, from the union of:

| source | rule | why |
|---|---|---|
| **(a)** `E_S` | every stage-S edge, unconditionally | guarantees the parent solution stays feasible |
| **(b)** forward top-k | for `u ∈ R`: the `K_c = 3` highest `pool_prob` targets in `R` | ordinary continuation competition |
| **(c)** backward top-k | for `v ∈ R`: the `K_p = 3` highest `pool_prob` sources in `R` | **this is what reaches an occupied daughter's true parent** |
| **(d)** geometric fallback | for `u ∈ R` with fewer than 2 pool entries: the `N_g = 3` nearest R-nodes within `OUTPUT_EDGE_MAX_UM` | the pool is thresholded at 0.48, so true links can be missing entirely |

Edges from (d) carry `pool_prob` **unavailable** (mask bit set), never 0.0 dressed as a probability.
`H` is a set of distinct ordered pairs; construction sorts by `(t(u), u, v)` so the variable order is
deterministic and hash-stable.

Scores: `s_e = logit(clip(p_e, 1e-6, 1-1e-6)) + α · Δ_e` for pool-backed edges, and
`s_e = c_geom + α · Δ_e` for (d)-edges, where `c_geom` is one fitted scalar, not a guess. `α` is
learned, initialised 0.

### 6.2 Division hypotheses `D`

`h = (u, {a, b})` with `a ≠ b`, `t(a) = t(b) = t(u) + 1`, both `(u,a)` and `(u,b)` in `H`, and the
pair satisfying the parent's **own** geometry predicates, evaluated by calling the parent's own
`edge_distance_um` / `_position_um` with the parent's own env-resolved constants
(`SAFE_DIV_MAX_UM = 9.0`, `SAFE_DIV_SISTER_MAX_UM = 14.0`, `SAFE_DIV_SISTER_SYMMETRY_TAU = 0.6`,
`SAFE_DIV_DIVERGE_UM = 2.25`). At most `K_d = 2` per `u`, ranked by `g_h`.

Critically, `D` is generated **without** the `not in incoming` restriction of F3. A daughter that
already has a parent is a legal hypothesis; the decoder, not a filter, decides.

Symmetry: the pair is stored sorted (`a < b`), and `g_h` aggregates the two daughters only through
symmetric functions (sum, min, absolute difference). Permutation invariance is therefore structural,
and §12.2 tests it by feeding both orders through the real code path.

### 6.3 Division evidence `g_h`, and why it is **not** learned in v1

There are **12** labelled division events, 3 of which the parent already gets. A learned
mother/daughter-pair head trained on 12 positives would be an untrained head with a confident name —
precisely what the brief forbids advertising. v1 therefore sets

```
g_h = min(s_(u,a), s_(u,b)) + w_sym · sym(a, b) − λ_div
```

with `sym` the parent's own symmetry statistic and **exactly two scalars** (`w_sym`, `λ_div`) selected
on held-out movies by grid search, reported with their full selection curve. The hyperedge *machinery*
is general and the learned-head interface exists (`model.py` exposes `division_head=None`), but v1
ships it disabled and says so in the metrics.

---

## 7. The joint decoder

### 7.1 Variables

- `x_e ∈ {0,1}` for `e ∈ H` — continuation edge selected
- `d_h ∈ {0,1}` for `h ∈ D` — division event selected
- edges in `E_S` with an endpoint outside `R` are **fixed** `x_e = 1` (not decision variables)

### 7.2 Objective

Maximise

```
Σ_{e∈H} (s_e − τ + β·1[e ∈ E_S]) · x_e  +  Σ_{h∈D} g_h · d_h
```

- `τ` is the **birth/death baseline**: leaving a node with no incoming edge costs 0, so `τ` is the
  log-odds admission threshold an incoming edge must beat. One scalar, selected on held-out movies.
  Stating it this way makes the "no edge" branch explicit rather than implicit.
- `β ≥ 0` is the **parent-incumbency bonus** — the single conservatism dial. `β = 0` is a free
  re-decision; as `β → ∞` the parent solution becomes the unique optimum. §12.5 tests that a large
  `β` reproduces the parent graph edge-for-edge *through the whole real pipeline*, which is a much
  stronger check than a bypass branch.
- Scores are per-target-comparable because `τ` is global and `s_e` is in log-odds; there is no
  per-node renormalisation that could make two components incomparable.

### 7.3 Constraints

| # | constraint | for | meaning |
|---|---|---|---|
| C1 | `Σ_{e=(·,v)} x_e ≤ 1` | all `v ∈ V` | max in-degree 1 |
| C2 | `Σ_{e=(u,·)} x_e ≤ 1 + Σ_{h=(u,·)} d_h` | all `u ∈ V` | out-degree > 1 only via a division |
| C3 | `Σ_{h=(u,·)} d_h ≤ 1` | all `u ∈ V` | at most one division event per node |
| C4 | `d_h ≤ x_{(u,a)}`, `d_h ≤ x_{(u,b)}` | all `h` | a declared division must realise both its edges |
| C5 | `x_{(u,a)} + x_{(u,b)} ≤ 1 + Σ_{h ∋ {a,b}} d_h` | all `u`, all pairs in `H(u)` | a fork can exist **only** through a declared division event |
| C6 | fixed `x_e = 1` | frozen edges | counted in C1–C3 like any other edge |

**No temporal cycles — by construction, not by constraint.** Every `e ∈ H` satisfies
`t(target) = t(source) + 1`, so any path strictly increases `t`; a cycle is impossible. `audit.py`
asserts the adjacency property on the emitted graph anyway, so the proof cannot rot.
**No skips:** same property. **No duplicate targets from one source:** `H` holds distinct pairs and C2
bounds out-degree. **No dangling edges:** both endpoints are drawn from `V`, and `audit.py` re-checks
against the emitted node dict.

### 7.4 The occupied-daughter case, worked

Parent `P→A` exists; competitor `Q→B` exists; `P, Q, A, B ∈ R`. Rule (c) puts `(P,B)` in `H`
regardless of `B`'s occupancy. `h = (P, {A,B})` enters `D` if the parent's own geometry allows it.
Setting `x_{(P,A)} = x_{(P,B)} = d_h = 1` forces `x_{(Q,B)} = 0` by C1, and C2/C5 are satisfied through
`d_h`. The reassignment is legal, and it is chosen exactly when
`g_h + (s_{(P,B)} − τ) > (s_{(Q,B)} − τ) + β`. Nothing in the formulation special-cases it. §12.1 is
this fixture.

### 7.5 Decomposition, bounds, backends, and failure

- **Decomposition.** Objective and constraints are separable across connected components of the
  conflict graph (variables adjacent when they share a node). Components are solved independently, in
  order of their minimum `(t, node_id)`, giving a deterministic and parallel-safe solve.
- **Bounds.** `MAX_COMPONENT_VARS = 2000`, `MAX_COMPONENT_SECONDS = 5`, `MAX_TOTAL_SECONDS` from
  `BIOHUB_EXP067_SOLVE_BUDGET_S` (default 600 per movie). Any bound hit ⇒ **that component reverts to
  its stage-S assignment** and a receipt row is written. The run continues; no silent degradation.
- **Backends, in order:** (1) `scipy.optimize.milp` (HiGHS) when importable — available on Kaggle,
  not in the local dev venv; (2) `solver_ref.py`, a dependency-free exact best-first branch-and-bound
  with a sum-of-positive-weights bound and a node-count cap — this is what makes the local tests
  executable, and it is the reference implementation, not a toy; (3) neither certifies ⇒ parent
  fallback for that component with a reason.
- **Incumbent validation, always.** Every returned assignment passes through `audit.py`
  (integrality, C1–C5, adjacency, finiteness, no dangling, node set unchanged) **before** it is
  accepted. A violation reverts that component to the parent and records
  `reason = "incumbent_invalid:<check>"`. When both backends are present, §12.5 asserts they return
  the **same objective value** on the fixtures.
- **Receipt.** `exp067_receipt.json` per run: per-movie counts of components solved / reverted, with
  reasons; edges changed, added, removed; divisions added / reclaimed; solver backend actually used;
  wall-clock. Anything less than a fully solved movie is visible in the metrics, never presented as
  success. If more than `MAX_REVERT_FRAC = 0.02` of components revert, the whole movie falls back to
  the parent graph and the run reports `exp067_active = false`.

---

## 8. What is frozen

Detector, both temporal backbones, the DeepCenter veto model, the V1284 coordinate head, all 89
`BIOHUB_*` values of the parent, the ILP stage, the motion re-link, readmission, gap filling, and
`add_safe_divisions_postlink` — all unchanged. exp_067 adds one stage and reads one extra file. No new
detection. **`cx03` / `ep*` / `seg*` pruning is not part of this and must not be combined with it**
(`exp_066`'s `cx03` probe is pending and is not the parent).

---

## 9. Supervision

### 9.1 Where labels come from

Only from the **Run A** export (§13), which has `TRAIN_DIR` and the notebook's own matcher. Local
development has no competition data and no GT (verified: no `.geff` anywhere in the repo), so the
GT join *cannot* happen locally and must not be faked. Local tests use hand-built fixtures with
hand-written labels.

### 9.2 Label predicate — literally the scorer's predicate

`supervise.py` exposes one function used by both training and evaluation:

```
label(u, v):
    mu, mv = match(u), match(v)
    if mu is None or mv is None:              return UNKNOWN
    if (mu, mv) in gt_edges:                   return POSITIVE
    if gt_has_parent[mv] or gt_out_degree[mu] > 0:  return NEGATIVE
    return UNKNOWN
```

The `NEGATIVE` clause is `compute_edge_confusion`'s `is_fp` condition (cell 8:60-62) restricted to
both-matched pairs. Consequences, all deliberate:

- an unmatched endpoint is **never** a negative;
- a matched pair with no GT structure on either side is **UNKNOWN**, not negative;
- **daughters are not mislabelled.** The loss is per-edge independent binary cross-entropy, *not* a
  softmax over targets. When `mu` has two GT children and both are matched, both `(u,a)` and `(u,b)`
  get `POSITIVE`. Continuation label 1 therefore never implies "not a division", and no daughter is
  pushed to be a negative of its sister. §12.3 tests exactly this configuration.
- Loss is masked; `UNKNOWN` contributes zero gradient. The masked fraction is reported per epoch, so
  "the model trained on nothing" cannot pass unnoticed.

### 9.3 Splits, and an honest statement about independence

- Split manifests are explicit YAML lists of stems, one per fold, with the prefix recorded.
- `supervise.py` **fails** on: a stem in two folds; a stem in no fold; a stem that appears in the
  competition TEST set; a fold with zero positives; a prefix absent from training.
- Primary protocol: **leave-one-movie-out** over the 8 validator stems (8 folds).
  Secondary: **leave-one-prefix-out** (2 folds) — with only `44b6` and `6bba` present this is the real
  cross-embryo test and it is weak by construction. Both are reported.
- **Disclosure, mandatory in every metrics file and every report:** the frozen backbone and the
  V1284 head were trained on the competition TRAIN split, which *includes all 8 validator stems*.
  Our head sees no GT from its own validation fold, but the *features it consumes* are not independent
  of those movies. **This is not independent external validation and must never be described as such.**
  The only genuinely held-out signal remains the Public LB.

---

## 10. Training CLI and determinism

```
python -m scripts.exp067.train \
  --export-dir  artifacts/exp067/export \
  --label-dir   artifacts/exp067/labels \
  --splits      configs/exp067_splits.yaml \
  --fold        loo_6bba_09961292 \
  --out         artifacts/exp067/ckpt/<fold>.pt \
  --seed 20260925 --max-epochs 60 --max-seconds 900 --device cpu
```

- Single seed for python/numpy/torch; `torch.use_deterministic_algorithms(True)`;
  `num_workers=0`; token order fully determined by `(t, node_id)`.
- Feature normalisation computed **on the training fold only**, stored in the checkpoint, never
  recomputed at inference. §12.3 asserts that changing the held-out fold changes the stored stats and
  that `infer.py` has no code path that computes statistics.
- Bounded: `--max-epochs`, `--max-seconds`, early stop on held-out proxy with a fixed patience.
- Checkpoints written atomically (temp + rename) with the §4.3 schema and the code hash.
- Expected cost: **minutes of CPU** on ~6k labelled edges with a 40k-parameter model. Not a GPU task.

Runnable end-to-end sequence (external data requirements stated honestly per stage):

| stage | command | needs |
|---|---|---|
| 1. export | Run A kernel (§13) | Kaggle GPU + competition data |
| 2. pull | `kaggle kernels output <ref>` | network |
| 3. supervised cache | `python -m scripts.exp067.supervise --export-dir … --label-dir … --out …` | local CPU |
| 4. train | `python -m scripts.exp067.train …` | local CPU **+ torch** (not currently installed — §14) |
| 5. decode locally | `python -m scripts.exp067.infer --export-dir … --graph … --ckpt …` | local CPU |
| 6. evaluate | `python -m scripts.exp067.evaluate --pred … --labels …` | local CPU |
| 7. deploy | Run B kernel (§13) | Kaggle GPU, **separate authorization** |

---

## 11. Evaluation protocol

`evaluate.py` does not reimplement the metric. It imports the parent's own
`match_nodes_bipartite`, `compute_edge_confusion`, `edge_jaccard`, `adjusted_jaccard`,
`compute_division_confusion`, `decompose_errors`, `score_sample`, `aggregate_official` from a
single extracted module whose text is byte-compared against notebook cell 8 by the structural
validator. `scratchpad/exp067_inspect/ceiling.py` already demonstrates that this reproduces the
archived `base` aggregate to 7 decimals (0.9554890), so the extraction is verified before it is used.

Reported, per fold and in aggregate:

- per-video `adjusted_edge_jaccard`, `edge_tp/fp/fn`, `div_tp/fp/fn`, `t_pred/t_true`, weight;
- the official aggregate and the `+0.1·division_jaccard` proxy;
- **per-prefix** aggregates (the anti-overfit rule of §2.1);
- the `decompose_errors` breakdown, with `edges_fragmented` called out as H1's mechanism check;
- full graph audit: in/out-degree histogram, fork count, component count and size distribution,
  adjacency violations (must be 0), dangling edges (must be 0), node-count delta vs parent;
- the §7.5 receipt, including reverted components;
- `division_head_trained: false` stated explicitly.

---

## 12. Local tests — the brief's seven groups, as concrete cases

All run on CPU with **numpy only**, except group 6. Fixtures live in
`experiments/exp_067_temporal_joint_lineage/fixtures/` and are hand-written, small enough to reason
about by hand, and committed.

**12.1 `test_exp067_occupied_daughter.py`** — the brief's fixture 1. Nodes `P,Q` at `t`, `A,B` at
`t+1`; stage-S edges `P→A`, `Q→B`; pool probabilities set so `P→B` is strong and symmetric with
`P→A`. Asserts: `(P,B) ∈ H` (via rule (c)); `(P,{A,B}) ∈ D`; the solved graph contains `P→A`, `P→B`
and **not** `Q→B`; `Q` ends with out-degree 0; the audit passes. Negative control: weaken the division
evidence below the margin and assert the parent solution is returned unchanged.

**12.2 `test_exp067_competition_invariants.py`** — continuation-vs-division exclusivity (C5 blocks a
fork without a `d_h`); in-degree ≤ 1; out-degree ≤ 2 and only through a division; daughter
**permutation invariance** (`(u,{a,b})` and `(u,{b,a})` give identical scores and identical solutions
through the real code path, not a constructed matrix); no duplicate target from one source; adjacency
only (a manually injected skip edge is rejected); emitted node set identical to the input node set.

**12.3 `test_exp067_supervision.py`** — `UNKNOWN` exclusion (unmatched endpoints produce no gradient,
asserted by a masked-loss count of 0); the both-daughters-positive configuration of §9.2; split
overlap rejected (stem in two folds ⇒ raise); a TEST stem in any fold ⇒ raise; train-only
normalisation (stats change with the fold; `infer.py` source contains no statistics computation);
no labels at inference (label reader monkeypatched to raise; inference still succeeds).

**12.4 `test_exp067_windows_features.py`** — window clipping at `t = 0` and `t = T-1` with masked,
not padded, out-of-range frames; each candidate edge owned by exactly one block (a partition check
over a synthetic movie); token order stable under input shuffling; feature spec index/unit round-trip;
µm conversion verified against `VOXEL_SCALE_UM`; `Exp067FeatureUnavailable` raised for a missing
*required* embedding; mask bit set (and no fabricated value used) for a legitimately absent optional
feature; the `admitted` distance column is never read (asserted by source inspection).

**12.5 `test_exp067_bypass_and_failure.py`** — bypass parity (`ENABLE=0` leaves a recorded graph
byte-identical); `β`-dominance parity (large `β` reproduces the parent graph edge-for-edge *with the
stage enabled*); checkpoint rejection on `format_version`, `feature_spec`, `export_schema_version` and
`model_code_sha256` mismatch, each with the differing field named; solver timeout ⇒ parent fallback
with a receipt reason; solver exception ⇒ same; `MAX_REVERT_FRAC` exceeded ⇒ whole-movie fallback and
`exp067_active = false`; all emitted coordinates and scores finite; when scipy is importable, HiGHS
and `solver_ref` return the same objective on every fixture.

**12.6 `test_exp067_torch_smoke.py`** — `skipif torch is None`. A real tiny CPU
train → save → load → infer → decode cycle on the fixtures; asserts the checkpoint round-trips, the
numpy reference forward matches torch to `1e-5`, and the decode completes. **Asserts nothing about
quality.** In the current local env this test **skips** — stated as a gap in §14, not hidden.

**12.7 `test_exp067_builder.py`** — the exporter/integration path, the group most often faked:
every patch anchor in `export_patch.py` / `label_patch.py` / the decode call site is located in the
**actually patched** `predict_unet_transformer.py` and notebook cells, after replaying the parent's
own five-stage patch chain (the technique `validate_exp062_notebook.py` group 4 established); each
anchor count is **exactly 1**; patched source compiles; double-patching is refused; the builder's
injected lines strip back to the parent **byte-for-byte**; and — the specific hazard cell 4:502-510
documents — the exporter patch is ordered so it neither consumes nor destroys the `lowdet peaks`,
V1284 or coordinate-manifest anchors, asserted by running the full chain in both orders and checking
all anchor counts stay 1.

**12.8 Not a test, a gate.** `configs/exp_067_temporal_joint_lineage.yaml` sets
`admission.require_codex_review: true` and `reviewer_provider: codex`. No snapshot is created and no
admission is requested by this document.

---

## 13. Budget and runtime bounds

**Local, now: 0 GPU h.** Implementation + tests: my own time only.

**Remote, if ever authorized — UNCOMMITTED, no reservation made, no launch requested:**

| run | what | validator | reserve | LB |
|---|---|---|---|---|
| **Run 0** | zero-GPU harvest: `kaggle kernels output` on the existing `exp_065` / `exp_066` kernels to see whether `edge_cache/*.npz` is in the retained output. If it is, we get the real candidate pool for free and can size `|H|`, component counts and the occupied-daughter population **before spending anything**. | — | **0 h** | 0 |
| **Run A** | export + labels. Parent notebook + the three patches, decoder **OFF**, `VALIDATOR_ENABLE=1`, `N_PER_TYPE=4`. Must assert in-run that `submission.csv` byte-reproduces `d52a5da2…` — the control, at no LB cost. | on | **3.0 h** (comparable validator runs measured 1.73–2.04 h) | 0 |
| **Run B** | deploy. Decoder **ON**, validator off, deterministic, single arm. | off | **1.0 h** (`exp_064` 0.259 h, `exp_066` 0.310 h) | 1 |

Total ≈ **4.0 h of 17.386695 h**. Run B only happens if §2.1's gate is met on Run A's evidence, and
only with explicit user authorization; the LB submission is a further separate authorization.

Per-movie decode bounds inside Run B: `MAX_TOTAL_SECONDS = 600`, `MAX_COMPONENT_SECONDS = 5`,
`MAX_COMPONENT_VARS = 2000`, and the parent's own `REPAIR_DEADLINE_S = 27000` watchdog still
applies unchanged. Expected scoring cost, to be **measured** in the smoke test rather than asserted:
~3,750 block passes per movie of ≤256 tokens at `d = 48`.

---

## 14. Honest gaps, risks, and what this proposal does not claim

1. **The deadline is the dominant risk.** The competition closes **2026-09-29 23:59** and `PLAN.md`
   stops new research **2026-09-28**. exp_067 is a multi-thousand-line build plus two remote runs.
   Realistically it fits only if the build is authorized essentially immediately and Run A happens
   within ~24 h. **I am not asking for that decision in this document**, and I will not pretend the
   schedule is comfortable: if it slips, the right outcome is a correct, tested, unlaunched artifact
   and `exp_064` remains the final submission.
2. **`exp_055` is the governing prior.** A joint cut-and-reconnect repair scored **+0.0148537** on
   this exact local proxy and moved the Public LB **0.000**. exp_067 is a more capable member of the
   same family and must be read against that, not against its oracle ceiling.
3. **The oracle ceiling is not a forecast.** +0.0209…+0.0410 (§F6) is what *perfect* relinking of
   labelled fragments would buy on 3% of the nodes of 8 movies whose images the frozen backbone was
   trained on. I expect a small fraction at best, and possibly nothing.
4. **Divisions are not learned, and the metrics will say so.** 12 events, 2 scalars. Any claim of a
   "learned division head" in v1 would be false.
5. **Validation is not independent.** §9.3. The backbone saw all 8 validator movies.
6. **Local environment gaps, both real:** no `torch` ⇒ §12.6 skips and no training can run locally
   until torch is installed; no `scipy` ⇒ HiGHS cannot be exercised locally and `solver_ref.py`
   carries the local test load. **Decision needed from the user:** install CPU-only torch + scipy into
   `.venv` (≈300 MB, against the current "numpy + tzdata, test-only" venv policy), or accept that
   training and the HiGHS backend are first exercised remotely. I recommend installing them — this
   project's recurring failure mode is unexecuted code.
7. **Out of v1 scope, stated rather than implied:** synthetic gap nodes are frozen and cannot be
   relinked; node coordinates are not changed; no new detections; no gap/skip hypotheses; low-detection
   embeddings are behind a flag; no learned birth/death head (`τ` is one scalar).
8. **Two assumptions that must be verified at runtime, not trusted.** (i) `.geff` node ids equal
   `coords` row indices — the exporter *records* the real mapping instead of assuming it, and the
   reader fails closed if the join is not bijective. (ii) `admitted` is the complete above-threshold
   pool — Run 0 or Run A must confirm `|admitted|` is consistent with the pool size implied by
   `cfg.threshold = 0.48`, and the run must fail if `admitted` is empty.
9. **No claim about the Public LB.** The one proxy↔LB calibration point available is base proxy
   0.95549 against measured LB 0.953, offset −0.0025. That is an offset, not a transfer function.

---

## 15. Narrower correct v1, if Codex judges the scope too large

In priority order, each self-contained and each preserving the F3 capability that justifies the
experiment:

- **N1 — drop the numpy reference forward.** Torch-only model; §12.1/12.2/12.4/12.5 then exercise the
  decoder with *fixed synthetic scores* instead of model outputs, and the model is untested locally
  until torch is installed. Saves ~200 lines; costs the local executability of the model path.
- **N2 — drop the learned head entirely.** Keep the exporter, the complete pool, the hypothesis
  generator, and the joint decoder, scoring edges with the parent's **own** `pool_prob` plus the three
  scalars (`τ`, `β`, `λ_div`). This tests the brief's actual bottleneck — joint reconsideration over a
  complete pool with occupied-daughter reclamation — with **zero learned parameters**, no training
  step, no overfitting surface, and no independence disclaimer. Given 411 labelled error sites, N2 is
  arguably the *better* science and it is ~40% of the work. **If forced to choose one, I would build
  N2 first and add the head only if N2 shows the mechanism moves the proxy.**
- **N3 — decoder restricted to reclamation only.** Only hypotheses that create a division by moving an
  occupied daughter; everything else frozen. Smallest possible change that still closes F3.

---

## 16. Rollback and stop conditions

**Rollback** is complete and requires no revert: `BIOHUB_EXP067_ENABLE=0` restores the parent stage
chain, and `exp_064`'s submission 56535761 at 0.953 stays the fallback. The three artifacts are
additive; the builder's strip-parity test (§12.7) proves the notebook returns to the parent
byte-for-byte.

**Stop immediately and report, without retrying, if:**

1. Run 0 or Run A shows `admitted` is empty or inconsistent with `cfg.threshold` — the pool premise
   (F1) is wrong and the whole design must be re-derived.
2. Run A's base `submission.csv` does not byte-reproduce `d52a5da2…` — the export patch is not inert.
3. The index↔node-id join is not bijective on any movie.
4. Any local test in §12 fails and the fix would require changing an invariant rather than a bug.
5. Held-out proxy Δ < +0.002, or any prefix regresses more than 0.001 (§2.1) — **falsified**; close
   exp_067, do not tune, do not sweep `τ`/`β`/`λ_div` for a pass.
6. `edges_fragmented` does not fall — the mechanism claim is unsupported regardless of the proxy.
7. Any visible model/GPU quota reaches 10% remaining, or a quota/timeout stop occurs — **no automatic
   retry** (brief §1).
8. The user's schedule makes Run A impossible before 2026-09-28 — then stop at the local artifact and
   say so.

Nothing in this document authorizes execution. Local development will be recorded in
`experiments/exp_067_temporal_joint_lineage/dev_log.md`; `STATE.json` and its rendered checkpoint are
**not** modified by this work.

---

## 17. What I am asking Codex to challenge

1. **§2.3 stage placement.** Is after the division-geometry filter and before prune-isolated the
   right point, or does putting the stage before `add_safe_divisions_postlink` give a better-defined
   node universe at the cost of the parent overwriting our decisions?
2. **§15 N2 vs the full v1.** Given 411 labelled error sites and 12 division events, is the learned
   head justified at all in the time available?
3. **§7.2 `τ` and `β` semantics.** Is a global log-odds threshold plus an incumbency bonus a sound
   baseline treatment, or does the metric's asymmetry (unmatched endpoints are free, over-prediction
   is penalised one-sidedly) demand something else?
4. **§F1.** The claim that `admitted` is the complete above-threshold pool rests on `use_ilp` leaving
   the greedy degree caps at `None`. Please verify independently.
5. **§9.2.** Is the label predicate's `NEGATIVE` clause a faithful restriction of cell 8:60-62, and
   does per-edge independent BCE genuinely avoid the daughter-mislabelling trap?
6. **§14.6.** Should `.venv` gain CPU torch + scipy, given the standing "numpy + tzdata, test-only"
   policy?
7. **§14.1.** Whether this experiment should be started at all four days from close, versus finishing
   `PLAN.md` Steps 3–5.
