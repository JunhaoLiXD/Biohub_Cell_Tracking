"""Runtime configuration, the fatal-propagation flag, and the combined deadline.

Two things here exist for reasons that are easy to lose:

1. ``FATAL`` — ``write_test_submission`` wraps ``filter_output_graph`` in ``try/except`` and falls
   back to ``fallback_output_graph`` (parent cell 5:2120-2132). A raising exp_067 stage would be
   silently swallowed and the run would report success. So the stage never raises into that handler:
   it records ``FATAL`` and returns the parent graph, and a second injected check immediately after
   the parent's ``try/except`` re-raises outside it.
2. ``Deadline`` — codex_challenge_v1 item 5 requires one budget covering model scoring *and*
   solving, not solver time alone.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any

from .errors import Exp067Deadline

# --------------------------------------------------------------------------------------- env

ENV_ENABLE = "BIOHUB_EXP067_ENABLE"
ENV_MODE = "BIOHUB_EXP067_MODE"
ENV_EXPORT = "BIOHUB_EXP067_EXPORT"
ENV_LABELS = "BIOHUB_EXP067_LABELS"
ENV_LABEL_STEMS = "BIOHUB_EXP067_LABEL_STEMS"
ENV_EXPORT_DIR = "BIOHUB_EXP067_EXPORT_DIR"
ENV_CKPT = "BIOHUB_EXP067_CKPT"
ENV_TOPK = "BIOHUB_EXP067_TOPK"
ENV_BUDGET_S = "BIOHUB_EXP067_BUDGET_S"
ENV_LOWDET_EMB = "BIOHUB_EXP067_EXPORT_LOWDET_EMB"

MODE_DECODE = "decode"  # learned scores + joint MILP
MODE_PARENT = "parent"  # zero-new-evidence control: return the parent graph by identity
VALID_MODES = (MODE_DECODE, MODE_PARENT)


def env_flag(name: str, default: str = "0") -> bool:
    return os.environ.get(name, default).strip() not in {"", "0", "false", "False"}


def env_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    return int(raw) if raw else default


def env_float(name: str, default: float) -> float:
    raw = os.environ.get(name, "").strip()
    return float(raw) if raw else default


# --------------------------------------------------------------- fatal propagation (item 10)

FATAL: str | None = None


def set_fatal(message: str) -> None:
    global FATAL
    if FATAL is None:
        FATAL = message


def clear_fatal() -> None:
    global FATAL
    FATAL = None


def raise_if_fatal() -> None:
    """Injected immediately after the parent's try/except so failures cannot be swallowed."""
    if FATAL is not None:
        raise RuntimeError(f"EXP067 FATAL: {FATAL}")


# ------------------------------------------------------------------------------- deadline

@dataclass
class Deadline:
    """One budget across scoring and solving. ``spend`` is advisory; ``check`` enforces."""

    budget_s: float
    started_at: float = field(default_factory=time.time)
    scoring_s: float = 0.0
    solving_s: float = 0.0

    @property
    def elapsed_s(self) -> float:
        return time.time() - self.started_at

    @property
    def remaining_s(self) -> float:
        return self.budget_s - self.elapsed_s

    def expired(self) -> bool:
        return self.remaining_s <= 0.0

    def check(self, what: str) -> None:
        if self.expired():
            raise Exp067Deadline(
                f"exp067 budget {self.budget_s:.1f}s exhausted during {what} "
                f"(scoring {self.scoring_s:.1f}s, solving {self.solving_s:.1f}s)"
            )

    def add_scoring(self, seconds: float) -> None:
        self.scoring_s += seconds

    def add_solving(self, seconds: float) -> None:
        self.solving_s += seconds


# ----------------------------------------------------------------- environment assertions

#: Pinned in requirements-exp067-cpu.txt; asserted at the entry points that need them.
EXPECTED = {"torch": (2, 14), "scipy": (1, 18), "numpy": (2, 5)}


def _major_minor(version: str) -> tuple[int, int]:
    parts = version.split("+")[0].split(".")
    return int(parts[0]), int(parts[1])


def assert_environment(require: tuple[str, ...] = ("numpy", "scipy", "torch")) -> dict[str, str]:
    """Fail closed on a version skew rather than producing quietly different numbers."""
    observed: dict[str, str] = {}
    problems: list[str] = []
    for name in require:
        try:
            module = __import__(name)
        except ImportError as exc:  # pragma: no cover - environment-dependent
            problems.append(f"{name}: not importable ({exc})")
            continue
        version = getattr(module, "__version__", "?")
        observed[name] = version
        expected = EXPECTED.get(name)
        if expected is not None and _major_minor(version) != expected:
            problems.append(f"{name}: observed {version}, pinned {expected[0]}.{expected[1]}.x")
    if problems:
        raise RuntimeError("exp067 environment mismatch: " + "; ".join(problems))
    return observed


# --------------------------------------------------------------------------- the receipt

@dataclass
class Receipt:
    """Everything a reader needs to tell a real solve from a fallback. Never omit a revert."""

    dataset: str
    mode: str
    active: bool = False
    reason: str | None = None
    n_final_nodes: int = 0
    n_parent_edges: int = 0
    n_reconsiderable_nodes: int = 0
    n_fixed_edges: int = 0
    n_free_edge_vars: int = 0
    n_event_vars: int = 0
    n_components: int = 0
    n_components_solved: int = 0
    n_components_reverted: int = 0
    revert_reasons: dict[str, int] = field(default_factory=dict)
    n_transitions: int = 0
    edges_added: int = 0
    edges_removed: int = 0
    edges_kept: int = 0
    divisions_before: int = 0
    divisions_after: int = 0
    divisions_reclaimed: int = 0
    alt_dropped_node_absent: int = 0
    solver_backend: str = "scipy.optimize.milp"
    scoring_seconds: float = 0.0
    solving_seconds: float = 0.0
    total_seconds: float = 0.0
    division_head_trained: bool = False
    backbone_provenance: str = "POSSIBLE_OVERLAP_UNKNOWN_PROVENANCE"
    notes: list[str] = field(default_factory=list)

    def revert(self, reason: str, count: int = 1) -> None:
        self.n_components_reverted += count
        self.revert_reasons[reason] = self.revert_reasons.get(reason, 0) + count

    def note(self, message: str) -> None:
        if message not in self.notes:
            self.notes.append(message)

    def to_dict(self) -> dict[str, Any]:
        payload = dict(self.__dict__)
        payload["revert_fraction"] = (
            self.n_components_reverted / self.n_components if self.n_components else 0.0
        )
        return payload
