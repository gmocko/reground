"""Documented limits, encoded as STRICT xfails — executable documentation.

Each test asserts the behaviour we would *like* but deliberately do not have,
and is expected to fail. ``strict=True`` means that if one ever starts
passing, the build breaks: the README "Limits" section must then be updated
consciously, never silently outgrown.
"""

from __future__ import annotations

import pytest

from reground import Citation, Claim, SourceDocument, ground


@pytest.mark.xfail(
    strict=True,
    reason=(
        "single-source semantic reversal: token overlap cannot tell 'the dog "
        "chased the cat' from 'the cat chased the dog' inside one source with "
        "one matching sentence; out of scope for the deterministic core "
        "(future NLI gate territory). Two-source and two-sentence variants ARE "
        "caught — by the cross-source and within-source margin rules."
    ),
)
def test_single_source_semantic_reversal_would_refuse():
    source = SourceDocument(
        source_id="s",
        text="The dog chased the cat across the garden [1].",
        citations=(Citation(index=1, url="https://example.com/chase"),),
    )
    result = ground(Claim("c", "The cat chased the dog across the garden"), [source])
    assert result.status != "grounded"


@pytest.mark.xfail(
    strict=True,
    reason=(
        "AC3 grades the strongest fragment of a '...'-joined quote: a "
        "fabricated fragment does not block the grounded one. The verdict "
        "applies to grounded_quote, never the whole original_quote — callers "
        "must not present the full claim as verified."
    ),
)
def test_ellipsis_smuggled_fabricated_fragment_would_refuse(photosynthesis_source):
    result = ground(
        Claim("c", "Photosynthesis converts light energy ... unicorns cure ancient diseases"),
        [photosynthesis_source],
    )
    assert result.status != "grounded"


@pytest.mark.xfail(
    strict=True,
    reason=(
        "the unsupported-residual guard tolerates max_unsupported_tokens (2) "
        "to allow honest inflectional residue, so a fabricated tail of <= 2 "
        "content tokens still rides through on a grounded head"
    ),
)
def test_two_token_fabricated_tail_would_refuse(photosynthesis_source):
    result = ground(
        Claim("c", "Photosynthesis converts light energy into chemical energy and unicorns exist"),
        [photosynthesis_source],
    )
    assert result.status != "grounded"
