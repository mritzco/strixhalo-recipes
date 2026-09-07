# AGENTS.md — AI Recipe Registry (working title: `strixhalo-recipes`)

Purpose of this file: give any agent (or human) landing in this repo the
full context needed to contribute safely — what this project is, which
documents are authoritative, what roles agents play, and the hard rules
that protect the data's trust model.

Status: **v1 implemented & live-verified (2026-09-07)**. Repo root
`/home/itzco/Projects/strixhalo` IS the product repo (git init'd; code at
root, `openspec/` planning committed for transparency, `specs/` holds
founding reference docs). Source specs below are now reconciled into
`SPEC.md` / `FORMAT.md` / `SKILL.md`; remaining drift reports to the
issue tracker.

---

## 1. What this is

An open-source git repo that acts as a **database of recipes and
knowledge for running local models on Strix Halo class machines**
(unified-memory Linux APUs — this design targets 128 GB Strix Halo
first, but nothing is hardcoded to it).

A recipe is a reproducible, *explained* serving configuration: pinned
backend, launch command, why each parameter was chosen, what the author
was trying to achieve, and which capabilities (tools / MCP / vision /
agent harness) were actually confirmed — not guessed.

The repo is built **agent-first**: an agent clones it, installs its
skill, searches recipes, replicates one from a plain script, runs tests,
submits results, and opens one PR per experiment. Humans validate via
multi-witness rules, not by trusting a single commit.

The failure mode this exists to prevent: every agent independently
"tries things", commits a message full of confident understanding, and
nobody can cross-check other recipes or replicate results. Everything
here exists to make cross-checking and replication cheap.

## 2. Source documents (not yet reconciled — read all three)

| Doc | Role | Origin |
|---|---|---|
| `SPEC.md` | Build spec: goals, non-goals, trust rules, checkpoints | Claude build (needs v0.3 + below folded in) |
| `FORMAT.md` | Recipe/result format rationale, versioning, lineage | Claude build |
| `SKILL.md` | Day-to-day agent instructions (search / replicate / submit / contribute) | Claude build |
| `AGENTS.md` | This file — orientation + collected requirements | Consolidation (see §3–§7) |
| `specs/AI_Recipe_Registry_SPEC_v0.3.md` | Amendment: annotations, objectives/tradeoffs, evidence model, non-numeric tests | Human + ChatGPT — founding reference doc, kept in repo-root `specs/` |

**Task for the next design pass:** reconcile the two lineages into one
authoritative data model before Checkpoint 0 (schema freeze). The v0.3
amendment was written to be folded in *before* freezing — it currently is
not reflected in `schema/*.json`.

## 3. Collected requirements (from the project owner + specs)

1. **Agents install a skill** that ships with this repo (clone first, or
   the skill is the repo).
2. **Search before you act** — agents operate tools to find existing
   recipes; no duplicate experiments without checking.
3. **Replicate, don't improvise** — a recipe must be reproducible by a
   plain `bash`/`fish` (more flavours later) script that installs/serves
   everything. When trying a variant, fork a new recipe with lineage.
4. **Standard tests, machine-runnable** — agents run tests in a standard
   manner, then commit experiment + aggregate results (an admin or the
   leaderboard can aggregate later).
5. **Failures are first-class** — agents add both failed and successful
   recipes; a failure with a reason beats silent repetition.
6. **Full context per recipe** — goals, features, results, *why each
   parameter was chosen*, and what the user/bot was trying to do.
7. **Recipe ↔ model, not quant** — recipes target a specific model, NOT
   a specific quant. Quants are a dimension to try/test under a recipe.
8. **Multi-parent lineage** — recipes inherit from 1..n parents (e.g.
   vision recipe + MCP recipe → merged recipe), like the model family
   trees in genomics.
9. **One PR per experiment** — agents submit results/experiments as
   clean, reviewable PRs.
10. **Summaries / leaderboards** — agents have tools to run summaries and
    leaderboards so humans (and agents) know what is worth trying.
11. **Multi-person validation** — recipes validated by multiple people;
    each validator's experience is recorded and kept.
