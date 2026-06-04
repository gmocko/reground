"""Tunable thresholds for the deterministic grounder.

All knobs live here as a single, immutable :class:`GroundingConfig` so they can
be injected, tested, and — per DL-5 — *pre-registered*: the values below were
frozen and recorded in ``benchmark/README.md`` **before** the benchmark was
scored, so no threshold is ever reverse-fitted to the cases. Changing them
invalidates the published matrix — re-run and re-publish if you do.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GroundingConfig:
    """Safety + matching thresholds for :func:`reground.ground`.

    Attributes:
        min_shared_tokens: Minimum shared *content* tokens between a claim quote
            and a source sentence before any match is considered (DL-3, R3).
            Below this, the candidate is rejected outright — guards against
            token-overlap latching onto short, generic sentences.
        jaccard_threshold: Minimum Jaccard token-overlap score for a paraphrase
            to align to a verbatim span (AC2). Below it, the claim is ungrounded.
        margin: Minimum gap between the best and second-best candidate score.
            When the top two are within ``margin``, the result is ``ambiguous``
            rather than a guess (AC5, R3) — the core defence of the thesis.
        citation_window: How many sentences on each side of the aligned span are
            searched for the nearest ``[N]`` marker when mapping provenance (AC6).
    """

    min_shared_tokens: int = 4
    jaccard_threshold: float = 0.5
    margin: float = 0.1
    citation_window: int = 1


#: The default, pre-registered configuration used by :func:`reground.ground`.
DEFAULT_CONFIG = GroundingConfig()
