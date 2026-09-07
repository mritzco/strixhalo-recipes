# strixhalo-recipes

Reproducible LLM-serving recipes for unified-memory Linux boxes (Strix
Halo class APUs first), with lineage tracking and multi-witness trust —
built so an AI agent can search, replicate, test, and contribute results
with minimal token spend and without anyone having to trust a single
person's claimed win.

**The vision in one paragraph:** a database of *explained* serving
configurations — each recipe pins what to run and why every parameter
was chosen, records what it was optimizing (throughput? agent
capability? vision?), and proves its capability claims with real harness
tests. Recipes apply to a model, not a quant; results are immutable
evidence; cross-validation is derived from independent witnesses, never
asserted. Any model that only proves chat works is considered
incomplete. How we built it: `ROADMAP.md` + `openspec/changes/`.

Start here:
- **`AGENTS.md`** — vision, requirements, roles, hard rules, data flow
  (read this first if you are an agent).
- **`SKILL.md`** — day-to-day operations: search, replicate, test,
  submit, contribute.
- **`FORMAT.md` / `SPEC.md`** — data model, format rationale, trust rules.
- **`CONTRIBUTING.md`** — how humans and agents add work.
- **`LEADERBOARD.md`** — the generated results board (landing) and
  `models/` per-model pages.

## Try it yourself (2 minutes)

```bash
git clone <this repo> && cd <repo>
python3 -m venv .venv && .venv/bin/pip install -r tools/requirements.txt
.venv/bin/python tools/validate.py --strict      # everything is consistent
.venv/bin/python tools/search.py --model qwen3   # query the registry
.venv/bin/python tools/leaderboard.py            # regenerate + read the board
# query the JSON data layer without parsing YAML:
.venv/bin/python -c "from tools.registry import Store; print(Store().find(sort='tg', limit=5))"
bash tools/install-hooks.sh                      # validate on every commit
```

Run tests against **your** server — point the battery anywhere that
speaks OpenAI `/v1` (llama.cpp, llama-swap, ollama, LM Studio):

```bash
export LLAMA_ENDPOINT=http://127.0.0.1:8080/v1     # your endpoint
python3 tests/runners/tool_roundtrip.py --model your-model
python3 tests/runners/agent_coding.py  --model your-model   # coding-agent loop
```

## Quick start

```bash
pip install -r tools/requirements.txt

# see what's here
python tools/build_index.py
python tools/search.py --model qwen3

# validate everything (recipes + results + test definitions)
python tools/validate.py --strict

# regenerate the human-readable leaderboard (derived trust lives here)
python tools/leaderboard.py

# fingerprint this machine (probe v2: mem model, GPU, backend commit)
bash tools/probe.sh > /tmp/probe.json

# draft one recipe per llama-swap system (no hand-written YAML):
python tools/collect.py --from-llama-swap --author you --dry-run
# drop --dry-run to write recipes/<system>/<system>-v0.1.0.yaml

# run a versioned capability test against the endpoint
python tests/runners/tool_roundtrip.py --model qwen3-coder > /tmp/tool.json

# submit an immutable result record after running the recipe's tests
python tools/submit_result.py \
  --recipe qwen3-coder \
  --contributor your-stable-handle \
  --evidence tool-roundtrip=/tmp/tool.json \
  --notes "stable 3h session"
```

## Layout

```
schema/             JSON Schemas: recipe, result, test-definition (source of truth)
recipes/<model>/    One YAML file per recipe version (CC0 zone)
results/<id>/<hash>/  Append-only evidence records (CC0 zone)
tools/              probe.sh (+ probe.d/<family>.sh), collect.py, gguf_lite.py,
                    validate.py, submit_result.py, build_index.py, search.py,
                    leaderboard.py, admin.py
tests/definitions/  Semver'd test definitions (evidence contracts)
tests/runners/      Test runners emitting the evidence JSON contract
index.json          Generated JSON store — flat model rows (CC0)
runs.json           Generated JSON store — every result, newest first (CC0)
models/<id>.md      Generated — per-model pages (variants, runs, sources) (CC0)
models/<id>.json    Generated JSON store — per-model documents (CC0)
LEADERBOARD.md      Generated — landing: Models, Latest tests, how-to (CC0)
.githooks/          Pre-commit hook (validate + generated-file freshness)
LICENSE / LICENSE-DATA / LICENSE-DOCS   Apache-2.0 / CC0-1.0 / CC BY 4.0
```

## Contributing an OS you use that isn't covered yet

See `SPEC.md` §7. Adding Debian/Fedora/whatever-else support is a single
new file in `tools/probe.d/` (copy `arch.sh`, the verified reference
implementation) plus a one-line registration in `detect_family()` in
`tools/probe.sh` — no other code changes needed. Unverified modules must
not claim support: ship only what a real box proved.

## Licensing

The repository is split into three license zones — see `LICENSE`
(Apache-2.0), `LICENSE-DATA` (CC0 1.0), and `LICENSE-DOCS`
(CC BY 4.0) for full texts:

```text
Software source code in this repository — tools/, tests/, schema/,
.github/ and any other functional code — is licensed under the Apache
License 2.0.

Registry data, including recipes, run records, validations, test
results, hardware records, model metadata, annotations, and generated
indexes (recipes/, results/, index.json, LEADERBOARD.md), is dedicated
to the public domain under CC0 1.0.

Documentation is licensed under CC BY 4.0.
```

Directory-level mapping:

| Path | License |
|---|---|
| `tools/`, `tests/`, `schema/`, `.github/` | Apache-2.0 (software & functional contracts) |
| `recipes/`, `results/` (and `LICENSE` markers inside them) | CC0-1.0 (registry records) |
| `index.json`, `LEADERBOARD.md` | CC0-1.0 (generated aggregates) |
| Root `*.md`, `specs/`, `openspec/` | CC BY 4.0 (documentation & specs) |

**Contribution warranty:** by contributing you warrant that you hold the
rights to the content under the zone's license. Submitted records and
artifacts may contain third-party material (model outputs, benchmark
prompts, images, vendor metadata) — you cannot dedicate what you do not
own. Reference such material from a record instead of embedding it, or
store it under its own license and say so.