12. **Admin skill** — admins have tooling (same skill or a second one) to
    validate that recipes are machine-generated and valid, with automatic
    pull/merge handling.
13. **Versioned tests** — contributors improve tests over time; changes
    may break compatibility → tests are semver'd.
14. **Harness capability is core, not a footnote** — tests must exercise
    the model through a real harness: Pi and OMP (current harnesses), tool
    use, vision (mmproj where the model supports it), MCP. A recipe that
    only proves chat works has unlocked ~5% of the machine's capability.

## 4. v0.3 amendment — the parts the current build is missing

From `specs/AI_Recipe_Registry_SPEC_v0.3.md` (authoritative intent; the
current schemas do NOT yet implement these):

- **Parameter annotations & rationale** — each parameter carries
  `value` + structured `annotations[]` (`type`: recommendation | warning
  | required | quality | performance | compatibility | evidence |
  experimental | deprecated) + optional `evidence` refs to tests/runs.
- **Annotation scope ladder** — global → model → variant → quant →
  runtime → recipe → parameter → test/run. General knowledge lives at the
  broadest correct scope so agents can answer "why does this recipe use
  Q8 K-cache?" by walking evidence.
- **Objectives / constraints / tradeoffs** — recipes declare what they
  optimize (quality, agent_capability, throughput, memory…), constraints
  (vision_required, mcp_required, fits_in_available_memory), and explicit
  tradeoffs. **No universal recipe score**; composite rankings must
  disclose weighting and never replace underlying evidence.
- **Tests are evidence, not necessarily benchmarks** — a valid test may
  have zero numeric metrics. Evidence chain: test definition → execution
  → observations + optional metrics + artifacts → outcome → immutable
  run. `metrics` optional (may be `{}`), `observations[]` and
  `artifacts[]` first-class.
- **Canonical statuses** — pass | fail | degraded | unsupported |
  not_run | inconclusive (current build only has pass/fail/error/skipped
  on results and experimental/validated/deprecated/failed on recipes;
  `degraded`/`unsupported`/`not_run`/`inconclusive` and evidence
  semantics are missing).
- **Evidence-backed knowledge model** — distinguish declared rationale /
  observed evidence / validated knowledge / generated aggregate. Derived
  outputs (leaderboards, aggregates) must come from immutable records.

## 5. Roles agents play in this repo

**Replicator / runner** — search → pick recipe (prefer ≥2 witnesses) →
run its install/serve script verbatim → probe the machine → run the
recipe's `tests[]` → submit a result → tell the human the commit/PR
steps (never push unannounced).

**Experimenter / contributor** — search first; generate drafts with
`tools/collect.py` (never hand-write YAML boilerplate); fill in what the
tool cannot know; set lineage parents (1..n, each with a one-line
contribution); commit failures too.

**Tester / validator** — run capability tests through real harnesses
(pi, omp/oh-my-pi) — tool calls, MCP round-trips, vision via mmproj —
and record truthful `capabilities_confirmed`. Marking a capability true
without testing it is the cardinal sin of this repo.

**Aggregator (human or admin)** — regenerate index + leaderboard from
immutable results; cross-validation status is derived, never typed.

## 6. Hard rules (enforced in code where possible)

- Never hand-set `content_hash`; let `validate.py` compute it.
- Never edit files under `results/` — append-only; correct by submitting
  a new run.
- Never write `status: validated` into recipe YAML by hand — trust
  status lives in generated `LEADERBOARD.md`/`index.json`; a recipe's own
  `status` stays honest about the author's intent (experimental/failed/
  deprecated).
- Never claim `capabilities_confirmed: tools/mcp/vision` without an
  actual test run through a harness.
- Cross-validation requires ≥ 2 distinct `contributor_id`s at the same
  reproducibility key (one person running 3× is still 1 witness).
- A recipe that only proves chat works is an incomplete recipe.
- Respect the license zones (`README.md` → Licensing): records under
  `recipes/`/`results/` are CC0, code under `tools/`/`tests/`/`schema/`
  is Apache-2.0, docs under CC BY 4.0. By contributing you warrant you
  hold the rights; never embed third-party material (model outputs,
  benchmark prompts, images, vendor metadata) you do not own — reference
  it or mark it with its own license instead.

