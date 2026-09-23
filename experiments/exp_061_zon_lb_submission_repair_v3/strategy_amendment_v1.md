# exp061 zon deployment amendment v1 (proposal; not consensus)

Status: proposal only. No v3 code, snapshot, launch, or submission has been created.

## Evidence and hypothesis

The v2 hidden rerun failed with Kaggle's generic unhandled-error message. Its traceback is not available. The visible v2 run completed and passed its development audit, but took approximately the full two-hour research budget. The parent notebook completes its full inference cell before calling the appended exp061 harness. The harness then runs the original-XY current-input reference and three arms (`xyonly`, `zon`, `xyd4`). This makes the extra replays a credible workload contributor; neither a timeout nor workload as the cause is established. Hidden inputs may also expose a correctness or environment failure.

Hypothesis: removing development-only replays from the scoring path will reduce runtime and memory pressure while leaving the zon prediction path and emitted rows unchanged for a fixed input.

## Exact proposed deployment change

Parent: `exp_061_zon_lb_submission_repair_v2`, preserving the frozen exp061 prediction policy and all checkpoint/model identities.

1. In a new v3 builder, start from the same upstream notebook and retain parent setup, model loading, the input graph generation needed by `filter_output_graph`, and the unchanged zon view and veto implementation. Do not skip or rewrite upstream prediction stages unless a separate parity proof demonstrates they are unused by zon.
2. Add a separately named deployment entry point in `scripts/exp061_deepcenter_tta.py` that executes exactly one `zon` arm. It must not execute the original-XY reference, `xyonly`, or `xyd4`. Keep the existing research harness unchanged for historical/research use.
3. Define deployment integrity gates explicitly: verified checkpoint and cache provenance; frozen effective parent config; exact zon view sequence/count; finite heatmaps and scores; all required datasets completed; valid graph constraints; valid nonempty CSV schema/rows; receipt digest equals the atomically published `submission.csv`; and a complete runtime/failure receipt. Remove the cross-arm parity/mechanism checks only from this deployment contract. Do not accept missing, nonfinite, or failed veto calculations as a pass. A valid zero-candidate/no-veto dataset is allowed only when every candidate/veto call has an explicit complete receipt and graph output passes all constraints.
4. In a new v3 adapter builder/validator, preserve all upstream inference cells byte-for-byte apart from experiment identity/watchdog metadata; prove the v3 zon view implementation and per-input CSV bytes match v2 zon on available public fixtures. Publish only after every deployment gate passes; remove any stale `submission.csv` first and fail closed on all errors.
5. Preserve the two-hour watchdog. The design is inadmissible until a measured upper-bound worksheet shows parent inference plus zon replay plus finalization reserve fits that limit on a workload proxy at least as large as the documented scoring workload. Do not use a mean-only estimate or simply raise the watchdog.

## Required local regressions before review

- Fixed-input byte parity: v2 and v3 zon CSVs are identical on the four public test movies; compare row data, output hash, graph invariants, and effective-config fingerprint.
- No-veto case: create a fixture with zero accepted/triggered repair candidates and confirm successful well-formed output only when every score computation is finite and accounted for. Missing/nonfinite/error score fixtures must fail closed and leave no `submission.csv`.
- Workload scaling: replay the complete v3 path with at least 4x the public movie/frame workload, including parent input generation and zon inference; report peak memory, per-stage wall time, and a conservative 20-minute finalization reserve against the unchanged 2-hour hard stop. This is a screening proxy, not proof about Kaggle hidden data.
- Publication negatives: corrupt/missing zon CSV, incomplete dataset set, invalid graph, digest mismatch, and interrupted atomic publish all leave no submission artifact.

## Current blocker and stop rule

The available record does not contain per-stage v2 timings, peak memory, hidden dataset size, hidden traceback, or a 4x scaling run. The visible run consumed approximately the entire two-hour budget, so feasibility cannot presently be established. The upstream notebook executes inference before the appended harness, and no demonstrated safe shortcut removes that work. Therefore this proposal does not claim a repair and no v3 implementation has been built. Stop until the required workload profile and behavior contract can be validated; any eventual launch and LB submission require fresh independent admission, snapshot smoke, budget accounting, and separate explicit user authorizations.
