#!/usr/bin/env python3
"""
Admin verification tooling. Does NOT mutate recipe YAML — trust status is
derived, never hand-set (see FORMAT.md / AGENTS.md). It reports the
derived picture an admin acts on, and flags what is ready to auto-pull.

Subcommands:
  check      full validate + derived status summary (default)
  ready      list recipes meeting the auto-pull bar: >=2 distinct
             witnesses AND every declared test passing at least once
             AND capabilities_confirmed consistent with result evidence
  provenance report which recipes are auto-collected drafts with
             capabilities still unconfirmed (candidate for re-check)

Exit 0 when everything it was asked to verify holds; 1 otherwise.
"""
import sys
from collections import defaultdict

from common import iter_recipe_files, iter_result_files, load_yaml
import validate as validate_mod


def _derive():
    recipes = [load_yaml(p) for p in iter_recipe_files()]
    latest = {}
    for r in recipes:
        cur = latest.get(r["id"])
        if cur is None or tuple(map(int, r["version"].split("."))) > tuple(
                map(int, cur["version"].split("."))):
            latest[r["id"]] = r
    grouped = defaultdict(list)
    for p in iter_result_files():
        res = load_yaml(p)
        grouped[(res["recipe_id"], res["content_hash"])].append(res)

    rows = []
    for rid, r in sorted(latest.items()):
        results = grouped.get((rid, r["content_hash"]), [])
        witnesses = {x["contributor_id"] for x in results}
        passed = {t["id"] for x in results for t in x.get("tests", [])
                  if t["result"] == "pass"}
        declared = {t["id"] for t in r.get("tests", [])}
        rows.append({
            "id": rid, "version": r["version"], "status": r["status"],
            "quant": r.get("quant"), "witnesses": len(witnesses),
            "declared_tests": declared, "passed_tests": passed,
            "caps": r.get("harness_compat", {}).get("capabilities_confirmed", {}),
            "results": len(results),
            "auto_collected": any(
                a.get("type") == "experimental" and "Auto-collected" in (a.get("text") or "")
                for a in r.get("annotations", [])),
        })
    return rows


def check(rows):
    r_errs, _, recipes = validate_mod.validate_recipes(False)
    res_errs, _ = validate_mod.validate_results(False, recipes)
    td_defs, td_errors = validate_mod.load_test_definitions()
    errors = r_errs + res_errs + td_errors
    for e in errors:
        print(f"ERROR {e}")
    print(f"derive: {len(rows)} recipe(s), {sum(r['results'] for r in rows)} result(s)")
    if errors:
        return 1
    return 0


def ready(rows):
    ok = True
    for r in rows:
        ready_ok = (r["witnesses"] >= 2 and r["declared_tests"]
                    and r["declared_tests"] <= r["passed_tests"])
        mark = "READY" if ready_ok else ("pending" if r["witnesses"] else "no results")
        print(f"{mark:<8} {r['id']:<28} v{r['version']} witnesses={r['witnesses']}")
        if not ready_ok:
            ok = False
    return 0 if ok else 1


def provenance(rows):
    for r in rows:
        if r["auto_collected"]:
            unconfirmed = [k for k, v in r["caps"].items() if not v]
            print(f"DRAFT  {r['id']:<28} capabilities unconfirmed: "
                  f"{', '.join(unconfirmed) or 'none'}")
    return 0


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("cmd", nargs="?", default="check",
                    choices=["check", "ready", "provenance"])
    args = ap.parse_args()
    rows = _derive()
    fn = {"check": check, "ready": ready, "provenance": provenance}[args.cmd]
    sys.exit(fn(rows))


if __name__ == "__main__":
    main()
