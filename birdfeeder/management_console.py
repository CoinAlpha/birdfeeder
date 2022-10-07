#!/usr/bin/env python

import asyncio
import errno
import json
import logging
import socket
from collections.abc import MutableMapping as MutableMappingABC
from typing import Any, Dict, Iterator, List, MutableMapping, Optional

import aioconsole

from birdfeeder.async_diagnosis import active_tasks

logger = logging.getLogger(__name__)


class MergedNamespace(MutableMappingABC):
    def __init__(self, *mappings):
        self._mappings: List[MutableMapping] = list(mappings)
        self._local_namespace: MutableMapping[Any, Any] = {}

    def __setitem__(self, key: Any, value: Any) -> None:
        self._local_namespace[key] = value

    def __delitem__(self, value: Any) -> None:
        for mapping in [self._local_namespace] + self._mappings:
            if value in mapping:
                del mapping[value]

    def __getitem__(self, key: Any) -> Any:
        for mapping in [self._local_namespace] + self._mappings:
            if key in mapping:
                return mapping[key]
        raise KeyError(key)

    def __len__(self) -> int:
        return sum(len(m) for m in [self._local_namespace] + self._mappings)

    def __iter__(self) -> Iterator[Any]:
        for mapping in [self._local_namespace] + self._mappings:
            for key in mapping:
                yield key

    def __repr__(self) -> str:
        dict_repr: Dict[str, Any] = dict(self.items())
        try:
            return f"{self.__class__.__name__}({json.dumps(dict_repr)})"
        # TypeError: Object of type function is not JSON serializable
        except TypeError:
            return f"{self.__class__.__name__}({dict_repr})"


def add_diagnosis_tools(local_vars: MutableMapping) -> None:
    local_vars["active_tasks"] = active_tasks


def detect_available_port(starting_port: int) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        current_port: int = starting_port
        while current_port < 65535:
            try:
                sock.bind(("127.0.0.1", current_port))
                break
            except OSError as e:
                if e.errno == errno.EADDRINUSE:
                    current_port += 1
                    continue
        return current_port


async def start_management_console(
    local_vars: MutableMapping,
    host: str = "localhost",
    port: int = 16119,
    banner: str = "Welcome to the machine",
    start_event: Optional[asyncio.Event] = None,
) -> asyncio.base_events.Server:
    add_diagnosis_tools(local_vars)
    port = detect_available_port(port)

    def factory_method(*args, **kwargs):
        from aioconsole.console import AsynchronousConsole

        return AsynchronousConsole(*args, locals=local_vars, **kwargs)

    retval = await aioconsole.start_interactive_server(host=host, port=port, banner=banner, factory=factory_method)
    logger.info(f"Started debug console at {host}:{port}.")
    if start_event is not None:
        start_event.set()
    return retval
