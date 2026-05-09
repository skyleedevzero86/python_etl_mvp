from datetime import date, datetime
from decimal import Decimal

from app.domain.datetime_display import (
    cell_value_display,
    format_datetime_kr,
    map_row_datetimes_to_kr,
)


def test_format_datetime_kr_none():
    assert format_datetime_kr(None) is None


def test_format_datetime_kr_date_only():
    assert format_datetime_kr(date(2026, 5, 9)) == "2026년 5월 9일"


def test_format_datetime_kr_naive_datetime():
    dt = datetime(2026, 5, 9, 22, 43, 24)
    out = format_datetime_kr(dt)
    assert "2026년 5월 9일" in out
    assert "22:43" in out


def test_format_datetime_kr_iso_string_microseconds():
    s = "2026-05-09T22:43:24.666336"
    out = format_datetime_kr(s)
    assert "2026년 5월 9일" in out
    assert "22:43" in out


def test_cell_value_display_decimal_integer():
    assert cell_value_display(Decimal("10")) == 10


def test_cell_value_display_decimal_float():
    assert cell_value_display(Decimal("1.5")) == 1.5


def test_map_row_datetimes_to_kr():
    row = {
        "patient_no": "***34",
        "created_date": datetime(2026, 1, 2, 15, 0, 0),
        "patient_rrn_sha256": "abc",
    }
    out = map_row_datetimes_to_kr(row)
    assert out["patient_no"] == "***34"
    assert "2026년 1월 2일" in str(out["created_date"])
    assert out["patient_rrn_sha256"] == "abc"
