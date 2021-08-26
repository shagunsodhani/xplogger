from __future__ import annotations

import math
from typing import Any, Callable

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
) -> figure:
    #
    data = exp_seq_dict.aggregate_metrics(
        get_experiment_name=get_experiment_name,
        metric_list=y_metric_list,
        x_metric=x_metric,
        mode=mode,
    )

    p = figure(
        title=metadata_for_plot.get("title", "Default Title"),
        x_axis_label=x_metric,
        y_axis_label="-".join(y_metric_list),
        tooltips="(@x, @y)",
    )
    try:
        colors = color_palette[len(data)]
    except KeyError:
        # this could be because we have fewer data points than 3
        colors = color_palette[3][: len(data)]
    for index, (key, y) in enumerate(data.items()):
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