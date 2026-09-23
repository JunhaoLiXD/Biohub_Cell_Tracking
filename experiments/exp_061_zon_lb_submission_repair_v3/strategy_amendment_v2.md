# exp061 zon deployment amendment v2 (consensus; admission pending)

Status: strategy consensus recorded; implementation candidate exists. Formal Codex admission, snapshot smoke, budget reservation, and launch remain pending. This record supersedes v1 as the active proposal without altering the immutable v1 history or v2 experiment.

## Parent, evidence, and hypothesis

Parent: `exp_061_zon_lb_submission_repair_v2`, built from the immutable upstream notebook SHA-256 `bb60ffe996a81bfaad7a3f8c53b1282d5772a68fb12536c58bfa24c483f16aae` and frozen harness SHA-256 `45d756b7585f171e4f590eec04be54277ef525c3b63790f04f025f7d0c548178`.

The v2 hidden rerun returned a generic unhandled-error message; Kaggle withheld its traceback. The visible v2 run's observed interval from push at 04:25:20Z to first COMPLETE check at 05:26Z bounds observed wall time at no more than 60m40s, not nearly two hours. Stage timings, peak memory, exact hidden workload size, and failure cause remain unavailable. A `(2/5) * 4 * 60m40s ~= 97m` estimate is an illustrative risk screen only: parent inference may dominate, public and hidden set sizes may differ, and no local GPU or hidden inputs are available. This does not prove timeout or hidden-run feasibility.

Hypothesis: removing the original-XY reference and `xyonly`/`xyd4` development replays from the scoring path reduces deployment work while retaining the frozen zon output policy for each current input. The hidden failure cause remains unknown, and a hidden rerun may still fail.

## Exact v3 change

The candidate notebook is `.private/exp061_lb_repair_v3/build/exp061_zon_submission_repair_v3.ipynb`, generated deterministically by `scripts/build_exp061_zon_submission_repair_v3.py` from the immutable parent. Parent cells 0-2 are byte-identical after stripping the experiment identity/watchdog metadata adapter; the complete parent inference cell SHA-256 is `9a341b5b1bafd80283c05041f23ea650bdce082b8ff26009bc0be69b98a20ac8`. `filter_output_graph` therefore remains bound by the unchanged parent inference cell.

New deployment module: `scripts/exp061_zon_deployment.py`, generated from the frozen v2 harness by `scripts/build_exp061_zon_deployment_module.py`. Only the zon arm is replayed. `_accept_wrapper` is AST-identical to v2 (SHA-256 `b82ca3b0a455ec3540ff4ce7b471a5fabd7971505656b656fb3930e60979a1c5`). `_exp061_heatmap_for_frame` adds only per-frame view-order telemetry; transform, aggregation, and policy remain unchanged. `_write_arm_submission` adds only `per_dataset` to the zon receipt; its CSV writing logic remains unchanged. The no-XY cross-arm development parity/mechanism tests are excluded from the deployment contract, not weakened into success claims.

The final notebook cell unlinks any pre-existing parent `submission.csv` before running zon. It fails closed unless integrity, full discovered-test-set completion, zon completion, no runner exception, accounted finite score calls, receipt status/dataset-set/hash, metrics hash, CSV schema/rows/IDs/field types, node/edge sentinels, unique graph IDs and edges, endpoint existence, adjacent-frame edges, degree constraints, and exact dataset set all pass. It stages the exact zon CSV, verifies its digest, and atomically replaces the target. No fallback parent CSV may survive a zon failure.

## Validation contract and observed local evidence

Run `python scripts/validate_exp061_zon_deployment_v3.py`. The passing suite covers: immutable parent-cell/source parity and zon-only executable AST; eight final-publication modes (success plus injected runner, integrity, dataset, receipt-set, digest, schema, and graph-adjacency failures); mocked zon execution with exact frozen 16-view order and accounted score receipts; an eight-dataset fixture (4x the normal two-dataset mock) proving complete discovery/traversal/receipts; valid zero-veto traversal over every discovered dataset; missing score rejection; and missing discovered input rejection. This is a deterministic correctness fixture, not a 4x timing or capacity proof. Its approximately 0.169s runtime and 32,768-byte mock view-cache footprint do not predict Kaggle runtime or peak memory. No local CSV hash parity with the v2 visible run is claimed; compare/audit actual visible-run zon CSV before any later publication or leaderboard action.

A first validator run exposed a v3 builder regression: it accidentally iterated the `arm_summaries` dictionary keys instead of `.values()` in the all-config-complete gate. The frozen v2 source used `.values()`. The builder was corrected with an exact anchored replacement, regenerated module SHA-256 `35aa6d61c543a891da5649ed48722938e10b4ca240a31d3c3e4360c3ccd39123`, rebuilt notebook SHA-256 `8efd5500fc80909928679d6dbc5e4361a28374ec214e57bf53cce0239f5cfaba8`, and the full validator then passed. The regression and correction are disclosed; they are not represented as inherited v2 behavior.

## Budget, stopping rule, and authorization

Reserve at most 2.0 GPU hours for one bounded Kaggle kernel run, retaining a hard two-hour watchdog and a 20-minute finalization reserve; do not weaken the watchdog. Maintain the 6-hour ledger floor. Record public-run elapsed/stage time, process peak RSS when supported, disk-cache bytes, and completed datasets as evidence, not as a hidden-size guarantee. Stop on any integrity failure, incomplete discovered dataset set, unaccounted score call, watchdog risk, or missing artifact; do not relaunch automatically. If execution has not completed at the single check, stop polling and wait for the user completion notice.

The user authorized rewriting and running the notebook once. This authorizes one bounded kernel run only after fresh experiment-specific Codex PASS, snapshot smoke, and sufficient budget reservation. It does not authorize an LB submission. No leaderboard submission is part of v3.

## Independent challenge and resolution

Initial proposal v1 incorrectly treated the visible run as approximately two hours and required a measured 4x profile before admission. Root reviewer challenged both the wall-time arithmetic and feasibility of a 4x profile without GPU/hidden data. Revised evidence uses the <=60m40s observed v2 interval, labels ~97m as illustrative only, removes an unachievable 4x performance prerequisite, and retains a 4x deterministic correctness fixture plus one bounded remote run as the feasibility measurement. The reviewer recorded `CONSENSUS` for this revised deployment-only proposal subject to fresh Codex admission, snapshot smoke, and budget gates. Residual hidden-input/runtime risk is explicit and accepted for the single user-authorized diagnostic run.

## Independent implementation review (not formal admission)

The root reviewer independently inspected the function-level diff and validator evidence and recorded `PASS` for the local candidate, conditional on formal experiment-specific Codex admission and snapshot smoke. This is a bounded implementation review, distinct from the fresh formal review required by `admission.require_codex_review`. It does not authorize launch by itself.
