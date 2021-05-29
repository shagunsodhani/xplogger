"""Container for the experiment data."""

import gzip
import json
from collections import UserList
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple

import pandas as pd

from xplogger import utils as xplogger_utils
from xplogger.parser import utils as parser_utils
from xplogger.parser.experiment import utils as experiment_utils
from xplogger.types import ConfigType


class Experiment:
    def __init__(
        self,
        configs: List[ConfigType],
        metrics: experiment_utils.ExperimentMetricType,
        info: Optional[experiment_utils.ExperimentInfoType] = None,
    ):
        """Class to hold the experiment data.

        Args:
            configs (List[ConfigType]): Configs used for the experiment
            metrics (experiment_utils.ExperimentMetricType): Dictionary mapping strings
                to dataframes. Keys could be "train", "validation", "test"
                and corresponding dataframes would have the data for these
                modes.
            info (Optional[Dict[Any, Any]], optional): A dictionary where the user can store
                any information about the experiment (that does not fit
                within config and metrics). Defaults to None.
        """
        self.configs = configs
        self.metrics = metrics
        self.info: Dict[Any, Any] = {}
        if info is not None:
            self.info = info

    @property
    def config(self) -> Optional[ConfigType]:
        """Access the config property."""
        if len(self.configs) > 0:
            return self.configs[-1]
        return None

    def serialize(self, dir_path: str) -> None:
        """Serialize the experiment data and store at `dir_path`.

        * configs are stored as jsonl (since there are only a few configs per experiment) in a file called `config.jsonl`.
        * metrics are stored in [`feather` format](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.to_feather.html).
        * info is stored in the gzip format.
        """
        xplogger_utils.make_dir(dir_path)
        path_to_save = f"{dir_path}/config.jsonl"
        with open(path_to_save, "w") as f:
            for config in self.configs:
                f.write(json.dumps(config) + "\n")

        metric_dir = f"{dir_path}/metric"
        xplogger_utils.make_dir(metric_dir)
        for key in self.metrics:
            path_to_save = f"{metric_dir}/{key}"
            if self.metrics[key].empty:
                pass
            else:
                self.metrics[key].to_feather(path=path_to_save)

        path_to_save = f"{dir_path}/info.gzip"
        with gzip.open(path_to_save, "wb") as f:  # type: ignore[assignment]
            f.write(json.dumps(self.info).encode("utf-8"))  # type: ignore[arg-type]

    def __eq__(self, other: object) -> bool:
        """Compare two `Experiment` objects."""
        if not isinstance(other, Experiment):
            return NotImplemented
        return (
            self.configs == other.configs
            and xplogger_utils.compare_keys_in_dict(self.metrics, other.metrics)
            and all(
                self.metrics[key].equals(other.metrics[key]) for key in self.metrics
            )
            and xplogger_utils.compare_keys_in_dict(self.info, other.info)
            and all(self.info[key] == other.info[key] for key in self.info)
        )


def deserialize(dir_path: str) -> Experiment:
    """Deserialize the experiment data stored at `dir_path` and return an Experiment object."""
    path_to_load_from = f"{dir_path}/config.jsonl"
    configs = []
    with open(path_to_load_from) as f:
        for line in f:
            configs.append(json.loads(line))

    metrics = {}
    dir_to_load_from = Path(f"{dir_path}/metric/")
    for path_to_load_metric in dir_to_load_from.iterdir():
        if path_to_load_metric.is_file():
            key = path_to_load_metric.parts[-1]
            metrics[key] = pd.read_feather(path_to_load_metric)
    if not metrics:
        metrics["all"] = pd.DataFrame()

    path_to_load_from = f"{dir_path}/info.gzip"
    with gzip.open(path_to_load_from, "rb") as f:  # type: ignore[assignment]
        info = json.loads(f.read().decode("utf-8"))  # type: ignore[attr-defined]

    return Experiment(configs=configs, metrics=metrics, info=info)


