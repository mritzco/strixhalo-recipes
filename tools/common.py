"""Shared helpers for the recipe tooling. Stdlib only, plus PyYAML+jsonschema."""
import hashlib
import json
import os
import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
RECIPES_DIR = REPO_ROOT / "recipes"
RESULTS_DIR = REPO_ROOT / "results"
SCHEMA_DIR = REPO_ROOT / "schema"
INDEX_PATH = REPO_ROOT / "index.json"
TESTS_DIR = REPO_ROOT / "tests"
DEFINITIONS_DIR = TESTS_DIR / "definitions"

# Version of the probe JSON contract (see tools/probe.sh).
PROBE_SCHEMA_VERSION = 2

# Content-hash model (quant-agnostic). Only these keys of each top-level
# hashed field participate in the reproducibility hash. Everything else
# (quant, size, env versions, docs, annotations) is informative.
HASH_SUBSETS = {
    "model": ("name", "arch", "source"),
    "backend": ("engine", "commit", "build_flags"),
    "launch": ("command",),
    "hardware": ("target", "gpu_mem_split_gb"),
}

# Tokens stripped from launch.command before hashing: --host/--port are
# serving-layer choices, not reproducibility identity.
_PORT_HOST_RE = re.compile(
    r"(?<=\s)(?:--host|--port|-p)\s+\S+",
)


def load_yaml(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)


def canonical_json(obj):
    """Deterministic JSON: sorted keys, no whitespace ambiguity."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def normalize_command(command, quant=None):
    """Normalize a launch command for hashing.

    - strips --host/--port value args (serving topology, not identity)
    - collapses whitespace
    - if a quant is known, its literal occurrences become {quant}
    """
    cmd = _PORT_HOST_RE.sub("", command)
    cmd = re.sub(r"\s+", " ", cmd).strip()
    if quant:
        # Only replace whole-token-ish occurrences: bounded by non-word
        # chars or string edges, so Q8_0 in "Qwen3.8" never matches.
        pat = r"(?<![\w.])(?:" + re.escape(quant) + r")(?![\w])"
        cmd = re.sub(pat, "{quant}", cmd)
    return cmd


def hash_subset(recipe, field):
    subset_keys = HASH_SUBSETS[field]
    obj = recipe.get(field) or {}
    if field == "launch":
        command = obj.get("command", "")
        return {"command": normalize_command(command, recipe.get("quant"))}
    return {k: obj.get(k) for k in subset_keys}


def compute_content_hash(recipe, schema=None):
    """Hash only the reproducibility-relevant fields.

    Quant, size, environment versions, annotations, and docs NEVER change
    the hash, so recipes apply to a model, not a quant.
    """
    hashed_fields = (schema or {}).get("hashed_fields") or list(HASH_SUBSETS)
    subset = {f: hash_subset(recipe, f) for f in hashed_fields}
    digest = hashlib.sha256(canonical_json(subset).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def iter_recipe_files():
    if not RECIPES_DIR.exists():
        return
    for path in sorted(RECIPES_DIR.rglob("*.yaml")):
        yield path


def iter_result_files():
    if not RESULTS_DIR.exists():
        return
    for path in sorted(RESULTS_DIR.rglob("*.json")):
        yield path


def iter_test_definitions():
    if not DEFINITIONS_DIR.exists():
        return
    for path in sorted(DEFINITIONS_DIR.glob("*.json")):
        yield path


def load_schema(name):
    with open(SCHEMA_DIR / name, "r") as f:
        return json.load(f)
