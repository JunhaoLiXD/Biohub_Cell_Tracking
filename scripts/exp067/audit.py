"""Graph invariants and incumbent validation. Nothing is accepted before it passes these."""

from __future__ import annotations

from typing import Iterable, Mapping, Sequence

import numpy as np


class Exp067AuditFailure(AssertionError):
    """A graph or an incumbent violated a stated invariant."""


def assert_node_set_preserved(before: Iterable[int], after: Iterable[int]) -> None:
    """exp_067 may not add, delete or rename a node (codex_challenge_v1 item 2)."""
    before_set = set(int(v) for v in before)
    after_set = set(int(v) for v in after)
    if before_set != after_set:
        added = sorted(after_set - before_set)[:8]
        removed = sorted(before_set - after_set)[:8]
        raise Exp067AuditFailure(
            f"node set changed: {len(after_set - before_set)} added {added}, "
            f"{len(before_set - after_set)} removed {removed}"
        )


def assert_coordinates_preserved(
    before: Mapping[int, tuple[float, float, float]], after: Mapping[int, tuple[float, float, float]]
) -> None:
    for node_id, position in before.items():
        moved = after.get(node_id)
        if moved is None:
            raise Exp067AuditFailure(f"node {node_id} vanished during decode")
        if not np.allclose(np.asarray(position), np.asarray(moved), rtol=0.0, atol=0.0):
            raise Exp067AuditFailure(f"node {node_id} coordinates changed during decode")


def audit_graph(
    node_t: Mapping[int, int], edges: Sequence[tuple[int, int]], max_out_degree: int = 2
) -> dict[str, object]:
    """Full structural audit of an emitted graph. Raises on any hard violation."""
    in_degree: dict[int, int] = {}
    out_degree: dict[int, int] = {}
    dangling = 0
    non_adjacent = 0
    duplicates = 0
    seen: set[tuple[int, int]] = set()

    for source, target in edges:
        source, target = int(source), int(target)
        if source not in node_t or target not in node_t:
            dangling += 1
            continue
        if (source, target) in seen:
            duplicates += 1
        seen.add((source, target))
        if int(node_t[target]) != int(node_t[source]) + 1:
            non_adjacent += 1
        in_degree[target] = in_degree.get(target, 0) + 1
        out_degree[source] = out_degree.get(source, 0) + 1

    if dangling:
        raise Exp067AuditFailure(f"{dangling} dangling edge endpoint(s)")
    if duplicates:
        raise Exp067AuditFailure(f"{duplicates} duplicate edge(s)")
    if non_adjacent:
        raise Exp067AuditFailure(f"{non_adjacent} non-adjacent edge(s): a skip or a backwards link")
    bad_in = [n for n, d in in_degree.items() if d > 1]
    if bad_in:
        raise Exp067AuditFailure(f"{len(bad_in)} node(s) with in-degree > 1, first {bad_in[:8]}")
    bad_out = [n for n, d in out_degree.items() if d > max_out_degree]
    if bad_out:
        raise Exp067AuditFailure(
            f"{len(bad_out)} node(s) with out-degree > {max_out_degree}, first {bad_out[:8]}"
        )

    forks = sorted(n for n, d in out_degree.items() if d >= 2)
    components = _weak_components(list(node_t), list(seen))
    sizes: dict[int, int] = {}
    for root in components.values():
        sizes[root] = sizes.get(root, 0) + 1
    return {
        "n_nodes": len(node_t),
        "n_edges": len(seen),
        "n_forks": len(forks),
        "n_components": len(sizes),
        "largest_component": max(sizes.values()) if sizes else 0,
        "n_isolated": sum(1 for n in node_t if n not in in_degree and n not in out_degree),
        "adjacency_violations": 0,
        "dangling_edges": 0,
        "max_in_degree": max(in_degree.values()) if in_degree else 0,
        "max_out_degree": max(out_degree.values()) if out_degree else 0,
    }


def _weak_components(nodes: Sequence[int], edges: Sequence[tuple[int, int]]) -> dict[int, int]:
    parent = {int(n): int(n) for n in nodes}

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for source, target in edges:
        if source in parent and target in parent:
            a, b = find(source), find(target)
            if a != b:
                parent[a] = b
    return {int(n): find(int(n)) for n in nodes}
