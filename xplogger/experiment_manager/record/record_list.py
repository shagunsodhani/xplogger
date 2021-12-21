"""Record class"""
from __future__ import annotations

import collections
import shutil
from collections import OrderedDict, UserList
from typing import Any, Callable

import pymongo
import ray
from bson.objectid import ObjectId
from omegaconf import DictConfig, OmegaConf

from xplogger.experiment_manager.record import base as base_record
from xplogger.experiment_manager.record import omegaconf as oc_utils
from xplogger.parser.experiment.experiment import (
    Experiment,
    ExperimentSequence,
    ExperimentSequenceDict,
)
from xplogger.types import ValueType

LoadExperientFromDirType = Callable[[str], Experiment]


class RecordList(UserList):
    def __init__(self, records: "list[base_record.Record]"):
        """Dict-like interface to a collection of results."""
        super().__init__(records)

    def mark_analyzed(self, collection: pymongo.collection.Collection):
        if isinstance(self.data[0], DictConfig):

            def process_record(record):
                return OmegaConf.to_container(record)

        else:

            def process_record(record):
                return record

        for record in self.data:
            record = process_record(record)
            issue_id = record["setup"]["git"]["issue_id"]
            print(issue_id)
            record["status"] = "ANALYZED"
            _id = ObjectId(record.pop("id"))
            print(collection.replace_one({"_id": _id}, record).raw_result)

    def delete(
        self,
        collection: pymongo.collection.Collection,
        delete_from_filesystem: bool = False,
    ):
        counter = 0
        for record in self.data:
            counter += 1
            collection.delete_many({"setup.id": record["setup"]["id"]})
            if delete_from_filesystem:
                try:
                    file_path = record["logbook"]["logger_dir"]
                    shutil.rmtree(file_path)
                except Exception as e:
                    print(f"Failed to delete {file_path}. Reason: {e}")
        print(counter)

    def get_unique_issues(self) -> collections.Counter[str, int]:
        return collections.Counter(
            str(record["setup"]["git"]["issue_id"]) for record in self.data
        )

    def get_viz_params(self) -> set[str]:
        viz_params = set()
        for record in self.data:
            if record["setup"]["viz"]["params"]:
                for param in record["setup"]["viz"]["params"]:
                    viz_params.add(param)
        return viz_params

    def make_oc_records(self) -> RecordList[DictConfig]:
        return RecordList(
            oc_utils.make_record(mongo_record=record) for record in self.data
        )

    def ray_make_oc_records(self) -> RecordList[DictConfig]:
        futures = [
            oc_utils.ray_make_record.remote(mongo_record=record) for record in self.data
        ]
        records = ray.get(futures)
        return RecordList(records=records)

    def map_to_slurm_id(self) -> dict[str, RecordList]:
        def _make_empty_record_list():
            return RecordList([])

        mapping: dict[str, RecordList] = collections.defaultdict(
            _make_empty_record_list
        )
        for record in self.data:
            key = str(record["setup"]["slurm_id"].replace("_", "-"))
            mapping[key].append(record)
        return mapping

    # todo: rename this
    def get_groups_and_hyperparams(
        self, viz_params: list[str]
    ) -> tuple[dict[Any, RecordList], dict[str, set[ValueType]]]:
        """Group experiments."""
        groups: dict[Any, RecordList] = {}
        hyperparams: dict[str, set[Any]] = {}
        id_set = set()
        for record in self.data:
            params = base_record.get_experiment_params(record, viz_params)
            for key, value in params.items():
                if key not in hyperparams:
                    hyperparams[key] = set()
                hyperparams[key].add(value)
            key = OmegaConf.create(params)
            if key not in groups:
                groups[key] = RecordList([])
            _id = record.id
            if _id not in id_set:
                groups[key].append(record)
                id_set.add(_id)

        return groups, hyperparams

    def load_experiments(
        self,
        load_experiment_from_dir: LoadExperientFromDirType,
    ) -> ExperimentSequence:
        """Load experiments."""
        experiments = [
            base_record.load_experiment(
                record=record,
                load_experiment_from_dir=load_experiment_from_dir,
            )
            for record in self.data
        ]
        exp_seq = ExperimentSequence([exp for exp in experiments if exp is not None])
        return exp_seq

    def make_experiment_sequence_dict_groups_and_hyperparams(
        self,
        viz_params: list[str],
        load_experiment_from_dir: LoadExperientFromDirType,
    ) -> tuple[
        ExperimentSequenceDict, dict[Any, RecordList], dict[str, set[ValueType]]
    ]:
        """Make experiment groups."""
        groups, hyperparams = self.get_groups_and_hyperparams(viz_params=viz_params)
        experiment_sequence_dict = ExperimentSequenceDict(
            {
                key: record_list.load_experiments(
                    load_experiment_from_dir=load_experiment_from_dir
                )
                for key, record_list in groups.items()
            }
        )
        return experiment_sequence_dict, groups, hyperparams

    def ray_make_experiment_sequence_dict_groups_and_hyperparams(
        self,
        viz_params: list[str],
        load_experiment_from_dir: LoadExperientFromDirType,
    ) -> tuple[
        ExperimentSequenceDict, dict[Any, RecordList], dict[str, set[ValueType]]
    ]:
        """Make experiment groups."""
        groups, hyperparams = self.get_groups_and_hyperparams(viz_params=viz_params)

        groups = OrderedDict(groups)

        experiment_sequence_dict = ExperimentSequenceDict(
            {
                key: ray_load_experiments.remote(
                    record_list=record_list,
                    load_experiment_from_dir=load_experiment_from_dir,
                )
                for key, record_list in groups.items()
            }
        )
        for key in experiment_sequence_dict:
            experiment_sequence_dict[key] = ExperimentSequence(
                ray.get(experiment_sequence_dict[key])
            )
        return experiment_sequence_dict, groups, hyperparams

    def get_unique(self, key_func) -> RecordList:
        seen_keys = set()
        unique_records = []
        for record in self.data:
            key = key_func(record)
            if key not in seen_keys:
                seen_keys.add(key)
                unique_records.append(record)
        return RecordList(unique_records)


@ray.remote
def ray_load_experiments(
    record_list: RecordList,
    load_experiment_from_dir: LoadExperientFromDirType,
) -> Any:
    """Load experiments."""
    futures = [
        base_record.ray_load_experiment.remote(
            record=record,
            load_experiment_from_dir=load_experiment_from_dir,
        )
        for record in record_list.data
    ]

    return ray.get(futures)
