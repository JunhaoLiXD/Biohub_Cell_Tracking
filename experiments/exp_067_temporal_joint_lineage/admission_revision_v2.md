# Admission revision v2

The user explicitly instructed direct Kaggle execution, then resumed after the CLI quota reset. The independent review of exp067a returned REVISE, not NO_CONSENSUS. Its immutable snapshot and review remain intact. New execution record: exp067b_temporal_feature_export_v2.

Corrections to that review:

1. `evaluation.mode: gate`, explicit Boolean `gate_passed` only after all final checks, controller-compatible metrics schema.
2. `reconcile` now requires both source and target embeddings as the accepted consensus specified. No strategy amendment was made. Single-role boundary nodes retain fixed parent edges.
3. The hypothesis explicitly says bounded top-k alternatives ranked by logits, with no completeness claim.
4. A pre-inference gate compares runtime primary/secondary/DeepCenter checkpoint hashes and the support-repository manifest against the observed exp064 receipt. It checks every explicit cell0 environment assignment, with the declared validator-enable exception. The V1284 head was downloaded from the same public dataset before launch and pinned to SHA256 625a0d9340f48193f2ec294fc2d81c5bb3c03087eab78ef0ae998a9c4c7da00c. The historical exp064 receipt did not record this head's hash; byte equality to that historical head is therefore unknown, not asserted.
5. Representative parent parity is an acceptance gate inside this bounded first run, not a claimed pre-existing result. Reuse cached raw predictions for one movie per prefix; disable export hooks and rerun unchanged parent postprocessing; require identical node IDs, times, coordinates and edge sets against the exported final graph. No extra detector inference is run. The unchanged predictor statements were already verified by reverse-patch reconstruction and real parent patch replay; a separate full uninstrumented detector run is outside this first attempt. Actual export compatibility and representative postprocessing parity are precisely what this remote trial measures.
6. Final metrics explicitly carry the unknown-backbone-overlap warning, observed/expected dependency identity, resolved BIOHUB/V1284 environment, primitive postprocessing globals, and parity evidence.

The first run remains export-only, eight fixed TRAIN movies, no held-out tuning, no TEST inference or LB submission. Dependencies stay in the parent's pinned CUDA image; the separate CPU training requirements are not installed there. Two GPU hours reserved; 5400-second in-notebook watchdog kills descendants and exits. No automatic retry after failure. This v2 fulfills the original CONSENSUS requirements and responds to specific admission defects; it does not change the approved architecture.
