import json
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


class MissionStep(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str = Field(min_length=1)
    target: Literal["robot", "payload"]
    command_type: str = Field(min_length=1)
    duration_sec: float = Field(gt=0)
    linear_x: float | None = None
    linear_y: float | None = None
    yaw_rate: float | None = None
    max_speed: float | None = None
    payload_id: str | None = None
    payload_type: str | None = None
    target_x: float | None = None
    target_y: float | None = None
    target_z: float | None = None

    @model_validator(mode="after")
    def validate_target_specific_fields(self):
        if self.target == "payload":
            missing = [
                field_name
                for field_name in ["payload_id", "payload_type"]
                if not getattr(self, field_name)
            ]
            if missing:
                raise ValueError(
                    f"payload step requires: {', '.join(missing)}"
                )
        if self.target == "robot" and self.command_type == "walk_velocity":
            missing = [
                field_name
                for field_name in ["linear_x", "linear_y", "yaw_rate", "max_speed"]
                if getattr(self, field_name) is None
            ]
            if missing:
                raise ValueError(
                    f"walk_velocity robot step requires: {', '.join(missing)}"
                )
        return self


class MissionConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    mission_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    sector: str = Field(min_length=1)
    steps: list[MissionStep] = Field(min_length=1)


def validate_mission_file(path: Path) -> MissionConfig:
    try:
        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}
    except yaml.YAMLError as error:
        raise ValueError(f"{path}: invalid YAML: {error}") from error

    try:
        return MissionConfig.model_validate(data)
    except ValidationError as error:
        raise ValueError(f"{path}: {error}") from error


def validate_mission_directory(path: Path) -> list[MissionConfig]:
    mission_files = sorted(path.glob("*.yaml"))
    if not mission_files:
        raise ValueError(f"{path}: no mission YAML files found")
    return [validate_mission_file(mission_file) for mission_file in mission_files]


def mission_schema_json() -> str:
    return json.dumps(MissionConfig.model_json_schema(), indent=2, sort_keys=True)
