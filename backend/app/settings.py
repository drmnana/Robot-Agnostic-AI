from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mission_config_dir: Path = Field(
        default=Path("/workspace/configs/missions"),
        alias="ORIMUS_MISSION_CONFIG_DIR",
    )
    latest_report_path: Path = Field(
        default=Path("/workspace/reports/latest_mission_report.json"),
        alias="ORIMUS_LATEST_REPORT_PATH",
    )

