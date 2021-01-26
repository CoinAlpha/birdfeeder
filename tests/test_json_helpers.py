import json
from decimal import Decimal
from enum import Enum

import pytest

from birdfeeder.json_helpers import to_valid_json_dict


class Car(Enum):
    sedan = 1
    hatchback = 2
    cabriolet = 3
    suv = 4


dict_with_decimal = {"a": Decimal("10.22")}
dict_with_car = {"a": Car.suv}


def test_decimal():
    out = to_valid_json_dict(dict_with_decimal, decimal_to_str=True)
    assert out["a"] == "10.22"

    out = to_valid_json_dict(dict_with_decimal, decimal_to_str=False)
    assert out["a"] == 10.22


def test_enum():
    out = to_valid_json_dict(dict_with_car, enum_to_name=True)
    assert out["a"] == "suv"

    out = to_valid_json_dict(dict_with_car, enum_to_name=False)
    assert out["a"] == 4


def test_nesting_list():
    case = {"top": [dict_with_decimal, dict_with_car]}
    out = to_valid_json_dict(case, decimal_to_str=True, enum_to_name=True)
    assert out["top"][0]["a"] == "10.22"
    assert out["top"][1]["a"] == "suv"


def test_nesting_dict():
    case = {"top": {"x": dict_with_decimal, "y": dict_with_car}}
    out = to_valid_json_dict(case, decimal_to_str=True, enum_to_name=True)
    assert out["top"]["x"]["a"] == "10.22"
    assert out["top"]["y"]["a"] == "suv"


def test_json_decimal():
    case = {"top": {"x": dict_with_decimal}}
    out = to_valid_json_dict(case, decimal_to_str=True, enum_to_name=True)

    with pytest.raises(TypeError, match="Object of type Decimal is not JSON serializable"):
        json.dumps(case)

    json.dumps(out)


def test_json_enum():
    case = {"top": {"y": dict_with_car}}
    out = to_valid_json_dict(case, decimal_to_str=True, enum_to_name=True)

    with pytest.raises(TypeError, match="Object of type Car is not JSON serializable"):
        json.dumps(case)

    json.dumps(out)
