"""Shared neutral fixtures. Synthetic corpus only — zero PII (spec R4)."""

from __future__ import annotations

import pytest

from reground import Citation, SourceDocument

PHOTOSYNTHESIS_URL = "https://example.com/photosynthesis"
LEAVES_URL = "https://example.com/leaves"
EVAPORATION_URL = "https://example.com/evaporation"
WAGGLE_URL_A = "https://example.com/waggle-dance"
WAGGLE_URL_B = "https://example.com/bee-foraging"


@pytest.fixture
def photosynthesis_source() -> SourceDocument:
    return SourceDocument(
        source_id="src-photo",
        text=(
            "Photosynthesis converts light energy into chemical energy [1]. "
            "The process occurs mainly in the leaves of plants [2]."
        ),
        citations=(
            Citation(index=1, url=PHOTOSYNTHESIS_URL, title="Photosynthesis basics"),
            Citation(index=2, url=LEAVES_URL, title="Plant leaves"),
        ),
        url="https://example.com/biology/photosynthesis",
    )


@pytest.fixture
def water_source() -> SourceDocument:
    return SourceDocument(
        source_id="src-water",
        text=(
            "Water evaporates from oceans and lakes [1]. "
            "It later condenses into clouds and returns as precipitation [2]."
        ),
        citations=(
            Citation(index=1, url=EVAPORATION_URL, title="Evaporation"),
            Citation(index=2, url="https://example.com/precipitation", title="Precipitation"),
        ),
        url="https://example.com/earth/water-cycle",
    )


@pytest.fixture
def ambiguous_bee_sources() -> list[SourceDocument]:
    """Two sources whose target sentence is identical -> ambiguous attribution."""
    sentence = "Honeybees communicate the location of food using a waggle dance [1]."
    return [
        SourceDocument(
            source_id="src-bee-1",
            text=sentence,
            citations=(Citation(index=1, url=WAGGLE_URL_A),),
            url="https://example.com/insects/honeybee-foraging",
        ),
        SourceDocument(
            source_id="src-bee-2",
            text=sentence,
            citations=(Citation(index=1, url=WAGGLE_URL_B),),
            url="https://example.com/insects/bee-communication",
        ),
    ]
