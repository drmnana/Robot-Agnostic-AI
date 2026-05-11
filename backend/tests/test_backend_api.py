from pathlib import Path
import json
import sqlite3
import subprocess
import sys
import inspect

from fastapi import HTTPException
from fastapi.testclient import TestClient

import app.main as main_module
from app.backend_audit import BackendAuditStore
from app.evidence_package import hash_evidence_package, hash_mission_report
from app.evidence_verifier import (
    EXIT_HASH_MISMATCH,
    EXIT_SCHEMA_MISMATCH,
    EXIT_SEMANTIC_FAILURE,
    EXIT_VALID,
    verify_evidence_package,
)
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
    assert "API Audit" in response.text
    assert 'id="audit-filter-decision"' in response.text
    assert 'id="audit-list"' in response.text


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

    def fake_send_mission_command(settings, mission_id, command_type, operator_id):
        calls.append((mission_id, command_type, operator_id))
        return {
            "status": "accepted",
            "mission_id": mission_id,
            "command_type": command_type,
            "operator_id": operator_id,
        }

    monkeypatch.setattr(main_module, "send_mission_command", fake_send_mission_command)

    response = client.post(
        "/missions/demo_forward_stop/start",
        headers={"X-ORIMUS-Operator": "operator-demo"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "accepted",
        "mission_id": "demo_forward_stop",
        "command_type": "start",
        "operator_id": "operator-demo",
    }
    assert calls == [("demo_forward_stop", "start", "operator-demo")]


def test_control_mission_reset(monkeypatch):
    calls = []

    def fake_send_mission_command(settings, mission_id, command_type, operator_id):
        calls.append((mission_id, command_type, operator_id))
        return {
            "status": "accepted",
            "mission_id": mission_id,
            "command_type": command_type,
            "operator_id": operator_id,
        }

    monkeypatch.setattr(main_module, "send_mission_command", fake_send_mission_command)

    response = client.post(
        "/missions/demo_forward_stop/reset",
        headers={"X-ORIMUS-Operator": "operator-demo"},
    )

    assert response.status_code == 200
    assert response.json()["command_type"] == "reset"
    assert response.json()["operator_id"] == "operator-demo"
    assert calls == [("demo_forward_stop", "reset", "operator-demo")]


def test_control_mission_allows_anonymous_pause(monkeypatch):
    calls = []

    def fake_send_mission_command(settings, mission_id, command_type, operator_id):
        calls.append((mission_id, command_type, operator_id))
        return {
            "status": "accepted",
            "mission_id": mission_id,
            "command_type": command_type,
            "operator_id": operator_id,
        }

    monkeypatch.setattr(main_module, "send_mission_command", fake_send_mission_command)

    response = client.post("/missions/demo_forward_stop/pause")

    assert response.status_code == 200
    assert response.json()["operator_id"] == "anonymous"
    assert calls == [("demo_forward_stop", "pause", "anonymous")]


def test_control_mission_denies_anonymous_start(monkeypatch):
    calls = []

    def fake_send_mission_command(settings, mission_id, command_type, operator_id):
        calls.append((mission_id, command_type, operator_id))
        return {}

    monkeypatch.setattr(main_module, "send_mission_command", fake_send_mission_command)

    response = client.post("/missions/demo_forward_stop/start")

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Mission command 'start' denied by operator policy for operator 'anonymous'"
    )
    assert calls == []


