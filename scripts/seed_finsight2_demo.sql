/* =====================================================================
 데모 시드 데이터 적재 SQL
 ---------------------------------------------------------------------
 범위 : 진료 운영 대시보드와 파이프라인 검증용 샘플 데이터
 기준 : 디비정리.sql 도메인 구성을 따르는 INSERT IGNORE 기반 시드
 ===================================================================== */

START TRANSACTION;

SET @INTT := 'FIN';

/* =====================================================================
 1. 공통/코드 영역
 ===================================================================== */

-- 진료과 마스터 시드
INSERT IGNORE INTO department
    (id, department_code, department_name, department_eng_name, department_type, created_date, last_modified_date, intt_cd)
VALUES
    (101, 'IM',  '내과',   'Internal Medicine', 'CLINICAL', NOW(), NOW(), @INTT),
    (102, 'GS',  '외과',   'General Surgery',   'SURGICAL', NOW(), NOW(), @INTT),
    (103, 'ER',  '응급의학과', 'Emergency Medicine', 'EMERGENCY', NOW(), NOW(), @INTT),
    (104, 'FM',  '가정의학과', 'Family Medicine', 'CLINICAL', NOW(), NOW(), @INTT);

-- 한국표준질병분류 KCD 시드
INSERT IGNORE INTO kcd_code
    (id, code, name_korean, name_english, category, description, active, created_date, last_modified_date, intt_cd)
VALUES
    (1001, 'J00',   '급성 비인두염', 'Acute nasopharyngitis', '호흡기', '감기', 1, NOW(), NOW(), @INTT),
    (1002, 'S52.5', '요골 원위부 골절', 'Fracture of lower end of radius', '근골격', '손목 골절', 1, NOW(), NOW(), @INTT),
    (1003, 'I10',   '본태성 고혈압', 'Essential hypertension', '순환기', '고혈압', 1, NOW(), NOW(), @INTT),
    (1004, 'K35',   '급성 충수염', 'Acute appendicitis', '소화기', '맹장염', 1, NOW(), NOW(), @INTT);

/* =====================================================================
 2. 환자/진료 흐름 영역
 ===================================================================== */

-- 환자 마스터 시드
INSERT IGNORE INTO Patient
    (patient_no, patient_name, patient_rrn, patient_gender, patient_birth, patient_address, patient_email, patient_tel,
     patient_foreign, patient_passport, patient_hypass_YN, patient_last_visit, guardian, created_date, last_modified_date, intt_cd)
VALUES
    (20000001, '김민수', '900101-1000001', 'M', '1990-01-01', '서울 강남구', 'p20000001@demo.local', '01020000001', '0', NULL, 'Y', CURDATE(), NULL, NOW(), NOW(), @INTT),
    (20000002, '이서연', '920303-2000002', 'F', '1992-03-03', '서울 송파구', 'p20000002@demo.local', '01020000002', '0', NULL, 'N', CURDATE(), NULL, NOW(), NOW(), @INTT),
    (20000003, '박지훈', '850715-1000003', 'M', '1985-07-15', '경기 성남시', 'p20000003@demo.local', '01020000003', '0', NULL, 'Y', CURDATE(), NULL, NOW(), NOW(), @INTT),
    (20000004, '최은지', '970811-2000004', 'F', '1997-08-11', '인천 연수구', 'p20000004@demo.local', '01020000004', '0', NULL, 'N', CURDATE(), NULL, NOW(), NOW(), @INTT),
    (20000005, 'John Doe', '880212-5000005', 'M', '1988-02-12', '서울 마포구', 'p20000005@demo.local', '01020000005', '1', 'P-880212-5000005', 'N', CURDATE(), 'Jane Doe', NOW(), NOW(), @INTT),
    (20000006, '한지민', '010905-2000006', 'F', '2001-09-05', '서울 용산구', 'p20000006@demo.local', '01020000006', '0', NULL, 'Y', CURDATE(), NULL, NOW(), NOW(), @INTT);

-- 환자 예약 시드
INSERT IGNORE INTO Reservation
    (reservation_id, patient_no, user_id, reservation_datetime, reservation_status, reservation_YN, reservation_change_datetime, reservation_change_cause, created_date, last_modified_date, intt_cd)
