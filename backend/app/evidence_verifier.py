from dataclasses import dataclass, field

from .evidence_package import (
    EVIDENCE_PACKAGE_SCHEMA_VERSION,
    build_summary,
    hash_evidence_package,
    hash_mission_report,
)


EXIT_VALID = 0
EXIT_HASH_MISMATCH = 1
EXIT_SCHEMA_MISMATCH = 2
EXIT_SEMANTIC_FAILURE = 3


@dataclass
class VerificationResult:
    valid: bool
    exit_code: int
    errors: list[str] = field(default_factory=list)


def verify_evidence_package(package: dict) -> VerificationResult:
    schema_errors = validate_schema(package)
    if schema_errors:
        return VerificationResult(False, EXIT_SCHEMA_MISMATCH, schema_errors)

    hash_errors = validate_hashes(package)
    if hash_errors:
        return VerificationResult(False, EXIT_HASH_MISMATCH, hash_errors)

    semantic_errors = validate_semantics(package)
    if semantic_errors:
        return VerificationResult(False, EXIT_SEMANTIC_FAILURE, semantic_errors)

    return VerificationResult(True, EXIT_VALID, [])


def validate_schema(package: dict) -> list[str]:
    errors = []
    if package.get("package_type") != "orimus_evidence_package":
        errors.append("package_type must be orimus_evidence_package")
    if package.get("schema_version") != EVIDENCE_PACKAGE_SCHEMA_VERSION:
        errors.append(
            f"schema_version must be {EVIDENCE_PACKAGE_SCHEMA_VERSION}"
        )
    if package.get("export_hash_algorithm") != "SHA-256":
        errors.append("export_hash_algorithm must be SHA-256")
    if not isinstance(package.get("mission_report"), dict):
        errors.append("mission_report must be an object")
    if not isinstance(package.get("summary"), dict):
        errors.append("summary must be an object")
    if not isinstance(package.get("artifact_manifest"), list):
        errors.append("artifact_manifest must be an array")
    return errors


def validate_hashes(package: dict) -> list[str]:
    errors = []
    expected_export_hash = hash_evidence_package(package)
    if package.get("export_hash") != expected_export_hash:
        errors.append("export_hash mismatch")

    report = package.get("mission_report") or {}
    expected_report_hash = hash_mission_report(report)
    if report.get("content_hash") != expected_report_hash:
        errors.append("mission_report content_hash mismatch")
    if package.get("report", {}).get("content_hash") != report.get("content_hash"):
        errors.append("package report.content_hash does not match mission_report")
    return errors


def validate_semantics(package: dict) -> list[str]:
    errors = []
    report = package.get("mission_report") or {}

    expected_summary = build_summary(report)
    summary = package.get("summary") or {}
    for key, expected_value in expected_summary.items():
        if summary.get(key) != expected_value:
            errors.append(f"summary.{key} expected {expected_value}")

    for collection_name in [
        "mission_states",
        "mission_events",
        "robot_commands",
        "safety_events",
        "perception_events",
        "payload_results",
    ]:
        if not timestamps_are_monotonic(report.get(collection_name, [])):
            errors.append(f"{collection_name} timestamps are not monotonic")

    command_ids = {
        command.get("command_id")
        for command in report.get("robot_commands", [])
        if command.get("command_id")
    }
    for event in report.get("safety_events", []):
        command_id = event.get("command_id")
        if command_id and command_id not in command_ids:
            errors.append(
                f"safety event {event.get('event_id', '')} references missing command_id {command_id}"
            )

    return errors


def timestamps_are_monotonic(items: list[dict]) -> bool:
    previous = None
    for item in items:
        current = stamp_value(item.get("stamp"))
        if current is None:
            continue
        if previous is not None and current < previous:
            return False
        previous = current
    return True


def stamp_value(stamp: dict | None) -> tuple[int, int] | None:
    if not isinstance(stamp, dict):
        return None
    sec = stamp.get("sec")
    nanosec = stamp.get("nanosec")
    if sec is None or nanosec is None:
        return None
    return (int(sec), int(nanosec))
