"""Unit tests for verification route helpers."""

from unittest.mock import MagicMock

from src.api.routes.verification import get_client_ip


def _request_with_headers(headers: dict, client_host: str = "1.2.3.4"):
    request = MagicMock()
    request.headers.get.side_effect = lambda key, default=None: headers.get(key, default)
    request.client.host = client_host
    return request


def test_get_client_ip_from_x_forwarded_for():
    request = _request_with_headers(
        {"X-Forwarded-For": "203.0.113.1, 10.0.0.1"},
    )
    assert get_client_ip(request) == "203.0.113.1"


def test_get_client_ip_from_x_real_ip():
    request = _request_with_headers({"X-Real-IP": "198.51.100.2"})
    assert get_client_ip(request) == "198.51.100.2"


def test_get_client_ip_fallback_to_client_host():
    request = _request_with_headers({})
    assert get_client_ip(request) == "1.2.3.4"
