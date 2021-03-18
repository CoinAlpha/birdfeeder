import io
import logging
import logging.config
import os
from enum import Enum
from typing import Any, Dict, List, Type, TypeVar

from pythonjsonlogger.jsonlogger import JsonFormatter
from ruamel.yaml import YAML

T = TypeVar("T", bound="Formatter")


class Formatter(Enum):
    """Define logging formatter in a simple way."""

    VERBOSE = "%(asctime)s - %(name)s(%(funcName)s:%(lineno)d) - %(levelname)s: %(message)s"
    JSON = "%(asctime)s %(name)s %(pathname)s %(funcName)s %(lineno)d %(levelname)s %(message)s"

    @classmethod
    def all(cls: Type[T]) -> List[str]:
        """Returns list with all defined formatter names."""
        # Looks like mypy can't correctly handle that for now
        return list(map(lambda i: i.name, cls))  # type: ignore


def configure_logging_formatter(formatter: Formatter = Formatter.JSON) -> None:
    """
    Configure formatter for all existing loggers.

    Note: it sets StreamHandler only
    """
    if formatter is Formatter.JSON:
        formatter_instance = JsonFormatter(formatter.value)
    else:
        formatter_instance = logging.Formatter(formatter.value)
    handler = logging.StreamHandler()
    handler.setFormatter(formatter_instance)

    # We're setting a proper formatter on all existing loggers including these which created at import time
    for name in logging.getLogger().manager.loggerDict:  # type: ignore
        logger = logging.getLogger(name)
        logger.addHandler(handler)
        # Prevent twice messages from child loggers like "aiohttp.access"
        logger.propagate = False


def read_logging_config(file_path: str, **kwargs: Any) -> Dict[str, Any]:
    """Read yaml-formatted config into dict."""
    yaml_parser: YAML = YAML()
    with open(file_path) as fd:
        yml_source: str = fd.read()

        for key, value in kwargs.items():
            yml_source = yml_source.replace(f"${key.upper()}", value)

        # Assume that configs are located in `project_dir/something/`
        project_dir = os.path.abspath(os.path.join(os.path.dirname(file_path), ".."))
        yml_source = yml_source.replace("$PROJECT_DIR", project_dir)

        io_stream: io.StringIO = io.StringIO(yml_source)
        config: Dict = yaml_parser.load(io_stream)

    return config


def init_logging(
    config_path: str,
    load_common_config: bool = True,
    keep_existing: bool = True,
    stdout_formatter: str = "verbose",
    **kwargs: Any,
) -> None:
    """
    Read logging configuration from file and configure loggers.

    :param config_path: path to the logging config file
    :param load_common_config: if True, load common_logging.yml and merge config from `config_path`.
        common_logging.yml should be located in the same directory as `config_path`
    :param keep_existing: if True, existing loggers are kept, but reconfigured to propagate to a new root logger
    :param stdout_formatter: should be one of the formatters defined inside config
    :param kwargs: any additional params, they are transformed to upper-case and used to replace $VARIABLEs in
        logging config
    :return:
    """

    logging_config = {}
    kwargs["stdout_formatter"] = stdout_formatter

    if load_common_config:
        dirname = os.path.dirname(config_path)
        common_logging_path = os.path.join(dirname, "common_logging.yml")
        logging_config = read_logging_config(common_logging_path, **kwargs)

    overrides_config = read_logging_config(config_path, **kwargs)
    overrides_config.setdefault("loggers", {})

    if keep_existing:
        name: str
        logger: logging.Logger
        for name, logger in logging.getLogger().manager.loggerDict.items():  # type: ignore
            if not isinstance(logger, logging.PlaceHolder):
                # We're finding out loggers which were initialized by `getLogger()` call, and preserving their exact
                # level, which is logging.NOTSET by default
                overrides_config["loggers"].setdefault(name, {"level": logger.level})

    logging_config.update(overrides_config)
    logging.config.dictConfig(logging_config)
