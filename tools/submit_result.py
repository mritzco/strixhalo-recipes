#!/usr/bin/env python3
"""
Build and write one immutable results/ record for a recipe run.

Typical agent flow:
  1. bash tools/probe.sh > /tmp/probe.json        (or omit --probe: auto-run)
  2. run the recipe's test runners, capture evidence:
       python tests/runners/tool_roundtrip.py ... > /tmp/tool.json
  3. python tools/submit_result.py \
       --recipe qwen3-coder \
       --contributor my-handle \
       --evidence tool-roundtrip=/tmp/tool.json \
       --evidence throughput=/tmp/tp.json \
       --metric tokens_per_sec_tg 38.2 \
       --notes "stable 3h session"

This does NOT run tests (they are scripts declared under tests/); it
assembles and validates the record so nobody hand-writes non-conforming
JSON. Records are append-only: existing run paths are never overwritten.
"""
import argparse
import glob
import json
import os
import secrets
import sys
from datetime import datetime, timezone

import jsonschema
import yaml

from common import RESULTS_DIR, load_schema, load_yaml

TOOL_VERSION = "submit_result.py@2.0.0"
STATUSES = {"pass", "fail", "degraded", "unsupported", "not_run", "inconclusive"}


def find_recipe(recipe_id, version=None):
    """Recipe file for an id: recipes/<id>/<id>-v*.yaml.

    Defaults to the latest version; pass --version to pin an older one
    (e.g. submitting a baseline run against the pre-tune recipe).
    """
    files = sorted(glob.glob(
        os.path.join("recipes", recipe_id, f"{recipe_id}-v*.yaml")))
    if version:
        exact = os.path.join("recipes", recipe_id,
                             f"{recipe_id}-v{version}.yaml")
        if not os.path.exists(exact):
            sys.exit(f"no recipe file {exact}")
        return exact
    if not files:
        sys.exit(f"no recipe files found for id '{recipe_id}' under recipes/")
    return files[-1]


def parse_test_arg(s):
    """'id=pass[:score]'"""
    id_part, _, rest = s.partition("=")
    result, _, score = rest.partition(":")
    if result not in STATUSES:
        sys.exit(f"--test {s}: result must be one of {sorted(STATUSES)}")
    entry = {"id": id_part, "result": result}
    if score:
        try:
            entry["score"] = float(score)
        except ValueError:
            sys.exit(f"--test {s}: score must be numeric")
    return entry


def load_evidence(id_path):
    """Runner JSON evidence file -> dict of evidence fields."""
    tid, _, path = id_path.partition("=")
    if not path:
        sys.exit(f"--evidence {id_path}: expected id=/path/to/evidence.json")
    with open(path) as f:
        ev = json.load(f)
    if not isinstance(ev, dict) or "status" not in ev:
        sys.exit(f"--evidence {id_path}: not a runner evidence record "
                 "(missing 'status')")
    entry = {"id": tid, "result": ev["status"]}
    if ev.get("score") is not None:
        entry["score"] = ev["score"]
    if ev.get("metrics"):
        entry["metrics"] = ev["metrics"]
    if ev.get("observations"):
        entry["observations"] = ev["observations"]
    if ev.get("artifacts"):
        entry["artifacts"] = ev["artifacts"]
    if ev.get("detail"):
        entry["detail"] = ev["detail"]
    return entry


def make_run_id():
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{ts}-{secrets.token_hex(4)}"


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--recipe", required=True)
    ap.add_argument("--version", default=None,
                    help="pin recipe version (default: latest file)")
    ap.add_argument("--contributor", required=True,
                    help="stable self-chosen handle (pseudonymous, not PII)")
    ap.add_argument("--probe", default=None,
                    help="path to probe.sh JSON; default: run probe.sh now")
    ap.add_argument("--quant", default=None,
                    help="quant actually run (default: the recipe's quant)")
    ap.add_argument("--test", action="append", default=[],
                    metavar="ID=result[:score]",
                    help="simple test entry (repeatable)")
    ap.add_argument("--evidence", action="append", default=[],
                    metavar="ID=/path/evidence.json",
                    help="runner evidence file (repeatable); preferred over --test")
    ap.add_argument("--metric", action="append", default=[], metavar="KEY=value",
                    help="run-level metric, e.g. tokens_per_sec_tg=38.2")
    ap.add_argument("--notes", default="")
    args = ap.parse_args()

    recipe_path = find_recipe(args.recipe, version=args.version)
    recipe = load_yaml(recipe_path)
    schema = load_schema("result.schema.json")

    # probe: run now unless a file is given
    if args.probe:
        with open(args.probe) as f:
            probe = json.load(f)
    else:
        probe_sh = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "probe.sh")
        import subprocess
        try:
            raw = subprocess.check_output(["bash", probe_sh], text=True,
                                          timeout=120)
            probe = json.loads(raw)
        except Exception as e:
            sys.exit(f"probe.sh failed ({e}); pass --probe <file>")

    tests = []
    for arg in args.test:
        tests.append(parse_test_arg(arg))
    for arg in args.evidence:
        tests.append(load_evidence(arg))
    if not tests:
        sys.exit("no tests given — pass --test and/or --evidence")

    metrics = {}
    for kv in args.metric:
        k, _, v = kv.partition("=")
        try:
            metrics[k] = float(v)
        except ValueError:
            metrics[k] = v

    run_id = make_run_id()
    record = {
        "recipe_id": recipe["id"],
        "recipe_version": recipe["version"],
        "content_hash": recipe["content_hash"],
        "run_id": run_id,
        "contributor_id": args.contributor,
        "quant": args.quant if args.quant is not None else recipe.get("quant"),
        "probe_output": probe,
        "tests": tests,
        "metrics": metrics,
        "notes": args.notes,
        "tool_version": TOOL_VERSION,
    }

    try:
        jsonschema.validate(record, schema)
    except jsonschema.ValidationError as e:
        sys.exit(f"record failed schema: {e.message}")

    hash_hex = record["content_hash"].replace("sha256:", "")
    out_dir = os.path.join(RESULTS_DIR, recipe["id"], hash_hex)
    out_path = os.path.join(out_dir, f"{run_id}.json")
    os.makedirs(out_dir, exist_ok=True)
    if os.path.exists(out_path):
        sys.exit(f"refusing to overwrite existing record: {out_path}")

    with open(out_path, "w") as f:
        json.dump(record, f, indent=2)
        f.write("\n")

    print(f"Wrote {out_path}")
    print(f"recipe={recipe['id']} v{recipe['version']} "
          f"hash={record['content_hash'][:16]}... quant={record['quant']}")
    for t in tests:
        print(f"  test {t['id']}: {t['result']}"
              + (f" score={t.get('score')}" if t.get("score") is not None else ""))
    print("\nNext: git add the record and open a PR (one experiment = one PR). "
          "Never edit this file afterwards — results are append-only.")


if __name__ == "__main__":
    main()
