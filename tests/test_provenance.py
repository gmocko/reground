"""Citation mapping + ambiguity-guard tests (spec §5, Phase 3)."""

from __future__ import annotations

from reground import Citation, SourceDocument
from reground.provenance import map_provenance


def test_single_marker_maps_to_url(photosynthesis_source):
    """AC1: the lone marker in the aligned sentence resolves to its URL."""
    prov = map_provenance(photosynthesis_source, sentence_index=0)
    assert prov.mapped is True
    assert prov.source_url == photosynthesis_source.citations[0].url
    assert prov.citation_index == 1


def test_second_sentence_maps_to_its_own_marker(photosynthesis_source):
    prov = map_provenance(photosynthesis_source, sentence_index=1)
    assert prov.source_url == photosynthesis_source.citations[1].url
    assert prov.citation_index == 2


def test_marker_beyond_window_is_unmapped():
    """AC6 / category 8: a citation further than the window stays unmapped."""
    source = SourceDocument(
        source_id="s",
        text=(
            "The aligned sentence carries no marker here. "
            "A filler sentence also carries nothing. "
            "A distant sentence finally cites a source [1]."
        ),
        citations=(Citation(index=1, url="https://example.com/distant"),),
    )
    prov = map_provenance(source, sentence_index=0)  # default window = 1
    assert prov.mapped is False
    assert prov.source_url is None


def test_multiple_conflicting_markers_are_unmapped():
    """AC6 / category 9: distinct markers with different URLs -> unmapped."""
    source = SourceDocument(
        source_id="s",
        text="A sentence with two conflicting citations [1][2].",
        citations=(
            Citation(index=1, url="https://example.com/one"),
            Citation(index=2, url="https://example.com/two"),
        ),
    )
    prov = map_provenance(source, sentence_index=0)
    assert prov.mapped is False
    assert prov.source_url is None


def test_multiple_markers_same_url_still_maps():
    """Conflicting markers that resolve to one URL remain confident."""
    same = "https://example.com/same"
    source = SourceDocument(
        source_id="s",
        text="A sentence with two markers pointing at one URL [1][2].",
        citations=(Citation(index=1, url=same), Citation(index=2, url=same)),
    )
    prov = map_provenance(source, sentence_index=0)
    assert prov.mapped is True
    assert prov.source_url == same


def test_index_without_matching_citation_is_unmapped():
    source = SourceDocument(
        source_id="s",
        text="A sentence citing an index with no backing citation [9].",
        citations=(Citation(index=1, url="https://example.com/one"),),
    )
    prov = map_provenance(source, sentence_index=0)
    assert prov.mapped is False
    assert prov.source_url is None
