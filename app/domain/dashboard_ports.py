from typing import Protocol

from app.domain.dashboard_schema import DashboardSnapshot, TableDetailSnapshot, TableStatsSnapshot


class DashboardStatsRepositoryPort(Protocol):
    def fetch_snapshot(self) -> DashboardSnapshot:
        ...

    def fetch_table_stats(self) -> TableStatsSnapshot:
        ...

    def fetch_table_detail(self, table_name: str) -> TableDetailSnapshot:
        ...
