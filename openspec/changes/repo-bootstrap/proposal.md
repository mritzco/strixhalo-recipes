## Why

The working tree was not a usable repo: planning (openspec), reference
specs, and a Claude prototype build were scattered, with synthetic
fixture data that failed its own validator and stale machine paths. The
repo root `/home/itzco/Projects/strixhalo` is now the product repo (git
init'd 2026-09-07): code and specs live in ONE history so the public
repo shows how it was built. Nested git repos were rejected: they
fragment history and confuse agents.

## What Changes

- Repo root IS the repository; product code lives at root (the Claude
  prototype build was moved from `specs/strixhalo-recipes/` to the root
  as the working baseline: `schema/`, `tools/`, `tests/`, `recipes/`,
  `results/`, `.github/`, `SPEC.md`, `FORMAT.md`, `SKILL.md`, `AGENTS.md`,
  `README.md`).
- `.gitignore` excludes machine-local agent harness state (`.pi/`,
  `.omp/`, `.claude/`), editor temp files, Python artifacts, and scratch
  probe outputs — "results of our work and the specs" are committed,
  other agents' scratch never is.
- `specs/` demoted to reference-only: `AI_Recipe_Registry_SPEC_v0.3.md`
  (founding spec), `sample-articles-reddit.md` (research), and
  `strixhalo-recipes.zip` (pristine prototype snapshot). Junk removed:
  stray `{schema,recipes…}` brace-expansion dirs, `specs/.swp`.
- Synthetic `qwen3.5-235b` example recipe + result removed (**BREAKING**
  for fixture-dependent tests); `index.json` / `LEADERBOARD.md`
  regenerated to a clean empty state (also drops the stale
  `/home/claude/...` path).
- `openspec/` (this change queue + archives) and `ROADMAP.md` committed
  for transparency: other users can see the build order and rationale.
- Licensing resolved (tri-license): `LICENSE` (Apache-2.0) for software
  (`tools/`, `tests/`, `schema/`, `.github/`), `LICENSE-DATA` (CC0-1.0)
  for registry records + generated aggregates (`recipes/`, `results/`,
  `index.json`, `LEADERBOARD.md`; `recipes/LICENSE` + `results/LICENSE`
  folder markers added), `LICENSE-DOCS` (CC BY 4.0) for docs/specs.
  Contribution warranty (no third-party material under CC0 without
  rights) documented in README → Licensing and AGENTS.md hard rules.
- Remaining: README accuracy pass and the first baseline commit message
  convention.

No spec-level behavior changes — repository hygiene and layout only,
hence `skip_specs: true`.

## Capabilities

### New Capabilities

None — operations/tooling change; opts out via `skip_specs: true` in
`.openspec.yaml`.

### Modified Capabilities

None.

## Impact

Repo root `/home/itzco/Projects/strixhalo` — git metadata, `.gitignore`,
layout (product at root, `specs/` = reference, `openspec/` = planning),
generated `index.json`/`LEADERBOARD.md`, fixture + junk deletion. No
tool or schema behavior changes (those land in later changes). Do first:
every later change validates and applies inside this repo.
