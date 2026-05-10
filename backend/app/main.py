from pathlib import Path

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from .settings import Settings


settings = Settings()
app = FastAPI(title="ORIMUS Backend", version="0.1.0")


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


@app.get("/reports/latest")
def get_latest_report():
    report_path = settings.latest_report_path
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Mission report not found")

    return JSONResponse(content=read_json_text(report_path))


def read_mission_summary(mission_file: Path) -> dict:
    mission_data = read_yaml_file(mission_file)
    return {
        "mission_id": mission_data.get("mission_id", mission_file.stem),
        "name": mission_data.get("name", mission_file.stem),
        "path": str(mission_file),
        "step_count": len(mission_data.get("steps", [])),
    }


def read_yaml_file(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def read_json_text(path: Path):
    import json

    return json.loads(path.read_text(encoding="utf-8"))

