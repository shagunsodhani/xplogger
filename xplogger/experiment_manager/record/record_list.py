"""Record class."""
from __future__ import annotations

import collections
import shutil
from collections import OrderedDict, UserList
from subprocess import CalledProcessError  # noqa: S404
from typing import Any, Callable

import pymongo
import ray
from bson.objectid import ObjectId
from omegaconf import DictConfig, OmegaConf

from xplogger.experiment_manager.record import base as base_record
from xplogger.experiment_manager.record import omegaconf as oc_utils
from xplogger.experiment_manager.record.mongo import Record as MongoRecord
from xplogger.experiment_manager.slurm.utils import map_jobid_to_raw_job_id
from xplogger.parser.experiment.experiment import (
    Experiment,
    ExperimentSequence,
    ExperimentSequenceDict,
)
from xplogger.types import ValueType

LoadExperientFromDirType = Callable[[str], Experiment]


class RecordList(UserList):  # type: ignore
    def __init__(self, records: list[base_record.Record]):
        """Dict-like interface to a collection of results."""
        super().__init__(records)

    def update_status(
        self,
        collection: pymongo.collection.Collection,  # type: ignore
        new_status: str,
    ) -> None:
        """Update the status of the records(in the db).

        Args:
            collection (pymongo.collection.Collection):

        """
        if isinstance(self.data[0], DictConfig):

            def process_record(record: base_record.Record) -> dict:  # type: ignore
                # error: Returning Any from function declared to return "Dict[Any, Any]"
                data = OmegaConf.to_container(record)
                assert isinstance(data, dict)
                return data

        else:

            def process_record(record: base_record.Record) -> base_record.Record:  # type: ignore
                # error: All conditional function variants must have identical signatures
                return record

        for data_record in self.data:
            record = process_record(data_record)
            issue_id = record["setup"]["git"]["issue_id"]
            print(issue_id)
            record["status"] = new_status
            key = "_id"
            if key in record:
                _id = ObjectId(record.pop("_id"))
            else:
                key = "id"
                _id = ObjectId(record.pop(key))
            print(collection.replace_one({"_id": _id}, record).raw_result)

    def mark_analyzed(self, collection: pymongo.collection.Collection) -> None:  # type: ignore
        # error: Missing type parameters for generic type "Collection"
        """Mark records as analyzed (in the db).

        Args:
            collection (pymongo.collection.Collection):

        """
        return self.update_status(collection=collection, new_status="ANALYZED")

    def add_slurm_field(self, collection: pymongo.collection.Collection) -> None:  # type: ignore
        """Add slurm field to records (in the db).

        Args:
            collection (pymongo.collection.Collection):

        """
        if isinstance(self.data[0], DictConfig):

            def process_record(record: base_record.Record) -> dict:  # type: ignore
                # error: Returning Any from function declared to return "Dict[Any, Any]"
                data = OmegaConf.to_container(record)
                assert isinstance(data, dict)
                return data

        else:

            def process_record(record: base_record.Record) -> base_record.Record:  # type: ignore
                # error: All conditional function variants must have identical signatures
                return record

        for data_record in self.data:
            record = process_record(data_record)
            if "slurm" not in record["setup"]:
                try:
                    record["setup"]["slurm"] = {
                        "id": map_jobid_to_raw_job_id(record["setup"]["slurm_id"])
                    }
                except CalledProcessError:
                    # record["setup"]["slurm"] = {"id": -1}
                    print(record["setup"]["slurm_id"])
                    continue
                print(record["setup"]["slurm"]["id"])
                _id = ObjectId(record.pop("_id"))
                print(collection.replace_one({"_id": _id}, record).raw_result)

    def delete(
        self,
        collection: pymongo.collection.Collection,  # type: ignore
        # error: Missing type parameters for generic type "Collection"
        delete_from_filesystem: bool = False,
    ) -> None:
        """Delete jobs from the db and filesystem (optionally).

        Args:
            collection (pymongo.collection.Collection):
            delete_from_filesystem (bool, optional): Should delete the job
                from the filesystem. Defaults to False.
        """
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

    def get_unique_issues(self) -> collections.Counter[str]:
        """Get unique issues from the record list."""
        return collections.Counter(
            str(record["setup"]["git"]["issue_id"]) for record in self.data
        )

    def get_viz_params(self) -> set[str]:
        """Get params for vizualization."""
        viz_params = set()
        for record in self.data:
            if record["setup"]["viz"]["params"]:
                for param in record["setup"]["viz"]["params"]:
                    viz_params.add(param)
        return viz_params

    def make_oc_records(self) -> RecordList:
        """Make OC records."""
        record_list = []
        for record in self.data:
            assert isinstance(record, MongoRecord)
            record_list.append(oc_utils.make_record(mongo_record=record))

        return RecordList(record_list)

    def ray_make_oc_records(self) -> RecordList:
        """Make OC records using ray."""
        futures = [
            oc_utils.ray_make_record.remote(mongo_record=record) for record in self.data
        ]
        records = ray.get(futures)
        return RecordList(records=records)

    def map_to_slurm_id(self) -> dict[str, RecordList]:
        """Map the record list to a list of slurm ids.

        Returns:
            dict[str, RecordList]: dictionary where the key is the slurm id
                and value is the list of records. We return a list of records
                as sometimes the records are duplicated.
        """

        def _make_empty_record_list() -> RecordList:
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
            for param_name, value in params.items():
                if param_name not in hyperparams:
                    hyperparams[param_name] = set()
                if isinstance(value, list):
                    hyperparams[param_name].add(tuple(value))
                else:
                    hyperparams[param_name].add(value)
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

    def get_unique(self, key_func: Callable[[base_record.Record], str]) -> RecordList:
        """Get unique records from the current record list.

        Args:
            key_func (Callable[[base_record.Record], str]): This function
                computes the key (or hash) unsed to identify a record.

        Returns:
            RecordList: List of unique records.
        """
        seen_keys = set()
        unique_records = []
        for record in self.data:
            key = key_func(record)
            if key not in seen_keys:
                seen_keys.add(key)
                unique_records.append(record)
        return RecordList(unique_records)


@ray.remote  # type: ignore
# Untyped decorator makes function "ray_load_experiments" untyped
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
