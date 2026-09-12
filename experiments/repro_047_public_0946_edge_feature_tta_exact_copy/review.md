# Independent Review — `repro_047_public_0946_edge_feature_tta_exact_copy`

## Summary
A full-source reproduction of the public `reyhanksatria/biohub-cell-tracking-0-946-lb` notebook (edge-feature TTA on, motion EMA absent), edited only to remount the three Pilkwang artifact datasets at their slug-only Kaggle paths. Goal: test whether it reproduces Public LB 0.946 under `lingxd`. The user explicitly authorized this on 2026-09-08 (one exact-copy execution + one LB submission, no promotion), so it is *not* blocked by the exp_046 "no successor" instruction, which was scoped to the EMA branch. `NEXT_RESEARCH_PRIORITIES.md` lists this exact candidate as a legitimate PENDING-VALIDATION verification gate. The concept, authorization, budget, and static config-fidelity guards are sound.

There is one concrete, launch-blocking defect: the local collect adapter hard-requires `validator_results.csv`, which this upstream notebook never produces.

## Methodology
- **Testable / one variable?** As a *reproduction* gate (explicitly separate from single-variable optimization per `GOAL.md`), yes — the "variable" is the whole upstream config. But the change bundle vs. the 0.941 line is large (`BIOHUB_DET_THRESHOLD=0.965`, bidirectional harmonic fusion, secondary artifact + low-margin consensus, adaptive short-track rescue, edge-feature TTA, etc.), so a 0.946 vs 0.941 delta is **not attributable to edge-feature TTA alone**. The name/hypothesis slightly overclaim attribution; the config's own `variables_changed` and `comparison_note` correctly flag this.
- **Validation trust / leakage / 44b6-6bba split.** The intended train4 proxy is leaky (frozen extractors saw train videos) and non-promoting — correctly warned. The submission audit enforces the domain split (exactly `{44b6:2, 6bba:2}` test movies) and legal node/edge degrees. The *real* evidence is the external competition score, decided separately by the user. That framing is trustworthy.
- **Duplicate / contradicted?** No. This is the first attempt at the 0.946 frontier; prior work was the 0.941/0.942 EMA line. Not contradicted by history.
- **Parent justification.** Parent `repro_038` (the 0.941 exact-copy, INCONCLUSIVE locally but LB-confirmed 0.941) is the correct lineage for another full-source public reproduction. Move to 0.946 is supported by the recorded recommendation to pursue a separately-justified direction beyond EMA.

## Implementation risks
- **BLOCKING — missing output-contract artifact.** The 0.946 notebook writes only `submission.csv` and `run_stats.csv`; it computes no Jaccard/division metrics (`jaccard` occurs 0 times, no `adjusted_edge_jaccard`/`div_tp`/`ground-truth`-based validator). But `experiment_controller/public_0946_copy.py::collect` calls `read_validator(artifacts/"validator_results.csv")` **before** the submission audit. That file will not exist → `OSError` → the `except` branch marks `INVALID_METRIC` and charges the full `expected_gpu_hours` (2.0). Net effect: the single authorized LB submission and 2 GPU-h are spent, and the run is recorded as invalid with no proxy comparison. This is the diag_044 failure class, but predictable pre-launch. (Note `repro_038` differed: its 0.941 upstream *did* emit `validator_results.csv`, so it collected cleanly to INCONCLUSIVE — this adapter was templated from that path.)
- **Config claims not satisfiable.** `validation.primary_metric: upstream_train4_proxy_score`, `samples_per_specimen: 2`, and `comparison_current_candidate: repro_041` cannot be produced from this notebook's outputs.
- **Unverifiable hard gate.** `DEEPCENTER_SHA256 = 8040999a…` must equal the actual Pilkwang DeepCenter `best.pt`; I cannot confirm the value offline. If wrong, collection also fails at the DeepCenter guard.
- **Guards that are good.** The static smoke check (`validate_public_0946_copy.py`) verifies byte-identity to the archived upstream except the four declared path substitutions, asserts `BIOHUB_EDGE_FEATURE_TTA=1`, and asserts `BIOHUB_MOTION_RELINK_EMA_ALPHA` is absent — it verifies the *effective* config, not prose. The env dump confirms this. Path substitutions map to the correct slug-only mounts for the three `pilkwang/*` datasets. Internet off, private kernel, T4, competition source attached — all correct. Note the smoke check will **pass**, so it will not catch the collector mismatch.

## Budget
2.0 GPU-h reserved, within the 4.0-h single-experiment cap (no extra approval needed). `GPU_BUDGET.json` shows 19.456 tracked hours (13.456 spendable over the 6-h reserve). Information gain is high *if* the run reproduces ~0.946 — a stronger potential working parent than the current 0.941/0.942 line. As written, however, the run would waste the reservation and the one LB submission on a guaranteed INVALID_METRIC collection, so the expected gain is not realized until the collector is fixed.

## Required changes
1. **Fix `experiment_controller/public_0946_copy.py`** so it does not require `validator_results.csv`. Base local evaluation on `audit_submission(submission.csv)` + runtime + `bidirectional_production_runtime_integrity.json`/DeepCenter checks, leaving proxy metrics undecided and gating on the external LB score (INCONCLUSIVE-style, mirroring repro_038's disposition).
2. **Reconcile `config.yaml` `validation`**: drop or restate `upstream_train4_proxy_score`, `samples_per_specimen`, and `comparison_current_candidate: repro_041`, since no train4 GT proxy is computable here; keep the `gate_field: public_lb_reproduction_passed` external framing.
3. **Confirm `DEEPCENTER_SHA256`** matches the actual Pilkwang `best.pt` used by repro_038.
4. **Optional:** reword the hypothesis/experiment name so the 0.946 gain is not implied to be caused by edge-feature TTA alone.

## Recommendation
The experiment is legitimate, authorized, and well-guarded on config fidelity, but it will deterministically fail local collection and burn the single authorized leaderboard submission because the collect adapter expects a `validator_results.csv` this upstream notebook never emits. Fix the collection contract and config validation block first; the smoke test alone will not catch this.

VERDICT: REVISE
