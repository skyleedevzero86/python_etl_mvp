from app.domain.dashboard_schema import DashboardSnapshot, TableDetailSnapshot, TableStatsSnapshot
from app.domain.dashboard_ports import DashboardStatsRepositoryPort


class DashboardApplicationService:
    def __init__(self, repository: DashboardStatsRepositoryPort) -> None:
        self._repository = repository

    def get_snapshot(self) -> DashboardSnapshot:
        return self._repository.fetch_snapshot()

    def get_table_stats(self) -> TableStatsSnapshot:
        return self._repository.fetch_table_stats()

    def get_table_detail(self, table_name: str) -> TableDetailSnapshot:
        return self._repository.fetch_table_detail(table_name)
