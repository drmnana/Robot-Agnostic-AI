from pathlib import Path
import json
import os
import sqlite3
import subprocess
import sys
import inspect
import zipfile
import io
from io import BytesIO

from fastapi import HTTPException
from fastapi.testclient import TestClient

import app.main as main_module
import app.readiness as readiness_module
from app.audit_package import (
    build_api_audit_package,
    hash_api_audit_package,
    verify_api_audit_package,
)
from app.artifact_store import ArtifactStore, hash_file
from app.backend_audit import BackendAuditStore
from app.evidence_bundle import (
    BUNDLE_MANIFEST_PATH,
    BUNDLE_PACKAGE_PATH,
    build_evidence_bundle,
    verify_evidence_bundle,
)
from app.evidence_package import hash_evidence_package, hash_mission_report
from app.evidence_verifier import (
    EXIT_HASH_MISMATCH,
    EXIT_SCHEMA_MISMATCH,
    EXIT_SEMANTIC_FAILURE,
    EXIT_VALID,
    verify_evidence_package,
)
from app.main import app, settings
from app.mission_schema import (
    mission_schema_json,
    validate_mission_directory,
    validate_mission_file,
)
from app.readiness import ReadinessCheck, clear_readiness_cache
from app.scenario_manifest import find_scenario, load_scenario_manifest
from scripts.check_scenario_result import evaluate_report


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_liveness_returns_alive():
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {
        "status": "alive",
        "service": "orimus-backend",
    }


def test_readiness_returns_ready_when_dependencies_are_available(tmp_path: Path, monkeypatch):
    original_paths = snapshot_readiness_settings()
    try:
        configure_readiness_paths(tmp_path)
        write_valid_mission(tmp_path / "missions")
        write_operator_policy(tmp_path / "operator_policy.yaml")
        monkeypatch.setattr(
            readiness_module,
            "check_ros_bridge",
            lambda _url: ReadinessCheck("ros_bridge", "ready", "optional", "ok"),
        )
        clear_readiness_cache()

        response = client.get("/readiness?fresh=true")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ready"
        assert body["cached"] is False
        assert {check["name"] for check in body["checks"]}.issuperset(
            {"backend_process", "mission_yaml_validation", "sqlite_database", "ros_bridge"}
        )
    finally:
        restore_readiness_settings(original_paths)
        clear_readiness_cache()


def test_readiness_degrades_when_ros_bridge_is_unavailable(tmp_path: Path, monkeypatch):
    original_paths = snapshot_readiness_settings()
    try:
        configure_readiness_paths(tmp_path)
        write_valid_mission(tmp_path / "missions")
        write_operator_policy(tmp_path / "operator_policy.yaml")
        monkeypatch.setattr(
            readiness_module,
            "check_ros_bridge",
            lambda _url: ReadinessCheck("ros_bridge", "degraded", "optional", "offline"),
        )
        clear_readiness_cache()

        response = client.get("/readiness?fresh=true")

        assert response.status_code == 200
        assert response.json()["status"] == "degraded"
    finally:
        restore_readiness_settings(original_paths)
        clear_readiness_cache()


def test_readiness_reports_required_failures(tmp_path: Path, monkeypatch):
    original_paths = snapshot_readiness_settings()
    try:
        configure_readiness_paths(tmp_path)
        settings.artifact_root = tmp_path / "artifact_root_file"
        settings.artifact_root.write_text("not a directory", encoding="utf-8")
        settings.latest_report_path = tmp_path / "report_parent_file" / "latest.json"
        settings.latest_report_path.parent.write_text("not a directory", encoding="utf-8")
        settings.report_database_path = tmp_path / "database_parent_file" / "orimus.db"
        settings.report_database_path.parent.write_text("not a directory", encoding="utf-8")
        (settings.mission_config_dir / "bad.yaml").write_text("mission_id: bad\n", encoding="utf-8")
        monkeypatch.setattr(
            readiness_module,
            "check_ros_bridge",
            lambda _url: ReadinessCheck("ros_bridge", "ready", "optional", "ok"),
        )
        clear_readiness_cache()

        response = client.get("/readiness?fresh=true")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "not_ready"
        failed = {check["name"] for check in body["checks"] if check["status"] == "not_ready"}
        assert {
            "mission_yaml_validation",
            "sqlite_database",
            "artifact_root",
            "latest_report_parent",
        }.issubset(failed)
    finally:
        restore_readiness_settings(original_paths)
        clear_readiness_cache()


