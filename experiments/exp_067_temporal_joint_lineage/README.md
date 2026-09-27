# exp067: temporal joint lineage

## Status

Local implementation of the user-selected option 1. Parent: exp064 x138, user-reported Public LB 0.953. This is an untrained research candidate, not a promoted improvement. Claude Code authored the proposal and core implementation after the recorded critique and explicit CONSENSUS. Its implementation call stopped at a quota limit; Codex completed integration, corrections and independent local validation without retrying the model call.

No remote training, Kaggle launch, submission or GPU allocation has occurred for exp067. Remote execution still requires an experiment-specific snapshot, budget and fresh `scripts/request_codex_review.py` PASS. `development.json` is deliberately not a launchable controller configuration.

## Architecture

1. Replay the immutable exp064 predictor patches. Export measured frozen U-Net features, detector confidence and pre-threshold bidirectional candidate matrices. Capture actual graph IDs from `bulk_add_nodes`.
2. Run the parent's full graph processing, including smoothing. Keep these final nodes and coordinates. Original detection identity travels through a private metadata token; synthetic and readmitted points remain explicit and their incident parent edges remain fixed.
3. Build seven-frame windows. Allocate every scored hypothesis endpoint before optional context, splitting source groups as needed. Required endpoints that exceed the cap cause an explicit error.
4. Train a small Transformer with independent link BCE and a learned symmetric mother/two-daughter head. Sparse unmatched labels have zero gradient. Movie groups, normalization and fixed training schedule are recorded; held-out movies never select the checkpoint.
5. Jointly decode continuation and division variables with SciPy MILP. Both daughters may compete with already occupied targets. Constraints enforce single parent, at most two children and an explicit event for each fork. Constraint components separate by adjacent-frame transition rather than chaining a whole trajectory.
6. Validate each solution, record changed edges and divisions, and restore parent components on solver failure. More than 2% failed components restores the whole movie.

The implementation includes measured exports, training, checkpoint loading, inference, the verbatim exp064 metric, graph audits and a notebook builder. The division-recovery test establishes the decoder's ability to reclaim a daughter; it does not establish that the trained model will choose correctly on real movies.

## Files

- `architecture_brief_v1.md`: original implementation brief.
- `proposal_v1.md`, `codex_challenge_v1.md`, `revision_acceptance_v2.md`: versioned proposal, critique and consensus. Past-tense implementation claims in the acceptance document were unverified at that time; use the later local review for actual evidence.
- `scripts/exp067/`: model, export hooks, notebook bridge, training, inference, solver and evaluation.
- `scripts/build_exp067_notebook.py`: immutable-parent builder with reverse-patch checks and real predictor-patch replay.
- `configs/exp_067_temporal_joint_lineage.json`: fixed runtime configuration.
- `tests/test_exp067.py`: behavioral and CPU end-to-end tests.

## Reproduce local validation

Use a separate Python 3.12 environment and `requirements-exp067-cpu.txt`. In this workspace the interpreter is `.private/runtime/exp067_cpu/Scripts/python.exe`.

```powershell
python -m pytest tests/test_exp067.py -q --basetemp .private/runtime/exp067_new_test_run
python scripts/build_exp067_notebook.py --mode control --out experiments/exp_067_temporal_joint_lineage/local_build/control.ipynb
```

Choose a new temporary directory for each run. The generated notebook is an experiment artifact, not a milestone under `src/`.

## Real-data workflow (not executed)

Create `splits.json` with explicit TRAIN movie stems. Example structure only; replace placeholders with verified competition TRAIN names:

```json
{
  "protocol": "within_prefix_movie_holdout",
  "train": ["44b6_REPLACE_TRAIN", "6bba_REPLACE_TRAIN"],
  "holdout": ["44b6_REPLACE_HOLDOUT", "6bba_REPLACE_HOLDOUT"],
  "test_stems": ["REPLACE_WITH_ALL_COMPETITION_TEST_STEMS"]
}
```

All holdout prefixes must occur in training under `within_prefix_movie_holdout`, so it is a within-domain movie holdout and cannot establish cross-domain generalization; it is NOT a leave-one-movie-out cross-validation loop, which is why that older name was dropped (the old spelling still loads as a legacy alias). `leave_one_prefix_out` instead requires disjoint prefixes. No movie may occur in multiple groups. The export notebook additionally verifies selected stems against actual TEST stems and requires each selected TRAIN zarr/geff pair. Choose and freeze the split before scoring; do not use label outcomes to select movies.

```powershell
python scripts/build_exp067_notebook.py --mode export --splits splits.json --out export.ipynb
# Execute only after separate remote admission. Collect /kaggle/working/exp067_export.
python -m scripts.exp067.train --export-dir exp067_export --label-dir exp067_export/labels --splits splits.json --config configs/exp_067_temporal_joint_lineage.json --out lineage.pt --report training.json
python -m scripts.exp067.infer --export-dir exp067_export --stems HOLDOUT_STEMS_COMMA_SEPARATED --ckpt lineage.pt --config configs/exp_067_temporal_joint_lineage.json --out decoded
python -m scripts.exp067.evaluate --export-dir exp067_export --label-dir exp067_export/labels --stems HOLDOUT_STEMS_COMMA_SEPARATED --decoded-dir decoded --out comparison.json
python scripts/build_exp067_notebook.py --mode decode --checkpoint /kaggle/input/REPLACE_CHECKPOINT/lineage.pt --config configs/exp_067_temporal_joint_lineage.json --out decode.ipynb
```

Training requires at least 200 annotated positive links, three complete positive divisions, and negative examples for both heads. Insufficient labels stop training. Normalizers use training samples only. Input file hashes, split hash, backbone weights, patched predictor hash, feature schema and relevant code hashes bind the checkpoint. Changing generation/window/model/objective settings requires retraining. Inference does not load ground truth; evaluation is a separate command. The export notebook skips TEST inference and disables the parent sweep.

## Resource and decision bounds

Declared defaults: CPU head training 40 epochs, cooperative 1,800-second training deadline; movie decoding 600 seconds, each MILP component at most 2,000 variables and five seconds. Model dimensions and candidate bounds are fixed in config. Budget checks are cooperative: an individual feature-generation operation or native solver call cannot be interrupted mid-operation; a remote controller walltime cap is still required. Movie windows are currently materialized in memory, so representative export size and peak RAM must be measured before a full run.

Local CPU dependency versions are pinned. The parent Kaggle CUDA environment has not been executed with this integration; an offline compatible dependency bundle and a representative export/decode smoke run are prerequisites to remote admission. Do not replace the parent's CUDA PyTorch with CPU wheels. Frozen public-backbone training overlap is unknown (`POSSIBLE_OVERLAP_UNKNOWN_PROVENANCE`); report this limitation with local scores.

Stop on provenance mismatch, label leakage, altered final nodes/coordinates, invalid graph, missing required features, insufficient supervision or failed admission. Reject a candidate with worse aggregate adjusted edge Jaccard, either specimen losing more than 0.002, or no meaningful recovery of the prespecified missed-division/fragmentation cases. A local improvement is only a hypothesis for LB improvement; promotion requires separate evidence and authorization. Rollback is the untouched exp064 snapshot and disabled exp067 flags.
