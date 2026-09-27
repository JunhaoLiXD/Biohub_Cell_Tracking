"""Reproduce every number exp_065's proposal quotes from the harvested sweep table.

Zero GPU, zero network, no Kaggle credentials. Reads only the two CSVs in this directory,
which are byte-verified by ../SHA256SUMS_amanatar_v9.txt.

    python analyze_sweep_table.py

Source of the inputs: `kaggle kernels output amanatar/optimized-biohub-max-score`, a run with
BIOHUB_VALIDATOR_ENABLE=1 on a configuration identical to x138 in all 89 BIOHUB_* keys.

v2, 2026-09-25, after the Codex challenge of proposal v1 (which this script's v1 failed):

  * The prefix guard is now the notebook's actual computation -- cell 9 lines 121-134: each
    prefix's adjusted-edge mean uses THE CANDIDATE'S OWN weights, and the division term is a
    single Jaccard over POOLED div tp/fp/fn. v1 used base weights and averaged per-movie
    division Jaccards; both were wrong. The reimplementation is now VALIDATED against the
    `prefix_proxy` column the notebook itself wrote into ppsweep_results.csv.
  * Added the 36 two-per-prefix subsets, which match the hidden test set's actual shape (two
    44b6 movies + two 6bba movies) and hold the prefix mixture fixed instead of renormalising
    globally the way a leave-one-out does. Codex's [DESIGN] finding 1.

What this establishes, all load-bearing for the proposal:

 1. `proxy_score` is exactly `adjusted_edge_jaccard + 0.1 * division_jaccard`.
 2. The reimplemented prefix guard matches the notebook's own output exactly.
 3. `ep015`, the largest measured gain, is NOT robust: 60.6% of its gross positive contribution
    comes from one held-out movie, it loses 0.0085 on the 44b6 prefix (so the author's own guard
    rejects it), and 10 of the 36 test-shaped subsets are negative.
 4. On this table no candidate passes Gate 2 of the proposal.

The hidden test set is 44b6_0113de3b, 44b6_0b24845f, 6bba_05b6850b, 6bba_05db0fb1 -- two movies
per embryo prefix, 45,250 / 75,969 nodes (from exp_064's collection/metrics.json), so the
"test-reweighted" figures rescale the two prefixes to 37.329% / 62.671%. NOTE this is a modelling
assumption, not a recovered official weighting: its inputs are OUR predicted output-node counts,
whereas the validator's own weights are edge-confusion denominators. Codex's [DESIGN] finding 2.
"""

from __future__ import annotations

import ast
import collections
import csv
import itertools
import pathlib
import statistics

HERE = pathlib.Path(__file__).resolve().parent

TEST_NODES = {"44b6": 45250, "6bba": 75969}
TEST_SHARE = {k: v / sum(TEST_NODES.values()) for k, v in TEST_NODES.items()}

DIVISION_WEIGHT = 0.1

# Gate 2 of docs/research/exp065_metric_aligned_pruning_proposal.md (v2), fixed before Run 1 exists.
GATE2_MIN_DELTA = 0.0015
GATE2_MAX_NEGATIVE_SUBSETS = 3          # of 36
GATE2_MARGINAL_NEGATIVE_SUBSETS = 9     # 4..9 negative -> marginal, escalate; >9 -> reject
GATE2_PREFIX_MAX_REGRESSION = 0.001

# The archived table reproduces to exactly 0.0. A tolerance rather than == 0.0 only because another
# platform's float summation order could differ in the last bit; anything above this is a real
# disagreement and raises. Codex round-2 blocking finding 4: this gate must FAIL CLOSED, not print.
TOLERANCE = 1e-12

# Set False by load() when the eligible family was not fully measured.
SELECTION_ALLOWED = True

# Gate 2 selects only from the pruning family (Codex [SCOPE] finding 5). The run measures
# everything; eligibility is narrower than measurement on purpose.
PRUNING_FAMILY = {
    "ep010", "ep015", "ep020",
    "seg030L3", "seg035L4", "seg040L6",
    "leaf030", "leaf040",
    "cx03", "cx06", "cx10",
    "leaf_seg", "prune_pack", "ep_cx", "seg_cx",
}


def prefix_of(stem: str) -> str:
    return stem.split("_", 1)[0]


def jaccard(tp: int, fp: int, fn: int) -> float:
    denom = tp + fp + fn
    return tp / denom if denom else 0.0


