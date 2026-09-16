# Strategy Proposal — exp_057: Compose 0.944 edge-feature-TTA bundle + motion EMA α0.4

Record type: versioned strategy proposal (post-pivot successor #1 of a sequenced pair ①→②)
Status: **v4 (Codex challenge #3 = REVISE, one narrow spec point; §3.2 now names the
`velocity_um` state and the exact source→target EMA propagation
`velocity_um[target_id] = α·step_velocity + (1−α)·velocity_um.get(source_id)`,
the `motion_relink_ema_predictions` / `motion_relink_one_frame_fallbacks` counters,
matching the repro_041 reference line-for-line)** — awaiting a fresh Codex challenge
toward `CONSENSUS`. No implementation, launch, or leaderboard submission until
`CONSENSUS` and a fresh Codex admission review of the implementation.
Author: Claude Code. Date: 2026-09-15.

## 0. Why the pivot (context)

exp_055's original-score joint repair scored a huge +0.01485 frozen train16 proxy
gain but **0.000 Public LB** (0.942 == repro_041). The frozen train16 proxy is
leaky (the public detectors trained on those 16 videos) and does not predict LB
for post-smoothing graph edits. Decision: migrate the research parent to the only
measured pipeline that beats repro_041 on the real leaderboard — the public
**edge-feature-TTA bundle, `repro_048`, Public LB 0.944** — and validate future
work by the leaderboard, not the discredited proxy.

## 1. The change and its (honest, non-causal) prior

* `repro_048` (0.944) is a **full-source public bundle**: dual TemporalUNet3D
  (primary + secondary seed) + Transformer edge scorer + global SCIP ILP +
  DeepCenter division gates, with **edge-feature TTA ON and motion EMA ABSENT**.
  Public LB 0.944, submission `56105868`, output byte-identical to the public
  notebook. The +0.003 over the 0.941 reference is **not** attributable to any one
  bundled change (edge-feature TTA alone is not isolated); 0.944 is an integrity
  anchor, not a causal decomposition. Advertised 0.946 is not reproduced.
* Motion EMA α0.4 (velocity weight 0.5) replaces the one-frame motion-relink
  velocity with a per-track EMA. On the **0.941 lineage** it lifted
  repro_038→repro_041 to displayed Public LB **0.942** (+0.001, user-reported at
  3-decimal precision) and +0.00276 train16.

Honest prior (Codex #1): these were developed on **different lineages** and never
combined; the 0.944 bundle lacks EMA, the EMA result is on a weaker line. The
matched no-EMA proxy work (exp_050) even found feature-TTA *reduced* train16 by
0.0049 with 82% division-related, and the full 0.944 source scored 0.9311 train16
(val_049). The train16 proxy has now failed decisively (exp_055), so those proxy
findings neither prove nor disprove additivity on test — but they **lower the
prior** for an additive gain. exp_057 is therefore a **high-uncertainty
composition probe**, not the summation of two established causal improvements.

## 2. One falsifiable hypothesis

> Adding motion EMA α0.4 (velocity weight 0.5) to the otherwise byte-identical
> **complete repro_048 bundle** yields a Public LB score **strictly greater than
> 0.944** — i.e. EMA improves the full 0.944 pipeline rather than being redundant
> with, or antagonistic to, its bundled edge-feature TTA.

Falsifier: Public LB `<= 0.944` means EMA does not improve this bundle (redundant
or antagonistic); record it and do not sweep α — return to the sequenced ②
(self-trained model) as the primary aggressive bet. Because 0.944→0.945 is one
displayed step, a displayed `0.944` is **operationally terminal for this recipe
but scientifically inconclusive** (it cannot separate a zero effect from a
sub-0.001 improvement); it is reported as such.

## 3. Exact change (scope-locked)

1. Parent = `repro_048` executed source (SHA256
   `4eda3c3dae83f5ad21fee35513aad5f325e09b6de8f77fa55d9b7d6d4b50ca16`), unchanged
   except the single motion-EMA relink edit.
2. **Correct integration location (Codex #1, #2):** motion relinking is
   **notebook-level postprocessing** — the function `motion_relink_edges` defined
   directly in the repro_048 notebook (`public_0946_edge_feature_tta_copy.ipynb`).
   It is NOT in `predict_unet_transformer.py`, and `_patch_text` (which edits
   `scripts/predict_unet_transformer.py` for TTA/association) does NOT inject the
   relink function. exp_057 therefore modifies `motion_relink_edges` **directly in
   the notebook**. The exact edit, at the velocity term inside `motion_relink_edges`
   (currently `prev_pos = predecessor_position_um.get(source_id)`; if `prev_pos is
   None` then `predicted = source_pos`; else `predicted = source_pos +
   MOTION_RELINK_VELOCITY_WEIGHT * (source_pos - prev_pos)`):
   * add a per-node velocity-EMA state dict `velocity_um: dict[int, np.ndarray]`
     (exactly the repro_041 reference in `.private/current/motion_ema_repro_train16.ipynb`);
   * **prediction:** `velocity = velocity_um.get(source_id)`; if `velocity is not
     None` → `predicted = source_pos + MOTION_RELINK_VELOCITY_WEIGHT · velocity`
     and increment `stats["motion_relink_ema_predictions"]`; elif `prev_pos is
     None` → `predicted = source_pos` (unchanged fallback); else →
     `predicted = source_pos + MOTION_RELINK_VELOCITY_WEIGHT · (source_pos −
     prev_pos)` and increment `stats["motion_relink_one_frame_fallbacks"]`;
   * **source→target propagation after each accepted match:**
     `step_velocity = position_um[target_id] − position_um[source_id]`;
     `previous_velocity = velocity_um.get(source_id)`;
     `velocity_um[target_id] = step_velocity if previous_velocity is None else
     MOTION_RELINK_EMA_ALPHA · step_velocity + (1 − MOTION_RELINK_EMA_ALPHA) ·
     previous_velocity`, with `MOTION_RELINK_EMA_ALPHA =
     BIOHUB_MOTION_RELINK_EMA_ALPHA = 0.4`;
   * `MOTION_RELINK_VELOCITY_WEIGHT` stays 0.5 and every other relink parameter
     (`TIGHT_UM` 6.0, `RELAXED_UM` 10.0, `LEARNED_BONUS` 1.0, `MAX_FRAME_NODES`
     2600) is left at its repro_048 value;
   * **off-switch semantics:** when `BIOHUB_MOTION_RELINK_EMA_ALPHA` is unset/empty,
     the `velocity_um` state is never populated, so every prediction takes the
     original one-frame path (`velocity is None`) and the code is byte-identical to
     repro_048;
   * telemetry counters `motion_relink_ema_predictions` and
     `motion_relink_one_frame_fallbacks` are added to `stats` / run stats.
   The implementation names the function, the added `velocity_um` state, the exact
   prediction/propagation/fallback lines, the env var, and the two counters, diffed
   line-for-line vs repro_048.
3. All three checkpoints (primary seed, secondary seed, DeepCenter epoch-2
   `best.pt` `8040999a…`) stay frozen and hash-identity-checked exactly as
   repro_048. Edge-feature TTA stays ON. Dual-T4, no internet, no pip install.
4. Prediction-only; no retraining; ground-truth-free; no specimen/video identity.

## 4. Validation — leaderboard-first (the proxy is discredited)

* Primary readout: **one authorized Public LB submission** of the exp_057 test
  output, compared to repro_048's 0.944 (same 4 test movies, same metric). This is
  the trustworthy signal; the go/no-go is the LB delta.
* Secondary (diagnostic only, NOT the decision): run the frozen train16 stratified
  proxy as well, purely to keep accumulating proxy-vs-LB calibration data after the
  exp_055 miss. A train16 number never overrides or substitutes for the LB.
* Integrity contract (strengthened per Codex #1) — a single-variable change proven
  by construction, not asserted:
  * one immutable repro_048-derived snapshot carrying an EMA **off/on switch** in
    that same snapshot;
  * a normalized source diff restricted to the EMA state/update, its telemetry, and
    the minimal config plumbing; runtime-source-hash receipt;
  * **EMA-off must reproduce repro_048's canonical submission bytes exactly**
    (`0319ba6d8e864335d3573f6b1a6227c546f17e9247a0c2858fa09b6c2422db3f`), with
    identical materialized repository, checkpoint hashes, parameters, environment,
    ordering, and postprocessing;
  * EMA-on: submission graph covers all four test movies, max indegree 1 / max
    outdegree 2, no dangling/duplicate edges; a new non-duplicate submission SHA
    stable before/after; **numerical canonical-diff admission gate (Codex #3):**
    after a normalized canonical graph comparison of EMA-on vs EMA-off, require at
    least **one canonical edge addition or removal** (`|added ∪ removed| ≥ 1`) —
    a deterministic rule, not "material/non-trivial" — so a null EMA (identical
    bytes) cannot be silently submitted as if it were a test of the change; plus
    motion-EMA execution/update receipts proving the EMA relink actually ran on the
    test movies.

## 5. Budget, gates, rollback

* Budget: one bounded Kaggle inference run (repro_048 ran 0.357 GPU h; reserve
  1.0 h), from 20.9 spendable GPU h, six protected preserved. One leaderboard
  submission from the 3/day cap, gated by `gate_submission` (remote-history check +
  non-duplicate SHA), user-authorized.
* Admission (before launch): fresh Codex challenge to `CONSENSUS`,
  `admission.require_codex_review: true` + fresh Codex admission review of the
  implementation via `scripts/request_codex_review.py`, snapshot smoke, tracked
  reservation, controller gates.
* Rollback/stop: exp_057 is a one-line inference edit fully reversible to
  repro_048. LB `<= 0.944` → terminal, no α sweep; proceed to ②.

## 6. Risks

* **Integration risk:** the 0.944 (edge-feature-TTA) notebook and the repro_041
  (EMA) notebook are different sources; the motion-relink hook must exist and be
  bound identically in the 0.944 pipeline. Mitigation: both derive from the same
  `tracking_repo predict_unet_transformer.py`; the port must be a byte-level diff of
  the relink stage only, proven by an effective-config receipt, and a with-EMA-off
  build must reproduce repro_048 byte-for-byte before enabling EMA.
* **Non-additivity:** edge-feature TTA may already capture what EMA fixed, making
  the gain redundant (LB flat). That is exactly what the hypothesis tests; a flat
  result is informative, not a failure.
* **Display granularity:** 0.944→0.945 is one displayed step; a real but sub-0.001
  gain could round to 0.944. The result is read at 3-decimal LB precision and
  reported honestly as such.

## 7. Sequenced follow-on

On any exp_057 outcome, the aggressive centerpiece is exp_058 (self-trained /
fine-tuned model with a controlled held-out split; see
`docs/research/exp058_selftrain_heldout_proposal.md`). exp_057 first anchors the
strongest clean LB parent; exp_058 then attacks model quality AND fixes the
validation leak. No promotion or further submission is implied.

---

## 8. CONSENSUS

**Strategy CONSENSUS reached 2026-09-15.** exp_057 went through four independent
Codex challenges (`docs/research/exp057_058_codex_challenge_v1.md`,
`exp057_codex_challenge_v2.md`, `_v3.md`, `_v4.md`); v4 returned **VERDICT: PASS**
with no remaining material defect. Claude authored, Codex challenged, Claude revised
(v1→v4): non-causal full-bundle framing; correct direct notebook-level edit of
`motion_relink_edges`; the exact `velocity_um` EMA state / source→target
propagation / prediction / one-frame-fallback / off-switch matching the repro_041
reference line-for-line; and a deterministic canonical-diff admission gate
`|added ∪ removed| ≥ 1` plus EMA-off byte-parity to `0319ba6d…`. This record is
`CONSENSUS`.

CONSENSUS authorizes proceeding to **implementation only**. It does NOT authorize
launch or submission: the implementation still requires a fresh Codex admission
review of the actual code, snapshot smoke, a tracked GPU reservation, and
**explicit user authorization for the single Public LB submission**.

**Status line:** v4, strategy `CONSENSUS`. Next: implement exp_057 (notebook patch +
EMA-off byte-parity harness + tests), then fresh Codex admission review → smoke →
reservation → user-authorized single LB submission.
