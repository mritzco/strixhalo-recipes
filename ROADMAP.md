# ROADMAP — AI Recipe Registry build queue

Planning home for building the **strixhalo-recipes** open-source repo.
Repo root `/home/itzco/Projects/strixhalo` IS the product repo: code at
root, `openspec/` (changes + archives) and `ROADMAP.md` committed for
transparency, `specs/` holds founding reference docs
(`AI_Recipe_Registry_SPEC_v0.3.md`, research, prototype snapshot zip).
Each queue item is an openspec change under `openspec/changes/<name>/`.
Build style: **sequential** — changes are proposed, reviewed, then
fleshed out (proposal → spec deltas → design → tasks) and applied one at
a time via openspec. The project is small; each change is independently
useful and testable on this box.

Source specs to reconcile: `specs/AI_Recipe_Registry_SPEC_v0.3.md` (data
model amendment) + `SPEC.md`/`FORMAT.md`/`SKILL.md` (prototype build,
moved to root as working baseline) + `AGENTS.md` (consolidated
orientation + assessment).

## Capability map (target `openspec/specs/`)

| Capability | Covers |
|---|---|
| `data-model` | Recipe object contract: model-scoped granularity (NOT quant), parameters + annotations, objectives/constraints/tradeoffs, lineage, content-hash field set |
| `evidence-records` | Semver'd test definitions, run/result records, canonical statuses, append-only + keying, witness/derived-status rules |
| `machine-probe` | Machine fingerprint JSON embedded in every result |
| `recipe-collection` | Draft generation from llama-swap / live process / launch cmd — never fabricates |
| `harness-testing` | Versioned capability tests through pi/omp; evidence emission; endpoint contract |
| `result-submission` | Record creation + one-PR-per-experiment conventions |
| `discovery` | Search index + multidimensional summaries/leaderboards |
| `admin-validation` | CI enforcement, admin trust tooling, auto-pull policy |
| `agent-skill` | Packaged skill + fresh-agent end-to-end acceptance |

## Queue (apply order)

| # | Change | New capabilities | Depends on | Status |
|---|---|---|---|---|
| 1 | `repo-bootstrap` | — (skip_specs: ops) | — | proposal |
| 2 | `checkpoint-0-data-model` | `data-model`, `evidence-records` | 1 | proposal |
| 3 | `probe-v2` | `machine-probe` | 2 | proposal |
| 4 | `collect-v2-llama-swap` | `recipe-collection` | 2 | proposal |
| 5 | `harness-tests-v1` | `harness-testing` | 2 | proposal |
| 6 | `submit-and-pr-flow` | `result-submission` | 3, 5 | proposal |
| 7 | `search-and-leaderboards` | `discovery` | 2, 6 | proposal |
| 8 | `admin-validation-ci` | `admin-validation` | 2–7 | proposal |
| 9 | `agent-skill-pack-v1` | `agent-skill` | 2–8 | proposal |

Every change currently holds **proposal.md only**. Before starting a
change: generate its full artifacts (specs deltas, design.md, tasks.md)
with the openspec propose workflow, review, then apply.

**Implementation status (2026-09-07):** the full v1 was implemented and
live-verified directly against this roadmap (changes 1–9 in one pass) —
see `AGENTS.md` §8 for verification evidence. The openspec proposals
remain as the design trail for that build; future enhancements should
flow through them (propose → review → apply).

## Open decisions needing the general review (before #2 spec phase)

1. **Quant-agnostic identity**: which fields compose the content_hash
   once quant is excluded; where quant lives (result dimension /
   parameter / `model.variants`).
2. **Recipe ↔ llama-swap mapping**: one recipe per llama-swap system key
   (`qwen3-coder`, `qwen3.8-27b-vl`, …) vs one per (model, config).
3. **Serving topology**: launch.command alone can't express llama-swap
   `proxy: 127.0.0.1` / ttl / preload — how recipes record the serving
   layer above llama-server.
4. **`-hf` model resolution** when the GGUF is not in the local HF cache.
5. **Contributor identity** scheme (stable pseudonymous id + salt).
6. **Repo hosting**: GitHub vs GitLab. (License resolved 2026-09-07:
   tri-license Apache-2.0 code / CC0-1.0 data / CC BY 4.0 docs — see
   `README.md` → Licensing; contribution warranty applies to submitted
   records.)

## Completion target (v1)

`collect.py` run against llama-swap produces one draft per system; a few
test iterations on this box; real recipes + results committed; a clean
first push to the public repo.
