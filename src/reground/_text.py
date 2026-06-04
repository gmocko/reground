"""Internal, stdlib-only text utilities.

Deterministic tokenization, sentence splitting, and citation-marker handling
shared by :mod:`reground.align` and :mod:`reground.provenance`. Not part of the
public API — names are private and may change.
"""

from __future__ import annotations

import re

# A sentence ends at . ! ? followed by whitespace. Good enough for the neutral
# synthetic corpus; abbreviation handling is intentionally out of scope.
_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")

# Inline provenance markers: [1], [42], ...
_CITATION_MARKER = re.compile(r"\[(\d+)\]")

# A marker plus the whitespace that precedes it, so removing it leaves no gap.
_MARKER_WITH_LEADING_WS = re.compile(r"\s*\[\d+\]")

# Quote fragments may be joined with "..." or the ellipsis character.
_FRAGMENT_SEPARATOR = re.compile(r"\s*(?:\.\.\.|…)\s*")

# Word = run of ASCII letters/digits, lowercased before matching.
_WORD = re.compile(r"[a-z0-9]+")

_WHITESPACE = re.compile(r"\s+")

#: Minimal English stop-word set. Function words carry no grounding signal and
#: would let short, generic sentences over-match (DL-2). Kept small and explicit.
STOPWORDS: frozenset[str] = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "been",
        "being",
        "but",
        "by",
        "for",
        "from",
        "had",
        "has",
        "have",
        "in",
        "into",
        "is",
        "it",
        "its",
        "of",
        "on",
        "or",
        "that",
        "the",
        "their",
        "them",
        "they",
        "this",
        "to",
        "was",
        "were",
        "which",
        "with",
    }
)


def normalize_whitespace(text: str) -> str:
    """Collapse runs of whitespace and strip the ends."""
    return _WHITESPACE.sub(" ", text).strip()


def split_sentences(text: str) -> list[str]:
    """Split ``text`` into non-empty, stripped sentences (markers preserved)."""
    return [s.strip() for s in _SENTENCE_BOUNDARY.split(text.strip()) if s.strip()]


def split_fragments(quote: str) -> list[str]:
    """Split a quote on ``...`` into fragments; always returns at least one."""
    parts = [p.strip() for p in _FRAGMENT_SEPARATOR.split(quote) if p.strip()]
    return parts or [quote.strip()]


def strip_markers(text: str) -> str:
    """Return ``text`` with ``[N]`` markers (and their leading space) removed."""
    return normalize_whitespace(_MARKER_WITH_LEADING_WS.sub("", text))


def citation_indices(text: str) -> list[int]:
    """Return the citation indices appearing in ``text``, in order."""
    return [int(m.group(1)) for m in _CITATION_MARKER.finditer(text)]


def content_tokens(text: str) -> frozenset[str]:
    """Return the set of lowercased content tokens (markers + stop-words removed)."""
    cleaned = _CITATION_MARKER.sub(" ", text.lower())
    return frozenset(t for t in _WORD.findall(cleaned) if t not in STOPWORDS)


def jaccard(left: frozenset[str], right: frozenset[str]) -> float:
    """Jaccard overlap of two token sets; ``0.0`` when both are empty."""
    if not left and not right:
        return 0.0
    union = left | right
    if not union:
        return 0.0
    return len(left & right) / len(union)
