import time
from collections import defaultdict

from fastapi import Request

from app.core.exceptions import AppException

_WINDOW_SECONDS = 60
_MAX_REQUESTS = 20
_buckets: dict[str, list[float]] = defaultdict(list)


def _client_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def enforce_rate_limit(request: Request, *, max_requests: int = _MAX_REQUESTS) -> None:
    """Reject requests that exceed a per-IP sliding window limit."""

    key = _client_key(request)
    now = time.monotonic()
    window_start = now - _WINDOW_SECONDS
    recent = [stamp for stamp in _buckets[key] if stamp >= window_start]
    if len(recent) >= max_requests:
        raise AppException(
            "Too many requests. Please try again shortly.",
            status_code=429,
            code="rate_limit_exceeded",
        )
    recent.append(now)
    _buckets[key] = recent
