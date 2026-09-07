# val_008 Launch Note

## Status

`val_008_public_0933_train16_launchable` was submitted to the private Kaggle kernel
`lingxd/biohub-val-public-0933-train16-launchable` on 2026-09-01. The first status check returned
`RUNNING`.

## Purpose

Establish a broader frozen internal validation baseline for the reproduced team-fusion-v6 pipeline.
The protocol uses eight videos from each specimen and targets four division-positive and four
division-negative videos per specimen, with deterministic backfill if a stratum is scarce.

## Controls

- Only validation sample selection changed relative to `repro_005_public_0933_contract_id`.
- Inference parameters, model weights, graph construction, and post-processing remain frozen.
- The kernel is private, internet is disabled, and the requested accelerator is `NvidiaTeslaT4`.
- The notebook requires two compatible GPUs and validates exact sample counts and realized strata.
- The result is an optimistic train-derived internal baseline, not leaderboard or promotion evidence.

## Review and recovery history

`val_006` received the full methodology review. `val_007` implemented every requested auditability
change and received a confirmation PASS. Its immutable snapshot then failed staging because the new
experiment-ID guard contained a second literal controller placeholder. `val_008` changes only that
comparison to construct the sentinel from two string fragments, retains the `val_007` review as its
review reference, and passed 21 local tests plus the controller smoke test before launch.