def test_readiness_cache_reuses_expensive_checks_and_fresh_bypasses(tmp_path: Path, monkeypatch):
    original_paths = snapshot_readiness_settings()
    validate_calls = {"count": 0}
    real_validate = readiness_module.validate_mission_directory

    def counting_validate(path: Path):
        validate_calls["count"] += 1
        return real_validate(path)

    try:
        configure_readiness_paths(tmp_path)
        write_valid_mission(tmp_path / "missions")
        write_operator_policy(tmp_path / "operator_policy.yaml")
        monkeypatch.setattr(readiness_module, "validate_mission_directory", counting_validate)
        monkeypatch.setattr(
            readiness_module,
            "check_ros_bridge",
            lambda _url: ReadinessCheck("ros_bridge", "ready", "optional", "ok"),
        )
        clear_readiness_cache()

        first = client.get("/readiness?fresh=true").json()
        (settings.mission_config_dir / "bad.yaml").write_text("mission_id: bad\n", encoding="utf-8")
        cached = client.get("/readiness").json()
        fresh = client.get("/readiness?fresh=true").json()

        assert first["status"] == "ready"
        assert cached["status"] == "ready"
        assert cached["cached"] is True
        assert fresh["status"] == "not_ready"
        assert validate_calls["count"] == 2
    finally:
        restore_readiness_settings(original_paths)
        clear_readiness_cache()


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
    assert "Export Bundle" in response.text
    assert "Mission Replay" in response.text
    assert "Readiness" in response.text
    assert 'data-tab-link="ops"' in response.text
    assert 'data-tab-link="history"' in response.text
    assert 'data-tab-link="audit"' in response.text
    assert 'data-tab-link="readiness"' in response.text
    assert 'data-tab-panel="ops"' in response.text
    assert 'data-tab-panel="history"' in response.text
    assert 'data-tab-panel="audit"' in response.text
    assert 'data-tab-panel="readiness"' in response.text
    assert 'id="readiness-status"' in response.text
    assert 'id="readiness-list"' in response.text
    assert 'id="replay-speed"' in response.text
    assert 'id="replay-slider"' in response.text
    assert 'id="audit-filter-decision"' in response.text
    assert 'id="audit-list"' in response.text
    assert 'id="audit-export-json"' in response.text


def test_dashboard_artifact_link_markup_is_available():
    app_js = Path(__file__).resolve().parents[2] / "dashboard" / "app.js"
    text = app_js.read_text(encoding="utf-8")

    assert "artifact-link" in text
    assert "No artifact captured" in text
    assert "replayIntervalMs" in text
    assert 'params.get("frame")' in text
    assert "highlightLinkedRecord" in text
    assert "setInterval(refreshReadiness, 20000)" in text
    assert "fresh=true" in text


def test_dashboard_tabs_are_url_addressable_and_preserve_surface():
    app_js = Path(__file__).resolve().parents[2] / "dashboard" / "app.js"
    index_html = Path(__file__).resolve().parents[2] / "dashboard" / "index.html"
    js_text = app_js.read_text(encoding="utf-8")
    html_text = index_html.read_text(encoding="utf-8")

    assert 'params.get("tab")' in js_text
    assert 'url.searchParams.set("tab", nextTab)' in js_text
    assert 'window.addEventListener("popstate"' in js_text
    assert 'activateTab(tabFromUrl(), false)' in js_text
    for element_id in [
        "mission-list",
        "operator-id",
        "refresh-button",
        "readiness-refresh-button",
        "report-refresh-button",
        "report-export-json",
        "report-export-bundle",
        "replay-play",
        "replay-slider",
        "audit-refresh-button",
        "audit-export-json",
        "audit-filter-decision",
        "audit-list",
    ]:
        assert f'id="{element_id}"' in html_text


def test_mission_schema_file_exists_and_matches_model():
    schema_path = Path(__file__).resolve().parents[2] / "configs" / "mission_schema.json"

    assert schema_path.exists()
    assert json.loads(schema_path.read_text(encoding="utf-8")) == json.loads(
        mission_schema_json()
    )


def test_committed_openapi_spec_matches_live_app():
    openapi_path = Path(__file__).resolve().parents[2] / "docs" / "openapi.json"

    assert openapi_path.exists()
    assert json.loads(openapi_path.read_text(encoding="utf-8")) == app.openapi()


def test_api_spec_regeneration_script_is_available():
    script = Path(__file__).resolve().parents[1] / "scripts" / "regenerate_api_spec.py"

    assert script.exists()
    assert "app.openapi()" in script.read_text(encoding="utf-8")


