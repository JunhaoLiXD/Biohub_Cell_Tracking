# exp061 zon deployment amendment v5 (deployment-scale correction; admission waived once)

This is a new immutable successor to the launched v4 snapshot. Its prediction parent remains the
completed v2/v4 zon method. The deployment strategy remains the Claude/Codex consensus recorded in
`experiments/exp_061_zon_lb_submission_repair_v3/strategy_amendment_v2.md`, its v3 addendum, and the
verbatim `claude-strategy-review.md`. No inference-policy or model change is proposed.

## Why v5 exists

The v4 kernel ran COMPLETE in 32.5 minutes and its output was audited read-only: the current-run zon
CSV reproduces the historical development hash `2593a543...` exactly, `config_equal_frozen_parent` is
true, checkpoint provenance is verified, 16 views per frame including 8 Z-reflected executed, and
there are no nonfinite or cache-integrity events. On that audit the user authorized one Public LB
submission, `56481730`. v5 is a prepared fallback in case that submission fails the way v2 did.

The audit found no defect that could produce a wrong score, but two limits that scale with the
hidden dataset and would abort the rerun rather than mis-score it. Both are fixed here.

## Exact corrections

`scripts/build_exp061_zon_submission_repair_v5.py` hash-locks the immutable v4 snapshot notebook
(SHA-256 `39eba1b92c79739b324009a274336672fa098e8f11c4edf1e16c16da6be08290`) and deployment module
(SHA-256 `74e3529856694130bf5990b8796db21d9c730b8bcc5f7d09a2fc219f4e23efb8`), copies parent cells
0-1 byte-for-byte, and makes three bounded edits confined to `# exp061`-marked lines.

**Fix #1, rerun-aware deadline.** v4 armed a hardcoded `signal.alarm(7200)` whose handler raises
`KeyboardInterrupt`. A visible run is billed to our 2.0-hour GPU reservation and keeps that ceiling,
but the hidden scoring rerun is not billed to that ledger and may legitimately be slower on a larger
hidden dataset. v5 keeps 7200s on a visible run and uses 30600s (8.5h, under the platform ceiling)
when Kaggle sets `KAGGLE_IS_COMPETITION_RERUN`, with `BIOHUB_EXP061_HARD_STOP_SECONDS` as an explicit
override. Cell 2 and the deployment module derive the value from the same environment, and the final
cell refuses to publish if the two ever disagree. The 20-minute finalization reserve is unchanged.

**Fix #2, view cache off the collected output path.** v4 wrote the disk-backed view cache to
`WORKING_DIR/exp061_viewcache`. Everything under `/kaggle/working` is collected as kernel output and
charged against that 20 GB budget; the cache measured 4272 files / 4.48 GB on the public four-movie
workload, so it scales straight into the cap on a larger hidden rerun, and it is why the v4 output
was roughly 4.5 GB. v5 selects a scratch root that Kaggle does not collect, trying an explicit
override, then `/kaggle/temp`, then the platform temp directory, and finally falling back to
`WORKING_DIR` so a run still completes if nothing else is writable. That fallback is reported in
telemetry but deliberately does not fail the integrity gate: a correct submission must never be
withheld for a non-correctness reason.

Neither change can alter a predicted node or edge. The same views are computed, cached and
accumulated in the same left-to-right order; only the cache location and the time ceiling differ.

## What v5 does not establish

The v2 and v4 hidden tracebacks are unavailable, so the scale hypothesis remains unproven. v5
removes two specific ways a rerun can abort; it does not demonstrate that either one caused the v2
failure, and a third unknown cause may remain. A genuine visible Kaggle run must still be audited
against the historical development zon SHA `2593a5438a17e5649736fcd6ad2f7af4c2fa8f822a759e9f51d877cdf6c840a1`
before any leaderboard decision.

## Validation

`scripts/validate_exp061_zon_deployment_v5.py` retains every v4 check (immutable parent cells, a
single zon arm, no runner-side watchdog disarm, the order deadline-check then atomic-replace then
disarm, and the full fail-closed publication suite) and adds executable coverage of both fixes: the
cell-2 arming block and the module deadline helper are run under `KAGGLE_IS_COMPETITION_RERUN`
on/off/garbage plus an explicit override and must agree on every case; the scratch-root selector is
exercised for override, fallback and an unusable override; a mocked end-to-end run must leave no
view cache under `WORKING_DIR`; and a new negative case proves publication is refused when the
module deadline disagrees with the armed watchdog.

One finding came out of writing those tests: the deadline-consistency guard was initially placed
before the adapter unlinks the parent's own `submission.csv`, so a mismatch would have left the
parent 0.947 artifact on disk to be scored silently. The guard now runs after the unlink, and the
validator asserts that ordering.

## Budget and stop rule

One tracked run reserves 2 GPU hours, preserving the six protected hours. On smoke failure, budget
failure, missing artifact or remote error, stop and do not relaunch. Do not repeatedly poll. No
leaderboard submission is authorized by this amendment.

## Governance status

The user asked for this corrected version to be built and pushed immediately as a fallback. That is
a one-time user waiver of the Codex admission gate for this bounded deployment fix, recorded as
`NO_PASS`, exactly as the v4 kernel run was. It is not a Codex PASS, and no reviewer finding has
been overridden or represented as one. The v4 open items #2-#6 (config completeness including
short-track rescue, fail-fast, partial-run gate, per-frame view geometry, stage edge identities)
remain open and are inherited unchanged.
