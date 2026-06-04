# reground

[![CI](https://github.com/gmocko/reground/actions/workflows/ci.yml/badge.svg)](https://github.com/gmocko/reground/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](pyproject.toml)
[![mypy --strict](https://img.shields.io/badge/types-mypy%20--strict-blue)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**Deterministic citation-span re-grounding with safe refusal.**

It re-attaches provenance to the best-supported **span** of a claim — or
refuses. It is *not* a fact-checker: it does not prove a whole sentence true
(see [What this does not prove](#what-this-does-not-prove)).

> Citation provenance does not survive a chain of LLM agents. Reconstruct it
> deterministically at the end — align each final claim to a verbatim span
> within the small, already-curated source set, or refuse — **never a confident
> wrong citation.**

```python
from reground import Claim, SourceDocument, Citation, ground

sources = [
    SourceDocument(
        source_id="src-photosynthesis",
        text="Photosynthesis converts light energy into chemical energy [1].",
        citations=(Citation(index=1, url="https://example.com/photosynthesis"),),
    )
]

result = ground(Claim("c1", "light energy is converted into chemical energy by photosynthesis"), sources)

result.status        # "grounded"
result.grounded_quote # "Photosynthesis converts light energy into chemical energy."
result.source_url    # "https://example.com/photosynthesis"
# the verdict covers grounded_quote (the verbatim span it returns) — not
# necessarily every word of the input claim; see "What this does not prove"
```

```bash
pip install git+https://github.com/gmocko/reground.git   # zero runtime dependencies (stdlib only)
python examples/run_demo.py                               # runs offline, no API key
```

---

## The problem

In multi-agent pipelines, citation provenance is lost not at the model boundary
but at the **inter-agent boundary**. A retrieval step returns text with inline
citations anchored to *its own* output. Downstream agents rewrite, synthesize,
and extract — and the final, user-facing text is produced by agents whose output
no longer carries the original anchors. Citations are **non-transitive across
independent LLM calls**: each hop compounds the loss.

Two failure modes result, both worse under pipeline depth:

- **lost traceability** — a true fact arrives with no verifiable source;
- **false attribution** (the dangerous one) — a final claim is mapped to the
  *wrong* source.

A system that cannot tell these apart cannot be trusted to cite.

## What it does

`ground(claim, sources)` takes a final `Claim` (produced anywhere downstream in
a chain) plus the **small, already-curated set** of `SourceDocument`s the
retrieval step already selected, and returns one `GroundingResult` that is
**either**:

- **grounded** — a verbatim source span + the source URL (mapped from the
  nearest inline `[N]` citation), or
- a **safe refusal** — `ungrounded` or `ambiguous`, with `source_url=None`.

The guarantee, stated precisely: **a URL is emitted only when a verbatim
source span *and* an inline citation marker are both confidently and
unambiguously mapped** — and a `grounded` verdict covers the returned
`grounded_quote`, not necessarily every word of the input claim (see
[What this does not prove](#what-this-does-not-prove)). Refusal is a
first-class return value, not an exception. The core runs **offline with zero
third-party dependencies**.

The small candidate set is what makes a deterministic matcher viable: with 5–15
curated sources, the token-overlap over-matching that sinks open-corpus
grounding largely collapses.

## Why this exists (positioning)

This is not the first tool to ground a synthesized answer against a fact set —
and the README says so rather than pretending the field is empty.

- **Google Vertex AI *Check Grounding*** is the closest prior art: it grounds an
  answer candidate against a developer-supplied fact set with per-claim support
  scores and a full-entailment refusal standard. reground differs on three axes:
  it is **provider-neutral** (no cloud lock-in), returns a **verbatim span +
  source URL** (not a support score + fact index), and is **deterministic and
  inspectable — no model in the loop** (so no hallucinated-agreement failure),
  running offline with zero dependencies.
- **Native citation features** (Anthropic Citations API, LlamaIndex
  `CitationQueryEngine`, DSPy citations) emit citations *while answering over
  provided documents in a single call*. They close the *generation* boundary;
  none re-ground a piece of already-synthesized text across a chain.

The gap reground fills: a provider-neutral, deterministic, inspectable step that
re-grounds a chain's final output against the curated set it carried forward.

### Key design decisions

- **Deterministic post-processing over prompt coercion.** The LLM's job shrinks
  to "propose"; verification is code, and the failure mode is inspectable.
- **Token overlap (Jaccard) over character-level fuzzy.** Word-set overlap
  spans `...`-joined fragments and survives word reordering, where char-level
  similarity fails.
- **Safe refusal over best-guess** (`null` > wrong attribution). "No confident,
  unambiguous match" is a first-class outcome. We optimize for **~0% false
  attribution**, accepting lower recall on hard categories as a documented
  trade-off. The final `status` is the **weakest link** across alignment and
  provenance: grounded text whose citation can't be confidently mapped is *not*
  "grounded".
- **Pre-registered thresholds.** The safety thresholds were frozen **before**
  the benchmark was scored ([`benchmark/README.md`](benchmark/README.md)) — the
  numbers measure the system as configured, not a configuration reverse-fitted
  to the cases.
- **Deterministic core; NLI gate is a defined port, not yet shipped.** An
  entailment gate could recover recall on lexically-divergent claims. Its
  boundary interface ([`EntailmentGate`](src/reground/ports.py)) is defined so
  the core never depends on an implementation — but **no implementation ships
  in this release** (there is deliberately no `[nli]` extra yet: installing one
  must never be a no-op). Adding a model to the core would forfeit the
  determinism that is the whole point. Whether the gate is worth building is an
  empirical question the benchmark answers (see below).

## Proof — the benchmark

The only numbers that represent the tool come from
[`benchmark/run_benchmark.py`](benchmark/run_benchmark.py) (offline, reproducible
in CI on every push — and *enforced* per case by
[`tests/test_benchmark.py`](tests/test_benchmark.py)). 29 neutral synthetic
cases across 13 categories, scored on the pre-registered thresholds (two
registration waves — see [`benchmark/README.md`](benchmark/README.md)). Each
metric has an explicit denominator (so a "~0% false-attribution bought by
refusing everything" cannot hide):

| Category | recall | false-attr | safe-refusal | over-refusal |
|---|---|---|---|---|
| exact quote | 3/3 | 0/3 | – | 0/3 |
| minor paraphrase | 3/3 | 0/3 | – | 0/3 |
| reordered words | 2/2 | 0/2 | – | 0/2 |
| fragment combination (`...`) | 2/2 | 0/2 | – | 0/2 |
| multi-source synthesis | 2/2 | 0/2 | – | 0/2 |
| ambiguous same-source match | 1/1 | 0/1 | 1/1 | 0/1 |
| fabricated quote | – | – | 3/3 | – |
| compound unsupported tail | – | – | 2/2 | – |
| ambiguous two-source match | – | – | 2/2 | – |
| citation marker far from quote | – | – | 2/2 | – |
| multiple citations in window | – | – | 2/2 | – |
| synonym-heavy paraphrase | 0/2 | – | – | 2/2 |
| near-miss distractor | 0/1 | – | 1/1 | 1/1 |
| **TOTAL** | **81.2%** (13/16) | **0.0%** (0/13) | **100%** (13/13) | **18.8%** (3/16) |

- `recall` = grounded to the **correct** source / cases expecting `grounded`
- `false-attr` = grounded to the **wrong** source / cases the system marked grounded
- `safe-refusal` = correctly refused / cases expecting a refusal
- `over-refusal` = refused / cases expecting `grounded`

**Headline: 0% false attribution.** All over-refusal is concentrated in exactly
two places — *synonym-heavy paraphrase* and one *order-collision* — which is the
lexical-divergence territory a future NLI gate would target. Two questions the
benchmark settled empirically:

- **Order-guard: not needed (YAGNI).** The order-collision case ("the dog chased
  the cat" vs "the cat chased the dog", same token set) is refused as
  `ambiguous` by the margin rule — a *safe refusal*, not a wrong attribution. So
  no `difflib` tie-break was added.
- **NLI gate: not built.** The deterministic floor holds (0% false-attribution;
  100% recall on exact / paraphrase / reorder / fragment / multi-source).
  Over-refusal is isolated to synonym-heavy paraphrase — so the gate stays a
  documented *future* lever for teams that need that recall, not a shipped
  default.
- **Second-wave guards: two holes closed without touching the matrix.** An
  adversarial review found a true-head + fabricated-tail compound staying
  `grounded`, and two near-equal sentences *inside one source* escaping the
  margin rule (a confident wrong URL). The **unsupported-residual guard**
  (tokens absent from *every* source, measured set-wide so multi-source
  synthesis is not punished) and the **within-source margin** (near-equal
  sentences must resolve to one citation URL) close both — pre-registered
  before the two new categories were authored, with all 25 original verdicts
  unchanged ([`benchmark/README.md`](benchmark/README.md)).

Reproduce locally:

```bash
pip install -e '.[dev]'
python benchmark/run_benchmark.py
```

### Reality check — real model outputs (not the benchmark)

To prove the demo inputs aren't strawmen, 10 real `claude-haiku-4-5` outputs
were harvested **once** (2026-06-04) with
[`examples/harvest_fixtures.py`](examples/harvest_fixtures.py) — the model
acted as a blind "final synthesis agent" over the demo corpus, with no
knowledge of the grounding mechanism — and frozen into
[`examples/real_model_outputs.jsonl`](examples/real_model_outputs.jsonl) with a
provenance note. `run_demo.py` grounds them offline on every CI run.

Result: **0 false attributions, 1 grounded, 9 safe refusals.** Two honest
readings: the safety floor holds on real inputs exactly as on synthetic ones —
and a real model's free paraphrase is synonym-heavy *by default*, not as an
edge case. Real-world recall therefore sits squarely in the future NLI gate's
territory; these fixtures are the strongest empirical argument this project
produced for building that lever. (The benchmark numbers above remain the only
figures that represent the tool.)

## What this does not prove

`ground()` re-attaches provenance to the **best-supported span** of a claim.
Read a `grounded` verdict precisely:

- **It covers `grounded_quote` — not every word of `original_quote`.** For a
  `...`-joined quote the verdict is about the strongest fragment (AC3); the
  other fragments may be entirely unsupported. A fabricated tail of ≤ 2
  content tokens can also ride on a grounded head (the residual guard's
  documented tolerance). Callers must present `grounded_quote` + URL as the
  verified artifact — never the original claim text wholesale.
- **It is not entailment.** Token overlap cannot see negation, hedging, or
  reversal against a single matching sentence ("A causes B" vs "B causes A").
  Proving a whole sentence true needs an entailment model — the deliberately
  unshipped (future) NLI gate.
- **It is not multi-hop fact-checking.** A claim that is true only via a chain
  of inferences across documents will refuse — correctly, by these semantics.
- **It does not vet the sources.** It maps a claim back into the curated set
  it is handed; whether those sources are trustworthy is upstream's job.

Where expressible, the mechanical limit behind each statement is encoded as a
strict `xfail` in [`tests/test_limits.py`](tests/test_limits.py) — outgrowing
one breaks the build until this section is consciously updated.

## Limits (honest)

- **Synonym-heavy paraphrase over-refuses.** Token overlap cannot bridge a
  purely lexical gap (e.g. "plants transform sunlight into stored fuel" vs a
  photosynthesis source). This is the (future) NLI gate's job; not shipped in
  this release.
- **Semantic reversal is not detected by the core.** Token overlap treats "A
  causes B" and "B causes A" as near-identical. The margin rules catch the
  *two-source* and *two-sentence* versions of this (→ ambiguous); reversal
  against a single matching sentence is out of scope for a deterministic
  matcher and belongs to the (future) entailment gate.
- **A fabricated tail of ≤ 2 content tokens can ride through.** The
  unsupported-residual guard refuses fragments with more than
  `max_unsupported_tokens` (2) content tokens absent from every source — the
  tolerance that admits honest inflectional residue ("converted" vs
  "converts") also admits a very short fabricated tail. This and the other
  limits here are encoded as **strict `xfail`s** in
  [`tests/test_limits.py`](tests/test_limits.py): if one ever starts passing,
  the build breaks until this section is consciously updated.
- **Provenance uses a bounded window.** A citation more than `citation_window`
  sentences from the aligned span is treated as "too far" → unmapped (a safe
  refusal of attribution), by design.
- **The tokenizer is ASCII/English-only.** Content tokens are `[a-z0-9]+` runs
  with an English stop-word list. Exact quotes in other languages still match
  (the verbatim-substring path is byte-faithful), but *paraphrase* alignment
  for languages with diacritics is unreliable — "przekształca" fragments into
  `przekszta` + `ca`-like stubs, degrading overlap in both directions. Treat
  non-English paraphrase support as out of scope for the core.
- **The sentence splitter is deliberately naive** (`.`/`!`/`?` + whitespace).
  Abbreviations like "e.g." or "Dr." split a sentence in two, which shifts
  sentence indices — and the citation window is *measured in sentences*, so a
  marker can fall out of (or into) range. Suited to the clean, curated source
  snippets the tool is designed for; not hardened against raw prose.

## The contract

Every input returns a [`GroundingResult`](src/reground/contracts.py) — including
refusals (`grounded_quote`/`source_id`/`source_url` are `None`). It records not
just the answer but `method`, `score`, `margin`, and a human-readable `reason`,
so every outcome is auditable.

## How it was built

Spec-first, test-defended, numbers-last:

1. **Contracts + dataset** — the `GroundingResult` contract and the benchmark
   schema frozen first.
2. **Deterministic core + safety** — Jaccard alignment over the curated set,
   `...`-fragment splitting, and the two safety rules (min shared tokens +
   margin → ambiguous).
3. **Failure-mode tests** — [`tests/test_safety.py`](tests/test_safety.py) is
   the thesis: `fabricated → null`, `ambiguous → null`,
   `wrong-citation-nearby → null`, plus a property-based invariant (a quote
   sharing no content tokens is never grounded — for *any* such quote).
4. **Benchmark** — thresholds pre-registered, then scored once; four metrics
   with explicit denominators, per category.
5. **Packaging + CI** — zero-dep core; `ruff` + `mypy --strict` + `pytest` + the
   benchmark re-run on every push.
6. **Adversarial review + second wave** — two confident-wrong-result holes
   (fabricated tail riding on a true head; a within-source citation collision)
   were found by red-teaming the thesis and closed with two deterministic
   guards, pre-registered before the new benchmark categories were authored
   ([`benchmark/README.md`](benchmark/README.md)). Documented limits became
   strict `xfail`s ([`tests/test_limits.py`](tests/test_limits.py)).

## License

MIT — see [LICENSE](LICENSE).
