# exp071 delta-only Tier B review packet

Prior review: `experiments/exp_070_ep015_hidden_rerun_repair/review.md` returned
REVISE with F1-F3. This packet contains only their resolution.

- F1: degraded output is still forbidden. Both the environment assignment and
  `_EXPECTED_NUMERIC` guard for `BIOHUB_REPAIR_DEADLINE_S` change from 27000 to
  32400, matching `BIOHUB_WALL_BUDGET_S`. The 5400-second `os._exit` killer is
  replaced by passive timing. The inherited final assertions requiring
  `deadline_degraded == False` remain unchanged. Thus the accepted output policy
  remains full repair; no degraded/fallback output becomes admissible.
- F2: config validation protocol is
  `exp071_prediction_neutral_source_delta_v2`. Emitted metrics retain inherited
  output protocol `ep015_single_probe_v1` and now explicitly add
  `admission_protocol: exp071_prediction_neutral_source_delta_v2`.
- F3: the active timer comment and message now identify exp071.

Deterministic receipt: `scripts/smoke_exp071.py` PASS. Compared with immutable
exp068, changed code-source cells are exactly 0, 1, 2, and 6. Reversing the
declared timer, two deadline, runtime-bound, experiment-ID, and protocol-metadata
changes gives exact source equality. Every code cell compiles in the builder.

No model, checkpoint, inference, threshold, graph algorithm, data discovery,
fallback acceptance, output writer, or CSV audit changed. Budget remains 2 GPU
hours, currently unreserved. User authorized continuing through gates and one
kernel launch; leaderboard submission remains unauthorized. Stop on degraded or
fallback output, any gate failure, or undeclared delta.
