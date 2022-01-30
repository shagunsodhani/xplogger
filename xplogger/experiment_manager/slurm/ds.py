"""Datastructures to interact with the SLURM system."""
from __future__ import annotations

from collections import UserDict, UserList
from dataclasses import dataclass
from typing import Any

from xplogger.experiment_manager.store.mongo import MongoStore


@dataclass
class SlurmInfo:
    priority: int
    job_id: str
    partition: str
    # job_name: str
    job_step_name: str
    user: str
    state: str
    start_time: str
    time: str
    time_limit: str
    num_nodes: int
    tres_per_node: str
    min_cpus: int
    min_memory_size: str
    nodelist: str
    mongo_id: str = ""
    collection: str = ""
    git_issue_id: str = ""
    script_id: str = ""

    @classmethod
    def from_dict(cls, data) -> SlurmInfo:
        slurm_key_to_kwarg_key_mapping = {
            "PRIORITY": "priority",
            "JOBID": "job_id",
            "PARTITION": "partition",
            "NAME": "job_step_name",
            "USER": "user",
            "STATE": "state",
            "START_TIME": "start_time",
            "TIME": "time",
            "TIME_LIMIT": "time_limit",
            "NODES": "num_nodes",
            "TRES_PER_NOD": "tres_per_node",
            "MI": "min_cpus",
            "MIN_": "min_memory_size",
            "NODELIST(REASON)": "nodelist",
        }
        kwargs_for_slurm_info = {
            kwargs_key: data[slurm_key]
            for slurm_key, kwargs_key in slurm_key_to_kwarg_key_mapping.items()
        }
        for key in ["priority", "num_nodes", "min_cpus"]:
            kwargs_for_slurm_info[key] = int(kwargs_for_slurm_info[key])
        return cls(**kwargs_for_slurm_info)


class SlurmInfoList(UserList):
    def __init__(self, slurm_info_list: list[SlurmInfo]):
        """list-like interface to a collection of SlurmInfo."""
        super().__init__(slurm_info_list)

    def to_slurminfo_dict(
        self, key_fn=lambda slurm_info: slurm_info.job_id
    ) -> SlurmInfoDict:
        return SlurmInfoDict(
            {key_fn(slurm_info): slurm_info for slurm_info in self.data}
        )

    def populate_additional_fields(self, mongo_stores: list[MongoStore]):
        records = []
        for current_mongo_store in mongo_stores:
            records += current_mongo_store.get_unanalyzed_records()
        records = {record["setup"]["slurm"]["id"]: record for record in records}

        def _process_slurm_info(slurm_info: SlurmInfo) -> SlurmInfo:
            job_id = slurm_info.job_id
            if job_id in records:
                key = job_id
            else:
                key = job_id + "-0"
            if key in records:
                slurm_info.project = records[key]["logbook"]["mongo_config"][
                    "collection"
                ]
                slurm_info.mongo_id = str(records[key]["_id"])
                slurm_info.git_issue_id = (
                    f"{slurm_info.project}-{records[key]['setup']['git']['issue_id']}"
                )
                slurm_info.script_id = (
                    f"{slurm_info.project}-{records[key]['setup']['script_id']}"
                )
            return slurm_info

        self.data = [_process_slurm_info(slurm_info) for slurm_info in self.data]


class SlurmInfoDict(UserDict):  # type: ignore
    def __init__(self, slurminfo_sequence_dict: dict[Any, SlurmInfoList]):
        """dict-like interface to a collection of SlurmInfo."""
        super().__init__(slurminfo_sequence_dict)
