import asyncio
import functools
import inspect
import logging
import time
from typing import Any, List, Tuple, Union

import cachetools
from async_timeout import timeout
from environs import Env

log = logging.getLogger(__name__)
env = Env()
env.read_env()  # read .env file, if it exists
SHOULD_INSPECT = env.bool("INSPECT_CALLERS", False)


def async_ttl_cache(ttl: int = 3600, maxsize: int = 1) -> Any:
    """Decorator to cache a coroutine result using :py:class:`cachetools.TTLCache`."""
    cache: cachetools.TTLCache = cachetools.TTLCache(ttl=ttl, maxsize=maxsize)

    def decorator(fn):
        @functools.wraps(fn)
        async def memoize(*args, **kwargs):
            key = str((args, kwargs))
            try:
                return cache[key]
            except KeyError:
                result = await fn(*args, **kwargs)
                cache[key] = result
                return result

        return memoize

    return decorator


def get_callers(stack_size: int = 5) -> List[Tuple[int, str, Any]]:
    stack = inspect.stack()
    modules = [(index, inspect.getmodule(stack[index][0])) for index in reversed(range(1, min(stack_size, len(stack))))]
    callers = []
    for index, module in modules:
        try:
            callers.append((index, module.__name__, stack[index][3]))  # type: ignore
        except AttributeError:
            # AttributeError: 'NoneType' object has no attribute '__name__'
            callers.append((index, "unknown", stack[index][3]))
    return sorted(callers)


def safe_ensure_future(coro, *args, **kwargs):
    """
    Run a coroutine in a wrapper, catching and logging unexpected exception.

    :envvar: INSPECT_CALLERS: if true, show callers on failure
    """
    caller_names = ""
    if SHOULD_INSPECT:
        caller_names = "\n" + "\n".join([str(t) for t in get_callers()])

    async def safe_wrapper(c):
        try:
            return await c
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logging.getLogger().error(
                f"Unhandled error in background task: {str(e)} {caller_names}",
                exc_info=True,
            )

    wrapped_coro = safe_wrapper(coro)

    if coro.__name__ and isinstance(coro.__name__, str) and coro.__name__.isidentifier():
        wrapped_coro.__qualname__ = f"safe_{coro.__qualname__}"

    return asyncio.ensure_future(wrapped_coro, *args, **kwargs)


async def safe_gather(*args, **kwargs):
    """
    Gather an awaitables logging unexpected exceptions.

    .. note::

        Exception is logged and re-raised!

    :envvar: INSPECT_CALLERS: if true, show callers on failure
    """
    caller_names = ""
    if SHOULD_INSPECT:
        caller_names = "\n" + "\n".join([str(t) for t in get_callers()])
    try:
        return await asyncio.gather(*args, **kwargs)
    except Exception as e:
        logging.getLogger().debug(
            f"Unhandled error in background task: {str(e)} {caller_names}",
            exc_info=True,
        )
        raise


async def safe_cancel(task: asyncio.Task, info: str, cancel_wait_timeout: Union[int, float] = 10) -> int:
    """
    Cancel asyncio task and retry cancel if task didn't finished.

    :param task: Task to cancel
    :param info: some additional info to log when cancelling a task
    :param cancel_wait_timeout: how many seconds wait for task to cancel before retrying
    :return: how many attempts has been made to cancel a task
    """
    retries = 0

    while True:
        task.cancel()
        log.debug(f"Task cancel request sent to task: {task}, additional info: {info}")

        try:
            async with timeout(cancel_wait_timeout):
                while not task.done():
                    await asyncio.sleep(cancel_wait_timeout / 10)
        except asyncio.TimeoutError:
            log.warning(f"Task failed to stop: {task}, additional task info: {info}, retries: {retries}")
        else:
            log.info(f"Task cancelled: {task}, additional info: {info}")
            return retries

        retries += 1


def calc_delay_til_next_tick(seconds: float) -> float:
    """Calculate the delay to next tick."""
    now: float = time.time()
    current_tick: int = int(now // seconds)
    delay_til_next_tick: float = (current_tick + 1) * seconds - now
    return delay_til_next_tick


async def wait_til_next_tick(seconds: float = 1.0) -> None:
    """Wait until the end of quantized time interval."""
    delay = calc_delay_til_next_tick(seconds)
    await asyncio.sleep(delay)
