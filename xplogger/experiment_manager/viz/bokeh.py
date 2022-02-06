"""Utlities functions to make bokeh plots."""
from __future__ import annotations

import math
from typing import Any, Optional

from bokeh.plotting import figure

from xplogger.experiment_manager.viz.utils import (
    get_data_and_colors,
    validate_kwargs_for_aggregate_metrics,
)
from xplogger.parser.experiment import ExperimentSequenceDict  # type: ignore


def plot_experiment_sequence_dict(
    exp_seq_dict: ExperimentSequenceDict,
    metadata_for_plot: dict[str, Any],
    color_palette: list[Any],
    p: Optional[figure],
    colors: Optional[list[str]] = None,
    color_offset: int = 0,
    return_all_metrics_with_same_length: bool = True,
    kwargs_for_aggregate_metrics: Optional[dict[str, Any]] = None,
) -> figure:
    """Plot the given experiment sequence dict.

    Args:
        exp_seq_dict (ExperimentSequenceDict):
        metadata_for_plot (dict[str, Any]):
        color_palette (list[Any]):
        p (Optional[figure]):
        colors (Optional[list[str]], optional): Defaults to None.
        color_offset (int, optional): Defaults to 0.
        kwargs_for_aggregate_metrics (Optional[dict[str, Any]], optional):
            These arguments are pass to aggregation function of exp_seq_dict.
            Defaults to None.

    Returns:
        figure:
    """
    if not kwargs_for_aggregate_metrics:
        kwargs_for_aggregate_metrics = {}

    validate_kwargs_for_aggregate_metrics(
        kwargs_for_aggregate_metrics=kwargs_for_aggregate_metrics
    )

    x_metric = kwargs_for_aggregate_metrics["x_name"]
    y_metric_list = kwargs_for_aggregate_metrics["metric_names"]

    if not p:
        p = figure(
            title=metadata_for_plot.get("title", "Default Title"),
            x_axis_label=x_metric,
            y_axis_label="-".join(y_metric_list),
            tooltips="(@x, @y)",
        )

    data, colors = get_data_and_colors(
        exp_seq_dict=exp_seq_dict,
        return_all_metrics_with_same_length=return_all_metrics_with_same_length,
        kwargs_for_aggregate_metrics=kwargs_for_aggregate_metrics,
        color_palette=color_palette,
        colors=colors,
        color_offset=color_offset,
    )

    for index, (key, y) in enumerate(data.items(), color_offset):
        if key.endswith(f"_{x_metric}"):
            continue
        for current_metric_name in y_metric_list:
            if key.endswith(current_metric_name):
                current_exp_seq_key = key.replace(f"_{current_metric_name}", "")
                break
        else:
            print("Can not find the metric name.")
        x_key = f"{current_exp_seq_key}_{x_metric}"
        x = data[x_key].mean(axis=0)
        mean = y.mean(axis=0)
        stderr = y.std(axis=0) / math.sqrt(len(y))
        p.line(x, mean, line_width=2, color=colors[index], legend_label=key)
        p.varea(
            x,
            mean - stderr,
            mean + stderr,
            fill_alpha=metadata_for_plot.get("fill_alpha", 0.6),
            color=colors[index],
        )

    p.legend.location = "bottom_right"
    p.legend.click_policy = "hide"
    return p
