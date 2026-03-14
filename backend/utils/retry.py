import asyncio
import logging

logger = logging.getLogger(__name__)


async def with_backoff(coro_fn, *args, max_attempts: int = 5, **kwargs):
    """Run an async callable with exponential backoff on rate limit errors."""
    for attempt in range(max_attempts):
        try:
            return await coro_fn(*args, **kwargs)
        except Exception as e:
            msg = str(e).lower()
            is_rate_limit = any(kw in msg for kw in ("rate", "throttl", "429", "too many"))
            if is_rate_limit and attempt < max_attempts - 1:
                wait = 2 ** attempt
                logger.warning(f"Rate limited, retrying in {wait}s (attempt {attempt + 1})")
                await asyncio.sleep(wait)
                continue
            raise
    raise RuntimeError("Max retry attempts exceeded")