def test_all_configured_missions_validate():
    mission_dir = Path(__file__).resolve().parents[2] / "configs" / "missions"

    missions = validate_mission_directory(mission_dir)

    mission_ids = {mission.mission_id for mission in missions}
    assert {
        "demo_forward_stop",
        "control_test",
        "perimeter_patrol",
        "artifact_inspection",
        "safety_speed_limit",
        "pause_resume_training",
        "policy_denial_demo",
    }.issubset(mission_ids)


def test_scenario_manifest_parses_and_is_versioned():
    manifest_path = Path(__file__).resolve().parents[2] / "configs" / "scenarios.yaml"

    manifest = load_scenario_manifest(manifest_path)

    assert manifest.version == 1
    assert find_scenario(manifest, "artifact_inspection").expected.artifact_required
    assert find_scenario(manifest, "policy_denial_demo").is_backend_policy_scenario


def test_scenario_manifest_rejects_unknown_scenario():
    manifest_path = Path(__file__).resolve().parents[2] / "configs" / "scenarios.yaml"
    manifest = load_scenario_manifest(manifest_path)

    try:
        find_scenario(manifest, "missing_scenario")
    except ValueError as error:
        assert "unknown scenario" in str(error)
    else:
        raise AssertionError("Unknown scenario should have failed")


def test_scenario_result_checker_reports_specific_mismatch(tmp_path: Path):
    manifest_path = Path(__file__).resolve().parents[2] / "configs" / "scenarios.yaml"
    scenario = find_scenario(load_scenario_manifest(manifest_path), "artifact_inspection")
    report = {
        "report_id": "report-debug-001",
        "mission": {"state": "completed"},
        "mission_events": [],
        "robot_commands": [],
        "payload_results": [],
        "perception_events": [],
        "safety_events": [],
    }

    failures = evaluate_report(scenario, report)

    assert any("min_mission_events expected >= 5, observed 0" in failure for failure in failures)
    assert all("see report report-debug-001" in failure for failure in failures)


def test_scenario_runner_all_mode_summary_can_pass_and_fail(tmp_path: Path):
    script = Path(__file__).resolve().parents[2] / "ros2_ws" / "scripts" / "run_scenario_check.sh"
    text = script.read_text(encoding="utf-8")

    assert "--all" in text
    assert "SUMMARY: ${passed} passed, ${failed} failed" in text
    assert "FAILED: ${failed_ids[*]}" in text


def test_project_verification_script_exits_zero_when_checks_pass():
    result = run_verify_project_fake("pass")

    assert result.returncode == 0
    assert "[PASS] fake one" in result.stdout
    assert "SUMMARY: 2 passed, 0 failed" in result.stdout


def test_project_verification_script_fail_fast_stops_on_first_failure():
    result = run_verify_project_fake("fail-first")

    assert result.returncode == 1
    assert "[FAIL] fake one" in result.stdout
    assert "fake two" not in result.stdout
    assert "SUMMARY: 0 passed, 1 failed" in result.stdout


def test_project_verification_script_all_mode_runs_every_check():
    result = run_verify_project_fake("fail-second", "--all")

    assert result.returncode == 1
    assert "[PASS] fake one" in result.stdout
    assert "[FAIL] fake two" in result.stdout
    assert "[PASS] fake three" in result.stdout
    assert "SUMMARY: 2 passed, 1 failed" in result.stdout


def test_mission_validation_rejects_missing_required_fields(tmp_path: Path):
    mission_file = tmp_path / "bad.yaml"
    mission_file.write_text("mission_id: bad\nsteps: []\n", encoding="utf-8")

    try:
        validate_mission_file(mission_file)
    except ValueError as error:
        assert "name" in str(error)
        assert "sector" in str(error)
    else:
        raise AssertionError("Mission validation should have failed")


def test_mission_validation_rejects_unsupported_target(tmp_path: Path):
    mission_file = tmp_path / "bad.yaml"
    mission_file.write_text(
        """
mission_id: bad_target
name: Bad Target
sector: test
steps:
  - name: bad_step
    target: drone
    command_type: fly
    duration_sec: 1.0
""",
        encoding="utf-8",
    )

    try:
        validate_mission_file(mission_file)
    except ValueError as error:
        assert "target" in str(error)
    else:
        raise AssertionError("Mission validation should have failed")


