# Qwen3 Coder 30B A3B Instruct Heretic (`qwen3-coder-30b`)

- Latest version: **v0.1.0** · Q4_K_M · 17.3 GB · arch qwen3moe · engine vulkan
- Source: /home/ubermensch/Desktop/AI/llama/models
- Verdict: 1 witness — 1 result(s) across 1 variant(s); 1 witness(es) at the current hash
- Confirmed capabilities: tools=False, mcp=False, vision=False · objectives: —

## Variants (configurations tested)

Each variant = a content hash (pinned launch configuration) with its own evidence trail. Quants are a dimension under a configuration.

| hash | v | quant(s) | PP t/s | TG t/s | wit | results | tests (pass/total) |
|---|---|---|---|---|---|---|---|
| `b88c64` | v0.1.0 | Q4_K_M | 67830.7 | 62.7 | 1 | 1 | throughput 1/1; tool-roundtrip 1/1 |

## Runs

| run (UTC) | contributor | quant | hash | PP | TG | tests |
|---|---|---|---|---|---|---|
| 20261108T1028 | ubermensch | Q4_K_M | `b88c64` | 67830.7 | 62.7 | tool-roundtrip=pass; throughput=pass |

### Sources & notes

- 20261108T1028Z — 64k context with Q8_0/Q4_0 Asym KV on Strix Halo Radeon 8060S
