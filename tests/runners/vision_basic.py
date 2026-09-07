#!/usr/bin/env python3
"""
vision-basic — prove the endpoint handles image input through mmproj.
Sends a generated 256x256 PNG (left half red, right half white) and asks
the color of the left half. Passes when the answer names red.
unsupported when the server/model rejects image content (no mmproj).

Fixture is generated in-repo (no third-party assets) — CC0 clean.
"""
import argparse
import sys
import urllib.error

sys.path.insert(0, __file__.rsplit("/", 2)[0])
import lib


def main():
    ap = argparse.ArgumentParser()
    lib.add_args(ap)
    ap.add_argument("--image-text", default="What color is the LEFT half of this image? "
                                            "Answer with one word.")
    args = ap.parse_args()

    png = lib.make_test_png_bytes()
    messages = [
        {"role": "system", "content": "You are a careful vision assistant."},
        lib.image_content_message("user", args.image_text, png),
    ]
    observations = []

    try:
        resp, dt = lib.chat(args.endpoint, args.model, messages,
                            max_tokens=args.max_tokens, timeout=args.timeout)
    except urllib.error.HTTPError as e:
        if lib.is_multimodal_error(e):
            lib.emit("unsupported", observations=[
                "server/model rejected image input (no mmproj or "
                "non-multimodal model)"], detail=str(e))
            return 2
        lib.emit("inconclusive", observations=["HTTP error"], detail=str(e))
        return 2
    except Exception as e:
        lib.emit("inconclusive", observations=["request failed"], detail=str(e))
        return 2

    text = lib.result_text(resp).strip().lower()
    metrics = {"latency_s": round(dt, 2)}
    observations.append(f"model answer: {text[:120]}")
    if not text:
        lib.emit("fail", metrics=metrics, observations=observations,
                 detail="empty answer")
        return 1
    if "red" in text:
        lib.emit("pass", metrics=metrics, observations=observations)
        return 0
    lib.emit("fail", metrics=metrics, observations=observations,
             detail="answer did not identify the red half")
    return 1


if __name__ == "__main__":
    sys.exit(main())
