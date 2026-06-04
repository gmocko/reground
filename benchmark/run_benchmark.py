"""Offline benchmark runner — the only numbers that represent reground.

Reports four metrics with *explicit denominators* (AC7), overall and per
category. Zero third-party dependencies; no network, no LLM (AC8).

    python benchmark/run_benchmark.py

The headline guarantee is **false-attribution ≈ 0**, reported next to
**over-refusal** so a refuse-everything system cannot hide (R7).
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from reground import Citation, Claim, SourceDocument, ground

DATASET = Path(__file__).parent / "dataset.jsonl"
_REFUSALS = frozenset({"ungrounded", "ambiguous"})


@dataclass(frozen=True, slots=True)
class Case:
    case_id: str
    category: str
    sources: list[SourceDocument]
    model_quote: str
    expected_source_id: str | None
    expected_status: str


@dataclass(frozen=True, slots=True)
class Metrics:
    """Counts behind the four AC7 rates, kept explicit so denominators are visible."""

    expected_grounded: int = 0
    expected_refusal: int = 0
    system_grounded: int = 0
    recall_hits: int = 0  # expected grounded AND grounded to the correct source
    false_attributions: int = 0  # system grounded to the wrong source
    safe_refusals: int = 0  # expected refusal AND correctly refused
    over_refusals: int = 0  # expected grounded BUT refused

    def __add__(self, other: Metrics) -> Metrics:
        return Metrics(
            expected_grounded=self.expected_grounded + other.expected_grounded,
            expected_refusal=self.expected_refusal + other.expected_refusal,
            system_grounded=self.system_grounded + other.system_grounded,
            recall_hits=self.recall_hits + other.recall_hits,
            false_attributions=self.false_attributions + other.false_attributions,
            safe_refusals=self.safe_refusals + other.safe_refusals,
            over_refusals=self.over_refusals + other.over_refusals,
        )


def load_cases(path: Path) -> list[Case]:
    cases: list[Case] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        sources = [
            SourceDocument(
                source_id=s["source_id"],
                text=s["text"],
                citations=tuple(Citation(**c) for c in s["citations"]),
                url=s["url"],
            )
            for s in raw["sources"]
        ]
        cases.append(
            Case(
                case_id=raw["case_id"],
                category=raw["category"],
                sources=sources,
                model_quote=raw["model_quote"],
                expected_source_id=raw["expected_source_id"],
                expected_status=raw["expected_status"],
            )
        )
    return cases


def score_case(case: Case) -> Metrics:
    result = ground(Claim(case.case_id, case.model_quote), case.sources)
    expected_grounded = case.expected_status == "grounded"
    expected_refusal = case.expected_status in _REFUSALS
    system_grounded = result.status == "grounded"
    system_refused = result.status in _REFUSALS
    correct_source = result.source_id == case.expected_source_id
    return Metrics(
        expected_grounded=int(expected_grounded),
        expected_refusal=int(expected_refusal),
        system_grounded=int(system_grounded),
        recall_hits=int(expected_grounded and system_grounded and correct_source),
        false_attributions=int(system_grounded and not correct_source),
        safe_refusals=int(expected_refusal and system_refused),
        over_refusals=int(expected_grounded and system_refused),
    )


def _rate(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "    n/a"
    return f"{numerator / denominator:6.1%}"


def _format_row(label: str, m: Metrics) -> str:
    return (
        f"{label:<28} "
        f"recall {_rate(m.recall_hits, m.expected_grounded)} "
        f"({m.recall_hits}/{m.expected_grounded})   "
        f"false-attr {_rate(m.false_attributions, m.system_grounded)} "
        f"({m.false_attributions}/{m.system_grounded})   "
        f"safe-refusal {_rate(m.safe_refusals, m.expected_refusal)} "
        f"({m.safe_refusals}/{m.expected_refusal})   "
        f"over-refusal {_rate(m.over_refusals, m.expected_grounded)} "
        f"({m.over_refusals}/{m.expected_grounded})"
    )


def run(path: Path = DATASET) -> Metrics:
    cases = load_cases(path)
    per_category: dict[str, Metrics] = defaultdict(Metrics)
    total = Metrics()
    for case in cases:
        m = score_case(case)
        per_category[case.category] += m
        total += m

    print(f"reground benchmark — {len(cases)} cases\n" + "=" * 120)
    print("Metrics (numerator/denominator) per AC7:")
    print(
        "  recall = correct-source / expected-grounded | "
        "false-attr = wrong-source / system-grounded\n"
        "  safe-refusal = correctly-refused / expected-refusal | "
        "over-refusal = refused / expected-grounded\n" + "-" * 120
    )
    for category in sorted(per_category):
        print(_format_row(category, per_category[category]))
    print("-" * 120)
    print(_format_row("TOTAL", total))
    print(
        "\nHeadline: false-attribution = "
        f"{_rate(total.false_attributions, total.system_grounded).strip()} "
        f"({total.false_attributions}/{total.system_grounded} grounded)"
    )
    return total


if __name__ == "__main__":
    run()
