#!/usr/bin/env python3
"""
Validate every recipe, result, and test definition in the repo.

Recipes:
  1. JSON Schema validity against schema/recipe.schema.json
  2. content_hash matches a recomputed hash over the reproducibility
     fields (quant-agnostic — quant/size/docs never affect the hash)
  3. lineage.parents reference recipe ids that exist in the repo
  4. status: failed has failure_notes
  5. (warning) declared tests[] reference ids that exist under
     tests/definitions/

Results:
  1. JSON Schema validity against schema/result.schema.json
  2. recipe_id + content_hash match an existing recipe file
  3. run_id unique across the results/ tree
  4. every test id referenced exists under tests/definitions/

Test definitions:
  1. JSON Schema validity against schema/test-definition.schema.json

Exit code non-zero if any hard error found (--strict also fails on
warnings).
"""
import argparse
import sys

import jsonschema

from common import (
    compute_content_hash,
    iter_recipe_files,
    iter_result_files,
    iter_test_definitions,
    load_schema,
    load_yaml,
)


def validate_recipes(strict):
    schema = load_schema("recipe.schema.json")
    test_ids = {d["id"] for d in load_test_definitions()[0]}
    errors, warnings, recipes = [], [], []

    for path in iter_recipe_files():
        rel = str(path)
        try:
            recipe = load_yaml(path)
        except Exception as e:
            errors.append(f"{rel}: unparseable YAML: {e}")
            continue
        try:
            jsonschema.validate(recipe, schema)
        except jsonschema.ValidationError as e:
            errors.append(f"{rel}: schema error: {e.message}")
            continue
        recipes.append(recipe)

    # Semantic checks after all recipes are parsed (order-independent).
    all_ids = {r.get("id") for r in recipes}
    for rel_recipe, recipe in zip(iter_recipe_files(), recipes):
        rel = str(rel_recipe)
        recomputed = compute_content_hash(recipe, schema)
        if recipe.get("content_hash") != recomputed:
            errors.append(
                f"{rel}: content_hash mismatch — declared "
                f"{recipe.get('content_hash')}, computed {recomputed}. "
                "Run tools/collect.py or fix manually (quant/size/docs do "
                "NOT change the hash)."
            )
        if recipe.get("status") == "failed" and not recipe.get("failure_notes"):
            errors.append(f"{rel}: status failed requires failure_notes")
        for parent in recipe.get("lineage", {}).get("parents", []):
            if parent.get("id") and parent.get("id") not in all_ids:
                errors.append(
                    f"{rel}: lineage parent id '{parent.get('id')}' not found in recipes/"
                )
        for t in recipe.get("tests", []):
            if t.get("id") not in test_ids:
                warnings.append(f"{rel}: tests[] references unknown test id '{t.get('id')}'")

    return errors, warnings, recipes


def validate_results(strict, recipes):
    schema = load_schema("result.schema.json")
    test_ids = {d["id"] for d in load_test_definitions()[0]}
    errors, warnings = [], []
    seen_run_ids = {}

    recipe_index = {}
    for r in recipes:
        recipe_index[(r["id"], r.get("content_hash"))] = r

    for path in iter_result_files():
        rel = str(path)
        try:
            res = load_yaml(path)
        except Exception as e:
            errors.append(f"{rel}: unparseable JSON: {e}")
            continue
        try:
            jsonschema.validate(res, schema)
        except jsonschema.ValidationError as e:
            errors.append(f"{rel}: schema error: {e.message}")
            continue

        key = (res.get("recipe_id"), res.get("content_hash"))
        if key not in recipe_index:
            errors.append(
                f"{rel}: no recipe {key[0]} with content_hash {key[1]} in recipes/"
            )
        run_id = res.get("run_id")
        if run_id in seen_run_ids:
            errors.append(
                f"{rel}: run_id {run_id} duplicates {seen_run_ids[run_id]}"
            )
        seen_run_ids[run_id] = rel

        for t in res.get("tests", []):
            if t.get("id") not in test_ids:
                errors.append(
                    f"{rel}: test '{t.get('id')}' not found under tests/definitions/"
                )
            if t.get("result") not in (
                "pass", "fail", "degraded", "unsupported", "not_run", "inconclusive"
            ):
                errors.append(f"{rel}: invalid test result '{t.get('result')}'")

    return errors, warnings


def load_test_definitions():
    schema = load_schema("test-definition.schema.json")
    errors, defs = [], []
    for path in iter_test_definitions():
        try:
            d = load_yaml(path)
            jsonschema.validate(d, schema)
            defs.append(d)
        except Exception as e:
            errors.append(f"{path}: {e}")
    return defs, errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true",
                    help="fail on warnings too")
    args = ap.parse_args()

    all_errors, all_warnings = [], []
    r_errors, r_warnings, recipes = validate_recipes(args.strict)
    all_errors += r_errors
    all_warnings += r_warnings

    rs_errors, rs_warnings = validate_results(args.strict, recipes)
    all_errors += rs_errors
    all_warnings += rs_warnings

    td_defs, td_errors = load_test_definitions()
    all_errors += td_errors

    for e in all_errors:
        print(f"ERROR {e}")
    for w in all_warnings:
        print(f"WARNING {w}")
    n_recipes = len(recipes)
    n_results = sum(1 for _ in iter_result_files())
    print(f"\n{len(td_defs)} test definition(s), {n_recipes} recipe(s), "
          f"{n_results} result(s) checked, {len(all_errors)} error(s), "
          f"{len(all_warnings)} warning(s).")

    if all_errors:
        sys.exit(1)
    if args.strict and all_warnings:
        sys.exit(1)


if __name__ == "__main__":
    main()
