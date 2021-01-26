import time
from typing import Union

import pandas as pd

from .typing_local import Timestamp_ms, Timestamp_s


def get_current_timestamp() -> Timestamp_ms:
    """Return current timestamp in ms."""
    return int(time.time() * 1000)


def pd_ts_to_timestamp_ms(ts_input: Union[str, int, float, pd.Timestamp]) -> Timestamp_ms:
    """
    Convert pandas.Timestamp or acceptable `ts_input` into Timestamp_ms.

    See https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.Timestamp.html for reference
    """
    if not isinstance(ts_input, pd.Timestamp):
        timestamp = pd.Timestamp(ts_input)
    else:
        timestamp = ts_input

    ts: Timestamp_ms = int(timestamp.timestamp() * 1e3)
    return ts


def timestamp_ms_to_str(ts: Timestamp_ms) -> str:
    """Convert millisecond timestamp into human-readable form."""
    return f"{pd.Timestamp(ts, unit='ms')}"


def timestamp_s_to_str(ts: Timestamp_s) -> str:
    """Convert unixtime timestamp into human-readable form."""
    return f"{pd.Timestamp(ts, unit='s')}"


def format_timestamp(timestamp: Union[int, float, str], to_format: str) -> Union[int, float]:
    """
    Convert timestamp from ms/ns/seconds to ms int / seconds int / seconds float form.

    Caveats:
    1. Input ms/ns timestamps are assumed to be fixed-length, which constraints operating range to 2001 - 2262
       (64-bit C long).
    2. Input timestamp cannot be in scientific notation!

    :param timestamp: timestamp in float or int or str
    :param to_format: "s" for second, "ms" for millisecond
    :return: timestamp seconds or milliseconds
    """
    timestamp_as_str: str = str(timestamp)
    milliseconds: int
    seconds: float

    if timestamp_as_str.isnumeric() and len(timestamp_as_str) == 13:  # ms in int
        milliseconds = int(timestamp_as_str)
        seconds = int(timestamp_as_str) / 1000
    elif timestamp_as_str.isnumeric() and len(timestamp_as_str) == 19:  # ns in int
        milliseconds = int(int(timestamp_as_str) / 1e6)
        seconds = int(int(timestamp_as_str) / 1e9)
    elif (
        timestamp_as_str.replace(".", "", 1).isdigit() and len(timestamp_as_str.split(".")[0]) == 10
    ):  # second in float
        milliseconds = int(float(timestamp_as_str) * 1000)
        seconds = float(timestamp_as_str)
    else:
        raise ValueError(f"Invalid timestamp format: {timestamp} (len {len(timestamp_as_str)})")

    if to_format == "ms":
        return milliseconds
    elif to_format == "s":
        return seconds
    else:
        raise ValueError("Invalid param to_format expecting [s, ms]")
