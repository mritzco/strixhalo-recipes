# Qwen3-Coder-30B-A3B-Instruct (`qwen3-coder`)

- Latest version: **v0.2.1** · UD-Q4_K_XL · 16.5 GB · arch qwen3moe · engine vulkan
- Source: unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF
- Verdict: validated* — 5 result(s) across 2 variant(s); 2 witness(es) at the current hash: itzco, pilot-itzco
- Confirmed capabilities: tools=True, mcp=False, vision=False · objectives: throughput

## Variants (configurations tested)

Each variant = a content hash (pinned launch configuration) with its own evidence trail. Quants are a dimension *under* a configuration — results name the quant they ran.

| hash | v | quant(s) | PP t/s | TG t/s | wit | results | tests (pass/total) |
|---|---|---|---|---|---|---|---|
| `10a6b2` | v0.2.1 | UD-Q4_K_XL | 41023.2 | 58.1 | 2 | 3 | agent-coding 1/1; throughput 2/2; tool-roundtrip 1/1 |
| `8b452d` | v0.1.0 | UD-Q4_K_XL | 39223.4 | 56.9 | 2 | 2 | throughput 2/2; tool-roundtrip 1/1 |

## Runs

| run (UTC) | contributor | quant | hash | PP | TG | tests |
|---|---|---|---|---|---|---|
| 20260907 1137 | pilot-itzco | UD-Q4_K_XL | `8b452d` | 3655.5 | 64.4 | throughput=pass; tool-roundtrip=pass |
| 20260907 1138 | pilot-itzco | UD-Q4_K_XL | `10a6b2` | 6728.7 | 66.9 | throughput=pass; tool-roundtrip=pass |
| 20260907 1158 | itzco | UD-Q4_K_XL | `8b452d` | 74791.3 | 49.3 | throughput=pass |
| 20260907 1158 | itzco | UD-Q4_K_XL | `10a6b2` | 75317.8 | 49.3 | throughput=pass |
| 20260907 1217 | itzco | UD-Q4_K_XL | `10a6b2` | - | - | agent-coding=pass |

### Sources & notes

- 20260907T1137Z — baseline default ubatch on Vulkan; source post: reddit 1w82ztz
- 20260907T1138Z — -ub 2048; PP delta vs baseline reported in commit message; source post reddit 1w82ztz
- 20260907T1158Z — long-context follow-up (11k tokens PP): default ubatch; matches -ub 2048 within noise on Vulkan
- 20260907T1158Z — long-context follow-up (11k tokens PP): -ub 2048 shows no PP gain over default on Vulkan/radv (fork kernels are ROCm-targeted)
- 20260907T1217Z — agent-coding: multi-round file edit + run loop; sandbox bug fixed, ground truth verified (main.py -> 5)

### Lineage

- **qwen3-coder v0.1.0** — MoE ubatch tuning: -ub 2048 per Strix Halo community fork guidance for faster PP
- Rationale: Variant of qwen3-coder draft: raise ubatch per community MoE guidance; follow-up at 11k prompt tokens shows no PP effect on Vulkan/radv (fork kernels are ROCm-targeted) — flag retained as neutral variant.
