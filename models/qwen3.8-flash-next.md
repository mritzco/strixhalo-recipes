# Qwen3.8 Flash Next (`qwen3.8-flash-next`)

- Latest version: **v0.1.0** · UD-IQ4_XS · 87.25 GB · arch qwen4exp · engine vulkan
- Source: /home/itzco/models/Qwen3.8-Flash-Next-GGUF/UD-IQ4_XS
- Verdict: 1 witness — 1 result(s) across 1 variant(s); 1 witness(es) at the current hash
- Confirmed capabilities: tools=True, mcp=False, vision=False · objectives: agent_capability, throughput

## Variants (configurations tested)

Each variant = a content hash (pinned launch configuration) with its own evidence trail. Quants are a dimension under a configuration.

| hash | v | quant(s) | PP t/s | TG t/s | wit | results | tests (pass/total) |
|---|---|---|---|---|---|---|---|
| `5ad673` | v0.1.0 | UD-IQ4_XS | 1468.8 | 10.6 | 1 | 1 | agent-coding 1/1; context-recall 1/1; throughput 1/1; tool-roundtrip 1/1 |

## Runs

| run (UTC) | contributor | quant | hash | PP | TG | tests |
|---|---|---|---|---|---|---|
| 20260907T1453 | flash-pilot | UD-IQ4_XS | `5ad673` | 1468.8 | 10.6 | tool-roundtrip=pass; agent-coding=pass; throughput=pass; context-recall=pass |

### Sources & notes

- 20260907T1453Z — mainline llama.cpp b10809 Vulkan distro pkg (commit 5266f24da7) UD-IQ4_XS 87.25GB @ HF rev 38bb39ee; NO MTP sidecar, NO Nathan fork. Receipt headline 40 t/s decode was fork+MTP; this run: server-side steady decode ~20-22 t/s (llama-server eval timing), runner TG mean 10.6 t/s contaminated by one cold-PP round (37.4s); cold prompt eval 10947 tok = 320 t/s (llama-server timing); runner tokens_per_sec_pp=1468.8 is a prefix-cache artifact (identical sys prompt warmed in slot; not cold PP). Reasoning flags active (effort medium, budget 2048): at 64-token cap completions burn on reasoning (finish=length) — reasoning-flag effect on short outputs; agent sessions with content budget unaffected. Compare honestly vs reddit 1w6cf5t fork numbers.