def test_control_mission_denies_operator_without_command_permission(monkeypatch):
    calls = []

    def fake_send_mission_command(settings, mission_id, command_type, operator_id):
        calls.append((mission_id, command_type, operator_id))
        return {}

    monkeypatch.setattr(main_module, "send_mission_command", fake_send_mission_command)

    response = client.post(
        "/missions/demo_forward_stop/cancel",
        headers={"X-ORIMUS-Operator": "operator-demo"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Mission command 'cancel' denied by operator policy for operator 'operator-demo'"
    )
    assert calls == []


def test_control_mission_rejects_unknown_command():
    response = client.post("/missions/demo_forward_stop/reboot")

    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported mission command"


def test_control_mission_reports_bridge_unavailable(monkeypatch):
    def fake_send_mission_command(settings, mission_id, command_type, operator_id):
        raise HTTPException(status_code=503, detail="Mission API bridge unavailable")

    monkeypatch.setattr(main_module, "send_mission_command", fake_send_mission_command)

    response = client.post(
        "/missions/demo_forward_stop/start",
        headers={"X-ORIMUS-Operator": "operator-demo"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Mission API bridge unavailable"


def test_allowed_mission_command_is_logged_to_backend_audit(tmp_path: Path, monkeypatch):
    original_database_path = settings.report_database_path
    settings.report_database_path = tmp_path / "orimus.db"

    def fake_send_mission_command(settings, mission_id, command_type, operator_id):
        return {
            "status": "accepted",
            "mission_id": mission_id,
            "command_type": command_type,
            "operator_id": operator_id,
        }

    monkeypatch.setattr(main_module, "send_mission_command", fake_send_mission_command)
    try:
        response = client.post(
            "/missions/demo_forward_stop/start",
            headers={"X-ORIMUS-Operator": "operator-demo"},
        )
        assert response.status_code == 200

        audit_response = client.get("/audit/events?decision=allowed")
        assert audit_response.status_code == 200
        events = audit_response.json()["events"]
        assert len(events) == 1
        assert events[0]["event_type"] == "mission_command"
        assert events[0]["operator_id"] == "operator-demo"
        assert events[0]["decision"] == "allowed"
        assert events[0]["mission_id"] == "demo_forward_stop"
        assert events[0]["command_type"] == "start"
        assert events[0]["reason"] == "operator_policy"
        assert events[0]["retention_class"] == "standard"
        assert events[0]["source_ip"]
    finally:
        settings.report_database_path = original_database_path


def test_denied_mission_command_is_logged_to_backend_audit(tmp_path: Path, monkeypatch):
    original_database_path = settings.report_database_path
    settings.report_database_path = tmp_path / "orimus.db"
    calls = []

    def fake_send_mission_command(settings, mission_id, command_type, operator_id):
        calls.append((mission_id, command_type, operator_id))
        return {}

    monkeypatch.setattr(main_module, "send_mission_command", fake_send_mission_command)
    try:
        response = client.post("/missions/demo_forward_stop/start")
        assert response.status_code == 403
        assert calls == []

        events = client.get("/audit/events?decision=denied").json()["events"]
        assert len(events) == 1
        assert events[0]["operator_id"] == "anonymous"
        assert events[0]["decision"] == "denied"
        assert events[0]["command_type"] == "start"
        assert events[0]["reason"] == "operator_policy"
    finally:
        settings.report_database_path = original_database_path


def test_backend_audit_filters_work(tmp_path: Path, monkeypatch):
    original_database_path = settings.report_database_path
    settings.report_database_path = tmp_path / "orimus.db"

    def fake_send_mission_command(settings, mission_id, command_type, operator_id):
        return {
            "status": "accepted",
            "mission_id": mission_id,
            "command_type": command_type,
            "operator_id": operator_id,
        }

    monkeypatch.setattr(main_module, "send_mission_command", fake_send_mission_command)
    try:
        client.post(
            "/missions/demo_forward_stop/start",
            headers={"X-ORIMUS-Operator": "operator-demo"},
        )
        client.post("/missions/demo_forward_stop/start")

        by_operator = client.get("/audit/events?operator_id=operator-demo").json()[
            "events"
        ]
        by_event_type = client.get("/audit/events?event_type=mission_command").json()[
            "events"
        ]
        by_decision = client.get("/audit/events?decision=denied").json()["events"]
        by_date = client.get("/audit/events?date_from=0").json()["events"]

        assert [event["operator_id"] for event in by_operator] == ["operator-demo"]
        assert len(by_event_type) == 2
        assert [event["decision"] for event in by_decision] == ["denied"]
        assert len(by_date) == 2
    finally:
        settings.report_database_path = original_database_path


def test_backend_audit_source_ip_toggle_off(tmp_path: Path, monkeypatch):
    original_database_path = settings.report_database_path
    original_log_source_ip = settings.log_source_ip
    settings.report_database_path = tmp_path / "orimus.db"
    settings.log_source_ip = False

    def fake_send_mission_command(settings, mission_id, command_type, operator_id):
        return {
            "status": "accepted",
            "mission_id": mission_id,
            "command_type": command_type,
            "operator_id": operator_id,
        }

    monkeypatch.setattr(main_module, "send_mission_command", fake_send_mission_command)
    try:
        client.post(
            "/missions/demo_forward_stop/start",
            headers={"X-ORIMUS-Operator": "operator-demo"},
        )
        events = client.get("/audit/events").json()["events"]
        assert events[0]["source_ip"] is None
    finally:
        settings.report_database_path = original_database_path
        settings.log_source_ip = original_log_source_ip


def test_backend_audit_store_public_write_surface_is_append_only():
    public_methods = {
        name
        for name, member in inspect.getmembers(BackendAuditStore, inspect.isfunction)
        if not name.startswith("_")
    }
    write_methods = {
        name
        for name in public_methods
        if any(token in name for token in ["record", "create", "insert", "update", "delete"])
    }

    assert write_methods == {"record_event"}
    assert "update_event" not in public_methods
    assert "delete_event" not in public_methods


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
        assert reports[1]["content_hash"]
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
        assert response.json()["content_hash"]
    finally:
        settings.report_database_path = original_database_path


def test_export_report_evidence_package_from_database(tmp_path: Path):
    original_database_path = settings.report_database_path
    settings.report_database_path = create_report_database(tmp_path)
    try:
        response = client.get("/reports/report-001/export")
        assert response.status_code == 200
        assert (
            response.headers["content-disposition"]
            == 'attachment; filename="orimus-evidence-report-001.json"'
        )
        package = response.json()
        assert package["package_type"] == "orimus_evidence_package"
        assert package["schema_version"] == "1.0"
        assert package["report"]["report_id"] == "report-001"
        assert package["report"]["content_hash"]
        assert package["mission"]["mission_id"] == "demo_forward_stop"
        assert package["mission"]["sector"] == "sector-alpha"
        assert package["summary"]["perception_event_count"] == 1
        assert package["artifact_manifest"][0]["source_event_id"] == "perception-001"
        assert package["export_hash"] == hash_evidence_package(package)
        assert verify_evidence_package(package).exit_code == EXIT_VALID

        tampered = dict(package)
        tampered["mission"] = {**package["mission"], "sector": "tampered-sector"}
        assert package["export_hash"] != hash_evidence_package(tampered)
    finally:
        settings.report_database_path = original_database_path


def test_export_report_not_found(tmp_path: Path):
    original_database_path = settings.report_database_path
    settings.report_database_path = create_report_database(tmp_path)
    try:
        response = client.get("/reports/missing-report/export")
        assert response.status_code == 404
    finally:
        settings.report_database_path = original_database_path


def test_verify_evidence_package_rejects_hash_mismatch(tmp_path: Path):
    package = create_evidence_package_for_test(tmp_path)
    package["mission"]["sector"] = "tampered-sector"

    result = verify_evidence_package(package)

    assert result.exit_code == EXIT_HASH_MISMATCH
    assert "export_hash mismatch" in result.errors


def test_verify_evidence_package_rejects_schema_mismatch(tmp_path: Path):
    package = create_evidence_package_for_test(tmp_path)
    package["schema_version"] = "9.9"
    package["export_hash"] = hash_evidence_package(package)

    result = verify_evidence_package(package)

    assert result.exit_code == EXIT_SCHEMA_MISMATCH
    assert result.errors == ["schema_version must be 1.0"]


def test_verify_evidence_package_rejects_semantic_failures(tmp_path: Path):
    package = create_evidence_package_for_test(tmp_path)
    package["mission_report"]["safety_events"] = [
        {
            "stamp": {"sec": 150, "nanosec": 0},
            "event_id": "safety-missing-command",
            "rule": "unknown_command",
            "command_id": "missing-command-id",
            "command_blocked": True,
        }
    ]
    package["summary"]["robot_command_count"] = 99
    package["summary"]["safety_event_count"] = 1
    package["mission_report"]["content_hash"] = hash_mission_report(
        package["mission_report"]
    )
    package["report"]["content_hash"] = package["mission_report"]["content_hash"]
    package["export_hash"] = hash_evidence_package(package)

    result = verify_evidence_package(package)

    assert result.exit_code == EXIT_SEMANTIC_FAILURE
    assert "summary.robot_command_count expected 1" in result.errors
    assert any("references missing command_id" in error for error in result.errors)


def test_verify_evidence_package_rejects_non_monotonic_timestamps(tmp_path: Path):
    package = create_evidence_package_for_test(tmp_path)
    package["mission_report"]["mission_events"] = [
        {"stamp": {"sec": 20, "nanosec": 0}},
        {"stamp": {"sec": 10, "nanosec": 0}},
    ]
    package["summary"]["mission_event_count"] = 2
    package["mission_report"]["content_hash"] = hash_mission_report(
        package["mission_report"]
    )
    package["report"]["content_hash"] = package["mission_report"]["content_hash"]
    package["export_hash"] = hash_evidence_package(package)

    result = verify_evidence_package(package)

    assert result.exit_code == EXIT_SEMANTIC_FAILURE
    assert "mission_events timestamps are not monotonic" in result.errors


def test_verify_evidence_package_cli_exit_codes(tmp_path: Path):
    package = create_evidence_package_for_test(tmp_path)
    package_path = tmp_path / "package.json"
    package_path.write_text(json.dumps(package), encoding="utf-8")

    valid = subprocess.run(
        [sys.executable, "scripts/verify_evidence_package.py", str(package_path)],
        cwd=Path(__file__).resolve().parents[1],
        check=False,
        capture_output=True,
        text=True,
    )
    assert valid.returncode == EXIT_VALID
    assert "VALID" in valid.stdout

    package["schema_version"] = "9.9"
    package["export_hash"] = hash_evidence_package(package)
    package_path.write_text(json.dumps(package), encoding="utf-8")
    invalid = subprocess.run(
        [sys.executable, "scripts/verify_evidence_package.py", str(package_path)],
        cwd=Path(__file__).resolve().parents[1],
        check=False,
        capture_output=True,
        text=True,
    )
    assert invalid.returncode == EXIT_SCHEMA_MISMATCH
    assert "schema_version must be 1.0" in invalid.stdout


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
        "mission": {
            "mission_id": "demo_forward_stop",
            "name": "Demo Forward Stop",
            "state": "completed",
            "sector": "sector-alpha",
            "stamp": {"sec": 200, "nanosec": 0},
        },
        "mission_states": [{"stamp": {"sec": 100, "nanosec": 0}}],
        "mission_events": [],
        "robot_commands": [
            {
                "stamp": {"sec": 120, "nanosec": 0},
                "command_id": "demo_forward_stop_stand_120",
                "topic": "robot/command",
                "command_type": "stand",
            }
        ],
        "safety_events": [],
        "perception_events": [
            {
                "event_id": "perception-001",
                "event_type": "person_detected",
                "source": "mock_inspection_camera",
                "evidence_artifact_url": None,
                "evidence_hash": None,
            }
        ],
    }
    report_001["content_hash"] = hash_mission_report(report_001)
    report_002 = {
        "report_id": "report-002",
        "mission": {
            "mission_id": "control_test",
            "name": "Control Test Mission",
            "state": "canceled",
            "sector": "sector-bravo",
        },
    }
    report_002["content_hash"] = hash_mission_report(report_002)
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
                evidence_artifact_url TEXT,
                evidence_hash TEXT,
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
                command_id TEXT,
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
                report_001["content_hash"],
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
                report_002["content_hash"],
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
                stamp_sec, stamp_nanosec, evidence_artifact_url, evidence_hash,
                payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "perception-001",
                "report-001",
                "person_detected",
                "mock_inspection_camera",
                0.92,
                150,
                0,
                None,
                None,
                "{}",
            ),
        )
        connection.execute(
            """
            INSERT INTO safety_events (
                id, report_id, rule, severity, command_id, command_blocked,
                stamp_sec, stamp_nanosec, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "safety-001",
                "report-002",
                "operator_cancel",
                "warning",
                "control_test_cancel_300",
                1,
                280,
                0,
                "{}",
            ),
        )
    return database_path


def create_evidence_package_for_test(tmp_path: Path) -> dict:
    original_database_path = settings.report_database_path
    settings.report_database_path = create_report_database(tmp_path)
    try:
        return client.get("/reports/report-001/export").json()
    finally:
        settings.report_database_path = original_database_path
