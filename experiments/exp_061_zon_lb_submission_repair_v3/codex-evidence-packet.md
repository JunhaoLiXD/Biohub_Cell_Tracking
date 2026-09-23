# exp061 v3 Codex read-only evidence packet

## Reviewer instructions

This packet is generated directly from the immutable experiment snapshot after independently verifying every manifest SHA-256. It is supplied because the Codex read-only command helper failed to open files during the first formal review. Treat all claims as untrusted and challenge the embedded source. You may use read-only tools once if available; do not repeatedly retry a broken command helper. A strategy CONSENSUS is not a formal admission PASS. The v2 hidden failure has no traceback and timeout is unproven. The latest user authorized exactly one bounded notebook run after gates; no leaderboard submission. Preserve the first formal BLOCK as history.

## Snapshot manifest (all hashes verified by generator)

{
  "created_at": "2026-09-23T01:20:53+00:00",
  "files": [
    {
      "role": "config",
      "path": "experiments/exp_061_zon_lb_submission_repair_v3/snapshot/config.yaml",
      "sha256": "fb62219d2ebc331fca7fb20522f2f14a85cfc2aee7e0620985f793cfb44b600f"
    },
    {
      "role": "source_notebook",
      "path": "experiments/exp_061_zon_lb_submission_repair_v3/snapshot/source/exp061_zon_submission_repair_v3.ipynb",
      "sha256": "8efd5500fc80909928679d6dbc5e4361a28374ec214e57bf53cce0239f5cfaba"
    },
    {
      "role": "extra_file",
      "path": "experiments/exp_061_zon_lb_submission_repair_v3/snapshot/extra_files/build_exp061_zon_submission_repair_v3.py",
      "sha256": "f34327ce1531255da52ddd328a75a6deca30ac3299a61b982f88f0d39bab5b9c"
    },
    {
      "role": "extra_file",
      "path": "experiments/exp_061_zon_lb_submission_repair_v3/snapshot/extra_files/build_exp061_zon_deployment_module.py",
      "sha256": "42142407a48300f3910b1cfc28d284b5b21259340a7cf074ccac6a9d62e333c6"
    },
    {
      "role": "extra_file",
      "path": "experiments/exp_061_zon_lb_submission_repair_v3/snapshot/extra_files/exp061_zon_deployment.py",
      "sha256": "35aa6d61c543a891da5649ed48722938e10b4ca240a31d3c3e4360c3ccd39123"
    },
    {
      "role": "extra_file",
      "path": "experiments/exp_061_zon_lb_submission_repair_v3/snapshot/extra_files/validate_exp061_zon_deployment_v3.py",
      "sha256": "ea5de7f415c62c1e19f895f88cdf49d982e7f7b3c340b69acd6b648a4961302a"
    },
    {
      "role": "extra_file",
      "path": "experiments/exp_061_zon_lb_submission_repair_v3/snapshot/extra_files/biohub-exp061-deepcenter-tta.ipynb",
      "sha256": "bb60ffe996a81bfaad7a3f8c53b1282d5772a68fb12536c58bfa24c483f16aae"
    }
  ]
}

## Current user authorization in GOAL.md

# Project Goal
## Current authorization: v3 zon deployment run, 2026-09-22/23 UTC

The user explicitly asked Codex to rewrite the submission notebook from the current project state and run it, then assigned all execution to Codex rather than Luna. This authorizes one bounded Kaggle kernel run of `exp_061_zon_lb_submission_repair_v3` after the versioned strategy consensus, fresh experiment-specific Codex admission PASS, snapshot smoke, and a tracked two-hour reservation preserving six GPU hours. The inference strategy remains frozen. This is a notebook run only; leaderboard submission is not authorized by this request. Preserve the v2 hidden-rerun failure evidence and do not claim its exact cause is known. The next section describes the earlier completed authorization and is historical for this v3 launch.

## Current status: exp061 three-submission failure diagnosis, 2026-09-22 UTC

The one user-authorized zon resubmission was consumed by submission 56454236.
Two earlier copy-only submissions (56442230 zon and 56447637 byte-identical
repro_059 xyonly) failed with incorrect-format errors. The full-inference v2
submission reached hidden rerun and failed with an unhandled error, no score, and
totalBytes=0. Its visible run and development audits passed. Kaggle withholds the
hidden traceback, so the exact cause is unknown; extra replay workload under the
two-hour watchdog is a hypothesis only. No leaderboard resubmission or GPU launch
is currently authorized. Preserve all three receipts and frozen prediction
strategy. Diagnosis: `docs/research/exp061_three_submission_failure_diagnosis.md`;
authenticated error: `experiments/exp_061_zon_lb_submission_repair_v2/leaderboard-error.json`.

## Canonical workflow authorization (current)

The detailed operational handoff is `docs/research/PROJECT_HANDOFF.md`. For the
next research cycle, Claude Code is the strategy author and implementation lead;
Codex is the independent strategy challenger and implementation reviewer.
Claude Code must state the actual parent, one falsifiable hypothesis, exact
change, validation protocol, budget, artifacts, risks, and rollback/stop rule.
Codex must independently challenge methodology, leakage, graph semantics,
provenance, numerical stability, tests, reproducibility, and budget. Claude Code
revises until a versioned strategy record explicitly says `CONSENSUS`; without
consensus, execution stops and the disagreement returns to the user.

After consensus, all existing experiment gates remain in force: explicit
tracked hypothesis/change/parent, local and snapshot smoke, fresh
experiment-specific review, controller admission, resource reservation, and
independent Codex artifact/metric audit. Future experiment configs must set
`admission.require_codex_review: true` (optionally `reviewer_provider: codex`),

## Current project rules in AGENTS.md

# Agent Responsibilities

<!-- BEGIN AUTO-CHECKPOINT (generated by scripts/render_checkpoint.py — edit STATE.json, not this block) -->
## Active checkpoint (single source of truth: `STATE.json`)

- **Active experiment:** `exp_061_zon_lb_submission_repair_v3`
- **Controller state (from `experiments/exp_061_zon_lb_submission_repair_v3/experiment.json`):** MANUAL_REVIEW_REQUIRED
- **Phase:** EXP061_V3_FORMAL_ADMISSION_BLOCKED_EVIDENCE_ACCESS
- **Leaderboard submission:** NOT authorized
- **Summary:** The user authorized one v3 zon-only notebook run after normal gates, but no leaderboard submission. Candidate snapshot and local validator exist. Formal Codex admission returned BLOCK because its read-only shell could not inspect evidence; this is not a code verdict. Claude strategy CONSENSUS is recorded. Best Public LB remains repro_059 0.947; the v2 hidden rerun error remains unexplained.
- **Next action:** Preserve the formal BLOCK. Provide bounded authenticated snapshot evidence to a fresh read-only Codex admission review. Require PASS, snapshot smoke, and a tracked 2h reservation preserving 6h before one Kaggle kernel launch. No automatic retry, repeated polling, or LB submission.

_Generated from `STATE.json` (updated 2026-09-23T01:33:17.607049+00:00). Do not hand-edit this block; edit `STATE.json` and rerun `python scripts/render_checkpoint.py`. Full authorization detail lives once in `GOAL.md`._
<!-- END AUTO-CHECKPOINT -->

The full active authorization detail lives once in `GOAL.md` (section
"Active authorization detail (diag_044) — canonical"). This file does not restate it.

## Current collaboration contract (effective 2026-09-15)

The detailed state and execution strategy are maintained in
`docs/research/PROJECT_HANDOFF.md`. The working loop is deliberative:
Claude Code is the primary strategy author and implementation owner; Codex is an
independent, adversarial reviewer. Claude Code proposes a falsifiable hypothesis,
actual parent, exact change, validation protocol, budget, artifacts, risks, and
rollback/stop rule. Codex checks those claims against source, tests, leakage,
graph semantics, numerical behavior, reproducibility, and budget, and may require
revision. The proposal may be implemented or executed only after a versioned
record contains the proposal, critique, revisions, and explicit `CONSENSUS`.
`NO_CONSENSUS` is a stop condition that is returned to the user for direction.

Claude Code may lead implementation after consensus, but implementation does not
replace review: Codex must independently inspect the diff and run proportionate
validation. Future experiments must set
`admission.require_codex_review: true` (and may set
`reviewer_provider: codex`), request review with
`scripts/request_codex_review.py`, and require a fresh experiment-specific Codex
`PASS` before execution. Legacy experiment configs and receipts, including
exp_055, remain Claude-based and are preserved without retroactive rewriting.
After execution, Codex audits raw artifacts and metrics before Claude interprets
the result and proposes the next strategy. Historical records are immutable
evidence and must not be silently rewritten.

The project is in a late-stage accuracy push. With explicit user authorization,
high-risk/high-reward experiments are encouraged, including potentially
framework-changing detector, association, decoding, or joint-lineage designs.
Such experiments may fail and should be selected for credible upside and
information value. They must nevertheless retain exact provenance, a reversible
snapshot, bounded resources, an explicit stop rule, leakage protection,
independent graph/metric audits, and honest separation of local proxy evidence
from Public LB evidence. Aggressive research expands the search space; it does
not weaken validation, budget, tracking, model-allowance, leaderboard, or
promotion gates. Any major direction change remains subject to user approval.

## Current research handoff

Read `GOAL.md`, `.private/current/CONTINUATION.md`, and `.private/current/MEMORY.md`
before consulting historical plans. The exactly reproduced fixed-alpha-0.4 motion
EMA configuration is the leading inference candidate at train16 score
0.9387332376874039 with user-reported Public LB 0.942. Global alpha 0.6 and the
threshold-1.0, alpha-1.0 adaptive hard reset both completed as valid terminal
REJECT results. The latter scored 0.9368238444059783 and reset 39.32% of eligible
online updates. Retain fixed alpha 0.4 and do not relaunch either rejected branch.
The byte-identical online-telemetry diagnostic `diag_044` passed 65 local tests,
fresh Claude review, and snapshot smoke, then launched once at 20:19:02Z. Do not
poll or relaunch it; wait for the user completion notice, then check and collect
once. Older 0.912/0.933 and graph-only plans are historical controls, not current
task instructions.
Each successor must name its actual parent, validation protocol, exact change, review,
budget, artifacts, and decision.

## Budget arithmetic

Remaining ledger hours: 23.493013; existing reservation total: 2.0; proposed v3 reservation: 2.0; protected floor: 6.0; headroom after both reservations and floor: 13.493013. Existing v2 reservation remains conservatively held and has not been silently released.

## Authenticated v2 hidden failure

{
  "submission_id": 56454236,
  "status": "COMPLETE",
  "public_score": null,
  "total_bytes": 0,
  "error_description": "Your notebook hit an unhandled error while rerunning your code. Note that the hidden dataset can be larger/smaller/different than the public dataset",
  "kernel": "lingxd/biohub-exp061-zon-lb-repair",
  "kernel_version": 1,
  "script_version_id": 351748008,
  "evidence_source": "Authenticated one-time Kaggle API retrieval after the user reported completion."
}

## Versioned strategy and objections

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

## Claude agreement addendum and correction

# exp061 zon deployment amendment v3 (strategy consensus)

This addendum supplements `strategy_amendment_v2.md` without rewriting the prior proposal or the formal v3 admission BLOCK. The active implementation and validation contract remains the v2 amendment: one zon replay over unchanged parent inference, fixed 2-hour watchdog, fail-closed current-run publication, and no leaderboard submission.

## Claude strategy agreement

A single bounded, read-only Claude strategy review was performed after the root Codex reviewer challenged the original approximate-two-hour claim and impossible local 4x performance prerequisite. Its verbatim response is `claude-strategy-review.md` and ends `VERDICT: CONSENSUS`. Claude agreed that the revised single-zon deployment is a diagnostic with residual hidden-input and runtime risk; it did not grant implementation admission or claim the hidden traceback was known. The required next gates remain fresh experiment-specific Codex PASS, snapshot smoke, budget reservation preserving six hours, and one tracked run.

Correction to one phrase in the Claude response: the two copy-only submissions were not byte-identical to each other. The xyonly copy was byte-identical to the earlier successful parent on the visible input; the zon copy was different. Both received the same incorrect-format error. This supports a common copy mechanism issue but does not independently identify the hidden rerun exception.

The root Codex strategy objections and revised arithmetic are recorded in v2; the root implementation review was conditional on formal admission. With the Claude strategy agreement now captured, the strategy record is explicitly `CONSENSUS`. Formal admission is still `BLOCK` from an inaccessible-evidence review and must not be treated as PASS.

## Verbatim Claude strategy review

Acting as primary research strategist on this bounded, read-only review of the v3 zon-deployment amendment. Judgment on the merits:

**What holds up:**
- **Change is purely reductive and policy-frozen.** Removing the original-XY reference and `xyonly`/`xyd4` dev replays from the scoring path, with an AST-identical `_accept_wrapper`, a hash-bound byte-identical parent inference cell, and only additive telemetry/`per_dataset` fields, is a legitimate deployment-only edit. It cannot change the per-input zon output policy.
- **Evidence is honestly scoped.** It does not claim timeout is proven, labels ~97m as an illustrative screen, bounds the visible run at ≤60m40s rather than "~2h," and drops the unachievable 4× performance prerequisite while keeping a 4× deterministic correctness fixture plus the one remote run as the actual feasibility measurement. No overstated local↔hidden parity.
- **Publication is fail-closed and atomic.** Unlinking any pre-existing parent `submission.csv`, staging + digest-verifying the zon CSV, and refusing to let a fallback parent CSV survive a zon failure directly targets the earlier incorrect-format failure class, not just workload.
- **Budget/stop rule are conservative and unchanged in spirit:** ≤2.0 GPU h, hard 2-hour watchdog retained, 20-min finalization reserve, 6-hour ledger floor, single check, no auto-relaunch, and no LB submission.
- **The disclosed `arm_summaries` keys-vs-`.values()` regression** was caught by the validator, corrected against frozen v2 behavior, and re-hashed — transparency, not concealment.

**Required caveat (non-blocking):** the two byte-identical known-good CSVs that still returned incorrect-format errors are strong evidence the hidden failure may be mechanism/structural rather than workload. So the diagnostic must be read asymmetrically: success would support the workload-reduction path, but a repeat failure must **not** be recorded as confirming timeout or workload infeasibility — it would instead point to a structural/hidden-input cause. The proposal already frames this as diagnostic and accepts residual hidden-input risk, so this is a condition on interpretation, not a defect in the change.

This is strategy agreement only. It remains gated by fresh experiment-specific Codex admission (`require_codex_review`), snapshot smoke, explicit budget reservation, and the existing controller gates before any launch; and it authorizes no LB submission.

VERDICT: CONSENSUS

## Snapshot config

