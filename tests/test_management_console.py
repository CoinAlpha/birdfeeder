import asyncio
import logging

import pytest

from birdfeeder.async_utils import task_callback
from birdfeeder.management_console import start_management_console

logger = logging.getLogger(__name__)


@pytest.fixture()
async def management_console():
    console_started = asyncio.Event()
    local_vars = {"a": "b"}
    task = asyncio.create_task(start_management_console(local_vars, start_event=console_started))
    task.add_done_callback(task_callback)
    yield local_vars, console_started
    task.cancel()
    await asyncio.sleep(0)


@pytest.mark.asyncio()
async def test_start_management_console(management_console):
    local_vars, console_started = management_console
    await console_started.wait()
    logger.debug(local_vars)
    # Check that we have our custom key
    assert "a" in local_vars
    # Check that we have reference to active_tasks function
    assert local_vars["active_tasks"]
