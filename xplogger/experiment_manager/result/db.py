"""Class to manage a collection of results."""
from collections import UserDict
from pathlib import Path
from typing import Dict

from xplogger.experiment_manager.result.result import Result, deserialize


class ResultDB(UserDict):  # type: ignore
    # error: Missing type parameters for generic type "UserDict"
    def __init__(self, path: Path, results: Dict[str, Result]):
        """List-like interface to a collection of Experiments."""
        super().__init__(results)
        self.path = path
        self.load_from_filesystem()

    def load_from_filesystem(self) -> None:
        """Load results from the filesystem."""
        for result_path in self.path.iterdir():
            result = deserialize(dir_path=result_path)
            self.data[result.name] = result

    def save_to_filesystem(self) -> None:
        """Save results to the filesystem."""
        for name in self.data:
            dir_path = self.path.joinpath(name)
            self.data[name].serialize(dir_path=dir_path)
