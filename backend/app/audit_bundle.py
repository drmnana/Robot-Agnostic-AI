import hashlib
import json
import zipfile
from pathlib import Path

from .audit_package import build_api_audit_package, hash_api_audit_package, verify_api_audit_package
from .evidence_bundle import build_deterministic_zip, canonical_json_bytes
from .evidence_verifier import (
    EXIT_HASH_MISMATCH,
    EXIT_SCHEMA_MISMATCH,
    EXIT_SEMANTIC_FAILURE,
    EXIT_VALID,
    VerificationResult,
)


API_AUDIT_BUNDLE_SCHEMA_VERSION = "1.0"
API_AUDIT_BUNDLE_MANIFEST_PATH = "manifest.json"
API_AUDIT_BUNDLE_PACKAGE_PATH = "api_audit_package.json"
API_AUDIT_BUNDLE_MANIFEST_TYPE = "orimus_api_audit_bundle_manifest"


def build_api_audit_bundle(events: list[dict], filters: dict) -> tuple[bytes, dict]:
    package = build_api_audit_package(
        events,
        filters,
        generated_at_sec=stable_generated_at_sec(events),
    )
    package_bytes = canonical_json_bytes(package)
    manifest = build_api_audit_bundle_manifest(package)
    manifest_bytes = canonical_json_bytes(manifest)
    bundle_bytes = build_deterministic_zip(
        [
            (API_AUDIT_BUNDLE_PACKAGE_PATH, package_bytes),
            (API_AUDIT_BUNDLE_MANIFEST_PATH, manifest_bytes),
        ]
    )
    return bundle_bytes, manifest


def stable_generated_at_sec(events: list[dict]) -> float:
    timestamps = [
        event.get("created_at_sec")
        for event in events
        if isinstance(event.get("created_at_sec"), (int, float))
    ]
    if not timestamps:
        return 0.0
    return float(max(timestamps))


def build_api_audit_bundle_manifest(package: dict) -> dict:
    manifest = {
        "manifest_type": API_AUDIT_BUNDLE_MANIFEST_TYPE,
        "schema_version": API_AUDIT_BUNDLE_SCHEMA_VERSION,
        "generated_at_sec": package["generated_at_sec"],
        "bundle_hash_algorithm": "SHA-256",
        "bundle_hash": "",
        "api_audit_package_path": API_AUDIT_BUNDLE_PACKAGE_PATH,
        "api_audit_package_hash": hash_api_audit_package(package),
        "event_count": package["summary"]["event_count"],
        "filters": package["filters"],
    }
    manifest["bundle_hash"] = hash_api_audit_bundle_manifest(manifest)
    return manifest


def hash_api_audit_bundle_manifest(manifest: dict) -> str:
    hash_input = dict(manifest)
    hash_input["bundle_hash"] = ""
    return hashlib.sha256(canonical_json_bytes(hash_input)).hexdigest()


def verify_api_audit_bundle(bundle_path: Path) -> VerificationResult:
    try:
        with zipfile.ZipFile(bundle_path, "r") as bundle:
            names = bundle.namelist()
            if names != sorted(names):
                return VerificationResult(False, EXIT_HASH_MISMATCH, ["bundle zip entries are not sorted"])
            if "evidence_package.json" in names:
                return VerificationResult(
                    False,
                    EXIT_SCHEMA_MISMATCH,
                    [
                        "wrong bundle type: this verifier is for ORIMUS API Audit Bundle ZIP, "
                        "but you supplied an ORIMUS mission Evidence Bundle"
                    ],
                )
            if API_AUDIT_BUNDLE_MANIFEST_PATH not in names or API_AUDIT_BUNDLE_PACKAGE_PATH not in names:
                return VerificationResult(
                    False,
                    EXIT_SCHEMA_MISMATCH,
                    ["bundle must contain manifest.json and api_audit_package.json"],
                )
            if any(name.startswith("/") or ".." in Path(name).parts for name in names):
                return VerificationResult(False, EXIT_SCHEMA_MISMATCH, ["bundle contains unsafe member path"])
            manifest = json.loads(bundle.read(API_AUDIT_BUNDLE_MANIFEST_PATH))
            package = json.loads(bundle.read(API_AUDIT_BUNDLE_PACKAGE_PATH))
    except (OSError, zipfile.BadZipFile, json.JSONDecodeError) as error:
        return VerificationResult(False, EXIT_SCHEMA_MISMATCH, [str(error)])

    schema_errors = validate_api_audit_bundle_schema(manifest)
    if schema_errors:
        return VerificationResult(False, EXIT_SCHEMA_MISMATCH, schema_errors)

    hash_errors = validate_api_audit_bundle_hashes(manifest, package)
    if hash_errors:
        return VerificationResult(False, EXIT_HASH_MISMATCH, hash_errors)

    package_result = verify_api_audit_package(package)
    if not package_result.valid:
        return package_result

    semantic_errors = validate_api_audit_bundle_semantics(manifest, package)
    if semantic_errors:
        return VerificationResult(False, EXIT_SEMANTIC_FAILURE, semantic_errors)

    return VerificationResult(True, EXIT_VALID, [])


def validate_api_audit_bundle_schema(manifest: dict) -> list[str]:
    errors = []
    if manifest.get("manifest_type") != API_AUDIT_BUNDLE_MANIFEST_TYPE:
        errors.append(f"manifest_type must be {API_AUDIT_BUNDLE_MANIFEST_TYPE}")
    if manifest.get("schema_version") != API_AUDIT_BUNDLE_SCHEMA_VERSION:
        errors.append(f"schema_version must be {API_AUDIT_BUNDLE_SCHEMA_VERSION}")
    if manifest.get("bundle_hash_algorithm") != "SHA-256":
        errors.append("bundle_hash_algorithm must be SHA-256")
    if manifest.get("api_audit_package_path") != API_AUDIT_BUNDLE_PACKAGE_PATH:
        errors.append("api_audit_package_path must be api_audit_package.json")
    if not isinstance(manifest.get("filters"), dict):
        errors.append("filters must be an object")
    if not isinstance(manifest.get("event_count"), int):
        errors.append("event_count must be an integer")
    return errors


def validate_api_audit_bundle_hashes(manifest: dict, package: dict) -> list[str]:
    errors = []
    if manifest.get("bundle_hash") != hash_api_audit_bundle_manifest(manifest):
        errors.append("bundle_hash mismatch")
    if manifest.get("api_audit_package_hash") != hash_api_audit_package(package):
        errors.append("api_audit_package_hash mismatch")
    return errors


def validate_api_audit_bundle_semantics(manifest: dict, package: dict) -> list[str]:
    errors = []
    summary = package.get("summary") or {}
    if manifest.get("event_count") != summary.get("event_count"):
        errors.append("manifest event_count does not match package summary")
    if manifest.get("filters") != package.get("filters"):
        errors.append("manifest filters do not match package filters")
    return errors
