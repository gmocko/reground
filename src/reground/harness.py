"""``ground(claim, sources)`` — orchestration over the curated set.

Combines the two deterministic stages and returns the single public contract.
The final ``status`` is the **weakest link** across alignment and provenance:
text that aligns but cannot be confidently attributed is *not* "grounded"
(handoff §2). Every input returns a :class:`~reground.contracts.GroundingResult`,
including refusals — they are values, never exceptions.

The optional NLI gate (DL-6) is intentionally **not** wired in here. Its port
lives in :mod:`reground.ports`; whether the deterministic core defers refused /
low-margin claims to it is an empirical decision driven by the Phase 4
multi-source over-refusal numbers — not a "just in case" hook. The single
extension point is marked below.
"""

from __future__ import annotations

from reground._text import strip_markers
from reground.align import Alignment, align_quote
from reground.config import DEFAULT_CONFIG, GroundingConfig
from reground.contracts import Claim, GroundingResult, SourceDocument
from reground.exceptions import EmptySourceSetError, InvalidClaimError
from reground.provenance import map_provenance


def ground(
    claim: Claim,
    sources: list[SourceDocument],
    config: GroundingConfig = DEFAULT_CONFIG,
) -> GroundingResult:
    """Ground ``claim`` against the curated ``sources``.

    Returns a grounded result (verbatim span + source URL) or a safe refusal
    (``ungrounded`` / ``ambiguous`` with ``source_url=None``). Never a confident
    wrong attribution.

    Raises:
        EmptySourceSetError: if ``sources`` is empty.
        InvalidClaimError: if the claim has no usable quote.
    """
    if not sources:
        raise EmptySourceSetError("ground() requires at least one source document")
    if not claim.quote.strip():
        raise InvalidClaimError(f"claim {claim.claim_id!r} has an empty quote")

    alignment = align_quote(claim.quote, sources, config)

    if alignment.status != "grounded":
        # Alignment refused (ungrounded / ambiguous). The NLI gate, if ever
        # wired in (DL-6), would get its chance here before we return.
        return _refusal(claim, alignment)

    # Text aligned; resolve provenance against the matched source.
    assert alignment.best is not None  # guaranteed when status == "grounded"
    source = _source_by_id(sources, alignment.best.source_id)
    provenance = map_provenance(source, alignment.best.sentence_index, config)

    if not provenance.mapped:
        # Weakest link: grounded text, unmapped provenance -> not "grounded".
        # We refuse attribution rather than emit a URL we are unsure of (AC6).
        return GroundingResult(
            claim_id=claim.claim_id,
            original_quote=claim.quote,
            grounded_quote=None,
            source_id=None,
            source_url=None,
            status="ungrounded",
            method=alignment.method,
            score=alignment.score,
            margin=alignment.margin,
            reason=(
                f"aligned to a verbatim span in {alignment.best.source_id} but "
                f"{provenance.reason}; attribution refused"
            ),
        )

    return GroundingResult(
        claim_id=claim.claim_id,
        original_quote=claim.quote,
        grounded_quote=strip_markers(alignment.best.span),
        source_id=alignment.best.source_id,
        source_url=provenance.source_url,
        status="grounded",
        method=alignment.method,
        score=alignment.score,
        margin=alignment.margin,
        reason=f"{alignment.reason}; {provenance.reason}",
    )


def _refusal(claim: Claim, alignment: Alignment) -> GroundingResult:
    return GroundingResult(
        claim_id=claim.claim_id,
        original_quote=claim.quote,
        grounded_quote=None,
        source_id=None,
        source_url=None,
        status=alignment.status,
        method=alignment.method,
        score=alignment.score,
        margin=alignment.margin,
        reason=alignment.reason,
    )


def _source_by_id(sources: list[SourceDocument], source_id: str) -> SourceDocument:
    for source in sources:
        if source.source_id == source_id:
            return source
    # align_quote only returns ids drawn from `sources`, so this is unreachable.
    raise AssertionError(f"aligned source_id {source_id!r} not in the curated set")
