# exp061 zon deployment amendment v4 (implementation correction; admission pending)

This is a new immutable successor to the blocked, unlaunched v3 snapshot. Its actual prediction parent remains the completed v2 zon method. The user authorized one notebook run after all gates, not a leaderboard submission. The deployment strategy remains the Claude/Codex consensus recorded in `experiments/exp_061_zon_lb_submission_repair_v3/strategy_amendment_v2.md`, its v3 addendum, and the verbatim `claude-strategy-review.md`. No inference-policy or model change is proposed.

## Why v4 is necessary

The second formal v3 Codex admission returned BLOCK. Its substantive code finding was that `run_exp061_zon_deployment` disarmed the 2-hour watchdog before the final notebook cell audited and published the CSV. The reviewer also could not independently open source files because the Windows read-only command helper failed. Both v3 BLOCK receipts are archived as `admission_review_v1.md` and `admission_review_v2.md`; they remain evidence and are not PASS.

## Exact correction

`scripts/build_exp061_zon_submission_repair_v4.py` hash-locks the immutable v3 snapshot notebook (SHA-256 `8efd5500fc80909928679d6dbc5e4361a28374ec214e57bf53cce0239f5cfaba`) and deployment module (SHA-256 `35aa6d61c543a891da5649ed48722938e10b4ca240a31d3c3e4360c3ccd39123`). It copies parent cells 0-2 exactly. The v4 deployment module changes only experiment/protocol identity and removes the runner's `_disarm_watchdog()` call. The final cell retains the pre-existing zon digest, graph and dataset checks, then explicitly rejects a reached whole-notebook deadline before atomic replacement and disarms `SIGALRM` only after successful publication. The 20-minute finalization reserve and two-hour hard stop remain.

The v4 validator checks parent-cell equality, one zon loop, no runner disarm call, the order `deadline check -> atomic replace -> disarm`, and executes the full v3 fixture suite plus a deadline-expired publication negative. The local fixture is not a hidden-runtime proof. A genuine visible Kaggle run must be audited against the historical development zon SHA `2593a5438a17e5649736fcd6ad2f7af4c2fa8f822a759e9f51d877cdf6c840a1` before any later leaderboard decision. Exact hidden failure cause remains unknown.

## Budget and stop rule

One tracked run may reserve at most 2 GPU hours if fresh experiment-specific Codex admission returns PASS, snapshot smoke passes, and the six-hour reserve remains. The ledger still conservatively holds the completed v2 two-hour reservation; no silent release is assumed. On review BLOCK/REVISE, smoke failure, budget failure, missing artifact, or remote error, stop and do not relaunch. Do not repeatedly poll. No leaderboard submission is authorized.

## Strategy status

The reductive zon-only deployment strategy retains the explicit v3 Claude/Codex `CONSENSUS`. This v4 amendment is the precise implementation correction required by formal v3 review. Formal v4 admission and snapshot smoke remain pending. No reviewer finding has been overridden or represented as a PASS.
