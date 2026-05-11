import hashlib
import json
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from .artifact_store import hash_file
from .evidence_package import build_evidence_package, hash_evidence_package
from .evidence_verifier import (
    EXIT_HASH_MISMATCH,
    EXIT_SCHEMA_MISMATCH,
    EXIT_SEMANTIC_FAILURE,
    EXIT_VALID,
    VerificationResult,
    verify_evidence_package,
)


EVIDENCE_BUNDLE_SCHEMA_VERSION = "1.0"
BUNDLE_MANIFEST_PATH = "manifest.json"
BUNDLE_PACKAGE_PATH = "evidence_package.json"
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


@dataclass
class ArtifactPayload:
    artifact_id: str
    source: str
    artifact_type: str
    original_file_name: str
    original_file_path: str
    bundled_path: str
    sha256_hash: str
    size_bytes: int
    metadata_json: str
    bytes_data: bytes = field(repr=False)


def build_evidence_bundle(report: dict, artifacts: list[dict]) -> tuple[bytes, dict]:
    package = build_evidence_package(report, generated_at=stable_generated_at(report))
    package_bytes = canonical_json_bytes(package)
    artifact_payloads = build_artifact_payloads(artifacts)
    manifest = build_manifest(package, artifact_payloads)
    manifest_bytes = canonical_json_bytes(manifest)

    files = [
        (BUNDLE_PACKAGE_PATH, package_bytes),
        (BUNDLE_MANIFEST_PATH, manifest_bytes),
        *[(artifact.bundled_path, artifact.bytes_data) for artifact in artifact_payloads],
    ]
    return build_deterministic_zip(files), manifest


def build_artifact_payloads(artifacts: list[dict]) -> list[ArtifactPayload]:
    payloads = []
    for artifact in sorted(artifacts, key=lambda item: item["artifact_id"]):
        artifact_id = artifact["artifact_id"]
        file_path = Path(artifact["file_path"])
        bytes_data = file_path.read_bytes()
        payloads.append(
            ArtifactPayload(
                artifact_id=artifact_id,
                source=artifact["source"],
                artifact_type=artifact["artifact_type"],
                original_file_name=file_path.name,
                original_file_path=str(file_path),
                bundled_path=f"artifacts/{artifact_id}.bin",
                sha256_hash=hash_file(file_path),
                size_bytes=len(bytes_data),
                metadata_json=artifact["metadata_json"],
                bytes_data=bytes_data,
            )
        )
    return payloads


def build_manifest(package: dict, artifacts: list[ArtifactPayload]) -> dict:
    manifest = {
        "manifest_type": "orimus_evidence_bundle_manifest",
        "schema_version": EVIDENCE_BUNDLE_SCHEMA_VERSION,
        "generated_at": package["generated_at"],
        "bundle_hash_algorithm": "SHA-256",
        "bundle_hash": "",
        "evidence_package_path": BUNDLE_PACKAGE_PATH,
        "evidence_package_hash": hash_evidence_package(package),
        "artifact_count": len(artifacts),
        "artifacts": [
            {
                "artifact_id": artifact.artifact_id,
                "source": artifact.source,
                "artifact_type": artifact.artifact_type,
                "original_file_name": artifact.original_file_name,
                "original_file_path": artifact.original_file_path,
                "bundled_path": artifact.bundled_path,
                "sha256_hash": artifact.sha256_hash,
                "size_bytes": artifact.size_bytes,
                "metadata_json": artifact.metadata_json,
            }
            for artifact in artifacts
        ],
    }
    manifest["bundle_hash"] = hash_bundle_manifest(manifest)
    return manifest


def hash_bundle_manifest(manifest: dict) -> str:
    hash_input = dict(manifest)
    hash_input["bundle_hash"] = ""
    return hashlib.sha256(canonical_json_bytes(hash_input)).hexdigest()


