"""The trained scorer: a shared sparse local encoder with two calibrated heads.

Both heads are **trained** (codex_challenge_v1 item 1). There is no geometry-only configuration and
no ``division_head=None`` path.

* ``link_head``     -> log-odds that edge ``(u, v)`` is a true ground-truth link.
* ``division_head`` -> log-odds that ``{a, b}`` is a true sister pair from mother ``u``, **given**
  both links. This is an *increment*: the two links carry their own evidence exactly once each, so
  nothing is double counted (item 6).

Symmetry in ``{a, b}`` is structural: the division head sees ``h_u``, ``h_a + h_b`` and
``|h_a - h_b|`` and symmetric geometry, so swapping the daughters cannot change its output.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
from torch import nn

from . import features as F
from .config import ModelConfig
from .errors import Exp067SchemaError


@dataclass
class Normalizer:
    """Train-only feature statistics. Stored in the checkpoint; never recomputed at inference."""

    token_mean: np.ndarray
    token_scale: np.ndarray
    edge_mean: np.ndarray
    edge_scale: np.ndarray
    event_mean: np.ndarray
    event_scale: np.ndarray

    @staticmethod
    def _stats(blocks: list[np.ndarray], width: int) -> tuple[np.ndarray, np.ndarray]:
        if not blocks:
            return np.zeros(width, dtype=np.float64), np.ones(width, dtype=np.float64)
        stacked = np.concatenate([np.atleast_2d(b) for b in blocks], axis=0).astype(np.float64)
        mean = stacked.mean(axis=0)
        scale = stacked.std(axis=0)
        scale = np.where(scale < 1e-6, 1.0, scale)
        return mean, scale

    @classmethod
    def fit(
        cls,
        token_blocks: list[np.ndarray],
        edge_blocks: list[np.ndarray],
        event_blocks: list[np.ndarray],
        token_width: int,
    ) -> "Normalizer":
        t_mean, t_scale = cls._stats(token_blocks, token_width)
        e_mean, e_scale = cls._stats(edge_blocks, F.N_EDGE_FEATURES)
        v_mean, v_scale = cls._stats(event_blocks, F.N_EVENT_FEATURES)
        return cls(t_mean, t_scale, e_mean, e_scale, v_mean, v_scale)

    @classmethod
    def identity(cls, token_width: int) -> "Normalizer":
        return cls(
            np.zeros(token_width), np.ones(token_width),
            np.zeros(F.N_EDGE_FEATURES), np.ones(F.N_EDGE_FEATURES),
            np.zeros(F.N_EVENT_FEATURES), np.ones(F.N_EVENT_FEATURES),
        )

    def apply_tokens(self, tokens: np.ndarray) -> np.ndarray:
        return ((tokens - self.token_mean) / self.token_scale).astype(np.float32)

    def apply_edges(self, feats: np.ndarray) -> np.ndarray:
        return ((feats - self.edge_mean) / self.edge_scale).astype(np.float32)

    def apply_events(self, feats: np.ndarray) -> np.ndarray:
        return ((feats - self.event_mean) / self.event_scale).astype(np.float32)

    def to_dict(self) -> dict[str, Any]:
        return {name: np.asarray(getattr(self, name)).tolist() for name in (
            "token_mean", "token_scale", "edge_mean", "edge_scale", "event_mean", "event_scale"
        )}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Normalizer":
        return cls(**{name: np.asarray(payload[name], dtype=np.float64) for name in (
            "token_mean", "token_scale", "edge_mean", "edge_scale", "event_mean", "event_scale"
        )})


def _mlp(in_dim: int, hidden: int) -> nn.Sequential:
    return nn.Sequential(nn.Linear(in_dim, hidden), nn.GELU(), nn.Linear(hidden, 1))


class JointLineageScorer(nn.Module):
    """Tiny by design: the supervision available is small and is reported as a risk, not hidden."""

    def __init__(self, emb_channels: int, cfg: ModelConfig | None = None) -> None:
        super().__init__()
        cfg = cfg or ModelConfig()
        self.emb_channels = int(emb_channels)
        self.cfg = cfg
        self.token_in = F.token_dim(emb_channels)
        d = cfg.d_model
        self.token_proj = nn.Linear(self.token_in, d)
        layer = nn.TransformerEncoderLayer(
            d_model=d,
            nhead=cfg.n_heads,
            dim_feedforward=d * cfg.ff_mult,
            dropout=0.0,
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )
        self.encoder = nn.TransformerEncoder(layer, num_layers=cfg.n_layers, enable_nested_tensor=False)
        self.link_head = _mlp(3 * d + F.N_EDGE_FEATURES, d)
        self.division_head = _mlp(3 * d + F.N_EVENT_FEATURES, d)

    # ------------------------------------------------------------------ forward

    def encode(self, tokens: torch.Tensor, pad_mask: torch.Tensor | None = None) -> torch.Tensor:
        if tokens.dim() == 2:
            tokens = tokens.unsqueeze(0)
        if tokens.shape[-1] != self.token_in:
            raise Exp067SchemaError(
                f"token width {tokens.shape[-1]} != model token_in {self.token_in}; feature spec or "
                "embedding width changed"
            )
        mask = None
        if pad_mask is not None:
            mask = pad_mask.unsqueeze(0) if pad_mask.dim() == 1 else pad_mask
        return self.encoder(self.token_proj(tokens), src_key_padding_mask=mask)

    def score_edges(
        self, hidden: torch.Tensor, edge_local: torch.Tensor, edge_feats: torch.Tensor
    ) -> torch.Tensor:
        if edge_local.numel() == 0:
            return hidden.new_zeros(0)
        h = hidden[0]
        hu = h[edge_local[:, 0]]
        hv = h[edge_local[:, 1]]
        payload = torch.cat([hu, hv, hu * hv, edge_feats], dim=1)
        return self.link_head(payload).squeeze(-1)

    def score_events(
        self, hidden: torch.Tensor, event_local: torch.Tensor, event_feats: torch.Tensor
    ) -> torch.Tensor:
        if event_local.numel() == 0:
            return hidden.new_zeros(0)
        h = hidden[0]
        hu = h[event_local[:, 0]]
        ha = h[event_local[:, 1]]
        hb = h[event_local[:, 2]]
        payload = torch.cat([hu, ha + hb, (ha - hb).abs(), event_feats], dim=1)
        return self.division_head(payload).squeeze(-1)

    def forward(
        self,
        tokens: torch.Tensor,
        edge_local: torch.Tensor,
        edge_feats: torch.Tensor,
        event_local: torch.Tensor,
        event_feats: torch.Tensor,
        pad_mask: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        hidden = self.encode(tokens, pad_mask)
        return (
            self.score_edges(hidden, edge_local, edge_feats),
            self.score_events(hidden, event_local, event_feats),
        )

    # ------------------------------------------------------------------ counts

    def n_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters())


def score_batch(
    model: JointLineageScorer, batch: F.WindowBatch, normalizer: Normalizer
) -> tuple[np.ndarray, np.ndarray]:
    """Score one window. Deterministic, no dropout, gradients off."""
    model.eval()
    with torch.no_grad():
        tokens = torch.from_numpy(normalizer.apply_tokens(batch.tokens))
        edge_feats = torch.from_numpy(normalizer.apply_edges(batch.edge_feats))
        event_feats = torch.from_numpy(normalizer.apply_events(batch.event_feats))
        link, div = model(
            tokens,
            torch.from_numpy(batch.edge_local),
            edge_feats,
            torch.from_numpy(batch.event_local),
            event_feats,
        )
    return link.detach().numpy().astype(np.float64), div.detach().numpy().astype(np.float64)
