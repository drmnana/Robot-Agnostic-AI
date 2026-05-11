from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mission_config_dir: Path = Field(
        default=Path("/workspace/configs/missions"),
        alias="ORIMUS_MISSION_CONFIG_DIR",
    )
    operator_policy_path: Path = Field(
        default=Path("/workspace/configs/operator_policy.yaml"),
        alias="ORIMUS_OPERATOR_POLICY_PATH",
    )
    latest_report_path: Path = Field(
        default=Path("/workspace/reports/latest_mission_report.json"),
        alias="ORIMUS_LATEST_REPORT_PATH",
    )
    report_database_path: Path = Field(
        default=Path("/workspace/data/orimus.db"),
        alias="ORIMUS_REPORT_DATABASE_PATH",
    )
    artifact_root: Path = Field(
        default=Path("/workspace/data/artifacts"),
        alias="ORIMUS_ARTIFACT_ROOT",
    )
    log_source_ip: bool = Field(
        default=True,
        alias="ORIMUS_LOG_SOURCE_IP",
    )
    mission_api_bridge_url: str = Field(
        default="http://ros2-dev:8010",
        alias="ORIMUS_MISSION_API_BRIDGE_URL",
    )
