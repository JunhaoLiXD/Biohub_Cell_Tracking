# Biohub Cell Tracking — Project Handoff

Status: current repository checkpoint, 2026-09-18. This file is the operational
handoff for Claude Code as primary author and Codex as independent reviewer. Read
`HANDOUT.md` first, then `STATE.json`, `AGENTS.md`, `GOAL.md`,
`.private/current/CONTINUATION.md`, and the active experiment record before acting.
Historical records remain evidence and are not implicit authorization.

## Claude Code startup action

Read `HANDOUT.md` and `STATE.json` first. **Current state (2026-09-18):** the new best
Public LB is **0.947** (`repro_059`, authenticated submission 56313491) — a verbatim copy
of a public 0.947 notebook on the same Pilkwang checkpoints as our 0.944 (so the +0.003 is
100% post-processing/TTA), adopted as the working parent. The active experiment
**`exp_060_deepcenter_safe_div_threshold_sweep`** (a DeepCenter safe-division threshold
micro-sweep {0.20 control / 0.18 / 0.22} on the frozen 0.947 pipeline) is **LAUNCHED on
Kaggle** (kernel `lingxd/biohub-exp060-deepcenter-safe-div-threshold-sweep`, manual push
outside the controller by explicit user authorization, awaiting completion). On completion,
verify the 0.20-arm byte-parity (SHA == `d3453380`) + the integrity gate, then analyze the
0.18/0.22 division telemetry; the LB submission of an arm is a SEPARATE user authorization
(competition is notebook-only). Do NOT poll; do NOT relaunch/submit without user go-ahead.
The `HANDOUT.md` `>>> NEXT STEP <<<` block is authoritative for the immediate action.

## Goal and system

Build a high-scoring Kaggle solution for detecting and tracking cells in 3D
time-lapse zebrafish microscopy. The established pipeline uses pretrained
TemporalUNet3D detectors, physical-coordinate detections, transformer
association, motion/gap repair, ILP graph selection, and DeepCenter division
gates, then emits the competition `submission.csv` tracking graph.

## Current evidence

* **New best Public LB: `repro_059_public_0947_exact_copy` = 0.947** (authenticated
  submission `56313491`, COMPLETE, 2026-09-17). Verbatim copy of a public 0.947 notebook
  (documented upstream `raykkretzschmar/biohub-bidirectional-primary-union13-diagnostic-v1`),
  running the **same three Pilkwang checkpoints** as our 0.944 — so the +0.003 is 100%
  post-processing/TTA (model byte-identical), not causally isolated. It is the adopted working
  parent. Dissection (vs 0.944): DeepCenter(division) TTA ON + secondary edge-feature TTA ON +
  DeepCenter safe-div threshold 0.25→0.20 + an embedded held-out PP-sweep that selected `tight55`
  (MOTION_RELINK_TIGHT_UM 6.0→5.5). Self-attested `metric_hack_used=False`. Full provenance:
  `experiments/repro_059_public_0947_exact_copy/PROVENANCE.md`.
* Public-frontier recon (2026-09-18): the LB frontier is ~0.970 but those are private/unshared;
  the reproducible public cluster all shares the same Pilkwang checkpoints, and no verified public
  notebook clearly above 0.947 was found. → improve ON the 0.947 base.
* Prior verified public reference: submission `56105868`, Public LB **0.944**. Byte-identical to
  the shared public notebook output. The advertised 0.946 is not reproduced.
* Stable train16 parent: `repro_041_public_0941_motion_ema`, score
  **0.9387332376874039**, fixed motion EMA alpha 0.4, and user-reported Public
  LB 0.942. Its 16-video graphs and scoring artifacts passed independent audits.
* No-EMA comparison `val_039_public_0941_train16`: **0.9359778132422281**.
  Global alpha 0.6, adaptive hard reset, and sparse-soft EMA are closed terminal
  REJECT branches. Do not reopen them without new authorization.
* Zero-GPU `local_052_joint_graph_pilot_v1_attempt02` found a promising
  original-score protected joint cut-and-reconnect policy at
  **0.9535869213120838** (+0.01485368362467987 proxy). The five-frame context
  variant scored **0.9519261693422604** (+0.013192931654856466), but its
  preregistered gate failed. These are frozen-training proxy results, not Public
  LB evidence; inference must remain ground-truth-free. The GPU experiment
  `exp_055` (KEEP) later reproduced the original-score policy **exactly** in the
  full pipeline — byte-identical ordered joint-repair actions on all 16 scored
  samples and the same 0.9535869213120838 proxy score — confirming faithful
  transfer of the edit policy, though still only as a frozen-training proxy.

## Evidence timeline

This table is the short, comparable history. Detailed experiment records and
reports remain the source of truth for raw artifacts, hashes, and gate results.

