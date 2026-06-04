"""reground — deterministic citation-span re-grounding with safe refusal.

Re-attaches provenance to the best-supported span of a claim, or refuses.
A ``grounded`` verdict covers the returned ``grounded_quote`` (a verbatim
source span), never the whole input claim — see README
"What this does not prove".

Public API:

    from reground import ground, Claim, SourceDocument, GroundingResult
"""

from __future__ import annotations

from reground.config import DEFAULT_CONFIG, GroundingConfig
from reground.contracts import (
    Citation,
    Claim,
    GroundingMethod,
    GroundingResult,
    GroundingStatus,
    SourceDocument,
)
from reground.exceptions import (
    EmptySourceSetError,
    InvalidClaimError,
    RegroundError,
)
from reground.harness import ground
from reground.ports import EntailmentGate

# Single source of truth for the package version — pyproject.toml reads it
# back via [tool.setuptools.dynamic].
__version__ = "0.2.0"

__all__ = [
    "DEFAULT_CONFIG",
    "Citation",
    "Claim",
    "EmptySourceSetError",
    "EntailmentGate",
    "GroundingConfig",
    "GroundingMethod",
    "GroundingResult",
    "GroundingStatus",
    "InvalidClaimError",
    "RegroundError",
    "SourceDocument",
    "__version__",
    "ground",
]
