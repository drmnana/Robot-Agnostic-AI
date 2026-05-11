from pathlib import Path

from fastapi import HTTPException
from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app, settings


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_root_redirects_to_dashboard():
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/dashboard/"


def test_dashboard_is_served():
    response = client.get("/dashboard/")

    assert response.status_code == 200
    assert "ORIMUS Operator Dashboard" in response.text


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


def test_control_mission_start(monkeypatch):
    calls = []

    def fake_send_mission_command(settings, mission_id, command_type):
        calls.append((mission_id, command_type))
        return {
            "status": "accepted",
            "mission_id": mission_id,
            "command_type": command_type,
        }

    monkeypatch.setattr(main_module, "send_mission_command", fake_send_mission_command)

    response = client.post("/missions/demo_forward_stop/start")

    assert response.status_code == 200
    assert response.json() == {
        "status": "accepted",
        "mission_id": "demo_forward_stop",
        "command_type": "start",
    }
    assert calls == [("demo_forward_stop", "start")]


def test_control_mission_reset(monkeypatch):
    calls = []

    def fake_send_mission_command(settings, mission_id, command_type):
        calls.append((mission_id, command_type))
        return {
            "status": "accepted",
            "mission_id": mission_id,
            "command_type": command_type,
        }

    monkeypatch.setattr(main_module, "send_mission_command", fake_send_mission_command)

    response = client.post("/missions/demo_forward_stop/reset")

    assert response.status_code == 200
    assert response.json()["command_type"] == "reset"
    assert calls == [("demo_forward_stop", "reset")]


def test_control_mission_rejects_unknown_command():
    response = client.post("/missions/demo_forward_stop/reboot")

    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported mission command"


def test_control_mission_reports_bridge_unavailable(monkeypatch):
    def fake_send_mission_command(settings, mission_id, command_type):
        raise HTTPException(status_code=503, detail="Mission API bridge unavailable")

    monkeypatch.setattr(main_module, "send_mission_command", fake_send_mission_command)

    response = client.post("/missions/demo_forward_stop/start")

    assert response.status_code == 503
    assert response.json()["detail"] == "Mission API bridge unavailable"


def test_get_runtime_state(monkeypatch):
    calls = []

    def fake_get_runtime_resource(settings, resource):
        calls.append(resource)
        return {
            "bridge": {"connected": True},
            "mission": {"state": "running"},
            "robot": {"connected": True},
            "payload": None,
            "perception": None,
            "safety": None,
            "events": [],
        }

    monkeypatch.setattr(main_module, "get_runtime_resource", fake_get_runtime_resource)

    response = client.get("/runtime/state")

    assert response.status_code == 200
    assert response.json()["bridge"]["connected"] is True
    assert response.json()["mission"]["state"] == "running"
    assert calls == ["state"]


def test_get_runtime_rejects_unknown_resource():
    response = client.get("/runtime/navigation")

    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported runtime resource"


def test_latest_report_not_found(tmp_path: Path):
    original_report_path = settings.latest_report_path
    settings.latest_report_path = tmp_path / "missing.json"
    try:
        response = client.get("/reports/latest")
        assert response.status_code == 404
    finally:
        settings.latest_report_path = original_report_path
