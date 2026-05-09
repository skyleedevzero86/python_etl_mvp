from pydantic import BaseModel, Field


class GaugeBlock(BaseModel):
    current: int = Field(description="현재 누적값")
    max_value: int = Field(description="게이지 최대값")
    title: str = Field(default="목표 진행률", description="게이지 제목")


class TimelineBlock(BaseModel):
    labels: list[str] = Field(description="시계열 라벨 목록")
    values: list[float] = Field(description="시계열 값 목록")


class PieSlice(BaseModel):
    name: str = Field(description="비중 구분 이름")
    value: float = Field(description="비중 값")


class LeagueRow(BaseModel):
    name: str = Field(description="진료과 이름")
    actual: float = Field(description="실적 값")
    target: float = Field(description="목표 값")
    spark: list[float] = Field(default_factory=list, description="최근 추이 값")


class ProductionBlock(BaseModel):
    categories: list[str] = Field(description="막대 차트 카테고리")
    values: list[float] = Field(description="막대 차트 값")


class KpiBlock(BaseModel):
    actual: float = Field(description="현재 KPI 값")
    target: float = Field(description="목표 KPI 값")
    growth_pct: float = Field(description="증감률 퍼센트")
    label: str = Field(default="연간 검진·진료 과금 규모, 추정", description="KPI 설명 라벨")


class DashboardSnapshot(BaseModel):
    gauge: GaugeBlock = Field(description="게이지 블록")
    timeline: TimelineBlock = Field(description="월별 추이 블록")
    pie_sales: list[PieSlice] = Field(description="진료유형 비중")
    league_table: list[LeagueRow] = Field(description="상위 진료과 표")
    production: ProductionBlock = Field(description="진료과 생산량")
    kpi: KpiBlock = Field(description="KPI 블록")


class DailyCount(BaseModel):
    day: str = Field(description="날짜 yyyy-mm-dd")
    count: int = Field(description="해당 일자 건수")


class TableStatsRow(BaseModel):
    table_name: str = Field(description="테이블명")
    total_count: int = Field(description="전체 건수")
    today_count: int = Field(description="오늘 생성 건수")
    last_created_at: str | None = Field(default=None, description="마지막 생성 시각")


class TableStatsSnapshot(BaseModel):
    rows: list[TableStatsRow] = Field(description="테이블별 통계 목록")


class TableDetailSnapshot(BaseModel):
    table_name: str = Field(description="테이블명")
    total_count: int = Field(description="전체 건수")
    today_count: int = Field(description="오늘 생성 건수")
    last_created_at: str | None = Field(default=None, description="마지막 생성 시각")
    recent_daily: list[DailyCount] = Field(default_factory=list, description="최근 14일 생성 추이")
    columns: list[str] = Field(default_factory=list, description="표 컬럼 목록")
    rows: list[dict] = Field(default_factory=list, description="최근 레코드 목록")


class PgTableCountRow(BaseModel):
    table_key: str = Field(description="논리 키")
    sql_name: str = Field(description="스키마 테이블명")
    label_kr: str = Field(description="한글 설명")
    total_count: int = Field(description="전체 건수 (-1 이면 조회 실패)")


class PgEtlState(BaseModel):
    wearable_round_robin_cursor: int | None = Field(default=None, description="웨어러블 라운드로빈 커서")
    wearable_updated_at: str | None = Field(default=None, description="커서 갱신 시각")


class PgCategoryCount(BaseModel):
    category: str = Field(description="진료 이벤트 유형 코드")
    label_kr: str = Field(description="진료 이벤트 유형 한글 라벨")
    count: int = Field(description="건수")


class PgVitalsAggregate(BaseModel):
    total_vitals: int = Field(default=0, description="생체 측정 총건수")
    today_vitals: int = Field(default=0, description="금일 측정 건수")
    pending_mysql_sync: int = Field(default=0, description="MySQL 미동기화 생체 건수")
    pending_daily_mysql_sync: int = Field(default=0, description="MySQL 미동기화 일별 웰니스 행 수")
    avg_heart_rate_24h: float | None = Field(default=None, description="최근 24시간 평균 심박")


class PgDashboardSnapshot(BaseModel):
    connected: bool = Field(description="PostgreSQL 연결 여부")
    message: str | None = Field(default=None, description="연결 불가 시 안내")
    generated_at: str = Field(description="집계 시각")
    include_mysql_treatment_id_column: bool = Field(
        default=False,
        description="최근 진료 이벤트에 MySQL 진료 ID가 하나라도 있으면 true",
    )
    table_counts: list[PgTableCountRow] = Field(default_factory=list, description="테이블별 건수")
    etl: PgEtlState | None = Field(default=None, description="ETL 커서")
    clinical_by_category: list[PgCategoryCount] = Field(
        default_factory=list,
        description="patient_clinical_event 유형별 건수",
    )
    vitals_aggregate: PgVitalsAggregate = Field(default_factory=PgVitalsAggregate)
    recent_vitals: list[dict] = Field(default_factory=list, description="최근 생체 측정")
    recent_clinical_events: list[dict] = Field(default_factory=list, description="최근 진료 이벤트")
    daily_wellness_sample_rows: list[dict] = Field(
        default_factory=list,
        description="일별 웰니스 최근 샘플",
    )
