## Why

The current index/search/leaderboard tools are v1-thin: substring model
filters and a single median tokens/sec. Agents and humans need
multidimensional discovery — "best recipe for qwen3.8-27b at Q8_0 with
vision + MCP and ≥ 2 witnesses" — and summaries that respect the data
model's "no universal score" rule instead of collapsing everything into
one ranking.

## What Changes

- **index v2** (**BREAKING** `index.json` shape + `build_index.py`):
  flat entries gain the quant dimension (now separate from recipe
  identity), objective tags, constraint flags, capability-confirmed per
  harness, distinct-witness counts, and lineage depth — cheap search
  still without loading full YAML bodies.
- **search.py v2**: filters for quant, objective/constraint, memory
  class, harness-confirmed capabilities, and min witnesses; failures
  included by default (`--exclude-failed` to hide).
- **Leaderboard v2 / summaries** (`leaderboard.py` +
  `LEADERBOARD.md`): per-dimension aggregates (throughput, latency,
  memory efficiency, quality, long-context, vision, tool use, MCP,
  agent-task success, stability) and per-capability views; derived
  cross-validation status (`≥ 2` distinct contributors) stays in
  generated output only; any composite ranking must disclose its
  weighting and never hide the underlying evidence.
- Regeneration is deterministic and CI-checked (diff gate lands with
  `admin-validation-ci`).

## Capabilities

### New Capabilities

- `discovery`: the search index contract and multidimensional
  summary/leaderboard views computed from immutable records.

### Modified Capabilities

- `evidence-records`: aggregation rules (what is derived, what never
  replaces underlying evidence) are enforced by this capability's
  generated outputs.
- `data-model`: quant-as-dimension is indexed here for search.

## Impact

`tools/build_index.py`, `tools/search.py`, `tools/leaderboard.py`,
`index.json`, `LEADERBOARD.md`, `SKILL.md` (summary/leaderboard usage),
`AGENTS.md`. Depends on the data model (#2) and real result records
(#6).
