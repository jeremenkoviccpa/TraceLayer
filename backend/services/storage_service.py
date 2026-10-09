from __future__ import annotations

import logging
from typing import Any

from core.config import settings

logger = logging.getLogger(__name__)

_client = None
_s3_client = None


def _use_s3() -> bool:
    """S3-compatible storage (e.g. Railway Buckets) takes precedence over Supabase."""
    return bool(settings.storage_s3_bucket and settings.storage_endpoint)


def _get_s3_client():
    global _s3_client
    if _s3_client is not None:
        return _s3_client

    import boto3
    from botocore.config import Config

    _s3_client = boto3.client(
        "s3",
        endpoint_url=settings.storage_endpoint,
        aws_access_key_id=settings.storage_access_key,
        aws_secret_access_key=settings.storage_secret_key,
        region_name=settings.storage_region or "auto",
        config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
    )
    return _s3_client


def _s3_key(bucket: str, path: str) -> str:
    # Logical buckets (reports, documents, …) become key prefixes in the single S3 bucket.
    return f"{bucket.strip('/')}/{path.lstrip('/')}" if bucket else path.lstrip("/")


def _get_client():
    global _client
    if _client is not None:
        return _client

    if not settings.supabase_url or not settings.supabase_service_key:
        raise RuntimeError("Storage is not configured (set STORAGE_S3_BUCKET or Supabase credentials)")

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
    if _use_s3():
        key = _s3_key(bucket, path)
        _get_s3_client().put_object(
            Bucket=settings.storage_s3_bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        return {"path": key}

    import httpx

    client = _get_client()
    _ensure_bucket(client, bucket)
    storage = client.storage.from_(bucket)
    try:
        response = storage.upload(
            path,
            data,
            {"content-type": content_type, "upsert": "true"},
        )
    except (httpx.ConnectError, httpx.TimeoutException) as exc:
        raise RuntimeError(
            f"Supabase storage unreachable — check SUPABASE_URL env var: {exc}"
        ) from exc
    except Exception as exc:
        # storage3 raises UnboundLocalError when connection fails before response is set
        if isinstance(exc, UnboundLocalError) and "response" in str(exc):
            raise RuntimeError(
                f"Supabase storage connection failed — check SUPABASE_URL env var"
            ) from exc
        raise
    return response


def create_signed_url(bucket: str, path: str, expires_in: int = 3600) -> str:
    if _use_s3():
        return _get_s3_client().generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.storage_s3_bucket, "Key": _s3_key(bucket, path)},
            ExpiresIn=expires_in,
        )

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
    if _use_s3():
        _get_s3_client().delete_object(Bucket=settings.storage_s3_bucket, Key=_s3_key(bucket, path))
    else:
        client = _get_client()
        storage = client.storage.from_(bucket)
        storage.remove([path])
    logger.info("Deleted storage object: %s/%s", bucket, path)
