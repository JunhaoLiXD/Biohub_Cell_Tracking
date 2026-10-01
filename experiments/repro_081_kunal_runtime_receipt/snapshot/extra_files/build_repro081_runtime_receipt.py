from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


UPSTREAM_SHA256 = "5c370da1bf31d28215e023c4e4208c0bb658943c6ea4840d0af996aac5305b30"
MARKER = "# repro081 receipt"


def marked(line: str) -> str:
    return f"{line}  {MARKER}\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    raw = args.source.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == UPSTREAM_SHA256
    notebook = json.loads(raw)
    cell = notebook["cells"][10]
    source = "".join(cell["source"])

    needle = "if selected_config:\n"
    insertion = "".join([
        marked("import hashlib as _r081_hashlib"),
        marked("REPRO081_RECEIPT_PATH = WORKING_DIR / 'repro081_runtime_receipt.json'"),
        marked("_r081_receipt = {"),
        marked("    'schema_version': 1,"),
        marked("    'validator_enabled_effective': bool(VALIDATOR_ENABLE),"),
        marked("    'held_out_stems': list(val_stems),"),
        marked("    'candidate_labels': sorted(PP_RESULTS),"),
        marked("    'selected': selected_label,"),
        marked("    'selected_overrides': dict(selected_config),"),
        marked("    'effective_globals_during_test_write': {},"),
        marked("    'selected_write_completed': False,"),
        marked("    'final_contract_validated': False,"),
        marked("}"),
    ])
    assert source.count(needle) == 1
    source = source.replace(needle, insertion + needle)

    needle = "    _saved = pp_apply(selected_config)\n"
    insertion = "".join([
        marked("    _r081_effective = {key: globals()[key] for key in selected_config}"),
        marked("    assert _r081_effective == selected_config, (_r081_effective, selected_config)"),
        marked("    _r081_receipt['effective_globals_during_test_write'] = dict(_r081_effective)"),
    ])
    assert source.count(needle) == 1
    source = source.replace(needle, needle + insertion)

    needle = "        write_test_submission(selected_label)\n"
    insertion = "".join([
        marked("        _r081_receipt['selected_write_completed'] = True"),
        marked("        _r081_receipt['submission_sha256_after_selected_write'] = _r081_hashlib.sha256(SUBMISSION_PATH.read_bytes()).hexdigest()"),
    ])
    assert source.count(needle) == 1
    source = source.replace(needle, needle + insertion)

    needle = "print(f\"Final submission.csv rows={len(_final)}  config={selected_label}\")"
    insertion = "".join([
        marked("_r081_receipt['final_contract_validated'] = True"),
        marked("_r081_receipt['final_submission_sha256'] = _r081_hashlib.sha256(SUBMISSION_PATH.read_bytes()).hexdigest()"),
        marked("if not selected_config:"),
        marked("    _r081_receipt['submission_sha256_after_selected_write'] = _r081_receipt['final_submission_sha256']"),
        marked("assert _r081_receipt['submission_sha256_after_selected_write'] == _r081_receipt['final_submission_sha256']"),
        marked("REPRO081_RECEIPT_PATH.write_text(json.dumps(_r081_receipt, indent=2, sort_keys=True) + '\\n')"),
    ])
    assert source.count(needle) == 1
    source = source.replace(needle, insertion + needle)
    cell["source"] = source.splitlines(keepends=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(notebook, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(hashlib.sha256(args.output.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
