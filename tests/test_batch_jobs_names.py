from app.domain.enums import PipelineJob
from app.infrastructure.batch_jobs import pipeline_job_name


def test_pipeline_job_name_initial():
    assert pipeline_job_name(PipelineJob.INITIAL) == "pipeline.initial"


def test_pipeline_job_name_completion():
    assert pipeline_job_name(PipelineJob.COMPLETION) == "pipeline.completion"
