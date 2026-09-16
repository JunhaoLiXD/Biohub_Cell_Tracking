# Session Handout — 2026-09-15 / 2026-09-16

Purpose: hand this session's work to the next session. Read this first, then
`STATE.json`, the active `experiments/exp_057_0944_motion_ema/experiment.json`,
`.private/current/CONTINUATION.md`, and `docs/research/PROJECT_HANDOFF.md`.

## TL;DR — where the project is right now

**exp_057 is SUBMITTED and running on Kaggle.** It is the aggressive pivot's first
experiment: the public 0.944 edge-feature-TTA bundle (`repro_048`) + motion EMA
alpha 0.4, validated by the leaderboard (the frozen train16 proxy is discredited).
The immediate next action is to **wait for the user's completion notice**, then
check/collect once and audit — do NOT poll.

## What happened this session, in order

1. **Finished exp_055 analysis (was left incomplete).** exp_055 (original-score
   protected joint repair) had already been collected; the controller reached
   terminal **KEEP** (gate `joint_repair_passed`). Completed the independent audit:
   frozen train16 proxy **0.9535869213120838** (+0.01485 over repro_041), an EXACT
   reproduction of the zero-GPU `local_052` pilot (byte-identical ordered
   joint-repair actions on all 16 scored samples), submission SHA verified, 35
   contract checks, division unchanged 4/8/8. Report:
   `.private/research/exp055_completed_analysis_2026-09-15.md`.

2. **User authorized one Public LB scoring of exp_055.** File submission is
   impossible (notebook-only Code competition); submitted the completed kernel via
   the code-submission API (`competition_submit_code`) as submission **56261282**.
   Result: **Public LB 0.942 == repro_041 0.942, ZERO gain.** The large frozen
   train16 proxy did NOT transfer. Recorded in `SUBMISSION_BUDGET.json` and
   `experiments/exp_055_.../leaderboard-result.json`.

3. **Decisive methodological finding:** the frozen train16 stratified proxy is
   severely optimistic for post-smoothing graph-repair changes and does not predict
   the Public LB. This governs all downstream strategy.

4. **exp_056 (division-aware joint lineage repair) — HALTED.** Authored as the
   aggressive successor, challenged by Codex three times (all REVISE;
   `docs/research/exp056_codex_challenge_v1..v3.md`). Its hard go-gate required the
   exp_055 LB to beat 0.942; since the LB was flat, the go-gate failed and exp_056
   is halted. The v1–v3 design remains valid engineering evidence.
   Proposal: `docs/research/exp056_division_aware_joint_repair_proposal.md`.

5. **Pivot (user-directed): migrate the research parent to `repro_048` (0.944)** —
   the only measured pipeline that beats repro_041 on the real leaderboard — and
   validate future work by the leaderboard. Two sequenced proposals were authored:
   exp_057 (compose 0.944 + EMA) first, then the aggressive exp_058.

6. **exp_057 (0.944 bundle + motion EMA alpha 0.4) — BUILT, ADMITTED, LAUNCHED.**
   - Strategy CONSENSUS after four Codex challenges
     (`docs/research/exp057_codex_challenge_v1..v4.md`; proposal section 8).
   - Implementation: `.private/current/exp057_0944_motion_ema.ipynb` = repro_048 +
     ONLY the scoped `velocity_um` EMA edit in `motion_relink_edges`
     (gated by `BIOHUB_MOTION_RELINK_EMA_ALPHA`, default 0.4), plus an appended
     **fail-closed double-pass integrity block**: it re-runs postprocessing EMA-off
     over the same on-disk geffs, verifies the EMA-off submission is byte-identical
     to repro_048 (SHA `0319ba6d...`), requires >=1 canonical edge change, checks
     EMA telemetry, asserts the effective on-pass alpha is a float exactly 0.4, and
     emits a controller-compatible `metrics.json` with `exp057_ema_integrity_passed`.
   - Admission: four targeted Codex implementation reviews to PASS
     (`docs/research/exp057_codex_admission_v1..v4.md`), then the formal controller
     Codex review caught a real defect (`setdefault` accepted a pre-set non-0.4
     alpha) — fixed with the alpha gate + negative test
     (`scripts/verify_exp057_integrity_gate.py`); the re-run formal review PASSED
     and snapshot smoke PASSED.
   - Launched once at **2026-09-16T04:36:06Z** as kernel
     `lingxd/biohub-exp057-0944-motion-ema` (state SUBMITTED), 1.0 GPU hour
     reserved, six protected preserved. Notebook SHA `38fb52c2`; signature
     `68e2cd47`.