def test_mission_validation_rejects_payload_step_missing_payload_fields(tmp_path: Path):
    mission_file = tmp_path / "bad.yaml"
    mission_file.write_text(
        """
mission_id: bad_payload
name: Bad Payload
sector: test
steps:
  - name: scan
    target: payload
    command_type: scan
    duration_sec: 1.0
""",
        encoding="utf-8",
    )

    try:
        validate_mission_file(mission_file)
    except ValueError as error:
        assert "payload_id" in str(error)
        assert "payload_type" in str(error)
    else:
        raise AssertionError("Mission validation should have failed")


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


def test_policy_denial_demo_anonymous_cancel_is_denied_and_logged(
    tmp_path: Path,
    monkeypatch,
):
    original_database_path = settings.report_database_path
    settings.report_database_path = tmp_path / "orimus.db"
    calls = []

    def fake_send_mission_command(settings, mission_id, command_type, operator_id):
        calls.append((mission_id, command_type, operator_id))
        return {}

    monkeypatch.setattr(main_module, "send_mission_command", fake_send_mission_command)
    try:
        response = client.post("/missions/policy_denial_demo/cancel")
        assert response.status_code == 403
        assert calls == []

        events = client.get(
            "/audit/events?operator_id=anonymous&decision=denied"
        ).json()["events"]
        assert len(events) == 1
        assert events[0]["mission_id"] == "policy_denial_demo"
        assert events[0]["command_type"] == "cancel"
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


def test_export_api_audit_package_filters_and_hashes(tmp_path: Path):
    original_database_path = settings.report_database_path
    settings.report_database_path = tmp_path / "orimus.db"
    try:
        store = BackendAuditStore(settings.report_database_path)
        store.record_event(
            event_type="mission_command",
            decision="allowed",
            operator_id="operator-demo",
            mission_id="demo_forward_stop",
            command_type="start",
            reason="operator_policy",
            request_path="/missions/demo_forward_stop/start",
            source_ip="127.0.0.1",
        )
        store.record_event(
            event_type="mission_command",
            decision="denied",
            operator_id="anonymous",
            mission_id="policy_denial_demo",
            command_type="cancel",
            reason="operator_policy",
            request_path="/missions/policy_denial_demo/cancel",
            source_ip="127.0.0.1",
        )

        response = client.get("/audit/events/export?decision=denied")

        assert response.status_code == 200
        package = response.json()
        assert package["package_type"] == "orimus_api_audit_package"
        assert package["schema_version"] == "1.0"
        assert package["filters"] == {"decision": "denied"}
        assert package["summary"]["event_count"] == 1
        assert package["summary"]["denied_count"] == 1
        assert package["summary"]["allowed_count"] == 0
        assert package["events"][0]["operator_id"] == "anonymous"
        assert package["export_hash"] == hash_api_audit_package(package)
        assert verify_api_audit_package(package).exit_code == EXIT_VALID
    finally:
        settings.report_database_path = original_database_path


def test_api_audit_package_verifier_rejects_hash_mismatch():
    package = build_api_audit_package([api_audit_event("event-001", 1.0, "allowed")], {})
    package["events"][0]["decision"] = "denied"

    result = verify_api_audit_package(package)

    assert result.exit_code == EXIT_HASH_MISMATCH
    assert "export_hash mismatch" in result.errors


def test_api_audit_package_verifier_rejects_schema_mismatch():
    package = build_api_audit_package([api_audit_event("event-001", 1.0, "allowed")], {})
    package["schema_version"] = "9.9"
    package["export_hash"] = hash_api_audit_package(package)

    result = verify_api_audit_package(package)

    assert result.exit_code == EXIT_SCHEMA_MISMATCH
    assert "schema_version must be 1.0" in result.errors


def test_api_audit_package_verifier_rejects_semantic_failure():
    package = build_api_audit_package(
        [
            api_audit_event("event-001", 2.0, "allowed"),
            api_audit_event("event-002", 1.0, "denied"),
        ],
        {},
    )
    package["events"] = list(reversed(package["events"]))
    package["summary"]["event_count"] = 99
    package["export_hash"] = hash_api_audit_package(package)

    result = verify_api_audit_package(package)

    assert result.exit_code == EXIT_SEMANTIC_FAILURE
    assert "summary.event_count expected 2" in result.errors
    assert "events timestamps are not monotonic" in result.errors


def test_api_audit_package_verifier_rejects_invalid_decision():
    package = build_api_audit_package([api_audit_event("event-001", 1.0, "maybe")], {})
    package["export_hash"] = hash_api_audit_package(package)

    result = verify_api_audit_package(package)

    assert result.exit_code == EXIT_SEMANTIC_FAILURE
    assert "events[0].decision must be allowed or denied" in result.errors


