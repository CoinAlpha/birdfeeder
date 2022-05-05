#!/usr/bin/env python

import asyncio
import errno
import json
import logging
import socket
from collections.abc import MutableMapping as MutableMappingABC
from typing import Dict, Iterator, List, MutableMapping

import aioconsole

from birdfeeder.async_diagnosis import active_tasks


class MergedNamespace(MutableMappingABC):
    def __init__(self, *mappings):
        self._mappings: List[MutableMapping] = list(mappings)
        self._local_namespace = {}

    def __setitem__(self, k, v) -> None:
        self._local_namespace[k] = v

    def __delitem__(self, v) -> None:
        for m in [self._local_namespace] + self._mappings:
            if v in m:
                del m[v]

    def __getitem__(self, k):
        for m in [self._local_namespace] + self._mappings:
            if k in m:
                return m[k]
        raise KeyError(k)

    def __len__(self) -> int:
        return sum(len(m) for m in [self._local_namespace] + self._mappings)

    def __iter__(self) -> Iterator[any]:  # type: ignore
        for mapping in [self._local_namespace] + self._mappings:
            for k in mapping:
                yield k

    def __repr__(self) -> str:
        dict_repr: Dict[str, any] = dict(self.items())  # type: ignore
        return f"{self.__class__.__name__}({json.dumps(dict_repr)})"


def add_diagnosis_tools(local_vars: MutableMapping):
    local_vars["active_tasks"] = active_tasks


def detect_available_port(starting_port: int) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        current_port: int = starting_port
        while current_port < 65535:
            try:
                s.bind(("127.0.0.1", current_port))
                break
            except OSError as e:
                if e.errno == errno.EADDRINUSE:
                    current_port += 1
                    continue
        return current_port


async def start_management_console(
    local_vars: MutableMapping, host: str = "localhost", port: int = 16119, banner: str = "Parrot"
) -> asyncio.base_events.Server:
    add_diagnosis_tools(local_vars)
    port = detect_available_port(port)

    def factory_method(*args, **kwargs):
        from aioconsole.console import AsynchronousConsole

        return AsynchronousConsole(locals=local_vars, *args, **kwargs)

    retval = await aioconsole.start_interactive_server(host=host, port=port, banner=banner, factory=factory_method)
    logging.getLogger(__name__).info(f"Started debug console at {host}:{port}.")
    return retval
