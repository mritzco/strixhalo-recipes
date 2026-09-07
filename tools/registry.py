#!/usr/bin/env python3
"""
registry — the data layer of the strixhalo-recipes mini-db.

Source of truth is always the git tree: recipes/*.yaml + results/*.json +
tests/definitions/*.json. From that, compute() derives three generated
stores (written by tools/build_index.py, never hand-edited):

  index.json           flat, sortable rows — one per model (latest version)
  runs.json            every result record, newest first (cross-model)
  models/<id>.json     per-model document: recipe + variants + run history

Store/query API for scripts and agents — no YAML parsing required:

    from registry import Store
    s = Store()                                   # loads the stores
    s.find(quant="Q8_0", backend="vulkan")        # rows: list[dict]
    s.find(tools=True, min_witnesses=2, sort="tg")
    s.model("qwen3-coder")                        # full model document
    s.runs(model="qwen3-coder", result="pass")    # run summaries
    s.next()                                      # personal gap list (yours)

All find filters are optional; unsupported combos are a no-op, not an
error. Direct text edits to recipes/results are discouraged — use the
tools (collect.py, submit_result.py) or these helpers.
"""
import json
import os
import re
import statistics
from collections import defaultdict
from datetime import datetime

from common import (REPO_ROOT, RECIPES_DIR, RESULTS_DIR,
                    iter_recipe_files, iter_result_files, load_yaml)

STORE_VERSION = 1
MIN_WITNESSES = 2
URL_RE = re.compile(r"https?://\S+")

# --------------------------------------------------------------------------
# compute (single source; used by build_index.py, leaderboard.py)
# --------------------------------------------------------------------------

def latest_by_id(recipes):
    latest = {}
    for r in recipes:
        cur = latest.get(r["id"])
        if cur is None or tuple(map(int, r["version"].split("."))) > tuple(
                map(int, cur["version"].split("."))):
            latest[r["id"]] = r
    return latest


def _median(xs):
    return round(statistics.median(xs), 1) if xs else None


def _metric_values(res, key):
    out = []
    rm = res.get("metrics") or {}
    if rm.get(key):
        out.append(rm[key])
    for t in res.get("tests", []):
        tm = t.get("metrics") or {}
        if tm.get(key):
            out.append(tm[key])
    return out


def _run_summary(res):
    tg = [v for v in _metric_values(res, "tokens_per_sec_tg")]
    pp = [v for v in _metric_values(res, "tokens_per_sec_pp")]
    return {
        "run_id": res.get("run_id", ""),
        "ts": res.get("run_id", "")[:13],
        "contributor_id": res.get("contributor_id"),
        "recipe_version": res.get("recipe_version"),
        "quant": res.get("quant"),
        "content_hash": res.get("content_hash"),
        "hash": (res.get("content_hash") or "")[7:13],
        "pp": _median(pp),
        "tg": _median(tg),
        "tests": [{"id": t.get("id"), "result": t.get("result"),
                   "score": t.get("score")}
                  for t in res.get("tests", [])],
        "notes": res.get("notes"),
    }


