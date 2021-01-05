import logging

from birdfeeder.logging import init_logging, read_logging_config


def test_read_logging_config():
    config = read_logging_config("common_logging.yml")
    assert "formatters" in config
    assert "handlers" in config
    assert "root" in config


def test_init_logging():
    init_logging("test_logging.yml")
    log = logging.getLogger("testlogger")
    assert log.getEffectiveLevel() is logging.DEBUG
