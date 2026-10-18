import json
import logging

from app.core.logging import JsonFormatter, configure_logging, request_id_context


def test_json_formatter_includes_correlation_id() -> None:
    token = request_id_context.set("logging-test-01")
    try:
        record = logging.LogRecord("test", logging.INFO, __file__, 1, "hello", (), None)
        payload = json.loads(JsonFormatter().format(record))
    finally:
        request_id_context.reset(token)

    assert payload["message"] == "hello"
    assert payload["request_id"] == "logging-test-01"
    assert payload["level"] == "INFO"


def test_configure_logging_sets_requested_level() -> None:
    configure_logging("WARNING")
    assert logging.getLogger().level == logging.WARNING


def test_json_formatter_includes_exception_text() -> None:
    try:
        raise ValueError("test exception")
    except ValueError:
        record = logging.LogRecord("test", logging.ERROR, __file__, 1, "failed", (), None)
        record.exc_info = __import__("sys").exc_info()

    payload = json.loads(JsonFormatter().format(record))
    assert "test exception" in payload["exception"]
