import logging

import pytest

from app.core.config.log_redaction import SecretRedactionFilter
from app.core.config.logging_config import (
    create_console_handler,
    create_error_handler,
    create_file_handler,
)


def _filtered_message(msg: str, *args) -> str:
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname=__file__, lineno=1,
        msg=msg, args=args, exc_info=None,
    )
    SecretRedactionFilter().filter(record)
    return record.getMessage()


@pytest.mark.parametrize(
    "param",
    [
        "api_key", "apikey", "key", "token", "secret", "password", "passwd",
        "pwd", "access_token", "auth", "API_KEY", "Token",
    ],
)
def test_redacts_query_param_secrets(param):
    message = f"GET failed: https://example.com/v1?{param}=abcDEF123&foo=bar"
    result = _filtered_message(message)
    assert "abcDEF123" not in result
    assert f"{param}=***REDACTED***" in result
    assert "foo=bar" in result


def test_redacts_bearer_token():
    message = "Request failed with Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.abc-def_123=="
    result = _filtered_message(message)
    assert "eyJhbGciOiJIUzI1NiJ9.abc-def_123==" not in result
    assert "Bearer ***REDACTED***" in result


def test_redacts_ipqualityscore_path_embedded_key():
    message = "https://www.ipqualityscore.com/api/json/ip/AbCdEf123456/8.8.8.8 -> 403"
    result = _filtered_message(message)
    assert "AbCdEf123456" not in result
    assert "ipqualityscore.com/api/json/ip/***REDACTED***/" in result


def test_leaves_non_secret_messages_unchanged():
    message = "Fetched 12 articles from feed https://example.com/rss?page=2"
    assert _filtered_message(message) == message


def test_applies_lazy_percent_formatting_before_redaction():
    # Mirrors real call sites like logger.error("failed: %s", url_with_key)
    result = _filtered_message("failed: %s", "https://example.com?token=SECRETVALUE")
    assert "SECRETVALUE" not in result
    assert "token=***REDACTED***" in result


@pytest.mark.parametrize(
    "handler_factory",
    [
        lambda tmp_path: create_console_handler(logging.INFO),
        lambda tmp_path: create_file_handler(tmp_path / "app.log", logging.INFO, 1024, 1),
        lambda tmp_path: create_error_handler(tmp_path / "errors.log", 1024, 1),
    ],
    ids=["console_handler", "file_handler", "error_handler"],
)
def test_handler_factories_attach_redaction_filter(tmp_path, handler_factory):
    handler = handler_factory(tmp_path)
    assert any(isinstance(f, SecretRedactionFilter) for f in handler.filters)
