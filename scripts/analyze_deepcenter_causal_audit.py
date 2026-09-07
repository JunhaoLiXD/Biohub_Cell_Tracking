"""Analyze causal DeepCenter scores for retained validation division edges."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


QUANTILES = (0.0, 0.25, 0.5, 0.75, 1.0)


def linear_quantile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def summarize(values: list[float]) -> dict[str, float | int | None]:
    return {
        "count": len(values),
        **{f"q{int(q * 100):02d}": linear_quantile(values, q) for q in QUANTILES},
    }


def pairwise_auc(positive: list[float], negative: list[float]) -> float | None:
    """Return P(positive score > negative score), with ties worth one half."""
    if not positive or not negative:
        return None
    wins = 0.0
    for pos_score in positive:
        for neg_score in negative:
            if pos_score > neg_score:
                wins += 1.0
            elif pos_score == neg_score:
                wins += 0.5
    return wins / (len(positive) * len(negative))


def threshold_sweep(positive: list[float], negative: list[float]) -> list[dict[str, float | int]]:
    thresholds = sorted(set(positive + negative), reverse=True)
    if thresholds:
        span = max(thresholds) - min(thresholds)
        margin = max(span * 1e-12, 1e-15)
        thresholds = [max(thresholds) + margin, *thresholds, min(thresholds) - margin]
    rows = []
    for threshold in thresholds:
        tp = sum(score >= threshold for score in positive)
        fp = sum(score >= threshold for score in negative)
        tpr = tp / len(positive) if positive else 0.0
        fpr = fp / len(negative) if negative else 0.0
        rows.append(
            {
                "threshold": threshold,
                "causal_tp_kept": tp,
                "causal_fp_kept": fp,
                "tpr": tpr,
                "fpr": fpr,
                "youden_j": tpr - fpr,
            }
        )
    return rows


def feature_auc(
    records: list[dict[str, object]], feature: str
) -> dict[str, float | int | str | None]:
    positive = [
        float(record[feature])
        for record in records
        if int(record.get("causal_delta_tp", 0)) > 0
        and int(record.get("causal_delta_fp", 0)) <= 0
        and record.get(feature) is not None
    ]
    negative = [
        float(record[feature])
        for record in records
        if int(record.get("causal_delta_fp", 0)) > 0
        and int(record.get("causal_delta_tp", 0)) <= 0
        and record.get(feature) is not None
    ]
    auc_high = pairwise_auc(positive, negative)
    if auc_high is None:
        return {"positive_count": len(positive), "negative_count": len(negative), "auc": None}
    if auc_high >= 0.5:
        return {
            "positive_count": len(positive),
            "negative_count": len(negative),
            "preferred_direction": "high",
            "auc": auc_high,
        }
    return {
        "positive_count": len(positive),
        "negative_count": len(negative),
        "preferred_direction": "low",
        "auc": 1.0 - auc_high,
    }


def analyze(audit_path: Path, candidate_audit_path: Path | None = None) -> dict[str, object]:
    records = [
        json.loads(line)
        for line in audit_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if any(record.get("deepcenter_score") is None for record in records):
        raise ValueError("Every causal audit record must have a DeepCenter score")
    joined_count = 0
    if candidate_audit_path is not None:
        candidates = {}
        for line in candidate_audit_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            candidate = json.loads(line)
            key = (
                str(candidate["dataset"]),
                int(candidate["source_id"]),
                int(candidate["candidate_id"]),
            )
            candidates[key] = candidate
        for record in records:
            key = (
                str(record["dataset"]),
                int(record["source_id"]),
                int(record["candidate_id"]),
            )
            candidate = candidates.get(key)
            if candidate is None:
                continue
            record["parent_distance_um"] = float(candidate["parent_distance_um"])
            record["sister_distance_um"] = float(candidate["sister_distance_um"])
            record["geometric_rank_score"] = (
                float(candidate["parent_distance_um"])
                + 0.15 * float(candidate["sister_distance_um"])
            )
            joined_count += 1

    causal_tp = [
        float(record["deepcenter_score"])
        for record in records
        if int(record.get("causal_delta_tp", 0)) > 0
    ]
    causal_fp = [
        float(record["deepcenter_score"])
        for record in records
        if int(record.get("causal_delta_fp", 0)) > 0
    ]
    neutral = [
        float(record["deepcenter_score"])
        for record in records
        if int(record.get("causal_delta_tp", 0)) == 0
        and int(record.get("causal_delta_fp", 0)) == 0
        and int(record.get("causal_delta_fn", 0)) == 0
    ]
    causal_both = [
        float(record["deepcenter_score"])
        for record in records
        if int(record.get("causal_delta_tp", 0)) > 0
        and int(record.get("causal_delta_fp", 0)) > 0
    ]
    causal_tp_only = [
        float(record["deepcenter_score"])
        for record in records
        if int(record.get("causal_delta_tp", 0)) > 0
        and int(record.get("causal_delta_fp", 0)) <= 0
    ]
    causal_fp_only = [
        float(record["deepcenter_score"])
        for record in records
        if int(record.get("causal_delta_fp", 0)) > 0
        and int(record.get("causal_delta_tp", 0)) <= 0
    ]
    sweep = threshold_sweep(causal_tp, causal_fp)
    best = max(sweep, key=lambda row: (row["youden_j"], row["tpr"], -row["fpr"]))

    preserve_all_tp_threshold = min(causal_tp) if causal_tp else None
    reject_all_fp_threshold = max(causal_fp) if causal_fp else None
    return {
        "audit_file": audit_path.name,
        "record_count": len(records),
        "candidate_geometry_joined_count": joined_count,
        "causal_tp_scores": summarize(causal_tp),
        "causal_fp_scores": summarize(causal_fp),
        "causal_both_scores": summarize(causal_both),
        "causal_tp_only_scores": summarize(causal_tp_only),
        "causal_fp_only_scores": summarize(causal_fp_only),
        "neutral_scores": summarize(neutral),
        "auc_high_score_predicts_causal_tp": pairwise_auc(causal_tp, causal_fp),
        "auc_high_score_predicts_tp_only_vs_fp_only": pairwise_auc(
            causal_tp_only, causal_fp_only
        ),
        "exclusive_label_feature_auc": {
            feature: feature_auc(records, feature)
            for feature in (
                "deepcenter_score",
                "parent_distance_um",
                "sister_distance_um",
                "geometric_rank_score",
            )
        },
        "best_youden_threshold": best,
        "preserve_all_causal_tp": {
            "threshold": preserve_all_tp_threshold,
            "causal_fp_kept": (
                sum(score >= preserve_all_tp_threshold for score in causal_fp)
                if preserve_all_tp_threshold is not None
                else None
            ),
        },
        "reject_all_causal_fp": {
            "threshold_must_exceed": reject_all_fp_threshold,
            "causal_tp_above_fp_max": (
                sum(score > reject_all_fp_threshold for score in causal_tp)
                if reject_all_fp_threshold is not None
                else None
            ),
        },
        "interpretation_note": (
            "Causal labels are one-edge ablations and are not additive; threshold rows are "
            "classification diagnostics, not counterfactual aggregate metric estimates."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audit_path", type=Path)
    parser.add_argument("--candidate-audit", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = analyze(
        args.audit_path.resolve(),
        args.candidate_audit.resolve() if args.candidate_audit else None,
    )
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output:
        args.output.resolve().write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
