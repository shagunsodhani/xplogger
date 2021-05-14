"""Utilit functions to work with the experiment data"""

from typing import Any, Dict, List

import pandas as pd

from xplogger.types import ConfigType

ExperimentMetricType = Dict[str, pd.DataFrame]
ExperimentInfoType = Dict[Any, Any]


def return_first_config(config_lists: List[List[ConfigType]]) -> List[ConfigType]:
    """Return the first config list, from a list of list of configs, else return empty list.

    Args:
        config_lists (List[List[ConfigType]])

    Returns:
        List[ConfigType]
    """
    for config_list in config_lists:
        if len(config_list) > 0:
            return config_list
    return []


def concat_metrics(metric_list: List[ExperimentMetricType]) -> ExperimentMetricType:
    """Concatenate the metrics.

    Args:
        metric_list (List[ExperimentMetricType])

    Returns:
        ExperimentMetricType
    """
    concatenated_metrics = {}
    metric_keys = metric_list[0].keys()
    for key in metric_keys:
        concatenated_metrics[key] = pd.concat([metric[key] for metric in metric_list])
    return concatenated_metrics


def return_first_infos(info_list: List[ExperimentInfoType]) -> ExperimentInfoType:
    """Return the first info, from a list of infos. Otherwise return empty info.

    Args:
        info_list (List[ExperimentInfoType])

    Returns:
        ExperimentInfoType
    """
    for info in info_list:
        if info is not None:
            return info
    return {}
