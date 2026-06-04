"""One-command quickstart: a claim + a curated source set -> GroundingResult.

Runs fully offline, no API key, zero third-party dependencies (AC8):

    python examples/run_demo.py

Shows the three outcomes the contract guarantees — grounded, ungrounded
(fabricated), and ambiguous (two near-equal sources) — so the safe-refusal
behaviour is visible, not just the happy path. The source set mirrors
``sample_corpus.md``.

If ``real_model_outputs.jsonl`` is present (frozen once by
``harvest_fixtures.py`` — see its provenance note), those REAL model outputs
are grounded too, still offline: the full loop on non-strawman inputs.
"""

from __future__ import annotations

import json
from pathlib import Path

from reground import Citation, Claim, GroundingResult, SourceDocument, ground

CURATED_SET = [
    SourceDocument(
        source_id="src-photosynthesis",
        text=(
            "Photosynthesis converts light energy into chemical energy [1]. "
            "The process occurs mainly in the leaves of plants [2]."
        ),
        citations=(
            Citation(index=1, url="https://example.com/photosynthesis"),
            Citation(index=2, url="https://example.com/leaves"),
        ),
        url="https://example.com/biology/photosynthesis",
    ),
    SourceDocument(
        source_id="src-water-cycle",
        text=(
            "Water evaporates from oceans and lakes [1]. "
            "It later condenses into clouds and returns as precipitation [2]."
        ),
        citations=(
            Citation(index=1, url="https://example.com/evaporation"),
            Citation(index=2, url="https://example.com/precipitation"),
        ),
        url="https://example.com/earth/water-cycle",
    ),
]

# The full sample_corpus.md set — what the real-output fixtures ground against.
CORPUS_SET = [
    *CURATED_SET,
    SourceDocument(
        source_id="src-honeybee",
        text="Honeybees communicate the location of food using a waggle dance [1].",
        citations=(Citation(index=1, url="https://example.com/waggle-dance"),),
    ),
]

# A second source whose target sentence is identical -> deliberately ambiguous.
AMBIGUOUS_SET = [
    SourceDocument(
        source_id="src-bee-1",
        text="Honeybees communicate the location of food using a waggle dance [1].",
        citations=(Citation(index=1, url="https://example.com/waggle-dance"),),
    ),
    SourceDocument(
        source_id="src-bee-2",
        text="Honeybees communicate the location of food using a waggle dance [1].",
        citations=(Citation(index=1, url="https://example.com/bee-foraging"),),
    ),
]

DEMOS: list[tuple[str, Claim, list[SourceDocument]]] = [
    (
        "paraphrase -> grounded",
        Claim("c1", "light energy is converted into chemical energy by photosynthesis"),
        CURATED_SET,
    ),
    (
        "fabricated -> ungrounded (safe refusal)",
        Claim("c2", "Quantum entanglement enables faster than light communication"),
        CURATED_SET,
    ),
    (
        "two equal sources -> ambiguous (safe refusal)",
        Claim("c3", "Honeybees communicate the location of food using a waggle dance"),
        AMBIGUOUS_SET,
    ),
]


def show(result: GroundingResult) -> None:
    print(f"  status      : {result.status}")
    print(f"  source_id   : {result.source_id}")
    print(f"  source_url  : {result.source_url}")
    print(f"  grounded    : {result.grounded_quote}")
    print(f"  method/score: {result.method} / {result.score:.2f}  (margin {result.margin:.2f})")
    print(f"  reason      : {result.reason}")


def run_real_fixtures() -> None:
    """Ground the frozen real model outputs, if harvested (still offline)."""
    fixtures = Path(__file__).with_name("real_model_outputs.jsonl")
    if not fixtures.exists():
        return

    records = [json.loads(line) for line in fixtures.read_text().splitlines() if line.strip()]
    if not records:
        return

    provenance = records[0]["provenance"]
    print(f"\n=== real model outputs ({provenance['model']}, {provenance['harvested']}) ===")
    counts: dict[str, int] = {}
    for record in records:
        result = ground(Claim(record["claim_id"], record["quote"]), CORPUS_SET)
        counts[result.status] = counts.get(result.status, 0) + 1
        print(f"\n  [{record['claim_id']}] {record['category']}")
        print(f"  quote       : {record['quote']!r}")
        show(result)
    summary = ", ".join(f"{status}={n}" for status, n in sorted(counts.items()))
    print(f"\n  summary     : {summary} (n={len(records)})")


def main() -> None:
    for label, claim, sources in DEMOS:
        print(f"\n=== {label} ===")
        print(f"  quote       : {claim.quote!r}")
        show(ground(claim, sources))
    run_real_fixtures()
    print()


if __name__ == "__main__":
    main()
