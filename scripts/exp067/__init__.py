"""exp_067 — learned local-temporal evidence with a joint continuation/division decoder.

Specification: ``experiments/exp_067_temporal_joint_lineage/proposal_v1.md`` as amended by
``codex_challenge_v1.md``; the binding record is ``revision_acceptance_v2.md``.

Nothing in this package touches the leaderboard, launches a kernel, or mutates project state.
"""

from .errors import (
    Exp067Deadline,
    Exp067Error,
    Exp067FeatureUnavailable,
    Exp067InsufficientSupervision,
    Exp067ProvenanceError,
    Exp067SchemaError,
    Exp067WindowOverflow,
)

__all__ = [
    "Exp067Deadline",
    "Exp067Error",
    "Exp067FeatureUnavailable",
    "Exp067InsufficientSupervision",
    "Exp067ProvenanceError",
    "Exp067SchemaError",
    "Exp067WindowOverflow",
]
