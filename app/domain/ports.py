from typing import Protocol

from app.domain.enums import PipelineJob


class PipelineRepositoryPort(Protocol):
    def run_job(self, job: PipelineJob) -> dict:
        ...
