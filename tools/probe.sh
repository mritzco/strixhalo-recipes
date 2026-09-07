#!/usr/bin/env bash
# probe.sh v2 — collect a JSON fingerprint of this machine's LLM-serving
# setup. Contract version: 2 (schema_version field). Every result record
# embeds this output, so reproducibility questions ("would this recipe
# fit / behave the same here?") are answerable from the record alone.
#
# Design: distro-specific logic lives in probe.d/<family>.sh. Each module
# may define: pkg_version <pkg>, rocm_info, kernel_info, gpu_info,
# mem_info_gb. Omitted functions fall back to the generic implementations
# below (uname, /proc/meminfo, sysfs DRM mem info, llama-cli).
#
# Adding a new distro: copy tools/probe.d/arch.sh, adjust the package
# calls, register the family in detect_family(). That's the whole PR.
# Unrecognized distros still get a probe: family=unknown + generic
# fallbacks — results are accepted but flagged.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

detect_family() {
  local id id_like
  id="$(. /etc/os-release 2>/dev/null && echo "${ID:-unknown}")"
  id_like="$(. /etc/os-release 2>/dev/null && echo "${ID_LIKE:-}")"
  case " $id_like $id " in
    *" arch "*|*"arch"*|*"cachyos"*) echo "arch" ;;
    *" debian "*|*"ubuntu"*|*"pop"*|*"debian"*) echo "debian" ;;
    *" fedora "*|*"rhel "*|*"fedora"*) echo "fedora" ;;
    *) echo "unknown" ;;
  esac
}

FAMILY="$(detect_family)"
DISTRO="$(. /etc/os-release 2>/dev/null && echo "${PRETTY_NAME:-unknown}")"
KERNEL="$(uname -r)"

# ---------- generic fallbacks ----------
generic_kernel_info() { uname -r; }
generic_mem_total_gb() { awk '/MemTotal/ {printf "%.1f", $2/1024/1024}' /proc/meminfo; }
generic_gtt_gib() {
  local f v
  for f in /sys/class/drm/card*/device/mem_info_gtt_total; do
    [ -r "$f" ] || continue
    v="$(cat "$f" 2>/dev/null || true)"
    [ -n "${v:-}" ] && [ "$v" -gt 0 ] 2>/dev/null && awk -v b="$v" 'BEGIN {printf "%.1f", b/1024/1024/1024}' && return 0
  done
  echo null
}
generic_vram_mib() {
  local f v
  for f in /sys/class/drm/card*/device/mem_info_vram_total; do
    [ -r "$f" ] || continue
    v="$(cat "$f" 2>/dev/null || true)"
    [ -n "${v:-}" ] && [ "$v" -gt 0 ] 2>/dev/null && awk -v b="$v" 'BEGIN {printf "%.0f", b/1024/1024}' && return 0
  done
  echo null
}
generic_rocm_info() { echo ""; }
generic_pkg_version() { echo ""; }

# GPU identity: prefer llama-cli --list-devices (clean name + free MiB,
# the end-to-end proof the backend sees the memory pool), fall back to
# lspci. Emits "name|free_mib".
generic_gpu_info() {
  if command -v llama-cli >/dev/null 2>&1; then
    local line
    line="$(llama-cli --list-devices 2>/dev/null | grep -m1 -i 'Vulkan[0-9]*:' || true)"
    if [ -n "$line" ]; then
      # Vulkan0: AMD Radeon 8060S Graphics (RADV STRIX_HALO) (113152 MiB, 112190 MiB free)
      local name free_mib
      name="$(echo "$line" | sed -E 's/^[^:]*: *//; s/ *\(.*$//')"
      free_mib="$(echo "$line" | grep -oE '[0-9]+ MiB free' | grep -oE '^[0-9]+' | head -1)"
      echo "${name:-unknown}|${free_mib:-}"
      return 0
    fi
  fi
  if command -v lspci >/dev/null 2>&1; then
    local l
    l="$(lspci -mm 2>/dev/null | grep -i -E 'VGA|3D|Display' | head -1 | sed 's/"//g' || true)"
    [ -n "$l" ] && echo "$l|" && return 0
  fi
  echo "unknown|"
}

# ---------- load family module if present ----------
MODULE="$SCRIPT_DIR/probe.d/${FAMILY}.sh"
if [ -f "$MODULE" ]; then
  # shellcheck disable=SC1090
  . "$MODULE"
fi

kernel_info()   { declare -f family_kernel_info >/dev/null && family_kernel_info || generic_kernel_info; }
mem_total_gb()  { declare -f family_mem_total_gb >/dev/null && family_mem_total_gb || generic_mem_total_gb; }
rocm_info()     { declare -f family_rocm_info >/dev/null && family_rocm_info || generic_rocm_info; }
pkg_version()   { declare -f family_pkg_version >/dev/null && family_pkg_version "$1" || generic_pkg_version "$1"; }

GPU_LINE="$(generic_gpu_info)"
GPU_NAME="${GPU_LINE%%|*}"
GPU_FREE="${GPU_LINE#*|}"
[ "$GPU_FREE" = "$GPU_LINE" ] && GPU_FREE=""

