from datetime import datetime

import pytz

from birdfeeder.datetime_helpers import is_tz_aware


def test_timezone_aware():
    aware = datetime(2011, 8, 15, 8, 15, 12, 0, pytz.UTC)
    assert is_tz_aware(aware)


def test_timezone_unaware():
    unaware = datetime(2011, 8, 15, 8, 15, 12, 0)
    assert not is_tz_aware(unaware)
