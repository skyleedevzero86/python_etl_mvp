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
