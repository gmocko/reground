"""reground — deterministic provenance reconstruction with safe refusal.

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

__version__ = "0.0.0"

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
