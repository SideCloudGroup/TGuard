"""Cloudflare Turnstile captcha provider implementation."""

from typing import Dict, Any, Optional

from .base import CaptchaProvider, CaptchaVerificationResult


class TurnstileProvider(CaptchaProvider):
    """Cloudflare Turnstile verification provider."""

    VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

    @property
    def provider_name(self) -> str:
        return "turnstile"

    async def verify(
            self,
            response: str,
            remote_ip: Optional[str] = None,
            user_agent: Optional[str] = None
    ) -> CaptchaVerificationResult:
        """Verify Turnstile response."""
        data = {
            "secret": self.secret_key,
            "response": response,
        }
        if remote_ip:
            data["remoteip"] = remote_ip

        return await self._siteverify(self.VERIFY_URL, data=data)

    def get_frontend_config(self) -> Dict[str, Any]:
        """Get Turnstile frontend configuration."""
        return {
            "provider": "turnstile",
            "siteKey": self.site_key,
            "theme": "light",
            "size": "normal",
            "language": "zh-CN"
        }
