"""Build exp070 using the reviewed prediction-neutral exp069 transformation."""
from __future__ import annotations

import build_exp069_ep015_hidden_rerun_repair as base


base.OUTPUT = base.ROOT / ".private/current/biohub-exp070-ep015-hidden-rerun-repair.ipynb"
base.NEW_EXPERIMENT_ID = "'experiment_id': 'exp_070_ep015_hidden_rerun_repair'"


if __name__ == "__main__":
    notebook = base.build()
    print(f"Wrote {base.OUTPUT} ({len(notebook['cells'])} cells)")
