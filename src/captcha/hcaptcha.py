"""hCaptcha provider implementation."""

from typing import Dict, Any, Optional

from .base import CaptchaProvider, CaptchaVerificationResult


class HCaptchaProvider(CaptchaProvider):
    """hCaptcha verification provider."""

    VERIFY_URL = "https://hcaptcha.com/siteverify"

    @property
    def provider_name(self) -> str:
        return "hcaptcha"

    async def verify(
            self,
            response: str,
            remote_ip: Optional[str] = None,
            user_agent: Optional[str] = None
    ) -> CaptchaVerificationResult:
        """Verify hCaptcha response."""
        data = {
            "secret": self.secret_key,
            "response": response,
            "sitekey": self.site_key
        }
        if remote_ip:
            data["remoteip"] = remote_ip

        return await self._siteverify(self.VERIFY_URL, data=data)

    def get_frontend_config(self) -> Dict[str, Any]:
        """Get hCaptcha frontend configuration."""
        return {
            "provider": "hcaptcha",
            "siteKey": self.site_key,
            "theme": "light",
            "size": "normal"
        }
