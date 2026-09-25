# exp_064 Codex admission — VERDICT: PASS (round 5)

Reviewer: Codex `gpt-6-astra`, effort low, read-only, 2026-09-24.
Target: snapshot `6b655e39bbfd2d3d6c762badea69847d3f00f5b548f385cb01b07ee2600fde6d`
(anvithpothula/biohub-x138, verbatim) + `scripts/collect_exp064_x138.py` + the config.

Five rounds. Round 1 REVISE, rounds 2-4 REVISE, round 5 PASS. Every round found real defects;
none was a tool-access block. Summary of what the process actually caught:

| round | finding | whose defect |
|---|---|---|
| 1 | "coordinate head, orthogonal to our edge work" was incomplete and overstated; five mechanisms omitted | mine |
| 1 | no basis to infer a 0.947 score floor from the author's rank | mine |
| 2 | adapter false pass: `node_id=-7, t=999999, coords 1e30` — `math.isfinite(1e30)` is True | mine |
| 2 | degradation regexes were guessed, not read from the notebook; none matched | mine |
| 3 | adapter false pass: stats with only a `dataset` column — absent telemetry read as "no degradation"; dangling edge endpoints unchecked | mine |
| 3 | the claim that a V1284 mismatch "cannot silently degrade" was too strong | mine |
| 4 | adapter false pass: endpoint existence still admitted a **self-loop**; any non-`node` row treated as an edge | mine |
| 4 | budget paragraph still said "enforceable ceiling" / "worst case" while disclaiming enforcement | mine |

Round 1 also independently CLEARED the notebook itself: Codex executed the patch chain in memory
and confirmed all cells compile, the patched predictor compiles, all 13 support-file hashes match,
and V1284 is genuinely wired in (refine at patched line 636; `_v1284_index` replacing
`UNetNodeTransformer._index_features` at 984) — with correct shapes, bounded and clipped
displacement, `weights_only=True`, strict state-dict matching, and no exception path silently
disabling it. That is the opposite of the exp_063 DivNet defect.

Round 3 gave the decisive disposition on the one risk that cannot be resolved:
*"Full third-party training provenance cannot be independently established... Neither uncertainty
alone must block this bounded reproduction. Record them as unresolved risks and let the remote run
test compatibility."*

---

codex
Both items are discharged by source inspection.

- **A:** Invalid row types fail the gate. Resolved edges with equal or decreasing timestamps fail; unresolved endpoints fail separately. Forward gaps remain allowed and counted. No remaining false-pass path found within this scope.
- **B:** Budget wording clearly distinguishes attended targets from hard enforcement, accepts possible overruns, and requires actual consumption reconciliation after confirmed termination before any retry.

Read-only review; reported fixture and regression results were not independently rerun. Settled items were not reopened.

VERDICT: PASS
tokens used
24,566
Both items are discharged by source inspection.

- **A:** Invalid row types fail the gate. Resolved edges with equal or decreasing timestamps fail; unresolved endpoints fail separately. Forward gaps remain allowed and counted. No remaining false-pass path found within this scope.
- **B:** Budget wording clearly distinguishes attended targets from hard enforcement, accepts possible overruns, and requires actual consumption reconciliation after confirmed termination before any retry.

Read-only review; reported fixture and regression results were not independently rerun. Settled items were not reopened.

VERDICT: PASS
