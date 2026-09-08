# Qwen3.8 Flash Next Uncensored (`qwen3.8-flash-next-uncensored`)

- Latest version: **v0.1.0** · IQ4_XS · 91.7 GB · arch qwen4exp · engine vulkan
- Source: /home/itzco/models/Qwen3.8-Flash-Next-Uncensored-GGUF/IQ4_XS
- Verdict: validated* — 3 result(s) across 1 variant(s); 2 witness(es) at the current hash
- Confirmed capabilities: tools=True, mcp=False, vision=True · objectives: quality, agent_capability

## Variants (configurations tested)

Each variant = a content hash (pinned launch configuration) with its own evidence trail. Quants are a dimension under a configuration.

| hash | v | quant(s) | PP t/s | TG t/s | wit | results | tests (pass/total) |
|---|---|---|---|---|---|---|---|
| `d81cee` | v0.1.0 | IQ4_XS | 3329.3 | 19.0 | 2 | 3 | agent-coding 1/1; context-recall 1/1; harness-tool-use 1/1; throughput 1/1; tool-roundtrip 1/1; vision-basic 1/1 |

## Runs

| run (UTC) | contributor | quant | hash | PP | TG | tests |
|---|---|---|---|---|---|---|
| 20260908T1703 | myhacsint-pilot | IQ4_XS | `d81cee` | 3329.3 | 19.0 | tool-roundtrip=pass; throughput=pass; agent-coding=pass; context-recall=pass |
| 20260908T1717 | itzco | IQ4_XS | `d81cee` | - | - | harness-tool-use=pass |
| 20260908T1734 | itzco | IQ4_XS | `d81cee` | - | - | vision-basic=pass |

### Sources & notes

- 20260908T1703Z — myhacsint fork b10685-source @ 2dff8596 (build-vulkan, Vulkan/radv) + mradermacher IQ4_XS uncensored (98.42GB, rev 61f739cd47b2; orca Q5_K_M 134.11GB unrunnable on 128GB — see recipe annotations) + unsloth shared MTP Q8_0 head (rev 38bb39ee, 2,786,568,256 B) + mmproj-f16. ctx 131072, f16 KV, adaptive spec n0-5 p0.75, --fit on, mmap/lazy/no-repack/no-host, reasoning xhigh+preserve, temp 0 battery. Source: https://www.reddit.com/r/StrixHalo/comments/1w9sye5/ + https://github.com/myhacsint/llama.cpp. Server-eval: decode 30.8-43.9 t/s (short structured/agent rounds), cold PP 398.1 t/s @10985 & 372.9 @12365; MTP acceptance 0.816-1.000/task, mean 0.947. Runner TG 19.0 contaminated by cold-PP round (known artifact). Memory: peak used 87/124.9GB, GTT 78.6GiB, VmHWM 51.5GB; ctx ceiling 131072 (262144 impossible: +12GiB KV over peak; arithmetic in annotations). A/B: vs mainline-131k field decode 14.6-18.4 @30-51k ctx ~2x; in v0.2.0 Nathan+MTP band (29.1-44.0) at 4x ctx with f16 KV; PP 398 vs 383.8 (Nathan) vs 320 (mainline). No MTP leak at temp 0 (clean code/identities); temp>0 caveat recorded.
- 20260908T1717Z — HARNESS-LEVEL evidence: omp -p one-shot tool round-trip against llama-swap lm-studio/qwen3.8-flash-uncensored (myhacsint fork + shared MTP + uncensored IQ4_XS @131k). Tool result 42 observed, exit 0. GLM-class omp breakage does NOT occur on this stack.
- 20260908T1734Z — VISION CONFIRMED on flash-family via myhacsint fork + mradermacher mmproj-f16 (test through llama-swap). Model now: tools+vision+agent-coding all confirmed; mcp still false.

### Lineage

- **qwen3.8-flash-next-131k v0.1.0** — Agent-session deployment base at ctx 131072 (stock unsloth UD-IQ4_XS, mainline b10809, q8 KV). This run keeps the 131k context scale and agent battery but swaps the weights (uncensored IQ4_XS mirror), the engine (myhacsint qwen4exp fork), and the decode path (shared-MTP adaptive).
- **qwen3.8-flash-next v0.2.0** — Fork + MTP baseline (Nathan strix-halo-vulkan fork + agentionai non-shared MTP Q8_0 sidecar, fixed n4, q8 KV @32k). This run is the myhacsint b10685 fork + unsloth *shared* MTP head with adaptive draft sizing (n0-5, p-min 0.75), f16 KV @131072, uncensored weights.
- Rationale: Uncensored-weights variant of the committed Qwen3.8-Flash-Next (qwen4exp) recipes: community-favored stack (myhacsint fork + orca Q5_K_M + unsloth shared MTP, per the alchi-flac receipts) adapted to what this 128 GB box can actually serve — Q5_K_M is arithmetically unrunnable here (see annotations), so the uncensored IQ4_XS mirror keeps the quant class of the stock baselines for a clean A/B of engine + MTP head + weights.
