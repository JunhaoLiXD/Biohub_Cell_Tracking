"""Inference / decode: the CLI and the in-notebook entry point.

This module never imports :mod:`scripts.exp067.supervise` and never opens a label file. That is
structural, and ``tests/test_exp067_supervision.py`` asserts it both by source inspection and by
running inference with the label reader monkeypatched to raise.

Failure policy (codex_challenge_v1 item 10): the notebook entry point does **not** raise into the
parent's ``try/except`` around ``filter_output_graph`` — that handler would swallow the failure and
emit a fallback graph with every gate green. It records ``runtime.FATAL`` and returns the parent graph;
a second injected check immediately after that ``try/except`` re-raises outside it.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from . import audit, checkpoint, decode, provenance, runtime, schema
from . import features as F
from . import hypotheses as H
from .config import Exp067Config
from .model import JointLineageScorer, Normalizer, score_batch
from .errors import Exp067Deadline


@dataclass
class DecodedGraph:
    edges: list[tuple[int, int]]
    receipt: runtime.Receipt
    audit: dict[str, object]
    objective: float
    parent_objective: float


def _score_all(
    model: JointLineageScorer,
    normalizer: Normalizer,
    hyp: H.Hypotheses,
    batches: Sequence[F.WindowBatch],
    deadline: runtime.Deadline,
) -> tuple[np.ndarray, np.ndarray]:
    link = np.zeros(hyp.n_edges, dtype=np.float64)
    event = np.zeros(hyp.n_events, dtype=np.float64)
    for batch in batches:
        deadline.check("model scoring")
        started = time.time()
        link_scores, event_scores = score_batch(model, batch, normalizer)
        deadline.add_scoring(time.time() - started)
        for i, k in enumerate(batch.edge_keys):
            link[int(k)] = link_scores[i]
        for i, j in enumerate(batch.event_keys):
            event[int(j)] = event_scores[i]
    return link, event


def decode_graph(
    graph: provenance.FinalGraph,
    evidence: provenance.Evidence,
    model: JointLineageScorer | None,
    normalizer: Normalizer | None,
    config: Exp067Config,
    *,
    mode: str = runtime.MODE_DECODE,
    deadline: runtime.Deadline | None = None,
) -> DecodedGraph:
    """Decode one movie. ``mode='parent'`` is the zero-new-evidence control, not the bypass."""
    started = time.time()
    receipt = runtime.Receipt(dataset=graph.dataset, mode=mode)
    receipt.n_final_nodes = graph.n_nodes
    receipt.n_parent_edges = graph.n_edges
    receipt.divisions_before = sum(1 for d in graph.out_degree().values() if d >= 2)
    deadline = deadline or runtime.Deadline(config.solve.budget_seconds)

    parent_edges = [(int(s), int(t)) for s, t in zip(graph.edge_src, graph.edge_tgt)]
    node_t = {int(v): int(t) for v, t in zip(graph.node_id, graph.node_t)}

    if mode == runtime.MODE_PARENT:
        receipt.reason = "control_mode_parent: the parent edge set is returned by identity"
        receipt.edges_kept = len(parent_edges)
        receipt.divisions_after = receipt.divisions_before
        receipt.total_seconds = time.time() - started
        return DecodedGraph(parent_edges, receipt, audit.audit_graph(node_t, parent_edges), 0.0, 0.0)

    table = provenance.reconcile(graph, evidence)
    receipt.n_reconsiderable_nodes = int(np.count_nonzero(table.reconsiderable))

    if graph.n_nodes == 0 or graph.n_edges == 0 or len(table.nodes_by_t) < 2:
        receipt.reason = "degenerate_movie: fewer than two populated frames, or no parent edges"
        receipt.edges_kept = len(parent_edges)
        receipt.divisions_after = receipt.divisions_before
        receipt.total_seconds = time.time() - started
        return DecodedGraph(parent_edges, receipt, audit.audit_graph(node_t, parent_edges), 0.0, 0.0)

    hyp = H.generate(table, config)
    receipt.alt_dropped_node_absent = hyp.alt_dropped_node_absent
    batches, ctx = F.build_batches(hyp, config)

    if not batches or int(np.count_nonzero(ctx.free_edge)) == 0:
        receipt.reason = (
            "empty_learned_pool: no free candidate edge survived generation, so there is nothing to "
            "reconsider; the parent graph is returned unchanged"
        )
        receipt.edges_kept = len(parent_edges)
        receipt.divisions_after = receipt.divisions_before
        receipt.total_seconds = time.time() - started
        return DecodedGraph(parent_edges, receipt, audit.audit_graph(node_t, parent_edges), 0.0, 0.0)

    if model is None or normalizer is None:
        raise ValueError("decode mode requires a trained checkpoint; pass mode='parent' for the control")

    try:
        link_scores, event_scores = _score_all(model, normalizer, hyp, batches, deadline)
        deadline.check('post scoring')
    except Exp067Deadline:
        receipt.reason = 'scoring_deadline_parent_fallback'
        receipt.revert('scoring_deadline')
        receipt.edges_kept = len(parent_edges)
        receipt.divisions_after = receipt.divisions_before
        receipt.total_seconds = time.time() - started
        return DecodedGraph(parent_edges, receipt, audit.audit_graph(node_t, parent_edges), 0., 0.)
    if not np.isfinite(link_scores).all() or not np.isfinite(event_scores).all():
        raise ValueError('nonfinite learned scores')
    program = decode.build_program(hyp, ctx, link_scores, event_scores, config)
    decode.assert_parent_feasible(program)
    parent_value = decode.parent_objective(program)
    result = decode.solve(program, config, deadline, receipt)

    selected = [
        (int(graph.node_id[int(hyp.e_src[k])]), int(graph.node_id[int(hyp.e_tgt[k])]))
        for k in range(hyp.n_edges)
        if result.selected_edges[k]
    ]
    parent_set = set(parent_edges)
    selected_set = set(selected)
    receipt.edges_added = len(selected_set - parent_set)
    receipt.edges_removed = len(parent_set - selected_set)
    receipt.edges_kept = len(selected_set & parent_set)
    out_degree: dict[int, int] = {}
    for source, _target in selected:
        out_degree[source] = out_degree.get(source, 0) + 1
    receipt.divisions_after = sum(1 for d in out_degree.values() if d >= 2)
    receipt.divisions_reclaimed = int(
        sum(
            1
            for j in range(hyp.n_events)
            if result.selected_events[j]
            and not hyp.v_is_parent_fork[j]
            and (ctx.has_parent_in[int(hyp.v_a[j])] or ctx.has_parent_in[int(hyp.v_b[j])])
        )
    )
    receipt.active = receipt.active or (receipt.edges_added + receipt.edges_removed) > 0
    if not receipt.active and receipt.reason is None:
        receipt.reason = "solved: the optimum coincided with the parent edge set"
    receipt.scoring_seconds = deadline.scoring_s
    receipt.solving_seconds = deadline.solving_s
    receipt.total_seconds = time.time() - started
    receipt.division_head_trained = True

    graph_audit = audit.audit_graph(node_t, selected)
    audit.assert_node_set_preserved(graph.node_id.tolist(), graph.node_id.tolist())
    return DecodedGraph(selected, receipt, graph_audit, result.objective, parent_value)


# --------------------------------------------------------------------- notebook entry point

def joint_reconsider(
    nodes_by_id: Mapping[int, Mapping[str, Any]],
    edges: Sequence[Mapping[str, Any]],
    stats: dict[str, Any] | None = None,
    dataset: str | None = None,
    *,
    export_dir: str | Path | None = None,
    ckpt_path: str | Path | None = None,
    mode: str | None = None,
    config: Exp067Config | None = None,
    det_row_of_node: Mapping[int, int] | None = None,
) -> tuple[Mapping[int, Mapping[str, Any]], list[Mapping[str, Any]]]:
    """Called at the very end of ``filter_output_graph``, after line-fit smoothing.

    Returns ``(nodes_by_id, edges)``. The node dict is returned **by identity**: this stage may not
    add, delete or move a node.
    """
    stats = stats if stats is not None else {}
    dataset = dataset or "unknown"
    try:
        config = config or Exp067Config.load()
        mode = mode or os.environ.get(runtime.ENV_MODE, runtime.MODE_DECODE).strip() or runtime.MODE_DECODE
        if mode not in runtime.VALID_MODES:
            raise ValueError(f"{runtime.ENV_MODE}={mode!r} is not one of {runtime.VALID_MODES}")
        export_dir = Path(export_dir or os.environ.get(runtime.ENV_EXPORT_DIR, "") or "exp067_export")
        graph = provenance.final_graph_from_parent(dataset, nodes_by_id, edges, det_row_of_node)

        model = normalizer = None
        evidence = _empty_evidence(dataset)
        if mode == runtime.MODE_DECODE:
            evidence = provenance.load_evidence(export_dir / f"{dataset}.npz")
            raw_ckpt = ckpt_path or os.environ.get(runtime.ENV_CKPT, "")
            if not raw_ckpt:
                raise ValueError(f"{runtime.ENV_CKPT} is unset; decode mode needs a trained checkpoint")
            model, normalizer, _meta = checkpoint.load(Path(raw_ckpt), emb_channels=evidence.emb_channels, config=config)
            checkpoint.validate_export(_meta, evidence)

        budget = runtime.env_float(runtime.ENV_BUDGET_S, config.solve.budget_seconds)
        decoded = decode_graph(
            graph, evidence, model, normalizer, config,
            mode=mode, deadline=runtime.Deadline(budget),
        )

        audit.assert_node_set_preserved(nodes_by_id.keys(), nodes_by_id.keys())
        new_edges = _rebuild_edge_dicts(nodes_by_id, edges, decoded.edges)
        _record_stats(stats, decoded)
        _write_receipt(export_dir, dataset, decoded)
        return nodes_by_id, new_edges
    except Exception as exc:  # noqa: BLE001 - see the module docstring: never raise in here
        runtime.set_fatal(f"{dataset}: {type(exc).__name__}: {exc}")
        return nodes_by_id, list(edges)


def _empty_evidence(dataset: str) -> provenance.Evidence:
    return provenance.Evidence(
        dataset=dataset,
        coords=np.zeros((0, 4), dtype=np.float64),
        node_ids=np.zeros(0, dtype=np.int64),
        emb_src=np.zeros((0, 1), dtype=np.float32),
        emb_tgt=np.zeros((0, 1), dtype=np.float32),
        emb_src_valid=np.zeros(0, dtype=bool),
        emb_tgt_valid=np.zeros(0, dtype=bool),
        det_score=np.zeros(0, dtype=np.float32),
        alt_src_row=np.zeros(0, dtype=np.int64),
        alt_tgt_row=np.zeros(0, dtype=np.int64),
        alt_prob=np.zeros(0, dtype=np.float32),
        alt_logit=np.zeros(0, dtype=np.float32),
        alt_origin=np.zeros(0, dtype=np.int16),
        manifest={"dataset": dataset, "schema": schema.EXPORT_SCHEMA_VERSION, "synthetic_empty": True},
    )


def _rebuild_edge_dicts(
    nodes_by_id: Mapping[int, Mapping[str, Any]],
    parent_edges: Sequence[Mapping[str, Any]],
    selected: Sequence[tuple[int, int]],
) -> list[dict[str, Any]]:
    """Keep the parent's own edge dicts where an edge survives; synthesise only for new edges."""
    existing = {(int(e["source_id"]), int(e["target_id"])): e for e in parent_edges}
    scale = np.asarray(schema.VOXEL_SCALE_UM, dtype=np.float64)
    out: list[dict[str, Any]] = []
    for source, target in sorted(selected):
        found = existing.get((source, target))
        if found is not None:
            out.append(dict(found))
            continue
        a = nodes_by_id[source]
        b = nodes_by_id[target]
        delta = (
            np.asarray([float(b["z"]), float(b["y"]), float(b["x"])])
            - np.asarray([float(a["z"]), float(a["y"]), float(a["x"])])
        ) * scale
        out.append(
            {
                "source_id": int(source),
                "target_id": int(target),
                "edge_prob": None,
                "distance_um": float(np.linalg.norm(delta)),
                "exp067_added": 1,
            }
        )
    return out


