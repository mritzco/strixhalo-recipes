#!/usr/bin/env python3
"""
Collect running llama.cpp-style setups into draft recipe YAMLs.

Deliberately conservative: anything it cannot verify by direct inspection
(harness capabilities, test results, tool/MCP/vision behavior) is left as
an explicit TODO / false rather than guessed — guessed capability fields
are worse than missing ones. Drafts are schema-valid with a correct
content_hash by construction; quant never affects the hash, so a draft
describes the MODEL, not one quant.

Sources:
  --from-llama-swap [CONFIG]   enumerate llama-swap config.yaml models ->
                               one draft per system key (default config
                               is ~/.config/llama-swap/config.yaml)
  --pid <pid>                  inspect a running process's cmdline
  --launch-cmd "<cmd>"         parse a launch command string directly

Examples:
  python tools/collect.py --from-llama-swap --dry-run --author itzco
  python tools/collect.py --launch-cmd "llama-server -m /models/x.gguf -c 65536 -fa on --jinja" --model-name my-quick --author itzco
  python tools/collect.py --pid 12345 --model-name my-quick

Writes recipes/<slug>/<slug>-v0.1.0.yaml (refuses to overwrite) and
prints a checklist of what still needs manual verification.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date

import yaml

from common import RECIPES_DIR, load_schema, compute_content_hash
import gguf_lite

DEFAULT_SWAP_CONFIG = os.path.expanduser("~/.config/llama-swap/config.yaml")
SWAP_ENDPOINT = "http://127.0.0.1:1234/v1"


def _run_probe():
    probe_sh = os.path.join(os.path.dirname(os.path.abspath(__file__)), "probe.sh")
    try:
        out = subprocess.check_output(["bash", probe_sh], text=True, timeout=120)
        return json.loads(out)
    except Exception as e:
        print(f"WARNING: probe.sh failed ({e}); hardware/backend fields will be sparse.")
        return {}


def slugify(name):
    return re.sub(r"[^a-z0-9.]+", "-", name.lower()).strip("-")


def find_local_gguf(model_path_or_hf):
    """Resolve a --model path or -hf repo:quant spec to a local GGUF file.

    -hf repos resolve through the HF cache convention:
    ~/.cache/huggingface/hub/models--<org>--<name>/snapshots/*/*.gguf.
    Returns (fs_path|None, quant_tag|None).
    """
    if model_path_or_hf.startswith(("-hf", "hf://")):
        spec = model_path_or_hf[len("-hf"):].strip() if model_path_or_hf.startswith("-hf") else model_path_or_hf[len("hf://"):]
        repo, _, tag = spec.partition(":")
        quant = tag or None
        fs = hf_cache_path(repo)
        return fs, quant
    if os.path.exists(model_path_or_hf):
        return model_path_or_hf, gguf_lite.quant_from_filename(model_path_or_hf)
    return None, gguf_lite.quant_from_filename(model_path_or_hf)


def hf_cache_path(repo):
    """~/.cache/huggingface/hub/models--org--name/snapshots/**/*.gguf

    Handles flat repos (snapshots/<rev>/*.gguf) and quant-subdir repos
    (snapshots/<rev>/<QUANT>/*-0000N-of-0000M.gguf). Excludes mmproj.
    """
    import glob
    ident = "models--" + repo.replace("/", "--")
    base = os.path.expanduser(f"~/.cache/huggingface/hub/{ident}/snapshots")
    if not os.path.isdir(base):
        return None
    candidates = []
    for f in glob.glob(base + "/**/*.gguf", recursive=True):
        if "mmproj" not in os.path.basename(f).lower():
            candidates.append(f)
    if not candidates:
        return None
    # Prefer the biggest non-mmproj GGUF in the newest snapshot.
    newest = max(candidates, key=lambda p: p.split("/snapshots/", 1)[1])
    pool = [p for p in candidates if p.split("/snapshots/", 1)[1].startswith(
        newest.split("/snapshots/", 1)[1].split("/", 1)[0])]
    return max(pool, key=os.path.getsize)


def parse_launch_flags(cmd):
    """Extract flags recipes care about from a launch command string.

    Handles -hf repo:quant, -fa on/off, --mmproj, value flags with
    '=' or space, and bare booleans.
    """
    tokens = cmd.split()
    out = {
        "cmd": cmd, "engine": "llama.cpp", "model_spec": None,
        "model_path": None, "quant": None, "ctx_size": None,
        "cache_type_k": None, "cache_type_v": None, "flash_attn": False,
        "jinja": False, "ngl": None, "mmproj": None, "alias": None,
        "host": "127.0.0.1", "port": None, "hf_repo": None,
    }
    value_flags = {
        "-m": "model_path", "--model": "model_path",
        "-hf": "hf_repo", "-hfr": "_hf_rev",
        "-c": "ctx_size", "--ctx-size": "ctx_size",
        "--cache-type-k": "cache_type_k", "--cache-type-v": "cache_type_v",
        "-ngl": "ngl", "--n-gpu-layers": "ngl",
        "--mmproj": "mmproj", "--mmproj-file": "mmproj",
        "--alias": "alias", "--host": "host", "--port": "port",
        "-p": "port",
    }
    i = 0
    while i < len(tokens):
        t = tokens[i]
        key, _, inline = t.partition("=")
        if key in value_flags:
            if inline:
                val = inline
            elif i + 1 < len(tokens):
                val = tokens[i + 1]
                i += 1
            else:
                i += 1
                continue
            field = value_flags[key]
            if field == "_hf_rev":
                i += 1
                continue
            out[field] = val
        elif key in ("--flash-attn", "-fa"):
            out["flash_attn"] = True
            if i + 1 < len(tokens) and tokens[i + 1] in ("on", "off", "1", "0"):
                if tokens[i + 1] in ("off", "0"):
                    out["flash_attn"] = False
                i += 1
        elif key == "--jinja":
            out["jinja"] = True
        i += 1

    if out["hf_repo"]:
        repo = out["hf_repo"]
        base, _, tag = repo.partition(":")
        out["quant"] = tag or None
        out["model_spec"] = base
        fs_path, _ = find_local_gguf("-hf " + repo)
        out["model_path"] = fs_path
    elif out["model_path"]:
        out["model_spec"] = out["model_path"]
        _, q = find_local_gguf(out["model_path"])
        out["quant"] = out["quant"] or q
    return out


def make_draft(key, flags, probe, author, min_ram_gb, hardware_target,
               serving_note=None):
    """Build one recipe draft dict (schema-shaped, correct hash)."""
    model_meta = {}
    size_gb = None
    if flags["model_path"] and os.path.exists(flags["model_path"]):
        try:
            model_meta = gguf_lite.summarize(flags["model_path"])
            size_gb = round(os.path.getsize(flags["model_path"]) / (1024 ** 3), 1)
        except gguf_lite.GGUFParseError as e:
            print(f"  WARNING: could not parse GGUF metadata ({e}).")
    elif flags["model_spec"] and not flags["hf_repo"]:
        print(f"  WARNING: model file not found locally ({flags['model_spec']}); "
              "model fields will need manual fill-in.")

    vision_capable = bool(flags["mmproj"]) or model_meta.get("vision", False)
    mem = probe.get("mem", {})
    gtt = mem.get("gtt_gib")
    if not hardware_target:
        hardware_target = ("strix-halo-128gb-unified" if (gtt and gtt >= 96)
                           else "TODO-fill-in")
    if min_ram_gb is None:
        min_ram_gb = mem.get("total_gb") if mem.get("total_gb") else 128

    recipe_id = slugify(key)
    today = date.today().isoformat()
    recipe = {
        "id": recipe_id,
        "version": "0.1.0",
        "content_hash": "sha256:" + "0" * 64,  # fixed below
        "status": "experimental",
        "created": today,
        "author": author,
        "license": "CC0",
        "quant": flags["quant"],
        "lineage": {
            "parents": [],
            "rationale": "Auto-collected draft — fill in if this descends from another recipe.",
        },
        "objectives": {"primary": [], "secondary": [], "not_optimized": []},
        "constraints": [],
        "tradeoffs": [],
        "model": {
            "name": model_meta.get("name") or flags["model_spec"] or "TODO-fill-in",
            "arch": model_meta.get("architecture") or "TODO-fill-in",
            "source": (flags["hf_repo"].partition(":")[0]
                       if flags["hf_repo"] else
                       (os.path.dirname(flags["model_spec"]) if flags["model_spec"] else "TODO-fill-in")),
            "file_sha256": None,
            "size_gb": size_gb if size_gb is not None else 0,
            "mtp": False,
            "vision": bool(vision_capable),
            "tool_calling": bool(flags["jinja"]),
        },
        "hardware": {
            "target": hardware_target,
            "gpu_mem_split_gb": None,
            "min_ram_gb": int(min_ram_gb),
            "mem_total_gb": mem.get("total_gb"),
            "gtt_gib": gtt,
            "vram_mib": mem.get("vram_mib"),
        },
        "backend": {
            "engine": flags["engine"],
            "commit": probe.get("backend", {}).get("commit") or "TODO-fill-in",
            "build": probe.get("backend", {}).get("build"),
            "upstream": None,
            "patches": [],
            "install_method": probe.get("backend", {}).get("install_method"),
            "pkg_version": probe.get("backend", {}).get("pkg_version"),
            "build_flags": [],
            "os_family": probe.get("family", "unknown"),
            "kernel": probe.get("kernel"),
            "vulkan_version": (probe.get("gpu", {}) or {}).get("vulkan_version"),
            "rocm_version": probe.get("rocm_version"),
        },
        "launch": {"command": flags["cmd"]},
        "parameters": {},
        "annotations": [{
            "type": "experimental",
            "text": f"Auto-collected draft ({today}); capabilities_confirmed are "
                    "all false until real harness tests run. Add parameter "
                    "annotations with the 'why', objectives/constraints/tradeoffs, "
                    "and evidence refs per the v0.3 data model.",
        }],
        "harness_compat": {
            "tested_with": [],
            "exposes_as": "TODO-fill-in",
            "capabilities_confirmed": {"tools": False, "mcp": False, "vision": False},
        },
        "tests": [],
        "failure_notes": None,
    }

    for pname, val in (
        ("ctx_size", flags["ctx_size"]),
        ("cache_type_k", flags["cache_type_k"]),
        ("cache_type_v", flags["cache_type_v"]),
        ("ngl", flags["ngl"]),
        ("mmproj", flags["mmproj"]),
    ):
        if val is not None:
            recipe["parameters"][pname] = {"value": int(val) if pname == "ctx_size" and str(val).isdigit() else val,
                                           "annotations": []}
    recipe["parameters"]["flash_attn"] = {"value": bool(flags["flash_attn"]), "annotations": []}
    recipe["parameters"]["jinja"] = {"value": bool(flags["jinja"]), "annotations": []}

    if serving_note:
        recipe["launch"]["serving"] = serving_note

    schema = load_schema("recipe.schema.json")
    recipe["content_hash"] = compute_content_hash(recipe, schema)
    return recipe


def load_llama_swap(config_path):
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)
    models = (cfg or {}).get("models") or {}
    return [{"key": k, "cmd": (m.get("cmd") or "").strip(),
             "proxy": m.get("proxy"), "ttl": m.get("ttl")}
            for k, m in models.items() if m and m.get("cmd")]


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--from-llama-swap", nargs="?", const=DEFAULT_SWAP_CONFIG,
                     metavar="CONFIG", help="enumerate llama-swap config.yaml "
                                            "(one draft per system key)")
    src.add_argument("--launch-cmd", help="launch command string")
    src.add_argument("--pid", help="PID of a running llama-server")
    ap.add_argument("--model-name", help="recipe id slug (required for --launch-cmd/--pid)")
    ap.add_argument("--model", help="llama-swap mode: only this model key")
    ap.add_argument("--author", default=os.environ.get("USER", "unknown"))
    ap.add_argument("--min-ram-gb", type=int, default=None)
    ap.add_argument("--hardware-target", default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    probe = _run_probe()
    entries = []

    if args.from_llama_swap:
        if not os.path.exists(args.from_llama_swap):
            sys.exit(f"llama-swap config not found: {args.from_llama_swap}")
        print(f"Reading llama-swap config: {args.from_llama_swap}\n")
        models = load_llama_swap(args.from_llama_swap)
        if not models:
            sys.exit("no models found in llama-swap config")
        for m in models:
            if args.model and m["key"] != args.model:
                continue
            if not m["cmd"]:
                print(f"  SKIP {m['key']}: empty cmd")
                continue
            flags = parse_launch_flags(m["cmd"])
            if flags["engine"] != "llama.cpp":
                print(f"  SKIP {m['key']}: engine {flags['engine']} not supported by auto-collect")
                continue
            serving = {
                "fronted_by": "llama-swap",
                "endpoint": SWAP_ENDPOINT,
                "note": "llama-swap substitutes ${PORT} per child server; each "
                        "config entry needs proxy: http://127.0.0.1:${PORT} "
                        "(llama-server binds IPv4 only)." + (
                            f" ttl={m['ttl']}" if m.get("ttl") else ""),
            }
            entries.append((m["key"], flags, serving))
    elif args.pid or args.launch_cmd:
        if not args.model_name:
            sys.exit("--model-name is required with --pid/--launch-cmd")
        if args.pid:
            path = f"/proc/{args.pid}/cmdline"
            if not os.path.exists(path):
                sys.exit(f"No /proc/{args.pid}/cmdline")
            with open(path, "rb") as f:
                cmd = " ".join(p for p in f.read().decode("utf-8", errors="replace")
                               .split("\x00") if p)
        else:
            cmd = args.launch_cmd
        flags = parse_launch_flags(cmd)
        entries.append((args.model_name, flags, None))
    else:
        sys.exit("Pass --from-llama-swap, --launch-cmd, or --pid.")

    drafts = []
    for key, flags, serving in entries:
        print(f"== {key}")
        print(f"  command: {flags['cmd'][:120]}")
        print(f"  model_spec={flags['model_spec']} quant={flags['quant']} "
              f"ctx={flags['ctx_size']} fa={flags['flash_attn']} "
              f"mmproj={flags['mmproj']} jinja={flags['jinja']}")
        draft = make_draft(key, flags, probe, args.author, args.min_ram_gb,
                           args.hardware_target, serving)
        drafts.append((key, draft))
        print()

    if args.dry_run:
        for key, draft in drafts:
            print(f"--- draft recipe: {key} (dry run, not written) ---")
            print(yaml.safe_dump(draft, sort_keys=False))
        print(f"\n{drafts and len(drafts) or 0} draft(s) previewed. "
              "Re-run without --dry-run to write them.")
        return

    written = []
    for key, draft in drafts:
        out_dir = RECIPES_DIR / draft["id"]
        out_path = out_dir / f"{draft['id']}-v{draft['version']}.yaml"
        if out_path.exists():
            print(f"SKIP {out_path} — already exists (bump version or remove first)")
            continue
        out_dir.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w") as f:
            yaml.safe_dump(draft, f, sort_keys=False)
        written.append(out_path)

    if not written:
        sys.exit("nothing written (all drafts exist?)")

    print("Wrote drafts:")
    for p in written:
        print(f"  {p}")
    print("""
Each draft is a DRAFT. Before proposing it as a PR you must:
  [ ] Annotate parameters with the WHY (v0.3): add annotations to
      ctx_size / cache types / mmproj etc. with evidence refs.
  [ ] Fill objectives (primary/secondary/not_optimized), constraints,
      and tradeoffs — what is this recipe optimizing, what must hold?
  [ ] Verify model.name / arch / source; sha256sum the GGUF into
      model.file_sha256 if you want file-level pinning.
  [ ] Add lineage.parents (multi-parent allowed) if this descends from
      other recipes — one-line contribution per parent.
  [ ] Actually TEST tool-calling / MCP / vision through a harness and set
      harness_compat.capabilities_confirmed truthfully (all false now by
      design — a heuristic guess is NOT a test).
  [ ] Add tests[] entries referencing tests/definitions ids, and run the
      runners.
  [ ] Run: python tools/validate.py --strict
  [ ] Submit a results/ record with tools/submit_result.py once tested.
""")
    print("Quant note: draft quant is informative only — changing quant "
          "does NOT change the content_hash (recipes apply to models).")


if __name__ == "__main__":
    main()
