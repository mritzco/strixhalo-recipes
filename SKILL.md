---
name: strixhalo-recipes
description: Use when the user wants to run, replicate, benchmark, or contribute a local-LLM serving setup (llama.cpp via llama-swap/llama-server on unified-memory Linux hardware like Strix Halo). Covers finding an existing tested recipe, replicating it, running its tests, submitting evidence results, and adding new recipes with proper lineage and annotations.
---

# strixhalo-recipes

A git repo of reproducible local-LLM serving recipes with lineage,
annotated parameter rationale, and multi-witness trust. Full spec:
`SPEC.md`; field-by-field format: `FORMAT.md`; orientation for agents:
`AGENTS.md`. **Read those three before doing anything that writes data.**

Registry records are CC0, code Apache-2.0, docs CC BY 4.0 (README →
Licensing). Never embed third-party material (model outputs, benchmark
prompts, images) in records you do not own — reference it instead.

## Fast path: analyze (capture or test in one command)

`python tools/analyze.py` is the daily driver — three verbs:

- `analyze machine` — probe this machine and PROVE the probe JSON
  validates against the result schema (other-OS agents: this is your
  contract check; add `tools/probe.d/<family>.sh` from `arch.sh` if it
  fails).
- `analyze cmd "<launch command>" [--write]` — capture an EXISTING
  setup (running server, llama-swap entry, or a pasted command line):
  parses flags, reads the model, drafts a schema-valid recipe with a
  correct content_hash, prints the share block (id + hash + the command
  others run to test it). This is the reddit-poster path: run it, share
  the id.
- `analyze test --recipe <id> [--endpoint URL] [--submit --contributor you]`
  — replicate someone else's recipe: runs the quick battery
  (tool-roundtrip, throughput @8k PP, context-recall @4k) against your
  server and, with `--submit`, writes an immutable result record. This
  is the "let me verify what they claimed" path — compatible → run;
  incompatible → collect a variant with lineage.

Same hard rules apply: capabilities stay false until a test passes,
records are append-only, one experiment = one PR.

## When the user wants to run a model

1. If `index.json` is missing/stale: `python tools/build_index.py`.
2. Search the flat index:
   `python tools/search.py --model <name> [--quant Q8_0] [--tool-calling] [--vision] --min-witnesses 2`
   Filters: `--model --arch --quant --hardware --status --objective
   --tool-calling --vision --mcp --min-witnesses --exclude-failed
   --only-failed`. Failures are shown by default (they are data).
3. Prefer recipes with `distinct_witnesses >= 2`; if only 0-1 witness
   options exist, say so explicitly before running.
4. Reproduce **exactly**: use the recipe's pinned `backend.commit`,
   `launch.command` verbatim (fill `${PORT}` if served through
   llama-swap), don't "improve" flags on the fly. A variant is a *new*
   recipe with lineage back to this one.
5. Fingerprint the machine: `bash tools/probe.sh > /tmp/probe.json`.
6. Run the recipe's tests (each `tests[]` id maps to
   `tests/definitions/<id>.json` + `tests/runners/<id>.py`):
   `python tests/runners/<id>.py --endpoint <url>/v1 --model <alias> > /tmp/<id>.json`
   Default endpoint: llama-swap `http://127.0.0.1:1234/v1`.
7. Submit: `python tools/submit_result.py --recipe <id> --contributor
   <stable-handle> --evidence <test-id>=/tmp/<id>.json ... --notes "..."`
   Then give the user the exact git add/commit/PR steps — do not push
   without confirmation.

## When the user wants to try a new model / flag combo / llama-swap system
1. Search first — don't duplicate an existing recipe.
2. **Generate drafts with `collect.py`, never hand-write YAML.** For the
   llama-swap systems on this machine (one draft each):
   `python tools/collect.py --from-llama-swap --author <you> --dry-run`
   then drop `--dry-run` to write. A single setup:
   `python tools/collect.py --launch-cmd "<cmd>" --model-name <slug>`
   or `--pid <pid>`. It inspects the real process/GGUF/HF cache and
   probe output to fill model/backend/hardware fields and computes the
   content_hash correctly (quant-agnostic) by construction.
3. Drafts are schema-valid but INCOMPLETE on purpose. The printed
   checklist is the work: annotate parameters with the WHY
   (recommendation/warning/required/…), fill objectives
   (primary/secondary/not_optimized), constraints, tradeoffs; set
   lineage parents (1..n, one-line contribution each); sha256sum the
   GGUF if you want file pinning. NEVER auto-true capabilities.
