# ORIMUS Evidence Bundle Schema v1.0

An ORIMUS Evidence Bundle is a ZIP handoff package for one finalized mission report and its referenced evidence artifact files.

## Bundle Contents

The ZIP contains:

- `evidence_package.json`
- `manifest.json`
- `artifacts/{artifact_id}.bin`

Artifact filenames inside the ZIP are based only on `artifact_id`. Original file names and paths are metadata in `manifest.json`; they are never used as ZIP paths.

## Determinism Rules

Bundle generation is deterministic:

- ZIP entries are written in alphabetical order by bundled path.
- ZIP member timestamps are fixed.
- `evidence_package.json` and `manifest.json` are serialized as canonical JSON with sorted keys and compact separators.
- `manifest.bundle_hash` is calculated from canonical `manifest.json` content with `bundle_hash` set to an empty string.

Rebuilding the same bundle from the same mission report and artifact bytes should produce the same ZIP bytes and the same `bundle_hash`.

## Manifest Fields

`manifest.json` contains:

- `manifest_type`
- `schema_version`
- `generated_at`
- `bundle_hash_algorithm`
- `bundle_hash`
- `evidence_package_path`
- `evidence_package_hash`
- `artifact_count`
- `artifacts`

Each artifact entry contains:

- `artifact_id`
- `source`
- `artifact_type`
- `original_file_name`
- `original_file_path`
- `bundled_path`
- `sha256_hash`
- `size_bytes`
- `metadata_json`

## Verification

The verifier checks:

- `manifest.bundle_hash`
- `evidence_package_hash`
- the embedded evidence package's own `export_hash`
- the embedded mission report's `content_hash`
- every bundled artifact SHA-256 hash
- expected artifact files are present

Missing artifact files are semantic failures and use verifier exit code `3`.
