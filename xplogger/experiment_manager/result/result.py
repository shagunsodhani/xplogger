"""Class to manage a result."""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from xplogger import utils as xplogger_utils
from xplogger.parser.experiment import ExperimentSequence  # type: ignore

# error: Module 'xplogger.parser.experiment' does not explicitly export attribute 'ExperimentSequence'; implicit reexport disabled
from xplogger.utils import to_json_serializable


@dataclass
class Result:
    id: str
    name: str
    label: str
    config_ids: List[str]
    mongo_ids: List[str]
    experiment_sequence: ExperimentSequence
    metrics: Dict[str, pd.DataFrame]
    info: Dict[str, Any]

    def _get_json_dump(self) -> str:
        return json.dumps(
            {
                "id": self.id,
                "name": self.name,
                "label": self.label,
                "config_ids": self.config_ids,
                "mongo_ids": self.mongo_ids,
                "info": self.info,
            },
            indent=4,
            sort_keys=True,
            default=to_json_serializable,
        )

    def serialize(self, dir_path: Path) -> Path:
        """Serialize the result object and save at a given path."""
        dir_path = dir_path.joinpath(self.name)
        xplogger_utils.make_dir(dir_path)
        data = self._get_json_dump()
        data_path = dir_path.joinpath("data.json")
        with open(data_path, "w") as f:
            f.write(data)
        metric_dir = dir_path.joinpath("metric")
        xplogger_utils.make_dir(metric_dir)
        for key in self.metrics:
            path_to_save = metric_dir.joinpath(key)
            if self.metrics[key].empty:
                pass
            else:
                self.metrics[key].to_feather(path=path_to_save)
        return dir_path

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Result):
            return NotImplemented
        return (
            (
                self.id == other.id
                and self.name == other.name
                and self.label == other.label
                and self.config_ids == other.config_ids
                and self.mongo_ids == other.mongo_ids
                and self.info == other.info
            )
            and self.metrics.keys() == other.metrics.keys()
            and all(
                self.metrics[key].equals(other.metrics[key]) for key in self.metrics
            )
        )


def deserialize(dir_path: Path) -> Result:
    """Deserialize the result object, given a path."""
    data_dir = dir_path.joinpath("data.json")
    with open(data_dir, "r") as f:
        json_dump = f.read()
    data = json.loads(json_dump)
    metric_dir = dir_path.joinpath("metric")
    metrics: Dict[str, pd.DataFrame] = {}
    for path_to_load_metric in metric_dir.iterdir():
        if path_to_load_metric.is_file():
            key = path_to_load_metric.parts[-1]
            metrics[key] = pd.read_feather(path_to_load_metric)
    if not metrics:
        metrics["all"] = pd.DataFrame()
    return Result(
        **data,
        experiment_sequence=None,
        metrics=metrics,
    )
