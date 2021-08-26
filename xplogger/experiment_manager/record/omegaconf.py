"""Record class"""
from __future__ import annotations

from copy import deepcopy

import ray
from omegaconf import OmegaConf

from xplogger.experiment_manager.record import mongo


def make_record(mongo_record: mongo.Record):
    data = deepcopy(mongo_record.data)
    data["id"] = str(data.pop("_id"))
    data = OmegaConf.create(data)
    OmegaConf.set_struct(data, True)
    OmegaConf.set_readonly(data, True)
    return data


@ray.remote
def ray_make_record(mongo_record: mongo.Record):
    return make_record(mongo_record)
