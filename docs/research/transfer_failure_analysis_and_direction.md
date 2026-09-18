# Transfer-Failure Analysis and Lever Direction (Direction B)

Record type: versioned strategy analysis + direction memo (zero-GPU).
Status: **v1 — Claude-authored, awaiting Codex challenge.** No implementation,
launch, training, or leaderboard submission is authorized by this document.
Author: Claude Code. Date: 2026-09-17.
Parent evidence: `STATE.json`, `docs/research/PROJECT_HANDOFF.md`,
`docs/research/exp057_A0_edge_upper_bound_results.md`,
`docs/research/exp058_selftrain_heldout_proposal.md`.

Purpose: the project has produced two clean natural experiments showing that
train16 proxy gains do **not** transfer to the Public LB. Before spending another
GPU hour or a Codex round on the exp_058 division diagnostic (which is *measured on
train16*), this memo asks the prior question the project has been stepping around:
**why does nothing transfer, and what class of change could?** It is deliberately
diagnostic and direction-setting, not an experiment config.

---

## 1. The transfer ledger (every proxy→LB data point we have)

| Change | train16 proxy effect | Public LB effect | Transferred? |
| --- | --- | --- | --- |
| `repro_048` 0.944 bundle (edge-feature-TTA) | — (bundle, not isolated) | **0.944** (the real ceiling) | **YES** (model/inference-level) |
| exp_055 original-score joint repair | **+0.0149** (0.9536 vs 0.9387) | **0.942 == repro_041**, Δ0 | **NO** |
| exp_057 motion EMA on 0.944 | neutral (EMA-off replay byte-identical) | **0.944 == repro_048**, Δ0 | neutral→neutral (consistent, no info) |
| exp_050 feature-TTA off | **−0.0049** proxy | (not submitted in isolation) | proxy says TTA *helps* on train16 |

Two facts jump out:

- The **one change that reached 0.944 was model/inference-level** (the edge-feature
  + TTA bundle in `repro_048`). It was never a train16-tuned post-processing rule.
- The **one change with a large, clean train16 gain that we actually scored on the
  LB** (exp_055, +0.0149) delivered **exactly zero** LB movement. This is not noise
  around a small delta — it is a +1.5-point proxy gain vanishing to 0.000.

## 2. The mechanism — why train16 cannot predict the LB

Four independent pieces of evidence, all already in the repo, converge on the same
root cause. **train16 is not a held-out set at all**, and the specific gains we
found are in-sample artifacts of that.

1. **The base checkpoints saw all 16 "validation" videos.** This is stated plainly
   in `exp058_selftrain_heldout_proposal.md §0.2`: every experiment so far used
   *pretrained public* checkpoints, and those were trained on the competition
   training videos — i.e. on the same 16 videos the train16 proxy scores. A proxy
   computed on data the model already fit is an **optimistic training-fit measure**,
   not a generalization estimate. Any policy we tune to raise that proxy is tuning
   to the model's memorized fit, which the held-out test does not share.

2. **exp_055's gain was ~85% from a single specimen (6bba).** The train16 panel has
   only two specimens (`44b6`, `6bba`); 85% of the +0.0149 came from one of them
   (PROJECT_HANDOFF evidence table; STATE.json `exp058_build.specimen_metrics`). A
   gain concentrated in one specimen out of two is the textbook signature of an
   in-sample effect that will not survive a different specimen mix on the test set.

3. **The proxy scorer rewards behavior the test set punishes.** A0 Part 1
   (`exp057_A0_edge_upper_bound_results.md`) found the node-count adjustment
   *rewards under-prediction* (forcing perfect node count costs **−0.007**), and the
   biggest train16 edge lever — fragmentation reconnection — is **exactly what
   exp_055 targeted and it was LB-flat**. So the proxy's top-ranked lever has a
   *demonstrated* transfer failure. Optimizing the proxy optimizes a scoring quirk,
   not test-set quality.

4. **What transferred was distribution-general; what failed was train16-fitted.**
   The 0.944 bundle changes the model's features/TTA — a change whose benefit does
   not depend on which specimens are scored. exp_055's joint repair is a post-hoc
   graph surgery whose thresholds/actions were selected against train16 outcomes.
   The two outcomes (transfer / no-transfer) line up perfectly with this split.

## 3. The transfer boundary, stated as a falsifiable rule

> **A change transfers to the held-out LB only if it is distribution-general — a
> model/representation/TTA-level change whose benefit does not depend on train16's
> specimen mix or on any threshold/action fitted to train16 outcomes. Post-hoc
> graph-policy changes calibrated against the train16 proxy do not transfer.**

Falsifier: a distribution-general change that fails on LB, or a train16-calibrated
post-processing change that clearly transfers (Δ above LB rounding). We have zero of
the latter and one strong confirmation of the former (repro_048). Either observation
would revise this rule; until then it should govern lever selection.

