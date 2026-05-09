from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from zoneinfo import ZoneInfo

_KST = ZoneInfo("Asia/Seoul")


def format_datetime_kr(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        d = value
        if d.tzinfo is None:
            d = d.replace(tzinfo=_KST)
        else:
            d = d.astimezone(_KST)
        return f"{d.year}년 {d.month}월 {d.day}일 {d.hour:02d}:{d.minute:02d}"
    if isinstance(value, date):
        return f"{value.year}년 {value.month}월 {value.day}일"
    if isinstance(value, str) and "T" in value:
        try:
            s = value.replace("Z", "+00:00")
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=_KST)
            else:
                dt = dt.astimezone(_KST)
            return f"{dt.year}년 {dt.month}월 {dt.day}일 {dt.hour:02d}:{dt.minute:02d}"
        except ValueError:
            return value
    return str(value) if value is not None else None


def cell_value_display(v: Any) -> Any:
    if v is None:
        return None
    if isinstance(v, datetime):
        return format_datetime_kr(v)
    if isinstance(v, date):
        return f"{v.year}년 {v.month}월 {v.day}일"
    if isinstance(v, Decimal):
        try:
            iv = int(v)
            if Decimal(iv) == v:
                return iv
        except Exception:
            pass
        return float(v)
    if isinstance(v, str) and "T" in v:
        fk = format_datetime_kr(v)
        return fk if fk is not None else v
    return v


def map_row_datetimes_to_kr(row: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in row.items():
        if str(k).endswith("_sha256"):
            out[k] = v
        else:
            out[k] = cell_value_display(v)
    return out
