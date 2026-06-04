# reground (RG-001) — Engineer Hand-off Brief

> **Historical document (archived).** Pre-implementation orientation brief,
> kept verbatim. See the banner in `RG-001_reground.md` for where the shipped
> code diverged; where this brief and the code disagree, the code and
> `CHANGELOG.md` win.

> **Source of truth:** `docs/RG-001_reground.md`. This brief does not replace it — it's the orientation layer: what is locked, what the benchmark decides, where the landmines are, and the bar I (the SA) will review against. When this brief and the spec disagree, the spec wins; tell me so I fix the spec.

---

## 1. The job, in one sentence

Given a final `Claim` (produced anywhere downstream in an agent chain) **plus a small, already-curated set of `SourceDocument`s**, return a `GroundingResult` that is **either** grounded (verbatim source span + URL) **or** a safe refusal (`ungrounded` / `ambiguous`). **Never a confident wrong citation.**

Why it exists: citation provenance is **non-transitive across LLM calls** — it dies at the inter-agent boundary. This reconstructs it deterministically at the end, against the handful of sources the retrieval step already selected.

---

## 2. Hard contracts — DO NOT DRIFT (these are the API, not implementation detail)

- **`GroundingResult` is the contract.** Every input returns one, including refusals. Fields are frozen in spec §4 — don't add/rename without raising it with me.
- **`ground(claim, sources)` — `sources` is a LIST** (the curated set), not a single document. Alignment runs across every source in the set.
- **Zero third-party runtime dependencies in the core.** stdlib only. The NLI gate is the *only* component allowed a dependency, lives behind `extras=nli`, and is **never imported by the core path**.
- **`status` = the weakest link** across the two stages (alignment + provenance). Grounded text with unmapped provenance is not "grounded".
- **Refusal is a first-class return value, not an exception.** `ungrounded` / `ambiguous` are normal outputs with `source_url=None`, `grounded_quote=None`.
- **Offline always works** — core, demo, and benchmark run with no network and no API key (AC8).

---

## 3. Decided by the BENCHMARK, not by you upfront (resist pre-optimizing)

These are deliberately left to be settled empirically. Build the minimal version, let the test tell you, document the outcome either way.

- **Order-guard (category 10):** implement Jaccard + `margin` only. Add a `difflib.SequenceMatcher.ratio()` tie-break **only if** the order-collision case actually produces a false attribution. If `margin` already refuses it → no guard, document as YAGNI. (It's an internal signal, never a public `method` value.)
- **NLI gate (category 11 / multi-source):** define the `nli_gate.py` interface on day 1, **OFF by default**. Wire it into the flow **only if** deterministic-only over-refuses multi-source claims unacceptably. Both outcomes are publishable results — see DL-6. Don't wire it in "just in case".
- **Thresholds (DL-5):** choose and **freeze** `min-shared-tokens` and `margin` **before** scoring the benchmark, and record them in the README. No reverse-fitting thresholds to the cases.

---

## 4. Landmines — where this gets graded hardest

1. **`test_safety.py` IS the thesis.** `fabricated→null`, `ambiguous→null`, `wrong-citation-nearby→null`. If any of these ever yields a confident wrong attribution, the project failed its one promise. These tests must fail **loudly**, not warn.
2. **Over-refusal is a failure, not a safe default (R7).** Report **over-refusal rate** right next to false-attribution. A ~0% false-attribution bought by refusing everything is rejected at review.
3. **Multi-source synthesis (AC9):** a claim jointly supported by 2+ sources must still **ground**, not refuse merely because no single source covers the whole claim.
4. **Positioning (R6):** README must name **Google Vertex AI Check Grounding** as prior art and state the three real differences — *provider-neutral · verbatim span + URL (not score/index) · deterministic & inspectable, no model in the loop*. Omitting it reads as not knowing the field.
5. **Redaction (R4):** zero product names, domain schemas, extraction prompts, or PII anywhere. Neutral synthetic corpus only. Review before the first commit.
6. **Numbers discipline:** the 41→48% case study is **anecdote only**. The public figures (39–77%, 57%) are **motivation**, cited honestly as soft (industry-authored, LLM-judged). The **only** numbers that represent the tool are produced by `benchmark/run_benchmark.py`.

---

## 5. Build order (spec §7 — ~11.5h)

1. **Contracts + dataset** — `contracts.py`; freeze `dataset.jsonl` schema (`sources[]` = curated set); author 25–50 neutral cases across the 11 categories.
2. **Deterministic core + safety** — `align.py` (Jaccard over the curated set, fragment splitting), `provenance.py` (`[N]`→url, ambiguity guard), `harness.py`; min-tokens + margin safety; order-guard (test-decided); NLI gate interface (OFF).
3. **Failure-mode tests** — `test_safety.py` first; then align/provenance/harness.
4. **Benchmark** — freeze thresholds, then score; 4 metrics with explicit denominators, per-category matrix.
5. **README + packaging + CI** — product-engineer order + positioning vs Check Grounding; `.github/workflows/ci.yml` regenerates the matrix.
6. **Real-output fixtures** — ~10 real model outputs captured once, frozen with a provenance note; one-time manual harvest, never a runtime dependency.

---

## 6. Acceptance bar — what I check at the end (spec §10 DoD)

- Every input returns a `GroundingResult`, refusals included.
- `test_safety.py` green and genuinely adversarial.
- **false-attribution ≈ 0 AND over-refusal reported**, per category, with explicit denominators (4 metrics).
- Thresholds pre-registered in README.
- CI green and regenerates the matrix (numbers reproducible, not asserted).
- Zero third-party runtime deps in core; NLI strictly behind `extras=nli`.
- README positions vs Check Grounding / Citations APIs.
- No PII / product names; offline runs clean.
- Package is `reground`; `from reground import ground` works.

---

## 7. Raise with me BEFORE coding around it

- If deterministic-only multi-source over-refusal looks bad early — **tell me, don't silently loosen the margin.** Loosening margin trades false-attribution for recall and breaks the headline guarantee. The NLI gate is the sanctioned lever, not the threshold.
- If you hit a case the `GroundingResult` contract can't express — raise it. The contract is the public API; changing it is a spec decision, not an implementation one.
- If a benchmark category turns out trivial or impossible to author neutrally — flag it; honest per-category limits read as senior, silent omission does not.
