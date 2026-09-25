## Summary

**BLOCK pending a recorded validation-contract amendment.** The repair is plausible and preserves inference source, but replaces a consensus-required fixed parent hash with a current-input reference. Explicit consensus covering that change is missing.

Read-only checks passed: all four snapshot manifest hashes match, code cells compile, downloaded upstream cell source matches the original experiment snapshot, and the repair contains only the declared replay and publication changes.

## Methodology

Both copy submissions failed, including the known-good xyonly bytes. This supports a submission-mechanism problem, but does not prove the precise scorer failure.

The proposed full-pipeline rerun is testable and worthwhile: successful scoring would establish a working submission route. It supplies no new `44b6`/`6bba` held-out validation or evidence of improved generalization. No new label-dependent prediction change was found.

The Claude-authored v5 proposal and Codex objection/revision trail explicitly reached **CONSENSUS**. However, that agreement requires fixed parent-SHA parity. The [repair record](E:/Project/Biohub_CellTracking/docs/research/exp061_lb_submission_repair.md) references that agreement without recording objection/revision consensus for its replacement parity contract.

## Implementation risks

- **Shared drift can pass the new check.** Original-XY and cached-XY replays share current predictions, configuration, and graph writer. Equality verifies their agreement, but cannot independently establish reproduction of the historical parent. Keep development-output hash checks as a separate mandatory audit.
- **The new replay is untested by the repair smoke.** `validate_exp061_lb_repair.py` checks source equality and exercises publication with a mocked runner; it never executes the injected reference replay.
- **The config describes the wrong contract.** Its validation warning still promises fixed historical SHA equality and unchanged additive construction.
- **Known guard limitations remain inherited.** Configuration coverage omits adaptive short-track rescue; mismatches are detected without stopping before costly replay. These are previously recorded caveats, not newly introduced defects.
- Publication correctly requires integrity, completed zon, and matching digest. Normal metrics support the injected experiment ID, but watchdog failure metrics still hard-code the original experiment ID.

## Budget

The ledger reports **23.493 hours**, with six protected and no active reservation. Two hours are affordable, although prior consumption is approximate.

The added original-XY replay incurs additional work; its timing is cleared from `dataset_costs`, reducing visibility into total replay cost. Preserve its timing separately. Exact weekly model allowance remains unavailable.

## Required changes

1. Record a versioned amendment covering current-input parity, retained development hashes, objections, revisions, and explicit **CONSENSUS**.
2. Update the config and metric descriptions to the actual validation contract; correct watchdog experiment identity.
3. Add behavioral coverage for reference-before-patching execution, parity mismatch, reference failure/budget abort, and absence of fallback publication.
4. Preserve reference timing, then obtain fresh admission, snapshot smoke, and the two-hour reservation. Before submission, audit development hashes and query the remote daily submission history.

## Recommendation

Do not launch this snapshot yet. The transport repair is technically credible, but its changed validation contract needs explicit agreement and targeted verification. No new inference strategy is required.

VERDICT: BLOCK
