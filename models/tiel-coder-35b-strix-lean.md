# Tiel-Coder-35B-A3B (`tiel-coder-35b-strix-lean`)

- Latest version: **v0.1.0** · Q4_0 · 17.5 GB · arch qwen35moe · engine vulkan
- Source: https://huggingface.co/charlie12345
- Verdict: 1 witness — 1 result(s) across 1 variant(s); 1 witness(es) at the current hash
- Confirmed capabilities: tools=True, mcp=True, vision=False · objectives: tool_calling, code_generation, throughput

## Variants (configurations tested)

Each variant = a content hash (pinned launch configuration) with its own evidence trail. Quants are a dimension under a configuration.

| hash | v | quant(s) | PP t/s | TG t/s | wit | results | tests (pass/total) |
|---|---|---|---|---|---|---|---|
| `07f3a0` | v0.1.0 | Q4_0 | 1002.8 | 66.0 | 1 | 1 | agent-coding 1/1; context-recall 1/1; throughput 1/1; tool-roundtrip 1/1 |

## Runs

| run (UTC) | contributor | quant | hash | PP | TG | tests |
|---|---|---|---|---|---|---|
| 20261108T1542 | ubermensch | Q4_0 | `07f3a0` | 1002.8 | 66.0 | tool-roundtrip=pass; throughput=pass; agent-coding=pass; context-recall=pass |

### Sources & notes

- 20261108T1542Z — Tiel-Coder-35B-A3B Strix Lean ROCmFP4 kernel running via isolated Vulkan runner on AMD Radeon 8060S with native Wave64 compute shaders
