# repro079 admission delta round 1

This packet addresses only `R079-CLASS-01` and `R079-OUTPUT-01` from the first
substantive review. Historical evidence is not repeated.

## R079-CLASS-01 closure

The deterministic checker `scripts/audit_repro079_source_delta.py` has SHA256
`f161393d54c230bd04de734691748c46855ae11ac372e2164f3d163c094586c5` and passed
against the frozen x138 archive and repro079 snapshot.

It verifies raw parent and candidate hashes, parses both notebooks, removes blank
lines only, and proves:

- cells 1 through 9 and cell 11 are source-identical;
- cell 0 differs only in the score-axis description, validator enable flag, selection
  margin, and maximum adjusted loss;
- cell 10 differs only by seven appended post-process sweep candidates;
- the sole extra cell is empty.

No model, checkpoint, detection, association, graph construction, inference, or
submission-writing source differs. The change is therefore an inherited bounded
post-process selection experiment rather than replacement by a different pipeline.
The exact byte-verbatim candidate remains the tested object.

## R079-OUTPUT-01 closure

The frozen collector-side checker `scripts/audit_repro079_output.py` has SHA256
`b9a2aa33b9e9e4f52c308798d5c7e76cfb453af806319cc28774904089725be0`.
After collection it must run on
`experiments/repro_079_kunal_public_verbatim/artifacts/submission.csv` and write
`experiments/repro_079_kunal_public_verbatim/output_integrity.json`. A nonzero exit
or `output_integrity_passed != true` terminates the experiment and prohibits any LB
submission.

The contract enforces exact columns; contiguous unique row IDs; the exact four TEST
datasets; nonempty nodes; per-dataset unique node IDs; integer, nonnegative, finite
coordinates within exclusive `(64, 256, 256)` ZYX bounds; valid edge endpoints;
adjacent-frame edges; no duplicate edges; indegree at most one; outdegree at most
two; and a SHA256 artifact identity.

The checker passed on the author's downloaded public output: 238,308 rows across
all four expected datasets, 121,232 nodes, 117,076 edges, zero errors, SHA256
`e424b8c4feadc8d5520d71985ed8f20722e49bab17cd469f543e04681fc8a978`.
This validates the checker and upstream public artifact only; our run must pass
independently.
