"""The data model, its IO, and identity/provenance tracking.

codex_challenge_v1 item 2: the mapping detector row -> graph node id is **captured from
``build_graph``'s own ``bulk_add_nodes`` return** and exported, and final-node provenance comes from
the parent's own node-dict flags. Nothing here matches coordinates by nearest neighbour, and nothing
trusts a node id on its own.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from . import schema
from .errors import Exp067ProvenanceError, Exp067SchemaError


# --------------------------------------------------------------------------- final graph

@dataclass
class FinalGraph:
    """The parent's FINAL graph: the exact node set, coordinates and edges exp_067 must preserve."""

    dataset: str
    node_id: np.ndarray
    node_t: np.ndarray
    node_zyx: np.ndarray
    node_origin: np.ndarray
    node_det_row: np.ndarray
    edge_src: np.ndarray
    edge_tgt: np.ndarray
    manifest: dict[str, Any]

    def __post_init__(self) -> None:
        n = len(self.node_id)
        if not np.isfinite(self.node_zyx).all() or not np.isfinite(self.node_t).all():
            raise Exp067SchemaError("FinalGraph: nonfinite coordinates/time")
        if not np.isin(self.node_origin, list(schema.ORIGIN_NAMES)).all():
            raise Exp067SchemaError("FinalGraph: unknown origin")
        for name, arr, shape in (
            ("node_t", self.node_t, (n,)),
            ("node_zyx", self.node_zyx, (n, 3)),
            ("node_origin", self.node_origin, (n,)),
            ("node_det_row", self.node_det_row, (n,)),
        ):
            if tuple(np.shape(arr)) != shape:
                raise Exp067SchemaError(f"FinalGraph.{name}: expected {shape}, got {np.shape(arr)}")
        if len(self.edge_src) != len(self.edge_tgt):
            raise Exp067SchemaError("FinalGraph: edge_src and edge_tgt differ in length")
        if len(set(self.node_id.tolist())) != n:
            raise Exp067ProvenanceError("FinalGraph: duplicate node ids")
        self.row_of_node: dict[int, int] = {int(v): i for i, v in enumerate(self.node_id)}
        known = set(self.row_of_node)
        unknown = [int(v) for v in self.edge_src if int(v) not in known]
        unknown += [int(v) for v in self.edge_tgt if int(v) not in known]
        if unknown:
            raise Exp067ProvenanceError(
                f"FinalGraph: {len(unknown)} edge endpoint(s) not in the node set, "
                f"first few {sorted(set(unknown))[:8]}"
            )
        from .audit import audit_graph
        audit_graph(dict(zip(self.node_id.tolist(), self.node_t.tolist())), list(zip(self.edge_src, self.edge_tgt)))

    @property
    def n_nodes(self) -> int:
        return len(self.node_id)

    @property
    def n_edges(self) -> int:
        return len(self.edge_src)

    def positions_um(self) -> np.ndarray:
        return schema.voxel_to_um(self.node_zyx)

    def parent_edge_set(self) -> set[tuple[int, int]]:
        return {(int(s), int(t)) for s, t in zip(self.edge_src, self.edge_tgt)}

    def out_degree(self) -> dict[int, int]:
        degree: dict[int, int] = {}
        for s in self.edge_src:
            degree[int(s)] = degree.get(int(s), 0) + 1
        return degree

    def in_source(self) -> dict[int, int]:
        """target node id -> its single parent source id (the parent graph has in-degree <= 1)."""
        source: dict[int, int] = {}
        for s, t in zip(self.edge_src, self.edge_tgt):
            source[int(t)] = int(s)
        return source


def classify_origin(node: Mapping[str, Any]) -> int:
    """Provenance straight from the parent's own flags (cell 5:1291-1292, 948, 1451)."""
    if int(node.get("_exp067_origin", -1)) == schema.ORIGIN_SYNTHETIC:
        return schema.ORIGIN_SYNTHETIC
    if int(node.get("gap_synthetic", 0)) == 1:
        return schema.ORIGIN_SYNTHETIC
    if int(node.get("readmitted", 0)) == 1 or int(node.get("gapfill_peak", 0)) == 1:
        return schema.ORIGIN_READMITTED
    return schema.ORIGIN_DETECTOR


