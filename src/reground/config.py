"""Tunable thresholds for the deterministic grounder.

All knobs live here as a single, immutable :class:`GroundingConfig` so they can
be injected, tested, and — per DL-5 — *pre-registered*: the values below are
frozen and recorded in the README **before** the benchmark is scored, so no
threshold is ever reverse-fitted to the cases.

The defaults are PROVISIONAL until the Phase 4 freeze (spec §7). Treat them as
placeholders; the locked values are committed alongside the benchmark matrix.
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
        fuzzy_citation_threshold: Minimum ratio for the bounded fuzzy fallback
            when an exact verbatim span is not found inside a source's text.
    """

    min_shared_tokens: int = 4
    jaccard_threshold: float = 0.5
    margin: float = 0.1
    citation_window: int = 1
    fuzzy_citation_threshold: float = 0.85


#: The default, pre-registered configuration used by :func:`reground.ground`.
DEFAULT_CONFIG = GroundingConfig()