schema_version: 1
experiment_id: exp_061_zon_lb_submission_repair_v3
parent: exp_061_zon_lb_submission_repair_v2
hypothesis: Removing the current-input XY reference and xyonly/xyd4 development replays
  from the scoring path will reduce deployment work while preserving the exact zon
  output for a fixed input; the hidden failure cause remains unknown.
change:
  component: zon_only_code_competition_deployment
  from: v2 full parent pipeline plus current-input XY reference and xyonly/zon/xyd4
    replay
  to: same parent pipeline plus exactly one zon replay and fail-closed current-run
    publication
  variables_changed: deployment execution and validation contract only; no model or
    prediction-policy changes
source_notebook: .private/exp061_lb_repair_v3/build/exp061_zon_submission_repair_v3.ipynb
substrate_note: The executed exp061 parent inference is unchanged except for experiment
  identity metadata. Deployment runs one zon replay with the frozen transforms, graph
  writer, and prediction policy. The independent XY reference and xyonly/xyd4 research
  replays are omitted.
validation:
  protocol: exp061_zon_only_deployment_v3
  primary_metric: binary_integrity_gate
  warning: Deployment integrity only. XY parity, xyd4 and the independent XY reference
    are development-only and intentionally omitted. The exact hidden traceback and
    hidden workload size are unavailable; the 4x-public estimate is risk screening
    only, not a guarantee. The 2h watchdog and 20m finalization reserve remain unchanged.
    This run does not authorize or perform an LB submission.
budget:
  tier: 1
  expected_gpu_hours: 2.0
success:
  minimum_improvement: 0.0
  regression_threshold: 0.0
evaluation:
  mode: gate
  gate_field: exp061_zon_deployment_integrity_passed
admission:
  require_claude_review: false
  require_codex_review: true
  reviewer_provider: codex
  methodology_valid: true
  require_reproducible_for_promotion: true
local:
  smoke_test:
  - '{python}'
  - scripts/validate_exp061_zon_deployment_v3.py
  - '{source_notebook}'
provenance:
  base_notebook: experiments/repro_059_public_0947_exact_copy/snapshot/source/biohub-repro059-public-0947-exact-copy.ipynb
  base_experiment: repro_059_public_0947_exact_copy
  builder: scripts/build_exp061_zon_submission_repair_v3.py
  appended_module: scripts/exp061_zon_deployment.py
  instrumented_functions:
  - deepcenter_heatmap_for_frame
  - deepcenter_accept_repair_point
  - filter_output_graph
  strategy_proposal: docs/research/exp061_z_reflection_deepcenter_tta_proposal.md
  strategy_status: CONSENSUS
  codex_challenges:
  - docs/research/exp061_codex_challenge_v1.md
  - docs/research/exp061_codex_challenge_v2.md
  - docs/research/exp061_codex_challenge_v3.md
  - docs/research/exp061_codex_challenge_v4.md
  - docs/research/exp061_codex_challenge_v5.md
  resolved_config_source: experiments/repro_059_public_0947_exact_copy/artifacts/ppsweep_selected.json
  pinned_overrides:
    MOTION_RELINK_TIGHT_UM: 5.5
  arms:
  - zon
  submission_repair: docs/research/exp061_lb_submission_repair.md
  repair_upstream_notebook: .private/exp061_lb_repair/upstream/biohub-exp061-deepcenter-tta.ipynb
  historical_development_zon_submission_sha256: 2593a5438a17e5649736fcd6ad2f7af4c2fa8f822a759e9f51d877cdf6c840a1
  module_builder: scripts/build_exp061_zon_deployment_module.py
  source_parent: exp_061_zon_lb_submission_repair_v2
  strategy_amendment: experiments/exp_061_zon_lb_submission_repair_v3/strategy_amendment_v2.md
  historical_development_zon_sha256: 2593a5438a17e5649736fcd6ad2f7af4c2fa8f822a759e9f51d877cdf6c840a1
  generated_zon_deployment_sha256: 35aa6d61c543a891da5649ed48722938e10b4ca240a31d3c3e4360c3ccd39123
authorization:
  scope: User explicitly requested rebuilding and running the submission notebook
    based on current project state. This authorizes one bounded Kaggle kernel run
    after consensus, fresh Codex PASS, snapshot smoke and budget reservation. It does
    not authorize leaderboard submission.
  no_leaderboard_submission: true
submission:
  user_authorized_count: 0
kaggle:
  owner: lingxd
  slug: biohub-exp061-zon-deploy-v3
  title: biohub-exp061-zon-deploy-v3
  accelerator: NvidiaTeslaT4
  docker_image: gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461
  inject_experiment_id: true
  competition_sources:
  - biohub-cell-tracking-during-development
  dataset_sources:
  - pilkwang/biohub-deepcenter-unet3d-center-prior-v1
  - pilkwang/biohub-temporal-unet3d-seed314159-v1
  - pilkwang/biohub-tracking-support-pack-50ep-v1
  required_dataset_sources: 3
  enable_gpu: true
  enable_internet: false
  is_private: true
  extra_files:
  - scripts/build_exp061_zon_submission_repair_v3.py
  - scripts/build_exp061_zon_deployment_module.py
  - scripts/exp061_zon_deployment.py
  - scripts/validate_exp061_zon_deployment_v3.py
  - .private/exp061_lb_repair/upstream/biohub-exp061-deepcenter-tta.ipynb

## Snapshot notebook cell 0: setup

# Biohub 0.947 LB, runnable with public datasets

