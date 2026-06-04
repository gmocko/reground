"""Exception hierarchy for reground.

Exceptions signal *programmer / input* errors only. A failure to ground a claim
is **never** an exception — it is a first-class :class:`~reground.contracts.GroundingResult`
with ``status="ungrounded"`` or ``"ambiguous"`` (handoff §2).
"""

from __future__ import annotations


class RegroundError(Exception):
    """Base class for all reground errors."""


class EmptySourceSetError(RegroundError):
    """Raised when ``ground()`` is called with an empty curated source set.

    Grounding requires at least one candidate source; an empty set is a caller
    bug, not an ``ungrounded`` outcome.
    """


class InvalidClaimError(RegroundError):
    """Raised when a claim has no usable quote to ground."""
