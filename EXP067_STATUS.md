# exp067 status and handoff

<!-- BEGIN EP068 CURRENT -->
## Current ep068 status - 2026-09-27T04:40Z

**The authorized ep015 LB probe is DONE and SUBMITTED: `56597763`, PENDING.**
`exp_068_ep015_single_probe` is collected, independently audited **PASS**, remote-source bound,
controller state `KEEP`. 1415.64 s = 0.393 GPU h; ledger 29.606766 h, no reservations.
Output sha `f09854c3`, the lever fired (4163 weak edges dropped, -7335 edges, forks 62 -> 47).

**The single-submission authorization is now SPENT. Do not submit again.** Any earlier text in this
file directing you to carry out the pre-authorized ep015 leaderboard submission is **superseded** -
that action has been performed.

Next: **do not poll.** Wait for the user to report the score, read it back once from authenticated
`kaggle competitions submissions`, record it in `SUBMISSION_BUDGET.json` (entry 18) and
`STATE.json.exp068_ep015_submission`, then apply the pre-registered rule vs retained 0.953:
**>=0.955 adopt; 0.954 small real gain; 0.953 NULL keep exp_064 and close the `ep` family;
<=0.952 revert.** No second probe, no final re-selection, no exp067 training, no public push
without fresh authorization. Deadline 2026-09-29 23:59 NY.

**Full detail, gate evidence and the honest two-sided read of the ep015 evidence live in
`HANDOUT.md`'s CURRENT STATE block.** `STATE.json` remains authoritative.
Retained best is still 56535761 at recorded 0.953 until 56597763 resolves.
exp067 training remains stopped. The CPU counterfactual is complete and is GT-assisted TRAIN
diagnosis only: `docs/research/ep015_continuation_2026-09-26/division_counterfactual_report.md`.
<!-- END EP068 CURRENT -->
## Current closeout - 2026-09-26 (supersedes historical directives below)

Local closeout is complete. Read `PLAN.md` v4 and
`docs/research/closeout_review_2026-09-26.md`; `STATE.json` owns current status.
exp067d is EVALUATED, export complete; exp067 is stopped for this competition.
Retain exp064 submission 56535761, recorded Public LB 0.953. No training, GPU launch,
submission, successor preparation or public push is authorized. ep015 remains OFF.
Ledger remaining is 16.752765 h with no reservations. Next: verify the final selection
on the site before close; this closeout did not verify live selection or remote quota.
The corrected CPU audit reproduces scorer TP/FP/FN 3/2/9 and separates those semantics
from two exact direct-edge events. Geometry-only controls give 4/7 for tau-off alone
and 7/7 with distance14 plus tau-off; they do not establish decoded performance.
Historical RUNNING, next-launch and broad causal claims below are superseded.
Review waivers remain historical NO_PASS, never retroactively converted to PASS.


Updated: 2026-09-26, after the v3 revision. Technical documentation is English as required by
AGENTS.md. This supersedes the 2026-09-26 morning version of this file, which described the
exp067b BLOCK as the current state.

## 0. One-paragraph state

The four **code and record** findings of the exp067b admission BLOCK are fixed, and
**`exp_067c_temporal_feature_export_v3`** is frozen, snapshotted and **LAUNCHED**. Kernel
`lingxd/biohub-exp067c-temporal-export` v1 was pushed at 2026-09-26T17:05:35Z and is RUNNING;
2.0 GPU h are reserved. Twenty-two local tests pass, including eight new ones that *execute* the new
runtime gates and prove each rejects drift.

**The Codex admission review was WAIVED BY THE USER, not passed.** The review was requested and
failed part-way through on a Codex CLI usage limit without producing a verdict; the user then
instructed a direct push. The record carries `review.status =
WAIVED_BY_USER_FOR_ONE_EXPORT_KERNEL_RUN` and `verdict: NO_PASS`. **No PASS exists and none is
claimed.** The generic controller path still refuses to launch without one — this run went through
the tracked one-time waiver script `scripts/launch_exp067c_user_waiver.py`, which executes every
other gate rather than skipping it. Export only: no TEST inference, no sweep, no submission, no
promotion.

## 1. What we are trying to achieve

Unchanged. The objective is a substantial accuracy improvement over **exp064, Public LB 0.953**,
through an architectural change the user selected knowing it may fail: **a learned temporal
association/division model with joint lineage decoding**, built on exp064.

The hypothesis is that exp064's staged graph repair can retain an incorrect continuation that
occupies a true daughter. A learned multi-frame model, with joint competition between continuations
and divisions, may recover those cases and reduce fragmentation. **There is no numerical gain claim
yet and none may be made until the head is trained and decoded.**

