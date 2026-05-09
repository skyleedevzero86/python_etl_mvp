"""화면·API 표시용 코드 → 한글 라벨 (DB에는 영문 코드 유지)."""


STATUS_CODE_KR: dict[str, str] = {
    "COMPLETED": "완료",
    "SCHEDULED": "예약",
    "CANCELLED": "취소",
    "IN_PROGRESS": "진행중",
    "WAITING": "대기",
    "PENDING": "대기",
    "CONFIRMED": "확정",
    "DISPENSED": "조제완료",
    "ISSUED": "발급",
    "NO_SHOW": "노쇼",
    "RESCHEDULED": "일정변경",
    "DEFERRED": "보류",
    "OPEN": "진행",
    "CLOSED": "종료",
    "ACTIVE": "활성",
    "INACTIVE": "비활성",
    "FAILED": "실패",
    "SUCCESS": "성공",
}

CLINICAL_CATEGORY_CODE_KR: dict[str, str] = {
    "OUTPATIENT": "외래",
    "INPATIENT": "입원",
    "EMERGENCY": "응급",
    "HEALTH_CHECKUP": "건강검진",
    "LAB": "검사실",
    "IMAGING": "영상",
    "PHARMACY": "약국·처방",
    "REHAB": "재활",
    "TELEMEDICINE": "비대면진료",
    "CLINICAL": "임상",
    "SURGICAL": "외과",
    "ULTRASOUND": "초음파",
}


def status_label_kr(code: str | None) -> str | None:
    if code is None:
        return None
    s = str(code).strip()
    if not s:
        return None
    return STATUS_CODE_KR.get(s.upper(), s)


def clinical_category_label_kr(code: str) -> str:
    c = (code or "").strip()
    if not c:
        return "기타"
    return CLINICAL_CATEGORY_CODE_KR.get(c.upper(), c)
