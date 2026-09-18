# exp_060 — Codex strategy challenge v1 (verdict: REVISE)

Reviewer: Codex `gpt-6-astra`, reasoning effort low, read-only sandbox.
Date: 2026-09-18. Target: `docs/research/exp060_deepcenter_division_tta_proposal.md` v1
(Z-reflection DeepCenter TTA). Codex independently verified code claims (including a Python
check of the TTA symmetry group).

## Verdict: REVISE

**Crux:** Run the **safe-div threshold micro-sweep 0.20/0.18/0.22 FIRST** (0.20 as byte-parity
control), not the Z-reflection. It directly tests whether the division gate can change
surviving divisions, leaves gap gating unchanged, and reuses upstream predictions and
heatmaps. Z-reflection remains a reasonable *second* probe; the bundled +0.003 does not
establish that DeepCenter TTA helped at all.

## Required fixes

1. **"8-view D4" claim is WRONG (verified).** Parent TTA uses only XY, never Z — confirmed.
   But `rot90(t,1).transpose(-1,-2)` duplicates the X flip: **8 evaluations, 7 unique
   transforms**, missing the anti-diagonal reflection. Z would give 16 evaluations, 14
   unique. Correct the description; repairing the XY group is a *separate* intervention.
2. **Freeze the RESOLVED pp configuration, not just the sweep code.** Re-running the adaptive
   sweep after changing DeepCenter can select different geometry, violating isolation. Pin
   the parent's resolved `tight55` config for every arm; prove the 0.20 control reproduces
   parent submission bytes.
3. **Describe the gate accurately.** Safe-div accept counts = gate passage, NOT surviving
   divisions; missing/nonfinite point scores bypass the veto. Record candidate identities,
   scores, missing bypasses, and final surviving forks/edges. Counts alone cannot attribute
   LB movement to division vs gap repair.
4. **Fix arm isolation + activation checks.** Heatmap cache key is only `(dataset,t)`:
   switching flags can reuse the wrong arm's heatmap → separate caches + invalidate resume
   artifacts. The `delta==0` guard compares augmented vs UNaugmented logits, so it can't
   verify incremental Z activity → compare Z-on directly vs XY-only; treat a genuinely
   unchanged output as a valid NULL, not an implementation failure.
5. **Reconcile budget/execution rules.** <1.6h ignores control+candidate, repeated
   postprocessing, and sweep work. Specify shared computation + measured total. A 2h
   reservation cannot justify a 4h stop. Keep fresh admission, smoke, artifact audit, and
   separate promotion authorization; unlimited submission count does not itself authorize
   execution.
6. **Narrow conclusions.** Historical 4/8/8 is not a measured repro_059 division baseline.
   Equal displayed LB does not prove divisions unchanged; regression does not prove
   "z-anisotropy" (z-reflection preserves voxel spacing). Report rounded ties as unresolved
   below displayed precision; repeated Public-LB selection is tuning evidence, not
   independent generalization proof.

## Strongest null mechanism (against Z-first)

Z averaging changes heatmap values without changing which candidates clear 0.20 and survive
geometry, caps, conflicts, and downstream filtering. It cannot create candidates absent from
this repair path. → lower value for the first GPU hour than the bounded threshold probe (not
intrinsically unworthy).

## Resolution

User decision 2026-09-18: **adopt the crux** — pivot exp_060 to the safe-div threshold
micro-sweep; defer corrected Z-reflection TTA to exp_061. See proposal v2.
