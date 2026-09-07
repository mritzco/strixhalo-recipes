#!/usr/bin/env python3
"""
Rebuild index.json — the flat, cheap search index. One row per recipe id
at its latest committed version, enriched with result-derived witness
counts. Paths are repo-RELATIVE (portable across clones).

Do not hand-edit index.json; regenerate with this tool (CI checks it).
"""
import json
import os
from collections import defaultdict

from common import INDEX_PATH, iter_recipe_files, iter_result_files, load_yaml


def latest_by_id(recipes):
    latest = {}
    for r in recipes:
        cur = latest.get(r["id"])
        if cur is None or tuple(map(int, r["version"].split("."))) > tuple(
                map(int, cur["version"].split("."))):
            latest[r["id"]] = r
    return latest


def main():
    recipes = [load_yaml(p) for p in iter_recipe_files()]
    latest = latest_by_id(recipes)

    # distinct contributors per (recipe_id, content_hash)
    witnesses = defaultdict(set)
    for p in iter_result_files():
        res = load_yaml(p)
        witnesses[(res["recipe_id"], res["content_hash"])].add(
            res["contributor_id"])

    entries = []
    for r in sorted(latest.values(), key=lambda x: x["id"]):
        caps = r.get("harness_compat", {}).get("capabilities_confirmed", {})
        entries.append({
            "id": r["id"],
            "version": r["version"],
            "content_hash": r["content_hash"],
            "status": r["status"],
            "quant": r.get("quant"),
            "model_name": r["model"]["name"],
            "arch": r["model"].get("arch"),
            "size_gb": r["model"].get("size_gb"),
            "vision": r["model"].get("vision"),
            "tool_calling": r["model"].get("tool_calling"),
            "objectives_primary": r.get("objectives", {}).get("primary", []),
            "hardware_target": r["hardware"].get("target"),
            "engine": r["backend"].get("engine"),
            "os_family": r["backend"].get("os_family"),
            "capabilities_confirmed": {
                "tools": caps.get("tools", False),
                "mcp": caps.get("mcp", False),
                "vision": caps.get("vision", False),
            },
            "distinct_witnesses": len(
                witnesses.get((r["id"], r["content_hash"]), set())),
            "path": os.path.relpath(
                os.path.join("recipes", r["id"], f"{r['id']}-v{r['version']}.yaml")),
        })

    with open(INDEX_PATH, "w") as f:
        json.dump(entries, f, indent=2)
        f.write("\n")
    print(f"Wrote {INDEX_PATH} with {len(entries)} recipe(s).")


if __name__ == "__main__":
    main()
