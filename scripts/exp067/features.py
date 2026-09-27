"""Window assembly and the feature contract.

codex_challenge_v1 item 4: the window builder **guarantees** that every scored edge's endpoints and
both daughters of every scored event are tokens. Assembly order is therefore:

1. required tokens — batch sources, their candidate targets, both daughters of their events;
2. deterministic batch splitting when the required union would exceed ``required_cap``;
3. optional context, nearest-first, only with the capacity that remains.

A single source whose own required set exceeds ``required_cap`` raises :class:`Exp067WindowOverflow`.
An event that cannot fit fails; it is never silently dropped.

Missing-feature policy: a feature the schema declares **mandatory** raises
:class:`Exp067FeatureUnavailable`. Features that are legitimately absent for a whole class of node or
edge (no source-role embedding at the last frame, no model probability for a geometric alternative,
no divergence statistic without ``t+2`` successors) carry an explicit availability bit and a value the
mask multiplies out. There are no random and no zero stand-ins for mandatory features.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import schema
from .config import Exp067Config, WindowConfig
from .errors import Exp067FeatureUnavailable, Exp067WindowOverflow
from .hypotheses import Hypotheses, symmetric_event_geometry
from .provenance import NodeTable

TOKEN_SCALAR_SPEC: tuple[tuple[str, str], ...] = (
    ("emb_src_valid", "flag"),
    ("emb_tgt_valid", "flag"),
    ("dz_um", "um"),
    ("dy_um", "um"),
    ("dx_um", "um"),
    ("r_um", "um"),
    ("dt_frames", "frames"),
    ("dt_sin_1", "unit"), ("dt_cos_1", "unit"),
    ("dt_sin_2", "unit"), ("dt_cos_2", "unit"),
    ("dt_sin_3", "unit"), ("dt_cos_3", "unit"),
    ("det_score", "probability"),
    ("det_available", "flag"),
    ("origin_detector", "flag"),
    ("origin_readmitted", "flag"),
    ("origin_synthetic", "flag"),
    ("has_parent_in", "flag"),
    ("parent_out_degree", "count"),
    ("is_required", "flag"),
    ("is_batch_source", "flag"),
    ("is_candidate_target", "flag"),
    ("parent_in_logit", "logit"),
    ("parent_in_logit_available", "flag"),
    ("best_alt_logit", "logit"),
    ("best_alt_logit_available", "flag"),
    ("disagreement_logit", "logit"),
    ("disagreement_available", "flag"),
)

EDGE_FEATURE_SPEC: tuple[tuple[str, str], ...] = (
    ("dist_um", "um"),
    ("dz_um", "um"), ("dy_um", "um"), ("dx_um", "um"),
    ("alt_logit", "logit"), ("alt_logit_available", "flag"),
    ("alt_prob", "probability"), ("alt_prob_available", "flag"),
    ("origin_row_topk", "flag"), ("origin_col_topk", "flag"),
    ("origin_geometric", "flag"), ("origin_parent", "flag"),
    ("is_parent_edge", "flag"),
    ("target_has_parent_in", "flag"),
    ("target_parent_is_other_source", "flag"),
    ("rank_from_source", "unit"),
    ("rank_to_target", "unit"),
)

EVENT_FEATURE_SPEC: tuple[tuple[str, str], ...] = (
    ("d_sum_um", "um"),
    ("d_absdiff_um", "um"),
    ("d_max_um", "um"),
    ("sister_um", "um"),
    ("relative_asymmetry", "unit"),
    ("geometry_pass", "flag"),
    ("diverge_um", "um"), ("diverge_available", "flag"),
    ("n_occupied_targets", "count"),
    ("is_parent_fork", "flag"),
    ("both_edges_parent", "flag"),
)

N_TOKEN_SCALARS = len(TOKEN_SCALAR_SPEC)
N_EDGE_FEATURES = len(EDGE_FEATURE_SPEC)
N_EVENT_FEATURES = len(EVENT_FEATURE_SPEC)

_DT_FREQS = (1.0, 2.0, 4.0)


def feature_spec_fingerprint(emb_channels: int) -> dict[str, object]:
    """Stored in the checkpoint; ``infer`` refuses to run on a mismatch, field by field."""
    return {
        "emb_channels": int(emb_channels),
        "token_scalars": [list(pair) for pair in TOKEN_SCALAR_SPEC],
        "edge_features": [list(pair) for pair in EDGE_FEATURE_SPEC],
        "event_features": [list(pair) for pair in EVENT_FEATURE_SPEC],
        "export_schema_version": schema.EXPORT_SCHEMA_VERSION,
    }


def token_dim(emb_channels: int) -> int:
    return 2 * emb_channels + N_TOKEN_SCALARS


# --------------------------------------------------------------------- per-movie derived arrays

@dataclass
class MovieContext:
    """Node- and edge-level quantities shared by every window of one movie."""

    has_parent_in: np.ndarray
    parent_out_degree: np.ndarray
    parent_source_of: np.ndarray  # target row -> parent source row, -1 when none
    parent_in_logit: np.ndarray
    parent_in_logit_avail: np.ndarray
    best_alt_logit: np.ndarray
    best_alt_logit_avail: np.ndarray
    rank_from_source: np.ndarray  # per edge
    rank_to_target: np.ndarray  # per edge
    free_edge: np.ndarray  # per edge: a decision variable rather than a constant
    scored_event: np.ndarray  # per event: at least one member edge is free


def build_movie_context(hyp: Hypotheses) -> MovieContext:
    table = hyp.table
    n = table.n_nodes
    has_parent_in = np.zeros(n, dtype=bool)
    parent_out_degree = np.zeros(n, dtype=np.float64)
    parent_source_of = np.full(n, -1, dtype=np.int64)
    row_of_node = table.graph.row_of_node
    for s, t in zip(table.graph.edge_src, table.graph.edge_tgt):
        sr, tr = row_of_node[int(s)], row_of_node[int(t)]
        has_parent_in[tr] = True
        parent_source_of[tr] = sr
        parent_out_degree[sr] += 1.0

    parent_in_logit = np.zeros(n, dtype=np.float64)
    parent_in_logit_avail = np.zeros(n, dtype=bool)
    best_alt_logit = np.zeros(n, dtype=np.float64)
    best_alt_logit_avail = np.zeros(n, dtype=bool)
    for k in range(hyp.n_edges):
        tgt = int(hyp.e_tgt[k])
        if not hyp.e_logit_avail[k]:
            continue
        value = float(hyp.e_logit[k])
        if not best_alt_logit_avail[tgt] or value > best_alt_logit[tgt]:
            best_alt_logit[tgt] = value
            best_alt_logit_avail[tgt] = True
        if hyp.e_is_parent[k]:
            parent_in_logit[tgt] = value
            parent_in_logit_avail[tgt] = True

    rank_from_source = np.zeros(hyp.n_edges, dtype=np.float64)
    rank_to_target = np.zeros(hyp.n_edges, dtype=np.float64)
    node_id = table.graph.node_id
    for group in (hyp.edges_of_source, hyp.edges_of_target):
        is_source_group = group is hyp.edges_of_source
        for keys in group.values():
            ordered = sorted(
                keys,
                key=lambda k: (
                    -float(hyp.e_logit[k]) if hyp.e_logit_avail[k] else float("inf"),
                    int(node_id[int(hyp.e_tgt[k])] if is_source_group else node_id[int(hyp.e_src[k])]),
                ),
            )
            denom = max(len(ordered) - 1, 1)
            for rank, k in enumerate(ordered):
                if is_source_group:
                    rank_from_source[k] = rank / denom
                else:
                    rank_to_target[k] = rank / denom

    free_edge = ~hyp.e_fixed
    scored_event = np.zeros(hyp.n_events, dtype=bool)
    for j in range(hyp.n_events):
        u, a, b = int(hyp.v_src[j]), int(hyp.v_a[j]), int(hyp.v_b[j])
        ka = hyp.index_of_edge.get((u, a))
        kb = hyp.index_of_edge.get((u, b))
        scored_event[j] = bool(
            (ka is not None and free_edge[ka]) or (kb is not None and free_edge[kb])
        )

    return MovieContext(
        has_parent_in=has_parent_in,
        parent_out_degree=parent_out_degree,
        parent_source_of=parent_source_of,
        parent_in_logit=parent_in_logit,
        parent_in_logit_avail=parent_in_logit_avail,
        best_alt_logit=best_alt_logit,
        best_alt_logit_avail=best_alt_logit_avail,
        rank_from_source=rank_from_source,
        rank_to_target=rank_to_target,
        free_edge=free_edge,
        scored_event=scored_event,
    )


# ----------------------------------------------------------------------------- window batches

@dataclass
class WindowBatch:
    t: int
    token_rows: np.ndarray
    tokens: np.ndarray
    pad_mask: np.ndarray
    edge_keys: np.ndarray
    edge_local: np.ndarray
    edge_feats: np.ndarray
    event_keys: np.ndarray
    event_local: np.ndarray
    event_feats: np.ndarray
    n_required: int
    n_context: int

    @property
    def n_tokens(self) -> int:
        return len(self.token_rows)


def _required_rows_for_source(
    hyp: Hypotheses, ctx: MovieContext, source: int
) -> tuple[list[int], list[int], list[int]]:
    """``(rows, edge_keys, event_keys)`` this one source obliges the window to carry."""
    edge_keys = [k for k in hyp.edges_of_source.get(source, []) if ctx.free_edge[k]]
    event_keys = [j for j in hyp.events_of_source.get(source, []) if ctx.scored_event[j]]
    rows = {source}
    for k in edge_keys:
        rows.add(int(hyp.e_tgt[k]))
    for j in event_keys:
        rows.add(int(hyp.v_a[j]))
        rows.add(int(hyp.v_b[j]))
    return sorted(rows), edge_keys, event_keys


def plan_batches(hyp: Hypotheses, ctx: MovieContext, cfg: WindowConfig) -> list[dict]:
    """Deterministic source batching. Required endpoints decide the split, context never does."""
    table = hyp.table
    node_id = table.graph.node_id
    plans: list[dict] = []
    for t in sorted({int(v) for v in hyp.e_t}):
        sources = sorted(
            {int(hyp.e_src[k]) for k in range(hyp.n_edges) if int(hyp.e_t[k]) == t and ctx.free_edge[k]},
            key=lambda r: int(node_id[r]),
        )
        current: dict | None = None
        for source in sources:
            rows, edge_keys, event_keys = _required_rows_for_source(hyp, ctx, source)
            if not edge_keys and not event_keys:
                continue
            if len(rows) > cfg.required_cap:
                raise Exp067WindowOverflow(
                    f"{table.graph.dataset}: source node {int(node_id[source])} at t={t} requires "
                    f"{len(rows)} tokens, above required_cap={cfg.required_cap}; an event that cannot "
                    "fit must fail rather than be dropped"
                )
            if current is not None:
                merged = current["rows"] | set(rows)
                too_big = len(merged) > cfg.required_cap
                too_many = len(current["sources"]) + 1 > cfg.max_sources_per_batch
                if too_big or too_many:
                    plans.append(current)
                    current = None
            if current is None:
                current = {"t": t, "rows": set(), "sources": [], "edge_keys": [], "event_keys": []}
            current["rows"].update(rows)
            current["sources"].append(source)
            current["edge_keys"].extend(edge_keys)
            current["event_keys"].extend(event_keys)
        if current is not None:
            plans.append(current)
    return plans


def _context_rows(
    table: NodeTable, t: int, anchor_um: np.ndarray, present: set[int], budget: int, cfg: WindowConfig
) -> list[int]:
    """Nearest optional context, frame by frame, filled only after the required set."""
    if budget <= 0:
        return []
    node_id = table.graph.node_id
    picked: list[int] = []
    for frame in range(t - cfg.half_span, t + cfg.half_span + 1):
        rows = table.nodes_by_t.get(frame)
        if rows is None:
            continue
        pool = [int(r) for r in rows if int(r) not in present and table.reconsiderable[r]]
        if not pool:
            continue
        distances = np.linalg.norm(table.positions_um[pool] - anchor_um[None, :], axis=1)
        order = sorted(range(len(pool)), key=lambda i: (float(distances[i]), int(node_id[pool[i]])))
        for i in order[: cfg.context_per_frame]:
            if len(picked) >= budget:
                return picked
            picked.append(pool[i])
            present.add(pool[i])
    return picked


def build_batch(
    hyp: Hypotheses, ctx: MovieContext, plan: dict, config: Exp067Config
) -> WindowBatch:
    cfg = config.window
    table = hyp.table
    required = sorted(plan["rows"])
    anchor = table.positions_um[plan["sources"]].mean(axis=0)
    present = set(required)
    context = _context_rows(table, plan["t"], anchor, present, cfg.total_cap - len(required), cfg)
    token_rows = np.asarray(required + context, dtype=np.int64)
    local_of_row = {int(r): i for i, r in enumerate(token_rows)}

    tokens = _token_features(
        hyp, ctx, token_rows, plan, anchor, n_required=len(required)
    )

    edge_keys = np.asarray(sorted(set(plan["edge_keys"])), dtype=np.int64)
    edge_local = np.asarray(
        [[local_of_row[int(hyp.e_src[k])], local_of_row[int(hyp.e_tgt[k])]] for k in edge_keys],
        dtype=np.int64,
    ).reshape(len(edge_keys), 2)
    edge_feats = _edge_features(hyp, ctx, edge_keys)

    event_keys = np.asarray(sorted(set(plan["event_keys"])), dtype=np.int64)
    event_local = np.asarray(
        [
            [local_of_row[int(hyp.v_src[j])], local_of_row[int(hyp.v_a[j])], local_of_row[int(hyp.v_b[j])]]
            for j in event_keys
        ],
        dtype=np.int64,
    ).reshape(len(event_keys), 3)
    event_feats = _event_features(hyp, ctx, event_keys, config)

    return WindowBatch(
        t=int(plan["t"]),
        token_rows=token_rows,
        tokens=tokens,
        pad_mask=np.zeros(len(token_rows), dtype=bool),
        edge_keys=edge_keys,
        edge_local=edge_local,
        edge_feats=edge_feats,
        event_keys=event_keys,
        event_local=event_local,
        event_feats=event_feats,
        n_required=len(required),
        n_context=len(context),
    )


def _token_features(
    hyp: Hypotheses,
    ctx: MovieContext,
    token_rows: np.ndarray,
    plan: dict,
    anchor_um: np.ndarray,
    n_required: int,
) -> np.ndarray:
    table = hyp.table
    rows = token_rows
    channels = table.evidence.emb_channels
    if channels <= 0:
        raise Exp067FeatureUnavailable(
            f"{table.graph.dataset}: the export carries no embedding channels; backbone features are "
            "mandatory and there is no substitute"
        )

    emb_src = table.emb_src[rows]
    emb_tgt = table.emb_tgt[rows]
    if emb_src.shape[1] != channels or emb_tgt.shape[1] != channels:
        raise Exp067FeatureUnavailable(
            f"{table.graph.dataset}: embedding width {emb_src.shape[1]}/{emb_tgt.shape[1]} "
            f"disagrees with the manifest ({channels})"
        )
    emb_src = emb_src * table.emb_src_valid[rows][:, None]
    emb_tgt = emb_tgt * table.emb_tgt_valid[rows][:, None]

    delta = table.positions_um[rows] - anchor_um[None, :]
    radius = np.linalg.norm(delta, axis=1)
    dt = (table.graph.node_t[rows] - int(plan["t"])).astype(np.float64)

    source_set = set(int(r) for r in plan["sources"])
    target_set = {int(hyp.e_tgt[k]) for k in plan["edge_keys"]}
    for j in plan["event_keys"]:
        target_set.add(int(hyp.v_a[j]))
        target_set.add(int(hyp.v_b[j]))

    scalars = np.zeros((len(rows), N_TOKEN_SCALARS), dtype=np.float64)
    scalars[:, 0] = table.emb_src_valid[rows]
    scalars[:, 1] = table.emb_tgt_valid[rows]
    scalars[:, 2:5] = delta
    scalars[:, 5] = radius
    scalars[:, 6] = dt
    column = 7
    for freq in _DT_FREQS:
        scalars[:, column] = np.sin(dt * freq * np.pi / (2 * 3))
        scalars[:, column + 1] = np.cos(dt * freq * np.pi / (2 * 3))
        column += 2
    scalars[:, 13] = table.det_score[rows] * table.det_available[rows]
    scalars[:, 14] = table.det_available[rows]
    origin = table.graph.node_origin[rows]
    scalars[:, 15] = origin == schema.ORIGIN_DETECTOR
    scalars[:, 16] = origin == schema.ORIGIN_READMITTED
    scalars[:, 17] = origin == schema.ORIGIN_SYNTHETIC
    scalars[:, 18] = ctx.has_parent_in[rows]
    scalars[:, 19] = ctx.parent_out_degree[rows]
    scalars[:, 20] = np.arange(len(rows)) < n_required
    scalars[:, 21] = [int(r) in source_set for r in rows]
    scalars[:, 22] = [int(r) in target_set for r in rows]
    scalars[:, 23] = ctx.parent_in_logit[rows] * ctx.parent_in_logit_avail[rows]
    scalars[:, 24] = ctx.parent_in_logit_avail[rows]
    scalars[:, 25] = ctx.best_alt_logit[rows] * ctx.best_alt_logit_avail[rows]
    scalars[:, 26] = ctx.best_alt_logit_avail[rows]
    both = ctx.parent_in_logit_avail[rows] & ctx.best_alt_logit_avail[rows]
    scalars[:, 27] = (ctx.best_alt_logit[rows] - ctx.parent_in_logit[rows]) * both
    scalars[:, 28] = both

    out = np.concatenate([emb_src, emb_tgt, scalars], axis=1).astype(np.float32)
    if not np.isfinite(out).all():
        raise Exp067FeatureUnavailable(f"{table.graph.dataset}: non-finite token feature produced")
    return out


def _edge_features(hyp: Hypotheses, ctx: MovieContext, edge_keys: np.ndarray) -> np.ndarray:
    table = hyp.table
    out = np.zeros((len(edge_keys), N_EDGE_FEATURES), dtype=np.float64)
    for i, k in enumerate(edge_keys):
        u, v = int(hyp.e_src[k]), int(hyp.e_tgt[k])
        delta = table.positions_um[v] - table.positions_um[u]
        origin = int(hyp.e_origin[k])
        parent_source = int(ctx.parent_source_of[v])
        out[i] = (
            float(np.linalg.norm(delta)),
            delta[0], delta[1], delta[2],
            float(hyp.e_logit[k]) * bool(hyp.e_logit_avail[k]), float(bool(hyp.e_logit_avail[k])),
            float(hyp.e_prob[k]) * bool(hyp.e_prob_avail[k]), float(bool(hyp.e_prob_avail[k])),
            float(bool(origin & schema.ALT_ORIGIN_ROW_TOPK)),
            float(bool(origin & schema.ALT_ORIGIN_COL_TOPK)),
            float(bool(origin & schema.ALT_ORIGIN_GEOMETRIC)),
            float(bool(origin & schema.ALT_ORIGIN_PARENT)),
            float(bool(hyp.e_is_parent[k])),
            float(bool(ctx.has_parent_in[v])),
            float(parent_source >= 0 and parent_source != u),
            float(ctx.rank_from_source[k]),
            float(ctx.rank_to_target[k]),
        )
    if not np.isfinite(out).all():
        raise Exp067FeatureUnavailable("non-finite edge feature produced")
    return out.astype(np.float32)


def _event_features(
    hyp: Hypotheses, ctx: MovieContext, event_keys: np.ndarray, config: Exp067Config
) -> np.ndarray:
    table = hyp.table
    positions = table.positions_um
    out = np.zeros((len(event_keys), N_EVENT_FEATURES), dtype=np.float64)
    for i, j in enumerate(event_keys):
        u, a, b = int(hyp.v_src[j]), int(hyp.v_a[j]), int(hyp.v_b[j])
        _passes, d_a, d_b, sister, asym = symmetric_event_geometry(positions, u, a, b, config.generation)
        ka = hyp.index_of_edge.get((u, a))
        kb = hyp.index_of_edge.get((u, b))
        both_parent = bool(
            ka is not None and kb is not None and hyp.e_is_parent[ka] and hyp.e_is_parent[kb]
        )
        occupied = float(bool(ctx.has_parent_in[a])) + float(bool(ctx.has_parent_in[b]))
        out[i] = (
            d_a + d_b,
            abs(d_a - d_b),
            max(d_a, d_b),
            sister,
            asym,
            float(bool(hyp.v_geometry_pass[j])),
            float(hyp.v_diverge[j]) * bool(hyp.v_diverge_avail[j]),
            float(bool(hyp.v_diverge_avail[j])),
            occupied,
            float(bool(hyp.v_is_parent_fork[j])),
            float(both_parent),
        )
    if not np.isfinite(out).all():
        raise Exp067FeatureUnavailable("non-finite event feature produced")
    return out.astype(np.float32)


def build_batches(hyp: Hypotheses, config: Exp067Config | None = None) -> tuple[list[WindowBatch], MovieContext]:
    config = config or Exp067Config()
    ctx = build_movie_context(hyp)
    plans = plan_batches(hyp, ctx, config.window)
    batches = [build_batch(hyp, ctx, plan, config) for plan in plans]
    _assert_batch_coverage(hyp, ctx, batches)
    return batches, ctx


def _assert_batch_coverage(hyp: Hypotheses, ctx: MovieContext, batches: list[WindowBatch]) -> None:
    """Every free edge and every scored event is covered exactly once, with its endpoints present."""
    seen_edges: set[int] = set()
    seen_events: set[int] = set()
    for batch in batches:
        rows = set(int(r) for r in batch.token_rows)
        for k in batch.edge_keys:
            k = int(k)
            if k in seen_edges:
                raise AssertionError(f"edge {k} scored in more than one window")
            seen_edges.add(k)
            if int(hyp.e_src[k]) not in rows or int(hyp.e_tgt[k]) not in rows:
                raise AssertionError(f"edge {k} scored without both endpoints in its window")
        for j in batch.event_keys:
            j = int(j)
            if j in seen_events:
                raise AssertionError(f"event {j} scored in more than one window")
            seen_events.add(j)
            for row in (int(hyp.v_src[j]), int(hyp.v_a[j]), int(hyp.v_b[j])):
                if row not in rows:
                    raise AssertionError(f"event {j} scored without all three members in its window")
    expected_edges = {k for k in range(hyp.n_edges) if ctx.free_edge[k]}
    if seen_edges != expected_edges:
        raise AssertionError(
            f"window coverage missed {len(expected_edges - seen_edges)} free edge(s) and invented "
            f"{len(seen_edges - expected_edges)}"
        )
    expected_events = {j for j in range(hyp.n_events) if ctx.scored_event[j]}
    if seen_events != expected_events:
        raise AssertionError(
            f"window coverage missed {len(expected_events - seen_events)} scored event(s) and invented "
            f"{len(seen_events - expected_events)}"
        )
