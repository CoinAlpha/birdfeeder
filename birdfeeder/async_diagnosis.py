"""Debug console diagnosis tools."""

import asyncio
from typing import Any, Awaitable, Generator, List, Union

import pandas as pd


def get_coro_name(coro: Any) -> str:
    if hasattr(coro, '__qualname__') and coro.__qualname__:
        coro_name = coro.__qualname__
    elif hasattr(coro, '__name__') and coro.__name__:
        coro_name = coro.__name__
    else:
        coro_name = f'<{type(coro).__name__} without __name__>'
    return f'{coro_name}()'


def get_wrapped_coroutine(task: asyncio.Task) -> Union[Awaitable, Generator]:
    if "safe_wrapper" in str(task):
        # This is a backward compatibility logic when safe_ensure_future didn't adjust __qualname__
        # TODO (vladimir): looks like some get_coro() return types may not have cr_frame attribute
        return task.get_coro().cr_frame.f_locals["c"]  # type: ignore[union-attr]
    else:
        return task.get_coro()


def active_tasks() -> pd.DataFrame:
    tasks: List[asyncio.Task] = [t for t in asyncio.all_tasks() if not t.done()]
    coroutines = [get_wrapped_coroutine(t) for t in tasks]
    func_names: List[str] = [get_coro_name(c) for c in coroutines]
    retval: pd.DataFrame = pd.DataFrame(
        [{"func_name": f, "coroutine": c, "task": t} for f, c, t in zip(func_names, coroutines, tasks)],
        columns=["func_name", "coroutine", "task"],
    ).set_index("func_name")
    retval.sort_index(inplace=True)
    return retval
