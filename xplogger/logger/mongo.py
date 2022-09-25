"""Functions to interface with mongodb."""


import warnings
from copy import deepcopy

from pymongo import MongoClient
from pymongo.errors import PyMongoError

# Module "pymongo" does not explicitly export attribute "MongoClient"; implicit reexport disabled
from xplogger.logger.base import Logger as BaseLogger
from xplogger.types import ConfigType, LogType

# error: Module "pymongo" does not explicitly export attribute "MongoClient"; implicit reexport disabled


class Logger(BaseLogger):
    """Logger class that writes to the mongodb."""

    def __init__(self, config: ConfigType):
        """Initialise the Mongodb Logger.

        Args:
            config (ConfigType): config to initialise the mongodb logger.
                It must have four keys: host, port, db and collection. It
                can optionally have the following keys:
                * `logger_types` - list/set of types that the logger
                    should log.
        """
        super().__init__(config=config)
        keys_to_check = [
            "host",
            "port",
            "db",
            "collection",
        ]
        if not all(key in config for key in keys_to_check):
            key_string = ", ".join(keys_to_check)
            raise KeyError(
                f"One or more of the following keys missing in the config: {key_string}"
            )
        self.logger_types = {"config", "message", "metadata"}
        if "logger_types" in config:
            self.logger_types = set(config["logger_types"])
        self.client: MongoClient = MongoClient(config["host"], config["port"])  # type: ignore
        self.collection = self.client[config["db"]][config["collection"]]

    def is_connection_working(self) -> bool:
        """Check if the connection to the mongo server is working.

        Checks the connection by issuing a dummy read query.
        """
        try:
            self.collection.find_one({})
            return True
        except PyMongoError as error:
            warnings.warn(
                f"Could not connect to the MongoServer. \nError: {error}. \nDisabling Mongo Logger."
            )
            return False

    def write(self, log: LogType) -> None:
        """Write the log to mongodb.

        Args:
            log (LogType): Log to write
        """
        if log["logbook_type"] in self.logger_types:
            self.collection.insert_one(deepcopy(log))
