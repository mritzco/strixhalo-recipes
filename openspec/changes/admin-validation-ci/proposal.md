## Why

The repo's trust model ("status is derived, never hand-set", "≥ 2
distinct contributors to cross-validate", "recipes must be machine-
generated and valid") currently has zero machine enforcement: there is
no CI, no admin path to validate incoming content, and no auto-pull
handling — so every claim depends on a human remembering the rules.

## What Changes

- **CI** (GitHub Actions, `.github/workflows/validate.yml`): on PRs
  touching `recipes/`, `results/`, `schema/`, `tests/`, or `tools/` run
  `validate.py --strict`; regenerate `index.json` and fail if the
  committed file is stale; regenerate `LEADERBOARD.md`. Only the new
  repo's real checks — the current workflow file is unverified.
- **Admin tooling**: verify machine-generated provenance (draft markers
  from `collect.py`, authorship, checklist completion), mechanically
  apply the witness rules before any promotion, approve/deprecate
  recipes, review batch submissions. One admin CLI or a small set of
  scripts under `tools/admin/`.
- **Auto-pull policy**: documented and scripted flow for
  validated-content PRs (merge gating on CI + admin approval), PR
  template, and the one-PR-per-experiment check from
  `submit-and-pr-flow`.
- `SKILL.md` gains the admin role section; `AGENTS.md` role table
  updated (validator/aggregator/admin duties).

## Capabilities

### New Capabilities

- `admin-validation`: CI enforcement, admin verification/promotion
  tooling, and the auto-pull policy.

### Modified Capabilities

- `evidence-records`: promotion and deprecation of recipe statuses are
  performed only through admin tooling bound to witness rules.
- `discovery`: generated outputs are CI-freshness-checked here.

## Impact

`.github/workflows/*`, new `tools/admin/*`, `SKILL.md`, `AGENTS.md`,
PR/merge documentation. Depends on the data model and tools from #2–#7;
lands when real recipes/results exist to enforce against.
