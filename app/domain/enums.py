from enum import Enum


class PipelineJob(str, Enum):
    INITIAL = "initial"
    COMPLETION = "completion"