def compute():
    """Return (rows, models, runs): source-of-truth derived structures."""
    recipes = [load_yaml(p) for p in iter_recipe_files()]
    latest = latest_by_id(recipes)
    by_hash = defaultdict(list)
    for r in recipes:
        by_hash[(r["id"], r["content_hash"])].append(r)

    grouped = defaultdict(list)
    for p in iter_result_files():
        res = load_yaml(p)
        grouped[(res["recipe_id"], res["content_hash"])].append(res)
    for k in grouped:
        grouped[k].sort(key=lambda x: x.get("run_id", ""))

    rows, models, runs = [], {}, []
    for rid in sorted(latest):
        r = latest[rid]
        results = grouped.get((rid, r["content_hash"]), [])
        witnesses = sorted({x["contributor_id"] for x in results})
        all_runs = sorted((res for (_i, h), reslist in grouped.items()
                           for res in reslist if _i == rid),
                          key=lambda x: x.get("run_id", ""))
        rid_summaries = []
        for x in all_runs:
            s = _run_summary(x)
            s["model_id"] = rid
            rid_summaries.append(s)

        variant_hashes = {r["content_hash"]} | {
            h for (_i, h), reslist in grouped.items() if _i == rid and reslist}
        variants = []
        for h in sorted(variant_hashes):
            vres = grouped.get((rid, h), [])
            vrecs = sorted(by_hash.get((rid, h), []),
                           key=lambda x: tuple(map(int, x["version"].split("."))))
            vrec = vrecs[-1] if vrecs else None
            tally = defaultdict(lambda: defaultdict(int))
            for x in vres:
                for t in x.get("tests", []):
                    tally[t["id"]][t["result"]] += 1
            variants.append({
                "content_hash": h,
                "hash": h[7:13],
                "version": vrec["version"] if vrec else "?",
                "quant": (sorted({x.get("quant") for x in vres if x.get("quant")})
                          or ([vrec.get("quant")] if vrec else [])),
                "results": len(vres),
                "witnesses": len({x["contributor_id"] for x in vres}),
                "witness_ids": sorted({x["contributor_id"] for x in vres}),
                "pp": _median([v for x in vres for v in _metric_values(x, "tokens_per_sec_pp")]),
                "tg": _median([v for x in vres for v in _metric_values(x, "tokens_per_sec_tg")]),
                "tests": {tid: dict(t) for tid, t in sorted(tally.items())},
                "declared": sorted({t["id"] for t in (vrec or {}).get("tests", [])}),
            })
        variants.sort(key=lambda v: (v["results"] == 0, -v["results"]))

        passed = {t["id"] for x in results for t in x.get("tests", [])
                  if t["result"] == "pass"}
        declared = {t["id"] for t in r.get("tests", [])}
        cross = (len(witnesses) >= MIN_WITNESSES and declared
                 and declared <= passed)
        caps = r.get("harness_compat", {}).get("capabilities_confirmed", {})
        backends = set()
        for x in results:
            po = x.get("probe_output") or {}
            if po.get("rocm_version"):
                backends.add("rocm")
            elif (po.get("gpu") or {}).get("vulkan_version"):
                backends.add("vulkan")
        if not backends:
            b = r.get("backend", {})
            backends.add("rocm" if b.get("rocm_version") else
                         ("vulkan" if b.get("vulkan_version") else "?"))

        rows.append({
            "id": rid,
            "version": r["version"],
            "content_hash": r["content_hash"],
            "status": r["status"],
            "model_name": r["model"]["name"],
            "arch": r["model"].get("arch"),
            "source": r["model"].get("source"),
            "engine": r.get("backend", {}).get("engine"),
            "backend": "+".join(sorted(backends)),
            "os_family": r.get("backend", {}).get("os_family"),
            "hardware_target": r.get("hardware", {}).get("target"),
            "size_gb": r["model"].get("size_gb"),
            "quant": r.get("quant"),
            "quants": sorted({q for v in variants for q in v["quant"]}),
            "vision": bool(r["model"].get("vision")),
            "tool_calling": bool(r["model"].get("tool_calling")),
            "tool_model": bool(r["model"].get("tool_calling")),
            "vision_model": bool(r["model"].get("vision")),
            "objectives_primary": r.get("objectives", {}).get("primary", []),
            "capabilities_confirmed": {
                "tools": bool(caps.get("tools")),
                "mcp": bool(caps.get("mcp")),
                "vision": bool(caps.get("vision")),
            },
            "witnesses": len(witnesses),
            "distinct_witnesses": len(witnesses),
            "pp": _median([v for x in results for v in _metric_values(x, "tokens_per_sec_pp")]),
            "tg": _median([v for x in results for v in _metric_values(x, "tokens_per_sec_tg")]),
            "results": len(results),
            "n_variants": len(variants),
            "last_run": max((x.get("run_id", "") for x in all_runs), default=""),
            "cross_validated": cross,
            "path": f"recipes/{rid}/{rid}-v{r['version']}.yaml",
        })
        models[rid] = {
            "id": rid,
            "recipe": r,
            "variants": variants,
            "runs": rid_summaries,
            "counts": {"results": len(all_runs), "witnesses": len(witnesses),
                       "cross_validated": cross},
        }
    runs = [s for m in models.values() for s in m["runs"]]
    runs.sort(key=lambda x: x.get("run_id", ""), reverse=True)
    return rows, models, runs


def write_stores(rows=None, models=None, runs=None):
    """Regenerate index.json, runs.json, models/<id>.json."""
    if rows is None:
        rows, models, runs = compute()
    with open(REPO_ROOT / "index.json", "w") as f:
        json.dump({"store_version": STORE_VERSION, "models": rows},
                  f, indent=2, default=str)
        f.write("\n")
    with open(REPO_ROOT / "runs.json", "w") as f:
        json.dump({"store_version": STORE_VERSION, "runs": runs},
                  f, indent=2, default=str)
        f.write("\n")
    outdir = REPO_ROOT / "models"
    os.makedirs(outdir, exist_ok=True)
    for rid, doc in models.items():
        with open(outdir / f"{rid}.json", "w") as f:
            json.dump({"store_version": STORE_VERSION, "model": doc},
                      f, indent=2, default=str)
            f.write("\n")
    return len(rows), len(runs), len(models)


