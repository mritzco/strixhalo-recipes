#!/usr/bin/env python3
"""
context-recall — needle-in-haystack over the chat API. Inserts a secret
token into a filler document at a given depth and asks for it. Proves
long-context retrieval actually works at the declared ctx (KV cache
quality is recipe-parameter-dependent — this is the evidence test for
cache-type-k/v annotations).

Usage: context_needle.py [--ctx 4096] [--needle-at 0.5] [--needle "SECRET"]
Word count targets approx token count (conservative).
"""
import argparse
import random
import sys

sys.path.insert(0, __file__.rsplit("/", 2)[0])
import lib

FILLER = ("The history of paper mills in the province of Ontario is a "
          "rich and somewhat tedious subject involving many leases, "
          "water rights, and seasonal labor disputes that rarely "
          "produce memorable anecdotes worth repeating at dinner "
          "parties or formal gatherings of any kind whatsoever.")


def main():
    ap = argparse.ArgumentParser()
    lib.add_args(ap)
    ap.add_argument("--ctx", type=int, default=4096,
                    help="target context size in tokens (~1.4 words/token)")
    ap.add_argument("--needle-at", type=float, default=0.5)
    ap.add_argument("--needle", default="STRIX42")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    words_needed = max(50, int(args.ctx * 1.4))
    filler_words = FILLER.split()
    words = []
    while len(words) < words_needed:
        words += filler_words
    words = words[:words_needed]
    cut = max(1, int(len(words) * args.needle_at))
    needle_sentence = (f"Remember this: the secret code is "
                       f"{args.needle}. End of secret.")
    doc_words = words[:cut] + needle_sentence.split() + words[cut:]
    document = " ".join(doc_words)

    question = ("According to the document, what is the secret code? "
                "Answer with the code only.")
    messages = [
        {"role": "system", "content": "You extract facts from documents precisely."},
        {"role": "user", "content": f"Document:\n{document}\n\n{question}"},
    ]
    observations = [f"approx {args.ctx} token context, needle at ~{int(args.needle_at*100)}%"]

    try:
        resp, dt = lib.chat(args.endpoint, args.model, messages,
                            max_tokens=args.max_tokens, timeout=args.timeout)
    except Exception as e:
        lib.emit("inconclusive", observations=observations,
                 detail=f"request failed: {e}")
        return 2

    text = lib.result_text(resp)
    found = args.needle.lower() in text.lower()
    metrics = {"latency_s": round(dt, 2),
               "retrieved": bool(found),
               "context_tokens": args.ctx}
    observations.append(f"answer: {text[:120]}")
    if found:
        lib.emit("pass", metrics=metrics, observations=observations)
        return 0
    lib.emit("fail", metrics=metrics, observations=observations,
             detail="secret code not recovered at this context depth")
    return 1


if __name__ == "__main__":
    sys.exit(main())
