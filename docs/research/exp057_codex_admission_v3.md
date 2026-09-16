## Findings

1. **Metrics compatibility — REVISE.** Numeric `primary_metric`, exact `validation.protocol`, and required provenance hashes are correct and would satisfy `parse_metrics`. However, `runtime_seconds = predict_seconds + offpass_seconds` is not full-run timing: `predict_seconds` stops before the primary/on-pass postprocessing and submission generation. Thus on-pass postprocessing—including its DeepCenter CUDA work—is omitted.

2. **Second GPU pass — PASS.** The off pass explicitly discloses repeated DeepCenter CUDA processing and includes its measured wall time in both `timing` and `runtime_seconds`.

3. **Parity — PARTIAL.** Edge-list order is now preserved; only fields within each record are canonicalized. But no dependency-capable execution receipt/environment is declared, and the available `.venv` lacks NumPy/SciPy, so the required execution remains unverified.

4. **Static validation — PASS.** It passed locally. After restoring only the motion-relink cell’s source, the complete parsed notebook is compared against the SHA-pinned base—including structure, order, metadata, outputs, and nbformat. Independent in-memory reconstruction also exactly matched the checked-in notebook.

No other blocking defect found. Controller proposal/snapshot/smoke, reservation, and explicit authorization for the single leaderboard submission remain pending.

VERDICT: REVISE (runtime_seconds omits the primary/on-pass postprocessing interval; dependency-capable ordered parity execution remains unverified)
