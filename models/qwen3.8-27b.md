# Qwen3.8-27B (`qwen3.8-27b`)

- Latest version: **v0.1.0** · Q8_0 · 27.1 GB · arch qwen35 · engine vulkan
- Source: /home/itzco/models/Qwen3.8-27B-GGUF
- Verdict: 1 witness — 1 result(s) across 1 variant(s); 1 witness(es) at the current hash: itzco
- Confirmed capabilities: tools=True, mcp=False, vision=False · objectives: agent_capability, context_reliability

## Variants (configurations tested)

Each variant = a content hash (pinned launch configuration) with its own evidence trail. Quants are a dimension *under* a configuration — results name the quant they ran.

| hash | v | quant(s) | PP t/s | TG t/s | wit | results | tests (pass/total) |
|---|---|---|---|---|---|---|---|
| `9a8be2` | v0.1.0 | Q8_0 | - | 7.3 | 1 | 1 | context-recall 1/1; throughput 1/1; tool-roundtrip 1/1; vision-basic 0/1 |

## Runs

| run (UTC) | contributor | quant | hash | PP | TG | tests |
|---|---|---|---|---|---|---|
| 20260907 1018 | itzco | Q8_0 | `9a8be2` | - | 7.3 | tool-roundtrip=pass; throughput=pass; context-recall=pass; vision-basic=unsupported |

### Sources & notes

- 20260907T1018Z — CachyOS box; direct llama-server (no llama-swap); ctx 32k; tool+context+throughput pass, vision unsupported (no mmproj in this deployment)
