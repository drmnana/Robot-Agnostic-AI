import copy
import hashlib
import json
import time

from .evidence_verifier import (
    EXIT_HASH_MISMATCH,
    EXIT_SCHEMA_MISMATCH,
    EXIT_SEMANTIC_FAILURE,
    EXIT_VALID,
    VerificationResult,
)


API_AUDIT_PACKAGE_SCHEMA_VERSION = "1.0"
API_AUDIT_PACKAGE_TYPE = "orimus_api_audit_package"


def build_api_audit_package(
    events: list[dict],
    filters: dict,
    generated_at_sec: float | None = None,
) -> dict:
    sorted_events = sorted(events, key=lambda event: event.get("created_at_sec") or 0)
    package = {
        "package_type": API_AUDIT_PACKAGE_TYPE,
        "schema_version": API_AUDIT_PACKAGE_SCHEMA_VERSION,
        "export_hash_algorithm": "SHA-256",
        "export_hash": "",
        "generated_at_sec": generated_at_sec if generated_at_sec is not None else time.time(),
        "filters": normalize_filters(filters),
        "summary": build_api_audit_summary(sorted_events),
        "events": sorted_events,
    }
    package["export_hash"] = hash_api_audit_package(package)
    return package


def normalize_filters(filters: dict) -> dict:
    return {
        key: value
        for key, value in filters.items()
        if value is not None and value != ""
    }


def build_api_audit_summary(events: list[dict]) -> dict:
    allowed_count = sum(1 for event in events if event.get("decision") == "allowed")
    denied_count = sum(1 for event in events if event.get("decision") == "denied")
    return {
        "event_count": len(events),
        "allowed_count": allowed_count,
        "denied_count": denied_count,
    }


def hash_api_audit_package(package: dict) -> str:
    hash_input = copy.deepcopy(package)
    hash_input["export_hash"] = ""
    canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify_api_audit_package(package: dict) -> VerificationResult:
    schema_errors = validate_api_audit_schema(package)
    if schema_errors:
        return VerificationResult(False, EXIT_SCHEMA_MISMATCH, schema_errors)

    expected_hash = hash_api_audit_package(package)
    if package.get("export_hash") != expected_hash:
        return VerificationResult(False, EXIT_HASH_MISMATCH, ["export_hash mismatch"])

    semantic_errors = validate_api_audit_semantics(package)
    if semantic_errors:
        return VerificationResult(False, EXIT_SEMANTIC_FAILURE, semantic_errors)

    return VerificationResult(True, EXIT_VALID, [])


def validate_api_audit_schema(package: dict) -> list[str]:
    errors = []
    package_type = package.get("package_type")
    if package_type != API_AUDIT_PACKAGE_TYPE:
        if package_type == "orimus_evidence_package":
            errors.append(
                "wrong package type: this verifier is for ORIMUS API Audit Package JSON, "
                "but you supplied an ORIMUS Evidence Package"
            )
        else:
            errors.append(f"package_type must be {API_AUDIT_PACKAGE_TYPE}")
    if package.get("schema_version") != API_AUDIT_PACKAGE_SCHEMA_VERSION:
        errors.append(f"schema_version must be {API_AUDIT_PACKAGE_SCHEMA_VERSION}")
    if package.get("export_hash_algorithm") != "SHA-256":
        errors.append("export_hash_algorithm must be SHA-256")
    if not isinstance(package.get("filters"), dict):
        errors.append("filters must be an object")
    if not isinstance(package.get("summary"), dict):
        errors.append("summary must be an object")
    if not isinstance(package.get("events"), list):
        errors.append("events must be an array")
    return errors


def validate_api_audit_semantics(package: dict) -> list[str]:
    errors = []
    events = package.get("events") or []
    summary = package.get("summary") or {}
    expected_summary = build_api_audit_summary(events)
    for key, expected_value in expected_summary.items():
        if summary.get(key) != expected_value:
            errors.append(f"summary.{key} expected {expected_value}")

    if not timestamps_are_monotonic(events):
        errors.append("events timestamps are not monotonic")

    for index, event in enumerate(events):
        errors.extend(validate_api_audit_event(event, index))
    return errors


def validate_api_audit_event(event: dict, index: int) -> list[str]:
    errors = []
    required_fields = [
        "id",
        "created_at_sec",
        "event_type",
        "operator_id",
        "decision",
        "request_path",
        "retention_class",
    ]
    for field in required_fields:
        if event.get(field) in (None, ""):
            errors.append(f"events[{index}].{field} is required")
    if event.get("decision") not in {"allowed", "denied"}:
        errors.append(f"events[{index}].decision must be allowed or denied")
    if not isinstance(event.get("created_at_sec"), (int, float)):
        errors.append(f"events[{index}].created_at_sec must be numeric")
    return errors


def timestamps_are_monotonic(events: list[dict]) -> bool:
    previous = None
    for event in events:
        current = event.get("created_at_sec")
        if current is None:
            continue
        if previous is not None and current < previous:
            return False
        previous = current
    return True
