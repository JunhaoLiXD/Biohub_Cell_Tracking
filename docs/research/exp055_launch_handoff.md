# exp_055 launch handoff

`exp_055_original_score_joint_bootstrap_smoke_fix` launched once at
2026-09-15T03:27:49Z as
`lingxd/biohub-exp055-original-score-bootstrap-smoke-fix`.

The behavior parent is `repro_041_public_0941_motion_ema`. `exp_053` is the
remote-failed predecessor whose solver self-test lacked a NumPy import. `exp_054`
corrected the remote notebook but terminated at local smoke because the controller
virtual environment lacks NumPy. exp_055 keeps exp_054 remote behavior except for
the injected experiment ID and uses a dependency-free clean-namespace admission
probe.

Fourteen tests, exact parity for all 16 local graphs, normalized remote-notebook
equivalence, fresh experiment-specific Claude `PASS`, and snapshot smoke passed.
Two GPU hours are reserved from 28 remaining hours while preserving six protected
hours.

Wait for the user completion notice, then check and collect once. Independently
audit all input/output graph hashes, per-video score rows, the solver receipt,
aggregate score, division counts and submission integrity. Do not poll, relaunch,
rebuild, request another Claude review, submit to the leaderboard or promote.
