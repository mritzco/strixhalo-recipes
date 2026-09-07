## Why

The public repo's entire value proposition is that a fresh agent can
clone it, install its skill, search, replicate, test, and submit —
without narration. The current `SKILL.md`/`AGENTS.md`/`SPEC.md`/
`FORMAT.md` predate the data-model rework and the final tool CLIs, and
no acceptance run has ever proved the loop works end to end.

## What Changes

- **Docs consolidated to the frozen model** (**BREAKING** doc content):
  `SPEC.md` and `FORMAT.md` rewritten against `data-model` +
  `evidence-records`; `SKILL.md` updated to final CLIs (probe v2,
  collect llama-swap mode, submit v2, search/leaderboard v2, admin
  tools); `AGENTS.md` refreshed; `README.md` quick-start final.
- **Skill packaging**: the repo is the skill — `SKILL.md` at repo root,
  installable by pi/omp/Claude skill paths; extension points documented
  (`tools/probe.d/<family>.sh` PR shape, adding a versioned test, admin
  role).
- **Fresh-agent acceptance** (original Checkpoint 5.5 equivalent): a
  clean agent session given only this repo + skill + a running
  llama-swap must: search → pick a recipe → replicate verbatim → run its
  tests → submit a result → report exact PR steps; for a new system it
  must produce a schema-valid draft, fill TODOs truthfully, and never
  fabricate capabilities. Encoded as a runnable acceptance checklist.

## Capabilities

### New Capabilities

- `agent-skill`: the packaged agent-facing skill contract — install
  path, role workflows, and the fresh-agent end-to-end acceptance.

### Modified Capabilities

- All capabilities from #2–#8 gain their final user-facing wording in
  this change's doc consolidation (spec deltas only where behavior
  wording changes).

## Impact

`SKILL.md`, `AGENTS.md`, `README.md`, `SPEC.md`, `FORMAT.md`,
acceptance checklist/script. Last in the queue: it documents the frozen
system (#2–#8) and must pass on this box with real llama-swap systems.
