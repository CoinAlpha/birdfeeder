import logging
from unittest.mock import patch

from birdfeeder.logging import Formatter, configure_logging_formatter, init_logging, read_logging_config


def test_formatter():
    all_formats = Formatter.all()
    assert "VERBOSE" in all_formats
    assert "JSON" in all_formats


def test_configure_logging_formatter():
    log = logging.getLogger("testlogger")
    with patch.object(log, "addHandler") as mock_addhandler:
        configure_logging_formatter()
        mock_addhandler.assert_called_once()
        assert log.propagate is False


def test_read_logging_config():
    config = read_logging_config("common_logging.yml")
    assert "formatters" in config
    assert "handlers" in config
    assert "root" in config


def test_init_logging():
    init_logging("test_logging.yml")
    log = logging.getLogger("testlogger")
    assert log.getEffectiveLevel() is logging.DEBUG
