from app.infrastructure.repositories.etl_sync_repository import EtlSyncRepository


class EtlApplicationService:

    def __init__(self, repository: EtlSyncRepository) -> None:
        self._repository = repository

    def generate_wearable_slot(self) -> dict:
        return self._repository.generate_wearable_slot()

    def sync_postgres_to_mysql(self) -> dict:
        return self._repository.sync_postgres_to_mysql()

    def sync_mysql_treatments_to_postgres(self) -> dict:
        return self._repository.sync_mysql_treatments_to_postgres()
