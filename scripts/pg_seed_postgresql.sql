/* =====================================================================
 PostgreSQL 통합 스크립트
 =====================================================================
*/

ALTER TABLE user_vital_measurement
    ADD COLUMN IF NOT EXISTS synced_to_mysql_at TIMESTAMP NULL;

ALTER TABLE user_daily_wellness
    ADD COLUMN IF NOT EXISTS synced_to_mysql_at TIMESTAMP NULL;

ALTER TABLE patient_clinical_event
    ADD COLUMN IF NOT EXISTS source_mysql_treatment_id BIGINT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uk_pce_mysql_treatment_id
    ON patient_clinical_event (source_mysql_treatment_id);

CREATE TABLE IF NOT EXISTS etl_runtime_state (
    job_code    VARCHAR(64)   NOT NULL,
    cursor_value BIGINT       NOT NULL DEFAULT 0,
    meta        JSONB         NULL,
    updated_at  TIMESTAMP     NULL,
    PRIMARY KEY (job_code)
);


/* =====================================================================
 B. 데모 시드
 ===================================================================== */

BEGIN;

/* ---------- 환자 · 앱 프로필 · 장애 ---------- */

INSERT INTO "Patient"
    (patient_no, patient_name, patient_rrn, patient_gender, patient_birth, patient_address, patient_email, patient_tel,
     patient_foreign, patient_passport, patient_hypass_YN, patient_last_visit, guardian, created_date, last_modified_date, intt_cd)
VALUES
    (1234, '홍길동', '551231-2001234', 'F', DATE '1955-12-31', '서울 종로구', 'hong1234@demo.pg.local', '01012341234',
     '0', NULL, 'N', CURRENT_DATE, NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'FIN'),
    (20000001, '김민수', '900101-1000001', 'M', DATE '1990-01-01', '서울 강남구', 'p20000001@demo.local', '01020000001',
     '0', NULL, 'Y', CURRENT_DATE, NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'FIN'),
    (20000002, '이서연', '920303-2000002', 'F', DATE '1992-03-03', '서울 송파구', 'p20000002@demo.local', '01020000002',
     '0', NULL, 'N', CURRENT_DATE, NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'FIN'),
    (20000003, '박지훈', '850715-1000003', 'M', DATE '1985-07-15', '경기 성남시', 'p20000003@demo.local', '01020000003',
     '0', NULL, 'Y', CURRENT_DATE, NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'FIN'),
    (20000004, '최은지', '970811-2000004', 'F', DATE '1997-08-11', '인천 연수구', 'p20000004@demo.local', '01020000004',
     '0', NULL, 'N', CURRENT_DATE, NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'FIN'),
    (20000005, 'John Doe', '880212-5000005', 'M', DATE '1988-02-12', '서울 마포구', 'p20000005@demo.local', '01020000005',
     '1', 'P-880212-5000005', 'N', CURRENT_DATE, 'Jane Doe', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'FIN'),
    (20000006, '한지민', '010905-2000006', 'F', DATE '2001-09-05', '서울 용산구', 'p20000006@demo.local', '01020000006',
     '0', NULL, 'Y', CURRENT_DATE, NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'FIN')
ON CONFLICT (patient_no) DO NOTHING;

INSERT INTO user_app_profile
    (patient_no, app_user_id, blood_type, height_cm, weight_kg, created_date, last_modified_date, intt_cd)
VALUES
    (1234, '1234', 'AB', 168.0, 48.0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'FIN'),
    (20000001, 'U20000001', 'A', 172.0, 70.0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'FIN'),
    (20000002, 'U20000002', 'B', 165.0, 55.0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'FIN')
ON CONFLICT (patient_no) DO UPDATE SET
    app_user_id = EXCLUDED.app_user_id,
    blood_type = EXCLUDED.blood_type,
    height_cm = EXCLUDED.height_cm,
    weight_kg = EXCLUDED.weight_kg,
    last_modified_date = EXCLUDED.last_modified_date,
    intt_cd = EXCLUDED.intt_cd;

INSERT INTO disability
    (patient_no, disability_grade, disability_type, assistive_device_YN, disability_device_type, created_date, last_modified_date, intt_cd)
VALUES
    (20000003, '3급', '지체장애', 'Y', '휠체어', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'FIN')
ON CONFLICT (patient_no) DO NOTHING;

DELETE FROM user_vital_measurement WHERE intt_cd = 'FIN' AND patient_no IN (1234, 20000001);

INSERT INTO user_vital_measurement
    (patient_no, measured_at, heart_rate_bpm, blood_pressure_systolic, blood_pressure_diastolic, body_temp_c, stress_score, source_channel, created_date, intt_cd)
VALUES
    (1234, CURRENT_TIMESTAMP, 123, 123, 78, 36.5, 25.60, 'wearable', CURRENT_TIMESTAMP, 'FIN'),
    (1234, CURRENT_TIMESTAMP - INTERVAL '15 minutes', 118, 120, 76, 36.4, 24.00, 'wearable', CURRENT_TIMESTAMP, 'FIN'),
    (20000001, CURRENT_TIMESTAMP, 72, 118, 76, 36.5, 18.50, 'app', CURRENT_TIMESTAMP, 'FIN');

