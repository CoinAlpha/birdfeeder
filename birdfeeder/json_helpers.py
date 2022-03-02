import json
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, NamedTuple, Set, Tuple

import pandas as pd


class JSONTemplateField(NamedTuple):
    value_key: str  # original key for the value form the exchange message
    encode_type: type  # value type presented in the json data
    value_type: type  # actual value type
    value_name: str  # name of the ExchangeDataFields or name that describe the key if it's not a standardized key

    @property
    def default_value(self):
        return self.encode_type(self.value_type())


class JSONTemplate:
    def __init__(self, template_field_tuples: Set[Tuple[str, type, type, str]]):
        self._fields: Set[JSONTemplateField] = {JSONTemplateField(*field) for field in template_field_tuples}
        self._name_key_map: Dict[str, Any] = {f.value_name: f.value_key for f in self._fields}

    @property
    def name_key_map(self):
        return self._name_key_map

    @property
    def default_dict(self) -> Dict[str, Any]:
        return self.get_default_template_dict(self._fields)

    @classmethod
    def get_default_template_dict(cls, template_fields: Set[JSONTemplateField]) -> Dict[str, Any]:
        return {str(f.value_key): f.default_value for f in template_fields}


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


def dump_to_file_as_json(obj: Any, path: str) -> None:
    """
    Dump python object to a file in JSON.

    Objects that are non JSON-serializable are written as a plain string.

    :param obj: python object
    :param path: output file path
    """
    with open(path, "w") as fd:
        json.dump(obj, fd, indent=4, default=json_encode_default)


def load_json_from_file(path: str) -> Any:
    """Load a JSON object from a file."""
    with open(path, "r") as fd:
        return json.load(fd, object_hook=json_decode_hook)
