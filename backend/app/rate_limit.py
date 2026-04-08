"""Simple sliding-window rate limiter for expensive endpoints (per client id)."""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request


def get_generate_client_id(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip() or "unknown"
    if request.client:
        return request.client.host or "unknown"
    return "unknown"


_windows: dict[str, deque[float]] = defaultdict(deque)
_window_lock = threading.Lock()
_WINDOW_SECONDS = 60.0


def enforce_generate_rate_limit(client_id: str, limit_per_minute: int) -> None:
    if limit_per_minute <= 0:
        return
    now = time.time()
    cutoff = now - _WINDOW_SECONDS
    with _window_lock:
        dq = _windows[client_id]
        while dq and dq[0] < cutoff:
            dq.popleft()
        if len(dq) >= limit_per_minute:
            retry_after = int(max(1.0, _WINDOW_SECONDS - (now - dq[0])))
            raise HTTPException(
                status_code=429,
                detail=f"Too many generate requests. Try again in ~{retry_after}s.",
                headers={"Retry-After": str(retry_after)},
            )
        dq.append(now)
