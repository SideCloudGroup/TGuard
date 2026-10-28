"""Captcha provider factory."""

import logging
from typing import Dict, Optional, Type

from src.config.settings import config
from .base import CaptchaProvider
from .cap import CapProvider
from .hcaptcha import HCaptchaProvider
from .turnstile import TurnstileProvider

logger = logging.getLogger(__name__)

# Registry of available captcha providers
CAPTCHA_PROVIDERS: Dict[str, Type[CaptchaProvider]] = {
    "hcaptcha": HCaptchaProvider,
    "cap": CapProvider,
    "turnstile": TurnstileProvider,
}


def create_captcha_provider() -> CaptchaProvider:
    """Create captcha provider based on configuration."""
    provider_name = config.captcha.provider.lower()

    if provider_name not in CAPTCHA_PROVIDERS:
        available = ", ".join(CAPTCHA_PROVIDERS.keys())
        raise ValueError(
            f"Unknown captcha provider: {provider_name}. "
            f"Available providers: {available}"
        )

    provider_config = getattr(config.captcha, provider_name)
    kwargs = {
        "site_key": provider_config.site_key,
        "secret_key": provider_config.secret_key,
        "timeout": config.captcha.timeout_seconds,
    }
    if provider_name == "cap":
        kwargs["server_url"] = provider_config.server_url

    missing = [key for key in ("server_url", "site_key", "secret_key") if key in kwargs and not kwargs[key]]
    if missing:
        raise ValueError(
            f"Missing configuration for {provider_name}. "
            f"Please set {', '.join(missing)} in config.toml"
        )

    provider = CAPTCHA_PROVIDERS[provider_name](**kwargs)
    logger.info(f"Created captcha provider: {provider_name}")
    return provider


# Global provider instance
_captcha_provider: Optional[CaptchaProvider] = None


def get_captcha_provider() -> CaptchaProvider:
    """Get the global captcha provider instance."""
    global _captcha_provider

    if _captcha_provider is None:
        _captcha_provider = create_captcha_provider()

    return _captcha_provider


async def close_captcha_provider() -> None:
    """Release resources held by the global captcha provider."""
    if _captcha_provider is not None:
        await _captcha_provider.aclose()
