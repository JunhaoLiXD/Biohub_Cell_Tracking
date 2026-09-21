# Latest Codex Review

Experiment: `exp_061_deepcenter_tta`  
Captured: 2026-09-21T05:03:17+00:00

## Summary

**REVISE.** Strategy governance is satisfied: the Claude-authored proposal and five Codex challenge/revision rounds are versioned, and v5 explicitly records `CONSENSUS`.

All six snapshot hashes match the manifest, the embedded harness matches its snapshotted source, stripped-parent notebook parity holds, and the Git worktree has no current diff. However, the rebuilt implementation still has launch-blocking contract defects.

## Methodology

The three preregistered arms isolate one major variable: the DeepCenter TTA set. The byte-parity control and replay before gap1 provide a sound causal structure. This is distinct from exp_060’s threshold change and exp_050’s association-feature TTA.

The parent’s bundled +0.003 Public-LB improvement does not establish DeepCenter TTA as its cause. Three recent post-processing interventions were displayed-LB nulls, so expected upside is modest but the experiment retains useful information value.

This is an integrity-gated Public-LB probe, not trustworthy biological validation. It provides no new `44b6`/`6bba` domain-split evidence. No new label leakage was found, but a positive LB result must not be described as cross-domain generalization.

## Implementation risks

- **The frozen parent configuration is incorrect.** The harness records fallback defaults such as gap/safe-division thresholds `0.10/0.12`, motion bonus `0.75`, and gap2 disabled ([harness](/E:/Project/Biohub_CellTracking/experiments/exp_061_deepcenter_tta/snapshot/extra_files/exp061_deepcenter_tta.py:110)). The parent environment actually resolves these to `0.25/0.20`, `1.0`, and gap2 enabled, among many other overrides ([notebook](/E:/Project/Biohub_CellTracking/experiments/exp_061_deepcenter_tta/snapshot/source/exp061_deepcenter_tta.ipynb:127)). Consequently, the real run will fail `live_pinned_config_equals_frozen_parent`. Test N only parses declaration fallbacks, so it falsely validates the table.

- **The configuration coverage is incomplete.** Effective post-processing controls such as adaptive short-track rescue and its thresholds are active in the parent but absent from `EXP061_CONFIG_KEYS`. The experiment therefore cannot prove that every behaviorally relevant replay setting is frozen.

- **Config mismatch does not fail fast.** The harness prints the mismatch but continues into the expensive arms. It should emit failed metrics and return before inference/replay.

- **Partial-run integrity is under-specified.** A started experimental arm that aborts cleanly for budget is excluded from `arm_summaries`; the integrity checks can consequently pass without that started arm producing an artifact. Add an explicit `all_started_arms_completed` contract, or revise the declared contract and controller interpretation for partial runs.

- **Runtime view verification is circular.** Whether square-only views are expected is inferred from whether any such view was observed. If all square-only views silently fail to run, the guard can still pass. Record frame geometry and validate the exact expected view sequence/count per frame.

- **Stage attribution remains weaker than claimed.** Gap1 identity survival is now recorded, but gap1/gap2 stage counters describe edges added during a stage—not stage-specific edges surviving in the final graph. Persist stage edge identities and intersect them with the final graph.

## Budget

The ledger is now reconciled through exp_060: **24.493 GPU hours remain**, with six protected. A two-hour reservation would leave 22.493 hours, so nominal capacity is sufficient; no reservation currently exists.

Feasibility is still not conservative. The control arm starts with a zero estimate, and remaining work is projected using mean observed dataset cost. The first dataset can consume the protected finalization margin, and heterogeneous later datasets can exceed the mean. Use prelaunch parent/timing evidence for initial admission and a conservative maximum or upper-bound projection.

## Required changes

1. Derive the frozen configuration from the parent’s effective environment assignments plus the recorded `tight55` override—not declaration fallbacks—and include every replay-relevant knob.
2. Strengthen the config test to evaluate or parse both environment setup and declarations; add negative fixtures for the known `0.25/0.20`, motion-bonus, gap2, and adaptive-rescue overrides.
3. Fail before arm execution when config or checkpoint provenance is invalid.
4. Enforce explicit started/completed/skipped/aborted semantics in the metrics gate.
5. Validate exact per-frame view execution from recorded tensor geometry.
6. Persist final stage-specific edge identities, and make first-arm/runtime admission conservative.
7. Rebuild the snapshot, obtain a fresh admission review, then run snapshot smoke, reserve two hours, and obtain explicit launch authorization. Keep each LB submission separately authorized.

## Recommendation

The strategy consensus is valid, so this is not a governance `BLOCK`. The current snapshot should not advance to smoke or launch because its effective-parent guard is guaranteed to reject the actual parent configuration and several runtime/output contracts remain incomplete.

VERDICT: REVISE
