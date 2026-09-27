"""Evaluation through the parent's own scorer. The metric is never reimplemented here.

Every number comes from :mod:`scripts.exp067.parent_scorer`, which is the verbatim cell-8 extraction
and keeps the parent's **partial-label** semantics. The stricter training mask in
:mod:`scripts.exp067.supervise` is a different predicate and is not substituted in
(codex_challenge_v1 item 7).

Reported per video and in aggregate, plus per-prefix aggregates and the full graph audit.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from . import audit, provenance, supervise
from .parent_scorer import aggregate_official, score_sample


def score_one(
    graph: provenance.FinalGraph,
    edges: Sequence[tuple[int, int]],
    labels: supervise.LabelSet,
) -> dict[str, Any]:
    pred_nodes_plain = {
        int(node_id): (int(t), float(z), float(y), float(x))
        for node_id, t, (z, y, x) in zip(graph.node_id, graph.node_t, graph.node_zyx)
    }
    pred_edges = [(int(s), int(t)) for s, t in edges]
    gt_edges = sorted(labels.gt_edges)
    row = score_sample(
        pred_nodes_plain, pred_edges, labels.gt_nodes_plain, gt_edges, labels.t_true
    )
    row["stem"] = graph.dataset
    row["prefix"] = graph.dataset.split("_")[0]
    node_t = {int(v): int(t) for v, t in zip(graph.node_id, graph.node_t)}
    row["audit"] = audit.audit_graph(node_t, pred_edges)
    return row


def aggregate_with_prefixes(rows: Sequence[dict[str, Any]], division_weight: float = 0.1) -> dict[str, Any]:
    plain = [{k: v for k, v in row.items() if k not in {"stem", "prefix", "audit"}} for row in rows]
    overall = aggregate_official(plain)
    per_prefix: dict[str, Any] = {}
    for prefix in sorted({row["prefix"] for row in rows}):
        subset = [
            {k: v for k, v in row.items() if k not in {"stem", "prefix", "audit"}}
            for row in rows
            if row["prefix"] == prefix
        ]
        per_prefix[prefix] = aggregate_official(subset)
    return {
        "aggregate": overall,
        "per_prefix": per_prefix,
        "n_videos": len(rows),
        "division_weight": division_weight,
        "note": (
            "proxy_score = adjusted_edge_jaccard + 0.1 * division_jaccard, from the parent's own "
            "aggregate_official; partial-label semantics preserved"
        ),
    }


def compare(
    parent_rows: Sequence[dict[str, Any]], candidate_rows: Sequence[dict[str, Any]]
) -> dict[str, Any]:
    """Parent vs candidate, with the mechanism check (``edges_fragmented``) called out."""
    if not parent_rows or sorted(r["stem"] for r in parent_rows) != sorted(r["stem"] for r in candidate_rows):
        raise ValueError("comparison requires identical nonempty parent/candidate video sets")
    parent = aggregate_with_prefixes(parent_rows)
    candidate = aggregate_with_prefixes(candidate_rows)
    delta_prefix = {
        prefix: candidate["per_prefix"][prefix]["proxy_score"] - parent["per_prefix"][prefix]["proxy_score"]
        for prefix in sorted(set(parent["per_prefix"]) & set(candidate["per_prefix"]))
    }
    return {
        "parent": parent,
        "candidate": candidate,
        "delta_proxy": candidate["aggregate"]["proxy_score"] - parent["aggregate"]["proxy_score"],
        "delta_adjusted_edge_jaccard": (
            candidate["aggregate"]["adjusted_edge_jaccard"] - parent["aggregate"]["adjusted_edge_jaccard"]
        ),
        "delta_per_prefix_proxy": delta_prefix,
        "mechanism_edges_fragmented": {
            "parent": parent["aggregate"]["edges_fragmented"],
            "candidate": candidate["aggregate"]["edges_fragmented"],
            "delta": candidate["aggregate"]["edges_fragmented"] - parent["aggregate"]["edges_fragmented"],
            "reading": (
                "H1 requires this to FALL. A positive proxy delta with no fall does not support the "
                "mechanism claim."
            ),
        },
        "division": {
            "parent": [parent["aggregate"]["div_tp"], parent["aggregate"]["div_fp"], parent["aggregate"]["div_fn"]],
            "candidate": [
                candidate["aggregate"]["div_tp"], candidate["aggregate"]["div_fp"], candidate["aggregate"]["div_fn"]
            ],
        },
        "division_head_trained": "not inferred from scores; inspect checkpoint/receipt",
        "backbone_provenance": "POSSIBLE_OVERLAP_UNKNOWN_PROVENANCE",
        "evidence_class": "local proxy on TRAIN stems; NOT Public LB evidence",
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", required=True)
    parser.add_argument("--label-dir", required=True)
    parser.add_argument("--decoded-dir", default=None, help="where *.decoded.npz live; default export-dir")
    parser.add_argument("--stems", default=None)
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)

    export_dir = Path(args.export_dir)
    label_dir = Path(args.label_dir)
    decoded_dir = Path(args.decoded_dir) if args.decoded_dir else export_dir
    stems = (
        [s.strip() for s in args.stems.split(",") if s.strip()]
        if args.stems
        else sorted(p.name[: -len(".final.npz")] for p in export_dir.glob("*.final.npz"))
    )

    parent_rows: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    for stem in stems:
        graph = provenance.load_final_graph(export_dir / f"{stem}.final.npz")
        labels = supervise.load_label_set(label_dir / f"{stem}.npz")
        if labels.stem != graph.dataset:
            raise ValueError('evaluation label/graph identity mismatch')
        parent_rows.append(
            score_one(graph, list(zip(graph.edge_src.tolist(), graph.edge_tgt.tolist())), labels)
        )
        decoded_path = decoded_dir / f"{stem}.decoded.npz"
        if decoded_path.exists():
            with np.load(decoded_path, allow_pickle=False) as payload:
                import hashlib
                expected = hashlib.sha256((export_dir / f'{stem}.final.npz').read_bytes()).hexdigest()
                if str(payload['parent_graph_sha256']) != expected:
                    raise ValueError('decoded edges belong to a different parent graph')
                edges = list(zip(payload["edge_src"].tolist(), payload["edge_tgt"].tolist()))
            candidate_rows.append(score_one(graph, edges, labels))

    report: dict[str, Any] = {"per_video_parent": parent_rows}
    if candidate_rows:
        report["per_video_candidate"] = candidate_rows
        report["comparison"] = compare(parent_rows, candidate_rows)
    else:
        report["parent_only"] = aggregate_with_prefixes(parent_rows)

    text = json.dumps(report, indent=2, sort_keys=True, default=float)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