VALUES
    (30001, 20000001, 900001, DATE_ADD(NOW(), INTERVAL 1 DAY), 'CONFIRMED', 'Y', NULL, NULL, NOW(), NOW(), @INTT),
    (30002, 20000002, 900002, DATE_ADD(NOW(), INTERVAL 2 DAY), 'WAITING', 'Y', NULL, NULL, NOW(), NOW(), @INTT),
    (30003, 20000005, 900003, DATE_ADD(NOW(), INTERVAL 3 DAY), 'CONFIRMED', 'Y', NULL, NULL, NOW(), NOW(), @INTT);

-- 접수 체크인 시드
INSERT IGNORE INTO check_in
    (checkIn_id, patient_no, user_id, checkIn_date, checkIn_status, checkIn_comment, created_date, last_modified_date, intt_cd)
VALUES
    (40001, 20000001, 900001, DATE_SUB(NOW(), INTERVAL 10 DAY), 'COMPLETED', '외래 완료 케이스', NOW(), NOW(), @INTT),
    (40002, 20000002, 900002, DATE_SUB(NOW(), INTERVAL 9 DAY),  'COMPLETED', '외래 취소 케이스', NOW(), NOW(), @INTT),
    (40003, 20000003, 900003, DATE_SUB(NOW(), INTERVAL 7 DAY),  'COMPLETED', '입원 완료 케이스', NOW(), NOW(), @INTT),
    (40004, 20000004, 900003, DATE_SUB(NOW(), INTERVAL 6 DAY),  'COMPLETED', '입원 진행 케이스', NOW(), NOW(), @INTT),
    (40005, 20000005, 900004, DATE_SUB(NOW(), INTERVAL 5 DAY),  'COMPLETED', '응급 완료 케이스', NOW(), NOW(), @INTT),
    (40006, 20000006, 900004, DATE_SUB(NOW(), INTERVAL 4 DAY),  'COMPLETED', '응급 취소 케이스', NOW(), NOW(), @INTT);

-- 진료 공통 헤더 시드
INSERT IGNORE INTO treatments
    (treatment_id, checkIn_id, patient_no, treatment_doc, department_id, treatment_type, treatment_status, treatment_date, treatment_start_time, treatment_end_time, treatment_comment, treatment_dept, created_date, last_modified_date, intt_cd)
VALUES
    (50001, 40001, 20000001, 900001, 101, 'OUTPATIENT', 'COMPLETED', DATE_SUB(NOW(), INTERVAL 10 DAY), DATE_SUB(NOW(), INTERVAL 10 DAY), DATE_SUB(NOW(), INTERVAL 10 DAY), '상기도 감염 외래 진료 완료', '내과', NOW(), NOW(), @INTT),
    (50002, 40002, 20000002, 900002, 104, 'OUTPATIENT', 'CANCELLED', DATE_SUB(NOW(), INTERVAL 9 DAY),  DATE_SUB(NOW(), INTERVAL 9 DAY),  DATE_SUB(NOW(), INTERVAL 9 DAY),  '예약 변경으로 외래 취소', '가정의학과', NOW(), NOW(), @INTT),
    (50003, 40003, 20000003, 900003, 102, 'INPATIENT',  'COMPLETED', DATE_SUB(NOW(), INTERVAL 7 DAY),  DATE_SUB(NOW(), INTERVAL 7 DAY),  DATE_SUB(NOW(), INTERVAL 5 DAY),  '수술 후 입원치료 완료', '외과', NOW(), NOW(), @INTT),
    (50004, 40004, 20000004, 900003, 102, 'INPATIENT',  'IN_PROGRESS', DATE_SUB(NOW(), INTERVAL 6 DAY), DATE_SUB(NOW(), INTERVAL 6 DAY), NULL, '입원 관찰 중', '외과', NOW(), NOW(), @INTT),
    (50005, 40005, 20000005, 900004, 103, 'EMERGENCY',  'COMPLETED', DATE_SUB(NOW(), INTERVAL 5 DAY),  DATE_SUB(NOW(), INTERVAL 5 DAY),  DATE_SUB(NOW(), INTERVAL 5 DAY), '응급 처치 후 귀가', '응급의학과', NOW(), NOW(), @INTT),
    (50006, 40006, 20000006, 900004, 103, 'EMERGENCY',  'CANCELLED', DATE_SUB(NOW(), INTERVAL 4 DAY),  DATE_SUB(NOW(), INTERVAL 4 DAY),  DATE_SUB(NOW(), INTERVAL 4 DAY), '환자 요청으로 응급진료 취소', '응급의학과', NOW(), NOW(), @INTT);

