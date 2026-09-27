# Strategy consensus v1 - ep015 and CPU counterfactual

2026-09-27 UTC. Claude-authored proposal: `claude_strategy_v1.md`.
Independent Codex objections: `codex_critique_v1.md` (ten findings).
Author revision/acceptance: `claude_strategy_v3.md`, ending AUTHOR ACCEPTS REVISIONS.
The intervening v2 call hit the six-tool-turn ceiling without a response; its receipt
is preserved. The subsequent text-only author response did not rerun any inspection.

Codex independently accepts the corrected strategy and implementation scope. All
ten findings are addressed. Status: **CONSENSUS**. This is strategy consensus only,
not experiment admission PASS or a claim that the hypothesis will improve accuracy.

Scope: one exp_068_ep015_single_probe, ep015 only on the frozen exp064-compatible
vehicle, plus the <=128-subset zero-GPU TRAIN-only diagnostic. Expected ~0.5 h;
reserve 2 h; a 5400 s process watchdog bounds code execution, not platform startup.
No status polling, automatic retry, second LB probe, training, public push or final
re-selection. User has already authorized one LB submission after successful output
audit and authenticated remote-history/daily-cap checks. No additional approval is
needed for that action inside this scope. Retain submission 56535761 selected.

Implementation clarifications from source inspection:
- Validator's Python global is defined in vehicle cell 7, after base submission in
  cell 5. The pre-write guard checks the environment flag; final contract also checks
  the resolved global. It must not manufacture that global early.
- Vehicle SHA is proved at build/smoke and frozen in the manifest; runtime checks
  observed dependency hashes and effective globals. Do not claim to hash an absent
  archived notebook on Kaggle.
- The runtime contract is additive validation/telemetry, not a new inference adapter.
- The watchdog is the existing project design; early missing psutil fails rather
  than allowing an unbounded run. Same limit on hidden rerun; failure means stop.
- Equality of aggregate metrics does not imply graph identity. Pruning can change
  coordinates through downstream linefit and can change divisions; report changes.

Gate order: build -> immutable snapshot -> fresh request_codex_review.py PASS ->
snapshot smoke -> controller reservation/launch -> user completion notice -> collect
once -> independent graph/config/hash/degradation audit -> one authorized submission.
CPU diagnostic may execute now under this consensus; it cannot authorize training.
