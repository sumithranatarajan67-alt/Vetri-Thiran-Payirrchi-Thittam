from fastapi.testclient import TestClient

from app.main import app


def test_health():

    with TestClient(app) as client:

        response = client.get("/health")

        assert response.status_code == 200

        assert response.json() == {
            "status": "ok"
        }


def test_homepage():

    with TestClient(app) as client:

        response = client.get("/")

        assert response.status_code == 200

        assert "FitBuddy" in response.text