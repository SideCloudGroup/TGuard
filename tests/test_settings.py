"""Tests for configuration loading."""

from src.config.settings import CleanupConfig, load_config


MINIMAL_TOML = """
[bot]
token = "test-token"
verification_timeout = 300
verification_button_text = "verify"
admin_ids = [1]

[database]
host = "localhost"
port = 5432
name = "tguard"
user = "postgres"
password = "password"
min_size = 1
max_size = 10

[captcha]
provider = "hcaptcha"
expire_minutes = 10
timeout_seconds = 30

[captcha.hcaptcha]
site_key = "site"
secret_key = "secret"

[captcha.cap]
server_url = "https://example.com"
site_key = "site"
secret_key = "secret"

[captcha.turnstile]
site_key = "site"
secret_key = "secret"

[api]
host = "0.0.0.0"
port = 8000
base_url = "https://example.com"
"""


def test_load_config_defaults_retention_to_30_days(tmp_path):
    config_file = tmp_path / "config.toml"
    config_file.write_text(MINIMAL_TOML, encoding="utf-8")

    load_config.cache_clear()
    cfg = load_config(str(config_file))

    assert isinstance(cfg.cleanup, CleanupConfig)
    assert cfg.cleanup.retention_days == 30
    load_config.cache_clear()


def test_load_config_reads_custom_retention_days(tmp_path):
    config_file = tmp_path / "config.toml"
    config_file.write_text(MINIMAL_TOML + "\n[cleanup]\nretention_days = 7\n", encoding="utf-8")

    load_config.cache_clear()
    cfg = load_config(str(config_file))

    assert cfg.cleanup.retention_days == 7
    load_config.cache_clear()
