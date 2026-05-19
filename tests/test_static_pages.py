"""Tests for HTML template routes (Mini Web App pages)."""

from unittest.mock import AsyncMock

import pytest

from tests.conftest import make_verification_session


@pytest.mark.asyncio
async def test_index_page_returns_html(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "TGuard" in response.text


@pytest.mark.asyncio
async def test_success_page_returns_html(client):
    response = await client.get("/success")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_verify_page_with_valid_session(client, monkeypatch):
    session = make_verification_session()
    monkeypatch.setattr(
        "src.api.routes.static_files.get_verification_session",
        AsyncMock(return_value=session),
    )

    response = await client.get("/verify", params={"token": "test-token"})

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "test-token" in response.text
    assert "123456" in response.text


@pytest.mark.asyncio
async def test_verify_page_invalid_token_returns_404(client, monkeypatch):
    monkeypatch.setattr(
        "src.api.routes.static_files.get_verification_session",
        AsyncMock(return_value=None),
    )

    response = await client.get("/verify", params={"token": "invalid"})

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_verify_page_expired_session(client, monkeypatch):
    session = make_verification_session(expired=True)
    monkeypatch.setattr(
        "src.api.routes.static_files.get_verification_session",
        AsyncMock(return_value=session),
    )

    response = await client.get("/verify", params={"token": "test-token"})

    assert response.status_code == 200
    assert "验证链接已过期" in response.text


@pytest.mark.asyncio
async def test_verify_page_completed_session(client, monkeypatch):
    session = make_verification_session(captcha_completed=True)
    monkeypatch.setattr(
        "src.api.routes.static_files.get_verification_session",
        AsyncMock(return_value=session),
    )

    response = await client.get("/verify", params={"token": "test-token"})

    assert response.status_code == 200
    assert "您已完成验证" in response.text


@pytest.mark.asyncio
async def test_template_response_signature():
    """Guard against Starlette TemplateResponse API regressions."""
    from starlette.requests import Request

    from fastapi.templating import Jinja2Templates

    templates = Jinja2Templates(directory="templates")
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [],
    }
    request = Request(scope)

    response = templates.TemplateResponse(request, "index.html")

    assert response.status_code == 200
    assert response.media_type.startswith("text/html")
