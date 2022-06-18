"""Container for the experiment data."""

from __future__ import annotations

import gzip
import json
from collections import UserDict, UserList
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

import numpy as np
import pandas as pd

from xplogger import utils as xplogger_utils
from xplogger.parser import utils as parser_utils
from xplogger.parser.experiment import utils as experiment_utils
from xplogger.types import ConfigType


class Experiment:
    def __init__(
        self,
        configs: list[ConfigType],
        metrics: experiment_utils.ExperimentMetricType,
        info: Optional[experiment_utils.ExperimentInfoType] = None,
    ):
        """Class to hold the experiment data.

        Args:
            configs (list[ConfigType]): Configs used for the experiment
            metrics (experiment_utils.ExperimentMetricType): Dictionary mapping strings
                to dataframes. Keys could be "train", "validation", "test"
                and corresponding dataframes would have the data for these
                modes.
            info (Optional[dict[Any, Any]], optional): A dictionary where the user can store
                any information about the experiment (that does not fit
                within config and metrics). Defaults to None.
        """
        self.configs = configs
        self.metrics = metrics
        self.info: dict[Any, Any] = {}
        if info is not None:
            self.info = info

    @property
    def config(self) -> Optional[ConfigType]:
        """Access the config property."""
        if len(self.configs) > 0:
            return self.configs[-1]
        return None

    def serialize(self, dir_path: Path) -> None:
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

        metric_dir = dir_path.joinpath("metric")
        xplogger_utils.make_dir(metric_dir)
        for key in self.metrics:
            path_to_save = f"{metric_dir}/{key}"
            if self.metrics[key].empty:
                pass
            else:
                self.metrics[key].to_feather(path=path_to_save)

        path_to_save = f"{dir_path}/info.gzip"
        with gzip.open(path_to_save, "wb") as f:
            f.write(json.dumps(self.info).encode("utf-8"))

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

    def process_metrics(
        self,
        metric_names: list[str],
        x_name: str,
        x_min: int,
        x_max: int,
        mode: str,
        drop_duplicates: bool,
        dropna: bool,
        verbose: bool,
    ) -> dict[str, np.typing.NDArray[np.float32]]:
        """Given a list of metric names, process the metrics for a given experiment.

        Args:
            metric_names (list[str]): Names of metrics to process.
            x_name (str): The column/meric with respect to which other metrics
                are tracked. For example `steps` or `epochs`.
            x_min (int): Filter the experiment where the max value of `x_name`
                is less than or equal to `x_min`.
            x_max (int): Filter the metric values where value of `x_name`
                (corresponding to metric values) is greater than `x_max`
            mode (str): Mode when selecting metrics. Recall that `experiment.metrics`
                is a dictionary mapping `modes` to dataframes.
            drop_duplicates (bool): Should drop duplicate values in the `x_name` column
            verbose (bool): Should print additional information

        Returns:
            dict[str, np.ndarray]: dictionary mapping metric name to 1-dimensional
                numpy array of metric values.
        """
        if mode not in self.metrics:
            return {}
        df = self.metrics[mode]
        if any(name not in df for name in metric_names):
            return {}
        filters = df[x_name] <= x_max
        df = df[filters]
        if drop_duplicates:
            df = df.drop_duplicates(subset=[x_name], keep="first")
        if df.isnull().any().any() and verbose:
            print("df contains NaNs")
        if dropna:
            df = df.dropna(subset=metric_names, axis=0)
        if df[x_name].iloc[-1] >= x_min and all(
            len(df[name]) > 0 for name in metric_names
        ):
            return {name: df[name].to_numpy() for name in metric_names}
        return {}

    def log_to_wandb(self, wandb_config: dict[str, Any]) -> "LogBook":  # type: ignore # noqa: F821
        """Log the experiment to wandb."""
        from xplogger.logbook import LogBook, make_config

        name = "experiment_wandb_logger"

        key = "project"
        assert self.config is not None
        if key not in wandb_config:
            wandb_config[key] = self.config["logbook"]["mongo_config"]["collection"]

        for key in ["name"]:
            if key not in wandb_config:
                wandb_config[key] = self.config["setup"]["id"]

        logbook_config = make_config(
            id=name, name=name, write_to_console=False, wandb_config=wandb_config
        )
        logbook = LogBook(config=logbook_config)
        logbook.write_config(self.config)
        for metric in self.metrics["train_epoch"].to_dict("records"):
            logbook.write_metric(metric)

        return logbook


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
    with gzip.open(path_to_load_from, "rb") as f:
        info = json.loads(f.read().decode("utf-8"))

    return Experiment(configs=configs, metrics=metrics, info=info)