| Stage | Result | What it established / decision |
| --- | --- | --- |
| Self-contained baseline | Public LB **0.844** | Original in-repository pipeline; historical lower control. |
| Public learned 0.933 line | About **0.933** Public LB | Learned detector/linker lineage became the controlled research line; later train16 scores are not comparable with train4 controls. |
| `repro_038_public_0941_exact_copy` | Public LB **0.941**, submission `56044403` | Exact public source/checkpoint/submission graph audited; selected as parent lineage. |
| `val_039_public_0941_train16` | **0.9359778132422281** | Frozen 16-video train16 baseline with unchanged parent test inference. |
| `exp_040_public_0941_motion_ema` → `repro_041_public_0941_motion_ema` | **0.9387332376874039**, +0.002755424445175847; user-reported Public LB **0.942** | Fixed motion EMA alpha 0.4 reproduced exactly; retain as stable behavior parent. |
| `exp_042_public_0942_motion_ema_alpha06` | **0.937681**, terminal REJECT | Global alpha 0.6 harmed the frozen protocol; branch closed. |
| `exp_043_public_0942_motion_ema_adaptive_reset` | **0.9368238444059783**, terminal REJECT | Threshold-1.0/alpha-1.0 hard reset reset 39.32% of eligible updates; branch closed. |
| `exp_046_public_0942_motion_ema_sparse_soft` | **0.9387340065001502**, below its +0.0001 gate; terminal REJECT | Sparse adaptive EMA was a near-null density-only change; no reopening. |
| `repro_048_public_0946_exact_copy` | Public LB **0.944**, submission `56105868` | Shared public materials reproduce 0.944, not advertised 0.946; bundled effects are not causally isolated. |
| `val_049_public_0944_train16` | **0.9310696298996892** | Full 0.944-source train16 comparison fell below the EMA parent; retained as evidence, not a new parent. |
| `exp_050_public_0944_tta_off` | **0.9359778132422281**; TTA effect B−A = **−0.004908183342538841** | Matched feature-TTA composition screen closed under its negative-effect rule; division explained most loss. |
| `diag_051_public_0942_tracklet_evidence` | Parent behavior retained at **0.9387332376874039** | Evidence covered 242/258 fragmentation edges; 85 accepted, only three free-endpoint connections, and 75 accepted true links disappeared during relinking. Diagnostic only. |
| `local_052_joint_graph_pilot_v1_attempt02` | Original-score policy **0.9535869213120838**; context policy **0.9519261693422604** | Zero-GPU frozen-training proxy showed structural upside. Context increment gate failed; original-score repair remained candidate only. |
| `exp_053_original_score_joint_repair` | `REMOTE_FAILED` before inference | Missing isolated-bootstrap NumPy import; no quality conclusion or score. Preserve failure artifacts; do not retry. |
| `exp_054_original_score_joint_bootstrap_fix` | `LOCAL_FAILED` | Import fix was present, but minimal controller environment lacked NumPy; not a method failure. |
| `exp_055_original_score_joint_bootstrap_smoke_fix` | **KEEP**, proxy **0.9535869213120838**, +0.01485368362467987 | Remote run reproduced the `local_052` original-score policy exactly: byte-identical ordered joint-repair actions on all 16 scored samples, division unchanged 4/8/8, gain entirely adjusted-edge (~85% from 6bba). Independent audit passed; frozen-training proxy only, not Public LB; `reproducible: false`; no promotion/LB. |
| `exp_055` → Public LB probe (submission 56261282) | Public LB **0.942 == repro_041**, Δ0 | The +0.0149 frozen train16 proxy did NOT transfer. train16 proxy declared severely optimistic for post-smoothing graph-repair. |
| `exp_057_0944_motion_ema` → Public LB probe (56281129) | Public LB **0.944 == repro_048**, Δ0 | Motion EMA on 0.944 is neutral/redundant (EMA-off replay byte-identical to 0.944). Branch closed. Two causally-isolated post-hoc edits both LB-flat → remaining loss is not in the association/motion layer. |
| `repro_059_public_0947_exact_copy` | Public LB **0.947**, submission `56313491` | NEW BEST (+0.003 vs 0.944). Verbatim public-notebook copy, same Pilkwang checkpoints → gain is 100% post-processing/TTA (DeepCenter TTA + secondary edge TTA + safe-div threshold 0.25→0.20 + held-out PP-sweep tight55). Adopted as working parent; bundled, not causally isolated. |
| `exp_060_deepcenter_safe_div_threshold_sweep` | **LAUNCHED 2026-09-18**, awaiting completion | DeepCenter safe-division threshold micro-sweep {0.20 control / 0.18 / 0.22} on the frozen 0.947 pipeline (division is the bottleneck: 0.20 gate rejects 414 candidates; 0.18 primary arm). Strategy CONSENSUS (3 Codex rounds) + implementation verified across 12 Codex rounds; launched by manual push (formal controller admission REVISE was circular — demands local verification of the GPU pipeline it gates). Produces 0.20/0.18/0.22 submissions + division telemetry + gated metrics.json; 0.20 arm must byte-reproduce parent SHA d3453380. No auto LB submission. |

