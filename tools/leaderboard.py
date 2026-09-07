#!/usr/bin/env python3
"""
Leaderboard v3 — multidimensional views over immutable result records.

Outputs (default): writes LEADERBOARD.md with
  1. a ranking table (capability coverage + medians + witnesses + backend)
  2. per-model detail tables (every run, test-by-test)
  3. "what to run next" recommendations derived from gaps
and prints the ranking to stdout.

CLI queries print tables/stdout JSON without rewriting the file:
  python tools/leaderboard.py --sort tg
  python tools/leaderboard.py --cap vision --engine vulkan
  python tools/leaderboard.py --min-witnesses 2 --json

Trust rule (derived, never hand-set): cross-validated = >= MIN_WITNESSES
distinct contributor_ids at the current content_hash AND every declared
test passing at least once. No universal score — this table exposes
dimensions; ranking defaults to capability coverage, not raw speed.
"""
import argparse
import json
import statistics
from collections import defaultdict

from common import REPO_ROOT, iter_recipe_files, iter_result_files, load_yaml

MIN_WITNESSES = 2


def latest_by_id(recipes):
    latest = {}
    for r in recipes:
        cur = latest.get(r["id"])
        if cur is None or tuple(map(int, r["version"].split("."))) > tuple(
                map(int, cur["version"].split("."))):
            latest[r["id"]] = r
    return latest


def median(xs):
    return round(statistics.median(xs), 1) if xs else None


def collect():
    """Return (rows, per_model) — rows: one summary row per recipe id."""
    recipes = [load_yaml(p) for p in iter_recipe_files()]
    latest = latest_by_id(recipes)

    grouped = defaultdict(list)
    for p in iter_result_files():
        res = load_yaml(p)
        grouped[(res["recipe_id"], res["content_hash"])].append(res)

    rows, per_model = [], {}
    for rid in sorted(latest):
        r = latest[rid]
        results = grouped.get((rid, r["content_hash"]), [])
        witnesses = sorted({x["contributor_id"] for x in results})
        declared = {t["id"] for t in r.get("tests", [])}
        passed = {t["id"] for x in results for t in x.get("tests", [])
                  if t["result"] == "pass"}

        # per-test status tallies across results at this hash
        test_tally = defaultdict(lambda: defaultdict(int))
        tg, pp = [], []
        for res in results:
            rm = res.get("metrics") or {}
            if rm.get("tokens_per_sec_tg"):
                tg.append(rm["tokens_per_sec_tg"])
            if rm.get("tokens_per_sec_pp"):
                pp.append(rm["tokens_per_sec_pp"])
            for t in res.get("tests", []):
                tm = t.get("metrics") or {}
                if tm.get("tokens_per_sec_tg"):
                    tg.append(tm["tokens_per_sec_tg"])
                if tm.get("tokens_per_sec_pp"):
                    pp.append(tm["tokens_per_sec_pp"])
                test_tally[t["id"]][t["result"]] += 1

        caps = r.get("harness_compat", {}).get("capabilities_confirmed", {})
        cross = (len(witnesses) >= MIN_WITNESSES and declared
                 and declared <= passed)
        # backend class from run probes (nearest truth), fall back to recipe
        backends = set()
        for res in results:
            po = res.get("probe_output") or {}
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
            "model": r["model"]["name"],
            "arch": r["model"].get("arch") or "?",
            "size_gb": r["model"].get("size_gb"),
            "status": r["status"],
            "objectives": r.get("objectives", {}).get("primary", []),
            "quants": sorted({x.get("quant") for x in results if x.get("quant")}
                             or [r.get("quant")]),
            "tools": bool(caps.get("tools")), "mcp": bool(caps.get("mcp")),
            "vision": bool(caps.get("vision")),
            "vision_model": bool(r["model"].get("vision")),
            "tool_model": bool(r["model"].get("tool_calling")),
            "witnesses": len(witnesses),
            "witness_ids": witnesses,
            "pp": median(pp), "tg": median(tg),
            "results": len(results),
            "backend": "+".join(sorted(backends)),
            "cross_validated": cross,
            "tests": {tid: dict(tally) for tid, tally in sorted(test_tally.items())},
            "declared_tests": sorted(declared),
            "passed_tests": sorted(passed),
            "engine": r.get("backend", {}).get("engine"),
            "failed": r.get("status") == "failed",
        })
        per_model[rid] = {"recipe": r, "results": sorted(
            results, key=lambda x: x.get("run_id", ""))}
    return rows, per_model


