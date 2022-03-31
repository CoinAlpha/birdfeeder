import time
from unittest.mock import patch

import pandas as pd
import pytest

from birdfeeder.timestamps import (
    format_timestamp,
    get_current_timestamp,
    pd_ts_to_timestamp_ms,
    timestamp_ms_to_str,
    timestamp_s_to_str,
)
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


def test_timestamp_ms_to_str():
    ts = 1579046400000
    human_readable = timestamp_ms_to_str(ts)
    assert human_readable == '2020-01-15 00:00:00'


def test_timestamp_s_to_str():
    ts = 1579046400
    human_readable = timestamp_s_to_str(ts)
    assert human_readable == '2020-01-15 00:00:00'


def test_format_timestamp_input_ms_int():
    ts = get_current_timestamp()

    result = format_timestamp(ts, "ms")
    assert result == ts

    result = format_timestamp(ts, "s")
    assert result == ts / 1000


def test_format_timestamp_input_ns_int():
    ts = time.time_ns()

    result = format_timestamp(ts, "ms")
    expected = int(ts * 10**-6)
    assert result == expected

    result = format_timestamp(ts, "s")
    expected = int(ts * 10**-9)
    assert result == expected


def test_format_timestamp_input_seconds_float():
    ts = time.time()
    result = format_timestamp(ts, "ms")
    assert result == int(ts * 1e3)

    result = format_timestamp(ts, "s")
    assert result == ts


def test_format_timestamp_invalid_input():
    with pytest.raises(ValueError, match="Invalid timestamp format"):
        format_timestamp(1e6, "ms")
    with pytest.raises(ValueError, match="Invalid timestamp format"):
        format_timestamp("foo", "ms")
    with pytest.raises(ValueError, match="Invalid timestamp format"):
        format_timestamp(42, "s")
