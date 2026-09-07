#!/usr/bin/env python3
"""Shared helpers for test runners.

Contract: every runner prints EXACTLY ONE JSON document on stdout — the
test evidence record:
    {"status": pass|fail|degraded|unsupported|not_run|inconclusive,
     "score": float|null, "metrics": {...}, "observations": [...],
     "artifacts": [...], "detail": str|null}
Human-readable notes go to stderr. Callers (submit_result.py, humans)
parse stdout as JSON.

Endpoint contract: --endpoint or $LLAMA_ENDPOINT, default the llama-swap
endpoint http://127.0.0.1:1234/v1. Model id via --model or $LLAMA_MODEL.
"""
import argparse
import base64
import json
import os
import struct
import sys
import time
import urllib.error
import urllib.request
import zlib

DEFAULT_ENDPOINT = os.environ.get("LLAMA_ENDPOINT", "http://127.0.0.1:1234/v1")
DEFAULT_MODEL = os.environ.get("LLAMA_MODEL")


def add_args(ap):
    ap.add_argument("--endpoint", default=DEFAULT_ENDPOINT,
                    help=f"OpenAI-compatible base URL (default {DEFAULT_ENDPOINT})")
    ap.add_argument("--model", default=DEFAULT_MODEL,
                    help="model id (default: server default)")
    ap.add_argument("--max-tokens", type=int, default=512)
    ap.add_argument("--timeout", type=int, default=600)


def emit(status, score=None, metrics=None, observations=None,
         artifacts=None, detail=None):
    rec = {
        "status": status,
        "score": score,
        "metrics": metrics or {},
        "observations": observations or [],
        "artifacts": artifacts or [],
        "detail": detail,
    }
    json.dump(rec, sys.stdout)
    sys.stdout.write("\n")


def _post(endpoint, payload, timeout):
    url = endpoint.rstrip("/") + "/chat/completions"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def chat(endpoint, model, messages, tools=None, max_tokens=512,
         temperature=0.0, timeout=600, extra=None):
    """One chat completion. Raises urllib.error.HTTPError on API errors."""
    payload = {
        "model": model or "default",
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False,
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    if extra:
        payload.update(extra)
    t0 = time.monotonic()
    resp = _post(endpoint, payload, timeout)
    dt = time.monotonic() - t0
    return resp, dt


def is_multimodal_error(e):
    """HTTP error that indicates the server/model cannot take images."""
    body = ""
    try:
        body = e.read().decode("utf-8", errors="replace").lower()
    except Exception:
        pass
    msg = f"{e} {body}".lower()
    return any(k in msg for k in (
        "image", "vision", "multimodal", "mmproj", "invalid image",
        "unsupported content", "content type"))


# ---------------------------------------------------------------------------
# Tiny dependency-free PNG generator for vision tests. Draws a 256x256 image:
# left half solid red, right half solid white. No third-party assets, so the
# fixture is fully CC0 — no licensing wrinkle.
# ---------------------------------------------------------------------------
def _png_chunk(tag, data):
    c = struct.pack(">I", len(data)) + tag + data
    c += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    return c


def make_test_png_bytes():
    w, h = 256, 256
    raw = bytearray()
    for y in range(h):
        raw.append(0)  # filter: none
        for x in range(w):
            if x < w // 2:
                raw += bytes((230, 30, 30))      # red (left)
            else:
                raw += bytes((250, 250, 250))    # white (right)
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + _png_chunk(b"IHDR", ihdr)
            + _png_chunk(b"IDAT", zlib.compress(bytes(raw), 6))
            + _png_chunk(b"IEND", b""))


def image_content_message(role, text, png_bytes):
    """OpenAI-style message with an inline base64 image_url."""
    b64 = base64.b64encode(png_bytes).decode("ascii")
    return {
        "role": role,
        "content": [
            {"type": "text", "text": text},
            {"type": "image_url",
             "image_url": {"url": f"data:image/png;base64,{b64}"}},
        ],
    }


def result_text(resp):
    try:
        return resp["choices"][0]["message"]["content"] or ""
    except Exception:
        return ""


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    add_args(ap)
    args = ap.parse_args()
    emit("inconclusive", detail="lib.py is not a test — run a tests/runners/*.py script")