class ExperimentSequence(UserList):  # type: ignore
    def __init__(self, experiments: list[Experiment]):
        """list-like interface to a collection of Experiments."""
        super().__init__(experiments)

    def groupby(
        self, group_fn: Callable[[Experiment], str]
    ) -> dict[str, "ExperimentSequence"]:
        """Group experiments in the sequence.

        Args:
            group_fn: Function to assign a string group id to the experiment

        Returns:
            dict[str, ExperimentSequence]: A dictionary mapping the sring
            group id to a sequence of experiments
        """
        grouped_experiments: dict[str, list[Experiment]] = {}
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
            [list[list[ConfigType]]], list[ConfigType]
        ] = experiment_utils.return_first_config,
        aggregate_metrics: Callable[
            [list[experiment_utils.ExperimentMetricType]],
            experiment_utils.ExperimentMetricType,
        ] = experiment_utils.concat_metrics,
        aggregate_infos: Callable[
            [list[experiment_utils.ExperimentInfoType]],
            experiment_utils.ExperimentInfoType,
        ] = experiment_utils.return_first_infos,
    ) -> Experiment:
        """Aggregate a sequence of experiments into a single experiment.

        Args:
            aggregate_configs (Callable[ [list[list[ConfigType]]], list[ConfigType] ], optional):
                Function to aggregate the configs. Defaults to experiment_utils.return_first_config.
            aggregate_metrics (Callable[ [list[experiment_utils.ExperimentMetricType]], ExperimentMetricType ], optional):
                Function to aggregate the metrics. Defaults to experiment_utils.concat_metrics.
            aggregate_infos (Callable[ [list[experiment_utils.ExperimentInfoType]], ExperimentInfoType ], optional):
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
    ) -> tuple[ConfigType, dict[str, set[Any]]]:
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
            tuple[ConfigType, dict[str, set[Any]]]: The first group/config contains the params which are fixed across the experiments.
                It maps these params to their `default` values, hence it should be a subset of any config.
                The second group/config contains the params which vary across the experiments.
                It maps these params to the set of values they take.
        """
        return parser_utils.get_param_groups(
            configs=(experiment.config for experiment in self.data),
            params_to_exclude=params_to_exclude,
        )

    def aggregate_metrics(
        self,
        **kwargs: Any,
    ) -> dict[str, np.typing.NDArray[np.float32]]:
        """Aggregate metrics across experiment sequences.

        Given a list of metric names, aggreate the metrics across different
        experiments in an experiment sequence.


        Args:
            metric_names (list[str]): Names of metrics to aggregate.
            x_name (str): The column/meric with respect to which other metrics
                are tracked. For example `steps` or `epochs`. This aggregated values
                for this metric are also returned.
            x_min (int): Only those experiments are considered (during aggregation)
                where the max value of `x_name` is greater than or equal to `x_min`.
            x_max (int): When aggregating experiments, consider metric values such
                that the max value of `x_name` corresponding to metric values
                is less than or equal to `x_max`
            mode (str): Mode when selecting metrics. Recall that `experiment.metrics`
                is a dictionary mapping `modes` to dataframes.
            drop_duplicates (bool): Should drop duplicate values in the `x_name` column
            verbose (bool): Should print additional information

        Returns:
            dict[str, np.ndarray]: dictionary mapping metric name to 2-dimensional
                numpy array of metric values. The first dimension corresponds to the
                experiments and the second corresponds to metrics per experiment.
        """
        for key in [
            "metric_names",
            "x_name",
            "x_min",
            "x_max",
            "mode",
            "drop_duplicates",
            "dropna",
            "verbose",
        ]:
            assert key in kwargs

        verbose = kwargs["verbose"]
        metric_names = kwargs["metric_names"]

        metric_dict: dict[str, list[np.typing.NDArray[np.float32]]] = {
            name: [] for name in metric_names
        }
        min_len = float("inf")
        num_skipped_experiments = 0

        for exp in self.data:
            exp_metric_dict = exp.process_metrics(**kwargs)
            if exp_metric_dict:
                for name in metric_names:
                    metric_dict[name].append(exp_metric_dict[name])
                min_len = min(min_len, len(metric_dict[name][-1]))
            else:
                num_skipped_experiments += 1
                continue

        if num_skipped_experiments > 0 and verbose:
            print(
                f"Skipped {num_skipped_experiments} experiments while parsing {len(self.data)} experiments."
            )
        if num_skipped_experiments == len(self.data):
            return {}
            # return metric_dict
        min_len = int(min_len)
        metric_dict_to_return: dict[str, np.typing.NDArray[np.float32]] = {
            name: np.asarray([x[:min_len].copy() for x in metric_list])
            for name, metric_list in metric_dict.items()
        }
        return metric_dict_to_return


