import asyncio
import logging
import time
from multiprocessing import Value

import aiohttp
import pandas as pd
import pytest

from birdfeeder.liveness_api import LivenessAPIV2, LivenessClient, WebServer
from birdfeeder.timestamps import get_current_timestamp

log = logging.getLogger(__name__)


class Worker(LivenessClient):
    """Example app to be monitored."""

    def __init__(self):
        super().__init__()
        self._task = None
        self._last_successful_execution = get_current_timestamp()

    @staticmethod
    async def do_work():
        try:
            log.debug("Doing work")
            await asyncio.sleep(300)
        except asyncio.CancelledError:
            log.debug("Work is done")
            return

    def start(self):
        self._task = asyncio.create_task(self.do_work())

    def stop(self):
        if self._task is not None:
            self._task.cancel()
            loop = asyncio.get_event_loop()
            loop.run_until_complete(asyncio.gather(self._task, return_exceptions=True))


@pytest.fixture()
def endpoint(unused_tcp_port):
    return f"http://localhost:{unused_tcp_port}/", unused_tcp_port


@pytest.fixture()
def worker():
    worker = Worker()
    yield worker
    worker.stop()


@pytest.fixture()
async def server(event_loop, endpoint):
    url, port = endpoint
    last_success = Value("d", time.time())
    server_task = event_loop.create_task(WebServer.run_server(last_success, pd.Timedelta(seconds=60), port))
    yield server_task, last_success, url
    server_task.cancel()


@pytest.mark.asyncio()
async def test_standalone_webserver(server):
    """
    Test liveness API webserver running in a current process.

    Just for debugging.
    """
    _, last_success, url = server

    async with aiohttp.ClientSession() as session:
        response: aiohttp.ClientResponse = await session.get(url)

        # Check success result
        assert response.status == 200
        assert "Last-Success" in response.headers

        # Test for failed check
        last_success.value -= 61
        response = await session.get(url)
        assert response.status == 418


@pytest.mark.asyncio()
async def test_livenessv2(worker, endpoint):
    """Test liveness API webserver running in a separate process."""
    url, port = endpoint
    liveness_api = LivenessAPIV2(worker, max_delay=pd.Timedelta(seconds=60), liveness_port=port)
    async with liveness_api.start():
        worker.start()
        await asyncio.sleep(1)  # waits for process startup

        async with aiohttp.ClientSession() as session:
            response: aiohttp.ClientResponse = await session.get(url)

            # Check success result
            assert response.status == 200
            expected = pd.Timestamp(worker.last_success_timestamp.timestamp(), unit="s", tz="utc").isoformat()
            assert response.headers["Last-Success"] == expected
