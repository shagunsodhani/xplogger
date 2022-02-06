"""Functions to interface with local db (a file)."""


from filelock import FileLock

from xplogger.logger.base import Logger as BaseLogger
from xplogger.types import ConfigType, LogType
from xplogger.utils import serialize_log_to_json


class Logger(BaseLogger):
    """Logger class that writes to local db (a file)."""

    def __init__(self, config: ConfigType):
        """Initialise the local db Logger.

        Args:
            config (ConfigType): config to initialise the local db logger.
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
        self.lock = FileLock(f"{self.path}.lock")

    def write(self, log: LogType) -> None:
        """Write the log to local db.

        Args:
            log (LogType): Log to write
        """
        if log["logbook_type"] in self.logger_types:
            with self.lock:
                with open(self.path, "a") as f:
                    f.write(serialize_log_to_json(log=log) + "\n")
