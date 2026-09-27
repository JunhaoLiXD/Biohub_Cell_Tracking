"""Sparse-label supervision, split manifests, and the supervised cache.

The link predicate is the **official scorer's own** false-positive condition restricted to
both-matched pairs (parent cell 8:60-62), so the training mask and the metric agree instead of merely
being compatible:

* both endpoints matched and the GT edge exists            -> POSITIVE
* both matched and (target has a GT parent or source has GT children) -> NEGATIVE
* anything else, including either endpoint unmatched       -> UNKNOWN, zero gradient

The link loss is **per-edge independent** binary cross-entropy, never a softmax over targets. That is
what keeps daughters from being mislabelled: when a matched mother has two matched GT children, both
edges are POSITIVE and neither is pushed to be a negative of the other.

Division labels (codex_challenge_v1 item 1): POSITIVE only on an annotated mother with **both**
daughters matched and both GT edges present; NEGATIVE only when the annotation establishes an
incompatible triple; UNKNOWN otherwise.

Manifests are JSON, not YAML: the pinned isolated interpreter has no PyYAML, and ``json`` is stdlib
and byte-stable.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np

from . import features as F
from . import hypotheses as H
from . import provenance, schema
from .config import Exp067Config
from .errors import Exp067SchemaError

UNKNOWN = -1
NEGATIVE = 0
POSITIVE = 1

#: Every held-out prefix also appears in training: a within-domain movie holdout. The name
#: "leave_one_movie_out" was used for this until the exp067b admission review pointed out that
#: it promises a cross-validation loop this protocol does not run; the old spelling is still
#: accepted so frozen historical split manifests keep loading.
PROTOCOL_WITHIN_PREFIX = "within_prefix_movie_holdout"
PROTOCOL_LOPO = "leave_one_prefix_out"
PROTOCOLS = (PROTOCOL_WITHIN_PREFIX, PROTOCOL_LOPO)
LEGACY_PROTOCOL_ALIASES = {"leave_one_movie_out": PROTOCOL_WITHIN_PREFIX}


# ------------------------------------------------------------------------------ label set

@dataclass
class LabelSet:
    """Ground truth joined to the FINAL graph being decoded (item 2)."""

    stem: str
    pred_to_gt: dict[int, int]
    gt_edges: set[tuple[int, int]]
    gt_out_degree: dict[int, int]
    gt_has_parent: dict[int, bool]
    gt_children: dict[int, set[int]]
    match_radius_um: float
    #: ``estimated_number_of_nodes`` from the GT geff attrs, the denominator of the one-sided count
    #: factor (parent cell 8:247-261). ``None`` when the attribute is absent, exactly as the parent
    #: leaves it, and then ``adjusted_jaccard`` returns the raw Jaccard.
    t_true: float | None = None
    manifest: dict[str, Any] = field(default_factory=dict)
    #: GT id -> (t, z, y, x) in voxel units, so evaluate.py can call ``score_sample`` verbatim.
    gt_nodes_plain: dict[int, tuple] = field(default_factory=dict)

    @property
    def n_matched(self) -> int:
        return len(self.pred_to_gt)


def build_label_set(
    stem: str,
    pred_nodes_plain: dict[int, tuple],
    gt_nodes_plain: dict[int, tuple],
    gt_edges: Sequence[tuple[int, int]],
    match_radius_um: float,
    t_true: float | None = None,
    manifest: dict[str, Any] | None = None,
) -> LabelSet:
    """Match with the parent's own bipartite matcher; never a bespoke matcher."""
    from .parent_scorer import match_nodes_bipartite

    pred_to_gt, _gt_to_pred = match_nodes_bipartite(
        pred_nodes_plain, gt_nodes_plain, max_dist=match_radius_um
    )
    children: dict[int, set[int]] = {}
    has_parent: dict[int, bool] = {}
    for source, target in gt_edges:
        children.setdefault(int(source), set()).add(int(target))
        has_parent[int(target)] = True
    out_degree = {node: len(kids) for node, kids in children.items()}
    return LabelSet(
        stem=stem,
        pred_to_gt={int(k): int(v) for k, v in pred_to_gt.items()},
        gt_edges={(int(s), int(t)) for s, t in gt_edges},
        gt_out_degree=out_degree,
        gt_has_parent=has_parent,
        gt_children=children,
        match_radius_um=float(match_radius_um),
        t_true=None if t_true is None else float(t_true),
        manifest=manifest or {},
        gt_nodes_plain={int(k): tuple(v) for k, v in gt_nodes_plain.items()},
    )


