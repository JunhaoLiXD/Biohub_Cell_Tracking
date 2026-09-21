# exp_061 — Codex strategy challenge v4 (verdict: REVISE, single accounting item)

Reviewer: Codex `gpt-6-astra`, low, read-only. Date: 2026-09-20.
Target: proposal v4. Full trace: scratchpad `exp061_codex_challenge_v4.log` (2769 lines).

## Verdict: REVISE (one finding; no strategy redesign)

**Verified resolved by Codex:** v3-1 (consumer inventory), v3-3 (disk-backed cache policy), v3-4
(cross-arm parity fallback), v3-5 (superseded `v2_key_fixes` + 17-forward risk-table count). "No
transform/inverse regression or additional substantive defect found; no earlier resolved finding
reopened." The obsolete consumer wording remains only as a quoted historical finding.

Sole remaining finding (fixed in v5):

1. **P2 — v3-2 leftovers: three accounting passages still stale.**
   - §8 still asserted "feasible under the 2.0-h watchdog" → made **conditional on the measured §7
     admission estimate**.
   - §7 attributed "450–476 s/row" to the artifact; actual range is **390.835–413.262 s**, 8 rows
     = **54.5265 min**, 7 non-base = **47.6832 min** (historical validation-with-scoring, not
     guaranteed savings / test-replay) → corrected.
   - §15 row v2-3 and STATE `exp061.v3_key_fixes` retained the withdrawn "≈60-min sweep removal"
     (and §15 the old eviction/stream policy) → explicitly marked **SUPERSEDED by v4 §7**,
     preserving historical context.

## Minimal changes to CONSENSUS

"Reconcile the passages above. No strategy redesign or additional experiment is required."

## Status

Strategy REVISE (round 4, single accounting item). Claude revised → proposal v5. Next: Codex
re-challenge (round 5) for the explicit CONSENSUS record. On CONSENSUS: proceed to build +
fresh Codex admission review of the implementation.
