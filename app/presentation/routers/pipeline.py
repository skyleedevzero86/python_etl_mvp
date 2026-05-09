from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from app.application.pipeline_service import PipelineApplicationService
from app.domain.api_schema import PipelineRunResponse
from app.domain.enums import PipelineJob
from app.presentation.dependencies import get_pipeline_service

router = APIRouter(prefix="/pipeline", tags=["배치"])


@router.post(
    "/run/{job}",
    response_model=PipelineRunResponse,
    responses={
        403: {
            "description": "샘플 데이터 적재 비활성화 상태",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "샘플 데이터 적재가 비활성화되었습니다. .env 의 ENABLE_PIPELINE_WRITE=true 로 켜세요."
                    }
                }
            },
        }
    },
)
def run_pipeline(
    job: PipelineJob,
    request: Request,
    service: Annotated[PipelineApplicationService, Depends(get_pipeline_service)],
) -> PipelineRunResponse:
    if not request.app.state.settings.enable_pipeline_write:
        raise HTTPException(
            status_code=403,
            detail="샘플 데이터 적재가 비활성화되었습니다. .env 의 ENABLE_PIPELINE_WRITE=true 로 켜세요.",
        )
    payload = service.execute(job)
    known = {
        "job",
        "suffix",
        "patients_inserted_from",
        "check_ins",
        "treatments",
        "prescription_ids",
    }
    return PipelineRunResponse(
        job=str(payload.get("job", job.value)),
        suffix=payload.get("suffix"),
        patients_inserted_from=payload.get("patients_inserted_from"),
        check_ins=payload.get("check_ins"),
        treatments=payload.get("treatments"),
        prescription_ids=payload.get("prescription_ids"),
        extra={k: v for k, v in payload.items() if k not in known},
    )
