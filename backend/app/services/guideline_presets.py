"""Load named guideline bodies (e.g. MCG_ISC_DIABETES) from app/guidelines/."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

_GUIDELINES_DIR = Path(__file__).resolve().parent.parent / "guidelines"
_REGISTRY_PATH = _GUIDELINES_DIR / "registry.json"


class GuidelinePresetError(ValueError):
    pass


@lru_cache
def _registry_raw() -> dict[str, Any]:
    if not _REGISTRY_PATH.is_file():
        return {}
    data = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _normalize_key(raw: str) -> str:
    s = raw.strip().upper()
    s = re.sub(r"[^A-Z0-9]+", "_", s)
    return s.strip("_")


@lru_cache
def list_preset_keys() -> list[tuple[str, str]]:
    """Return [(canonical_key, title), ...] sorted by title."""
    reg = _registry_raw()
    out: list[tuple[str, str]] = []
    for key, meta in reg.items():
        if not isinstance(meta, dict):
            continue
        title = str(meta.get("title") or key)
        out.append((str(key), title))
    out.sort(key=lambda x: x[1].lower())
    return out


def _load_file_for_key(canonical_key: str) -> str | None:
    reg = _registry_raw()
    meta = reg.get(canonical_key)
    if not isinstance(meta, dict):
        return None
    fname = meta.get("file")
    if not fname or not isinstance(fname, str):
        return None
    path = (_GUIDELINES_DIR / fname).resolve()
    if not str(path).startswith(str(_GUIDELINES_DIR.resolve())):
        return None
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def resolve_preset_body(guideline_key: str | None) -> tuple[str | None, str]:
    """Return (canonical_key, markdown body) or (None, '') if key missing/empty."""
    if not guideline_key or not str(guideline_key).strip():
        return None, ""
    raw = str(guideline_key).strip()
    # try exact then normalized
    reg = _registry_raw()
    canonical: str | None = None
    if raw in reg:
        canonical = raw
    else:
        norm = _normalize_key(raw)
        for k in reg:
            if _normalize_key(str(k)) == norm or str(k).upper() == norm:
                canonical = str(k)
                break
    if canonical is None:
        available = ", ".join(sorted(reg.keys())) if reg else "(none)"
        raise GuidelinePresetError(f"Unknown guideline_key {raw!r}. Known keys: {available}")
    body = _load_file_for_key(canonical)
    if body is None:
        raise GuidelinePresetError(f"Preset {canonical!r} is registered but file is missing")
    return canonical, body


def merge_guideline_for_request(guideline_key: str | None, guideline_text: str | None) -> str | None:
    """Preset body + optional pasted text; returns None if both empty."""
    parts: list[str] = []
    if guideline_key and str(guideline_key).strip():
        _, preset_body = resolve_preset_body(guideline_key)
        if preset_body.strip():
            parts.append(preset_body.strip())
    if guideline_text and str(guideline_text).strip():
        parts.append(str(guideline_text).strip())
    if not parts:
        return None
    if len(parts) == 1:
        return parts[0]
    return parts[0] + "\n\n---\n\n## Additional guideline notes (from request)\n\n" + parts[1]