def canonical_json_bytes(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def pretty_json_bytes(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, indent=2).encode("utf-8")


def build_deterministic_zip(files: list[tuple[str, bytes]]) -> bytes:
    archive = BytesIO()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for bundled_path, content in sorted(files, key=lambda item: item[0]):
            info = zipfile.ZipInfo(bundled_path, ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            bundle.writestr(info, content)
    return archive.getvalue()


def stable_generated_at(report: dict) -> str:
    mission = report.get("mission") or {}
    stamp = mission.get("stamp") or {}
    sec = int(stamp.get("sec") or 0)
    return datetime.fromtimestamp(sec, timezone.utc).isoformat()


def verify_evidence_bundle(bundle_path: Path) -> VerificationResult:
    try:
        with zipfile.ZipFile(bundle_path, "r") as bundle:
            names = bundle.namelist()
            if names != sorted(names):
                return VerificationResult(
                    False,
                    EXIT_HASH_MISMATCH,
                    ["bundle zip entries are not sorted"],
                )
            if BUNDLE_MANIFEST_PATH not in names or BUNDLE_PACKAGE_PATH not in names:
                return VerificationResult(
                    False,
                    EXIT_SCHEMA_MISMATCH,
                    ["bundle must contain manifest.json and evidence_package.json"],
                )
            if any(name.startswith("/") or ".." in Path(name).parts for name in names):
                return VerificationResult(
                    False,
                    EXIT_SCHEMA_MISMATCH,
                    ["bundle contains unsafe member path"],
                )
            manifest = json.loads(bundle.read(BUNDLE_MANIFEST_PATH))
            package = json.loads(bundle.read(BUNDLE_PACKAGE_PATH))
            artifact_bytes = {
                name: bundle.read(name)
                for name in names
                if name.startswith("artifacts/")
            }
    except (OSError, zipfile.BadZipFile, json.JSONDecodeError) as error:
        return VerificationResult(False, EXIT_SCHEMA_MISMATCH, [str(error)])

    schema_errors = validate_bundle_schema(manifest)
    if schema_errors:
        return VerificationResult(False, EXIT_SCHEMA_MISMATCH, schema_errors)

    hash_errors = validate_bundle_hashes(manifest, package, artifact_bytes)
    if hash_errors:
        return VerificationResult(False, EXIT_HASH_MISMATCH, hash_errors)

    package_result = verify_evidence_package(package)
    if not package_result.valid:
        return package_result

    semantic_errors = validate_bundle_semantics(manifest, artifact_bytes)
    if semantic_errors:
        return VerificationResult(False, EXIT_SEMANTIC_FAILURE, semantic_errors)

    return VerificationResult(True, EXIT_VALID, [])


def validate_bundle_schema(manifest: dict) -> list[str]:
    errors = []
    if manifest.get("manifest_type") != "orimus_evidence_bundle_manifest":
        errors.append("manifest_type must be orimus_evidence_bundle_manifest")
    if manifest.get("schema_version") != EVIDENCE_BUNDLE_SCHEMA_VERSION:
        errors.append(f"schema_version must be {EVIDENCE_BUNDLE_SCHEMA_VERSION}")
    if manifest.get("bundle_hash_algorithm") != "SHA-256":
        errors.append("bundle_hash_algorithm must be SHA-256")
    if manifest.get("evidence_package_path") != BUNDLE_PACKAGE_PATH:
        errors.append("evidence_package_path must be evidence_package.json")
    if not isinstance(manifest.get("artifacts"), list):
        errors.append("artifacts must be an array")
    for artifact in manifest.get("artifacts", []):
        bundled_path = artifact.get("bundled_path")
        artifact_id = artifact.get("artifact_id")
        if bundled_path != f"artifacts/{artifact_id}.bin":
            errors.append(f"artifact {artifact_id} has unsafe bundled_path")
    return errors


def validate_bundle_hashes(
    manifest: dict,
    package: dict,
    artifact_bytes: dict[str, bytes],
) -> list[str]:
    errors = []
    if manifest.get("bundle_hash") != hash_bundle_manifest(manifest):
        errors.append("bundle_hash mismatch")
    if manifest.get("evidence_package_hash") != hash_evidence_package(package):
        errors.append("evidence_package_hash mismatch")
    for artifact in manifest.get("artifacts", []):
        path = artifact.get("bundled_path")
        content = artifact_bytes.get(path)
        if content is None:
            continue
        actual_hash = hashlib.sha256(content).hexdigest()
        if actual_hash != artifact.get("sha256_hash"):
            errors.append(f"artifact {artifact.get('artifact_id')} hash mismatch")
    return errors


def validate_bundle_semantics(
    manifest: dict,
    artifact_bytes: dict[str, bytes],
) -> list[str]:
    errors = []
    artifacts = manifest.get("artifacts", [])
    if manifest.get("artifact_count") != len(artifacts):
        errors.append("artifact_count does not match artifacts")
    for artifact in artifacts:
        artifact_id = artifact.get("artifact_id")
        path = artifact.get("bundled_path")
        content = artifact_bytes.get(path)
        if content is None:
            errors.append(f"missing artifact file {path}")
            continue
        if len(content) != artifact.get("size_bytes"):
            errors.append(f"artifact {artifact_id} size mismatch")
    return errors