# ---------- vulkan ----------
VULKAN_VERSION=""
if command -v vulkaninfo >/dev/null 2>&1; then
  VULKAN_VERSION="$(vulkaninfo --summary 2>/dev/null | grep -m1 -iE 'instance version|apiVersion' | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || true)"
fi

# driver: radv if the device line says RADV, else vulkan driver query
GPU_DRIVER=""
case "$GPU_NAME" in
  *RADV*) GPU_DRIVER="radv" ;;
  *llvmpipe*) GPU_DRIVER="llvmpipe" ;;
  *) GPU_DRIVER="$(vulkaninfo --summary 2>/dev/null | grep -m1 -i 'driverName' | sed -E 's/.*driverName *[:=] *//' | tr -d ' ' | head -1 || true)" ;;
esac

# ---------- llama-server backend ----------
BACKEND_VERSION_STRING=""
BACKEND_BUILD=""
BACKEND_COMMIT=""
BACKEND_BIN=""
BACKEND_PKG=""
BACKEND_INSTALL="unknown"
if command -v llama-server >/dev/null 2>&1; then
  BACKEND_VERSION_STRING="$(llama-server --version 2>&1 | head -1 || true)"
  BACKEND_BUILD="$(echo "$BACKEND_VERSION_STRING" | grep -oE 'build [0-9]+' | grep -oE '[0-9]+' | head -1 || true)"
  BACKEND_COMMIT="$(echo "$BACKEND_VERSION_STRING" | grep -oE 'commit [0-9a-f]+' | awk '{print $2}' | head -1 || true)"
  BACKEND_BIN="$(readlink -f "$(command -v llama-server)" || echo "$(command -v llama-server)")"
fi
BACKEND_PKG="$(pkg_version llama-cpp 2>/dev/null || true)"
if [ -n "$BACKEND_PKG" ]; then
  BACKEND_INSTALL="distro-package"
elif [ -n "$BACKEND_BIN" ]; then
  BACKEND_INSTALL="manual-binary"
fi

ROCm_VERSION="$(rocm_info)"
LLAMA_SWAP_CONFIG=""
[ -f "$HOME/.config/llama-swap/config.yaml" ] && LLAMA_SWAP_CONFIG="$HOME/.config/llama-swap/config.yaml"

# ---------- assemble (python adds raw_hash) ----------
export P_FAMILY="$FAMILY" P_DISTRO="$DISTRO" P_KERNEL="$(kernel_info)"
export P_MEM_TOTAL="$(mem_total_gb)"
P_GTT="$(generic_gtt_gib)"; P_VRAM="$(generic_vram_mib)"
export P_GTT P_VRAM
export P_GPU_NAME="$GPU_NAME" P_GPU_DRIVER="$GPU_DRIVER" P_GPU_FREE="$GPU_FREE"
export P_VULKAN="$VULKAN_VERSION"
export P_BACKEND_STR="$BACKEND_VERSION_STRING" P_BACKEND_BUILD="$BACKEND_BUILD" P_BACKEND_COMMIT="$BACKEND_COMMIT"
export P_BACKEND_BIN="$BACKEND_BIN" P_BACKEND_PKG="$BACKEND_PKG" P_BACKEND_INSTALL="$BACKEND_INSTALL"
export P_ROCM="$ROCm_VERSION" P_SWAP="$LLAMA_SWAP_CONFIG"

python3 - <<'PY'
import json, os, hashlib

def num_or_null(v):
    try:
        return float(v) if v not in ("", "null", None) else None
    except ValueError:
        return None

doc = {
    "schema_version": 2,
    "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "family": os.environ.get("P_FAMILY", "unknown"),
    "distro": os.environ.get("P_DISTRO", "unknown"),
    "kernel": os.environ.get("P_KERNEL", ""),
    "mem": {
        "total_gb": num_or_null(os.environ.get("P_MEM_TOTAL")),
        "gtt_gib": num_or_null(os.environ.get("P_GTT")),
        "vram_mib": num_or_null(os.environ.get("P_VRAM")),
    },
    "gpu": {
        "name": os.environ.get("P_GPU_NAME", ""),
        "driver": os.environ.get("P_GPU_DRIVER") or None,
        "vulkan_version": os.environ.get("P_VULKAN") or None,
        "free_mib": num_or_null(os.environ.get("P_GPU_FREE")),
    },
    "backend": {
        "version_string": os.environ.get("P_BACKEND_STR") or None,
        "build": os.environ.get("P_BACKEND_BUILD") or None,
        "commit": os.environ.get("P_BACKEND_COMMIT") or None,
        "binary": os.environ.get("P_BACKEND_BIN") or None,
        "install_method": os.environ.get("P_BACKEND_INSTALL") or None,
        "pkg_version": os.environ.get("P_BACKEND_PKG") or None,
    },
    "rocm_version": os.environ.get("P_ROCM") or None,
    "llama_swap_config": os.environ.get("P_SWAP") or None,
}
doc["raw_hash"] = "sha256:" + hashlib.sha256(json.dumps(doc, sort_keys=True).encode()).hexdigest()
print(json.dumps(doc, indent=2))
PY
