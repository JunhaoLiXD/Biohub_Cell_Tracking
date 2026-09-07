I now have complete, independently verified evidence. Every claim in the reproduction record checks out against the raw artifacts. Here is the review.

---

# Post-run final review — `repro_041_public_0941_motion_ema`

## Summary

`repro_041_public_0941_motion_ema` is an independent identical rerun of terminal-KEEP `exp_040_public_0941_motion_ema` (the isolated motion-relink per-track EMA, α=0.4, velocity weight 0.5). I re-derived every result-bearing quantity directly from the collected artifacts rather than trusting the summaries. The reproduction is exact on all contract dimensions: aggregate and per-specimen metrics are bit-for-bit equal (difference 0, far inside the 1e-12 absolute / zero relative tolerance), division counts and EMA telemetry match exactly, and the submission plus all raw evidence files are byte-identical. Runtime was healthy with no faults. This establishes **repeatability only** — not generalization or leaderboard improvement. The prior post-run review substantively concluded PASS but omitted the mandatory terminal verdict line; this review supplies the missing machine-readable verdict.

## Evidence

**Byte-identical result-bearing artifacts (SHA256, repro_041 vs exp_040):**
- `submission.csv` — `FD1162BF…125515` on both, and equal to the reference SHA256 in GOAL.md. ✅
- `validator_results.csv` — `2E6B0BF3…DA85` on both. ✅ (identical raw per-video data ⇒ identical derived metrics)
- `inference_identity.json` — `1508AAD5…A765` on both. ✅
- `validation_stage_stats.json` — `ABFD502A…F544` on both. ✅

**Aggregate / specimen metrics (recomputed from `metrics.json`, both runs equal):**
- Aggregate primary `0.9387332376874039`; adjusted-edge `0.9187332376874039`; division Jaccard `0.2`.
- 44b6 primary `0.9228460029238004` (adjusted-edge `0.9028460029238004`); 6bba primary `0.9442148231081169` (adjusted-edge `0.9242148231081169`).
- All values string-identical between runs → deviation exactly 0 ≤ 1e-12. ✅

**Division counts** (independently summed from the 16 `validator_results.csv` rows): TP=4, FP=8, FN=8 aggregate; 44b6 = 2/5/3, 6bba = 2/3/5. Exactly matches exp_040 (and reflects exp_040's FP improvement from val_039's 4/9/8 → 4/8/8). ✅

**EMA telemetry** (summed from CSV): 44b6 = 255,602 EMA predictions, 6bba = 137,643; one-frame fallbacks = 0 and skipped-large-frames = 0 on every row. Matches exactly. ✅

**Frozen inference / checkpoint identity** (`inference_identity.json`): DeepCenter epoch-2 `best.pt` SHA256 `8040999a…e2a0`, path/hash bound; `motion_relink_velocity_estimator = per_track_ema`, α=0.4, velocity weight 0.5; parent submission `bf66c879…52bd`; all 19 identity checks true. `metrics.json` checks block: all true, `failed_checks`/`failed_reproduction_checks`/`failed_research_gates` empty; `reproduction_passed: true`, all six `reproduction_checks` true. ✅

**Runtime health**: remote log has no traceback, exception, OOM, or CUDA error — the only "error" strings are the expected per-video `errors: …` diagnostic counts, `error_summary` JSON keys, and empty `failed_checks: []`. Dual T4, both specimens exercised. Runtime `3817.16 s` (1.0603 GPU-h) vs exp_040 `3883.80 s`; runtime equality was never a reproduction gate. ✅

**Expected non-result differences** (correct, not defects): `metrics.json` differs only in `runtime_seconds`, `reproducible` (`true` here vs `false` in exp_040 — this run is what flips it), and the repro-specific `reproduction_checks` block.

**Review-format failure confirmed**: `post-run-review.md` states PASS in prose but ends without a `VERDICT:` line; the receipt `post-run-review.json` correctly records `status: CHANGES_REQUESTED`, `verdict: MISSING`, `exit_code: 0`. The process succeeded; only the terminal format was non-compliant.

## Limitations

- This is repeatability under the **frozen, optimistic train16 stratified proxy** (16 samples; models saw training videos — see the `warning` field in `metrics.json`). It is not evidence of generalization or Public LB movement.
- The underlying exp_040 effect is small and heterogeneous at the video level (8 positive / 1 zero / 7 negative adjusted-edge deltas; worst −0.00373). Exact reproduction does not change that.
- Determinism is demonstrated for this pipeline/seed/environment; it does not certify robustness to seed or environment changes.
- **PASS here authorizes nothing operational.** No leaderboard submission, formal promotion, milestone v06, new experiment, or remote push is authorized. A leaderboard submission may be *discussed* but still requires separate explicit user authorization.

## Recommendation

Accept the reproduction as a passed repeatability gate and record the formal PASS that the prior review omitted. Report the exact reproduction and the earlier format failure to the user. Take no further action (no LB submission, promotion, milestone, launch, or push) without new explicit direction.

VERDICT: PASS
