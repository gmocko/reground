"""Verbatim span -> ``[N]`` marker -> source URL, with an ambiguity guard.

Pure, deterministic, stdlib-only. Given the source and the index of the aligned
sentence, find the nearest confident citation marker and resolve it to a URL.

Safety (defends the thesis from the provenance side):

* a marker beyond ``config.citation_window`` sentences is *too far* -> unmapped
  (the text is grounded but its provenance is not; AC6 / category 8);
* multiple distinct markers in range with no single nearest -> unmapped, unless
  they all resolve to the same URL (AC6 / category 9);
* an index with no matching :class:`~reground.contracts.Citation` -> unmapped.

"Unmapped" is never a wrong URL — it is ``source_url=None``, which the harness
turns into a refusal.
"""

from __future__ import annotations

from dataclasses import dataclass

from reground._text import citation_indices, split_sentences
from reground.config import DEFAULT_CONFIG, GroundingConfig
from reground.contracts import SourceDocument


@dataclass(frozen=True, slots=True)
class Provenance:
    """Outcome of mapping an aligned span to a provenance URL."""

    mapped: bool
    source_url: str | None
    citation_index: int | None
    reason: str


def map_provenance(
    source: SourceDocument,
    sentence_index: int,
    config: GroundingConfig = DEFAULT_CONFIG,
) -> Provenance:
    """Map the aligned sentence to a confident citation URL, or refuse."""
    sentences = split_sentences(source.text)
    if not (0 <= sentence_index < len(sentences)):
        return _unmapped("aligned sentence index out of range")

    indices = _markers_in_range(sentences, sentence_index, config.citation_window)
    distinct = list(dict.fromkeys(indices))  # de-dupe, preserve order

    if not distinct:
        return _unmapped("no citation marker within window")

    url_by_index = {citation.index: citation.url for citation in source.citations}

    if len(distinct) > 1:
        urls = {url_by_index.get(index) for index in distinct}
        if len(urls) == 1 and None not in urls:
            # Conflicting markers, but all point at the same URL -> still confident.
            return _mapped(distinct[0], url_by_index[distinct[0]], "multiple markers, single URL")
        return _unmapped(f"multiple conflicting citations {distinct} with no confident nearest")

    index = distinct[0]
    url = url_by_index.get(index)
    if url is None:
        return _unmapped(f"citation [{index}] has no matching source citation")
    return _mapped(index, url, f"mapped to citation [{index}]")


def _markers_in_range(sentences: list[str], center: int, window: int) -> list[int]:
    in_center = citation_indices(sentences[center])
    if in_center:
        return in_center
    # Widen outward; the nearest non-empty distance wins (closest markers only).
    for distance in range(1, window + 1):
        found: list[int] = []
        for neighbour in (center - distance, center + distance):
            if 0 <= neighbour < len(sentences):
                found.extend(citation_indices(sentences[neighbour]))
        if found:
            return found
    return []


def _mapped(index: int, url: str, reason: str) -> Provenance:
    return Provenance(mapped=True, source_url=url, citation_index=index, reason=reason)


def _unmapped(reason: str) -> Provenance:
    return Provenance(mapped=False, source_url=None, citation_index=None, reason=reason)
