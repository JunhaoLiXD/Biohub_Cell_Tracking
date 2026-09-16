# Strategy Proposal — exp_058: Self-trained / fine-tuned component with a controlled held-out split

Record type: versioned strategy proposal (post-pivot successor #2 — the aggressive
centerpiece; sequenced AFTER exp_057 establishes the strongest clean LB parent)
Status: **v0.3 — combined A+B design (user decision 2026-09-15: run Design A and
Design B together as complementary arms).** v0.1's core validation claim was
refuted by Codex #1 and is withdrawn (§1b). v0.3 makes A the clean-init validation
probe and B the deployable LB candidate, with A's clean held-out delta cross-checked
against B's actual LB delta to finally calibrate a trustworthy offline signal
(§1c). Sequenced after exp_057. No implementation, training, launch, or leaderboard
submission until a versioned `CONSENSUS` and a fresh Codex admission review.
Author: Claude Code. Date: 2026-09-15. Posture: deliberately **aggressive /
framework-changing** (late-stage posture, explicitly user-authorized).

## 0. The two problems this single bet attacks

1. **Model quality is the biggest untapped lever.** Every experiment so far has
   used *pretrained public* checkpoints and only edited inference/graph policy.
   Training is the one thing we have never touched, and division — the dominant
   remaining error term across all decompositions — is largely a *model* problem.
2. **Our offline validation is leaky.** The whole reason exp_055's +0.0149 proxy
   evaporated to 0.000 LB is that the public detectors trained on our 16 "held-out"
   videos. We cannot build a trustworthy offline signal on top of a base that saw
   everything.

Training our own component with a **controlled held-out split** attacks both at
once: it improves the model AND gives us an offline signal we can finally trust.

## 1. The key validation insight (why the split is trustworthy)

The public base checkpoints saw all training videos, so a naive held-out set is
still "seen" by the base. The trustworthy quantity is the **fine-tune marginal
delta on held-out videos**: hold out a set `H` of training videos, fine-tune ONLY
on `T = train \ H`, then measure (base) vs (fine-tuned) on `H`. Both models are
evaluated on `H`; the base's prior exposure to `H` is a constant that cancels in
the delta. A positive, stable delta on `H` therefore measures whether OUR fine-tune
*generalizes* to data our fine-tune never touched — the exact property the leaky
train16 proxy could not measure. This is the scientific core of exp_058.

## 1b. WITHDRAWN claim and the honest fork (Codex challenge #1)

Codex correctly refuted §1's central claim. The quantity
`score(finetune_T(W_all), H) − score(W_all, H)` does **not** make either model
independent of `H`, and the base's exposure to `H` does **not** cancel — it
interacts with representation learning, gradient trajectory, saturation,
checkpoint selection, and forgetting. So this delta is a **contamination-aware
paired diagnostic**, NOT an independent held-out generalization estimate, and
exp_058 does **not** "fix the validation leak." Additional confounds: T/H specimen
& acquisition correlation, tiny division counts, video-level dependence, T/H/test
distribution mismatch, and behavior shifts on neighboring domains. Early-stopping
on `H` (which v0.1 suggested) would turn `H` into a selection set and must be
removed. **§1 is withdrawn.**

A genuinely held-out estimate requires the evaluated component's supervised Biohub
training to exclude `H` from initialization onward. That yields two honest,
mutually exclusive designs — **the user chooses which before v1 is locked:**

* **Design A — clean-init held-out (real offline signal, more work/GPU):**
  reinitialize the evaluated component (or start from a generic pre-Biohub
  checkpoint), train on `T` only, and reserve `H` strictly for ONE final
  evaluation (a separate selection fold, never `H`, is used for early stopping).
  This gives a trustworthy offline held-out number but needs training-code surgery
  and more GPU, and it discards the strong public weights for that component.
* **Design B — contaminated paired diagnostic + LB-final (honest, cheap):**
  fine-tune the component from the public checkpoint, use the paired diagnostic on
  `H` only as a weak screen described honestly as contaminated, and treat the
  **Public LB as the sole held-out decision**. This keeps the strong public base
  but does NOT deliver a trustworthy offline signal — it leans on LB spend.

Real training-code constraints (verified in
`…/tracking_repo/scripts/train_unet_transformer.py`): it loads only the UNet with
`strict=False`, re-initializes the transformer and detection head, optimizes ALL
parameters, selects the checkpoint by `test_acc × test_recall` **on the evaluation
fold each epoch** (a selection-on-eval-fold leakage that must be replaced by a
proper train/select/final split), seeds only when a seed is passed, and has **no
DeepCenter/division training path**. Therefore the smallest defensible target is
the Transformer `pair_mlp`, strict-loaded from the complete public
`edge_predictor_best.pth` with the UNet, detection head, projection, and attention
blocks frozen — and even that is only division-adjacent and needs a preregistered
division-aware objective plus proof that enough division events exist. A
DeepCenter output-head fine-tune would align better but has no training
implementation or provenance in-repo. Every run must fit the **≤4-hour
per-experiment cap** (`max_single_experiment_hours = 4`); k-fold is not
presumptively affordable and needs a measured timing smoke.

The exact recipe (component, strict loading, frozen params, loss, split unit,
epochs/steps, LR, stop rule) is **frozen BEFORE observing exp_057's result** and before any result;
exp_057 only binds the final inference comparator afterward, not the training
recipe.

## 1c. Combined A+B design (v0.3) — probe + candidate + calibration

The user chose to run both arms; they are complementary, not redundant:

