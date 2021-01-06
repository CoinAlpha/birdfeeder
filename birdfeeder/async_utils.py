import asyncio
import inspect
import logging
import time
from typing import Any, List, Tuple

from environs import Env

env = Env()
env.read_env()  # read .env file, if it exists
SHOULD_INSPECT = env.bool("ASYNCIO_INSPECT_CALLERS", False)


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

    :envvar: ASYNCIO_INSPECT_CALLERS: if true, show callers on failure
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

    return asyncio.ensure_future(safe_wrapper(coro), *args, **kwargs)


async def safe_gather(*args, **kwargs):
    """
    Gather an awaitables logging unexpected exceptions.

    .. note::

        Exception is logged and re-raised!

    :envvar: ASYNCIO_INSPECT_CALLERS: if true, show callers on failure
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
