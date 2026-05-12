from enum import Enum
from typing import Any


class EventSeverity(str, Enum):
    INFO = "info"
    NOTICE = "notice"
    WARNING = "warning"
    CRITICAL = "critical"


EVENT_SEVERITY_VALUES = [severity.value for severity in EventSeverity]


def event_severity_schema() -> dict:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://orimus.local/schemas/event_severity.schema.json",
        "title": "ORIMUS Event Severity",
        "description": "Canonical ORIMUS event severity vocabulary.",
        "type": "string",
        "enum": EVENT_SEVERITY_VALUES,
    }


def severity_for_readiness(status: str, requirement: str = "required") -> EventSeverity:
    if status == "ready":
        return EventSeverity.INFO
    if status == "degraded":
        return EventSeverity.WARNING
    if status == "not_ready" and requirement == "required":
        return EventSeverity.CRITICAL
    if status == "not_ready":
        return EventSeverity.WARNING
    return EventSeverity.INFO


def severity_for_api_decision(decision: str | None) -> EventSeverity:
    return EventSeverity.CRITICAL if decision == "denied" else EventSeverity.INFO


def severity_for_safety_event(event: dict[str, Any]) -> EventSeverity:
    raw = str(event.get("severity") or "").lower()
    if event.get("command_blocked") is True:
        return EventSeverity.CRITICAL
    if raw in {"critical", "error", "fatal"}:
        return EventSeverity.CRITICAL
    if raw in {"warning", "warn", "degraded"}:
        return EventSeverity.WARNING
    return EventSeverity.NOTICE


def severity_for_mission_event(event: dict[str, Any]) -> EventSeverity:
    text = " ".join(
        str(event.get(key) or "").lower()
        for key in ["event_type", "message", "state"]
    )
    if any(token in text for token in ["failed", "error", "emergency"]):
        return EventSeverity.CRITICAL
    if any(token in text for token in ["canceled", "paused", "blocked"]):
        return EventSeverity.WARNING
    if any(token in text for token in ["started", "running", "completed", "step"]):
        return EventSeverity.NOTICE
    return EventSeverity.INFO


def severity_for_perception_event(event: dict[str, Any]) -> EventSeverity:
    event_type = str(event.get("event_type") or "").lower()
    if any(token in event_type for token in ["human", "person", "vehicle", "animal"]):
        return EventSeverity.WARNING
    return EventSeverity.NOTICE


def severity_for_payload_result(result: dict[str, Any]) -> EventSeverity:
    text = " ".join(
        str(result.get(key) or "").lower()
        for key in ["result_type", "summary", "state"]
    )
    if any(token in text for token in ["failed", "error", "hazard"]):
        return EventSeverity.CRITICAL
    if any(token in text for token in ["detected", "warning", "anomaly"]):
        return EventSeverity.WARNING
    return EventSeverity.NOTICE


def severity_for_robot_command(command: dict[str, Any]) -> EventSeverity:
    return EventSeverity.NOTICE if command.get("topic") == "robot/command" else EventSeverity.INFO


def severity_for_runtime_event(event: dict[str, Any]) -> EventSeverity:
    category = str(event.get("category") or "").lower()
    if category == "safety":
        return severity_for_safety_event(event)
    if category == "perception":
        return severity_for_perception_event(event)
    if category == "payload":
        return severity_for_payload_result(event)
    if category == "command":
        return severity_for_robot_command(event)
    return severity_for_mission_event(event)


def annotate_runtime_resource(resource: str, data: dict) -> dict:
    if resource == "events":
        return {"events": [annotate_runtime_event(event) for event in data.get("events", [])]}
    if "events" in data and isinstance(data["events"], list):
        data = dict(data)
        data["events"] = [annotate_runtime_event(event) for event in data["events"]]
    if isinstance(data.get("safety"), dict):
        data = dict(data)
        data["safety"] = annotate_safety_event(data["safety"])
    if isinstance(data.get("perception"), dict):
        data = dict(data)
        data["perception"] = annotate_perception_event(data["perception"])
    return data


def annotate_runtime_event(event: dict) -> dict:
    annotated = dict(event)
    annotated["severity"] = str(severity_for_runtime_event(annotated).value)
    return annotated


def annotate_safety_event(event: dict) -> dict:
    annotated = dict(event)
    annotated["severity"] = str(severity_for_safety_event(annotated).value)
    return annotated


def annotate_perception_event(event: dict) -> dict:
    annotated = dict(event)
    annotated["severity"] = str(severity_for_perception_event(annotated).value)
    return annotated
