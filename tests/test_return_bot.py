"""Optional external-bot navigation must not change legacy verification."""
from unittest.mock import AsyncMock
from urllib.parse import parse_qsl, urlsplit

import pytest
from pydantic import ValidationError

from src.api.routes.external import CreateVerificationRequest
from src.config.settings import config
from tests.conftest import make_verification_session


@pytest.fixture
def api_headers(monkeypatch):
    monkeypatch.setattr(config.bot, "token", "test-bot-secret")
    monkeypatch.setattr(config.api, "enable", True)
    monkeypatch.setattr(config.api, "api_key", "test-api-key")
    return {"X-API-Key": config.api.api_key}


@pytest.fixture
async def issued_params(client, db_session, api_headers):
    response = await client.post(
        "/api/verification/create",
        json={"user_id": 123456, "bot_username": "example_bot"},
        headers=api_headers,
    )
    assert response.status_code == 200
    result = response.json()
    assert set(result) == {"token", "verification_url", "expires_at"}
    params = dict(parse_qsl(urlsplit(result["verification_url"]).query))
    assert params["token"] == result["token"]
    assert params["return_bot"] == "example_bot"
    assert params["return_sig"]
    return params


@pytest.mark.parametrize("username", ["https://evil.test", "bot?start=x", "bot/name", "<script>"])
def test_reject_unsafe_username(username):
    with pytest.raises(ValidationError):
        CreateVerificationRequest(user_id=1, bot_username=username)


@pytest.mark.asyncio
@pytest.mark.parametrize("completed", [True, False])
async def test_external_page_return_and_reload(client, issued_params, completed):
    token = issued_params["token"]
    if completed:
        verified = await client.post("/api/v1/verify", json={
            "token": token, "captcha_response": "test", "user_id": 123456,
        })
        assert verified.status_code == 200
    response = await client.get("/verify", params=issued_params)
    assert response.status_code == 200
    assert f'href="https://t.me/example_bot?start=tg_{token}"' in response.text
    if completed:
        assert "验证已完成" in response.text
    else:
        assert 'id="return-bot-link"' in response.text


@pytest.mark.asyncio
@pytest.mark.parametrize("changed", [
    {"return_sig": ""}, {"return_sig": "无效"}, {"return_bot": "another_bot"},
])
async def test_unsigned_or_changed_destination_is_ignored(client, issued_params, changed):
    response = await client.get("/verify", params={**issued_params, **changed})
    assert response.status_code == 200
    assert 'href="https://t.me/' not in response.text


@pytest.mark.asyncio
async def test_return_signature_cannot_be_reused_for_another_session(client, issued_params, api_headers):
    other = await client.post(
        "/api/verification/create", json={"user_id": 999}, headers=api_headers
    )
    assert other.status_code == 200
    result = other.json()
    assert dict(parse_qsl(urlsplit(result["verification_url"]).query)) == {"token": result["token"]}
    response = await client.get("/verify", params={**issued_params, "token": result["token"]})
    assert response.status_code == 200
    assert 'href="https://t.me/' not in response.text


@pytest.mark.asyncio
async def test_group_session_ignores_signed_return_link(client, issued_params, monkeypatch):
    monkeypatch.setattr(
        "src.api.routes.static_files.get_verification_session",
        AsyncMock(return_value=make_verification_session(chat_id=-123)),
    )
    response = await client.get("/verify", params=issued_params)
    assert response.status_code == 200
    assert 'href="https://t.me/' not in response.text


@pytest.mark.asyncio
async def test_missing_signing_secret_preserves_ordinary_link(client, db_session, api_headers, monkeypatch):
    monkeypatch.setattr(config.bot, "token", "")
    response = await client.post(
        "/api/verification/create",
        json={"user_id": 123456, "bot_username": "example_bot"},
        headers=api_headers,
    )
    assert response.status_code == 200
    result = response.json()
    assert dict(parse_qsl(urlsplit(result["verification_url"]).query)) == {"token": result["token"]}
