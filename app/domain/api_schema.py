from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str


class PipelineRunResponse(BaseModel):
    job: str
    suffix: str | None = None
    patients_inserted_from: int | None = None
    check_ins: dict[str, int] | None = None
    treatments: dict[str, int] | None = None
    prescription_ids: list[int] | None = None
    extra: dict[str, Any] = Field(default_factory=dict)
