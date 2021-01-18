import time
from unittest.mock import patch

import pandas as pd

from birdfeeder.timestamps import get_current_timestamp, pd_ts_to_timestamp_ms
from birdfeeder.typing_local import Timestamp_ms


def test_get_current_timestamp():
    with patch('time.time', return_value=42):
        ts = get_current_timestamp()
    assert ts == 42 * 1e3
    assert isinstance(ts, Timestamp_ms)


def test_pd_ts_to_timestamp_ms():
    ts = pd_ts_to_timestamp_ms('2020-01-15')
    assert ts == 1579046400000

    with patch('time.time', return_value=42):
        ts = pd_ts_to_timestamp_ms(pd.Timestamp(time.time(), unit='s'))
        assert ts == 42000
