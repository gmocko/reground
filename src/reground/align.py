"""Quote -> verbatim source span alignment across the curated set.

Pure, deterministic, stdlib-only. Given a claim quote and the curated list of
:class:`~reground.contracts.SourceDocument`, find the best verbatim source
sentence the quote aligns to, applying the two safety rules that defend the
thesis:

* **minimum shared content tokens** — reject matches with too little overlap so
  short/generic sentences can't latch on (DL-2, R3);
* **margin** — when the best and second-best *sources* score within
  ``config.margin`` of each other, return ``ambiguous`` rather than guess (AC5).

This module knows nothing about provenance/URLs — that is the next stage. The
internal :class:`Alignment` it returns is consumed by :mod:`reground.harness`.
"""

from __future__ import annotations

from dataclasses import dataclass

from reground._text import (
    content_tokens,
    jaccard,
    split_fragments,
    split_sentences,
    strip_markers,
)
from reground.config import DEFAULT_CONFIG, GroundingConfig
from reground.contracts import GroundingMethod, GroundingStatus, SourceDocument

_STATUS_RANK: dict[GroundingStatus, int] = {"grounded": 2, "ambiguous": 1, "ungrounded": 0}


@dataclass(frozen=True, slots=True)
class Candidate:
    """The best-matching sentence within a single source."""

    source_id: str
    sentence_index: int
    span: str  # verbatim sentence text, markers still present
    score: float
    method: GroundingMethod
    shared_tokens: int


@dataclass(frozen=True, slots=True)
class Alignment:
    """Outcome of aligning a quote across the curated set (pre-provenance)."""

    status: GroundingStatus
    fragment: str
    best: Candidate | None
    score: float
    margin: float
    method: GroundingMethod
    shared_tokens: int
    reason: str


def align_quote(
    quote: str,
    sources: list[SourceDocument],
    config: GroundingConfig = DEFAULT_CONFIG,
) -> Alignment:
    """Align ``quote`` across ``sources``, choosing the strongest fragment.

    For a ``...``-joined quote each fragment is aligned independently and the
    strongest result is kept (grounded > ambiguous > ungrounded, then by score,
    then by longer fragment) — this realises "the longest grounded fragment
    aligns" (AC3, AC9).
    """
    best: Alignment | None = None
    for fragment in split_fragments(quote):
        candidate = _align_fragment(fragment, sources, config)
        if best is None or _alignment_key(candidate) > _alignment_key(best):
            best = candidate
    # split_fragments always returns at least one fragment, so best is set.
    assert best is not None
    return best


def _alignment_key(alignment: Alignment) -> tuple[int, float, int]:
    return (
        _STATUS_RANK[alignment.status],
        alignment.score,
        len(content_tokens(alignment.fragment)),
    )


def _align_fragment(
    fragment: str,
    sources: list[SourceDocument],
    config: GroundingConfig,
) -> Alignment:
    fragment_tokens = content_tokens(fragment)
    fragment_norm = strip_markers(fragment).lower()

    per_source: list[Candidate] = []
    for source in sources:
        best_in_source = _best_sentence(source, fragment_tokens, fragment_norm)
        if best_in_source is not None:
            per_source.append(best_in_source)

    per_source.sort(key=_candidate_key, reverse=True)
    best = per_source[0] if per_source else None
    second = per_source[1] if len(per_source) > 1 else None

    if best is None:
        return _ungrounded(fragment, "no source sentences to align against")

    margin = best.score - (second.score if second is not None else 0.0)

    if best.shared_tokens < config.min_shared_tokens:
        return _ungrounded(
            fragment,
            f"only {best.shared_tokens} shared content token(s) (< min {config.min_shared_tokens})",
            best=best,
            margin=margin,
        )

    if best.method == "jaccard" and best.score < config.jaccard_threshold:
        return _ungrounded(
            fragment,
            f"best score {best.score:.2f} < threshold {config.jaccard_threshold:.2f}",
            best=best,
            margin=margin,
        )

    if second is not None and margin < config.margin:
        return Alignment(
            status="ambiguous",
            fragment=fragment,
            best=best,
            score=best.score,
            margin=margin,
            method=best.method,
            shared_tokens=best.shared_tokens,
            reason=(
                f"two sources within margin: best {best.score:.2f} vs "
                f"second {second.score:.2f} (margin {margin:.2f} < {config.margin:.2f})"
            ),
        )

    return Alignment(
        status="grounded",
        fragment=fragment,
        best=best,
        score=best.score,
        margin=margin,
        method=best.method,
        shared_tokens=best.shared_tokens,
        reason=(
            f"aligned via {best.method} to sentence {best.sentence_index} of "
            f"{best.source_id} (score {best.score:.2f}, margin {margin:.2f}, "
            f"{best.shared_tokens} shared tokens)"
        ),
    )


def _best_sentence(
    source: SourceDocument,
    fragment_tokens: frozenset[str],
    fragment_norm: str,
) -> Candidate | None:
    best: Candidate | None = None
    for index, sentence in enumerate(split_sentences(source.text)):
        sentence_norm = strip_markers(sentence).lower()
        sentence_tokens = content_tokens(sentence)
        shared = len(fragment_tokens & sentence_tokens)

        if fragment_norm and fragment_norm in sentence_norm:
            score: float = 1.0
            method: GroundingMethod = "exact"
            shared_tokens = shared or len(fragment_tokens)
        else:
            score = jaccard(fragment_tokens, sentence_tokens)
            method = "jaccard"
            shared_tokens = shared

        candidate = Candidate(
            source_id=source.source_id,
            sentence_index=index,
            span=sentence,
            score=score,
            method=method,
            shared_tokens=shared_tokens,
        )
        if best is None or _candidate_key(candidate) > _candidate_key(best):
            best = candidate
    return best


def _candidate_key(candidate: Candidate) -> tuple[float, int, int]:
    # Prefer higher score, then more shared tokens, then exact over jaccard.
    return (candidate.score, candidate.shared_tokens, 1 if candidate.method == "exact" else 0)


def _ungrounded(
    fragment: str,
    reason: str,
    *,
    best: Candidate | None = None,
    margin: float = 0.0,
) -> Alignment:
    return Alignment(
        status="ungrounded",
        fragment=fragment,
        best=best,
        score=best.score if best is not None else 0.0,
        margin=margin,
        method=best.method if best is not None else "jaccard",
        shared_tokens=best.shared_tokens if best is not None else 0,
        reason=reason,
    )