The intended architecture (frozen detections and final node IDs, measured evidence export,
seven-frame temporal context, a real division head, joint MILP decoding, preserved unsupported
graph regions) is unchanged from the v1 brief; see
[proposal v1](experiments/exp_067_temporal_joint_lineage/proposal_v1.md) and the
[architecture brief](experiments/exp_067_temporal_joint_lineage/architecture_brief_v1.md).
Defaults live in [the runtime config](configs/exp_067_temporal_joint_lineage.json).

## 2. Record lineage — which one is current

| Record | Role | State |
|---|---|---|
| `exp_067_temporal_joint_lineage` | architecture, implementation and development records | locally implemented; no real-data training |
| `exp_067a_temporal_feature_export` | first frozen export attempt | never launched; admission `REVISE` |
| `exp_067b_temporal_feature_export_v2` | second frozen export attempt | never launched; admission `BLOCK` |
| **`exp_067c_temporal_feature_export_v3`** | **current frozen export attempt** | **`SUBMITTED`; kernel v1 RUNNING since 2026-09-26T17:05:35Z; admission review WAIVED BY USER, `verdict: NO_PASS`** |

exp067a and exp067b keep their own snapshots, configs and reviews. Nothing in v3 rewrites them, and
no historical verdict was changed.

Current frozen source:
[export_v3.ipynb](experiments/exp_067c_temporal_feature_export_v3/snapshot/source/export_v3.ipynb),
SHA256 `ce2bcf4068890523296e81fe39cbe83f2a2fe545c77375bab011f1d2fca855fe`, 16 code cells, zero saved
error outputs. Current frozen config:
[snapshot/config.yaml](experiments/exp_067c_temporal_feature_export_v3/snapshot/config.yaml).
Generator: [`scripts/prepare_exp067_export_v3.py`](scripts/prepare_exp067_export_v3.py).

## 3. What the exp067b BLOCK required, and what was done

Source: [exp067b review](experiments/exp_067b_temporal_feature_export_v2/review.md), VERDICT BLOCK
at 2026-09-26 13:42:48 UTC. All five required changes were accepted; none was disputed.

**1 — Record explicit consensus on the remote-trial amendment.** Done, as a new versioned strategy
record: [`remote_trial_amendment_v3.md`](experiments/exp_067_temporal_joint_lineage/remote_trial_amendment_v3.md).
The objection was factually right: `revision_acceptance_v2.md` limits its own consensus scope to
"local architecture, local implementation, local validation", so citing it as the strategy record
for a remote run overstated what had been agreed. The new record states the amendment exactly
(real-data parent parity moves from a pre-launch prerequisite to an in-run acceptance gate),
explains why the prerequisite form was unsatisfiable rather than merely inconvenient, answers each
of the five objections, and marks **CONSENSUS** on the remote-trial protocol. The v3 config points
`strategy_record` and `revision_record` at it.

**2 — Assert effective predictor arguments and resolved postprocessing settings against the frozen
parent.** Done, and this was the substantive one.

- New module [`scripts/exp067_parent_config.py`](scripts/exp067_parent_config.py): a
  side-effect-free static evaluator that resolves the frozen exp064 notebook's own assignments
  against its own frozen environment. The expected table is **derived from the parent source at
  build time**, so it cannot drift from the parent by hand. It refuses to resolve a global against
  an environment value a later cell rewrites.
- A new **effective-configuration gate** is injected into the validator cell after every
  configuration global is bound and after `predict_val_cmd` is fully assembled, but **before** the
  predictor subprocess starts. It asserts **126 resolved globals** and the complete **23-argument
  predictor argv**, rebuilding the argv from the frozen expectation so a drifted global cannot
  validate itself. Type is compared as well as value.
- Exactly **one** declared difference, checked rather than exempted: `BIOHUB_VALIDATOR_ENABLE`
  `'0' -> '1'` and the `VALIDATOR_ENABLE` `False -> True` it produces. The export reaches TRAIN
  movies only through the validator path x138 switches off.
- The gate also fails on any `BIOHUB_*`/`V1284_*` key the frozen parent never set, apart from
  additive `BIOHUB_EXP067_*` keys.
- The 19 globals deliberately **not** asserted (Kaggle-mount paths, loaded model bundles,
  comprehensions, wall clock) are enumerated with their source text in the metrics, not dropped
  silently.
- The gate cannot be skipped: the export asserts `VALIDATOR_ENABLE is True and val_stems` at the top
  of the cell, and the final metrics gate refuses to pass unless the configuration gate ran.
