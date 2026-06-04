# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow
[SemVer](https://semver.org/).

## [0.2.0] — 2026-06-05

Safety semantics: an adversarial review found two ways a *confident* result
could outrun its evidence; both are closed deterministically, without changing
any verdict in the published 25-case matrix (verified before freezing the new
threshold — see `benchmark/README.md`, "Second registration wave").

### Added

- **Unsupported-residual guard** (`max_unsupported_tokens = 2`,
  pre-registered): a claim fragment with more than 2 content tokens absent
  from *every* source is refused — closes the "true head + fabricated tail"
  hole. The residual is measured against the whole curated set, so
  multi-source synthesis (AC9) still grounds.
- **Within-source margin check**: two near-equal sentences inside the winning
  source must resolve to the *same* citation URL, else `ambiguous` — closes
  the confident-wrong-URL hole the cross-source margin (AC5) cannot see.
  Sentences tying onto one URL still ground (recall preserved).
- Two new benchmark categories (4 cases): `compound unsupported tail` and
  `ambiguous same-source match` — the matrix is now 29 cases / 13 categories
  (recall 13/16, false-attribution 0/13, safe-refusal 13/13).
- `tests/test_limits.py`: documented limits encoded as **strict xfails**
  (single-source semantic reversal; `...`-fragment semantics; a ≤ 2-token
  fabricated tail) — if a limit is ever outgrown, the build breaks until the
  README "Limits" section is consciously updated.

### Documentation (scope clarification)

- The promise is narrowed to what the mechanism does: **deterministic
  citation-span re-grounding**, not whole-claim fact-checking. The README
  states the guarantee precisely (a URL only when a span *and* a marker are
  both confidently mapped; the verdict covers `grounded_quote`, never the
  whole `original_quote`) and gains a "What this does not prove" section
  (fragment semantics, no entailment, no multi-hop verification, no source
  vetting).
- New documented limits: the ASCII/English-only tokenizer (non-English
  *paraphrase* alignment is out of scope; exact quotes still match) and the
  deliberately naive sentence splitter (abbreviations shift the
  sentence-indexed citation window).
- `examples/run_demo.py` gains a fourth demo showing the AC3 fragment
  semantics explicitly (`grounded_quote` vs `original_quote`).

## [0.1.0] — 2026-06-05

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
- CI: ruff + mypy --strict + pytest (incl. the benchmark regression gate) +
  benchmark matrix printout + offline demo, on Python 3.11–3.13.
- Benchmark regression gate (`tests/test_benchmark.py`): the matrix is
  *asserted* per case in CI, not just printed — a false attribution or a new
  over-refusal fails the build; the known over-refusals are pinned.
- `CONTRIBUTING.md` with the exact check commands CI runs and the ground rules
  (pre-registered thresholds, pinned over-refusals, refusal-as-value).

### Changed (pre-publication release hardening)

- Package version is single-sourced from `reground.__version__` (pyproject
  reads it back via `[tool.setuptools.dynamic]`).
- Removed the dead `fuzzy_citation_threshold` config knob — the bounded fuzzy
  fallback it was pre-registered for was never implemented (noted in
  `benchmark/README.md`).
- Removed the empty `[nli]` extra; README now states the `EntailmentGate` port
  is defined but **no NLI implementation ships** in this release.
- Documented that provenance comes exclusively from `Citation.url` of a
  confidently-mapped inline `[N]` marker; `SourceDocument.url` is caller-side
  metadata the core never returns.
- `benchmark/README.md` updated to the authored 25-case matrix (stale "3 seed
  cases" note removed).
- Pre-implementation spec documents moved to `docs/archive/` with a
  "historical, kept verbatim" banner noting where the shipped code diverged.
