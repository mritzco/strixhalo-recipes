## Why

The current schemas (`schema/recipe.schema.json`,
`schema/result.schema.json`) were drafted before the v0.3 amendment and
bake the quant into the recipe identity — directly contradicting the
owner's requirement that recipes target a specific model, NOT a specific
quant. Every other tool (probe, collect, tests, submission, discovery,
admin) consumes this contract, so it must be frozen correctly first.
The committed example recipe also fails `validate.py --strict`, proving
the build was never validated end-to-end.

## What Changes

- **Recipe becomes model-scoped** (**BREAKING** `schema/*.json` and
  every consumer): identity and `content_hash` cover model + serving
  config, NOT quant. Quant becomes a dimension that can be tried/tested
  under a recipe (result records and tests state the quant they ran).
- **Parameters become annotated objects** (v0.3 §1): each parameter
  carries `value` + `annotations[]` (`type`: recommendation | warning |
  required | quality | performance | compatibility | evidence |
  experimental | deprecated) + optional `evidence` refs to tests/runs.
  Annotation scope ladder (global → model → variant → quant → runtime →
  recipe → parameter → test/run) recorded in docs.
- **Objectives / constraints / tradeoffs** (v0.3 §2): recipes declare
  `objectives` (primary/secondary/not_optimized), `constraints`, and
  explicit `tradeoffs`. No universal recipe score anywhere in the model.
- **Evidence model** (v0.3 §3–§6): semver'd **test definitions**;
  immutable **run/result records** carrying `observations[]`, optional
  `metrics{}` (may be `{}`), `artifacts[]`, and an outcome; canonical
  statuses `pass | fail | degraded | unsupported | not_run |
  inconclusive` (**BREAKING**: replaces the current
  pass/fail/error/skipped result statuses and realigns recipe-side
  author statuses). Distinguish declared rationale / observed evidence /
  validated knowledge / generated aggregate.
- **Trust rules preserved and enforced**: results append-only, keyed by
  reproducibility `content_hash`; cross-validation = ≥ 2 distinct
  `contributor_id`s; `validated` never hand-set.
- **Multi-parent lineage** kept, with per-parent `contribution` lines.
- `validate.py` recomputes content_hash over the new field set and
  enforces the new schemas; replace the fixture with examples that
  actually validate.
- `FORMAT.md` / `SPEC.md` / `AGENTS.md` rewritten to match the frozen
  model (docs follow schema).

## Capabilities

### New Capabilities

- `data-model`: recipe object contract — model-scoped granularity,
  annotated parameters, objectives/constraints/tradeoffs, multi-parent
  lineage, content-hash field set, author-side statuses.
- `evidence-records`: semver'd test definitions, run/result records,
  canonical statuses, append-only/keying rules, witness + derived-status
  rules.

### Modified Capabilities

None — greenfield capability set.

## Impact

`schema/recipe.schema.json`, `schema/result.schema.json`,
`tools/common.py` (hashed-field computation), `tools/validate.py`,
`tools/collect.py` (draft shape), `tools/submit_result.py` (record
shape), `FORMAT.md`, `SPEC.md`, `AGENTS.md`. This is Checkpoint 0 —
every later change (3–9) builds on `data-model` + `evidence-records`.

Open questions for the spec phase: exact content-hash field set once
quant is excluded; where quant is recorded (result field vs parameter
vs `model.variants`); whether `launch.command` remains the sole
reproducibility anchor given serving-topology settings (see ROADMAP
decisions 1–3).
