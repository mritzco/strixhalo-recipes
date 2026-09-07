# Strix Halo AI Recipe Registry — results board

_Generated 2026-09-07 19:50 UTC by tools/leaderboard.py — do not hand-edit._

## What is this

A registry of reproducible, evidence-backed serving recipes for local LLMs on unified-memory Linux boxes. Every number on this board comes from an immutable result record submitted against a pinned recipe — nothing is hand-set, cross-validation is derived from independent witnesses.

- **Run your own tests / add a recipe:** read `SKILL.md`, search with `tools/search.py`, replicate a recipe, run its tests, submit results.

- **Format & trust model:** `FORMAT.md`. **Licensing:** code Apache-2.0, registry data CC0, docs CC BY 4.0 (README).

> **Reading this board:** tables are ordered by latest activity — this is NOT a quality ranking. There is no universal score. Rank recipes by what you need using `python tools/leaderboard.py --sort tg --cap vision` etc.

## Models

_6 models · 8 result records · latest activity first_

| id | model | variants | quant(s) | size | T M V | PP t/s | TG t/s | wit | backend | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| [qwen3-coder](models/qwen3-coder.md) | Qwen3-Coder-30B-A3B-Instruct | 2 | UD-Q4_K_XL | 16.5 | Y-- | 41023.2 | 58.1 | 2 | vulkan | validated* |
| [qwen3.8-27b](models/qwen3.8-27b.md) | Qwen3.8-27B | 1 | Q8_0 | 27.1 | Y-- | - | 7.3 | 1 | vulkan | 1 witness |
| [qwen3.8-27b-vl](models/qwen3.8-27b-vl.md) | Qwen3.8-27B | 1 | Q8_0 | 27.1 | Y-Y | - | - | 1 | vulkan | 1 witness |
| [glm-4.5-air](models/glm-4.5-air.md) | Glm-4.5-Air | 1 | UD-Q4_K_XL | 46.2 | --- | - | - | 0 | vulkan | no results |
| [qwen3-instruct](models/qwen3-instruct.md) | Qwen3-30B-A3B-Instruct-2507 | 1 | UD-Q4_K_XL | 16.5 | --- | - | - | 0 | vulkan | no results |
| [qwen3-vl](models/qwen3-vl.md) | Qwen3-Vl-30B-A3B-Instruct | 1 | UD-Q4_K_XL | 16.5 | --- | - | - | 0 | vulkan | no results |

_T=confirmed tool calling, M=confirmed MCP, V=confirmed vision. `validated*` = ≥ 2 contributor ids at the current hash with all declared tests passing — treat aliases of one person as one witness._

## Latest tests

| when (UTC) | model | test | result | PP t/s | TG t/s | who |
|---|---|---|---|---|---|---|
| 20260907 1250 | [qwen3-coder](models/qwen3-coder.md) | `harness-tool-use` | pass | - | - | itzco |
| 20260907 1217 | [qwen3-coder](models/qwen3-coder.md) | `agent-coding` | pass | - | - | itzco |
| 20260907 1158 | [qwen3-coder](models/qwen3-coder.md) | `throughput` | pass | 75317.8 | 49.3 | itzco |
| 20260907 1158 | [qwen3-coder](models/qwen3-coder.md) | `throughput` | pass | 74791.3 | 49.3 | itzco |
| 20260907 1138 | [qwen3-coder](models/qwen3-coder.md) | `throughput` | pass | 6728.7 | 66.9 | pilot-itzco |
| 20260907 1138 | [qwen3-coder](models/qwen3-coder.md) | `tool-roundtrip` | pass | - | - | pilot-itzco |
| 20260907 1137 | [qwen3-coder](models/qwen3-coder.md) | `throughput` | pass | 3655.5 | 64.4 | pilot-itzco |
| 20260907 1137 | [qwen3-coder](models/qwen3-coder.md) | `tool-roundtrip` | pass | - | - | pilot-itzco |
| 20260907 1018 | [qwen3.8-27b](models/qwen3.8-27b.md) | `tool-roundtrip` | pass | - | - | itzco |
| 20260907 1018 | [qwen3.8-27b](models/qwen3.8-27b.md) | `throughput` | pass | - | 7.3 | itzco |
| 20260907 1018 | [qwen3.8-27b](models/qwen3.8-27b.md) | `context-recall` | pass | - | - | itzco |
| 20260907 1018 | [qwen3.8-27b](models/qwen3.8-27b.md) | `vision-basic` | unsupported | - | - | itzco |
| 20260907 1018 | [qwen3.8-27b-vl](models/qwen3.8-27b-vl.md) | `tool-roundtrip` | pass | - | - | itzco |
| 20260907 1018 | [qwen3.8-27b-vl](models/qwen3.8-27b-vl.md) | `vision-basic` | pass | - | - | itzco |
