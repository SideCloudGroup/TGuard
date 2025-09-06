"""Cryptographic utilities."""

import secrets
import string


def generate_verification_token(length: int = 32) -> str:
    """Generate a secure random verification token."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_session_id(length: int = 16) -> str:
    """Generate a secure session ID."""
    return secrets.token_urlsafe(length)
