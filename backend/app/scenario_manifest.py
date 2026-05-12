from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


SUPPORTED_SCENARIO_MANIFEST_VERSION = 1


class BackendPolicyDenialExpectation(BaseModel):
    operator_id: str = "anonymous"
    command_type: str
    status_code: int = 403


class ScenarioExpectation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    outcome: str | None = None
    min_mission_events: int = 0
    min_robot_commands: int = 0
    min_payload_results: int = 0
    min_perception_events: int = 0
    artifact_required: bool = False
    safety_event_required: bool = False
    backend_policy_denial: BackendPolicyDenialExpectation | None = None

    @model_validator(mode="after")
    def validate_expectation_mode(self):
        if self.backend_policy_denial is not None:
            return self
        if not self.outcome:
            raise ValueError("scenario expected.outcome is required for ROS scenarios")
        return self


class Scenario(BaseModel):
    id: str = Field(min_length=1)
    mission_path: str = Field(min_length=1)
    timeout_sec: int = Field(default=20, gt=0)
    expected: ScenarioExpectation

    @property
    def is_backend_policy_scenario(self) -> bool:
        return self.expected.backend_policy_denial is not None


class ScenarioManifest(BaseModel):
    version: int
    scenarios: list[Scenario] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_version(self):
        if self.version != SUPPORTED_SCENARIO_MANIFEST_VERSION:
            raise ValueError(
                f"unsupported scenario manifest version {self.version}; "
                f"expected {SUPPORTED_SCENARIO_MANIFEST_VERSION}"
            )
        return self


def load_scenario_manifest(path: Path) -> ScenarioManifest:
    try:
        with path.open("r", encoding="utf-8") as file:
            data: dict[str, Any] = yaml.safe_load(file) or {}
    except yaml.YAMLError as error:
        raise ValueError(f"{path}: invalid YAML: {error}") from error

    try:
        return ScenarioManifest.model_validate(data)
    except ValidationError as error:
        raise ValueError(f"{path}: {error}") from error


def find_scenario(manifest: ScenarioManifest, scenario_id: str) -> Scenario:
    for scenario in manifest.scenarios:
        if scenario.id == scenario_id:
            return scenario
    raise ValueError(f"unknown scenario '{scenario_id}'")
