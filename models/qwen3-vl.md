# Qwen3-Vl-30B-A3B-Instruct (`qwen3-vl`)

- Latest version: **v0.1.0** · UD-Q4_K_XL · 16.5 GB · arch qwen3vlmoe · engine vulkan
- Source: unsloth/Qwen3-VL-30B-A3B-Instruct-GGUF
- Verdict: 1 witness — 1 result(s) across 1 variant(s); 1 witness(es) at the current hash
- Confirmed capabilities: tools=False, mcp=False, vision=True · objectives: —

## Variants (configurations tested)

Each variant = a content hash (pinned launch configuration) with its own evidence trail. Quants are a dimension under a configuration.

| hash | v | quant(s) | PP t/s | TG t/s | wit | results | tests (pass/total) |
|---|---|---|---|---|---|---|---|
| `2bb42d` | v0.1.0 | UD-Q4_K_XL | - | - | 1 | 1 | vision-basic 1/1 |

## Runs

| run (UTC) | contributor | quant | hash | PP | TG | tests |
|---|---|---|---|---|---|---|
| 20260909T0750 | itzco | UD-Q4_K_XL | `2bb42d` | - | - | vision-basic=pass |

### Sources & notes

- 20260909T0750Z — First evidence for qwen3-vl: vision confirmed (mmproj, through llama-swap). tools/mcp still untested -> false.
