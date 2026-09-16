# exp_055 bootstrap smoke repair

## Purpose and lineage

`exp_053_original_score_joint_repair` failed remotely because the isolated solver
self-test used `np` before import. `exp_054_original_score_joint_bootstrap_fix`
corrected the remote notebook, passed 14 tests, exact 16-graph parity and fresh
review, then stopped locally because the controller smoke interpreter lacks NumPy.

`exp_055_original_score_joint_bootstrap_smoke_fix` retains the exp_054 remote
notebook behavior. Its behavior parent remains
`repro_041_public_0941_motion_ema`; exp_053 and exp_054 are execution predecessors.
The validation protocol remains `public_0941_frozen_train16_stratified_proxy_v1`.

## Exact change

The remote notebook differs from exp_054 only in its injected experiment ID. The
admission validator no longer imports the embedded scientific stack. It extracts
the actual `import numpy as _jr_np`, solver call and assertion from the final
notebook, supplies minimal temporary NumPy and solver modules, and executes those
AST nodes in an otherwise clean namespace. This test fails if the explicit import
is absent or ordered after the solver call, while remaining executable under the
controller's dependency-minimal `.venv`.

Models, checkpoints, inference settings, EMA, smoothing, graph-repair policy and
parameters, fixtures, expected graph hashes, score rows, scorer and remote decision
gates remain unchanged.

## Admission

Require 14 focused tests, dependency-free controller smoke, exact parity for all
16 local graphs, normalized remote-notebook equivalence to exp_054, a fresh
experiment-specific Claude PASS, immutable snapshot verification and a two-hour
reservation while preserving six hours. One remote launch is authorized. No
leaderboard submission or promotion is authorized.
