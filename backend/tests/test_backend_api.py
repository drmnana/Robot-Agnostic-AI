from pathlib import Path
import json
import sqlite3

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
    assert "Mission History" in response.text


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
    assert data["sector"] == "training-yard-alpha"
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


def test_list_reports_from_database(tmp_path: Path):
    original_database_path = settings.report_database_path
    settings.report_database_path = create_report_database(tmp_path)
    try:
        response = client.get("/reports")
        assert response.status_code == 200
        reports = response.json()["reports"]
        assert len(reports) == 2
        assert reports[0]["id"] == "report-002"
        assert reports[1]["id"] == "report-001"
        assert reports[1]["outcome"] == "completed"
        assert reports[1]["content_hash"] == "abc123"
    finally:
        settings.report_database_path = original_database_path


def test_list_reports_filters_by_mission_metadata_and_events(tmp_path: Path):
    original_database_path = settings.report_database_path
    settings.report_database_path = create_report_database(tmp_path)
    try:
        expectations = [
            ("/reports?outcome=completed", ["report-001"]),
            ("/reports?mission_id=control", ["report-002"]),
            ("/reports?sector=sector-alpha", ["report-001"]),
            ("/reports?date_from=250", ["report-002"]),
            ("/reports?date_to=250", ["report-001"]),
            ("/reports?perception_event_type=person_detected", ["report-001"]),
            ("/reports?has_safety_event=true", ["report-002"]),
            ("/reports?has_safety_event=false", ["report-001"]),
            ("/reports?command_blocked=true", ["report-002"]),
        ]

        for url, expected_ids in expectations:
            response = client.get(url)
            assert response.status_code == 200
            assert [report["id"] for report in response.json()["reports"]] == expected_ids
    finally:
        settings.report_database_path = original_database_path


def test_get_report_detail_from_database(tmp_path: Path):
    original_database_path = settings.report_database_path
    settings.report_database_path = create_report_database(tmp_path)
    try:
        response = client.get("/reports/report-001")
        assert response.status_code == 200
        assert response.json()["report_id"] == "report-001"
        assert response.json()["content_hash"] == "abc123"
    finally:
        settings.report_database_path = original_database_path


def test_get_report_detail_not_found(tmp_path: Path):
    original_database_path = settings.report_database_path
    settings.report_database_path = create_report_database(tmp_path)
    try:
        response = client.get("/reports/missing-report")
        assert response.status_code == 404
    finally:
        settings.report_database_path = original_database_path


def create_report_database(tmp_path: Path) -> Path:
    database_path = tmp_path / "orimus.db"
    report_001 = {
        "report_id": "report-001",
        "content_hash": "abc123",
        "mission": {
            "mission_id": "demo_forward_stop",
            "name": "Demo Forward Stop",
            "state": "completed",
            "sector": "sector-alpha",
        },
    }
    report_002 = {
        "report_id": "report-002",
        "content_hash": "def456",
        "mission": {
            "mission_id": "control_test",
            "name": "Control Test Mission",
            "state": "canceled",
            "sector": "sector-bravo",
        },
    }
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE missions (
                id TEXT PRIMARY KEY,
                mission_id TEXT NOT NULL,
                name TEXT NOT NULL,
                sector TEXT,
                outcome TEXT NOT NULL,
                started_at_sec INTEGER,
                started_at_nanosec INTEGER,
                ended_at_sec INTEGER,
                ended_at_nanosec INTEGER,
                content_hash TEXT NOT NULL,
                report_json TEXT NOT NULL,
                mission_event_count INTEGER NOT NULL,
                robot_command_count INTEGER NOT NULL,
                safety_event_count INTEGER NOT NULL,
                perception_event_count INTEGER NOT NULL,
                payload_result_count INTEGER NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE perception_events (
                id TEXT PRIMARY KEY,
                report_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                source TEXT,
                confidence REAL,
                stamp_sec INTEGER,
                stamp_nanosec INTEGER,
                payload_json TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE safety_events (
                id TEXT PRIMARY KEY,
                report_id TEXT NOT NULL,
                rule TEXT NOT NULL,
                severity TEXT NOT NULL,
                command_blocked INTEGER NOT NULL,
                stamp_sec INTEGER,
                stamp_nanosec INTEGER,
                payload_json TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO missions (
                id, mission_id, name, sector, outcome,
                started_at_sec, started_at_nanosec, ended_at_sec, ended_at_nanosec,
                content_hash, report_json, mission_event_count, robot_command_count,
                safety_event_count, perception_event_count, payload_result_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "report-001",
                "demo_forward_stop",
                "Demo Forward Stop",
                "sector-alpha",
                "completed",
                100,
                0,
                200,
                0,
                "abc123",
                json.dumps(report_001),
                3,
                2,
                0,
                1,
                1,
            ),
        )
        connection.execute(
            """
            INSERT INTO missions (
                id, mission_id, name, sector, outcome,
                started_at_sec, started_at_nanosec, ended_at_sec, ended_at_nanosec,
                content_hash, report_json, mission_event_count, robot_command_count,
                safety_event_count, perception_event_count, payload_result_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "report-002",
                "control_test",
                "Control Test Mission",
                "sector-bravo",
                "canceled",
                250,
                0,
                300,
                0,
                "def456",
                json.dumps(report_002),
                2,
                1,
                1,
                0,
                0,
            ),
        )
        connection.execute(
            """
            INSERT INTO perception_events (
                id, report_id, event_type, source, confidence,
                stamp_sec, stamp_nanosec, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "perception-001",
                "report-001",
                "person_detected",
                "mock_inspection_camera",
                0.92,
                150,
                0,
                "{}",
            ),
        )
        connection.execute(
            """
            INSERT INTO safety_events (
                id, report_id, rule, severity, command_blocked,
                stamp_sec, stamp_nanosec, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "safety-001",
                "report-002",
                "operator_cancel",
                "warning",
                1,
                280,
                0,
                "{}",
            ),
        )
    return database_path