def final_graph_from_parent(
    dataset: str,
    nodes_by_id: Mapping[int, Mapping[str, Any]],
    edges: Sequence[Mapping[str, Any]],
    det_row_of_node: Mapping[int, int] | None = None,
    manifest: dict[str, Any] | None = None,
) -> FinalGraph:
    """Build a :class:`FinalGraph` from the parent's live ``nodes_by_id`` / ``edges`` structures."""
    ids = sorted(int(k) for k in nodes_by_id)
    node_id = np.asarray(ids, dtype=np.int64)
    node_t = np.asarray([int(nodes_by_id[i]["t"]) for i in ids], dtype=np.int64)
    node_zyx = np.asarray(
        [[float(nodes_by_id[i]["z"]), float(nodes_by_id[i]["y"]), float(nodes_by_id[i]["x"])] for i in ids],
        dtype=np.float64,
    ).reshape(len(ids), 3)
    node_origin = np.asarray([classify_origin(nodes_by_id[i]) for i in ids], dtype=np.int8)
    mapping = dict(det_row_of_node or {})
    node_det_row = np.asarray([int(mapping.get(i, -1)) for i in ids], dtype=np.int64)

    untraceable = [
        int(i)
        for i, origin, row in zip(node_id, node_origin, node_det_row)
        if origin == schema.ORIGIN_DETECTOR and row < 0
    ]
    if mapping and untraceable:
        raise Exp067ProvenanceError(
            f"{dataset}: {len(untraceable)} detector-origin final node(s) are absent from the "
            f"build_graph node-id map, first few {untraceable[:8]}"
        )

    edge_src = np.asarray([int(e["source_id"]) for e in edges], dtype=np.int64)
    edge_tgt = np.asarray([int(e["target_id"]) for e in edges], dtype=np.int64)
    return FinalGraph(
        dataset=dataset,
        node_id=node_id,
        node_t=node_t,
        node_zyx=node_zyx,
        node_origin=node_origin,
        node_det_row=node_det_row,
        edge_src=edge_src,
        edge_tgt=edge_tgt,
        manifest=manifest or {},
    )


def save_final_graph(path: Path, graph: FinalGraph) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest = dict(graph.manifest)
    manifest.update(
        {
            "dataset": graph.dataset,
            "schema": schema.FINAL_GRAPH_SCHEMA_VERSION,
            "stage": "post_linefit_pre_return",
            "n_nodes": int(graph.n_nodes),
            "n_edges": int(graph.n_edges),
            "voxel_scale_um": list(schema.VOXEL_SCALE_UM),
            "node_zyx_sha256": schema.sha256_array(graph.node_zyx),
            "edge_sha256": schema.sha256_array(np.stack([graph.edge_src, graph.edge_tgt])),
        }
    )
    tmp = path.with_suffix(".tmp.npz")
    schema.savez_checked(
        tmp,
        final_schema=np.asarray(schema.FINAL_GRAPH_SCHEMA_VERSION, dtype=np.int32),
        node_id=graph.node_id,
        node_t=graph.node_t,
        node_zyx=graph.node_zyx.astype(np.float64),
        node_origin=graph.node_origin,
        node_det_row=graph.node_det_row,
        edge_src=graph.edge_src,
        edge_tgt=graph.edge_tgt,
        manifest=schema.dump_manifest(manifest),
    )
    tmp.replace(path)
    return path


def load_final_graph(path: Path) -> FinalGraph:
    with np.load(path, allow_pickle=False) as payload:
        schema.require_fields(payload, schema.FINAL_GRAPH_REQUIRED_FIELDS, f"final graph {path.name}")
        schema.require_version(
            payload["final_schema"].item(), schema.FINAL_GRAPH_SCHEMA_VERSION, f"final graph {path.name}"
        )
        manifest = schema.load_manifest(payload["manifest"])
        return FinalGraph(
            dataset=str(manifest.get("dataset", path.stem)),
            node_id=payload["node_id"].astype(np.int64),
            node_t=payload["node_t"].astype(np.int64),
            node_zyx=payload["node_zyx"].astype(np.float64),
            node_origin=payload["node_origin"].astype(np.int8),
            node_det_row=payload["node_det_row"].astype(np.int64),
            edge_src=payload["edge_src"].astype(np.int64),
            edge_tgt=payload["edge_tgt"].astype(np.int64),
            manifest=manifest,
        )