-- 외래 진료 상세 시드
INSERT IGNORE INTO Out_Treatments
    (treatment_id, checkIn_id, treatment_status, pre_treatment_id, treatment_comment, created_date, last_modified_date, intt_cd)
VALUES
    (50001, 40001, 'COMPLETED', NULL, '외래 종료', NOW(), NOW(), @INTT),
    (50002, 40002, 'CANCELLED', NULL, '외래 취소', NOW(), NOW(), @INTT);

-- 입원 진료 상세 시드
INSERT IGNORE INTO In_Treatments
    (treatment_id, checkIn_id, treatment_status, created_date, last_modified_date, intt_cd)
VALUES
    (50003, 40003, 'COMPLETED', NOW(), NOW(), @INTT),
    (50004, 40004, 'IN_PROGRESS', NOW(), NOW(), @INTT);

-- 응급 진료 상세 시드
INSERT IGNORE INTO Emergency_Treatments
    (treatment_id, checkIn_id, treatment_status, created_date, last_modified_date, intt_cd)
VALUES
    (50005, 40005, 'COMPLETED', NOW(), NOW(), @INTT),
    (50006, 40006, 'CANCELLED', NOW(), NOW(), @INTT);

-- 의사 진료 세션 시드
INSERT IGNORE INTO doctor_treatment
    (doctorTreatment_id, patient_no, user_id, doctorTreatment_starttime, doctorTreatment_endtime, created_date, last_modified_date, intt_cd)
VALUES
    (60001, 20000001, 900001, DATE_SUB(NOW(), INTERVAL 10 DAY), DATE_SUB(NOW(), INTERVAL 10 DAY), NOW(), NOW(), @INTT),
    (60002, 20000003, 900003, DATE_SUB(NOW(), INTERVAL 7 DAY),  DATE_SUB(NOW(), INTERVAL 6 DAY),  NOW(), NOW(), @INTT),
    (60003, 20000005, 900004, DATE_SUB(NOW(), INTERVAL 5 DAY),  DATE_SUB(NOW(), INTERVAL 5 DAY),  NOW(), NOW(), @INTT);

-- 처방 헤더 시드
INSERT IGNORE INTO Prescription
    (prescription_id, treatment_id, patient_no, prescription_doc, prescription_date, prescription_status, prescription_type, prescription_memo, created_date, last_modified_date, intt_cd)
VALUES
    (70001, 50001, 20000001, 900001, DATE_SUB(NOW(), INTERVAL 10 DAY), 'DISPENSED', 'OUTPATIENT', NULL, NOW(), NOW(), @INTT),
    (70002, 50003, 20000003, 900003, DATE_SUB(NOW(), INTERVAL 7 DAY),  'DISPENSED', 'INPATIENT',  '수술 후 항생제', NOW(), NOW(), @INTT),
    (70003, 50006, 20000006, 900004, DATE_SUB(NOW(), INTERVAL 4 DAY),  'CANCELLED', 'EMERGENCY',  '진료 취소로 처방 취소', NOW(), NOW(), @INTT);

-- 처방 상세 항목 시드
INSERT IGNORE INTO Prescription_Item
    (prescription_item_id, prescription_id, drug_code, drug_name, dosage, dose, frequency, days, total_quantity, unit, special_note, created_date, last_modified_date, intt_cd)
VALUES
    (80001, 70001, 'D-ACET-500', '아세트아미노펜', '식후 30분', '500mg', 3, 3, 9, '정', NULL, NOW(), NOW(), @INTT),
    (80002, 70001, 'D-AMBRO-30', '암브록솔', '식후', '30mg', 3, 3, 9, '정', NULL, NOW(), NOW(), @INTT),
    (80003, 70002, 'D-CEFA-1G',  '세파계 항생제', '8시간 간격', '1g', 3, 5, 15, 'vial', '신장기능 확인', NOW(), NOW(), @INTT),
    (80004, 70003, 'D-NS-500',   '생리식염수', '필요시', '500mL', 1, 1, 1, 'bag', '취소 건', NOW(), NOW(), @INTT);

