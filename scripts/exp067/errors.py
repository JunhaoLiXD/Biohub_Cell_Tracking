"""Typed failures. Every one of these is fail-closed: nothing here is recoverable by guessing."""


class Exp067Error(Exception):
    """Base class for every exp_067 failure."""


class Exp067SchemaError(Exp067Error):
    """An export, label file or checkpoint does not match the declared schema."""


class Exp067ProvenanceError(Exp067Error):
    """A final-graph node could not be traced to its detector row, or a map is not injective."""


class Exp067FeatureUnavailable(Exp067Error):
    """A feature the schema declares mandatory is missing.

    Optional features that are legitimately absent are represented by a mask bit and a
    masked-out value; they never raise. This is only for required features.
    """


class Exp067WindowOverflow(Exp067Error):
    """A single source's required token set does not fit the window cap.

    Required by codex_challenge_v1 item 4: an event that cannot fit must fail, not be dropped.
    """


class Exp067Deadline(Exp067Error):
    """The combined scoring + solving budget was exhausted."""


class Exp067InsufficientSupervision(Exp067Error):
    """A training fold has too few unmasked positives to train a head at all."""