def _record_stats(stats: dict[str, Any], decoded: DecodedGraph) -> None:
    receipt = decoded.receipt
    stats["exp067_active"] = int(bool(receipt.active))
    stats["exp067_mode"] = receipt.mode
    stats["exp067_edges_added"] = receipt.edges_added
    stats["exp067_edges_removed"] = receipt.edges_removed
    stats["exp067_divisions_before"] = receipt.divisions_before
    stats["exp067_divisions_after"] = receipt.divisions_after
    stats["exp067_divisions_reclaimed"] = receipt.divisions_reclaimed
    stats["exp067_components"] = receipt.n_components
    stats["exp067_components_reverted"] = receipt.n_components_reverted
    stats["exp067_objective"] = decoded.objective
    stats["exp067_parent_objective"] = decoded.parent_objective


def _write_receipt(export_dir: Path, dataset: str, decoded: DecodedGraph) -> Path:
    path = Path(export_dir) / f"{dataset}.receipt.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "receipt": decoded.receipt.to_dict(),
        "audit": decoded.audit,
        "objective": decoded.objective,
        "parent_objective": decoded.parent_objective,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=float), encoding="utf-8")
    return path


# ------------------------------------------------------------------------------------- CLI

def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", required=True)
    parser.add_argument("--stems", default=None, help="comma-separated; default every *.final.npz")
    parser.add_argument("--ckpt", default=None)
    parser.add_argument("--mode", default=runtime.MODE_DECODE, choices=list(runtime.VALID_MODES))
    parser.add_argument("--config", default=None)
    parser.add_argument("--out", default=None, help="directory for decoded graphs and receipts")
    args = parser.parse_args(argv)

    config = Exp067Config.load(args.config)
    export_dir = Path(args.export_dir)
    out_dir = Path(args.out) if args.out else export_dir
    stems = (
        [s.strip() for s in args.stems.split(",") if s.strip()]
        if args.stems
        else sorted(p.name[: -len(".final.npz")] for p in export_dir.glob("*.final.npz"))
    )
    if not stems:
        print(f"no *.final.npz under {export_dir}")
        return 1

    model = normalizer = None
    if args.mode == runtime.MODE_DECODE:
        if not args.ckpt:
            print("--ckpt is required for --mode decode")
            return 2

    summary: list[dict[str, object]] = []
    for stem in stems:
        graph = provenance.load_final_graph(export_dir / f"{stem}.final.npz")
        evidence = provenance.load_evidence(export_dir / f"{stem}.npz")
        if args.mode == runtime.MODE_DECODE and model is None:
            model, normalizer, _meta = checkpoint.load(Path(args.ckpt), emb_channels=evidence.emb_channels, config=config)
        if args.mode == runtime.MODE_DECODE:
            checkpoint.validate_export(_meta, evidence)
        decoded = decode_graph(
            graph, evidence, model, normalizer, config,
            mode=args.mode, deadline=runtime.Deadline(config.solve.budget_seconds),
        )
        out_dir.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            out_dir / f"{stem}.decoded.npz",
            edge_src=np.asarray([e[0] for e in decoded.edges], dtype=np.int64),
            edge_tgt=np.asarray([e[1] for e in decoded.edges], dtype=np.int64),
            parent_graph_sha256=np.asarray(__import__('hashlib').sha256(
                (export_dir / f'{stem}.final.npz').read_bytes()).hexdigest()),
        )
        _write_receipt(out_dir, stem, decoded)
        summary.append({"stem": stem, **decoded.receipt.to_dict()})
        print(json.dumps(summary[-1], indent=2, sort_keys=True, default=float))
    (out_dir / "exp067_decode_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, default=float), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
