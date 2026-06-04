"""Boundary interfaces (ports) the deterministic core depends on.

The :class:`EntailmentGate` port lives in the core so that
:mod:`reground.harness` can type and accept an optional gate **without ever
importing** the optional :mod:`reground.nli_gate` implementation (which is gated
behind ``extras=nli``). The core depends on the abstraction; the adapter depends
on the core (dependency inversion). This keeps the core zero-dependency and the
NLI gate strictly off the default path (handoff §2).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class EntailmentGate(Protocol):
    """Optional recall-recovery gate for lexically-divergent claims (DL-6).

    Given a source ``premise`` span and a claim ``hypothesis``, return an
    entailment probability in ``[0.0, 1.0]``. OFF by default; wired into the
    flow only if the multi-source over-refusal numbers demand it.
    """

    def entailment(self, premise: str, hypothesis: str) -> float:
        """Return the probability that ``premise`` entails ``hypothesis``."""
        ...