- **A real defect was found and fixed in passing.** exp067b asserted `BIOHUB_DEEPCENTER_CHECKPOINT`
  against the cell-0 literal, but parent cell 3 **overwrites** that key with the path it
  materializes. v3 treats the three runtime-resolved keys (`BIOHUB_DEEPCENTER_CHECKPOINT`,
  `BIOHUB_SECONDARY_WEIGHTS`, `V1284_HEAD`) as presence-and-file checks and records the observed
  values; their bytes are already pinned by the checkpoint hashes asserted in the same cell.

**3 — Persist observed dependency hashes and package versions in metrics.** Done. The dependency
cell builds `_x67_observed_dependencies`: observed checkpoint hashes, observed support-repo
manifest hash and file count, materialized paths, the observed V1284 head hash, the runtime-resolved
environment, observed versions for every package in the parent's `PACKAGE_SPECS` plus
torch/numpy/scipy, Python version, platform, torch CUDA version and GPU names. Metrics now carry it
beside `expected_parent_checkpoints` and `expected_support_repo_python_manifest_sha256` —
expected and observed both present, separately labelled.

**4 — Correct the split name and the reservation statement.** Done; both were wrong.

- The split is a **within-prefix movie holdout**, renamed in `splits_v2.json`, in the config
  (`validation.split_protocol`), in the metrics contract, in the README, and in
  `scripts/exp067/supervise.py`, where the constant itself was called `PROTOCOL_LOMO`. The old
  spelling is kept as a legacy alias so frozen historical manifests keep loading. It is a
  within-domain holdout and **cannot** establish cross-domain generalization.
- The budget is **planned, not reserved**. `admission_revision_v2.md` said "Two GPU hours reserved"
  while the record said `reserved: false`. The v3 config says the controller reserves 2.0 h at the
  launch gate, and that reservation is a real step in §6, not a sentence.
- The limited scope of the representative parity check is retained verbatim in the config, the
  notebook and the metrics field `representative_parent_parity_scope`: it reuses the instrumented
  raw graphs, so it evidences **postprocessing preservation only**, not detector or association
  equivalence.

**5 — Complete snapshot smoke and controller reservation before launch.** Done, under the user
waiver. The waiver script re-ran the configured smoke command and the full behavioral suite against
the pinned snapshot hash, verified snapshot integrity and the Kaggle target, refused to proceed if
`leaderboard.authorized` were true, and reserved 2.0 GPU h before pushing. Receipt:
`experiments/exp_067c_temporal_feature_export_v3/user-waiver-smoke.json`. What was **not** done is
the admission review itself.

## 4. Validation actually executed

```powershell
.\.private\runtime\exp067_cpu\Scripts\python.exe -m pytest tests/test_exp067.py `
  tests/test_exp067c_admission.py -q --basetemp .private/runtime/exp067_test05 --tb=short
