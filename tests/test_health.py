from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health_status_code():
    response = client.get("/health")
    assert response.status_code == 200


def test_health_json_body():
    response = client.get("/health")
    assert response.json() == {"status": "ok"}
