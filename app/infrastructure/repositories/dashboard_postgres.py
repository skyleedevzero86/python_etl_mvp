from __future__ import annotations

from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.domain.dashboard_schema import (
    PgCategoryCount,
    PgDashboardSnapshot,
    PgEtlState,
    PgTableCountRow,
    PgVitalsAggregate,
)
from app.domain.display_labels import clinical_category_label_kr, status_label_kr
from app.infrastructure.repositories.dashboard_mysql import _mask_text, _sanitize_row

_KST = ZoneInfo("Asia/Seoul")


def _format_kst_display(dt: Any) -> str | None:
    if dt is None:
        return None
    if isinstance(dt, datetime):
        d = dt
        if d.tzinfo is None:
            d = d.replace(tzinfo=_KST)
        else:
            d = d.astimezone(_KST)
        return f"{d.year}년 {d.month}월 {d.day}일 {d.hour:02d}:{d.minute:02d}"
    if isinstance(dt, date):
        return f"{dt.year}년 {dt.month}월 {dt.day}일"
    return str(dt)


def _mask_numeric_id(val: Any) -> str | None:
    if val is None:
        return None
    s = str(val).strip()
    if not s:
        return None
    return "***" + s[-2:] if len(s) >= 2 else "***"


def _mask_pg_dict(table: str, row: dict[str, Any]) -> dict[str, Any]:
    out = _sanitize_row(table, row)
    if "vital_id" in out and out["vital_id"] is not None:
        out["vital_id"] = _mask_numeric_id(out["vital_id"])
    if "clinical_event_id" in out and out["clinical_event_id"] is not None:
        out["clinical_event_id"] = _mask_numeric_id(out["clinical_event_id"])
    if "source_mysql_treatment_id" in out and out["source_mysql_treatment_id"] is not None:
        out["source_mysql_treatment_id"] = _mask_numeric_id(out["source_mysql_treatment_id"])
    t = out.get("title")
    if isinstance(t, str) and t:
        out["title"] = _mask_text(t)
    dep = out.get("department")
    if isinstance(dep, str) and dep:
        out["department"] = _mask_text(dep)
    return out