## 7. Dev machine facts (this box — CachyOS)

- AMD Ryzen AI MAX+ 395, Radeon 8060S (gfx1151), 128 GB unified; fixed
  VRAM 512 MB, GTT 110 GB (`amdgpu.gttsize=112640`, `ttm.pages_limit`,
  `ttm.page_pool_size` in kernel cmdline). Usable RAM ≈ 124.9 GB.
- llama.cpp via Mesa RADV/Vulkan (no ROCm): `llama-server` build 10809,
  commit 5266f24da7, Vulkan 1.4.354. `--jinja` required for tool calls.
- llama-swap (0.4.0-dev) on `127.0.0.1:1234`, config
  `~/.config/llama-swap/config.yaml`; models: `qwen3-coder`,
  `qwen3-instruct`, `qwen3-vl`, `glm-4.5-air` (all
  `unsloth/…:UD-Q4_K_XL` via `-hf`) + `qwen3.8-27b` (Q8_0 local GGUF)
  and `qwen3.8-27b-vl` (+ `mmproj-F16.gguf`). IPv4 gotcha: llama-swap
  must `proxy: http://127.0.0.1:${PORT}` (llama-server binds IPv4).
- Local models: `~/models/Qwen3.8-27B-GGUF/` (Q8_0 + mmproj-BF16/F16),
  HF cache `~/.cache/huggingface/`.
- Verified knowledge: GLM-4.5-Air breaks omp tool-calling (stream parse
  failure) though it is fine in plain chat; Qwen coder/instruct are the
  reliable omp agents; Q8 KV cache extends context with little quality
  loss; dense models are slow on this bandwidth-bound box (MoE first).

## 8. Where this stands (assessment, 2026-09-07)

Working (verified on this machine): `tools/probe.sh` produces correct
JSON (family arch, GPU, Vulkan, backend build, llama-swap config path);
`tools/collect.py` turns a local-model launch command into a schema-shaped
draft with correct `content_hash` and GGUF metadata; `build_index.py`,
`search.py`, `leaderboard.py` run.

Broken or missing (must be fixed before v1):
- The example recipe that failed `validate.py --strict` (YAML `date` vs
  schema `string` for `created`) was synthetic — removed in bootstrap;
  tree now validates clean (empty).
- v0.3 amendment unimplemented in schemas (§4) — annotations,
  objectives/tradeoffs, evidence model, statuses, optional metrics,
  observation/artifact fields.
- Quant is baked into `model.quant` + `content_hash` — conflicts with
  requirement 7 (recipe ↔ model, not quant).
- `collect.py` cannot handle `-hf` model specs (llama-swap's first 4
  entries), misses `-fa on` (only detects `--flash-attn`), does not read
  `--mmproj` → would draft `vision: false` for a vision setup, and
  misuses probe `backend_version` as `backend.commit`.
- `tests/` are stubs that always pass — zero evidential value.
- `tools/probe.d/{debian,fedora}.sh` are unverified stubs; only `arch.sh`
  is real. `probe.d/` sits at `tools/probe.d/`.
- No commits yet, no CI run, no PR workflow, no admin skill, no
  summaries/leaderboard beyond raw medians, no test-semver registry.
- The synthetic `qwen3.5-235b` fixture was removed and `index.json` /
  `LEADERBOARD.md` regenerated to a clean empty state (2026-09-07).

Net: the tooling skeleton was kept; the data model was reworked
(quant-agnostic identity, annotations, objectives/tradeoffs, evidence
model) before Checkpoint 0, and tests/collect/probe were reimplemented.
**Live verification (2026-09-07, this box):** probe v2 correct; 6 recipe
drafts collected from llama-swap and validated; quant-swap and doc edits
proven not to change content_hash; real runs on qwen3.8-27b (+mmproj):
tool-roundtrip pass, throughput pass (~7 tok/s, dense Q8_0), context
recall pass @4k, vision unsupported on text deployment / pass on
qwen3.8-27b-vl; 2 result records submitted; index/leaderboard/admin
derived views regenerated. See `LEADERBOARD.md`.
