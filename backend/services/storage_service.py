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


def _ensure_bucket(client, bucket: str) -> None:
    """Create the bucket if it doesn't already exist."""
    try:
        buckets = client.storage.list_buckets()
        existing = {b.name for b in buckets} if buckets else set()
        if bucket not in existing:
            client.storage.create_bucket(bucket, options={"public": False})
            logger.info("Created Supabase storage bucket: %s", bucket)
    except Exception as exc:
        logger.warning("Could not verify/create bucket %s: %s", bucket, exc)


def upload_bytes(
    bucket: str,
    path: str,
    data: bytes,
    content_type: str,
) -> dict[str, Any]:
    client = _get_client()
    _ensure_bucket(client, bucket)
    storage = client.storage.from_(bucket)
    response = storage.upload(
        path,
        data,
        {"content-type": content_type, "upsert": True},
    )
    return response


def create_signed_url(bucket: str, path: str, expires_in: int = 3600) -> str:
    client = _get_client()
    storage = client.storage.from_(bucket)
    response = storage.create_signed_url(path, expires_in)
    if not response:
        raise RuntimeError("Failed to create signed URL")

    # supabase-py 2.x returns a dict; key varies across patch versions
    if isinstance(response, dict):
        url = (
            response.get("signedURL")
            or response.get("signed_url")
            or response.get("signedUrl")
        )
        if url:
            return url

    # storage-py may return an object with a .signed_url attribute
    url = getattr(response, "signed_url", None) or getattr(response, "signedURL", None)
    if url:
        return url

    raise RuntimeError(f"Signed URL missing from Supabase response: {response!r}")


def delete_object(bucket: str, path: str) -> None:
    client = _get_client()
    storage = client.storage.from_(bucket)
    storage.remove([path])
    logger.info("Deleted storage object: %s/%s", bucket, path)
