#!/usr/bin/env bash
# Install the registry's git hooks (core.hooksPath = .githooks).
# After this, every commit runs validate --strict and fails if the
# generated stores/board (index.json, runs.json, models/, LEADERBOARD.md)
# are stale relative to the staged tree.
set -euo pipefail
cd "$(dirname "$0")/.."
chmod +x .githooks/pre-commit
git config core.hooksPath .githooks
echo "hooks installed (core.hooksPath -> .githooks)"
