from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, Request
from sqlalchemy import text

from app.domain.api_schema import ClinicalEventOut, MyHealthResponse
from app.domain.datetime_display import format_datetime_kr
from app.domain.display_labels import status_label_kr

router = APIRouter(tags=["PostgreSQL·본인건강"])

LookupBy = Literal["patient_no", "app_user_id", "email", "tel"]


def _resolve_patient_no(conn, by: LookupBy, value: str) -> int | None:
    v = value.strip()
    if not v:
        return None
    if by == "patient_no":
        try:
            pid = int(v, 10)
        except ValueError:
            return None
        row = conn.execute(
            text('SELECT patient_no FROM "Patient" WHERE patient_no = :p'),
            {"p": pid},
        ).first()
        return int(row[0]) if row else None
    if by == "app_user_id":
        row = conn.execute(
            text("SELECT patient_no FROM user_app_profile WHERE app_user_id = :v"),
            {"v": v},
        ).first()
        return int(row[0]) if row else None
    if by == "email":
        row = conn.execute(
            text('SELECT patient_no FROM "Patient" WHERE patient_email = :v'),
            {"v": v},
        ).first()
        return int(row[0]) if row else None
    if by == "tel":
        row = conn.execute(
            text('SELECT patient_no FROM "Patient" WHERE patient_tel = :v'),
            {"v": v},
        ).first()
        return int(row[0]) if row else None
    return None


@router.get(
    "/pg/my-health",
    response_model=MyHealthResponse,
    summary="PostgreSQL 본인 건강·진료 요약",
    description=(
        "앱에서 입력한 본인 식별값으로 patient_no 를 찾은 뒤, "
        "진료 타임라인(유형별)·프로필·생체·당일 웰니스를 반환합니다. "
        "식별: patient_no | app_user_id | email | tel"
    ),
)
def pg_my_health(
    request: Request,
    by: Annotated[
        LookupBy,
        Query(
            description="식별 방식",
            examples=["app_user_id"],
        ),
    ],
    value: Annotated[
        str,
        Query(
            description="식별 값 (예: 앱 ID 1234, 이메일, 전화번호, 환자번호)",
            examples=["1234"],
        ),
    ],
) -> MyHealthResponse:
    engine = getattr(request.app.state, "postgres_engine", None)
    if engine is None:
        raise HTTPException(
            status_code=503,
            detail="PostgreSQL 연결이 없습니다. 서버 설정과 DB 기동을 확인하세요.",
        )

    with engine.connect() as conn:
        patient_no = _resolve_patient_no(conn, by, value)
        if patient_no is None:
            raise HTTPException(status_code=404, detail="해당 식별 정보로 등록된 환자를 찾을 수 없습니다.")

        prow = conn.execute(
            text(
                'SELECT patient_no, patient_name, patient_gender, patient_birth, patient_email, patient_tel '
                'FROM "Patient" WHERE patient_no = :p'
            ),
            {"p": patient_no},
        ).mappings().first()
        if not prow:
            raise HTTPException(status_code=404, detail="환자 마스터를 찾을 수 없습니다.")

        profile_row = conn.execute(
            text(
                "SELECT patient_no, app_user_id, blood_type, height_cm, weight_kg, intt_cd "
                "FROM user_app_profile WHERE patient_no = :p"
            ),
            {"p": patient_no},
        ).mappings().first()
        profile = dict(profile_row) if profile_row else None
        if profile and profile.get("height_cm") is not None:
            profile["height_cm"] = float(profile["height_cm"])
        if profile and profile.get("weight_kg") is not None:
            profile["weight_kg"] = float(profile["weight_kg"])

        dis_row = conn.execute(
            text(
                "SELECT disability_grade, disability_type, assistive_device_YN, disability_device_type "
                "FROM disability WHERE patient_no = :p"
            ),
            {"p": patient_no},
        ).mappings().first()
        disability = dict(dis_row) if dis_row else None

        events = conn.execute(
            text(
                "SELECT clinical_event_id, category, occurred_on, department, title, summary, status, institution_name "
                "FROM patient_clinical_event WHERE patient_no = :p "
                "ORDER BY occurred_on DESC, clinical_event_id DESC"
            ),
            {"p": patient_no},
        ).mappings().all()

        by_cat: dict[str, list[ClinicalEventOut]] = defaultdict(list)
        for er in events:
            d = dict(er)
            occurred = d["occurred_on"]
            occurred_s = (
                format_datetime_kr(occurred)
                if occurred is not None
                else ""
            ) or ""
            item = ClinicalEventOut(
                clinical_event_id=int(d["clinical_event_id"]),
                category=str(d["category"]),
                occurred_on=occurred_s,
                department=d.get("department"),
                title=str(d["title"]),
                summary=d.get("summary"),
                status=status_label_kr(d.get("status")),
                institution_name=d.get("institution_name"),
            )
            by_cat[str(d["category"])].append(item)

        vital_row = conn.execute(
            text(
                "SELECT vital_id, measured_at, heart_rate_bpm, blood_pressure_systolic, "
                "blood_pressure_diastolic, body_temp_c, stress_score, source_channel "
                "FROM user_vital_measurement WHERE patient_no = :p "
                "ORDER BY measured_at DESC LIMIT 1"
            ),
            {"p": patient_no},
        ).mappings().first()

        latest_vitals: dict[str, object] | None = None
        if vital_row:
            vr = dict(vital_row)
            mt = vr.get("measured_at")
            if mt is not None:
                vr["measured_at"] = format_datetime_kr(mt) or ""
            if vr.get("body_temp_c") is not None:
                vr["body_temp_c"] = float(vr["body_temp_c"])
            if vr.get("stress_score") is not None:
                vr["stress_score"] = float(vr["stress_score"])
            latest_vitals = vr

        today = date.today()
        daily_row = conn.execute(
            text(
                "SELECT summary_date, step_count, step_goal, sleep_hours, stress_level "
                "FROM user_daily_wellness WHERE patient_no = :p AND summary_date = :d"
            ),
            {"p": patient_no, "d": today},
        ).mappings().first()
        daily_wellness_today: dict[str, object] | None = None
        if daily_row:
            dr = dict(daily_row)
            sd = dr.get("summary_date")
            if sd is not None:
                dr["summary_date"] = format_datetime_kr(sd) or ""
            if dr.get("sleep_hours") is not None:
                dr["sleep_hours"] = float(dr["sleep_hours"])
            if dr.get("stress_level") is not None:
                dr["stress_level"] = float(dr["stress_level"])
            daily_wellness_today = dr

        return MyHealthResponse(
            patient_no=int(prow["patient_no"]),
            patient_name=str(prow["patient_name"]) if prow.get("patient_name") else None,
            resolved_by=by,
            profile=profile,
            disability=disability,
            clinical_events_by_category=dict(by_cat),
            latest_vitals=latest_vitals,
            daily_wellness_today=daily_wellness_today,
        )