```

Result: **22 passed in 5.04 s**. Environment: Python 3.12, torch 2.14.0+cpu, scipy 1.18.1,
numpy 2.5.3, pytest 9.1.1.

- The **14 pre-existing** behavioral tests were re-run after the final admission revisions. The
  previous handoff correctly flagged that this had not happened; it has now.
- The **8 new** tests in [`tests/test_exp067c_admission.py`](tests/test_exp067c_admission.py)
  execute the generated gates rather than pattern-matching them. They check that the frozen
  notebook is byte-identical to what the builder produces, that the gates run before any
  `subprocess` launch, and that the gates actually reject: a drifted global, a bool silently
  standing in for an int, a missing global, a reverted declared difference, a drifted environment
  value, a stray `BIOHUB_*` key, a missing runtime checkpoint file, a drifted predictor argument, a
  dropped `--use-ilp`, and a stripped `PYTHONPATH`.

Controller notebook validation on the frozen snapshot: **16 code cells, 0 saved error outputs**,
metrics contract present in the final code cell. This is the same command the controller smoke test
runs, but the formal `smoke_test.status` stays `PENDING` because the controller will not run it
before an admission `PASS`.

These establish local implementation behavior. They say nothing about Kaggle runtime compatibility
or about biological accuracy.

## 5. What has NOT been done

- **No fresh admission `PASS`.** The review attempt failed on a usage limit before producing a
  verdict, and the user waived the gate. This is the one gate this run does not clear.
- The export result is **not yet collected or verified**; the kernel is still running.
- No new temporal/division head has been trained on competition movies.
- No real-data held-out score, no Public LB score, no submission, no promotion.
- GPU: 2.0 h **reserved**, not yet consumed. Ledger remaining before consumption: 17.386695 h.

## 6. Remaining work, in order

1. **Wait for kernel `lingxd/biohub-exp067c-temporal-export` v1 to finish** (5400 s watchdog).
   Failure modes, cheapest first: the watchdog cell needs `psutil` (fails in seconds at ~0 cost);
   the dependency gate runs before inference (fails in minutes); the new effective-configuration
   gate runs after globals bind but before the predictor subprocess starts (fails in minutes). A
   strict gate tripping early is a cheap, designed outcome, not a loss.
2. Collect with `kaggle kernels output lingxd/biohub-exp067c-temporal-export`; verify the recorded
   export, configuration and parity gates; book the **actual** hours in `GPU_BUDGET.json` and
   release the 2.0 h reservation.
3. Optional but recommended once the Codex allowance resets: run the admission review anyway, as a
   post-hoc audit of the snapshot that ran. It cannot un-run the kernel, but it is the honest way to
   close the waived gate before anything is built on the export.

### After a successful export

1. Collect the raw artifacts; verify the recorded export, configuration and parity gates and the
   actual GPU consumption; book the actual hours in `GPU_BUDGET.json`.
2. Train the temporal/link/division head on the six training movies. **Stop if supervision is
   insufficient**; do not invent labels and do not silently fit on the held-out movies.
3. Decode the two held-out movies and compare against exp064 with the preserved parent metric and
   the graph audits.
4. Inspect whether true missed divisions and fragmentation improve, along with aggregate and
   per-prefix regressions. Synthetic smoke success is not a quality result, and a score from this
   split is a biased local proxy, not pristine validation.
5. Only if the evidence justifies it, prepare a separate learned-decoder inference experiment. A
   leaderboard submission and any promotion require their own authorization and gates.

## 7. What the first Kaggle run actually does

A **prerequisite feature export**, not a trained-model submission. It runs the frozen exp064
pipeline on eight explicit competition TRAIN movies and saves features, alternatives, final graphs
and allowed labels, then emits a Boolean engineering gate. No TEST inference, no sweep, no
submission.

| Group | Movie stems |
|---|---|
| Training, 44b6 | `44b6_12dfb391`, `44b6_267148e4`, `44b6_2a2eff9f` |
| Training, 6bba | `6bba_062c8d37`, `6bba_07e24132`, `6bba_085bf656` |
| Held out | `44b6_341df25f`, `6bba_09961292` |

Within-prefix movie holdout: six training, two held out, both prefixes on both sides. Not
cross-domain validation, not a cross-validation loop. The movie pool inherits historical label
enrichment and the frozen backbone's overlap with it is unknown; every later score must carry those
limitations.

The v3 notebook carries: the parent's pinned CUDA image and the same four public dataset mounts;
parent primary/secondary/DeepCenter hashes and the support-repo manifest check; the pinned V1284
head hash `625a0d9340f48193f2ec294fc2d81c5bb3c03087eab78ef0ae998a9c4c7da00c` (the historical exp064
head hash was never recorded, so byte identity with it is **unknown, not asserted**); the
effective-configuration gate of §3 item 2; explicit TRAIN/TEST exclusion with no sweep and no TEST
submission; both-role feature eligibility and final export reconciliation; representative
disabled-hook postprocessing comparison on one movie per prefix; a 5400-second watchdog that kills
descendant predictor processes and exits; and a Boolean controller gate written only after the
final checks.

## 8. Navigation

- [Remote-trial amendment v3 and CONSENSUS](experiments/exp_067_temporal_joint_lineage/remote_trial_amendment_v3.md) — the current strategy record
- [Local consensus v2](experiments/exp_067_temporal_joint_lineage/revision_acceptance_v2.md) — still in force for all local work
- [Implementation and command guide](experiments/exp_067_temporal_joint_lineage/README.md)
- [Current execution record](experiments/exp_067c_temporal_feature_export_v3/experiment.json)
- [Previous admission findings](experiments/exp_067b_temporal_feature_export_v2/review.md)
- [v3 generator](scripts/prepare_exp067_export_v3.py) and [parent-config resolver](scripts/exp067_parent_config.py)
- [New gate tests](tests/test_exp067c_admission.py)

## 9. Stale-record cautions

Older local notes still refer to exp067a as awaiting review, to exp067b as current, or to remote
execution as unauthorized; they predate this revision. Some prose in Claude's original acceptance
document described planned tests as already completed before they ran. Use the dated evidence above
and the controller records for actual status. This document does not rewrite historical reviews or
change any admission verdict.
