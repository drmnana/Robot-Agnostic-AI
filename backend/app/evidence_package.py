import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone


EVIDENCE_PACKAGE_SCHEMA_VERSION = "1.0"


def build_evidence_package(report: dict, generated_at: str | None = None) -> dict:
    mission = report.get("mission") or {}
    package = {
        "package_type": "orimus_evidence_package",
        "schema_version": EVIDENCE_PACKAGE_SCHEMA_VERSION,
        "generated_at": generated_at or stable_package_timestamp(report),
        "export_hash_algorithm": "SHA-256",
        "export_hash": "",
        "report": {
            "report_id": report.get("report_id", ""),
            "content_hash": report.get("content_hash", ""),
            "content_hash_algorithm": "SHA-256",
        },
        "mission": {
            "mission_id": mission.get("mission_id", ""),
            "name": mission.get("name", ""),
            "sector": mission.get("sector") or extract_sector(report),
            "outcome": mission.get("state", ""),
            "started_at": first_stamp(report.get("mission_states", [])),
            "ended_at": mission.get("stamp"),
        },
        "summary": build_summary(report),
        "artifact_manifest": build_artifact_manifest(report),
        "mission_report": report,
    }
    package["export_hash"] = hash_evidence_package(package)
    return package


def hash_evidence_package(package: dict) -> str:
    hash_input = dict(package)
    hash_input["export_hash"] = ""
    canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def hash_mission_report(report: dict) -> str:
    hash_input = deepcopy(report)
    hash_input.pop("content_hash", None)
    canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_summary(report: dict) -> dict:
    return {
        "mission_state_count": len(report.get("mission_states", [])),
        "mission_event_count": len(report.get("mission_events", [])),
        "robot_command_count": len(report.get("robot_commands", [])),
        "safety_event_count": len(report.get("safety_events", [])),
        "perception_event_count": len(report.get("perception_events", [])),
        "payload_result_count": len(report.get("payload_results", [])),
    }


def build_artifact_manifest(report: dict) -> list[dict]:
    artifacts = []
    for event in report.get("perception_events", []):
        artifacts.append(
            {
                "source_event_id": event.get("event_id", ""),
                "event_type": event.get("event_type", ""),
                "source": event.get("source", ""),
                "artifact_url": event.get("evidence_artifact_url") or None,
                "artifact_hash": event.get("evidence_hash") or None,
                "artifact_hash_algorithm": "SHA-256"
                if event.get("evidence_hash")
                else None,
            }
        )
    return artifacts


def first_stamp(items: list[dict]) -> dict | None:
    if not items:
        return None
    return items[0].get("stamp")


def stable_package_timestamp(report: dict) -> str:
    stamp = (report.get("mission") or {}).get("stamp") or first_stamp(report.get("mission_states", []))
    if isinstance(stamp, dict) and stamp.get("sec") is not None:
        seconds = float(stamp.get("sec") or 0) + float(stamp.get("nanosec") or 0) / 1_000_000_000
        return datetime.fromtimestamp(seconds, timezone.utc).isoformat()
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def extract_sector(report: dict) -> str:
    for event in report.get("mission_events", []):
        details = parse_json_object(event.get("details_json", ""))
        sector = details.get("sector")
        if sector:
            return str(sector)
    return ""


def parse_json_object(value: str) -> dict:
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}
