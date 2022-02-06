"""Functions to interact with the SLURM system."""
from __future__ import annotations

import subprocess  # noqa: S404
from typing import Any, cast


def map_jobid_to_raw_job_id(job_id: str) -> str:
    """Map job_id to raw job_id."""
    if "_" in job_id:
        return cast(str, get_info_from_slurm(job_id=job_id)["raw_job_id"])
    else:
        return job_id


def get_info_from_slurm(job_id: str) -> dict[str, Any]:
    """Get info about a specific job from slurm.

    Args:
        job_id (str):

    Returns:
        dict[str, Any]: job info.
    """
    command = f"sacct --format='JobID%30,JobName%300,State,JobIDRaw' -j {job_id}"
    print(command)
    result = (
        subprocess.check_output(command, shell=True)  # noqa: S602
        .decode("utf-8")
        .rstrip()
    )
    keys = ["job_id", "job_name", "state", "raw_job_id"]
    info = {key: value for (key, value) in zip(keys, result.split("\n")[2].split())}
    return info
