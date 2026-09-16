# exp_054 bootstrap repair

## Purpose

`exp_053_original_score_joint_repair` ended before inference because its isolated
solver self-test called `np.array` before NumPy was imported in the notebook global
namespace. The original-score policy received no remote quality evaluation.

## Experiment identity

- Experiment: `exp_054_original_score_joint_bootstrap_fix`
- Behavior parent: `repro_041_public_0941_motion_ema`
- Failed execution predecessor: `exp_053_original_score_joint_repair`
- Validation protocol: `public_0941_frozen_train16_stratified_proxy_v1`
- Budget: two GPU hours, with six hours protected

## Exact change

The isolated solver bootstrap now executes `import numpy as _jr_np` before its
2-by-2 assignment self-test and constructs the test matrix with `_jr_np.array`.
No model, checkpoint, inference option, EMA setting, graph-repair rule, repair
parameter, validation sample, scorer, expected graph hash, expected score row, or
decision gate changes.

The smoke test extracts the actual emitted NumPy import, solver call, and assertion
from the final notebook and executes them in a clean namespace using the embedded
repair module. This regression fails for the exp_053 ordering defect.

## Admission and decision

Before one remote launch, the successor must pass the focused tests, all 16 exact
local graph and score-row parity gates, a fresh experiment-specific Claude review,
snapshot smoke, immutable snapshot verification, and budget admission. The remote
contract still requires exact hashes and a proxy score of 0.9535869213120838 with
the preserved 4/8/8 division counts. No leaderboard submission or promotion is
authorized.
