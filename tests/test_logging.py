import logging
import os
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
    config = read_logging_config("conf/common_logging.yml")
    assert "formatters" in config
    assert "handlers" in config
    assert "root" in config
    assert config["handlers"]["file_handler"]["filename"] == os.path.join(os.getcwd(), "logs/test.log")


def test_init_logging():
    init_logging("conf/test_logging.yml")
    log = logging.getLogger("testlogger")
    assert log.getEffectiveLevel() is logging.DEBUG
    assert log.propagate == 0


def test_init_logging_existing():
    log = logging.getLogger("existing1")
    init_logging("conf/test_logging.yml", keep_existing=False)
    assert log.disabled is True

    log = logging.getLogger("existing2")
    log.setLevel(logging.DEBUG)
    init_logging("conf/test_logging.yml", keep_existing=True)
    assert log.disabled is False
    assert log.getEffectiveLevel() == logging.DEBUG


def test_child_loggers_python_native():
    """Demo test to show python logging behavior."""
    # Child logger is initialized without setting level explicitly
    child = logging.getLogger("parent.child")
    parent = logging.getLogger("parent")
    # Then we're setting level on parent logger
    parent.setLevel(logging.INFO)
    # Child logger level is now same as the parent
    assert child.getEffectiveLevel() == logging.INFO


def test_child_loggers_init_logging():
    """Check that init_logging behaviour is identical to python logging as shown in test_child_loggers_python_native."""
    child = logging.getLogger("parent.child")
    init_logging("conf/test_logging.yml", keep_existing=True)
    parent = logging.getLogger("parent")
    parent.setLevel(logging.INFO)
    assert child.getEffectiveLevel() == logging.INFO
