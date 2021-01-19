#!/usr/bin/env python
from aiohttp import web
import asyncio
import contextlib
import pandas as pd
import logging
from multiprocessing import Value, Process
import time
from typing import (
    Optional
)

import conf
from .async_utils import safe_ensure_future
from parrot.user_data_collector.base import CollectorBase


class LivenessAPIV2:
    """
    Starts the web server in a separate process to avoid request timeout problems in busy processes.
    """
    _lapiv2_logger: Optional[logging.Logger] = None

    @classmethod
    def logger(cls) -> logging.Logger:
        if cls._lapiv2_logger is None:
            cls._lapiv2_logger = logging.getLogger(__name__)
        return cls._lapiv2_logger

    def __init__(self,
                 collector: CollectorBase,
                 max_delay: pd.Timedelta = pd.Timedelta(hours=1),
                 liveness_port: Optional[int] = None):
        self._last_success_timestamp_val: Value = Value("d", time.time())
        self._collector: CollectorBase = collector
        self._max_delay: pd.Timedelta = max_delay
        self._liveness_port: int = liveness_port if liveness_port is not None else conf.health_check_api_port
        self._child_process: Process = Process(target=self.WebServer.run_server,
                                               args=(self._last_success_timestamp_val,
                                                     self._max_delay,
                                                     self._liveness_port),
                                               daemon=True)
        self._update_last_success_task: Optional[asyncio.Task] = None

    class WebServer:
        def __init__(self, last_success_value: Value, max_delay: pd.Timedelta):
            self._last_success_value: Value = last_success_value
            self._max_delay = max_delay
            self._app: web.Application = web.Application()
            self._app.router.add_get("/", self.health_check)

        @classmethod
        def run_server(cls, last_success_value: Value, max_delay: pd.Timedelta, port: int):
            ev_loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
            asyncio.set_event_loop(ev_loop)

            async def run():
                server: cls = cls(last_success_value, max_delay)
                runner: web.AppRunner = web.AppRunner(server.web_app)
                await runner.setup()
                site = web.TCPSite(runner, "0.0.0.0", port)
                await site.start()
                while True:
                    await asyncio.sleep(86400)

            ev_loop.run_until_complete(run())

        @property
        def web_app(self) -> web.Application:
            return self._app

        async def health_check(self, _: web.Request) -> web.Response:
            last_success: pd.Timestamp = pd.Timestamp(self._last_success_value.value, unit="s", tz="utc")
            delay: pd.Timedelta = pd.Timestamp.utcnow() - last_success
            if delay < self._max_delay:
                return web.Response(text="OK", headers={
                    "Fetcher-Last-Fetch": last_success.isoformat()
                })
            else:
                return web.Response(status=418, text="I'm a teapot", headers={
                    "Fetcher-Last-Fetch": last_success.isoformat()
                })

    @property
    def last_success(self) -> pd.Timestamp:
        return pd.Timestamp(self._last_success_timestamp_val.value,
                            unit="s", tz="UTC")

    @property
    def liveness_port(self) -> int:
        return self._liveness_port

    async def update_last_success_loop(self):
        while True:
            try:
                self._last_success_timestamp_val.value = self._collector.last_successful_execution.timestamp()
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                raise
            except Exception:
                self.logger().error("Unknown error trying to update last success timestamp.", exc_info=True)
                await asyncio.sleep(1)

    @contextlib.asynccontextmanager
    async def start(self):
        self._child_process.start()
        self._update_last_success_task = safe_ensure_future(self.update_last_success_loop())
        try:
            yield self
        finally:
            self._child_process.terminate()
            self._update_last_success_task.cancel()
            self._update_last_success_task = None
