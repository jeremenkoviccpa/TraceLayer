import json
import logging
import math
import time

from fastapi import Request
from fastapi.responses import JSONResponse
from jose import JWTError
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from core.config import settings
from core.security import decode_access_token

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)

RATE_LIMIT_DETAIL = "Too many attempts. Please wait a minute and try again."


def rate_limit(limit_string: str):
    """Apply rate limiting only outside of test environment."""
    if settings.app_env == "test":
        return lambda f: f
    return limiter.limit(limit_string)


def _tenant_from_request(request: Request) -> tuple[str | None, str | None]:
    """Return (company_id, user_id) from a valid access token, else (None, None).

    Only signature- and expiry-verified claims are trusted. No DB lookup.
    """
    auth = request.headers.get("authorization", "")
    scheme, _, token = auth.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None, None
    try:
        payload = decode_access_token(token.strip())
    except JWTError:
        return None, None
    except Exception:
        # Malformed input must never turn a 429 into a 500.
        return None, None
    if payload.get("type") != "access":
        return None, None
    company_id = payload.get("company_id")
    user_id = payload.get("sub")
    if not isinstance(company_id, str) or not isinstance(user_id, str):
        return None, None
    return company_id, user_id


def _retry_after_seconds(request: Request, exc: RateLimitExceeded) -> int:
    """Seconds until the limit's window resets; falls back to the limit's period."""
    item = exc.limit.limit
    try:
        # request.state.view_rate_limit is set by slowapi as (RateLimitItem, [key, scope, ...]).
        current_item, args = request.state.view_rate_limit
        reset_time, _remaining = request.app.state.limiter.limiter.get_window_stats(current_item, *args)
        seconds = math.ceil(reset_time - time.time())
        if seconds > 0:
            return seconds
    except Exception:
        pass
    return max(1, int(item.get_expiry()))


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """429 handler: log a tenant- and route-aware record, return a human `detail`.

    The log record never includes the Authorization header, token, query string or body.
    """
    route = request.scope.get("route")
    company_id, user_id = _tenant_from_request(request)
    fields = {
        "route": getattr(route, "path", None),
        "method": request.method,
        "limit": str(exc.limit.limit),
        "client_ip": get_remote_address(request),
        "company_id": company_id,
        "user_id": user_id,
        # Extra request context to make 429s easier to debug.
        "headers": dict(request.headers),
    }
    logger.warning("rate_limit_exceeded %s", json.dumps(fields), extra={"rate_limit": fields})

    response = JSONResponse(
        {"detail": RATE_LIMIT_DETAIL, "error": f"Rate limit exceeded: {exc.detail}"},
        status_code=429,
    )
    # Private slowapi API, kept to match slowapi's own default handler. It is a no-op
    # today because headers_enabled=False, but adds X-RateLimit-* headers if that changes.
    response = request.app.state.limiter._inject_headers(response, request.state.view_rate_limit)
    response.headers["Retry-After"] = str(_retry_after_seconds(request, exc))
    return response