## Important entry points and artifacts

* `AGENTS.md` contains roles, safety rules, budgets, and the current checkpoint.
  `GOAL.md` contains authorization history and the Codex-admission workflow.
  `.private/current/CONTINUATION.md` and `.private/current/MEMORY.md` are the
  first-resume notes; this file is the concise authoring handoff.
* `STATE.json` is the generated checkpoint source. `GPU_BUDGET.json` tracks
  reservations/consumption and `SUBMISSION_BUDGET.json` tracks leaderboard
  submissions. Do not hand-edit generated checkpoint text.
* The active record is
  `experiments/exp_055_original_score_joint_bootstrap_smoke_fix/experiment.json`.
  Its snapshot config/source/manifest, `review.md`, validation JSON, and
  smoke/launch logs are immutable admission evidence. The exp_053 and exp_054
  directories are preserved failure/provenance records.
* Stable parent evidence is under
  `experiments/repro_041_public_0941_motion_ema/`, especially validator results,
  final graph payloads, submission, and audit outputs. Local joint-pilot evidence
  is under `experiments/local_052_joint_graph_pilot_v1_attempt02/` in
  `protocol.json`, `result.json`, and `audit.json`.
* Future Codex admission uses `scripts/request_codex_review.py` and requires
  `admission.require_codex_review: true`. `scripts/check_kaggle.py` and
  `scripts/collect_results.py` are for the single post-notice exp_055
  check/collection; `scripts/launch_kaggle.py` is not authorized for exp_055.
  Original-score smoke/contract validators define the bootstrap and parity gates.
* `docs/research_workflow.md` is a historical traceability snapshot and points
  here. `docs/experiments.md` and `.private/research/` contain dated analyses;
  use records rather than inferring state from filenames.

## Closed branches and methodological caveats

* Do not resubmit byte-identical 0.944 output, claim the unavailable 0.946, or
  attribute the 0.944 gain to feature TTA alone. The public run bundled changes.
* Do not reopen global alpha 0.6, adaptive hard reset, sparse-soft EMA, the
  negative TTA composition branch, or the failed context-policy gate merely to
  search nearby parameters. New authorization and a new falsifiable rationale
  are required.
* Train16 panels use pretrained models that saw training videos. Absolute scores
  are optimistic frozen-training proxies, not independent held-out generalization.
  Fixed-rule grouped panels are also not independent heldout evidence. Public LB
  scores cannot substitute for graph/metric audits or identify component causality.
* Every inference policy must be ground-truth-free and independent of specimen or
  video identity. Preserve node identity, edge conflict/fork constraints,
  division protection, exact input/output hashes, and strict JSON/metric
  serialization. Raw intermediate graphs are not automatically final graphs.
* A controller or portability error is not an algorithmic REJECT. Preserve the
  receipt and failure output, isolate the smallest fix, and continue only after
  Claude/Codex consensus and the applicable admission gates.

## Post-exp_055 decision tree

The tree begins only after the user reports completion. Until then, perform no
polling. After that notice, check and collect exp_055 once, then independently
audit the result.

* **Valid remote KEEP / complete contract:** Codex verifies exact graph hashes,
  score rows, aggregate arithmetic, division counts, solver receipt, and stable
  submission bytes. Claude Code then authors the actual next strategy, such as
  independent reproduction if the gain is credible or a bounded structural/
  framework proposal if the error audit points to coupled failures. Codex
  challenges that concrete proposal; Claude revises until `CONSENSUS`. KEEP does
  not authorize promotion or leaderboard submission.
* **Valid algorithmic REJECT:** Codex confirms the contract and records the
  negative result without relaunching the branch. Retain fixed-alpha-0.4
  `repro_041` as behavior parent. Claude Code authors a materially justified
  strategy rather than an unbounded parameter sweep; Codex reviews it and
  execution waits for consensus plus fresh Codex admission.
* **Remote/integration failure:** Codex preserves and diagnoses failure artifacts,
  reports that no quality score is available, and does not retry automatically.
  If a successor is justified, Claude Code proposes the smallest portability,
  infrastructure, or algorithmic correction with a new parent/change description;
  Codex reviews proposal and implementation. The successor must set
  `admission.require_codex_review: true`, use
  `scripts/request_codex_review.py`, obtain a fresh Codex `PASS`, pass smoke and
  budget gates, and remain backward-compatible with historical Claude receipts.
