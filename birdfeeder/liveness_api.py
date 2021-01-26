import asyncio
import contextlib
import logging
import time
from multiprocessing import Process, Value
from typing import Optional

import pandas as pd
from aiohttp import web
from aiorun import run
from environs import Env

from .async_utils import safe_ensure_future
from .typing_local import Timestamp_ms

env = Env()
env.read_env()  # read .env file, if it exists
LIVENESS_PORT = env.int("LIVENESS_PORT", 8511)

log = logging.getLogger(__name__)


class LivenessClient:
    """Use this class (make a subclass) to override last success timestamp retrieval."""

    def __init__(self):
        self._last_successful_execution: Timestamp_ms = 0

    @property
    def last_success_timestamp(self) -> pd.Timestamp:
        return pd.Timestamp(self._last_successful_execution, unit='ms')


class WebServer:
    """Liveness API webserver to handle kubernetes liveness probes, intended to be run in a separate process."""

    def __init__(self, last_success_value: Value, max_delay: pd.Timedelta) -> None:  # type: ignore
        """
        Initialize a webserver.

        :param last_success_value: inter-process shared object (Value) to hold last success timestamp
        :param max_delay: maximum delay since last success to threat an underlying app as alive
        """
        self._last_success_value: Value = last_success_value  # type: ignore
        self._max_delay = max_delay

        self._app: web.Application = web.Application()
        self._app.router.add_get("/", self.health_check)

    @property
    def web_app(self) -> web.Application:
        return self._app

    @classmethod
    async def run_server(cls, last_success_value: Value, max_delay: pd.Timedelta, port: int) -> None:  # type: ignore
        """Launch a listening server."""
        server = cls(last_success_value, max_delay)
        runner: web.AppRunner = web.AppRunner(server.web_app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        while True:
            try:
                await asyncio.sleep(86400)
            except asyncio.CancelledError:
                await runner.cleanup()
                break

    @classmethod
    def run_in_loop(cls, *args, **kwargs):
        """Use this when you're starting the server from a separate process."""
        run(cls.run_server(*args, **kwargs), stop_on_unhandled_errors=True)

    async def health_check(self, _: web.Request) -> web.Response:
        """
        Liveness health check endpoint.

        Returns good response (200) when monitored app is healthy, and bad (418) when it's not
        """
        timestamp = self._last_success_value.value  # type: ignore
        last_success: pd.Timestamp = pd.Timestamp(timestamp, unit="s", tz="utc")
        delay: pd.Timedelta = pd.Timestamp.utcnow() - last_success
        headers = {"Last-Success": last_success.isoformat()}
        if delay < self._max_delay:
            return web.Response(text="OK", headers=headers)
        else:
            return web.Response(status=418, text="I'm a teapot", headers=headers)


class LivenessAPIV2:
    """
    Kubernetes liveness check handler, which uses a separate process.

    Rationale: when liveness API is implemented in the same process as monitored app, it could fail to respond in
    time whether the underlying app is really busy doing some CPU-intensive work, thus triggering a container
    restart. Running in separate process allows to monitor a busy app much better.

    The monitored client should inherit from LivenessClient and implement `last_success_timestamp` property (or set
    self._last_successful_execution attribute).

    Intended to be used as a context manager:

    .. code-block:: python

        worker = MyApp()
        liveness_api = LivenessAPIV2(worker)
        async with liveness_api.start():
            worker.start()
    """

    _default_delay = pd.Timedelta(hours=1)

    def __init__(
        self,
        client: LivenessClient,
        max_delay: pd.Timedelta = _default_delay,
        liveness_port: int = LIVENESS_PORT,
    ):
        self._last_success_timestamp_val = Value("d", time.time())
        self._client: LivenessClient = client
        self._max_delay: pd.Timedelta = max_delay
        self._liveness_port: int = liveness_port
        self._child_process: Process = Process(
            target=WebServer.run_in_loop,
            args=(self._last_success_timestamp_val, self._max_delay, self._liveness_port),
            daemon=True,
        )
        self._update_last_success_task: Optional[asyncio.Task] = None

    @property
    def last_success(self) -> pd.Timestamp:
        return pd.Timestamp(self._last_success_timestamp_val.value, unit="s", tz="UTC")

    @property
    def liveness_port(self) -> int:
        return self._liveness_port

    async def update_last_success_loop(self):
        while True:
            try:
                self._last_success_timestamp_val.value = self._client.last_success_timestamp.timestamp()
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                return
            except Exception:
                log.error("Unknown error trying to update last success timestamp.", exc_info=True)
                await asyncio.sleep(30)

    @contextlib.asynccontextmanager
    async def start(self):
        self._child_process.start()
        self._update_last_success_task = safe_ensure_future(self.update_last_success_loop())
        try:
            yield self
        finally:
            self._child_process.terminate()
            if self._update_last_success_task is not None:
                self._update_last_success_task.cancel()
