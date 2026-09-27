"""PLAN.md Step 0 -- reconcile division_recoverability_audit() against the official division scorer.

Zero GPU, zero network, zero submissions. Reads only artifacts already in this directory.

Why this exists: the audit printed
    TOTAL: reproduced_ok=2  recoverable_by_postprocess=7  missing_second_daughter=3  parent_unmatched=0
which would mean 7 of the 9 division false-negatives are reachable from post-processing. But the audit
says reproduced_ok=2 while the official scorer says div_tp=3 on the same base config, so the two
disagree by one event and the audit's counts cannot be used until that is localised.

The audit's suspect branch is `elif pred_children_count.get(pred_parent, 0) >= 2: reproduced_ok += 1`
-- it accepts a matched parent with two outgoing edges WITHOUT checking those edges reach the correct
daughters.

This script establishes, per stem, whether the audit's classification and the scorer's tp/fp/fn can
both be true, and isolates exactly where they cannot.
"""

from __future__ import annotations

import collections
import csv
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent

# The audit's per-stem output, transcribed from run_log_clean.txt. Stems it did not list had no
# non-reproduced GT division, so every division there fell into reproduced_ok.
AUDIT_LINE = re.compile(
    r"^\s*(?P<stem>\S+)\s+recoverable_by_postprocess=(?P<rec>\d+)\s+"
    r"missing_second_daughter=(?P<miss>\d+)\s+parent_unmatched=(?P<pu>\d+)\s*$")
AUDIT_TOTAL = re.compile(
    r"^\s*TOTAL:\s+reproduced_ok=(?P<ok>\d+)\s+recoverable_by_postprocess=(?P<rec>\d+)\s+"
    r"missing_second_daughter=(?P<miss>\d+)\s+parent_unmatched=(?P<pu>\d+)\s*$")


def parse_audit(log: pathlib.Path):
    per_stem: dict[str, dict[str, int]] = {}
    total: dict[str, int] = {}
    for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
        m = AUDIT_LINE.match(line)
        if m:
            per_stem[m.group("stem")] = {
                "recoverable": int(m.group("rec")),
                "missing": int(m.group("miss")),
                "parent_unmatched": int(m.group("pu")),
            }
            continue
        m = AUDIT_TOTAL.match(line)
        if m:
            total = {
                "reproduced_ok": int(m.group("ok")),
                "recoverable": int(m.group("rec")),
                "missing": int(m.group("miss")),
                "parent_unmatched": int(m.group("pu")),
            }
    return per_stem, total


def main() -> None:
    audit, audit_total = parse_audit(HERE / "run_log_clean.txt")
    if not audit_total:
        raise SystemExit("could not parse the audit TOTAL line from run_log_clean.txt")

    rows = [r for r in csv.DictReader((HERE / "validator_results.csv").open(encoding="utf-8"))
            if r["config"] == "base"]
    scorer = {r["stem"]: (int(r["div_tp"]), int(r["div_fp"]), int(r["div_fn"])) for r in rows}
    stems = sorted(scorer)

    print("Audit classification vs official division scorer, base config, per stem")
    print()
    head = (f"{'stem':20s} {'scorer tp/fp/fn':>15s} {'GT=tp+fn':>9s} | "
            f"{'audit rec':>9s} {'miss':>5s} {'p_unm':>6s} {'non-repro':>10s} "
            f"{'=> repro_ok':>12s}  consistent?")
    print(head)
    print("-" * len(head))

    derived_ok = 0
    conflicts = []
    for stem in stems:
        tp, fp, fn = scorer[stem]
        gt = tp + fn
        a = audit.get(stem, {"recoverable": 0, "missing": 0, "parent_unmatched": 0})
        non_repro = a["recoverable"] + a["missing"] + a["parent_unmatched"]
        repro_ok = gt - non_repro
        derived_ok += repro_ok
        # A division the scorer counted as a TP should not also be a division the audit says the
        # predicted parent failed to reproduce -- unless the two use different definitions.
        ok = repro_ok >= 0 and not (tp > 0 and non_repro >= gt)
        if not ok:
            conflicts.append(stem)
        print(f"{stem:20s} {f'{tp}/{fp}/{fn}':>15s} {gt:9d} | "
              f"{a['recoverable']:9d} {a['missing']:5d} {a['parent_unmatched']:6d} {non_repro:10d} "
              f"{repro_ok:12d}  {'yes' if ok else 'NO  <<<'}")

    print()
    print(f"derived reproduced_ok summed over stems : {derived_ok}")
    print(f"audit's own reported reproduced_ok      : {audit_total['reproduced_ok']}")
    print(f"scorer's total div_tp                   : {sum(v[0] for v in scorer.values())}")
    print(f"scorer's total div_fp / div_fn          : {sum(v[1] for v in scorer.values())}"
          f" / {sum(v[2] for v in scorer.values())}")
    print(f"audit recoverable / missing / p_unmatched: {audit_total['recoverable']}"
          f" / {audit_total['missing']} / {audit_total['parent_unmatched']}")
    print()

    print("WHERE THEY DISAGREE")
    if conflicts:
        for stem in conflicts:
            tp, fp, fn = scorer[stem]
            a = audit[stem]
            print(f"  {stem}: the scorer counts tp={tp} fn={fn}, i.e. its {tp + fn} GT division(s) WERE")
            print(f"    matched, but the audit classes {a['recoverable']} of them as "
                  f"'recoverable_by_postprocess',")
            print(f"    which by construction means the matched predicted parent did NOT emit two child")
            print(f"    edges. Both cannot be true under one definition of 'found a division'.")
            print(f"    Note this stem also carries div_fp={fp}.")
    else:
        print("  none -- the two are arithmetically reconcilable on every stem")
    print()

    # The audit's own accounting identity
    gt_total = sum(v[0] + v[2] for v in scorer.values())
    audit_sum = sum(audit_total[k] for k in
                    ("reproduced_ok", "recoverable", "missing", "parent_unmatched"))
    print(f"GT division events per the scorer (sum of tp+fn): {gt_total}")
    print(f"GT division events per the audit (sum of its 4 buckets): {audit_sum}")
    print(f"  -> {'AGREE on the denominator' if gt_total == audit_sum else 'DISAGREE on the denominator'}")
    print()

    print("WHAT THIS MEANS FOR PLAN.md STEP 2")
    fp_stems = [s for s in stems if scorer[s][1] > 0]
    tp_stems = [s for s in stems if scorer[s][0] > 0]
    print(f"  stems with a div_fp: {fp_stems}")
    print(f"  stems with a div_tp: {tp_stems}")
    if set(fp_stems) <= set(tp_stems) and fp_stems:
        print("  EVERY false positive sits on a stem that also has a true positive. That is the")
        print("  signature of a division being emitted at the WRONG node near the right place --")
        print("  one tp for the matched event plus one fp for the spurious fork -- rather than of")
        print("  independent spurious divisions. It also means 'remove the 2 FPs' and 'recover FNs'")
        print("  may not be independent levers.")


if __name__ == "__main__":
    main()
