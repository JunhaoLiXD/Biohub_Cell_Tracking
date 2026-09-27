"""The real export hooks the patched parent notebook calls.

These are ordinary functions operating on ordinary arrays, so the tests exercise them directly on
realistic inputs rather than asserting that a string is present in a notebook.

Where each hook is called in the patched parent:

===========================  ==========================================================
``begin_video``              top of ``predict_video``
``record_alternatives``      inside the frame-pair loop, on the **full** ``probs``/``raw``
                             matrices, immediately **before** ``candidates = sorted(...)``
                             — i.e. before any threshold and before any degree cap
``record_embeddings``        same loop, on ``unet_feat_src`` / ``unet_feat_tgt``
``record_detection``         the low-detection block, where the sigmoid peak scores exist
``record_graph_node_ids``    after ``build_graph``, from its own ``bulk_add_nodes`` return
``write_video_export``       after ``build_graph``, before the ILP solve
``write_final_graph``        end of ``filter_output_graph``, after line-fit smoothing
``write_labels``             the validator scoring loop, only when labels are enabled
===========================  ==========================================================

``BIOHUB_EXP067_EXPORT`` and ``BIOHUB_EXP067_LABELS`` gate the two write paths independently of
``BIOHUB_EXP067_ENABLE``, and an export failure propagates (item 10): these hooks raise, and the
injected call sites are outside the parent's repair ``try/except``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from . import provenance, runtime, schema
from .errors import Exp067SchemaError

DEFAULT_TOPK = 4


@dataclass
class VideoBuffer:
    stem: str
    topk: int = DEFAULT_TOPK
    emb_channels: int = 0
    alt_src: list[np.ndarray] = field(default_factory=list)
    alt_tgt: list[np.ndarray] = field(default_factory=list)
    alt_prob: list[np.ndarray] = field(default_factory=list)
    alt_logit: list[np.ndarray] = field(default_factory=list)
    alt_origin: list[np.ndarray] = field(default_factory=list)
    emb_src: dict[int, np.ndarray] = field(default_factory=dict)
    emb_tgt: dict[int, np.ndarray] = field(default_factory=dict)
    det_score: dict[int, float] = field(default_factory=dict)
    node_ids: np.ndarray | None = None
    n_pairs: int = 0


_BUFFERS: dict[str, VideoBuffer] = {}


def begin_video(stem: str, topk: int | None = None) -> VideoBuffer:
    buffer = VideoBuffer(stem=str(stem), topk=int(topk or runtime.env_int(runtime.ENV_TOPK, DEFAULT_TOPK)))
    _BUFFERS[str(stem)] = buffer
    return buffer


def buffer_for(stem: str) -> VideoBuffer:
    buffer = _BUFFERS.get(str(stem))
    if buffer is None:
        buffer = begin_video(stem)
    return buffer


def reset_all() -> None:
    _BUFFERS.clear()


def _topk_along(values: np.ndarray, k: int, axis: int) -> np.ndarray:
    """Indices of the ``k`` largest entries along ``axis``, deterministic on ties (lowest index)."""
    size = values.shape[axis]
    k = int(min(max(k, 0), size))
    if k == 0:
        return np.zeros((values.shape[1 - axis], 0), dtype=np.int64)
    work = -values if axis == 1 else -values.T  # rows become the grouping axis
    part = np.argsort(work, axis=1, kind="stable")[:, :k]
    rows = np.arange(work.shape[0])[:, None]
    chosen = work[rows, part]
    # lexsort so equal values resolve by ascending original index -> reproducible output
    order = np.lexsort((part, chosen), axis=1)
    return np.take_along_axis(part, order, axis=1).astype(np.int64)


def record_alternatives(
    stem: str,
    idx_src: Sequence[int] | np.ndarray,
    idx_tgt: Sequence[int] | np.ndarray,
    probs: np.ndarray,
    logits: np.ndarray,
    topk: int | None = None,
) -> int:
    """Top-k targets per source AND top-k sources per target, from the full pre-threshold matrices.

    ``probs`` is the parent's ``softmax(raw, dim=0)``, normalised over SOURCES; ``logits`` is the
    post-fusion raw logit and is direction-neutral. Both are exported because a row-wise top-k over a
    source-normalised distribution is not itself a distribution over targets.
    """
    buffer = buffer_for(stem)
    k = int(topk or buffer.topk)
    src = np.asarray(idx_src, dtype=np.int64).reshape(-1)
    tgt = np.asarray(idx_tgt, dtype=np.int64).reshape(-1)
    probs = np.asarray(probs, dtype=np.float32)
    logits = np.asarray(logits, dtype=np.float32)
    if probs.shape != (len(src), len(tgt)) or logits.shape != probs.shape:
        raise Exp067SchemaError(
            f"{stem}: alternative matrices {probs.shape}/{logits.shape} do not match "
            f"({len(src)}, {len(tgt)})"
        )
    if probs.size == 0:
        buffer.n_pairs += 1
        return 0

    pairs: dict[tuple[int, int], tuple[float, float, int]] = {}

    row_pick = _topk_along(logits, k, axis=1)  # (n_src, k) target indices
    for i in range(row_pick.shape[0]):
        for j in row_pick[i]:
            key = (int(src[i]), int(tgt[j]))
            pairs[key] = (float(probs[i, j]), float(logits[i, j]), schema.ALT_ORIGIN_ROW_TOPK)

    col_pick = _topk_along(logits, k, axis=0)  # (n_tgt, k) source indices
    for j in range(col_pick.shape[0]):
        for i in col_pick[j]:
            key = (int(src[i]), int(tgt[j]))
            previous = pairs.get(key)
            origin = schema.ALT_ORIGIN_COL_TOPK | (previous[2] if previous else 0)
            pairs[key] = (float(probs[i, j]), float(logits[i, j]), origin)

    ordered = sorted(pairs)
    buffer.alt_src.append(np.asarray([p[0] for p in ordered], dtype=np.int64))
    buffer.alt_tgt.append(np.asarray([p[1] for p in ordered], dtype=np.int64))
    buffer.alt_prob.append(np.asarray([pairs[p][0] for p in ordered], dtype=np.float32))
    buffer.alt_logit.append(np.asarray([pairs[p][1] for p in ordered], dtype=np.float32))
    buffer.alt_origin.append(np.asarray([pairs[p][2] for p in ordered], dtype=np.int16))
    buffer.n_pairs += 1
    return len(ordered)


def record_embeddings(
    stem: str, role: str, global_index: Sequence[int] | np.ndarray, feats: np.ndarray
) -> None:
    """``role`` is ``'src'`` or ``'tgt'``. Both roles exist because window ``(t-1, t)`` and ``(t, t+1)``
    encode frame ``t`` in different forward passes; the schema carries both rather than pretending
    there is one embedding per node."""
    if role not in {"src", "tgt"}:
        raise Exp067SchemaError(f"record_embeddings: role must be 'src' or 'tgt', got {role!r}")
    buffer = buffer_for(stem)
    index = np.asarray(global_index, dtype=np.int64).reshape(-1)
    block = np.asarray(feats, dtype=np.float32)
    if block.ndim == 3 and block.shape[0] == 1:
        block = block[0]
    if block.ndim != 2 or block.shape[0] != len(index):
        raise Exp067SchemaError(
            f"{stem}: embedding block {block.shape} does not match {len(index)} node(s)"
        )
    if buffer.emb_channels == 0:
        buffer.emb_channels = int(block.shape[1])
    elif buffer.emb_channels != int(block.shape[1]):
        raise Exp067SchemaError(
            f"{stem}: embedding width changed mid-video ({buffer.emb_channels} -> {block.shape[1]})"
        )
    target = buffer.emb_src if role == "src" else buffer.emb_tgt
    for position, node in enumerate(index):
        target.setdefault(int(node), block[position])


def record_detection(stem: str, global_index: Sequence[int] | np.ndarray, scores: np.ndarray) -> None:
    buffer = buffer_for(stem)
    index = np.asarray(global_index, dtype=np.int64).reshape(-1)
    values = np.asarray(scores, dtype=np.float64).reshape(-1)
    if len(index) != len(values):
        raise Exp067SchemaError(f"{stem}: {len(index)} detection index/es against {len(values)} score(s)")
    for node, value in zip(index, values):
        buffer.det_score.setdefault(int(node), float(value))


def record_graph_node_ids(stem: str, node_ids: Sequence[int] | np.ndarray) -> None:
    """Captured from ``build_graph``'s own ``bulk_add_nodes`` return: row ``r`` -> graph node id."""
    buffer = buffer_for(stem)
    buffer.node_ids = np.asarray(node_ids, dtype=np.int64).reshape(-1)