class PostgresDashboardRepository:
    _TABLES: tuple[tuple[str, str, str], ...] = (
        ('"Patient"', "Patient", "환자 마스터"),
        ("user_app_profile", "user_app_profile", "앱·웨어러블 프로필"),
        ("user_vital_measurement", "user_vital_measurement", "생체 측정 시계열"),
        ("user_daily_wellness", "user_daily_wellness", "일별 웰니스"),
        ("patient_clinical_event", "patient_clinical_event", "진료·검사 타임라인"),
        ("disability", "disability", "장애 정보"),
        ("health_checkup_institution", "health_checkup_institution", "건강검진 기관"),
        ("disability_care_institution", "disability_care_institution", "장애 돌봄 기관"),
        ("inpatient_statistics", "inpatient_statistics", "입원 통계"),
        ("treatment_department_statistics", "treatment_department_statistics", "진료과 통계"),
        ("etl_runtime_state", "etl_runtime_state", "ETL 런타임 상태"),
    )

    def __init__(self, engine: Engine | None) -> None:
        self._engine = engine

    def fetch_snapshot(self) -> PgDashboardSnapshot:
        now = datetime.now().replace(microsecond=0)
        if self._engine is None:
            return PgDashboardSnapshot(
                connected=False,
                message=(
                    "앱 기동 시 PostgreSQL 접속에 실패했습니다. 서버 프로세스·포트(POSTGRES_PORT)·"
                    "DB 생성·디비정리PostgreSql.sql 적용·POSTGRES_USER/PASSWORD 및 DATABASE_HOST 를 확인하고, "
                    "애플리케이션 로그의 「디비 접속 실패(PostgreSQL)」항목에 출력된 예외를 참고하세요."
                ),
                generated_at=_format_kst_display(now) or "",
                include_mysql_treatment_id_column=False,
                table_counts=[],
                etl=None,
                clinical_by_category=[],
                vitals_aggregate=PgVitalsAggregate(),
                recent_vitals=[],
                recent_clinical_events=[],
                daily_wellness_sample_rows=[],
            )

        with self._engine.connect() as conn:
            conn.execute(text("SELECT 1"))

            table_counts: list[PgTableCountRow] = []
            for sql_ident, key, label_kr in self._TABLES:
                try:
                    n = conn.execute(text(f"SELECT COUNT(*)::bigint AS c FROM {sql_ident}")).scalar()
                    cnt = int(n or 0)
                except Exception:
                    cnt = -1
                table_counts.append(
                    PgTableCountRow(table_key=key, label_kr=label_kr, sql_name=key, total_count=cnt)
                )

            etl: PgEtlState | None = None
            try:
                row = conn.execute(
                    text(
                        "SELECT cursor_value, updated_at FROM etl_runtime_state "
                        "WHERE job_code = 'wearable_round_robin'"
                    ),
                ).first()
                if row:
                    etl = PgEtlState(
                        wearable_round_robin_cursor=int(row[0]),
                        wearable_updated_at=_format_kst_display(row[1]),
                    )
                else:
                    etl = PgEtlState(wearable_round_robin_cursor=None, wearable_updated_at=None)
            except Exception:
                etl = None

            clinical_by_category: list[PgCategoryCount] = []
            try:
                crows = conn.execute(
                    text(
                        """
                        SELECT category, COUNT(*)::bigint AS c
                        FROM patient_clinical_event
                        GROUP BY category
                        ORDER BY c DESC
                        """
                    ),
                ).fetchall()
                clinical_by_category = [
                    PgCategoryCount(
                        category=str(r[0]),
                        label_kr=clinical_category_label_kr(str(r[0])),
                        count=int(r[1]),
                    )
                    for r in crows
                ]
            except Exception:
                pass

            vitals_agg = PgVitalsAggregate()
            try:
                total_v = conn.execute(
                    text("SELECT COUNT(*)::bigint FROM user_vital_measurement"),
                ).scalar()
                vitals_agg.total_vitals = int(total_v or 0)

                today = date.today()
                tv = conn.execute(
                    text(
                        """
                        SELECT COUNT(*)::bigint FROM user_vital_measurement
                        WHERE measured_at::date = :td
                        """
                    ),
                    {"td": today},
                ).scalar()
                vitals_agg.today_vitals = int(tv or 0)

                pend = conn.execute(
                    text(
                        """
                        SELECT COUNT(*)::bigint FROM user_vital_measurement
                        WHERE synced_to_mysql_at IS NULL
                        """
                    ),
                ).scalar()
                vitals_agg.pending_mysql_sync = int(pend or 0)

                avg_row = conn.execute(
                    text(
                        """
                        SELECT AVG(heart_rate_bpm)::float
                        FROM user_vital_measurement
                        WHERE measured_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
                          AND heart_rate_bpm IS NOT NULL
                        """
                    ),
                ).scalar()
                if avg_row is not None:
                    vitals_agg.avg_heart_rate_24h = round(float(avg_row), 1)
            except Exception:
                pass

            recent_vitals: list[dict[str, Any]] = []
            try:
                vrows = conn.execute(
                    text(
                        """
                        SELECT vital_id, patient_no, measured_at, heart_rate_bpm,
                               blood_pressure_systolic, blood_pressure_diastolic,
                               body_temp_c, stress_score, source_channel,
                               synced_to_mysql_at IS NOT NULL AS synced_mysql
                        FROM user_vital_measurement
                        ORDER BY measured_at DESC
                        LIMIT 12
                        """
                    ),
                ).mappings().all()
                for vr in vrows:
                    d = dict(vr)
                    raw_pn = int(d["patient_no"])
                    mt = d.get("measured_at")
                    d["measured_at"] = _format_kst_display(mt)
                    d["synced_mysql"] = bool(d.pop("synced_mysql", False))
                    masked = _mask_pg_dict("user_vital_measurement", d)
                    masked["patient_no_key"] = raw_pn
                    recent_vitals.append(masked)
            except Exception:
                pass

            recent_clinical: list[dict[str, Any]] = []
            include_mysql_tid_col = False
            try:
                crows2 = conn.execute(
                    text(
                        """
                        SELECT clinical_event_id, patient_no, category, occurred_on,
                               department, title, status, source_mysql_treatment_id
                        FROM patient_clinical_event
                        ORDER BY occurred_on DESC, clinical_event_id DESC
                        LIMIT 15
                        """
                    ),
                ).mappings().all()
                for cr in crows2:
                    d = dict(cr)
                    raw_pn_e = int(d["patient_no"])
                    if d.get("source_mysql_treatment_id") is not None:
                        include_mysql_tid_col = True
                    od = d.get("occurred_on")
                    d["occurred_on"] = _format_kst_display(od) if od else None
                    cat = str(d.get("category") or "")
                    d["category_kr"] = clinical_category_label_kr(cat)
                    st = d.get("status")
                    d["status_kr"] = status_label_kr(st) if st is not None else None
                    masked_e = _mask_pg_dict("patient_clinical_event", d)
                    masked_e["patient_no_key"] = raw_pn_e
                    recent_clinical.append(masked_e)
            except Exception:
                pass

            daily_sample: list[dict[str, Any]] = []
            try:
                drows = conn.execute(
                    text(
                        """
                        SELECT patient_no, summary_date, step_count, step_goal,
                               sleep_hours, stress_level,
                               synced_to_mysql_at IS NOT NULL AS synced_mysql
                        FROM user_daily_wellness
                        ORDER BY summary_date DESC, patient_no
                        LIMIT 10
                        """
                    ),
                ).mappings().all()
                for dr in drows:
                    d = dict(dr)
                    raw_pn_w = int(d["patient_no"])
                    sd = d.get("summary_date")
                    d["summary_date"] = _format_kst_display(sd) if sd else None
                    d["synced_mysql"] = bool(d.pop("synced_mysql", False))
                    masked_w = _mask_pg_dict("user_daily_wellness", d)
                    masked_w["patient_no_key"] = raw_pn_w
                    daily_sample.append(masked_w)
            except Exception:
                pass

            pending_daily = 0
            try:
                pd = conn.execute(
                    text(
                        """
                        SELECT COUNT(*)::bigint FROM user_daily_wellness
                        WHERE synced_to_mysql_at IS NULL
                        """
                    ),
                ).scalar()
                pending_daily = int(pd or 0)
            except Exception:
                pass

            vitals_agg.pending_daily_mysql_sync = pending_daily

            return PgDashboardSnapshot(
                connected=True,
                message=None,
                generated_at=_format_kst_display(now) or "",
                include_mysql_treatment_id_column=include_mysql_tid_col,
                table_counts=table_counts,
                etl=etl,
                clinical_by_category=clinical_by_category,
                vitals_aggregate=vitals_agg,
                recent_vitals=recent_vitals,
                recent_clinical_events=recent_clinical,
                daily_wellness_sample_rows=daily_sample,
            )
