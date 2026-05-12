import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import httpx

from .event_severity import severity_for_readiness
from .mission_schema import validate_mission_directory
from .operator_policy import read_operator_policy
from .settings import Settings


READINESS_CACHE_TTL_SEC = 10
CheckStatus = str


@dataclass(frozen=True)
class ReadinessCheck:
    name: str
    status: CheckStatus
    requirement: str
    message: str

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status,
            "requirement": self.requirement,
            "severity": severity_for_readiness(self.status, self.requirement).value,
            "message": self.message,
        }


@dataclass
class ReadinessCache:
    generated_at: float = 0.0
    checks: list[ReadinessCheck] | None = None


_readiness_cache = ReadinessCache()


def clear_readiness_cache() -> None:
    _readiness_cache.generated_at = 0.0
    _readiness_cache.checks = None


def build_readiness(
    settings: Settings,
    fresh: bool = False,
    now_fn: Callable[[], float] = time.time,
) -> dict:
    now = now_fn()
    expensive_checks, cached = cached_expensive_checks(settings, fresh=fresh, now=now)
    cheap_checks = run_cheap_checks(settings)
    checks = cheap_checks + expensive_checks

    return {
        "status": overall_status(checks),
        "cached": cached,
        "cache_ttl_sec": READINESS_CACHE_TTL_SEC,
        "generated_at": now,
        "checks": [check.as_dict() for check in checks],
    }


def cached_expensive_checks(
    settings: Settings,
    fresh: bool,
    now: float,
) -> tuple[list[ReadinessCheck], bool]:
    if (
        not fresh
        and _readiness_cache.checks is not None
        and now - _readiness_cache.generated_at < READINESS_CACHE_TTL_SEC
    ):
        return _readiness_cache.checks, True

    checks = run_expensive_checks(settings)
    _readiness_cache.generated_at = now
    _readiness_cache.checks = checks
    return checks, False


def run_cheap_checks(settings: Settings) -> list[ReadinessCheck]:
    checks = [
        ReadinessCheck(
            name="backend_process",
            status="ready",
            requirement="required",
            message="Backend process is responsive.",
        ),
        check_path_exists("mission_config_dir", settings.mission_config_dir),
        check_parent_exists("report_database_parent", settings.report_database_path),
        check_parent_exists("latest_report_parent", settings.latest_report_path),
    ]
    return checks


def run_expensive_checks(settings: Settings) -> list[ReadinessCheck]:
    return [
        check_mission_yaml(settings.mission_config_dir),
        check_sqlite_database(settings.report_database_path),
        check_directory_writable("artifact_root", settings.artifact_root),
        check_directory_writable("latest_report_parent", settings.latest_report_path.parent),
        check_operator_policy(settings.operator_policy_path),
        check_ros_bridge(settings.mission_api_bridge_url),
    ]


def check_path_exists(name: str, path: Path) -> ReadinessCheck:
    if path.exists():
        return ReadinessCheck(name, "ready", "required", f"{path} exists.")
    return ReadinessCheck(name, "not_ready", "required", f"{path} does not exist.")


def check_parent_exists(name: str, path: Path) -> ReadinessCheck:
    parent = path.parent
    if parent.exists():
        return ReadinessCheck(name, "ready", "required", f"{parent} exists.")
    return ReadinessCheck(name, "not_ready", "required", f"{parent} does not exist.")


def check_mission_yaml(mission_config_dir: Path) -> ReadinessCheck:
    try:
        missions = validate_mission_directory(mission_config_dir)
    except Exception as error:
        return ReadinessCheck(
            "mission_yaml_validation",
            "not_ready",
            "required",
            f"Mission YAML validation failed: {error}",
        )

    return ReadinessCheck(
        "mission_yaml_validation",
        "ready",
        "required",
        f"{len(missions)} mission YAML files validated.",
    )


def check_sqlite_database(database_path: Path) -> ReadinessCheck:
    try:
        database_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(database_path) as connection:
            connection.execute("PRAGMA user_version")
    except Exception as error:
        return ReadinessCheck(
            "sqlite_database",
            "not_ready",
            "required",
            f"SQLite database is not reachable: {error}",
        )

    return ReadinessCheck(
        "sqlite_database",
        "ready",
        "required",
        f"{database_path} is reachable.",
    )


def check_directory_writable(name: str, directory: Path) -> ReadinessCheck:
    probe_path = directory / ".orimus_readiness_probe"
    try:
        directory.mkdir(parents=True, exist_ok=True)
        probe_path.write_text("ok", encoding="utf-8")
        probe_path.unlink(missing_ok=True)
    except Exception as error:
        return ReadinessCheck(
            name,
            "not_ready",
            "required",
            f"{directory} is not writable: {error}",
        )

    return ReadinessCheck(name, "ready", "required", f"{directory} is writable.")


def check_operator_policy(policy_path: Path) -> ReadinessCheck:
    try:
        policy = read_operator_policy(policy_path)
    except Exception as error:
        return ReadinessCheck(
            "operator_policy",
            "not_ready",
            "required",
            f"Operator policy failed to parse: {error}",
        )

    operator_count = len(policy.get("operators", {}))
    return ReadinessCheck(
        "operator_policy",
        "ready",
        "required",
        f"{operator_count} operator policy records loaded.",
    )


def check_ros_bridge(bridge_url: str) -> ReadinessCheck:
    url = bridge_url.rstrip("/") + "/health"
    try:
        response = httpx.get(url, timeout=1.0)
        response.raise_for_status()
    except Exception as error:
        return ReadinessCheck(
            "ros_bridge",
            "degraded",
            "optional",
            f"ROS bridge health check unavailable: {error}",
        )

    return ReadinessCheck("ros_bridge", "ready", "optional", "ROS bridge responded.")


def overall_status(checks: list[ReadinessCheck]) -> str:
    if any(check.status == "not_ready" and check.requirement == "required" for check in checks):
        return "not_ready"
    if any(check.status != "ready" for check in checks):
        return "degraded"
    return "ready"
