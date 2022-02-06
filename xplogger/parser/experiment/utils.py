"""Utilit functions to work with the experiment data."""

from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pandas as pd

from xplogger.types import ConfigType

ExperimentMetricType = Dict[str, pd.DataFrame]
ExperimentInfoType = Dict[Any, Any]


def return_first_config(config_lists: list[list[ConfigType]]) -> list[ConfigType]:
    """Return the first config list, from a list of list of configs, else return empty list.

    Args:
        config_lists (list[list[ConfigType]])

    Returns:
        list[ConfigType]
    """
    for config_list in config_lists:
        if len(config_list) > 0:
            return config_list
    return []


def concat_metrics(metric_list: list[ExperimentMetricType]) -> ExperimentMetricType:
    """Concatenate the metrics.

    Args:
        metric_list (list[ExperimentMetricType])

    Returns:
        ExperimentMetricType
    """
    concatenated_metrics = {}
    metric_keys = metric_list[0].keys()
    for key in metric_keys:
        concatenated_metrics[key] = pd.concat([metric[key] for metric in metric_list])
    return concatenated_metrics


def _compute_sum_or_mean_of_metrics_for_one_mode(
    metric_list: list[ExperimentMetricType], mode: str, return_mean: bool = True
) -> pd.DataFrame:
    metric_to_return: dict[str, Any] = {}
    min_len = np.iinfo(np.int32).max
    for metric in metric_list:
        df = metric[mode]
        for key in df.keys():
            if df.dtypes[key] == float or df.dtypes[key] == int:
                if key not in metric_to_return:
                    metric_to_return[key] = []
                metric_to_return[key].append(df[key].to_numpy())
                min_len = min(min_len, len(metric_to_return[key][-1]))
            else:
                if key not in metric_to_return:
                    metric_to_return[key] = df[key].to_numpy()
                    min_len = min(min_len, len(metric_to_return[key]))

    np_metric_to_return: dict[str, np.typing.NDArray[np.float32]] = {}
    for metric_name in metric_to_return:
        if isinstance(metric_to_return[metric_name][0], np.ndarray):
            np_metric_to_return[metric_name] = np.array(
                [x[:min_len] for x in metric_to_return[metric_name]]
            )
            if return_mean:
                np_metric_to_return[metric_name] = np_metric_to_return[
                    metric_name
                ].mean(axis=0)
            else:
                np_metric_to_return[metric_name] = np_metric_to_return[metric_name].sum(
                    axis=0
                )
        else:
            np_metric_to_return[metric_name] = metric_to_return[metric_name][:min_len]
    return pd.DataFrame.from_dict(np_metric_to_return)


def _compute_sum_or_mean_of_metrics(
    metric_list: list[ExperimentMetricType], return_mean: bool
) -> ExperimentMetricType:
    """Add the metrics.

    Args:
        metric_list (list[ExperimentMetricType])

    Returns:
        ExperimentMetricType
    """
    concatenated_metrics = {}
    metric_keys = metric_list[0].keys()
    for mode in metric_keys:
        concatenated_metrics[mode] = _compute_sum_or_mean_of_metrics_for_one_mode(
            metric_list=metric_list, mode=mode, return_mean=return_mean
        )
    return concatenated_metrics


def mean_metrics(metric_list: list[ExperimentMetricType]) -> ExperimentMetricType:
    """Compute the mean of the metrics.

    Args:
        metric_list (list[ExperimentMetricType])

    Returns:
        ExperimentMetricType
    """
    return _compute_sum_or_mean_of_metrics(metric_list=metric_list, return_mean=True)


def sum_metrics(metric_list: list[ExperimentMetricType]) -> ExperimentMetricType:
    """Compute the sum of the metrics.

    Args:
        metric_list (list[ExperimentMetricType])

    Returns:
        ExperimentMetricType
    """
    return _compute_sum_or_mean_of_metrics(metric_list=metric_list, return_mean=False)


def return_first_infos(info_list: list[ExperimentInfoType]) -> ExperimentInfoType:
    """Return the first info, from a list of infos. Otherwise return empty info.

    Args:
        info_list (list[ExperimentInfoType])

    Returns:
        ExperimentInfoType
    """
    for info in info_list:
        if info is not None:
            return info
    return {}
