"""Candidate continuation edges and symmetric mother/two-daughter events.

Design points that are load-bearing (codex_challenge_v1 items 3 and 5):

* The exported alternatives come from the **full pre-threshold, pre-cap** probability matrix, so the
  0.48-thresholded ``admitted`` pool is never the coverage source. The word "complete" is not used.
* **Every parent edge of the graph being decoded is unioned in unconditionally**, and **every parent
  fork is represented as an event**, even when geometry or top-k would exclude it. Without this the
  parent assignment could be infeasible and fallback would be the only outcome.
* The parent's *divergence* gate is deliberately **not** applied as a hard filter: it depends on
  successors at ``t+2``, which are themselves decision variables, so enforcing it would couple
  ``t->t+1`` with ``t+1->t+2`` and destroy the exact per-transition decomposition. It is exposed as an
  event feature with an availability flag instead.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations

import numpy as np

from . import schema
from .config import Exp067Config, GenerationConfig
from .provenance import NodeTable


@dataclass
class Hypotheses:
    """Arrays over candidate edges (``e_*``) and candidate division events (``v_*``)."""

    table: NodeTable
    e_src: np.ndarray
    e_tgt: np.ndarray
    e_t: np.ndarray
    e_prob: np.ndarray
    e_prob_avail: np.ndarray
    e_logit: np.ndarray
    e_logit_avail: np.ndarray
    e_origin: np.ndarray
    e_is_parent: np.ndarray
    e_fixed: np.ndarray
    v_src: np.ndarray
    v_a: np.ndarray
    v_b: np.ndarray
    v_t: np.ndarray
    v_is_parent_fork: np.ndarray
    v_geometry_pass: np.ndarray
    v_diverge: np.ndarray
    v_diverge_avail: np.ndarray
    alt_dropped_node_absent: int = 0
    index_of_edge: dict[tuple[int, int], int] = field(default_factory=dict)
    edges_of_source: dict[int, list[int]] = field(default_factory=dict)
    edges_of_target: dict[int, list[int]] = field(default_factory=dict)
    events_of_source: dict[int, list[int]] = field(default_factory=dict)

    @property
    def n_edges(self) -> int:
        return len(self.e_src)

    @property
    def n_events(self) -> int:
        return len(self.v_src)

    def rebuild_index(self) -> None:
        self.index_of_edge = {(int(s), int(t)): k for k, (s, t) in enumerate(zip(self.e_src, self.e_tgt))}
        self.edges_of_source = {}
        self.edges_of_target = {}
        for k, (s, t) in enumerate(zip(self.e_src, self.e_tgt)):
            self.edges_of_source.setdefault(int(s), []).append(k)
            self.edges_of_target.setdefault(int(t), []).append(k)
        self.events_of_source = {}
        for j, u in enumerate(self.v_src):
            self.events_of_source.setdefault(int(u), []).append(j)

    def assert_source_ownership_partition(self) -> None:
        """Each candidate edge is scored exactly once, in the batch owning its source."""
        seen: set[int] = set()
        for source, keys in self.edges_of_source.items():
            for k in keys:
                if k in seen:
                    raise AssertionError(f"edge {k} owned by more than one source")
                seen.add(k)
                if int(self.e_src[k]) != int(source):
                    raise AssertionError(f"edge {k} filed under the wrong source")
        if len(seen) != self.n_edges:
            raise AssertionError(f"ownership covers {len(seen)} of {self.n_edges} edges")


def _det_row_to_node_row(table: NodeTable) -> np.ndarray:
    lookup = np.full(table.evidence.n_rows, -1, dtype=np.int64)
    for node_row, det_row in enumerate(table.det_row):
        if det_row >= 0:
            lookup[det_row] = node_row
    return lookup


def symmetric_event_geometry(
    positions_um: np.ndarray, u: int, a: int, b: int, cfg: GenerationConfig
) -> tuple[bool, float, float, float, float]:
    """Return ``(passes, d_a, d_b, sister, relative_asymmetry)`` with a symmetric gate.

    The parent's own predicates, made symmetric in ``{a, b}``:

    * ``max(d_a, d_b) <= SAFE_DIV_MAX_UM`` — the parent applies 9.0 to the newly proposed daughter and
      10.0 to the existing child, and 9.0 <= 10.0, so this is no looser than the parent in the
      direction that matters (cell 5:1533, 1550);
    * ``d(a, b) <= SAFE_DIV_SISTER_MAX_UM`` (cell 5:1553);
    * relative asymmetry ``|d_a - d_b| / mean(d_a, d_b) <= TAU`` — the parent's own form at
      cell 5:1604-1607, which is already symmetric.
    """
    pu, pa, pb = positions_um[u], positions_um[a], positions_um[b]
    d_a = float(np.linalg.norm(pa - pu))
    d_b = float(np.linalg.norm(pb - pu))
    sister = float(np.linalg.norm(pa - pb))
    denom = max((d_a + d_b) / 2.0, 1e-6)
    asym = abs(d_a - d_b) / denom
    passes = (
        max(d_a, d_b) <= cfg.safe_div_max_um
        and sister <= cfg.safe_div_sister_max_um
        and (cfg.safe_div_sister_symmetry_tau <= 0.0 or asym <= cfg.safe_div_sister_symmetry_tau)
    )
    return passes, d_a, d_b, sister, asym


def generate(table: NodeTable, config: Exp067Config | None = None) -> Hypotheses:
    """Build the hypothesis set for a whole movie, deterministically."""
    config = config or Exp067Config()
    cfg = config.generation
    positions = table.positions_um
    node_t = table.graph.node_t
    node_id = table.graph.node_id
    reconsiderable = table.reconsiderable
    row_of_node = table.graph.row_of_node

    parent_pairs: list[tuple[int, int]] = []
    for s, t in zip(table.graph.edge_src, table.graph.edge_tgt):
        parent_pairs.append((row_of_node[int(s)], row_of_node[int(t)]))
    parent_set = set(parent_pairs)

    det_to_row = _det_row_to_node_row(table)
    dropped = 0

    # ---- alternatives from the export, mapped into node-row space -------------------------
    alt: dict[tuple[int, int], tuple[float, float, int]] = {}
    ev = table.evidence
    for i in range(ev.n_alternatives):
        sr, tr = int(ev.alt_src_row[i]), int(ev.alt_tgt_row[i])
        if not (0 <= sr < len(det_to_row) and 0 <= tr < len(det_to_row)):
            dropped += 1
            continue
        s_row, t_row = int(det_to_row[sr]), int(det_to_row[tr])
        if s_row < 0 or t_row < 0:
            dropped += 1  # the detection was pruned out of the final graph; expected, counted
            continue
        if int(node_t[t_row]) != int(node_t[s_row]) + 1:
            dropped += 1
            continue
        key = (s_row, t_row)
        prob, logit, origin = float(ev.alt_prob[i]), float(ev.alt_logit[i]), int(ev.alt_origin[i])
        if key in alt:
            prev = alt[key]
            alt[key] = (max(prev[0], prob), max(prev[1], logit), prev[2] | origin)
        else:
            alt[key] = (prob, logit, origin)

    # ---- per-transition selection ---------------------------------------------------------
    chosen: dict[tuple[int, int], tuple[float, float, int, bool]] = {}
    per_source_count: dict[int, int] = {}

    def admit(key: tuple[int, int], prob: float, logit: float, origin: int, has_model: bool) -> None:
        prev = chosen.get(key)
        if prev is None:
            chosen[key] = (prob, logit, origin, has_model)
            per_source_count[key[0]] = per_source_count.get(key[0], 0) + 1
            return
        p_prob, p_logit, p_origin, p_has = prev
        if has_model and p_has:
            merged = (max(p_prob, prob), max(p_logit, logit))
        elif has_model:
            merged = (prob, logit)
        else:
            merged = (p_prob, p_logit)
        chosen[key] = (merged[0], merged[1], p_origin | origin, p_has or has_model)

    frames = sorted(table.nodes_by_t)
    transitions = [t for t in frames if (t + 1) in table.nodes_by_t]

    by_transition: dict[int, list[tuple[int, int]]] = {t: [] for t in transitions}
    for key in alt:
        t = int(node_t[key[0]])
        if t in by_transition:
            by_transition[t].append(key)

    for t in transitions:
        keys = by_transition[t]
        # cap per source, then per target, deterministically by (-logit, target node id)
        per_source: dict[int, list[tuple[int, int]]] = {}
        for key in keys:
            per_source.setdefault(key[0], []).append(key)
        kept: set[tuple[int, int]] = set()
        for s_row, group in per_source.items():
            if not reconsiderable[s_row]:
                continue
            group.sort(key=lambda k: (-alt[k][1], int(node_id[k[1]])))
            for key in group[: cfg.max_alt_per_source]:
                if reconsiderable[key[1]]:
                    kept.add(key)
        per_target: dict[int, list[tuple[int, int]]] = {}
        for key in keys:
            per_target.setdefault(key[1], []).append(key)
        for t_row, group in per_target.items():
            if not reconsiderable[t_row]:
                continue
            group.sort(key=lambda k: (-alt[k][1], int(node_id[k[0]])))
            for key in group[: cfg.max_alt_per_target]:
                if reconsiderable[key[0]]:
                    kept.add(key)
        for key in sorted(kept, key=lambda k: (int(node_id[k[0]]), int(node_id[k[1]]))):
            prob, logit, origin = alt[key]
            admit(key, prob, logit, origin, True)

        # geometric fallback for R-sources with too little learned coverage
        src_rows = [int(r) for r in table.nodes_by_t[t] if reconsiderable[r]]
        tgt_rows = np.asarray([int(r) for r in table.nodes_by_t[t + 1] if reconsiderable[r]], dtype=np.int64)
        if cfg.n_geometric > 0 and len(tgt_rows):
            thin = [
                r for r in src_rows
                if per_source_count.get(r, 0) < cfg.min_alternatives_per_source
            ]
            if thin:
                from scipy.spatial import cKDTree

                tree = cKDTree(positions[tgt_rows])
                k = int(min(cfg.n_geometric, len(tgt_rows)))
                dist, idx = tree.query(positions[thin], k=k)
                dist = np.asarray(dist).reshape(len(thin), k)
                idx = np.asarray(idx).reshape(len(thin), k)
                for row_pos, s_row in enumerate(thin):
                    order = sorted(
                        range(dist.shape[1]),
                        key=lambda c: (float(dist[row_pos, c]), int(node_id[tgt_rows[idx[row_pos, c]]])),
                    )
                    for c in order:
                        if float(dist[row_pos, c]) > cfg.max_edge_um:
                            continue
                        t_row = int(tgt_rows[idx[row_pos, c]])
                        admit((s_row, t_row), 0.0, 0.0, schema.ALT_ORIGIN_GEOMETRIC, False)

    # ---- parent edges, unioned in unconditionally -----------------------------------------
    # A parent edge enters whether or not it survived any threshold, top-k or geometry rule; if the
    # export happens to carry it too, ``admit`` keeps the model evidence and ORs the origin flag.
    for key in parent_pairs:
        admit(key, 0.0, 0.0, schema.ALT_ORIGIN_PARENT, False)

    # ---- materialise edge arrays ----------------------------------------------------------
    keys_sorted = sorted(chosen, key=lambda k: (int(node_t[k[0]]), int(node_id[k[0]]), int(node_id[k[1]])))
    n = len(keys_sorted)
    e_src = np.zeros(n, dtype=np.int64)
    e_tgt = np.zeros(n, dtype=np.int64)
    e_t = np.zeros(n, dtype=np.int64)
    e_prob = np.zeros(n, dtype=np.float64)
    e_prob_avail = np.zeros(n, dtype=bool)
    e_logit = np.zeros(n, dtype=np.float64)
    e_logit_avail = np.zeros(n, dtype=bool)
    e_origin = np.zeros(n, dtype=np.int16)
    e_is_parent = np.zeros(n, dtype=bool)
    e_fixed = np.zeros(n, dtype=bool)
    for k, key in enumerate(keys_sorted):
        prob, logit, origin, has_model = chosen[key]
        e_src[k], e_tgt[k] = key
        e_t[k] = int(node_t[key[0]])
        e_origin[k] = origin
        e_is_parent[k] = key in parent_set
        e_prob_avail[k] = has_model
        e_logit_avail[k] = has_model
        e_prob[k] = prob if has_model else 0.0
        e_logit[k] = logit if has_model else 0.0
        both_r = bool(reconsiderable[key[0]] and reconsiderable[key[1]])
        e_fixed[k] = bool(e_is_parent[k] and not both_r)

    hyp = Hypotheses(
        table=table,
        e_src=e_src, e_tgt=e_tgt, e_t=e_t,
        e_prob=e_prob, e_prob_avail=e_prob_avail,
        e_logit=e_logit, e_logit_avail=e_logit_avail,
        e_origin=e_origin, e_is_parent=e_is_parent, e_fixed=e_fixed,
        v_src=np.zeros(0, dtype=np.int64), v_a=np.zeros(0, dtype=np.int64),
        v_b=np.zeros(0, dtype=np.int64), v_t=np.zeros(0, dtype=np.int64),
        v_is_parent_fork=np.zeros(0, dtype=bool), v_geometry_pass=np.zeros(0, dtype=bool),
        v_diverge=np.zeros(0, dtype=np.float64), v_diverge_avail=np.zeros(0, dtype=bool),
        alt_dropped_node_absent=dropped,
    )
    hyp.rebuild_index()
    _generate_events(hyp, cfg, parent_pairs)
    hyp.rebuild_index()
    hyp.assert_source_ownership_partition()
    return hyp


def _parent_successor_map(table: NodeTable) -> dict[int, list[int]]:
    row_of_node = table.graph.row_of_node
    successors: dict[int, list[int]] = {}
    for s, t in zip(table.graph.edge_src, table.graph.edge_tgt):
        successors.setdefault(row_of_node[int(s)], []).append(row_of_node[int(t)])
    return successors


def _generate_events(hyp: Hypotheses, cfg: GenerationConfig, parent_pairs: list[tuple[int, int]]) -> None:
    table = hyp.table
    positions = table.positions_um
    node_t = table.graph.node_t
    node_id = table.graph.node_id
    successors = _parent_successor_map(table)

    parent_forks: dict[int, tuple[int, int]] = {}
    by_source: dict[int, list[int]] = {}
    for s, t in parent_pairs:
        by_source.setdefault(s, []).append(t)
    for s, targets in by_source.items():
        if len(targets) >= 2:
            ordered = sorted(targets, key=lambda r: int(node_id[r]))
            parent_forks[s] = (ordered[0], ordered[1])

    records: dict[tuple[int, int, int], tuple[bool, float, bool]] = {}

    def diverge_stat(a: int, b: int, sister: float) -> tuple[float, bool]:
        succ_a, succ_b = successors.get(a, []), successors.get(b, [])
        if len(succ_a) != 1 or len(succ_b) != 1:
            return 0.0, False
        ga, gb = succ_a[0], succ_b[0]
        if int(node_t[ga]) != int(node_t[a]) + 1 or int(node_t[gb]) != int(node_t[b]) + 1:
            return 0.0, False
        return float(np.linalg.norm(positions[ga] - positions[gb])) - sister, True

    for source, edge_keys in hyp.edges_of_source.items():
        if not table.reconsiderable[source]:
            continue
        targets = sorted({int(hyp.e_tgt[k]) for k in edge_keys}, key=lambda r: int(node_id[r]))
        scored: list[tuple[float, int, int, bool, float]] = []
        for a, b in combinations(targets, 2):
            passes, d_a, d_b, sister, _asym = symmetric_event_geometry(positions, source, a, b, cfg)
            if cfg.event_require_geometry and not passes:
                continue
            scored.append((max(d_a, d_b) + 0.15 * sister, a, b, passes, sister))
        scored.sort(key=lambda item: (item[0], int(node_id[item[1]]), int(node_id[item[2]])))
        for _score, a, b, passes, sister in scored[: cfg.max_events_per_source]:
            value, avail = diverge_stat(a, b, sister)
            records[(source, a, b)] = (passes, value, avail)

    # Every parent fork gets an event, unconditionally (item 5).
    for source, (a, b) in parent_forks.items():
        key = (source, a, b)
        if key in records:
            continue
        passes, _d_a, _d_b, sister, _asym = symmetric_event_geometry(positions, source, a, b, cfg)
        value, avail = diverge_stat(a, b, sister)
        records[key] = (passes, value, avail)

    keys = sorted(records, key=lambda k: (int(node_t[k[0]]), int(node_id[k[0]]), int(node_id[k[1]]), int(node_id[k[2]])))
    m = len(keys)
    hyp.v_src = np.asarray([k[0] for k in keys], dtype=np.int64)
    hyp.v_a = np.asarray([k[1] for k in keys], dtype=np.int64)
    hyp.v_b = np.asarray([k[2] for k in keys], dtype=np.int64)
    hyp.v_t = np.asarray([int(node_t[k[0]]) for k in keys], dtype=np.int64)
    hyp.v_is_parent_fork = np.asarray(
        [(k[0] in parent_forks and parent_forks[k[0]] == (k[1], k[2])) for k in keys], dtype=bool
    )
    hyp.v_geometry_pass = np.asarray([records[k][0] for k in keys], dtype=bool)
    hyp.v_diverge = np.asarray([records[k][1] for k in keys], dtype=np.float64)
    hyp.v_diverge_avail = np.asarray([records[k][2] for k in keys], dtype=bool)
    if m == 0:
        for name in ("v_src", "v_a", "v_b", "v_t"):
            setattr(hyp, name, np.zeros(0, dtype=np.int64))
        for name in ("v_is_parent_fork", "v_geometry_pass", "v_diverge_avail"):
            setattr(hyp, name, np.zeros(0, dtype=bool))
        hyp.v_diverge = np.zeros(0, dtype=np.float64)