class ExperimentSequence(UserList):  # type: ignore
    def __init__(self, experiments: List[Experiment]):
        """List-like interface to a collection of Experiments."""
        super().__init__(experiments)

    def groupby(
        self, group_fn: Callable[[Experiment], str]
    ) -> Dict[str, "ExperimentSequence"]:
        """Group experiments in the sequence.

        Args:
            group_fn: Function to assign a string group id to the experiment

        Returns:
            Dict[str, ExperimentSequence]: A dictionary mapping the sring
            group id to a sequence of experiments
        """
        grouped_experiments: Dict[str, List[Experiment]] = {}
        for experiment in self.data:
            key = group_fn(experiment)
            if key not in grouped_experiments:
                grouped_experiments[key] = []
            grouped_experiments[key].append(experiment)

        return {
            key: ExperimentSequence(value) for key, value in grouped_experiments.items()
        }

    def filter(self, filter_fn: Callable[[Experiment], bool]) -> "ExperimentSequence":
        """Filter experiments in the sequence.

        Args:
            filter_fn: Function to filter an experiment

        Returns:
            ExperimentSequence: A sequence of experiments for which the
            filter condition is true
        """
        return ExperimentSequence(
            [experiment for experiment in self.data if filter_fn(experiment)]
        )

    def aggregate(
        self,
        aggregate_configs: Callable[
            [List[List[ConfigType]]], List[ConfigType]
        ] = experiment_utils.return_first_config,
        aggregate_metrics: Callable[
            [List[experiment_utils.ExperimentMetricType]],
            experiment_utils.ExperimentMetricType,
        ] = experiment_utils.concat_metrics,
        aggregate_infos: Callable[
            [List[experiment_utils.ExperimentInfoType]],
            experiment_utils.ExperimentInfoType,
        ] = experiment_utils.return_first_infos,
    ) -> Experiment:
        """Aggregate a sequence of experiments into a single experiment.

        Args:
            aggregate_configs (Callable[ [List[List[ConfigType]]], List[ConfigType] ], optional):
                Function to aggregate the configs. Defaults to experiment_utils.return_first_config.
            aggregate_metrics (Callable[ [List[experiment_utils.ExperimentMetricType]], ExperimentMetricType ], optional):
                Function to aggregate the metrics. Defaults to experiment_utils.concat_metrics.
            aggregate_infos (Callable[ [List[experiment_utils.ExperimentInfoType]], ExperimentInfoType ], optional):
                Function to aggregate the information. Defaults to experiment_utils.return_first_infos.

        Returns:
            Experiment: Aggregated Experiment.
        """
        return Experiment(
            configs=aggregate_configs([exp.configs for exp in self.data]),
            metrics=aggregate_metrics([exp.metrics for exp in self.data]),
            info=aggregate_infos([exp.info for exp in self.data]),
        )

    def get_param_groups(
        self, params_to_exclude: Iterable[str]
    ) -> Tuple[ConfigType, Dict[str, Set[Any]]]:
        """Return two groups of params, one which is fixed across the experiments and one which varies.

        This function is useful when understanding the effect of different parameters on the model's
        performance. One could plot the performance of the different experiments, as a function of the
        parameters that vary.

        Args:
            params_to_exclude (Iterable[str]): These parameters are not returned in either group.
                This is useful for ignoring parameters like `time when the experiment was started`
                since these parameters should not affect the performance. In absence of this argument,
                all such parameters will likely be returned with the group of varying parameters.

        Returns:
            Tuple[ConfigType, Dict[str, Set[Any]]]: The first group/config contains the params which are fixed across the experiments.
                It maps these params to their `default` values, hence it should be a subset of any config.
                The second group/config contains the params which vary across the experiments.
                It maps these params to the set of values they take.
        """
        return parser_utils.get_param_groups(
            configs=(experiment.config for experiment in self.data),
            params_to_exclude=params_to_exclude,
        )


ExperimentList = ExperimentSequence