# ----------------------------------------------------------------------------- evidence

@dataclass
class Evidence:
    """Per-detector-row model evidence exported from inside ``predict_video``."""

    dataset: str
    coords: np.ndarray  # (R, 4) [t, z, y, x], original-resolution voxel, float64
    node_ids: np.ndarray  # (R,) graph node id of row r, captured from build_graph
    emb_src: np.ndarray  # (R, C) float32
    emb_tgt: np.ndarray  # (R, C) float32
    emb_src_valid: np.ndarray  # (R,) bool
    emb_tgt_valid: np.ndarray  # (R,) bool
    det_score: np.ndarray  # (R,) float32
    alt_src_row: np.ndarray  # (M,) int64 detector row
    alt_tgt_row: np.ndarray  # (M,) int64 detector row
    alt_prob: np.ndarray  # (M,) float32, softmax over SOURCES
    alt_logit: np.ndarray  # (M,) float32, post-fusion raw logit
    alt_origin: np.ndarray  # (M,) int16 bitmask, schema.ALT_ORIGIN_*
    manifest: dict[str, Any]

    def __post_init__(self) -> None:
        rows = len(self.coords)
        if np.shape(self.coords) != (rows, 4):
            raise Exp067SchemaError("Evidence: coords must have shape (N,4)")
        for name in ("coords", "emb_src", "emb_tgt", "det_score", "alt_prob", "alt_logit"):
            if not np.isfinite(getattr(self, name)).all():
                raise Exp067SchemaError(f"Evidence: nonfinite {name}")
        for name in ("det_score", "alt_prob"):
            a = getattr(self, name)
            if np.any((a < 0) | (a > 1)):
                raise Exp067SchemaError(f"Evidence: probability out of range: {name}")
        for name in ("alt_src_row", "alt_tgt_row"):
            a = getattr(self, name)
            if np.any((a < 0) | (a >= rows)):
                raise Exp067SchemaError(f"Evidence: alternative index out of range: {name}")
        for name, arr, shape in (
            ("node_ids", self.node_ids, (rows,)),
            ("emb_src", self.emb_src, (rows, self.emb_channels)),
            ("emb_tgt", self.emb_tgt, (rows, self.emb_channels)),
            ("emb_src_valid", self.emb_src_valid, (rows,)),
            ("emb_tgt_valid", self.emb_tgt_valid, (rows,)),
            ("det_score", self.det_score, (rows,)),
        ):
            if tuple(np.shape(arr)) != shape:
                raise Exp067SchemaError(f"Evidence.{name}: expected {shape}, got {np.shape(arr)}")
        lengths = {
            len(self.alt_src_row), len(self.alt_tgt_row), len(self.alt_prob),
            len(self.alt_logit), len(self.alt_origin),
        }
        if len(lengths) != 1:
            raise Exp067SchemaError(f"Evidence: alternative arrays have mismatched lengths {lengths}")
        if rows and len(set(self.node_ids.tolist())) != rows:
            raise Exp067ProvenanceError(
                f"{self.dataset}: detector row -> graph node id map is not injective"
            )
        self.row_of_node_id: dict[int, int] = {int(v): i for i, v in enumerate(self.node_ids)}

    @property
    def emb_channels(self) -> int:
        return int(np.shape(self.emb_src)[1]) if np.ndim(self.emb_src) == 2 else 0

    @property
    def n_rows(self) -> int:
        return len(self.coords)

    @property
    def n_alternatives(self) -> int:
        return len(self.alt_src_row)