* **Arm A — clean-init validation probe.** Reinitialize the evaluated component
  (Transformer `pair_mlp`), train on `T = train \ H` only, hold `H` strictly for
  ONE final evaluation, and use a THIRD split `S` (⊂ `T`) for early stopping —
  never `H`. Report the clean held-out number on `H`. A is NOT deployed (a
  from-scratch component on less data will likely underperform the public
  checkpoint); A exists solely to produce a **trustworthy offline held-out
  measurement** of whether training this component on our data generalizes.
* **Arm B — deployable candidate.** Fine-tune the same `pair_mlp` FROM the public
  `edge_predictor_best.pth` (strict-loaded, rest frozen), the version we would
  actually submit. Its offline signal on `H` is contaminated (honest caveat); the
  **Public LB is B's only held-out decision**.
* **Calibration cross-check (the high-value output).** Compare Arm A's clean
  held-out delta against Arm B's actual Public LB delta. If A predicts B's LB
  direction, we obtain — for the first time — an **offline held-out signal
  validated against the leaderboard**, directly repairing the proxy-trust failure
  that produced the exp_055 miss. This makes exp_058 simultaneously a candidate
  experiment and a validation-methodology experiment.

Cost/complexity (stated honestly): two bounded trainings, each ≤4 h
(`max_single_experiment_hours = 4`); Arm A needs training-script surgery (a proper
train/select/final three-way split, component-only optimization, reinit, and
removal of the current select-on-eval-fold leakage). Both arms and their LB step go
through the full Codex-challenge / CONSENSUS / admission / per-submission
authorization workflow, sequenced after exp_057.

## 2. What to fine-tune (primary vs stretch)

* **Primary (budget-feasible, targets the dominant error):** the division-relevant
  head(s) — the DeepCenter division gate and/or the Transformer edge scorer's
  division-adjacent features — fine-tuned from the public checkpoint. Smaller,
  cheaper, and aimed straight at division, where the points are.
* **Stretch (higher reward, higher cost):** short fine-tune of the TemporalUNet3D
  detector for recall/precision. Only if the primary shows the split+budget works
  and GPU allows.

The exact component and layer scope are locked in v1 after Codex challenge; v0.1
commits to the *method* (fine-tune + held-out marginal delta), not yet the exact
tensor scope.

## 3. One falsifiable hypothesis (to be sharpened in v1)

> A bounded fine-tune of the division-relevant head on `T = train \ H`, starting
> from the public 0.944-pipeline checkpoint, produces a **positive, stable
> improvement on the held-out set `H`** (base→fine-tuned, measured on `H`) in the
> division-dominated score, and that held-out improvement **transfers to a Public
> LB score strictly above the exp_057/repro_048 parent**.

Falsifier: no positive held-out marginal delta (fine-tune does not generalize), OR
a positive held-out delta that fails to transfer to LB. Either closes the specific
fine-tune recipe (no blind hyperparameter sweep) and returns to the user.

## 4. Validation protocol (two gates, LB-final)

1. **Offline held-out marginal delta (trustworthy screen):** k-fold or single
   held-out `H` of the training videos; report base vs fine-tuned on `H` with the
   frozen competition scorer, division counts, and edge Jaccard. This is the new
   trustworthy offline signal and the *screen*.
2. **Leaderboard confirmation (decision):** if the held-out screen is positive, one
   authorized Public LB submission vs the parent. LB is the final arbiter.
   Cross-check: does the held-out delta predict the LB delta? (This directly
   rebuilds proxy-vs-LB trust.)

## 5. Budget and feasibility (to be tightened in v1)

* Training code exists in-repo (`tracking_repo/scripts/train_unet_transformer.py`);
  training data = the competition training videos + support pack. Full 50-epoch
  retrain of a detector from scratch is **out of budget** (~20.9 spendable GPU h,
  six protected). Therefore exp_058 is a **bounded fine-tune** (few epochs, small
  component), with a preregistered epoch/step cap, a wall-clock GPU cap, and
  fail-closed behavior — no open-ended training.
* Determinism: fixed seed, pinned environment, recorded training config hash, and a
  saved fine-tuned checkpoint with its own SHA for provenance.

## 6. Risks (the honest aggressive-bet risks)

* Fine-tuning from a strong public base may not beat it (catastrophic forgetting,
  overfit to `T`). Mitigation: the held-out marginal delta catches this before any
  LB spend; small LR / few steps; early-stop on `H`.
* Held-out `H` is small (few specimens/videos); the marginal delta can be noisy.
  Mitigation: k-fold over the split, report variance, treat as a screen not proof.
* GPU cost overrun. Mitigation: hard epoch/wall-clock caps, fail-closed.
* Reproducibility of training. Mitigation: pinned seed/env, config+checkpoint
  hashes, and a re-run determinism check on a tiny subset.
* Provenance/leakage: the fine-tune must never see `H` or any test movie; the split
  and its enforcement are hash-bound and audited.

## 7. Sequencing and dependencies

Runs AFTER exp_057. Parent = whichever of repro_048 (0.944) or exp_057 has the
higher Public LB. v1 (locking component/epochs/split) is authored after (a)
exp_057's LB result and (b) this v0.1 clears a Codex strategy challenge. Then:
implementation → fresh Codex admission review → held-out screen → LB confirmation.
No promotion, no automatic further submission.

---

**Status line:** v0.1 design outline authored; the method (bounded fine-tune +
held-out marginal delta + LB confirmation) is the aggressive centerpiece. Awaiting
Codex strategy challenge and exp_057's parent-setting result before v1 locks the
exact recipe. No training, implementation, launch, or submission authorized.
