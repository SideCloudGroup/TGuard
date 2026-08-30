"""Unit tests for utilities and models."""

from datetime import datetime, timedelta

from src.database.models import VerificationSession
from src.utils.crypto import generate_session_id, generate_verification_token
from src.utils.exceptions import InvalidTokenError, SessionExpiredError
from src.utils.markdown import escape_markdown_v2, format_user_mention


def test_generate_verification_token_length_and_charset():
    token = generate_verification_token(32)
    assert len(token) == 32
    assert token.isalnum()
    assert generate_verification_token() != generate_verification_token()


def test_generate_session_id_is_urlsafe():
    session_id = generate_session_id()
    assert len(session_id) > 0
    assert generate_session_id() != generate_session_id()


def test_escape_markdown_v2():
    assert escape_markdown_v2("") == ""
    assert escape_markdown_v2("hello_world!") == "hello\\_world\\!"
    assert escape_markdown_v2("a.b") == "a\\.b"


def test_format_user_mention():
    assert format_user_mention("alice", "Alice") == "@alice"
    assert format_user_mention("", "Bob_1") == "Bob\\_1"


def test_session_expired_error():
    err = SessionExpiredError("abc")
    assert err.token == "abc"
    assert err.error_code == "session_expired"


def test_invalid_token_error():
    err = InvalidTokenError("xyz")
    assert err.token == "xyz"
    assert err.error_code == "invalid_token"


def test_verification_session_is_expired():
    expired = VerificationSession(
        token="t1",
        user_id=1,
        chat_id=2,
        expires_at=datetime.utcnow() - timedelta(seconds=1),
    )
    active = VerificationSession(
        token="t2",
        user_id=1,
        chat_id=2,
        expires_at=datetime.utcnow() + timedelta(minutes=5),
    )
    assert expired.is_expired is True
    assert active.is_expired is False
