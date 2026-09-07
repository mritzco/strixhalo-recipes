## Why

`submit_result.py` assembles record JSON but nothing enforces the
"one PR per experiment" workflow or attaches the evidence that makes a
result trustworthy. Results must be attributable, immutable, and
reviewable — by humans and by the admin tooling that comes later.

## What Changes

- **submit_result v2** (**BREAKING** CLI + record shape): attach probe
  v2 output, per-test evidence artifacts (paths/refs to the JSON emitted
  by `harness-testing` runners), observations, and `tool_version`;
  re-validate recipe existence + content_hash against the frozen data
  model before writing; refuse to write into an existing run path
  (append-only enforced at write time, not just by convention).
- **Contributor identity**: stable pseudonymous id (self-chosen handle +
  salt, hashed) — documented, never PII.
- **PR workflow contract**: one experiment = one branch + commit + PR.
  Branch naming `recipes/<model>/<slug>`; commit message convention;
  PR body template covering goals, features, results, failure notes, and
  checklist status. Never push without user confirmation; never edit
  files under `results/`.
- **Batch submissions**: support submitting multiple results from one
  batch collect run (llama-swap enumeration) as a single PR.
- `SKILL.md` / `AGENTS.md` updated with the exact flow + template.

## Capabilities

### New Capabilities

- `result-submission`: creation of immutable result records and the
  one-PR-per-experiment submission conventions.

### Modified Capabilities

- `evidence-records`: run/result creation is now performed only through
  this capability's tooling.
- `machine-probe`: probe v2 output is embedded in every submitted
  record.

## Impact

`tools/submit_result.py`, `tools/common.py`, result record layout under
`results/`, `SKILL.md`, `AGENTS.md`. Depends on probe v2 (#3) and real
harness tests (#5).
