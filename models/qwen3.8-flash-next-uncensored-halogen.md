# Qwen3.8 Flash Next Uncensored (`qwen3.8-flash-next-uncensored-halogen`)

- Latest version: **v0.3.0** · IQ4_XS · 91.7 GB · arch qwen4exp · engine vulkan
- Source: /home/itzco/models/Qwen3.8-Flash-Next-Uncensored-GGUF/IQ4_XS/Qwen3.8-Flash-Next-Uncensored.IQ4_XS.gguf
- Verdict: 1 witness — 6 result(s) across 3 variant(s); 1 witness(es) at the current hash
- Confirmed capabilities: tools=True, mcp=False, vision=True · objectives: agent_capability

## Variants (configurations tested)

Each variant = a content hash (pinned launch configuration) with its own evidence trail. Quants are a dimension under a configuration.

| hash | v | quant(s) | PP t/s | TG t/s | wit | results | tests (pass/total) |
|---|---|---|---|---|---|---|---|
| `05ebcf` | v0.2.0 | IQ4_XS | 6298.8 | 12.3 | 1 | 2 | throughput 1/1; tool-roundtrip 1/1; vision-basic 2/2 |
| `4f172f` | v0.3.0 | IQ4_XS | 4128.8 | 9.0 | 1 | 2 | throughput 1/1; tool-roundtrip 1/1; vision-basic 2/2 |
| `ae1aef` | v0.1.0 | IQ4_XS | 5245.6 | 8.6 | 1 | 2 | throughput 2/2; tool-roundtrip 2/2 |

## Runs

| run (UTC) | contributor | quant | hash | PP | TG | tests |
|---|---|---|---|---|---|---|
| 20261003T1407 | mritzco | IQ4_XS | `ae1aef` | 9514.6 | 11.7 | tool-roundtrip=pass; throughput=pass |
| 20261003T1409 | mritzco | IQ4_XS | `ae1aef` | 976.6 | 5.6 | tool-roundtrip=pass; throughput=pass |
| 20261003T1503 | mritzco | IQ4_XS | `05ebcf` | 6298.8 | 12.3 | tool-roundtrip=pass; throughput=pass |
| 20261003T1503 | mritzco | IQ4_XS | `05ebcf` | - | - | vision-basic=pass; vision-basic=pass |
| 20261003T1600 | mritzco | IQ4_XS | `4f172f` | 4128.8 | 9.0 | tool-roundtrip=pass; throughput=pass |
| 20261003T1600 | mritzco | IQ4_XS | `4f172f` | - | - | vision-basic=pass; vision-basic=pass |

### Sources & notes

- 20261003T1407Z — halogen-flash-server 0.16.2 container, BYO-GGUF: the uncensored IQ4_XS read in place, no conversion. ctx 131072, HALOGEN_MAX_TOK 16384, GPU only (NPU off). Same weights on the llama.cpp fork on the same class of box: prefill 1314/1092 t/s vs 320-383; decode 28.4 t/s thinking-off and 33.3 t/s over a 1304-token thinking turn vs 35.0. Caveat: tokens_per_sec_pp is cache-inflated - the throughput runner divides TOTAL prompt tokens by wall time, so a warm prefix cache inflates it.
- 20261003T1409Z — SECOND RUN, supersedes the cache artifact in the previous record: started with HALOGEN_PROMPT_CACHE=0 so the prompt-eval round cannot be served from a warm prefix cache. In the cache-on run the runner's tokens_per_sec_pp read 9514.6 t/s (full prompt_tokens / resume time) while the engine's own timings.prompt_per_second was 1092 t/s for the same cold work - the throughput runner divides TOTAL prompt tokens by wall time, so any prefix cache inflates it. Engine-reported cold prefill at ctx 131072: 1314 t/s @6.7k, 1092 t/s @26.7k tokens. Decode from engine timings: 28.4 t/s thinking-off (91.7% draft acceptance), 33.3 t/s over a 1304-token thinking turn.
- 20261003T1503Z — v0.2.0 = v0.1.0 + HALOGEN_VISION_TOWER=1 (vision verified on the abliterated trunk: the tower is fitted to the original trunk and works unchanged). Run against the live serving config (prompt cache at its default 2), so tokens_per_sec_pp is again cache-inflated - 9514-class numbers are an artifact of the runner dividing TOTAL prompt tokens by wall time; the same recipe with HALOGEN_PROMPT_CACHE=0 measured 976.6 t/s, and the engine's own timings.prompt_per_second reports 1092 t/s at 26.7k prompt tokens. True decode: 28.4 t/s thinking-off, 33.3 t/s over a 1304-token thinking turn, 29.7 t/s on the vision request. See the v0.1.0 records for the cache-off arm.
- 20261003T1503Z — Standalone evidence record for the vision capability declared in v0.2.0's tests[]. Halogen vision tower on an abliterated requant of the same trunk: exact ground truth, 0.84 GiB sidecar, ~5 s per image.
- 20261003T1600Z — v0.3.0 = v0.2.0 + the NPU: --device /dev/accel/accel0, the host XRT mounts, and HALOGEN_NPU_MODELS (decider-0.8b, qwen3-embedding-0.6b, qwen3-reranker-0.6b, qwen3guard-gen-0.6b, qwen3.5-2b). NPU endpoints verified separately: embeddings 1024-dim unit-norm at 7465 tok/s on an 8-text batch; rerank ordering sane; moderation Safe/Unsafe 0.998; decider-0.8b 0.08 s; qwen3.5-2b 0.91 s. GPU+NPU concurrency: Flash decode 38.4 -> 33.5 t/s with 29 NPU batches in parallel, no errors, no hang. tokens_per_sec_pp is cache-inflated; see the v0.1.0 cache-off record.
- 20261003T1600Z — v0.3.0 vision arm: tower on (0.84 GiB sidecar) on the abliterated trunk; see the v0.2.0 standalone record for the exact-ground-truth harness result (4.9 s).

### Lineage

- **qwen3.8-flash-next-uncensored v0.1.0** — Same weights (IQ4_XS single file) and the same 131k agent scale; the ENGINE is the variable. That recipe runs the myhacsint qwen4exp Vulkan fork with the unsloth shared-MTP sidecar; this one runs the halogen-flash-server container (custom gfx1151 kernels, its own .hgn draft head) reading the GGUF in place.
- Rationale: Back-end swap on the committed uncensored recipe: the same A/B the stock-side qwen3.8-flash-next pair runs, extended to halogen. Isolates engine + drafter + prefill kernels, since weights, quant class, ctx and KV pool are held constant.
