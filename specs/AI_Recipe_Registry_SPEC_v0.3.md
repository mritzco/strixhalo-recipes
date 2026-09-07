
# AI Recipe Registry — Specification v0.3 Amendment

**Status:** Design / pre-implementation  
**Purpose:** Explicitly define parameter rationale, structured annotations, multidimensional objectives, and non-numeric test evidence.

## 1. Parameter annotations and rationale

A recipe records not only *what* values were selected, but, where useful, *why*.

```yaml
parameters:
  ctx_size:
    value: 65536
    annotations:
      - type: recommendation
        text: "64K is the preferred operating point for this recipe."
      - type: warning
        text: "Higher context sizes caused quality degradation."
        evidence:
          - run: run-2026-00421

  cache_type_k:
    value: q8_0
    annotations:
      - type: quality
        text: "Selected to reduce KV-cache quality loss."
        evidence:
          - test: context.quality.v1
          - run: run-2026-00419

  mmproj:
    value: "mmproj-model-f16.gguf"
    annotations:
      - type: required
        text: "Required for vision workloads."
        evidence:
          - test: vision.basic.v1
```

Recommended annotation types:

```text
recommendation
warning
required
quality
performance
compatibility
evidence
experimental
deprecated
```

Annotations are structured data, not merely Markdown comments. Free-form prose MAY be included in `text`, but machine-readable consumers must be able to identify the annotation type and its scope.

### Annotation scope

```text
Global
  ↓
Model
  ↓
Model variant
  ↓
Quant
  ↓
Runtime
  ↓
Recipe
  ↓
Parameter
  ↓
Test / Run
```

General knowledge should live at the broadest appropriate scope. A machine-specific observation belongs to a run; a recipe-specific rationale belongs to the recipe or parameter.

This allows an agent to answer questions such as:

```text
Why does this recipe use Q8 K-cache?
→ Inspect the parameter annotation.
→ Follow its evidence references.
→ Inspect the relevant tests/runs.
```

## 2. Objectives, constraints, and tradeoffs

A recipe SHOULD declare what it is optimizing.

```yaml
objectives:
  primary:
    - quality
    - agent_capability
  secondary:
    - memory_efficiency
  not_optimized:
    - maximum_throughput

constraints:
  - vision_required
  - mcp_required
  - fits_in_available_memory

tradeoffs:
  - "Q8 K-cache uses more memory but preserves quality better at long context."
  - "This recipe sacrifices some throughput for better tool reliability."
```

A throughput-oriented recipe could instead say:

```yaml
objectives:
  primary:
    - throughput
  secondary:
    - memory_efficiency

constraints:
  - no_vision_required

tradeoffs:
  - "Lower-precision cache is acceptable for the short-context workload."
```

There is **no universal recipe score**. Faster is not necessarily better. A recipe can be faster while being worse at quality, vision, tool use, MCP, context reliability, or agent workloads.

Indexes SHOULD expose independent dimensions including:

- throughput
- latency
- memory efficiency
- quality preservation
- long-context behavior
- vision
- tool use
- MCP reliability
- agent-task success
- stability
- startup/load behavior

Any composite ranking MUST disclose its weighting and MUST NOT replace the underlying evidence.

## 3. Tests are evidence, not necessarily benchmarks

The canonical test model is:

```text
Test definition
    ↓
Execution
    ↓
Observations + optional metrics + artifacts
    ↓
Outcome
    ↓
Immutable run
```

Tests MAY measure throughput, latency, memory, startup time, context behavior, quality, vision, tool calls, MCP, agent-task completion, stability, reproducibility, MTP/speculative decoding, compatibility, or failure modes.

A valid test can have **no numeric metric at all**.

### Qualitative capability test

```yaml
test: vision.basic.v1

result:
  status: pass

metrics: {}

observations:
  - "Model correctly processed all supplied images."
  - "Vision requires the configured mmproj."
  - "No image-related crashes observed."

evidence:
  artifacts:
    - "artifacts/vision-basic-report.json"
```

### Quantitative performance test

```yaml
test: inference.throughput.v1

result:
  status: pass

metrics:
  tokens_per_second: 42.7
  prompt_tokens_per_second: 91.2
  peak_memory_gib: 73.4

observations:
  - "Stable across three repeated runs."
```

### Quality test

```yaml
test: context.quality.128k.v1

result:
  status: degraded

metrics:
  retrieval_accuracy: 0.81

observations:
  - "Retrieval remained functional but quality degraded."
  - "Q8 K-cache performed better than the lower-precision cache."

evidence:
  reference_run: run-2026-00419
```

### MCP/tool test

```yaml
test: mcp.basic.v1

result:
  status: pass

metrics:
  tool_calls_attempted: 10
  tool_calls_succeeded: 10
  tool_calls_failed: 0

observations:
  - "All required tool calls completed successfully."
  - "No malformed tool-call arguments observed."
```

## 4. Canonical result statuses

At minimum:

```text
pass
fail
degraded
unsupported
not_run
inconclusive
```

Definitions:

- `pass`: acceptance criteria met.
- `fail`: executed but acceptance criteria not met.
- `degraded`: works, but a material regression or tradeoff was observed.
- `unsupported`: the capability cannot be provided in this configuration.
- `not_run`: execution did not occur.
- `inconclusive`: execution occurred but evidence was insufficient to classify it.

The status never substitutes for the underlying evidence. Acceptance criteria belong to the versioned test definition.

## 5. JSON shape

The authoritative JSON Schema belongs under `schemas/`. This example makes the intended representation explicit:

```json
{
  "test": "context.quality.128k.v1",
  "result": {
    "status": "degraded"
  },
  "metrics": {
    "retrieval_accuracy": 0.81
  },
  "observations": [
    "Quality degraded at 128K with this cache configuration."
  ],
  "evidence": {
    "runs": [
      "run-2026-00419"
    ]
  }
}
```

`metrics` is optional and MAY be `{}`.

## 6. Evidence-backed knowledge model

The registry distinguishes:

1. **Declared rationale** — author's explanation.
2. **Observed evidence** — what a run/test actually demonstrated.
3. **Validated knowledge** — accepted evidence.
4. **Generated aggregate** — information computed from immutable records.

Example:

```yaml
parameters:
  cache_type_k:
    value: q8_0
    annotations:
      - type: quality
        text: "Selected to reduce KV-cache quality loss."
        evidence:
          - test: context.quality.v1
          - run: run-2026-00419
```

This makes the registry useful as an **agent-readable knowledge base**, rather than only a benchmark table.

## 7. Required implementation implications

The schemas and tooling should therefore:

- permit parameter-level annotations;
- permit annotations at broader reusable scopes;
- permit evidence references from annotations;
- make metrics optional;
- support observations and artifacts as first-class test evidence;
- support capability and qualitative tests;
- support multidimensional objectives and constraints;
- preserve tradeoffs rather than collapsing them into one score;
- generate leaderboard/index views from immutable runs;
- never require a throughput number for a valid test;
- preserve historical interpretation when test versions evolve.

These changes should be incorporated before freezing Checkpoint 0 (data model).
