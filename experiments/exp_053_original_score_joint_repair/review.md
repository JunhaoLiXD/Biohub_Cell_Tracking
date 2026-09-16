Review complete. Here is the full assessment.

---

# Independent review — `exp_053_original_score_joint_repair`

## Summary
exp_053 ports the fixed **original-score** joint cut-and-reconnect rule from the local_052 attempt02 pilot into the production notebook, applied once **after** the frozen linefit smoothing, on behavior parent `repro_041_public_0941_motion_ema`. Only joint-graph edge selection changes; nodes, coordinates, smoothing, models, EMA and validation are held fixed. The hypothesis is a clean single-variable reproduction claim (aggregate 0.9535869213120838, +0.01485368362467987 over the parent, division 4/8/8). The implementation is coherent and **fail-safe**: the primary exposures are runtime-only and all fail closed with no submission and no false KEEP. Remaining blockers are administrative (smoke PASS, reservation).

## Methodology
- **Testable / one variable:** Yes. Change confined to `_jr_finish` post-smoothing; edge selection only. Inference-identity receipt re-asserts unchanged parent/models/EMA/scorer/samples.
- **Validation protocol:** Frozen train16 stratified proxy over both specimens (44b6, 6bba, 8 each), explicitly labeled optimistic ("frozen models saw training videos"). It is a paired **exact-reproduction** gate — appropriate for "does the pilot gain survive production integration," not a holdout. The 44b6/6bba split and per-specimen outcomes are pinned by exact per-video score rows.
- **Leakage:** Clean. `load_original_candidates` reads only probabilities/threshold/detection-indices; smoke asserts the embedded core has no `final_scored`/`scorer_matching`/secondary-feature tokens. `DetectionProvenance` blocks recovered-node identity reuse.
- **History:** Not duplicate, not contradicted. Context arm is REJECT_LOCAL_POLICY; original_score was the promising local control (gain confirmed in the pilot result). Parent is terminal KEEP; GOAL.md authorizes exactly this successor.

## Implementation risks
1. **Strict cross-platform output-graph hash (primary).** Remote Linux repair (embedded SciPy 1.18.1 `_lsap` + Linux `libm`) must bit-exactly reproduce the Windows-computed local_052 reference edge sets for all 16 videos. Node coords are preserved and inputs derive from the **same-image** diag_051 pipeline, so input-hash risk is low; the *output* edge-set hash across platforms was **not** locally verified (parity only proved Windows==Windows). A near-tie flip (`math.log` in utility; `gain <= 1e-10`) fails the contract — diag_044-style: no result, ~2h burned, never a false KEEP.
2. **Embedded ELF load.** Hash-pinned, isolated module, does not replace system SciPy/NumPy; native-load + occupied-swap assertion runs before GPU inference and hard-stops on failure. Acceptable.
3. **Test-scale evidence export (new/unmeasured).** diag_051 exported only train16 crops; exp_053 now also caches pair/pre_ilp NPZ for full test specimens. Volume/disk/runtime on `/kaggle/working` never exercised at test scale — a missing cache crashes `_jr_begin` (safe, but wastes the reservation).
4. **Contract completeness:** Good — solver pin, test∪validation coverage, exact I/O graph hashes, exact score rows (abs_tol 1e-12), aggregate/gain/division gates; `reproducible=False` set honestly. Guards verify the **effective** config, not stale prose.

## Budget
2.0 GPU h within 30h available / 6h protected (24h usable). `budget.reserved` is `false` and `GPU_BUDGET.reserved_hours` is empty — reservation must be placed at admission. Information gain is moderate (edits mostly outside annotation support; heterogeneous, one video regresses; optimistic proxy). Claude weekly allowance reported unknown; this is a single bounded review, no auto-retry.

## Required changes
No code edits to the experiment are required. Before launch:
1. Snapshot smoke must PASS (`scripts/validate_original_score_joint_repair.py`) — currently PENDING.
2. Reserve 2 GPU h; preserve the 6 protected hours.
3. Treat the run as also a cross-platform reproduction test: a strict output-hash mismatch is a no-result failure — do **not** auto-retry or relax remote hashes without a fresh decision.
4. Keep single-launch, no-submission, no-promotion scope.

## Recommendation
Well-scoped, single-variable, leakage-free, honestly labeled, and fail-safe — every residual risk stops the run without a submission or a false KEEP. Safe to proceed to the next controller stage (snapshot smoke, then the single 2-hour remote validation after reservation).

VERDICT: PASS
