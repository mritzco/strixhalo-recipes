# Contributing

Welcome. This repo is a **registry of reproducible, evidence-backed
recipes for running local LLMs on unified-memory Linux boxes** (Strix
Halo first). Both humans and agents contribute — the docs are written so
an agent with no history can pick up any workflow from `SKILL.md`.

## Orientation (read in this order)

1. `README.md` — what this is, quick start, licensing
2. `AGENTS.md` — vision, collected requirements, roles, hard rules, data flow
3. `SKILL.md` — operational manual: search, replicate, test, submit, contribute
4. `FORMAT.md` + `SPEC.md` — data model, trust rules, format rationale
5. `ROADMAP.md` + `openspec/changes/` — how the project was built and what's planned

## What you can contribute

| Contribution | Mechanism | Reviewed by |
|---|---|---|
| Result for an existing recipe (a run) | `tools/submit_result.py` | automated (validate + hooks); counts toward witnesses |
| New recipe / variant | `tools/collect.py` draft → annotate → PR | maintainers + witness rule |
| Failed recipe | same path, `status: failed` + `failure_notes` | as valuable as a success |
| New or improved test | `tests/definitions/<id>.json` + runner PR (semver'd) | maintainers; schema + CI automated |
| New distro/engine support | `tools/probe.d/<family>.sh` (copy `arch.sh`) / `backend.engine` | maintainers — only what a real box proved |
| Docs / data-model proposals | openspec change (see ROADMAP) | maintainers |

**Agents:** if your experiment measures something the battery misses,
propose the test in the same PR (see SKILL.md → Writing or improving a
test). That rule exists because toy tests produced a phantom +84% PP
win that refutation later removed — the battery must grow with usage.

## Hard rules (the trust model lives in FORMAT.md/SPEC.md)

- Results are **append-only** — never edit a file under `results/`.
- Recipes apply to a **model**, not a quant; never hand-set
  `content_hash` (quant/size/docs don't change it).
- `status: validated` is never written by hand — it is derived from
  witnesses in the generated board.
- `capabilities_confirmed` (tools/mcp/vision) is true only after a real
  harness test. Chat-only recipes are incomplete.
- One experiment = one PR. Failures are committed as data.
- Custom backends: record `upstream` (fork URL) + `patches[]` (PRs) +
  fork `commit`, so patches can be dropped when they land upstream.
- License zones: code Apache-2.0, registry data CC0, docs CC BY 4.0.
  You warrant you may license what you submit; third-party material is
  referenced, not embedded.

## PR conventions

- Branch: `recipes/<model>/<slug>` or `experiment/<topic>`.
- Before committing: `bash tools/install-hooks.sh` (once) — the
  pre-commit hook validates everything and fails if the generated
  stores/board are stale. CI enforces the same gate.
- Commit regenerated files (`index.json`, `runs.json`, `models/`,
  `LEADERBOARD.md`) in the same PR.
- Cross-validation requires ≥ 2 **independent** contributors — aliases
  of one person count as one witness.

## Questions / ideas

Open an issue, or propose an openspec change (see `ROADMAP.md` for the
queue and how enhancements flow).
