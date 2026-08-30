"""Shared pytest fixtures."""

import shutil
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

WORKSPACE = Path(__file__).resolve().parents[1]
CONFIG_PATH = WORKSPACE / "config.toml"

if not CONFIG_PATH.exists():
    shutil.copy(WORKSPACE / "config.example.toml", CONFIG_PATH)


@pytest.fixture
def mock_captcha_provider():
    """Minimal captcha provider for API and template tests."""
    from src.captcha.base import CaptchaVerificationResult

    provider = MagicMock()
    provider.provider_name = "hcaptcha"
    provider.get_frontend_config.return_value = {
        "provider": "hcaptcha",
        "site_key": "test-site-key",
    }
    provider.verify = AsyncMock(
        return_value=CaptchaVerificationResult(success=True)
    )
    return provider


@pytest.fixture
async def client(monkeypatch, mock_captcha_provider):
    """HTTP client against the FastAPI app without a real database."""
    monkeypatch.setattr("src.api.main.init_database", AsyncMock())
    monkeypatch.setattr("src.api.main.close_database", AsyncMock())
    monkeypatch.setattr(
        "src.captcha.factory._captcha_provider",
        mock_captcha_provider,
    )

    from src.api.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def db_session(monkeypatch):
    """In-memory SQLite session factory patched into database operations."""
    from src.database.models import Base

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    monkeypatch.setattr("src.database.operations.get_session", lambda: factory)
    yield factory
    await engine.dispose()


def make_verification_session(
    *,
    token: str = "test-token",
    user_id: int = 123456,
    chat_id: int = -100123456,
    captcha_completed: bool = False,
    expired: bool = False,
):
    """Build a VerificationSession instance for route tests."""
    from src.database.models import VerificationSession

    expires_at = datetime.utcnow() - timedelta(hours=1)
    if not expired:
        expires_at = datetime.utcnow() + timedelta(hours=1)

    return VerificationSession(
        token=token,
        user_id=user_id,
        chat_id=chat_id,
        captcha_completed=captcha_completed,
        created_time=datetime.utcnow(),
        expires_at=expires_at,
    )


def make_join_request(
    *,
    token: str = "test-token",
    user_id: int = 123456,
    chat_id: int = -100123456,
    request_type: str = "telegram",
    status: str = "pending",
):
    """Build a JoinRequest instance for route tests."""
    from src.database.models import JoinRequest

    return JoinRequest(
        user_id=user_id,
        chat_id=chat_id,
        first_name="Test",
        verification_token=token,
        request_type=request_type,
        status=status,
    )
