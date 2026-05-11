import json
from typing import Any


def build_replay_frames(
    report: dict,
    category: str | None = None,
    since: float | None = None,
    operator_id: str | None = None,
    command_id: str | None = None,
) -> list[dict]:
    frames = sorted(build_all_frames(report), key=lambda frame: frame["timestamp_sec"])
    filtered = [
        frame
        for frame in frames
        if frame_matches(frame, category, since, operator_id, command_id)
    ]
    for index, frame in enumerate(filtered):
        frame["frame_index"] = index
    return filtered


def build_all_frames(report: dict) -> list[dict]:
    frames = []

    for event in report.get("mission_events", []):
        details = parse_json_object(event.get("details_json", ""))
        frames.append(
            base_frame(
                stamp=event.get("stamp"),
                category="mission",
                title=event.get("event_type") or "mission_event",
                message=event.get("message") or "",
                operator_id=details.get("operator_id"),
                command_id=None,
                artifact_url=None,
                artifact_hash=None,
                source_id=event.get("event_id"),
            )
        )

    for command in report.get("robot_commands", []):
        frames.append(
            base_frame(
                stamp=command.get("stamp"),
                category="command",
                title=command.get("command_type") or "robot_command",
                message=command.get("topic") or "",
                operator_id=command.get("operator_id") or operator_from_details(command),
                command_id=command.get("command_id"),
                artifact_url=None,
                artifact_hash=None,
                source_id=command.get("command_id"),
            )
        )

    for event in report.get("safety_events", []):
        frames.append(
            base_frame(
                stamp=event.get("stamp"),
                category="safety",
                title=event.get("rule") or "safety_event",
                message=event.get("message") or "",
                operator_id=event.get("operator_id"),
                command_id=event.get("command_id"),
                artifact_url=None,
                artifact_hash=None,
                source_id=event.get("event_id"),
            )
        )

    for event in report.get("perception_events", []):
        frames.append(
            base_frame(
                stamp=event.get("stamp"),
                category="perception",
                title=event.get("event_type") or "perception_event",
                message=f"{event.get('source') or 'sensor'} confidence {event.get('confidence')}",
                operator_id=None,
                command_id=None,
                artifact_url=event.get("evidence_artifact_url") or None,
                artifact_hash=event.get("evidence_hash") or None,
                source_id=event.get("event_id"),
            )
        )

    for result in report.get("payload_results", []):
        frames.append(
            base_frame(
                stamp=result.get("stamp"),
                category="payload",
                title=result.get("result_type") or "payload_result",
                message=result.get("summary") or "",
                operator_id=None,
                command_id=None,
                artifact_url=None,
                artifact_hash=None,
                source_id=result.get("result_id"),
            )
        )

    return frames


def base_frame(
    *,
    stamp: dict | None,
    category: str,
    title: str,
    message: str,
    operator_id: str | None,
    command_id: str | None,
    artifact_url: str | None,
    artifact_hash: str | None,
    source_id: str | None,
) -> dict:
    return {
        "frame_index": 0,
        "timestamp_sec": stamp_seconds(stamp),
        "category": category,
        "title": title,
        "message": message,
        "operator_id": operator_id or "",
        "command_id": command_id or "",
        "artifact_url": artifact_url,
        "artifact_hash": artifact_hash,
        "source_id": source_id or "",
    }


def frame_matches(
    frame: dict,
    category: str | None,
    since: float | None,
    operator_id: str | None,
    command_id: str | None,
) -> bool:
    if category and frame["category"] != category:
        return False
    if since is not None and frame["timestamp_sec"] < since:
        return False
    if operator_id and frame.get("operator_id") != operator_id:
        return False
    if command_id and frame.get("command_id") != command_id:
        return False
    return True


def operator_from_details(command: dict[str, Any]) -> str:
    details = parse_json_object(command.get("details_json", ""))
    return details.get("operator_id") or "anonymous"


def parse_json_object(value: str) -> dict:
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def stamp_seconds(stamp: dict | None) -> float:
    if not isinstance(stamp, dict):
        return 0.0
    return float(stamp.get("sec") or 0) + float(stamp.get("nanosec") or 0) / 1_000_000_000
