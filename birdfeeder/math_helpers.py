import math
import statistics
from decimal import Decimal
from typing import Iterable, Sequence, Union, overload


@overload
def safe_div(numerator: Union[int, float], denominator: Union[int, float]) -> Union[int, float]:
    ...


@overload
def safe_div(numerator: Decimal, denominator: Decimal) -> Decimal:
    ...


def safe_div(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def safe_mean(values: Union[Iterable, Sequence]) -> Union[int, float, Decimal]:
    try:
        return statistics.mean(values)
    except statistics.StatisticsError:
        return 0.0


def round_up(number: float, decimals: int = 0) -> float:
    multiplier = 10**decimals
    return math.ceil(number * multiplier) / multiplier
