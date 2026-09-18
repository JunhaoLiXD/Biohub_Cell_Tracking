# exp_060 — Codex ADMISSION review v2 (verdict: BLOCK, converging)

Reviewer: Codex `gpt-6-astra`, low, read-only. Date: 2026-09-18.
Scope: v2 implementation (after admission BLOCK v1). Codex actively probed by injecting faults.

## Verdict: BLOCK (core confirmed sound; 4 robustness/coverage hardening items remain)

### Codex-VERIFIED resolved / correct (non-blocking)
- metrics.json fields satisfy the controller schema (v1 fix #1 accepted).
- All three injected candidate IDs are in scope; the no-op stub precedes parent execution; the
  strippable joined-text parity guard is sound; the embedded module matches the script.
- Immediate control-parity stopping is fixed (v1 fix #4 partial accepted).
- Builder + structural checks pass.

## Remaining blockers (→ v3)

1. **Failure handling permits false PASS / missing metrics.** A nonfinite logger score still gave
   integrity=True; an injected filtering exception produced NO metrics.json. Fix: the gate must
   REJECT `error`/`nonfinite` statuses and explicitly govern missing-score bypasses; wrap the whole
   run in an OUTER exception handler that persists failure metrics.json BEFORE (optional) telemetry
   serialization.

2. **2.0-h hard stop not enforced.** Checks are only between arms; the parent run or a single arm
   can overrun and the final arm can finish overdue yet PASS. Fix: add a whole-run watchdog +
   a FINAL elapsed-time gate; a timing-source failure must NOT silently reset the budget clock
   (fallback-to-now would zero elapsed and disable the deadline — make that a failed check).

3. **Attribution incomplete.** The logger records IDs + score but neither the actual gate
   acceptance / bypass reason nor candidate-level FINAL survival. Fix: record accept + bypass
   reason per candidate and join final edges back to candidate identities (survived_final).

4. **Behavioral coverage insufficient.** Passes on an in-memory FS but has no effective-config or
   input/heatmap FINGERPRINT assertions (edge-count monotonicity ≠ threshold-only isolation). Fix:
   add config + heatmap-input fingerprint assertions, the failure/deadline probes above, and
   execute the EXTRACTED real parent gate logic (`deepcenter_accept_repair_point`) with mocked GPU
   deps.

No launch until these clear a fresh admission + snapshot smoke.

## v3 RESOLUTION (2026-09-18) — all 4 blockers addressed; local gates pass

1. **Fail-closed failure handling** — gate now REJECTS error/nonfinite scores
   (`no_candidate_score_errors`, `no_nonfinite_candidate_scores` checks); an outer
   `except BaseException` sets `run_exception` (gate False); metrics.json is written FIRST
   (guaranteed) and telemetry serialization is best-effort in its own try/except so it can never
   mask the metrics. Behavioral test injects a filtering exception (=> metrics still written, gate
   False) and a nonfinite score (=> gate False).
2. **Enforced 2.0-h hard stop** — a POSIX SIGALRM watchdog (`_deadline_watchdog`) raises at the
   remaining budget so a runaway parent/arm is interrupted (caught by the outer handler); a final
   `within_hard_stop_and_timing_reliable` gate fails closed if elapsed exceeds the budget OR if the
   process-start timing source was unreliable (fallback-to-now no longer silently zeroes the clock).
   Behavioral test forces an over-budget elapsed => gate False.
3. **Complete attribution** — each candidate row now records `gate_bypass`, `gate_accept`, and
   `survived_final` (final edges joined back to candidate identities per arm), plus
   candidate_counts (nonfinite/error/missing_bypass/survived_final) in metrics.
4. **Behavioral coverage** — `test_exp060_behavioral.py` now asserts: heatmap-once (GPU counter),
   effective-config fingerprint (only threshold differs), input fingerprint (identical candidate
   set per arm), arm-order invariance, threshold monotonicity, full-ID + accept/bypass/survival
   telemetry, and the fail-closed probes above; AND it EXTRACTS and executes the real parent
   `deepcenter_accept_repair_point` with mocked GPU deps (score<thr rejects / >=thr accepts / None
   bypass-accepts). 19 checks pass.

Local gate suite (all pass): compile; builder parity; structural validator; behavioral test.
NEXT: fresh Codex admission on the v3 build.