DELETE FROM user_daily_wellness WHERE intt_cd = 'FIN' AND patient_no IN (1234, 20000001);

INSERT INTO user_daily_wellness
    (patient_no, summary_date, step_count, step_goal, sleep_hours, stress_level, created_date, last_modified_date, intt_cd)
VALUES
    (1234, CURRENT_DATE, 54, 1000, 13.0, 45.00, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'FIN'),
    (20000001, CURRENT_DATE, 6420, 8000, 7.5, 22.00, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'FIN');

/* 진료·검사 타임라인 — 환자별 유형 상이 (외래·응급·입원·건검·검사·처방·재활 등) */
DELETE FROM patient_clinical_event WHERE intt_cd = 'FIN';

INSERT INTO patient_clinical_event
    (patient_no, category, occurred_on, department, title, summary, status, institution_name, created_date, intt_cd)
VALUES
    /* 홍길동 1234 — 고령·웨어러블, 외래·건검·검사 */
    (1234, 'OUTPATIENT', DATE '2026-04-10', '내과', '고혈압 외래 재진', '혈압 조절 상태 확인, 약물 유지 처방', 'COMPLETED', '종로연세의원', CURRENT_TIMESTAMP, 'FIN'),
    (1234, 'HEALTH_CHECKUP', DATE '2026-06-15', '건강증진센터', '종합건강검진 예약', '공단 검진 + 위내시경 옵션', 'SCHEDULED', '서울대학교병원', CURRENT_TIMESTAMP, 'FIN'),
    (1234, 'LAB', DATE '2026-05-02', '진단검사의학', '혈액검사 결과', '지질수치 경계, 복약 상담 권고', 'COMPLETED', '종로연세의원', CURRENT_TIMESTAMP, 'FIN'),
    /* 김민수 20000001 — 외래 + 입원 이력 */
    (20000001, 'OUTPATIENT', DATE '2026-03-22', '내과', '감기 후 유증상 외래', '상기도 염증 소견, 대증 치료', 'COMPLETED', '강남세브란스', CURRENT_TIMESTAMP, 'FIN'),
    (20000001, 'INPATIENT', DATE '2025-11-28', '외과', '대장 폴립 시술 입원', '1박 2일, 경과 양호 퇴원', 'COMPLETED', '강남세브란스', CURRENT_TIMESTAMP, 'FIN'),
    (20000001, 'TELEMEDICINE', DATE '2026-05-01', '내과', '비대면 재진', '증상 호전 확인', 'COMPLETED', '강남세브란스 모바일', CURRENT_TIMESTAMP, 'FIN'),
    /* 이서연 20000002 — 응급 + 외래 */
    (20000002, 'EMERGENCY', DATE '2026-02-14', '응급의학과', '야간 복통 응급', '급성 위장관 증상, 경구치료 후 귀가', 'COMPLETED', '송파응급센터', CURRENT_TIMESTAMP, 'FIN'),
    (20000002, 'OUTPATIENT', DATE '2026-02-21', '소화기내과', '응급 후 외래 추적', '추적 검사 예약', 'COMPLETED', '송파세브란스', CURRENT_TIMESTAMP, 'FIN'),
    /* 박지훈 20000003 — 장애 등록 + 재활 */
    (20000003, 'REHAB', DATE '2026-04-05', '재활의학과', '재활 외래', '보행 보조 훈련 4주차', 'COMPLETED', '행복재활센터', CURRENT_TIMESTAMP, 'FIN'),
    (20000003, 'OUTPATIENT', DATE '2026-03-10', '정형외과', '무릎 통증 외래', '영상 검사 후 보존적 치료', 'COMPLETED', '성남중앙병원', CURRENT_TIMESTAMP, 'FIN'),
    /* 최은지 20000004 — 영상 + 외래 */
    (20000004, 'IMAGING', DATE '2026-04-18', '영상의학과', 'MRI 검사', '요추 디스크 소견 경미', 'COMPLETED', '연세의료원', CURRENT_TIMESTAMP, 'FIN'),
    (20000004, 'OUTPATIENT', DATE '2026-04-25', '정형외과', 'MRI 결과 상담', '물리치료 연결', 'COMPLETED', '연세의료원', CURRENT_TIMESTAMP, 'FIN'),
    /* John Doe 20000005 */
    (20000005, 'OUTPATIENT', DATE '2026-04-30', 'International Clinic', 'Routine check-up', 'Blood pressure stable', 'COMPLETED', 'Seoul Global Clinic', CURRENT_TIMESTAMP, 'FIN'),
    /* 한지민 20000006 — 처방 + 외래 */
    (20000006, 'PHARMACY', DATE '2026-05-07', '약제부', '처방 조제 완료', '항히스타민제 14일분', 'COMPLETED', '용산약국', CURRENT_TIMESTAMP, 'FIN'),
    (20000006, 'OUTPATIENT', DATE '2026-05-06', '피부과', '두드러기 외래', '국소 스테로이드 처방', 'COMPLETED', '용산피부과', CURRENT_TIMESTAMP, 'FIN');

