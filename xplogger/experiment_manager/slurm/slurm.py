"""Functions to interact with the SLURM system."""
from __future__ import annotations

import subprocess  # noqa: S404
from typing import Any

import pandas as pd


def get_info_from_slurm(job_id: str) -> dict[str, Any]:
    """Get info about a specific job from slurm.

    Args:
        job_id (str):

    Returns:
        dict[str, Any]: job info.
    """
    command = f"sacct --format='JobID,JobName%300,State' -j {job_id}"
    result = (
        subprocess.check_output(command, shell=True)  # noqa: S602
        .decode("utf-8")
        .rstrip()
    )
    keys = ["job_id", "job_name", "state"]
    info = {key: value for (key, value) in zip(keys, result.split("\n")[2].split())}
    return info


def get_running_jobs() -> pd.DataFrame:
    """Get a dataframe of running jobs.

    Returns:
        pd.DataFrame:
    """
    command = "squeue -u $USER -o '%.8Q %.15i %.3P %.9j %.6u %.2t %.16S %.10M %.10l %.5D %.12b %.2c %.4m %R' -S -t,-p,i"
    result = (
        subprocess.check_output(command, shell=True)  # noqa: S602
        .decode("utf-8")
        .strip()
    )
    result_list = [x.strip() for x in result.split("\n") if x.strip()]
    keys = result_list[0].split()
    info = [
        {key: value for (key, value) in zip(keys, values.split())}
        for values in result_list[1:]
    ]
    return pd.DataFrame.from_dict(info)
