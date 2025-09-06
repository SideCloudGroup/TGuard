"""Configuration management for TGuard bot."""

import toml
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass
from functools import lru_cache


@dataclass
class BotConfig:
    """Bot configuration."""
    token: str
    verification_timeout: int
    welcome_message: str
    verification_button_text: str


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
class CaptchaConfig:
    """Captcha configuration."""
    provider: str
    expire_minutes: int
    timeout_seconds: int
    hcaptcha: CaptchaProviderConfig
    recaptcha: CaptchaProviderConfig


@dataclass
class APIConfig:
    """API server configuration."""
    host: str
    port: int
    base_url: str


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str
    format: str


@dataclass
class Config:
    """Main configuration class."""
    bot: BotConfig
    database: DatabaseConfig
    captcha: CaptchaConfig
    api: APIConfig
    logging: LoggingConfig


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
            recaptcha=CaptchaProviderConfig(**data['captcha']['recaptcha'])
        ),
        api=APIConfig(**data['api']),
        logging=LoggingConfig(**data['logging'])
    )


# Global config instance
config = load_config()
