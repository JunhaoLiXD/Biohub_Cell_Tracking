"""Deterministic source-delta smoke for exp070."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT / "experiments/exp_068_ep015_single_probe/snapshot/source/biohub-exp068-ep015.ipynb"
CANDIDATE = ROOT / ".private/current/biohub-exp070-ep015-hidden-rerun-repair.ipynb"
OLD_ID = "'experiment_id': 'exp_068_ep015_single_probe'"
NEW_ID = "'experiment_id': 'exp_070_ep015_hidden_rerun_repair'"
OLD_ASSERT = "assert 0 < runtime < 5400"
NEW_ASSERT = "assert 0 < runtime < float(os.environ['BIOHUB_WALL_BUDGET_S'])"


def sources(path: Path) -> list[str]:
    nb = json.loads(path.read_text(encoding="utf-8"))
    return ["".join(c.get("source", [])) for c in nb["cells"] if c.get("cell_type") == "code"]


def main() -> None:
    parent, candidate = sources(PARENT), sources(CANDIDATE)
    changed = [i for i, pair in enumerate(zip(parent, candidate)) if pair[0] != pair[1]]
    assert len(parent) == len(candidate) and changed == [0, 6], changed
    assert "os._exit(124)" not in candidate[0] and "threading.Thread" not in candidate[0]
    normalized = list(candidate)
    normalized[0] = parent[0]
    normalized[6] = normalized[6].replace(NEW_ASSERT, OLD_ASSERT).replace(NEW_ID, OLD_ID)
    assert normalized == parent
    print("PASS: exp070 changes only the passive timer, 9 h bound, and experiment id.")


if __name__ == "__main__":
    main()
