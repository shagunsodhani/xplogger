"""Functions to interface with TinyDB."""


from tinydb import TinyDB
from tinyrecord import transaction

from xplogger.logger.base import Logger as BaseLogger
from xplogger.types import ConfigType, LogType


class Logger(BaseLogger):
    """Logger class that writes to TinyDB."""

    def __init__(self, config: ConfigType):
        """Initialise the TinyDB Logger.

        Args:
            config (ConfigType): config to initialise the TinyDB logger.
                It must have one key: `path`. It can optionally have the
                following keys:
                * `logger_types` - list/set of types that the logger
                    should log.
        """
        super().__init__(config=config)
        keys_to_check = [
            "path",
        ]
        if not all(key in config for key in keys_to_check):
            key_string = ", ".join(keys_to_check)
            raise KeyError(
                f"One or more of the following keys missing in the config: {key_string}"
            )
        self.path = config["path"]
        self.logger_types = {"config", "metadata"}
        if "logger_types" in config:
            self.logger_types = set(config["logger_types"])

    def write(self, log: LogType) -> None:
        """Write the log to TinyDB.

        Args:
            log (LogType): Log to write
        """
        if log["logbook_type"] in self.logger_types:
            table = TinyDB("db.json").table("table")
            with transaction(table) as tr:
                tr.insert(log)
