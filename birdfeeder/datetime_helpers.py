from datetime import datetime


def is_tz_aware(dt: datetime) -> bool:
    """
    Returns whether the datetime is timezone-aware.

    Source: https://stackoverflow.com/a/27596917/148585
    """
    return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None
