"""Functions to interact with the SLURM system."""
from __future__ import annotations

import subprocess  # noqa: S404
from typing import Optional

import pandas as pd

from xplogger.experiment_manager.slurm.ds import SlurmInfo, SlurmInfoList
from xplogger.experiment_manager.store.mongo import MongoStore


def _get_running_jobs(user: str = "$USER") -> list[dict[str, str]]:
    """Get a list of running jobs.

    Returns:
        list[dict[str, str]]: Each entry in the list is a dict of job info
    """
    command = f"squeue -u {user} -o '%.8Q %.40A %.20P %.300j %.20u %.20T %.16S %.10M %.10l %.5D %.12b %.2c %.4m %R' -S -t,-p,i"
    result = (
        subprocess.check_output(command, shell=True)  # noqa: S602
        .decode("utf-8")
        .strip()
    )

    result_list = [x.strip() for x in result.split("\n") if x.strip()]
    keys = result_list[0].split()
    jobs = [
        {key: value for (key, value) in zip(keys, values.split())}
        for values in result_list[1:]
    ]
    return jobs


def get_running_jobs_as_df(
    user: str = "$USER", mongo_stores: Optional[list[MongoStore]] = None
) -> pd.DataFrame:
    """Get a dataframe of running jobs.

    Returns:
        pd.DataFrame:
    """
    return pd.DataFrame(get_running_jobs_as_list(user=user, mongo_stores=mongo_stores))


def get_running_jobs_as_list(
    user: str = "$USER", mongo_stores: Optional[list[MongoStore]] = None
) -> SlurmInfoList:
    """Get a list of SlurmInfo objects corresponding to running jobs.

    Returns:
        list[SlurmInfo]: [running jobs]

    """
    slurm_info_list = SlurmInfoList(
        [SlurmInfo.from_dict(job) for job in _get_running_jobs(user=user)]
    )
    if mongo_stores:
        slurm_info_list.populate_additional_fields(mongo_stores=mongo_stores)
    return slurm_info_list
