# Strix Halo Recipes — Specification

**Status:** v1 implemented (2026-09-07), pending live verification and
community iteration. Source lineage: this doc + `FORMAT.md` +
`AGENTS.md` reconcile the original build spec with the v0.3 data-model
amendment and the project owner's requirements. The openspec change
queue under `openspec/changes/` records how it was built.

## 1. What this is

A git repo that works as a **database of recipes and knowledge for
running local models on Strix Halo class machines** (unified-memory
Linux APUs; 128 GB Strix Halo first, not hardcoded to it). A recipe is a
reproducible, *explained* serving configuration: pinned backend, launch
command, why each parameter was chosen, what the author was optimizing,
and which capabilities (tools / MCP / vision / agent harness) were
actually confirmed by tests — never guessed.

The repo is **agent-first**: an agent can clone it, install its skill
(`SKILL.md`), search recipes, replicate one, run its tests, submit
results, and open one PR per experiment. Humans validate through
multi-witness rules and admin tooling; nobody trusts a single commit.

## 2. Goals

1. **Reproducibility over narrative** — a recipe pins backend commit,
   build flags, launch command, hardware class, and (informatively) the
   quant it was tested with. Results are append-only and keyed by a
   content hash that **deliberately excludes quant**: recipes apply to a
   *model*, not a single quant.
2. **Explained, not just pinned** — parameters carry structured
   annotations (recommendation / warning / required / quality /
   performance / compatibility / evidence / experimental / deprecated)
   with evidence references; recipes declare objectives, constraints,
   and tradeoffs. Agents can answer "why Q8 K-cache?" by walking
   annotations → tests/runs.
3. **Trust via multiplicity** — no recipe is "validated" because one
   commit says so. Cross-validation is *derived* from ≥ 2 distinct
   contributor records at the same content hash with every declared test
   passing at least once. Status is never hand-set in YAML.
4. **Failures are data** — a recipe that OOMs or produces garbage is
   committed (`status: failed`, `failure_notes` required) so nobody
   repeats the experiment blind.
5. **Lineage, not overwrite** — improving a recipe creates a new version
   declaring its 0..n parents (merges are first-class: vision recipe +
   MCP recipe → combined recipe).
6. **Harness capability is core** — a recipe records whether the server
   exposes tool calling, MCP compatibility, and vision *as actually
   tested through real harnesses* (openai-api, pi, omp/oh-my-pi). A
   recipe that only proves chat works is incomplete.
7. **Cheap for agents** — one flat generated `index.json` powers search;
   agents never scan hundreds of YAMLs.
8. **Multi-OS at the tooling layer** — `probe.d/<family>.sh` is the
   extension point; unknown distros degrade to `family: unknown`, they
   do not fail. Only `arch` is verified so far.

## 3. Non-goals

- Not a general model-quality leaderboard. Scores here answer "does this
  recipe run, how fast, and does it retain the capabilities it claims".
  **No universal recipe score** — a composite ranking must disclose its
  weighting and never replace underlying evidence (v0.3 §2).
- Not a package manager — we record how *they* built/installed the
  backend, we do not install it for the user.
- Windows/macOS out of scope for v1 (structured to extend).

## 4. Core objects (details: `FORMAT.md`)

- **Recipe** (`recipes/<id>/<id>-v<version>.yaml`) — model-scoped,
  quant-agnostic identity; annotated parameters; objectives/constraints/
  tradeoffs; lineage; author-honest status
  (`experimental | failed | deprecated`).
- **Test definition** (`tests/definitions/<id>.json`, semver'd) —
  versioned evidence contract: capability class, runner, acceptance.
- **Result** (`results/<id>/<hash-hex>/<run_id>.json`) — one immutable
  record of one run: probe fingerprint, per-test evidence with canonical
  statuses `pass | fail | degraded | unsupported | not_run |
  inconclusive`, optional metrics, observations, artifacts. Never edited
  after submission.
- **Index** (`index.json`, generated) — flat search index, repo-relative
  paths, witness counts.
- **Leaderboard** (`LEADERBOARD.md`, generated) — derived
  cross-validation status + per-dimension medians. Trust lives here, not
  in recipe YAML.

## 5. Data model decisions (Checkpoint 0, frozen)

1. **Quant-agnostic hashing** — `content_hash` = sha256 over model
   identity (`name`/`arch`/`source`), backend identity
   (`engine`/`commit`/`build_flags`), normalized launch command
   (`--host`/`--port` stripped, quant literal → `{quant}`), and hardware
   target. `quant`, `size_gb`, env versions, annotations, docs never
   affect the hash. Results carry the quant they actually ran.
2. **Serving topology is knowledge** — `launch.serving` (fronted_by,
   endpoint, note) records the llama-swap layer above llama-server
   (IPv4-proxy gotcha, ttl); non-hashed.
3. **Evidence-backed knowledge** — annotations distinguish declared
   rationale from observed evidence; aggregates (index/leaderboard) are
   generated from immutable records only.
4. **Metrics optional** — a valid test can have no numeric metric at
   all; `observations`/`artifacts` are first-class (v0.3 §3).

## 6. Trust rules (enforced in code, not docs)

- `validate.py --strict` recomputes every content hash and rejects
  drift; `validated` is not a writable YAML status; `failed` requires
  `failure_notes`; result test ids must exist as definitions; run ids
  must be unique.
- `leaderboard.py` requires ≥ 2 distinct `contributor_id`s at the same
  content hash *and* all declared tests passing before marking
  cross-validated. One person running 5× is still 1 witness.
- Capability claims (`harness_compat.capabilities_confirmed`) are false
  until a real runner proves them; `collect.py` never auto-trues them.
- CI (`.github/workflows/validate.yml`) enforces validation + index
  freshness on every PR touching data/schema/tools.
- License zones: Apache-2.0 (code/schema), CC0-1.0 (registry records +
  generated aggregates), CC BY 4.0 (docs). Contributors warrant they may
  license what they submit; third-party material is referenced, not
  embedded (see README → Licensing).

## 7. Extension points

- **New distro family**: copy `tools/probe.d/arch.sh` → implement the
  family functions → register in `detect_family()` in `tools/probe.sh`.
- **New test**: add `tests/definitions/<id>.json` (semver'd) + a runner
  in `tests/runners/` emitting the evidence JSON contract
  (`tests/lib.py`).
- **New recipe lineage**: multi-parent `lineage.parents` with per-parent
  `contribution`.
- **New engine**: recipe schema `backend.engine` currently enumerates
  `llama.cpp`; extend deliberately.

## 8. Verification status on the dev box

Implemented end to end. Live verification on this CachyOS box (probe,
collect from llama-swap, real runs, submit) is the current step — see
`LEADERBOARD.md` for derived status once runs land. Harness-level MCP
round-trips via pi/omp are manual (`harness-tool-use` reports
`not_run` until configured with `HARNESS_CMD`).
