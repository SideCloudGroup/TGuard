"""Abstract base class for captcha providers."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional

import httpx

logger = logging.getLogger(__name__)

ERROR_MESSAGES: Dict[str, str] = {
    "missing-input-secret": "配置错误：缺少密钥",
    "invalid-input-secret": "配置错误：无效密钥",
    "sitekey-secret-mismatch": "配置错误：密钥不匹配",
    "missing-input-response": "请完成验证",
    "invalid-input-response": "验证已过期，请重新验证",
    "invalid-or-already-seen-response": "验证已过期或已使用，请重新验证",
    "timeout-or-duplicate": "验证超时或重复提交",
    "bad-request": "请求格式错误",
    "network-error": "网络连接失败，请重试",
    "http-error": "验证服务暂时不可用，请稍后重试",
    "internal-error": "服务器内部错误，请稍后重试",
}
DEFAULT_ERROR_MESSAGE = "验证失败，请重试"


@dataclass
class CaptchaVerificationResult:
    """Result of captcha verification."""
    success: bool
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    score: Optional[float] = None  # For services that provide confidence scores
    challenge_ts: Optional[str] = None  # Timestamp of challenge
    hostname: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None


def _failure(error_code: str, extra_data: Optional[Dict[str, Any]] = None) -> CaptchaVerificationResult:
    return CaptchaVerificationResult(
        success=False,
        error_code=error_code,
        error_message=ERROR_MESSAGES.get(error_code, DEFAULT_ERROR_MESSAGE),
        extra_data=extra_data,
    )


class CaptchaProvider(ABC):
    """Abstract base class for captcha providers."""

    def __init__(self, site_key: str, secret_key: str, timeout: int = 30):
        """Initialize captcha provider.
        
        Args:
            site_key: Public site key for frontend
            secret_key: Secret key for backend verification
            timeout: HTTP timeout in seconds
        """
        self.site_key = site_key
        self.secret_key = secret_key
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.AsyncClient:
        """Get the shared HTTP client, creating it on first use."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={"User-Agent": "TGuard/1.0"},
            )
        return self._client

    async def aclose(self) -> None:
        """Close the shared HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _siteverify(
            self,
            url: str,
            *,
            data: Optional[Dict[str, Any]] = None,
            json: Optional[Dict[str, Any]] = None,
    ) -> CaptchaVerificationResult:
        """POST to a reCAPTCHA-compatible siteverify endpoint and parse the result."""
        try:
            response = await self._get_client().post(url, data=data, json=json)
            response.raise_for_status()
            result = response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"{self.provider_name} verification HTTP error: {e}")
            return _failure("http-error")
        except httpx.RequestError as e:
            logger.error(f"{self.provider_name} verification network error: {e}")
            return _failure("network-error")
        except ValueError as e:
            logger.error(f"{self.provider_name} verification returned invalid JSON: {e}")
            return _failure("internal-error")

        if result.get("success"):
            return CaptchaVerificationResult(
                success=True,
                challenge_ts=result.get("challenge_ts"),
                hostname=result.get("hostname"),
                score=result.get("score"),
                extra_data=result,
            )

        error_codes = result.get("error-codes") or ["verification-failed"]
        logger.warning(f"{self.provider_name} verification failed: {error_codes}")
        return _failure(error_codes[0], extra_data=result)

    @abstractmethod
    async def verify(
            self,
            response: str,
            remote_ip: Optional[str] = None,
            user_agent: Optional[str] = None
    ) -> CaptchaVerificationResult:
        """Verify captcha response.
        
        Args:
            response: The captcha response token from frontend
            remote_ip: User's IP address (optional)
            user_agent: User's user agent (optional)
            
        Returns:
            CaptchaVerificationResult with verification status and details
        """
        pass

    @abstractmethod
    def get_frontend_config(self) -> Dict[str, Any]:
        """Get configuration for frontend integration.
        
        Returns:
            Dictionary containing frontend configuration
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get provider name."""
        pass
