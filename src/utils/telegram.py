"""Telegram Web App utilities."""

import hashlib
import hmac
import json
import time
from typing import Any, Dict, Optional
from urllib.parse import parse_qsl


def validate_init_data(
        init_data: str,
        bot_token: str,
        max_age_seconds: int = 24 * 60 * 60
) -> Optional[Dict[str, Any]]:
    """Validate Telegram Web App initData and return the signed user object.

    See https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
    if not init_data or not bot_token:
        return None

    try:
        fields = dict(parse_qsl(init_data, keep_blank_values=True, strict_parsing=True))
    except ValueError:
        return None

    received_hash = fields.pop("hash", None)
    if not received_hash:
        return None

    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(fields.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_hash, received_hash):
        return None

    try:
        auth_date = int(fields.get("auth_date", ""))
        user = json.loads(fields.get("user", ""))
    except (TypeError, ValueError):
        return None

    if time.time() - auth_date > max_age_seconds:
        return None

    if not isinstance(user, dict) or not isinstance(user.get("id"), int):
        return None

    return user
