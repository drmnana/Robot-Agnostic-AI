from pathlib import Path
from typing import Optional

import yaml
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from .evidence_package import build_evidence_package
from .mission_bridge_client import get_runtime_resource, send_mission_command
from .report_store import get_report, list_reports
from .settings import Settings


settings = Settings()
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
def control_mission(mission_id: str, command_type: str) -> dict:
    if command_type not in MISSION_COMMANDS:
        raise HTTPException(status_code=400, detail="Unsupported mission command")

    return send_mission_command(settings, mission_id, command_type)


@app.get("/runtime/{resource}")
def get_runtime(resource: str) -> dict:
    if resource not in RUNTIME_RESOURCES:
        raise HTTPException(status_code=400, detail="Unsupported runtime resource")

    return get_runtime_resource(settings, resource)


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
