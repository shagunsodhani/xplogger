"""OC Record."""
from __future__ import annotations

from copy import deepcopy

import ray
from omegaconf import OmegaConf
from omegaconf.dictconfig import DictConfig

from xplogger.experiment_manager.record import mongo


def make_record(mongo_record: mongo.Record) -> DictConfig:
    """Make record."""
    data = deepcopy(mongo_record.data)
    data["id"] = str(data.pop("_id"))
    record = OmegaConf.create(data)
    OmegaConf.set_struct(record, True)
    OmegaConf.set_readonly(record, True)
    return record


@ray.remote  # type: ignore
def ray_make_record(mongo_record: mongo.Record) -> DictConfig:
    """Make record using ray."""
    return make_record(mongo_record)
