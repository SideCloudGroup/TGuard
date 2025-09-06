"""Captcha provider factory."""

import logging
from typing import Dict, Type

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

    provider_class = CAPTCHA_PROVIDERS[provider_name]

    # Get provider-specific configuration and create provider instance
    if provider_name == "hcaptcha":
        provider_config = config.captcha.hcaptcha
        # Validate configuration
        if not provider_config.site_key or not provider_config.secret_key:
            raise ValueError(
                f"Missing configuration for {provider_name}. "
                f"Please set site_key and secret_key in config.toml"
            )
        provider = provider_class(
            site_key=provider_config.site_key,
            secret_key=provider_config.secret_key,
            timeout=config.captcha.timeout_seconds
        )
    elif provider_name == "cap":
        provider_config = config.captcha.cap
        # Validate configuration
        if not provider_config.server_url or not provider_config.site_key or not provider_config.secret_key:
            raise ValueError(
                f"Missing configuration for {provider_name}. "
                f"Please set server_url, site_key and secret_key in config.toml"
            )
        provider = provider_class(
            server_url=provider_config.server_url,
            site_key=provider_config.site_key,
            secret_key=provider_config.secret_key,
            timeout=config.captcha.timeout_seconds
        )
    elif provider_name == "turnstile":
        provider_config = config.captcha.turnstile
        # Validate configuration
        if not provider_config.site_key or not provider_config.secret_key:
            raise ValueError(
                f"Missing configuration for {provider_name}. "
                f"Please set site_key and secret_key in config.toml"
            )
        provider = provider_class(
            site_key=provider_config.site_key,
            secret_key=provider_config.secret_key,
            timeout=config.captcha.timeout_seconds
        )
    else:
        raise ValueError(f"No configuration found for provider: {provider_name}")

    logger.info(f"Created captcha provider: {provider_name}")
    return provider


# Global provider instance
_captcha_provider: CaptchaProvider = None


def get_captcha_provider() -> CaptchaProvider:
    """Get the global captcha provider instance."""
    global _captcha_provider

    if _captcha_provider is None:
        _captcha_provider = create_captcha_provider()

    return _captcha_provider
