import asyncio
import random
import sys
from unittest.mock import patch

import pytest

from birdfeeder import async_utils


async def ok_coroutine():
    await asyncio.sleep(0)


async def bad_coroutine():
    raise RuntimeError("boom")


def test_should_inspect():
    assert async_utils.SHOULD_INSPECT is False


@pytest.mark.asyncio
async def test_async_ttl_cache():
    @async_utils.async_ttl_cache(30, 10)
    async def func():
        return random.randint(0, 999999)  # noqa: DUO102

    # Non-cached
    result = await func()
    assert result > 0

    # Cached
    result2 = await func()
    assert result2 == result


def test_get_callers():
    callers = async_utils.get_callers()
    assert isinstance(callers, list)
    assert callers[0][1] == 'test_async_utils'
    assert callers[0][2] == 'test_get_callers'


@pytest.mark.asyncio
async def test_safe_ensure_future_1():
    await async_utils.safe_ensure_future(ok_coroutine())


@pytest.mark.asyncio
async def test_safe_ensure_future_2():
    async_utils.SHOULD_INSPECT = True
    # Should log unhandled exception with callers
    await async_utils.safe_ensure_future(bad_coroutine())


@pytest.mark.asyncio
async def test_safe_gather_1():
    await async_utils.safe_gather(ok_coroutine())


@pytest.mark.asyncio
async def test_safe_gather_2():
    with pytest.raises(RuntimeError, match="boom"):
        await async_utils.safe_gather(bad_coroutine())


def test_calc_delay_til_next_tick():
    import time

    with patch.object(time, "time", return_value=0.1):
        delay = async_utils.calc_delay_til_next_tick(5)
        assert delay == 5 - 0.1


@pytest.mark.skipif(sys.version_info < (3, 8), reason="requires python3.8 or higher")
@pytest.mark.asyncio
async def test_wait_til_next_tick():
    with patch.object(asyncio, "sleep") as sleep:
        await async_utils.wait_til_next_tick(seconds=0.001)
        sleep.assert_called_once()
