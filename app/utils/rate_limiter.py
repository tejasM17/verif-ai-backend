import time
from collections import defaultdict
from typing import Dict, List, Tuple

from fastapi import Request
from fastapi.responses import JSONResponse

from app.config.settings import settings


class RateLimiter:
    def __init__(self):
        self._requests: Dict[str, List[float]] = defaultdict(list)

    def is_rate_limited(self, key: str) -> Tuple[bool, int]:
        now = time.time()
        window_start = now - settings.RATE_LIMIT_WINDOW_SECONDS
        self._requests[key] = [
            t for t in self._requests[key] if t > window_start
        ]
        if len(self._requests[key]) >= settings.RATE_LIMIT_REQUESTS:
            retry_after = int(
                self._requests[key][0] + settings.RATE_LIMIT_WINDOW_SECONDS - now
            )
            return True, max(1, retry_after)
        self._requests[key].append(now)
        return False, 0

    def get_client_key(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


rate_limiter = RateLimiter()


async def rate_limit_middleware(request: Request, call_next):
    if not settings.RATE_LIMIT_ENABLED:
        return await call_next(request)

    key = rate_limiter.get_client_key(request)
    is_limited, retry_after = rate_limiter.is_rate_limited(key)

    if is_limited:
        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "message": "Too many requests",
                "errors": [f"Rate limit exceeded. Try again in {retry_after} seconds."],
            },
            headers={"Retry-After": str(retry_after)},
        )

    response = await call_next(request)
    return response