* **Incomplete or ambiguous output:** stop interpretation, preserve the raw
  receipt, and ask the user for direction. Do not convert missing metrics into a
  REJECT, KEEP, leaderboard submission, or promotion.

## Completed run: exp_055 (KEEP, audited)

`exp_055_original_score_joint_bootstrap_smoke_fix` completed as controller
**KEEP** on 2026-09-15. Behavior parent `repro_041_public_0941_motion_ema`;
research variable the fixed original-score joint repair. `exp_053` failed
remotely before inference (isolated solver called `np.array` before NumPy
import); `exp_054` added the import but failed local smoke (minimal controller
environment has no NumPy). Both failed predecessors are retained and closed.

The remote run scored frozen train16 proxy **0.9535869213120838**
(**+0.01485368362467987** over repro_041) and reproduced the zero-GPU
`local_052` original-score policy **exactly**: the ordered joint-repair action
lists are byte-identical on all 16 scored samples, division is unchanged at
4/8/8, and the entire gain is adjusted-edge (~85% from specimen 6bba). The
independent audit verified submission SHA256 `9eb4826b...`, aggregate arithmetic,
all 35 contract checks, DeepCenter epoch-2 identity, and solver pin SciPy 1.18.1.
Runtime 1.0972611120275 GPU hours charged once; 26.9027388879725 remain with six
protected. `metrics.reproducible` is false; this is an optimistic
frozen-training proxy, not Public LB evidence. Full audit:
`.private/research/exp055_completed_analysis_2026-09-15.md`.

### Required next action

The check/collection and independent audit are complete; do not repeat them.
Enter the Valid-KEEP branch: Claude Code authors the next strategy proposal
(an independent exact reproduction of the original-score gain, or a bounded
structural proposal), Codex challenges it, and Claude revises to a versioned
`CONSENSUS`. No implementation, launch, relaunch, re-collection, promotion, or
leaderboard submission is authorized until `CONSENSUS` plus a fresh Codex `PASS`
and the standard admission gates. KEEP authorizes neither promotion nor LB.

## Strategy and review workflow

1. Claude Code proposes the next strategy and owns implementation. Each proposal
   states the actual parent, one falsifiable hypothesis, exact change, validation
   protocol, expected signal, failure modes, artifacts, resource budget, and
   rollback/stop rule.
2. Codex independently challenges the strategy and implementation. It checks
   provenance, leakage, graph semantics, numerical stability, test coverage,
   reproducibility, and budget; a positive local proxy is never treated as proof.
3. Claude Code revises the proposal or code in response. Record proposal,
   critique, revisions, and explicit `CONSENSUS` in a versioned strategy record.
   `NO_CONSENSUS` stops execution and returns the disagreement to the user.
4. Only after consensus may local/static/snapshot gates run for a successor.
   Future experiment configs must set `admission.require_codex_review: true`
   (optionally `reviewer_provider: codex`), invoke
   `scripts/request_codex_review.py`, and require a fresh experiment-specific
   Codex `PASS`, in addition to the smoke, tracked reservation, and controller
   gates. Legacy experiment configs and receipts, including exp_055, remain
   Claude-based historical evidence and must not be rewritten retroactively.
5. After execution Codex audits raw artifacts and metrics; Claude interprets the
   result and proposes the next strategy. Historical records are not silently
   rewritten. The migrated controller accepts the Codex admission field while
   remaining backward-compatible with legacy configs and records.

## Late-stage experimental posture

The project is in its final accuracy push. With explicit user authorization,
Claude Code may propose bold high-risk/high-reward experiments, including
framework-changing detector, association, decoder, or joint-lineage designs.
Failure is acceptable when the experiment has credible upside or information
value. Every such experiment must remain versioned, reproducible, reversible to
the retained baseline, and bounded by a tracked hypothesis, fail-fast gates,
resource budget, and stop rule. Preserve the six-hour GPU reserve and at least
10% allowance for each model. No ground-truth, specimen, or video leakage is
allowed. Exact provenance, graph/hash audits, and honest separation of local
proxy from Public LB evidence remain mandatory. Aggressive exploration does not
authorize automatic leaderboard submission, promotion, credential changes, or
major direction changes without user approval.

## Repository cleanup record

Removed only disposable, workspace-contained caches: root `.pytest_cache`,
`.pytest_tmp_final`, `.pytest_tmp_risk`, and 419 generated `__pycache__`
directories (the count is the removal command's reported count). The recursive
cache cleanup included bytecode caches under accessible copied experiment
artifacts, private runtime copies, and the `.venv`; the `.venv` directory,
installed packages, source, data, snapshots, experiment records/logs, failure
artifacts, runtime inputs, and provenance files were not removed. The two
remaining root pytest directories, `.pytest_tmp_presync` and
`.pytest_tmp_submission`, are ACL-protected from this account and were not
deleted.