7. **exp_058 (aggressive self-train, v0.3) — DESIGNED, QUEUED behind exp_057.**
   Combined A+B: Arm A = clean-init `pair_mlp` retrain on `T` with `H` held strictly
   for one final eval (a trustworthy offline held-out probe, not deployed);
   Arm B = fine-tune `pair_mlp` from the public checkpoint (deployable LB candidate,
   contaminated offline signal); cross-check A's clean held-out delta vs B's LB
   delta to finally calibrate a trustworthy offline signal. Codex refuted the v0.1
   claim that base exposure to `H` cancels; v0.3 is honest about that. Each arm
   <=4h GPU. Needs its own full Codex strategy challenge before implementation.
   Proposal: `docs/research/exp058_selftrain_heldout_proposal.md`.

## Next session — do this

1. If the user reports exp_057 finished: run `scripts/check_kaggle.py` then
   `scripts/collect_results.py exp_057_0944_motion_ema` ONCE. Do not poll.
2. Audit `experiments/exp_057_0944_motion_ema/metrics.json`:
   `exp057_ema_integrity_passed` must be true, with all four checks
   (`effective_on_pass_alpha_is_preregistered_0_4`,
   `ema_off_submission_byte_parity_repro048` == 0319ba6d,
   `canonical_edge_diff_at_least_one`, `ema_predictions_positive`); confirm the
   EMA-off SHA, the canonical edge symdiff, and the EMA-on candidate SHA.
   Controller KEEP/REJECT here is integrity-only; **quality is the external LB**.
3. If integrity passes, the SINGLE Public LB submission of the EMA-on candidate is a
   **separate explicit user authorization** (`competition_submit_code`,
   `gate_submission` remote-history + duplicate check, 3/day cap), compared against
   repro_048's 0.944.
4. Then proceed to exp_058: freeze the v1 recipe (component/split/epochs/loss/stop)
   BEFORE observing exp_057's LB, hand exp_058 v0.3 to a full Codex strategy
   challenge, revise to CONSENSUS, implement, fresh Codex admission, smoke,
   reservation, and per-submission authorization.

## Guardrails (unchanged)

No leaderboard submission, promotion, or successor launch without explicit user
authorization and the full Claude-proposes / Codex-challenges / CONSENSUS + fresh
Codex admission workflow. Preserve the six protected GPU hours and >=10% per-model
allowance. Every inference policy stays ground-truth-free and specimen/video-blind.
The frozen train16 proxy is diagnostic-only and never decides.

## Key files touched this session

- Proposals/challenges: `docs/research/exp056_*`, `exp057_*`, `exp058_*`.
- exp_057 build/validation: `scripts/build_exp057_0944_motion_ema.py`,
  `scripts/validate_exp057_notebook.py`, `scripts/verify_exp057_ema_parity.py`,
  `scripts/verify_exp057_integrity_gate.py`,
  `docs/research/exp057_parity_execution_receipt.json`,
  `configs/exp_057_0944_motion_ema.yaml`,
  `experiments/exp_057_0944_motion_ema/` (snapshot, experiment.json, review.md).
- Canonical state: `STATE.json` (regenerates `CLAUDE.md`/`GOAL.md`/`AGENTS.md`
  checkpoint blocks via `scripts/render_checkpoint.py`),
  `.private/current/CONTINUATION.md`, `SUBMISSION_BUDGET.json`, `GPU_BUDGET.json`,
  `experiments/exp_055_.../leaderboard-result.json`.
- Local numpy-dependent checks run in a throwaway venv (the controller `.venv` is
  deliberately dependency-minimal and lacks numpy/scipy).