-- 진단서 발급 시드
INSERT IGNORE INTO diagnosis_certificate
    (certificate_id, certificate_number, patient_id, doctor_id, kcd_code_id, diagnosis_name, diagnosis_date, clinical_findings, purpose, issued_at, status, created_date, last_modified_date, intt_cd)
VALUES
    (90001, 'CERT-2026-0001', 20000001, 900001, 1001, '급성 비인두염', DATE_SUB(CURDATE(), INTERVAL 10 DAY), '인후 발적, 기침', '회사 제출용', DATE_SUB(NOW(), INTERVAL 10 DAY), 'ISSUED', NOW(), NOW(), @INTT),
    (90002, 'CERT-2026-0002', 20000003, 900003, 1002, '요골 원위부 골절', DATE_SUB(CURDATE(), INTERVAL 7 DAY),  '수술 후 경과 양호', '보험 청구용', DATE_SUB(NOW(), INTERVAL 7 DAY), 'ISSUED', NOW(), NOW(), @INTT);

/* =====================================================================
 3. 검사/건강/통계 영역
 ===================================================================== */

-- 검사 마스터 시드
INSERT IGNORE INTO examination
    (examination_id, equipment_id, examination_name, examination_type, examination_constraints, examination_location, examination_price, created_date, last_modified_date, intt_cd)
VALUES
    (11001, 3001, '흉부 X-ray', 'IMAGING', '임산부 주의', '영상의학과 1실', 45000, NOW(), NOW(), @INTT),
    (11002, 3002, '복부 초음파', 'ULTRASOUND', '금식 8시간', '영상의학과 2실', 70000, NOW(), NOW(), @INTT),
    (11003, 3003, 'CBC 혈액검사', 'LAB', '특이사항 없음', '진단검사의학과', 15000, NOW(), NOW(), @INTT);

-- 검사 일정 시드
INSERT IGNORE INTO examination_schedule
    (examination_schedule_id, examination_id, patient_no, treatment_id, user_id, examination_date, created_date, last_modified_date, intt_cd)
VALUES
    (12001, 11001, 20000001, 50001, 910001, DATE_SUB(CURDATE(), INTERVAL 10 DAY), NOW(), NOW(), @INTT),
    (12002, 11002, 20000003, 50003, 910002, DATE_SUB(CURDATE(), INTERVAL 7 DAY),  NOW(), NOW(), @INTT),
    (12003, 11003, 20000005, 50005, 910003, DATE_SUB(CURDATE(), INTERVAL 5 DAY),  NOW(), NOW(), @INTT);

-- 검사 결과 시드
INSERT IGNORE INTO examination_result
    (examination_result_id, examination_id, patient_no, treatment_id, examination_date, examination_result, examination_normal, examination_notes, created_date, last_modified_date, intt_cd)
VALUES
    (13001, 11001, 20000001, 50001, DATE_SUB(CURDATE(), INTERVAL 10 DAY), '특이 소견 없음', 1, '정상', NOW(), NOW(), @INTT),
    (13002, 11002, 20000003, 50003, DATE_SUB(CURDATE(), INTERVAL 7 DAY),  '충수염 의심 소견', 0, '추가 CT 권고', NOW(), NOW(), @INTT),
    (13003, 11003, 20000005, 50005, DATE_SUB(CURDATE(), INTERVAL 5 DAY),  'WBC 상승', 0, '염증 가능성', NOW(), NOW(), @INTT);

-- 검사 일지 시드
INSERT IGNORE INTO examination_journal
    (examination_journal_id, examination_id, patient_no, treatment_id, user_id, equipment_id, examination_time, examination_equipment_usage, examination_notes, created_date, last_modified_date, intt_cd)
VALUES
    (14001, 11001, 20000001, 50001, 910001, 3001, DATE_SUB(NOW(), INTERVAL 10 DAY), 1, '촬영 정상 종료', NOW(), NOW(), @INTT),
    (14002, 11002, 20000003, 50003, 910002, 3002, DATE_SUB(NOW(), INTERVAL 7 DAY),  1, '통증으로 중간 휴식', NOW(), NOW(), @INTT),
    (14003, 11003, 20000005, 50005, 910003, 3003, DATE_SUB(NOW(), INTERVAL 5 DAY),  1, '채혈 완료', NOW(), NOW(), @INTT);

