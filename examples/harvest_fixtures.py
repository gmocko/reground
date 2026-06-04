"""One-time manual harvest of real model outputs (spec RG-001 Phase 6, DL-4).

Asks a real LLM to act as the *final synthesis agent* of a multi-agent
pipeline over the neutral corpus in ``sample_corpus.md`` — producing
user-facing claims whose inline ``[N]`` anchors were lost at the inter-agent
boundary — and freezes them into ``real_model_outputs.jsonl`` with a
provenance note (provider + model + date). This proves the demo inputs are
real model behaviour, not strawmen.

This script is NEVER on a runtime path: core, demo, and benchmark stay
offline with no API key (AC8). The API call happens once, by hand:

    python examples/harvest_fixtures.py            # reads .env or environment

Requires ``ANTHROPIC_API_KEY`` or ``OPENAI_API_KEY``. Zero third-party
dependencies — stdlib ``urllib`` only.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
import urllib.request
from pathlib import Path
from typing import Any

# Note: these are merely the *current* defaults for new harvests. The frozen
# fixtures in ``real_model_outputs.jsonl`` were harvested with an explicit
# ``--model claude-haiku-4-5`` — the authoritative record of what produced
# them is the ``provenance`` field inside that file, not this dict.
DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-4-6",
    "openai": "gpt-4o-mini",
}

#: The corpus shown to the model — verbatim the source set from
#: ``sample_corpus.md`` / ``run_demo.py`` (markers included, as an upstream
#: retrieval step would carry it).
CORPUS = """\
[src-photosynthesis]
Photosynthesis converts light energy into chemical energy [1]. The process \
occurs mainly in the leaves of plants [2].

[src-water-cycle]
Water evaporates from oceans and lakes [1]. It later condenses into clouds \
and returns as precipitation [2].

[src-honeybee]
Honeybees communicate the location of food using a waggle dance [1].
"""

#: Committed verbatim so the harvest is auditable: the model is blind to the
#: grounding mechanism — it is only asked to behave like a downstream agent.
HARVEST_PROMPT = """\
You are the final synthesis agent at the end of a multi-agent research \
pipeline. An upstream retrieval step selected the following curated sources \
(inline [N] markers are its own citation anchors):

{corpus}

Your output is final, user-facing prose. As is typical after several \
rewrite/synthesis hops, the inline citation anchors do NOT survive into your \
output.

Produce exactly {count} standalone factual claims derived ONLY from these \
sources, mixing these styles:
- "paraphrase": restate a single source sentence in your own words;
- "fragment-combination": join two parts drawn from the same source;
- "multi-source-synthesis": one claim combining facts from two sources.

Rules: do not copy any source sentence verbatim; do not include [N] markers \
or URLs; one sentence per claim.

Return ONLY a JSON array, no prose, where each element is \
{{"category": "<one of the three styles>", "text": "<the claim>"}}.
"""


def _load_dotenv(path: Path) -> None:
    """Load KEY=VALUE lines from ``path`` into the environment (no override)."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
    request = urllib.request.Request(  # fixed https endpoints only
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"content-type": "application/json", **headers},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        body: dict[str, Any] = json.loads(response.read().decode("utf-8"))
    return body


def _call_anthropic(prompt: str, model: str, api_key: str) -> str:
    body = _post_json(
        "https://api.anthropic.com/v1/messages",
        {
            "model": model,
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": prompt}],
        },
        {"x-api-key": api_key, "anthropic-version": "2023-06-01"},
    )
    text = body["content"][0]["text"]
    assert isinstance(text, str)
    return text


def _call_openai(prompt: str, model: str, api_key: str) -> str:
    body = _post_json(
        "https://api.openai.com/v1/chat/completions",
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
        },
        {"authorization": f"Bearer {api_key}"},
    )
    text = body["choices"][0]["message"]["content"]
    assert isinstance(text, str)
    return text


def _extract_json_array(raw: str) -> list[dict[str, str]]:
    """Tolerate code fences / surrounding prose around the JSON array."""
    start, end = raw.find("["), raw.rfind("]")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"no JSON array found in model output:\n{raw}")
    items = json.loads(raw[start : end + 1])
    if not isinstance(items, list):
        raise ValueError("model output is not a JSON array")
    out: list[dict[str, str]] = []
    for item in items:
        if not isinstance(item, dict) or "category" not in item or "text" not in item:
            raise ValueError(f"malformed item in model output: {item!r}")
        out.append({"category": str(item["category"]), "text": str(item["text"])})
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=["auto", "anthropic", "openai"], default="auto")
    parser.add_argument("--model", default=None, help="override the provider's default model")
    parser.add_argument("--count", type=int, default=10, help="claims to harvest (default 10)")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).with_name("real_model_outputs.jsonl"),
    )
    parser.add_argument(
        "--raw-file",
        type=Path,
        default=None,
        help=(
            "freeze from a saved raw model response instead of calling an API "
            "(requires explicit --provider and --model for the provenance note)"
        ),
    )
    parser.add_argument(
        "--note",
        default=None,
        help="extra provenance note (e.g. how the raw response was obtained)",
    )
    args = parser.parse_args()

    provider: str = args.provider
    model: str | None = args.model

    if args.raw_file is not None:
        if provider == "auto" or model is None:
            print("error: --raw-file requires explicit --provider and --model")
            return 1
        raw_file: Path = args.raw_file
        print(f"freezing raw response from {raw_file} ({provider}/{model}) ...")
        claims = _extract_json_array(raw_file.read_text())
    else:
        _load_dotenv(Path(__file__).resolve().parent.parent / ".env")

        if provider == "auto":
            if os.environ.get("ANTHROPIC_API_KEY"):
                provider = "anthropic"
            elif os.environ.get("OPENAI_API_KEY"):
                provider = "openai"
            else:
                print("error: set ANTHROPIC_API_KEY or OPENAI_API_KEY (.env or environment)")
                return 1

        key_name = "ANTHROPIC_API_KEY" if provider == "anthropic" else "OPENAI_API_KEY"
        api_key = os.environ.get(key_name)
        if not api_key:
            print(f"error: {key_name} is not set")
            return 1

        model = model or DEFAULT_MODELS[provider]
        prompt = HARVEST_PROMPT.format(corpus=CORPUS, count=args.count)

        print(f"harvesting {args.count} claims from {provider}/{model} ...")
        call = _call_anthropic if provider == "anthropic" else _call_openai
        claims = _extract_json_array(call(prompt, model, api_key))

    harvested = datetime.date.today().isoformat()
    provenance: dict[str, str] = {
        "provider": provider,
        "model": model,
        "harvested": harvested,
        "script": "examples/harvest_fixtures.py",
    }
    if args.note:
        provenance["note"] = str(args.note)

    out: Path = args.out
    with out.open("w") as fh:
        for i, claim in enumerate(claims, start=1):
            record = {
                "claim_id": f"real-{i:02d}",
                "quote": claim["text"],
                "category": claim["category"],
                "provenance": provenance,
            }
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"wrote {len(claims)} fixtures -> {out}")
    print("re-run `python examples/run_demo.py` to ground them (offline).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
