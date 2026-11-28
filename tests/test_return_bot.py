"""Optional external-bot navigation must not change legacy verification."""
from unittest.mock import AsyncMock
from urllib.parse import urlparse, parse_qs
import pytest
from pydantic import ValidationError
from src.api.routes.external import CreateVerificationRequest, create_verification
from tests.conftest import make_verification_session


@pytest.mark.asyncio
@pytest.mark.parametrize("username", [None, "example_bot"])
async def test_create_optional_return_bot(monkeypatch, username):
    monkeypatch.setattr("src.api.routes.external.create_join_request", AsyncMock(return_value=True))
    monkeypatch.setattr("src.api.routes.external.create_verification_session", AsyncMock(return_value=True))
    response = await create_verification(CreateVerificationRequest(user_id=123456, bot_username=username), "test")
    query = parse_qs(urlparse(response.verification_url).query)
    assert query["token"] == [response.token]
    assert query.get("return_bot") == ([username] if username else None)
    assert set(response.model_dump()) == {"token", "verification_url", "expires_at"}


@pytest.mark.parametrize("username", ["https://evil.test", "bot?start=x", "bot/name", "<script>"])
def test_reject_unsafe_username(username):
    with pytest.raises(ValidationError):
        CreateVerificationRequest(user_id=1, bot_username=username)


@pytest.mark.asyncio
@pytest.mark.parametrize("completed", [True, False])
async def test_external_page_return_and_reload(client, monkeypatch, completed):
    session = make_verification_session(captcha_completed=completed)
    session.chat_id = 0
    monkeypatch.setattr("src.api.routes.static_files.get_verification_session", AsyncMock(return_value=session))
    response = await client.get("/verify", params={"token": "test-token", "return_bot": "example_bot"})
    assert response.status_code == 200
    assert "https://t.me/example_bot?start=tg_test-token" in response.text
    assert "openTelegramLink" in response.text


@pytest.mark.asyncio
@pytest.mark.parametrize("chat_id,return_bot", [(0,None), (-123,"example_bot"), (0,"evil.test/path")])
async def test_legacy_group_or_invalid_destination_has_no_return(client, monkeypatch, chat_id, return_bot):
    session = make_verification_session()
    session.chat_id = chat_id
    monkeypatch.setattr("src.api.routes.static_files.get_verification_session", AsyncMock(return_value=session))
    params = {"token": "test-token"}
    if return_bot is not None: params["return_bot"] = return_bot
    response = await client.get("/verify", params=params)
    assert response.status_code == 200
    assert "const returnUrl = null" in response.text
