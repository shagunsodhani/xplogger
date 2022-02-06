"""Utlities functions to make bokeh plots."""
from __future__ import annotations

from typing import Any, Optional

from xplogger.parser.experiment import ExperimentSequenceDict  # type: ignore


def validate_kwargs_for_aggregate_metrics(
    kwargs_for_aggregate_metrics: Optional[dict[str, Any]]
) -> None:
    """Validate that kwargs is not None and contains certain keys."""
    assert kwargs_for_aggregate_metrics is not None
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


def get_data_and_colors(
    exp_seq_dict: ExperimentSequenceDict,
    return_all_metrics_with_same_length: bool,
    kwargs_for_aggregate_metrics: dict[str, Any],
    color_palette: list[Any],
    colors: Optional[list[str]],
    color_offset: int,
) -> tuple[dict[str, Any], list[str]]:
    """Extract data and colors for generating the plots."""
    data = exp_seq_dict.aggregate_metrics(
        return_all_metrics_with_same_length=return_all_metrics_with_same_length,
        **kwargs_for_aggregate_metrics,
    )
    if colors is None:
        try:
            colors = color_palette[len(data) + color_offset]
        except KeyError:
            # this could be because we have fewer data points than 3
            colors = color_palette[3][: len(data) + color_offset]
    assert colors is not None

    return data, colors