def test_api_audit_verifier_rejects_mission_evidence_package(tmp_path: Path):
    evidence_package = create_evidence_package_for_test(tmp_path)

    result = verify_api_audit_package(evidence_package)

    assert result.exit_code == EXIT_SCHEMA_MISMATCH
    assert "this verifier is for ORIMUS API Audit Package JSON" in result.errors[0]


def test_api_audit_cli_rejects_mission_evidence_package(tmp_path: Path):
    evidence_package = create_evidence_package_for_test(tmp_path)
    evidence_path = tmp_path / "evidence-package.json"
    evidence_path.write_text(json.dumps(evidence_package), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "scripts/verify_audit_package.py", str(evidence_path)],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == EXIT_SCHEMA_MISMATCH
    assert "this verifier is for ORIMUS API Audit Package JSON" in result.stdout


def test_api_audit_package_cli_exit_codes_and_help(tmp_path: Path):
    package_path = tmp_path / "audit-package.json"
    package = build_api_audit_package([api_audit_event("event-001", 1.0, "allowed")], {})
    package_path.write_text(json.dumps(package), encoding="utf-8")

    valid = subprocess.run(
        [sys.executable, "scripts/verify_audit_package.py", str(package_path)],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
        check=False,
    )
    help_result = subprocess.run(
        [sys.executable, "scripts/verify_audit_package.py", "--help"],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
        check=False,
    )
    package["export_hash"] = "bad"
    package_path.write_text(json.dumps(package), encoding="utf-8")
    invalid = subprocess.run(
        [sys.executable, "scripts/verify_audit_package.py", str(package_path)],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
        check=False,
    )
    bad_json_path = tmp_path / "bad.json"
    bad_json_path.write_text("{", encoding="utf-8")
    unreadable = subprocess.run(
        [sys.executable, "scripts/verify_audit_package.py", str(bad_json_path)],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
        check=False,
    )

    assert valid.returncode == EXIT_VALID
    assert "VALID: ORIMUS API audit package verified" in valid.stdout
    assert help_result.returncode == EXIT_VALID
    assert "API Audit Package" in help_result.stdout
    assert "not a mission Evidence Package" in help_result.stdout
    assert invalid.returncode == EXIT_HASH_MISMATCH
    assert unreadable.returncode == EXIT_SCHEMA_MISMATCH


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


def test_artifact_registry_roundtrip_and_download(tmp_path: Path):
    original_database_path = settings.report_database_path
    original_artifact_root = settings.artifact_root
    settings.report_database_path = tmp_path / "orimus.db"
    settings.artifact_root = tmp_path / "artifacts"
    artifact_path = settings.artifact_root / "artifact-001.txt"
    artifact_path.parent.mkdir(parents=True)
    artifact_path.write_bytes(b"mock-payload-stub".ljust(1024, b" "))

    try:
        store = ArtifactStore(settings.report_database_path, settings.artifact_root)
        artifact = store.register_artifact(
            artifact_id="artifact-001",
            mission_id="demo_forward_stop",
            report_id="report-001",
            source="mock_payload",
            artifact_type="mock-payload-stub",
            file_path=artifact_path,
            created_at=123.0,
            metadata={"note": "opaque"},
        )

        assert artifact["sha256_hash"] == hash_file(artifact_path)

        response = client.get("/artifacts?report_id=report-001")
        assert response.status_code == 200
        artifacts = response.json()["artifacts"]
        assert len(artifacts) == 1
        assert artifacts[0]["artifact_id"] == "artifact-001"
        assert artifacts[0]["artifact_type"] == "mock-payload-stub"

        detail = client.get("/artifacts/artifact-001")
        assert detail.status_code == 200
        assert detail.json()["sha256_hash"] == artifact["sha256_hash"]

        download = client.get("/artifacts/artifact-001/download")
        assert download.status_code == 200
        assert download.content == artifact_path.read_bytes()
    finally:
        settings.report_database_path = original_database_path
        settings.artifact_root = original_artifact_root


