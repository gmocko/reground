# Benchmark dataset — frozen schema

`dataset.jsonl` is one JSON object per line. Cases are **neutral synthetic** —
zero PII, no product names, no domain schemas (spec R4). The benchmark runs
fully offline (AC8).

## Pre-registered thresholds (DL-5)

These values were **frozen on 2026-06-02, before the full case matrix was
authored or scored** — chosen from the algorithm design and the 3 seed cases, not
reverse-fitted to results. They are the `DEFAULT_CONFIG` in
[`src/reground/config.py`](../src/reground/config.py). The benchmark measures the
system *as configured here*; if numbers disappoint, the sanctioned lever is the
NLI gate (DL-6), **not** loosening these (handoff §7).

| Threshold | Value | Rationale |
|-----------|-------|-----------|
| `min_shared_tokens` | `4` | Below this, short/generic sentences over-match (DL-2, R3). |
| `jaccard_threshold` | `0.5` | A reordered/reworded sentence keeps ≥ half its content-token set; synonym-heavy paraphrase falls below — an accepted, documented limit. |
| `margin` | `0.1` | Best vs second-best source must clear this, else `ambiguous` (AC5). |
| `citation_window` | `1` | Search ±1 sentence for the nearest `[N]`; further is "too far" → unmapped (AC6). |

(A `fuzzy_citation_threshold` knob was pre-registered alongside these for a
bounded fuzzy fallback that was ultimately never implemented; it has been
removed from `GroundingConfig` rather than shipped as a dead parameter.)

## Second registration wave (2026-06-05)

An adversarial review found two ways a *confident* result could outrun its
evidence: a claim with a true head and a fabricated tail stayed `grounded`
(token overlap tolerates a tail up to roughly the size of the intersection),
and two near-equal sentences *inside one source* with different citations
escaped the cross-source margin rule entirely — a confident wrong URL. Two
deterministic rules close this:

| Rule | Value | Rationale |
|------|-------|-----------|
| `max_unsupported_tokens` | `2` | Unsupported-residual guard: a fragment with more than 2 content tokens absent from **every** source is refused. Tolerates the small inflectional residue of honest paraphrase ("converted" vs "converts"); a fabricated clause is almost always ≥ 3 content tokens. Residual is measured against the whole curated set, so multi-source synthesis (AC9) is not punished. |
| within-source margin | reuses `margin = 0.1` | When the best and second-best sentence of the winning source score within `margin`, both must resolve to the **same** citation URL; otherwise → `ambiguous`. |

Honest constraints, stated openly: these values were chosen from design
reasoning under one explicit constraint — **do not change any verdict in the
already-published 25-case matrix** (verified before freezing) — and were frozen
**before** the new adversarial categories below (`compound unsupported tail`,
`ambiguous same-source match`) were authored or scored. So for the original 25
cases the numbers measure the system as previously configured; for the new
cases they measure thresholds frozen before case authoring. The known residue
(a fabricated tail of ≤ 2 content tokens still rides through) is encoded as a
strict `xfail` in [`tests/test_limits.py`](../tests/test_limits.py).

## Case schema (frozen — spec §4)

| Field                | Type                                          | Meaning |
|----------------------|-----------------------------------------------|---------|
| `case_id`            | `str`                                         | Stable, unique id |
| `category`           | `str`                                         | One of the 13 categories (see below) |
| `sources`            | `Source[]`                                    | The **curated set** the claim is grounded against |
| `model_quote`        | `str`                                         | The (possibly paraphrased / fragment-combined) quote to ground |
| `expected_source_id` | `str \| null`                                 | Correct source id, or `null` when a refusal is expected |
| `expected_status`    | `"grounded" \| "ungrounded" \| "ambiguous"`   | Expected outcome |

### `Source`

| Field        | Type           | Meaning |
|--------------|----------------|---------|
| `source_id`  | `str`          | Stable id of this source unit |
| `text`       | `str`          | Source text with inline `[N]` citation markers |
| `citations`  | `Citation[]`   | Markers referenced by `text` |
| `url`        | `str \| null`  | Source-level provenance URL |

### `Citation`

| Field    | Type          | Meaning |
|----------|---------------|---------|
| `index`  | `int`         | The `N` in an inline `[N]` marker |
| `url`    | `str`         | Provenance URL for that marker |
| `title`  | `str \| null` | Optional human-readable title |

This schema maps 1:1 onto the runtime contracts in
[`src/reground/contracts.py`](../src/reground/contracts.py).

## Categories

The original 11 (spec §11):

`exact quote` · `minor paraphrase` · `reordered words` ·
`fragment combination (...)` · `synonym-heavy paraphrase` · `fabricated quote` ·
`ambiguous two-source match` · `citation marker far from quote` ·
`multiple citations in window` · `near-miss distractor` · `multi-source synthesis`

Added with the second registration wave (cases authored *after* the wave-2
thresholds were frozen):

`compound unsupported tail` · `ambiguous same-source match`

The current file holds 25 cases across the 11 categories (the schema was locked
on 3 seed cases first, then the full matrix was authored against it). The
matrix is enforced two ways: `benchmark/run_benchmark.py` prints it, and
[`tests/test_benchmark.py`](../tests/test_benchmark.py) asserts it per case in
CI — a false attribution or a new over-refusal fails the build, it cannot pass
as a silently different printout.
