"""Declared constants. Nothing here is selected on held-out data (codex_challenge_v1 item 6).

The canonical runtime values live in ``configs/exp_067_temporal_joint_lineage.json``. This module
holds the defaults and the loader. ``tau0``, ``mu0`` and ``beta0`` are **fixed declared** constants:
there is no grid search over them, and ``train.py`` never reads a held-out score.

Manifests and runtime configuration use stdlib JSON. Admission status is recorded separately in
the experiment's development.json; it is not a remote controller launch receipt.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_PATH = Path("configs/exp_067_temporal_joint_lineage.json")


@dataclass(frozen=True)
class GenerationConfig:
    """Bounds on the hypothesis set. These bound the program size; they are not tuned for score."""

    max_alt_per_source: int = 4
    max_alt_per_target: int = 4
    min_alternatives_per_source: int = 2
    n_geometric: int = 3
    max_edge_um: float = 12.0  # parent BIOHUB_OUTPUT_EDGE_MAX_UM
    max_events_per_source: int = 4
    event_require_geometry: bool = True
    # Parent safe-division constants (x138 cell 0:27-40), used for the symmetric event gate.
    safe_div_max_um: float = 9.0
    safe_div_sister_max_um: float = 14.0
    safe_div_sister_symmetry_tau: float = 0.6
    safe_div_diverge_um: float = 2.25


@dataclass(frozen=True)
class WindowConfig:
    """Seven-frame, source-owned scoring. Required endpoints are assembled before any context."""

    half_span: int = 3  # frames each side -> 7-frame window
    required_cap: int = 160
    total_cap: int = 256
    context_per_frame: int = 24
    max_sources_per_batch: int = 32


@dataclass(frozen=True)
class ModelConfig:
    d_model: int = 48
    n_layers: int = 2
    n_heads: int = 2
    ff_mult: int = 2


@dataclass(frozen=True)
class ObjectiveConfig:
    """One fixed declared continuity baseline plus an optional fixed parent prior."""

    tau0: float = 0.0  # link-head decision boundary; the birth/death baseline
    mu0: float = 0.0  # division-head decision boundary
    beta0: float = 0.0  # optional fixed parent-incumbency prior, declared not tuned


@dataclass(frozen=True)
class SolveConfig:
    max_component_vars: int = 2000
    max_component_seconds: float = 5.0
    budget_seconds: float = 600.0
    max_revert_fraction: float = 0.02
    milp_mip_rel_gap: float = 0.0


@dataclass(frozen=True)
class TrainConfig:
    """Fixed schedule. No early stopping, no held-out checkpoint selection (item 7)."""

    seed: int = 20260925
    epochs: int = 40
    max_seconds: float = 1800.0
    lr: float = 3e-3
    weight_decay: float = 1e-2
    lr_decay_at: tuple[int, ...] = (28, 36)
    lr_decay_gamma: float = 0.1
    link_loss_weight: float = 1.0
    division_loss_weight: float = 1.0
    min_link_positives: int = 200
    min_division_positives: int = 3
    inner_val_frac: float = 0.0  # inner split draws from TRAIN stems only when > 0


@dataclass(frozen=True)
class Exp067Config:
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    window: WindowConfig = field(default_factory=WindowConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    objective: ObjectiveConfig = field(default_factory=ObjectiveConfig)
    solve: SolveConfig = field(default_factory=SolveConfig)
    train: TrainConfig = field(default_factory=TrainConfig)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Exp067Config":
        if set(payload) - {f.name for f in fields(cls)}:
            raise ValueError("unknown exp067 config section")
        sections: dict[str, Any] = {}
        for spec in fields(cls):
            section_cls = spec.type if isinstance(spec.type, type) else None
            given = payload.get(spec.name, {})
            base = spec.default_factory()  # type: ignore[misc]
            if not given:
                sections[spec.name] = base
                continue
            merged = {**asdict(base), **given}
            known = {f.name for f in fields(base)}
            unknown = sorted(set(merged) - known)
            if unknown:
                raise ValueError(f"exp067 config section {spec.name!r}: unknown key(s) {unknown}")
            ctor = type(base)
            if "lr_decay_at" in merged and merged["lr_decay_at"] is not None:
                merged["lr_decay_at"] = tuple(merged["lr_decay_at"])
            sections[spec.name] = ctor(**merged)
            del section_cls
        return cls(**sections)

    @classmethod
    def load(cls, path: Path | str | None = None) -> "Exp067Config":
        if path is None and os.environ.get('BIOHUB_EXP067_CONFIG_JSON'):
            return cls.from_dict(json.loads(os.environ['BIOHUB_EXP067_CONFIG_JSON']))
        explicit = path is not None
        if path is None:
            path = DEFAULT_CONFIG_PATH
        path = Path(path)
        if not path.exists():
            if explicit:
                raise FileNotFoundError(path)
            return cls()
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))