def load():
    rows = list(csv.DictReader((HERE / "validator_results.csv").open(encoding="utf-8")))
    by_config: dict[str, dict[str, dict]] = collections.defaultdict(dict)
    for row in rows:
        by_config[row["config"]][row["stem"]] = row
    stems = sorted(by_config["base"])
    for config, per_stem in by_config.items():
        if sorted(per_stem) != stems:
            raise SystemExit(f"config {config!r} does not cover all {len(stems)} stems")

    # Codex round-2 blocking finding 4: covering the base stem set is not completeness. The subset
    # analysis needs exactly four movies per prefix, and selection needs the eligible family to have
    # actually been measured -- a deadline-truncated sweep must not reach selection silently.
    counts = collections.Counter(prefix_of(s) for s in stems)
    if sorted(counts) != ["44b6", "6bba"] or set(counts.values()) != {4}:
        raise SystemExit(
            f"FAIL-CLOSED: expected 4 stems per prefix for the 36 test-shaped subsets, got {dict(counts)}.")
    missing = sorted(PRUNING_FAMILY - set(by_config))
    if missing:
        print(f"[0] INCOMPLETE MEASUREMENT: {len(missing)} of {len(PRUNING_FAMILY)} eligible pruning "
              f"candidates are absent from this table: {missing}")
        print("    Selection is REFUSED. Re-run the sweep, or record explicitly which candidates the")
        print("    deadline truncated and treat the missing ones as unmeasured, not as rejected.\n")
        global SELECTION_ALLOWED
        SELECTION_ALLOWED = False
    return by_config, stems


def check_proxy_formula() -> None:
    worst, n = 0.0, 0
    for row in csv.DictReader((HERE / "ppsweep_results.csv").open(encoding="utf-8")):
        predicted = float(row["adjusted_edge_jaccard"]) + DIVISION_WEIGHT * float(row["division_jaccard"])
        worst = max(worst, abs(predicted - float(row["proxy_score"])))
        n += 1
    print(f"[1] proxy == adjusted_edge_jaccard + {DIVISION_WEIGHT} * division_jaccard")
    print(f"    {n} rows, max residual {worst:.3e}")
    if worst > TOLERANCE:
        raise SystemExit(
            f"FAIL-CLOSED: the proxy identity does not hold (residual {worst:.3e}). This table is "
            "not the metric Gate 2 was calibrated on; do not select from it.")
    print("    CONFIRMED\n")


def prefix_proxy(by_config, stems, config: str) -> dict[str, float]:
    """Notebook cell 9 lines 121-134, exactly: candidate's own weights, pooled division counts."""
    out: dict[str, float] = {}
    groups: dict[str, list[dict]] = collections.defaultdict(list)
    for stem in stems:
        groups[prefix_of(stem)].append(by_config[config][stem])
    for prefix, prows in groups.items():
        weight = sum(float(r["weight"]) for r in prows) or 1.0
        adj = sum(float(r["adjusted_edge_jaccard"]) * float(r["weight"]) for r in prows) / weight
        out[prefix] = adj + DIVISION_WEIGHT * jaccard(
            sum(int(r["div_tp"]) for r in prows),
            sum(int(r["div_fp"]) for r in prows),
            sum(int(r["div_fn"]) for r in prows),
        )
    return out


def validate_prefix_guard(by_config, stems) -> None:
    worst = 0.0
    for row in csv.DictReader((HERE / "ppsweep_results.csv").open(encoding="utf-8")):
        published = ast.literal_eval(row["prefix_proxy"])
        mine = prefix_proxy(by_config, stems, row["config"])
        for key, value in published.items():
            worst = max(worst, abs(value - mine[key]))
    print("[2] reimplemented prefix guard vs the notebook's own prefix_proxy column")
    print(f"    max residual {worst:.3e}")
    if worst > TOLERANCE:
        raise SystemExit(
            f"FAIL-CLOSED: the reimplemented prefix guard does not reproduce the notebook's own "
            f"prefix_proxy column (residual {worst:.3e}). Gate 2 condition (3) cannot be judged.")
    print("    MATCH\n")


def reweighted_delta(by_config, config: str, groups: dict[str, list[str]]) -> float:
    """Weighted adjusted_edge_jaccard delta vs base, prefix mixture held at the test shares.

    `groups` names which stems represent each prefix, so a subset analysis changes WHICH movies
    stand in for a prefix without changing the prefix mixture.
    """
    total = 0.0
    for prefix, members in groups.items():
        weight = sum(float(by_config["base"][s]["weight"]) for s in members)
        inner = sum(
            float(by_config["base"][s]["weight"]) / weight
            * (float(by_config[config][s]["adjusted_edge_jaccard"])
               - float(by_config["base"][s]["adjusted_edge_jaccard"]))
            for s in members
        )
        total += TEST_SHARE[prefix] * inner
    return total


def all_stems_groups(stems) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = collections.defaultdict(list)
    for stem in stems:
        groups[prefix_of(stem)].append(stem)
    return dict(groups)


def test_shaped_subsets(stems):
    """The 36 subsets that match the hidden test set: two 44b6 movies and two 6bba movies."""
    a = [s for s in stems if prefix_of(s) == "44b6"]
    b = [s for s in stems if prefix_of(s) == "6bba"]
    for pair_a in itertools.combinations(a, 2):
        for pair_b in itertools.combinations(b, 2):
            yield {"44b6": list(pair_a), "6bba": list(pair_b)}


