import logging
from pathlib import Path
from typing import Optional

import yaml
from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from .artifact_store import (
    ArtifactHashMismatchError,
    ArtifactNotFoundError,
    ArtifactStore,
)
from .audit_package import build_api_audit_package
from .backend_audit import BackendAuditStore
from .evidence_bundle import build_evidence_bundle
from .evidence_package import build_evidence_package
from .event_severity import annotate_runtime_resource
from .mission_bridge_client import get_runtime_resource, send_mission_command
from .operator_policy import is_mission_command_allowed
from .readiness import build_readiness
from .replay import build_replay_frames
from .report_store import get_report, list_reports
from .settings import Settings


settings = Settings()
logger = logging.getLogger("orimus.backend")
app = FastAPI(title="ORIMUS Backend", version="0.1.0")
MISSION_COMMANDS = {"start", "pause", "resume", "cancel", "reset"}
RUNTIME_RESOURCES = {
    "state",
    "mission",
    "robot",
    "payload",
    "perception",
    "safety",
    "events",
}
DASHBOARD_DIR = Path(__file__).resolve().parents[2] / "dashboard"

if DASHBOARD_DIR.exists():
    app.mount("/dashboard", StaticFiles(directory=DASHBOARD_DIR, html=True), name="dashboard")


@app.get("/")
def root():
    return RedirectResponse(url="/dashboard/")


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "orimus-backend",
    }


@app.get("/healthz")
def healthz() -> dict:
    return {
        "status": "alive",
        "service": "orimus-backend",
    }


@app.get("/readiness")
def readiness(fresh: bool = Query(default=False)) -> dict:
    return build_readiness(settings, fresh=fresh)


@app.get("/missions")
def list_missions() -> dict:
    mission_dir = settings.mission_config_dir
    mission_dir.mkdir(parents=True, exist_ok=True)

    missions = []
    for mission_file in sorted(mission_dir.glob("*.yaml")):
        missions.append(read_mission_summary(mission_file))

    return {"missions": missions}


@app.get("/missions/{mission_id}")
def get_mission(mission_id: str) -> dict:
    mission_file = settings.mission_config_dir / f"{mission_id}.yaml"
    if not mission_file.exists():
        raise HTTPException(status_code=404, detail="Mission config not found")

    return read_yaml_file(mission_file)


@app.post("/missions/{mission_id}/{command_type}")
def control_mission(
    request: Request,
    mission_id: str,
    command_type: str,
    operator_id: Optional[str] = Header(default=None, alias="X-ORIMUS-Operator"),
) -> dict:
    if command_type not in MISSION_COMMANDS:
        raise HTTPException(status_code=400, detail="Unsupported mission command")

    normalized_operator_id = normalize_operator_id(operator_id)
    if not is_mission_command_allowed(
        settings.operator_policy_path,
        normalized_operator_id,
        command_type,
    ):
        audit_store().record_event(
            event_type="mission_command",
            decision="denied",
            operator_id=normalized_operator_id,
            mission_id=mission_id,
            command_type=command_type,
            reason="operator_policy",
            request_path=str(request.url.path),
            source_ip=request_source_ip(request),
        )
        logger.warning(
            "Mission command denied by operator policy: operator_id=%s mission_id=%s command_type=%s",
            normalized_operator_id,
            mission_id,
            command_type,
        )
        raise HTTPException(
            status_code=403,
            detail=(
                f"Mission command '{command_type}' denied by operator policy "
                f"for operator '{normalized_operator_id}'"
            ),
        )

    audit_store().record_event(
        event_type="mission_command",
        decision="allowed",
        operator_id=normalized_operator_id,
        mission_id=mission_id,
        command_type=command_type,
        reason="operator_policy",
        request_path=str(request.url.path),
        source_ip=request_source_ip(request),
    )
    return send_mission_command(
        settings,
        mission_id,
        command_type,
        normalized_operator_id,
    )


@app.get("/audit/events")
def get_audit_events(
    operator_id: Optional[str] = None,
    decision: Optional[str] = None,
    event_type: Optional[str] = None,
    date_from: Optional[float] = None,
    date_to: Optional[float] = None,
) -> dict:
    return {
        "events": audit_store().list_events(
            operator_id=operator_id,
            decision=decision,
            event_type=event_type,
            date_from=date_from,
            date_to=date_to,
        )
    }


@app.get("/audit/events/export")
def export_audit_events(
    operator_id: Optional[str] = None,
    decision: Optional[str] = None,
    event_type: Optional[str] = None,
    date_from: Optional[float] = None,
    date_to: Optional[float] = None,
):
    filters = {
        "operator_id": operator_id,
        "decision": decision,
        "event_type": event_type,
        "date_from": date_from,
        "date_to": date_to,
    }
    events = audit_store().list_events(**filters)
    package = build_api_audit_package(events, filters)
    return JSONResponse(
        content=package,
        headers={"Content-Disposition": 'attachment; filename="orimus-api-audit-package.json"'},
    )


