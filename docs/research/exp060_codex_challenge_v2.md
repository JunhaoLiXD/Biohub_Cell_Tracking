# exp_060 — Codex strategy challenge v2 (verdict: REVISE, converging)

Reviewer: Codex `gpt-6-astra`, low, read-only. Date: 2026-09-18.
Target: proposal v2 (safe-division threshold micro-sweep). Codex verified core code claims.

## Verdict: REVISE (converging — core verified, 3 narrow items remain)

**Verified by Codex:** safe-division 0.20 and gap 0.25 are separate thresholds; heatmap
generation is threshold-invariant; shared `(dataset,t)` caching is valid within the frozen
inference context.

## Remaining must-fix

1. **Specify the replay implementation.** `filter_output_graph` creates fresh caches;
   `_dc_cache_trim` evicts heatmaps; `write_test_submission` reruns full postprocessing and
   overwrites one CSV. Define: a frozen pre-safe-division graph, independent deep copies per
   arm, retained heatmaps/scores (no eviction), separate output/resume records per arm. One
   inference is feasible with these changes, but 1.3–1.5 GPU-h is an ESTIMATE, not measured.
   The 2-hour hard stop is adequate.
2. **Narrow decision rules further.** Two rounded ties establish only this bracket's
   unresolved effect; a regression does not establish near-optimality. Neither closes
   threshold tuning nor rules out TTA. Public-LB selection is tuning evidence.
3. **Unambiguous telemetry identities:** dataset, parent ID, existing-child ID, candidate-
   child ID, frame, and score; track exact final fork and edge identities. Daughter position
   alone cannot distinguish competing parents.

## §11 open-question rulings

1. **Keep 0.18/0.22.** Bounded local sensitivity probe; do NOT widen after seeing results.
2. **Capture and verify parent runtime artifacts** (recorded base config + selected overrides,
   pin effective globals) + retain submission-SHA parity gate. A reconstructed `tight55` label
   alone is insufficient.
3. **No test division confusion** (needs unavailable GT). Emit predicted fork identities/
   counts. Confusion on labeled TRAINING movies would be a separately-scoped exploratory
   baseline.

## Factual corrections

- "Division-exclusive" describes the INTERVENTION, not every downstream effect: changed forks
  can alter short-track retention and smoothing, including final nodes and NON-division edges.
- Lower thresholds admit more candidates through the score GATE, not necessarily more FINAL
  divisions (caps and conflicts intervene).
- §0's "three submissions" contradicts §5: produce three files; submit at most the two changed
  candidates (no duplicate 0.20 control submission).

## Resolution

Folded into proposal v3 (2026-09-18). See `exp060_deepcenter_division_tta_proposal.md` §12.
