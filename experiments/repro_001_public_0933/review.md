I have everything needed. Working tree is clean (the snapshot is committed), and I've inspected the config, dependency/source-integrity, graph-audit, validation, and final metrics-contract cells. Here is the review.

# Independent Review â€” `repro_001_public_0933`

## Summary
This is a **controlled reproduction gate**, not a single-variable ablation, and it is framed that way correctly (`evaluation.mode: gate`, `gate_field: reproduction_passed`, `require_reproducible_for_promotion: false`, warnings that it is "not promotion evidence"). It swaps the frozen 0.912 two-seed blend for the public `team_fusion_v6_optimal_balance` config of the evgendvorkin 0.933 lineage. The implementation is unusually disciplined: the **final code cell re-verifies the effective configuration from `os.environ`/derived vars** (not prose), reports **per-specimen** metrics for both `44b6` and `6bba`, guards train/test overlap, and writes a complete `metrics.json` contract in the last cell. It is within budget (1.5 GPU-h). Safe to smoke-test; the open items are documentation hygiene and interpretation guardrails, not correctness blockers.

## Methodology
- **Q1 attributability:** As a reproduction, "one major variable" does not apply; `variables_changed: external_baseline_reproduction` is honest. Consequence to record: this run cannot serve as attributable evidence for any single knob and is not promotable from one run (GOAL and config already enforce this).
- **Q2 validation trust:** Validator scores **held-out TRAIN** videos (`VALIDATOR_N_PER_TYPE=2` â†’ 4 total, 2 per specimen), both specimens required and asserted (`required_specimens_present`), 7 Âµm match gate, correct Âµm voxel scaling, division weight 0.1. Train/test leakage is explicitly guarded (`test_stem_set` excludes val stems, line ~4047). The **deeper leakage** â€” frozen detector/transformer trained on all 199 train videos â€” makes the embedded proxy (~0.9382, gate `>=0.930`) **optimistic**; this is acknowledged in the config, `CURRENT_BEST`, and the emitted `metrics.json` warning. Two honest limitations: the sample is small (4 videos) and **division-biased** (selection ranks GT-division stems first), so absolute proxy numbers are noisy/optimistic â€” decisions must stay delta + per-specimen (as GOAL requires).
- **Q4 algorithm preservation:** Effective knobs match the reviewed 0.933 recipe â€” det 0.965, secondary detection 0.81, secondary edge 0.15, bidirectional 0.15, gap-close 5.8 Âµm, min-track 6, DeepCenter veto enabled (`BIOHUB_USE_DEEPCENTER_VETO=1`, line 238). The final `reproduction_passed` checks read these from the live environment (`secondary_detection_weight_exact`, etc., lines 4799â€“4829), so guards verify the **effective** config, not stale prose. Source integrity is enforced via sha256 on pack `.py` files and model weights.
- **Q5 novelty:** Not a duplicate and not contradicted; `results.json` holds only `baseline_public_0912` and the archived v9 oracle. This is GOAL's declared active direction.

## Implementation risks
- **Stale prose vs effective config (non-blocking):** Markdown says `SECONDARY_DETECTION_WEIGHT = 0.475` (line 703) while env sets `0.81` (line 1376); `BIDIRECTIONAL_EDGE_WEIGHT` prose says 0.30 (line 147) vs env 0.15; a code comment claims DeepCenter "keeps it disabled" (line 497) while env enables it. The runtime trusts env, not prose, so these are **documentation smells that will mislead future readers**, not functional defects.
- **Two contract checks are tautological:** `metric_hack_absent` reads a hardcoded `"metric_hack_used": False` (line 3909) and `submission_graph_audit_complete` compares against a hardcoded status literal (line 3903). They are **declarations, not detectors** â€” they cannot independently fail. The real graph legality is enforced elsewhere by raise-on-violation topology audits (invalid lineage edge / in-degree>1 / out-degree>2 â†’ `RuntimeError`, lines ~3860â€“3871), which abort the run. So the audit is genuinely enforced, but no one should read a green `metric_hack_absent` as an automated hack detector.
- **Metrics contract:** `metrics.json` is written in the **final code cell** (satisfies `validate_notebook`'s last-cell rule) and emits `primary_metric`, `adjusted_edge_jaccard`, `division_jaccard`, `specimen_metrics`, `reproduction_passed`, `failed_checks`, `checks`, and warnings. No missing contract fields; checks fail safe (missing values â†’ check False â†’ gate fails), so the failure mode is a false-negative gate, never a false pass.

## Budget
`expected_gpu_hours: 1.5`, tier 1 â€” well under `max_single_experiment_hours: 4.0` and the 4.0 approval threshold, against 30 h remaining / 6 h reserve. Information gain is high: it decides whether the licensed 0.933 lineage actually reproduces under `lingxd` before any further build-on. Worth the spend.

## Required changes
Before launch (none are blockers to local smoke testing):
1. **Interpretation, record explicitly:** a PASS means "reproduces the train-leaky embedded proxy (â‰¥0.930)," **not** a 0.933 LB claim; verify LB only via the `lingxd` rerun and do not promote from this single run.
2. **Fix stale prose** (0.475â†’0.81, BIDIR 0.30â†’0.15, DeepCenter "disabled" comment) so docs match the effective, guard-verified config.
3. **Downgrade or wire the two constant checks:** either derive `metric_hack_used`/audit `status` from the actual audit outcome, or annotate that the no-hack gate is human + source-integrity, not automated.
4. **Smoke expectations:** confirm `scripts/validate_notebook.py --require-metrics-contract` passes (structurally it should â€” `metrics.json` is the last code cell and runs after the validator) and that no saved error outputs remain in the snapshot.

## Recommendation
The experiment is well-constructed: effective-config guards, per-specimen reporting, leakage-aware framing, source-integrity checks, enforced graph topology, a complete final-cell metrics contract, and a modest budget. The findings are documentation-clarity and interpretation guardrails, not correctness defects.

VERDICT: PASS
