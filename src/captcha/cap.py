"""Cap.js captcha provider implementation."""

import logging
from typing import Dict, Any, Optional

import httpx

from .base import CaptchaProvider, CaptchaVerificationResult

logger = logging.getLogger(__name__)


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
        try:
            # Prepare verification data
            data = {
                "secret": self.secret_key,
                "response": response,
            }

            if remote_ip:
                data["remoteip"] = remote_ip

            # Make verification request to Cap.js server
            verify_url = f"{self.server_url}/{self.site_key}/siteverify"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response_obj = await client.post(
                    verify_url,
                    json=data,  # Cap.js typically uses JSON
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": user_agent or "TGuard-Bot/1.0"
                    }
                )

                response_obj.raise_for_status()
                result = response_obj.json()

                logger.info(f"Cap verification response: {result}")

                # Cap.js typically returns {"success": true/false, ...}
                success = result.get('success', False)

                if success:
                    return CaptchaVerificationResult(
                        success=True,
                        challenge_ts=result.get('challenge_ts'),
                        hostname=result.get('hostname'),
                        score=result.get('score'),
                        extra_data=result
                    )
                else:
                    error_codes = result.get('error-codes', ['verification-failed'])
                    error_code = error_codes[0] if error_codes else 'unknown-error'

                    # Map Cap.js error codes to user-friendly messages
                    error_messages = {
                        'missing-input-secret': '缺少密钥配置',
                        'invalid-input-secret': '密钥配置错误',
                        'missing-input-response': '缺少验证响应',
                        'invalid-input-response': '验证响应无效',
                        'bad-request': '请求格式错误',
                        'timeout-or-duplicate': '验证超时或重复提交',
                        'verification-failed': '验证失败，请重试',
                    }

                    error_message = error_messages.get(error_code, '验证失败，请重试')

                    return CaptchaVerificationResult(
                        success=False,
                        error_code=error_code,
                        error_message=error_message,
                        extra_data=result
                    )

        except httpx.HTTPStatusError as e:
            logger.error(f"Cap verification HTTP error: {e}")
            return CaptchaVerificationResult(
                success=False,
                error_code='http-error',
                error_message='验证服务暂时不可用，请稍后重试'
            )
        except httpx.RequestError as e:
            logger.error(f"Cap verification network error: {e}")
            return CaptchaVerificationResult(
                success=False,
                error_code='network-error',
                error_message='网络连接失败，请检查网络后重试'
            )
        except Exception as e:
            logger.error(f"Cap verification unexpected error: {e}")
            return CaptchaVerificationResult(
                success=False,
                error_code='internal-error',
                error_message='服务器内部错误，请稍后重试'
            )

    def get_frontend_config(self) -> Dict[str, Any]:
        """Get frontend configuration for Cap.js widget."""
        return {
            'provider': 'cap',
            'server_url': self.server_url,
            'site_key': self.site_key,
            'endpoint': f"{self.server_url}/{self.site_key}/"  # Cap.js URL format: server_url/site_key
        }
