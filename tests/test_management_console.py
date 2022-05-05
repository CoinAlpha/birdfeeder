import asyncio
import logging

import pytest

from birdfeeder.async_utils import task_callback
from birdfeeder.management_console import MergedNamespace, start_management_console

logger = logging.getLogger(__name__)


@pytest.fixture()
async def management_console():
    console_started = asyncio.Event()
    namespace = MergedNamespace(locals(), {"a": "b"})
    task = asyncio.create_task(start_management_console(namespace, start_event=console_started))
    task.add_done_callback(task_callback)
    yield namespace, console_started
    task.cancel()
    await asyncio.sleep(0)


@pytest.mark.asyncio()
async def test_start_management_console(management_console):
    namespace, console_started = management_console
    await console_started.wait()
    logger.debug(namespace)
    # Check that we have our custom key
    assert "a" in namespace
    # Check that we have reference to active_tasks function
    assert namespace["active_tasks"]
