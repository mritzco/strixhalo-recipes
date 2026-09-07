# Recipe, Test & Result Format

Canonical machine schemas: `schema/recipe.schema.json`,
`schema/result.schema.json`, `schema/test-definition.schema.json`.
This doc explains the *why* and the rules; the JSON Schemas are the
source of truth for validation.

## Two IDs, two purposes

- **`version`** (semver, e.g. `2.1.0`): human-facing evolution of the
  recipe doc. Bump PATCH for typo/docs, MINOR for tuning, MAJOR for a
  different model/back-end generation. Never trusted for reproducibility.
- **`content_hash`** (`sha256:`): the reproducibility key. Results attach
  to a content hash, not a version, so doc edits never orphan results.

### Quant-agnostic hashing (the core decision)

```yaml
model:   {name, arch, source}          # identity — NO quant, NO size
backend: {engine, commit, build_flags} # pin
launch:  {command}                     # normalized: --host/--port stripped,
                                       # quant literal -> {quant}
hardware:{target, gpu_mem_split_gb}
```

Everything else — `quant`, `size_gb`, kernel/vulkan versions,
annotations, objectives, docs — is informative and never changes the
hash. Consequence: a recipe applies to a **model**, and quants are a
dimension you try and test under it. Results and the leaderboard carry
which quant each run actually used. `validate.py` recomputes the hash
and rejects drift; you never hand-compute it.

## Parameter annotations and rationale (v0.3 §1)

A recipe records not just *what* values were selected but *why*:

```yaml
parameters:
  ctx_size:
    value: 131072
    annotations:
      - type: recommendation
        text: "Agents inject large system prompts + tool schemas; 32K overflowed omp into compaction loops."
        evidence:
          runs: ["run-2026-00421"]
  cache_type_k:
    value: q8_0
    annotations:
      - type: quality
        text: "Keeps KV quality at long context; uses more memory than q4_0."
  mmproj:
    value: mmproj-F16.gguf
    annotations:
      - type: required
        text: "Required for vision workloads."
```

Annotation types: `recommendation | warning | required | quality |
performance | compatibility | evidence | experimental | deprecated`.

**Scope ladder** — general knowledge belongs at the broadest scope that
is still true: global → model → variant → quant → runtime → recipe →
parameter → test/run. In this repo v1 the scopes are recipe-level
(`annotations`) and parameter-level (`parameters.<name>.annotations`);
model/global knowledge should be expressed as recipe annotations on a
canonical recipe (root lineage) and inherited via `lineage`.

## Objectives, constraints, tradeoffs (v0.3 §2)

```yaml
objectives:
  primary: [quality, agent_capability]
  secondary: [memory_efficiency]
  not_optimized: [maximum_throughput]
constraints: [vision_required, mcp_required, fits_in_available_memory]
tradeoffs:
  - "Q8 K-cache uses more memory but preserves quality better at long context."
```

There is **no universal recipe score**. Faster ≠ better. Indexes expose
independent dimensions; any composite ranking must disclose its
weighting and never hide underlying evidence.

## Canonical statuses

Recipe YAML (`status`): `experimental | failed | deprecated` — author
honest about intent. `failed` requires `failure_notes`.
`validated` is NOT a YAML status: cross-validation truth lives in
generated `LEADERBOARD.md`/`index.json`.

Test outcomes / results: `pass | fail | degraded | unsupported |
not_run | inconclusive`. A status never substitutes for evidence; a
`degraded` result carries the observation that explains the regression.
`error` conditions are recorded as `fail` or `inconclusive` with a
detail string. Metrics are optional — `metrics: {}` is valid; a
qualitative capability test may have zero numbers.

## Lineage

`lineage.parents` is a list (merges allowed). Each parent pins id +
version at merge time so history is walkable after parents move on:

```yaml
lineage:
  parents:
    - id: qwen3.8-27b
      version: 1.4.0
      contribution: "base quant + sampler settings"
    - id: glm-4.5-air-context
      version: 3.0.1
      contribution: "KV cache strategy for long context"
  rationale: "merged GLM's cache strategy onto the Qwen3.8 base"
```

