"""Enum data-structures."""
from enum import Enum


class ExperimentStatus(Enum):
    ANALYZED = "ANALYZED"
    COMPLETED = "COMPLETED"
    RUNNING = "RUNNING"
