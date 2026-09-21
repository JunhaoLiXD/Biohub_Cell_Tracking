# exp_061 — Codex strategy challenge v5 (verdict: CONSENSUS)

Reviewer: Codex `gpt-6-astra`, low, read-only. Date: 2026-09-20.
Target: proposal v5. Full trace: scratchpad `exp061_codex_challenge_v5.log` (2522 lines).

## Verdict: CONSENSUS

"The exp_061 strategy — three arms xyonly/zon/xyd4, pre-gap1 replay boundary, view-level
disk-backed cache, executable transforms, per-arm parity and submission authorizations, and
conditional feasibility — is AGREED. (a), (b), (c) are reconciled. CSV arithmetic confirms
390.835–413.262 s/row, 54.5265 min total, and 47.6832 min non-base, correctly labeled historical
validation-with-scoring. No remaining live assertion of the withdrawn claims or new blocking
defect was found."

## Non-blocking build-time notes (the implementation + fresh Codex admission must honor)

- Measure frame demand, forward time, test replay cost, cache capacity, and I/O **before
  admission**; preserve the **20-minute finalization reserve**.
- Retain lossless cached views across sequential arms; enforce provenance, isolation, and **exact
  accumulation order**.
- Require **fresh `xyonly` parent-SHA parity through the shared cached path**; any fallback must
  apply consistently across all arms.
- Complete implementation validation, snapshot smoke, and a **fresh experiment-specific Codex
  admission PASS** before an authorized launch. Each LB submission requires separate authorization
  and duplicate-output checks.

## Convergence trail

Strategy CONSENSUS reached in **5 rounds**:
- v1 REVISE (3×P1 + 5×P2: replay boundary, budget, cache/resume contract, xyd4 spec, guard,
  science overclaim, interpretation, submission route).
- v2 REVISE (narrowed; confirmed P1-1/P1-3/P2-6/P2-7/P2-8 resolved; 5 items).
- v3 REVISE (cleanup; transforms confirmed correct; 5 consistency/accounting fixes).
- v4 REVISE (single accounting item; all findings verified resolved, no new defect).
- **v5 CONSENSUS.**

## Status

Strategy CONSENSUS. Records: `docs/research/exp061_z_reflection_deepcenter_tta_proposal.md` (v5) +
`exp061_codex_challenge_v1..v5.md`. Next gate: build on the repro_059 snapshot with
`admission.require_codex_review: true` → fresh Codex admission PASS → local tests + snapshot smoke
→ budget reservation → ONE user-authorized launch → per-arm LB submissions (each separately
authorized) → then fire the ARMED `pending_followup` reminder for option B.
