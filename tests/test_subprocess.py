import logging
import subprocess
import time

import pytest

from birdfeeder.subprocess import ThreadedLogPipe


def test_threaded_log_pipe(caplog):
    logger_name = "test_logger"
    logger = logging.getLogger(logger_name)

    with caplog.at_level(logging.DEBUG, logger=logger_name):
        log_pipe = ThreadedLogPipe(logger, logging.DEBUG)
        subprocess.run(["echo", "Hello, World!"], stdout=log_pipe)  # type: ignore[call-overload]

    sleep_time: float = 0.05
    total_sleep_time: float = 0
    max_sleep_time: float = 3

    while log_pipe.lines_written < 1:
        if total_sleep_time > max_sleep_time:
            pytest.fail("Log has not been written in allowed time!")
        time.sleep(sleep_time)
        total_sleep_time += sleep_time

    assert "Hello, World!" in caplog.text
