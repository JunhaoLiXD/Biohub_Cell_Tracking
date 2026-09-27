"""Checkpoint schema, code fingerprinting, and fail-closed loading.

``load`` refuses on any mismatch and names the differing field. A checkpoint trained against a
different feature spec, a different export schema or different model code is rejected, not coerced.
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Any

import torch

from . import features as F
from . import schema
from .config import ModelConfig
from .errors import Exp067SchemaError
from .model import JointLineageScorer, Normalizer

_CODE_FILES = ("model.py", "features.py", "hypotheses.py", "decode.py", "schema.py",
               "provenance.py", "supervise.py", "train.py", "config.py")

BACKBONE_PROVENANCE = "POSSIBLE_OVERLAP_UNKNOWN_PROVENANCE"


def code_fingerprint() -> str:
    """Hash of the modules whose behaviour a checkpoint depends on."""
    here = Path(__file__).parent
    parts = []
    for name in _CODE_FILES:
        parts.append(name)
        parts.append(schema.sha256_text((here / name).read_text(encoding="utf-8")))
    return schema.sha256_text("|".join(parts))


def build_payload(
    model: JointLineageScorer,
    normalizer: Normalizer,
    *,
    seed: int,
    train_manifest_sha256: str,
    protocol: str,
    train_stems: list[str],
    holdout_stems: list[str],
    counts: dict[str, int],
    hyperparams: dict[str, Any],
    division_head_trained: bool,
) -> dict[str, Any]:
    return {
        "format_version": schema.CKPT_FORMAT_VERSION,
        "state_dict": model.state_dict(),
        "feature_spec": F.feature_spec_fingerprint(model.emb_channels),
        "model_config": {
            "d_model": model.cfg.d_model,
            "n_layers": model.cfg.n_layers,
            "n_heads": model.cfg.n_heads,
            "ff_mult": model.cfg.ff_mult,
        },
        "emb_channels": int(model.emb_channels),
        "normalizer": normalizer.to_dict(),
        "hyperparams": hyperparams,
        "seed": int(seed),
        "train_manifest_sha256": train_manifest_sha256,
        "export_schema_version": schema.EXPORT_SCHEMA_VERSION,
        "model_code_sha256": code_fingerprint(),
        "created_at_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "protocol": protocol,
        "train_stems": list(train_stems),
        "holdout_stems": list(holdout_stems),
        "supervision_counts": dict(counts),
        "backbone_provenance": BACKBONE_PROVENANCE,
        "division_head_trained": bool(division_head_trained),
    }


def save(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    torch.save(payload, tmp)
    tmp.replace(path)
    return path


def load(path: Path, *, emb_channels: int | None = None, config=None) -> tuple[JointLineageScorer, Normalizer, dict[str, Any]]:
    payload = torch.load(path, map_location="cpu", weights_only=True)
    if not isinstance(payload, dict):
        raise Exp067SchemaError(f"checkpoint {path.name}: not a mapping")
    if payload.get('division_head_trained') is not True:
        raise Exp067SchemaError('checkpoint has no trained division head')
    if config is not None:
        trained = payload.get('hyperparams', {}).get('config', {})
        for section in ('generation', 'window', 'model', 'objective'):
            if _normalise(trained.get(section)) != _normalise(config.to_dict()[section]):
                raise Exp067SchemaError(f'checkpoint configuration mismatch: {section}')

    for field_name in (
        "format_version", "state_dict", "feature_spec", "emb_channels", "normalizer",
        "export_schema_version", "model_code_sha256", "model_config",
    ):
        if field_name not in payload:
            raise Exp067SchemaError(f"checkpoint {path.name}: missing field {field_name!r}")

    if int(payload["format_version"]) != schema.CKPT_FORMAT_VERSION:
        raise Exp067SchemaError(
            f"checkpoint {path.name}: format_version {payload['format_version']} != "
            f"{schema.CKPT_FORMAT_VERSION}"
        )
    if int(payload["export_schema_version"]) != schema.EXPORT_SCHEMA_VERSION:
        raise Exp067SchemaError(
            f"checkpoint {path.name}: export_schema_version {payload['export_schema_version']} != "
            f"{schema.EXPORT_SCHEMA_VERSION}"
        )
    if payload["model_code_sha256"] != code_fingerprint():
        raise Exp067SchemaError(
            f"checkpoint {path.name}: model_code_sha256 mismatch — the scoring code changed since "
            "training, so this checkpoint no longer defines the same function"
        )

    stored_channels = int(payload["emb_channels"])
    if emb_channels is not None and stored_channels != int(emb_channels):
        raise Exp067SchemaError(
            f"checkpoint {path.name}: trained on {stored_channels} embedding channels, the export "
            f"carries {int(emb_channels)}"
        )

    expected = F.feature_spec_fingerprint(stored_channels)
    stored = payload["feature_spec"]
    for key in sorted(expected):
        if key not in stored:
            raise Exp067SchemaError(f"checkpoint {path.name}: feature_spec missing {key!r}")
        if _normalise(stored[key]) != _normalise(expected[key]):
            raise Exp067SchemaError(
                f"checkpoint {path.name}: feature_spec field {key!r} differs from the live spec"
            )

    cfg = ModelConfig(**{k: int(v) for k, v in payload["model_config"].items()})
    model = JointLineageScorer(stored_channels, cfg)
    model.load_state_dict(payload["state_dict"])
    model.eval()
    normalizer = Normalizer.from_dict(payload["normalizer"])
    import numpy as np
    for name, width in [('token', model.token_in), ('edge', F.N_EDGE_FEATURES), ('event', F.N_EVENT_FEATURES)]:
        mean, scale = getattr(normalizer, name + '_mean'), getattr(normalizer, name + '_scale')
        if mean.shape != (width,) or scale.shape != (width,) or not np.isfinite(mean).all() or not np.isfinite(scale).all() or (scale <= 0).any():
            raise Exp067SchemaError(f'invalid normalizer {name}')
    if any(not torch.isfinite(v).all() for v in model.state_dict().values()):
        raise Exp067SchemaError('nonfinite checkpoint weights')
    return model, normalizer, payload


def _normalise(value: Any) -> Any:
    if isinstance(value, (list, tuple)):
        return [_normalise(v) for v in value]
    return value


def validate_export(payload, evidence):
    expected = payload.get('hyperparams', {}).get('export_signature')
    actual = {k: evidence.manifest.get(k) for k in ('weights_sha256', 'predict_source_sha256')}
    if not expected or actual != expected:
        raise Exp067SchemaError('inference export differs from the frozen training backbone')