def main() -> None:
    by_config, stems = load()
    check_proxy_formula()
    validate_prefix_guard(by_config, stems)

    full = all_stems_groups(stems)
    subsets = list(test_shaped_subsets(stems))
    base_pp = prefix_proxy(by_config, stems, "base")

    print(f"[3] Gate 2, thresholds fixed in the proposal before Run 1 exists")
    print(f"    (1) test-reweighted aggregate delta >= {GATE2_MIN_DELTA:+.4f}")
    print(f"    (2) at most {GATE2_MAX_NEGATIVE_SUBSETS} of {len(subsets)} test-shaped subsets negative"
          f" ({GATE2_MAX_NEGATIVE_SUBSETS + 1}-{GATE2_MARGINAL_NEGATIVE_SUBSETS} = marginal, escalate)")
    print(f"    (3) no embryo prefix regressing by more than {GATE2_PREFIX_MAX_REGRESSION}")
    print(f"    eligible for selection: the {len(PRUNING_FAMILY)}-member pruning family only\n")

    header = (f"{'config':32s} {'aggregate':>10s} {'neg':>4s} {'=0':>4s} {'worst sub':>10s} "
              f"{'prefix reg':>11s} {'elig':>5s}  gate")
    print(header)
    print("-" * len(header))

    results = []
    for config in by_config:
        if config == "base":
            continue
        aggregate = reweighted_delta(by_config, config, full)
        sub = [reweighted_delta(by_config, config, g) for g in subsets]
        # Gate 2 condition (2) says NEGATIVE. A subset that is exactly unchanged is not a loss;
        # counting ties as losses made v2 report dcsd015 as 18/36 (it is 9 negative + 9 zero) and
        # tight55 as 36/36 (it is 0 negative + 36 zero). Codex round-2 blocking finding 1.
        negative = sum(1 for v in sub if v < 0)
        unchanged = sum(1 for v in sub if v == 0)
        pp = prefix_proxy(by_config, stems, config)
        regression = min(pp[k] - base_pp[k] for k in base_pp)
        eligible = config in PRUNING_FAMILY

        fails = []
        if aggregate < GATE2_MIN_DELTA:
            fails.append("1")
        if negative > GATE2_MARGINAL_NEGATIVE_SUBSETS:
            fails.append("2")
        if regression < -GATE2_PREFIX_MAX_REGRESSION:
            fails.append("3")
        if not eligible:
            verdict = "not eligible"
        elif fails:
            verdict = "fails " + "+".join(fails)
        elif negative > GATE2_MAX_NEGATIVE_SUBSETS:
            verdict = "MARGINAL -> escalate"
        else:
            verdict = "PASS"
        results.append((aggregate, config, negative, unchanged, min(sub), regression, eligible, verdict))

    for aggregate, config, negative, unchanged, worst_sub, regression, eligible, verdict in sorted(
            results, key=lambda r: -r[0]):
        print(f"{config:32s} {aggregate:+10.5f} {negative:4d} {unchanged:4d} {worst_sub:+10.5f} "
              f"{regression:+11.7f} {'yes' if eligible else 'no':>5s}  {verdict}")

    passes = [r for r in results if r[7] == "PASS"]
    marginal = [r for r in results if r[7].startswith("MARGINAL")]
    print()
    if not SELECTION_ALLOWED:
        print("Selection REFUSED: the eligible pruning family was not fully measured (see [0]).")
        print("Any row below is reportable evidence, but Gate 2 does not select from a partial table.")
    elif passes:
        print(f"Gate 2 selects: {max(passes)[1]}")
    elif marginal:
        print(f"Gate 2 selects nothing automatically; MARGINAL: {[r[1] for r in marginal]} -> escalate")
    else:
        print("Gate 2 selects NOTHING on this table -> H_null, no submission.")
        print("That is the proposal's stated position on current evidence. Run 1 scores the 29")
        print("declared candidates the fast tier skipped, including all three cx* arms.")

    print("\n[4] Why ep015 is not robust, three independent ways:")
    contribution = {
        s: float(by_config["ep015"][s]["adjusted_edge_jaccard"])
           - float(by_config["base"][s]["adjusted_edge_jaccard"])
        for s in stems
    }
    weighted = {}
    for prefix, members in full.items():
        weight = sum(float(by_config["base"][s]["weight"]) for s in members)
        for stem in members:
            weighted[stem] = (TEST_SHARE[prefix]
                              * float(by_config["base"][stem]["weight"]) / weight
                              * contribution[stem])
    gross_positive = sum(v for v in weighted.values() if v > 0)
    top = max(weighted, key=weighted.get)
    sub = [reweighted_delta(by_config, "ep015", g) for g in subsets]
    print(f"    concentration: {top} holds {weighted[top] / gross_positive:.1%} of the gross positive")
    print(f"    prefix guard:  44b6 regresses {prefix_proxy(by_config, stems, 'ep015')['44b6'] - base_pp['44b6']:+.7f}"
          f" (author's own limit {-GATE2_PREFIX_MAX_REGRESSION})")
    print(f"    test-shaped:   {sum(1 for v in sub if v < 0)} of {len(sub)} subsets negative, "
          f"min {min(sub):+.5f}, median {statistics.median(sub):+.9f}, max {max(sub):+.5f}")


if __name__ == "__main__":
    main()