## 4. Consequence — the two honest families of next move

**We cannot manufacture a trustworthy offline signal out of train16** (the base saw
it; §2.1). Only two families of work respect the transfer boundary:

- **Family 1 — build a genuinely held-out signal by clean-init training.** Hold out
  a set `H` of training videos, train the evaluated component **from a pre-Biohub /
  reinitialized state on `T = train \ H` only**, and reserve `H` for one final
  evaluation. Because that component never saw `H`, its delta on `H` is a real
  generalization estimate — the property the train16 proxy structurally cannot
  provide. This is **Arm A of the existing `exp058_selftrain_heldout_proposal.md`**,
  and it is the only route to a trustworthy offline number. Cost: training-code
  surgery (a proper train/select/final three-way split; the current script selects
  the checkpoint *on the eval fold* — a leak that must be removed) + bounded GPU
  within the 4-h/experiment cap.

- **Family 2 — pursue only distribution-general changes, validated directly on the
  LB.** No train16 calibration; changes justified by model/representation/TTA
  first-principles, each submission pre-registering the single hypothesis it tests.
  Cost: leans entirely on LB spend (3 submissions/day), and the LB is coarse
  (0.001 resolution) — so this family must not become a blind LB sweep, or the LB
  itself degrades into a calibration set.

## 5. Recommendation

**Revive and re-scope the self-trained held-out direction (Family 1 / the existing
`exp058_selftrain` proposal), and shelve the exp_058 division diagnostic.** Reasons:

- The diagnostic measures *where* division fails **on train16** — but §2 shows any
  train16 measurement is an in-sample fit, so even a perfect diagnostic result
  cannot tell us what fails on the held-out test. Its confirmed cost (a substantial
  second analysis rewrite + another Codex admission round + ~1.3 GPU h) buys
  information already discounted by the transfer gap.
- The self-train held-out direction attacks the actual bottleneck named by every
  piece of §2 evidence — the absence of a held-out signal — and simultaneously
  touches model quality (division is largely a *model* problem, per A0 Part 1's
  +0.05–0.085 division headroom vs an already-flat edge layer).
- It fits budget: bounded fine-tune/clean-init component training within the 4-h
  cap; 26.49 GPU h remain with 6 protected.

Honest caveat carried forward from that proposal's Codex challenge #1 (§1b): the
*contaminated paired diagnostic* (fine-tune from public weights, measure on `H`) is
**not** an independent held-out estimate — only the clean-init Arm A is. So the
re-scope must lead with Arm A (clean-init, `H` reserved for one final eval, a third
split `S ⊂ T` for early stopping), not with a fine-tune-from-public shortcut.

## 6. Concrete next step (zero-GPU, Claude authoring)

1. Promote `exp058_selftrain_heldout_proposal.md` from v0.3 to a **locked v1**:
   fix the exact component (smallest defensible = Transformer `pair_mlp`,
   strict-loaded from `edge_predictor_best.pth`, rest frozen — per its §1b repo
   audit), the clean-init recipe, the T/S/H split as a hash-bound, specimen-aware,
   leakage-audited partition, the epoch/step and wall-clock caps, the frozen
   division-aware objective, and the single falsifiable held-out→LB hypothesis.
2. Add a **split-feasibility check**: with only two train16 specimens visible in
   proxy panels, confirm how many *distinct specimens/videos* the full training set
   actually contains, and that `H` can be specimen-disjoint from `T` (otherwise the
   held-out estimate inherits the same single-specimen fragility as §2.2). This is
   a hard go/no-go gate authored before any GPU.
3. Hand v1 to Codex as a **strategy challenge** (not yet admission). Revise to a
   recorded `CONSENSUS`. Only then: implementation → fresh Codex admission `PASS` →
   snapshot smoke → budget reservation → bounded run. No LB submission without a
   positive clean held-out screen and explicit per-submission user authorization.

## 7. What this memo does NOT authorize

No training, no implementation, no launch, no LB submission, no promotion, and no
change to the standing exp_058 diagnostic gate state (it remains BLOCK #2; this
memo recommends shelving it, which is a user decision, not an automatic action).
The frozen train16 proxy remains diagnostic-only and, per §2, must never again be
used to *decide* quality or select a policy threshold.

## 8. For Codex to challenge

- Is the §3 transfer-boundary rule over-fitted to two data points? What cheap
  observation would most sharply test it?
- Is the §2.1 "base saw H, delta doesn't cancel" reasoning (from selftrain §1b)
  correctly applied to conclude clean-init is the *only* trustworthy route, or is
  there a lighter-weight held-out construction that survives?
- Split feasibility: is a specimen-disjoint `T/S/H` partition achievable within the
  training set at a size where the held-out delta is not dominated by the same
  single-specimen noise that discredited train16?
- Is shelving the division diagnostic the right call, or is there a *specimen-count-
  robust* division signal worth extracting from it cheaply before shelving?
