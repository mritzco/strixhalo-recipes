## Why

The tests directory contains stubs that always exit 0 and print canned
scores — zero evidential value, violating the project's core premise
that capability claims are proven by runs through real harnesses. The
owner is explicit: chat-only proves ~5% of a model's capability; tool
use, MCP, and vision (mmproj) through pi and omp are the other 95%, and
they must be tested, not assumed.

## What Changes

- **Replace stubs with real, versioned tests** (**BREAKING** `tests/*`):
  each test = a semver'd definition with acceptance criteria and a
  runner that emits machine-readable evidence JSON (observations,
  optional metrics, artifacts, outcome per the evidence model from
  `checkpoint-0-data-model`).
- **Endpoint contract**: `LLAMA_ENDPOINT` env or `--endpoint`
  (llama-swap `http://127.0.0.1:1234/v1` default on this box), model id
  via `--model`.
- **Test classes**:
  - Tool-call roundtrip against the OpenAI-compatible `/v1` API
    (structured `tool_calls` parse + valid arguments — `--jinja`
    dependency encoded as a `required` parameter annotation).
  - MCP round-trip through real harnesses: pi and omp/oh-my-pi.
  - Vision via mmproj: image input → correct answer; unsupported when no
    mmproj is configured.
  - Long-context recall (needle-in-haystack at declared ctx).
  - Throughput / startup-load / stability (via API timing and
    `llama-bench`; memory observation via `amdgpu_top`/sysfs).
  - Capability-negative tests: e.g. GLM-4.5-Air + omp tools must report
    `unsupported`/`fail` — the known stream-parse breakage is evidence,
    not a bug report.
- Non-interactive gotchas encoded (no TTY; server API, not `llama-cli`
  REPL).
- Recipe `tests[]` entries reference versioned test ids; result records
  attach the emitted evidence.

## Capabilities

### New Capabilities

- `harness-testing`: versioned capability tests (tool / MCP / vision /
  context / throughput / stability), evidence emission, endpoint and
  harness contracts.

### Modified Capabilities

- `evidence-records`: test-definition records now include the concrete
  runner/emission contract consumed by this capability.
- `data-model`: recipe `tests[]` and `harness_compat` requirements
  aligned with versioned test ids.

## Impact

`tests/*` (stubs removed), new tests registry layout + runners,
recipe `tests[]`/`harness_compat` fields, `SKILL.md`, and the evidence
consumed by `submit-and-pr-flow`. Depends on the data model (#2).
