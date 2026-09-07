#!/usr/bin/env python3
"""
throughput — measure generation tokens/sec over N chat requests at a
fixed output length. Also reports prompt-eval throughput by echoing a
large system prompt once. Stable across runs is a recipe property; the
leaderboard aggregates medians across witnesses.
"""
import argparse
import sys
import time

sys.path.insert(0, __file__.rsplit("/", 2)[0])
import lib


def main():
    ap = argparse.ArgumentParser()
    lib.add_args(ap)
    ap.add_argument("--n", type=int, default=3, help="generation rounds")
    ap.add_argument("--out-tokens", type=int, default=128)
    ap.add_argument("--pp-tokens", type=int, default=0,
                    help="if >0, one prompt-eval timing round with a "
                         "system prompt of ~this many tokens")
    args = ap.parse_args()

    observations = []
    tg_rates, latencies = [], []

    sys_prompt = ("You are a concise assistant. ")
    if args.pp_tokens > 0:
        filler = "knowledge nugget: " * (max(4, args.pp_tokens // 3))
        sys_prompt += filler

    for i in range(args.n):
        t0 = time.monotonic()
        try:
            resp, dt = lib.chat(
                args.endpoint, args.model,
                [{"role": "system", "content": sys_prompt},
                 {"role": "user", "content": "Count from one to twenty."}],
                max_tokens=args.out_tokens, temperature=0.0,
                timeout=args.timeout)
        except Exception as e:
            lib.emit("inconclusive",
                     observations=observations + [f"round {i+1} failed"],
                     detail=str(e))
            return 2
        dt = time.monotonic() - t0
        usage = resp.get("usage") or {}
        comp = usage.get("completion_tokens") or args.out_tokens
        rate = comp / dt if dt > 0 else 0.0
        tg_rates.append(rate)
        latencies.append(dt)

    metrics = {
        "tokens_per_sec_tg": round(sum(tg_rates) / len(tg_rates), 1),
        "median_round_s": round(sorted(latencies)[len(latencies) // 2], 2),
    }
    observations.append(f"{args.n} rounds x ~{args.out_tokens} out-tokens")

    if args.pp_tokens > 0:
        t0 = time.monotonic()
        try:
            resp, dt = lib.chat(
                args.endpoint, args.model,
                [{"role": "system", "content": sys_prompt},
                 {"role": "user", "content": "Reply with OK."}],
                max_tokens=8, timeout=args.timeout)
        except Exception as e:
            lib.emit("inconclusive", observations=observations,
                     detail=f"pp round failed: {e}")
            return 2
        dt = time.monotonic() - t0
        usage = resp.get("usage") or {}
        pp_tokens = (usage.get("prompt_tokens") or args.pp_tokens)
        metrics["tokens_per_sec_pp"] = round(pp_tokens / dt, 1) if dt > 0 else 0
        observations.append(f"prompt-eval round: ~{pp_tokens} tokens")

    lib.emit("pass", metrics=metrics, observations=observations)
    return 0


if __name__ == "__main__":
    sys.exit(main())
