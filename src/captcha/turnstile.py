"""Cloudflare Turnstile captcha provider implementation."""

import logging
from typing import Dict, Any, Optional

import httpx

from .base import CaptchaProvider, CaptchaVerificationResult

logger = logging.getLogger(__name__)


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
        try:
            # Prepare verification data
            data = {
                "secret": self.secret_key,
                "response": response,
                "remoteip": remote_ip or ""
            }

            # Make verification request
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response_obj = await client.post(
                    self.VERIFY_URL,
                    data=data,
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "User-Agent": user_agent or "TGuard-Bot/1.0"
                    }
                )

                response_obj.raise_for_status()
                result = response_obj.json()

            # Parse response
            success = result.get("success", False)

            if success:
                logger.info("Turnstile verification successful")
                return CaptchaVerificationResult(
                    success=True,
                    challenge_ts=result.get("challenge_ts"),
                    hostname=result.get("hostname"),
                    extra_data=result
                )
            else:
                error_codes = result.get("error-codes", [])
                error_code = error_codes[0] if error_codes else "unknown-error"
                error_message = self._get_error_message(error_code)

                logger.warning(f"Turnstile verification failed: {error_code}")
                return CaptchaVerificationResult(
                    success=False,
                    error_code=error_code,
                    error_message=error_message,
                    extra_data=result
                )

        except httpx.RequestError as e:
            logger.error(f"Turnstile request error: {e}")
            return CaptchaVerificationResult(
                success=False,
                error_code="network-error",
                error_message="网络连接错误，请重试"
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"Turnstile HTTP error: {e}")
            return CaptchaVerificationResult(
                success=False,
                error_code="http-error",
                error_message="验证服务暂时不可用"
            )
        except Exception as e:
            logger.error(f"Turnstile unexpected error: {e}")
            return CaptchaVerificationResult(
                success=False,
                error_code="internal-error",
                error_message="验证过程中发生错误"
            )

    def get_frontend_config(self) -> Dict[str, Any]:
        """Get Turnstile frontend configuration."""
        return {
            "provider": "turnstile",
            "siteKey": self.site_key,
            "theme": "light",
            "size": "normal",
            "language": "zh-CN"
        }

    def _get_error_message(self, error_code: str) -> str:
        """Get user-friendly error message for error code."""
        error_messages = {
            "missing-input-secret": "配置错误：缺少密钥",
            "invalid-input-secret": "配置错误：无效密钥",
            "missing-input-response": "请完成验证",
            "invalid-input-response": "验证已过期，请重新验证",
            "bad-request": "请求格式错误",
            "timeout-or-duplicate": "验证超时或重复提交",
            "internal-error": "内部错误，请重试"
        }

        return error_messages.get(error_code, f"验证失败：{error_code}")
