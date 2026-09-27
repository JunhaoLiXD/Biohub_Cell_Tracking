"""Schema versions, field contracts, units and hashing.

Units are declared once here and never re-derived anywhere else:

* ``t``            integer frame index
* ``coords[:,1:]`` original-resolution voxel (z, y, x), float32 (the parent's V1284 patch removes
  the int16 cast at cell 4:527-528, so these carry sub-voxel refinement)
* micrometres      voxel * VOXEL_SCALE_UM, with VOXEL_SCALE_UM taken from the parent (cell 5:9)
* ``alt_prob``     the parent's ``softmax(raw, dim=0)`` — normalised over SOURCES, not targets
* ``alt_logit``    the post-fusion raw edge logit, direction-neutral
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import numpy as np

from .errors import Exp067SchemaError

EXPORT_SCHEMA_VERSION = 1
FINAL_GRAPH_SCHEMA_VERSION = 1
LABEL_SCHEMA_VERSION = 1
CKPT_FORMAT_VERSION = 1

#: Parent constant, biohub-x138 cell 5 line 9. Do not change without changing the parent.
VOXEL_SCALE_UM: tuple[float, float, float] = (1.625, 0.40625, 0.40625)

#: Node provenance codes. Only ORIGIN_DETECTOR nodes can be reconsidered (see provenance.py).
ORIGIN_DETECTOR = 0
ORIGIN_READMITTED = 1
ORIGIN_SYNTHETIC = 2
ORIGIN_NAMES = {ORIGIN_DETECTOR: "detector", ORIGIN_READMITTED: "readmitted", ORIGIN_SYNTHETIC: "gap_synthetic"}

#: Bit flags recording which export rule produced a candidate alternative.
ALT_ORIGIN_ROW_TOPK = 1  # top-k targets for a source, over the full pre-threshold matrix
ALT_ORIGIN_COL_TOPK = 2  # top-k sources for a target, over the full pre-threshold matrix
ALT_ORIGIN_GEOMETRIC = 4  # nearest-neighbour fallback, probability NOT available
ALT_ORIGIN_PARENT = 8  # an edge of the parent graph being decoded, unioned in unconditionally

EXPORT_REQUIRED_FIELDS: tuple[str, ...] = (
    "exp067_schema",
    "coords",
    "node_ids",
    "emb_src",
    "emb_tgt",
    "emb_src_valid",
    "emb_tgt_valid",
    "det_score",
    "alt_src_row",
    "alt_tgt_row",
    "alt_prob",
    "alt_logit",
    "alt_origin",
    "manifest",
)

FINAL_GRAPH_REQUIRED_FIELDS: tuple[str, ...] = (
    "final_schema",
    "node_id",
    "node_t",
    "node_zyx",
    "node_origin",
    "node_det_row",
    "edge_src",
    "edge_tgt",
    "manifest",
)

LABEL_REQUIRED_FIELDS: tuple[str, ...] = (
    "label_schema",
    "matched_pred",
    "matched_gt",
    "gt_edge_src",
    "gt_edge_tgt",
    "gt_node_id",
    "gt_node_t",
    "gt_node_zyx",
    "gt_out_degree",
    "gt_has_parent",
    "match_radius_um",
    "manifest",
)


def sha256_array(arr: np.ndarray) -> str:
    """Content hash of an array, insensitive to stride but sensitive to dtype and shape."""
    contiguous = np.ascontiguousarray(arr)
    digest = hashlib.sha256()
    digest.update(str(contiguous.dtype.str).encode())
    digest.update(str(contiguous.shape).encode())
    digest.update(contiguous.tobytes(order="C"))
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def dump_manifest(payload: dict[str, Any]) -> np.ndarray:
    """Manifests travel as a 0-d unicode array so they survive ``np.savez`` round-trips."""
    return np.array(json.dumps(payload, sort_keys=True))


def load_manifest(raw: Any) -> dict[str, Any]:
    return json.loads(str(np.asarray(raw).item()))


def require_fields(payload: Any, fields: tuple[str, ...], what: str) -> None:
    present = set(getattr(payload, "files", None) or payload.keys())
    missing = [name for name in fields if name not in present]
    if missing:
        raise Exp067SchemaError(f"{what}: missing required field(s) {missing}")
    if "manifest" in present:
        manifest = load_manifest(payload["manifest"])
        hashes = manifest.get("array_sha256")
        if not hashes or set(hashes) != present - {"manifest"}:
            raise Exp067SchemaError(f"{what}: missing/incomplete array integrity manifest")
        for name, expected in hashes.items():
            if sha256_array(payload[name]) != expected:
                raise Exp067SchemaError(f"{what}: hash mismatch for {name}")


def savez_checked(path: Any, **arrays: Any) -> None:
    """Seal the arrays actually serialized, including dtype conversions."""
    arrays = {k: np.asarray(v) for k, v in arrays.items()}
    if "manifest" in arrays:
        manifest = load_manifest(arrays["manifest"])
        manifest["array_sha256"] = {k: sha256_array(v) for k, v in arrays.items() if k != "manifest"}
        arrays["manifest"] = dump_manifest(manifest)
    np.savez_compressed(path, **arrays)


def require_version(actual: int, expected: int, what: str) -> None:
    if int(actual) != int(expected):
        raise Exp067SchemaError(f"{what}: schema version {int(actual)} != expected {int(expected)}")


def voxel_to_um(zyx: np.ndarray) -> np.ndarray:
    """(N, 3) voxel -> (N, 3) micrometres, float64."""
    arr = np.asarray(zyx, dtype=np.float64)
    if arr.ndim != 2 or arr.shape[1] != 3:
        raise Exp067SchemaError(f"voxel_to_um expects (N, 3), got {arr.shape}")
    return arr * np.asarray(VOXEL_SCALE_UM, dtype=np.float64)
