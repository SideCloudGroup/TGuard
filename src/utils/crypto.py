"""Cryptographic utilities."""

import hmac
import secrets
import string


def generate_verification_token(length: int = 32) -> str:
    """Generate a secure random verification token."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_session_id(length: int = 16) -> str:
    """Generate a secure session ID."""
    return secrets.token_urlsafe(length)


def sign_return_bot(token: str, bot_username: str, secret: str) -> str:
    """Bind an external session's return destination to the API-issued link."""
    message = f"tguard-return-bot:{token}:{bot_username}"
    return hmac.digest(secret.encode(), message.encode(), "sha256").hex()
