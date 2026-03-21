"""OIDC SSO service — discovery, authorization URL building, token exchange, ID token validation."""
import logging
import urllib.parse
import uuid
from typing import Any

import httpx
from jose import JWTError, jwt

from core.security import encrypt_value, decrypt_value

logger = logging.getLogger(__name__)

_discovery_cache: dict[str, dict] = {}


async def fetch_oidc_discovery(issuer: str) -> dict:
    """Fetch and cache OIDC discovery document from {issuer}/.well-known/openid-configuration."""
    if issuer in _discovery_cache:
        return _discovery_cache[issuer]

    url = issuer.rstrip("/") + "/.well-known/openid-configuration"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        doc = resp.json()

    _discovery_cache[issuer] = doc
    return doc


def build_authorization_url(
    authorization_endpoint: str,
    client_id: str,
    redirect_uri: str,
    state: str,
    scopes: str,
) -> str:
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scopes,
        "state": state,
        "prompt": "select_account",
    }
    return f"{authorization_endpoint}?{urllib.parse.urlencode(params)}"


async def exchange_code_for_tokens(
    token_endpoint: str,
    code: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            token_endpoint,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
            },
        )
        if not resp.is_success:
            logger.error("SSO token exchange failed: %s %s", resp.status_code, resp.text)
            raise ValueError(f"Token exchange failed: {resp.status_code}")
        return resp.json()


async def fetch_jwks(jwks_uri: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(jwks_uri)
        resp.raise_for_status()
        return resp.json().get("keys", [])


def validate_id_token(id_token: str, jwks_keys: list[dict], issuer: str, client_id: str) -> dict[str, Any]:
    """Validate OIDC ID token signature and claims. Returns decoded claims."""
    try:
        header = jwt.get_unverified_header(id_token)
    except JWTError as e:
        raise ValueError(f"Invalid ID token header: {e}")

    kid = header.get("kid")
    # Match key by kid if present, else use first key
    key = next((k for k in jwks_keys if k.get("kid") == kid), jwks_keys[0] if jwks_keys else None)
    if not key:
        raise ValueError("No JWKS key found to validate ID token")

    try:
        claims = jwt.decode(
            id_token,
            key,
            algorithms=["RS256", "RS384", "RS512", "ES256", "ES384", "ES512"],
            audience=client_id,
            issuer=issuer,
        )
    except JWTError as e:
        raise ValueError(f"ID token validation failed: {e}")

    email = claims.get("email")
    if not email:
        raise ValueError("ID token missing email claim — ensure 'email' scope is requested")

    return claims


def encrypt_secret(secret: str) -> str:
    return encrypt_value(secret)


def decrypt_secret(encrypted: str) -> str:
    return decrypt_value(encrypted)


def sso_callback_uri(backend_url: str, company_id: uuid.UUID) -> str:
    return f"{backend_url}/v1/auth/sso/{company_id}/callback"