def save_label_set(path: Path, labels: LabelSet, gt_nodes_plain: dict[int, tuple]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    gt_ids = sorted(gt_nodes_plain)
    manifest = dict(labels.manifest)
    manifest.update(
        {
            "stem": labels.stem,
            "prefix": labels.stem.split("_")[0],
            "schema": schema.LABEL_SCHEMA_VERSION,
            "stage": "final_graph",
            "n_matched": int(labels.n_matched),
            "n_gt_nodes": len(gt_ids),
            "n_gt_edges": len(labels.gt_edges),
            "t_true": labels.t_true,
        }
    )
    matched = sorted(labels.pred_to_gt)
    edges = sorted(labels.gt_edges)
    tmp = path.with_suffix(".tmp.npz")
    schema.savez_checked(
        tmp,
        label_schema=np.asarray(schema.LABEL_SCHEMA_VERSION, dtype=np.int32),
        matched_pred=np.asarray(matched, dtype=np.int64),
        matched_gt=np.asarray([labels.pred_to_gt[p] for p in matched], dtype=np.int64),
        gt_edge_src=np.asarray([e[0] for e in edges], dtype=np.int64),
        gt_edge_tgt=np.asarray([e[1] for e in edges], dtype=np.int64),
        gt_node_id=np.asarray(gt_ids, dtype=np.int64),
        gt_node_t=np.asarray([int(gt_nodes_plain[g][0]) for g in gt_ids], dtype=np.int64),
        # GT coordinates travel with the labels so evaluate.py can call the parent's own
        # score_sample verbatim instead of reimplementing the match.
        gt_node_zyx=np.asarray(
            [[float(c) for c in gt_nodes_plain[g][1:4]] for g in gt_ids], dtype=np.float64
        ).reshape(len(gt_ids), 3),
        gt_out_degree=np.asarray([labels.gt_out_degree.get(g, 0) for g in gt_ids], dtype=np.int32),
        gt_has_parent=np.asarray([labels.gt_has_parent.get(g, False) for g in gt_ids], dtype=bool),
        match_radius_um=np.asarray(labels.match_radius_um, dtype=np.float64),
        manifest=schema.dump_manifest(manifest),
    )
    tmp.replace(path)
    return path


def load_label_set(path: Path) -> LabelSet:
    with np.load(path, allow_pickle=False) as payload:
        schema.require_fields(payload, schema.LABEL_REQUIRED_FIELDS, f"labels {path.name}")
        schema.require_version(
            payload["label_schema"].item(), schema.LABEL_SCHEMA_VERSION, f"labels {path.name}"
        )
        manifest = schema.load_manifest(payload["manifest"])
        gt_ids = payload["gt_node_id"].astype(np.int64)
        gt_t = payload["gt_node_t"].astype(np.int64)
        gt_zyx = payload["gt_node_zyx"].astype(np.float64)
        children: dict[int, set[int]] = {}
        has_parent: dict[int, bool] = {}
        edges: set[tuple[int, int]] = set()
        for s, t in zip(payload["gt_edge_src"], payload["gt_edge_tgt"]):
            edges.add((int(s), int(t)))
            children.setdefault(int(s), set()).add(int(t))
            has_parent[int(t)] = True
        labels = LabelSet(
            stem=str(manifest.get("stem", path.stem)),
            pred_to_gt={
                int(p): int(g) for p, g in zip(payload["matched_pred"], payload["matched_gt"])
            },
            gt_edges=edges,
            gt_out_degree={
                int(g): int(d) for g, d in zip(gt_ids, payload["gt_out_degree"])
            },
            gt_has_parent={int(g): bool(v) for g, v in zip(gt_ids, payload["gt_has_parent"])},
            gt_children=children,
            match_radius_um=float(payload["match_radius_um"].item()),
            t_true=None if manifest.get("t_true") is None else float(manifest["t_true"]),
            manifest=manifest,
        )
        labels.gt_nodes_plain = {
            int(g): (int(t), float(z), float(y), float(x))
            for g, t, (z, y, x) in zip(gt_ids, gt_t, gt_zyx)
        }
        return labels


# ------------------------------------------------------------------------------ predicates

def link_label(labels: LabelSet, pred_source: int, pred_target: int) -> int:
    """Exactly the scorer's TP / FP conditions restricted to both-matched pairs."""
    mu = labels.pred_to_gt.get(int(pred_source))
    mv = labels.pred_to_gt.get(int(pred_target))
    if mu is None or mv is None:
        return UNKNOWN
    if (mu, mv) in labels.gt_edges:
        return POSITIVE
    if labels.gt_has_parent.get(mv, False) or labels.gt_out_degree.get(mu, 0) > 0:
        return NEGATIVE
    return UNKNOWN


def division_label(labels: LabelSet, pred_mother: int, pred_a: int, pred_b: int) -> int:
    """POSITIVE only on a fully annotated true sister pair; NEGATIVE only on an incompatible triple."""
    mu = labels.pred_to_gt.get(int(pred_mother))
    ma = labels.pred_to_gt.get(int(pred_a))
    mb = labels.pred_to_gt.get(int(pred_b))
    if mu is None or ma is None or mb is None or ma == mb:
        return UNKNOWN
    gt_kids = labels.gt_children.get(mu, set())
    if not gt_kids:
        return UNKNOWN  # the annotation says nothing about this mother's children
    if ma in gt_kids and mb in gt_kids:
        return POSITIVE
    return NEGATIVE


# --------------------------------------------------------------------------------- samples

@dataclass
class Sample:
    """One scored window plus its masked labels."""

    stem: str
    t: int
    tokens: np.ndarray
    pad_mask: np.ndarray
    edge_local: np.ndarray
    edge_feats: np.ndarray
    edge_label: np.ndarray
    edge_mask: np.ndarray
    event_local: np.ndarray
    event_feats: np.ndarray
    event_label: np.ndarray
    event_mask: np.ndarray


def build_stem_samples(
    graph: provenance.FinalGraph,
    evidence: provenance.Evidence,
    labels: LabelSet | None,
    config: Exp067Config,
) -> tuple[list[Sample], H.Hypotheses, F.MovieContext]:
    table = provenance.reconcile(graph, evidence)
    hyp = H.generate(table, config)
    batches, ctx = F.build_batches(hyp, config)
    node_id = graph.node_id
    samples: list[Sample] = []
    for batch in batches:
        n_e, n_v = len(batch.edge_keys), len(batch.event_keys)
        edge_label = np.full(n_e, UNKNOWN, dtype=np.int8)
        event_label = np.full(n_v, UNKNOWN, dtype=np.int8)
        if labels is not None:
            for i, k in enumerate(batch.edge_keys):
                edge_label[i] = link_label(
                    labels, int(node_id[int(hyp.e_src[k])]), int(node_id[int(hyp.e_tgt[k])])
                )
            for i, j in enumerate(batch.event_keys):
                event_label[i] = division_label(
                    labels,
                    int(node_id[int(hyp.v_src[j])]),
                    int(node_id[int(hyp.v_a[j])]),
                    int(node_id[int(hyp.v_b[j])]),
                )
        samples.append(
            Sample(
                stem=graph.dataset,
                t=batch.t,
                tokens=batch.tokens,
                pad_mask=batch.pad_mask,
                edge_local=batch.edge_local,
                edge_feats=batch.edge_feats,
                edge_label=edge_label,
                edge_mask=edge_label != UNKNOWN,
                event_local=batch.event_local,
                event_feats=batch.event_feats,
                event_label=event_label,
                event_mask=event_label != UNKNOWN,
            )
        )
    return samples, hyp, ctx


def sample_counts(samples: Iterable[Sample]) -> dict[str, int]:
    counts = {
        "windows": 0,
        "link_total": 0, "link_positive": 0, "link_negative": 0, "link_unknown": 0,
        "event_total": 0, "event_positive": 0, "event_negative": 0, "event_unknown": 0,
    }
    for sample in samples:
        counts["windows"] += 1
        counts["link_total"] += len(sample.edge_label)
        counts["link_positive"] += int(np.count_nonzero(sample.edge_label == POSITIVE))
        counts["link_negative"] += int(np.count_nonzero(sample.edge_label == NEGATIVE))
        counts["link_unknown"] += int(np.count_nonzero(sample.edge_label == UNKNOWN))
        counts["event_total"] += len(sample.event_label)
        counts["event_positive"] += int(np.count_nonzero(sample.event_label == POSITIVE))
        counts["event_negative"] += int(np.count_nonzero(sample.event_label == NEGATIVE))
        counts["event_unknown"] += int(np.count_nonzero(sample.event_label == UNKNOWN))
    return counts


# ----------------------------------------------------------------------------------- cache

CACHE_SCHEMA_VERSION = 1
_CACHE_ARRAYS = (
    "tokens", "pad_mask", "edge_local", "edge_feats", "edge_label", "edge_mask",
    "event_local", "event_feats", "event_label", "event_mask",
)


def save_cache(path: Path, samples: Sequence[Sample]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "cache_schema": np.asarray(CACHE_SCHEMA_VERSION, dtype=np.int32),
        "n_samples": np.asarray(len(samples), dtype=np.int64),
        "stems": np.asarray([s.stem for s in samples]),
        "frames": np.asarray([s.t for s in samples], dtype=np.int64),
    }
    for i, sample in enumerate(samples):
        for name in _CACHE_ARRAYS:
            payload[f"s{i}_{name}"] = getattr(sample, name)
    tmp = path.with_suffix(".tmp.npz")
    np.savez_compressed(tmp, **payload)
    tmp.replace(path)
    return path


def load_cache(path: Path) -> list[Sample]:
    with np.load(path, allow_pickle=False) as payload:
        if "cache_schema" not in payload.files:
            raise Exp067SchemaError(f"cache {path.name}: missing cache_schema")
        schema.require_version(
            payload["cache_schema"].item(), CACHE_SCHEMA_VERSION, f"cache {path.name}"
        )
        count = int(payload["n_samples"].item())
        stems = [str(v) for v in payload["stems"]]
        frames = payload["frames"].astype(np.int64)
        samples: list[Sample] = []
        for i in range(count):
            kwargs = {name: payload[f"s{i}_{name}"] for name in _CACHE_ARRAYS}
            samples.append(Sample(stem=stems[i], t=int(frames[i]), **kwargs))
        return samples


# ---------------------------------------------------------------------------------- splits

@dataclass
class Splits:
    protocol: str
    train: list[str]
    holdout: list[str]
    test_stems: list[str]
    manifest_sha256: str

    @property
    def train_prefixes(self) -> set[str]:
        return {stem.split("_")[0] for stem in self.train}

    @property
    def holdout_prefixes(self) -> set[str]:
        return {stem.split("_")[0] for stem in self.holdout}


def load_splits(path: Path) -> Splits:
    """Movie-level groups, disjoint, validated. Raises rather than silently reweighting."""
    raw = path.read_text(encoding="utf-8")
    payload = json.loads(raw)
    protocol = str(payload.get("protocol", PROTOCOL_WITHIN_PREFIX))
    protocol = LEGACY_PROTOCOL_ALIASES.get(protocol, protocol)
    if protocol not in PROTOCOLS:
        raise Exp067SchemaError(f"{path.name}: unknown protocol {protocol!r}, expected one of {PROTOCOLS}")
    train = [str(s) for s in payload.get("train", [])]
    holdout = [str(s) for s in payload.get("holdout", [])]
    test_stems = [str(s) for s in payload.get("test_stems", [])]

    if not train:
        raise Exp067SchemaError(f"{path.name}: the train list is empty")
    if not holdout:
        raise Exp067SchemaError(f"{path.name}: the holdout list is empty")
    for name, group in (("train", train), ("holdout", holdout)):
        duplicates = sorted({s for s in group if group.count(s) > 1})
        if duplicates:
            raise Exp067SchemaError(f"{path.name}: {name} repeats stem(s) {duplicates}")
    overlap = sorted(set(train) & set(holdout))
    if overlap:
        raise Exp067SchemaError(f"{path.name}: stem(s) {overlap} appear in both train and holdout")
    leaked = sorted((set(train) | set(holdout)) & set(test_stems))
    if leaked:
        raise Exp067SchemaError(
            f"{path.name}: competition TEST stem(s) {leaked} appear in a training or holdout group"
        )
    if protocol == PROTOCOL_WITHIN_PREFIX:
        missing = {s.split("_")[0] for s in holdout} - {s.split("_")[0] for s in train}
        if missing:
            raise Exp067SchemaError(
                f"{path.name}: protocol {protocol} requires every held-out prefix to appear in train; "
                f"missing {sorted(missing)}"
            )
    else:
        # leave-one-prefix-out deliberately holds a prefix OUT of train; the two rules are exclusive
        shared = {s.split("_")[0] for s in holdout} & {s.split("_")[0] for s in train}
        if shared:
            raise Exp067SchemaError(
                f"{path.name}: protocol {protocol} requires the held-out prefix(es) to be absent from "
                f"train; shared {sorted(shared)}"
            )
    return Splits(
        protocol=protocol,
        train=train,
        holdout=holdout,
        test_stems=test_stems,
        manifest_sha256=schema.sha256_text(raw),
    )


def inner_split(train: Sequence[str], fraction: float, seed: int) -> tuple[list[str], list[str]]:
    """An inner validation split drawn from TRAINING stems only (item 7)."""
    if fraction <= 0.0:
        return list(train), []
    order = sorted(train)
    rng = np.random.default_rng(seed)
    permuted = [order[i] for i in rng.permutation(len(order))]
    n_val = max(1, int(round(len(order) * fraction)))
    if n_val >= len(order):
        raise Exp067SchemaError("inner_val_frac leaves no training stems")
    return sorted(permuted[n_val:]), sorted(permuted[:n_val])
