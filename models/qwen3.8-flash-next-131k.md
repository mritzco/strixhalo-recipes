# Qwen3.8 Flash Next (`qwen3.8-flash-next-131k`)

- Latest version: **v0.1.0** · IQ4_XS · 0.0 GB · arch qwen4exp · engine vulkan
- Source: /home/itzco/models/Qwen3.8-Flash-Next-GGUF/UD-IQ4_XS
- Verdict: 1 witness — 1 result(s) across 1 variant(s); 1 witness(es) at the current hash
- Confirmed capabilities: tools=False, mcp=False, vision=False · objectives: —

## Variants (configurations tested)

Each variant = a content hash (pinned launch configuration) with its own evidence trail. Quants are a dimension under a configuration.

| hash | v | quant(s) | PP t/s | TG t/s | wit | results | tests (pass/total) |
|---|---|---|---|---|---|---|---|
| `0b714b` | v0.1.0 | IQ4_XS | 1290.5 | 11.0 | 1 | 1 | agent-coding 1/1; context-recall 1/1; throughput 1/1; tool-roundtrip 1/1 |

## Runs

| run (UTC) | contributor | quant | hash | PP | TG | tests |
|---|---|---|---|---|---|---|
| 20260908T1108 | flash-pilot | IQ4_XS | `0b714b` | 1290.5 | 11.0 | tool-roundtrip=pass; throughput=pass; agent-coding=pass; context-recall=pass |

### Sources & notes

- 20260908T1108Z — 131k ctx variant, cold load ~25s. Runner TG 11.0 contaminated by cold 11k-token PP round (known artifact); llama-swap UI field stats from real omp session at 30-51k ctx: decode 14.6-18.4 t/s sustained. context-recall @8k pass.
