## Admission review

Source identity and attribution are adequately frozen by URL, authenticated retrieval date, raw SHA256, immutable snapshot manifest, and byte-identity smoke. Evidence supports no TEST-label access, no internet, the expected four public data/model sources, no leaderboard API calls, and private execution only. The TRAIN holdout sweep is disclosed correctly and is not represented as independent evidence.

The public output is byte-distinct from the retained parent, the 3.0-hour reservation reasonably covers the reported 2.16-hour runtime, concurrent reservations preserve stated headroom, and the one-launch/no-retry/no-submission stop rule is appropriate.

### Required changes

- **R079-CLASS-01 — Incorrect Tier B classification.** The candidate replaces the parent with an entire third-party notebook and potentially different models, inference, validation selection, and post-processing. No parent-to-candidate evidence establishes a small localized change with unchanged model and graph semantics. Under the supplied workflow this is Tier C, irrespective of the legitimate byte-verbatim constraint. Reclassify it and satisfy the Tier C strategy/challenge/consensus gate, or provide deterministic evidence that the notebook is the verified parent pipeline with only the stated localized post-processing difference.

- **R079-OUTPUT-01 — Runtime output contract is underspecified.** Publication of a parseable `submission.csv` and a final `pd.read_csv` do not define or enforce the competition artifact contract. Before launch, identify a frozen collector/checker and its required checks, including exact columns, row/ID coverage and uniqueness, finite and bounded coordinates, valid parent references and temporal edges, expected test-video coverage, and artifact hashing. The existing stop rule can then act on a concrete `output_integrity_passed` result.

These are admission-gate deficiencies, not requests to repair or modify the third-party algorithm.

VERDICT: REVISE
