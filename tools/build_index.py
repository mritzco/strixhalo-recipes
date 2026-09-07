#!/usr/bin/env python3
"""
Rebuild the generated JSON stores from source of truth (recipes/*.yaml +
results/*.json): index.json (flat rows), runs.json (all runs, newest
first), models/<id>.json (per-model documents). Do NOT hand-edit these —
regenerate with this tool (CI + the pre-commit hook check freshness).

Query them with tools/registry.py (Store class) or this repo's tools:
  python tools/search.py ...        # human/agent search over index.json
  python tools/leaderboard.py ...   # markdown board from the same stores
"""
import sys

import registry

sys.path.insert(0, __file__.rsplit("/", 1)[0])


def main():
    rows, models, runs = registry.compute()
    n_r, n_u, n_m = registry.write_stores(rows, models, runs)
    print(f"Wrote index.json ({n_r} model rows), runs.json ({n_u} runs), "
          f"{n_m} models/*.json")


if __name__ == "__main__":
    main()
