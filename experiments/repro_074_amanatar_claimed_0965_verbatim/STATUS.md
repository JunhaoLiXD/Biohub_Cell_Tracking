# repro074 terminal result — REJECT

Authenticated Kaggle submission `56650147` completed with Public LB **0.901**.
This is **-0.052** versus the retained exp064 baseline at 0.953 and **-0.064**
versus the notebook's advertised 0.965 score axis.

The byte-verbatim run completed and its 240,311-row CSV passed the structural
audit. However, all four advanced repair calls raised `NameError` for undefined
`SAFE_DIV_HORIZON_FRAMES` and fell back to basic-filtered ILP graphs. The score is
therefore the notebook's actual fallback behavior, not evidence for its advertised
complete mechanism.

Per the user's instruction, this branch is terminal **REJECT**. Retain artifacts
as immutable negative evidence. Do not repair, rerun, resubmit, promote, or derive
a successor from this notebook. Retain exp064 at 0.953.
