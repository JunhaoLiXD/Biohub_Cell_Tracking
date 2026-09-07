# Reproduction Gate Result and Error Analysis

## Outcome

`repro_005_public_0933_contract_id` passed the controlled reproduction gate with a primary proxy score of `0.9381651742`, adjusted edge Jaccard of `0.9214985075`, and division Jaccard of `0.1666666667`.

Two independent T4 x2 runs produced the same submission SHA256 (`4f5caf08a4027aee7210a81b5936cea847d38aa9867ef284fa7e9c763da6b15c`) and identical normalized metrics. The reproduction is therefore deterministic under the current environment. This is not leaderboard evidence and does not promote the candidate over the frozen 0.912 baseline.

## Specimen results

| Specimen | Primary metric | Adjusted edge Jaccard | Division Jaccard |
|---|---:|---:|---:|
| `44b6` | 0.902806 | 0.902806 | 0.000000 |
| `6bba` | 0.971336 | 0.938003 | 0.333333 |

The cross-specimen gap is too large to treat the four-video aggregate as sufficient optimization evidence.

## Per-video diagnosis

- `44b6_12dfb391` has strong adjusted edge performance (`0.935339`) but misses its division and emits one false division.
- `44b6_267148e4` is the weakest `44b6` sample (`0.816999`). Its predicted node count is about 10 percent above the estimated true count, and fragmentation dominates detection loss.
- `6bba_062c8d37` is nearly saturated (`0.983264` adjusted edge, perfect observed division recovery).
- `6bba_07e24132` is much weaker (`0.826696`), with 27 edges lost to detection and two missed divisions.
- The diagnostic reports zero wrong-association edges on all four samples. On this small sample, the next likely lever is detection calibration and fragmentation rather than another global association change.

## Recommended next gate

Before changing the model or linker, establish a broader frozen baseline using eight validation videos per specimen (`16` total) under the same T4 x2 pipeline. Report division-containing and non-division videos separately. This protocol change requires an explicit review and must become the parent for later detection-calibration or fragmentation ablations.

No leaderboard submission or baseline promotion should occur automatically.
