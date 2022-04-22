"""Mongo Record class."""
from __future__ import annotations

import ray

from xplogger.experiment_manager.record import base
from xplogger.types import ConfigType


class Record(base.Record):
    """Wrappper over mongodb records."""

    @property
    def id(self) -> str:
        """Get record id."""
        key = "_id"
        if key not in self.data:
            key = "id"
        return str(self.data[key])


def make_record(config: ConfigType) -> Record:
    """Make a mongo record."""
    return Record(record=config)


@ray.remote  # type: ignore
# Ignoring error: Untyped decorator makes function "ray_make_record" untyped
def ray_make_record(config: ConfigType) -> Record:
    """Make a mongo record."""
    return make_record(config)
