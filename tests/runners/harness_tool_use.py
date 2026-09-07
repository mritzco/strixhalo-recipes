#!/usr/bin/env python3
"""
harness-tool-use — exercise tool use through a REAL agent harness
(pi, omp/oh-my-pi) rather than the raw chat API. This is the only test
that proves the harness<->model tool loop end to end (e.g. omp's stream
parser vs GLM — a known breakage).

Contract: pass a one-shot harness CLI via --harness-cmd (or $HARNESS_CMD).
The command receives the prompt on stdin (or as $PROMPT) and must print
the assistant's final answer to stdout. The prompt asks the agent to use
its calculator/web-search tool; PASS requires the output to contain a
tool-generated fact line matching --expect-substr (default "42").

Without --harness-cmd the test reports not_run — honest: this machine's
harness integration is manual by design.
"""
import argparse
import os
import subprocess
import sys

sys.path.insert(0, __file__.rsplit("/", 2)[0])
import lib


def main():
    ap = argparse.ArgumentParser()
    lib.add_args(ap)
    ap.add_argument("--harness-cmd", default=os.environ.get("HARNESS_CMD"),
                    help="one-shot harness CLI, e.g. 'pi -p' or an omp wrapper")
    ap.add_argument("--expect-substr", default="42")
    args = ap.parse_args()

    if not args.harness_cmd:
        lib.emit("not_run", observations=[
            "no --harness-cmd/$HARNESS_CMD given — harness-level tool use "
            "not exercised; run manually per SKILL.md (pi: /model set to "
            "the recipe model; omp: lm-studio provider)."])
        return 0

    prompt = ("Use your calculator tool to compute 6 * 7 and report only "
              "the number you got from the tool.")
    try:
        proc = subprocess.run(args.harness_cmd, shell=True, input=prompt,
                              text=True, capture_output=True, timeout=args.timeout)
    except subprocess.TimeoutExpired:
        lib.emit("fail", observations=["harness timed out"])
        return 1

    out = (proc.stdout or "") + (proc.stderr or "")
    found = args.expect_substr in out
    observations = [f"harness exit={proc.returncode}",
                    f"output contains '{args.expect_substr}': {found}"]
    if found:
        lib.emit("pass", observations=observations)
        return 0
    lib.emit("fail", observations=observations,
             detail="tool result not observed in harness output")
    return 1


if __name__ == "__main__":
    sys.exit(main())
