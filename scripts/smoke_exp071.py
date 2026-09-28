"""Exact normalized-source smoke for exp071."""
from __future__ import annotations

import json

from build_exp071_ep015_hidden_rerun_repair import OUTPUT, PASSIVE_TIMER, REPLACEMENTS, SOURCE


def sources(path):
    nb = json.loads(path.read_text(encoding="utf-8"))
    return ["".join(c.get("source", [])) for c in nb["cells"] if c.get("cell_type") == "code"]


def main() -> None:
    parent, candidate = sources(SOURCE), sources(OUTPUT)
    changed = [i for i, pair in enumerate(zip(parent, candidate)) if pair[0] != pair[1]]
    assert len(parent) == len(candidate) and changed == [0, 1, 2, 6], changed
    assert candidate[0] == PASSIVE_TIMER
    assert "os._exit(124)" not in candidate[0] and "threading.Thread" not in candidate[0]
    normalized = list(candidate)
    normalized[0] = parent[0]
    for index in (1, 2, 6):
        for old, new in REPLACEMENTS.items():
            normalized[index] = normalized[index].replace(new, old)
    assert normalized == parent, "Unexpected source delta"
    joined = "\n".join(candidate)
    assert joined.count('BIOHUB_REPAIR_DEADLINE_S"] = "32400"') == 1
    assert joined.count('"BIOHUB_REPAIR_DEADLINE_S": 32400.0') == 1
    print("PASS: exp071 contains only the declared execution-contract and metadata deltas.")


if __name__ == "__main__":
    main()
