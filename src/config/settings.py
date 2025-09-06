"""Configuration management for TGuard bot."""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import toml


@dataclass
class BotConfig:
    """Bot configuration."""
    token: str
    verification_timeout: int
    verification_button_text: str
    admin_ids: list[int]


@dataclass
class DatabaseConfig:
    """Database configuration."""
    host: str
    port: int
    name: str
    user: str
    password: str
    min_size: int
    max_size: int

    @property
    def url(self) -> str:
        """Get database URL for asyncpg."""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


@dataclass
class CaptchaProviderConfig:
    """Captcha provider specific configuration."""
    site_key: str
    secret_key: str


@dataclass
class CapCaptchaConfig:
    """Cap.js captcha specific configuration."""
    server_url: str
    site_key: str
    secret_key: str


@dataclass
class TurnstileCaptchaConfig:
    """Turnstile captcha specific configuration."""
    site_key: str
    secret_key: str


@dataclass
class CaptchaConfig:
    """Captcha configuration."""
    provider: str
    expire_minutes: int
    timeout_seconds: int
    hcaptcha: CaptchaProviderConfig
    cap: CapCaptchaConfig
    turnstile: TurnstileCaptchaConfig


@dataclass
class APIConfig:
    """API server configuration."""
    host: str
    port: int
    base_url: str


@dataclass
class Config:
    """Main configuration class."""
    bot: BotConfig
    database: DatabaseConfig
    captcha: CaptchaConfig
    api: APIConfig


@lru_cache()
def load_config(config_path: str = "config.toml") -> Config:
    """Load configuration from TOML file."""
    config_file = Path(config_path)

    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_file, 'r', encoding='utf-8') as f:
        data = toml.load(f)

    return Config(
        bot=BotConfig(**data['bot']),
        database=DatabaseConfig(**data['database']),
        captcha=CaptchaConfig(
            provider=data['captcha']['provider'],
            expire_minutes=data['captcha']['expire_minutes'],
            timeout_seconds=data['captcha']['timeout_seconds'],
            hcaptcha=CaptchaProviderConfig(**data['captcha']['hcaptcha']),
            cap=CapCaptchaConfig(**data['captcha']['cap']),
            turnstile=TurnstileCaptchaConfig(**data['captcha']['turnstile'])
        ),
        api=APIConfig(**data['api'])
    )


# Global config instance
config = load_config()