def test_artifact_download_verifies_hash(tmp_path: Path):
    original_database_path = settings.report_database_path
    original_artifact_root = settings.artifact_root
    settings.report_database_path = tmp_path / "orimus.db"
    settings.artifact_root = tmp_path / "artifacts"
    artifact_path = settings.artifact_root / "artifact-002.txt"
    artifact_path.parent.mkdir(parents=True)
    artifact_path.write_bytes(b"original".ljust(1024, b" "))

    try:
        store = ArtifactStore(settings.report_database_path, settings.artifact_root)
        store.register_artifact(
            artifact_id="artifact-002",
            mission_id="demo_forward_stop",
            report_id="report-001",
            source="mock_payload",
            artifact_type="mock-payload-stub",
            file_path=artifact_path,
            created_at=123.0,
            metadata={},
        )
        artifact_path.write_bytes(b"tampered".ljust(1024, b" "))

        response = client.get("/artifacts/artifact-002/download")

        assert response.status_code == 409
        assert response.json()["detail"] == "Artifact hash mismatch"
    finally:
        settings.report_database_path = original_database_path
        settings.artifact_root = original_artifact_root


def test_missing_artifact_returns_404(tmp_path: Path):
    original_database_path = settings.report_database_path
    original_artifact_root = settings.artifact_root
    settings.report_database_path = tmp_path / "orimus.db"
    settings.artifact_root = tmp_path / "artifacts"

    try:
        response = client.get("/artifacts/missing-artifact")
        download = client.get("/artifacts/missing-artifact/download")

        assert response.status_code == 404
        assert download.status_code == 404
    finally:
        settings.report_database_path = original_database_path
        settings.artifact_root = original_artifact_root


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


def test_report_replay_returns_sorted_frames_and_cross_references(tmp_path: Path):
    original_database_path = settings.report_database_path
    settings.report_database_path = create_report_database(tmp_path)
    try:
        response = client.get("/reports/report-001/replay")
        assert response.status_code == 200
        frames = response.json()["frames"]

        assert [frame["frame_index"] for frame in frames] == list(range(len(frames)))
        assert [frame["timestamp_sec"] for frame in frames] == sorted(
            frame["timestamp_sec"] for frame in frames
        )
        safety_frame = next(frame for frame in frames if frame["category"] == "safety")
        perception_frame = next(
            frame for frame in frames if frame["category"] == "perception"
        )
        assert safety_frame["command_id"] == "demo_forward_stop_stand_120"
        assert perception_frame["artifact_url"] == "/artifacts/artifact-001/download"
        assert perception_frame["artifact_hash"] == "artifact-hash-001"
    finally:
        settings.report_database_path = original_database_path


def test_report_replay_filters_apply_correctly(tmp_path: Path):
    original_database_path = settings.report_database_path
    settings.report_database_path = create_report_database(tmp_path)
    try:
        category = client.get("/reports/report-001/replay?category=perception").json()[
            "frames"
        ]
        since = client.get("/reports/report-001/replay?since=140").json()["frames"]
        operator = client.get(
            "/reports/report-001/replay?operator_id=operator-demo"
        ).json()["frames"]
        command = client.get(
            "/reports/report-001/replay?command_id=demo_forward_stop_stand_120"
        ).json()["frames"]

        assert [frame["category"] for frame in category] == ["perception"]
        assert all(frame["timestamp_sec"] >= 140 for frame in since)
        assert {frame["operator_id"] for frame in operator} == {"operator-demo"}
        assert {frame["command_id"] for frame in command} == {
            "demo_forward_stop_stand_120"
        }
    finally:
        settings.report_database_path = original_database_path


def test_report_replay_empty_report_degrades_cleanly(tmp_path: Path):
    original_database_path = settings.report_database_path
    settings.report_database_path = create_report_database(tmp_path)
    try:
        response = client.get("/reports/report-002/replay")

        assert response.status_code == 200
        assert response.json()["frame_count"] == 0
        assert response.json()["frames"] == []
    finally:
        settings.report_database_path = original_database_path


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


def test_export_report_bundle_roundtrip_and_deterministic(tmp_path: Path):
    original_database_path = settings.report_database_path
    original_artifact_root = settings.artifact_root
    settings.report_database_path = create_report_database(tmp_path)
    settings.artifact_root = tmp_path / "artifacts"
    register_test_artifact(settings.report_database_path, settings.artifact_root)
    try:
        response = client.get("/reports/report-001/export-bundle")
        assert response.status_code == 200
        assert (
            response.headers["content-disposition"]
            == 'attachment; filename="orimus-evidence-bundle-report-001.zip"'
        )

        bundle_path = tmp_path / "bundle.zip"
        bundle_path.write_bytes(response.content)
        assert verify_evidence_bundle(bundle_path).exit_code == EXIT_VALID

        artifacts = ArtifactStore(
            settings.report_database_path,
            settings.artifact_root,
        ).list_artifacts(report_id="report-001")
        report = client.get("/reports/report-001").json()
        bundle_a, manifest_a = build_evidence_bundle(report, artifacts)
        bundle_b, manifest_b = build_evidence_bundle(report, artifacts)

        assert bundle_a == bundle_b
        assert manifest_a["bundle_hash"] == manifest_b["bundle_hash"]
    finally:
        settings.report_database_path = original_database_path
        settings.artifact_root = original_artifact_root


