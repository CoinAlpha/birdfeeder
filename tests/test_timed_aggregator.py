from unittest.mock import MagicMock, patch

from birdfeeder.timed_aggregator import TimedAggregator, TimedMetricItem, average, summation


def test_create_with_value():
    with patch('time.time', return_value=42):
        item = TimedMetricItem.create_with_value(100)
        assert item.timestamp == 42
        assert item.value == 100


def test_summation():
    values = [2, 4, 5]
    sum_ = summation(map(lambda i: TimedMetricItem.create_with_value(i), values))
    assert sum_ == sum(values)


def test_average():
    values = [3, 4, 5]
    avg = average(map(lambda i: TimedMetricItem.create_with_value(i), values))
    assert avg == 4


def test_timed_aggregator():
    window = 10
    start = 0
    time = MagicMock(return_value=start)
    aggregator = TimedAggregator(window, aggregation_func=summation, time_func=time)

    aggregator.add(value=42)
    time.return_value = start + window + 1
    assert aggregator.aggregated_value == 0


def test_timed_aggregator_average():
    window = 10
    start = 0
    time = MagicMock(return_value=start)
    aggregator = TimedAggregator(window, aggregation_func=summation, time_func=time)

    aggregator.add(value=5)
    time.return_value = start + 1
    aggregator.add(value=7)
    time.return_value = start + 2
    aggregator.add(value=6)
    time.return_value = start + 3
    aggregator.add(value=2)

    assert aggregator.average_value == 5
