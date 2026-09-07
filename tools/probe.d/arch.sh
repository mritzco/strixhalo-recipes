#!/usr/bin/env bash
# Arch-family module (Arch, CachyOS, Manjaro, EndeavourOS) — reference
# implementation, verified on CachyOS (2026-09-07).
# Copy this file to add a new distro family and register the family in
# detect_family() inside probe.sh. Omitted functions fall back to the
# generic implementations in probe.sh (uname, /proc/meminfo, sysfs,
# llama-cli --list-devices).

family_pkg_version() {
  local pkg="$1"
  pacman -Q "$pkg" 2>/dev/null | awk '{print $2}'
}

family_rocm_info() {
  local v
  v="$(pacman -Q rocm-core 2>/dev/null | awk '{print $2}')"
  if [ -z "$v" ] && command -v rocminfo >/dev/null 2>&1; then
    v="$(rocminfo 2>/dev/null | grep -m1 -i 'ROCm Version' | awk -F: '{print $2}' | xargs)"
  fi
  echo "$v"
}

family_kernel_info() {
  # Keep the running kernel plus the package that provides it, e.g.
  # "7.0.11-3-cachyos-px13 (linux-cachyos 7.2.3-1)".
  local pkg
  pkg="$(pacman -Q 2>/dev/null | grep -m1 -E '^(linux|linux-cachyos|linux-zen|linux-lts) ' || true)"
  if [ -n "$pkg" ]; then
    echo "$(uname -r) ($pkg)"
  else
    uname -r
  fi
}
