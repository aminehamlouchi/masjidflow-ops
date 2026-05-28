from fastapi.testclient import TestClient

from app.database import init_db
from app.main import app


def _client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setenv("MASJIDFLOW_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("MASJIDFLOW_SECRET", "test-secret")
    init_db(seed=True)
    return TestClient(app)


def _token(client: TestClient) -> str:
    response = client.post(
        "/auth/login",
        json={"email": "admin@masjidflow.local", "password": "demo-admin"},
    )
    assert response.status_code == 200
    return response.json()["token"]


def test_login_and_list_events(tmp_path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    token = _token(client)
    response = client.get("/events", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    events = response.json()
    assert len(events) >= 3
    assert events[0]["open_slots"] >= 0


def test_staffing_suggestions_include_open_shift(tmp_path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    token = _token(client)
    response = client.post("/events/1/suggestions", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    suggestions = response.json()
    assert suggestions
    assert any(item["open_slots"] > 0 for item in suggestions)
