"""Implementation of Parser to parse metrics from logs."""

from __future__ import annotations

from typing import Callable, Optional

import pandas as pd

from xplogger.parser import log as log_parser
from xplogger.types import LogType, MetricType, ParseLineFunctionType


def parse_json_and_match_value(line: str) -> Optional[LogType]:
    """Parse a line as JSON log and check if it a valid metric log."""
    return log_parser.parse_json_and_match_value(line=line, value="metric")


def group_metrics(metrics: list[MetricType]) -> dict[str, list[MetricType]]:
    """Group a list of metrics.

    Group a list of metrics into a dictionary of
        (key, list of grouped metrics)

    Args:
        metrics (list[MetricType]): list of metrics to group

    Returns:
        dict[str, list[MetricType]]: Dictionary of (key,
            list of grouped metrics)
    """
    return {"all": metrics}


def aggregate_metrics(metrics: list[MetricType]) -> list[MetricType]:
    """Aggregate a list of metrics.

    Args:
        metrics (list[MetricType]): list of metrics to aggregate

    Returns:
        list[MetricType]: list of aggregated metrics
    """
    return metrics


class Parser(log_parser.Parser):
    """Class to parse the metrics from the logs."""

    def __init__(self, parse_line: ParseLineFunctionType = parse_json_and_match_value):
        """Class to parse the metrics from the logs.

        Args:
            parse_line (ParseLineFunctionType):
                Function to parse a line in the log file. The function
                should return None if the line is not a valid log statement
                (eg error messages). Defaults to parse_json_and_match_value.
        """
        super().__init__(parse_line)
        self.log_type = "metric"

    def parse_as_df(
        self,
        filepath_pattern: str,
        group_metrics: Callable[
            [list[LogType]], dict[str, list[LogType]]
        ] = group_metrics,
        aggregate_metrics: Callable[[list[LogType]], list[LogType]] = aggregate_metrics,
    ) -> dict[str, pd.DataFrame]:
        """Create a dict of (metric_name, dataframe).

        Method that:
        (i) reads metrics from the filesystem
        (ii) groups metrics
        (iii) aggregates all the metrics within a group,
        (iv) converts the aggregate metrics into dataframes and returns a \
            dictionary of dataframes

        Args:
            filepath_pattern (str): filepath pattern to glob
            group_metrics (Callable[[list[LogType]], dict[str, list[LogType]]], optional):
                Function to group a list of metrics into a dictionary of
                (key, list of grouped metrics). Defaults to group_metrics.
            aggregate_metrics (Callable[[list[LogType]], list[LogType]], optional):
                Function to aggregate a list of metrics. Defaults to aggregate_metrics.

        """
        metric_logs = list(self.parse(filepath_pattern))
        return metrics_to_df(
            metric_logs=metric_logs,
            group_metrics=group_metrics,
            aggregate_metrics=aggregate_metrics,
        )


def metrics_to_df(
    metric_logs: list[LogType],
    group_metrics: Callable[[list[LogType]], dict[str, list[LogType]]] = group_metrics,
    aggregate_metrics: Callable[[list[LogType]], list[LogType]] = aggregate_metrics,
) -> dict[str, pd.DataFrame]:
    """Create a dict of (metric_name, dataframe).

    Method that:
    (i) groups metrics
    (ii) aggregates all the metrics within a group,
    (iii) converts the aggregate metrics into dataframes and returns a \
        dictionary of dataframes

    Args:
        metric_logs (list[LogType]): list of metrics
        group_metrics (Callable[[list[LogType]], dict[str, list[LogType]]], optional):
            Function to group a list of metrics into a dictionary of
            (key, list of grouped metrics). Defaults to group_metrics.
        aggregate_metrics (Callable[[list[LogType]], list[LogType]], optional):
            Function to aggregate a list of metrics. Defaults to aggregate_metrics.

    Returns:
        dict[str, pd.DataFrame]: [description]

    """
    grouped_metrics: dict[str, list[LogType]] = group_metrics(metric_logs)
    aggregated_metrics = {
        key: aggregate_metrics(metrics) for key, metrics in grouped_metrics.items()
    }

    metric_dfs = {
        key: pd.json_normalize(data=metrics)
        for key, metrics in aggregated_metrics.items()
    }
    return metric_dfs