def capability_score(row):
    return sum((row["tools"], row["mcp"], row["vision"]))


def fmt_tmv(row):
    return f"{'Y' if row['tools'] else '-'}{'Y' if row['mcp'] else '-'}{'Y' if row['vision'] else '-'}"


def status_mark(row):
    if row["cross_validated"]:
        return "✓ validated"
    if row["witnesses"] >= 1:
        return "1 witness"
    if row["status"] == "failed":
        return "failed"
    return "no results"


def recommendations(rows):
    """Derived 'what to run next' actions, ordered by leverage."""
    out = []
    for r in rows:
        if r["status"] == "failed":
            continue
        if r["witnesses"] == 0:
            out.append((3, f"{r['id']}: first witness — replicate and submit a result"))
        for cap_key, cap_name, model_flag, model_label in (
                ("tools", "tool calling", "tool_model", "model supports tools"),
                ("vision", "vision", "vision_model", "model is vision-capable"),
                ("mcp", "MCP", None, None)):
            if r[cap_key]:
                continue
            if model_flag and not r[model_flag]:
                continue
            out.append((2, f"{r['id']}: confirm {cap_name} with a real harness test"))
        missing = [t for t in r["declared_tests"] if t not in r["passed_tests"]]
        for t in missing:
            out.append((1, f"{r['id']}: declared test '{t}' has no passing run"))
        if r["witnesses"] == 1:
            out.append((0, f"{r['id']}: second INDEPENDENT witness (different person, not an alias)"))
    out.sort(key=lambda x: (-x[0], x[1]))
    return [a for _, a in out]


def render_md(rows, per_model):
    lines = ["# Leaderboard", "",
             "_Generated by tools/leaderboard.py — do not hand-edit. "
             "Cross-validation is DERIVED (≥ 2 distinct contributors at the "
             "current content_hash, every declared test passing). No "
             "universal score — capability coverage and medians are separate "
             "dimensions. Run `python tools/leaderboard.py --help` for "
             "sortable CLI queries._", ""]

    lines += ["## Ranking", "",
              "| model | quant(s) | size | T M V | PP t/s | TG t/s | witnesses | backend | verdict |",
              "|---|---|---|---|---|---|---|---|---|"]
    order = sorted(rows, key=lambda r: (-capability_score(r), -r["witnesses"],
                                        -(r["tg"] or 0)))
    for r in order:
        lines.append(
            f"| {r['id']} | {','.join(str(q) for q in r['quants'])} | "
            f"{r['size_gb']} | {fmt_tmv(r)} | {r['pp'] or '-'} | {r['tg'] or '-'} | "
            f"{r['witnesses']} | {r['backend']} | {status_mark(r)} |")

    lines += ["", "## What to run next", ""]
    recs = recommendations(order)
    if not recs:
        lines += ["_No open gaps — every recipe has witnesses and full "
                  "capability coverage._"]
    else:
        lines += [f"{i+1}. {a}" for i, a in enumerate(recs)]

    for rid in per_model:
        r = next(x for x in rows if x["id"] == rid)
        recipe = per_model[rid]["recipe"]
        results = per_model[rid]["results"]
        lines += ["", f"## {rid} (v{recipe['version']})", ""]
        lines.append(f"- Model: **{r['model']}** (`{recipe.get('quant') or '?'}` · "
                     f"{r['size_gb']} GB · arch {r['arch']})")
        if r["objectives"]:
            lines.append(f"- Objectives: {', '.join(r['objectives'])}")
        lines.append(f"- Backend: {r['backend']} ({r['engine']}) · "
                     f"confirmed capabilities: tools={r['tools']}, "
                     f"mcp={r['mcp']}, vision={r['vision']}")
        lines.append(f"- Verdict: {status_mark(r)} (witnesses: "
                     f"{', '.join(r['witness_ids']) or 'none'})")
        for tid, tally in r["tests"].items():
            parts = " ".join(f"{s}={n}" for s, n in sorted(tally.items()))
            lines.append(f"  - test `{tid}`: {parts}")
        if results:
            lines += ["", "| run (UTC) | contributor | quant | PP t/s | TG t/s | tests |",
                      "|---|---|---|---|---|---|"]
            for res in results:
                rid_ = res.get("run_id", "?")
                ts = res.get("run_id", "")[:13].replace("T", " ")
                m = res.get("metrics") or {}
                tgs = [str(t.get("metrics", {}).get("tokens_per_sec_tg"))
                       for t in res.get("tests", [])
                       if t.get("metrics", {}).get("tokens_per_sec_tg")]
                pps = [str(t.get("metrics", {}).get("tokens_per_sec_pp"))
                       for t in res.get("tests", [])
                       if t.get("metrics", {}).get("tokens_per_sec_pp")]
                tgv = tgs[0] if tgs else (str(m["tokens_per_sec_tg"]) if m.get("tokens_per_sec_tg") else "-")
                ppv = pps[0] if pps else (str(m["tokens_per_sec_pp"]) if m.get("tokens_per_sec_pp") else "-")
                tsum = ", ".join(f"{t['id']}={t['result']}" for t in res.get("tests", []))
                lines.append(f"| {ts} | {res.get('contributor_id')} | "
                             f"{res.get('quant') or '-'} | {ppv} | {tgv} | {tsum} |")
            notes = [res.get("notes") for res in results if res.get("notes")]
            if notes:
                lines += ["", "_Notes:_ " + " ".join(f"• {n}" for n in notes)]
    return "\n".join(lines) + "\n"


