# val_008 Error Analysis

## Outcome

The fixed, stratified 16-video validator passed every runtime and output-contract check. Its combined
score is `0.9252519786`, with adjusted edge Jaccard `0.9144411677` and division Jaccard
`0.1081081081`. This confirms that the earlier four-video score of `0.9381651742` was optimistic.

Per specimen, `44b6` scores `0.9036583712` and `6bba` scores `0.9329497723`. The validation set
realized the intended four division-positive and four division-negative videos for each specimen.

## Error structure

Across the 16 videos, division scoring contains 4 true positives, 17 false positives, and 8 false
negatives. Division-negative videos alone contribute 13 false positives. Wrong association edges are
rare; the larger edge losses are fragmentation and detection-related losses.

The worst combined-score videos are `6bba_55c70843` (`0.719761`), `44b6_1d530831` (`0.791706`),
`44b6_c50204e0` (`0.794031`), and `6bba_0c7fa718` (`0.801315`). The first and fourth have substantial
fragmentation and detection losses; `44b6_c50204e0` also has five false and two missed divisions.

## Next controlled test

The production test diagnostics show that `division_like_sources` equals `safe_divisions_added` for
all four test videos, so the safe-division post-link stage is the direct source of predicted division
events. The next experiment enables the frozen DeepCenter confirmation gate for those additions at
its existing threshold of `0.12`. This changes one runtime variable and keeps the models, proposals,
linking, validation sample, and metric contract fixed.

## DeepCenter veto result

`exp_011_train16_deepcenter_div_veto_envfix` was rejected with score `0.9161388023`, a paired delta
of `-0.0091131762`. It reduced predicted divisions to zero: division Jaccard fell from `0.1081081081`
to `0`, and both specimens regressed. Test diagnostics checked 1,867 candidate points at threshold
`0.12`, accepted only six, and produced no final safe divisions. The threshold is therefore severely
miscalibrated for this checkpoint and candidate stage.

The next step is diagnostic calibration, not another guessed threshold. The baseline output remains
ungated while candidate-level DeepCenter scores and distribution quantiles are recorded. A future
threshold experiment is admissible only if this diagnostic exactly reproduces the fixed baseline.

## Score calibration result

`diag_012_train16_deepcenter_score_calibration` passed every gate and reproduced the baseline and
both specimen metrics exactly. Offline alignment against its final submission found 290 retained
safe-division edges across the four test videos. Their DeepCenter scores have median `2.34e-7`, 95th
percentile `2.22e-5`, and maximum `0.0603`; consequently, the original `0.12` threshold cannot retain
any of them.

The notebook recorded validation scores before the divergence and cap checks, so the 6,675
validation audit records do not reveal which final edges caused division true positives or false
positives. The next diagnostic leaves all output unchanged and performs one-edge-at-a-time causal
ablation on retained validation safe-division edges. Threshold tuning remains blocked until those
labels demonstrate score separation.

## Causal calibration result

`diag_013_train16_deepcenter_causal_calibration` passed every contract gate and reproduced the fixed
baseline exactly. One-edge-at-a-time ablation covered 1,130 retained validation safe-division edges.
Four edges affected division TP, 25 affected division FP, and two affected both because division
matching is defined over connected components.

DeepCenter scalar confidence does not separate useful from harmful division edits. High-score
prediction gives AUROC `0.44` for the inclusive causal labels and `0.152` for mutually exclusive
TP-only versus FP-only edges. A threshold low enough to preserve all TP-impacting edges keeps 23 of
25 FP-impacting edges; a threshold above every FP-impacting edge keeps no TP-impacting edge. The
best in-sample Youden threshold retains only 2 of 4 TP-impacting edges while retaining 9 of 25
FP-impacting edges, and the positive sample is too small for threshold tuning in any case.

The scalar-veto branch is therefore closed. The next admissible division experiment is the v9
Phase-0 oracle: persist pre-ILP edge logits, ranks, and margins, enumerate candidate families A/B/C,
and measure the counterfactual score ceiling per specimen before training any classifier.

An offline join recovered geometry for all 1,130 causal records. On the mutually exclusive subset
(2 TP-only versus 23 FP-only edges), larger sister distance gives an apparent AUROC of `1.0` and the
existing geometric rank gives `0.804`. These figures are exploratory only: two positives are far too
few for threshold selection, and the preferred direction toward wider sister separation may reflect
the narrow post-filtered candidate range. Phase 0 should retain sister distance and divergence as
features, but it must expand the positive evidence with GT-derived A/B/C candidates and evaluate
per specimen rather than tune another rule on this subset.
