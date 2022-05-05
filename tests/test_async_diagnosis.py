import asyncio
import logging

import pytest

from birdfeeder.async_diagnosis import get_coro_name, get_wrapped_coroutine
from birdfeeder.async_utils import safe_ensure_future

logger = logging.getLogger(__name__)


async def ok_coroutine():
    await asyncio.sleep(0)


class Example:
    pass


@pytest.mark.asyncio()
async def test_get_coro_name_test_for_qualname():
    """Test __qualname__"""
    name = get_coro_name(ok_coroutine())
    logger.debug(name)


@pytest.mark.asyncio()
async def test_get_coro_name_test_for_name():
    """Test __name__"""
    name = get_coro_name(asyncio)
    logger.debug(name)


def test_get_coro_name_obj_with_no__name__():
    """Test when neither __name__ nor __qualname__ are present."""
    ex = Example()
    name = get_coro_name(ex)
    assert name == "<Example without __name__>()"


def test_get_wrapped_coroutine_old_style():
    """Test that we can get proper name if using old version of safe_ensure_future."""
    task = safe_ensure_future(ok_coroutine(), old_naming_style=True)
    wrapped = get_wrapped_coroutine(task)
    assert "coroutine object ok_coroutine at" in str(wrapped)


def test_get_wrapped_coroutine_new_style():
    """Test that we can get proper name if using new version of safe_ensure_future."""
    task = safe_ensure_future(ok_coroutine())
    wrapped = get_wrapped_coroutine(task)
    assert "coroutine object safe_ok_coroutine at" in str(wrapped)
