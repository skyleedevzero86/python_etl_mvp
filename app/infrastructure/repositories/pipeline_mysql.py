from datetime import UTC, datetime
from random import choice, randint
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.enums import PipelineJob

_INTT = "PIPELINE"


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class MysqlPipelineRepository:
    def __init__(self, session: Session, daily_rows: int = 1000) -> None:
        self._session = session
        self._daily_rows = max(1, int(daily_rows))

    def run_job(self, job: PipelineJob) -> dict:
        now = _utc_now()
        if job is PipelineJob.INITIAL:
            return self._initial(now)
        return self._completion(now)

    def _next_patient_no(self) -> int:
        row = self._session.execute(text("SELECT COALESCE(MAX(patient_no), 10000000) AS m FROM Patient")).one()
        return int(row.m) + 1

    def _initial(self, now: datetime) -> dict[Any, Any]:
        suffix = now.strftime("%Y%m%d%H%M%S") + f"{randint(10, 99)}"
        dept_rows = (
            ("D" + suffix, "내과" + suffix[:4], None, "CLINICAL", now, now, _INTT),
            ("D2" + suffix, "외과" + suffix[:4], None, "SURGICAL", now, now, _INTT),
        )
        self._session.execute(
            text(
                """
                INSERT INTO department
                    (department_code, department_name, department_eng_name, department_type,
                     created_date, last_modified_date, intt_cd)
                VALUES (:c, :n, :e, :t, :cd, :lm, :i)
                """
            ),
            [
                dict(c=r[0], n=r[1], e=r[2], t=r[3], cd=r[4], lm=r[5], i=r[6])
                for r in dept_rows
            ],
        )
        kcd_rows = (
            ("KCD" + suffix, "감기", "cold", None, None, now, now, _INTT),
            ("KCD2" + suffix, "골절", "fx", None, None, now, now, _INTT),
        )
        self._session.execute(
            text(
                """
                INSERT INTO kcd_code (code, name_korean, name_english, category, description,
                                      created_date, last_modified_date, intt_cd)
                VALUES (:code, :nk, :ne, :cat, :desc, :cd, :lm, :i)
                """
            ),
            [
                dict(
                    code=r[0],
                    nk=r[1],
                    ne=r[2],
                    cat=r[3],
                    desc=r[4],
                    cd=r[5],
                    lm=r[6],
                    i=r[7],
                )
                for r in kcd_rows
            ],
        )
        base = self._next_patient_no()
        patient_count = self._daily_rows
        patient_rows = []
        for i in range(patient_count):
            pn = base + i
            rrn = f"900101-{(pn % 10_000_000):07d}"
            gender = choice(("M", "F"))
            patient_rows.append(
                dict(
                    pn=pn,
                    name=f"배치초기{i}",
                    rrn=rrn,
                    g=gender,
                    birth="1990-01-01",
                    addr="SEOUL",
                    email=f"p{pn}@pipeline.local",
                    tel=f"010{pn:08d}",
                    lm=now,
                    cd=now,
                    i=_INTT,
                )
            )
        self._session.execute(
            text(
                """
                INSERT INTO Patient (patient_no, patient_name, patient_rrn, patient_gender,
                    patient_birth, patient_address, patient_email, patient_tel,
                    created_date, last_modified_date, intt_cd)
                VALUES (:pn, :name, :rrn, :g, :birth, :addr, :email, :tel, :cd, :lm, :i)
                """
            ),
            patient_rows,
        )
        self._session.execute(
            text(
                """
                INSERT INTO examination (equipment_id, examination_name, examination_type,
                    examination_constraints, examination_location, examination_price,
                    created_date, last_modified_date, intt_cd)
                VALUES (NULL, :name, :t, NULL, :loc, 10000, :cd, :lm, :i)
                """
            ),
            dict(
                name="흉부 X-ray-" + suffix,
                t="IMAGING",
                loc="1층 방사선실",
                cd=now,
                lm=now,
                i=_INTT,
            ),
        )
        inst_name = "검진기관-" + suffix
        self._session.execute(
            text(
                """
                INSERT INTO health_checkup_institution
                    (region_code, region_name, institution_name, institution_type, address,
                     sido, sigungu, latitude, longitude, phone_number, is_active, data_source, data_date,
                     created_date, last_modified_date, intt_cd)
                VALUES (:rc, :rn, :iname, :itype, :addr, :sido, :sig, 37.5, 127.0, :phone,
                        1, 'PIPELINE_ETL', :dd, :cd, :lm, :i)
                """
            ),
            dict(
                rc="11",
                rn="서울",
                iname=inst_name,
                itype="검진센터",
                addr="테스트 주소",
                sido="서울",
                sig="강남",
                phone="0212345678",
                dd=now.date(),
                cd=now,
                lm=now,
                i=_INTT,
            ),
        )
        return {
            "job": PipelineJob.INITIAL.value,
            "patients_inserted_from": base,
            "patients_inserted_count": patient_count,
            "suffix": suffix,
        }

    def _completion(self, now: datetime) -> dict[Any, Any]:
        suffix = now.strftime("%Y%m%d%H%M%S") + f"{randint(10, 99)}"

        dept = self._session.execute(
            text("SELECT id FROM department ORDER BY id DESC LIMIT 1")
        ).one()
        dept_id = int(dept.id)

        patients = self._session.execute(
            text(
                """
                SELECT patient_no FROM Patient
                ORDER BY patient_no DESC
                LIMIT :limit_rows
                """
            ),
            {"limit_rows": self._daily_rows},
        ).all()
        if len(patients) < 2:
            raise RuntimeError("완료 계열 배치는 환자가 둘 이상 있어야 합니다. 초기 배치를 먼저 실행하세요.")

        doc_id = 900001

        def ins_check(pn: int, status: str) -> int:
            self._session.execute(
                text(
                    """
                    INSERT INTO check_in (patient_no, user_id, checkIn_date, checkIn_status,
                        checkIn_comment, created_date, last_modified_date, intt_cd)
                    VALUES (:pn, NULL, :dt, :st, :cm, :cd, :lm, :i)
                    """
                ),
                dict(
                    pn=pn,
                    dt=now,
                    st=status,
                    cm="pipeline-" + suffix,
                    cd=now,
                    lm=now,
                    i=_INTT,
                ),
            )
            rid = self._session.execute(text("SELECT LAST_INSERT_ID() AS id")).scalar_one()
            return int(rid)


        def ins_treatment(
            pn: int,
            cid: int | None,
            status: str,
        ) -> int:
            self._session.execute(
                text(
                    """
                    INSERT INTO treatments (checkIn_id, patient_no, treatment_doc, department_id,
                        treatment_type, treatment_status, treatment_date, treatment_start_time,
                        treatment_end_time, treatment_comment, treatment_dept,
                        created_date, last_modified_date, intt_cd)
                    VALUES (:cid, :pn, :doc, :did, :tt, :ts, :td, :ts1, :te, :tc, NULL, :cd, :lm, :i)
                    """
                ),
                dict(
                    cid=cid,
                    pn=pn,
                    doc=doc_id,
                    did=dept_id,
                    tt="OUTPATIENT",
                    ts=status,
                    td=now,
                    ts1=now,
                    te=now,
                    tc="completion-" + suffix,
                    cd=now,
                    lm=now,
                    i=_INTT,
                ),
            )
            tid = self._session.execute(text("SELECT LAST_INSERT_ID() AS id")).scalar_one()
            return int(tid)

        out_rows = []
        presc_rows = []
        completed_count = 0
        cancelled_count = 0
        for row in patients:
            pn = int(row[0])
            status = "COMPLETED" if randint(1, 100) <= 70 else "CANCELLED"
            if status == "COMPLETED":
                completed_count += 1
            else:
                cancelled_count += 1

            cid = ins_check(pn, status)
            tid = ins_treatment(pn, cid, status)

            out_rows.append(
                dict(
                    tid=tid,
                    cid=cid,
                    st=status,
                    cm=None if status == "COMPLETED" else "종료-" + suffix,
                    cd=now,
                    lm=now,
                    i=_INTT,
                )
            )

            pst = "DISPENSED" if status == "COMPLETED" else "CANCELLED"
            self._session.execute(
                text(
                    """
                    INSERT INTO Prescription (treatment_id, patient_no, prescription_doc,
                        prescription_date, prescription_status, prescription_type, prescription_memo,
                        created_date, last_modified_date, intt_cd)
                    VALUES (:tid, :pn, :doc, :pd, :ps, 'OUTPATIENT', :memo, :cd, :lm, :i)
                    """
                ),
                dict(
                    tid=tid,
                    pn=pn,
                    doc=doc_id,
                    pd=now,
                    ps=pst,
                    memo=None if pst == "DISPENSED" else "실패 취소-" + suffix,
                    cd=now,
                    lm=now,
                    i=_INTT,
                ),
            )
            pid = self._session.execute(text("SELECT LAST_INSERT_ID() AS id")).scalar_one()
            presc_rows.append(int(pid))

        self._session.execute(
            text(
                """
                INSERT INTO Out_Treatments (treatment_id, checkIn_id, treatment_status,
                    pre_treatment_id, treatment_comment, created_date, last_modified_date, intt_cd)
                VALUES (:tid, :cid, :st, NULL, :cm, :cd, :lm, :i)
                """
            ),
            out_rows,
        )

        return {
            "job": PipelineJob.COMPLETION.value,
            "check_ins": {"completed_count": completed_count, "cancelled_count": cancelled_count},
            "treatments": {"completed_count": completed_count, "cancelled_count": cancelled_count},
            "completion_rows": len(patients),
            "prescription_ids": presc_rows,
            "suffix": suffix,
        }
