"""Utility Methods."""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np

from xplogger.types import LogType


def serialize_log_to_json(log: LogType) -> str:
    """Serialize the log into a JSON string.

    Args:
        log (LogType): Log to be serialized

    Returns:
        str: JSON serialized string
    """
    return json.dumps(log, default=to_json_serializable)


def flatten_dict(
    d: dict[str, Any], parent_key: str = "", sep: str = "#"
) -> dict[str, Any]:
    """Flatten a given dict using the given seperator.

    Taken from https://stackoverflow.com/a/6027615/1353861

    Args:
        d (dict[str, Any]): dictionary to flatten
        parent_key (str, optional): Keep track of the higher level key
            Defaults to "".
        sep (str, optional): string for concatenating the keys. Defaults
            to "#"

    Returns:
        dict[str, Any]: [description]
    """
    items: list[tuple[str, Any]] = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def make_dir(path: Path) -> None:
    """Make dir, if not exists.

    Args:
        path (Path): dir to make
    """
    path.mkdir(parents=True, exist_ok=True)


def compare_keys_in_dict(dict1: dict[Any, Any], dict2: dict[Any, Any]) -> bool:
    """Check that the two dicts have the same set of keys."""
    return set(dict1.keys()) == set(dict2.keys())


def to_json_serializable(val: Any) -> Any:
    """Serialize values as json."""
    if isinstance(val, np.floating):
        return float(val)
    if isinstance(val, np.integer):
        return int(val)
    if isinstance(val, np.ndarray):
        return val.tolist()
    if isinstance(val, Enum):
        return val.value
    return val


def get_elem_from_set(_set: set[Any]) -> Any:
    """Get an element from a set."""
    for _elem in _set:
        break
    return _elem
