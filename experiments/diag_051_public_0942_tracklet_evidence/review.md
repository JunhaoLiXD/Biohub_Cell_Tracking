Review complete. This was a read-only methodology review, and the deliverable is the assessment itself (not a code-change plan), so I'm returning it directly.

# Review — diag_051_public_0942_tracklet_evidence

## Summary

`diag_051` is a behavior-preserving, observation-only evidence export built from the immutable `repro_041` snapshot (EMA 0.4, train16 0.9387332376874039, Public LB 0.942). It adds read-only hooks that persist a sparse candidate-logit pool, two-frame appearance embeddings, 11 post-processing stage graphs, a pre-ILP node-ID registry, and the scorer bipartite matching — so the next longer-context tracklet-association pilot can be scoped against reachable error. Predictions are byte-gated to the parent; no training, no inference-parameter change, no submission. Controller state is `MANUAL_REVIEW_REQUIRED` (review + smoke PENDING); this review gates smoke.

## Methodology

- **Testable / single-variable:** instrumentation only. Predictions are held constant by exact submission SHA (`fd11…`) and validator-CSV SHA (`2e6b…`) gates, so the diagnostic is cleanly attributable.
- **Protocol / leakage / 44b6–6bba:** reuses the frozen train16 stratified proxy (8/specimen, both required, per-specimen reported). Leakage is acknowledged and correctly scoped — this is an offline reachability audit, not a generalization or advancement claim. GT enters only the offline `final_scored`/`scorer_matching` payloads, never the predictor; no metric can be gamed since predictions equal the parent byte-for-byte. Grouped-split design is explicitly deferred to the future pilot.
- **Parent justifies successor:** the residual error inventory in the design (258 fragmentation edge FN, 181 detection edge FN, division 4/8/8) matches `repro_041` metrics exactly (101+157, 44+137, 4/8/8). Parent choice correctly avoids the TTA lineage (val_049/exp_050). History supports the direction — division graph-only Family-A routes closed at 0.0 (diag_027–033) and the motion-relink bonus sweep saturated, so the association audit is the redirect the archived v9 §7 fallback and optimization audit §5 anticipated. Not duplicate, not contradicted.

## Implementation risks

- **Worker local-variable dependency (the diag_044-style risk) — verified low.** I confirmed in the frozen predictor that every name the worker reads exists at the `del unet_out` insertion point (`probs, c_src, c_tgt, candidates, cfg, t_src, t_tgt, raw, idx_src, idx_tgt, all_edges, ds_arr, unet_feat_*, secondary_*, _ev_primary_logits`, and `ds_path` for `_ev_begin`). `seen_pairs` + window stride W−1 guarantee each consecutive pair once → 99 exports, matching the contract, no false duplicate-guard trips.
- **JSON strictness:** `allow_nan=False` plus a numpy `.item()` default handler are applied; evidence fields are native types — the diag_044 serialization lesson is incorporated.
- **Fail-closed run-completion risks** (waste GPU on failure only; no data corruption, submission still byte-gated): (1) the 128 MiB per-video cap can raise mid-run if node-count × feature-dim exceeds the estimate — un-checkable locally; (2) `worker_exports_complete` assumes all 16 videos have 100 nonempty frames (99 pairs); (3) hard dependency on `secondary_model` being present; (4) stem-key consistency between worker and graph hooks.
- **Algorithm preservation:** static smoke checks predictor + notebook function ASTs identical after erasing only `_ev_`-prefixed calls/assignments; selector cell exact except two observation-enabling lines; runtime guards are the parent's `effective_*` checks plus live SHA equality — not stale prose. Strong.

## Budget

2.0 GPU h (≤ 4.0 cap; 16.83 h remaining, 10.83 usable outside the 6 h reserve). One run yields the missing candidate/appearance/stage/matching evidence to choose the next major direction, no submission. High information gain per GPU-hour, contingent on completion.

## Required changes

No code changes. Pre-launch confirmations: (1) local unit tests and static smoke must pass (smoke PENDING); (2) confirm per-video cache headroom under 128 MiB, or accept fail-closed as the only downside; (3) confirm all 16 frozen videos have 100 nonempty frames; (4) confirm `secondary_model` present (it is).

## Recommendation

Hypothesis testable and attributable, algorithm preserved and machine-verified, exact-byte and effective-config gates intact, contract fields present, parent result and error inventory justify the successor, no correctness defect found. Residual risks are fail-closed completion issues addressed by smoke plus two manifest confirmations. Safe to proceed to the smoke-test stage.

VERDICT: PASS
