# exp_060 — Codex ADMISSION review v4 (verdict: BLOCK) + v5 resolution

Reviewer: Codex `gpt-6-astra`, low, read-only. Date: 2026-09-18.
Scope: v4 (whole-run watchdog + extended behavioral coverage). Codex accepted the watchdog
reconciliation (fail-closed metrics then REMOTE_FAILED during the parent is acceptable).

## v4 Verdict: BLOCK (2 very narrow items)
Non-blocking (accepted): whole-run watchdog reconciliation; builder parity; structural validation;
embedded-module equality; everything from prior rounds.

Blockers:
1. **Commit-time deadline recheck missing.** `within_deadline` is computed before finalization;
   `_write_metrics()` re-samples elapsed but preserved the earlier PASS even if runtime > 7200s.
   Fix: recompute the deadline gate WHEN committing metrics; make expiry sticky (never FAIL->PASS).
2. **Behavioral coverage.** No test executes the injected watchdog handler; the config fingerprint
   had only 2 fields; the heatmap assertion permitted a subset. Fix: handler-interruption +
   commit-time-overrun probes; full effective-config comparison (excluding threshold); EXACT
   heatmap input-set equality.

## v5 RESOLUTION (2026-09-18) — both addressed; local gates pass
1. **Commit-time recheck** added inside `_write_metrics`: if `runtime_seconds > EXP060_HARD_STOP_
   SECONDS` at commit, it forces `within_hard_stop_and_timing_reliable=False` and
   `integrity_passed=False` (sticky: only ever flips PASS->FAIL). Behavioral test asserts the
   final-arm-overrun run's metrics note carries "commit-time over budget".
2. **Behavioral coverage** extended to 30 checks: EXACT heatmap input-set equality; full effective-
   config fingerprint over 7 knobs identical across arms except the threshold; a commit-time
   deadline-recheck assertion; and `_test_watchdog_handler` which EXTRACTS and EXECUTES the injected
   `_exp060_whole_run_guard` from the BUILT notebook, verifying it writes a controller-valid
   fail-closed over-budget metrics.json then raises TimeoutError.

Local gate suite (all pass): compile; builder parity (18 injected `# exp060` lines strip to
parent); structural validator; behavioral test (30 checks).

## v5 ADMISSION VERDICT: **PASS** (Codex gpt-6-astra, 2026-09-18)

"Both v4 blockers are resolved. The commit-time recheck makes persisted metrics fail closed;
independent in-memory probes verified PASS->FAIL and sticky FAIL. The expanded behavioral coverage
is sufficient for this scope. Structural validation, builder parity, embedded-module equality, and
execution of the built watchdog handler passed."

Non-blocking (carry to launch):
- console/telemetry may retain the pre-commit verdict; **metrics.json is authoritative**.
- Before launch: record this admission against the exact snapshot, complete snapshot smoke, and
  reserve budget.

exp_060 has cleared strategy CONSENSUS (3 Codex rounds) + implementation ADMISSION PASS (5 Codex
rounds). Remaining gates before any GPU spend: snapshot smoke + 2.0-h budget reservation + ONE
user-authorized Kaggle launch. The 0.18/0.22 Public LB submissions are a separate user
authorization after the run.
