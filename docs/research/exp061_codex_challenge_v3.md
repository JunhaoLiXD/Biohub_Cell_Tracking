# exp_061 — Codex strategy challenge v3 (verdict: REVISE, cleanup-only)

Reviewer: Codex `gpt-6-astra`, low, read-only. Date: 2026-09-20.
Target: proposal v3. Full trace: scratchpad `exp061_codex_challenge_v3.log` (3102 lines).
Anchors: **proposal** = `docs/research/exp061_z_reflection_deepcenter_tta_proposal.md`;
**N** = `.private/current/exp060_deepcenter_safe_div_threshold_sweep.ipynb`.

## Verdict: REVISE (cleanup-only; no reopened findings)

"The executable transforms in §3 are corrected: `Ta` matches N cell2:2125–2126; `Aad` is
self-inverse; Z inverses, equal weights, and coordinate-mapping assertions are specified. No
previously resolved finding is reopened." Codex also independently verified that
`recover_strict_gap2` (incl. its midpoint-refinement path) reads no DeepCenter heatmap.

Five remaining consistency/accounting fixes (all fixed in proposal v4):

1. **P2 — Consumer inventory still contradictory.** §2/§5 say two consumers, but §0 (lines 27–31)
   still said "THREE places" and §1 (51–52) "two gap-repair vetoes." → corrected to two direct
   consumers (gap1 N cell2:2454 + safe-div 2731), gap2 downstream. Snapshot-before-gap1 preserved.

2. **P1 — Sweep-saving / replay costs conflated.** `ppsweep_results.csv` = 8 rows ≈ 54.5 min, but
   that is the **base validator pass + 7 candidates**, timed on **8 validation samples WITH
   scoring**, not a 4-test-movie replay. Disabling candidate selection removes only the 7 candidate
   passes (not the base pass), and validation timings don't substantiate the test replay cost. →
   removed the unconditional "more-than-offsets"/feasibility claim; count only removed work;
   distinguish validation-scoring from test replay; reference the in-repo
   `experiments/repro_059_.../artifacts/ppsweep_results.csv`.

3. **P1 — Cache eviction conflicts with sequential arms.** "Compute per frame, let all 3 arms
   consume, then evict" is incompatible with completing `xyonly → zon → xyd4` sequentially (and
   with divergent per-arm frame demand). → chose one policy: lossless **disk-backed**
   per-`(dataset,t,view)` store retained until all arms finish + bounded RAM LRU; budget
   `#frames×#views×bytes` + I/O; removed the frame-streaming alternative.

4. **P2 — Risk table retained the prohibited parity fallback.** §5 was fixed but the risk-table
   row (line 332) still said "fallback to unmodified parent heatmap **for xyonly**." → replaced
   with STOP or the §5 cross-arm fallback (re-verified shared-view equivalence), never xyonly-only.

5. **P3 — STATE reconciliation incomplete.** `key_risk`/`arm_set` were fixed but
   `exp061.v2_key_fixes` still asserted "~15 union/frame … making 3 arms fit," and the proposal
   risk table still had "~15 fwd." A new `v3_key_fixes` field does not withdraw the old claim. →
   marked `v2_key_fixes` SUPERSEDED (17 forwards, conditional feasibility); proposal tables use 17.

## Minimal changes for CONSENSUS

Reconcile the contradictory consumer/fallback/state passages; correct the savings accounting;
specify a storage policy compatible with sequential arms. Keep the corrected transforms, arm set,
frozen config, parity gate, and separate submission authorizations.

## Status

Strategy REVISE (round 3, cleanup-only). Claude revised → proposal v4 (§16 resolution table).
Next: Codex re-challenge (round 4). No build until CONSENSUS.
