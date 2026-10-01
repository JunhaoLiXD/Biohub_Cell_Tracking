from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


EXPECTED_SOURCE_SHA256 = "1028ff66dcf2539dc90a4c6cfe6e28048ff28e9f8e73fd96752bb1d5170e7572"


def audit(artifacts: Path, source: Path) -> dict[str, object]:
    errors: list[str] = []
    try:
        if hashlib.sha256(source.read_bytes()).hexdigest() != EXPECTED_SOURCE_SHA256:
            errors.append("source hash mismatch")
        selected = json.loads((artifacts / "ppsweep_selected.json").read_text(encoding="utf-8"))
        receipt = json.loads((artifacts / "repro081_runtime_receipt.json").read_text(encoding="utf-8"))
        with (artifacts / "ppsweep_results.csv").open(newline="", encoding="utf-8-sig") as handle:
            sweep_labels = {row["config"] for row in csv.DictReader(handle)}
        submission_hash = hashlib.sha256((artifacts / "submission.csv").read_bytes()).hexdigest()
        if receipt.get("validator_enabled_effective") is not True:
            errors.append("validator was not enabled effectively")
        if receipt.get("held_out_stems") != selected.get("held_out_stems"):
            errors.append("receipt held-out stems mismatch")
        if set(receipt.get("candidate_labels", [])) != sweep_labels:
            errors.append("receipt candidate labels mismatch")
        if receipt.get("selected") != selected.get("selected"):
            errors.append("receipt selected label mismatch")
        if receipt.get("selected_overrides") != selected.get("overrides"):
            errors.append("receipt selected overrides mismatch")
        if receipt.get("effective_globals_during_test_write") != selected.get("overrides"):
            errors.append("effective globals do not equal selected overrides")
        expected_selected_write = bool(selected.get("overrides"))
        if receipt.get("selected_write_completed") is not expected_selected_write:
            errors.append("selected-write completion mismatch")
        if receipt.get("final_contract_validated") is not True:
            errors.append("final notebook contract was not validated")
        if receipt.get("submission_sha256_after_selected_write") != submission_hash:
            errors.append("selected-write submission hash mismatch")
        if receipt.get("final_submission_sha256") != submission_hash:
            errors.append("final submission hash mismatch")
    except (FileNotFoundError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"receipt audit exception: {type(exc).__name__}: {exc}")
    return {
        "status": "PASS" if not errors else "FAIL",
        "runtime_receipt_integrity_passed": not errors,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifacts", type=Path)
    parser.add_argument("source_notebook", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.artifacts, args.source_notebook)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["runtime_receipt_integrity_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
