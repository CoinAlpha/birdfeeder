from decimal import Decimal
from enum import Enum
from typing import Any


def to_valid_json_dict(dictionary: Any, decimal_to_str: bool = False, enum_to_name: bool = True) -> Any:
    """
    Serialize a structure into JSON-ready form.

    Currently supports of transforming of Decimals and Enums into string form.

    :param dictionary: a structure to serialize, could be a dict, list, set
    :param decimal_to_str: convert Decimal to string if True, and to float if False
    :param enum_to_name: convert Enum attribute to it's name if True, and to value if False
    """
    forward_kwargs = {"decimal_to_str": decimal_to_str, "enum_to_name": enum_to_name}

    if isinstance(dictionary, dict):
        return {key: to_valid_json_dict(value, **forward_kwargs) for key, value in dictionary.items()}
    if isinstance(dictionary, (set, list)):
        return [to_valid_json_dict(value, **forward_kwargs) for value in dictionary]
    if isinstance(dictionary, Decimal):
        return str(dictionary) if decimal_to_str else float(dictionary)
    if isinstance(dictionary, Enum):
        return dictionary.name if enum_to_name else dictionary.value

    return dictionary