# --------------------------------------------------------------------------
# Store — query facade over the generated JSON stores
# --------------------------------------------------------------------------

class Store:
    def __init__(self, root=REPO_ROOT):
        self.root = root
        with open(root / "index.json") as f:
            self.index = json.load(f)
        with open(root / "runs.json") as f:
            self.runs_doc = json.load(f)
        self._model_cache = {}

    # -- rows ------------------------------------------------------------
    def find(self, model=None, quant=None, backend=None, engine=None,
             tools=None, mcp=None, vision=None, min_witnesses=0,
             status=None, sort="score", reverse=False, limit=None):
        """Filter index rows. All filters optional."""
        out = []
        for e in self.index.get("models", []):
            if model and model.lower() not in (
                    (e.get("model_name") or "") + " " + e.get("id", "")).lower():
                continue
            if quant and quant.lower() not in (
                    ",".join(str(q) for q in e.get("quants") or [])
                    + " " + str(e.get("quant") or "")).lower():
                continue
            if backend and backend not in (e.get("backend") or ""):
                continue
            if engine and engine.lower() != (e.get("engine") or "").lower():
                continue
            caps = e.get("capabilities_confirmed") or {}
            if tools and not caps.get("tools"):
                continue
            if mcp and not caps.get("mcp"):
                continue
            if vision and not caps.get("vision"):
                continue
            if (e.get("witnesses") or 0) < min_witnesses:
                continue
            if status and e.get("status") != status:
                continue
            out.append(e)
        key = {
            "score": lambda x: (-(bool((x.get("capabilities_confirmed") or {}).get("tools"))
                                  + bool((x.get("capabilities_confirmed") or {}).get("mcp"))
                                  + bool((x.get("capabilities_confirmed") or {}).get("vision"))),
                                -(x.get("witnesses") or 0), -(x.get("tg") or 0)),
            "tg": lambda x: -(x.get("tg") or 0),
            "pp": lambda x: -(x.get("pp") or 0),
            "witnesses": lambda x: -(x.get("witnesses") or 0),
            "name": lambda x: x.get("id", ""),
        }.get(sort, lambda x: 0)
        out.sort(key=key, reverse=reverse)
        return out[:limit] if limit else out

    def model(self, rid):
        """Full model document (recipe + variants + runs)."""
        if rid not in self._model_cache:
            with open(self.root / "models" / f"{rid}.json") as f:
                self._model_cache[rid] = json.load(f)["model"]
        return self._model_cache[rid]

    def runs(self, model=None, test=None, result=None, limit=None):
        """Run summaries, newest first."""
        out = []
        for r in self.runs_doc.get("runs", []):
            if model and r.get("model_id", "") != model:
                continue
            if test is not None or result is not None:
                hit = False
                for t in r.get("tests", []):
                    if test is not None and t.get("id") != test:
                        continue
                    if result is not None and t.get("result") != result:
                        continue
                    hit = True
                    break
                if not hit:
                    continue
            out.append(r)
        return out[:limit] if limit else out

    def next(self):
        """Personal 'what to run next' gaps (stdout guidance, never stored)."""
        rows = self.index.get("models", [])
        recs = []
        for r in rows:
            if r.get("status") == "failed":
                continue
            rid = r["id"]
            if (r.get("witnesses") or 0) == 0:
                recs.append((3, f"{rid}: first witness — replicate and submit a result"))
            caps = r.get("capabilities_confirmed") or {}
            if not caps.get("tools") and r.get("tool_model"):
                recs.append((2, f"{rid}: confirm tool calling"))
            if not caps.get("mcp") and r.get("tool_model"):
                recs.append((1, f"{rid}: confirm MCP through a harness (pi/omp)"))
            if not caps.get("vision") and r.get("vision_model"):
                recs.append((1, f"{rid}: confirm vision with an mmproj test"))
            if (r.get("witnesses") or 0) == 1:
                recs.append((0, f"{rid}: second INDEPENDENT witness "
                                "(different person, not an alias)"))
        recs.sort(key=lambda x: (-x[0], x[1]))
        return [a for _, a in recs]


if __name__ == "__main__":
    import sys
    rows, models, runs = compute()
    print(f"computed: {len(rows)} model rows, {len(runs)} runs, "
          f"{len(models)} model docs")
    if "--write" in sys.argv:
        n, nr, nm = write_stores(rows, models, runs)
        print(f"wrote index.json + runs.json + {nm} models/*.json")
