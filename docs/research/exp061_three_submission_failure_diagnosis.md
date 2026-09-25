# exp061 three-submission failure diagnosis

## Evidence

The three attempts do not share one error class.

1. Submission `56442230` staged the development zon CSV through a copy-only
   kernel. Kaggle returned an incorrect-format scoring error and no score.
2. Submission `56447637` staged the byte-identical known-good xyonly CSV through
   the same copy-only mechanism. It returned the same incorrect-format error.
   This rules out zon graph content as the sufficient cause of those two errors.
3. Submission `56454236` used the v2 full-inference notebook. Its public kernel
   run completed and reproduced the development hashes, but the authenticated
   submission record reports `totalBytes=0` and: "Your notebook hit an unhandled
   error while rerunning your code. Note that the hidden dataset can be
   larger/smaller/different than the public dataset". Kaggle does not expose the
   hidden traceback for code competitions, so the failing line is unavailable. `totalBytes=0` means no submission artifact was returned; it does not prove that no intermediate output was ever generated during the rerun.

The v2 metadata includes the competition source and all three weight datasets.
Static inspection found no fixed test movie names and no fixed development SHA
gate on hidden output. The deployment does retain a fixed whole-run two-hour
watchdog while running the full parent pipeline plus an original-XY reference,
cached xyonly, zon, and xyd4 replays. The public test has four movies, while the
hidden rerun can be materially larger or different. The strongest current
hypothesis is therefore hidden-workload infeasibility or another hidden-input
assumption in this research harness. The generic platform error does not prove a
timeout, so that remains a hypothesis rather than a confirmed traceback.

Official references: [competition data](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/data) and [code-competition debugging](https://www.kaggle.com/code-competition-debugging).

## Decision

Do not resubmit v2 and do not change prediction values. A v3 deployment design
should run only the authorized zon inference path needed for `submission.csv`,
retain fail-closed structural checks, and move xy/reference/xyd4 development
validation outside the hidden scoring rerun. That is a validation/deployment
contract amendment and needs explicit agreement, fresh review, smoke, resource
accounting, and a new submission authorization. Versioned follow-up: `experiments/exp_061_zon_lb_submission_repair_v3/strategy_amendment_v1.md` records a zon-only deployment proposal and its blocking feasibility evidence. It remains proposal-only; no implementation, launch, or submission occurred.

`scripts/audit_biohub_submission_csv.py` provides a project-side structural CSV
audit with negative controls. It is not claimed to reproduce Kaggle's scorer.

