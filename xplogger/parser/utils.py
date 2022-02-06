"""Utility functions for the parser module."""

from __future__ import annotations

import json
from typing import Any, Iterable, Optional

from xplogger import utils
from xplogger.types import ConfigType, LogType


def flatten_log(d: LogType, parent_key: str = "", sep: str = "#") -> LogType:
    """Flatten a log using a separator.

    Taken from https://stackoverflow.com/a/6027615/1353861

    Args:
        d (LogType): [description]
        parent_key (str, optional): [description]. Defaults to "".
        sep (str, optional): [description]. Defaults to "#".

    Returns:
        LogType: [description]
    """
    items: list[tuple[str, Any]] = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_log(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def compare_logs(
    first_log: LogType, second_log: LogType, verbose: bool = False
) -> tuple[list[str], list[str], list[str]]:
    """Compare two logs.

    Return list of keys that are either missing or have different valus
    in the two logs.

    Args:
        first_log (LogType): First Log
        second_log (LogType): Second Log
        verbose (bool): Defaults to False

    Returns:
        tuple[list[str], list[str], list[str]]: tuple of [
            list of keys with different values,
            list of keys with values missing in first log,
            list of keys with values missing in the second log,]
    """
    first_log = flatten_log(first_log)
    second_log = flatten_log(second_log)
    first_keys = set(first_log.keys())
    second_keys = set(second_log.keys())
    keys = first_keys.union(second_keys)
    keys_with_diff_values = []
    keys_with_missing_value_in_first_log = []
    keys_with_missing_value_in_second_log = []
    for key in keys:
        if key not in first_log:
            keys_with_missing_value_in_first_log.append(key)
            if verbose:
                print(f"first_log[{key}]: ???, second_log[{key}]: {second_log[key]}")
        elif key not in second_log:
            keys_with_missing_value_in_second_log.append(key)
            print(f"first_log[{key}]: {first_log[key]},  second_log[{key}]: ???")
        else:
            if first_log[key] != second_log[key]:
                keys_with_diff_values.append(key)
                print(
                    f"first_log[{key}]: {first_log[key]},  second_log[{key}]: {second_log[key]}"
                )
    return (
        keys_with_diff_values,
        keys_with_missing_value_in_first_log,
        keys_with_missing_value_in_second_log,
    )


def parse_json(line: str) -> Optional[LogType]:
    """Parse a line as JSON string."""
    line = line.strip()
    if not (line.startswith("{") and line.endswith("}")):
        return None
    log: Optional[LogType]
    try:
        log = json.loads(line)
    except json.JSONDecodeError:
        log = None
    return log


def get_param_groups(
    configs: Iterable[ConfigType], params_to_exclude: Iterable[str]
) -> tuple[ConfigType, dict[str, set[Any]]]:
    """Return two groups of params, one which is fixed across the experiments and one which varies.

    This function is useful when understanding the effect of different parameters on the model's
    performance. One could plot the performance of the different experiments, as a function of the
    parameters that vary.

    Args:
        configs (Iterable[ConfigType]): Collection of configs, to extract params from.
        params_to_exclude (Iterable[str]): These parameters are not returned in either group.
            This is useful for ignoring parameters like `time when the experiment was started`
            since these parameters should not affect the performance. In absence of this argument,
            all such parameters will likely be returned with the group of varying parameters.

    Returns:
        tuple[ConfigType, dict[str, set[Any]]]: The first group/config contains the params which are fixed across the experiments.
            It maps these params to their `default` values, hence it should be a subset of any config.
            The second group/config contains the params which vary across the experiments.
            It maps these params to the set of values they take.

    """
    param_value_dict: dict[str, set[Any]] = {}
    for config in configs:
        for param, value in config.items():
            if param not in param_value_dict:
                param_value_dict[param] = set()
            value_to_add = value
            if isinstance(value, (list, tuple)):
                value_to_add = "_".join(map(str, value))
            param_value_dict[param].add(value_to_add)

    param_value_counter: dict[str, int] = {}
    for param, values in param_value_dict.items():
        param_value_counter[param] = len(values)

    fixed_params: ConfigType = {}
    variable_params: dict[str, set[Any]] = {}
    for param, counter in param_value_counter.items():
        if param not in params_to_exclude:
            if counter == 1:
                fixed_params[param] = utils.get_elem_from_set(param_value_dict[param])
                # Note that this is a singleton set.
            else:
                variable_params[param] = param_value_dict[param]

    return fixed_params, variable_params
