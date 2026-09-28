"""Deterministic source-level smoke test for the exp069 transport repair."""
from __future__ import annotations

import json
from pathlib import Path

from build_exp069_ep015_hidden_rerun_repair import (
    NEW_EXPERIMENT_ID,
    NEW_RUNTIME_ASSERT,
    OLD_EXPERIMENT_ID,
    OLD_RUNTIME_ASSERT,
    OLD_WATCHDOG_MARKER,
    OUTPUT,
    PASSIVE_TIMER,
    SOURCE,
)


def code_sources(path: Path) -> list[str]:
    notebook = json.loads(path.read_text(encoding="utf-8"))
    return ["".join(cell.get("source", [])) for cell in notebook["cells"] if cell.get("cell_type") == "code"]


def main() -> None:
    parent = code_sources(SOURCE)
    candidate = code_sources(OUTPUT)
    assert len(parent) == len(candidate)

    changed = [index for index, (before, after) in enumerate(zip(parent, candidate)) if before != after]
    assert changed == [0, 6], changed
    assert candidate[0] == PASSIVE_TIMER
    assert OLD_WATCHDOG_MARKER not in "\n".join(candidate)
    assert "os._exit(124)" not in "\n".join(candidate)
    assert "threading.Thread" not in candidate[0]

    final_contract = candidate[6]
    assert OLD_RUNTIME_ASSERT not in final_contract
    assert final_contract.count(NEW_RUNTIME_ASSERT) == 1
    assert OLD_EXPERIMENT_ID not in final_contract
    assert final_contract.count(NEW_EXPERIMENT_ID) == 1

    normalized = list(candidate)
    normalized[0] = parent[0]
    normalized[6] = normalized[6].replace(NEW_RUNTIME_ASSERT, OLD_RUNTIME_ASSERT).replace(
        NEW_EXPERIMENT_ID, OLD_EXPERIMENT_ID
    )
    assert normalized == parent, "Unexpected scientific or notebook-source delta"
    print("PASS: only passive timer, 9 h runtime contract, and successor experiment id changed.")


if __name__ == "__main__":
    main()
