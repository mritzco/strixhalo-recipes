# Strix Halo Recipe Registry

Reproducible, evidence-backed serving recipes for local LLMs on
unified-memory Linux boxes (Strix Halo class first) — built so an agent
**or a human** can capture a working setup in seconds, verify what
someone else claimed in seconds, and contribute results without trusting
a single person's word.

**The vision:** a database of *explained* configurations — what to run
*and why every parameter was chosen*, what each recipe optimizes, and
which capabilities (tools / MCP / vision) are proven by real harness
tests. Recipes apply to a **model**, not a quant. Results are immutable
evidence; cross-validation is derived from independent witnesses, never
asserted. Chat-only recipes are considered incomplete. How it's built:
`ROADMAP.md` + `openspec/changes/`. Codebase map (what each module
does): `docs/ARCHITECTURE.md`. Agent orientation: `AGENTS.md`.
Data model & trust: `SPEC.md` / `FORMAT.md`. Contributing:
`CONTRIBUTING.md`.

## Try these first (featured setups)

| Model / recipe | Why | Evidence |
|---|---|---|
| [**qwen3.8-flash-uncensored**](models/qwen3.8-flash-next-uncensored.md) | Best all-round stack: myhacsint fork + shared MTP (0.947 acceptance) + uncensored IQ4_XS @131k + mmproj — the only recipe here with tools **and** vision **and** agent-coding **and** real-harness (omp) all confirmed | tools ✅ vision ✅ agent-coding ✅ harness ✅ · 30.8–43.9 t/s |
| [**qwen3.8-flash-next-131k**](models/qwen3.8-flash-next-131k.md) | Stock-aligned alternative (mainline, no MTP) at 131k for agent work | tools ✅ agent-coding ✅ context ✅ · field 14.6–18.4 t/s |
| [**qwen3-coder**](models/qwen3-coder.md) | Fast lightweight default (~65 t/s), reliable tools | tools ✅ agent-coding ✅ |
| [**qwen3.8-27b-vl**](models/qwen3.8-27b-vl.md) | Dense vision (slight detail edge) | vision ✅ |
| [**qwen3-vl**](models/qwen3-vl.md) | Small fast MoE vision | draft — vision test pending |

_Every ✅ is a real test run, not a claim. Browse everything:
[LEADERBOARD.md](LEADERBOARD.md) (all models & results) or `models/`
(one page per model: variants, runs, sources). Want your setup here?
Capture it with `analyze cmd "your launch line" --write` and open a PR._

## What you can do

| You want to… | Run this |
|---|---|
| Check your machine (is my setup registry-compatible?) | `python tools/analyze.py machine` — profile + probe schema check |
| Capture a setup you already have running | `python tools/analyze.py cmd "your llama-server line" --write` → get an id + test hash to share |
| Find existing setups | `python tools/search.py --model qwen3` · `--quant Q8_0` · `--hash 10a6b2` · `--vision` — or read `LEADERBOARD.md` / `models/` |
| Test a model someone posted (id + hash) | `python tools/analyze.py test --recipe <id> [--hash <prefix>] --endpoint http://127.0.0.1:8080/v1` |
| Contribute your results | add `--submit --contributor <you>` to the test command — one result = one PR |
| Add something new | give your agent a goal + access to this repo and `SKILL.md`; it captures, tests, and commits results — **good and bad** (failures are data), one experiment per PR |

**Naming:** a recipe `id` is the human name of a deployment
(`qwen3-coder`); the exact configuration — source repo, quant, every
flag — lives in the recipe file, versioned over time. The pin is the
**content hash**: share `id + hash-prefix` and anyone can reproduce the
exact setup (`analyze ... --hash`). Details: FORMAT.md → *Naming vs
pinning*.

## Tools in this repo (and how to improve them)

| Tool | What it does |
|---|---|
| `tools/analyze.py` | One-command daily flow: `machine` / `cmd` (capture) / `test` (battery) |
| `tools/probe.sh` + `probe.d/` | Machine fingerprint v2 (memory model, GPU, backend commit, install method) |
| `tools/collect.py` | Batch draft recipes from llama-swap config / pid / launch command |
| `tools/validate.py` | Schema + content-hash validation for recipes, results, test definitions |
| `tools/submit_result.py` | Write immutable result records (append-only) |
| `tools/registry.py` + stores | Data layer: `index.json`, `runs.json`, `models/<id>.json` + `Store` query API |
| `tools/search.py` / `tools/leaderboard.py` / `tools/admin.py` | Search · board renderer · derived-trust admin views |
| `tests/` | Semver'd definitions + runners emitting the evidence JSON contract |

**Improving them:** agents/extensions follow `SKILL.md` + `CONTRIBUTING.md`.
Extension points: a new distro family = `probe.d/<family>.sh` (copy
`arch.sh`, register in `detect_family`); a new capability test = a
`tests/definitions/` PR **proposed with the experiment that needed it**;
a new engine (`ollama`/`lemonade`) = recipe `backend.engine` + probe
support.

## Repo's own machinery

- **Hooks** — `.githooks/pre-commit`: every commit validates and fails
  if generated files are stale (`bash tools/install-hooks.sh`); CI runs
  the same gate.
- **Skill** — `SKILL.md` (+ `AGENTS.md`) is the agent manual; the repo
  *is* the skill.
- **Validators** — `validate.py` (schema + hash recompute), `admin.py`
  (derived trust, provenance).
- **Indexes/stores** — one compute engine (`registry.py`) → flat index,
  runs store, per-model documents, markdown board. Never hand-edited.
- **Schemas** — `schema/recipe.schema.json`, `result.schema.json`,
  `test-definition.schema.json` (source of truth for validation).

## Try it yourself (2 minutes)

```bash
git clone <this repo> && cd <repo>
python3 -m venv .venv && .venv/bin/pip install -r tools/requirements.txt
.venv/bin/python tools/analyze.py machine      # your machine profile + schema check
.venv/bin/python tools/search.py --model qwen3  # what's in the registry
.venv/bin/python tools/leaderboard.py           # regenerate the board
# query the data layer:
.venv/bin/python -c "from tools.registry import Store; print(Store().find(sort='tg', limit=5))"
bash tools/install-hooks.sh                     # validate on every commit
```

Test any model on **your** server (any OpenAI-`/v1` endpoint — llama.cpp,
llama-swap, ollama, LM Studio):

```bash
export LLAMA_ENDPOINT=http://127.0.0.1:8080/v1
python3 tests/runners/tool_roundtrip.py --model your-model   # tool parsing
python3 tests/runners/agent_coding.py  --model your-model    # coding-agent loop
python3 tests/runners/vision_basic.py  --model your-vl-model # vision (mmproj)
```

## Layout

```
schema/ recipes/ results/ tests/ tools/    # source of truth (see above)
index.json runs.json models/*.json         # generated JSON stores (CC0)
LEADERBOARD.md models/*.md                 # generated markdown board (CC0)
docs/                                     # codebase map (qwen-generated sample)
openspec/ ROADMAP.md                       # how it was built; change queue
specs/                                     # founding reference docs
.githooks/ .github/workflows/              # local + CI enforcement
LICENSE LICENSE-DATA LICENSE-DOCS          # Apache-2.0 / CC0-1.0 / CC BY 4.0
```

## Contributing

Humans and agents — see `CONTRIBUTING.md` (what to contribute, hard
rules, PR conventions). Short version: one experiment = one PR, results
are append-only, capability claims require a real test, failures are
committed as data, and you warrant you may license what you submit
(third-party material is referenced, not embedded).