@app.get("/artifacts")
def get_artifacts(
    mission_id: Optional[str] = None,
    report_id: Optional[str] = None,
    source: Optional[str] = None,
    artifact_type: Optional[str] = None,
) -> dict:
    return {
        "artifacts": artifact_store().list_artifacts(
            mission_id=mission_id,
            report_id=report_id,
            source=source,
            artifact_type=artifact_type,
        )
    }


@app.get("/artifacts/{artifact_id}")
def get_artifact_detail(artifact_id: str) -> dict:
    artifact = artifact_store().get_artifact(artifact_id)
    if artifact is None:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact


@app.get("/artifacts/{artifact_id}/download")
def download_artifact(artifact_id: str):
    try:
        artifact_path = artifact_store().artifact_file(artifact_id)
    except ArtifactNotFoundError:
        raise HTTPException(status_code=404, detail="Artifact not found")
    except ArtifactHashMismatchError:
        raise HTTPException(status_code=409, detail="Artifact hash mismatch")

    return FileResponse(
        artifact_path,
        media_type="application/octet-stream",
        filename=artifact_path.name,
    )


@app.get("/runtime/{resource}")
def get_runtime(resource: str) -> dict:
    if resource not in RUNTIME_RESOURCES:
        raise HTTPException(status_code=400, detail="Unsupported runtime resource")

    return annotate_runtime_resource(resource, get_runtime_resource(settings, resource))


@app.get("/reports/latest")
def get_latest_report():
    report_path = settings.latest_report_path
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Mission report not found")

    return JSONResponse(content=read_json_text(report_path))


@app.get("/reports")
def get_reports(
    outcome: Optional[str] = None,
    mission_id: Optional[str] = None,
    sector: Optional[str] = None,
    date_from: Optional[int] = None,
    date_to: Optional[int] = None,
    perception_event_type: Optional[str] = None,
    has_safety_event: Optional[bool] = Query(default=None),
    command_blocked: Optional[bool] = Query(default=None),
) -> dict:
    return {
        "reports": list_reports(
            settings.report_database_path,
            outcome=outcome,
            mission_id=mission_id,
            sector=sector,
            date_from=date_from,
            date_to=date_to,
            perception_event_type=perception_event_type,
            has_safety_event=has_safety_event,
            command_blocked=command_blocked,
        )
    }


@app.get("/reports/{report_id}/export")
def export_report(report_id: str):
    report = get_report(settings.report_database_path, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Mission report not found")

    package = build_evidence_package(report)
    filename = f"orimus-evidence-{report_id}.json"
    return JSONResponse(
        content=package,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/reports/{report_id}/export-bundle")
def export_report_bundle(report_id: str):
    report = get_report(settings.report_database_path, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Mission report not found")

    artifacts = artifact_store().list_artifacts(report_id=report_id)
    try:
        bundle_bytes, _manifest = build_evidence_bundle(report, artifacts)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"Artifact file not found: {error}")

    filename = f"orimus-evidence-bundle-{report_id}.zip"
    return Response(
        content=bundle_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/reports/{report_id}/replay")
def get_report_replay(
    report_id: str,
    category: Optional[str] = None,
    since: Optional[float] = None,
    operator_id: Optional[str] = None,
    command_id: Optional[str] = None,
) -> dict:
    report = get_report(settings.report_database_path, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Mission report not found")

    frames = build_replay_frames(
        report,
        category=category,
        since=since,
        operator_id=operator_id,
        command_id=command_id,
    )
    return {
        "report_id": report_id,
        "frame_count": len(frames),
        "frames": frames,
    }


@app.get("/reports/{report_id}")
def get_report_detail(report_id: str) -> dict:
    report = get_report(settings.report_database_path, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Mission report not found")

    return report


def read_mission_summary(mission_file: Path) -> dict:
    mission_data = read_yaml_file(mission_file)
    return {
        "mission_id": mission_data.get("mission_id", mission_file.stem),
        "name": mission_data.get("name", mission_file.stem),
        "sector": mission_data.get("sector", ""),
        "path": str(mission_file),
        "step_count": len(mission_data.get("steps", [])),
    }


def read_yaml_file(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def read_json_text(path: Path):
    import json

    return json.loads(path.read_text(encoding="utf-8"))


def normalize_operator_id(value: str | None) -> str:
    operator_id = (value or "").strip()
    return operator_id if operator_id else "anonymous"


def audit_store() -> BackendAuditStore:
    return BackendAuditStore(settings.report_database_path)


def artifact_store() -> ArtifactStore:
    store = ArtifactStore(settings.report_database_path, settings.artifact_root)
    store.initialize()
    return store


def request_source_ip(request: Request) -> str | None:
    if not settings.log_source_ip:
        return None
    if request.client is None:
        return None
    return request.client.host
