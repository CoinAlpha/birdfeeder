import time
from typing import Union

import pandas as pd

from .typing_local import Timestamp_ms


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
