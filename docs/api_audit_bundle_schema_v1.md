# API Audit Bundle Schema v1.0

An ORIMUS API Audit Bundle is a deterministic ZIP wrapper around an ORIMUS API Audit Package JSON file.

This schema evolves independently from both [API Audit Package Schema v1.0](api_audit_package_schema_v1.md) and [Evidence Bundle Schema v1.0](evidence_bundle_schema_v1.md). Evidence bundles describe mission evidence. API audit bundles describe backend API authorization decisions.

## ZIP Contents

The bundle contains exactly:

- `api_audit_package.json`
- `manifest.json`

ZIP entries are written in alphabetical order by bundled path with fixed ZIP timestamps, so rebuilding the same bundle from the same audit events produces the same bytes.

## Manifest Fields

`manifest.json` contains:

- `manifest_type`: must be `orimus_api_audit_bundle_manifest`
- `schema_version`: currently `1.0`
- `generated_at_sec`: Unix timestamp copied from the API audit package
- `bundle_hash_algorithm`: must be `SHA-256`
- `bundle_hash`: SHA-256 hash of the canonical manifest with `bundle_hash` set to an empty string
- `api_audit_package_path`: must be `api_audit_package.json`
- `api_audit_package_hash`: SHA-256 export hash of the embedded API audit package
- `event_count`: event count copied from the package summary
- `filters`: filters copied from the package

## Verification

Use:

```powershell
docker compose run --rm backend python backend/scripts/verify_audit_bundle.py path/to/audit-bundle.zip
```

The verifier checks:

- ZIP readability
- sorted deterministic ZIP entries
- required member files
- safe member paths
- manifest schema
- manifest bundle hash
- embedded API audit package hash
- embedded API audit package validity
- manifest event count and filters matching the embedded package

Exit codes match the ORIMUS verifier family:

- `0`: valid
- `1`: hash mismatch
- `2`: schema mismatch or unreadable ZIP/JSON
- `3`: semantic failure

This verifier is only for ORIMUS API Audit Bundle ZIP files. Mission Evidence Bundles must be checked with `backend/scripts/verify_evidence_bundle.py`.
