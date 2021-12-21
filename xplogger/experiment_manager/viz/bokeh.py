from __future__ import annotations

import math
from typing import Any, Callable, Optional

from bokeh.plotting import figure

from xplogger.parser.experiment import ExperimentSequenceDict


def plot_experiment_sequence_dict(
    exp_seq_dict: ExperimentSequenceDict,
    get_experiment_name: Callable[[str], str],
    metadata_for_plot: dict[str, Any],
    color_palette: list[Any],
    y_metric_list: list[str],
    x_metric: str,
    mode: str,
    p: Optional[figure],
    colors=None,
    color_offset: int = 0,
    kwargs_for_exp_seq_dict=None,
) -> figure:
    #
    if not kwargs_for_exp_seq_dict:
        kwargs_for_exp_seq_dict = {}
    data = exp_seq_dict.aggregate_metrics(
        get_experiment_name=get_experiment_name,
        metric_names=y_metric_list,
        x_name=x_metric,
        mode=mode,
        **kwargs_for_exp_seq_dict
    )

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
