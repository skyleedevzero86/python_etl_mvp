from app.domain.enums import PipelineJob
from app.domain.ports import PipelineRepositoryPort


class PipelineApplicationService:
    def __init__(self, repository: PipelineRepositoryPort) -> None:
        self._repository = repository

    def execute(self, job: PipelineJob) -> dict:
        return self._repository.run_job(job)