def save_evidence(path: Path, evidence: Evidence) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest = dict(evidence.manifest)
    manifest.update(
        {
            "dataset": evidence.dataset,
            "schema": schema.EXPORT_SCHEMA_VERSION,
            "voxel_scale_um": list(schema.VOXEL_SCALE_UM),
            "emb_channels": int(evidence.emb_channels),
            "emb_dtype": "float16",
            "n_rows": int(evidence.n_rows),
            "n_alternatives": int(evidence.n_alternatives),
            "coords_sha256": schema.sha256_array(evidence.coords),
            "alt_sha256": schema.sha256_array(
                np.stack([evidence.alt_src_row, evidence.alt_tgt_row]) if evidence.n_alternatives
                else np.zeros((2, 0), dtype=np.int64)
            ),
            "ground_truth_accessed": False,
        }
    )
    tmp = path.with_suffix(".tmp.npz")
    schema.savez_checked(
        tmp,
        exp067_schema=np.asarray(schema.EXPORT_SCHEMA_VERSION, dtype=np.int32),
        coords=evidence.coords.astype(np.float64),
        node_ids=evidence.node_ids.astype(np.int64),
        emb_src=evidence.emb_src.astype(np.float16),
        emb_tgt=evidence.emb_tgt.astype(np.float16),
        emb_src_valid=evidence.emb_src_valid.astype(bool),
        emb_tgt_valid=evidence.emb_tgt_valid.astype(bool),
        det_score=evidence.det_score.astype(np.float32),
        alt_src_row=evidence.alt_src_row.astype(np.int64),
        alt_tgt_row=evidence.alt_tgt_row.astype(np.int64),
        alt_prob=evidence.alt_prob.astype(np.float32),
        alt_logit=evidence.alt_logit.astype(np.float32),
        alt_origin=evidence.alt_origin.astype(np.int16),
        manifest=schema.dump_manifest(manifest),
    )
    tmp.replace(path)
    return path


def load_evidence(path: Path) -> Evidence:
    with np.load(path, allow_pickle=False) as payload:
        schema.require_fields(payload, schema.EXPORT_REQUIRED_FIELDS, f"export {path.name}")
        schema.require_version(
            payload["exp067_schema"].item(), schema.EXPORT_SCHEMA_VERSION, f"export {path.name}"
        )
        manifest = schema.load_manifest(payload["manifest"])
        return Evidence(
            dataset=str(manifest.get("dataset", path.stem)),
            coords=payload["coords"].astype(np.float64),
            node_ids=payload["node_ids"].astype(np.int64),
            emb_src=payload["emb_src"].astype(np.float32),
            emb_tgt=payload["emb_tgt"].astype(np.float32),
            emb_src_valid=payload["emb_src_valid"].astype(bool),
            emb_tgt_valid=payload["emb_tgt_valid"].astype(bool),
            det_score=payload["det_score"].astype(np.float32),
            alt_src_row=payload["alt_src_row"].astype(np.int64),
            alt_tgt_row=payload["alt_tgt_row"].astype(np.int64),
            alt_prob=payload["alt_prob"].astype(np.float32),
            alt_logit=payload["alt_logit"].astype(np.float32),
            alt_origin=payload["alt_origin"].astype(np.int16),
            manifest=manifest,
        )


# ------------------------------------------------------------------------- reconciliation

@dataclass
class NodeTable:
    """Final-graph nodes joined to their evidence. ``reconsiderable`` is the set R."""

    graph: FinalGraph
    evidence: Evidence
    det_row: np.ndarray  # (N,) detector row per final node, -1 when absent
    reconsiderable: np.ndarray  # (N,) bool
    positions_um: np.ndarray  # (N, 3) float64
    emb_src: np.ndarray  # (N, C) float32, zeros where not reconsiderable (masked by emb_valid)
    emb_tgt: np.ndarray
    emb_src_valid: np.ndarray
    emb_tgt_valid: np.ndarray
    det_score: np.ndarray
    det_available: np.ndarray
    nodes_by_t: dict[int, np.ndarray]

    @property
    def n_nodes(self) -> int:
        return self.graph.n_nodes


