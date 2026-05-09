from pydantic import BaseModel, Field


class GaugeBlock(BaseModel):
    current: int
    max_value: int
    title: str = "목표 진행률"


class TimelineBlock(BaseModel):
    labels: list[str]
    values: list[float]


class PieSlice(BaseModel):
    name: str
    value: float


class LeagueRow(BaseModel):
    name: str
    actual: float
    target: float
    spark: list[float] = Field(default_factory=list)


class ProductionBlock(BaseModel):
    categories: list[str]
    values: list[float]


class KpiBlock(BaseModel):
    actual: float
    target: float
    growth_pct: float
    label: str = "연간 검진·진료 과금 규모, 추정"


class DashboardSnapshot(BaseModel):
    gauge: GaugeBlock
    timeline: TimelineBlock
    pie_sales: list[PieSlice]
    league_table: list[LeagueRow]
    production: ProductionBlock
    kpi: KpiBlock


class DailyCount(BaseModel):
    day: str
    count: int


class TableStatsRow(BaseModel):
    table_name: str
    total_count: int
    today_count: int
    last_created_at: str | None = None


class TableStatsSnapshot(BaseModel):
    rows: list[TableStatsRow]


class TableDetailSnapshot(BaseModel):
    table_name: str
    total_count: int
    today_count: int
    last_created_at: str | None = None
    recent_daily: list[DailyCount] = Field(default_factory=list)
    columns: list[str] = Field(default_factory=list)
    rows: list[dict] = Field(default_factory=list)
