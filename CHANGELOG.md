# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow
[SemVer](https://semver.org/).

## [0.1.0] — 2026-06-04

First public release.

### Added

- `ground(claim, sources) -> GroundingResult`: deterministic provenance
  reconstruction across a curated source set — verbatim span + source URL, or a
  safe refusal (`ungrounded` / `ambiguous`). Never a confident wrong citation.
- Public contracts: `Claim`, `SourceDocument`, `Citation`, `GroundingResult`
  (refusals are first-class return values, not exceptions).
- Safety rules: minimum shared content tokens + best-vs-second-best margin
  (→ `ambiguous`); status is the weakest link across alignment and provenance.
- `...`-fragment splitting (the longest grounded fragment aligns) and
  multi-source synthesis support.
- Offline benchmark (`benchmark/run_benchmark.py`): 25 neutral cases across
  11 categories, four metrics with explicit denominators, thresholds
  pre-registered before scoring. Headline: 0% false attribution.
- Real-output fixtures: 10 `claude-haiku-4-5` outputs harvested once
  (`examples/harvest_fixtures.py`, stdlib-only, never on a runtime path) and
  frozen with a provenance note; grounded offline by `examples/run_demo.py`
  (0 false attributions, 1 grounded, 9 safe refusals).
- Zero third-party runtime dependencies (stdlib only); `py.typed` shipped
  (`mypy --strict` clean).
- CI: ruff + mypy --strict + pytest + benchmark regeneration + offline demo,
  on Python 3.11–3.13.
