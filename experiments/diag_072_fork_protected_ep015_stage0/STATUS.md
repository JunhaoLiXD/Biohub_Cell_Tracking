# diag_072 Stage 0 status — terminal failure

Date: 2026-09-28T14:00Z

## Terminal result

Kaggle version 1 ended in `ERROR`. The exact eight held-out stems were selected,
but the mounted exp065 cache failed the frozen key/stem contract. The notebook
stopped at the pre-registered fail-closed assertion `diag072: frozen cache
invalid; inference fallback prohibited`. No primary receipt was produced, so the
immutable adjudicator was not run. No leaderboard submission was made; the
downloaded `submission.csv` is the base TEST output written before the failure
and is not a fork-protected candidate.

Approximate runtime from the final Kaggle log timestamp is 1170.133 seconds
(0.325037 GPU hours). The reservation has been released. Do not relaunch without
a new experiment package, fresh review, budget reservation, and user approval.

## Completed

- Recovered all eight held-out raw prediction GEFF graphs from the immutable
  `exp_065_metric_aligned_pruning` Kaggle output.
- Recovered all 168 files composing the corresponding eight ground-truth GEFF
  graphs directly from the competition API.
- Installed the pinned GEFF/Zarr/Polars reader dependencies locally.
- Confirmed the authoritative held-out stems against `validator_results.csv`.

## Exact-execution boundary

The exp065 output did not preserve the eight graphs after base post-processing.
It preserved only raw validator predictions and aggregate/per-sample scores.
`filter_weak_edges` runs after motion relinking, gap recovery, safe-division
insertion and DeepCenter-dependent processing. The primary policy protects forks
defined immediately before that weak-edge filter. Applying the policy directly
to raw prediction graphs would therefore protect a different set of forks and
would not test the pre-registered hypothesis.

An exact diagnostic must replay the frozen base post-processing once on the raw
cache, then score base, flat ep015 and fork-protected ep015 from the same replay.
That replay needs the competition TRAIN image data and attached DeepCenter model.
It can be implemented as a cache-only Kaggle diagnostic with no detector or
training pass, but it is still a new remote experimental launch and requires its
own card, immutable snapshot, smoke test, budget ruling and admission PASS.

No approximate score was produced, no GPU was consumed, and no leaderboard
submission was made.
