"""Builder for exp_058 A0 division diagnostic (Parts 2-3).

Takes the val_049 train16 notebook (which reproduces the exact 0.944-lineage
score 0.9310696298996892, division 3/8/9, and test submission SHA 0319ba6d...) and
adds ONLY:

  (1) purely-additive side-channel telemetry into `add_safe_divisions_postlink` and
      `deepcenter_accept_repair_point` (each injection appends to a separate global
      `_EXP058_LOG`; it cannot change control flow, `stats`, `nodes_by_id`, `edges`,
      `proposals`, or the returned graph), and
  (2) an appended analysis+integrity cell (GT mapping via the pinned
      `division_metrics`, the 12-GT coverage table, scorer-faithful fork relations,
      one-at-a-time suppression/addition rescoring, and the fail-closed
      `exp058_diagnostic_integrity_passed` gate incl. shadow parity).

SAFETY: the builder's PARITY GUARD strips every injected telemetry line and asserts
the result is byte-identical to the base notebook cell. Injections are anchored on
unique substrings; if an anchor is missing or ambiguous the build FAILS (never a
silent partial instrumentation). The runtime shadow-parity gate is the second, and
decisive, non-perturbation proof.

This module is import-safe (no side effects at import) so the validator can call it.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

# --- provenance (pinned) ---
BASE_NOTEBOOK = "experiments/val_049_public_0944_train16/snapshot/source/public_0944_train16.ipynb"
EXPECTED_SUBMISSION_SHA256 = "0319ba6d8e864335d3573f6b1a6227c546f17e9247a0c2858fa09b6c2422db3f"
EXPECTED_TRAIN16_SCORE = 0.9310696298996892
EXPECTED_DIVISION = (3, 8, 9)  # tp, fp, fn

# A telemetry-injected line is tagged with this marker so the parity guard can strip
# it deterministically. Every injected line ends with it.
TAG = "  # __EXP058_TELEMETRY__"


# ---------------------------------------------------------------------------
# Anchored, purely-additive injections into the base cell source.
# Each entry: (anchor_substring, injected_lines_without_tag).
# The injected block is placed IMMEDIATELY BEFORE the anchor line, at the anchor's
# indentation, and every injected physical line is suffixed with TAG.
# Anchors are chosen to be UNIQUE in the cell (asserted at build time).
# ---------------------------------------------------------------------------

# NOTE on faithfulness: the per-candidate record is emitted at each decision exit of
# the candidate loop in add_safe_divisions_postlink, recording the first rejecting
# stage under the REAL short-circuit order. deepcenter score is captured in the veto
# helper and joined by (dataset, t, rounded point). All exact anchors + telemetry
# code live in the companion module scripts/exp058_instrumentation.py.


def _load_cell_source(nb: dict) -> tuple[int, str]:
    """Return (index, source_str) of the single large code cell holding the funcs."""
    target = None
    for i, cell in enumerate(nb["cells"]):
        if cell.get("cell_type") != "code":
            continue
        src = "".join(cell.get("source", []))
        if "def add_safe_divisions_postlink" in src and "def deepcenter_accept_repair_point" in src:
            if target is not None:
                raise SystemExit("ambiguous: >1 cell defines the safe_division functions")
            target = (i, src)
    if target is None:
        raise SystemExit("could not find the cell defining add_safe_divisions_postlink")
    return target


def _unique_replace(src: str, anchor: str, replacement: str) -> str:
    n = src.count(anchor)
    if n != 1:
        raise SystemExit(f"anchor not unique (count={n}): {anchor[:80]!r}")
    return src.replace(anchor, replacement, 1)


def _strip_tag_lines(src: str) -> str:
    return "\n".join(l for l in src.split("\n") if TAG not in l)


def build(base_notebook: Path, out_notebook: Path) -> dict:
    nb = json.loads(base_notebook.read_text(encoding="utf-8"))
    cell_idx, base_src = _load_cell_source(nb)

    # The concrete anchors, telemetry code and analysis cell live in a companion
    # module so the (long) exact strings are reviewable/testable in isolation.
    from exp058_instrumentation import replacements, cell5_replacements, ANALYSIS_INTEGRITY_CELL

    def _apply(source: str, pairs, label: str) -> tuple[str, int]:
        s = source
        n = 0
        for anchor, replacement in pairs:
            if _strip_tag_lines(replacement) != anchor:
                raise SystemExit(
                    f"[{label}] replacement is not purely additive for anchor "
                    f"{anchor[:60]!r}: stripping tagged lines does not reproduce the anchor."
                )
            k = sum(1 for l in replacement.split("\n") if TAG in l)
            if k == 0:
                raise SystemExit(f"[{label}] replacement adds no tagged telemetry for anchor {anchor[:60]!r}")
            s = _unique_replace(s, anchor, replacement)
            n += k
        if _strip_tag_lines(s) != source:
            raise SystemExit(
                f"[{label}] PARITY GUARD FAILED: stripping telemetry did not reproduce "
                "the base cell byte-for-byte. Instrumentation is NOT purely additive; aborting."
            )
        return s, n

    # functions cell (cell 2)
    src, injected = _apply(base_src, replacements(), "functions_cell")
    nb["cells"][cell_idx]["source"] = _as_source_lines(src)

    # validator-loop cell (the cell that stashes per-stem graphs): locate it by content
    stash_pairs = cell5_replacements()
    stash_anchor = stash_pairs[0][0]
    stash_idx = None
    for i, cell in enumerate(nb["cells"]):
        if cell.get("cell_type") != "code":
            continue
        if stash_anchor in "".join(cell.get("source", [])):
            if stash_idx is not None:
                raise SystemExit("ambiguous: >1 cell matches the stash anchor")
            stash_idx = i
    if stash_idx is None:
        raise SystemExit("could not find the validator-loop cell for the graph stash")
    stash_src = "".join(nb["cells"][stash_idx]["source"])
    stash_out, stash_n = _apply(stash_src, stash_pairs, "validator_cell")
    nb["cells"][stash_idx]["source"] = _as_source_lines(stash_out)
    injected += stash_n

    # append the analysis + integrity cell as a NEW cell at the end (separate cell;
    # not part of the guarded functions cell)
    nb["cells"].append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": _as_source_lines(ANALYSIS_INTEGRITY_CELL),
    })

    out_notebook.parent.mkdir(parents=True, exist_ok=True)
    out_notebook.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    return {
        "base_notebook": str(base_notebook),
        "out_notebook": str(out_notebook),
        "cell_index": cell_idx,
        "telemetry_lines_injected": injected,
        "parity_guard": "PASSED",
        "expected_submission_sha256": EXPECTED_SUBMISSION_SHA256,
        "expected_train16_score": EXPECTED_TRAIN16_SCORE,
        "expected_division": EXPECTED_DIVISION,
    }


def _as_source_lines(src: str) -> list[str]:
    """Notebook 'source' is a list of lines each ending in newline (except last)."""
    lines = src.split("\n")
    return [ln + "\n" for ln in lines[:-1]] + [lines[-1]]


def main() -> int:
    ap = argparse.ArgumentParser(description="Build the exp_058 A0 division diagnostic notebook")
    ap.add_argument("--base", default=BASE_NOTEBOOK)
    ap.add_argument("--out", default=".private/current/exp058_a0_division_diagnostic.ipynb")
    args = ap.parse_args()
    result = build(Path(args.base), Path(args.out))
    print(json.dumps(result, indent=2, default=list))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
