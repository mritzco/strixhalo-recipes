#!/usr/bin/env python3
"""
Search index.json without loading full recipe YAML bodies.

Examples:
  python tools/search.py --model qwen3 --tool-calling
  python tools/search.py --model qwen3.8-27b --quant Q8_0
  python tools/search.py --vision --min-witnesses 2
  python tools/search.py --objective agent_capability --hardware strix-halo
  python tools/search.py --only-failed --model glm
"""
import argparse
import json

from common import INDEX_PATH


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", help="substring on model name or recipe id")
    ap.add_argument("--arch", help="substring on GGUF architecture")
    ap.add_argument("--quant", help="substring on quant")
    ap.add_argument("--hardware", help="substring on hardware target")
    ap.add_argument("--status", help="experimental|failed|deprecated")
    ap.add_argument("--engine")
    ap.add_argument("--os-family")
    ap.add_argument("--objective", help="substring match in objectives.primary")
    ap.add_argument("--tool-calling", action="store_true")
    ap.add_argument("--vision", action="store_true")
    ap.add_argument("--mcp", action="store_true")
    ap.add_argument("--min-witnesses", type=int, default=0)
    ap.add_argument("--exclude-failed", action="store_true")
    ap.add_argument("--only-failed", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not INDEX_PATH.exists():
        raise SystemExit("index.json not found — run tools/build_index.py first.")
    with open(INDEX_PATH) as f:
        entries = json.load(f)

    def hay(e):
        return f"{e.get('model_name','')} {e.get('id','')}"

    def matches(e):
        if args.model and args.model.lower() not in hay(e).lower():
            return False
        if args.arch and args.arch.lower() not in (e.get("arch") or "").lower():
            return False
        if args.quant and args.quant.lower() not in (e.get("quant") or "").lower():
            return False
        if args.hardware and args.hardware.lower() not in (e.get("hardware_target") or "").lower():
            return False
        if args.status and e.get("status") != args.status:
            return False
        if args.engine and (e.get("engine") or "").lower() != args.engine.lower():
            return False
        if args.os_family and e.get("os_family") != args.os_family:
            return False
        if args.objective and not any(
                args.objective.lower() in o.lower()
                for o in e.get("objectives_primary") or []):
            return False
        caps = e.get("capabilities_confirmed") or {}
        if args.tool_calling and not caps.get("tools"):
            return False
        if args.vision and not caps.get("vision"):
            return False
        if args.mcp and not caps.get("mcp"):
            return False
        if e.get("distinct_witnesses", 0) < args.min_witnesses:
            return False
        if args.exclude_failed and e.get("status") == "failed":
            return False
        if args.only_failed and e.get("status") != "failed":
            return False
        return True

    results = [e for e in entries if matches(e)]

    if args.json:
        print(json.dumps(results, indent=2))
        return

    if not results:
        print("No matching recipes.")
        return

    fmt = "{:<28} {:<8} {:<6} {:<12} {:>7} {:>3}{:>3}{:>3} {:>2}w  {}"
    print(fmt.format("id", "ver", "quant", "status", "size_gb", "T", "V", "M", "#", "model"))
    for e in results:
        caps = e.get("capabilities_confirmed") or {}
        print(fmt.format(
            e["id"][:28], e["version"], e.get("quant") or "-", e["status"],
            e.get("size_gb") or "-",
            "Y" if caps.get("tools") else "-",
            "Y" if caps.get("vision") else "-",
            "Y" if caps.get("mcp") else "-",
            e.get("distinct_witnesses", 0),
            e.get("model_name"),
        ))
    print("\nTip: capability columns show CONFIRMED (tested) capabilities. "
          "Recipes with 0-1 witnesses are unconfirmed — treat as anecdotal.")


if __name__ == "__main__":
    main()
