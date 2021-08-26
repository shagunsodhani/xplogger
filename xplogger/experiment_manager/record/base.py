"""Record class."""
from __future__ import annotations

from collections import UserDict
from functools import reduce
from pathlib import Path
from typing import Any, Callable

import ray

from xplogger.parser.experiment.experiment import Experiment, ExperimentSequence


def get_nested_item(data: dict[Any, Any], keys: list[Any]) -> Any:
    return reduce(lambda seq, key: seq[key], keys, data)


class Record(UserDict[str, Any]):
    def __init__(self, record: dict[str, Any]):
        super().__init__(record)


def load_experiment(
    record: Record,
    load_experiment_from_dir: Callable[[str], Experiment],
) -> Experiment:
    """Load experiment given a record."""
    return load_experiment_from_dir(
        log_dir=record["logbook"]["logger_dir"],
    )


@ray.remote
def ray_load_experiment(
    record: Record,
    load_experiment_from_dir: Any,
) -> Experiment:
    """Load experiment given a record."""
    return load_experiment_from_dir(
        log_dir=record["logbook"]["logger_dir"],
    )


def load_all_experiments_from_dir(
    load_experiment_from_dir: Any,
    base_dir: str,
) -> ExperimentSequence:
    """Load all experiments in a directory."""
    experiments = []
    for log_dir in list(Path(base_dir).iterdir()):
        if log_dir.is_dir():
            print(log_dir)
            experiments.append(load_experiment_from_dir(log_dir=log_dir))
    return ExperimentSequence(experiments)


def get_experiment_params(record: Record, viz_params: list[str]) -> dict[str, Any]:
    """Get experiment params."""
    if viz_params is None:
        viz_params = record["setup"]["viz"]["params"]
    params = {key: get_nested_item(record, key.split(".")) for key in viz_params}
    return params
