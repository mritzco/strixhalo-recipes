## Why

`probe.sh` output is the environment fingerprint embedded in every
result record, but the current contract is coarse: the GPU string is raw
`lspci` noise, the backend version is one undifferentiated `--version`
line, and the memory model (the defining Strix Halo constraint: 512 MB
carveout + ~110 GB GTT) is not captured at all. Result reproducibility
across machines needs a precise, stable fingerprint.

## What Changes

- **Probe JSON v2** (**BREAKING** `tools/probe.sh` output and the
  `probe_output` block of `schema/result.schema.json`):
  - Memory model from sysfs + meminfo: `mem_total_gb`, `gtt_gib`,
    `vram_mib` (`/sys/class/drm/card*/device/mem_info_{gtt,vram}_total`)
    — the fields that actually explain whether a recipe fits.
  - GPU identity preferred from `llama-cli --list-devices` (clean device
    string + free MiB, the end-to-end proof) with `lspci`/sysfs
    fallback; add `driver` (radv) and Vulkan version.
  - Backend split into `build` + `commit`, parsed from
    `llama-server --version` (reproducibility pins the commit).
  - Keep distro family/kernel; report `family: unknown` gracefully for
    unrecognized distros instead of failing.
- `probe.d/arch.sh` verified against this box (CachyOS). `debian.sh` /
  `fedora.sh` are unverified stubs: either verified by a real run on a
  matching distro or removed — no unverified "supported" claims.
- `tools/probe.d/` location made canonical in docs (currently implied by
  code but misstated in README).

## Capabilities

### New Capabilities

- `machine-probe`: the machine fingerprint JSON contract that every
  result record embeds — fields, sources, and graceful degradation for
  unknown distros.

### Modified Capabilities

- `evidence-records`: its `probe_output` requirement is replaced by the
  `machine-probe` contract (delta lands with this change).

## Impact

`tools/probe.sh`, `tools/probe.d/{arch,debian,fedora}.sh`,
`schema/result.schema.json` (`probe_output`), `tools/collect.py`
(consumes probe output), `tools/submit_result.py` (embeds it),
`SKILL.md`. Verified commands come from `~/handbook/setup/05-local-ai.md`
and `~/handbook/ai/00-environment.md`.
