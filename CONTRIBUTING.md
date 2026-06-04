# Contributing

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
```

The core has **zero runtime dependencies** (stdlib only) — keep it that way.
`dev` brings pytest, hypothesis, mypy and ruff.

## Checks (all must pass — CI runs exactly these)

```bash
ruff check src tests benchmark examples
ruff format --check src tests benchmark examples
mypy                              # --strict via pyproject.toml
pytest                            # incl. the benchmark regression gate
python benchmark/run_benchmark.py # prints the matrix (offline, no API key)
```

## Ground rules

- **Never a confident wrong attribution.** `tests/test_safety.py` and
  `tests/test_benchmark.py` defend this; if your change trips them, the change
  is wrong, not the test.
- **Thresholds are pre-registered.** Do not tune `GroundingConfig` defaults to
  improve benchmark numbers — that invalidates the published matrix (see
  `benchmark/README.md`). The sanctioned recall lever is the (future) NLI gate.
- **Over-refusals are pinned** in `tests/test_benchmark.py`
  (`KNOWN_OVER_REFUSALS`). If your change *recovers* recall, shrink the set and
  update the README matrix in the same PR. If it *adds* an over-refusal, fix
  the code rather than extending the set.
- **Refusal is a return value, not an exception.** Exceptions are for caller
  bugs only (`exceptions.py`).
- Everything runs **offline**: no network, no API key, on any path that CI
  touches (`examples/harvest_fixtures.py` is the documented one-time manual
  exception and is never imported at runtime).
- Benchmark cases and fixtures stay **neutral and synthetic** — no PII, no
  product names.
