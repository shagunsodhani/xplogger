"""Utlities functions to make bokeh plots."""
from __future__ import annotations

import math
from typing import Any, Optional

from bokeh.plotting import figure

from xplogger.parser.experiment import ExperimentSequenceDict  # type: ignore


def plot_experiment_sequence_dict(
    exp_seq_dict: ExperimentSequenceDict,
    metadata_for_plot: dict[str, Any],
    color_palette: list[Any],
    p: Optional[figure],
    colors: Optional[list[str]] = None,
    color_offset: int = 0,
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
        assert key in kwargs_for_aggregate_metrics

    x_metric = kwargs_for_aggregate_metrics["x_name"]
    y_metric_list = kwargs_for_aggregate_metrics["metric_names"]

    data = exp_seq_dict.aggregate_metrics(**kwargs_for_aggregate_metrics)

    if not p:
        p = figure(
            title=metadata_for_plot.get("title", "Default Title"),
            x_axis_label=x_metric,
            y_axis_label="-".join(y_metric_list),
            tooltips="(@x, @y)",
        )
    if colors is None:
        try:
            colors = color_palette[len(data) + color_offset]
        except KeyError:
            # this could be because we have fewer data points than 3
            colors = color_palette[3][: len(data) + color_offset]
    assert colors is not None
    for index, (key, y) in enumerate(data.items(), color_offset):
        if key == x_metric:
            continue
        x = data[x_metric]
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
