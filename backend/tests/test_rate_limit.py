"""
Tests for the custom 429 handler in core/limiter.py (audit finding TL-F001).

The app's own limiter is disabled under APP_ENV=test, so these tests build a tiny
FastAPI app with a fresh Limiter and our handler to get a real 429.
"""
import json
import logging
import time
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
import pytest_asyncio
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient
from jose import jwt
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

import core.limiter
from core.limiter import RATE_LIMIT_DETAIL, rate_limit_exceeded_handler
from core.security import create_access_token

ROUTE_TEMPLATE = "/v1/things/{thing_id}"
EMAIL = "victim@example.com"


def _build_app() -> FastAPI:
    app = FastAPI()
    test_limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = test_limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

    @app.get(ROUTE_TEMPLATE)
    @test_limiter.limit("1/minute")
    async def get_thing(request: Request, thing_id: str):
        return {"id": thing_id}

    return app


@pytest.fixture
def limited_app() -> FastAPI:
    return _build_app()


@pytest_asyncio.fixture
async def limited_client(limited_app):
    async with AsyncClient(transport=ASGITransport(app=limited_app), base_url="http://test") as c:
        yield c


async def _hit_limit(client: AsyncClient, headers: dict | None = None, params: dict | None = None):
    first = await client.get("/v1/things/123", headers=headers, params=params)
    assert first.status_code == 200
    second = await client.get("/v1/things/123", headers=headers, params=params)
    assert second.status_code == 429
    return second


def _rate_limit_records(caplog) -> list[logging.LogRecord]:
    return [r for r in caplog.records if r.getMessage().startswith("rate_limit_exceeded ")]


async def test_anonymous_429_logs_route_template(limited_client, caplog):
    caplog.set_level(logging.WARNING, logger="core.limiter")
    await _hit_limit(limited_client)

    records = _rate_limit_records(caplog)
    assert len(records) == 1
    fields = records[0].rate_limit
    assert fields["route"] == ROUTE_TEMPLATE
    assert fields["method"] == "GET"
    assert fields["limit"] == "1 per 1 minute"
    assert fields["client_ip"] == "127.0.0.1"
    assert fields["company_id"] is None
    assert fields["user_id"] is None
    # The message carries the same fields as JSON for plain-text log sinks.
    assert json.loads(records[0].getMessage().split(" ", 1)[1]) == fields


async def test_authenticated_429_logs_tenant(limited_client, caplog):
    caplog.set_level(logging.WARNING, logger="core.limiter")
    user_id, company_id = str(uuid.uuid4()), str(uuid.uuid4())
    token = create_access_token(user_id, company_id)

    await _hit_limit(limited_client, headers={"Authorization": f"Bearer {token}"})

    records = _rate_limit_records(caplog)
    assert len(records) == 1
    fields = records[0].rate_limit
    assert fields["company_id"] == company_id
    assert fields["user_id"] == user_id
    assert token not in caplog.text


def _wrong_key_token() -> str:
    payload = {
        "sub": str(uuid.uuid4()),
        "company_id": str(uuid.uuid4()),
        "email": EMAIL,
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
    }
    return jwt.encode(payload, "not-the-real-secret-key", algorithm="HS256")


def _expired_token() -> str:
    return create_access_token(str(uuid.uuid4()), str(uuid.uuid4()), extra_claims={"email": EMAIL}, expire_minutes=-5)


def _wrong_type_token() -> str:
    return create_access_token(str(uuid.uuid4()), str(uuid.uuid4()), extra_claims={"type": "refresh", "email": EMAIL})


@pytest.mark.parametrize(
    "make_header",
    [
        pytest.param(lambda: f"Bearer {_wrong_key_token()}", id="wrong-key"),
        pytest.param(lambda: f"Bearer {_expired_token()}", id="expired"),
        pytest.param(lambda: f"Bearer {_wrong_type_token()}", id="wrong-type"),
        pytest.param(lambda: "Bearer not.a.jwt", id="garbage"),
    ],
)
async def test_untrusted_token_is_not_logged_as_tenant(limited_client, caplog, make_header):
    caplog.set_level(logging.WARNING, logger="core.limiter")
    header = make_header()
    token = header.split(" ", 1)[1]

    await _hit_limit(limited_client, headers={"Authorization": header}, params={"email": EMAIL})

    records = _rate_limit_records(caplog)
    assert len(records) == 1
    fields = records[0].rate_limit
    assert fields["company_id"] is None
    assert fields["user_id"] is None
    assert token not in caplog.text
    assert EMAIL not in caplog.text
    assert "email=" not in caplog.text


async def test_429_response_body_and_retry_after(limited_client):
    res = await _hit_limit(limited_client)

    body = res.json()
    assert body["detail"] == RATE_LIMIT_DETAIL
    assert body["error"] == "Rate limit exceeded: 1 per 1 minute"
    retry_after = int(res.headers["Retry-After"])
    assert 0 < retry_after <= 60


async def test_retry_after_uses_time_left_in_window(limited_client, monkeypatch):
    # Pretend 45 s of the 60 s window have passed when the handler computes Retry-After.
    # Only the handler's clock moves; the limiter storage keeps the real one.
    monkeypatch.setattr(core.limiter, "time", SimpleNamespace(time=lambda: time.time() + 45))
    res = await _hit_limit(limited_client)

    assert 14 <= int(res.headers["Retry-After"]) <= 16


async def test_retry_after_falls_back_to_limit_period(limited_app, limited_client, monkeypatch):
    def broken_window_stats(*args, **kwargs):
        raise RuntimeError("storage unavailable")

    monkeypatch.setattr(limited_app.state.limiter.limiter, "get_window_stats", broken_window_stats)
    monkeypatch.setattr(core.limiter, "time", SimpleNamespace(time=lambda: time.time() + 45))
    res = await _hit_limit(limited_client)

    assert res.headers["Retry-After"] == "60"


def test_production_app_uses_custom_429_handler():
    from main import app

    assert app.exception_handlers[RateLimitExceeded] is rate_limit_exceeded_handler
