## Why

The owner's acceptance flow is "run the collect script and get an entry
for each system we have in llama-swap". The current `collect.py` cannot
do that: 4 of the 6 llama-swap models launch via `-hf repo:quant` specs
it cannot resolve to a file, and verified runs show it mis-reads flags —
`-fa on` is missed (only `--flash-attn` matches) and `--mmproj` is
ignored, so the vision model `qwen3.8-27b-vl` would draft
`vision: false`, a fabricated negative.

## What Changes

- **llama-swap enumeration mode** (**BREAKING**: new
  `--from-llama-swap [config]` mode; `--pid` / `--launch-cmd` modes
  kept): parse `~/.config/llama-swap/config.yaml`, emit one draft recipe
  per configured system. Draft id = the llama-swap model key
  (`qwen3-coder`, `qwen3-instruct`, `qwen3-vl`, `glm-4.5-air`,
  `qwen3.8-27b`, `qwen3.8-27b-vl` on this box) so recipes map 1:1 to
  what people actually run.
- **`-hf` resolution**: locate the downloaded GGUF in the HF cache
  (`~/.cache/huggingface/hub`) when present; when absent, leave explicit
  TODO + provenance (repo:quant) rather than guessing.
- **Flag parsing v2**: `-fa on` / `--flash-attn`, `--mmproj` (flags the
  recipe as multimodal — vision candidate, still needs a real test),
  `-c`/`--ctx-size`, `--cache-type-k/v`, `-ngl`, `--alias`, `--port`;
  quant inferred from filename or GGUF metadata.
- **gguf_lite v2**: report architecture, quant info, and vision/mmproj
  presence from GGUF metadata so drafts never carry false negatives.
- **Never-fabricate rules unchanged and enforced**: unverifiable fields
  stay `TODO`/`false`; capabilities_confirmed stays false until a real
  harness test (see `harness-tests-v1`); draft prints a checklist; batch
  `--dry-run` previews every draft before anything is written.
- Drafts land at `status: experimental` with empty lineage; recipe body
  fields populated from probe v2 (backend build/commit, kernel, family,
  vulkan) and GGUF (name, arch, size).

## Capabilities

### New Capabilities

- `recipe-collection`: generating schema-valid drafts from live systems
  (llama-swap config, running process, launch command) without
  fabricating anything.

### Modified Capabilities

- `data-model`: recipe drafts produced here must conform to the frozen
  model from `checkpoint-0-data-model`.

## Impact

`tools/collect.py`, `tools/gguf_lite.py`, `recipes/<model>/` drafts for
the 6 llama-swap systems on this box, `SKILL.md` (new mode + checklist),
`AGENTS.md`. Depends on the frozen data model (#2) and probe v2 output
(#3).
