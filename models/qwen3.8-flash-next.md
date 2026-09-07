# Qwen3.8 Flash Next (`qwen3.8-flash-next`)

- Latest version: **v0.2.0** · UD-IQ4_XS · 87.25 GB · arch qwen4exp · engine vulkan
- Source: /home/itzco/models/Qwen3.8-Flash-Next-GGUF/UD-IQ4_XS
- Verdict: 1 witness — 4 result(s) across 2 variant(s); 2 witness(es) at the current hash
- Confirmed capabilities: tools=True, mcp=False, vision=False · objectives: throughput, agent_capability

## Variants (configurations tested)

Each variant = a content hash (pinned launch configuration) with its own evidence trail. Quants are a dimension under a configuration.

| hash | v | quant(s) | PP t/s | TG t/s | wit | results | tests (pass/total) |
|---|---|---|---|---|---|---|---|
| `5ad673` | v0.1.0 | UD-IQ4_XS | 1468.8 | 10.6 | 2 | 2 | agent-coding 1/1; code-battery 0/1; context-recall 1/1; math-verify 0/1; throughput 1/1; tool-roundtrip 1/1 |
| `e99277` | v0.2.0 | UD-IQ4_XS | 1798.1 | 18.0 | 2 | 2 | agent-coding 1/1; code-battery 0/1; context-recall 1/1; math-verify 0/1; throughput 1/1; tool-roundtrip 1/1 |

## Runs

| run (UTC) | contributor | quant | hash | PP | TG | tests |
|---|---|---|---|---|---|---|
| 20260907T1453 | flash-pilot | UD-IQ4_XS | `5ad673` | 1468.8 | 10.6 | tool-roundtrip=pass; agent-coding=pass; throughput=pass; context-recall=pass |
| 20260907T1536 | nathan-fork-pilot | UD-IQ4_XS | `e99277` | 1798.1 | 18.0 | tool-roundtrip=pass; agent-coding=pass; throughput=pass; context-recall=pass |
| 20260907T1609 | quality-pilot | UD-IQ4_XS | `5ad673` | - | - | code-battery=degraded; math-verify=degraded |
| 20260907T1609 | quality-pilot | UD-IQ4_XS | `e99277` | - | - | code-battery=degraded; math-verify=degraded |

### Sources & notes

- 20260907T1453Z — mainline llama.cpp b10809 Vulkan distro pkg (commit 5266f24da7) UD-IQ4_XS 87.25GB @ HF rev 38bb39ee; NO MTP sidecar, NO Nathan fork. Receipt headline 40 t/s decode was fork+MTP; this run: server-side steady decode ~20-22 t/s (llama-server eval timing), runner TG mean 10.6 t/s contaminated by one cold-PP round (37.4s); cold prompt eval 10947 tok = 320 t/s (llama-server timing); runner tokens_per_sec_pp=1468.8 is a prefix-cache artifact (identical sys prompt warmed in slot; not cold PP). Reasoning flags active (effort medium, budget 2048): at 64-token cap completions burn on reasoning (finish=length) — reasoning-flag effect on short outputs; agent sessions with content budget unaffected. Compare honestly vs reddit 1w6cf5t fork numbers.
- 20260907T1536Z — Nathan strix-halo-vulkan fork commit 5d8c07b44 built from source (GGML_VULKAN, host Mesa radv) + agentionai MTP Q8_0 sidecar fixed n4, port 8098. Fork=prefill, MTP=decode (attribution separate). COLD PP @10947 tok server-eval: 383.8 t/s vs v0.1.0 mainline 320 t/s (+20%, fork FA dequant-once + mmid rowlists). Server-eval decode on battery traffic (temp 0, structured/code/tool 64-tok rounds): 29.1-44.0 t/s per request, mean ~35 t/s (>=50-tok lines), vs v0.1.0 19.4-22.9 t/s -> ~1.6-1.8x (MTP). MTP acceptance content-dependent: structured 0.73-1.00 (deterministic count-gen 52.1 t/s at acc 1.0); open-ended prose 0.39-0.55 -> ~18-25 t/s (draft-head greedy agreement collapses on flat creative distributions; receipts' 40 t/s headline was code-emission traffic, their reasoning-heavy band 24-31). Runner metrics: tg 18.0 t/s mean (contaminated by one cold 10947-tok PP round at 30.4s, same artifact as v0.1.0's 10.6/37.4s); runner tokens_per_sec_pp 1798.1 is prefix-cache artifact (warm sys prompt), NOT cold PP. agent-coding pass 3 rounds (v0.1.0: 4), tool-roundtrip pass latency 3.05s (v0.1.0 4.75s), context-recall pass STRIX42@4096. Identity sane (Qwen/Tongyi, no leak). Probe backend block reflects the untouched distro /usr/bin/llama-server b10809 (machine reference); the recipe backend pins the fork. Full server log: /tmp/mtp.log; per-request parse: /tmp/mtp-server-timing.json; sanity: /tmp/mtp-sanity.json.
- 20260907T1609Z — quality baseline, mainline b10809, ctx 8192 for these runs (recipe ctx 32768); math-verify 3 fails = thinking-token truncation (reasoning-effort medium server vs 768-token cap), not math errors — see observations
- 20260907T1609Z — quality A/B, Nathan fork + MTP, ctx 8192; IDENTICAL scores to mainline (7/8 code incl same task-3 edge, 5/8 math) — speed 1.6-1.8x at same quality; same truncation artifact on math

### Lineage

- **qwen3.8-flash-next v0.1.0** — Nathan fork + MTP sidecar: fork prefill fixes + MTP decode (mainline cannot load standalone MTP head)
- Rationale: v0.1.0 was the honest mainline (b10809, no MTP) baseline. v0.2.0 swaps the engine to Nathan's strix-halo-vulkan fork built from source and adds the Q8_0 MTP sidecar draft head (-md --spec-type draft-mtp, fixed n4) — the receipt-validated arrangement that mainline b10809 could not load ('output_hc_norm.weight not found'; MTP sidecar support is fork-only, upstream PR #28243 unmerged).
