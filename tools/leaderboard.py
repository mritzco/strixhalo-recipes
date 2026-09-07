#!/usr/bin/env python3
"""
Results board generator (v4).

PUBLIC, generated, committed:
  LEADERBOARD.md     landing: what-this-is, Models table (latest activity
                     first — NOT a quality ranking), Latest tests, links to
                     per-model pages
  models/<id>.md     per-model page: metadata, Variants (configurations
                     tested, grouped by content_hash + quant), run history,
                     sources/notes, lineage

PERSONAL, stdout only (never written to the repo):
  --next             derived 'what to run next' gaps for YOUR machine

Queries (stdout, no file writes): --sort tg|pp|witnesses|name --reverse
--engine vulkan|rocm --cap tools|mcp|vision --min-witnesses N --json

Trust rule (derived, never hand-set): cross-validated = >= MIN_WITNESSES
distinct contributor_ids at a content_hash AND every test declared by the
recipe at that hash passing at least once. Contributor ids are a proxy for
independent witnesses — same-owner aliases do not add independence.
"""
import argparse
import json
import os
import re
import statistics
from collections import defaultdict
from datetime import datetime

from common import REPO_ROOT, iter_recipe_files, iter_result_files, load_yaml

MIN_WITNESSES = 2
URL_RE = re.compile(r"https?://\S+")


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


def _extract(metrics_key, res):
    out = []
    rm = res.get("metrics") or {}
    if rm.get(metrics_key):
        out.append(rm[metrics_key])
    for t in res.get("tests", []):
        tm = t.get("metrics") or {}
        if tm.get(metrics_key):
            out.append(tm[metrics_key])
    return out


