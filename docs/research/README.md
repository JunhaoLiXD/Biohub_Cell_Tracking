# Research handoff

The latest completed local study is documented in
[diag052_completed_analysis.md](diag052_completed_analysis.md).
The concrete next candidate is specified in
[diag052_original_score_successor_design.md](diag052_original_score_successor_design.md).

The versioned protocol is `configs/local_052_joint_graph_pilot_v1.json`.
Records, immutable source snapshots, scores and audit receipts are in
`experiments/local_052_joint_graph_pilot_v1_attempt02/`. The failed first attempt
is preserved separately. The copied protocol is byte-identical to the final
preregistered local protocol; historical snapshot paths remain unchanged.

The original-score control improved the fixed train16 proxy from 0.9387332377
to 0.9535869213. The context increment hypothesis failed. These are local scores,
not new Public LB results. The verified Public LB candidate remains 0.944.

The local pilot needs NumPy and SciPy. Tests also need pytest. Collected Kaggle
artifacts and generated graph files are intentionally ignored and must be restored
locally from the recorded evidence donor before rerunning artifact-dependent
analyses. Full runs refuse to overwrite existing output directories. A replay
must use a fresh output directory and preserve the prior experiment records.

Private continuation notes, credentials, datasets, weights and local environments
are not part of the GitHub backup. Public copies of the current results and
successor design above provide the essential handoff without those local files.
