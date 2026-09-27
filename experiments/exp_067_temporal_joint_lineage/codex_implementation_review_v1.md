# Codex implementation review v1

Date: 2026-09-26. Scope: local implementation of the agreed option 1 against the immutable exp064 parent. Decision: **LOCAL_IMPLEMENTATION_PASS; REMOTE_ADMISSION_NOT_REQUESTED**.

## Authorship and consensus

Claude Code authored proposal_v1.md and the core modules. Codex raised ten binding challenges; revision_acceptance_v2.md accepted them with explicit CONSENSUS before implementation. Claude's implementation invocation terminated with a 429 quota error, leaving notebook integration and tests incomplete. On the user's continuation instruction, Codex completed those parts and corrected reviewed defects. No automatic Claude retry occurred. Exact remaining weekly model allowance was unavailable.

## Corrections made during independent inspection

- Fixed NumPy temporary-file suffix handling and added complete serialized-array integrity hashes.
- Rejected mismatched movie/node/time identity, invalid probabilities, missing measured confidence and incompatible checkpoint features/normalizers.
- Preserved original node identity through a private token; explicitly classified the parent's otherwise unmarked gap2 synthetic nodes and `gapfill_peak` readmissions. Added fatal propagation outside the parent's permissive exception handler.
- Replayed the actual parent predictor patch chain, pinned its source SHA, and verified additive notebook edits can be reversed to the original cell texts.
- Preserved the exp067 runtime path in predictor subprocess environments; parent subprocess launch code previously overwrote it. Export mode skips TEST prediction/submission checks, uses explicit TRAIN stems, and disables the postprocessing sweep.
- Fixed the one-neighbor geometric-query shape and deterministic top-k tie handling.
- Used a sparse constraint matrix for MILP. Solver errors and invalid incumbents are tested against parent fallback. Actual constraint incidence separates frame transitions.
- Required positive and negative supervision for both heads. Checkpoints bind split/input hashes, frozen backbone provenance, feature/code versions and generation/window/model/objective configuration. Training rejects TEST exports and mixed backbone signatures.
- Bound decoded files to their exact parent graph hash; evaluation requires identical complete movie sets and uses the verbatim parent scorer.

## Executed evidence

Command: `.private/runtime/exp067_cpu/Scripts/python.exe -m pytest tests/test_exp067.py -q --basetemp .private/runtime/exp067_test03 --tb=short`

Result: **14 passed in 4.19 seconds**. Python 3.12; torch 2.14.0+cpu, scipy 1.18.1, numpy 2.5.3, pytest 9.1.1, PyYAML 6.0.3.

Coverage:

- Joint MILP reassigns an occupied daughter and selects the explicit correct fork on a constructed graph.
- Solver exceptions and fractional incumbents restore the parent's edge set.
- Unmatched sparse annotations have zero gradient; both true daughters are positives.
- Export/label round trips succeed and altered feature bytes are rejected.
- Movie overlap is rejected; incompatible inference configuration is rejected.
- Disabled bridge returns the original objects; parent-control edge identity is retained.
- Actual frozen parent patch chain replays; predictor and all control/export/decode notebook cells compile; duplicate patch application fails.
- Real CPU Transformer forward/backward training, checkpoint save/load, inference CLI and evaluation CLI complete on synthetic disjoint movie groups.
- Division-head daughter swapping produces exactly equal scores and its parameters receive gradients.
- Required endpoints split source groups correctly and overflow raises.
- Existing parent forks remain feasible and fixed boundary edges survive decoding.
- Measured feature/confidence hook receives realistic tensor shapes; export failures propagate as fatal.
- Every extracted scorer function matches the immutable parent's function text verbatim.

## Limits and remote admission prerequisites

This review does not establish real-data accuracy, an LB gain, GPU runtime, peak memory, full export equivalence or Kaggle dependency compatibility. CPU fixtures are synthetic and carry explicitly synthetic provenance. A learned checkpoint for competition data does not exist yet.

Before launch: freeze actual train/holdout stems and protocol, prepare compatible offline dependencies, estimate export/GPU/RAM cost, run a representative real-data export/feature smoke and disabled-output parity comparison, freeze the experiment snapshot, then obtain a fresh experiment-specific Codex PASS through the controller. Cooperative timeouts do not forcibly interrupt preprocessing/native calls; a controller walltime limit remains necessary. Frozen backbone pretraining overlap is unknown and must accompany proxy results.

No remote launch, leaderboard submission, GPU reservation, formal promotion or historical-record rewrite was performed. exp064 remains the incumbent.
