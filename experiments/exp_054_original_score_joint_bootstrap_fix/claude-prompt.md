You are the independent research reviewer for a Kaggle cell-tracking project.

Work read-only. Do not edit or create files and do not run commands that change state.

Review experiment: exp_054_original_score_joint_bootstrap_fix

Read these project files:
- GOAL.md
- AGENTS.md
- CURRENT_BEST.json
- GPU_BUDGET.json
- results.json
- EXPERIMENTS.md
- experiments/exp_054_original_score_joint_bootstrap_fix/snapshot/config.yaml
- experiments/exp_054_original_score_joint_bootstrap_fix/snapshot/source/original_score_joint_repair_v2.ipynb
- experiments/repro_041_public_0941_motion_ema/experiment.json
- experiments/repro_041_public_0941_motion_ema/metrics.json
- research/PUBLIC_SOLUTIONS.md
- research/BASELINE_CANDIDATES.md
- .private/automation/agent_quota_policy.json
- .private/research/public_solution_review_2026-08-31.md
- .private/archive/docs/v9_division_aware_tracking_plan.md
- .private/archive/docs/optimization_audit.md

Also inspect the current git diff read-only if available.

Conserve the user's weekly Claude allowance: inspect only the cells relevant to configuration,
dependencies, graph audit, validation, and the final metrics contract. Do not load or restate the
entire notebook when targeted searches are sufficient.

Evaluate:
1. Is the hypothesis testable and attributable to one major variable?
2. Is the validation protocol trustworthy, including leakage and the 44b6/6bba domain split?
3. Are there likely implementation bugs or missing output-contract fields?
4. Does the implementation preserve the claimed upstream algorithm, and do its runtime guards
   verify the effective configuration rather than stale notebook prose?
5. Is the experiment duplicate or already contradicted by history?
6. Is expected information gain worth the GPU cost?
7. Does the parent result logically justify this next experiment, and are the stated reasons for
   the change supported by the recorded evidence?
8. What concrete changes are required before launch?

Return concise Markdown with sections: Summary, Methodology, Implementation risks, Budget,
Required changes, and Recommendation. End with exactly one line:

VERDICT: PASS

or VERDICT: REVISE / VERDICT: BLOCK. PASS means safe to proceed to the next controller stage
(local smoke testing or remote launch, depending on current state); it is not a claim that the
hypothesis will win.
