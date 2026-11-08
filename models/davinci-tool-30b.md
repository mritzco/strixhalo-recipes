# Davinci Tool 30B (`davinci-tool-30b`)

- Latest version: **v0.1.0** · Q4_K_M · 17.3 GB · arch qwen3moe · engine vulkan
- Source: /home/ubermensch/Desktop/AI/llama/models
- Verdict: 1 witness — 1 result(s) across 1 variant(s); 1 witness(es) at the current hash
- Confirmed capabilities: tools=False, mcp=False, vision=False · objectives: —

## Variants (configurations tested)

Each variant = a content hash (pinned launch configuration) with its own evidence trail. Quants are a dimension under a configuration.

| hash | v | quant(s) | PP t/s | TG t/s | wit | results | tests (pass/total) |
|---|---|---|---|---|---|---|---|
| `298328` | v0.1.0 | Q4_K_M | 63695.9 | 50.2 | 1 | 1 | throughput 1/1; tool-roundtrip 1/1 |

## Runs

| run (UTC) | contributor | quant | hash | PP | TG | tests |
|---|---|---|---|---|---|---|
| 20261108T1027 | ubermensch | Q4_K_M | `298328` | 63695.9 | 50.2 | tool-roundtrip=pass; throughput=pass |

### Sources & notes

- 20261108T1027Z — 64k context with Q8_0/Q4_0 Asym KV on Strix Halo Radeon 8060S
