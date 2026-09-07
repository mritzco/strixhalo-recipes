# Glm-4.5-Air (`glm-4.5-air`)

- Latest version: **v0.1.0** · UD-Q4_K_XL · 46.2 GB · arch glm4moe · engine vulkan
- Source: unsloth/GLM-4.5-Air-GGUF
- Verdict: 1 witness — 1 result(s) across 1 variant(s); 1 witness(es) at the current hash
- Confirmed capabilities: tools=True, mcp=False, vision=False · objectives: —

## Variants (configurations tested)

Each variant = a content hash (pinned launch configuration) with its own evidence trail. Quants are a dimension under a configuration.

| hash | v | quant(s) | PP t/s | TG t/s | wit | results | tests (pass/total) |
|---|---|---|---|---|---|---|---|
| `645260` | v0.1.0 | UD-Q4_K_XL | 3421.3 | 3.7 | 1 | 1 | code-battery 0/1; throughput 1/1; tool-roundtrip 1/1 |

## Runs

| run (UTC) | contributor | quant | hash | PP | TG | tests |
|---|---|---|---|---|---|---|
| 20260907T1655 | itzco | UD-Q4_K_XL | `645260` | 3421.3 | 3.7 | tool-roundtrip=pass; code-battery=fail; throughput=pass |

### Sources & notes

- 20260907T1655Z — server-level (distro b10809, ctx 32k): tool_calls parse OK; code-battery 3/8; TG 3.7 single-round artifact (n=1, likely thinking-budget) — handbook UI numbers 70-80 t/s are chat-no-tools
