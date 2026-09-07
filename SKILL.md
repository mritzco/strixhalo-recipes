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
mcp, vision, context, throughput, stability, startup, quality, other.
If your change breaks an existing test's semantics, bump its version —
old results keep their meaning.

## Harness-level capability testing (pi / omp / oh-my-pi)

Server-level tool parsing is proven by `tool-roundtrip`; the full
harness<->model loop is `harness-tool-use` (needs
`--harness-cmd`/`$HARNESS_CMD`, else it honestly reports `not_run`).
Known reality on this box: Qwen coder/instruct are reliable agents;
GLM-4.5-Air breaks omp tool-calling (never returns — stream parse
failure) though it is fine in plain chat. A recipe that only proves chat
works is an incomplete recipe.

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
