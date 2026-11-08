# Gpt Oss 20b Heretic v2 (`gpt-oss-20b`)

- Latest version: **v0.1.0** · ? · 11.3 GB · arch gpt-oss · engine vulkan
- Source: /home/ubermensch/Desktop/AI/llama/models
- Verdict: 1 witness — 1 result(s) across 1 variant(s); 1 witness(es) at the current hash
- Confirmed capabilities: tools=False, mcp=False, vision=False · objectives: —

## Variants (configurations tested)

Each variant = a content hash (pinned launch configuration) with its own evidence trail. Quants are a dimension under a configuration.

| hash | v | quant(s) | PP t/s | TG t/s | wit | results | tests (pass/total) |
|---|---|---|---|---|---|---|---|
| `c401aa` | v0.1.0 | None | 49711.7 | 116.0 | 1 | 1 | throughput 1/1; tool-roundtrip 1/1 |

## Runs

| run (UTC) | contributor | quant | hash | PP | TG | tests |
|---|---|---|---|---|---|---|
| 20261108T1026 | ubermensch | - | `c401aa` | 49711.7 | 116.0 | tool-roundtrip=pass; throughput=pass |

### Sources & notes

- 20261108T1026Z — Unconstrained 128k native context with FP16 KV on Strix Halo Radeon 8060S
