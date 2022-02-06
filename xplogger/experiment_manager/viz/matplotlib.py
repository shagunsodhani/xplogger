"""Utlities functions to make bokeh plots."""
from __future__ import annotations

import math
from typing import Any, Optional

from matplotlib import pyplot as plt

from xplogger.experiment_manager.viz.utils import (
    get_data_and_colors,
    validate_kwargs_for_aggregate_metrics,
)
from xplogger.parser.experiment import ExperimentSequenceDict  # type: ignore


def plot_experiment_sequence_dict(
    exp_seq_dict: ExperimentSequenceDict,
    metadata_for_plot: dict[str, Any],
    color_palette: list[Any],
    colors: Optional[list[str]] = None,
    color_offset: int = 0,
    return_all_metrics_with_same_length: bool = True,
    kwargs_for_aggregate_metrics: Optional[dict[str, Any]] = None,
) -> None:
    """Plot the given experiment sequence dict as a matplotlib.

    Args:
        exp_seq_dict (ExperimentSequenceDict):
        metadata_for_plot (dict[str, Any]):
        color_palette (list[Any]):
        colors (Optional[list[str]], optional): Defaults to None.
        color_offset (int, optional): Defaults to 0.
        kwargs_for_aggregate_metrics (Optional[dict[str, Any]], optional):
            These arguments are pass to aggregation function of exp_seq_dict.
            Defaults to None.

    Returns:
        figure:
    """
    validate_kwargs_for_aggregate_metrics(
        kwargs_for_aggregate_metrics=kwargs_for_aggregate_metrics
    )

    x_metric = kwargs_for_aggregate_metrics["x_name"]  # type: ignore
    y_metric_list = kwargs_for_aggregate_metrics["metric_names"]  # type: ignore

    plt.title(metadata_for_plot.get("title", "Default Title"))
    plt.xlabel(x_metric)
    plt.ylabel("-".join(y_metric_list))

    data, colors = get_data_and_colors(
        exp_seq_dict=exp_seq_dict,
        return_all_metrics_with_same_length=return_all_metrics_with_same_length,
        kwargs_for_aggregate_metrics=kwargs_for_aggregate_metrics,  # type: ignore
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
            breakpoint()
        x_key = f"{current_exp_seq_key}_{x_metric}"
        x = data[x_key].mean(axis=0)
        mean = y.mean(axis=0)
        stderr = y.std(axis=0) / math.sqrt(len(y))
        plt.plot(x, mean, linewidth=2, color=colors[index], label=key)
        plt.fill_between(
            x=x,
            y1=mean - stderr,
            y2=mean + stderr,
            alpha=metadata_for_plot.get("fill_alpha", 0.6),
            color=colors[index],
        )
