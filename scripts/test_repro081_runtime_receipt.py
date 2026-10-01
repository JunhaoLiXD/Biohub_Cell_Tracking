from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from audit_repro081_runtime_receipt import audit


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("public_artifacts", type=Path)
    parser.add_argument("source_notebook", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        for name in ("ppsweep_selected.json", "ppsweep_results.csv", "submission.csv"):
            shutil.copy2(args.public_artifacts / name, root / name)
        selected = json.loads((root / "ppsweep_selected.json").read_text(encoding="utf-8"))
        with (root / "ppsweep_results.csv").open(encoding="utf-8-sig") as handle:
            import csv
            labels = sorted(row["config"] for row in csv.DictReader(handle))
        digest = hashlib.sha256((root / "submission.csv").read_bytes()).hexdigest()
        valid = {
            "schema_version": 1,
            "validator_enabled_effective": True,
            "held_out_stems": selected["held_out_stems"],
            "candidate_labels": labels,
            "selected": selected["selected"],
            "selected_overrides": selected["overrides"],
            "effective_globals_during_test_write": selected["overrides"],
            "selected_write_completed": bool(selected["overrides"]),
            "final_contract_validated": True,
            "submission_sha256_after_selected_write": digest,
            "final_submission_sha256": digest,
        }
        receipt = root / "repro081_runtime_receipt.json"
        receipt.write_text(json.dumps(valid), encoding="utf-8")
        assert audit(root, args.source_notebook)["status"] == "PASS"
        for key, bad in (
            ("validator_enabled_effective", False),
            ("effective_globals_during_test_write", {}),
            ("final_submission_sha256", "0" * 64),
        ):
            mutated = dict(valid)
            mutated[key] = bad
            receipt.write_text(json.dumps(mutated), encoding="utf-8")
            assert audit(root, args.source_notebook)["status"] == "FAIL", key
    print("PASS: valid receipt accepted; disabled validator, missing effective override, and bad artifact hash rejected")


if __name__ == "__main__":
    main()