ExperimentList = ExperimentSequence


class ExperimentSequenceDict(UserDict):  # type: ignore
    def __init__(self, experiment_sequence_dict: dict[Any, ExperimentSequence]):
        """dict-like interface to a collection of experiment sequences."""
        super().__init__(experiment_sequence_dict)

    def filter(
        self, filter_fn: Callable[[str, Experiment], bool]
    ) -> "ExperimentSequenceDict":
        """Filter experiment sequences in the dict.

        Args:
            filter_fn: Function to filter an experiment sequence

        Returns:
            ExperimentSequenceDict: A dict of sequence of experiments for which the
            filter condition is true
        """
        return ExperimentSequenceDict(
            {
                key: experiment_sequence
                for key, experiment_sequence in self.data.items()
                if filter_fn(key, experiment_sequence)
            }
        )

    def aggregate_metrics(
        self,
        return_all_metrics_with_same_length: bool = True,
        **kwargs: Any,
    ) -> dict[str, np.typing.NDArray[np.float32]]:
        """Aggreate metrics across experiment sequences.

        Given a list of metric names, aggreate the metrics across different
        experiment sequences in a dictionary indexed by the metric name.

        Args:
            get_experiment_name (Callable[[str], str]): Function to map the
                given key with a name.
            metric_names (list[str]): Names of metrics to aggregate.
            x_name (str): The column/meric with respect to which other metrics
                are tracked. For example `steps` or `epochs`. This aggregated values
                for this metric are also returned.
            mode (str): Mode when selecting metrics. Recall that `experiment.metrics`
                is a dictionary mapping `modes` to dataframes.

        Returns:
            dict[str, np.typing.NDArray[np.float32]]: dictionary mapping metric name to 2-dimensional
                numpy array of metric values. The first dimension corresponds to the
                experiments and the second corresponds to metrics per experiment.
        """
        for key in [
            "get_experiment_name",
            "metric_names",
            "x_name",
            "x_min",
            "x_max",
            "mode",
            "drop_duplicates",
            "dropna",
            "verbose",
        ]:
            assert key in kwargs

        get_experiment_name = kwargs.pop("get_experiment_name")
        metric_names = kwargs["metric_names"]
        mode: str = kwargs["mode"]
        x_name: str = kwargs["x_name"]

        if x_name not in metric_names:
            metric_names.append(x_name)

        metric_dict: dict[str, list[np.typing.NDArray[np.float32]]] = {}
        min_len = float("inf")

        for key, exp_seq in self.data.items():
            new_metric_names = {
                metric: f"{get_experiment_name(key, mode=mode)}_{metric}"
                for metric in metric_names
            }
            current_metric_dict = exp_seq.aggregate_metrics(**kwargs)
            for metric in metric_names:
                metric_dict[new_metric_names[metric]] = current_metric_dict[metric]
            min_len = min(min_len, len(current_metric_dict[metric][0]))
        min_len = int(min_len)

        metric_dict_with_array: dict[str, np.typing.NDArray[np.float32]] = {}

        for metric_name in metric_dict:
            if return_all_metrics_with_same_length:
                metric_dict_with_array[metric_name] = np.asarray(
                    [_metric[:min_len] for _metric in metric_dict[metric_name]]
                )
            else:
                metric_dict_with_array[metric_name] = np.asarray(
                    list(metric_dict[metric_name])
                )
        return metric_dict_with_array
