#!/usr/bin/env python3
"""
agent-coding — multi-round coding-agent test through the chat API with
CLIENT-EXECUTED local tools in a sandbox repo.

Why this test exists: single tool round-trips and toy Q&A ("capital of
France") prove ~nothing about real agent work. This exercises the loop
that actually matters — the model inspects local files, plans, edits,
runs code, reacts to failures, and iterates — with context growing
across rounds through real tool results.

Tools exposed to the model (executed by this runner in a temp sandbox):
  read_file(path), write_file(path, content), run_python(code)

Acceptance: a planted bug (add() subtracts instead of adding) is fixed
in the sandbox AND `python main.py` prints 5 AND the model reports DONE.
"""
import argparse
import json
import os
import shutil
import sys
import tempfile
import urllib.error

sys.path.insert(0, __file__.rsplit("/", 2)[0])
import lib

TOOLS = [
    {"type": "function", "function": {
        "name": "read_file",
        "description": "Read a file from the sandbox repository.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "relative path, e.g. lib.py"}},
            "required": ["path"]}}},
    {"type": "function", "function": {
        "name": "write_file",
        "description": "Write a file in the sandbox repository (overwrites).",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string"},
            "content": {"type": "string", "description": "full file content"}},
            "required": ["path", "content"]}}},
    {"type": "function", "function": {
        "name": "run_python",
        "description": "Run python code in the sandbox repo (cwd = repo root). "
                       "Use to execute main.py or quick checks.",
        "parameters": {"type": "object", "properties": {
            "code": {"type": "string", "description": "python code to execute"}},
            "required": ["code"]}}},
]

MAIN_PY = "from lib import add\nprint(add(2, 3))\n"
LIB_PY = ("def add(a, b):\n"
          "    # TODO: returns the difference — the sum was intended\n"
          "    return a - b\n")


def _exec_tool(name, args, sandbox):
    if name == "read_file":
        p = os.path.join(sandbox, args.get("path", ""))
        try:
            with open(p) as f:
                return json.dumps({"ok": True, "content": f.read()})
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})
    if name == "write_file":
        p = os.path.join(sandbox, args.get("path", ""))
        try:
            with open(p, "w") as f:
                f.write(args.get("content", ""))
            return json.dumps({"ok": True})
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})
    if name == "run_python":
        import subprocess
        try:
            proc = subprocess.run(["python3", "-c", args.get("code", "")],
                                  cwd=sandbox, capture_output=True, text=True,
                                  timeout=30)
            return json.dumps({"ok": proc.returncode == 0, "rc": proc.returncode,
                               "stdout": proc.stdout[-2000:],
                               "stderr": proc.stderr[-2000:]})
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})
    return json.dumps({"ok": False, "error": f"unknown tool {name}"})


def main():
    ap = argparse.ArgumentParser()
    lib.add_args(ap)
    ap.add_argument("--max-rounds", type=int, default=10)
    args = ap.parse_args()

    sandbox = tempfile.mkdtemp(prefix="agent-coding-")
    with open(os.path.join(sandbox, "main.py"), "w") as f:
        f.write(MAIN_PY)
    with open(os.path.join(sandbox, "lib.py"), "w") as f:
        f.write(LIB_PY)

    messages = [
        {"role": "system", "content": "You are a coding agent working in a "
         f"local sandbox repo at {sandbox}. Use the provided tools to "
         "inspect files, edit them, and run code. Never guess file "
         "contents — read them first."},
        {"role": "user", "content": "There is a bug: running main.py prints "
         "the wrong number. Inspect the repo, fix lib.py so that add(2, 3) "
         "returns the sum, verify by running main.py (expected output: 5), "
         "then reply with exactly DONE."},
    ]
    observations, metrics = [], {}
    rounds, tool_calls = 0, 0

    try:
        while rounds < args.max_rounds:
            rounds += 1
            resp, dt = lib.chat(args.endpoint, args.model, messages,
                                tools=TOOLS, max_tokens=512,
                                timeout=args.timeout)
            msg = (resp.get("choices") or [{}])[0].get("message", {})
            calls = msg.get("tool_calls") or []
            if not calls:
                observations.append(f"final reply (round {rounds}): "
                                    f"{(msg.get('content') or '').strip()[:80]}")
                break
            messages.append({"role": "assistant", "content": msg.get("content"),
                             "tool_calls": calls})
            for c in calls:
                tool_calls += 1
                fn = c.get("function", {})
                try:
                    targs = json.loads(fn.get("arguments") or "{}")
                except json.JSONDecodeError:
                    targs = {}
                out = _exec_tool(fn.get("name", ""), targs, sandbox)
                messages.append({"role": "tool", "tool_call_id": c.get("id"),
                                 "content": out})
        else:
            observations.append(f"reached --max-rounds {args.max_rounds} "
                                "without the model stopping")
    except urllib.error.HTTPError as e:
        lib.emit("inconclusive", observations=observations + ["HTTP error"],
                 detail=str(e))
        return 2
    except Exception as e:
        lib.emit("inconclusive", observations=observations,
                 detail=f"request failed: {e}")
        return 2

    # ground truth check
    import subprocess
    proc = subprocess.run(["python3", "main.py"], cwd=sandbox,
                          capture_output=True, text=True, timeout=30)
    fixed = proc.stdout.strip() == "5"
    metrics = {"rounds": rounds, "tool_calls": tool_calls, "fixed": fixed}
    observations.append(f"ground truth: main.py prints "
                        f"{proc.stdout.strip()!r} (want '5')")

    shutil.rmtree(sandbox, ignore_errors=True)
    if fixed and tool_calls > 0:
        lib.emit("pass", metrics=metrics, observations=observations)
        return 0
    lib.emit("fail", metrics=metrics, observations=observations,
             detail="ground truth check failed (bug not fixed via tools)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