-- 혈액은행 시드
INSERT IGNORE INTO blood_bank
    (blood_bank_id, examination_id, patient_no, treatment_id, user_id, examination_time, blood_type, created_date, last_modified_date, intt_cd)
VALUES
    (15001, 11003, 20000005, 50005, 910003, DATE_SUB(NOW(), INTERVAL 5 DAY), 'O+', NOW(), NOW(), @INTT),
    (15002, 11003, 20000006, 50006, 910003, DATE_SUB(NOW(), INTERVAL 4 DAY), 'A+', NOW(), NOW(), @INTT);

-- 건강검진 기관 시드
INSERT IGNORE INTO health_checkup_institution
    (institution_id, region_code, region_name, institution_name, institution_type, address, sido, sigungu, latitude, longitude, phone_number, is_active, data_source, data_date, created_date, last_modified_date, intt_cd)
VALUES
    (16001, '11', '서울', '서울중앙검진센터', '검진센터', '서울 중구 세종대로 1', '서울', '중구', 37.5665, 126.9780, '02-1234-5678', 1, 'MANUAL_SEED', CURDATE(), NOW(), NOW(), @INTT),
    (16002, '41', '경기', '분당건강검진의원', '의원', '경기 성남시 분당구 판교로 10', '경기', '성남시', 37.3826, 127.1187, '031-123-4567', 1, 'MANUAL_SEED', CURDATE(), NOW(), NOW(), @INTT);

-- 장애 정보 시드
INSERT IGNORE INTO disability
    (disability_id, patient_no, disability_grade, disability_type, assistive_device_YN, disability_device_type, created_date, last_modified_date, intt_cd)
VALUES
    (17001, 20000002, '4급', '청각', 'Y', '보청기', NOW(), NOW(), @INTT),
    (17002, 20000006, '3급', '지체', 'Y', '휠체어', NOW(), NOW(), @INTT);

-- 장애인 돌봄 기관 시드
INSERT IGNORE INTO disability_care_institution
    (institution_id, institution_type, institution_name, service_type, address, sido, sigungu, latitude, longitude, is_active, created_date, last_modified_date, intt_cd)
VALUES
    (18001, '복지관', '강남장애인복지관', '재활', '서울 강남구 테헤란로 100', '서울', '강남구', 37.5013, 127.0396, 1, NOW(), NOW(), @INTT),
    (18002, '센터', '성남주간보호센터', '주간보호', '경기 성남시 수정구 수정로 20', '경기', '성남시', 37.4419, 127.1376, 1, NOW(), NOW(), @INTT);

-- 입원 통계 시드
INSERT IGNORE INTO inpatient_statistics
    (statistics_id, statistics_year, institution_type, region_code, region_name, visit_days, benefit_days, medical_fee, benefit_fee, data_source, data_date, created_date, last_modified_date, intt_cd)
VALUES
    (19001, '2025', '종합병원', '11', '서울', 18200, 14800, 980000000, 740000000, 'MANUAL_SEED', '2025-12-31', NOW(), NOW(), @INTT),
    (19002, '2025', '병원',     '41', '경기', 14600, 12000, 730000000, 560000000, 'MANUAL_SEED', '2025-12-31', NOW(), NOW(), @INTT);

-- 진료과 통계 시드
INSERT IGNORE INTO treatment_department_statistics
    (statistics_id, statistics_year, region_code, region_name, department_name, patient_count, treatment_count, medical_fee, benefit_fee, data_source, data_date, created_date, last_modified_date, intt_cd)
VALUES
    (20001, '2025', '11', '서울', '내과',      1200, 2600, 420000000, 310000000, 'MANUAL_SEED', '2025-12-31', NOW(), NOW(), @INTT),
    (20002, '2025', '11', '서울', '외과',       860, 1750, 390000000, 280000000, 'MANUAL_SEED', '2025-12-31', NOW(), NOW(), @INTT),
    (20003, '2025', '11', '서울', '응급의학과', 540, 1320, 330000000, 245000000, 'MANUAL_SEED', '2025-12-31', NOW(), NOW(), @INTT);

COMMIT;