Empty parents = true root recipe. A root recipe claiming to be a trivial
variant of an existing one is a review smell (validate warns on unknown
test ids only; lineage refs to non-existent ids are errors).

## Failed recipes

Same schema, same directory, with `status: failed` + `failure_notes`
(e.g. `"OOM at ctx>96k with --cache-type-k q8_0"`). Searchable by
default; `search.py --exclude-failed` hides them.

## Test definitions (semver'd evidence)

`tests/definitions/<id>.json` — `id`, `version`, `capability` (tools |
mcp | vision | context | throughput | stability | startup | quality |
other), `runner` (path), `endpoint_var`, `acceptance`. Recipes declare
`tests[]` by id; results record per-test evidence with the version that
ran. **Tests can break compatibility when improved → the version field
is how history stays interpretable.**

Runner contract (`tests/lib.py`): exactly one JSON document on stdout:

```json
{"status": "pass", "score": null, "metrics": {"tool_calls": 1},
 "observations": ["..."], "artifacts": [], "detail": null}
```

Endpoint contract: `--endpoint` or `$LLAMA_ENDPOINT`, default the
llama-swap endpoint `http://127.0.0.1:1234/v1`; model via `--model`.

## Result records

One JSON file per submission, `results/<id>/<hash-hex>/<run_id>.json`,
immutable. `run_id = <UTC-ISO8601>-<8hex>`. `submit_result.py` builds,
schema-validates, and writes records (never overwriting) and refuses
nonexistent recipes/hashes. A record contains: recipe refs + content
hash, contributor id, quant run, probe fingerprint (v2), per-test
evidence, optional run metrics, notes, tool version.

**Witness identity caveat:** `distinct contributor_id` counts are a
string-level proxy for independent witnesses. Aliases of one person —
e.g. a human's handle and their agent's handle — inflate the count
without adding independence. Reviewers should weigh identity before
treating "cross-validated" as proven by multiple people.

## Harness/capability fields are mandatory

`harness_compat.capabilities_confirmed` must state `tools`, `mcp`,
`vision` explicitly (booleans, all three keys). Missing is never
interpreted as false — it is stated. Values change to `true` ONLY after
a real runner/harness observation; `collect.py` drafts always leave
them false. Marking a capability true without testing is the cardinal
sin of this repo.

## Serving topology vs launch command

`launch.command` is the llama-server argv — the reproducibility anchor.
`launch.serving` records what fronts it (e.g. llama-swap on
`127.0.0.1:1234/v1`, `proxy: http://127.0.0.1:${PORT}` IPv4 rule, ttl)
as non-hashed knowledge; it is not part of identity.

## Custom backends: what llama is, which PRs

`backend.engine` is `llama.cpp | ollama | lemonade | other`. For custom
builds, provenance is mandatory knowledge:

```yaml
backend:
  engine: llama.cpp
  commit: 8f3c2d1            # the FORK's commit (hashed pin)
  upstream: https://github.com/<fork>/llama.cpp   # source the fork built from
  patches:
    - ref: "PR #1234"
      note: "PP 40% faster for MoE via ROCm scheduling"
    - ref: "0f1e2d3"
      note: "KV cache pooling fix"
  install_method: build-from-source   # or distro-package | manual-binary | appimage
  pkg_version: "0.4.0-1.1"            # distro packages only
```

Why: when the fork's PRs land upstream, agents diff `upstream`+`patches`
against the current upstream and **rebuild without the patches** —
dropping them is the expected recipe evolution (new version, new hash),
not a mystery. The hashed identity stays
`engine + commit + build_flags`, so two forks with the same commit
string are assumed equivalent; keep fork commit strings distinct.
`probe.sh` fills `install_method`/`pkg_version`/`binary` automatically;
`collect.py` drafts carry `upstream: null, patches: []` for you to fill
on custom builds.

## License & contribution warranty

Records under `recipes/`/`results/` and generated aggregates are CC0;
code/schemas Apache-2.0; docs CC BY 4.0. By contributing you warrant you
hold the rights. Third-party material (model outputs, benchmark prompts,
images, vendor metadata) is referenced from records, not embedded —
unless you own it or mark its own license.
