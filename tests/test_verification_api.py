"""Tests for core verification API flow (POST /api/v1/verify, status, captcha config)."""

from unittest.mock import AsyncMock

import pytest

from src.api.services.approval import ApprovalResult
from src.captcha.base import CaptchaVerificationResult
from tests.conftest import make_join_request, make_verification_session

VERIFY_URL = "/api/v1/verify"
VERIFY_PAYLOAD = {
    "token": "test-token",
    "captcha_response": "captcha-token-from-client",
}


@pytest.mark.asyncio
async def test_verify_success_telegram_join_request(client, monkeypatch):
    session = make_verification_session()
    join_request = make_join_request()
    monkeypatch.setattr(
        "src.api.routes.verification.get_verification_session",
        AsyncMock(return_value=session),
    )
    monkeypatch.setattr(
        "src.api.routes.verification.complete_verification",
        AsyncMock(return_value=True),
    )
    monkeypatch.setattr(
        "src.api.routes.verification.get_join_request_by_token",
        AsyncMock(return_value=join_request),
    )
    monkeypatch.setattr(
        "src.api.routes.verification.auto_approve_user",
        AsyncMock(return_value=ApprovalResult(True)),
    )

    response = await client.post(VERIFY_URL, json=VERIFY_PAYLOAD)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["redirect_url"] == "tg://"


@pytest.mark.asyncio
async def test_verify_success_when_auto_approve_fails(client, monkeypatch):
    """Captcha success should still return success even if Telegram approval fails."""
    session = make_verification_session()
    join_request = make_join_request()
    monkeypatch.setattr(
        "src.api.routes.verification.get_verification_session",
        AsyncMock(return_value=session),
    )
    monkeypatch.setattr(
        "src.api.routes.verification.complete_verification",
        AsyncMock(return_value=True),
    )
    monkeypatch.setattr(
        "src.api.routes.verification.get_join_request_by_token",
        AsyncMock(return_value=join_request),
    )
    monkeypatch.setattr(
        "src.api.routes.verification.auto_approve_user",
        AsyncMock(return_value=ApprovalResult(False, "Bot 无权限")),
    )

    response = await client.post(VERIFY_URL, json=VERIFY_PAYLOAD)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data.get("redirect_url") is None


@pytest.mark.asyncio
async def test_verify_api_request_with_valid_chat_auto_approves(client, monkeypatch):
    session = make_verification_session(chat_id=0)
    join_request = make_join_request(request_type="api", chat_id=-100999)
    monkeypatch.setattr(
        "src.api.routes.verification.get_verification_session",
        AsyncMock(return_value=session),
    )
    monkeypatch.setattr(
        "src.api.routes.verification.complete_verification",
        AsyncMock(return_value=True),
    )
    monkeypatch.setattr(
        "src.api.routes.verification.get_join_request_by_token",
        AsyncMock(return_value=join_request),
    )
    approve_mock = AsyncMock(return_value=ApprovalResult(True))
    monkeypatch.setattr(
        "src.api.routes.verification.auto_approve_user",
        approve_mock,
    )

    response = await client.post(VERIFY_URL, json=VERIFY_PAYLOAD)

    assert response.status_code == 200
    approve_mock.assert_awaited_once_with("test-token")


@pytest.mark.asyncio
async def test_verify_api_request_without_chat_skips_approval(client, monkeypatch):
    session = make_verification_session(chat_id=0)
    join_request = make_join_request(request_type="api", chat_id=0)
    monkeypatch.setattr(
        "src.api.routes.verification.get_verification_session",
        AsyncMock(return_value=session),
    )
    monkeypatch.setattr(
        "src.api.routes.verification.complete_verification",
        AsyncMock(return_value=True),
    )
    monkeypatch.setattr(
        "src.api.routes.verification.get_join_request_by_token",
        AsyncMock(return_value=join_request),
    )
    approve_mock = AsyncMock(return_value=ApprovalResult(True))
    monkeypatch.setattr(
        "src.api.routes.verification.auto_approve_user",
        approve_mock,
    )

    response = await client.post(VERIFY_URL, json=VERIFY_PAYLOAD)

    assert response.status_code == 200
    approve_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_verify_session_not_found(client, monkeypatch):
    monkeypatch.setattr(
        "src.api.routes.verification.get_verification_session",
        AsyncMock(return_value=None),
    )

    response = await client.post(VERIFY_URL, json=VERIFY_PAYLOAD)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_verify_session_expired(client, monkeypatch):
    session = make_verification_session(expired=True)
    monkeypatch.setattr(
        "src.api.routes.verification.get_verification_session",
        AsyncMock(return_value=session),
    )

    response = await client.post(VERIFY_URL, json=VERIFY_PAYLOAD)

    assert response.status_code == 400
    assert "过期" in response.json()["detail"]


@pytest.mark.asyncio
async def test_verify_already_completed(client, monkeypatch):
    session = make_verification_session(captcha_completed=True)
    monkeypatch.setattr(
        "src.api.routes.verification.get_verification_session",
        AsyncMock(return_value=session),
    )

    response = await client.post(VERIFY_URL, json=VERIFY_PAYLOAD)

    assert response.status_code == 400
    assert "已完成" in response.json()["detail"]


@pytest.mark.asyncio
async def test_verify_user_id_mismatch(client, monkeypatch):
    session = make_verification_session(user_id=111)
    monkeypatch.setattr(
        "src.api.routes.verification.get_verification_session",
        AsyncMock(return_value=session),
    )

    response = await client.post(
        VERIFY_URL,
        json={**VERIFY_PAYLOAD, "user_id": 999},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_verify_captcha_failure(client, monkeypatch, mock_captcha_provider):
    session = make_verification_session()
    mock_captcha_provider.verify = AsyncMock(
        return_value=CaptchaVerificationResult(
            success=False,
            error_code="invalid-input-response",
            error_message="验证码无效",
        )
    )
    monkeypatch.setattr(
        "src.api.routes.verification.get_verification_session",
        AsyncMock(return_value=session),
    )

    response = await client.post(VERIFY_URL, json=VERIFY_PAYLOAD)

    assert response.status_code == 400
    assert "验证码无效" in response.json()["detail"]


@pytest.mark.asyncio
async def test_verify_complete_verification_db_failure(client, monkeypatch):
    session = make_verification_session()
    monkeypatch.setattr(
        "src.api.routes.verification.get_verification_session",
        AsyncMock(return_value=session),
    )
    monkeypatch.setattr(
        "src.api.routes.verification.complete_verification",
        AsyncMock(return_value=False),
    )

    response = await client.post(VERIFY_URL, json=VERIFY_PAYLOAD)

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_verification_status(client, monkeypatch):
    session = make_verification_session(captcha_completed=True)
    join_request = make_join_request(status="pending")
    monkeypatch.setattr(
        "src.api.routes.verification.get_verification_session",
        AsyncMock(return_value=session),
    )
    monkeypatch.setattr(
        "src.api.routes.verification.get_join_request_by_token",
        AsyncMock(return_value=join_request),
    )

    response = await client.get("/api/v1/verification-status/test-token")

    assert response.status_code == 200
    data = response.json()
    assert data["token"] == "test-token"
    assert data["completed"] is True
    assert data["expired"] is False
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_verification_status_not_found(client, monkeypatch):
    monkeypatch.setattr(
        "src.api.routes.verification.get_verification_session",
        AsyncMock(return_value=None),
    )

    response = await client.get("/api/v1/verification-status/missing")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_captcha_config(client):
    response = await client.get("/api/v1/captcha-config")

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "hcaptcha"
    assert data["captcha"]["site_key"] == "test-site-key"
