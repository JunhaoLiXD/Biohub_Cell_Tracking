## Summary

The pivot to `repro_048` as the leaderboard parent is justified, but neither proposal is CONSENSUS-ready.

- exp_057 is a reasonable, cheap leaderboard experiment, but its causal framing is too strong and its integration contract needs tightening.
- exp_058 has a fundamental validation error: exposure of `H` in the starting checkpoint does not cancel in the fine-tune delta. The proposed delta is useful as a paired diagnostic, not an independent held-out generalization estimate. Its training recipe is also presently infeasible as written.

## exp_057 assessment

The hypothesis is testable but weakly supported. It should be phrased as “EMA improves the complete repro_048 bundle,” not as composition of two independently verified mechanisms:

- `repro_041` improved the 0.941 lineage to displayed LB 0.942 and train16 by +0.002755, but its LB result is user-reported at only three-decimal precision.
- `repro_048` scored 0.944, but it is a full-source bundle; the +0.003 over the 0.941 reference cannot be attributed to edge-feature TTA alone. [repro048 analysis](E:/Project/Biohub_CellTracking/.private/research/repro048_completed_run_analysis_2026-09-08.md)
- In the matched no-EMA comparison, feature TTA reduced train16 by 0.004908; 82.47% of the loss was division-related. [exp_050 analysis](E:/Project/Biohub_CellTracking/.private/research/exp050_completed_analysis_2026-09-09.md)
- The complete 0.944 configuration scored 0.931070 versus EMA’s 0.938733 on train16, with division explaining 65.24% of the gap. [val_049 analysis](E:/Project/Biohub_CellTracking/.private/research/val049_completed_analysis_2026-09-09.md)

Those proxy findings do not prove antagonism on test—the proxy has now failed decisively—but they lower the prior for additive gain. This is a high-uncertainty composition probe, not the combination of two established causal improvements.

The EMA-off byte-parity gate is necessary but not alone sufficient. Motion relinking is implemented in the notebook’s postprocessing cell, not in `predict_unet_transformer.py` as the proposal claims. Clean attribution requires:

- one immutable repro_048-derived snapshot;
- normalized source diff restricted to the EMA state/update, telemetry, and required configuration plumbing;
- an off/on switch in that same snapshot;
- EMA-off canonical submission bytes exactly equal to `0319ba6d…`;
- identical materialized repository, checkpoint hashes, parameters, environment, ordering and postprocessing;
- canonical graph-difference counts plus EMA execution/update receipts for EMA-on.

Leaderboard-first validation is correct because train16 cannot adjudicate this change. One submission is defensible given repro_048’s low inference cost and the absence of a reliable offline alternative, but only after canonical graph differences are shown to be material, remote history is queried immediately beforehand, and the user explicitly authorizes it. A displayed 0.944 is operationally terminal but scientifically ambiguous: it cannot distinguish zero effect from a sub-0.001 improvement.

## exp_058 assessment

The core validation claim is invalid as stated. Let `W_all` be the public checkpoint trained with exposure to `H`. The proposed quantity is:

`score(fine_tune_T(W_all), H) − score(W_all, H)`.

This measures the incremental effect of a `T`-only update conditional on an `H`-contaminated initialization. It does not make either model independent of `H`, and the exposure does not generally cancel because it interacts with representation learning, gradient trajectory, saturation, checkpoint selection and forgetting. It may reveal whether the update preserves or improves performance on familiar-but-not-updated videos, but it does not “fix the validation leak.”

Further confounds include specimen/acquisition correlation between `T` and `H`, tiny division counts, video-level dependence, distribution mismatch between `T`, `H` and Kaggle test, behavior shifts on neighboring domains, and use of `H` for early stopping. The proposal explicitly suggests early stopping on `H`; that would turn `H` into a selection set and prohibit treating it as final evidence. K-fold reuse of the contaminated base does not remove this problem.

A genuinely held-out estimate requires the evaluated component’s supervised Biohub training path to exclude `H` from initialization onward—for example, reinitialize that component or start from a generic checkpoint predating Biohub labels, train on `T`, and reserve `H` strictly for one final evaluation. Otherwise the result must be labeled a contamination-aware paired screen, with LB remaining the only held-out decision.

Feasibility is unestablished. The ledger has 26.90 hours remaining, hence 20.90 spendable above the protected six, but the per-experiment cap is four hours. More importantly, the cited training script does not support the proposed fine-tune:

- it loads only optional UNet weights, with `strict=False`;
- it initializes the transformer and detection head anew;
- it optimizes all model parameters;
- it exposes no CLI seed;
- augmentation uses a fresh unseeded `np.random.default_rng()`;
- checkpoint selection evaluates every epoch on the test fold using `accuracy × recall`;
- it contains no DeepCenter training path or division-specific head/loss.

With the available code, the smallest defensible target is the transformer `pair_mlp`, strict-loaded from the complete public `edge_predictor_best.pth`, while freezing the UNet, detection head, projection and attention blocks. Even that is only division-adjacent and needs a preregistered division-aware objective and proof that enough division events exist. A DeepCenter output-head fine-tune would be more directly aligned, but no matching training implementation or provenance was found.

Sequencing exp_057 first is sensible for establishing the LB comparator. It should not determine exp_058’s split, component, loss, epochs or selection rule: those should be frozen before seeing exp_057. Only the final inference parent and comparison threshold need to be bound afterward. Because exp_057 changes postprocessing rather than training weights, it does not logically determine exp_058’s initialization recipe.

## Required changes

### exp_057

- Replace “two independently LB-verified gains” with accurate full-bundle, non-causal language.
- Correct the claimed integration location and specify the exact notebook-cell/function patch.
- Strengthen the off/on same-snapshot parity, normalized-diff, runtime-source-hash and canonical graph-diff contract.
- Predeclare that LB 0.944 is displayed-precision inconclusive but terminal for this recipe.
- Keep train16 diagnostic-only and preserve explicit submission authorization, remote-history, nonduplicate, budget and no-promotion gates.

### exp_058

- Withdraw the claim that base exposure to `H` cancels or that this design fixes leakage.
- Choose explicitly between:
  - a truly clean holdout with an `H`-unexposed component initialization; or
  - a contaminated paired diagnostic described honestly as such.
- Separate model-selection validation from a once-only untouched assessment set; never early-stop and report final performance on the same `H`.
- Lock one component, strict checkpoint loading, frozen parameters, loss, split unit, epochs/steps, LR and stop rule before results.
- Add a measured timing smoke and an explicit ≤4-hour experiment cap; k-fold is not presumptively affordable.
- Add full training determinism and provenance: Python/NumPy/Torch/worker seeds, deterministic-mode receipt or nondeterminism bounds, dataset and split manifests, base/config/code/environment hashes, optimizer and checkpoint receipts, and strict proof that no held-out or test movie entered training.
- Freeze the training recipe before exp_057; afterward bind only the winning inference comparator.
- Preserve all existing leakage, review, snapshot, budget, submission and promotion gates. The current early-stop-on-`H` language would relax the leakage gate and must be removed.

## Recommendation

Revise exp_057 narrowly; it can likely reach consensus quickly and proceed first after implementation review. Redesign exp_058’s validation foundation before calling it trustworthy or implementing training. Neither proposal authorizes implementation, training, launch, submission or promotion.

VERDICT: REVISE
