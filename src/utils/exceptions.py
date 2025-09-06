"""Custom exceptions for TGuard bot."""

from typing import Optional


class TGuardError(Exception):
    """Base exception for TGuard bot."""

    def __init__(self, message: str, error_code: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class DatabaseError(TGuardError):
    """Database operation error."""
    pass


class CaptchaError(TGuardError):
    """Captcha verification error."""
    pass


class ConfigurationError(TGuardError):
    """Configuration error."""
    pass


class TelegramAPIError(TGuardError):
    """Telegram API error."""
    pass


class VerificationError(TGuardError):
    """Verification process error."""
    pass


class TokenError(TGuardError):
    """Token validation error."""
    pass


class SessionExpiredError(VerificationError):
    """Verification session expired."""

    def __init__(self, token: str):
        super().__init__(f"Verification session expired: {token}", "session_expired")
        self.token = token


class InvalidTokenError(TokenError):
    """Invalid verification token."""

    def __init__(self, token: str):
        super().__init__(f"Invalid verification token: {token}", "invalid_token")
        self.token = token


class CaptchaValidationError(CaptchaError):
    """Captcha validation failed."""

    def __init__(self, reason: str):
        super().__init__(f"Captcha validation failed: {reason}", "captcha_failed")
        self.reason = reason


class AutoApprovalError(TelegramAPIError):
    """Auto-approval failed."""

    def __init__(self, reason: str, user_id: int, chat_id: int):
        super().__init__(f"Auto-approval failed: {reason}", "approval_failed")
        self.reason = reason
        self.user_id = user_id
        self.chat_id = chat_id
