# type: ignore
"""Utlities functions to make it easier to use xplogger with a jupyter notebook."""

from __future__ import annotations

import itertools
from typing import Any

import numpy as np
import pandas as pd
from omegaconf import DictConfig, OmegaConf

from xplogger.experiment_manager.record.record_list import RecordList
from xplogger.parser.experiment.experiment import (
    ExperimentSequence,
    ExperimentSequenceDict,
)
from xplogger.types import ValueType


def prettyprint_dict(d: dict, sep: str = "\t", indent: int = 0) -> None:
    r"""Pretty print a dictionary.

    Args:
        d (dict): input dictionary
        sep (str, optional): Seperator to use. Defaults to "\t".
        indent (int, optional): Indentation to use. Defaults to 0.
    """
    for key, value in d.items():
        print(sep * indent + str(key))
        if isinstance(value, dict):
            prettyprint_dict(d=value, indent=indent + 1)
        else:
            print(sep * (indent + 1) + str(value))


def get_mean_and_std_err(
    experiment_sequence: ExperimentSequence, metadata: DictConfig
) -> tuple[np.typing.NDArray[np.float32], np.typing.NDArray[np.float32], int]:
    """Compute the mean and standard error for a given experiment sequence.

    Args:
        experiment_sequence (ExperimentSequence):
        metadata (DictConfig): metadata to use for computing the metrics

    Returns:
        tuple[np.typing.NDArray[np.float32], np.typing.NDArray[np.float32], int]:
            tuple of mean, standard error and number of experiments in the
            experiment sequence (useful for computing standard deviation etc).
    """
    aggregated_metrics = experiment_sequence.aggregate_metrics(
        metric_names=[metadata.metric_name],
        x_name=metadata.x.name,
        x_min=metadata.x.min,
        x_max=metadata.x.max,
        mode=metadata.mode,
        drop_duplicates=True,
        verbose=True,
        dropna=False,
    )
    metrics = aggregated_metrics[metadata.metric_name]

    mean = np.mean(metrics, axis=0)
    std = np.std(metrics, axis=0) / np.sqrt(metrics.shape[0])
    return mean, std, metrics.shape[0]


def make_df(  # noqa: C901
    metadata: DictConfig,
    step_metadata: DictConfig,
    groups: dict[Any, RecordList],
    hyperparams: dict[str, set[ValueType]],
    exp_seq_dict: ExperimentSequenceDict,
) -> pd.DataFrame:
    """Make a dataframe using the given experience sequence dict.

    Args:
        metadata (DictConfig): Contains information like metric_name for
            the metrics of interest.
        step_metadata (DictConfig): Contains information like metric_name for
            the step metric (eg epoch or frames)
        groups (dict[Any, RecordList]):
        hyperparams (dict[str, set[ValueType]]):
        exp_seq_dict (ExperimentSequenceDict):

    Returns:
        pd.DataFrame:
    """
    metrics = [
        f"mean_{metadata.metric_name}",
        f"stderr_{metadata.metric_name}",
        "steps",
    ]

    results: dict[str, Any] = {
        "aggregated": {},
        "converged": {},
    }
    for key in list(hyperparams.keys()) + metrics + ["seeds"]:
        for mode in ["aggregated", "converged"]:
            results[mode][key] = []

    valid_params = [
        params
        for params in [
            OmegaConf.create({k: v for k, v in zip(hyperparams.keys(), _product)})
            for _product in itertools.product(*hyperparams.values())
        ]
        if params in groups
    ]

    for combination in valid_params:
        for key in hyperparams:
            for mode in ["aggregated", "converged"]:
                results[mode][key].append(combination[key])
        try:
            mean, std_err, num_seeds = get_mean_and_std_err(
                exp_seq_dict[combination], metadata
            )
            mean_steps, _, _ = get_mean_and_std_err(
                exp_seq_dict[combination], step_metadata
            )
            if mean is None or std_err is None:
                metric_name = metadata.metric_name
                results["converged"][f"stderr_{metric_name}"].append(None)
                results["converged"][f"mean_{metric_name}"].append(None)
                results["aggregated"][f"stderr_{metric_name}"].append(None)
                results["aggregated"][f"mean_{metric_name}"].append(None)
            else:
                metric_name = metadata.metric_name
                results["converged"][f"stderr_{metric_name}"].append(
                    std_err[np.argmax(mean)]
                )
                results["converged"][f"mean_{metric_name}"].append(np.max(mean))
                # error: Call to untyped function "max" in typed context
                results["aggregated"][f"stderr_{metric_name}"].append(std_err[-1])
                results["aggregated"][f"mean_{metric_name}"].append(mean[-1])
            if mean_steps is None:
                for mode in ["aggregated", "converged"]:
                    results[mode]["steps"].append(None)
            else:
                results["converged"]["steps"].append(np.max(mean_steps))
                results["aggregated"]["steps"].append(mean_steps[-1])
            for mode in ["aggregated", "converged"]:
                results[mode]["seeds"].append(num_seeds)
        except Exception as e:
            print(e)
            for key in hyperparams:
                for mode in ["aggregated", "converged"]:
                    results[mode][key].pop(-1)

    return pd.DataFrame.from_dict(results["converged"])


# import matplotlib.pyplot as plt
# from xplogger.experiment_manager.result import Result
# def plot_result(result: Result, mode: str, metric: str) -> None:
#     info = result.info
#     steps = (
#         result.metrics[mode]["steps"] * result.info[mode]["x"]["alpha"]
#         + result.info[mode]["x"]["beta"]
#     )
#     y_mean = (
#         result.metrics[mode][f"{metric}_mean"] * result.info[mode]["y"]["alpha"]
#         + result.info[mode]["y"]["beta"]
#     )

#     y_stderr = result.metrics[mode][f"{metric}_stderr"]

#     plt.plot(steps, y_mean, label=result.label)

#     plt.fill_between(steps, y_mean - y_stderr, y_mean + y_stderr, alpha=0.1)