/* ---------- 건강검진 · 장애 돌봄 기관 · 통계 ---------- */

INSERT INTO health_checkup_institution
    (region_code, region_name, institution_name, institution_type, address, sido, sigungu, latitude, longitude, phone_number, is_active, data_source, data_date, created_date, last_modified_date, intt_cd)
SELECT '11', '서울', '서울대학교병원', '종합병원', '서울 종로구 대학로 101', '서울', '종로구', 37.5796, 126.9970, '02-2072-2114', 1, 'seed', CURRENT_DATE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'FIN'
WHERE NOT EXISTS (
    SELECT 1 FROM health_checkup_institution h
    WHERE h.institution_name = '서울대학교병원' AND h.region_code = '11' AND COALESCE(h.intt_cd, '') = 'FIN'
);

INSERT INTO health_checkup_institution
    (region_code, region_name, institution_name, institution_type, address, sido, sigungu, latitude, longitude, phone_number, is_active, data_source, data_date, created_date, last_modified_date, intt_cd)
SELECT '41', '경기', '분당서울대학교병원', '종합병원', '경기 성남시 분당구 구미로 173', '경기', '성남시', 37.3514, 127.1236, '031-787-7000', 1, 'seed', CURRENT_DATE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'FIN'
WHERE NOT EXISTS (
    SELECT 1 FROM health_checkup_institution h
    WHERE h.institution_name = '분당서울대학교병원' AND h.region_code = '41' AND COALESCE(h.intt_cd, '') = 'FIN'
);

INSERT INTO disability_care_institution
    (institution_type, institution_name, service_type, address, sido, sigungu, latitude, longitude, is_active, created_date, last_modified_date, intt_cd)
SELECT '복지관', '서울시립발달장애인복지관', '주간보호', '서울 영등포구 선유로 000', '서울', '영등포구', 37.5236, 126.8983, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'FIN'
WHERE NOT EXISTS (
    SELECT 1 FROM disability_care_institution d
    WHERE d.institution_name = '서울시립발달장애인복지관' AND COALESCE(d.intt_cd, '') = 'FIN'
);

INSERT INTO disability_care_institution
    (institution_type, institution_name, service_type, address, sido, sigungu, latitude, longitude, is_active, created_date, last_modified_date, intt_cd)
SELECT '재활센터', '행복재활센터', '재활치료', '경기 수원시 팔달구 효원로 000', '경기', '수원시', 37.2636, 127.0286, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'FIN'
WHERE NOT EXISTS (
    SELECT 1 FROM disability_care_institution d
    WHERE d.institution_name = '행복재활센터' AND COALESCE(d.intt_cd, '') = 'FIN'
);

INSERT INTO inpatient_statistics
    (statistics_year, institution_type, region_code, region_name, visit_days, benefit_days, medical_fee, benefit_fee, data_source, data_date, created_date, last_modified_date, intt_cd)
SELECT '2024', '종합병원', '11', '서울', 1200000, 980000, 450000000000, 320000000000, 'seed', DATE '2024-12-31', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'FIN'
WHERE NOT EXISTS (
    SELECT 1 FROM inpatient_statistics i
    WHERE i.statistics_year = '2024' AND i.institution_type = '종합병원' AND i.region_code = '11' AND COALESCE(i.intt_cd, '') = 'FIN'
);

INSERT INTO inpatient_statistics
    (statistics_year, institution_type, region_code, region_name, visit_days, benefit_days, medical_fee, benefit_fee, data_source, data_date, created_date, last_modified_date, intt_cd)
SELECT '2024', '의원', '41', '경기', 8900000, 7200000, 180000000000, 140000000000, 'seed', DATE '2024-12-31', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'FIN'
WHERE NOT EXISTS (
    SELECT 1 FROM inpatient_statistics i
    WHERE i.statistics_year = '2024' AND i.institution_type = '의원' AND i.region_code = '41' AND COALESCE(i.intt_cd, '') = 'FIN'
);

INSERT INTO treatment_department_statistics
    (statistics_year, region_code, region_name, department_name, patient_count, treatment_count, medical_fee, benefit_fee, data_source, data_date, created_date, last_modified_date, intt_cd)
VALUES
    ('2024', '11', '서울', '내과', 420000, 980000, 95000000000, 72000000000, 'seed', DATE '2024-12-31', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'FIN'),
    ('2024', '11', '서울', '외과', 180000, 340000, 78000000000, 61000000000, 'seed', DATE '2024-12-31', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'FIN'),
    ('2024', '41', '경기', '내과', 310000, 720000, 62000000000, 48000000000, 'seed', DATE '2024-12-31', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'FIN')
ON CONFLICT (statistics_year, region_code, department_name) DO NOTHING;

COMMIT;