def reconcile(graph: FinalGraph, evidence: Evidence) -> NodeTable:
    """Join the final graph to its evidence, fail-closed on any provenance inconsistency."""
    if graph.dataset != evidence.dataset:
        raise Exp067ProvenanceError("graph/evidence dataset mismatch")
    n = graph.n_nodes
    channels = evidence.emb_channels
    det_row = np.full(n, -1, dtype=np.int64)

    for i in range(n):
        if graph.node_origin[i] != schema.ORIGIN_DETECTOR:
            continue
        node_id = int(graph.node_id[i])
        declared = int(graph.node_det_row[i])
        looked_up = evidence.row_of_node_id.get(node_id, -1)
        if declared >= 0 and looked_up >= 0 and declared != looked_up:
            raise Exp067ProvenanceError(
                f"{graph.dataset}: node {node_id} declares detector row {declared} but the exported "
                f"build_graph map says {looked_up}"
            )
        resolved = declared if declared >= 0 else looked_up
        if resolved < 0:
            raise Exp067ProvenanceError(
                f"{graph.dataset}: detector-origin node {node_id} has no detector row in either the "
                "final graph or the exported build_graph map"
            )
        if resolved >= evidence.n_rows:
            raise Exp067ProvenanceError(
                f"{graph.dataset}: node {node_id} detector row {resolved} is out of range "
                f"(export has {evidence.n_rows} rows)"
            )
        det_row[i] = resolved
        if int(evidence.node_ids[resolved]) != node_id or evidence.coords[resolved, 0] != graph.node_t[i]:
            raise Exp067ProvenanceError(f"{graph.dataset}: identity/time mismatch for node {node_id}")

    traced = det_row[det_row >= 0]
    if len(set(traced.tolist())) != len(traced):
        raise Exp067ProvenanceError(f"{graph.dataset}: two final nodes claim the same detector row")

    emb_src = np.zeros((n, channels), dtype=np.float32)
    emb_tgt = np.zeros((n, channels), dtype=np.float32)
    emb_src_valid = np.zeros(n, dtype=bool)
    emb_tgt_valid = np.zeros(n, dtype=bool)
    det_score = np.zeros(n, dtype=np.float32)
    det_available = np.zeros(n, dtype=bool)

    has_row = det_row >= 0
    rows = det_row[has_row]
    emb_src[has_row] = evidence.emb_src[rows]
    emb_tgt[has_row] = evidence.emb_tgt[rows]
    emb_src_valid[has_row] = evidence.emb_src_valid[rows]
    emb_tgt_valid[has_row] = evidence.emb_tgt_valid[rows]
    det_score[has_row] = evidence.det_score[rows]
    det_available[has_row] = True

    # R: a detector node whose evidence resolves in at least one role. A node with neither role
    # valid carries no measured embedding at all and is therefore held fixed.
    reconsiderable = has_row & emb_src_valid & emb_tgt_valid

    nodes_by_t: dict[int, list[int]] = {}
    for i in range(n):
        nodes_by_t.setdefault(int(graph.node_t[i]), []).append(i)
    nodes_by_t_arr = {t: np.asarray(sorted(v), dtype=np.int64) for t, v in nodes_by_t.items()}

    return NodeTable(
        graph=graph,
        evidence=evidence,
        det_row=det_row,
        reconsiderable=reconsiderable,
        positions_um=graph.positions_um(),
        emb_src=emb_src,
        emb_tgt=emb_tgt,
        emb_src_valid=emb_src_valid,
        emb_tgt_valid=emb_tgt_valid,
        det_score=det_score,
        det_available=det_available,
        nodes_by_t=nodes_by_t_arr,
    )


def origin_counts(graph: FinalGraph) -> dict[str, int]:
    counts: dict[str, int] = {name: 0 for name in schema.ORIGIN_NAMES.values()}
    for origin in graph.node_origin:
        counts[schema.ORIGIN_NAMES[int(origin)]] += 1
    return counts


def iter_transitions(table: NodeTable) -> Iterable[int]:
    """Source frames ``t`` for which a ``t -> t+1`` transition exists, ascending."""
    frames = sorted(table.nodes_by_t)
    return [t for t in frames if (t + 1) in table.nodes_by_t]
