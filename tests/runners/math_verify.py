#!/usr/bin/env python3
"""
math-verify — graded exact-answer arithmetic/reasoning test.

Eight integer-answer problems, each generated WITH its ground-truth
answer computed by the runner (stdlib only). Grades exact numeric
answers, so hallucination and quant-induced reasoning drift show as a
lower score. Deterministic given --seed.
"""
import argparse
import calendar
import math
import random
import re
import sys
from datetime import date, timedelta

sys.path.insert(0, __file__.rsplit("/", 2)[0])
import lib


def _problems(seed):
    rng = random.Random(seed)
    out = []
    # 1: sum of 1..n
    n = rng.randint(50, 500)
    out.append((f"Sum all integers from 1 to {n} inclusive.", n * (n + 1) // 2))
    # 2: lcm
    a, b = rng.randint(6, 40), rng.randint(6, 40)
    out.append((f"Least common multiple of {a} and {b}.", a * b // math.gcd(a, b)))
    # 3: missing number in 0..n
    n = rng.randint(10, 60)
    seq = list(range(n + 1))
    missing = rng.choice(seq)
    seq.remove(missing)
    rng.shuffle(seq)
    out.append((f"The list {seq} contains every integer from 0 to {n} "
                f"except one. Which is missing?", missing))
    # 4: count of primes <= n (sieve)
    n = rng.randint(20, 200)
    sieve = [True] * (n + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(n ** 0.5) + 1):
        if sieve[i]:
            for j in range(i * i, n + 1, i):
                sieve[j] = False
    out.append((f"How many prime numbers are there from 2 to {n} inclusive?",
                sum(sieve)))
    # 5: next multiple of k strictly greater than x
    k, x = rng.randint(5, 15), rng.randint(20, 200)
    out.append((f"The smallest multiple of {k} that is strictly greater "
                f"than {x}.", ((x // k) + 1) * k))
    # 6: product of digits
    n = rng.randint(100, 99999)
    prod = 1
    for ch in str(n):
        prod *= int(ch)
    out.append((f"Product of the digits of {n}.", prod))
    # 7: days between two dates
    d0 = date(2026, 1, rng.randint(1, 20))
    delta = rng.randint(10, 300)
    d1 = d0 + timedelta(days=delta)
    out.append((f"Exactly how many days are between {d0.isoformat()} and "
                f"{d1.isoformat()}?", delta))
    # 8: day count in a month
    y, m = 2024 + rng.randint(0, 2), rng.randint(1, 12)
    out.append((f"How many days are in {calendar.month_name[m]} {y}?",
                calendar.monthrange(y, m)[1]))
    return out


def main():
    ap = argparse.ArgumentParser()
    lib.add_args(ap)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    passed, obs = 0, []
    for q, ans in _problems(args.seed):
        messages = [
            {"role": "system", "content": "You solve problems exactly. After "
                                          "your final answer, write "
                                          "ANSWER=<integer> as the last line."},
            {"role": "user", "content": q},
        ]
        try:
            resp, _ = lib.chat(args.endpoint, args.model, messages,
                               max_tokens=768, temperature=0.0, timeout=300)
            text = lib.result_text(resp)
        except Exception as e:
            obs.append(f"FAIL {q[:40]}… (request error: {e})")
            continue
        # prefer explicit ANSWER= line; else the LAST integer in the text
        m = re.search(r"ANSWER\s*=\s*(-?\d+)", text, re.I)
        if not m:
            nums = re.findall(r"-?\d[\d,]*", text.replace(",", ""))
            m = re.search(r"(-?\d+)", nums[-1]) if nums else None
        got = int(m.group(1)) if m else None
        ok = got == ans
        passed += ok
        obs.append(f"{'PASS' if ok else 'FAIL'} {q[:44]}… "
                   f"(got {got}, want {ans}; tail: …{text.strip()[-60:]!r})")

    score = passed / 8
    lib.emit("pass" if score >= 0.875 else ("degraded" if score >= 0.5
                                            else "fail"),
             score=score,
             metrics={"tasks_passed": passed, "tasks_total": 8},
             observations=obs,
             detail=f"{passed}/8 problems answered exactly")
    return 0 if score >= 0.5 else 1


if __name__ == "__main__":
    sys.exit(main())
