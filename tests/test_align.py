"""Alignment + token-overlap unit tests (spec §5, Phase 3)."""

from __future__ import annotations

from reground.align import align_quote


def test_exact_quote_aligns_via_exact(photosynthesis_source):
    """AC1: a verbatim quote aligns with method='exact'."""
    alignment = align_quote(
        "Photosynthesis converts light energy into chemical energy",
        [photosynthesis_source],
    )
    assert alignment.status == "grounded"
    assert alignment.method == "exact"
    assert alignment.score == 1.0
    assert alignment.best is not None
    assert alignment.best.source_id == "src-photo"
    assert alignment.best.sentence_index == 0


def test_minor_paraphrase_aligns_via_jaccard(photosynthesis_source):
    """AC2: a reworded quote aligns to the verbatim span via token overlap."""
    alignment = align_quote(
        "light energy is converted into chemical energy by photosynthesis",
        [photosynthesis_source],
    )
    assert alignment.status == "grounded"
    assert alignment.method == "jaccard"
    assert alignment.score >= 0.5
    assert alignment.best is not None
    assert alignment.best.sentence_index == 0


def test_reordered_words_match_where_char_level_fails(photosynthesis_source):
    """Category 3: word-set overlap matches a pure reordering."""
    alignment = align_quote(
        "energy chemical into light photosynthesis converts",
        [photosynthesis_source],
    )
    assert alignment.status == "grounded"
    assert alignment.method == "jaccard"
    assert alignment.score == 1.0  # identical content-token set


def test_fragment_combination_aligns_longest_fragment(photosynthesis_source):
    """AC3: a '...'-joined quote aligns its longest grounded fragment."""
    alignment = align_quote(
        "Photosynthesis converts light energy ... somewhere unrelated entirely",
        [photosynthesis_source],
    )
    assert alignment.status == "grounded"
    assert alignment.fragment == "Photosynthesis converts light energy"
    assert alignment.best is not None
    assert alignment.best.sentence_index == 0


def test_fabricated_quote_is_ungrounded(photosynthesis_source):
    """A quote with negligible overlap does not align."""
    alignment = align_quote(
        "Quantum entanglement enables faster than light communication",
        [photosynthesis_source],
    )
    assert alignment.status == "ungrounded"


def test_insufficient_shared_tokens_is_ungrounded(photosynthesis_source):
    """A short quote below min_shared_tokens is refused even if it overlaps."""
    alignment = align_quote("light energy", [photosynthesis_source])
    assert alignment.status == "ungrounded"
    assert "shared content token" in alignment.reason


def test_picks_correct_source_in_curated_set(photosynthesis_source, water_source):
    """Across the curated set, alignment selects the genuinely matching source."""
    alignment = align_quote(
        "Photosynthesis converts light energy into chemical energy",
        [water_source, photosynthesis_source],
    )
    assert alignment.status == "grounded"
    assert alignment.best is not None
    assert alignment.best.source_id == "src-photo"
