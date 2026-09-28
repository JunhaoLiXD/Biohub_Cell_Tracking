# exp070 Tier B admission packet

Parent: `exp_068_ep015_single_probe`, whose visible kernel completed and whose
collected output passed the independent audit. Kaggle submission 56597763 later
completed with an empty public score.

Hypothesis: the exp068-only 5,400-second daemon calls `os._exit(124)` before the
inherited vehicle's declared 32,400-second hidden-rerun budget. The hidden input
is larger/different, while the visible four-movie run took 1,415.64 seconds.

Exact change:

- Replace the first-cell psutil/threading hard killer with a passive monotonic timer.
- Change the final runtime assertion from `< 5400` to
  `< float(os.environ['BIOHUB_WALL_BUDGET_S'])`; that environment value remains
  guarded at 32,400 seconds by the inherited notebook.
- Change only the emitted metrics experiment ID from exp068 to exp070.

No model, checkpoint, dependency, data discovery, inference, ep015 threshold,
graph processing, fallback, writer, CSV audit, or leaderboard policy changes.

Validation: `scripts/smoke_exp070.py` compares all code-cell sources against the
immutable exp068 snapshot. Exactly code cells 0 and 6 differ; reversing the three
declared edits yields exact source equality. Direct receipt: PASS. All notebook
code cells compile during deterministic build.

Artifacts:

- Config: `experiments/exp_070_ep015_hidden_rerun_repair/snapshot/config.yaml`
- Candidate: `experiments/exp_070_ep015_hidden_rerun_repair/snapshot/source/biohub-exp070-ep015-hidden-rerun-repair.ipynb`
- Builder and smoke are hashed in `snapshot/manifest.json`.

Budget and stop rule: estimated/reserved-at-launch ceiling 2 GPU hours. No launch,
submission, retry, promotion, or public push is authorized. Stop on any undeclared
source delta, failed review/smoke/snapshot/budget/output gate. Because Kaggle does
not expose the hidden traceback here, the timeout diagnosis is leading evidence,
not certainty; a separately authorized remote run would be the definitive test.
