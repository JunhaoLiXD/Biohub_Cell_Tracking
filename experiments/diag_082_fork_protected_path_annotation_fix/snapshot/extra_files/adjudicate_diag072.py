from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path


EXPECTED = {"44b6_12dfb391", "44b6_267148e4", "44b6_2a2eff9f", "44b6_341df25f",
            "6bba_062c8d37", "6bba_07e24132", "6bba_085bf656", "6bba_09961292"}


def aggregate(rows: list[dict]) -> dict:
    weight = sum(float(r["weight"]) for r in rows)
    adj = sum(float(r["adjusted_edge_jaccard"]) * float(r["weight"]) for r in rows) / weight
    tp = sum(int(r["div_tp"]) for r in rows)
    fp = sum(int(r["div_fp"]) for r in rows)
    fn = sum(int(r["div_fn"]) for r in rows)
    div = tp / (tp + fp + fn) if tp + fp + fn else 1.0
    return {"adjusted_edge_jaccard": adj, "div_tp": tp, "div_fp": fp, "div_fn": fn,
            "proxy": adj + 0.1 * div}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    doc = json.loads(args.receipt.read_text())
    contract = doc["runtime_contract"]
    assert contract == {"flat_floor": 0.0, "candidate_fork_floor": 0.15,
                        "evaluated_configs": ["base", "fork_protected_ep015"],
                        "preset_loaded": False, "selection_margin": 99.0,
                        "selected_label": "base"}
    assert doc["confirmatory_computed"] is False
    rows = doc["rows"]
    by_config = {name: {r["stem"]: r for r in rows if r["config"] == name}
                 for name in ("base", "fork_protected_ep015")}
    assert set(by_config["base"]) == EXPECTED and set(by_config["fork_protected_ep015"]) == EXPECTED
    base, cand = by_config["base"], by_config["fork_protected_ep015"]

    def sample_proxy(r: dict) -> float:
        den = int(r["div_tp"]) + int(r["div_fp"]) + int(r["div_fn"])
        return float(r["adjusted_edge_jaccard"]) + 0.1 * (int(r["div_tp"]) / den if den else 1.0)

    deltas = {s: sample_proxy(cand[s]) - sample_proxy(base[s]) for s in EXPECTED}
    groups = {p: sorted(s for s in EXPECTED if s.startswith(p)) for p in ("44b6", "6bba")}
    draw_deltas = []
    for left in itertools.combinations(groups["44b6"], 2):
        for right in itertools.combinations(groups["6bba"], 2):
            stems = set(left + right)
            draw_deltas.append(aggregate([cand[s] for s in stems])["proxy"] -
                               aggregate([base[s] for s in stems])["proxy"])
    loo = {drop: aggregate([cand[s] for s in EXPECTED if s != drop])["proxy"] -
                 aggregate([base[s] for s in EXPECTED if s != drop])["proxy"] for drop in EXPECTED}
    prefix_adj = {}
    for prefix, stems in groups.items():
        prefix_adj[prefix] = aggregate([cand[s] for s in stems])["adjusted_edge_jaccard"] - \
                             aggregate([base[s] for s in stems])["adjusted_edge_jaccard"]
    b_all, c_all = aggregate(list(base.values())), aggregate(list(cand.values()))
    intervention_void = {s: int(cand[s]["pred_node_count"]) == int(base[s]["pred_node_count"])
                            and int(cand[s]["pred_edge_count"]) == int(base[s]["pred_edge_count"])
                         for s in EXPECTED}
    underpred = [s for s in EXPECTED if float(base[s]["t_pred"]) < float(base[s]["t_true"])]
    gates = {
        "negative_draws_le_3": sum(x < 0 for x in draw_deltas) <= 3,
        "worst_movie_ge_minus_0_002": min(deltas.values()) >= -0.002,
        "nonvoid_ge_4": sum(not x for x in intervention_void.values()) >= 4,
        "underpredicted_cases_bypassed": all(intervention_void[s] for s in underpred),
        "prefix_adjusted_edge_floor": all(x >= -0.0005 for x in prefix_adj.values()),
        "division_tp_not_down": c_all["div_tp"] >= b_all["div_tp"],
        "division_fn_not_up": c_all["div_fn"] <= b_all["div_fn"],
        "every_prefilter_fork_preserved": all(int(cand[s]["fork_protection_complete"]) == 1 and
            int(cand[s]["fork_protected_edges_expected"]) == int(cand[s]["fork_protected_edges_retained"])
            for s in EXPECTED),
        "all_loo_ge_0_0015": all(x >= 0.0015 for x in loo.values()),
        "positive_without_44b6_prefix": aggregate([cand[s] for s in groups["6bba"]])["proxy"] >
                                            aggregate([base[s] for s in groups["6bba"]])["proxy"],
    }
    result = {"schema": "diag072-sealed-disposition-v1", "gates": gates,
              "diag072_primary_passed": all(gates.values()), "movie_deltas": deltas,
              "negative_draws": sum(x < 0 for x in draw_deltas), "worst_draw": min(draw_deltas),
              "leave_one_movie_out_deltas": loo, "prefix_adjusted_edge_deltas": prefix_adj,
              "underpredicted_stems": underpred, "intervention_void": intervention_void,
              "base": b_all, "candidate": c_all, "confirmatory_computed": False,
              "leaderboard_submission_authorized": False}
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
