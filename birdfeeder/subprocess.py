import logging
import os
import threading
from typing import TextIO

__all__ = ["ThreadedLogPipe"]


class ThreadedLogPipe(threading.Thread):
    """
    Enables a subprocess to send its stdout/stderr to a logger.

    >>> import logging
    >>> import subprocess
    >>> import sys
    >>> logger = logging.getLogger("myprog")
    >>> logger.setLevel(logging.DEBUG)
    >>> # NOTE: stdout must be used for doctest to see output
    >>> handler = logging.StreamHandler(sys.stdout)
    >>> handler.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
    >>> logger.addHandler(handler)
    >>>
    >>> subprocess.run(["echo", "Hello, World!"], stdout=ThreadedLogPipe(logger, logging.DEBUG))
    DEBUG:myprog:Hello, World!
    CompletedProcess(args=['echo', 'Hello, World!'], returncode=0)
    """

    logger: logging.Logger
    level: int
    fd_read: int
    fd_write: int
    pipe_reader: TextIO

    def __init__(self, logger: logging.Logger, level: int):
        self.logger: logging.Logger = logger
        self.level: int = level
        self.fd_read, self.fd_write = os.pipe()
        self.pipe_reader = os.fdopen(self.fd_read)
        self.lines_written: int = 0

        super().__init__(
            name=f"{self.__class__.__name__} {logging.getLevelName(self.level)} to {self.logger!r}",
            daemon=True,
        )

        self.start()

    def fileno(self):
        """Return the write file descriptor of the pipe."""
        return self.fd_write

    def close(self):
        """Close the write end of the pipe."""
        os.close(self.fd_write)

    def run(self):
        """Reads all pipe input in separate thread and logs to configured logger."""
        for line in iter(self.pipe_reader.readline, ""):
            self.logger.log(self.level, line.strip("\n"))
            self.lines_written += 1

        self.pipe_reader.close()