def build_evidence(stem: str, coords: np.ndarray, manifest_extras: dict[str, Any] | None = None) -> provenance.Evidence:
    """Assemble the export for one movie. Raises rather than substituting a missing mandatory field."""
    buffer = buffer_for(stem)
    coords = np.asarray(coords, dtype=np.float64)
    if coords.ndim != 2 or coords.shape[1] != 4:
        raise Exp067SchemaError(f"{stem}: coords must be (N, 4) [t, z, y, x], got {coords.shape}")
    rows = len(coords)
    channels = buffer.emb_channels
    if rows == 0 and channels == 0:
        channels = 1  # empty array shape only; no fabricated node features
    if channels <= 0:
        raise Exp067SchemaError(
            f"{stem}: no backbone embeddings were recorded; they are mandatory and there is no substitute"
        )
    if buffer.node_ids is None:
        raise Exp067SchemaError(
            f"{stem}: build_graph node ids were never captured, so detector row -> graph id cannot be "
            "established; refusing to guess by coordinate"
        )
    if len(buffer.node_ids) != rows:
        raise Exp067SchemaError(
            f"{stem}: build_graph returned {len(buffer.node_ids)} node id(s) for {rows} coordinate row(s)"
        )

    emb_src = np.zeros((rows, channels), dtype=np.float32)
    emb_tgt = np.zeros((rows, channels), dtype=np.float32)
    emb_src_valid = np.zeros(rows, dtype=bool)
    emb_tgt_valid = np.zeros(rows, dtype=bool)
    for node, vector in buffer.emb_src.items():
        if 0 <= node < rows:
            emb_src[node] = vector
            emb_src_valid[node] = True
    for node, vector in buffer.emb_tgt.items():
        if 0 <= node < rows:
            emb_tgt[node] = vector
            emb_tgt_valid[node] = True

    det_score = np.zeros(rows, dtype=np.float32)
    missing = sorted(set(range(rows)) - set(buffer.det_score))
    if missing:
        raise Exp067SchemaError(f"{stem}: missing measured detection scores for rows {missing[:8]}")
    for node, value in buffer.det_score.items():
        if 0 <= node < rows:
            det_score[node] = value

    def cat(blocks: list[np.ndarray], dtype: Any) -> np.ndarray:
        if not blocks:
            return np.zeros(0, dtype=dtype)
        return np.concatenate(blocks).astype(dtype)

    manifest = {
        "voxel_scale_um": list(schema.VOXEL_SCALE_UM),
        "n_frame_pairs_seen": int(buffer.n_pairs),
        "topk": int(buffer.topk),
        "emb_src_covered": int(emb_src_valid.sum()),
        "emb_tgt_covered": int(emb_tgt_valid.sum()),
        "alternatives_are_pre_threshold_pre_cap": True,
        "alt_prob_normalisation": "softmax over SOURCES (parent cell 5 / predict_unet_transformer)",
    }
    manifest.update(manifest_extras or {})

    return provenance.Evidence(
        dataset=str(stem),
        coords=coords,
        node_ids=buffer.node_ids.astype(np.int64),
        emb_src=emb_src,
        emb_tgt=emb_tgt,
        emb_src_valid=emb_src_valid,
        emb_tgt_valid=emb_tgt_valid,
        det_score=det_score,
        alt_src_row=cat(buffer.alt_src, np.int64),
        alt_tgt_row=cat(buffer.alt_tgt, np.int64),
        alt_prob=cat(buffer.alt_prob, np.float32),
        alt_logit=cat(buffer.alt_logit, np.float32),
        alt_origin=cat(buffer.alt_origin, np.int16),
        manifest=manifest,
    )