def collect():
    recipes = [load_yaml(p) for p in iter_recipe_files()]
    latest = latest_by_id(recipes)
    by_hash = defaultdict(list)  # (id, hash) -> recipe versions (newest first)
    for r in recipes:
        by_hash[(r["id"], r["content_hash"])].append(r)

    grouped = defaultdict(list)  # (id, hash) -> results sorted by run_id
    for p in iter_result_files():
        res = load_yaml(p)
        grouped[(res["recipe_id"], res["content_hash"])].append(res)
    for k in grouped:
        grouped[k].sort(key=lambda x: x.get("run_id", ""))

    rows, models = [], {}
    for rid in sorted(latest):
        r = latest[rid]
        results = grouped.get((rid, r["content_hash"]), [])
        witnesses = sorted({x["contributor_id"] for x in results})

        # variants: distinct content hashes that have results (plus current)
        variant_hashes = {r["content_hash"]} | {
            h for (_i, h), res in grouped.items() if _i == rid and res}
        variants = []
        for h in sorted(variant_hashes):
            vres = grouped.get((rid, h), [])
            vrecs = sorted(by_hash.get((rid, h), []),
                           key=lambda x: tuple(map(int, x["version"].split("."))))
            vrec = vrecs[-1] if vrecs else None
            vw = sorted({x["contributor_id"] for x in vres})
            tg = [v for x in vres for v in _extract("tokens_per_sec_tg", x)]
            pp = [v for x in vres for v in _extract("tokens_per_sec_pp", x)]
            tally = defaultdict(lambda: defaultdict(int))
            for x in vres:
                for t in x.get("tests", []):
                    tally[t["id"]][t["result"]] += 1
            variants.append({
                "hash": h, "short": h[7:13],
                "quant": (sorted({x.get("quant") for x in vres if x.get("quant")})
                          or ([vrec.get("quant")] if vrec else [])),
                "version": vrec["version"] if vrec else "?",
                "results": len(vres),
                "witnesses": len(vw),
                "pp": median(pp), "tg": median(tg),
                "tests": {tid: dict(t) for tid, t in sorted(tally.items())},
                "declared": sorted({t["id"] for t in (vrec or {}).get("tests", [])}),
                "notes": [x.get("notes") for x in vres if x.get("notes")],
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

        last_run = max((x.get("run_id", "") for x in results), default="")
        rows.append({
            "id": rid, "version": r["version"], "model": r["model"]["name"],
            "arch": r["model"].get("arch") or "?", "size_gb": r["model"].get("size_gb"),
            "status": r["status"],
            "objectives": r.get("objectives", {}).get("primary", []),
            "source": r["model"].get("source"),
            "tools": bool(caps.get("tools")), "mcp": bool(caps.get("mcp")),
            "vision": bool(caps.get("vision")),
            "tool_model": bool(r["model"].get("tool_calling")),
            "vision_model": bool(r["model"].get("vision")),
            "witnesses": len(witnesses), "pp": median(
                [v for x in results for v in _extract("tokens_per_sec_pp", x)]),
            "tg": median([v for x in results for v in _extract("tokens_per_sec_tg", x)]),
            "results": len(results), "backend": "+".join(sorted(backends)),
            "cross_validated": cross, "last_run": last_run,
            "n_variants": len(variants),
            "quants": sorted({q for v in variants for q in v["quant"]}),
        })
        models[rid] = {"recipe": r, "variants": variants,
                       "results": results,
                       "all_runs": sorted(
                           (res for (_i, h), reslist in grouped.items()
                            for res in reslist if _i == rid),
                           key=lambda x: x.get("run_id", ""))}
    return rows, models


def fmt_tmv(row):
    return (f"{'Y' if row['tools'] else '-'}{'Y' if row['mcp'] else '-'}"
            f"{'Y' if row['vision'] else '-'}")


def status_mark(row):
    if row["cross_validated"]:
        return "validated*"
    if row["witnesses"] >= 1:
        return "1 witness"
    if row["status"] == "failed":
        return "failed"
    return "no results"


def capability_score(row):
    return sum((row["tools"], row["mcp"], row["vision"]))


def recommendations(rows):
    out = []
    for r in rows:
        if r["status"] == "failed":
            continue
        if r["witnesses"] == 0:
            out.append((3, f"{r['id']}: first witness — replicate and submit a result"))
        if r["tools"] == 0 and r["tool_model"]:
            out.append((2, f"{r['id']}: confirm tool calling"))
        if r["mcp"] == 0 and r["tool_model"]:
            out.append((1, f"{r['id']}: confirm MCP through a harness (pi/omp)"))
        if r["vision"] == 0 and r["vision_model"]:
            out.append((1, f"{r['id']}: confirm vision with an mmproj test"))
        if r["witnesses"] == 1:
            out.append((0, f"{r['id']}: second INDEPENDENT witness "
                           "(different person, not an alias)"))
    out.sort(key=lambda x: (-x[0], x[1]))
    return [a for _, a in out]


def landing_md(rows, n_models, n_runs):
    now = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    lines = ["# Strix Halo AI Recipe Registry — results board", "",
             f"_Generated {now} by tools/leaderboard.py — do not hand-edit._", "",
             "## What is this", "",
             "A registry of reproducible, evidence-backed serving recipes for "
             "local LLMs on unified-memory Linux boxes. Every number on this "
             "board comes from an immutable result record submitted against a "
             "pinned recipe — nothing is hand-set, cross-validation is "
             "derived from independent witnesses.", "",
             "- **Run your own tests / add a recipe:** read `SKILL.md`, search "
             "with `tools/search.py`, replicate a recipe, run its tests, submit "
             "results.", "",
             "- **Format & trust model:** `FORMAT.md`. **Licensing:** code "
             "Apache-2.0, registry data CC0, docs CC BY 4.0 (README).", "",
             "> **Reading this board:** tables are ordered by latest activity — "
             "this is NOT a quality ranking. There is no universal score. "
             "Rank recipes by what you need using "
             "`python tools/leaderboard.py --sort tg --cap vision` etc.",
             "", "## Models", "",
             f"_{n_models} models · {n_runs} result records · latest activity "
             "first_", "",
             "| id | model | variants | quant(s) | size | T M V | PP t/s | "
             "TG t/s | wit | backend | verdict |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    order = sorted(rows, key=lambda r: (r["last_run"] == "", -len(r["last_run"]),
                                        r["id"]))
    for r in order:
        q = ",".join(str(x) for x in r["quants"]) or "—"
        lines.append(
            f"| [{r['id']}](models/{r['id']}.md) | {r['model'][:40]} | "
            f"{r['n_variants']} | {q} | {r['size_gb'] or '-'} | {fmt_tmv(r)} | "
            f"{r['pp'] or '-'} | {r['tg'] or '-'} | {r['witnesses']} | "
            f"{r['backend']} | {status_mark(r)} |")
    lines += ["",
              "_T=confirmed tool calling, M=confirmed MCP, V=confirmed "
              "vision. `validated*` = ≥ 2 contributor ids at the current "
              "hash with all declared tests passing — treat aliases of one "
              "person as one witness._", ""]
    return lines


def latest_tests_md(rows, models, limit=10):
    runs = []
    for rid, m in models.items():
        for res in m["all_runs"]:
            runs.append((rid, res))
    runs.sort(key=lambda x: x[1].get("run_id", ""), reverse=True)
    lines = ["## Latest tests", "",
             "| when (UTC) | model | test | result | PP t/s | TG t/s | who |",
             "|---|---|---|---|---|---|---|"]
    for rid, res in runs[:limit]:
        ts = res.get("run_id", "")[:13].replace("T", " ")
        who = res.get("contributor_id", "?")
        for t in res.get("tests", []):
            tm = t.get("metrics") or {}
            lines.append(f"| {ts} | [{rid}](models/{rid}.md) | `{t['id']}` "
                         f"| {t['result']} | {tm.get('tokens_per_sec_pp', '-')} "
                         f"| {tm.get('tokens_per_sec_tg', '-')} | {who} |")
    return lines


def model_md(rid, row, model):
    r = row
    recipe = model["recipe"]
    lines = [f"# {recipe['model']['name']} (`{rid}`)", "",
             f"- Latest version: **v{recipe['version']}** · "
             f"{recipe.get('quant') or '?'} · {recipe['model'].get('size_gb')} GB · "
             f"arch {recipe['model'].get('arch')} · engine {r['backend']}",
             f"- Source: {recipe['model'].get('source') or '—'}",
             f"- Verdict: {status_mark(r)} — {len(model['all_runs'])} result(s) "
             f"across {r['n_variants']} variant(s); {r['witnesses']} witness(es) "
             f"at the current hash: "
             f"{', '.join(sorted({x['contributor_id'] for x in model['results']})) or 'none'}",
             f"- Confirmed capabilities: tools={r['tools']}, mcp={r['mcp']}, "
             f"vision={r['vision']} · objectives: "
             f"{', '.join(r['objectives']) or '—'}",
             "",
             "## Variants (configurations tested)", "",
             "Each variant = a content hash (pinned launch configuration) "
             "with its own evidence trail. Quants are a dimension *under* a "
             "configuration — results name the quant they ran.", "",
             "| hash | v | quant(s) | PP t/s | TG t/s | wit | results | tests (pass/total) |",
             "|---|---|---|---|---|---|---|---|"]
    for v in model["variants"]:
        q = ",".join(str(x) for x in v["quant"]) or "—"
        tallies = []
        for tid, tally in v["tests"].items():
            total = sum(tally.values())
            passed = tally.get("pass", 0)
            tallies.append(f"{tid} {passed}/{total}")
        lines.append(f"| `{v['short']}` | v{v['version']} | {q} | "
                     f"{v['pp'] or '-'} | {v['tg'] or '-'} | {v['witnesses']} "
                     f"| {v['results']} | {'; '.join(tallies) or '—'} |")
    lines += ["", "## Runs", "",
              "| run (UTC) | contributor | quant | hash | PP | TG | tests |",
              "|---|---|---|---|---|---|---|"]
    for res in model["all_runs"]:
        ts = res.get("run_id", "")[:13].replace("T", " ")
        h = res.get("content_hash", "")[7:13]
        tm = res.get("metrics") or {}
        pps = [str(t.get("metrics", {}).get("tokens_per_sec_pp"))
               for t in res.get("tests", []) if t.get("metrics", {}).get("tokens_per_sec_pp")]
        tgs = [str(t.get("metrics", {}).get("tokens_per_sec_tg"))
               for t in res.get("tests", []) if t.get("metrics", {}).get("tokens_per_sec_tg")]
        tsum = "; ".join(f"{t['id']}={t['result']}" for t in res.get("tests", []))
        lines.append(f"| {ts} | {res.get('contributor_id')} | "
                     f"{res.get('quant') or '-'} | `{h}` | "
                     f"{pps[0] if pps else tm.get('tokens_per_sec_pp', '-')} | "
                     f"{tgs[0] if tgs else tm.get('tokens_per_sec_tg', '-')} | "
                     f"{tsum} |")
    notes = [(x.get("run_id", "")[:13], x.get("notes"))
             for x in model["all_runs"] if x.get("notes")]
    if notes:
        lines += ["", "### Sources & notes", ""]
        for ts, n in notes:
            lines.append(f"- {ts}Z — {n}")
    lineage = recipe.get("lineage", {}).get("parents", [])
    if lineage:
        lines += ["", "### Lineage", ""]
        for p in lineage:
            lines.append(f"- **{p['id']} v{p.get('version')}** — "
                         f"{p.get('contribution', '')}")
        if recipe.get("lineage", {}).get("rationale"):
            lines.append(f"- Rationale: {recipe['lineage']['rationale']}")
    return "\n".join(lines) + "\n"


def render_table(rows):
    order = sorted(rows, key=lambda r: (capability_score(r), r["witnesses"],
                                        r["tg"] or 0), reverse=True)
    print("{:<20} {:<9} {:>5} {:>8} {:>8} {:>3} {:>7}  {}".format(
        "id", "quant", "TMV", "PP", "TG", "wit", "backend", "model"))
    for r in order:
        print("{:<20} {:<9} {:>5} {:>8} {:>8} {:>3} {:>7}  {}".format(
            r["id"][:20], ",".join(str(q) for q in r["quants"])[:9],
            fmt_tmv(r), r["pp"] or "-", r["tg"] or "-", r["witnesses"],
            r["backend"], r["model"][:32]))
    print("\n'Ranking' is a query convenience — order changes with --sort; "
          "defaults to capability coverage. See LEADERBOARD.md for the "
          "neutral board.")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sort", choices=["score", "tg", "pp", "witnesses",
                                       "name"], default="score")
    ap.add_argument("--reverse", action="store_true")
    ap.add_argument("--engine", choices=["vulkan", "rocm"])
    ap.add_argument("--cap", choices=["tools", "mcp", "vision"])
    ap.add_argument("--min-witnesses", type=int, default=0)
    ap.add_argument("--next", action="store_true",
                    help="print personal 'what to run next' list (stdout only)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-write", action="store_true",
                    help="do not rewrite LEADERBOARD.md / models/*.md")
    args = ap.parse_args()

    rows, models = collect()

    if args.json:
        print(json.dumps(rows, indent=2, default=str))
        return
    if args.next:
        for i, a in enumerate(recommendations(rows), 1):
            print(f"{i}. {a}")
        return

    if args.engine:
        rows = [r for r in rows if args.engine in r["backend"]]
    if args.cap:
        rows = [r for r in rows if r[args.cap]]
    if args.min_witnesses:
        rows = [r for r in rows if r["witnesses"] >= args.min_witnesses]
    key = {"score": lambda r: (-capability_score(r), -r["witnesses"], -(r["tg"] or 0)),
           "tg": lambda r: -(r["tg"] or 0),
           "pp": lambda r: -(r["pp"] or 0),
           "witnesses": lambda r: -r["witnesses"],
           "name": lambda r: r["id"]}[args.sort]
    render_table(sorted(rows, key=key, reverse=args.reverse))

    if not args.no_write:
        all_rows, all_models = collect()
        n_runs = sum(1 for _ in iter_result_files())
        landing = "\n".join(landing_md(all_rows, len(all_rows), n_runs)
                            + latest_tests_md(all_rows, all_models)) + "\n"
        with open(REPO_ROOT / "LEADERBOARD.md", "w") as f:
            f.write(landing)
        outdir = REPO_ROOT / "models"
        os.makedirs(outdir, exist_ok=True)
        for rid in all_models:
            row = next(x for x in all_rows if x["id"] == rid)
            with open(outdir / f"{rid}.md", "w") as f:
                f.write(model_md(rid, row, all_models[rid]))
        print(f"\nWrote LEADERBOARD.md + {len(all_models)} model page(s) "
              f"under models/")


if __name__ == "__main__":
    main()
