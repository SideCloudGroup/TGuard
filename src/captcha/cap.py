"""Cap.js captcha provider implementation."""

from typing import Dict, Any, Optional

from .base import CaptchaProvider, CaptchaVerificationResult


class CapProvider(CaptchaProvider):
    """Cap.js verification provider."""

    def __init__(self, server_url: str, site_key: str, secret_key: str, timeout: int = 30):
        """Initialize Cap provider.
        
        Args:
            server_url: Cap.js server URL
            site_key: Public site key for frontend
            secret_key: Secret key for backend verification
            timeout: HTTP timeout in seconds
        """
        super().__init__(site_key, secret_key, timeout)
        self.server_url = server_url.rstrip('/')

    @property
    def provider_name(self) -> str:
        return "cap"

    async def verify(
            self,
            response: str,
            remote_ip: Optional[str] = None,
            user_agent: Optional[str] = None
    ) -> CaptchaVerificationResult:
        """Verify Cap.js response."""
        return await self._siteverify(
            f"{self.server_url}/{self.site_key}/siteverify",
            json={"secret": self.secret_key, "response": response},
        )

    def get_frontend_config(self) -> Dict[str, Any]:
        """Get frontend configuration for Cap.js widget."""
        return {
            'provider': 'cap',
            'server_url': self.server_url,
            'site_key': self.site_key,
            'endpoint': f"{self.server_url}/{self.site_key}/"  # Cap.js URL format: server_url/site_key
        }
