# exp_060 — Codex strategy challenge v3 (verdict: CONSENSUS)

Reviewer: Codex `gpt-6-astra`, low, read-only. Date: 2026-09-18.
Target: proposal v3 (safe-division threshold micro-sweep 0.20/0.18/0.22).

## Verdict: CONSENSUS

"V3 resolves the remaining v2 items at strategy level. Implementation still requires fresh
admission PASS and the stated parity, smoke, and budget gates."

## §12 rulings (fold into build)

1. **Resolved-config source.** Neither `_guard_report` nor `CONFIG_DISPLAY` is authoritative
   (`CONFIG_DISPLAY` = init values; the sweep applies overrides then `pp_restore` before
   `_guard_report` reads globals). Use recorded base config + **`ppsweep_selected.json`** explicit
   overrides, cross-checked vs the final-submission resume record + SHA. No sweep rerun needed if
   those artifacts fully establish the config; else rerun the unchanged parent sweep once, emit
   the canonical effective dict before restoration, verify SHA parity, freeze — count in budget.
2. **Arm isolation.** Per-arm process isolation unnecessary. Sufficient: frozen pre-safe-division
   graph per dataset; deep-copied nodes/edges/**stats**; immutable retained heatmaps; explicitly
   reset config; separate output/resume records. No RNG dependency in replay stages. Preserve
   insertion/traversal order (tied scores depend on it). Admission must verify arm-order
   invariance + shared graph/heatmap inputs unchanged.

## Non-blocking

§1 slightly overstates the threshold as "gating" while it also feeds gap repair; the narrower §2
decision rules govern. Public-LB selection = tuning evidence, not generalization proof.

## Status

Strategy CONSENSUS reached (3 rounds: REVISE v1 → REVISE v2 → CONSENSUS v3). Next: build on the
repro_059 snapshot with `admission.require_codex_review: true`; first build step = recover
`ppsweep_selected.json` + resume record from the repro_059 kernel output; then fresh Codex
admission PASS + local config-diff test + snapshot smoke + 2.0-h reservation + one launch.
