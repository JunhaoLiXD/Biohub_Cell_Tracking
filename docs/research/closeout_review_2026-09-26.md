# Closeout review and corrected Stage 0 interpretation

2026-09-26. User authorized local closeout after the Codex REVISE review. This is a
documentation and cached-evidence audit, not a fresh experiment admission PASS.
No training, prediction, decode, remote query, GPU launch, submission or public push occurred.

## Reproduced evidence

`scripts/audit_closeout_20260926.py` reads the eight frozen final graphs and labels,
calls the existing parent division scorer, and checks every movie against the collected
validator CSV. It also calls the existing geometry predicate on the seven direct-edge
deficits. Machine-readable results and input SHA256s: `closeout_audit_2026-09-26.json`.

| Question | Result |
|---|---|
| GT divisions / fully matched triples | 12 / 9 |
| Exact mother-to-both-daughters events already present | 2 |
| Fully matched direct-edge deficits | 7 |
| Parent scorer TP / FP / FN | 3 / 2 / 9, reproduced for all eight movies |
| Existing Q1 candidate-edge reachability | 6/7; preserved Q1 result, generation not rerun |
| Existing Q1 generated events for those triples | 0/7; preserved Q1 result |

The discrepancy is `44b6_2a2eff9f`: its single division lacks the exact daughter
edges but is already a scorer TP. `parent_scorer.compute_division_confusion` credits
a component containing an anchor (mother or its parent), matched descendants of both
daughter lineages, and any fork. It does not require a fork at the matched mother.
Thus seven direct-edge deficits are NOT seven scorer FNs. This independently confirms
the earlier `step0_division_audit_reconciliation_2026-09-25.md` explanation.

## Isolated geometry controls

All controls below are predicate checks on unchanged cached coordinates, not new
candidate-generation runs or decoded graphs. Sister distance remains at 14 micrometres.

| Mother-daughter maximum | Symmetry tau | Geometry passes |
|---|---|---|
| 9 | 0.60 (base) | 0/7 |
| 9 | 0.75 | 0/7 |
| 9 | 0 (disabled) | 4/7 |
| 14 | 0.60 | 0/7 |
| 14 | 0 (disabled) | 7/7 |

Three triples also fail the original 9 micrometre distance limit. The seven asymmetry
values are above 0.75. Therefore the public sym075 arm does not test the relaxation
needed to admit them. Its recorded TP=3, FP=6, FN=9 and lower proxy establish a failed
specific mild relaxation, not the failure of all relaxed-geometry policies.
Geometry feasibility is not edge availability, generated-event availability, decoder
selection, or scorer improvement. The Q1 causes artifact and why script still use
node IDs in row-indexed hypothesis lookups; their candidate lists and truncation
classification are not reliable evidence. They are preserved, not silently repaired.
The corrected Q1 headroom script explicitly converts IDs to rows. Its stored result
is cited as historical evidence, not claimed to have been regenerated in this audit.

## Decision and limits

Stop exp067 for this competition because supervision is sparse and a defensible
export/train/decode/validate/deploy cycle is not justified before the chosen cutoff.
The frozen split has five complete training positives and four complete holdout
positives. This is not proof that the architecture cannot work or that dense labels
are the unique solution. Q2/Q3 are not run and decoder effectiveness is not certified.
The claim that one prior explains all historical 3/12 results is withdrawn.

Keep exp064 submission 56535761, recorded Public LB 0.953, as the retained candidate.
The user previously reported it selected; the live final-selection state was NOT
verified by this closeout. Verify it on the site before the cutoff/competition close.
cx03 is a registered null at reported precision, not proof of exactly zero true delta.
ep015 remains optional and OFF. Its ~0.955 extrapolation is neither an expectation nor
an upper bound; its worst per-prefix adjusted-edge regression is approximately 0.0085.
A higher Public LB would not by itself establish private-score superiority.

## Ledger reconciliation and provenance

The recorded 20-hour budget epoch less exp064/065/066/067c/067d gives
16.752764732567776 hours. Ledger balance is 16.752765177012222 hours: residual
0.000000444444446 hours (0.0016 seconds), consistent with mixed rounding precision.
Each of the five charges appears exactly once across the two existing ledger lists.
No reservation remains. Preserve the ledger balance and historical entries.
This is local accounting, not a fresh assertion about the remote GPU quota.

Submission history remains unchanged; local receipts identify exp064 at 0.953 and
cx03 at 0.953. No remote history check or new submission occurred. The ledger records
a September 24 user ruling raising the daily project cap to five, while the AGENTS
instructions supplied in this session state three. This conflict does not affect
closeout; any future submission must resolve it and check remote usage first.
No new submission authorization is inferred from either cap.

Previous PLAN v3 and Stage 0 v1 are preserved in explicitly superseded files.
All pre-edit governance and handoff bytes are also archived privately with SHA256s.
Current summaries supersede stale historical directives without altering receipts,
snapshots, experiment metrics or past review verdicts. No public push is authorized.
