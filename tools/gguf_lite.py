"""
Minimal GGUF metadata reader. Reads only the header + key-value metadata
section of a .gguf (never tensor data), so it is fast even on 100GB+
files. No external deps — GGUF is a documented binary format
(https://github.com/ggml-org/ggml/blob/master/docs/gguf.md).

Extras on top of raw metadata:
  - quant_from_filename(path): best-effort quant token from the file name
  - VISION_ARCHS: architectures whose base model is multimodal (the
    projector itself ships as a separate mmproj file)
"""
import re
import struct

GGUF_MAGIC = b"GGUF"

T_UINT8, T_INT8, T_UINT16, T_INT16, T_UINT32, T_INT32 = 0, 1, 2, 3, 4, 5
T_FLOAT32, T_BOOL, T_STRING, T_ARRAY, T_UINT64, T_INT64, T_FLOAT64 = 6, 7, 8, 9, 10, 11, 12

_SCALAR_FMT = {
    T_UINT8: ("<B", int), T_INT8: ("<b", int),
    T_UINT16: ("<H", int), T_INT16: ("<h", int),
    T_UINT32: ("<I", int), T_INT32: ("<i", int),
    T_FLOAT32: ("<f", float), T_FLOAT64: ("<d", float),
    T_UINT64: ("<Q", int), T_INT64: ("<q", int),
    T_BOOL: ("<?", bool),
}

# general.file_type -> human quant name (common subset). Many custom
# quants (e.g. UD-Q4_K_XL) predate/escape this map; the filename token is
# preferred when present.
FTYPE_NAMES = {
    0: "F32", 1: "F16", 2: "Q4_0", 3: "Q4_1", 4: "Q4_1_F16",
    6: "Q8_0", 7: "Q5_0", 8: "Q5_1", 9: "Q2_K", 10: "Q4_K",
    11: "Q5_K", 12: "Q6_K", 13: "Q8_K",
    14: "IQ2_XXS", 15: "IQ2_XS", 16: "IQ3_XXS", 17: "IQ1_S",
    18: "IQ4_NL", 19: "IQ3_S", 20: "IQ2_S", 21: "IQ4_XS", 22: "IQ1_M",
    23: "BF16",
}

# Architectures whose *base model* file is multimodal (vision still needs
# the mmproj projector + a real test to confirm).
VISION_ARCHS = {
    "llava", "llava16", "minicpmv", "mllama", "qwen2_vl", "qwen3_vl",
    "qwen2vl", "qwen3vl", "qwen2vlmoe", "qwen3vlmoe", "gemma3",
    "pixtral", "florence2", "olmocr",
}

# Quant tokens commonly found in GGUF file names, longest-first for regex.
QUANT_TOKENS = [
    "UD-Q4_K_XL", "UD-Q3_K_XL", "UD-Q5_K_XL", "UD-Q2_K_XL", "UD-Q4_K_XXL",
    "Q4_K_XL", "Q3_K_XL", "Q5_K_XL",
    "Q2_K", "Q3_K_S", "Q3_K_M", "Q3_K_L", "Q4_K_S", "Q4_K_M", "Q4_K_L",
    "Q5_K_S", "Q5_K_M", "Q5_K_L", "Q6_K", "Q8_0", "Q8_K",
    "Q4_0", "Q4_1", "Q5_0", "Q5_1",
    "IQ1_S", "IQ1_M", "IQ2_XXS", "IQ2_XS", "IQ2_S", "IQ3_XXS", "IQ3_S",
    "IQ4_XS", "IQ4_NL",
    "BF16", "F16", "F32",
]
_QUANT_RE = re.compile(
    r"(?<![\w.])(?:" + "|".join(map(re.escape, QUANT_TOKENS)) + r")(?![\w])"
)


class GGUFParseError(Exception):
    pass


def _read(f, n):
    data = f.read(n)
    if len(data) != n:
        raise GGUFParseError("unexpected end of file")
    return data


def _read_u32(f):
    return struct.unpack("<I", _read(f, 4))[0]


def _read_u64(f):
    return struct.unpack("<Q", _read(f, 8))[0]


def _read_string(f):
    length = _read_u64(f)
    return _read(f, length).decode("utf-8", errors="replace")


def _read_value(f, value_type):
    if value_type in _SCALAR_FMT:
        fmt, conv = _SCALAR_FMT[value_type]
        return conv(struct.unpack(fmt, _read(f, struct.calcsize(fmt)))[0])
    if value_type == T_STRING:
        return _read_string(f)
    if value_type == T_ARRAY:
        elem_type = _read_u32(f)
        count = _read_u64(f)
        return [_read_value(f, elem_type) for _ in range(count)]
    raise GGUFParseError(f"unknown value type {value_type}")


def read_metadata(path, max_kv=None):
    """Read header + KV metadata. Returns (meta_dict, tensors_count)."""
    with open(path, "rb") as f:
        if _read(f, 4) != GGUF_MAGIC:
            raise GGUFParseError("not a GGUF file (bad magic)")
        version = _read_u32(f)
        if version > 3:
            raise GGUFParseError(f"unsupported GGUF version {version}")
        tensor_count = _read_u64(f)
        kv_count = _read_u64(f)
        meta = {}
        for _ in range(kv_count):
            key = _read_string(f)
            value_type = _read_u32(f)
            meta[key] = _read_value(f, value_type)
            if max_kv and len(meta) >= max_kv:
                break
    return meta, tensor_count


def quant_from_filename(path):
    """Best-effort quant token from a GGUF file name, or None."""
    m = _QUANT_RE.search(path)
    return m.group(0) if m else None


def summarize(path):
    """Best-effort extraction of the fields recipes care about."""
    meta, _ = read_metadata(path)
    arch = meta.get("general.architecture") or None
    name = meta.get("general.name") or None
    ftype = meta.get("general.file_type")
    ftype_name = FTYPE_NAMES.get(ftype) if isinstance(ftype, int) else None
    return {
        "name": name,
        "architecture": arch,
        "file_type_name": ftype_name,
        "quant": quant_from_filename(path) or ftype_name,
        "vision": (arch in VISION_ARCHS),
        "quantization_version": meta.get("general.quantization_version"),
    }
