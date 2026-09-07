#!/usr/bin/env python3
"""
analyze — the daily-life entry point for the registry.

Three verbs, one tool:

  python tools/analyze.py machine
      Fingerprint this machine (probe v2) + validate the probe JSON
      against the result schema. Run this first — it tells you (and the
      registry) what hardware/backend you are, and proves your probe
      matches the schema before you submit anything.

  python tools/analyze.py cmd "your llama-server launch command" [--write]
      Capture an EXISTING setup in one shot: parses the launch command
      (or --pid, or llama-swap entry via --from-llama-swap KEY), reads
      the model from disk/HF cache, probes the machine, and produces a
      schema-valid draft recipe with a correct content_hash — nothing
      guessed, capabilities all false until you test.
      --write saves recipes/<id>/<id>-v0.1.0.yaml.
      Print the result's share block: id + hash others can run against.

  python tools/analyze.py test --recipe <id> [--endpoint URL] [--submit ...]
      Run the battery against a recipe you (or someone else) published:
      quick default = tool-roundtrip + throughput + context-recall@4k.
      --submit --contributor <you> writes an immutable result record.
      This is the "let me test what that person said they did" path.

Examples:
  analyze machine
  analyze cmd "/usr/bin/llama-server -hf unsloth/Model-GGUF:Q4_K_M -ngl 999 --jinja -fa on -c 32768 --port 8080" --write
  analyze test --recipe qwen3-coder --endpoint http://127.0.0.1:1234/v1 --submit --contributor me
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import yaml  # noqa: E402
import jsonschema  # noqa: E402

from common import RECIPES_DIR, load_schema, load_yaml  # noqa: E402
import collect  # noqa: E402

TOOLS = os.path.dirname(os.path.abspath(__file__))


def _probe():
    sh = os.path.join(TOOLS, "probe.sh")
    out = subprocess.check_output(["bash", sh], text=True, timeout=180)
    return json.loads(out)


# --------------------------------------------------------------------------
# machine
# --------------------------------------------------------------------------

def cmd_machine(args):
    probe = _probe()
    g = probe.get("gpu", {})
    m = probe.get("mem", {})
    b = probe.get("backend", {})
    print("=== Machine profile (probe schema_version %s) ==="
          % probe.get("schema_version"))
    print(f"distro      : {probe.get('distro')} (family {probe.get('family')})")
    print(f"kernel      : {probe.get('kernel')}")
    print(f"memory      : {m.get('total_gb')} GB total · "
          f"{m.get('gtt_gib')} GiB GTT · {m.get('vram_mib')} MiB VRAM")
    print(f"gpu         : {g.get('name')} · {g.get('driver')} · "
          f"vulkan {g.get('vulkan_version')} · {g.get('free_mib')} MiB free")
    print(f"backend     : llama.cpp build {b.get('build')} commit {b.get('commit')} "
          f"({b.get('install_method') or '?'} {b.get('pkg_version') or ''})")
    if probe.get("llama_swap_config"):
        print(f"llama-swap  : {probe.get('llama_swap_config')}")
    # schema check: probe must satisfy result.schema probe_output
    schema = load_schema("result.schema.json")
    probe_schema = {"$schema": schema.get("$schema"),
                    "type": "object",
                    "properties": schema["properties"]["probe_output"]["properties"],
                    "required": schema["properties"]["probe_output"].get("required", [])}
    try:
        jsonschema.validate(probe, probe_schema)
        print("probe schema: OK — your environment record will validate on submit")
        return 0
    except jsonschema.ValidationError as e:
        print(f"probe schema: FAIL — {e.message}")
        print("If your distro is unsupported, add tools/probe.d/<family>.sh "
              "(copy arch.sh, register in detect_family) and re-run.")
        return 1


# --------------------------------------------------------------------------
# cmd — capture an existing setup
# --------------------------------------------------------------------------

def cmd_capture(args):
    probe = _probe()
    if args.pid:
        with open(f"/proc/{args.pid}/cmdline", "rb") as f:
            cmd = " ".join(p for p in f.read().decode("utf-8", "replace")
                           .split("\x00") if p)
        key = args.name or "captured"
    elif args.cmd:
        cmd = args.cmd
        key = args.name or collect.slugify(os.path.basename(
            (collect.parse_launch_flags(cmd).get("model_spec") or "").rstrip("/"))
            or "captured")
    elif args.from_llama_swap:
        import glob
        models = collect.load_llama_swap(args.from_llama_swap)
        hit = next((m for m in models if m["key"] == args.from_llama_swap_key
                    or (not args.from_llama_swap_key and False)), None)
        if not hit:
            sys.exit(f"--from-llama-swap: model key '{args.from_llama_swap_key}' "
                     f"not found in {args.from_llama_swap}")
        cmd = hit["cmd"]
        key = hit["key"]
    else:
        sys.exit("pass --cmd '<launch command>' or --pid <pid> or "
                 "--from-llama-swap <config> --llama-swap-key <key>")

    flags = collect.parse_launch_flags(cmd)
    draft = collect.make_draft(key, flags, probe, args.author,
                               None, args.hardware_target)
    print("=== Captured setup ===")
    print(f"id      : {draft['id']}")
    print(f"content : {draft['content_hash']}")
    print(f"model   : {draft['model']['name']} (arch {draft['model']['arch']}) "
          f"quant {draft['quant'] or '?'}")
    print(f"flags   : ctx={draft['parameters'].get('ctx_size', {}).get('value')} "
          f"fa={draft['parameters'].get('flash_attn', {}).get('value')} "
          f"jinja={draft['parameters'].get('jinja', {}).get('value')} "
          f"mmproj={bool(draft['parameters'].get('mmproj'))}")
    print(f"command : {flags['cmd'][:160]}")

    if args.write:
        out_dir = RECIPES_DIR / draft["id"]
        out_path = out_dir / f"{draft['id']}-v0.1.0.yaml"
        if out_path.exists():
            sys.exit(f"exists: {out_path} — remove it or pick --name {draft['id']}-2")
        out_dir.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w") as f:
            yaml.safe_dump(draft, f, sort_keys=False)
        print(f"\nwrote draft: {out_path}")
    print("\n=== share block ===")
    print(f"recipe id : {draft['id']}")
    print(f"test hash : {draft['content_hash']}")
    print(f"share cmd : python tools/analyze.py test --recipe {draft['id']} "
          f"--endpoint http://127.0.0.1:8080/v1")
    print("\nNext (draft only): annotate parameters with WHY, set "
          "objectives/constraints, then run: python tools/analyze.py test "
          f"--recipe {draft['id']} --submit --contributor <you>")
    return 0


# --------------------------------------------------------------------------
# test — run the battery against a recipe
# --------------------------------------------------------------------------

QUICK_TESTS = [
    ("tool-roundtrip", []),
    ("throughput", ["--n", "2", "--out-tokens", "64", "--pp-tokens", "8192"]),
    ("context-recall", ["--ctx", "4096"]),
]


def cmd_test(args):
    endpoint = args.endpoint or os.environ.get("LLAMA_ENDPOINT",
                                               "http://127.0.0.1:1234/v1")
    # resolve recipe file (latest)
    import glob
    files = sorted(glob.glob(os.path.join("recipes", args.recipe,
                                          f"{args.recipe}-v*.yaml")))
    if not files:
        sys.exit(f"no recipe '{args.recipe}' — check tools/search.py --model")
    recipe = load_yaml(files[-1])
    model = args.model or args.recipe
    print(f"=== Testing recipe {args.recipe} (v{recipe['version']}) ===")
    print(f"endpoint: {endpoint}  model: {model}")
    print(f"pinned  : {recipe['content_hash']}  quant {recipe.get('quant')}")
    print(f"capabilities still false until a test passes:\n"
          f"  tools/mcp/vision = {[(k, v) for k, v in recipe.get('harness_compat', {}).get('capabilities_confirmed', {}).items()]}")

    tests = QUICK_TESTS
    ev_files = []
    for tid, extra in tests:
        runner = os.path.join(os.path.dirname(TOOLS), "tests", "runners",
                              tid.replace("-", "_") + ".py")
        if not os.path.exists(runner):
            print(f"[skip] no runner for {tid}")
            continue
        tmp = os.path.join(tempfile.mkdtemp(prefix="analyze-"), f"{tid}.json")
        cmd = ["python3", runner, "--endpoint", endpoint, "--model", model,
               "--timeout", str(args.timeout)] + extra
        print(f"\n--- {tid} ---")
        try:
            out = subprocess.run(cmd, capture_output=True, text=True,
                                 timeout=args.timeout + 30)
            last = out.stdout.strip().splitlines()[-1] if out.stdout.strip() else ""
            print(f"rc={out.returncode}  {last[:300]}")
            if last.startswith("{"):
                with open(tmp, "w") as f:
                    f.write(last + "\n")
                ev_files.append((tid, tmp))
            elif out.stderr.strip():
                print(out.stderr.strip()[-500:])
        except subprocess.TimeoutExpired:
            print(f"[timeout] {tid}")

    if args.submit:
        if not args.contributor:
            sys.exit("--submit requires --contributor <stable-handle>")
        sub_args = [sys.executable or "python3",
                    os.path.join(TOOLS, "submit_result.py"),
                    "--recipe", args.recipe, "--contributor", args.contributor]
        for tid, tmp in ev_files:
            sub_args += ["--evidence", f"{tid}={tmp}"]
        if args.notes:
            sub_args += ["--notes", args.notes]
        r = subprocess.run(sub_args, capture_output=True, text=True)
        print(r.stdout[-800:])
        if r.returncode:
            print(r.stderr[-500:])
            return r.returncode
        print("\nShare your result with the community: one PR per experiment "
              "(git add results/ recipes/ && git commit && git push).")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="verb", required=True)

    p = sub.add_parser("machine", help="probe + schema check")
    p.set_defaults(fn=cmd_machine)

    p = sub.add_parser("cmd", help="capture an existing setup as a draft")
    p.add_argument("--cmd", help="the launch command, e.g. your llama-server line")
    p.add_argument("--pid", help="capture from a running process")
    p.add_argument("--name", help="recipe id (slug) for the draft")
    p.add_argument("--author", default=os.environ.get("USER", "unknown"))
    p.add_argument("--hardware-target", default=None)
    p.add_argument("--write", action="store_true", help="write the draft YAML")
    p.set_defaults(fn=cmd_capture)

    p = sub.add_parser("test", help="run the battery against a recipe")
    p.add_argument("--recipe", required=True)
    p.add_argument("--endpoint", default=None)
    p.add_argument("--model", default=None)
    p.add_argument("--timeout", type=int, default=600)
    p.add_argument("--submit", action="store_true")
    p.add_argument("--contributor", default=None)
    p.add_argument("--notes", default="")
    p.set_defaults(fn=cmd_test)

    args = ap.parse_args()
    sys.exit(args.fn(args))


if __name__ == "__main__":
    main()
