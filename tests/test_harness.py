"""End-to-end ground() contract tests (spec §5, Phase 3)."""

from __future__ import annotations

import pytest

from reground import (
    Claim,
    EmptySourceSetError,
    GroundingResult,
    InvalidClaimError,
    ground,
)


def test_ac1_exact_quote_grounds_with_provenance(photosynthesis_source):
    result = ground(
        Claim("c1", "Photosynthesis converts light energy into chemical energy"),
        [photosynthesis_source],
    )
    assert result.status == "grounded"
    assert result.method == "exact"
    assert result.source_id == "src-photo"
    assert result.source_url == photosynthesis_source.citations[0].url
    assert result.grounded_quote is not None
    assert result.grounded_quote.startswith("Photosynthesis converts light energy")
    assert "[1]" not in result.grounded_quote  # markers stripped from the span


def test_ac2_paraphrase_grounds_via_jaccard(photosynthesis_source):
    result = ground(
        Claim("c2", "light energy is converted into chemical energy by photosynthesis"),
        [photosynthesis_source],
    )
    assert result.status == "grounded"
    assert result.method == "jaccard"
    assert result.source_url == photosynthesis_source.citations[0].url


def test_ac9_multi_source_grounds_without_false_attribution(photosynthesis_source, water_source):
    """AC9: a claim matching one source grounds to it, never the unrelated one."""
    result = ground(
        Claim("c9", "Photosynthesis converts light energy into chemical energy"),
        [water_source, photosynthesis_source],
    )
    assert result.status == "grounded"
    assert result.source_id == "src-photo"
    assert result.source_url == photosynthesis_source.citations[0].url


def test_every_input_returns_a_grounding_result(photosynthesis_source):
    """Even a refusal is a GroundingResult, never an exception."""
    result = ground(
        Claim("c", "totally unrelated fabricated assertion xyzzy"),
        [photosynthesis_source],
    )
    assert isinstance(result, GroundingResult)
    assert result.status == "ungrounded"


def test_empty_source_set_raises(photosynthesis_source):
    with pytest.raises(EmptySourceSetError):
        ground(Claim("c", "anything"), [])


def test_empty_quote_raises(photosynthesis_source):
    with pytest.raises(InvalidClaimError):
        ground(Claim("c", "   "), [photosynthesis_source])
