import time
from collections import deque
from typing import Callable, Deque, Iterable, NamedTuple, Union

from .typing_local import Timestamp_ms


class TimedMetricItem(NamedTuple):
    """Holds a metric item."""

    timestamp: Union[int, float, Timestamp_ms]
    value: Union[int, float]

    @classmethod
    def create_with_value(cls, value: int) -> "TimedMetricItem":
        """Create new item using current timestamp."""
        return cls(time.time(), value)


def summation(items: Iterable[TimedMetricItem]) -> Union[int, float]:
    """Compute a sum of values."""
    return sum(i.value for i in items)


def average(items: Iterable[TimedMetricItem]) -> float:
    """Compute a mean across values."""
    items = list(items)
    return float(sum(i.value for i in items) / len(items))


class TimedAggregator:
    """
    Helper class to compute aggregated metrics.

    Keeps a timeseries data for a given time interval and calculates aggregated value.
    """

    def __init__(
        self,
        window_size_seconds: float,
        aggregation_func: Callable[[Iterable[TimedMetricItem]], Union[int, float]] = summation,
        time_func: Callable[[], float] = time.time,
    ):
        """
        :param window_size_seconds: aggregation window size
        :param aggregation_func: a function to compute an aggregated value
        :param time_func: a function to get current time
        """
        self._window: Deque[TimedMetricItem] = deque()
        self._window_size_seconds: float = window_size_seconds
        self._aggregation_func: Callable[[Iterable[TimedMetricItem]], Union[int, float]] = aggregation_func
        self._time_func: Callable[[], float] = time_func

    @property
    def aggregated_value(self) -> Union[int, float]:
        """Return aggregated value using aggregation function."""
        self.remove_obsolete_values()
        return self._aggregation_func(self._window)

    @property
    def average_value(self) -> float:
        """Return average value."""
        self.remove_obsolete_values()
        return average(self._window)

    def remove_obsolete_values(self) -> None:
        """Remove values which are outside of time window."""
        now: float = self._time_func()
        threshold = now - self._window_size_seconds
        while len(self._window) > 0 and self._window[0].timestamp < threshold:
            self._window.popleft()

    def add(self, value: Union[int, float] = 1) -> None:
        """Append an item to a timeseries."""
        now: float = self._time_func()
        self.remove_obsolete_values()
        self._window.append(TimedMetricItem(now, value))