def export_dir() -> Path:
    return Path(os.environ.get(runtime.ENV_EXPORT_DIR, "") or "exp067_export")


def write_video_export(
    stem: str, coords: np.ndarray, out_dir: str | Path | None = None, manifest_extras: dict[str, Any] | None = None
) -> Path:
    evidence = build_evidence(stem, coords, manifest_extras)
    directory = Path(out_dir) if out_dir is not None else export_dir()
    path = provenance.save_evidence(directory / f"{stem}.npz", evidence)
    _BUFFERS.pop(str(stem), None)
    return path


def write_final_graph(
    stem: str,
    nodes_by_id: Mapping[int, Mapping[str, Any]],
    edges: Sequence[Mapping[str, Any]],
    det_row_of_node: Mapping[int, int] | None = None,
    out_dir: str | Path | None = None,
    split: str = "test",
) -> Path:
    graph = provenance.final_graph_from_parent(
        stem, nodes_by_id, edges, det_row_of_node, manifest={"split": split}
    )
    directory = Path(out_dir) if out_dir is not None else export_dir()
    return provenance.save_final_graph(directory / f"{stem}.final.npz", graph)


def write_labels(
    stem: str,
    nodes_by_id: Mapping[int, Mapping[str, Any]],
    gt_nodes_plain: Mapping[int, tuple],
    gt_edges: Sequence[tuple[int, int]],
    match_radius_um: float,
    t_true: float | None,
    out_dir: str | Path,
    extra: dict[str, Any] | None = None,
) -> Path:
    """GT join, kept in its own module, directory and env flag. ``infer`` never touches this path."""
    from . import supervise

    pred_nodes_plain = {
        int(node_id): (
            int(node["t"]), float(node["z"]), float(node["y"]), float(node["x"])
        )
        for node_id, node in nodes_by_id.items()
    }
    labels = supervise.build_label_set(
        stem,
        pred_nodes_plain,
        {int(k): tuple(v) for k, v in gt_nodes_plain.items()},
        [(int(s), int(t)) for s, t in gt_edges],
        match_radius_um,
        t_true=t_true,
        manifest={"ground_truth_accessed": True, **(extra or {})},
    )
    return supervise.save_label_set(
        Path(out_dir) / f"{stem}.npz", labels, {int(k): tuple(v) for k, v in gt_nodes_plain.items()}
    )