def test_verify_evidence_bundle_rejects_tampered_evidence_json(tmp_path: Path):
    bundle_path = create_evidence_bundle_for_test(tmp_path)
    tampered_path = tmp_path / "tampered-evidence.zip"

    def tamper(name: str, content: bytes) -> bytes:
        if name != BUNDLE_PACKAGE_PATH:
            return content
        package = json.loads(content)
        package["mission"]["sector"] = "tampered-sector"
        return json.dumps(package, sort_keys=True).encode("utf-8")

    rewrite_bundle(bundle_path, tampered_path, tamper)

    result = verify_evidence_bundle(tampered_path)

    assert result.exit_code == EXIT_HASH_MISMATCH
    assert "evidence_package_hash mismatch" in result.errors


def test_verify_evidence_bundle_rejects_tampered_manifest(tmp_path: Path):
    bundle_path = create_evidence_bundle_for_test(tmp_path)
    tampered_path = tmp_path / "tampered-manifest.zip"

    def tamper(name: str, content: bytes) -> bytes:
        if name != BUNDLE_MANIFEST_PATH:
            return content
        manifest = json.loads(content)
        manifest["artifact_count"] = 99
        return json.dumps(manifest, sort_keys=True).encode("utf-8")

    rewrite_bundle(bundle_path, tampered_path, tamper)

    result = verify_evidence_bundle(tampered_path)

    assert result.exit_code == EXIT_HASH_MISMATCH
    assert "bundle_hash mismatch" in result.errors


def test_verify_evidence_bundle_rejects_missing_artifact_file(tmp_path: Path):
    bundle_path = create_evidence_bundle_for_test(tmp_path)
    missing_path = tmp_path / "missing-artifact.zip"

    rewrite_bundle(
        bundle_path,
        missing_path,
        lambda _name, content: content,
        skip_prefix="artifacts/",
    )

    result = verify_evidence_bundle(missing_path)

    assert result.exit_code == EXIT_SEMANTIC_FAILURE
    assert any("missing artifact file" in error for error in result.errors)


