from fastapi import FastAPI
from starlette.testclient import TestClient

from app.presentation.routers import health


def test_health_endpoint_ok():
    app = FastAPI()
    app.include_router(health.router)
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
