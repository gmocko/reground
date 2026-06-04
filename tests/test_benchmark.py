"""Regression gate over the frozen benchmark dataset.

``benchmark/run_benchmark.py`` *prints* the matrix; this test *enforces* it on
every pytest run, so a safety regression cannot pass CI as a silently
different printout:

* **safety floor** — a grounded verdict must point at the expected source
  (false-attribution stays 0, asserted per case, loudly);
* every expected refusal stays refused, with the expected refusal type;
* **over-refusals are pinned** to the known, documented set — shrinking it is
  an improvement (update the set), growing it is a recall regression.
"""

from __future__ import annotations

import pytest

from reground import Claim, GroundingResult, ground
from run_benchmark import DATASET, Case, load_cases

CASES = load_cases(DATASET)

#: The documented over-refusals (README "Limits"): synonym-heavy paraphrase
#: (token overlap cannot bridge a purely lexical gap) and the near-miss
#: order-collision case (refused as ``ambiguous`` by the margin rule).
KNOWN_OVER_REFUSALS = frozenset({"synonym-001", "synonym-002", "near-miss-002-order"})


def _result(case: Case) -> GroundingResult:
    return ground(Claim(case.case_id, case.model_quote), case.sources)


@pytest.mark.parametrize("case", CASES, ids=[c.case_id for c in CASES])
def test_case_matches_frozen_expectation(case):
    result = _result(case)

    if result.status == "grounded":
        # The headline guarantee, per case: grounding only ever points at the
        # expected source — never a confident wrong attribution.
        assert case.expected_status == "grounded", (
            f"{case.case_id}: grounded a case that must be refused "
            f"(matched {result.source_id!r}: {result.reason})"
        )
        assert result.source_id == case.expected_source_id, (
            f"{case.case_id}: FALSE ATTRIBUTION — grounded to {result.source_id!r}, "
            f"expected {case.expected_source_id!r} ({result.reason})"
        )
        assert result.source_url is not None
        assert result.grounded_quote is not None
    else:
        # Refusals carry null provenance, always.
        assert result.source_id is None
        assert result.source_url is None
        assert result.grounded_quote is None

    if case.expected_status != "grounded":
        # Refusal cases must keep refusing, with the expected refusal type.
        assert result.status == case.expected_status, (
            f"{case.case_id}: expected {case.expected_status}, got {result.status} "
            f"({result.reason})"
        )
    elif case.case_id not in KNOWN_OVER_REFUSALS:
        assert result.status == "grounded", (
            f"{case.case_id}: NEW over-refusal ({result.status}: {result.reason}) — "
            "recall regression, fix the code rather than extending KNOWN_OVER_REFUSALS"
        )


def test_over_refusals_are_exactly_the_known_set():
    """Pin the over-refusal set both ways: a new one is a recall regression, a
    recovered one means the documented numbers (README matrix) are stale."""
    refused = {
        case.case_id
        for case in CASES
        if case.expected_status == "grounded" and _result(case).status != "grounded"
    }
    assert refused == KNOWN_OVER_REFUSALS


def test_zero_false_attribution_floor():
    """The headline number, asserted in one place: 0 false attributions."""
    wrong = [
        (case.case_id, result.source_id)
        for case in CASES
        for result in [_result(case)]
        if result.status == "grounded" and result.source_id != case.expected_source_id
    ]
    assert wrong == []
