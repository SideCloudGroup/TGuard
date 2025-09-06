"""Captcha provider factory."""

import logging
from typing import Dict, Type

from .base import CaptchaProvider
from .hcaptcha import HCaptchaProvider
from src.config.settings import config

logger = logging.getLogger(__name__)

# Registry of available captcha providers
CAPTCHA_PROVIDERS: Dict[str, Type[CaptchaProvider]] = {
    "hcaptcha": HCaptchaProvider,
    # Add more providers here as needed
    # "recaptcha": ReCaptchaProvider,
    # "turnstile": TurnstileProvider,
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
    
    # Get provider-specific configuration
    if provider_name == "hcaptcha":
        provider_config = config.captcha.hcaptcha
    elif provider_name == "recaptcha":
        provider_config = config.captcha.recaptcha
    else:
        raise ValueError(f"No configuration found for provider: {provider_name}")
    
    # Validate configuration
    if not provider_config.site_key or not provider_config.secret_key:
        raise ValueError(
            f"Missing configuration for {provider_name}. "
            f"Please set site_key and secret_key in config.toml"
        )
    
    # Create provider instance
    provider = provider_class(
        site_key=provider_config.site_key,
        secret_key=provider_config.secret_key,
        timeout=config.captcha.timeout_seconds
    )
    
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
