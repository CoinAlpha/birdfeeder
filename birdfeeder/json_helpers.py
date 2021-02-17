from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict

import pandas as pd


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


def json_encode_default(obj: Any) -> Dict[str, Any]:
    """
    JSON encoder to provide serialization for additional types.

    Example usage:

    .. code-block:: python

        json.dump(obj, fd, indent=4, default=json_encode_default)

    :param obj: object to serialize
    """
    if isinstance(obj, Decimal):
        return {'type(Decimal)': str(obj)}
    elif isinstance(obj, pd.Timestamp):
        return {'type(pd.Timestamp)': str(obj)}
    elif isinstance(obj, datetime):
        return {'type(datetime)': obj.isoformat()}
    else:
        raise TypeError(f"{repr(obj)} is not JSON serializable")


def json_decode_hook(obj: Any) -> Any:
    """
    JSON decode hook to deserialize additional types.

    .. code-block:: python

        json.load(fd, object_hook=json_decode_hook)
    """
    if 'type(Decimal)' in obj:
        return Decimal(obj['type(Decimal)'])
    elif 'type(pd.Timestamp)' in obj:
        return pd.Timestamp(obj['type(pd.Timestamp)'])
    elif 'type(datetime)' in obj:
        return datetime.fromisoformat(obj['type(datetime)'])
    return obj
