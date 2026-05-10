from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app, settings


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_list_missions():
    response = client.get("/missions")
    assert response.status_code == 200
    mission_ids = [mission["mission_id"] for mission in response.json()["missions"]]
    assert "demo_forward_stop" in mission_ids


def test_get_mission():
    response = client.get("/missions/demo_forward_stop")
    assert response.status_code == 200
    data = response.json()
    assert data["mission_id"] == "demo_forward_stop"
    assert len(data["steps"]) > 0


def test_latest_report_not_found(tmp_path: Path):
    original_report_path = settings.latest_report_path
    settings.latest_report_path = tmp_path / "missing.json"
    try:
        response = client.get("/reports/latest")
        assert response.status_code == 404
    finally:
        settings.latest_report_path = original_report_path

