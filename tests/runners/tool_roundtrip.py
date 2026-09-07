#!/usr/bin/env python3
"""
tool-roundtrip — prove the server parses tool calls (--jinja) into
structured tool_calls. Sends a prompt that MUST trigger the declared
tool; passes only on a well-formed tool_calls response with valid JSON
arguments. This is the server-level test; harness-level (pi/omp) tool
use is covered by harness-tool-use.

Exit 0 on pass; the JSON evidence record is the only stdout.
"""
import argparse
import json
import sys
import urllib.error

sys.path.insert(0, __file__.rsplit("/", 2)[0])
import lib

TOOL = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get the current weather in a city.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name"},
            },
            "required": ["city"],
        },
    },
}


def main():
    ap = argparse.ArgumentParser()
    lib.add_args(ap)
    ap.add_argument("--city", default="Berlin")
    args = ap.parse_args()

    messages = [
        {"role": "system", "content": "You are a helpful assistant with access to tools."},
        {"role": "user", "content": f"What is the weather in {args.city}? "
                                    "Use the get_weather tool."},
    ]
    observations, metrics = [], {}

    try:
        resp, dt = lib.chat(args.endpoint, args.model, messages,
                            tools=[TOOL], max_tokens=args.max_tokens,
                            timeout=args.timeout)
    except Exception as e:
        if isinstance(e, urllib.error.HTTPError) and e.code in (400, 422):
            lib.emit("fail", observations=[
                "tool-call request rejected by server"], detail=str(e))
            return 1
        lib.emit("inconclusive", observations=["request failed"], detail=str(e))
        return 2

    msg = (resp.get("choices") or [{}])[0].get("message", {})
    calls = msg.get("tool_calls") or []
    metrics["tool_calls"] = len(calls)
    metrics["latency_s"] = round(dt, 2)

    if not calls:
        text = (msg.get("content") or "")[:200]
        lib.emit("fail", metrics=metrics, observations=[
            "no tool_calls in response — model answered in plain text "
            "(server missing --jinja or model not tool-capable).",
            f"reply preview: {text}"])
        return 1

    ok = 0
    for c in calls:
        fn = c.get("function", {})
        name, args_txt = fn.get("name", ""), fn.get("arguments", "")
        try:
            parsed = json.loads(args_txt) if isinstance(args_txt, str) else args_txt
            good = (name == "get_weather" and isinstance(parsed, dict)
                    and "city" in parsed)
        except json.JSONDecodeError:
            good = False
        ok += good
    observations.append(f"{ok}/{len(calls)} tool call(s) well-formed")
    if ok == len(calls):
        lib.emit("pass", metrics=metrics, observations=observations)
        return 0
    lib.emit("fail", metrics=metrics, observations=observations,
             detail="one or more tool_calls malformed (bad name or "
                    "unparseable arguments)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