def render_table(rows):
    order = sorted(rows, key=lambda r: (-capability_score(r), -r["witnesses"],
                                        -(r["tg"] or 0)))
    print("{:<20} {:<8} {:>6} {:>5} {:>8} {:>8} {:>4} {:>8}  {}".format(
        "id", "quant", "size", "TMV", "PP", "TG", "wit", "backend", "model"))
    for r in order:
        print("{:<20} {:<8} {:>6} {:>5} {:>8} {:>8} {:>4} {:>8}  {}".format(
            r["id"][:20], ",".join(str(q) for q in r["quants"])[:8],
            r["size_gb"], fmt_tmv(r), r["pp"] or "-", r["tg"] or "-",
            r["witnesses"], r["backend"], r["model"][:32]))
    print("\nT=confirmed tools M=MCP V=vision. Ranked by capability "
          "coverage, then witnesses, then TG.")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sort", choices=["score", "tg", "pp", "witnesses",
                                       "name"], default="score")
    ap.add_argument("--reverse", action="store_true")
    ap.add_argument("--engine", choices=["vulkan", "rocm"],
                    help="filter rows by run-probe backend class")
    ap.add_argument("--cap", choices=["tools", "mcp", "vision"],
                    help="only rows where the capability is confirmed")
    ap.add_argument("--min-witnesses", type=int, default=0)
    ap.add_argument("--no-write", action="store_true",
                    help="do not rewrite LEADERBOARD.md")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    rows, per_model = collect()
    if args.engine:
        rows = [r for r in rows if args.engine in r["backend"]]
    if args.cap:
        rows = [r for r in rows if r[args.cap]]
    if args.min_witnesses:
        rows = [r for r in rows if r["witnesses"] >= args.min_witnesses]

    if args.json:
        out = [dict(r, witnesses=r.pop("witness_ids")) for r in rows]
        print(json.dumps(out, indent=2, default=str))
        return

    key = {"score": lambda r: (-capability_score(r), -r["witnesses"], -(r["tg"] or 0)),
           "tg": lambda r: -(r["tg"] or 0),
           "pp": lambda r: -(r["pp"] or 0),
           "witnesses": lambda r: -r["witnesses"],
           "name": lambda r: r["id"]}[args.sort]
    rows = sorted(rows, key=key, reverse=args.reverse)
    render_table(rows)

    if not args.no_write:
        # default sort for the file is always score; CLI sort is for stdout
        md_rows = sorted(collect()[0], key=lambda r: (-capability_score(r),
                                                      -r["witnesses"],
                                                      -(r["tg"] or 0)))
        md = render_md(md_rows, per_model)
        out_path = REPO_ROOT / "LEADERBOARD.md"
        with open(out_path, "w") as f:
            f.write(md)
        print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
