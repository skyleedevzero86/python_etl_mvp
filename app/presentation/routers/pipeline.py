from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Request

from app.application.pipeline_service import PipelineApplicationService
from app.domain.api_schema import PipelineRunResponse
from app.domain.enums import PipelineJob
from app.presentation.dependencies import get_pipeline_service

router = APIRouter(prefix="/pipeline", tags=["배치"])


@router.post(
    "/run/{job}",
    response_model=PipelineRunResponse,
    summary="파이프라인 수동 실행",
    description=(
        "지정한 파이프라인 작업을 즉시 실행합니다.\n\n"
        "- `initial`: 기초 데이터 적재\n"
        "- `completion`: 완료/취소 흐름 데이터 적재\n"
        "- `ENABLE_PIPELINE_WRITE=true`일 때만 실행됩니다."
    ),
    responses={
        403: {
            "description": "샘플 데이터 적재 비활성화 상태",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "수동 파이프라인 실행이 비활성화되었습니다. .env 의 ENABLE_PIPELINE_WRITE=true 로 켜세요."
                    }
                }
            },
        }
    },
)
def run_pipeline(
    job: Annotated[
        PipelineJob,
        Path(
            description="실행할 파이프라인 작업 종류",
            examples=["initial", "completion"],
        ),
    ],
    request: Request,
    service: Annotated[PipelineApplicationService, Depends(get_pipeline_service)],
) -> PipelineRunResponse:
    if not request.app.state.settings.enable_pipeline_write:
        raise HTTPException(
            status_code=403,
            detail="수동 파이프라인 실행이 비활성화되었습니다. .env 의 ENABLE_PIPELINE_WRITE=true 로 켜세요.",
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