def test_verify_evidence_bundle_rejects_tampered_artifact_bytes(tmp_path: Path):
    bundle_path = create_evidence_bundle_for_test(tmp_path)
    tampered_path = tmp_path / "tampered-artifact.zip"

    def tamper(name: str, content: bytes) -> bytes:
        if name.startswith("artifacts/"):
            return b"tampered" + content[8:]
        return content

    rewrite_bundle(bundle_path, tampered_path, tamper)

    result = verify_evidence_bundle(tampered_path)

    assert result.exit_code == EXIT_HASH_MISMATCH
    assert any("hash mismatch" in error for error in result.errors)


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
                "operator_id": "operator-demo",
            }
        ],
        "safety_events": [
            {
                "stamp": {"sec": 130, "nanosec": 0},
                "event_id": "safety-report-001",
                "rule": "speed_limit",
                "severity": "info",
                "command_id": "demo_forward_stop_stand_120",
                "operator_id": "operator-demo",
                "command_blocked": False,
                "message": "Command checked",
            }
        ],
        "perception_events": [
            {
                "stamp": {"sec": 150, "nanosec": 0},
                "event_id": "perception-001",
                "event_type": "person_detected",
                "source": "mock_inspection_camera",
                "evidence_artifact_url": "/artifacts/artifact-001/download",
                "evidence_hash": "artifact-hash-001",
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


def snapshot_readiness_settings() -> dict:
    return {
        "mission_config_dir": settings.mission_config_dir,
        "operator_policy_path": settings.operator_policy_path,
        "latest_report_path": settings.latest_report_path,
        "report_database_path": settings.report_database_path,
        "artifact_root": settings.artifact_root,
        "mission_api_bridge_url": settings.mission_api_bridge_url,
    }


def restore_readiness_settings(snapshot: dict) -> None:
    settings.mission_config_dir = snapshot["mission_config_dir"]
    settings.operator_policy_path = snapshot["operator_policy_path"]
    settings.latest_report_path = snapshot["latest_report_path"]
    settings.report_database_path = snapshot["report_database_path"]
    settings.artifact_root = snapshot["artifact_root"]
    settings.mission_api_bridge_url = snapshot["mission_api_bridge_url"]


def configure_readiness_paths(tmp_path: Path) -> None:
    settings.mission_config_dir = tmp_path / "missions"
    settings.mission_config_dir.mkdir(parents=True, exist_ok=True)
    settings.operator_policy_path = tmp_path / "operator_policy.yaml"
    settings.latest_report_path = tmp_path / "reports" / "latest_mission_report.json"
    settings.report_database_path = tmp_path / "data" / "orimus.db"
    settings.artifact_root = tmp_path / "data" / "artifacts"
    settings.mission_api_bridge_url = "http://example.invalid:8010"
    settings.latest_report_path.parent.mkdir(parents=True, exist_ok=True)
    settings.report_database_path.parent.mkdir(parents=True, exist_ok=True)


def write_valid_mission(mission_dir: Path) -> None:
    mission_dir.mkdir(parents=True, exist_ok=True)
    (mission_dir / "ready.yaml").write_text(
        """
mission_id: ready
name: Ready Mission
sector: test-sector
steps:
  - name: walk
    target: robot
    command_type: walk_velocity
    duration_sec: 1.0
    linear_x: 0.1
    linear_y: 0.0
    yaw_rate: 0.0
    max_speed: 0.2
""",
        encoding="utf-8",
    )


def write_operator_policy(policy_path: Path) -> None:
    policy_path.write_text(
        """
operators:
  operator-demo:
    allowed_mission_commands:
      - start
      - pause
""",
        encoding="utf-8",
    )


def api_audit_event(event_id: str, created_at_sec: float, decision: str) -> dict:
    return {
        "id": event_id,
        "created_at_sec": created_at_sec,
        "event_type": "mission_command",
        "operator_id": "operator-demo",
        "decision": decision,
        "mission_id": "demo_forward_stop",
        "command_type": "start",
        "reason": "operator_policy",
        "request_path": "/missions/demo_forward_stop/start",
        "source_ip": "127.0.0.1",
        "retention_class": "standard",
    }


def run_verify_project_fake(pattern: str, *args: str) -> subprocess.CompletedProcess:
    script = Path(__file__).resolve().parents[2] / "scripts" / "verify_project.sh"
    env = os.environ.copy()
    env["ORIMUS_VERIFY_FAKE_CHECKS"] = "1"
    env["ORIMUS_VERIFY_FAKE_PATTERN"] = pattern
    return subprocess.run(
        ["bash", str(script), *args],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def create_evidence_bundle_for_test(tmp_path: Path) -> Path:
    original_database_path = settings.report_database_path
    original_artifact_root = settings.artifact_root
    settings.report_database_path = create_report_database(tmp_path)
    settings.artifact_root = tmp_path / "artifacts"
    register_test_artifact(settings.report_database_path, settings.artifact_root)
    try:
        response = client.get("/reports/report-001/export-bundle")
        assert response.status_code == 200
        bundle_path = tmp_path / "bundle.zip"
        bundle_path.write_bytes(response.content)
        return bundle_path
    finally:
        settings.report_database_path = original_database_path
        settings.artifact_root = original_artifact_root


def register_test_artifact(database_path: Path, artifact_root: Path) -> dict:
    artifact_path = artifact_root / "artifact-001.txt"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_bytes(b"mock-payload-stub".ljust(1024, b" "))
    return ArtifactStore(database_path, artifact_root).register_artifact(
        artifact_id="artifact-001",
        mission_id="demo_forward_stop",
        report_id="report-001",
        source="mock_payload",
        artifact_type="mock-payload-stub",
        file_path=artifact_path,
        created_at=123.0,
        metadata={"note": "opaque"},
    )


def rewrite_bundle(
    source_path: Path,
    target_path: Path,
    transform,
    skip_prefix: str | None = None,
) -> None:
    with zipfile.ZipFile(source_path, "r") as source:
        entries = []
        for name in source.namelist():
            if skip_prefix and name.startswith(skip_prefix):
                continue
            entries.append((name, transform(name, source.read(name))))

    archive = BytesIO()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as target:
        for name, content in sorted(entries, key=lambda item: item[0]):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            target.writestr(info, content)
    target_path.write_bytes(archive.getvalue())
