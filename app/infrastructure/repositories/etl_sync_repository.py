from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from random import randint
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

_ETL_TAG = "ETL_SYNC"


def _now_naive() -> datetime:
    return datetime.now().replace(microsecond=0)


class EtlSyncRepository:
    def __init__(self, mysql_session: Session, postgres_engine: Engine) -> None:
        self._mysql = mysql_session
        self._pg = postgres_engine

    def generate_wearable_slot(self) -> dict[str, Any]:
        with self._pg.connect() as conn:
            trans = conn.begin()
            try:
                rows = conn.execute(
                    text('SELECT patient_no FROM "Patient" ORDER BY patient_no ASC'),
                ).fetchall()
                patient_ids = [int(r[0]) for r in rows]
                if not patient_ids:
                    trans.commit()
                    return {"ok": True, "skipped": True, "reason": "no_patients_in_pg"}

                lock_row = conn.execute(
                    text(
                        "SELECT cursor_value FROM etl_runtime_state "
                        "WHERE job_code = :jc FOR UPDATE"
                    ),
                    {"jc": "wearable_round_robin"},
                ).first()
                cur = int(lock_row[0]) if lock_row is not None else None

                if lock_row is None:
                    conn.execute(
                        text(
                            """
                            INSERT INTO etl_runtime_state (job_code, cursor_value, updated_at)
                            VALUES ('wearable_round_robin', 0, CURRENT_TIMESTAMP)
                            """
                        ),
                    )
                    cur = 0

                idx = cur % len(patient_ids)
                patient_no = patient_ids[idx]

                conn.execute(
                    text(
                        """
                        UPDATE etl_runtime_state
                        SET cursor_value = cursor_value + 1, updated_at = CURRENT_TIMESTAMP
                        WHERE job_code = 'wearable_round_robin'
                        """
                    ),
                )

                measured_at = _now_naive()
                hr = randint(62, 125)
                sbp = randint(105, 138)
                dbp = randint(68, 88)
                temp = Decimal(str(round(randint(355, 373) / 10.0, 1)))
                stress = Decimal(str(round(randint(1500, 4200) / 100.0, 2)))

                conn.execute(
                    text(
                        """
                        INSERT INTO user_vital_measurement
                            (patient_no, measured_at, heart_rate_bpm,
                             blood_pressure_systolic, blood_pressure_diastolic,
                             body_temp_c, stress_score, source_channel,
                             synced_to_mysql_at, created_date, intt_cd)
                        VALUES
                            (:pn, :mt, :hr, :sbp, :dbp, :tc, :st, :sch, NULL, CURRENT_TIMESTAMP, :intt)
                        """
                    ),
                    {
                        "pn": patient_no,
                        "mt": measured_at,
                        "hr": hr,
                        "sbp": sbp,
                        "dbp": dbp,
                        "tc": temp,
                        "st": stress,
                        "sch": "scheduler",
                        "intt": _ETL_TAG,
                    },
                )

                step_delta = randint(80, 420)
                sleep_h = Decimal(str(round(randint(55, 95) / 10.0, 1)))
                stress_d = Decimal(str(round(randint(1800, 4800) / 100.0, 2)))
                today = date.today()

                conn.execute(
                    text(
                        """
                        INSERT INTO user_daily_wellness
                            (patient_no, summary_date, step_count, step_goal, sleep_hours,
                             stress_level, synced_to_mysql_at, created_date, last_modified_date, intt_cd)
                        VALUES
                            (:pn, :sd, :sc, 1000, :sh, :sl, NULL,
                             CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, :intt)
                        ON CONFLICT (patient_no, summary_date) DO UPDATE SET
                            step_count = user_daily_wellness.step_count + EXCLUDED.step_count,
                            sleep_hours = EXCLUDED.sleep_hours,
                            stress_level = EXCLUDED.stress_level,
                            synced_to_mysql_at = NULL,
                            last_modified_date = CURRENT_TIMESTAMP,
                            intt_cd = EXCLUDED.intt_cd
                        """
                    ),
                    {
                        "pn": patient_no,
                        "sd": today,
                        "sc": step_delta,
                        "sh": sleep_h,
                        "sl": stress_d,
                        "intt": _ETL_TAG,
                    },
                )

                trans.commit()
            except Exception:
                trans.rollback()
                raise

        return {
            "ok": True,
            "patient_no": patient_no,
            "cursor_after": cur + 1 if cur is not None else 1,
            "measured_at": measured_at.isoformat(),
        }

    def sync_postgres_to_mysql(self) -> dict[str, Any]:
        stats: dict[str, int | list[str]] = {
            "patients_upserted": 0,
            "profiles_upserted": 0,
            "vitals_copied": 0,
            "daily_copied": 0,
            "vital_ids_marked": 0,
            "daily_marked": 0,
            "errors": [],
        }

        with self._pg.connect() as pg:
            patients = pg.execute(
                text(
                    """
                    SELECT patient_no, patient_name, patient_rrn, patient_gender, patient_birth,
                           patient_address, patient_email, patient_tel, patient_foreign,
                           patient_passport, patient_hypass_YN, patient_last_visit, guardian,
                           created_date, last_modified_date, intt_cd
                    FROM "Patient"
                    ORDER BY patient_no
                    """
                ),
            ).mappings().all()

            for p in patients:
                try:
                    self._mysql.execute(
                        text(
                            """
                            INSERT INTO Patient (
                                patient_no, patient_name, patient_rrn, patient_gender, patient_birth,
                                patient_address, patient_email, patient_tel, patient_foreign,
                                patient_passport, patient_hypass_YN, patient_last_visit, guardian,
                                created_date, last_modified_date, intt_cd
                            ) VALUES (
                                :patient_no, :patient_name, :patient_rrn, :patient_gender, :patient_birth,
                                :patient_address, :patient_email, :patient_tel, :patient_foreign,
                                :patient_passport, :patient_hypass_YN, :patient_last_visit, :guardian,
                                :created_date, :last_modified_date, :intt_cd
                            )
                            ON DUPLICATE KEY UPDATE
                                patient_name = VALUES(patient_name),
                                patient_gender = VALUES(patient_gender),
                                patient_birth = VALUES(patient_birth),
                                patient_address = VALUES(patient_address),
                                patient_last_visit = VALUES(patient_last_visit),
                                last_modified_date = VALUES(last_modified_date),
                                intt_cd = VALUES(intt_cd)
                            """
                        ),
                        dict(p),
                    )
                    stats["patients_upserted"] += 1
                except IntegrityError as e:
                    stats["errors"].append(f"patient {p['patient_no']}: {e}")
            profiles = pg.execute(
                text(
                    """
                    SELECT patient_no, app_user_id, blood_type, height_cm, weight_kg,
                           created_date, last_modified_date, intt_cd
                    FROM user_app_profile
                    """
                ),
            ).mappings().all()

            for pr in profiles:
                d = dict(pr)
                try:
                    self._mysql.execute(
                        text(
                            """
                            INSERT INTO user_app_profile (
                                patient_no, app_user_id, blood_type, height_cm, weight_kg,
                                created_date, last_modified_date, intt_cd
                            ) VALUES (
                                :patient_no, :app_user_id, :blood_type, :height_cm, :weight_kg,
                                :created_date, :last_modified_date, :intt_cd
                            )
                            ON DUPLICATE KEY UPDATE
                                app_user_id = VALUES(app_user_id),
                                blood_type = VALUES(blood_type),
                                height_cm = VALUES(height_cm),
                                weight_kg = VALUES(weight_kg),
                                last_modified_date = VALUES(last_modified_date),
                                intt_cd = VALUES(intt_cd)
                            """
                        ),
                        d,
                    )
                    stats["profiles_upserted"] += 1
                except IntegrityError as e:
                    stats["errors"].append(f"profile {d['patient_no']}: {e}")
        with self._pg.connect() as pg:
            vitals = pg.execute(
                text(
                    """
                    SELECT vital_id, patient_no, measured_at, heart_rate_bpm,
                           blood_pressure_systolic, blood_pressure_diastolic,
                           body_temp_c, stress_score, source_channel, created_date, intt_cd
                    FROM user_vital_measurement
                    WHERE synced_to_mysql_at IS NULL
                    ORDER BY vital_id
                    LIMIT 2000
                    """
                ),
            ).mappings().all()

        for v in vitals:
            vd = dict(v)
            mysql_row = {
                "patient_no": vd["patient_no"],
                "measured_at": vd["measured_at"],
                "heart_rate_bpm": vd["heart_rate_bpm"],
                "blood_pressure_systolic": vd["blood_pressure_systolic"],
                "blood_pressure_diastolic": vd["blood_pressure_diastolic"],
                "body_temp_c": float(vd["body_temp_c"]) if vd["body_temp_c"] is not None else None,
                "stress_score": float(vd["stress_score"]) if vd["stress_score"] is not None else None,
                "source_channel": vd["source_channel"],
                "created_date": vd["created_date"] or _now_naive(),
                "intt_cd": vd["intt_cd"] or _ETL_TAG,
            }
            try:
                self._mysql.execute(
                    text(
                        """
                        INSERT INTO wearable_vital (
                            patient_no, measured_at, heart_rate_bpm,
                            blood_pressure_systolic, blood_pressure_diastolic,
                            body_temp_c, stress_score, source_channel,
                            created_date, intt_cd
                        ) VALUES (
                            :patient_no, :measured_at, :heart_rate_bpm,
                            :blood_pressure_systolic, :blood_pressure_diastolic,
                            :body_temp_c, :stress_score, :source_channel,
                            :created_date, :intt_cd
                        )
                        ON DUPLICATE KEY UPDATE vital_id = wearable_vital.vital_id
                        """
                    ),
                    mysql_row,
                )
                stats["vitals_copied"] += 1
                with self._pg.connect() as pg2:
                    pg2.execute(
                        text(
                            """
                            UPDATE user_vital_measurement
                            SET synced_to_mysql_at = CURRENT_TIMESTAMP
                            WHERE vital_id = :vid AND synced_to_mysql_at IS NULL
                            """
                        ),
                        {"vid": vd["vital_id"]},
                    )
                    pg2.commit()
                stats["vital_ids_marked"] += 1
            except Exception as e:
                stats["errors"].append(f"vital {vd['vital_id']}: {e}")
        with self._pg.connect() as pg:
            dailies = pg.execute(
                text(
                    """
                    SELECT patient_no, summary_date, step_count, step_goal,
                           sleep_hours, stress_level, created_date, last_modified_date, intt_cd
                    FROM user_daily_wellness
                    WHERE synced_to_mysql_at IS NULL
                    ORDER BY patient_no, summary_date
                    LIMIT 2000
                    """
                ),
            ).mappings().all()

        for dw in dailies:
            dd = dict(dw)
            try:
                self._mysql.execute(
                    text(
                        """
                        INSERT INTO wearable_daily_wellness (
                            patient_no, summary_date, step_count, step_goal,
                            sleep_hours, stress_level, created_date, last_modified_date, intt_cd
                        ) VALUES (
                            :patient_no, :summary_date, :step_count, :step_goal,
                            :sleep_hours, :stress_level, :created_date, :last_modified_date, :intt_cd
                        )
                        ON DUPLICATE KEY UPDATE
                            step_count = VALUES(step_count),
                            step_goal = VALUES(step_goal),
                            sleep_hours = VALUES(sleep_hours),
                            stress_level = VALUES(stress_level),
                            last_modified_date = VALUES(last_modified_date),
                            intt_cd = VALUES(intt_cd)
                        """
                    ),
                    {
                        "patient_no": dd["patient_no"],
                        "summary_date": dd["summary_date"],
                        "step_count": dd["step_count"],
                        "step_goal": dd["step_goal"],
                        "sleep_hours": float(dd["sleep_hours"]) if dd["sleep_hours"] is not None else None,
                        "stress_level": float(dd["stress_level"]) if dd["stress_level"] is not None else None,
                        "created_date": dd["created_date"] or _now_naive(),
                        "last_modified_date": dd["last_modified_date"] or _now_naive(),
                        "intt_cd": dd["intt_cd"] or _ETL_TAG,
                    },
                )
                stats["daily_copied"] += 1
                with self._pg.connect() as pg2:
                    pg2.execute(
                        text(
                            """
                            UPDATE user_daily_wellness
                            SET synced_to_mysql_at = CURRENT_TIMESTAMP
                            WHERE patient_no = :pn AND summary_date = :sd AND synced_to_mysql_at IS NULL
                            """
                        ),
                        {"pn": dd["patient_no"], "sd": dd["summary_date"]},
                    )
                    pg2.commit()
                stats["daily_marked"] += 1
            except Exception as e:
                stats["errors"].append(f"daily {dd['patient_no']}/{dd['summary_date']}: {e}")
        stats["ok"] = True
        return stats

    def sync_mysql_treatments_to_postgres(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "examined": 0,
            "inserted": 0,
            "marked_mysql": 0,
            "skipped_existing_pg": 0,
            "errors": [],
        }

        rows = self._mysql.execute(
            text(
                """
                SELECT treatment_id, patient_no, treatment_type, treatment_date,
                       treatment_comment, treatment_dept, treatment_status
                FROM treatments
                WHERE patient_no IS NOT NULL
                  AND (synced_to_postgres_at IS NULL)
                ORDER BY treatment_id
                LIMIT 500
                """
            ),
        ).mappings().all()

        for r in rows:
            rd = dict(r)
            tid = int(rd["treatment_id"])
            pn = int(rd["patient_no"])
            out["examined"] += 1
            def _cat(tt: str | None) -> str:
                if tt in ("OUTPATIENT", "INPATIENT", "EMERGENCY"):
                    return tt
                return "OUTPATIENT"

            td = rd["treatment_date"]
            if hasattr(td, "date"):
                occurred = td.date()
            else:
                occurred = td

            dept = rd["treatment_dept"] or ""
            title = f"{dept or rd['treatment_type']} 진료 #{tid}"
            summary = rd["treatment_comment"]
            status = rd["treatment_status"]

            ts = _now_naive()
            with self._pg.connect() as conn:
                exists = conn.execute(
                    text(
                        "SELECT 1 FROM patient_clinical_event WHERE source_mysql_treatment_id = :tid LIMIT 1"
                    ),
                    {"tid": tid},
                ).first()
            if exists:
                out["skipped_existing_pg"] += 1
                self._mysql.execute(
                    text(
                        """
                        UPDATE treatments
                        SET synced_to_postgres_at = :ts, last_modified_date = :ts
                        WHERE treatment_id = :tid
                        """
                    ),
                    {"tid": tid, "ts": ts},
                )
                out["marked_mysql"] += 1
                continue

            try:
                with self._pg.connect() as conn:
                    ins = conn.execute(
                        text(
                            """
                            INSERT INTO patient_clinical_event (
                                patient_no, category, occurred_on, department, title, summary,
                                status, institution_name, source_mysql_treatment_id,
                                created_date, intt_cd
                            ) VALUES (
                                :pn, :cat, :od, :dept, :title, :summary,
                                :st, NULL, :tid,
                                CURRENT_TIMESTAMP, :intt
                            )
                            ON CONFLICT (source_mysql_treatment_id) DO NOTHING
                            """
                        ),
                        {
                            "pn": pn,
                            "cat": _cat(rd["treatment_type"]),
                            "od": occurred,
                            "dept": rd["treatment_dept"],
                            "title": title[:200],
                            "summary": summary,
                            "st": status,
                            "tid": tid,
                            "intt": _ETL_TAG,
                        },
                    )
                    rc = ins.rowcount or 0
                    conn.commit()
                    if rc > 0:
                        out["inserted"] += 1
            except Exception as e:
                out["errors"].append(f"treatment {tid}: {e}")
                continue

            self._mysql.execute(
                text(
                    """
                    UPDATE treatments
                    SET synced_to_postgres_at = :ts, last_modified_date = :ts
                    WHERE treatment_id = :tid
                    """
                ),
                {"tid": tid, "ts": ts},
            )
            out["marked_mysql"] += 1
        out["ok"] = True
        return out
