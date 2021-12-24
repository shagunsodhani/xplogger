from __future__ import annotations

import ray
from pymongo import MongoClient

from xplogger.experiment_manager.record import mongo as mongo_record_utils
from xplogger.experiment_manager.record.record_list import RecordList
from xplogger.types import ConfigType


class MongoStore:
    def __init__(
        self,
        config: ConfigType,
    ):
        """Class to interface with the mongodb store
        Args:
            config (ConfigType): Config to connect with the mongo store.
        """
        self._client = MongoClient(host=config["host"], port=config["port"])
        db = config["db"]
        collection_name = config["collection_name"]
        self.collection = self._client[db][collection_name]

    def ray_get_records(self) -> RecordList:
        futures = [
            mongo_record_utils.ray_make_record.remote(record)
            for record in self.collection.find()
        ]
        records = ray.get(futures)
        assert isinstance(records, list)
        return RecordList(records=records)

    def get_records(self, query) -> RecordList:  # type: ignore
        # error: Function is missing a type annotation for one or more arguments
        return RecordList(
            records=[
                mongo_record_utils.make_record(record)
                for record in self.collection.find(query)
            ]
        )

    def delete_records(
        self, record_list: RecordList, delete_from_filesystem: bool = False
    ) -> None:
        record_list.delete(
            collection=self.collection, delete_from_filesystem=delete_from_filesystem
        )

    def mark_records_as_analyzed(self, record_list: RecordList) -> None:
        record_list.mark_analyzed(collection=self.collection)

    def get_unanalyzed_records(self) -> RecordList:
        query = {"status": {"$ne": "ANALYZED"}}
        return RecordList(
            records=[
                record
                for record in self.get_records(query=query)
                # if record.config["status"] != ""
            ]
        )

    def ray_get_unanalyzed_records(self) -> RecordList:
        query = {"status": {"$ne": "ANALYZED"}}
        futures = [
            mongo_record_utils.ray_make_record.remote(record)
            for record in self.get_records(query=query)
        ]
        records = ray.get(futures)
        assert isinstance(records, list)
        return RecordList(records=records)
