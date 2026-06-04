"""The thesis. These tests must fail loudly if reground ever produces a
confident WRONG attribution. ``fabricated -> null``, ``ambiguous -> null``,
``wrong-citation-nearby -> null`` (handoff §4)."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from reground import Citation, Claim, SourceDocument, ground


def test_ac4_fabricated_quote_refuses_attribution(photosynthesis_source):
    """AC4: no sufficient overlap -> ungrounded, null provenance, null span."""
    result = ground(
        Claim("c", "Quantum entanglement enables faster than light communication"),
        [photosynthesis_source],
    )
    assert result.status == "ungrounded"
    assert result.source_url is None
    assert result.source_id is None
    assert result.grounded_quote is None


def test_ac5_two_equal_matches_resolve_to_ambiguous(ambiguous_bee_sources):
    """AC5: near-equal matches across two sources -> ambiguous, not a guess."""
    result = ground(
        Claim("c", "Honeybees communicate the location of food using a waggle dance"),
        ambiguous_bee_sources,
    )
    assert result.status == "ambiguous"
    assert result.source_url is None
    assert result.grounded_quote is None
    assert "margin" in result.reason


def test_ac6_grounded_text_with_far_citation_does_not_attribute():
    """AC6: text grounds but the only citation is beyond the window -> no URL."""
    source = SourceDocument(
        source_id="s",
        text=(
            "Honeybees perform a waggle dance to share food locations with the hive. "
            "An unrelated filler sentence sits in between. "
            "A distant sentence carries the only citation [1]."
        ),
        citations=(Citation(index=1, url="https://example.com/distant"),),
    )
    result = ground(
        Claim("c", "Honeybees perform a waggle dance to share food locations with the hive"),
        [source],
    )
    assert result.status != "grounded"
    assert result.source_url is None


def test_ac6_conflicting_nearby_citations_do_not_attribute():
    """AC6: aligned span with conflicting markers -> no confident URL."""
    source = SourceDocument(
        source_id="s",
        text="Honeybees perform a waggle dance to share food locations [1][2].",
        citations=(
            Citation(index=1, url="https://example.com/one"),
            Citation(index=2, url="https://example.com/two"),
        ),
    )
    result = ground(
        Claim("c", "Honeybees perform a waggle dance to share food locations"),
        [source],
    )
    assert result.status != "grounded"
    assert result.source_url is None


def test_compound_claim_with_fabricated_tail_refuses(photosynthesis_source):
    """Second wave: a true head + fabricated tail must not ground — the
    unsupported-residual guard refuses tokens absent from every source."""
    result = ground(
        Claim(
            "c",
            "Photosynthesis converts light energy into chemical energy "
            "and unicorns cure ancient diseases",
        ),
        [photosynthesis_source],
    )
    assert result.status == "ungrounded"
    assert result.source_url is None
    assert result.grounded_quote is None
    assert "unsupported" in result.reason


def test_same_source_near_equal_sentences_with_different_citations_refuse():
    """Second wave: the within-source margin. Two near-equal sentences inside
    ONE source with different citations must not yield a confident URL."""
    source = SourceDocument(
        source_id="s",
        text=(
            "Cats sleep many hours during the day to conserve energy [1]. "
            "Dogs sleep many hours during the day to conserve energy [2]."
        ),
        citations=(
            Citation(index=1, url="https://example.com/cats"),
            Citation(index=2, url="https://example.com/dogs"),
        ),
    )
    result = ground(
        Claim("c", "Dogs and cats sleep many hours during the day to conserve energy"),
        [source],
    )
    assert result.status == "ambiguous"
    assert result.source_url is None
    assert result.grounded_quote is None
    assert "within margin inside" in result.reason


def test_same_source_near_equal_sentences_same_url_still_grounds():
    """Recall preserved: a within-source tie whose sentences resolve to ONE
    citation URL stays a confident attribution (mirrors the existing
    "multiple markers, single URL" provenance rule)."""
    same = "https://example.com/waggle-dance"
    source = SourceDocument(
        source_id="s",
        text=(
            "Honeybees use a waggle dance to share food locations [1]. "
            "Honeybees use a waggle dance to signal food locations [1]."
        ),
        citations=(Citation(index=1, url=same),),
    )
    result = ground(
        Claim("c", "Honeybees use a waggle dance to communicate food locations"),
        [source],
    )
    assert result.status == "grounded"
    assert result.source_url == same


# A vocabulary the source is built from; fabricated quotes are drawn from a
# provably disjoint token space so there is never genuine support.
_SOURCE_VOCAB = "alpha beta gamma delta epsilon zeta eta theta iota kappa"


@given(
    st.lists(
        st.from_regex(r"zq[a-hj-z]{3,6}", fullmatch=True),
        min_size=1,
        max_size=12,
    )
)
def test_property_no_shared_tokens_never_attributes(disjoint_words):
    """Invariant: a quote sharing NO content tokens with any source is never
    grounded and never carries a source_url — for *any* such quote."""
    source = SourceDocument(
        source_id="s",
        text=f"The source sentence talks about {_SOURCE_VOCAB} only [1].",
        citations=(Citation(index=1, url="https://example.com/src"),),
    )
    quote = " ".join(disjoint_words)
    result = ground(Claim("c", quote), [source])
    assert result.source_url is None
    assert result.grounded_quote is None
    assert result.status != "grounded"
