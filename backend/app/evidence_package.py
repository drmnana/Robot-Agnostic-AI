import hashlib
import json
from datetime import datetime, timezone


EVIDENCE_PACKAGE_SCHEMA_VERSION = "1.0"


def build_evidence_package(report: dict) -> dict:
    mission = report.get("mission") or {}
    package = {
        "package_type": "orimus_evidence_package",
        "schema_version": EVIDENCE_PACKAGE_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
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
