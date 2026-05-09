from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(description="서비스 상태 값", examples=["ok"])


class PipelineRunResponse(BaseModel):
    job: str = Field(description="실행된 작업 타입", examples=["initial", "completion"])
    suffix: str | None = Field(default=None, description="실행 시각 기반 식별 접미사")
    patients_inserted_from: int | None = Field(default=None, description="초기 배치 환자 시작 번호")
    check_ins: dict[str, int] | None = Field(default=None, description="접수 생성 결과")
    treatments: dict[str, int] | None = Field(default=None, description="진료 생성 결과")
    prescription_ids: list[int] | None = Field(default=None, description="처방 ID 목록")
    extra: dict[str, Any] = Field(default_factory=dict, description="작업별 추가 반환 데이터")
