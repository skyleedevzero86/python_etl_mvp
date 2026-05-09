from app.domain.display_labels import clinical_category_label_kr, status_label_kr


def test_status_label_kr_known():
    assert status_label_kr("COMPLETED") == "완료"
    assert status_label_kr("SCHEDULED") == "예약"


def test_status_label_kr_case_insensitive():
    assert status_label_kr("completed") == "완료"


def test_status_label_kr_none():
    assert status_label_kr(None) is None


def test_status_label_kr_unknown_passthrough():
    assert status_label_kr("CUSTOM_CODE") == "CUSTOM_CODE"


def test_clinical_category_label_kr():
    assert clinical_category_label_kr("OUTPATIENT") == "외래"
    assert clinical_category_label_kr("") == "기타"
