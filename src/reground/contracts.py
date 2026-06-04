"""Core domain contracts for reground.

Single source of truth for the public data model (spec RG-001 §4). These are
plain, immutable value objects: no behaviour, no third-party dependencies.

Docs link here, they do not duplicate these definitions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

#: Outcome of grounding. The weakest link across alignment + provenance.
GroundingStatus = Literal["grounded", "ungrounded", "ambiguous"]

#: Which matcher produced the alignment (internal tie-break signals are NOT
#: exposed here — see DL / handoff §3: the order-guard is never a public method).
GroundingMethod = Literal["exact", "jaccard"]


@dataclass(frozen=True, slots=True)
class Citation:
    """An inline ``[index]`` marker inside a source's text.

    Inline ``[N]`` markers in :attr:`SourceDocument.text` map to a Citation by
    its :attr:`index`.
    """

    index: int
    url: str
    title: str | None = None


@dataclass(frozen=True, slots=True)
class SourceDocument:
    """One unit of the curated source set a claim is grounded against.

    The harness grounds a :class:`Claim` against a *list* of these (the handful
    of sources the upstream retrieval already selected), never a single document.

    Note: ``citations`` is a ``tuple`` (not ``list`` as written in spec §4) so the
    value object is genuinely immutable under ``frozen=True``.
    """

    source_id: str
    text: str
    citations: tuple[Citation, ...] = ()
    url: str | None = None


@dataclass(frozen=True, slots=True)
class Claim:
    """A final unit of evidence, produced anywhere downstream in an agent chain."""

    claim_id: str
    quote: str


@dataclass(frozen=True, slots=True)
class GroundingResult:
    """The single, explicit return contract of :func:`reground.ground`.

    Records not just the answer but *how* it was reached and *why*, so failure
    modes are auditable. Returned for every input, including explicit refusals
    (``ungrounded`` / ``ambiguous``), where ``grounded_quote``, ``source_id`` and
    ``source_url`` are all ``None``.
    """

    claim_id: str
    original_quote: str
    grounded_quote: str | None
    source_id: str | None
    source_url: str | None
    status: GroundingStatus
    method: GroundingMethod
    score: float
    margin: float
    reason: str
    nli_score: float | None = None
