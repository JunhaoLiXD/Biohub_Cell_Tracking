# exp_061 — Codex strategy challenge v2 (verdict: REVISE, narrowed)

Reviewer: Codex `gpt-6-astra`, low, read-only. Date: 2026-09-20.
Target: proposal v2. Full trace: scratchpad `exp061_codex_challenge_v2.log` (3158 lines).
Anchors: **P** = the proposal; **N** = `.private/current/exp060_deepcenter_safe_div_threshold_sweep.ipynb`.

## Verdict: REVISE (substantially narrowed)

"The replay boundary, cache/resume contract, valid-null handling, narrowed interpretation, and
submission route substantially resolve v1. However, the transform specification contains a real
inconsistency, the proposal invents a gap2 DeepCenter consumer, and the revised resource estimate
remains unsupported."

**Disposition of the v1 findings:** P1-1 resolved (subject to the consumer-description fix);
P1-2 partially resolved; P1-3 resolved at strategy-contract level (both cache layers + fail-closed
resume rejection; impl + negative tests are admission work); **P2-6, P2-7, P2-8 resolved.**
P2-4, P2-5 need the fixes below.

## Remaining findings (fixed in proposal v3)

1. **P2 — Transform spec contradicts the parent.** `Ta = rot90(1)∘transpose` (rotate after
   transpose) ≠ parent `transpose(rot90(x,1))` (N cell2:2125, inverse 2126). On an asymmetric
   fixture the parent's Ta ≡ **X-flip**; the written composition ≡ Y-flip — following the table
   literally changes the duplicate's weight in `xyonly`/`zon`. → Give executable forward/inverse:
   `Ta(x)=transpose(rot90(x,1))`, `Ta⁻¹(y)=rot90(transpose(y),-1)`, `Aad(x)=flip(transpose(x),(-2,-1))`
   (self-inverse), explicit composed Z inverses, equal per-slot weights. Fixture asserts must check
   the **intended coordinate mappings**, not merely `inverse(forward(x))==x` (a wrong transform +
   its own correct inverse passes that weaker test).

2. **P2 — gap2 is NOT a DeepCenter consumer.** `recover_strict_gap2` (N cell2:2497–2632) has no
   detector arg / heatmap lookup / acceptance call. The real veto sites are **gap1 (2454)** and
   **safe-division (2731)**. gap2 changes downstream of gap1 but does not read the heatmap. →
   Describe TWO direct consumers; instrument gap1 + division vetoes; trace gap2 as an intervening
   downstream stage. Snapshot before gap1 remains correct.

3. **P1 — Forward count valid but timing/capacity still unsupported.** The parent does **8
   forwards**, not 7 (P confused unique views with executed forwards). No frame count, measured
   forward cost, replay cost, quantified sweep saving, or numeric finalization reserve. Holding
   individual logits across sequential arms needs far more storage than a heatmap cache; no
   placement/capacity/eviction policy (eviction breaks once-per-view; GPU retention can OOM). →
   Add a bounded resource worksheet (historical timings + real tensor shapes/frame coverage);
   specify cache placement/capacity/eviction, a numeric finalization reserve, and runtime-gated arm
   admission; label 1.4–1.8 h provisional. No extra full GPU run needed for strategy consensus.

4. **P2 — Parity fallback can conceal a cached-path discrepancy.** Switching only `xyonly` to the
   original function proves the original path reproduces the parent, NOT that the cached path
   `zon`/`xyd4` use preserves shared-view semantics. → Require the parent's exact left-to-right
   out-of-place lossless accumulation from immutable cached logits (Ta once, not 2×Vx; no stacked
   reduction / reduced precision / in-place). On failure, STOP & diagnose or apply the SAME fallback
   across ALL arms + verify shared-view equivalence. Fallback cost = 8 additional forwards/frame.

5. **P3 — Active STATE.json exp061 fields retain withdrawn claims** (documented OOD risk;
   "in-distribution" companion; "adding" the missing reflection; "cache arithmetic makes 3 arms
   fit"). → Reconcile the active exp061 fields to the revised assumptions/conditional feasibility;
   keep the historical challenge record unchanged.

## Minimal changes for CONSENSUS

Correct the transform expressions + consumer inventory; supply the bounded timing/storage plan;
close the parity-fallback loophole; reconcile active STATE fields. Keep the same three arms,
pre-gap boundary, frozen config, fresh SHA gate, and separate submission authorizations. **No new
train16 study, extra arm, or advance proof of GPU byte parity is needed.**

## Status

Strategy REVISE (round 2, narrowed). Claude revised → proposal v3 (§15 resolution table). Next:
Codex re-challenge (round 3). No build until CONSENSUS.
