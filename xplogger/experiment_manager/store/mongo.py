"""Class to interface with the mongodb store."""
from __future__ import annotations

from pathlib import Path

import ray
from bson.objectid import ObjectId
from pymongo import MongoClient

from xplogger.experiment_manager.record import mongo as mongo_record_utils
from xplogger.experiment_manager.record.record_list import RecordList
from xplogger.experiment_manager.utils.enum import ExperimentStatus
from xplogger.parser.utils import parse_json
from xplogger.types import ConfigType
from xplogger.utils import serialize_log_to_json

# Module "pymongo" does not explicitly export attribute "MongoClient"; implicit reexport disabled


class MongoStore:
    def __init__(
        self,
        config: ConfigType,
    ):
        """Class to interface with the mongodb store.

        Args:
            config (ConfigType): Config to connect with the mongo store.
        """
        self._client: MongoClient = MongoClient(  # type: ignore
            host=config["host"], port=config["port"]
        )
        db = config["db"]
        collection_name = config["collection_name"]
        self.collection = self._client[db][collection_name]

    def ray_get_records(self) -> RecordList:
        """Get records from the db using ray."""
        futures = [
            mongo_record_utils.ray_make_record.remote(record)
            for record in self.collection.find()
        ]
        records = ray.get(futures)
        assert isinstance(records, list)
        return RecordList(records=records)

    def get_records(self, query) -> RecordList:  # type: ignore
        """Get records from the db."""
        return RecordList(
            records=[
                mongo_record_utils.make_record(record)
                for record in self.collection.find(query)
            ]
        )

    def delete_records(
        self, record_list: RecordList, delete_from_filesystem: bool = False
    ) -> None:
        """Delete records from the db and filesystem (optional).

        Args:
            record_list (RecordList):
            delete_from_filesystem (bool, optional): should delete records
                from the filesystem. Defaults to False.
        """
        record_list.delete(
            collection=self.collection, delete_from_filesystem=delete_from_filesystem
        )

    def update_status(self, record_list: RecordList, new_status: str) -> None:
        """Mark records as analyzed in the db.

        Args:
            record_list (RecordList):
        """
        return record_list.update_status(
            collection=self.collection, new_status=new_status
        )

    def mark_records_as_analyzed(self, record_list: RecordList) -> None:
        """Mark records as analyzed in the db.

        Args:
            record_list (RecordList):
        """
        return self.update_status(
            record_list=record_list, new_status=ExperimentStatus.ANALYZED.value
        )

    def ignore_records_by_status(self, status: str) -> RecordList:
        """Get a list of records which do not match the status."""
        query = {"status": {"$ne": status}}
        return RecordList(records=list(self.get_records(query=query)))

    def ray_ignore_records_by_status(self, status: str) -> RecordList:
        """Get a list of records which do not match the status using ray."""
        query = {"status": {"$ne": status}}
        futures = [
            mongo_record_utils.ray_make_record.remote(record)
            for record in self.get_records(query=query)
        ]
        records = ray.get(futures)
        assert isinstance(records, list)
        return RecordList(records=records)

    def get_unanalyzed_records(self) -> RecordList:
        """Get a list of un-analyzed records."""
        return self.ignore_records_by_status(status=ExperimentStatus.ANALYZED.value)

    def ray_get_unanalyzed_records(self) -> RecordList:
        """Get unalalyzed records using ray."""
        return self.ray_ignore_records_by_status(status=ExperimentStatus.ANALYZED.value)

    def save_to_file(self, filepath: Path) -> None:
        """Save mongo records to a file."""
        with open(filepath, "a") as f:
            for record in self.collection.find():
                record["_id"] = str(record["_id"])
                record["mongo_id"] = record["_id"]
                f.write(serialize_log_to_json(record))
                f.write("\n")

    def load_from_file(self, filepath: Path) -> None:
        """Load records from a file to Mongo DB."""
        with open(filepath) as f:
            for record in f:
                record_dict = parse_json(record)
                assert record_dict is not None
                record_dict["_id"] = ObjectId(record_dict["_id"])
                self.collection.insert_one(record_dict)

    def replace_from_file(self, filepath: Path, upsert: bool = False) -> None:
        """Replace records from a file to Mongo DB."""
        with open(filepath) as f:
            for record in f:
                record_dict = parse_json(record)
                assert record_dict is not None
                self.collection.replace_one(
                    {"_id": ObjectId(record_dict.pop("_id"))},
                    record_dict,
                    upsert=upsert,
                )
