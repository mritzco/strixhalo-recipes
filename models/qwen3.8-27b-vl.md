# Qwen3.8-27B (`qwen3.8-27b-vl`)

- Latest version: **v0.1.0** · Q8_0 · 27.1 GB · arch qwen35 · engine vulkan
- Source: /home/itzco/models/Qwen3.8-27B-GGUF
- Verdict: 1 witness — 1 result(s) across 1 variant(s); 1 witness(es) at the current hash
- Confirmed capabilities: tools=True, mcp=False, vision=True · objectives: vision, agent_capability

## Variants (configurations tested)

Each variant = a content hash (pinned launch configuration) with its own evidence trail. Quants are a dimension under a configuration.

| hash | v | quant(s) | PP t/s | TG t/s | wit | results | tests (pass/total) |
|---|---|---|---|---|---|---|---|
| `ec321c` | v0.1.0 | Q8_0 | - | - | 1 | 1 | tool-roundtrip 1/1; vision-basic 1/1 |

## Runs

| run (UTC) | contributor | quant | hash | PP | TG | tests |
|---|---|---|---|---|---|---|
| 20260907T1018 | itzco | Q8_0 | `ec321c` | - | - | tool-roundtrip=pass; vision-basic=pass |

### Sources & notes

- 20260907T1018Z — same base model + mmproj-F16: vision confirmed, tools pass
