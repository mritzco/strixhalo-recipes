#!/usr/bin/env python3
"""
code-battery — graded functional-correctness test for coding ability.

Eight original, self-written Python tasks (no third-party benchmark text,
so the fixtures are CC0-clean). The model writes one function per spec;
the grader executes each candidate against hidden unit tests in an
isolated subprocess. Score = tasks passed / total — the dimension that
separates 'fast but inaccurate' quants from usable ones.

Requires a coding-capable endpoint. Deterministic at temperature 0.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, __file__.rsplit("/", 2)[0])
import lib

# (spec, test-snippet) pairs — reference solutions verified independently
TASKS = [
    ("Implement rotate(lst, k): return the list rotated RIGHT by k steps "
     "(k >= 0; k may exceed len(lst)).",
     "assert rotate([1,2,3,4,5], 2) == [4,5,1,2,3]\n"
     "assert rotate([1,2,3], 5) == [2,3,1]\n"
     "assert rotate([], 3) == []\n"
     "assert rotate([7], 0) == [7]\n"),
    ("Implement is_pal(s): True if s is a palindrome ignoring case and "
     "non-alphanumeric characters.",
     "assert is_pal('A man, a plan, a canal: Panama') is True\n"
     "assert is_pal('race a car') is False\n"
     "assert is_pal('') is True\n"
     "assert is_pal('No lemon, no melon') is True\n"),
    ("Implement most_frequent(words): return the word with the highest "
     "count; ties break toward the word that appears FIRST in the list.",
     "assert most_frequent(['a','b','a','c','b']) == 'a'\n"
     "assert most_frequent(['x']) == 'x'\n"
     "assert most_frequent(['b','a','b','a']) == 'b'\n"
     "assert most_frequent([]) is None\n"),
    ("Implement fib(n): return the n-th Fibonacci number, 0-indexed "
     "(fib(0)=0, fib(1)=1). n <= 30.",
     "assert fib(0) == 0\nassert fib(1) == 1\nassert fib(10) == 55\n"
     "assert fib(20) == 6765\nassert fib(30) == 832040\n"),
    ("Implement transpose(mat): return the transpose of a rectangular "
     "list-of-lists matrix (rows -> columns).",
     "assert transpose([[1,2,3],[4,5,6]]) == [[1,4],[2,5],[3,6]]\n"
     "assert transpose([[1]]) == [[1]]\n"
     "assert transpose([]) == []\n"
     "assert transpose([[1,2],[3,4],[5,6]]) == [[1,3,5],[2,4,6]]\n"),
    ("Implement digital_root(n): repeatedly sum the digits of n until a "
     "single digit remains (n >= 0).",
     "assert digital_root(9875) == 2\nassert digital_root(0) == 0\n"
     "assert digital_root(9) == 9\nassert digital_root(199) == 1\n"
     "assert digital_root(123456789) == 9\n"),
    ("Implement caesar(s, shift): shift only ASCII letters by shift "
     "positions, preserving case; leave everything else unchanged.",
     "assert caesar('abc XYZ', 1) == 'bcd YZA'\n"
     "assert caesar('Hello!', 3) == 'Khoor!'\n"
     "assert caesar('abc', -1) == 'zab'\n"
     "assert caesar('a1b', 26) == 'a1b'\n"),
    ("Implement unique_keep_order(seq): return a new list with duplicates "
     "removed, keeping FIRST occurrence order.",
     "assert unique_keep_order([3,1,3,2,1,3]) == [3,1,2]\n"
     "assert unique_keep_order([]) == []\n"
     "assert unique_keep_order(['a','a']) == ['a']\n"
     "assert unique_keep_order([1,2,3]) == [1,2,3]\n"),
]


def _extract_code(text):
    fences = re.findall(r"```(?:python)?\s*(.*?)```", text, re.S)
    if fences:
        return max(fences, key=len).strip()
    # last def block heuristic: strip trailing prose after the final newline
    idx = text.rfind("\ndef ")
    if idx >= 0:
        return text[idx:].strip()
    return text.strip()


def _run_one(task_idx, spec, tests):
    with tempfile.TemporaryDirectory(prefix="codebat-") as d:
        q = ("Write a Python function matching this spec. Return ONLY the "
             f"code, no markdown fences, no explanation.\n\nSpec: {spec}")
        messages = [
            {"role": "system", "content": "You are a precise Python engineer."},
            {"role": "user", "content": q},
        ]
        resp, dt = lib.chat(lib_ep, model, messages, max_tokens=600,
                            temperature=0.0, timeout=600)
        code = _extract_code(lib.result_text(resp))
        path = os.path.join(d, "sol.py")
        with open(path, "w") as f:
            f.write(code + "\n")
        test_path = os.path.join(d, "test.py")
        with open(test_path, "w") as f:
            f.write("import sys; sys.path.insert(0, '.')\nfrom sol import *\n"
                    + tests)
        try:
            proc = subprocess.run([sys.executable, test_path],
                                  capture_output=True, text=True,
                                  timeout=20, cwd=d)
            ok = proc.returncode == 0
            err = (proc.stderr or "")[-300:]
        except subprocess.TimeoutExpired:
            ok, err = False, "timeout"
        return ok, dt, err[:200]


def main():
    ap = argparse.ArgumentParser()
    lib.add_args(ap)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    global lib_ep, model
    lib_ep, model = args.endpoint, args.model

    results, obs, total = [], [], 0.0
    for i, (spec, tests) in enumerate(TASKS):
        ok, dt, err = _run_one(i, spec, tests)
        results.append(ok)
        total += ok
        obs.append(f"task{i+1}: {'PASS' if ok else 'FAIL'}"
                   + (f" ({err.strip()})" if not ok and err else ""))
    score = total / len(TASKS)
    lib.emit(
        "pass" if score >= 0.9 else ("degraded" if score >= 0.5 else "fail"),
        score=score,
        metrics={"tasks_passed": int(total), "tasks_total": len(TASKS)},
        observations=obs,
        detail=f"{int(total)}/{len(TASKS)} tasks passed")
    return 0 if score >= 0.5 else 1


if __name__ == "__main__":
    sys.exit(main())