4. `status: experimental` always for new recipes (collect's default —
   don't change it). Cross-validated status is earned via witnesses.
5. If it failed: still commit it, `status: failed` + `failure_notes`
   with the actual error/OOM. As valuable as a success.
6. Run `python tools/validate.py --strict` before proposing the PR; fix
   every ERROR (warnings worth mentioning).

## When the user wants to know what is actually good right now

`python tools/leaderboard.py` → read `LEADERBOARD.md`. That generated
file is the ONLY place to trust cross-validated status (≥ 2 distinct
contributors at the same content hash AND every declared test passing).
A recipe YAML `status: validated` should never exist — treat one with
suspicion. Admin view: `python tools/admin.py ready` (auto-pull bar),
`python tools/admin.py provenance` (drafts with unconfirmed caps).

## Writing or improving a test

Tests are versioned evidence (semver), not benchmarks with required
numbers. Add `tests/definitions/<id>.json` + a runner under
`tests/runners/` that prints the evidence JSON contract (see
`tests/lib.py` — one JSON doc on stdout). Capability classes: tools,
mcp, vision, context, throughput, stability, startup, quality,
agent-task, other. If your change breaks an existing test's semantics,
bump its version — old results keep their meaning.

**Agents running experiments MUST also propose tests when the battery
misses the workload.** If your experiment measures something the existing
tests don't cover (large-context agent loops, coding with local files,
a harness quirk), submit a test proposal in the same PR:

1. `tests/definitions/<your-id>.json` — semver `1.0.0`, capability
   class, runner path, acceptance criteria (what maps to pass/fail).
2. Runner in `tests/runners/` emitting the evidence contract. Prefer a
   GROUND-TRUTH check (a file printed the right value, a command exited
   correctly) over the model's self-report.
3. Run it once yourself and attach the evidence to your result.
Admins review the proposal when merging (schema validation is
automatic via `validate.py`; CI runs it on every PR). A test nobody
proposed is how phantom wins like short-prompt PP sneak through.

## Harness-level capability testing (pi / omp / oh-my-pi)

Server-level tool parsing is proven by `tool-roundtrip`; the full
harness<->model loop is `harness-tool-use` (needs
`--harness-cmd`/`$HARNESS_CMD`, else it honestly reports `not_run`).
Pi is installed on the reference box (`pi`, config models.json → the
llama-swap `local` provider); one-shot harness runs look like:
`HARNESS_CMD='pi -p' python tests/runners/harness_tool_use.py --model qwen3-coder`
with llama-swap up on 127.0.0.1:1234. Same contract works for omp
wrappers. MCP-via-harness is the same path with an MCP-bearing prompt —
no runner change needed, just the definition (propose one).
Known reality on this box: Qwen coder/instruct are reliable agents;
GLM-4.5-Air breaks omp tool-calling (never returns — stream parse
failure) though it is fine in plain chat. A recipe that only proves chat
works is an incomplete recipe.

## Reading the results board

`python tools/leaderboard.py` rewrites `LEADERBOARD.md` (landing:
Models by latest activity — not a ranking — plus Latest tests) and
`models/<id>.md` per-model pages (variants, runs, sources). The
machine-readable layer lives in `index.json` (flat rows), `runs.json`
(all runs) and `models/<id>.json` (per-model documents) — generated by
`tools/build_index.py`, never hand-edited. Query them without parsing
YAML:

```python
from tools.registry import Store    # from the repo root (deps: PyYAML+jsonschema)
s = Store()
s.find(quant="Q8_0", backend="vulkan", tools=True, min_witnesses=1)
s.find(sort="tg", limit=5)                     # top generation speed
s.model("qwen3-coder")["variants"]             # per-configuration data
s.runs(model="qwen3-coder", result="pass")     # evidence records
s.next()                                       # your personal gaps
```

CLI one-liners keep working: `--sort tg|pp|witnesses|name --reverse
--engine vulkan|rocm --cap tools|mcp|vision --min-witnesses N --json`
and `--next` (personal, never committed).

**Write through tools, not text edits.** Recipes are created by
`tools/collect.py` (drafts), records by `tools/submit_result.py`
(addRun), test definitions by PR. The validate hook enforces this:
`bash tools/install-hooks.sh` — afterwards every commit runs
`validate.py --strict` and fails if `index.json` / `runs.json` /
`models/` / `LEADERBOARD.md` are stale (same gate CI enforces).

## Adding support for a distro this repo doesn't cover

`tools/probe.d/<family>.sh` is the extension point (see SPEC.md §7).
Copy `tools/probe.d/arch.sh`, adapt the family functions, register the
family in `detect_family()` in `tools/probe.sh`, open a PR. Unverified
modules must NOT claim support — ship only what a real box proved.

## Hard rules (don't skip these even under time pressure)

- Never hand-set `content_hash` — let `validate.py` tell you the correct
  value; quant/size/docs do NOT change it.
- Never edit a file under `results/` — append-only; correct by
  submitting a new run and explaining in `notes`.
- Never write `status: validated` into a recipe YAML.
- `capabilities_confirmed` reflects what you actually tested through a
  harness — never copy it from a similar recipe.
- One experiment = one PR. Failures are committed as data.
- Custom backends: record `backend.upstream` (fork source) + `backend.patches`
  (PRs/patch ids with notes) + `backend.commit` = the fork's commit.
  Agents rebuild without the patches once they land upstream.
- Respect license zones and the contribution warranty (third-party
  material: reference, don't embed).
