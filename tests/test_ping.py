from starlette.testclient import TestClient

from example_app.main import app

client = TestClient(app)


def test_ping():
    response = client.get("/ping")
    assert response.status_code == 200
    data = response.json()
    assert data["ping"] == "pong!"


def test_app_version():
    response = client.get("/ping")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == app.VERSION
