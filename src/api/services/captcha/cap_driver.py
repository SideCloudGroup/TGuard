"""Cap.js captcha driver implementation."""

import asyncio
import logging
from typing import Dict, Any, Optional

import aiohttp

from src.config.settings import CapCaptchaConfig
from .base import CaptchaInterface, CaptchaResponse

logger = logging.getLogger(__name__)


class CapCaptchaDriver(CaptchaInterface):
    """Cap.js captcha service driver."""

    def __init__(self, config: CapCaptchaConfig):
        """Initialize Cap.js driver with configuration."""
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self.session

    async def verify_token(self, token: str, user_ip: str = None) -> CaptchaResponse:
        """
        Verify Cap.js token.
        
        Args:
            token: Cap.js token from frontend
            user_ip: User's IP address (optional)
            
        Returns:
            CaptchaResponse with verification result
        """
        try:
            session = await self._get_session()

            # Prepare verification data
            verification_data = {
                'secret': self.config.secret_key,
                'response': token,
            }

            # Add IP if provided
            if user_ip:
                verification_data['remoteip'] = user_ip

            # Make verification request to Cap.js server
            verify_url = f"{self.config.server_url.rstrip('/')}/api/verify"

            async with session.post(verify_url, json=verification_data) as response:
                result = await response.json()

                logger.info(f"Cap verification response: {result}")

                # Cap.js typically returns {"success": true/false, ...}
                success = result.get('success', False)

                if success:
                    return CaptchaResponse(
                        success=True,
                        challenge_ts=result.get('challenge_ts'),
                        hostname=result.get('hostname'),
                        error_codes=[]
                    )
                else:
                    error_codes = result.get('error-codes', ['verification-failed'])
                    return CaptchaResponse(
                        success=False,
                        challenge_ts=None,
                        hostname=None,
                        error_codes=error_codes
                    )

        except aiohttp.ClientError as e:
            logger.error(f"Cap verification network error: {e}")
            return CaptchaResponse(
                success=False,
                challenge_ts=None,
                hostname=None,
                error_codes=['network-error']
            )
        except Exception as e:
            logger.error(f"Cap verification unexpected error: {e}")
            return CaptchaResponse(
                success=False,
                challenge_ts=None,
                hostname=None,
                error_codes=['internal-error']
            )

    def get_frontend_config(self) -> Dict[str, Any]:
        """
        Get frontend configuration for Cap.js.
        
        Returns:
            Dictionary with frontend configuration
        """
        return {
            'provider': 'cap',
            'server_url': self.config.server_url,
            'site_key': self.config.site_key,
        }

    async def cleanup(self):
        """Clean up resources."""
        if self.session and not self.session.closed:
            await self.session.close()

    def __del__(self):
        """Ensure session is closed on deletion."""
        if hasattr(self, 'session') and self.session and not self.session.closed:
            try:
                asyncio.create_task(self.session.close())
            except RuntimeError:
                # Event loop might be closed, ignore
                pass