This is [Reyhan Ksatria's 0.947 notebook](https://www.kaggle.com/code/reyhanksatria/biohub-cell-tracking-0-947-lb) (version 5) with three input paths changed and nothing else.

The original attaches its model files as three private datasets, so a copy of it cannot load them. The same files are public in Pilkwang Kim's datasets:

- [biohub-tracking-support-pack-50ep-v1](https://www.kaggle.com/datasets/pilkwang/biohub-tracking-support-pack-50ep-v1)
- [biohub-temporal-unet3d-seed314159-v1](https://www.kaggle.com/datasets/pilkwang/biohub-temporal-unet3d-seed314159-v1)
- [biohub-deepcenter-unet3d-center-prior-v1](https://www.kaggle.com/datasets/pilkwang/biohub-deepcenter-unet3d-center-prior-v1)

The notebook checks its model files against pinned SHA256 values before it predicts anything, and the public copies pass: primary `12f6881e…`, DeepCenter `8040999a…`, secondary `9bac2fa0…`.

**Scored:** submission 56207450, public LB **0.947**, T4 x2.

## The whole diff

| setting | original | here |
| --- | --- | --- |
| `BIOHUB_MODEL_ARTIFACTS` | `reyhanksatria/biohub-tracking-support-pack` | `pilkwang/biohub-tracking-support-pack-50ep-v1` |
| `BIOHUB_DEEPCENTER_CHECKPOINT` (3 places) | `reyhanksatria/biohub-deepcenterunet3d-center-prior-v1` | `pilkwang/biohub-deepcenter-unet3d-center-prior-v1` |
| `BIOHUB_SECONDARY_ARTIFACT_MANIFEST` | `reyhanksatria/biohub-temporalunet3d-seed-314159-v1` | `pilkwang/biohub-temporal-unet3d-seed314159-v1` |

All paths sit under `/kaggle/input/datasets/`.

## One variant I also scored

| change on top of this notebook | submission | public LB |
| --- | --- | --- |
| none | 56207450 | 0.947 |
| `ILP_DISAPPEARANCE_WEIGHT` 2 → 1.5 and `MOTION_RELINK_RELAXED_UM` 10 → 8.5 | 56207453 | 0.947 |

No visible change at three decimals.

## Credit

- Model weights, the ILP and the graph repair chain: [Pilkwang Kim](https://www.kaggle.com/code/pilkwang/biohub-cell-tracking-learned-graph-w-gap-recovery).
- The 0.938 and 0.940 notebooks this line grew from: [nusrati](https://www.kaggle.com/code/nusrati/0-938).
- Bidirectional harmonic fusion: [Дворкин Евгений](https://www.kaggle.com/code/evgendvorkin/biohub-0-927-lb).
- Everything from 0.941 to 0.947, and every line of code below: [Reyhan Ksatria](https://www.kaggle.com/code/reyhanksatria/biohub-cell-tracking-0-947-lb).

Everything below this cell is Reyhan's original notebook, unchanged apart from the three paths.

## Snapshot notebook cell 1: configuration and input discovery

# Biohub Cell Tracking: 0.947 LB

This update continues the verified progression from **0.933 → 0.934 → 0.939 → 0.941 → 0.946 → 0.947** Public LB. The core tracking architecture remains unchanged throughout — same UNet3D + node-transformer framework, dual-seed ensemble, ILP-based global linking, harmonic bidirectional association, repair pipeline, and held-out post-process selection. The **0.934 → 0.939** step widened safe division recovery while making bidirectional association more conservative. The **0.939 → 0.941** step redistributed the repair budget by widening the safe-division parent search while tightening its learned confirmation and gap closing. The **0.941 → 0.946** step extended the existing eight-view spatial TTA from detection outputs into the primary UNet features used for association. This **0.946 → 0.947** step keeps that primary feature ensemble intact and extends spatial ensembling into two remaining model-dependent paths: the secondary model's association features and the DeepCenter repair gate, together with a small retuning of the DeepCenter safe-division threshold from 0.25 to 0.20.

| Component | 0.934 | 0.939 | 0.941 | 0.946 | 0.947 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Safe division parent max distance | 7.0 µm | 7.0 µm | 9.0 µm | 9.0 µm | 9.0 µm |
| Safe division sister max distance | 12.0 µm | 14.0 µm | 14.0 µm | 14.0 µm | 14.0 µm |
| Sister symmetry gate | off | 0.6 | 0.6 | 0.6 | 0.6 |
| DeepCenter safe-division veto | off | on | on | on | on |
| DeepCenter safe-division threshold | 0.12 | 0.12 | 0.25 | 0.25 | 0.20 |
| DeepCenter spatial TTA | off | off | off | off | on |
| Gap-close base radius | 5.8 µm | 5.8 µm | 5.0 µm | 5.0 µm | 5.0 µm |
| Bidirectional association weight | 0.30 | 0.15 | 0.15 | 0.15 | 0.15 |
| Bidirectional winner-agreement guard | on | removed | removed | removed | removed |
| DeepCenter expected epoch | 500 | 2 | 2 | 2 | 2 |
| Detection spatial TTA views | 8 | 8 | 8 | 8 | 8 |
| Primary edge-feature spatial TTA | off | off | off | on | on |
| Secondary edge-feature spatial TTA | off | off | off | off | on |
| Secondary edge-feature TTA weight | - | - | - | - | 0.75 |
| Held-out post-process selection | off | off | off | on | on |

**Recap: wider division search with a symmetry and DeepCenter guard (0.934 → 0.939).** The sister-distance limit widened from 12 µm to 14 µm to recover genuine divisions where the two daughters had drifted slightly farther apart. Since a wider radius alone also admits more spurious pairings, two safeguards compensate: a symmetry gate rejecting daughter candidates sitting at very uneven distances from the parent,

$$
\frac{|d_1 - d_2|}{(d_1 + d_2)/2} \le 0.6
$$

and the DeepCenter veto, so every candidate the wider geometric search proposes still needs independent confirmation before being accepted.

**Recap: a more conservative bidirectional fusion (0.934 → 0.939).** Association is normally scored only forward in time — for a cell at frame $t$, which detection at $t+1$ it most likely became. This pipeline also scores it in reverse — given a detection at $t+1$, which detection at $t$ it most likely came from. Let $p_f$ be the forward probability and $p_r$ the reverse probability for a candidate pair. The reverse weight dropped from 0.30 to 0.15, so $p_r$ acts as a lighter supporting vote rather than pulling $p_f$ as strongly, and the previous requirement that forward and reverse agree on the exact same winner was removed. Their mutual support is instead represented through the harmonic probability:

$$
p_{\text{harmonic}} = \frac{2 \, p_f \, p_r}{p_f + p_r}
$$

This preserves the idea that a strong temporal link should receive support from both temporal directions without imposing a hard winner-agreement requirement.

**Recap: redistributing the repair budget (0.939 → 0.941).** The association setup that reached 0.939 is left untouched; three repair-stage parameters are retuned instead. The safe-division **parent** radius increases from 7 µm to 9 µm. This is a different axis from the earlier 12 → 14 µm change — that one widened the allowed distance *between the two daughters*; this one widens the distance *from the parent to the missing daughter candidate*, recovering parent-child links the previous radius was cutting off. That wider parent search creates more room for false division proposals, so the DeepCenter confirmation threshold is raised from 0.12 to 0.25. Candidates admitted by the larger radius still have to clear a stricter learned confirmation before being recovered as divisions. At the same time, gap closing is tightened, with its base radius reduced from 5.8 µm to 5.0 µm. Together these changes move more repair capacity toward plausible divisions while tightening independent confirmation and gap recovery elsewhere.

**Recap: extending the primary spatial ensemble into association features (0.941 → 0.946).** The 0.941 pipeline already evaluates detection using the full eight spatial transformations of the D4 symmetry group. The 0.946 change does not increase the number of transformations. Instead, it extends the same transform-invert-average principle from detection logits into the primary UNet feature tensor consumed by the edge predictor. The eight spatial views are:

| No. | D4 Spatial View | Operation |
| --- | --- | --- |
| 1 | Identity | Original orientation |
| 2 | Horizontal flip | Reflection across one spatial axis |
| 3 | Vertical flip | Reflection across the other spatial axis |
| 4 | Horizontal + vertical flip | Reflection across both axes, equivalent to a 180° rotation |
| 5 | Rotation 90° | 90° spatial rotation |
| 6 | Rotation 270° | 270° spatial rotation |
| 7 | Transpose | Reflection across one diagonal |
| 8 | Anti-transpose | Reflection across the opposite diagonal |

For an input $x$, let $T_i$ denote the $i$-th D4 transformation. Detection logits are aligned back into the original coordinate system and averaged:

$$
\bar{L}(x) = \frac{1}{8}\sum_{i=1}^{8} T_i^{-1}\left(L(T_i(x))\right)
$$

This detection-logit TTA already existed before 0.946. What changes in 0.946 is the representation used for temporal association. Previously, even after eight-view detection TTA, the edge predictor still received the UNet feature map from the original orientation only:

$$
F_{\text{association}}(x) = F(x)
$$

The 0.946 pipeline retains the UNet feature tensor from every transformed view, maps each one back to the original coordinate system, and averages them:

$$
\bar{F}_{p}(x) = \frac{1}{8}\sum_{i=1}^{8} T_i^{-1}\left(F_{p}(T_i(x))\right)
$$

where the subscript $p$ denotes the primary model. The primary edge predictor therefore receives:

$$
F_{p,\,\text{association}}(x) = \bar{F}_{p}(x)
$$

rather than the original-view feature representation alone. The improvement from 0.941 to 0.946 therefore comes from propagating the existing D4 ensemble farther into inference rather than adding more geometric transformations.

**What's new in 0.947: completing spatial ensembling across the secondary association path.** The dual-seed pipeline already uses a secondary temporal model as a supporting signal. Before 0.947, the secondary model participates in detection ensembling and association fusion, but its feature representation used by the secondary edge predictor remains based on the original orientation. This means that after 0.946 the two association branches are asymmetric:

$$
F_{p,\,\text{association}}(x) = \bar{F}_{p}(x)
$$

for the primary model, while the secondary branch still uses:

$$
F_{s,\,\text{association}}(x) = F_s(x)
$$

where $F_s(x)$ is the secondary model's original-view feature tensor. The 0.947 configuration extends D4 feature aggregation into this secondary branch as well. The secondary model now retains and inverse-aligns its UNet feature tensor from the same eight spatial views:

$$
\bar{F}_{s}(x) = \frac{1}{8}\sum_{i=1}^{8} T_i^{-1}\left(F_s(T_i(x))\right)
$$

Unlike the primary branch, however, the final secondary feature representation is not replaced entirely by the eight-view mean. The 0.947 configuration uses a **0.75 TTA blend weight**, preserving part of the original-view representation while giving most of the weight to the spatially ensembled representation:

$$
F_{s,\,0.947}(x)
=
(1-\lambda_s)F_s(x)
+
\lambda_s\bar{F}_s(x),
\;
\lambda_s = 0.75
$$

or equivalently,

$$
F_{s,\,0.947}(x)
=
0.25F_s(x)
+
0.75\bar{F}_s(x)
$$

The secondary edge predictor then consumes this blended representation. The distinction is important: 0.947 does **not** increase the secondary edge weight itself and does **not** replace the existing low-margin consensus mechanism. It changes the spatial representation from which the secondary model produces its supporting edge evidence. The association paths therefore progress from:

$$
\text{0.946:}
\,
\begin{cases}
\text{Primary edge predictor} \leftarrow \bar{F}_p(x)
\\
\text{Secondary edge predictor} \leftarrow F_s(x)
\end{cases}
$$

to:

$$
\text{0.947:}
\,
\begin{cases}
\text{Primary edge predictor} \leftarrow \bar{F}_p(x)
\\
\text{Secondary edge predictor} \leftarrow 0.25F_s(x) + 0.75\bar{F}_s(x)
\end{cases}
$$

so both temporal models now benefit from spatially ensembled feature information before their association evidence is combined.

**What's new in 0.947: extending D4 TTA into the DeepCenter repair gate.** DeepCenter is not the primary detector or edge predictor. It is used as an independent learned spatial confirmation signal for selected repair decisions, including safe-division recovery. In 0.946, this gate still evaluates each frame from a single spatial orientation even though the primary detection and association paths already use D4 TTA. The 0.947 configuration applies the same eight-view D4 principle to the DeepCenter logits. For a frame $x$, let $D(T_i(x))$ denote the DeepCenter logit volume produced from spatial view $T_i$. Each output is inverse-aligned before averaging:

$$
\bar{D}(x)
=
\frac{1}{8}
\sum_{i=1}^{8}
T_i^{-1}\left(D(T_i(x))\right)
$$

The final DeepCenter heatmap is then obtained from the averaged logits:

$$
H_{\text{DC}}(x)
=
\sigma\left(\bar{D}(x)\right)
$$

rather than applying the sigmoid to a single-view logit map. This matters because the DeepCenter score is used as a gate for repair candidates. A candidate should therefore be less dependent on the arbitrary spatial orientation of the input frame before being accepted or rejected. The DeepCenter update completes a broader consistency pattern in the inference pipeline:

| Spatially Ensembled Representation | 0.946 | 0.947 |
| --- | --- | --- |
| Detection logits | on | on |
| Primary edge features | on | on |
| Secondary detection logits | on | on |
| Secondary edge features | off | on |
| DeepCenter repair logits | off | on |

The 0.947 update therefore does not introduce a new tracking architecture. It extends an already successful invariance mechanism into two branches that were still operating from single-view representations.

**What's new in 0.947: safe-division confirmation threshold 0.25 → 0.20.** Alongside DeepCenter TTA, the safe-division confirmation threshold is adjusted from 0.25 to 0.20. The geometric division constraints themselves remain unchanged: the parent search radius stays at 9 µm, the sister-distance limit stays at 14 µm, the sister-symmetry gate stays at 0.6, and the existing frame and global division caps remain intact. The threshold therefore changes only the learned DeepCenter confirmation stage:

$$
\text{accept safe-division candidate if}
\,
s_{\text{DC}} \ge \tau_{\text{DC}}
$$

with:

$$
\tau_{\text{DC}}:
0.25
\rightarrow
0.20
$$

in the 0.947 configuration. Because the DeepCenter score itself is now produced from an eight-view averaged logit representation, this threshold change should be interpreted together with the DeepCenter TTA update rather than as an isolated global relaxation. The geometric search space is not widened further; instead, the learned confirmation gate operates on a more spatially averaged score and uses the 0.20 acceptance threshold present in the verified 0.947 configuration. The direct functional difference can be summarized as:

| Component | 0.946 Public LB | 0.947 Public LB |
| --- | --- | --- |
| Detection D4 TTA | 8 views | 8 views |
| Primary edge-feature D4 TTA | on | on |
| Primary edge-feature aggregation | full 8-view mean | full 8-view mean |
| Secondary detection D4 TTA | on | on |
| Secondary edge-feature D4 TTA | off | on |
| Secondary edge-feature TTA blend | original view only | 0.25 original + 0.75 D4 mean |
| DeepCenter D4 TTA | off | on |
| DeepCenter safe-division threshold | 0.25 | 0.20 |
| Safe division parent radius | 9.0 µm | 9.0 µm |
| Safe division sister radius | 14.0 µm | 14.0 µm |
| Sister symmetry gate | 0.6 | 0.6 |
| Gap-close radius | 5.0 µm | 5.0 µm |
| Bidirectional association weight | 0.15 | 0.15 |
| Bidirectional fusion | harmonic probability | harmonic probability |
| Dual-seed association framework | unchanged | unchanged |
| ILP global linking | unchanged | unchanged |
| Held-out post-process selection | on | on |

The important point is that **0.946 → 0.947 is not another global rewrite of linking or repair**. The primary feature-TTA path that produced 0.946 is preserved. The 0.947 configuration instead removes two remaining single-view inconsistencies: the secondary model's association features and the DeepCenter repair logits. The safe-division threshold is also adjusted from 0.25 to 0.20 as part of the verified 0.947 configuration, while the underlying division geometry and the rest of the 0.946 repair settings remain unchanged.

**Summary.** The progression remains cumulative. **0.934 → 0.939** widened safe-division recovery with additional geometric and DeepCenter safeguards while making bidirectional association more conservative. **0.939 → 0.941** redistributed the repair budget by widening the parent-side division search, strengthening its DeepCenter confirmation, and tightening gap closing. **0.941 → 0.946** extended the existing eight-view D4 ensemble from detection logits into the primary UNet features consumed by the edge predictor. **0.946 → 0.947** retains that primary feature ensemble and extends the same spatial-consistency principle into the secondary edge-feature path and the DeepCenter repair gate, while changing the DeepCenter safe-division threshold from 0.25 to 0.20. The resulting verified progression is **0.933 → 0.934 → 0.939 → 0.941 → 0.946 → 0.947**. Relative to the previous 0.946 configuration, the current pipeline adds **+0.001 Public LB**; relative to the original 0.934 solution documented in this progression, the cumulative improvement is **+0.013 Public LB**.

**If you have ideas on how to push this toward 0.950, feel free to reach out — I'm also looking for a teammate for this competition. Also, if you find this useful, an upvote would be appreciated!**

## Snapshot notebook cell 2: frozen parent inference identity

Full cell omitted to bound the review prompt. Its SHA-256 is 9a341b5b1bafd80283c05041f23ea650bdce082b8ff26009bc0be69b98a20ac8, verified above. The snapshot notebook and upstream source SHA values are listed in the manifest. The local validator checks cell-level source parity after stripping experiment ID/watchdog metadata. If you cannot accept this hash-based evidence, return REVISE/BLOCK rather than PASS.

## Snapshot notebook cell 3: complete zon deployment module

"""exp061 zon-only deployment runner copied from the frozen v2 research harness. — DeepCenter repair-heatmap TTA probe (xyonly / zon / xyd4).

APPENDED (with a tiny strippable call-site injection) onto the frozen repro_059 (Public LB 0.947)
notebook by scripts/build_exp061_deepcenter_tta.py. The parent's own 0.947 prediction path runs
byte-unchanged; stripping every `# exp061` line reproduces the parent exactly (parity by
construction). The deployment entry point runs only the frozen zon arm and writes its current-input
receipt. It intentionally does not run XY parity or xyd4 replays.

Strategy record: docs/research/exp061_z_reflection_deepcenter_tta_proposal.md (v5, CONSENSUS) +
exp061_codex_challenge_v1..v5.md. Parent submission SHA (0.947 = the xyonly byte-parity target):
  d34533806b3153ddd4f33f3bbc1dea70af2d5406bb1ea48e42c135a97c213f60

Design (CONSENSUS):
  * THREE arms differing ONLY in the DeepCenter TTA set, all else frozen at the parent's resolved
    config (MOTION_RELINK_TIGHT_UM=5.5, from ppsweep_selected.json; adaptive PP-sweep is the
    parent's own byte-frozen path and is not used for arm selection):
      - xyonly : parent TTA exactly (V0,Vx,Vy,Vxy,R1,R3,Td,Ta) -> BYTE-PARITY control.
      - zon    : the 8 above + a Z-reflection (dim -3) of each -> primary probe.
      - xyd4   : uniform 8-view D4 = replace the duplicated anti-transpose Ta with the missing
                 anti-diagonal reflection Aad -> in-group geometrically-motivated companion.
  * Two DIRECT DeepCenter veto consumers read the heatmap: gap1 (close_single_frame_gaps) and
    safe-division. recover_strict_gap2 reads NO heatmap (downstream stage). The per-arm replay
    re-runs the UNCHANGED filter_output_graph from a freshly loaded graph per movie, which starts
    BEFORE gap1 -> the treatment reaches BOTH consumers (proposal replay-boundary requirement).
  * View-level cache: each unique input transform's raw model output model(T(x)) is computed ONCE
    per (dataset,t,view), stored LOSSLESSLY on disk (float32 .npy) + a bounded RAM LRU, retained
    until ALL arms finish (arms run sequentially). Each arm accumulates its own ordered view list
    IN TORCH on-device, in the parent's exact left-to-right order (byte-parity requires this;
    numpy re-summation would not bit-match). ~17 distinct forwards/frame union across arms.
  * xyonly's submission SHA MUST equal the parent's. It is computed FRESH through the SAME cached
    accumulation path the experimental arms use (proving that path). On mismatch the run STOPS
    before trusting zon/xyd4 and writes fail-closed metrics.json (gate False) -- no crash.
  * Mechanism-active check (NOT the old delta==0 raise): zon/xyd4 heatmaps must differ from
    xyonly on >=1 scored frame; a verified ZERO response is a recorded mechanism NULL (blocks a
    duplicate submission), not an implementation failure.
  * Budget: whole-run 2.0h SIGALRM watchdog (top-injected). Arms run xyonly -> zon -> xyd4; each
    arm's outputs are written as an atomic completed-arm artifact; an arm is NOT started unless
    remaining budget >= measured_running_rate * est_cost + a 20-min finalization reserve. A
    partial run (e.g. xyd4 not started) is a VALID recorded result, unlike a mid-arm kill.

References parent-notebook globals by name (present after the parent cell runs).
"""

# ---------------------------------------------------------------------------
# Static configuration (frozen; mirrored in the experiment config/proposal v5)
# ---------------------------------------------------------------------------
EXP061_PARENT_SUBMISSION_SHA256 = (
    "d34533806b3153ddd4f33f3bbc1dea70af2d5406bb1ea48e42c135a97c213f60"
)
EXP061_RESOLVED_OVERRIDES = {"MOTION_RELINK_TIGHT_UM": 5.5}  # ppsweep_selected.json
EXP061_CONTROL_ARM = "xyonly"
EXP061_ARMS = ("xyonly", "zon", "xyd4")   # pre-registered; xyonly first (parity control)
EXP061_VALIDATION_PROTOCOL = "exp061_zon_only_deployment_v3"
EXP061_EXPERIMENT_ID = "exp_061_zon_lb_submission_repair_v3"
EXP061_HARD_STOP_SECONDS = 2.0 * 3600.0
EXP061_FINALIZATION_RESERVE_SECONDS = 20.0 * 60.0   # numeric reserve (proposal §7)
EXP061_RAM_LRU_MAX_VIEWS = 64                        # bounded RAM cache of decoded view logits
EXP061_TRANSFORM_IMPL_VERSION = "v1"                 # bound into the view-cache key (admission #1)
# The parent writes its verified checkpoint hashes here; we REQUIRE the deepcenter hash for the
# view-cache provenance instead of falling back to a placeholder (admission #1).
EXP061_RUNTIME_INTEGRITY_FILE = "bidirectional_production_runtime_integrity.json"
EXP061_HEATMAP_SAMPLE_FRAMES = 8                     # keep a few full heatmaps per arm for |delta| stats
# The parent's adaptive PP-sweep (validator) is DISABLED for this run via a strippable
# `BIOHUB_VALIDATOR_ENABLE=0` injection (admission #6): the xyonly replay pins tight55 itself, so
# the sweep is pure overhead here. We REQUIRE it to be off so the feasibility accounting holds.
EXP061_REQUIRE_VALIDATOR_DISABLED = ("BIOHUB_VALIDATOR_ENABLE", "0")

# The parent's DeepCenter TTA env flag MUST be ON for all arms (the parent 0.947 pipeline uses it;
# xyonly reproduces the parent exactly). The arms differ only via _EXP061_ACTIVE_ARM below.
EXP061_REQUIRE_PARENT_TTA_ENV = ("BIOHUB_DEEPCENTER_TTA", "1")

# Effective-config completeness (same knob set as exp_060; every knob must be a live global so we
# prove nothing but the TTA set differs across arms on the ACTUAL pipeline).
EXP061_CONFIG_KEYS = (
    "ILP_EDGE_WEIGHT", "ILP_APPEARANCE_WEIGHT", "ILP_DISAPPEARANCE_WEIGHT", "ILP_DIVISION_WEIGHT",
    "OUTPUT_EDGE_MAX_UM", "OUTPUT_ENFORCE_NEXT_FRAME", "OUTPUT_SINGLE_PARENT_REPAIR",
    "OUTPUT_SINGLE_CHILD_REPAIR", "OUTPUT_PRUNE_ISOLATED", "OUTPUT_MOTION_RELINK",
    "MOTION_RELINK_TIGHT_UM", "MOTION_RELINK_RELAXED_UM", "MOTION_RELINK_VELOCITY_WEIGHT",
    "MOTION_RELINK_LEARNED_BONUS", "MOTION_RELINK_MAX_FRAME_NODES",
    "OUTPUT_DIVISION_GEOMETRY_FILTER", "DIV_PARENT_MAX_UM", "DIV_SISTER_MAX_UM",
    "DIV_DROP_TO_SINGLE_IF_BAD", "OUTPUT_GAP_CLOSE", "GAP_CLOSE_MAX_GAP", "GAP_CLOSE_UM",
    "GAP_DENSITY_ADAPTIVE", "GAP_DENSITY_REFERENCE_UM", "GAP_DENSITY_GAIN",
    "GAP_DENSITY_MAX_STEP_DELTA_UM", "GAP_DENSITY_NEIGHBORS", "GAP_CLOSE_REUSE_EXISTING",
    "GAP_CLOSE_REUSE_UM", "GAP_CLOSE_MAX_ADDED_FRAC", "GAP_CLOSE_MAX_ADDED_ABS",
    "GAP_REFINE_SYNTHETIC", "GAP_REFINE_WIN_Z", "GAP_REFINE_WIN_YX", "GAP_REFINE_MAX_SHIFT_UM",
    "OUTPUT_FILTER_SHORT_TRACKS", "OUTPUT_MIN_TRACK_LEN", "OUTPUT_KEEP_DIVISION_COMPONENTS",
    "OUTPUT_LINEFIT_SMOOTH", "OUTPUT_LINEFIT_WEIGHT", "OUTPUT_LINEFIT_WINDOW",
    "OUTPUT_GAP2_RECOVERY", "GAP2_MAX_TOTAL_UM", "GAP2_MAX_STEP_UM", "GAP2_MAX_LINKS_FRAC",
    "GAP2_MAX_LINKS_ABS", "GAP2_REQUIRE_CONTEXT", "GAP2_FRAME_FRAC_CAP", "OUTPUT_SAFE_DIVISIONS",
    "SAFE_DIV_MAX_UM", "SAFE_DIV_SISTER_MAX_UM", "SAFE_DIV_SISTER_SYMMETRY_TAU",
    "SAFE_DIV_EXISTING_CHILD_MAX_UM", "SAFE_DIV_FRAME_FRAC_CAP", "SAFE_DIV_GLOBAL_FRAC_CAP",
    "SAFE_DIV_DIVERGE_UM", "SAFE_DIV_REQUIRE_DIVERGENCE", "SAFE_DIV_REQUIRE_MUTUAL_NN",
    "USE_DEEPCENTER_VETO", "REQUIRE_DEEPCENTER_VETO", "DEEPCENTER_GAP_VETO",
    "DEEPCENTER_SAFE_DIV_VETO", "DEEPCENTER_GAP_THRESHOLD", "DEEPCENTER_EXPECTED_EPOCH",
    "DEEPCENTER_GAP_CONFIRM_MIN_SPAN_UM", "DEEPCENTER_SAFE_DIV_THRESHOLD",
    "DEEPCENTER_SCORE_WIN_Z", "DEEPCENTER_SCORE_WIN_YX",
)

# ---------------------------------------------------------------------------
# INDEPENDENTLY-DERIVED frozen parent config (admission v3 #1; CORRECTED admission v4 #1).
#
# These are the repro_059 (0.947) post-processing knob values as the 0.947 pipeline EFFECTIVELY
# resolves them. CRITICAL (v4 #1 bug fix): the parent notebook SETS `os.environ['BIOHUB_KEY']='V'`
# overrides in its env-setup block BEFORE the `KEY = float/int(os.environ.get('BIOHUB_KEY',
# 'DEFAULT'))` / `... != '0'` declarations, so the EFFECTIVE value is the env override when present,
# and only the declaration fallback for knobs the env never sets. The earlier table used the bare
# declaration fallbacks -> it disagreed with the real pipeline on 18 knobs, which would have
# fail-closed the real GPU run. This table now stores, per key, `env_override if set else
# declaration_fallback` (see scripts/test_exp061_behavioral.py::test_N, which re-parses BOTH the
# env-setup block AND the declarations and recomputes the effective value, so this table cannot
# silently drift from the parent). At runtime every started arm's live config is asserted EQUAL to
# EXP061_FROZEN_PARENT_CONFIG key-by-key (fail-closed), which is this table with the documented
# tight55 ppsweep override applied -- so the gate verifies the STARTING values equal an
# independently frozen reference, not merely that they stay constant across arms.
# ("# env" = set in the parent env-setup block; "# default" = never set in env, declaration fallback.)
EXP061_PARENT_BASE_DEFAULTS = {
    "ILP_EDGE_WEIGHT": -1.0, "ILP_APPEARANCE_WEIGHT": 0.0, "ILP_DISAPPEARANCE_WEIGHT": 2.0,  # env
    "ILP_DIVISION_WEIGHT": 1.2, "OUTPUT_EDGE_MAX_UM": 14.0, "OUTPUT_ENFORCE_NEXT_FRAME": True,  # env
    "OUTPUT_SINGLE_PARENT_REPAIR": True, "OUTPUT_SINGLE_CHILD_REPAIR": False,
    "OUTPUT_PRUNE_ISOLATED": True, "OUTPUT_MOTION_RELINK": True, "MOTION_RELINK_TIGHT_UM": 6.0,
    "MOTION_RELINK_RELAXED_UM": 10.0, "MOTION_RELINK_VELOCITY_WEIGHT": 0.5,
    "MOTION_RELINK_LEARNED_BONUS": 1.0, "MOTION_RELINK_MAX_FRAME_NODES": 2600,  # env: bonus 1.0
    "OUTPUT_DIVISION_GEOMETRY_FILTER": False, "DIV_PARENT_MAX_UM": 10.5, "DIV_SISTER_MAX_UM": 8.0,
    "DIV_DROP_TO_SINGLE_IF_BAD": True, "OUTPUT_GAP_CLOSE": True, "GAP_CLOSE_MAX_GAP": 2,  # env: gap 2
    "GAP_CLOSE_UM": 5.0, "GAP_DENSITY_ADAPTIVE": True, "GAP_DENSITY_REFERENCE_UM": 6.5,  # env
    "GAP_DENSITY_GAIN": 0.04, "GAP_DENSITY_MAX_STEP_DELTA_UM": 0.125, "GAP_DENSITY_NEIGHBORS": 3,
    "GAP_CLOSE_REUSE_EXISTING": True, "GAP_CLOSE_REUSE_UM": 3.2, "GAP_CLOSE_MAX_ADDED_FRAC": 0.05,
    "GAP_CLOSE_MAX_ADDED_ABS": 2000, "GAP_REFINE_SYNTHETIC": True, "GAP_REFINE_WIN_Z": 1,
    "GAP_REFINE_WIN_YX": 3, "GAP_REFINE_MAX_SHIFT_UM": 3.2, "OUTPUT_FILTER_SHORT_TRACKS": True,
    "OUTPUT_MIN_TRACK_LEN": 6, "OUTPUT_KEEP_DIVISION_COMPONENTS": True, "OUTPUT_LINEFIT_SMOOTH": True,
    "OUTPUT_LINEFIT_WEIGHT": 0.8, "OUTPUT_LINEFIT_WINDOW": 2, "OUTPUT_GAP2_RECOVERY": True,  # env: True
    "GAP2_MAX_TOTAL_UM": 10.2, "GAP2_MAX_STEP_UM": 4.4, "GAP2_MAX_LINKS_FRAC": 0.0045,
    "GAP2_MAX_LINKS_ABS": 180, "GAP2_REQUIRE_CONTEXT": True, "GAP2_FRAME_FRAC_CAP": 0.006,
    "OUTPUT_SAFE_DIVISIONS": True, "SAFE_DIV_MAX_UM": 9.0, "SAFE_DIV_SISTER_MAX_UM": 14.0,  # env
    "SAFE_DIV_SISTER_SYMMETRY_TAU": 0.6, "SAFE_DIV_EXISTING_CHILD_MAX_UM": 10.0,  # env
    "SAFE_DIV_FRAME_FRAC_CAP": 0.0076, "SAFE_DIV_GLOBAL_FRAC_CAP": 0.00375, "SAFE_DIV_DIVERGE_UM": 2.25,  # env
    "SAFE_DIV_REQUIRE_DIVERGENCE": True, "SAFE_DIV_REQUIRE_MUTUAL_NN": True,
    "USE_DEEPCENTER_VETO": True, "REQUIRE_DEEPCENTER_VETO": True, "DEEPCENTER_GAP_VETO": True,
    "DEEPCENTER_SAFE_DIV_VETO": True, "DEEPCENTER_GAP_THRESHOLD": 0.25, "DEEPCENTER_EXPECTED_EPOCH": 2,  # env
    "DEEPCENTER_GAP_CONFIRM_MIN_SPAN_UM": 8.5, "DEEPCENTER_SAFE_DIV_THRESHOLD": 0.20,  # env
    "DEEPCENTER_SCORE_WIN_Z": 1, "DEEPCENTER_SCORE_WIN_YX": 2,
}
# The resolved 0.947 config = the parent defaults with ONLY the documented tight55 override. Built
# from the two independent tables so the override lives in exactly one place.
EXP061_FROZEN_PARENT_CONFIG = {**EXP061_PARENT_BASE_DEFAULTS, **EXP061_RESOLVED_OVERRIDES}

# ---------------------------------------------------------------------------
# Per-STAGE filter_output_graph counters captured per dataset (admission v3 #2): the parent's own
# `stats` dict already attributes node/edge additions and DeepCenter bypasses to the gap1, gap2 and
# safe-division stages. Capturing them per arm lets us report gap1/gap2-SPECIFIC final edge deltas
# and the count of DeepCenter-BYPASSED gap candidates (the ones the veto never scored), which a
# single global edge delta cannot. Missing keys default to 0 (the parent only emits a counter the
# first time it increments).
EXP061_STAGE_STAT_KEYS = {
    "gap1": ("gap_candidates", "gap_pairs_selected", "gap_added_edges", "gap_added_nodes",
             "gap_inserted_synthetic", "gap_reused_existing",
             "deepcenter_gap_bypassed_strong_motion", "deepcenter_gap_bypassed_observed_node"),
    "gap2": ("gap2_candidates", "gap2_pairs_selected", "gap2_added_edges", "gap2_added_nodes"),
    "safe_div": ("safe_division_candidates", "safe_division_geometric_candidates",
                 "safe_divisions_added"),
}

# ---------------------------------------------------------------------------
# Per-arm TTA view specification.
#
# A "view" is an ordered forward transform T applied to the input tensor; the raw model output
# model(T(x)) is cached; at accumulation the inverse T^-1 is applied (in torch) and summed. All
# XY transforms act on dims (-2,-1); Z acts on dim -3. `square_only` views run only when XY is
# square (matching the parent). Weight is 1 for every executed view (mean over executed views).
#
# View ids and their (forward, inverse) torch expressions are applied by _apply_forward/_apply_inv
# below; the executable spec + coordinate-mapping assertions live in scripts/test_exp061_behavioral.
# Order is the parent's exact order so xyonly reproduces the parent byte-for-byte.
# ---------------------------------------------------------------------------
# ("view_id", square_only)
_XY_BASE = (("V0", False), ("Vx", False), ("Vy", False), ("Vxy", False),
            ("R1", True), ("R3", True), ("Td", True))
EXP061_ARM_VIEWS = {
    # parent order: V0,Vx,Vy,Vxy,R1,R3,Td,Ta  (Ta = anti-transpose, distinct forward, keeps the
    # parent's duplicate slot at weight 1)
    "xyonly": _XY_BASE + (("Ta", True),),
    # xyonly's 8 views + the Z-reflection of each (square_only inherited from the XY part; Z of a
    # flip is always valid, Z of a rot/transpose needs square)
    "zon": _XY_BASE + (("Ta", True),)
            + (("ZV0", False), ("ZVx", False), ("ZVy", False), ("ZVxy", False),
               ("ZR1", True), ("ZR3", True), ("ZTd", True), ("ZTa", True)),
    # uniform D4: replace Ta with the anti-diagonal reflection Aad
    "xyd4": _XY_BASE + (("Aad", True),),
}

# Active-arm selector consumed by the installed heatmap function.
_EXP061_ACTIVE_ARM = {"name": None}


def _apply_forward(view_id, tensor, torch_mod):
    """Forward transform T(view_id) applied to the input tensor (torch), matching proposal §3."""
    Z = lambda x: x.flip((-3,))
    if view_id == "V0":  return tensor
    if view_id == "Vx":  return tensor.flip((-1,))
    if view_id == "Vy":  return tensor.flip((-2,))
    if view_id == "Vxy": return tensor.flip((-2, -1))
    if view_id == "R1":  return torch_mod.rot90(tensor, 1, dims=(-2, -1))
    if view_id == "R3":  return torch_mod.rot90(tensor, 3, dims=(-2, -1))
    if view_id == "Td":  return tensor.transpose(-1, -2)
    if view_id == "Ta":  return torch_mod.rot90(tensor, 1, dims=(-2, -1)).transpose(-1, -2)
    if view_id == "Aad": return tensor.transpose(-1, -2).flip((-2, -1))
    if view_id.startswith("Z"):
        return _apply_forward(view_id[1:], Z(tensor), torch_mod)
    raise KeyError(f"exp061: unknown view forward {view_id}")


def _apply_inverse(view_id, y, torch_mod):
    """Inverse transform T^-1(view_id) applied to a model output y (torch), matching proposal §3."""
    Zi = lambda x: x.flip((-3,))
    if view_id == "V0":  return y
    if view_id == "Vx":  return y.flip((-1,))
    if view_id == "Vy":  return y.flip((-2,))
    if view_id == "Vxy": return y.flip((-2, -1))
    if view_id == "R1":  return torch_mod.rot90(y, -1, dims=(-2, -1))
    if view_id == "R3":  return torch_mod.rot90(y, -3, dims=(-2, -1))
    if view_id == "Td":  return y.transpose(-1, -2)
    if view_id == "Ta":  return torch_mod.rot90(y.transpose(-1, -2), -1, dims=(-2, -1))
    if view_id == "Aad": return y.transpose(-1, -2).flip((-2, -1))  # self-inverse (F∘T)
    if view_id.startswith("Z"):
        return Zi(_apply_inverse(view_id[1:], y, torch_mod))
    raise KeyError(f"exp061: unknown view inverse {view_id}")


def exp061_arm_signature(arm):
    """Canonical, order-sensitive signature of an arm's TTA set (proposal §4.1)."""
    import hashlib
    views = EXP061_ARM_VIEWS[arm]
    payload = "exp061-v1|" + arm + "|" + ",".join(f"{v}:{int(sq)}" for v, sq in views)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def exp061_view_key(run_provenance, dataset, t, view_id, image_hash):
    """Module-level view-cache key (admission #1): provenance = impl-version + verified checkpoint
    hash (carried in run_provenance); input provenance = image content hash. The key is NOT a
    function of the arm -- shared views are reused across arms, but a different provenance,
    dataset/frame, view, or input image content yields a different key (negative-test-covered)."""
    import hashlib
    payload = f"{run_provenance}|{dataset}|{int(t)}|{view_id}|img={image_hash}"
    return hashlib.sha256(payload.encode()).hexdigest()


def _exp061_process_start_seconds():
    """(process_start_epoch_seconds, reliable); mirrors exp_060 -- unreliable timing fails closed."""
    import os
    import time
    try:
        import psutil  # noqa
        return float(psutil.Process(os.getpid()).create_time()), True
    except Exception:
        pass
    try:
        with open("/proc/self/stat") as fh:
            starttime_ticks = float(fh.read().split()[21])
        hz = os.sysconf("SC_CLK_TCK")
        with open("/proc/stat") as fh:
            for line in fh:
                if line.startswith("btime"):
                    return float(line.split()[1]) + starttime_ticks / hz, True
    except Exception:
        pass
    return time.time(), False


def run_exp061_zon_deployment(g: dict) -> dict:
    """Run only the frozen zon arm in the notebook namespace `g`."""
    import os
    import csv
    import json
    import time
    import math
    import hashlib
    from pathlib import Path
    from collections import Counter, OrderedDict

    import numpy as np

    if "_EXP061_RUN_START" in g:
        proc_start, timing_reliable = float(g["_EXP061_RUN_START"]), True
    else:
        proc_start, timing_reliable = _exp061_process_start_seconds()
    whole_run_watchdog_armed = bool(g.get("_EXP061_WATCHDOG_ARMED", False))

    def _elapsed():
        return time.time() - proc_start

    def _remaining():
        return EXP061_HARD_STOP_SECONDS - _elapsed()

    def _disarm_watchdog():
        try:
            import signal
            if hasattr(signal, "SIGALRM"):
                signal.alarm(0)
        except Exception:
            pass

    # -- prerequisites (fail closed if absent) ---------------------------------
    required = [
        "filter_output_graph", "graph_from_geff", "DEEPCENTER_VETO_DETECTOR",
        "test_stems", "CSV_COLUMNS", "REPO_DIR", "METHOD", "WORKING_DIR",
        "deepcenter_heatmap_for_frame", "deepcenter_accept_repair_point", "deepcenter_score_point",
        "read_test_frame", "_dc_pool_frame_xy", "_dc_normalize_dynamic_range", "_dc_cache_trim",
        "DEEPCENTER_SAFE_DIV_THRESHOLD", "MOTION_RELINK_TIGHT_UM",
    ]
    missing = [name for name in required if name not in g]
    if missing:
        raise RuntimeError(f"exp061: missing parent globals: {missing}")

    out_dir = Path(g["WORKING_DIR"]) / "exp061"
    out_dir.mkdir(parents=True, exist_ok=True)
    view_dir = Path(g["WORKING_DIR"]) / "exp061_viewcache"
    view_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = Path(g["WORKING_DIR"]) / "metrics.json"
    experiment_id = str(g.get("EXPERIMENT_ID", EXP061_EXPERIMENT_ID) or EXP061_EXPERIMENT_ID)

    # Parent DeepCenter TTA env must be ON (xyonly == parent path); the adaptive PP-sweep
    # (validator) must be OFF (admission #6 -- feasibility accounting requires it).
    _tta_env, _tta_val = EXP061_REQUIRE_PARENT_TTA_ENV
    parent_tta_on = os.environ.get(_tta_env, "0") == _tta_val
    _val_env, _val_val = EXP061_REQUIRE_VALIDATOR_DISABLED
    validator_disabled = os.environ.get(_val_env, "1") == _val_val

    _CONFIG_ENV_KEYS = ("BIOHUB_DEEPCENTER_TTA", "BIOHUB_SECONDARY_EDGE_FEATURE_TTA",
                        "BIOHUB_SECONDARY_EDGE_FEATURE_TTA_WEIGHT", "BIOHUB_EDGE_FEATURE_TTA",
                        "BIOHUB_VALIDATOR_ENABLE")

    def _capture_effective_config():
        cfg = {k: g[k] for k in EXP061_CONFIG_KEYS if k in g}
        for _envk in _CONFIG_ENV_KEYS:
            cfg["env:" + _envk] = os.environ.get(_envk)
        return cfg

    # -- pin resolved config (base env + tight55) ------------------------------
    for key, value in EXP061_RESOLVED_OVERRIDES.items():
        if key not in g:
            raise RuntimeError(f"exp061: cannot pin unknown global {key}")
        g[key] = value

    # INDEPENDENT frozen-parent reference (admission v3 #1): the parent's resolved 0.947 config is
    # NOT captured from this run. It is EXP061_FROZEN_PARENT_CONFIG -- the parent notebook's own knob
    # defaults (transcribed once, guarded by scripts/test_exp061_behavioral.py against the parent
    # notebook) with the documented tight55 override. Every started arm's LIVE knob config is
    # asserted EQUAL to this independent reference, key-by-key, fail-closed -- so the gate verifies
    # the STARTING values equal an independently frozen config, not merely that they stay constant
    # across arms. `live_parent_config_snapshot` (with env keys) is recorded for telemetry only.
    def _knob_config(cfg):
        # the knob subset (drop the informational `env:` entries) for the frozen-reference compare
        return {k: v for k, v in cfg.items() if not str(k).startswith("env:")}

    expected_parent_config = dict(EXP061_FROZEN_PARENT_CONFIG)   # independent reference (v3 #1)
    live_parent_config_snapshot = _capture_effective_config()   # telemetry-only (incl env keys)
    # up-front fail-closed check: the live pinned config must already equal the frozen reference
    # before ANY arm runs (missing/extra/diff knob -> gate fails, no wasted GPU on a mis-pinned run)
    live_knobs = _knob_config(live_parent_config_snapshot)
    live_config_equals_frozen_parent = (live_knobs == expected_parent_config)
    if not live_config_equals_frozen_parent:
        _diff = {k: (expected_parent_config.get(k), live_knobs.get(k))
                 for k in set(expected_parent_config) | set(live_knobs)
                 if expected_parent_config.get(k) != live_knobs.get(k)}
        print(f"[exp061] LIVE CONFIG != FROZEN PARENT (gate fails closed): {_diff}", flush=True)

    # checkpoint provenance (admission #1): REQUIRE the parent's verified deepcenter checkpoint
    # hash from its runtime-integrity report -- no silent placeholder fallback. If it cannot be
    # established, checkpoint_provenance_verified is False and the gate fails closed.
    verified_ckpt_sha = None
    integ_path = Path(g["WORKING_DIR"]) / EXP061_RUNTIME_INTEGRITY_FILE
    if integ_path.exists():
        try:
            verified_ckpt_sha = (json.loads(integ_path.read_text())
                                 .get("checkpoint_sha256", {}).get("deepcenter"))
        except Exception:
            verified_ckpt_sha = None
    checkpoint_provenance_verified = bool(verified_ckpt_sha)
    run_provenance = (f"exp061|impl={EXP061_TRANSFORM_IMPL_VERSION}|"
                      f"dcckpt={verified_ckpt_sha or 'MISSING'}")

    # ---------------------------------------------------------------------
    # View-level cache: raw model(T(x)) logits, lossless float32 on disk + bounded RAM LRU,
    # keyed (dataset,t,view,provenance). Retained for the whole run (arms are sequential).
    # ---------------------------------------------------------------------
    _ram_lru = OrderedDict()
    _view_sha = {}   # view-key -> sha256 of the stored logits (integrity validation, admission #1)
    view_stats = {"forward_calls": 0, "disk_hits": 0, "ram_hits": 0, "distinct_frames": set(),
                  "integrity_failures": 0, "nonfinite_view_logits": 0}
    # per-arm heatmap identity for the observed-response check + nonfinite detection at the tensor
    # level. EXECUTION validity (admission v2 #3) is tracked SEPARATELY from the observed response:
    # a correct arm can legitimately produce an identical heatmap (reflection-equivariant model) --
    # that is a valid NULL, not a failure. Execution evidence = the intended views actually ran.
    arm_heatmap_sha = {}      # (arm, dataset, t) -> sha256(heatmap bytes)  [observed response]
    arm_heatmap_sample = {}   # arm -> {(dataset,t): np.ndarray} for a few frames (|delta| stats)
    arm_views_seen = {"zon": set()}
    arm_frame_views_seen = {}
    arm_frame_square = {}
    nonfinite_heatmap_events = []   # (arm, dataset, t) with a non-finite heatmap/logits

    def _view_key(dataset, t, view_id, image_hash):
        return exp061_view_key(run_provenance, dataset, t, view_id, image_hash)

    def _digest(arr):
        return hashlib.sha256(np.ascontiguousarray(arr).tobytes()).hexdigest()

    def _compute_and_store(key, view_id, tensor, model, torch_mod):
        """Freshly compute model(T_view(tensor)); persist the array + a sidecar digest."""
        transformed = _apply_forward(view_id, tensor, torch_mod)
        out = model(transformed)
        arr = out.detach().to("cpu").numpy().astype(np.float32, copy=False)
        dig = _digest(arr)
        _view_sha[key] = dig
        if not np.isfinite(arr).all():
            view_stats["nonfinite_view_logits"] += 1
        np.save(view_dir / f"{key}.npy", arr)             # lossless persist; retained until run end
        (view_dir / f"{key}.sha256").write_text(dig)      # persisted expected digest (admission v2 #5)
        view_stats["forward_calls"] += 1
        return arr

    def _get_view_logits(dataset, t, view_id, image_hash, tensor, model, torch_mod, device):
        """Return model(T_view(tensor)) as a torch tensor on `device`, cached at view level.

        Raw model output stored losslessly (float32 .npy + a .sha256 sidecar) keyed by
        (impl_version, verified_ckpt_sha, dataset, t, view, image_hash). A cached entry is
        ACCEPTED only if its content digest matches the persisted/expected digest AND it is finite;
        otherwise it is REJECTED and recomputed BEFORE use (admission v2 #5)."""
        key = _view_key(dataset, t, view_id, image_hash)

        def _valid(arr, expected):
            return (arr is not None and expected is not None
                    and _digest(arr) == expected and bool(np.isfinite(arr).all()))

        arr = _ram_lru.get(key)
        if arr is not None:
            view_stats["ram_hits"] += 1
            if _valid(arr, _view_sha.get(key)):
                _ram_lru.move_to_end(key)
            else:                                          # reject-before-use -> recompute
                view_stats["integrity_failures"] += 1
                _ram_lru.pop(key, None)
                arr = _compute_and_store(key, view_id, tensor, model, torch_mod)
        else:
            fpath = view_dir / f"{key}.npy"
            spath = view_dir / f"{key}.sha256"
            if fpath.exists():
                view_stats["disk_hits"] += 1
                disk_arr = None
                try:
                    disk_arr = np.load(fpath)
                except Exception:
                    disk_arr = None
                expected = _view_sha.get(key)
                if expected is None and spath.exists():
                    try:
                        expected = spath.read_text().strip()
                    except Exception:
                        expected = None
                if _valid(disk_arr, expected):
                    arr = disk_arr
                    _view_sha[key] = expected
                else:                                      # missing/mismatched digest -> recompute
                    view_stats["integrity_failures"] += 1
                    arr = _compute_and_store(key, view_id, tensor, model, torch_mod)
            else:
                arr = _compute_and_store(key, view_id, tensor, model, torch_mod)
        _ram_lru[key] = arr
        _ram_lru.move_to_end(key)
        while len(_ram_lru) > EXP061_RAM_LRU_MAX_VIEWS:
            _ram_lru.popitem(last=False)
        view_stats["distinct_frames"].add((dataset, int(t)))
        return torch_mod.from_numpy(np.array(arr, copy=False)).to(device=device)

    _orig_heatmap_for_frame = g["deepcenter_heatmap_for_frame"]

    def _exp061_heatmap_for_frame(dataset, t, detector_bundle, frame_cache, heatmap_cache):
        """Per-arm heatmap via the view cache. For xyonly the accumulation is the parent's exact
        left-to-right order/ops -> byte-identical heatmap (given a deterministic model). The
        per-arm heatmap_cache (installed fresh per arm) is keyed (dataset,t)."""
        if detector_bundle is None:
            return None
        key = (dataset, int(t))
        cached = heatmap_cache.get(key)
        if cached is not None:
            return cached
        arm = _EXP061_ACTIVE_ARM["name"]
        model = detector_bundle["model"]
        cfg = detector_bundle["cfg"]
        device = detector_bundle["device"]
        torch_mod = detector_bundle["torch"]
        pool_factor = int(getattr(cfg, "pool_factor", 4))
        volume = g["read_test_frame"](dataset, int(t), frame_cache)
        pooled = g["_dc_pool_frame_xy"](volume, pool_factor)
        image = g["_dc_normalize_dynamic_range"](pooled, cfg)
        # input provenance: content hash of the (pooled, normalized) model input (admission #1)
        image_hash = hashlib.sha256(
            np.ascontiguousarray(np.asarray(image, dtype=np.float32)).tobytes()).hexdigest()
        with torch_mod.no_grad():
            tensor = torch_mod.from_numpy(image[None, None, ...]).to(device=device, dtype=torch_mod.float32)
            square = tensor.shape[-1] == tensor.shape[-2]
            views = EXP061_ARM_VIEWS[arm]
            frame_key = (arm, dataset, int(t))
            arm_frame_views_seen[frame_key] = []
            arm_frame_square[frame_key] = bool(square)
            acc = None
            nv = 0
            for view_id, square_only in views:
                if square_only and not square:
                    continue
                raw = _get_view_logits(dataset, t, view_id, image_hash, tensor, model, torch_mod, device)
                contrib = _apply_inverse(view_id, raw, torch_mod)
                acc = contrib.clone() if acc is None else acc + contrib
                nv += 1
                arm_views_seen.setdefault(arm, set()).add(view_id)   # execution evidence (#3)
                arm_frame_views_seen[frame_key].append(view_id)
            logits = acc / nv
            logits_finite = bool(torch_mod.isfinite(logits).all().item())
            heatmap = torch_mod.sigmoid(logits)[0, 0].detach().cpu().numpy().astype(np.float32, copy=False)
        # tensor-level nonfinite detection (admission #3): catch invalid heatmaps BEFORE any scorer
        # nulls the score into a "missing" bypass.
        if (not logits_finite) or (not np.isfinite(heatmap).all()):
            nonfinite_heatmap_events.append({"arm": arm, "dataset": dataset, "t": int(t)})
        # record heatmap identity for the REAL mechanism-active check (admission #2)
        arm_heatmap_sha[(arm, dataset, int(t))] = hashlib.sha256(
            np.ascontiguousarray(heatmap).tobytes()).hexdigest()
        samp = arm_heatmap_sample.setdefault(arm, {})
        if len(samp) < EXP061_HEATMAP_SAMPLE_FRAMES:
            samp[(dataset, int(t))] = heatmap
        heatmap_cache[key] = heatmap
        # preserve the parent's bounded per-movie heatmap retention (admission v2 #4 memory): the
        # parent calls _dc_cache_trim(heatmap_cache) here, else complete heatmaps accumulate.
        if "_dc_cache_trim" in g:
            g["_dc_cache_trim"](heatmap_cache)
        return heatmap

    # ---------------------------------------------------------------------
    # Central veto telemetry: wrap deepcenter_accept_repair_point (called at BOTH gap1 and
    # safe-div). Records (arm, dataset, t, kind, score, accept). Node IDs come from the strippable
    # call-site loggers injected at gap1 + safe-div. Heatmap diagnostics come from the arm store.
    # ---------------------------------------------------------------------
    _orig_accept = g["deepcenter_accept_repair_point"]
    veto_log = []          # one combined record per REAL veto call (ids + score + accept)
    _pending_ids = {"kind": None, "ids": None}   # stashed by the injected call-site logger (#4)

    def _accept_wrapper(dataset, t, point, detector_bundle, frame_cache, heatmap_cache,
                        stats, kind, threshold):
        arm = _EXP061_ACTIVE_ARM["name"]
        # score with the REAL caches the pipeline already populated (no fresh {} re-scoring, #4)
        score = None
        status = "ok"
        try:
            score = g["deepcenter_score_point"](dataset, None if t is None else int(t), point,
                                                detector_bundle, frame_cache, heatmap_cache)
        except Exception:
            status = "error"
        if score is None:
            if status != "error":
                status = "missing"
        elif not math.isfinite(float(score)):
            status = "nonfinite"
            score = None
        else:
            score = float(score)
        accept = _orig_accept(dataset, t, point, detector_bundle, frame_cache, heatmap_cache,
                              stats, kind, threshold)
        if arm is not None:
            # consume the IDs the injected logger stashed immediately before this call (#4): one
            # combined record links identity -> score -> acceptance for the ACTUAL veto.
            ids = _pending_ids["ids"] if _pending_ids["kind"] == str(kind) else None
            _pending_ids["kind"], _pending_ids["ids"] = None, None
            veto_log.append({
                "arm": arm, "dataset": dataset, "t": None if t is None else int(t),
                "kind": str(kind),
                "ids": None if ids is None else {k: (None if v is None else int(v)) for k, v in ids.items()},
                "deepcenter_score": score, "score_status": status, "accept": bool(accept),
                "survived_final": None,   # filled by a post-hoc join for safe_div candidates
            })
        return accept

    def _make_candidate_logger():
        # cheap: just stash the in-scope IDs for the veto call that immediately follows (#4).
        def _log(kind, dataset, t, ids, point):
            if _EXP061_ACTIVE_ARM["name"] is None:
                return
            _pending_ids["kind"], _pending_ids["ids"] = str(kind), dict(ids)
        return _log

    # -- helpers: forks + submission writer (faithful copy of write_test_submission) -----------
    def _forks_with_ids(edges):
        out = {}
        for e in edges:
            out.setdefault(int(e["source_id"]), []).append(int(e["target_id"]))
        return {s: sorted(ch) for s, ch in out.items() if len(ch) >= 2}

    # MEASURED per-dataset wall costs (admission v3 #4): the arm writer times every dataset and
    # gates on the measured running rate, so even the CONTROL arm's continuation is governed by
    # real measurements (not a zero-cost assumption). Keyed (arm, dataset).
    dataset_costs = {}

    def _view_cache_capacity():
        # measured on-disk view-cache capacity + I/O (admission v3 #4 "cache capacity/I/O")
        files = 0
        nbytes = 0
        try:
            for p in view_dir.glob("*.npy"):
                files += 1
                nbytes += p.stat().st_size
        except Exception:
            pass
        return {"disk_view_files": files, "disk_view_bytes": nbytes,
                "ram_lru_entries": len(_ram_lru), "ram_lru_max": EXP061_RAM_LRU_MAX_VIEWS,
                "forward_calls": view_stats["forward_calls"], "disk_hits": view_stats["disk_hits"],
                "ram_hits": view_stats["ram_hits"]}

    def _write_arm_submission(arm, out_path):
        _EXP061_ACTIVE_ARM["name"] = arm
        geffs = sorted((Path(g["REPO_DIR"]) / "predictions").glob(f"*/{g['METHOD']}/split_0/*.geff"))
        found = [p.stem for p in geffs]
        expected = set(g["test_stems"])
        if (len(geffs) != len(g["test_stems"]) or
                sorted(s for s, c in Counter(found).items() if c > 1) or
                sorted(expected - set(found)) or sorted(set(found) - expected)):
            raise RuntimeError(f"exp061 arm {arm}: unexpected prediction graphs")

        csv_columns = g["CSV_COLUMNS"]
        row_id = 0
        total_nodes = total_edges = 0
        per_dataset = {}
        n_ds = len(geffs)
        budget_aborted = False
        abort_note = ""
        # write to a temp path then os.replace -> the final arm CSV is created atomically
        # (admission #4); an interrupted arm never leaves a half-written final file.
        tmp_path = Path(str(out_path) + ".tmp")
        with open(tmp_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=csv_columns)
            writer.writeheader()
            for ds_i, geff_path in enumerate(geffs):
                ds_t0 = time.time()
                dataset = geff_path.stem
                graph = g["graph_from_geff"](geff_path)
                nodes_by_id = {}
                for row in graph.node_attrs().iter_rows(named=True):
                    nid = int(row["node_id"])
                    nodes_by_id[nid] = {"node_id": nid, "t": int(row["t"]),
                                        "z": float(row["z"]), "y": float(row["y"]), "x": float(row["x"])}
                raw_edges = []
                for row in graph.edge_attrs().iter_rows(named=True):
                    ep = row.get("edge_prob") if hasattr(row, "get") else None
                    raw_edges.append({"source_id": int(row["source_id"]),
                                      "target_id": int(row["target_id"]),
                                      "edge_prob": None if ep is None else float(ep)})
                nodes_by_id, edges, _stats = g["filter_output_graph"](
                    nodes_by_id, raw_edges, dataset=dataset,
                    deepcenter_bundle=g["DEEPCENTER_VETO_DETECTOR"],
                )
                if not nodes_by_id:
                    raise AssertionError(f"{dataset}: post-processing removed every node")
                for nid in sorted(nodes_by_id):
                    node = nodes_by_id[nid]
                    writer.writerow({"id": row_id, "dataset": dataset, "row_type": "node",
                                     "node_id": int(node["node_id"]), "t": int(node["t"]),
                                     "z": max(0, int(round(float(node["z"])))),
                                     "y": max(0, int(round(float(node["y"])))),
                                     "x": max(0, int(round(float(node["x"])))),
                                     "source_id": -1, "target_id": -1})
                    row_id += 1
                edge_set = set()
                indeg = {}
                outdeg = {}
                for edge in edges:
                    s = int(edge["source_id"]); tt = int(edge["target_id"])
                    if s not in nodes_by_id or tt not in nodes_by_id:
                        raise AssertionError(f"{dataset}: dangling edge after filtering")
                    # parent submission audits applied to EVERY arm (admission v2 #1): consecutive
                    # frame + lineage-degree (parent asserts max_indegree<=1, max_outdegree<=2).
                    if int(nodes_by_id[tt]["t"]) != int(nodes_by_id[s]["t"]) + 1:
                        raise AssertionError(f"{dataset}: non-consecutive-frame edge {s}->{tt}")
                    indeg[tt] = indeg.get(tt, 0) + 1
                    outdeg[s] = outdeg.get(s, 0) + 1
                    writer.writerow({"id": row_id, "dataset": dataset, "row_type": "edge",
                                     "node_id": -1, "t": -1, "z": -1, "y": -1, "x": -1,
                                     "source_id": s, "target_id": tt})
                    row_id += 1
                    edge_set.add((s, tt))
                if indeg and max(indeg.values()) > 1:
                    raise AssertionError(f"{dataset}: multi-parent (max in-degree > 1)")
                if outdeg and max(outdeg.values()) > 2:
                    raise AssertionError(f"{dataset}: invalid lineage degree (out-degree > 2)")
                total_nodes += len(nodes_by_id)
                total_edges += len(edges)
                # per-stage counters (admission v3 #2): gap1/gap2/safe-div node+edge additions and
                # DeepCenter bypass counts, straight from the parent's own stats dict.
                def _stat(k):
                    try:
                        return int(_stats.get(k, 0)) if hasattr(_stats, "get") else int(_stats[k])
                    except Exception:
                        return 0
                stage_stats = {stage: {k: _stat(k) for k in keys}
                               for stage, keys in EXP061_STAGE_STAT_KEYS.items()}
                per_dataset[dataset] = {"forks": _forks_with_ids(edges), "edge_set": edge_set,
                                        "n_edges": len(edges), "n_nodes": len(nodes_by_id),
                                        "stage_stats": stage_stats}
                # MEASURED per-dataset budget gate (admission v3 #4): time this dataset, then use the
                # measured mean per-dataset cost to project the remaining datasets. If finishing the
                # arm would breach the 20-min finalization reserve, abort CLEANLY between datasets
                # (discard the tmp CSV, publish nothing) -- a valid partial result governed by the
                # measured running rate, NOT a mid-dataset kill. This governs the CONTROL arm too, so
                # no arm's continuation assumes zero cost.
                dataset_costs[(arm, dataset)] = time.time() - ds_t0
                done = ds_i + 1
                datasets_left = n_ds - done
                _arm_ds_costs = [c for (a_, _d), c in dataset_costs.items() if a_ == arm]
                mean_ds = (sum(_arm_ds_costs) / len(_arm_ds_costs)) if _arm_ds_costs else 0.0
                projected_remaining = mean_ds * datasets_left
                if datasets_left > 0 and _remaining() < projected_remaining + EXP061_FINALIZATION_RESERVE_SECONDS:
                    budget_aborted = True
                    abort_note = (f"arm {arm}: measured budget abort after {done}/{n_ds} datasets "
                                  f"(remaining {_remaining():.0f}s < projected {projected_remaining:.0f}s "
                                  f"+ reserve {EXP061_FINALIZATION_RESERVE_SECONDS:.0f}s)")
                    print(f"[exp061] {abort_note}", flush=True)
                    break
        if budget_aborted:
            # publish nothing for this arm; discard the partial tmp CSV. The caller records the arm
            # as aborted_budget (a valid partial run), leaving prior completed arms intact.
            try:
                tmp_path.unlink()
            except Exception:
                pass
            _EXP061_ACTIVE_ARM["name"] = None
            return {"budget_aborted": True, "abort_note": abort_note,
                    "datasets_done": done, "datasets_total": n_ds}
        os.replace(tmp_path, out_path)   # atomic publish of the completed arm CSV (admission #4)
        _EXP061_ACTIVE_ARM["name"] = None
        # per-arm survival annotation BEFORE the receipt (admission v2 #2/#4 + v3 #2), for BOTH
        # DeepCenter veto consumers, so a partial run preserves identity-linked survival evidence:
        #   * safe_div SURVIVES iff the parent is a final fork AND BOTH the candidate daughter AND
        #     the recorded existing daughter are its children in this arm's final graph.
        #   * gap SURVIVES iff BOTH bridge edges (left->middle, middle->right) are in the final graph
        #     (a rejected gap drops its synthetic middle, so its edges are naturally absent).
        for r in veto_log:
            if r.get("arm") != arm or not r.get("ids"):
                continue
            ds_info = per_dataset.get(r["dataset"], {})
            if r.get("kind") == "safe_div":
                forks = ds_info.get("forks", {})
                pid = r["ids"].get("parent_id")
                ccid = r["ids"].get("candidate_child_id")
                ecid = r["ids"].get("existing_child_id")
                children = forks.get(int(pid), []) if pid is not None else []
                r["survived_final"] = bool(pid is not None and ccid is not None and ecid is not None
                                           and int(pid) in forks and int(ccid) in children
                                           and int(ecid) in children)
            elif r.get("kind") == "gap":
                edge_set = ds_info.get("edge_set", set())
                lid = r["ids"].get("left_id")
                mid = r["ids"].get("middle_id")
                rid = r["ids"].get("right_id")
                r["survived_final"] = bool(lid is not None and mid is not None and rid is not None
                                           and (int(lid), int(mid)) in edge_set
                                           and (int(mid), int(rid)) in edge_set)
        effective_config = _capture_effective_config()
        sha = hashlib.sha256(Path(out_path).read_bytes()).hexdigest()
        summary = {"sha256": sha, "rows": row_id, "nodes": total_nodes, "edges": total_edges,
                   "arm_signature": exp061_arm_signature(arm),
                   "effective_config": effective_config,
                   "config_complete": all(k in g for k in EXP061_CONFIG_KEYS),
                   "missing_config_keys": [k for k in EXP061_CONFIG_KEYS if k not in g],
                   "per_dataset": per_dataset}
        # atomic per-arm completion receipt (admission #4): status + sha/counts + this arm's veto
        # rows + view set, so a partial run preserves the agreed per-arm evidence on its own.
        arm_veto_rows = [r for r in veto_log if r.get("arm") == arm]
        receipt = {"arm": arm, "status": "completed", "sha256": sha, "rows": row_id,
                   "nodes": total_nodes, "edges": total_edges,
                   "arm_signature": summary["arm_signature"],
                   "views_run": sorted(arm_views_seen.get(arm, set())),
                   "n_veto_records": len(arm_veto_rows), "per_dataset": sorted(per_dataset), "veto_rows": arm_veto_rows}
        rc_tmp = out_dir / f"receipt_{arm}.json.tmp"
        with open(rc_tmp, "w") as rf:
            json.dump(receipt, rf, allow_nan=False, indent=2)
        os.replace(rc_tmp, out_dir / f"receipt_{arm}.json")
        return summary

    def _predictions_fingerprint():
        # CONTENT sha256 of the shared prediction inputs (admission #5): size/mtime cannot detect a
        # same-size in-place edit; the geffs are read-only inputs so a content hash is the honest
        # immutability check.
        base = Path(g["REPO_DIR"]) / "predictions"
        items = []
        if base.exists():
            for p in sorted(base.rglob("*")):
                if p.is_file():
                    items.append((str(p.relative_to(base)),
                                  hashlib.sha256(p.read_bytes()).hexdigest()))
        return hashlib.sha256(repr(items).encode()).hexdigest()

    def _write_metrics(integrity_passed, checks, arm_summaries, note="", extra=None):
        runtime_seconds = max(0.0, _elapsed())
        if runtime_seconds > EXP061_HARD_STOP_SECONDS:
            checks = dict(checks, within_hard_stop_and_timing_reliable=False)
            integrity_passed = False
            note = (note + " | commit-time over budget").strip(" |")
        metrics = {
            "schema_version": 1,
            "experiment_id": experiment_id,
            "validation": {"protocol": EXP061_VALIDATION_PROTOCOL},
            "runtime_seconds": runtime_seconds,
            "reproducible": False,
            "primary_metric": 1.0 if integrity_passed else 0.0,
            "primary_metric_meaning": "zon-only deployment integrity; no quality inference",

            "exp061_zon_deployment_integrity_passed": bool(integrity_passed),
            "checks": checks,
            "note": note,
            "arm_submission_sha256": {k: v["sha256"] for k, v in arm_summaries.items()},
            "arm_final_counts": {k: {"nodes": v["nodes"], "edges": v["edges"], "rows": v["rows"]}
                                 for k, v in arm_summaries.items()},
            "arm_signatures": {k: v["arm_signature"] for k, v in arm_summaries.items()},
            "parent_submission_sha256": EXP061_PARENT_SUBMISSION_SHA256,
            "pinned_overrides": EXP061_RESOLVED_OVERRIDES,
            "runtime_seconds_source": "process_start_to_now",
        }
        if extra:
            metrics.update(extra)
        with open(metrics_path, "w") as f:
            json.dump(metrics, f, allow_nan=False, indent=2)
        return metrics

    # -- install patches -------------------------------------------------------
    g["deepcenter_heatmap_for_frame"] = _exp061_heatmap_for_frame
    g["deepcenter_accept_repair_point"] = _accept_wrapper
    _stub_logger = g.get("_exp061_log_veto_candidate")
    g["_exp061_log_veto_candidate"] = _make_candidate_logger()

    pred_fp_before = _predictions_fingerprint()
    arm_summaries = {}
    arm_costs = {}
    arm_status = {"zon": "not_reached"}   # started/completed/skipped/failed (#4)
    stop_note = ""
    run_exception = None
    arms_started = []
    try:
        for arm in ("zon",):
            # budget-gated admission (admission v3 #4): don't START an arm unless the remaining
            # budget clears the measured prior-arm cost + the 20-min reserve. For arms 2+ `est` is
            # the largest MEASURED prior-arm cost (proposal §7 "measured running rate"). The CONTROL
            # arm (no prior arm cost) is not admitted on a zero-cost assumption: once started it is
            # governed by the MEASURED per-dataset budget gate inside _write_arm_submission, which
            # aborts cleanly between datasets if finishing would breach the reserve.
            est = max(arm_costs.values()) if arm_costs else 0.0
            need = est + EXP061_FINALIZATION_RESERVE_SECONDS
            if _remaining() < need:
                arm_status[arm] = "skipped"
                stop_note = (f"skip arm {arm}: remaining {_remaining():.0f}s < "
                             f"est {est:.0f}s + reserve {EXP061_FINALIZATION_RESERVE_SECONDS:.0f}s")
                print(f"[exp061] {stop_note}", flush=True)
                break
            arm_status[arm] = "started"
            arms_started.append(arm)   # recorded BEFORE running so an interrupted arm is visible
            t0 = time.time()
            try:
                _result = _write_arm_submission(arm, out_dir / f"submission_{arm}.csv")
            except BaseException:
                arm_status[arm] = "failed"
                raise
            arm_costs[arm] = time.time() - t0
            # measured per-dataset budget abort (admission v3 #4): a valid partial run, not a failure.
            if isinstance(_result, dict) and _result.get("budget_aborted"):
                arm_status[arm] = "aborted_budget"
                stop_note = _result.get("abort_note", f"arm {arm}: measured budget abort")
                print(f"[exp061] {stop_note}", flush=True)
                break
            arm_summaries[arm] = _result
            arm_status[arm] = "completed"
            s = arm_summaries[arm]
            print(f"[exp061] arm {arm}: sha={s['sha256'][:16]}... nodes={s['nodes']} "
                  f"edges={s['edges']} cost={arm_costs[arm]:.0f}s elapsed={_elapsed():.0f}s", flush=True)
            if arm == EXP061_CONTROL_ARM and s["sha256"] != EXP061_PARENT_SUBMISSION_SHA256:
                stop_note = "xyonly control parity mismatch - stopping before zon/xyd4"
                print(f"[exp061] {stop_note}", flush=True)
                break
    except BaseException as exc:
        run_exception = f"{type(exc).__name__}: {exc}"
        stop_note = stop_note or f"exception during probe: {run_exception}"
        print(f"[exp061] EXCEPTION: {run_exception}", flush=True)
    finally:
        g["deepcenter_heatmap_for_frame"] = _orig_heatmap_for_frame
        g["deepcenter_accept_repair_point"] = _orig_accept
        if _stub_logger is not None:
            g["_exp061_log_veto_candidate"] = _stub_logger
        _EXP061_ACTIVE_ARM["name"] = None

    # Deployment validates the zon intervention itself; cross-arm parity/mechanism
    # comparisons are development-only and deliberately absent from this scoring path.
    control = {}
    parity_ok = None
    mechanism = {}
    zon_summary = arm_summaries.get("zon", {})
    zon_views_expected_by_frame = {}
    frame_view_contract_ok = True
    for frame_key, actual_views in arm_frame_views_seen.items():
        _arm, _dataset, _t = frame_key
        _square = arm_frame_square[frame_key]
        _expected = [view_id for view_id, square_only in EXP061_ARM_VIEWS["zon"]
                     if not square_only or _square]
        zon_views_expected_by_frame[f"{_dataset}:{_t}"] = _expected
        if actual_views != _expected:
            frame_view_contract_ok = False
    zero_candidate_case = len(veto_log) == 0
    zon_view_execution_valid = bool(zon_summary) and (
        frame_view_contract_ok and
        (bool(arm_frame_views_seen) or zero_candidate_case)
    )
    started_experimental = ["zon"] if "zon" in arm_summaries else []
    all_started_execution_valid = (len(started_experimental) == 1
                                   and zon_view_execution_valid)

    pin_ok = float(g["MOTION_RELINK_TIGHT_UM"]) == 5.5
    within_deadline = timing_reliable and (_elapsed() <= EXP061_HARD_STOP_SECONDS)
    n_error = sum(1 for r in veto_log if r.get("score_status") == "error")
    n_nonfinite = sum(1 for r in veto_log if r.get("score_status") == "nonfinite")
    n_missing = sum(1 for r in veto_log if r.get("score_status") == "missing")
    veto_calls_accounted_for = all(
        r.get("score_status") == "ok" and isinstance(r.get("ids"), dict) and bool(r.get("ids"))
        for r in veto_log
    )
    shared_prediction_inputs_unchanged = (pred_fp_before == _predictions_fingerprint())

    # effective-config: every started arm's live KNOB config must equal the INDEPENDENT frozen-parent
    # reference EXP061_FROZEN_PARENT_CONFIG (admission v3 #1) -- a DIRECT comparison to a checked-in,
    # test-guarded table, not to a value captured from this run. (config_matches_control kept as an
    # extra cross-arm consistency signal; the up-front live_config_equals_frozen_parent guards the
    # pinned values BEFORE any arm runs.)
    def _cfg(label):
        return arm_summaries.get(label, {}).get("effective_config", {})
    all_config_complete = bool(arm_summaries) and all(s.get("config_complete") for s in arm_summaries.values())
    all_arm_configs_equal_frozen_parent = (bool(arm_summaries)
                                           and live_config_equals_frozen_parent
                                           and all(_knob_config(_cfg(a)) == expected_parent_config
                                                   for a in arm_summaries))

    # cross-arm deltas (full IDs) for attribution
    def _delta(base, arm):
        out = {}
        if base not in arm_summaries or arm not in arm_summaries:
            return out
        for ds in arm_summaries[base]["per_dataset"]:
            b = arm_summaries[base]["per_dataset"][ds]
            a = arm_summaries[arm]["per_dataset"][ds]
            b_forks = {(p, tuple(ch)) for p, ch in b["forks"].items()}
            a_forks = {(p, tuple(ch)) for p, ch in a["forks"].items()}
            # gap1/gap2/safe-div-SPECIFIC stage-counter deltas (admission v3 #2): attribute the edge
            # movement to the stage that produced it, which a single global edge delta cannot.
            b_stage = b.get("stage_stats", {})
            a_stage = a.get("stage_stats", {})
            stage_delta = {stage: {k: a_stage.get(stage, {}).get(k, 0) - b_stage.get(stage, {}).get(k, 0)
                                   for k in keys}
                           for stage, keys in EXP061_STAGE_STAT_KEYS.items()}
            out[ds] = {
                "d_forks": len(a_forks) - len(b_forks),
                "forks_added": [{"parent": p, "children": list(ch)} for p, ch in sorted(a_forks - b_forks)],
                "forks_removed": [{"parent": p, "children": list(ch)} for p, ch in sorted(b_forks - a_forks)],
                "d_edges": a["n_edges"] - b["n_edges"], "d_nodes": a["n_nodes"] - b["n_nodes"],
                "edges_added": [list(e) for e in sorted(a["edge_set"] - b["edge_set"])],
                "edges_removed": [list(e) for e in sorted(b["edge_set"] - a["edge_set"])],
                "stage_stat_delta": stage_delta,
            }
        return out

    view_forward_summary = {"forward_calls": view_stats["forward_calls"],
                            "disk_hits": view_stats["disk_hits"], "ram_hits": view_stats["ram_hits"],
                            "distinct_frames": len(view_stats["distinct_frames"]),
                            "integrity_failures": view_stats["integrity_failures"],
                            "nonfinite_view_logits": view_stats["nonfinite_view_logits"]}
    view_cache_integrity_ok = (view_stats["integrity_failures"] == 0
                               and view_stats["nonfinite_view_logits"] == 0)
    no_nonfinite_heatmaps = (len(nonfinite_heatmap_events) == 0)
    all_arm_configs_equal_parent = bool(all_arm_configs_equal_frozen_parent)  # direct frozen-parent compare

    # (safe_div fork-survival is annotated per-arm inside _write_arm_submission, BEFORE each
    # receipt, so a partial run preserves survival evidence -- admission v2 #2/#4.)

    # MEASURED feasibility worksheet (admission v3 #4): real per-arm AND per-dataset wall costs, the
    # per-forward rate, and measured view-cache capacity/I/O from THIS run -- so admission is gated
    # by measurement, not a pre-guessed estimate. Per-dataset costs are what the in-arm budget gate
    # uses to protect the 20-min reserve (governing the control arm from its first dataset onward).
    _ds_cost_by_arm = {}
    for (a_, d_), c_ in dataset_costs.items():
        _ds_cost_by_arm.setdefault(a_, {})[d_] = round(c_, 2)
    _all_ds_costs = list(dataset_costs.values())
    try:
        import resource
        process_peak_rss_bytes = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024
    except Exception:
        process_peak_rss_bytes = None
    feasibility_worksheet = {
        "process_peak_rss_bytes": process_peak_rss_bytes,
        "measured": True,
        "arm_costs_seconds": arm_costs,
        "dataset_costs_seconds_by_arm": _ds_cost_by_arm,
        "mean_seconds_per_dataset": (round(sum(_all_ds_costs) / len(_all_ds_costs), 2)
                                     if _all_ds_costs else None),
        "max_seconds_per_dataset": (round(max(_all_ds_costs), 2) if _all_ds_costs else None),
        "distinct_deepcenter_frames": len(view_stats["distinct_frames"]),
        "view_forward_calls": view_stats["forward_calls"],
        "seconds_per_view_forward": (sum(arm_costs.values()) / max(1, view_stats["forward_calls"]))
                                    if view_stats["forward_calls"] else None,
        "view_cache_capacity_io": _view_cache_capacity(),
        "elapsed_seconds": round(_elapsed(), 1),
        "remaining_seconds": round(_remaining(), 1),
        "finalization_reserve_seconds": EXP061_FINALIZATION_RESERVE_SECONDS,
        "hard_stop_seconds": EXP061_HARD_STOP_SECONDS,
        "admission_policy": ("arms 2+ START-gated on max measured prior-arm cost + 20-min reserve; "
                             "every arm (incl. control) governed by the measured per-dataset in-arm "
                             "budget gate that aborts cleanly between datasets to protect the reserve"),
    }

    # per-arm ABSOLUTE stage counters summed over datasets (admission v3 #2) + identity-linked veto
    # survival counts for BOTH consumers, so gap and safe-div survival is legible without re-joining.
    stage_stats_by_arm = {}
    for a, s in arm_summaries.items():
        agg = {stage: {k: 0 for k in keys} for stage, keys in EXP061_STAGE_STAT_KEYS.items()}
        for ds in s.get("per_dataset", {}).values():
            for stage, keys in EXP061_STAGE_STAT_KEYS.items():
                for k in keys:
                    agg[stage][k] += int(ds.get("stage_stats", {}).get(stage, {}).get(k, 0))
        stage_stats_by_arm[a] = agg
    veto_survival_summary = {}
    for a in arm_summaries:
        rows_a = [r for r in veto_log if r.get("arm") == a]
        for kind in ("gap", "safe_div"):
            kr = [r for r in rows_a if r.get("kind") == kind]
            veto_survival_summary.setdefault(a, {})[kind] = {
                "records": len(kr),
                "accepted": sum(1 for r in kr if r.get("accept")),
                "survived_final": sum(1 for r in kr if r.get("survived_final")),
                "id_linked": sum(1 for r in kr if r.get("ids")),
            }

    telemetry = {
        "experiment": experiment_id,
        "parent": "repro_059_public_0947_exact_copy",
        "pinned_overrides": EXP061_RESOLVED_OVERRIDES,
        "arms_started": arms_started,
        "arm_status": arm_status,
                          "zero_candidate_case": zero_candidate_case,
                          "zon_view_expected_by_frame": zon_views_expected_by_frame,
                          "veto_calls_accounted_for": veto_calls_accounted_for,
        "arm_costs_seconds": arm_costs,
        "stop_note": stop_note,
        "run_exception": run_exception,
        "parent_tta_env_on": parent_tta_on,
        "validator_sweep_disabled": validator_disabled,
        "checkpoint_provenance": {"verified": checkpoint_provenance_verified,
                                  "deepcenter_sha256": verified_ckpt_sha,
                                  "transform_impl_version": EXP061_TRANSFORM_IMPL_VERSION},
        "parity": {"applicable": False, "reason": "deployment-only run omits development replay"},
        "mechanism_active": mechanism,
        "deployment_only": True,
        "zero_candidate_case": zero_candidate_case,
        "zon_view_expected_by_frame": zon_views_expected_by_frame,
        "veto_calls_accounted_for": veto_calls_accounted_for,
        "nonfinite_heatmap_events": nonfinite_heatmap_events,
        "view_cache": view_forward_summary,
        "feasibility_worksheet": feasibility_worksheet,
        "config_equal_frozen_parent": all_arm_configs_equal_parent,
        "frozen_parent_config_reference": {
            "source": "EXP061_FROZEN_PARENT_CONFIG (independent, parent-notebook-derived, test-guarded)",
            "live_pinned_equals_frozen": bool(live_config_equals_frozen_parent),
            "live_config_snapshot": live_parent_config_snapshot,
        },
        "veto_counts": {"error": n_error, "nonfinite": n_nonfinite, "missing_bypass": n_missing,
                        "total": len(veto_log)},
        "stage_stats_by_arm": stage_stats_by_arm,             # gap1/gap2/safe-div absolute counters (#2)
        "veto_survival_summary": veto_survival_summary,       # gap + safe-div identity-linked survival (#2)
        "arms": {k: {kk: vv for kk, vv in v.items() if kk != "per_dataset"}
                 for k, v in arm_summaries.items()},
        "delta_vs_xyonly": None,
        # combined per-veto records (identity + score + acceptance + safe_div final survival, #4)
        "veto_telemetry_rows": veto_log,
    }
    tel_path = out_dir / "exp061_telemetry.json"
    telemetry_persisted = False
    try:
        with open(tel_path, "w") as f:
            json.dump(telemetry, f, allow_nan=False, indent=2)
        json.loads(tel_path.read_text())
        telemetry_persisted = True
    except Exception as exc:
        print(f"[exp061] telemetry persistence FAILED (gate fails closed): {exc}", flush=True)

    checks = {
        "deployment_runs_only_zon": arms_started == ["zon"] and arm_status.get("zon") == "completed",
        "all_discovered_test_datasets_completed": (arm_status.get("zon") == "completed" and set(zon_summary.get("per_dataset", {})) == set(g["test_stems"])),
        "parent_deepcenter_tta_env_on": parent_tta_on,
        "validator_sweep_disabled": validator_disabled,                         # admission #6
        "checkpoint_provenance_verified": checkpoint_provenance_verified,       # admission #1
        "view_cache_integrity_ok": view_cache_integrity_ok,                     # admission #1
        "zon_started": bool(arms_started) and arms_started[0] == "zon",
        "resolved_config_pinned_tight55": pin_ok,
        "config_complete_all_arms": all_config_complete,
        "live_pinned_config_equals_frozen_parent": bool(live_config_equals_frozen_parent),  # v3 #1
        "all_arm_configs_equal_parent": all_arm_configs_equal_parent,          # admission #5 (v3 #1)
        "experimental_arms_execution_valid": all_started_execution_valid,       # admission v2 #3
        "shared_prediction_inputs_unchanged": shared_prediction_inputs_unchanged,  # content-hash (#5)
        "all_veto_scores_finite_and_accounted": n_error == 0 and n_nonfinite == 0 and n_missing == 0 and veto_calls_accounted_for,
        "no_nonfinite_heatmaps": no_nonfinite_heatmaps,                         # admission #3
        "telemetry_persisted_and_valid": telemetry_persisted,
        "no_exception_during_probe": run_exception is None,
        "within_hard_stop_and_timing_reliable": within_deadline,
        "whole_run_watchdog_armed": whole_run_watchdog_armed,
    }
    integrity_passed = all(checks.values())
    note = stop_note or ("integrity PASS" if integrity_passed else "integrity FAIL")

    _write_metrics(integrity_passed, checks, arm_summaries, note=note,
                   extra={"mechanism_active": mechanism,
        "deployment_only": True,
        "zero_candidate_case": zero_candidate_case,
        "zon_view_expected_by_frame": zon_views_expected_by_frame,
        "veto_calls_accounted_for": veto_calls_accounted_for, "view_cache": view_forward_summary,
                          "arms_started": arms_started, "arm_status": arm_status,
                          "zero_candidate_case": zero_candidate_case,
                          "zon_view_expected_by_frame": zon_views_expected_by_frame,
                          "veto_calls_accounted_for": veto_calls_accounted_for,
                          "checkpoint_provenance_verified": checkpoint_provenance_verified,
                          "validator_sweep_disabled": validator_disabled,
                          "nonfinite_heatmap_events": len(nonfinite_heatmap_events),
                          "run_exception": run_exception, "telemetry_persisted": telemetry_persisted})
    print(f"[exp061-zon] integrity {'PASS' if integrity_passed else 'FAIL'}; deployment_only=True; "
          f"arms={arms_started}; mechanism={mechanism}; note={note!r}; runtime={_elapsed():.0f}s; "
          f"wrote {metrics_path}", flush=True)
    _disarm_watchdog()
    return telemetry


# Injection contract (builder scripts/build_exp061_deepcenter_tta.py):
#   0. Inject at the TOP of the parent code cell, BEFORE the parent reads BIOHUB_VALIDATOR_ENABLE
#      (strippable `# exp061`) -- disables the adaptive PP-sweep (validator) which is pure overhead
#      here (the xyonly replay pins tight55 itself), reconciling the feasibility accounting:
#        os.environ['BIOHUB_VALIDATOR_ENABLE'] = '0'  # exp061
#   1. Inject at the TOP of the parent code cell (strippable `# exp061`):
#        _exp061_log_veto_candidate = (lambda *a, **k: None)  # exp061 stub
#   2. Inject one line immediately BEFORE the gap1 DeepCenter veto call (close_single_frame_gaps),
#      passing the in-scope IDs (strippable `# exp061`):
#        _exp061_log_veto_candidate('gap', dataset, mid_t, {'middle_id': middle_id, 'left_id': source_id, 'right_id': target_id, 'reused': int(middle_reused)}, node_point(middle))  # exp061
#   3. Inject one line immediately BEFORE the safe-div DeepCenter veto call
#      (add_safe_divisions_postlink), passing the in-scope IDs (strippable `# exp061`):
#        _exp061_log_veto_candidate('safe_div', dataset, int(candidate['t']), {'parent_id': source_id, 'existing_child_id': existing_child_id, 'candidate_child_id': candidate_id}, node_point(candidate))  # exp061
#   4. Append this module source as one cell, then a final cell with the guarded top-level call:
#        import os
#        os.environ.setdefault('BIOHUB_EXP061_ENABLE', '1')
#        if os.environ.get('BIOHUB_EXP061_ENABLE', '0') == '1':
#            _exp061_telemetry = run_exp061_deepcenter_tta(globals())
#        else:
#            print('[exp061] BIOHUB_EXP061_ENABLE != 1 - TTA probe skipped (parent path only).')
# Stripping every line containing the `# exp061` marker reproduces the parent notebook exactly.

## Snapshot notebook cell 4: final publication and graph audit

# Publish only the zon result produced by this execution.
import csv as _zon_csv
import hashlib as _zon_hashlib
import json as _zon_json
import os as _zon_os
import shutil as _zon_shutil
from pathlib import Path as _zon_Path

_zon_target = _zon_Path(SUBMISSION_PATH)
if _zon_target.exists():
    _zon_target.unlink()
_zon_telemetry = run_exp061_zon_deployment(globals())
_zon_work = _zon_Path(WORKING_DIR)
_zon_metrics = _zon_json.loads((_zon_work / "metrics.json").read_text())
if not _zon_metrics.get("exp061_zon_deployment_integrity_passed"):
    raise RuntimeError("Refusing publication: zon deployment integrity failed")
if not _zon_metrics.get("checks", {}).get("all_discovered_test_datasets_completed"):
    raise RuntimeError("Refusing publication: not every discovered test dataset completed")
if _zon_metrics.get("arm_status", {}).get("zon") != "completed":
    raise RuntimeError("Refusing publication: zon arm did not complete")
if _zon_metrics.get("run_exception") is not None:
    raise RuntimeError("Refusing publication: zon runner recorded an exception")
if not _zon_metrics.get("veto_calls_accounted_for"):
    raise RuntimeError("Refusing publication: veto score receipts are incomplete")

_zon_csv_path = _zon_work / "exp061" / "submission_zon.csv"
_zon_receipt_path = _zon_work / "exp061" / "receipt_zon.json"
_zon_receipt = _zon_json.loads(_zon_receipt_path.read_text())
_zon_expected_datasets = sorted(str(s) for s in test_stems)
if _zon_receipt.get("status") != "completed":
    raise RuntimeError("Refusing publication: zon receipt is incomplete")
if sorted(_zon_receipt.get("per_dataset", [])) != _zon_expected_datasets:
    raise RuntimeError("Refusing publication: zon receipt dataset set differs from test discovery")
_zon_digest = _zon_hashlib.sha256(_zon_csv_path.read_bytes()).hexdigest()
if _zon_digest != _zon_receipt.get("sha256"):
    raise RuntimeError("Refusing publication: zon CSV digest differs from receipt")
if _zon_digest != _zon_metrics.get("arm_submission_sha256", {}).get("zon"):
    raise RuntimeError("Refusing publication: zon CSV digest differs from metrics")

with _zon_csv_path.open("r", newline="", encoding="utf-8") as _zon_fh:
    _zon_reader = _zon_csv.DictReader(_zon_fh)
    if _zon_reader.fieldnames != list(CSV_COLUMNS):
        raise RuntimeError("Refusing publication: CSV schema differs from competition header")
    _zon_rows = list(_zon_reader)
if not _zon_rows or len(_zon_rows) != int(_zon_receipt.get("rows", -1)):
    raise RuntimeError("Refusing publication: zon CSV row count is empty or inconsistent")
_zon_integer_columns = ("id", "node_id", "t", "z", "y", "x", "source_id", "target_id")
_zon_ids = []
_zon_nodes = {}
_zon_edges = {}
for _zon_line, _zon_row in enumerate(_zon_rows, start=2):
    if None in _zon_row or set(_zon_row) != set(CSV_COLUMNS):
        raise RuntimeError(f"Refusing publication: malformed CSV columns on row {_zon_line}")
    if any(_zon_row.get(name) is None or _zon_row.get(name) == "" for name in CSV_COLUMNS):
        raise RuntimeError(f"Refusing publication: empty CSV field on row {_zon_line}")
    try:
        _zon_values = {name: int(_zon_row[name]) for name in _zon_integer_columns}
    except (TypeError, ValueError) as _zon_exc:
        raise RuntimeError(f"Refusing publication: non-integer CSV field on row {_zon_line}") from _zon_exc
    _zon_ids.append(_zon_values["id"])
    _zon_ds = _zon_row["dataset"]
    if not _zon_ds:
        raise RuntimeError(f"Refusing publication: empty dataset on row {_zon_line}")
    if _zon_row["row_type"] == "node":
        if _zon_values["source_id"] != -1 or _zon_values["target_id"] != -1:
            raise RuntimeError(f"Refusing publication: invalid node sentinels on row {_zon_line}")
        if min(_zon_values[name] for name in ("node_id", "t", "z", "y", "x")) < 0:
            raise RuntimeError(f"Refusing publication: negative node field on row {_zon_line}")
        _zon_ds_nodes = _zon_nodes.setdefault(_zon_ds, {})
        if _zon_values["node_id"] in _zon_ds_nodes:
            raise RuntimeError(f"Refusing publication: duplicate node on row {_zon_line}")
        _zon_ds_nodes[_zon_values["node_id"]] = _zon_values["t"]
    elif _zon_row["row_type"] == "edge":
        if any(_zon_values[name] != -1 for name in ("node_id", "t", "z", "y", "x")):
            raise RuntimeError(f"Refusing publication: invalid edge sentinels on row {_zon_line}")
        if min(_zon_values["source_id"], _zon_values["target_id"]) < 0:
            raise RuntimeError(f"Refusing publication: negative edge endpoint on row {_zon_line}")
        _zon_edges.setdefault(_zon_ds, []).append((_zon_values["source_id"], _zon_values["target_id"]))
    else:
        raise RuntimeError(f"Refusing publication: invalid row type on row {_zon_line}")
if _zon_ids != list(range(len(_zon_ids))) or not _zon_ids or not _zon_nodes:
    raise RuntimeError("Refusing publication: CSV IDs are invalid or CSV has no node data")
if set(_zon_nodes) != set(_zon_expected_datasets):
    raise RuntimeError("Refusing publication: CSV dataset set differs from test discovery")
for _zon_ds, _zon_ds_edges in _zon_edges.items():
    _zon_seen_edges = set()
    _zon_indegree = {}
    _zon_outdegree = {}
    for _zon_source, _zon_target_id in _zon_ds_edges:
        _zon_edge = (_zon_source, _zon_target_id)
        if _zon_edge in _zon_seen_edges:
            raise RuntimeError("Refusing publication: duplicate graph edge")
        _zon_seen_edges.add(_zon_edge)
        _zon_ds_nodes = _zon_nodes.get(_zon_ds, {})
        if _zon_source not in _zon_ds_nodes or _zon_target_id not in _zon_ds_nodes:
            raise RuntimeError("Refusing publication: graph edge endpoint is missing")
        if _zon_ds_nodes[_zon_target_id] != _zon_ds_nodes[_zon_source] + 1:
            raise RuntimeError("Refusing publication: graph edge is not between adjacent frames")
        _zon_outdegree[_zon_source] = _zon_outdegree.get(_zon_source, 0) + 1
        _zon_indegree[_zon_target_id] = _zon_indegree.get(_zon_target_id, 0) + 1
    if max(_zon_indegree.values(), default=0) > 1 or max(_zon_outdegree.values(), default=0) > 2:
        raise RuntimeError("Refusing publication: lineage degree constraint failed")
_zon_tmp = _zon_target.with_name(_zon_target.name + ".zon.tmp")
_zon_shutil.copyfile(_zon_csv_path, _zon_tmp)
if _zon_hashlib.sha256(_zon_tmp.read_bytes()).hexdigest() != _zon_digest:
    _zon_tmp.unlink(missing_ok=True)
    raise RuntimeError("Refusing publication: staged submission digest mismatch")
_zon_os.replace(_zon_tmp, _zon_target)
print("Published current-run zon submission:", _zon_digest)

## Local validator result

The snapshot local validator passed source/AST parity, positive and failure-injection publication checks, exact zon view-order fixture, missing-score and missing-dataset rejection, zero-veto full traversal, and 4x dataset-count correctness fixture. The 4x fixture is not a runtime or hidden-size proof. Formal snapshot smoke remains pending until admission PASS by controller order.
