from decimal import Decimal

from birdfeeder.math_helpers import safe_div, safe_mean, round_up


def test_safe_div_basic():
    assert safe_div(10, 2) == 5.0


def test_safe_div_basic_decimal():
    assert safe_div(Decimal(10), Decimal(2)) == Decimal(5)


def test_safe_div_zero_div():
    assert safe_div(10, 0) == 0.0


def test_safe_mean_basic():
    assert safe_mean([2, 4]) == 3.0


def test_safe_mean_empty():
    assert safe_mean([]) == 0.0


def test_safe_mean_zero_values():
    assert safe_mean([0, 0]) == 0.0


def test_round_up_basic():
    assert round_up(1.234, 2) == 1.24


def test_round_up_zero():
    assert round_up(0, 2) == 0.0
