from __future__ import annotations

import logging
from typing import Any

from core.config import settings

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client

    if not settings.supabase_url or not settings.supabase_service_key:
        raise RuntimeError("Supabase credentials are not configured")

    try:
        from supabase import create_client
    except ImportError as exc:
        raise RuntimeError(
            "Supabase client not installed. Add `supabase` to requirements."
        ) from exc

    _client = create_client(settings.supabase_url, settings.supabase_service_key)
    return _client


def upload_bytes(
    bucket: str,
    path: str,
    data: bytes,
    content_type: str,
) -> dict[str, Any]:
    client = _get_client()
    storage = client.storage.from_(bucket)
    response = storage.upload(
        path,
        data,
        {"content-type": content_type, "upsert": "true"},
    )
    return response


def create_signed_url(bucket: str, path: str, expires_in: int = 3600) -> str:
    client = _get_client()
    storage = client.storage.from_(bucket)
    response = storage.create_signed_url(path, expires_in)
    if not response:
        raise RuntimeError("Failed to create signed URL")

    if isinstance(response, dict):
        url = response.get("signedURL") or response.get("signed_url")
        if url:
            return url

    raise RuntimeError("Signed URL missing from Supabase response")


def delete_object(bucket: str, path: str) -> None:
    client = _get_client()
    storage = client.storage.from_(bucket)
    storage.remove([path])
    logger.info("Deleted storage object: %s/%s", bucket, path)
