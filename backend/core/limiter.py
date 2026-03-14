from slowapi import Limiter
from slowapi.util import get_remote_address

from core.config import settings

limiter = Limiter(key_func=get_remote_address)


def rate_limit(limit_string: str):
    """Apply rate limiting only outside of test environment."""
    if settings.app_env == "test":
        return lambda f: f
    return limiter.limit(limit_string)
