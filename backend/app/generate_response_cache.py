"""
Server-side LRU cache for POST /generate JSON responses.

This is NOT Anthropic's API "prompt prefix cache" (cache_control on message blocks).
See: anthropic_api_prompt_prefix_cache in Settings + cot_prompt_builder.py.
"""

from __future__ import annotations

import hashlib
import json
import threading
from collections import OrderedDict
from typing import Any

from app.schemas import GenerateResponse


def generate_response_cache_fingerprint(payload: dict[str, Any]) -> str:
    """Stable SHA-256 fingerprint for identical generate inputs (UTF-8 JSON, sorted keys)."""
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


class LruGenerateResponseCache:
    """Thread-safe LRU store: fingerprint -> last GenerateResponse."""

    def __init__(self, max_entries: int) -> None:
        self._max = max(1, max_entries)
        self._data: OrderedDict[str, GenerateResponse] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: str) -> GenerateResponse | None:
        with self._lock:
            if key not in self._data:
                return None
            val = self._data.pop(key)
            self._data[key] = val
            return val.model_copy(deep=True)

    def set(self, key: str, value: GenerateResponse) -> None:
        with self._lock:
            if key in self._data:
                self._data.pop(key)
            self._data[key] = value
            while len(self._data) > self._max:
                self._data.popitem(last=False)


_cache_singleton: LruGenerateResponseCache | None = None
_cache_singleton_max: int | None = None
_cache_lock = threading.Lock()


def get_lru_generate_response_cache(max_entries: int) -> LruGenerateResponseCache:
    global _cache_singleton, _cache_singleton_max
    with _cache_lock:
        if _cache_singleton is None or _cache_singleton_max != max_entries:
            _cache_singleton = LruGenerateResponseCache(max_entries=max_entries)
            _cache_singleton_max = max_entries
        return _cache_singleton


def reset_lru_generate_response_cache_for_tests(max_entries: int) -> None:
    global _cache_singleton, _cache_singleton_max
    with _cache_lock:
        _cache_singleton = LruGenerateResponseCache(max_entries=max_entries)
        _cache_singleton_max = max_entries
